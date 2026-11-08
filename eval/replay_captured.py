"""Replay the sets captured from the app (FEEDBACK_CAPTURE) into RAG and no-RAG answers for the
pairwise eval, through the service's own code. docs/plans/pairwise_eval_v2_plan.md section 7.

The answers the app stored are not used: both sides are written here, after the answer key is
committed, with one prompt, one model and one KB, so the sides differ only in the context. The
RAG side goes through the same payload adapter, retrieval and service._generate() as POST
/feedback (tests/test_replay_captured.py holds them equal). The no-RAG side changes the context
and nothing else.

    python eval/replay_captured.py coverage        # the 36 cells so far: no database, no API
    python eval/replay_captured.py check-context   # retrieval against the capture: database, no API
    python eval/replay_captured.py estimate        # calls and rough tokens: no database, no API
    python eval/replay_captured.py run --llm gemini:gemini-3.6-flash --max-calls 80   # PAID

One sample per side: the first answer that succeeds is the answer. A rerun fills only what is
missing (a failed call or a stopped run) and never rewrites an answer. `run` makes no embedding
call: a query missing from .cache/query_vectors/ stops it (tools/fill_query_cache.py, also paid).

The output goes in capture/ because the payloads hold the medical history: capture/ is gitignored.
It has the keys eval/judge_pairwise.py reads. The redraws for the A/A check are in each session's
`aa`, apart from `rag` and `no_rag`.
"""
import argparse
import glob
import hashlib
import json
import os
import random
import statistics
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from error_taxonomy import ERROR_TAXONOMY  # noqa: E402
from rag_core.app_input import overall_score  # noqa: E402

DEFAULT_CAPTURES = os.path.join(ROOT, "capture", "*.jsonl")
DEFAULT_OUT = os.path.join(ROOT, "capture", "replay_test.json")
# The 7 sets captured on 2026-11-02 were read while writing prompt v15 and v16: not test data.
DEFAULT_SINCE = "2026-11-06T00:00:00Z"
TARGET_REPS, TARGET_SETS = 10, 1
PERSISTENT_MIN = 0.7  # the fault on at least this share of the attempts
SPORADIC_MIN, SPORADIC_MAX = 0.2, 0.4
STRAY_MAX = 1  # other rules on more attempts than this make the set a mixed one
NO_RAG_CONTEXT = "No external context provided."  # the same text as every earlier no-RAG run
AA_DEFAULT = 8
SEED = 6613
SLEEP_S = 15  # between calls, as the batch scripts do
MAX_FAILURES_IN_A_ROW = 3
CELLS_WANTED = sum(2 * len(rules) + 3 for rules in ERROR_TAXONOMY.values())


# --- which cell of the test set a captured set fills -------------------------------------

