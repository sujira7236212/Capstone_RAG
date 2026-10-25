"""The app's FeedbackInput -> the session payload the prompt reads.

FeedbackInput is MU-Capstone-Application's contract (lib/analysis/contracts.ts, ADR-0007);
docs/plans/feedback_input_example.json is the shape agreed for it. The payload is the shape
of the mock sessions (mock_data/build_mock_sessions.py), because that is what prompt v14 was
written and evaluated against. Fields the app sends that v14 has no wording for are not
invented into it; each comes in with the prompt version that explains it (v15).

Kept from the app, as decided 2026-10-25 (docs/plans/app_integration_plan.md D3): the
attempt counts. total_reps = attempts and correct_reps are the app's own numbers, so the
feedback cannot contradict what the user sees on the same screen; abandoned_attempts is
passed through next to them.

Similarity comes in two shapes until the app switches over: the agreed one
(set: mean_score + body_parts, attempt: score + body_parts) and the app's current one
(overall + five regions). Only the overall number is passed: v14 reads one score per rep,
and a body part's score says how far it was from the expert, not in which direction, which
a prompt with no rule for it would guess at.

Not passed to the model at all: the profile's name, age, gender, weight and height. The
medical history is carried as `health_notes`, held back by prompt.model_payload until a
prompt has the rules for using it.
"""

STATUS = {"correct": "completed", "incorrect": "completed", "abandoned": "abort"}


def overall_score(similarity):
    """The one overall number of either similarity shape, None when there is none."""
    if not similarity:
        return None
    for key in ("mean_score", "score", "overall"):
        if similarity.get(key) is not None:
            return similarity[key]
    return None


def _rep(attempt):
    rep = {"rep_no": attempt["attempt_no"], "status": STATUS[attempt["outcome"]]}
    score = overall_score(attempt.get("similarity"))
    if score is not None:
        rep["similarity_scores_percent"] = {"overall": score}
    violations = sorted(attempt.get("violations") or [], key=lambda v: v.get("priority", 99))
    rep["errors"] = []
    for v in violations:
        error = {"error_type": v["rule"]}
        if v.get("state"):
            error["state_occurred"] = v["state"].upper()
        rep["errors"].append(error)
    return rep


def _summary(set_summary):
    t = set_summary["totals"]
    summary = {
        "total_reps": t["attempts"],
        "correct_reps": t["correct_reps"],
        "incorrect_reps": t["attempts"] - t["correct_reps"],
        "abandoned_attempts": t.get("abandoned_attempts", 0),
    }
    score = overall_score(set_summary.get("similarity"))
    if score is not None:
        summary["overall_score"] = score
    return summary


def _previous_workout(workout):
    """The newest past workout as v14's historical_comparison. A past set carries no
    violations (SetSummary), so previous_common_errors cannot be built and is left out (D4)."""
    sets = workout.get("sets") or []
    attempts = sum(s["totals"]["attempts"] for s in sets)
    correct = sum(s["totals"]["correct_reps"] for s in sets)
    prev = {
        "previous_session_date": workout["started_at"][:10],
        "previous_correct_reps": correct,
        "previous_incorrect_reps": attempts - correct,
    }
    # A set's score averages its completed reps, so the workout's weighs each set by them.
    scored = [(overall_score(s.get("similarity")), s["totals"]["completed_reps"]) for s in sets]
    scored = [(score, n) for score, n in scored if score is not None and n]
    if scored:
        prev["previous_overall_score"] = round(sum(sc * n for sc, n in scored) / sum(n for _, n in scored), 1)
    return prev


def session_from_feedback_input(inp):
    """FeedbackInput (a dict parsed from the app's JSON) -> the session dict test_rag_compare
    and the service pass to retrieval and to prompt.model_payload."""
    exercise = inp["exercise"]
    current = inp["set"]
    session = {
        "exercise_id": exercise["id"],
        "name": exercise.get("name") or exercise["id"],
        "summary": _summary(current),
        "reps_detail": [_rep(a) for a in current.get("attempts") or []],
    }
    history = inp.get("history") or []
    if history:
        session["historical_comparison"] = _previous_workout(history[0])
    health = (inp.get("profile") or {}).get("medical_history")
    if health is not None:
        session["health_notes"] = health
    return session
