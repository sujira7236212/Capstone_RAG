"""Checklist judge (eval/judge_checklist.py): prompt, reply validation, retry, cache, summary.
Offline: a fake client stands in for the judge.

    python tests/test_judge_checklist.py
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "eval"))

import build_answer_key as bak  # noqa: E402
import judge_checklist as jc  # noqa: E402

FAILED = []
jc.time.sleep = lambda s: None  # no waiting on retries


def check(name, got, want):
    if got != want:
        FAILED.append(name)
        print(f"FAIL  {name}: {got!r}, wanted {want!r}")


def attempt(no, rules=()):
    return {"attempt_no": no, "outcome": "incorrect" if rules else "correct", "similarity": {"score": 80.0},
            "violations": [{"rule": r} for r in rules]}


def payload(rules_per_attempt):
    attempts = [attempt(i + 1, r) for i, r in enumerate(rules_per_attempt)]
    return {"exercise": {"id": "bicep-curl", "name": "Bicep curl"},
            "workout": {"target_reps": 10, "target_sets": 1, "earlier_sets": []},
            "set": {"set_no": 1, "kind": "initial", "ended_by": "target_reached",
                    "totals": {"attempts": len(attempts), "completed_reps": len(attempts),
                               "correct_reps": sum(not r for r in rules_per_attempt), "abandoned_attempts": 0},
                    "similarity": {"mean_score": 82.0}, "attempts": attempts}}


ANSWER = ("Fault elbow_flare: Your elbow drifted forward.\nFix: Pin your upper arm to your ribs.\n"
          "Fault partial_curl: You stopped short of a straight arm.\nFix: Straighten the arm fully.\n\n"
          "Details elbow_flare:\nLikely cause: A weight too heavy for the biceps alone.\n"
          "Drill: Wall curls, 3 sets of 10.\nCheck: Your upper arm stays vertical in the mirror.\n")
FAULT_PAYLOAD = payload([["elbow_flare"], [], ["partial_curl"], [], ["elbow_flare", "partial_curl"]] + [[]] * 5)
CLEAN_PAYLOAD = payload([[]] * 10)
CHECKLIST = jc.load_checklist()
KEY = bak.build(forbidden_path=os.path.join(tempfile.gettempdir(), "no_forbidden_advice.json"))
UNIT = {"unit": "s1|rag", "label": "s1", "side": "rag", "payload": FAULT_PAYLOAD, "text": ANSWER}
QUOTE = "Your elbow drifted forward."


def good_reply(items, faults, flip=None):
    """A well-formed reply: 'yes' everywhere (or `flip` items 'no'), quotes where needed."""
    rows = []
    for i in items:
        ans = "no" if flip and i["id"] in flip else "yes"
        row = {"id": i["id"], "answer": ans, "evidence": QUOTE if ans == i["evidence_when"] else ""}
        if i.get("per_fault") and faults:
            row["per_fault"] = {f: ans for f in faults}
        rows.append(row)
    return {"items": rows}


class Fake:
    """Answers from a list of reply objects (or strings) in order; records the prompts."""

    def __init__(self, replies):
        self.replies, self.prompts = list(replies), []

    def complete(self, prompt):
        self.prompts.append(prompt)
        r = self.replies.pop(0)
        return r if isinstance(r, str) else json.dumps(r)


# --- the checklist and the items asked
check("20 items", len(CHECKLIST["items"]), 20)
check("5 per criterion", sorted(sum(1 for i in CHECKLIST["items"] if i["criterion"] == c) for c in jc.CRITERIA), [5, 5, 5, 5])
check("ids unique", len({i["id"] for i in CHECKLIST["items"]}), 20)
check("every item has both examples", [i["id"] for i in CHECKLIST["items"] if not (i.get("yes_example") and i.get("no_example"))], [])
check("examples use the shoulder press, outside the system",
      any(w in json.dumps(CHECKLIST["items"]).lower() for w in ("squat", "lunge", "push-up", "curl")), False)
check("clean set: the plan's 5 items", sorted(i["id"] for i in jc.items_for(CHECKLIST, CLEAN_PAYLOAD)), ["A1", "A2", "A3", "A5", "C5"])
check("clean set: A3 asks the clean question",
      next(i for i in jc.items_for(CHECKLIST, CLEAN_PAYLOAD) if i["id"] == "A3")["question"].startswith("On a set with no fault"), True)
check("fault set: all 20", len(jc.items_for(CHECKLIST, FAULT_PAYLOAD)), 20)

# --- the prompt
prompt, items, faults, identity = jc.build_prompt(UNIT, CHECKLIST, KEY)
check("faults of the set", faults, ["elbow_flare", "partial_curl"])
check("prompt: the answer is in it", ANSWER.strip() in prompt, True)
check("prompt: facts are in it", '"facts"' in prompt, True)
check("prompt: blind - no side, no retrieved context", ("rag" in prompt.lower().split(), "[mistake" in prompt), (False, False))
check("prompt: order is seeded by the answer", [i["id"] for i in jc.build_prompt(UNIT, CHECKLIST, KEY)[1]], [i["id"] for i in items])
check("prompt: another answer, another order",
      [i["id"] for i in jc.build_prompt({**UNIT, "text": ANSWER + "x"}, CHECKLIST, KEY)[1]] != [i["id"] for i in items], True)
no_key = jc.build_prompt(UNIT, CHECKLIST, KEY, use_key=False)[0]
check("--no-key: no facts, no rule_key, exercise_faults kept", ('"facts"' in no_key, '"rule_key"' in no_key,
      "exercise_faults" in no_key), (False, False, True))
patched = jc.build_prompt({**UNIT, "key_patch": {"facts": {"target_reached": False}}}, CHECKLIST, KEY)
check("key_patch: the swapped fact is shown", '"target_reached": false' in patched[0], True)
check("key_patch: changes the cache identity", patched[3]["key"] != identity["key"], True)

# --- quotes
check("quote: exact", jc.quote_found(QUOTE, ANSWER), True)
check("quote: case, spacing and curly quotes ignored", jc.quote_found("your   ELBOW drifted forward", ANSWER), True)
check("quote: two joined with |", jc.quote_found("Wall curls, 3 sets of 10 | Pin your upper arm", ANSWER), True)
check("quote: ... skips text", jc.quote_found("Your elbow ... forward", ANSWER), True)
check("quote: not in the answer", jc.quote_found("Do pull-ups instead", ANSWER), False)
check("quote: empty", jc.quote_found("", ANSWER), False)
check("quote: JSON debris around it is dropped", jc.quote_found('"Pin your upper arm",', ANSWER), True)
check("quote: debris only is still empty", jc.quote_found('",', ANSWER), False)
check("quote: two places glued without | are not one quote",
      jc.quote_found("Your elbow drifted forward Wall curls, 3 sets of 10", ANSWER), False)

# --- validation (form only)
records, problems = jc.validate(good_reply(items, faults), items, faults, ANSWER)
check("valid reply", (len(records), problems), (20, []))
r = good_reply(items, faults)
r["items"] = r["items"][:-1]
check("a missing item is a problem", bool(jc.validate(r, items, faults, ANSWER)[1]), True)
r = good_reply(items, faults)
r["items"].append(dict(r["items"][0]))
check("an item answered twice is a problem", any("twice" in p for p in jc.validate(r, items, faults, ANSWER)[1]), True)
r = good_reply(items, faults)
yes_item = next(row for row in r["items"] if next(i for i in items if i["id"] == row["id"])["evidence_when"] == "yes")
yes_item["evidence"] = ""
check("a 'yes' on a there-is item needs a quote", any("needs a quote" in p for p in jc.validate(r, items, faults, ANSWER)[1]), True)
r = good_reply(items, faults, flip={"A1"})
next(row for row in r["items"] if row["id"] == "A1")["evidence"] = "made up words"
check("a 'no' on a nothing-wrong item needs a real quote", any("not in the answer" in p for p in jc.validate(r, items, faults, ANSWER)[1]), True)
r = good_reply(items, faults)
row = next(row for row in r["items"] if "per_fault" in row)
row["per_fault"] = {"elbow_flare": "yes"}
check("per_fault must cover every fault", any("per_fault" in p for p in jc.validate(r, items, faults, ANSWER)[1]), True)
r = good_reply(items, faults)
row = next(row for row in r["items"] if "per_fault" in row)
row["per_fault"]["partial_curl"] = "no"
check("an item's yes must agree with its per_fault", any("disagrees" in p for p in jc.validate(r, items, faults, ANSWER)[1]), True)
r = good_reply(items, faults)
r["items"][0]["answer"] = "maybe"
check("only yes or no", bool(jc.validate(r, items, faults, ANSWER)[1]), True)
r = good_reply(items, faults)
r["items"] += ["", "", {}]
check("empty filler entries are ignored", jc.validate(r, items, faults, ANSWER)[1], [])
r = good_reply(items, faults, flip={next(row["id"] for row in good_reply(items, faults)["items"] if "per_fault" in row)})
row = next(row for row in r["items"] if "per_fault" in row and row["answer"] == "no")
del row["per_fault"]
check("a per_fault item answered no still needs per_fault",
      any("per_fault" in p for p in jc.validate(r, items, faults, ANSWER)[1]), True)
check("the prompt asks per_fault before answer", "fill \"per_fault\" FIRST" in jc.build_prompt(UNIT, CHECKLIST, KEY)[0], True)
check("not a dict with items", jc.validate({"x": [1, 2]}, items, faults, ANSWER)[1], ["no 'items' list"])
check("a bare items list is read as the list", jc.validate(good_reply(items, faults)["items"], items, faults, ANSWER)[1], [])
check("a bare list of junk is still a problem", bool(jc.validate([1, 2], items, faults, ANSWER)[1]), True)
clean_unit = {"unit": "c|rag", "label": "c", "side": "rag", "payload": CLEAN_PAYLOAD, "text": "Keep: Steady reps.\n\nProgress: First set."}
_, c_items, c_faults, _ = jc.build_prompt(clean_unit, CHECKLIST, KEY)
check("clean set: valid without per_fault", jc.validate(good_reply(c_items, c_faults), c_items, c_faults,
      "Keep: Steady reps. Your elbow drifted forward.")[1], [])

# --- one call: retry once, then invalid
fake = Fake([{"items": []}, good_reply(items, faults)])
res = jc.judge_unit(fake, UNIT, CHECKLIST, KEY, log=lambda *a: None)
check("a bad form is asked again once and can pass", (res["valid"], len(fake.prompts)), (True, 2))
fake = Fake(["not json at all", "{\"items\": []}"])
res = jc.judge_unit(fake, UNIT, CHECKLIST, KEY, log=lambda *a: None)
check("still bad after the retry: invalid, no verdicts", (res["valid"], res["items"], len(fake.prompts)), (False, {}, 2))


class Flaky(Fake):
    def complete(self, prompt):
        if not getattr(self, "failed", False):
            self.failed = True
            raise RuntimeError("HTTP 429: rate limit")
        return super().complete(prompt)


res = jc.judge_unit(Flaky([good_reply(items, faults)]), UNIT, CHECKLIST, KEY, log=lambda *a: None)
check("a rate limit is retried, not counted as a format failure", (res["valid"], len(res["tries"])), (True, 1))


class DailyLimit(Fake):
    def complete(self, prompt):
        raise RuntimeError("HTTP 429: Rate limit reached for model x on tokens per day (TPD): Limit 200000")


try:
    jc.judge_unit(DailyLimit([]), UNIT, CHECKLIST, KEY, log=lambda *a: None)
    check("a daily limit stops the run at once", "no stop", "stopped")
except SystemExit as e:
    check("a daily limit stops the run at once", "daily limit" in str(e), True)

# --- run: cache per judge
with tempfile.TemporaryDirectory() as tmp:
    out = os.path.join(tmp, "judge.json")
    units = [UNIT, {**UNIT, "unit": "s1|no_rag", "side": "no_rag", "text": ANSWER + "Next Session Plan:\n1. Rest.\n"}]
    replies = [good_reply(jc.build_prompt(u, CHECKLIST, KEY)[1], faults) for u in units]
    data, calls = jc.run(units, CHECKLIST, KEY, "fake:judge", out, Fake(replies), log=lambda *a: None)
    check("run: one call per answer", (calls, len(data["calls"])), (2, 2))
    data, calls = jc.run(units, CHECKLIST, KEY, "fake:judge", out, Fake([]), log=lambda *a: None)
    check("run again: everything cached, no call", calls, 0)
    try:
        jc.run(units, CHECKLIST, KEY, "fake:other", out, Fake([]), log=lambda *a: None)
        check("another judge in the same file stops", False, True)
    except SystemExit:
        pass
    data, calls = jc.run(units, CHECKLIST, KEY, "fake:judge", os.path.join(tmp, "j2.json"), Fake(replies[:1]),
                         max_calls=1, log=lambda *a: None)
    check("--max-calls stops the run", calls, 1)

# --- split by criterion: one request per criterion, merged; invalid if any part is
replies = [good_reply(jc.build_prompt(UNIT, CHECKLIST, KEY, only=(c,))[1], faults) for c in jc.CRITERIA]
fake = Fake(replies)
res = jc.judge_unit(fake, UNIT, CHECKLIST, KEY, log=lambda *a: None, split="criterion")
check("split: 4 requests, 20 items merged", (len(fake.prompts), len(res["items"]), res["valid"]), (4, 20, True))
check("split: each request asks 5 items", [p.count('"evidence_when": ') for p in fake.prompts], [5, 5, 5, 5])
check("split: part of the cache identity", res["identity"].get("split"), "criterion")
fake = Fake([replies[0], {"items": []}, {"items": []}])
res = jc.judge_unit(fake, UNIT, CHECKLIST, KEY, log=lambda *a: None, split="criterion")
check("split: one part invalid after its retry -> the answer is invalid", (res["valid"], len(fake.prompts)), (False, 3))
c_replies = [good_reply(its, []) for its in (jc.build_prompt(clean_unit, CHECKLIST, KEY, only=(c,))[1] for c in jc.CRITERIA) if its]
fake = Fake(c_replies)
res = jc.judge_unit(fake, {**clean_unit, "text": clean_unit["text"] + " Your elbow drifted forward."}, CHECKLIST, KEY,
                    log=lambda *a: None, split="criterion")
check("split on a clean set: only criteria with items are asked", (len(fake.prompts), sorted(res["items"])),
      (2, ["A1", "A2", "A3", "A5", "C5"]))


class Rejecting(Fake):
    def complete(self, prompt):
        self.prompts.append(prompt)
        raise RuntimeError('HTTP 400: {"error":{"code":"json_validate_failed"}}')


fake = Rejecting([])
res = jc.judge_unit(fake, UNIT, CHECKLIST, KEY, log=lambda *a: None)
check("a JSON-mode rejection is a format failure: asked once more, not 5 times", (res["valid"], len(fake.prompts)), (False, 2))


class TooLarge(Fake):
    def complete(self, prompt):
        raise RuntimeError("HTTP 413: Request too large for model")


try:
    jc.judge_unit(TooLarge([]), UNIT, CHECKLIST, KEY, log=lambda *a: None)
    check("a request the provider can never take stops the run", False, True)
except SystemExit:
    pass

# --- estimate makes no call
est = jc.estimate([UNIT, clean_unit], CHECKLIST, KEY)
check("estimate: requests and tokens", (est["requests"], est["input_tokens"] > 0), (2, True))
est_split = jc.estimate([UNIT, clean_unit], CHECKLIST, KEY, split="criterion")
check("estimate --split: 4 + 2 requests, each smaller", (est_split["requests"],
      est_split["input_per_request"] < est["input_per_request"]), (6, True))

# --- statistics
check("majority 2 of 3", jc.majority(["yes", "no", "yes"]), "yes")
check("two that disagree: dropped", jc.majority(["yes", "no"]), None)
check("one vote", jc.majority(["no"]), "no")
check("no vote", jc.majority([]), None)
check("AC1: full agreement is 1", jc.gwet_ac1([[3, 0], [0, 3], [3, 0]]), 1.0)
check("Fleiss kappa: full agreement is 1", jc.fleiss_kappa([[3, 0], [0, 3]]), 1.0)
check("AC1 stays high when nearly every answer is yes", round(jc.gwet_ac1([[3, 0]] * 9 + [[2, 1]]), 2) > 0.8, True)
check("Holm adjusts and keeps order", jc._holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])

# --- summary over three fake judges
with tempfile.TemporaryDirectory() as tmp:
    sessions, units = [], []
    for k in range(4):
        p = FAULT_PAYLOAD
        for side, text in (("rag", ANSWER + f"#{k}r"), ("no_rag", ANSWER + f"#{k}n")):
            units.append({"unit": f"s{k}|{side}", "label": f"s{k}", "side": side, "payload": p, "text": text})
    files = []
    for j in range(3):
        replies = []
        for u in units:
            its = jc.build_prompt(u, CHECKLIST, KEY)[1]
            flip = {"C2", "D3"} if u["side"] == "no_rag" else set()  # RAG ahead by 2 items of 20
            replies.append(good_reply(its, faults, flip=flip))
        path = os.path.join(tmp, f"j{j}.json")
        jc.run(units, CHECKLIST, KEY, f"fake:j{j}", path, Fake(replies), log=lambda *a: None)
        files.append(path)
    report = jc.summarize(units, files, CHECKLIST)
    check("summary: the main difference", "mean difference: +10.0 points (+2.00 items of 20)" in report, True)
    check("summary: win / loss", "win / loss / tie: 4 / 0 / 0" in report, True)
    check("summary: a pilot is flagged", "too few for a conclusion" in report, True)
    check("summary: per-fault table", "| elbow_flare |" in report, True)
    check("summary: A5 reported", "A5 failed: RAG 0 · no-RAG 0" in report, True)

if FAILED:
    print(f"{len(FAILED)} failed")
    sys.exit(1)
print("all passed")