def set_id(inp):
    """The same set captured twice (Retry in the app) has the same id. The input carries no set
    id, and similarity is left out because a retry may have scored it since."""
    s = inp["set"]
    attempts = [{k: v for k, v in a.items() if k != "similarity"} for a in s.get("attempts") or []]
    key = [inp["exercise"]["id"], (inp.get("profile") or {}).get("display_name"), s.get("set_no"), s.get("kind"),
           s.get("ended_by"), attempts]
    return hashlib.sha1(json.dumps(key, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


def has_medical_history(inp):
    text = ((inp.get("profile") or {}).get("medical_history") or "").strip().rstrip(".").lower()
    return text not in ("", "none")


def rule_counts(set_):
    """rule -> attempts it fired on. A rule recorded twice on one attempt counts once."""
    counts = Counter()
    for attempt in set_.get("attempts") or []:
        counts.update({v["rule"] for v in attempt.get("violations") or []})
    return counts


def classify(inp):
    """(cell, None) for a set the test can use, (None, reason) for one it cannot."""
    exercise = inp["exercise"]["id"]
    rules = ERROR_TAXONOMY.get(exercise)
    if rules is None:
        return None, "unknown_exercise"
    set_, workout = inp["set"], inp.get("workout") or {}
    if set_.get("kind") != "initial":
        return None, "repair_set"
    if workout.get("target_reps") != TARGET_REPS or workout.get("target_sets") != TARGET_SETS:
        return None, f"target_not_{TARGET_REPS}x{TARGET_SETS}"
    if overall_score(set_.get("similarity")) is None:
        return None, "no_similarity"
    if set_["similarity"].get("model") == "stub":  # SIMILARITY_URL unset: believable numbers, no motion read
        return None, "stub_similarity"
    counts = rule_counts(set_)
    if any(rule not in rules for rule in counts):
        return None, "unknown_rule"
    if not counts:
        if has_medical_history(inp):
            return None, "medical_without_fault"
        return f"{exercise}/clean", None
    if has_medical_history(inp):
        return f"{exercise}/medical", None
    main = min(counts, key=lambda r: (-counts[r], r))
    attempts = set_["attempts"]
    others = sum(1 for a in attempts if {v["rule"] for v in a.get("violations") or []} - {main})
    if others > STRAY_MAX:
        return f"{exercise}/mixed", None
    share = counts[main] / len(attempts)
    if share >= PERSISTENT_MIN:
        return f"{exercise}/{main}/persistent", None
    if SPORADIC_MIN <= share <= SPORADIC_MAX:
        return f"{exercise}/{main}/sporadic", None
    return None, "between_patterns"


def read_captures(paths):
    """Each set once, oldest first, keeping its latest capture that has similarity. Returns
    (records, lines read, lines that did not parse)."""
    by_id, lines, bad = {}, 0, 0
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                lines += 1
                try:
                    record = json.loads(line)
                    sid = set_id(record["input"])
                except (ValueError, KeyError, TypeError):
                    bad += 1
                    continue
                old = by_id.get(sid)
                keep_old = old is not None and overall_score(old["input"]["set"].get("similarity")) is not None \
                    and overall_score(record["input"]["set"].get("similarity")) is None
                if not keep_old:
                    by_id[sid] = {**record, "id": sid, "captured_at": (old or record)["captured_at"]}
    return sorted(by_id.values(), key=lambda r: (r["captured_at"], r["id"])), lines, bad


def build_test_set(records, since=DEFAULT_SINCE):
    """Fixed before anyone reads an answer: the first set captured in a cell is its test set,
    a later one in that cell is surplus (available to dev). Returns (test, surplus, reasons)."""
    test, surplus, reasons = {}, [], Counter()
    for record in records:
        if record["captured_at"] < since:
            reasons["before_since"] += 1
            continue
        cell, reason = classify(record["input"])
        if cell is None:
            reasons[reason] += 1
        elif cell in test:
            surplus.append({**record, "cell": cell})
        else:
            test[cell] = {**record, "cell": cell}
    return test, surplus, reasons


def row_numbers():
    """cell -> its row on the 36-set sheet (docs/plans/data_collection_36_sets.md section 5): in
    each exercise the persistent rows, the sporadic rows, then mixed, medical and clean."""
    cells = []
    for exercise, rules in ERROR_TAXONOMY.items():
        cells += [f"{exercise}/{rule}/persistent" for rule in rules]
        cells += [f"{exercise}/{rule}/sporadic" for rule in rules]
        cells += [f"{exercise}/{kind}" for kind in ("mixed", "medical", "clean")]
    return {cell: n for n, cell in enumerate(cells, 1)}


def sets_on_file(records, since=DEFAULT_SINCE):
    """Each set from `since`, newest first: which row it fills, whether that row already had a
    set in these records, or why it does not count."""
    rows, seen, out = row_numbers(), set(), []
    for record in records:
        if record["captured_at"] < since:
            continue
        cell, reason = classify(record["input"])
        out.append({"at": record["captured_at"], "exercise": record["input"]["exercise"]["id"], "cell": cell,
                    "row": rows.get(cell), "repeat": cell in seen, "reason": reason})
        if cell:
            seen.add(cell)
    return out[::-1]


# --- coverage --------------------------------------------------------------------------

def coverage_report(records, lines, bad, since=DEFAULT_SINCE):
    test, surplus, reasons = build_test_set(records, since)
    extra = Counter(r["cell"] for r in surplus)

    def box(cell):
        have = 1 if cell in test else 0
        return f"{have}" + (f" +{extra[cell]}" if extra[cell] else "")

    out = [f"{len(test)}/{CELLS_WANTED} cells filled · {len(records)} distinct sets from {lines} captured requests"
           f" · counted from {since}", "", f"{'rule':<46}{'persistent':<12}sporadic"]
    for exercise, rules in ERROR_TAXONOMY.items():
        for rule in rules:
            out.append(f"{exercise + '/' + rule:<46}{box(f'{exercise}/{rule}/persistent'):<12}"
                       f"{box(f'{exercise}/{rule}/sporadic')}")
    out += ["", f"{'exercise':<46}{'mixed':<12}{'medical':<12}clean"]
    for exercise in ERROR_TAXONOMY:
        out.append(f"{exercise:<46}{box(f'{exercise}/mixed'):<12}{box(f'{exercise}/medical'):<12}"
                   f"{box(f'{exercise}/clean')}")
    chosen = list(test.values())
    people = {(r["input"].get("profile") or {}).get("display_name") for r in chosen}
    repairs = [r for r in records if r["input"]["set"].get("kind") == "repair" and r["captured_at"] >= since]
    out += ["", "Across the test set so far:",
            f"  first workout of the exercise: {sum(not r['input'].get('history') for r in chosen)}"
            f" · with a past workout: {sum(bool(r['input'].get('history')) for r in chosen)}",
            f"  ended by the user: {sum(r['input']['set'].get('ended_by') == 'user_ended' for r in chosen)} (want 4+)",
            f"  people: {len(people)} (want 2-3)",
            f"  repair sets that still had a fault, reported apart: "
            f"{sum(bool(rule_counts(r['input']['set'])) for r in repairs)} (want 2-4)"]
    if reasons or bad:
        out += ["", "Not counted:"] + [f"  {reason}: {n}" for reason, n in sorted(reasons.items())]
        if bad:
            out.append(f"  lines that did not parse: {bad}")
    return "\n".join(out)


# --- the service's code ----------------------------------------------------------------

def load_service():
    """Imported only by the commands that need it. Nothing here calls POST /feedback, so its
    capture file stays out of it."""
    from service import app as svc
    return svc


class RefuseEmbedding:
    """Stands in for the embedding model behind the query cache: no paid call from this script."""

    def embed_query(self, text):
        raise RuntimeError(f"query not in the cache, run tools/fill_query_cache.py (paid): {text[:80]}")


def open_store(svc):
    store = svc.deps.vectorstore()
    embeddings = getattr(store, "embeddings", None)
    if hasattr(embeddings, "inner"):
        embeddings.inner = RefuseEmbedding()
    return store


def payload_of(svc, record):
    """As POST /feedback does: the contract's parsing, then the adapter."""
    return svc.payload_from_feedback_input(svc.FeedbackInput.model_validate(record["input"]).model_dump())


def retrieve(svc, store, payload):
    errors = svc.rule_names(payload)
    exercise = payload["exercise"]
    context, _ = svc.retrieve_kb_context(store, exercise["id"], exercise["name"], errors, cfg=svc.DEFAULT_CONFIG)
    return context


def generate(svc, context, payload):
    """As POST /feedback does: the model's JSON, then the text the app would store."""
    return svc._render(svc._generate(context, payload, time.monotonic() + svc.TIMEOUT_S), payload)


# --- commands that make no LLM call ----------------------------------------------------

def check_context(svc, test):
    """Retrieval again, compared with what the capture recorded. A difference means the KB, the
    gate or the taxonomy changed since the set was captured: not an error, but the replay then
    uses today's context, not that one."""
    store = open_store(svc)
    same, different = 0, []
    for cell, record in sorted(test.items()):
        context = retrieve(svc, store, payload_of(svc, record))
        if context == record.get("context"):
            same += 1
        else:
            different.append(cell)
    return same, different


def rough_tokens(text_chars):
    return text_chars // 4


def estimate(test, aa, system_prompt_chars, human_template_chars):
    """Calls and rough input tokens (4 characters a token). Output comes from the captured answers
    and leaves out the model's thinking tokens, so read it as a lower bound for pricing."""
    records = list(test.values())
    calls = 2 * len(records) + min(aa, sum(not r["cell"].endswith("/clean") for r in records))
    if not records:
        return {"sessions": 0, "calls": 0, "input_tokens": 0, "output_tokens": 0}
    fixed = system_prompt_chars + human_template_chars
    payload = [len(json.dumps(r["payload"], indent=2)) for r in records]
    context = [len(r.get("context") or "") for r in records]
    answers = [len(r.get("feedback") or "") for r in records if r.get("feedback")]
    both_sides = sum(2 * (fixed + p) + c + len(NO_RAG_CONTEXT) for p, c in zip(payload, context))
    per_call = both_sides / (2 * len(records))
    return {"sessions": len(records), "calls": calls, "input_tokens": rough_tokens(int(per_call * calls)),
            "output_tokens": rough_tokens(int(statistics.mean(answers) * calls)) if answers else None}


# --- run -------------------------------------------------------------------------------

def choose_aa(test, n, seed=SEED):
    """{cell: side} for the redraws: fault sessions only, half on each side, fixed by the seed."""
    cells = sorted(c for c in test if not c.endswith("/clean"))
    random.Random(f"{seed}|aa").shuffle(cells)
    return {cell: ("rag" if i % 2 == 0 else "no_rag") for i, cell in enumerate(cells[:n])}


def _save(run, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(run, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _new_run(svc, aa, seed):
    from rag_core.generate import LLM_TEMPERATURE  # the default svc.deps.chain leaves in place
    return {"llm": svc.VERSION["llm"], "temperature": LLM_TEMPERATURE,
            "retrieval": svc.VERSION["collection"], "version": svc.VERSION, "system_prompt_sha1":
            hashlib.sha1(svc.APP_SYSTEM_PROMPT.encode("utf-8")).hexdigest(), "seed": seed, "aa": aa,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sessions": [], "failures": []}


def _load_or_new(svc, out, aa, seed):
    if not os.path.exists(out):
        return _new_run(svc, aa, seed)
    with open(out, encoding="utf-8") as f:
        run = json.load(f)
    fresh = _new_run(svc, aa, seed)
    for key in ("version", "system_prompt_sha1", "seed", "aa"):
        if run.get(key) != fresh[key]:
            raise SystemExit(f"{out} was written with another {key}: {run.get(key)} now {fresh[key]}. "
                             "A run has one setup: pick a new --out.")
    return run


def replay(svc, test, out, max_calls, aa=AA_DEFAULT, seed=SEED, sleep_s=SLEEP_S, log=print):
    """Fills every missing answer, at most `max_calls` LLM calls this time, failed ones included.
    Returns (run, calls made). Saved after every answer, so stopping loses nothing."""
    run = _load_or_new(svc, out, aa, seed)
    sessions = {s["label"]: s for s in run["sessions"]}
    aa_sides = choose_aa(test, aa, seed)
    store = open_store(svc)
    calls = failures_in_a_row = 0

    def one_call(cell, side, context, payload):
        nonlocal calls, failures_in_a_row
        if calls and sleep_s:
            time.sleep(sleep_s)
        calls += 1
        try:
            text = generate(svc, context, payload)
        except svc.ServiceError as e:
            failures_in_a_row += 1
            run["failures"].append({"label": cell, "side": side, "status": e.status, "error": e.message,
                                    "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            log(f"  failed {cell} {side}: {e.status} {e.message}")
            return None
        failures_in_a_row = 0
        return text

    for cell, record in sorted(test.items()):
        session = sessions.get(cell)
        payload = payload_of(svc, record)
        if session is None:
            session = {"label": cell, "exercise_id": payload["exercise"]["id"], "capture_id": record["id"],
                       "payload": payload, "context": retrieve(svc, store, payload), "rag": [], "no_rag": []}
            sessions[cell] = session
            run["sessions"].append(session)
            _save(run, out)
        elif session["capture_id"] != record["id"]:
            raise SystemExit(f"{cell}: {out} has set {session['capture_id']}, the capture now gives {record['id']}")
        # Which side goes first is drawn per session, so a model that drifts during the run
        # does not lean on one side.
        order = ["rag", "no_rag"]
        random.Random(f"{seed}|{cell}|order").shuffle(order)
        for side in order:
            if session[side]:
                continue
            if calls >= max_calls:
                log(f"stopped at --max-calls {max_calls}")
                return run, calls
            context = session["context"] if side == "rag" else NO_RAG_CONTEXT
            text = one_call(cell, side, context, payload)
            if text is not None:
                session[side] = [text]
            _save(run, out)
            if failures_in_a_row >= MAX_FAILURES_IN_A_ROW:
                log(f"stopped after {MAX_FAILURES_IN_A_ROW} failures in a row")
                return run, calls
        side = aa_sides.get(cell)
        if side and not session.get("aa") and session[side]:
            if calls >= max_calls:
                log(f"stopped at --max-calls {max_calls}")
                return run, calls
            context = session["context"] if side == "rag" else NO_RAG_CONTEXT
            text = one_call(cell, side, context, payload)
            if text is not None:
                session["aa"] = {"side": side, "text": text}
            _save(run, out)
            if failures_in_a_row >= MAX_FAILURES_IN_A_ROW:
                log(f"stopped after {MAX_FAILURES_IN_A_ROW} failures in a row")
                return run, calls
    return run, calls


def missing_answers(run, aa_sides):
    sessions = {s["label"]: s for s in run["sessions"]}
    return [s["label"] for s in run["sessions"] if not s["rag"] or not s["no_rag"]] + \
           [cell for cell in aa_sides if not (sessions.get(cell) or {}).get("aa")]


# --- command line ----------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["coverage", "check-context", "estimate", "run"])
    ap.add_argument("--capture", nargs="+", help=f"capture files (default {DEFAULT_CAPTURES})")
    ap.add_argument("--since", default=DEFAULT_SINCE, help=f"count sets captured from this time (default {DEFAULT_SINCE})")
    ap.add_argument("--aa", type=int, default=AA_DEFAULT, help=f"sessions redrawn for the A/A check (default {AA_DEFAULT})")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--llm", help="run: what the service is set to, e.g. gemini:gemini-3.6-flash, or it stops")
    ap.add_argument("--max-calls", type=int, help="run: the most LLM calls to pay for this time (required)")
    ap.add_argument("--sleep", type=float, default=SLEEP_S)
    ap.add_argument("--allow-incomplete", action="store_true", help="run: with cells still empty (a trial, not the test)")
    ap.add_argument("--allow-dirty", action="store_true", help="run: with uncommitted changes (a trial, not the test)")
    args = ap.parse_args()

    paths = args.capture or sorted(glob.glob(DEFAULT_CAPTURES))
    if not paths:
        raise SystemExit(f"no capture file at {DEFAULT_CAPTURES}: is FEEDBACK_CAPTURE set in .env?")
    records, lines, bad = read_captures(paths)

    if args.command == "coverage":
        print(coverage_report(records, lines, bad, args.since))
        return
    test, _, _ = build_test_set(records, args.since)

    if args.command == "estimate":
        from rag_core.prompt import APP_SYSTEM_PROMPT, HUMAN_TEMPLATE
        print(json.dumps(estimate(test, args.aa, len(APP_SYSTEM_PROMPT), len(HUMAN_TEMPLATE)), indent=2))
        print("Rough: 4 characters a token, output without thinking tokens. Filled cells only.")
        return

    svc = load_service()
    if args.command == "check-context":
        same, different = check_context(svc, test)
        print(f"{same} sets retrieve the context their capture holds, {len(different)} do not")
        for cell in different:
            print(f"  {cell}")
        return

    if args.max_calls is None or args.llm is None:
        raise SystemExit("run makes paid calls: give --llm and --max-calls (see `estimate`)")
    if args.llm != svc.VERSION["llm"]:
        raise SystemExit(f"--llm {args.llm} but the service is set to {svc.VERSION['llm']}")
    if len(test) < CELLS_WANTED and not args.allow_incomplete:
        raise SystemExit(f"{len(test)}/{CELLS_WANTED} cells filled: see `coverage`, or --allow-incomplete for a trial")
    if svc.VERSION["commit"].endswith("-dirty") and not args.allow_dirty:
        raise SystemExit(f"uncommitted changes ({svc.VERSION['commit']}): commit first so the answers can be traced")
    run, calls = replay(svc, test, args.out, args.max_calls, args.aa, args.seed, args.sleep)
    left = missing_answers(run, choose_aa(test, args.aa, args.seed))
    print(f"{calls} calls this time, {len(run['failures'])} failed so far, {len(left)} answers still missing -> {args.out}")


if __name__ == "__main__":
    main()
