"""rag_core/app_input.py: the app's FeedbackInput -> the session payload prompt v14 reads.
Two inputs: docs/plans/feedback_input_example.json (the agreed shape: repair set, abandoned
attempt with null similarity, one past workout) and tests/fixtures/
feedback_input_current_app_shape.json (what lib/analysis/contracts.ts sends today: five
similarity regions, full violation records, no history). Plain asserts, no API key or DB:

    python tests/test_app_input.py
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from rag_core.app_input import session_from_feedback_input  # noqa: E402
from rag_core.prompt import model_payload  # noqa: E402

failed = 0


def check(name, got, expected):
    global failed
    if got != expected:
        failed += 1
        print(f"FAIL  {name}\n  got: {got}\n  exp: {expected}")


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


example = load("docs/plans/feedback_input_example.json")
current = load("tests/fixtures/feedback_input_current_app_shape.json")

# --- the agreed shape ---------------------------------------------------------------
s = session_from_feedback_input(example)
check("example: exercise", (s["exercise_id"], s["name"]), ("squat", "Squat"))
check("example: summary keeps the app's counts", s["summary"],
      {"total_reps": 5, "correct_reps": 2, "incorrect_reps": 3, "abandoned_attempts": 1, "overall_score": 63.4})
check("example: rep numbers are attempt numbers", [r["rep_no"] for r in s["reps_detail"]], [1, 2, 3, 4, 5])
check("example: outcome -> status", [r["status"] for r in s["reps_detail"]],
      ["completed", "completed", "completed", "completed", "abort"])
check("example: per-attempt score", [r.get("similarity_scores_percent") for r in s["reps_detail"]],
      [{"overall": 71.8}, {"overall": 55.6}, {"overall": 73.4}, {"overall": 52.9}, None])
check("example: errors in priority order", [[e["error_type"] for e in r["errors"]] for r in s["reps_detail"]],
      [[], ["knee_valgus"], [], ["partial_squat", "rounded_back"], ["partial_squat"]])
check("example: body parts not passed", "body_parts" in json.dumps(s), False)
check("example: previous workout", s["historical_comparison"],
      {"previous_session_date": "2026-10-22", "previous_correct_reps": 3, "previous_incorrect_reps": 7,
       # sets weighed by completed reps: (55.2 * 5 + 60.1 * 4) / 9
       "previous_overall_score": 57.4})
check("example: no previous_common_errors (D4)", "previous_common_errors" in s["historical_comparison"], False)
check("example: health notes carried", s["health_notes"], "Left knee ACL reconstruction in 2024, no pain now")

p = model_payload(s)
check("example: health notes held back from the model", "health_notes" in p, False)
check("example: medical history text not in payload", "ACL" in json.dumps(p), False)

# --- the app's current shape --------------------------------------------------------
c = session_from_feedback_input(current)
check("current: summary from overall", c["summary"],
      {"total_reps": 4, "correct_reps": 1, "incorrect_reps": 3, "abandoned_attempts": 1, "overall_score": 71})
check("current: attempt overall", [r.get("similarity_scores_percent") for r in c["reps_detail"]],
      [{"overall": 82}, {"overall": 64}, {"overall": 67}, None])
check("current: violations sorted by priority, not by arrival",
      [e["error_type"] for e in c["reps_detail"][1]["errors"]], ["hip_sag_or_pike", "elbow_flare"])
check("current: state upper-cased for state_occurred",
      [e.get("state_occurred") for e in c["reps_detail"][1]["errors"]], ["CONCENTRIC", "ECCENTRIC"])
check("current: state_occurred held back", [e for r in model_payload(c)["reps_detail"] for e in r["errors"]],
      [{"error_type": "hip_sag_or_pike"}, {"error_type": "elbow_flare"},
       {"error_type": "partial_pushup"}, {"error_type": "partial_pushup"}])
check("current: no history -> no historical_comparison", "historical_comparison" in c, False)
pc = json.dumps(model_payload(c))
for private in ("Test User", "female", "162", "58"):
    check(f"current: profile field {private!r} not sent", f'"{private}"' in pc or f": {private}," in pc, False)
check("current: region scores not passed", "back_core" in pc, False)
check("current: violation messages not passed", "Tuck your elbows" in pc, False)

# --- edge cases ---------------------------------------------------------------------
clean = copy.deepcopy(current)
for a in clean["set"]["attempts"]:
    a["violations"] = []
    a["similarity"] = None
clean["set"]["similarity"] = None
clean["profile"]["medical_history"] = "none"
cs = session_from_feedback_input(clean)
check("clean: no errors anywhere", [r["errors"] for r in cs["reps_detail"]], [[], [], [], []])
check("clean: similarity failed -> no score keys", "overall_score" in cs["summary"]
      or any("similarity_scores_percent" in r for r in cs["reps_detail"]), False)

unscored = copy.deepcopy(example)
for st in unscored["history"][0]["sets"]:
    st["similarity"] = None
check("history without similarity -> no previous score",
      "previous_overall_score" in session_from_feedback_input(unscored)["historical_comparison"], False)

no_state = copy.deepcopy(current)
no_state["set"]["attempts"][2]["violations"][0]["state"] = None
check("violation without state -> no state_occurred key",
      session_from_feedback_input(no_state)["reps_detail"][2]["errors"], [{"error_type": "partial_pushup"}])

print("all passed" if not failed else f"{failed} failure(s)")
sys.exit(1 if failed else 0)
