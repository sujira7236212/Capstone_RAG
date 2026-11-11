"""Prompt v17's answer: the model writes JSON, the service writes the text the app stores.

Why (2026-11-07, the user's plan for prompt and layout): v16 asked the model for labelled plain
text and the one v16 answer with faults on Gemini came back with hyphen bullets and labels the
prompt had ruled out, which the app then showed raw. A JSON schema keeps the model inside the
slots, and the text is built here, so it always has the same shape. The app's contract does not
change: POST /feedback still answers `{feedback: string}`, stored in sets.llm_feedback.

The text, paragraphs separated by one blank line (MU-Capstone-Application lib/feedback-text.ts
reads it; change both together, tests/test_feedback_format.py pins it):

    Fault <rule>: <fault>          one pair per fault, as in v16, so an app that only
    Fix: <fix>                     knows v16 still shows the list
    (or a single "Keep: <keep>" line on a set with no fault)

    Progress: <progress>

    Details <rule>:                one block per fault, shown when the user opens it
    What it is: ...
    Why it matters: ...            (prompt v18)
    Likely cause: ...
    Setup change: ...
    Drill: ...
    Check: ...
    In this set: ...

    Next Session Plan:
    1. ...

Nothing is reworded or cut here: fields are only trimmed of line breaks, bullet symbols and a
repeated label, so a too-long field stays too long and eval/check_feedback_layout.py reports it.
"""
import json
import re

# (JSON field, label in the text, word limit the prompt gives). The order is the order shown.
DETAIL_FIELDS = (
    ("what_it_is", "What it is", 25),
    ("why_it_matters", "Why it matters", 25),  # v18
    ("likely_cause", "Likely cause", 15),
    ("setup_change", "Setup change", 15),
    ("drill", "Drill", 20),
    ("check", "Check", 15),
    ("in_this_set", "In this set", 20),
)
FAULT_LIMITS = {"fault": 15, "fix": 12}
TOP_LIMITS = {"keep": 15, "progress": 25}  # "health" removed 2026-11-11 with the medical history
NEXT_LIMIT = 12
NEXT_MAX = 2

PLAN_HEADING = "Next Session Plan:"

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")
_BULLET = re.compile(r"^(?:[-*•]|\d+[.)])\s+")


class FormatError(ValueError):
    """The model's answer is not the JSON prompt v17 asks for."""


def answer_schema(rules):
    """The JSON schema of one answer for a set whose faults are `rules` (a set of rule keys).
    Every rule key the model may write is listed, so it cannot invent or misspell one, and a set
    with no fault has no `faults` field at all. Gemini takes this as response_json_schema."""
    text = {"type": "string"}
    props = {
        "keep": text,
        "progress": text,
        "next": {"type": "array", "items": text, "minItems": 1, "maxItems": NEXT_MAX},
    }
    required = ["keep", "progress", "next"]
    if rules:
        fault = {"rule": {"type": "string", "enum": sorted(rules)}, "fault": text, "fix": text}
        fault.update({name: text for name, _, _ in DETAIL_FIELDS})
        props = {"faults": {"type": "array", "minItems": 1, "maxItems": len(rules),
                            "items": {"type": "object", "properties": fault, "required": list(fault)}},
                 **props}
        required.insert(0, "faults")
    return {"type": "object", "properties": props, "required": required}


def _clean(value, label=None):
    """One line of plain words: line breaks joined, a leading bullet and a repeated label dropped."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise FormatError(f"a field is {type(value).__name__}, not text")
    text = " ".join(value.split())
    text = _BULLET.sub("", text)
    if label and text.lower().startswith(label.lower() + ":"):
        text = text[len(label) + 1:].lstrip()
    return text


def parse_answer(raw):
    """The model's raw output -> a dict. Tolerates a ```json fence around it."""
    if not isinstance(raw, str):
        raise FormatError("the answer is not text")
    try:
        answer = json.loads(_FENCE.sub("", raw.strip()))
    except json.JSONDecodeError as e:
        raise FormatError(f"the answer is not JSON ({e.msg} at {e.pos})") from None
    if not isinstance(answer, dict):
        raise FormatError("the answer is not a JSON object")
    return answer


def render_feedback(raw, rules):
    """The model's raw JSON -> the text the app stores. `rules`: the rule keys in the set.

    Kept strict where the app depends on it: a set with faults needs at least one fault with its
    fault and fix lines, a clean set needs its keep line. A fault the set does not carry is dropped
    (the schema already forbids it), and so is a second entry for the same rule."""
    answer = parse_answer(raw)
    paragraphs = []
    faults = []
    if rules:
        seen = set()
        for item in answer.get("faults") or []:
            if not isinstance(item, dict):
                continue
            rule = item.get("rule")
            if rule not in rules or rule in seen:
                continue
            fault, fix = _clean(item.get("fault"), "Fault"), _clean(item.get("fix"), "Fix")
            if not fault or not fix:
                raise FormatError(f"{rule}: the fault or the fix is empty")
            seen.add(rule)
            faults.append((rule, fault, fix, item))
        if not faults:
            raise FormatError("a set with faults came back with none")
        paragraphs.append("\n".join(f"Fault {rule}: {fault}\nFix: {fix}" for rule, fault, fix, _ in faults))
    else:
        keep = _clean(answer.get("keep"), "Keep")
        if not keep:
            raise FormatError("a set with no fault came back without its keep line")
        paragraphs.append(f"Keep: {keep}")

    progress = _clean(answer.get("progress"), "Progress")
    if progress:
        paragraphs.append(f"Progress: {progress}")

    for rule, _, _, item in faults:
        lines = [f"{label}: {text}" for name, label, _ in DETAIL_FIELDS
                 if (text := _clean(item.get(name), label))]
        if lines:
            paragraphs.append("\n".join([f"Details {rule}:"] + lines))

    steps = answer.get("next") or []
    steps = [s for s in (_clean(x) for x in ([steps] if isinstance(steps, str) else steps)) if s]
    if steps:
        paragraphs.append("\n".join([PLAN_HEADING] + [f"{i}. {s}" for i, s in enumerate(steps, 1)]))
    return "\n\n".join(paragraphs)
