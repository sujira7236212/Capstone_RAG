"""Feedback service (docs/plans/app_integration_plan.md A5).

The app's writeFeedback() (MU-Capstone-Application lib/analysis/feedback.ts, ADR-0007) posts
its FeedbackInput here and stores the answer in sets.llm_feedback. Any non-2xx answer is shown
to the user as "Feedback failed: <body>" with a Retry button (the app's docs/HANDOVER.md
section 3), so every error body is one plain-text sentence a user can read.

Run it bound to localhost, never on a public interface:
    python -m service

Configuration, all from the environment (the repo's .env is read too):
    KB_DATABASE_URL      Postgres that holds the KB's langchain tables: the app's Supabase
                         one, e.g. postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres
                         locally (filled by tools/copy_kb.py). Unset: DATABASE_URL, the
                         database the eval scripts use
    GOOGLE_API_KEY       query embeddings (gemini-embedding-2) and the Gemini LLM. Queries
                         are served from .cache/query_vectors/ (tools/fill_query_cache.py),
                         so with a full cache a request makes no embedding call
    KB_COLLECTION        default embedding_config.default_collection()
    FEEDBACK_LLM_PROVIDER  gemini (default, D5) or groq: a free model while the integration
                         is tried out (2026-10-27), needs GROQ_API_KEY
    FEEDBACK_LLM_MODEL   default gemini-3.6-flash (D5), or qwen/qwen3.8-27b on groq (the model
                         eval/generate_groq.py ran v14 on)
    FEEDBACK_LLM_THINKING  Gemini's thinking_level, default low: at the model's own default,
                         v14's long answer did not finish inside 34 s on the first live call
                         (2026-10-25); "" keeps the model's default
    FEEDBACK_TIMEOUT_S   budget for one request, default 45: the app gives up at 60
    FEEDBACK_PORT        default 8100

Each request is logged with its duration, version and chunks kept per error. The profile,
the medical history and the feedback text are never logged.
"""
import json
import logging
import os
import subprocess
import sys
import threading
import time
from typing import Literal, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.responses import PlainTextResponse  # noqa: E402
from pydantic import BaseModel, ConfigDict  # noqa: E402

import embedding_config  # noqa: E402
from rag_core.app_input import payload_from_feedback_input, rule_names  # noqa: E402
from rag_core.generate import build_chain  # noqa: E402
from rag_core.prompt import APP_PROMPT_VERSION, APP_SYSTEM_PROMPT  # noqa: E402
from rag_core.query_cache import CachedEmbeddings  # noqa: E402
from rag_core.retrieval import DEFAULT_CONFIG, open_vectorstore, retrieve_kb_context  # noqa: E402

log = logging.getLogger("feedback")

KB_COLLECTION = os.environ.get("KB_COLLECTION") or embedding_config.default_collection()
KB_DATABASE_URL = os.environ.get("KB_DATABASE_URL") or None  # None: embedding_config.get_connection()
DEFAULT_MODELS = {"gemini": "gemini-3.6-flash", "groq": "qwen/qwen3.8-27b"}
LLM_PROVIDER = os.environ.get("FEEDBACK_LLM_PROVIDER") or "gemini"
if LLM_PROVIDER not in DEFAULT_MODELS:
    raise SystemExit(f"FEEDBACK_LLM_PROVIDER={LLM_PROVIDER!r}, want one of {sorted(DEFAULT_MODELS)}")
LLM_MODEL = os.environ.get("FEEDBACK_LLM_MODEL") or DEFAULT_MODELS[LLM_PROVIDER]
LLM_THINKING = (os.environ.get("FEEDBACK_LLM_THINKING", "low") or None) if LLM_PROVIDER == "gemini" else None
LLM_KEY_ENV = {"gemini": "GOOGLE_API_KEY", "groq": "GROQ_API_KEY"}[LLM_PROVIDER]
TIMEOUT_S = float(os.environ.get("FEEDBACK_TIMEOUT_S") or 45)
RATE_LIMIT_WAIT_S = 3  # one retry after a 429, only if the budget still has room for a call
MIN_CALL_S = 10  # an LLM call given less than this would only time out


def _commit():
    """The checked-out commit, '-dirty' when the tree has changes: feedback written by an
    uncommitted prompt or gate must not look like it came from a tagged one."""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                             text=True, timeout=5, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                               capture_output=True, text=True, timeout=5).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return os.environ.get("FEEDBACK_COMMIT", "unknown")


VERSION = {"prompt": APP_PROMPT_VERSION, "collection": KB_COLLECTION, "llm": f"{LLM_PROVIDER}:{LLM_MODEL}",
           "thinking": LLM_THINKING, "commit": _commit()}


# --- the input contract -------------------------------------------------------------
# Only the fields the adapter reads are declared, so a contract break is a readable 422
# instead of a KeyError. Everything else the app sends is accepted and passed through.

class _Open(BaseModel):
    model_config = ConfigDict(extra="allow")


class Exercise(_Open):
    id: str
    name: str = ""


class Totals(_Open):
    attempts: int
    completed_reps: int
    correct_reps: int
    abandoned_attempts: int = 0


class Violation(_Open):
    rule: str
    priority: int = 99


class Attempt(_Open):
    attempt_no: int
    outcome: Literal["correct", "incorrect", "abandoned"]
    violations: list[Violation] = []
    similarity: Optional[dict] = None


class SetSummary(_Open):
    set_no: int
    kind: str = "initial"
    totals: Totals
    similarity: Optional[dict] = None


class CurrentSet(SetSummary):
    attempts: list[Attempt]


