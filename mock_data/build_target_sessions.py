"""Extra single-fault mock sessions for the three thin rules (strict/v6b plan, step 2/5
quality layer): shallow_lunge, straight_back_leg, partial_pushup, 5 sessions each.

Same format and the same check() as build_mock_sessions.py. Every session holds one fault
only, so its retrieval queries are exactly those of the existing single-fault session of
that rule (retrieval depends on exercise_id + the set of error_types only) - the contexts
already in compare_output/ can be reused without embedding anything.

The 5 variants differ in what the generator has to reason about, not in the fault:
  late     - fault only in the last reps (fatigue), not in the previous session
  most     - fault on most reps, and it was the previous session's main fault
  improving- fault on 2 reps, previous session had it on many
  early    - fault on the first reps, then clean
  every    - fault on (almost) every rep

    python mock_data/build_target_sessions.py   # check + write mock_sessions_targets_<ex>.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_mock_sessions import abort, bad, build, check, ok  # noqa: E402

FIRST_N = 101  # session numbers 101.. so ids never collide with mock_sessions_<ex>.json


def variants(rule, fault, other):
    """fault(score) -> one faulty entry; other = a different rule of the exercise for history."""
    return [
        (f"{rule} late", (78, 8, 2, [other]), [
            ok(91), ok(90), ok(90), ok(89), ok(88), ok(88), ok(87), fault(61), fault(57), fault(54)]),
        (f"{rule} most", (64, 3, 7, [rule]), [
            fault(60), ok(86), fault(58), fault(59), ok(85), fault(56), fault(57), ok(84), fault(55), fault(53)]),
        (f"{rule} improving", (63, 3, 7, [rule, other]), [
            ok(90), fault(62), ok(89), ok(89), fault(60), ok(88), ok(88), ok(87), ok(87), ok(86)]),
        (f"{rule} early", (74, 6, 4, [other]), [
            fault(58), fault(60), fault(62), ok(85), ok(87), ok(88), ok(88), ok(89), ok(89), ok(88)]),
        (f"{rule} every", (60, 2, 8, [rule]), [
            fault(57), fault(56), fault(58), fault(55), fault(57), fault(54), fault(55), fault(53), fault(52), fault(51)]),
    ]


# shallow_lunge / partial_pushup fire only on an abort, straight_back_leg only on a counted rep
TARGETS = {
    "lunge": (variants("shallow_lunge", lambda s: abort(s - 8, "shallow_lunge"), "forward_trunk_lean")
              + variants("straight_back_leg", lambda s: bad(s, "straight_back_leg"), "forward_trunk_lean")),
    "push-up": variants("partial_pushup", lambda s: abort(s - 8, "partial_pushup"), "hip_sag_or_pike"),
}


def main():
    for exercise, sessions in TARGETS.items():
        out = []
        for n, (label, previous, entries) in enumerate(sessions, FIRST_N):
            rule = label.split()[0]
            check(exercise, rule, entries)  # single-fault check keys on the rule name
            if previous[1] + previous[2] != len(entries):
                sys.exit(f"{exercise}/{label}: previous correct + incorrect != {len(entries)}")
            out.append(build(exercise, n, label, previous, entries))
        path = os.path.join(HERE, f"mock_sessions_targets_{exercise}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"{exercise}: {len(out)} sessions -> {os.path.relpath(path)}")
        for s in out:
            errs = sorted({e["error_type"] for r in s["reps_detail"] for e in r["errors"]})
            print(f"   {s['session_id']} {s['report_label']:<32} {s['summary']} "
                  f"abort={sum(r['status'] == 'abort' for r in s['reps_detail'])} errors={errs} "
                  f"prev={s['historical_comparison']['previous_common_errors']}")


if __name__ == "__main__":
    main()
