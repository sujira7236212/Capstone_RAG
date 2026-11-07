"""eval/replay_captured.py with the vector store and the LLM chain replaced: no database, no API
key, no paid call.

    python tests/test_replay_captured.py
"""
import json
import os
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "eval"))
os.environ.setdefault("GOOGLE_API_KEY", "test-key")

from fastapi.testclient import TestClient  # noqa: E402

import judge_pairwise  # noqa: E402
import replay_captured as rc  # noqa: E402
from service import app as svc  # noqa: E402

svc.CAPTURE_PATH = None  # a FEEDBACK_CAPTURE in .env must not collect these fake requests
svc.RATE_LIMIT_WAIT_S = 0
failed = 0


def check(name, got, expected):
    global failed
    if got != expected:
        failed += 1
        print(f"FAIL  {name}\n  got: {got}\n  exp: {expected}")


def attempt(n, *rules):
    return {"attempt_no": n, "outcome": "incorrect" if rules else "correct", "frame_end": n * 10,
            "similarity": {"score": 70.0}, "violations": [{"rule": r, "priority": 1} for r in rules]}


def make_input(exercise, attempts, medical="None", name="A", ended_by="target_reached", kind="initial",
               target=(10, 1), scored=True, history=()):
    return {"profile": {"display_name": name, "medical_history": medical, "age": 30, "gender": "x",
                        "weight_kg": 60, "height_cm": 170},
            "exercise": {"id": exercise, "name": exercise, "rules": []},
            "workout": {"target_reps": target[0], "target_sets": target[1], "rest_seconds": 60, "earlier_sets": []},
            "set": {"set_no": 1, "kind": kind, "ended_by": ended_by, "feedback": None,
                    "totals": {"attempts": len(attempts), "completed_reps": len(attempts),
                               "correct_reps": sum(not a["violations"] for a in attempts), "abandoned_attempts": 0},
                    "similarity": {"mean_score": 70.0} if scored else None, "attempts": attempts},
            "history": list(history)}


def faulty(rule, wrong, total=10):
    return [attempt(i, rule) if i <= wrong else attempt(i) for i in range(1, total + 1)]


def record(inp, at="2026-11-07T00:00:00Z", context="captured context", feedback="old answer"):
    return {"captured_at": at, "input": inp, "payload": rc.load_service().payload_from_feedback_input(inp),
            "context": context, "feedback": feedback, "version": {"prompt": "v16"}}


def read(records):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "c.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
            f.write("not json\n")
        return rc.read_captures([path])


def cell_of(inp):
    return rc.classify(inp)


# --- which cell ----------------------------------------------------------------------------
check("36 cells", rc.CELLS_WANTED, 36)
check("persistent at 7 of 10", cell_of(make_input("squat", faulty("partial_squat", 7))),
      ("squat/partial_squat/persistent", None))
check("sporadic at 2", cell_of(make_input("squat", faulty("rounded_back", 2))), ("squat/rounded_back/sporadic", None))
check("sporadic at 4", cell_of(make_input("squat", faulty("rounded_back", 4))), ("squat/rounded_back/sporadic", None))
check("5 of 10 is between", cell_of(make_input("squat", faulty("rounded_back", 5))), (None, "between_patterns"))
check("1 of 10 is too few", cell_of(make_input("squat", faulty("rounded_back", 1))), (None, "between_patterns"))
stray = faulty("elbow_flare", 8)
stray[9] = attempt(10, "partial_curl")
check("one stray attempt stays single", cell_of(make_input("bicep-curl", stray)),
      ("bicep-curl/elbow_flare/persistent", None))
mixed = faulty("elbow_flare", 6)
mixed[8], mixed[9] = attempt(9, "partial_curl"), attempt(10, "partial_curl")
check("two other attempts make it mixed", cell_of(make_input("bicep-curl", mixed)), ("bicep-curl/mixed", None))
both = [attempt(i, "elbow_flare", "partial_curl") for i in range(1, 11)]
check("both on every attempt is mixed", cell_of(make_input("bicep-curl", both)), ("bicep-curl/mixed", None))
clean = [attempt(i) for i in range(1, 11)]
check("clean", cell_of(make_input("lunge", clean)), ("lunge/clean", None))
check("'none.' is no history", cell_of(make_input("lunge", clean, medical=" none. ")), ("lunge/clean", None))
check("medical with a fault", cell_of(make_input("lunge", faulty("shallow_lunge", 3), medical="knee surgery")),
      ("lunge/medical", None))
