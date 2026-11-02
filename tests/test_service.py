"""service/app.py through FastAPI's TestClient, with the vector store, the LLM chain and the
row count replaced: no database, no API key, no paid call.

    python tests/test_service.py
"""
import copy
import json
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("GOOGLE_API_KEY", "test-key")

from fastapi.testclient import TestClient  # noqa: E402

from rag_core.generate import GroqError  # noqa: E402
from service import app as svc  # noqa: E402

failed = 0


def check(name, got, expected):
    global failed
    if got != expected:
        failed += 1
        print(f"FAIL  {name}\n  got: {got}\n  exp: {expected}")


class Doc:
    def __init__(self, text, kind, tags):
        self.id = text
        self.page_content = text
        self.metadata = {"text": text, "item_kind": kind, "fault_tags": tags, "exercise_id": "squat",
                         "source": "C:/data/squat/Paper.pdf [part 1/2]"}


DOCS = [Doc("Knees collapse inward as you stand up.", "mistake", "|knee_valgus|"),
        Doc("Push the knees out over the toes.", "principle", "|knee_valgus|"),
        Doc("Stopping well above parallel.", "mistake", "|partial_squat|")]


class Store:
    collection_name = "fake"
    embeddings = types.SimpleNamespace(embed_query=lambda q: q)

    def similarity_search_with_score(self, query, k, filter):
        like = (filter.get("fault_tags") or {}).get("$like", "").strip("%")
        hits = [d for d in DOCS if d.metadata["item_kind"] in filter["item_kind"]["$in"]
                and like in d.metadata["fault_tags"]]
        return [(d, 0.1) for d in hits[:k]]

    similarity_search_with_score_by_vector = similarity_search_with_score


class Chain:
    """Records what the model would have been sent; answers from `script` in order."""

    def __init__(self, script):
        self.script, self.calls = list(script), []

    def __call__(self, context, timeout):
        outer = self

        class _C:
            def invoke(self, payload):
                outer.calls.append({"context": context, "payload": payload, "timeout": timeout})
                step = outer.script.pop(0)
                if isinstance(step, Exception):
                    raise step
                return step
        return _C()


def setup(script, rows=10, store=Store):
    """`store` and a callable `rows` are factories, called the way Deps calls its own."""
    chain = Chain(script)
    svc.deps.vectorstore = store
    svc.deps.chain = chain
    svc.deps.count_rows = rows if callable(rows) else (lambda: rows)
    return chain


svc.RATE_LIMIT_WAIT_S = 0
svc.CAPTURE_PATH = None  # a FEEDBACK_CAPTURE in .env must not collect these fake requests
client = TestClient(svc.app)
with open(os.path.join(ROOT, "docs/plans/feedback_input_example.json"), encoding="utf-8") as f:
    EXAMPLE = json.load(f)

# --- happy path ---------------------------------------------------------------------
chain = setup(["Good set. Push your knees out."])
r = client.post("/feedback", json=EXAMPLE)
check("ok: status", r.status_code, 200)
body = r.json()
check("ok: feedback text", body["feedback"], "Good set. Push your knees out.")
check("ok: version keys", sorted(body["version"]), ["collection", "commit", "llm", "prompt", "thinking"])
check("ok: prompt version", body["version"]["prompt"], "v16")
check("ok: one LLM call", len(chain.calls), 1)
sent = chain.calls[0]
check("ok: context retrieved for the set's faults", "[mistake | re: knee_valgus |" in sent["context"], True)
check("ok: payload in the app's keys", json.loads(sent["payload"])["set"]["totals"]["attempts"], 5)
captured = {}
real_build_chain = svc.build_chain
svc.build_chain = lambda context, model, **kw: captured.update(kw)
svc.Deps().chain("ctx", timeout=5)
svc.build_chain = real_build_chain
check("ok: the chain gets the app prompt", captured.get("system_prompt") is svc.APP_SYSTEM_PROMPT, True)
check("ok: medical history sent (v15, mock profiles)", json.loads(sent["payload"])["profile"],
      {"medical_history": "Left knee ACL reconstruction in 2024, no pain now"})
check("ok: timeout within budget", 0 < sent["timeout"] <= svc.TIMEOUT_S, True)

# --- the input contract -------------------------------------------------------------
setup(["unused"])
bad = copy.deepcopy(EXAMPLE)
bad["set"]["attempts"][0]["outcome"] = "skipped"
r = client.post("/feedback", json=bad)
check("422: status", r.status_code, 422)
check("422: plain text naming the field", r.headers["content-type"].startswith("text/plain")
      and "set.attempts.0.outcome" in r.text, True)
missing = copy.deepcopy(EXAMPLE)
del missing["exercise"]
r = client.post("/feedback", json=missing)
check("422: missing exercise", (r.status_code, "exercise" in r.text), (422, True))
extra = copy.deepcopy(EXAMPLE)
extra["profile"]["display_name"] = "Someone"
extra["set"]["attempts"][1]["violations"][0]["message"] = "Knees out"
chain = setup(["fine"])
check("extra app fields accepted", client.post("/feedback", json=extra).status_code, 200)
check("only the medical history of the profile is sent",
      ("Someone" in chain.calls[0]["payload"], "Knees out" in chain.calls[0]["payload"]), (False, False))

