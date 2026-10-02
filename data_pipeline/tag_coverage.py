"""Count tagged items per rule and item kind in a curated folder, straight from the JSON
(no ingest, no API). Used between T3 curation rounds to decide which rules still need
sources (docs/rule_change_v6_plan.md T3); the decision must come from these counts, never
from eval results.

    python data_pipeline/tag_coverage.py [curated_data_v6] [--min 5]
"""
import argparse
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from error_taxonomy import ERROR_TAXONOMY

KINDS = {"common_mistakes": "mistake", "consequences": "consequence",
         "core_principles": "principle", "specific_findings": "finding"}


def coverage(folder: str):
    counts = collections.defaultdict(collections.Counter)
    sources = collections.defaultdict(set)
    items, untagged = collections.Counter(), collections.Counter()
    for path in glob.glob(os.path.join(folder, "**", "*.json"), recursive=True):
        exercise = os.path.relpath(path, folder).split(os.sep)[0]
        with open(path, encoding="utf-8") as f:
            windows = json.load(f)
        for w in windows:
            for field, kind in KINDS.items():
                for item in w.get(field, []):
                    items[exercise] += 1
                    if not item.get("applies_to_fault"):
                        untagged[exercise] += 1
                    for code in item.get("applies_to_fault", []):
                        counts[code][kind] += 1
                        sources[code].add(os.path.basename(path))
    return counts, sources, items, untagged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", default="curated_data_v6")
    ap.add_argument("--min", type=int, default=5, help="flag a rule with fewer tagged items of a kind")
    args = ap.parse_args()
    counts, sources, items, untagged = coverage(args.folder)
    print("items per exercise:", {k: f"{v} ({untagged[k]} untagged)" for k, v in sorted(items.items())})
    print(f"\n| exercise | rule | mistake | consequence | principle | finding | sources | below {args.min} |")
    print("|---|---|---|---|---|---|---|---|")
    for exercise, faults in ERROR_TAXONOMY.items():
        for code in faults:
            c = counts[code]
            low = [k for k in ("mistake", "consequence", "principle") if c[k] < args.min]
            print(f"| {exercise} | {code} | {c['mistake']} | {c['consequence']} | {c['principle']} | "
                  f"{c['finding']} | {len(sources[code])} | {', '.join(low) or '-'} |")


if __name__ == "__main__":
    main()