check("medical clean is not a cell", cell_of(make_input("lunge", clean, medical="knee surgery")),
      (None, "medical_without_fault"))
check("repair apart", cell_of(make_input("squat", clean, kind="repair")), (None, "repair_set"))
check("other target", cell_of(make_input("squat", clean, target=(8, 2))), (None, "target_not_10x1"))
check("no similarity", cell_of(make_input("squat", clean, scored=False)), (None, "no_similarity"))
stubbed = make_input("squat", clean)
stubbed["set"]["similarity"]["model"] = "stub"
check("the app's similarity stub", cell_of(stubbed), (None, "stub_similarity"))
check("rule of another exercise", cell_of(make_input("squat", faulty("elbow_flare", 8))), (None, "unknown_rule"))

# --- reading: duplicates, order, the cut-off, first in a cell --------------------------------
A = make_input("squat", faulty("partial_squat", 8))
A_unscored = make_input("squat", faulty("partial_squat", 8), scored=False)
records, lines, bad = read([record(A_unscored, "2026-11-07T01:00:00Z"), record(A, "2026-11-07T02:00:00Z"),
                            record(A_unscored, "2026-11-07T03:00:00Z")])
check("Retry captures one set", (len(records), lines, bad), (1, 4, 1))
check("the capture with similarity is kept", rc.overall_score(records[0]["input"]["set"]["similarity"]), 70.0)
check("its first time stays", records[0]["captured_at"], "2026-11-07T01:00:00Z")
check("another person's set is another set", rc.set_id(A) == rc.set_id(make_input("squat", faulty("partial_squat", 8), name="B")), False)

B = make_input("squat", faulty("partial_squat", 9, 10), name="B")
old = make_input("squat", faulty("partial_squat", 7), name="old")
records, _, _ = read([record(B, "2026-11-08T00:00:00Z"), record(A, "2026-11-07T00:00:00Z"), record(old, "2026-11-02T00:00:00Z")])
test, surplus, reasons = rc.build_test_set(records)
check("the first in a cell is the test set", test["squat/partial_squat/persistent"]["input"]["profile"]["display_name"], "A")
check("the next is surplus", [r["input"]["profile"]["display_name"] for r in surplus], ["B"])
check("before the cut-off does not count", reasons["before_since"], 1)
report = rc.coverage_report(records, 3, 0)
check("the report counts and names no one", ("1/36 cells" in report, "1 +1" in report, "before_since: 1" in report,
                                             "old" not in report.replace("before", "")), (True, True, True, True))


# --- run -------------------------------------------------------------------------------------
class Chain:
    """Records what the model would have been sent; answers from `script` in order."""

    def __init__(self, script):
        self.script, self.calls = list(script), []

    def __call__(self, context, timeout):
        outer = self

        class _C:
            def invoke(self, payload):
                outer.calls.append({"context": context, "payload": payload})
                step = outer.script.pop(0) if outer.script else "answer"
                if isinstance(step, Exception):
                    raise step
                return step
        return _C()


CONTEXT = "retrieved context"
svc.retrieve_kb_context = lambda store, ex, name, errors, cfg=None: (CONTEXT, [])


def setup(script=()):
    chain = Chain(script)
    svc.deps.vectorstore = lambda: types.SimpleNamespace(embeddings=types.SimpleNamespace(inner="paid model"))
    svc.deps.chain = chain
    return chain


def replay(test, out, max_calls=100, aa=0):
    return rc.replay(svc, test, out, max_calls, aa=aa, sleep_s=0, log=lambda _: None)


def full(inp, cell):
    return {cell: {**record(inp), "id": rc.set_id(inp), "cell": cell}}


INP = make_input("squat", faulty("partial_squat", 8), medical="knee surgery", name="Private Name")
ONE = full(INP, "squat/partial_squat/persistent")