# --- failures the app shows as "Feedback failed: ..." -------------------------------
chain = setup([RuntimeError("429 RESOURCE_EXHAUSTED"), "second try"])
r = client.post("/feedback", json=EXAMPLE)
check("429 once: retried and answered", (r.status_code, r.json()["feedback"], len(chain.calls)), (200, "second try", 2))

setup([RuntimeError("429 RESOURCE_EXHAUSTED"), RuntimeError("429 RESOURCE_EXHAUSTED")])
r = client.post("/feedback", json=EXAMPLE)
check("429 twice: 503 plain text", (r.status_code, r.text),
      (503, "the language model is busy right now, try again in a minute"))

chain = setup([GroqError("Groq HTTP 429: Rate limit reached", retry_after=0.01), "after the wait"])
r = client.post("/feedback", json=EXAMPLE)
check("groq 429 with retry-after: waited and answered", (r.status_code, len(chain.calls)), (200, 2))

chain = setup([GroqError("Groq HTTP 429: Rate limit reached", retry_after=600), "unused"])
r = client.post("/feedback", json=EXAMPLE)
check("groq 429, wait past the budget: 503 at once", (r.status_code, len(chain.calls)), (503, 1))

setup([TimeoutError("Read timed out")])
r = client.post("/feedback", json=EXAMPLE)
check("timeout: 504", r.status_code, 504)

setup([ValueError("API key not valid")])
r = client.post("/feedback", json=EXAMPLE)
check("other LLM error: 502, provider text not leaked", (r.status_code, "API key" in r.text), (502, False))


def broken_store():
    raise ConnectionError("connection refused")


setup(["unused"], store=broken_store)
r = client.post("/feedback", json=EXAMPLE)
check("DB down: 503", (r.status_code, r.text), (503, "the exercise knowledge base is not reachable, try again"))

old_timeout = svc.TIMEOUT_S
svc.TIMEOUT_S = svc.MIN_CALL_S - 1
chain = setup(["unused"])
r = client.post("/feedback", json=EXAMPLE)
check("no budget left: 504 without calling the LLM", (r.status_code, len(chain.calls)), (504, 0))
svc.TIMEOUT_S = old_timeout

# --- FEEDBACK_CAPTURE -------------------------------------------------------------------
import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    old_capture = svc.CAPTURE_PATH
    svc.CAPTURE_PATH = None
    setup(["not captured"])
    client.post("/feedback", json=EXAMPLE)
    check("capture off: nothing written", os.listdir(tmp), [])

    svc.CAPTURE_PATH = os.path.join(tmp, "capture", "requests.jsonl")
    setup(["Good set. Push your knees out."])
    client.post("/feedback", json=EXAMPLE)
    setup([ValueError("API key not valid")])
    client.post("/feedback", json=EXAMPLE)
    setup(["unused"], store=broken_store)
    client.post("/feedback", json=EXAMPLE)
    with open(svc.CAPTURE_PATH, encoding="utf-8") as f:
        lines = [json.loads(line) for line in f]
    check("capture: one line per request, failures included", len(lines), 3)
    ok, llm_failed, db_failed = lines
    check("capture: the app's input as sent", ok["input"]["set"]["totals"], EXAMPLE["set"]["totals"])
    check("capture: rule names as a sorted JSON list",
          (isinstance(ok["errors"], list), len(ok["errors"]) > 0, ok["errors"] == sorted(ok["errors"])), (True, True, True))
    check("capture: medical history kept", ok["input"]["profile"]["medical_history"],
          EXAMPLE["profile"]["medical_history"])
    check("capture: payload, context, answer, version",
          (ok["payload"]["set"]["totals"]["attempts"], "[mistake | re: knee_valgus |" in ok["context"],
           ok["feedback"], ok["version"]["prompt"], ok["error"]), (5, True, "Good set. Push your knees out.", "v16", None))
    check("capture: LLM failure keeps the context and the error",
          (llm_failed["context"] is not None, llm_failed["feedback"], llm_failed["error"]["status"]), (True, None, 502))
    check("capture: DB failure has no context", (db_failed["context"], db_failed["error"]["status"]), (None, 503))

    svc.CAPTURE_PATH = os.path.join(tmp, "not-a-dir.jsonl", "requests.jsonl")
    open(os.path.join(tmp, "not-a-dir.jsonl"), "w").close()  # a file where the folder should be
    setup(["still answered"])
    r = client.post("/feedback", json=EXAMPLE)
    check("capture write fails: request still answered", (r.status_code, r.json()["feedback"]), (200, "still answered"))
    svc.CAPTURE_PATH = old_capture

# --- health -------------------------------------------------------------------------
setup([], rows=2197)
r = client.get("/health")
check("health: ok", (r.status_code, r.json()["ok"], r.json()["rows"]), (200, True, 2197))
setup([], rows=0)
check("health: empty collection", client.get("/health").status_code, 503)


def db_down():
    raise ConnectionError("refused")


setup([], rows=db_down)
check("health: DB down", client.get("/health").status_code, 503)

print("all passed" if not failed else f"{failed} failure(s)")
sys.exit(1 if failed else 0)
