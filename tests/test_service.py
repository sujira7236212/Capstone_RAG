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
check("ok: prompt version", body["version"]["prompt"], "v14")
check("ok: one LLM call", len(chain.calls), 1)
sent = chain.calls[0]
check("ok: context retrieved for the set's faults", "[mistake | re: knee_valgus |" in sent["context"], True)
check("ok: payload is the adapted session", json.loads(sent["payload"])["summary"]["total_reps"], 5)
check("ok: medical history never sent", "ACL" in sent["payload"] or "health_notes" in sent["payload"], False)
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
setup(["fine"])
check("extra app fields accepted", client.post("/feedback", json=extra).status_code, 200)

# --- failures the app shows as "Feedback failed: ..." -------------------------------
chain = setup([RuntimeError("429 RESOURCE_EXHAUSTED"), "second try"])
r = client.post("/feedback", json=EXAMPLE)
check("429 once: retried and answered", (r.status_code, r.json()["feedback"], len(chain.calls)), (200, "second try", 2))

setup([RuntimeError("429 RESOURCE_EXHAUSTED"), RuntimeError("429 RESOURCE_EXHAUSTED")])
r = client.post("/feedback", json=EXAMPLE)
check("429 twice: 503 plain text", (r.status_code, r.text),
      (503, "the language model is busy right now, try again in a minute"))

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
