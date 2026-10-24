"""Context-layer metrics of step 5: v6 strict (A) vs v6b strict (B) on the target rules.

    python eval/score_target_labels.py [--relabel 24=relevant,27=relevant]

Reads eval/labels_target_rules_v6b.json (one label per unique block) and the two strict
context files per exercise, and prints, per (session, target rule): blocks, matching rule
(relevant), wrong_fault, irrelevant, contradicts_rule, precision - and per kind the number
of relevant blocks A -> B. --relabel overrides labels for a sensitivity check. Offline.
"""
import argparse
import collections
import json
import sys

sys.path.insert(0, "eval")
from strict_offline_from_compare import parse_blocks  # noqa: E402

ARMS = {"A": "compare_output/strict_v6b/context_v6_strict_{ex}.json", "B": "compare_output/strict_v6b/context_v6b_strict_{ex}.json"}
KINDS = ("mistake", "consequence", "principle", "finding")
LABELS = ("relevant", "wrong_fault", "irrelevant", "contradicts_rule")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--relabel", default="", help="n=label,... override for a sensitivity check")
    args = ap.parse_args()
    with open("eval/labels_target_rules_v6b.json", encoding="utf-8") as f:
        chunks = json.load(f)["chunks"]
    for item in filter(None, args.relabel.split(",")):
        n, label = item.split("=")
        next(c for c in chunks if c["n"] == int(n))["label"] = label
    by_key = {(c["rule"], c["kind"], c["text"]): c for c in chunks}
    rules = {c["rule"] for c in chunks}

    for ex in ("lunge", "push-up"):
        sessions = {}
        for arm, pat in ARMS.items():
            with open(pat.format(ex=ex), encoding="utf-8") as f:
                for s in json.load(f)["sessions"]:
                    blocks = parse_blocks(s["context"]) if s["context"].startswith("[") else []
                    sessions.setdefault(s["payload"]["session_id"], {})[arm] = blocks
        for sid, arms in sessions.items():
            for rule in sorted(rules):
                if not any(b["label"] == rule for blocks in arms.values() for b in blocks):
                    continue
                print(f"\n{sid} {rule}")
                per_kind = {}
                for arm in ARMS:
                    mine = [b for b in arms[arm] if b["label"] == rule]
                    lab = [by_key[(rule, b["kind"], b["text"])] for b in mine]  # KeyError = unlabelled block
                    c = collections.Counter(x["label"] for x in lab)
                    prec = c["relevant"] / len(lab) if lab else float("nan")
                    print(f"  {arm}: blocks {len(lab)} | " + " ".join(f"{l} {c[l]}" for l in LABELS)
                          + f" | precision {prec:.2f} | #" + ",".join(str(x["n"]) for x in lab))
                    per_kind[arm] = collections.Counter(x["kind"] for x in lab if x["label"] == "relevant")
                print("  relevant per kind A->B: " + ", ".join(
                    f"{k} {per_kind['A'][k]}->{per_kind['B'][k]}" for k in KINDS))


if __name__ == "__main__":
    main()