# The RAG side sends the model exactly what POST /feedback sends it.
chain = setup()
response = TestClient(svc.app).post("/feedback", json=INP)
check("the endpoint answers", response.status_code, 200)
sent_by_service = chain.calls[0]
with tempfile.TemporaryDirectory() as tmp:
    out = os.path.join(tmp, "r.json")
    chain = setup()
    run, calls = replay(ONE, out)
    by_context = {c["context"]: c["payload"] for c in chain.calls}
    check("two calls for two sides", calls, 2)
    check("RAG side = the service's call", {"context": CONTEXT, "payload": by_context[CONTEXT]}, sent_by_service)
    check("no-RAG side: the same payload", by_context[rc.NO_RAG_CONTEXT], sent_by_service["payload"])
    check("the same text as earlier no-RAG runs", rc.NO_RAG_CONTEXT, "No external context provided.")
    check("the answer stored is not used", "old answer" in json.dumps(run), False)
    check("the name stays out of the output", "Private Name" in open(out, encoding="utf-8").read(), False)
    check("the model's medical history is in the payload", run["sessions"][0]["payload"]["profile"], {"medical_history": "knee surgery"})

    # A rerun pays for nothing and rewrites nothing.
    before = open(out, encoding="utf-8").read()
    chain = setup(["must not be used"])
    run, calls = replay(ONE, out)
    check("rerun: no call", (calls, len(chain.calls)), (0, 0))
    check("rerun: same file", open(out, encoding="utf-8").read(), before)

    # judge_pairwise.py reads it.
    loaded, sessions = judge_pairwise.load_run(out, "rag")
    pairs, skipped = judge_pairwise.make_pairs(loaded, sessions, "rag", loaded, sessions, "no_rag", 1, "none")
    check("judge_pairwise makes one pair", (len(pairs), skipped), (1, []))

with tempfile.TemporaryDirectory() as tmp:
    # A failed call: logged, no answer written, the next run fills only that one.
    out = os.path.join(tmp, "r.json")
    chain = setup([RuntimeError("boom"), "only answer"])
    run, calls = replay(ONE, out)
    session = run["sessions"][0]
    check("one side answered, the failure logged", (calls, len(run["failures"]), len(session["rag"]) + len(session["no_rag"])), (2, 1, 1))
    kept = session["rag"] + session["no_rag"]
    chain = setup(["second try"])
    run, calls = replay(ONE, out)
    session = run["sessions"][0]
    check("the rerun makes one call", calls, 1)
    check("the answer that succeeded is kept", set(kept) <= set(session["rag"] + session["no_rag"]), True)
    check("each side has one sample", (len(session["rag"]), len(session["no_rag"])), (1, 1))

with tempfile.TemporaryDirectory() as tmp:
    # --max-calls is a ceiling and failures count; three failures in a row stop the run.
    out = os.path.join(tmp, "r.json")
    many = {**full(INP, "squat/partial_squat/persistent"),
            **full(make_input("lunge", faulty("shallow_lunge", 8)), "lunge/shallow_lunge/persistent")}
    chain = setup()
    _, calls = replay(many, out, max_calls=3)
    check("stops at the ceiling", (calls, len(chain.calls)), (3, 3))
with tempfile.TemporaryDirectory() as tmp:
    out = os.path.join(tmp, "r.json")
    chain = setup([RuntimeError("down")] * 10)
    _, calls = replay(many, out)
    check("stops after 3 failures in a row", calls, 3)
with tempfile.TemporaryDirectory() as tmp:
    # A run has one setup.
    out = os.path.join(tmp, "r.json")
    setup()
    replay(ONE, out)
    with open(out, encoding="utf-8") as f:
        data = json.load(f)
    data["system_prompt_sha1"] = "another prompt"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f)
    try:
        replay(ONE, out)
        check("another prompt refuses the file", "went on", "SystemExit")
    except SystemExit as e:
        check("another prompt refuses the file", "system_prompt_sha1" in str(e), True)

# --- A/A -------------------------------------------------------------------------------------
cells = {}
for exercise, rules in rc.ERROR_TAXONOMY.items():
    for rule in rules:
        cells.update(full(make_input(exercise, faulty(rule, 8)), f"{exercise}/{rule}/persistent"))
    cells.update(full(make_input(exercise, clean, name=exercise), f"{exercise}/clean"))
sides = rc.choose_aa(cells, 8)
check("8 redraws", len(sides), 8)
check("half each side", sorted(sides.values()), ["no_rag"] * 4 + ["rag"] * 4)
check("no clean session", any(c.endswith("/clean") for c in sides), False)
check("fixed by the seed", rc.choose_aa(cells, 8), sides)
with tempfile.TemporaryDirectory() as tmp:
    out = os.path.join(tmp, "r.json")
    chain = setup()
    run, calls = replay(cells, out, aa=8)
    check("16 sessions x 2 + 8 redraws", calls, 16 * 2 + 8)
    check("redraws stay out of the samples", all(len(s["rag"]) == len(s["no_rag"]) == 1 for s in run["sessions"]), True)
    check("every redraw stored", sorted(s["aa"]["side"] for s in run["sessions"] if s.get("aa")), sorted(sides.values()))
    check("nothing missing", rc.missing_answers(run, sides), [])

