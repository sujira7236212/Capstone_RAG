"""rag_core/feedback_format.py: prompt v17's JSON -> the text the app stores. The labels pinned here
are the ones MU-Capstone-Application lib/feedback-text.ts reads; change both together. No API key
or DB:

    python tests/test_feedback_format.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from rag_core.feedback_format import FormatError, answer_schema, render_feedback  # noqa: E402

failed = 0


def check(name, got, expected):
    global failed
    if got != expected:
        failed += 1
        print(f"FAIL  {name}\n  got: {got!r}\n  exp: {expected!r}")


def raises(name, fn):
    global failed
    try:
        fn()
    except FormatError:
        return
    failed += 1
    print(f"FAIL  {name}: no FormatError")


def fault(rule, **kw):
    item = {"rule": rule, "fault": f"{rule} went wrong.", "fix": f"Fix {rule}.", "what_it_is": "Looks like this.",
            "why_it_matters": "Your shoulder takes it.", "likely_cause": "Going too fast.", "setup_change": "Slow the tempo.", "drill": "Wall curls, 2 sets of 8.",
            "check": "Mirror, side on.", "in_this_set": "Attempts 1 and 4."}
    item.update(kw)
    return item


def answer(**kw):
    out = {"faults": [fault("elbow_flare"), fault("partial_curl")], "keep": "", "progress": "Up from 82.9.",
           "next": ["Pause at the bottom.", "Same load."]}
    out.update(kw)
    return json.dumps(out)


RULES = {"elbow_flare", "partial_curl"}

# --- the schema ---------------------------------------------------------------------------
s = answer_schema(RULES)
check("schema: rule keys listed, sorted", s["properties"]["faults"]["items"]["properties"]["rule"]["enum"],
      ["elbow_flare", "partial_curl"])
check("schema: at most one entry per rule", s["properties"]["faults"]["maxItems"], 2)
check("schema: every fault field required", s["properties"]["faults"]["items"]["required"],
      ["rule", "fault", "fix", "what_it_is", "why_it_matters", "likely_cause", "setup_change", "drill", "check",
       "in_this_set"])
check("schema: a clean set has no faults field", "faults" in answer_schema(set())["properties"], False)
check("schema: no health slot (medical history removed 2026-11-11)",
      ("health" in s["properties"], s["required"]), (False, ["faults", "keep", "progress", "next"]))

# --- the text -----------------------------------------------------------------------------
text = render_feedback(answer(), RULES)
paragraphs = text.split("\n\n")
check("text: the v16 summary block first, unchanged",
      paragraphs[0].splitlines(),
      ["Fault elbow_flare: elbow_flare went wrong.", "Fix: Fix elbow_flare.",
       "Fault partial_curl: partial_curl went wrong.", "Fix: Fix partial_curl."])
check("text: progress", paragraphs[1], "Progress: Up from 82.9.")
check("text: one details block per fault, in order",
      paragraphs[2].splitlines(),
      ["Details elbow_flare:", "What it is: Looks like this.", "Why it matters: Your shoulder takes it.",
       "Likely cause: Going too fast.",
       "Setup change: Slow the tempo.", "Drill: Wall curls, 2 sets of 8.", "Check: Mirror, side on.",
       "In this set: Attempts 1 and 4."])
check("text: the plan last", paragraphs[-1].splitlines(),
      ["Next Session Plan:", "1. Pause at the bottom.", "2. Same load."])
check("text: no health paragraph", "Health:" in text, False)
check("text: a health field from an old answer is not shown",
      render_feedback(answer(health="With your knee history, stay pain-free."), RULES), text)

clean = render_feedback(json.dumps({"keep": "Smooth and controlled.", "progress": "First set on record.",
                                    "next": ["Same again."]}), set())
check("clean: keep line, progress, plan", clean,
      "Keep: Smooth and controlled.\n\nProgress: First set on record.\n\nNext Session Plan:\n1. Same again.")

# --- cleaning, never rewording ------------------------------------------------------------
messy = answer(faults=[fault("elbow_flare", fix="- Fix: Pin the\npaper.", drill="", check="  Mirror.  ")])
lines = render_feedback(messy, RULES)
check("clean: bullet, repeated label and line break dropped", "Fix: Pin the paper." in lines, True)
check("clean: an empty detail is left out", "Drill:" in lines, False)
check("clean: spaces trimmed", "Check: Mirror." in lines, True)
check("fence around the JSON tolerated", render_feedback("```json\n" + answer() + "\n```", RULES), render_feedback(answer(), RULES))
dup = answer(faults=[fault("elbow_flare"), fault("elbow_flare", fault="again"), fault("knee_valgus")])
check("a repeated rule and a rule the set lacks are dropped",
      render_feedback(dup, RULES).split("\n\n")[0].splitlines(),
      ["Fault elbow_flare: elbow_flare went wrong.", "Fix: Fix elbow_flare."])
check("a single next item as a string", render_feedback(answer(next="Rest well."), RULES).endswith("1. Rest well."), True)

# --- what the app cannot do without -------------------------------------------------------
raises("not JSON", lambda: render_feedback("Fault elbow_flare: plain text", RULES))
raises("a JSON list", lambda: render_feedback("[]", RULES))
raises("faults expected, none given", lambda: render_feedback(answer(faults=[]), RULES))
raises("only faults the set lacks", lambda: render_feedback(answer(faults=[fault("knee_valgus")]), RULES))
raises("an empty fix", lambda: render_feedback(answer(faults=[fault("elbow_flare", fix=" ")]), RULES))
raises("a clean set without its keep line", lambda: render_feedback(json.dumps({"keep": ""}), set()))
raises("a field that is not text", lambda: render_feedback(answer(progress=3), RULES))

print("all passed" if not failed else f"{failed} failure(s)")
sys.exit(1 if failed else 0)
