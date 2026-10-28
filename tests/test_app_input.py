"""rag_core/app_input.py: the app's FeedbackInput -> the payload prompt v15a reads.
Three inputs: docs/plans/feedback_input_example.json (repair set, abandoned attempt with null
similarity, one past workout), tests/fixtures/feedback_input_current_app_shape.json (the older
similarity shape: overall plus five regions, no history) and tests/fixtures/
feedback_input_app_2026-10-28.json (the app's own docs/feedback-input-example.json, built by its
feedbackInput: earlier sets, five past workouts, unscored history). Plain asserts, no API key or DB:

    python tests/test_app_input.py
"""
import copy
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from rag_core.app_input import payload_from_feedback_input, rule_names  # noqa: E402
from rag_core.prompt import APP_SYSTEM_PROMPT, SYSTEM_PROMPT  # noqa: E402

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
app = load("tests/fixtures/feedback_input_app_2026-10-28.json")

# --- the prompts --------------------------------------------------------------------
check("v14 prompt unchanged by the split", hashlib.sha1(SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
      "bd4b464157381df74fed3805f0b36ca8b8177437")
check("app prompt keeps v14's tasks and rules", APP_SYSTEM_PROMPT[APP_SYSTEM_PROMPT.index("Your tasks:"):],
      SYSTEM_PROMPT[SYSTEM_PROMPT.index("Your tasks:"):])
for key in ("violations[].rule", "attempt_no", "outcome", "totals", "mean_score", "earlier_sets", "target_reps"):
    check(f"app prompt explains {key}", key in APP_SYSTEM_PROMPT, True)
for key in ("error_type", "reps_detail", "total_reps", "previous_common_errors"):
    check(f"app prompt has no v14 key {key}", f"`{key}`" in APP_SYSTEM_PROMPT, False)

# --- the agreed example -------------------------------------------------------------
p = payload_from_feedback_input(example)
check("example: top-level keys", list(p), ["exercise", "workout", "set", "history"])
check("example: exercise", p["exercise"], {"id": "squat", "name": "Squat"})
check("example: totals are the app's counts", p["set"]["totals"],
      {"attempts": 5, "completed_reps": 4, "correct_reps": 2, "abandoned_attempts": 1})
check("example: set score", (p["set"]["set_no"], p["set"]["similarity"]), (1, {"mean_score": 63.4}))
check("example: attempt keys", list(p["set"]["attempts"][0]), ["attempt_no", "outcome", "similarity", "violations"])
check("example: outcomes as the app sends them", [a["outcome"] for a in p["set"]["attempts"]],
      ["correct", "incorrect", "correct", "incorrect", "abandoned"])
check("example: per-attempt score, abandoned null", [a["similarity"] for a in p["set"]["attempts"]],
      [{"score": 71.8}, {"score": 55.6}, {"score": 73.4}, {"score": 52.9}, None])
check("example: violations in priority order", [[v["rule"] for v in a["violations"]] for a in p["set"]["attempts"]],
      [[], ["knee_valgus"], [], ["partial_squat", "rounded_back"], ["partial_squat"]])
check("example: rule names for retrieval", rule_names(p), {"knee_valgus", "partial_squat", "rounded_back"})
check("example: target and earlier set", p["workout"],
      {"target_reps": 5, "target_sets": 3, "earlier_sets": [
          {"set_no": 1, "totals": {"attempts": 5, "completed_reps": 5, "correct_reps": 1, "abandoned_attempts": 0},
           "similarity": {"mean_score": 58.3}}]})
check("example: newest past workout only, by date", [(h["started_at"], len(h["sets"])) for h in p["history"]],
      [("2026-10-22", 2)])
check("example: past set scores", [s["similarity"] for s in p["history"][0]["sets"]],
      [{"mean_score": 55.2}, {"mean_score": 60.1}])
sent = json.dumps(p)
for absent in ("body_parts", "kind", "repair", "ended_by", "message", "state", "threshold", "rep_stats",
               "profile", "medical_history", "ACL", "feedback", "rest_seconds"):
    check(f"example: {absent!r} not sent", f'"{absent}' in sent or absent in sent.replace('"', ""), False)

# --- the older similarity shape -----------------------------------------------------
c = payload_from_feedback_input(current)
check("current: set score from overall", c["set"]["similarity"], {"mean_score": 71})
check("current: attempt score from overall", [a["similarity"] for a in c["set"]["attempts"]],
      [{"score": 82}, {"score": 64}, {"score": 67}, None])
check("current: violations sorted by priority, not by arrival",
      [v["rule"] for v in c["set"]["attempts"][1]["violations"]], ["hip_sag_or_pike", "elbow_flare"])
check("current: no history -> no history key", "history" in c, False)
check("current: no earlier sets", c["workout"]["earlier_sets"], [])
pc = json.dumps(c)
for private in ("Test User", "female", "162", "58"):
    check(f"current: profile field {private!r} not sent", f'"{private}"' in pc or f": {private}," in pc, False)
check("current: region scores not passed", "back_core" in pc, False)
check("current: violation messages not passed", "Tuck your elbows" in pc, False)

# --- the app's own example ----------------------------------------------------------
a = payload_from_feedback_input(app)
check("app: set", (a["set"]["set_no"], a["set"]["totals"]["correct_reps"], a["set"]["similarity"]),
      (3, 10, {"mean_score": 61.5}))
check("app: two earlier sets with scores", [(s["set_no"], s["similarity"]) for s in a["workout"]["earlier_sets"]],
      [(1, {"mean_score": 62.1}), (2, {"mean_score": 86.5})])
check("app: past sets sorted by set_no", [s["set_no"] for s in a["history"][0]["sets"]], [1, 2, 3])
check("app: unscored past sets -> similarity null", {json.dumps(s["similarity"]) for s in a["history"][0]["sets"]},
      {"null"})
check("app: abandoned attempt", a["set"]["attempts"][1],
      {"attempt_no": 2, "outcome": "abandoned", "similarity": None, "violations": [{"rule": "partial_squat"}]})

# --- edge cases ---------------------------------------------------------------------
clean = copy.deepcopy(current)
for at in clean["set"]["attempts"]:
    at["violations"] = []
    at["similarity"] = None
clean["set"]["similarity"] = None
cs = payload_from_feedback_input(clean)
check("clean: no violations anywhere", [at["violations"] for at in cs["set"]["attempts"]], [[], [], [], []])
check("clean: no rule names", rule_names(cs), set())
check("clean: similarity failed -> null everywhere",
      [cs["set"]["similarity"]] + [at["similarity"] for at in cs["set"]["attempts"]], [None] * 5)

no_workout = copy.deepcopy(current)
del no_workout["workout"]
check("no workout -> empty earlier sets, no target", payload_from_feedback_input(no_workout)["workout"],
      {"target_reps": None, "target_sets": None, "earlier_sets": []})

print("all passed" if not failed else f"{failed} failure(s)")
sys.exit(1 if failed else 0)