class Workout(_Open):
    target_reps: Optional[int] = None
    target_sets: Optional[int] = None
    earlier_sets: list[SetSummary] = []


class PastWorkout(_Open):
    started_at: str
    sets: list[SetSummary] = []


class Profile(_Open):
    medical_history: Optional[str] = None


class FeedbackInput(_Open):
    profile: Profile = Profile()
    exercise: Exercise
    workout: Workout = Workout()
    set: CurrentSet
    history: list[PastWorkout] = []


# --- dependencies, replaceable in tests ---------------------------------------------

class ServiceError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message


class Deps:
    """The vector store is opened on first use, not at import, so the service starts (and
    /health can say what is wrong) while the database is still down."""

    def __init__(self):
        self._lock = threading.Lock()
        self._vectorstore = None

    def vectorstore(self):
        with self._lock:
            if self._vectorstore is None:
                self._vectorstore = open_vectorstore(KB_COLLECTION, connection=KB_DATABASE_URL,
                                                     embeddings=CachedEmbeddings(embedding_config.get_embeddings()))
            return self._vectorstore

    def chain(self, context, timeout):
        return build_chain(context, LLM_MODEL, timeout=timeout, max_retries=1, thinking_level=LLM_THINKING,
                           provider=LLM_PROVIDER, system_prompt=APP_SYSTEM_PROMPT)

    def count_rows(self):
        import sqlalchemy
        engine = sqlalchemy.create_engine(KB_DATABASE_URL or embedding_config.get_connection())
        try:
            with engine.connect() as conn:
                return conn.execute(sqlalchemy.text(
                    "SELECT count(*) FROM langchain_pg_embedding e "
                    "JOIN langchain_pg_collection c ON c.uuid = e.collection_id WHERE c.name = :name"),
                    {"name": KB_COLLECTION}).scalar_one()
        finally:
            engine.dispose()


deps = Deps()
app = FastAPI(title="RAG feedback", docs_url=None, redoc_url=None)


@app.exception_handler(ServiceError)
def _service_error(request: Request, exc: ServiceError):
    return PlainTextResponse(exc.message, status_code=exc.status)


@app.exception_handler(RequestValidationError)
def _bad_input(request: Request, exc: RequestValidationError):
    where = "; ".join(f"{'.'.join(str(p) for p in e['loc'] if p != 'body')}: {e['msg']}" for e in exc.errors()[:3])
    return PlainTextResponse(f"the feedback input does not match the contract ({where})", status_code=422)


def _is_rate_limit(e):
    return "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)


def _is_timeout(e):
    text = f"{type(e).__name__} {e}".lower()
    return "timeout" in text or "timed out" in text or "deadline" in text


def _generate(context, payload, deadline):
    payload = json.dumps(payload, indent=2)
    for attempt in (1, 2):
        remaining = deadline - time.monotonic()
        if remaining < MIN_CALL_S:
            raise ServiceError(504, "the language model did not answer in time, try again")
        try:
            return deps.chain(context, timeout=remaining).invoke(payload)
        except Exception as e:  # noqa: BLE001 - every provider error becomes one readable line
            # Groq's 429 names its wait (rag_core.generate.GroqError.retry_after); Gemini's does not.
            wait = getattr(e, "retry_after", None) or RATE_LIMIT_WAIT_S
            if _is_rate_limit(e) and attempt == 1 and deadline - time.monotonic() > MIN_CALL_S + wait:
                log.warning("rate limited, retrying once in %ss", wait)
                time.sleep(wait)
                continue
            log.error("generation failed: %s: %s", type(e).__name__, str(e)[:300])
            if _is_rate_limit(e):
                raise ServiceError(503, "the language model is busy right now, try again in a minute")
            if _is_timeout(e):
                raise ServiceError(504, "the language model did not answer in time, try again")
            raise ServiceError(502, "the language model could not write feedback this time, try again")


@app.post("/feedback")
def feedback(inp: FeedbackInput):
    # A plain def: FastAPI runs it in its thread pool, so the blocking DB and HTTP calls
    # below do not stall other requests.
    started = time.monotonic()
    deadline = started + TIMEOUT_S
    payload = payload_from_feedback_input(inp.model_dump())
    errors = rule_names(payload)
    exercise = payload["exercise"]
    try:
        context, metrics = retrieve_kb_context(deps.vectorstore(), exercise["id"], exercise["name"],
                                               errors, cfg=DEFAULT_CONFIG)
    except Exception as e:  # noqa: BLE001
        log.error("retrieval failed: %s: %s", type(e).__name__, str(e)[:300])
        raise ServiceError(503, "the exercise knowledge base is not reachable, try again")
    text = _generate(context, payload, deadline)
    kept = {}
    for m in metrics:
        kept[m["error"]] = kept.get(m["error"], 0) + m["kept"]
    log.info(json.dumps({"ms": round((time.monotonic() - started) * 1000), "exercise": exercise["id"],
                         "kind": inp.set.kind, "kept": kept, "chars": len(text), **VERSION}))
    return {"feedback": text, "version": VERSION}


@app.get("/health")
def health():
    try:
        rows = deps.count_rows()
    except Exception as e:  # noqa: BLE001
        log.error("health: %s: %s", type(e).__name__, str(e)[:300])
        raise ServiceError(503, "the knowledge base database is not reachable")
    if not rows:
        raise ServiceError(503, f"the knowledge base collection {KB_COLLECTION} is empty or missing")
    for key in sorted({"GOOGLE_API_KEY", LLM_KEY_ENV}):
        if not os.environ.get(key):
            raise ServiceError(503, f"{key} is not set")
    return {"ok": True, "rows": rows, "version": VERSION}
