"""The judge's answer key (eval/build_answer_key.py): facts from a session, per-rule parts from the
rule cards. Offline, no API.

    python tests/test_build_answer_key.py
"""
import glob
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "eval"))

import build_answer_key as bak  # noqa: E402
from error_taxonomy import ERROR_TAXONOMY  # noqa: E402

FAILED = []


def check(name, got, want):
    if got != want:
        FAILED.append(name)
        print(f"FAIL  {name}: {got!r}, wanted {want!r}")


def attempt(no, outcome="correct", rules=(), score=80.0):
    return {"attempt_no": no, "outcome": outcome, "similarity": None if outcome == "abandoned" else {"score": score},
            "violations": [{"rule": r} for r in rules]}


def payload(attempts, kind="initial", set_no=2, ended_by="user_ended", earlier=None, history=None, score=70.0,
            correct=6, exercise="squat"):
    p = {"exercise": {"id": exercise, "name": exercise.title()},
         "workout": {"target_reps": 10, "target_sets": 2, "earlier_sets": earlier or []},
         "set": {"set_no": set_no, "kind": kind, "ended_by": ended_by,
                 "totals": {"attempts": len(attempts), "completed_reps": len(attempts) - 1, "correct_reps": correct,
                            "abandoned_attempts": 1},
                 "similarity": {"mean_score": score}, "attempts": attempts}}
    if history:
        p["history"] = history
    return p


ATTEMPTS = [attempt(1, "incorrect", ["knee_varus"]), attempt(2), attempt(3, "incorrect", ["knee_varus", "rounded_back"]),
            attempt(4), attempt(5), attempt(6, "abandoned", ["partial_squat"]), attempt(7), attempt(8),
            attempt(9, "incorrect", ["knee_varus"])]
EARLIER = [{"set_no": 1, "kind": "initial", "ended_by": "attempt_cap",
            "totals": {"attempts": 12, "completed_reps": 12, "correct_reps": 4, "abandoned_attempts": 0},
            "similarity": {"mean_score": 65.0}}]

f = bak.facts_for(payload(ATTEMPTS, earlier=EARLIER))
check("faults: attempts per rule", {r: v["attempts"] for r, v in f["faults"].items()},
      {"knee_varus": [1, 3, 9], "rounded_back": [3], "partial_squat": [6]})
check("faults: counts out of every attempt", (f["faults"]["knee_varus"]["count"], f["faults"]["knee_varus"]["of_attempts"]), (3, 9))
# 9 attempts: 1-3 early, 4-6 mid, 7-9 late
check("by_third: numbers, not a description", f["faults"]["knee_varus"]["by_third"], {"early": 2, "mid": 0, "late": 1})
check("abandoned attempts with their rules", f["abandoned_attempts"], [{"attempt_no": 6, "rules": ["partial_squat"]}])
check("target not reached when user_ended", (f["ended_by"], f["target_reached"]), ("user_ended", False))
check("last set", f["set"]["last_set"], True)
check("earlier set compared", f["compare_with"]["earlier_sets"][0]["score_change"], "+5.0")
check("rep count change has no decimal", f["compare_with"]["earlier_sets"][0]["correct_change"], "+2")
check("no history", f["compare_with"]["history"], "none")
check("not the first set on record", "first_set_on_record" in f["compare_with"], False)
check("equipment from the exercise", f["equipment"].startswith("body weight only"), True)
check("fault change is unknown", f["fault_change_vs_before"], bak.FAULT_CHANGE)

not_alike = [dict(EARLIER[0], similarity=None)]
f = bak.facts_for(payload(ATTEMPTS, earlier=not_alike))
check("a past score the adapter nulled is 'not comparable'", f["compare_with"]["earlier_sets"][0]["score"], bak.NOT_COMPARABLE)
check("and has no score change", "score_change" in f["compare_with"]["earlier_sets"][0], False)

repair_earlier = EARLIER + [{"set_no": 2, "kind": "initial", "ended_by": "user_ended",
                             "totals": {"attempts": 9, "completed_reps": 9, "correct_reps": 3, "abandoned_attempts": 0},
                             "similarity": {"mean_score": 60.0}}]
f = bak.facts_for(payload(ATTEMPTS, kind="repair", earlier=repair_earlier))
check("repair: the first try of the same set", f["compare_with"]["first_try_of_this_set"]["correct_reps"], 3)

clean = [attempt(i) for i in range(1, 11)]
f = bak.facts_for(payload(clean, set_no=1, ended_by="target_reached", correct=10))
check("clean set: no faults", f["faults"], "none: a clean set")
check("clean set: target reached", f["target_reached"], True)
check("first set on record", f["compare_with"].get("first_set_on_record"), True)
f = bak.facts_for(payload(clean, set_no=1, history=[{"started_at": "2026-11-03", "sets": [EARLIER[0]]}]))
check("history compared", f["compare_with"]["history"]["sets"][0]["score_change"], "+5.0")

# Per rule, from the cards
check("equipment for every exercise in the taxonomy", sorted(bak.EQUIPMENT), sorted(ERROR_TAXONOMY))
with tempfile.TemporaryDirectory() as tmp:
    key = bak.build(forbidden_path=os.path.join(tmp, "none.json"))
rules = [r for rs in ERROR_TAXONOMY.values() for r in rs]
check("rule_key: every rule", sorted(key["rule_key"]), sorted(rules))
check("rule_key: definition, causes, consequences and correct form filled",
      [r for r, v in key["rule_key"].items() if not all(v[k] for k in ("definition", "causes", "consequences", "correct_form"))], [])
check("forbidden_advice: not written yet means empty lists, said so", (key["forbidden_advice"],
      sum(len(v["forbidden_advice"]) for v in key["rule_key"].values())), ("not written", 0))
check("exercise_faults: every exercise, every rule", {e: sorted(v) for e, v in key["exercise_faults"].items()},
      {e: sorted(r) for e, r in ERROR_TAXONOMY.items()})
session = bak.key_for_session(key, payload(ATTEMPTS))
check("session key: only this set's rules", sorted(session["rule_key"]), ["knee_varus", "partial_squat", "rounded_back"])
check("session key: the exercise's faults", sorted(session["exercise_faults"]), sorted(ERROR_TAXONOMY["squat"]))
check("session key: no clean-set rules", bak.key_for_session(key, payload(clean))["rule_key"], {})

# The generator never sees the key (plan 5.3)
for path in glob.glob(os.path.join(ROOT, "rag_core", "*.py")) + glob.glob(os.path.join(ROOT, "service", "*.py")):
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    for name in ("answer_key", "build_answer_key", "checklist_v1", "forbidden_advice"):
        check(f"{os.path.relpath(path, ROOT)} does not read {name}", name in src, False)

if FAILED:
    print(f"{len(FAILED)} failed")
    sys.exit(1)
print("all passed")
