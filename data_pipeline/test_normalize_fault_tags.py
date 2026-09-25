"""Cases for curator.normalize_fault_tags(): the three spellings found in
kb_gemini_curated_v5 (compare_output/ablation_log.md R0) plus the cases it must leave
alone. Plain asserts so it runs without pytest:

    python data_pipeline/test_normalize_fault_tags.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curator import normalize_fault_tags

CASES = [
    # the three variants seen in v5
    (("squat", ["partial_squat"]), ["partial squat"]),
    (("squat", ["knee valgus", "knee_valgus"]), ["knee valgus"]),
    (("bicep-curl", ["partial range_of_motion"]), ["partial range of motion"]),
    # case / whitespace, order kept
    (("squat", ["Butt  Wink", "partial_squat"]), ["butt wink", "partial squat"]),
    # must NOT change: already canonical, unknown code, another exercise's code
    (("lunge", ["shallow lunge"]), ["shallow lunge"]),
    (("squat", ["heels_lifting"]), ["heels_lifting"]),
    (("push-up", ["partial_squat"]), ["partial_squat"]),
    (("squat", []), []),
    (("squat", None), []),
]


def main():
    failed = 0
    for (exercise, tags), expected in CASES:
        got = normalize_fault_tags(tags, exercise)
        if got != expected:
            failed += 1
            print(f"FAIL\n  in:  {exercise} {tags}\n  got: {got}\n  exp: {expected}")
    print(f"{len(CASES) - failed}/{len(CASES)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
