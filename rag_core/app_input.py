"""The app's FeedbackInput -> the JSON the model reads (prompt.APP_SYSTEM_PROMPT, v15a).

FeedbackInput is MU-Capstone-Application's contract (lib/analysis/contracts.ts, ADR-0007);
docs/plans/feedback_input_example.json is an example of it. Since v15a (2026-10-28) the payload
keeps the app's own key names and nesting (exercise, workout, set, totals, attempt_no, outcome,
violations[].rule, similarity.score / mean_score), the same names the similarity service
answers with, instead of the mock sessions' v14 format (summary, reps_detail, status,
error_type). The eval scripts keep v14's format and prompt.

Passed: the exercise, the target per set and the earlier sets of this workout, the set's totals
and overall score, each attempt's number, outcome, overall score and fault keys in priority
order, and the newest past workout's sets. Kept from 2026-10-25 (docs/plans/
app_integration_plan.md D3): the app's own counts, so the feedback cannot contradict what the
user sees on the same screen.

Similarity: only the overall number, as in v14. The app sends the agreed shape (set
mean_score, attempt score); the older `overall` shape is still read. A body part's score says
how far it was from the expert, not in which direction, which a prompt with no rule for it
would guess at.

Not passed to the model at all: the profile (name, age, gender, weight, height, and the medical
history, which waits for v15's rules and the consent wording, D6), the set's kind and how it
ended, the violation's message, state, value and threshold, rep_stats, frames and durations,
and every similarity field beyond the overall score.
"""


def overall_score(similarity):
    """The one overall number of either similarity shape, None when there is none."""
    if not similarity:
        return None
    for key in ("mean_score", "score", "overall"):
        if similarity.get(key) is not None:
            return similarity[key]
    return None


def _similarity(similarity, key):
    score = overall_score(similarity)
    return None if score is None else {key: score}


def _totals(totals):
    return {k: totals.get(k, 0) for k in ("attempts", "completed_reps", "correct_reps", "abandoned_attempts")}


def _attempt(attempt):
    violations = sorted(attempt.get("violations") or [], key=lambda v: v.get("priority", 99))
    return {
        "attempt_no": attempt["attempt_no"],
        "outcome": attempt["outcome"],
        "similarity": _similarity(attempt.get("similarity"), "score"),
        "violations": [{"rule": v["rule"]} for v in violations],
    }


def _set(set_summary):
    return {
        "set_no": set_summary["set_no"],
        "totals": _totals(set_summary["totals"]),
        "similarity": _similarity(set_summary.get("similarity"), "mean_score"),
    }


def _past_workout(workout):
    """The newest past workout. Its sets carry no violations (SetSummary), so the model is told
    not to compare faults with it. The app does not order them, so they are sorted here."""
    return {
        "started_at": workout["started_at"][:10],
        "sets": [_set(s) for s in sorted(workout.get("sets") or [], key=lambda s: s["set_no"])],
    }


def payload_from_feedback_input(inp):
    """FeedbackInput (a dict parsed from the app's JSON) -> the payload the model is shown."""
    exercise = inp["exercise"]
    workout = inp.get("workout") or {}
    current = inp["set"]
    payload = {
        "exercise": {"id": exercise["id"], "name": exercise.get("name") or exercise["id"]},
        "workout": {
            "target_reps": workout.get("target_reps"),
            "target_sets": workout.get("target_sets"),
            "earlier_sets": [_set(s) for s in workout.get("earlier_sets") or []],
        },
        "set": {**_set(current), "attempts": [_attempt(a) for a in current.get("attempts") or []]},
    }
    history = inp.get("history") or []
    if history:
        payload["history"] = [_past_workout(history[0])]
    return payload


def rule_names(payload):
    """The fault keys in the set, what retrieval looks up."""
    return {v["rule"] for a in payload["set"]["attempts"] for v in a["violations"]}