# --- no paid embedding, no LLM in check-context and estimate ---------------------------------
inner_holder = types.SimpleNamespace(embeddings=types.SimpleNamespace(inner="paid model"))
svc.deps.vectorstore = lambda: inner_holder
rc.open_store(svc)
try:
    inner_holder.embeddings.inner.embed_query("a query")
    check("a missing query stops", "went on", "RuntimeError")
except RuntimeError as e:
    check("a missing query stops", "fill_query_cache" in str(e), True)

chain = setup()
same_test = full(INP, "squat/partial_squat/persistent")
check("check-context: differs from the capture", rc.check_context(svc, same_test), (0, ["squat/partial_squat/persistent"]))
same_test["squat/partial_squat/persistent"]["context"] = CONTEXT
check("check-context: same", rc.check_context(svc, same_test), (1, []))
check("check-context calls no LLM", chain.calls, [])

est = rc.estimate(ONE, 0, 4000, 0)
check("estimate: calls", est["calls"], 2)
check("estimate: empty", rc.estimate({}, 8, 4000, 0)["calls"], 0)
check("estimate: redraws stop at the fault sessions", rc.estimate(ONE, 8, 4000, 0)["calls"], 3)

# --- the collectors' page: the rows on the sheet, no command line -----------------------------
rows = rc.row_numbers()
check("sheet: 36 rows", sorted(rows.values()), list(range(1, rc.CELLS_WANTED + 1)))
check("sheet: rows the page numbers",
      [rows[c] for c in ("squat/partial_squat/persistent", "squat/partial_squat/sporadic", "squat/mixed", "squat/medical",
                         "squat/clean", "push-up/hip_sag_or_pike/persistent", "push-up/hip_sag_or_pike/sporadic",
                         "lunge/shallow_lunge/persistent", "lunge/straight_back_leg/sporadic",
                         "bicep-curl/elbow_flare/persistent", "bicep-curl/clean")],
      [1, 5, 9, 10, 11, 12, 14, 19, 26, 30, 36])

on_file = rc.sets_on_file([record(make_input("squat", faulty("knee_valgus", 8)), at="2026-11-07T00:00:00Z"),
                           record(make_input("squat", faulty("knee_valgus", 9)), at="2026-11-07T00:01:00Z"),
                           record(make_input("squat", faulty("knee_valgus", 5)), at="2026-11-07T00:02:00Z"),
                           record(make_input("squat", faulty("knee_valgus", 8)), at="2026-11-02T00:00:00Z")])
check("page: newest first, old sets left out", [i["at"][-9:-4] for i in on_file], ["00:02", "00:01", "00:00"])
check("page: a row, a repeat, a reason", [(i["row"], i["repeat"], i["reason"]) for i in on_file],
      [(None, False, "between_patterns"), (2, True, None), (2, False, None)])

page = TestClient(svc.app)
svc.CAPTURE_PATH = None
check("page: says when nothing is being captured", "FEEDBACK_CAPTURE" in page.get("/coverage").text, True)
check("download: nothing to send", page.get("/capture.jsonl").status_code, 404)
with tempfile.TemporaryDirectory() as tmp:
    svc.CAPTURE_PATH = os.path.join(tmp, "c.jsonl")
    check("page: no file yet", page.get("/coverage").status_code, 200)
    with open(svc.CAPTURE_PATH, "w", encoding="utf-8") as f:
        for r in (record(make_input("squat", faulty("knee_valgus", 8), medical="Private text", name="Secret Name")),
                  record(make_input("squat", faulty("knee_varus", 5)), at="2026-11-07T00:01:00Z")):
            f.write(json.dumps(r) + "\n")
    html_page = page.get("/coverage").text
    check("page: the row of a set", "แถว #10" in html_page, True)
    check("page: why a set does not count", "สัดส่วนท่าผิด" in html_page, True)
    check("page: 1 of 36", "1/36" in html_page, True)
    check("page: links to the shared sheet", "claude.ai/artifact/" in html_page, True)
    check("page: no profile, no answer", any(s in html_page for s in ("Private text", "Secret Name", "old answer")), False)
    download = page.get("/capture.jsonl")
    check("download: the file", download.text.count("\n"), 2)
    check("download: a name of its own", "capture.jsonl" in download.headers["content-disposition"], True)
    download.close()
svc.CAPTURE_PATH = None

print("all passed" if not failed else f"{failed} failure(s)")
sys.exit(1 if failed else 0)
