"""Cases for error_taxonomy.resolve() against the 2026-09-25 rule set: rule name, the
on-screen cue, "_" vs " ", superseded codes, and the codes that must stay unknown.
Plain asserts so it runs without pytest:

    python test_error_taxonomy.py
"""
import sys

from error_taxonomy import ERROR_TAXONOMY, LEGACY_CODES, resolve

CASES = [
    # (error_type, exercise_id) -> expected code, or None for unknown
    (("knee_valgus", "squat"), "knee_valgus"),
    (("Knee Valgus", "squat"), "knee_valgus"),
    (("Push knees out", "squat"), "knee_valgus"),
    (("Keep knees in line", "squat"), "knee_varus"),
    (("Keep back straight", "squat"), "back_straight"),
    (("Lower Your Chest", "push-up"), "elbow_depth"),
    (("Raise your front knee", "lunge"), "front_knee_too_deep"),
    (("Full range of motion", "Bicep Curl"), "full_rom"),
    # superseded codes, per exercise
    (("Partial squat", "squat"), "knee_depth"),
    (("Hip sag", "push-up"), "body_alignment"),
    (("Partial range of motion", "push-up"), "elbow_depth"),
    (("Partial range of motion", "bicep-curl"), "full_rom"),
    (("Elbow flare", "bicep-curl"), "elbow_away"),
    (("Excessive forward trunk lean", "lunge"), "torso_upright"),
    # no current rule behind these
    (("Butt wink", "squat"), None),
    (("heels lifting", "squat"), None),
    # another exercise's code does not leak across
    (("knee_valgus", "lunge"), None),
]


def main():
    failed = 0
    for (error_type, exercise), expected in CASES:
        r = resolve(error_type, exercise)
        got = r["code"] if r["known"] else None
        if got != expected:
            failed += 1
            print(f"FAIL  resolve({error_type!r}, {exercise!r}) -> {got!r}, expected {expected!r}")
    # every legacy target must be a real rule of that exercise
    for ex, codes in LEGACY_CODES.items():
        for old, new in codes.items():
            if new not in ERROR_TAXONOMY[ex]:
                failed += 1
                print(f"FAIL  LEGACY_CODES[{ex!r}][{old!r}] -> {new!r} is not a rule of {ex}")
    print(f"{len(CASES) - failed}/{len(CASES)} passed" if not failed else f"{failed} failure(s)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
