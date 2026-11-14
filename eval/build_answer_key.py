"""The judge's answer key for the pairwise eval v2 (docs/plans/pairwise_eval_v2_plan.md section 5).

Three parts, none of them read from the KB or from any answer:
  facts           per session, computed from the payload the generator was shown (the app's set
                  data after rag_core.app_input): counts, attempt numbers, scores, what there is to
                  compare with. Code reads data here; it never reads an answer (plan section 4).
  rule_key        per rule, from eval/rule_cards.json (expert-approved cards) plus
                  eval/forbidden_advice_v1.json when it exists (plan 5.3: drafted from the cards
                  only, approved by the expert). Used as "must not contradict", never as a target.
  exercise_faults per exercise, every rule's definition: the judge uses it only for the
                  "would it still be true for another fault of this exercise" test.

facts are built at judging time from each session's payload (eval/judge_checklist.py), so a set
captured later needs no rebuild; this script writes the per-rule parts to eval/answer_key_v1.json
and can print the facts of a replay run for inspection.

    python eval/build_answer_key.py                       # write eval/answer_key_v1.json
    python eval/build_answer_key.py --facts capture/replay_dev_pilot_v19.json   # print facts
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from error_taxonomy import ERROR_TAXONOMY  # noqa: E402

CARDS = os.path.join(ROOT, "eval", "rule_cards.json")
FORBIDDEN = os.path.join(ROOT, "eval", "forbidden_advice_v1.json")
OUT = os.path.join(ROOT, "eval", "answer_key_v1.json")
KEY_VERSION = 1

# The app's scope (the user, 2026-11-08), the same facts as the Equipment paragraph of the app
# prompt. tests/test_build_answer_key.py fails when an exercise in the taxonomy is missing here.
EVERYDAY = "nothing beyond everyday things (a wall, a chair, a step)"
EQUIPMENT = {
    "squat": f"body weight only: no advice to add, reduce or change a load or weight; {EVERYDAY}",
    "push-up": f"body weight only: no advice to add, reduce or change a load or weight; {EVERYDAY}",
    "lunge": f"body weight only: no advice to add, reduce or change a load or weight; {EVERYDAY}",
    "bicep-curl": f"dumbbells; {EVERYDAY}",
}
NOT_COMPARABLE = "not comparable"
FAULT_CHANGE = "unknown: earlier sets and history do not list faults"


# --- facts ---------------------------------------------------------------------------------

def _score(similarity, key):
    """A number, or None when the set was not scored or its score is not comparable (the adapter
    nulls a past score measured with another model or reference)."""
    if not similarity:
        return None
    value = similarity.get(key)
    return round(float(value), 1) if isinstance(value, (int, float)) else None


def _signed(change):
    """+1.6 / -2 / same: a score keeps its decimal, a rep count does not."""
    if not change:
        return "same"
    return f"{change:+d}" if isinstance(change, int) else f"{change:+.1f}"


def _thirds(numbers, n):
    """Where in the set the attempts fall: early / mid / late thirds of the n attempts, by
    position. Numbers, not a description, so judges need not interpret a pattern (review
    2026-11-12 item 3)."""
    out = {"early": 0, "mid": 0, "late": 0}
    for no in numbers:
        out[("early", "mid", "late")[min(2, (no - 1) * 3 // max(n, 1))]] += 1
    return out


def _compared(other, score, correct):
    """An earlier set or a past workout's set, against this set."""
    other_score = _score(other.get("similarity"), "mean_score")
    other_correct = (other.get("totals") or {}).get("correct_reps")
    row = {"set_no": other.get("set_no"), "kind": other.get("kind") or "initial",
           "correct_reps": other_correct,
           "correct_change": _signed(correct - other_correct) if other_correct is not None else "unknown",
           "score": other_score if other_score is not None else NOT_COMPARABLE}
    if other.get("ended_by"):
        row["ended_by"] = other["ended_by"]
    if other_score is not None and score is not None:
        row["score_change"] = _signed(round(score - other_score, 1))
    return row


