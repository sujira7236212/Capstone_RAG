"""Checks prompt v17 answers against the layout the app shows. No API, no database.

For each captured request that has the model's raw JSON (`raw`, prompt v17 onward) it reports:
  - words per field against the limit the prompt gives (rag_core/feedback_format.py)
  - the words a user reads before opening anything (fault + fix lines, health, progress) and the total
  - faults the set carries that the answer leaves out
  - a rule key written outside its `rule` field
  - a fix repeated by the plan or by the fault's own details (shared content words)
  - numbers in neither the Context nor the set's data: allowed in setup_change, drill and next as
    the model's own instruction (the user's call, 2026-11-07), flagged anywhere else. A digit
    matches anywhere in that text, so this misses a number that happens to appear elsewhere
Older records (no `raw`) get their total words only, as a baseline.

    python eval/check_feedback_layout.py capture/app_requests.jsonl [--last N] [--json]
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from rag_core.feedback_format import (DETAIL_FIELDS, FAULT_LIMITS, NEXT_LIMIT, TOP_LIMITS,  # noqa: E402
                                      FormatError, parse_answer)

INSTRUCTION_FIELDS = {"setup_change", "drill", "next"}
NUMBER_WORDS = {"two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "twelve", "fifteen",
                "twenty", "thirty", "forty", "fifty", "hundred"}
STOP = set("""a an the and or but to of in on at for with your you it its is are be this that as so up
down then from into by not no do does one each every keep make let get stay more less than""".split())


def words(text):
    return len((text or "").split())


def content_words(text):
    return {w for w in re.findall(r"[a-z]+", (text or "").lower()) if w not in STOP and len(w) > 3}


def numbers(text):
    t = (text or "").lower()
    return set(re.findall(r"\d+(?:\.\d+)?", t)) | {w for w in re.findall(r"[a-z]+", t) if w in NUMBER_WORDS}


def check(record):
    out = {"captured_at": record.get("captured_at"), "prompt": (record.get("version") or {}).get("prompt"),
           "exercise": record["payload"]["exercise"]["id"], "total_words": words(record.get("feedback")), "issues": []}
    raw = record.get("raw")
    if raw is None:
        return out
    try:
        answer = parse_answer(raw)
    except FormatError as e:
        out["issues"].append(f"raw: {e}")
        return out
    rules = sorted({v["rule"] for a in record["payload"]["set"]["attempts"] for v in a["violations"]})
    # Numbers the model may state: the Context's, and the set's own (scores, attempt numbers, targets).
    known = (record.get("context") or "").lower() + json.dumps(record["payload"])
    issues = out["issues"]
    fields = []  # (where, field name, text, limit)
    faults = [f for f in answer.get("faults") or [] if isinstance(f, dict)]
    for f in faults:
        r = f.get("rule")
        for name, limit in FAULT_LIMITS.items():
            fields.append((r, name, f.get(name), limit))
        for name, _, limit in DETAIL_FIELDS:
            fields.append((r, name, f.get(name), limit))
    for name, limit in TOP_LIMITS.items():
        fields.append(("set", name, answer.get(name), limit))
    for i, step in enumerate(answer.get("next") or []):
        fields.append(("set", "next", step, NEXT_LIMIT))

    out["fields"] = {}
    for where, name, text, limit in fields:
        n = words(text)
        out["fields"].setdefault(name, []).append(n)
        if n > limit:
            issues.append(f"{where}.{name}: {n} words, limit {limit}")
        leaked = [k for k in rules if k in (text or "")]
        if leaked:
            issues.append(f"{where}.{name}: rule key {leaked[0]} in the text")
        stray = {x for x in numbers(text) if x not in known}
        if stray and name not in INSTRUCTION_FIELDS:
            issues.append(f"{where}.{name}: number(s) in neither the Context nor the set: {sorted(stray)}")
        elif stray:
            out.setdefault("own_instruction_numbers", []).append(f"{where}.{name}: {sorted(stray)}")

    missing = [r for r in rules if r not in {f.get("rule") for f in faults}]
    if missing:
        issues.append(f"faults left out: {missing}")
    plan = " ".join(answer.get("next") or [])
    for f in faults:
        fix = content_words(f.get("fix"))
        for name in ("next", "what_it_is", "setup_change"):
            other = plan if name == "next" else f.get(name)
            shared = fix & content_words(other)
            if len(fix) and len(shared) / len(fix) >= 0.5:
                issues.append(f"{f.get('rule')}: the fix is repeated in {name} ({sorted(shared)})")
    out["first_layer_words"] = sum(words(f.get("fault")) + words(f.get("fix")) for f in faults) + \
        words(answer.get("keep")) + words(answer.get("health")) + words(answer.get("progress"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("capture", nargs="+")
    ap.add_argument("--last", type=int, help="only the last N records")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    records = []
    for path in args.capture:
        with open(path, encoding="utf-8") as f:
            records += [json.loads(line) for line in f if line.strip()]
    records = [r for r in records if r.get("feedback") and r.get("payload")]
    if args.last:
        records = records[-args.last:]
    results = [check(r) for r in records]
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return
    for r in results:
        head = f"{r['captured_at']} {r['exercise']} {r['prompt']}: {r['total_words']} words"
        if "first_layer_words" in r:
            head += f", {r['first_layer_words']} before opening anything"
        print(head)
        for issue in r["issues"]:
            print(f"  ! {issue}")
        for note in r.get("own_instruction_numbers", []):
            print(f"  · own instruction number {note}")


if __name__ == "__main__":
    main()
