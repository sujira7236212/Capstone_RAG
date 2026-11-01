"""The app's FeedbackInput -> the JSON the model reads (prompt.APP_SYSTEM_PROMPT, v15).

FeedbackInput is MU-Capstone-Application's contract (lib/analysis/contracts.ts, ADR-0007; its
docs/feedback-input-structure.json describes every field). docs/plans/feedback_input_example.json
is the agreed example and tests/fixtures/feedback_input_app_2026-10-28.json a real one. Since v15a
(2026-10-28) the payload keeps the app's own key names and nesting (exercise, workout, set,
totals, attempt_no, outcome, violations[].rule, similarity.score / mean_score), the same names the
similarity service answers with, instead of the mock sessions' v14 format (summary, reps_detail,
status, error_type). The eval scripts keep v14's format and prompt.

Passed: the exercise; the medical history (v15, while the profiles are mock data: D6 in
docs/plans/app_integration_plan.md is still open); the target per set and the earlier sets of
this workout; the set's number, kind, how it ended, totals and scores; each attempt's number,
outcome, scores and fault keys in priority order; and the newest past workout's sets. Kept from
2026-10-25 (plan D3): the app's own counts, so the feedback cannot contradict what the user sees
on the same screen.

Similarity (v15, the user's choice of 2026-10-30): the overall score and the per-body-part
scores, of the set (mean_score, body_parts) and of each attempt (score, body_parts). The older
`overall` shape is still read, with no body parts: its regions are not the app's. An earlier
set's or a past workout's scores go only when they came from the same scoring model and
reference as this set's; the app's structure says other scores do not compare, so they are sent
as null.

Not passed to the model at all: the rest of the profile (name, age, gender, weight, height), the
exercise's rules, rest_seconds, the feedback already written for earlier sets, the violation's
message, state, value and threshold (the message waits for a run on the real model, plan A3),
rep_number, rep_stats, frames and durations (duration_s waits until the feedback is good), and
every similarity field beyond the two above.
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
    if score is None:
        return None
    out = {key: score}
    if similarity.get("body_parts"):
        out["body_parts"] = similarity["body_parts"]
    return out


def _scored_alike(similarity, current):
    """False when both sets name their scoring model and reference and either differs. A set
    that names neither (the stub, the older shape) is taken as comparable."""
    if not similarity or not current:
        return True
    for key in ("model", "reference"):
        if similarity.get(key) is not None and current.get(key) is not None and similarity[key] != current[key]:
            return False
    return True


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


def _set(set_summary, current_similarity=None):
    similarity = set_summary.get("similarity")
    out = {"set_no": set_summary["set_no"], "kind": set_summary.get("kind") or "initial"}
    if set_summary.get("ended_by"):
        out["ended_by"] = set_summary["ended_by"]
    out["totals"] = _totals(set_summary["totals"])
    out["similarity"] = (_similarity(similarity, "mean_score")
                         if _scored_alike(similarity, current_similarity) else None)
    return out


def _past_workout(workout, current_similarity):
    """The newest past workout. Its sets carry no violations (SetSummary), so the model is told
    not to compare faults with it. The app does not order them, so they are sorted here."""
    return {
        "started_at": workout["started_at"][:10],
        "sets": [_set(s, current_similarity) for s in sorted(workout.get("sets") or [], key=lambda s: s["set_no"])],
    }


def payload_from_feedback_input(inp):
    """FeedbackInput (a dict parsed from the app's JSON) -> the payload the model is shown."""
    exercise = inp["exercise"]
    workout = inp.get("workout") or {}
    current = inp["set"]
    scored = current.get("similarity")
    payload = {"exercise": {"id": exercise["id"], "name": exercise.get("name") or exercise["id"]}}
    medical_history = ((inp.get("profile") or {}).get("medical_history") or "").strip()
    if medical_history:
        payload["profile"] = {"medical_history": medical_history}
    payload["workout"] = {
        "target_reps": workout.get("target_reps"),
        "target_sets": workout.get("target_sets"),
        "earlier_sets": [_set(s, scored) for s in workout.get("earlier_sets") or []],
    }
    payload["set"] = {**_set(current), "attempts": [_attempt(a) for a in current.get("attempts") or []]}
    history = inp.get("history") or []
    if history:
        payload["history"] = [_past_workout(history[0], scored)]
    return payload


def rule_names(payload):
    """The fault keys in the set, what retrieval looks up."""
    return {v["rule"] for a in payload["set"]["attempts"] for v in a["violations"]}
