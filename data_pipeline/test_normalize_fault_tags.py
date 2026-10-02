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
    # the v5 kind of variant (space vs underscore), against the 2026-09-28 rule names
    (("squat", ["partial squat"]), ["partial_squat"]),
    (("squat", ["knee valgus", "knee_valgus"]), ["knee_valgus"]),
    (("bicep-curl", ["partial curl"]), ["partial_curl"]),
    # case / whitespace, order kept
    (("squat", ["Rounded  Back", "partial squat"]), ["rounded_back", "partial_squat"]),
    # must NOT change: already canonical, unknown code, another exercise's code
    (("lunge", ["forward_trunk_lean"]), ["forward_trunk_lean"]),
    (("squat", ["heels_lifting"]), ["heels_lifting"]),
    (("push-up", ["partial squat"]), ["partial squat"]),
    # a superseded code is a different word, not a spelling: mapping it is the
    # retagger's job (LEGACY_CODES), not this function's
    (("squat", ["knee depth"]), ["knee depth"]),
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