def facts_for(payload):
    """The session facts the judge takes as true (plan 5.3, judge rule 1)."""
    s = payload["set"]
    workout = payload.get("workout") or {}
    attempts = s.get("attempts") or []
    n = len(attempts)
    totals = s.get("totals") or {}
    correct = totals.get("correct_reps", 0)
    score = _score(s.get("similarity"), "mean_score")
    target_reps, target_sets = workout.get("target_reps"), workout.get("target_sets")

    faults = {}
    for a in attempts:
        for v in a.get("violations") or []:
            faults.setdefault(v["rule"], []).append(a["attempt_no"])
    fault_facts = {rule: {"attempts": sorted(set(nos)), "count": len(set(nos)), "of_attempts": n,
                          "by_third": _thirds(sorted(set(nos)), n)}
                   for rule, nos in faults.items()}
    abandoned = [{"attempt_no": a["attempt_no"], "rules": [v["rule"] for v in a.get("violations") or []]}
                 for a in attempts if a.get("outcome") == "abandoned"]

    ended_by = s.get("ended_by")
    reached = ended_by == "target_reached"
    earlier = [_compared(e, score, correct) for e in workout.get("earlier_sets") or []]
    compare = {"earlier_sets": earlier or "none"}
    if s.get("kind") == "repair":
        first = [e for e in earlier if e["set_no"] == s.get("set_no") and e["kind"] == "initial"]
        compare["first_try_of_this_set"] = first[0] if first else "not in the data"
    history = payload.get("history") or []
    if history:
        past = history[0]
        compare["history"] = {"started_at": past.get("started_at"),
                              "sets": [_compared(p, score, correct) for p in past.get("sets") or []]}
    else:
        compare["history"] = "none"
    if not earlier and not history and s.get("kind") != "repair":
        compare["first_set_on_record"] = True

    return {
        "exercise": payload["exercise"]["id"],
        "equipment": EQUIPMENT.get(payload["exercise"]["id"], "unknown"),
        "set": {"set_no": s.get("set_no"), "kind": s.get("kind") or "initial", "target_reps": target_reps,
                "target_sets": target_sets,
                "last_set": bool(target_sets) and (s.get("set_no") or 0) >= target_sets},
        "faults": fault_facts or "none: a clean set",
        "abandoned_attempts": abandoned or "none",
        "totals": {k: totals.get(k, 0) for k in ("attempts", "completed_reps", "correct_reps", "abandoned_attempts")},
        "score": score if score is not None else "not scored",
        "ended_by": ended_by or "unknown",
        "target_reached": reached,
        "compare_with": compare,
        "fault_change_vs_before": FAULT_CHANGE,
    }


# --- per rule --------------------------------------------------------------------------------

def load_cards(path=CARDS):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["cards"]


def _card_for(cards, rule):
    for card in cards:
        if rule in card.get("rule_names", []):
            return card
    raise KeyError(f"no rule card names {rule}")


def load_forbidden(path=FORBIDDEN):
    """{rule: [advice, ...]} and whether the expert approved it. Missing file = not written yet:
    A5 then rests on its general conditions (no pushing through pain, no added load while the form
    is still wrong, no diagnosis), plan section 9 item 4."""
    if not os.path.exists(path):
        return {}, "not written"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("rules", {}), "approved" if data.get("approved_by") else "draft, not approved"


def rule_key(cards, forbidden=None):
    forbidden = forbidden or {}
    out = {}
    for exercise, rules in ERROR_TAXONOMY.items():
        for rule in rules:
            card = _card_for(cards, rule)
            info = card.get("relevant_info") or {}
            out[rule] = {
                "exercise": exercise,
                "definition": card["definition"]["en"],
                "excludes": [x["en"] for x in card.get("excludes") or []],
                "causes": (info.get("causes") or {}).get("en", ""),
                "consequences": (info.get("consequences") or {}).get("en", ""),
                "correct_form": (info.get("correct_form") or {}).get("en", ""),
                "forbidden_advice": list(forbidden.get(rule, [])),
            }
    return out


def exercise_faults(cards):
    return {exercise: {rule: _card_for(cards, rule)["definition"]["en"] for rule in rules}
            for exercise, rules in ERROR_TAXONOMY.items()}


def build(cards_path=CARDS, forbidden_path=FORBIDDEN):
    cards = load_cards(cards_path)
    forbidden, status = load_forbidden(forbidden_path)
    with open(cards_path, "rb") as f:
        cards_sha = hashlib.sha1(f.read()).hexdigest()
    return {"key_version": KEY_VERSION, "rule_cards_sha1": cards_sha, "forbidden_advice": status,
            "equipment": EQUIPMENT, "rule_key": rule_key(cards, forbidden), "exercise_faults": exercise_faults(cards)}


def key_for_session(key, payload):
    """What one judge call is shown: the facts, the rule_key of this set's rules only, and the
    exercise's fault list."""
    facts = facts_for(payload)
    rules = facts["faults"] if isinstance(facts["faults"], dict) else {}
    return {"facts": facts,
            "rule_key": {r: {k: v for k, v in key["rule_key"][r].items() if k != "exercise"} for r in rules},
            "exercise_faults": key["exercise_faults"].get(facts["exercise"], {})}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--facts", help="a replay run JSON (eval/replay_captured.py): print each session's facts")
    args = ap.parse_args()
    if args.facts:
        with open(args.facts, encoding="utf-8") as f:
            run = json.load(f)
        for s in run["sessions"]:
            print(f"## {s['label']}")
            print(json.dumps(facts_for(s["payload"]), ensure_ascii=False, indent=1))
        return
    key = build()
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(key, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"{args.out}: {len(key['rule_key'])} rules · forbidden_advice {key['forbidden_advice']}")


if __name__ == "__main__":
    main()
