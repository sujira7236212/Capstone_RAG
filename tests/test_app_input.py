"""rag_core/app_input.py: the app's FeedbackInput -> the payload prompt v15 reads.
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
check("app prompt shares v14's rules for the Context",
      APP_SYSTEM_PROMPT[APP_SYSTEM_PROMPT.index("How to read the Context:"):],
      SYSTEM_PROMPT[SYSTEM_PROMPT.index("How to read the Context:"):])
check("app prompt asks for JSON", "Answer with one JSON object and nothing else" in APP_SYSTEM_PROMPT, True)
# v17: the JSON fields rag_core/feedback_format.py reads (tests/test_feedback_format.py pins the text the
# app parses). "Why it matters" is out of the fields; _RULES (v14's) still names it as a past section.
for field in ("`faults`", "`rule`", "`fault`", "`fix`", "`what_it_is`", "`likely_cause`", "`setup_change`",
              "`drill`", "`check`", "`in_this_set`", "`keep`", "`progress`", "`health`", "`next`"):
    check(f"app prompt: field {field}", field in APP_SYSTEM_PROMPT, True)
check("app prompt: no why_it_matters field", "why_it_matters" in APP_SYSTEM_PROMPT, False)
check("app prompt has health rules", "User health notes" in APP_SYSTEM_PROMPT, True)
check("v14 prompt has no health rules", "User health notes" in SYSTEM_PROMPT, False)
for key in ("violations[].rule", "attempt_no", "outcome", "totals", "mean_score", "earlier_sets", "target_reps",
            "body_parts", "kind", "ended_by", "medical_history"):
    check(f"app prompt explains {key}", key in APP_SYSTEM_PROMPT, True)
for key in ("error_type", "reps_detail", "total_reps", "previous_common_errors"):
    check(f"app prompt has no v14 key {key}", f"`{key}`" in APP_SYSTEM_PROMPT, False)

# --- the agreed example -------------------------------------------------------------
p = payload_from_feedback_input(example)
check("example: top-level keys", list(p), ["exercise", "profile", "workout", "set", "history"])
check("example: medical history", p["profile"], {"medical_history": "Left knee ACL reconstruction in 2024, no pain now"})
check("example: exercise", p["exercise"], {"id": "squat", "name": "Squat"})
check("example: totals are the app's counts", p["set"]["totals"],
      {"attempts": 5, "completed_reps": 4, "correct_reps": 2, "abandoned_attempts": 1})
check("example: set", [p["set"][k] for k in ("set_no", "kind", "ended_by")], [1, "repair", "user_ended"])
check("example: set scores", p["set"]["similarity"],
      {"mean_score": 63.4, "body_parts": {"torso": 53.3, "right_leg": 68.8, "left_leg": 70.7}})
check("example: attempt keys", list(p["set"]["attempts"][0]), ["attempt_no", "outcome", "similarity", "violations"])
check("example: outcomes as the app sends them", [a["outcome"] for a in p["set"]["attempts"]],
      ["correct", "incorrect", "correct", "incorrect", "abandoned"])
check("example: per-attempt score, abandoned null",
      [a["similarity"] and a["similarity"]["score"] for a in p["set"]["attempts"]], [71.8, 55.6, 73.4, 52.9, None])
check("example: per-attempt body parts", p["set"]["attempts"][3]["similarity"]["body_parts"],
      {"torso": 31.8, "right_leg": 63.4, "left_leg": 65.0})
check("example: violations in priority order", [[v["rule"] for v in a["violations"]] for a in p["set"]["attempts"]],
      [[], ["knee_valgus"], [], ["partial_squat", "rounded_back"], ["partial_squat"]])
check("example: rule names for retrieval", rule_names(p), {"knee_valgus", "partial_squat", "rounded_back"})
check("example: target and earlier set", p["workout"],
      {"target_reps": 5, "target_sets": 3, "earlier_sets": [
          {"set_no": 1, "kind": "initial", "ended_by": "attempt_cap",
           "totals": {"attempts": 5, "completed_reps": 5, "correct_reps": 1, "abandoned_attempts": 0},
           "similarity": {"mean_score": 58.3, "body_parts": {"torso": 42.0, "right_leg": 65.9, "left_leg": 67.2}}}]})
check("example: newest past workout only, by date", [(h["started_at"], len(h["sets"])) for h in p["history"]],
      [("2026-10-22", 2)])
check("example: past sets", [(s["kind"], s["similarity"]["mean_score"]) for s in p["history"][0]["sets"]],
      [("initial", 55.2), ("repair", 60.1)])
sent = json.dumps(p)
for absent in ("message", "state", "threshold", "rep_stats", "rep_number", "feedback", "rest_seconds"):
    check(f"example: {absent!r} not sent", f'"{absent}' in sent or absent in sent.replace('"', ""), False)

# --- the older similarity shape -----------------------------------------------------
c = payload_from_feedback_input(current)
check("current: set score from overall, no regions", c["set"]["similarity"], {"mean_score": 71})
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
check("current: medical history 'none' is passed as written", c["profile"], {"medical_history": "none"})
check("current: violation messages not passed", "Tuck your elbows" in pc, False)

# --- the app's own example ----------------------------------------------------------
a = payload_from_feedback_input(app)
check("app: set", (a["set"]["set_no"], a["set"]["kind"], a["set"]["ended_by"], a["set"]["totals"]["correct_reps"]),
      (3, "initial", "target_reached", 10))
check("app: set scores, only the two agreed keys", a["set"]["similarity"],
      {"mean_score": 61.5, "body_parts": {"torso": 44.4, "left_leg": 64.4, "right_leg": 74.8}})
check("app: attempt scores, only the two agreed keys", a["set"]["attempts"][0]["similarity"],
      {"score": 61.9, "body_parts": {"torso": 47.4, "left_leg": 61.6, "right_leg": 75.1}})
check("app: two earlier sets with scores", [(s["set_no"], s["similarity"]["mean_score"]) for s in a["workout"]["earlier_sets"]],
      [(1, 62.1), (2, 86.5)])
check("app: medical history 'None' is passed as written", a["profile"], {"medical_history": "None"})
pa = json.dumps(a)
for absent in ("weakest_body_part", "mean_score_correct", "tracking_confidence", "warnings", "skipped_reason",
               "service_version", "bpe_v3", "reference", "Kavee", "display_name", "Keep knees in line"):
    check(f"app: {absent!r} not sent", absent in pa, False)
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

other_model = copy.deepcopy(app)
other_model["workout"]["earlier_sets"][0]["similarity"]["model"] = "bpe_v2"
other_model["history"][0]["sets"][0]["similarity"] = {"mean_score": 40, "model": "bpe_v3_seed2026",
                                                     "reference": {"kind": "package", "source": "a coach's take"}}
om = payload_from_feedback_input(other_model)
check("another scoring model -> earlier set score null",
      [s["similarity"] and s["similarity"]["mean_score"] for s in om["workout"]["earlier_sets"]], [None, 86.5])
check("another reference -> past set score null", om["history"][0]["sets"][0]["similarity"], None)

no_profile = copy.deepcopy(app)
del no_profile["profile"]
blank = copy.deepcopy(app)
blank["profile"]["medical_history"] = "  "
check("no profile -> no profile key", "profile" in payload_from_feedback_input(no_profile), False)
check("blank medical history -> no profile key", "profile" in payload_from_feedback_input(blank), False)

no_workout = copy.deepcopy(current)
del no_workout["workout"]
check("no workout -> empty earlier sets, no target", payload_from_feedback_input(no_workout)["workout"],
      {"target_reps": None, "target_sets": None, "earlier_sets": []})

print("all passed" if not failed else f"{failed} failure(s)")
sys.exit(1 if failed else 0)
