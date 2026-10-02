"""Cases for the T4 curator changes (docs/rule_change_v6_plan.md T4): routing general/
items to an exercise, mapping exercise_type, the T3a skip list, and the fault-code
block (all 12 rules for general/, card excludes as "do not tag when"). Plain asserts so
it runs without pytest or an API key:

    python data_pipeline/test_route_general.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curator import (_fault_code_block, _prompt_context, exercise_for_type, load_skip_list,
                     route_general_window)

failed = 0


def check(name, got, expected):
    global failed
    if got != expected:
        failed += 1
        print(f"FAIL  {name}\n  got: {got}\n  exp: {expected}")


def item(text, tags=()):
    return {"text": text, "applies_to_fault": list(tags)}


def window(exercise_type, **fields):
    w = {"exercise_type": exercise_type, "source": "data/general/x.pdf",
         "core_principles": [], "common_mistakes": [], "specific_findings": [], "consequences": []}
    w.update(fields)
    return w


def texts(routed, ex, field):
    return [i["text"] for i in routed.get(ex, {}).get(field, [])]


# --- exercise_for_type -----------------------------------------------------------------
for given, expected in [
    ("Back Squat", "squat"), ("Push-up", "push-up"), ("Forward Lunge", "lunge"),
    ("Dumbbell Biceps Curl", "bicep-curl"), ("Generic", None), ("", None),
    ("Leg Curl", None), ("Hamstring Curl", None), ("Deadlift", None),
]:
    check(f"exercise_for_type({given!r})", exercise_for_type(given), expected)

# --- route_general_window --------------------------------------------------------------
# one tag -> that exercise, even when the window says another exercise
r = route_general_window(window("Generic", common_mistakes=[item("knees cave in", ["knee_valgus"])]))
check("tag routes to its exercise", sorted(r), ["squat"])
check("tag kept", r["squat"]["common_mistakes"][0]["applies_to_fault"], ["knee_valgus"])
check("routed_from set", r["squat"]["routed_from"], "general")
check("window-level tags recomputed", r["squat"]["applies_to_fault"], ["knee_valgus"])

# tags from two exercises -> a copy in each, each with only its own exercise's tags
r = route_general_window(window("Generic", core_principles=[
    item("keep the trunk upright", ["rounded_back", "forward_trunk_lean"])]))
check("two exercises", sorted(r), ["lunge", "squat"])
check("squat copy tags", r["squat"]["core_principles"][0]["applies_to_fault"], ["rounded_back"])
check("lunge copy tags", r["lunge"]["core_principles"][0]["applies_to_fault"], ["forward_trunk_lean"])

# no tag, exercise_type maps -> that exercise; no tag, Generic -> general
r = route_general_window(window("Barbell Back Squat", core_principles=[item("brace before descending")]))
check("untagged + mappable", texts(r, "squat", "core_principles"), ["brace before descending"])
r = route_general_window(window("Generic", core_principles=[item("warm up first")]))
check("untagged + generic", sorted(r), ["general"])

# a mixed window splits item by item
r = route_general_window(window("Lunge", common_mistakes=[
    item("front knee too deep", ["excessive_front_knee_flexion"]),
    item("elbows flare out", ["elbow_flare"]),
    item("rushing the reps")]))
check("mixed: lunge", texts(r, "lunge", "common_mistakes"), ["front knee too deep", "rushing the reps"])
check("mixed: curl", texts(r, "bicep-curl", "common_mistakes"), ["elbows flare out"])
check("mixed: lunge window tags", r["lunge"]["applies_to_fault"], ["excessive_front_knee_flexion"])

# an unknown tag is not a route: the item falls back like an untagged one
r = route_general_window(window("Generic", consequences=[item("strains the knee", ["heels_lifting"])]))
check("unknown tag", sorted(r), ["general"])

# --- fault-code block ------------------------------------------------------------------
block = _fault_code_block("general")
for code in ("partial_squat", "hip_sag_or_pike", "straight_back_leg", "partial_curl"):
    check(f"general block has {code}", f'"{code}"' in block, True)
check("general block grouped", "  lunge:" in block and "  bicep-curl:" in block, True)
squat = _fault_code_block("squat")
check("squat block has no lunge rule", '"shallow_lunge"' in squat, False)
check("excludes line under knee_varus", "do not tag when: Knees caving inward (knee_valgus)" in squat, True)

# an exercise folder keeps the v5 wording; general/ gets the explicit-exercise rule
ctx = _prompt_context("squat")
check("squat filed_under", ctx["filed_under"],
      "It is filed under the exercise 'squat'. Extract information an AI exercise feedback system can use "
      "to tell a user what is wrong with their squat technique and why it matters")
check("squat no exercise_type rule", ctx["exercise_type_rule"], "")
check("general exercise_type rule", "ONLY when the text names that exercise explicitly"
      in _prompt_context("general")["exercise_type_rule"], True)

# --- skip list -------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "prefilter.json")
    entries = [
        {"path": "data/squat/a.pdf", "decision": "drop", "reason": "off topic"},
        {"path": "data/squat/b.pdf", "decision": "keep", "reason": "ok"},
        {"url": "https://x.example/u", "list": "data/squat/urls.txt", "decision": "drop", "reason": "ads"},
    ]
    json.dump({"entries": entries}, open(p, "w", encoding="utf-8"))
    paths, urls = load_skip_list(p, d)
    check("skip: dropped path", list(paths.values()), ["off topic"])
    check("skip: path is absolute", next(iter(paths)), os.path.normcase(os.path.join(d, "data", "squat", "a.pdf")))
    check("skip: dropped url", urls, {"https://x.example/u": "ads"})

    entries.append({"path": "data/general/c.pdf", "decision": "pending", "reason": "?"})
    json.dump({"entries": entries}, open(p, "w", encoding="utf-8"))
    try:
        load_skip_list(p, d)
        check("skip: pending refuses", "no error", "SystemExit")
    except SystemExit:
        pass

print("all passed" if not failed else f"{failed} failure(s)")
sys.exit(1 if failed else 0)
