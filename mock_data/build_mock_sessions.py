"""Build the KB v6 mock sessions: one file per exercise, mock_data/mock_sessions_<exercise>.json
(docs/progress/t3_curation_status.md section 8.1 step 6). The app makes the user pick one exercise
first, so each file holds that exercise only: one session per rule (that fault alone), one
mixed session (several faults in one set, to test priority) and one clean session.

Session format = what system 1 sends (user, 2026-10-02/03):
- error_type is the rule key in error_taxonomy.py, never a display name; the same keys go in
  historical_comparison.previous_common_errors.
- state_occurred is the FSM state (docs/rules/system1/RULES_AND_FSM_CONDENSED.md): CONCENTRIC,
  INFLECTION or ECCENTRIC. NOTE the spec names CONCENTRIC "going down" (the counting angle
  falling), which is the eccentric muscle phase in squat, lunge and push-up - the prompt has
  to explain the states, not this file.
- status "completed" = counted rep (REP_COMPLETED, re-descend included); "abort" = an
  attempt that returned before the count bar (REP_ABANDONED), not counted by the FSM. An
  abort with a fault is an incorrect rep (user, 2026-10-03), so the summary counts every
  entry: total_reps = correct_reps + incorrect_reps, overall_score over all entries.
  Assumption until system 1 confirms: an abort is an entry in reps_detail and rep_no runs
  over all entries.

check() enforces the spec so a mock never shows something system 1 cannot produce:
- rep-scope rules are checked once at the end of an attempt: ECCENTRIC on a completed rep,
  CONCENTRIC on an abort. Frame rules fire during the attempt; an abort never reached
  INFLECTION, so its frame rules are CONCENTRIC.
- shallow_lunge and partial_pushup fire only on aborts (their bar is the count bar);
  excessive_front_knee_flexion, straight_back_leg, knee_valgus and knee_varus need the rep
  to reach depth, so only on completed reps; knee_valgus/knee_varus and
  shallow_lunge/excessive_front_knee_flexion never share a rep.
- errors on a rep are listed in rule priority order (show one, record all).

    python mock_data/build_mock_sessions.py          # check + write the 4 files
    python mock_data/build_mock_sessions.py --check  # check only
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from error_taxonomy import ERROR_TAXONOMY  # noqa: E402

DATE, PREVIOUS_DATE = "2026-10-03", "2026-10-02"
NAMES = {"squat": "Squat", "push-up": "Push-up", "lunge": "Lunge", "bicep-curl": "Bicep Curl"}
PREFIX = {"squat": "SQ", "push-up": "PU", "lunge": "LU", "bicep-curl": "BC"}

FRAME_RULES = {"rounded_back", "hip_sag_or_pike", "forward_trunk_lean", "elbow_flare"}
ABORT_ONLY = {"shallow_lunge", "partial_pushup"}
COMPLETED_ONLY = {"excessive_front_knee_flexion", "straight_back_leg", "knee_valgus", "knee_varus"}
EXCLUSIVE = [{"knee_valgus", "knee_varus"}, {"shallow_lunge", "excessive_front_knee_flexion"}]

C, I, E = "CONCENTRIC", "INFLECTION", "ECCENTRIC"


def ok(score):
    """A clean counted rep."""
    return ("completed", score, [])


def bad(score, *errors):
    """A counted rep with faults; each error is a rule key (rep rule, state set by check
    rules) or a (key, state) pair for a frame rule."""
    return ("completed", score, list(errors))


def abort(score, *errors):
    return ("abort", score, list(errors))


# (label, previous session: (score, correct, incorrect, common errors), entries)
SESSIONS = {
    "squat": [
        ("partial_squat", (72, 5, 5, ["partial_squat", "rounded_back"]), [
            ok(90), ok(88), bad(64, "partial_squat"), ok(86), ok(85),
            bad(61, "partial_squat"), ok(84), bad(58, "partial_squat"),
            abort(45, "partial_squat"), bad(55, "partial_squat")]),
        ("knee_valgus", (74, 6, 4, ["knee_valgus"]), [
            ok(91), ok(89), ok(90), bad(62, "knee_valgus"), ok(87),
            bad(60, "knee_valgus"), ok(86), bad(57, "knee_valgus"), ok(84), bad(56, "knee_valgus")]),
        ("knee_varus", (75, 6, 4, ["knee_varus"]), [
            ok(90), bad(63, "knee_varus"), ok(89), ok(88), bad(61, "knee_varus"),
            ok(87), ok(86), bad(60, "knee_varus"), ok(85), bad(59, "knee_varus")]),
        ("rounded_back", (73, 6, 4, ["rounded_back", "partial_squat"]), [
            ok(92), ok(90), bad(63, ("rounded_back", I)), ok(88), ok(87),
            bad(60, ("rounded_back", I)), ok(85), bad(58, ("rounded_back", C)), ok(84),
            bad(55, ("rounded_back", I))]),
        ("mixed", (70, 4, 6, ["knee_valgus", "rounded_back"]), [
            ok(89), bad(62, "knee_valgus"), ok(87), bad(55, "partial_squat", ("rounded_back", C)),
            ok(85), bad(57, "knee_valgus", ("rounded_back", I)), ok(83), bad(60, "partial_squat"),
            abort(42, "partial_squat", ("rounded_back", C)), bad(54, "knee_valgus", ("rounded_back", I))]),
        ("clean", (76, 6, 4, ["partial_squat", "knee_valgus"]), [
            ok(92), ok(90), ok(91), ok(89), ok(90), ok(88), ok(89), ok(87), ok(88), ok(86)]),
    ],
    "push-up": [
        ("hip_sag_or_pike", (73, 6, 4, ["hip_sag_or_pike"]), [
            ok(91), ok(90), ok(88), bad(63, ("hip_sag_or_pike", C)), ok(87),
            bad(60, ("hip_sag_or_pike", I)), ok(85), bad(58, ("hip_sag_or_pike", I)), ok(84),
            bad(56, ("hip_sag_or_pike", C))]),
        ("partial_pushup", (74, 7, 3, ["partial_pushup"]), [
            ok(90), ok(89), ok(88), ok(87), abort(50, "partial_pushup"), ok(85),
            abort(48, "partial_pushup"), ok(84), abort(45, "partial_pushup"), ok(83)]),
        ("mixed", (71, 5, 5, ["hip_sag_or_pike", "partial_pushup"]), [
            ok(89), ok(88), bad(61, ("hip_sag_or_pike", I)), ok(86),
            abort(46, ("hip_sag_or_pike", C), "partial_pushup"), bad(58, ("hip_sag_or_pike", C)),
            ok(84), abort(44, "partial_pushup"), bad(55, ("hip_sag_or_pike", I)),
            abort(40, ("hip_sag_or_pike", C), "partial_pushup")]),
        ("clean", (75, 6, 4, ["hip_sag_or_pike", "partial_pushup"]), [
            ok(91), ok(90), ok(89), ok(90), ok(88), ok(89), ok(87), ok(88), ok(86), ok(87)]),
    ],
    "lunge": [
        ("shallow_lunge", (70, 6, 4, ["shallow_lunge"]), [
            ok(89), ok(88), abort(52, "shallow_lunge"), ok(86), abort(50, "shallow_lunge"),
            ok(85), abort(47, "shallow_lunge"), ok(84), abort(45, "shallow_lunge"), ok(83)]),
        ("excessive_front_knee_flexion", (74, 6, 4, ["excessive_front_knee_flexion"]), [
            ok(90), bad(64, "excessive_front_knee_flexion"), ok(89), ok(88),
            bad(61, "excessive_front_knee_flexion"), ok(87), bad(60, "excessive_front_knee_flexion"),
            ok(85), ok(86), bad(58, "excessive_front_knee_flexion")]),
        ("forward_trunk_lean", (73, 6, 4, ["forward_trunk_lean"]), [
            ok(91), ok(89), bad(63, ("forward_trunk_lean", C)), ok(88), ok(87),
            bad(60, ("forward_trunk_lean", I)), ok(85), bad(59, ("forward_trunk_lean", I)), ok(84),
            bad(56, ("forward_trunk_lean", C))]),
        ("straight_back_leg", (72, 6, 4, ["straight_back_leg", "shallow_lunge"]), [
            ok(90), ok(89), bad(62, "straight_back_leg"), ok(88), bad(60, "straight_back_leg"),
            ok(86), ok(87), bad(58, "straight_back_leg"), ok(85), bad(57, "straight_back_leg")]),
        ("mixed", (69, 4, 6, ["forward_trunk_lean", "straight_back_leg"]), [
            ok(88), bad(60, ("forward_trunk_lean", C), "straight_back_leg"), ok(86),
            abort(46, "shallow_lunge"), bad(62, "excessive_front_knee_flexion"), ok(84),
            bad(57, ("forward_trunk_lean", I), "straight_back_leg"),
            abort(43, "shallow_lunge", ("forward_trunk_lean", C)), ok(83), bad(59, "straight_back_leg")]),
        ("clean", (75, 6, 4, ["forward_trunk_lean", "shallow_lunge"]), [
            ok(91), ok(90), ok(89), ok(90), ok(88), ok(89), ok(87), ok(88), ok(87), ok(86)]),
    ],
    "bicep-curl": [
        ("elbow_flare", (74, 6, 4, ["elbow_flare"]), [
            ok(92), ok(90), bad(63, ("elbow_flare", C)), ok(89), ok(88),
            bad(61, ("elbow_flare", C)), ok(86), bad(59, ("elbow_flare", E)), ok(85),
            bad(56, ("elbow_flare", C))]),
        ("partial_curl", (73, 6, 4, ["partial_curl"]), [
            ok(91), ok(90), ok(89), bad(64, "partial_curl"), ok(87), bad(62, "partial_curl"),
            ok(86), bad(60, "partial_curl"), abort(48, "partial_curl"), ok(84)]),
        ("mixed", (70, 5, 5, ["elbow_flare", "partial_curl"]), [
            ok(90), bad(62, ("elbow_flare", C)), ok(88), bad(61, "partial_curl"), ok(86),
            abort(44, ("elbow_flare", C), "partial_curl"), bad(58, ("elbow_flare", C), "partial_curl"),
            ok(84), bad(57, ("elbow_flare", E)), ok(83)]),
        ("clean", (76, 6, 4, ["elbow_flare", "partial_curl"]), [
            ok(92), ok(91), ok(90), ok(90), ok(89), ok(89), ok(88), ok(88), ok(87), ok(87)]),
    ],
}


def rep_errors(exercise, status, errors):
    """[(key, state)] with rep-rule states filled in, in priority order."""
    priority = list(ERROR_TAXONOMY[exercise])
    out = []
    for e in errors:
        key, state = (e, None) if isinstance(e, str) else e
        if key in FRAME_RULES:
            if state is None:
                raise ValueError(f"{exercise}: frame rule {key} needs a state")
        else:
            if state is not None:
                raise ValueError(f"{exercise}: rep rule {key} gets its state from the status")
            state = E if status == "completed" else C
        out.append((key, state))
    return sorted(out, key=lambda ks: priority.index(ks[0]))


def check(exercise, label, entries):
    where = f"{exercise}/{label}"
    rules = set(ERROR_TAXONOMY[exercise])
    if len(entries) != 10:
        raise ValueError(f"{where}: {len(entries)} entries, want 10")
    for n, (status, _, errors) in enumerate(entries, 1):
        keys = {e if isinstance(e, str) else e[0] for e in errors}
        if keys - rules:
            raise ValueError(f"{where} #{n}: not a {exercise} rule: {keys - rules}")
        for pair in EXCLUSIVE:
            if pair <= keys:
                raise ValueError(f"{where} #{n}: {sorted(pair)} never share a rep")
        if status == "completed" and keys & ABORT_ONLY:
            raise ValueError(f"{where} #{n}: {keys & ABORT_ONLY} fire only on an abort")
        if status == "abort":
            if keys & COMPLETED_ONLY:
                raise ValueError(f"{where} #{n}: {keys & COMPLETED_ONLY} need the rep to reach depth")
            if not errors:
                raise ValueError(f"{where} #{n}: an abort in a mock should say why")
        for key, state in rep_errors(exercise, status, errors):
            if status == "abort" and state != C:
                raise ValueError(f"{where} #{n}: an abort never left CONCENTRIC ({key} {state})")
    if label in rules:
        seen = {e if isinstance(e, str) else e[0] for _, _, errs in entries for e in errs}
        if seen != {label}:
            raise ValueError(f"{where}: single-fault session shows {sorted(seen)}")


def build(exercise, n, label, previous, entries):
    reps = []
    for rep_no, (status, score, errors) in enumerate(entries, 1):
        reps.append({
            "rep_no": rep_no,
            "status": status,
            "similarity_scores_percent": {"overall": score},
            "errors": [{"error_type": k, "state_occurred": s} for k, s in rep_errors(exercise, status, errors)],
        })
    # An abort with a fault is an incorrect rep (user, 2026-10-03), so the summary counts
    # every entry: total = correct + incorrect, score averaged over all of them.
    correct = sum(1 for r in reps if r["status"] == "completed" and not r["errors"])
    p_score, p_correct, p_incorrect, p_errors = previous
    return {
        "session_id": f"{PREFIX[exercise]}-{DATE.replace('-', '')}-{n:03d}",
        "exercise_id": exercise,
        "name": NAMES[exercise],
        "report_label": f"{NAMES[exercise]} — {label}",
        "date": DATE,
        "historical_comparison": {
            "previous_session_date": PREVIOUS_DATE,
            "previous_overall_score": p_score,
            "previous_correct_reps": p_correct,
            "previous_incorrect_reps": p_incorrect,
            "previous_common_errors": p_errors,
        },
        "summary": {
            "total_reps": len(reps),
            "correct_reps": correct,
            "incorrect_reps": len(reps) - correct,
            "overall_score": round(sum(r["similarity_scores_percent"]["overall"] for r in reps) / len(reps)),
        },
        "reps_detail": reps,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    args = ap.parse_args()
    if set(SESSIONS) != set(ERROR_TAXONOMY):
        sys.exit(f"exercises differ from error_taxonomy: {sorted(SESSIONS)} vs {sorted(ERROR_TAXONOMY)}")
    for exercise, sessions in SESSIONS.items():
        labels = [s[0] for s in sessions]
        missing = set(ERROR_TAXONOMY[exercise]) - set(labels)
        if missing or "mixed" not in labels or "clean" not in labels:
            sys.exit(f"{exercise}: needs one session per rule + mixed + clean (missing {sorted(missing)})")
        for label, previous, entries in sessions:
            check(exercise, label, entries)
            if previous[1] + previous[2] != len(entries):
                sys.exit(f"{exercise}/{label}: previous correct + incorrect != {len(entries)}")
            for key in previous[3]:
                if key not in ERROR_TAXONOMY[exercise]:
                    sys.exit(f"{exercise}/{label}: previous_common_errors has {key!r}")
        out = [build(exercise, n, *s) for n, s in enumerate(sessions, 1)]
        path = os.path.join(HERE, f"mock_sessions_{exercise}.json")
        print(f"{exercise}: {len(out)} sessions OK" + ("" if args.check else f" -> {os.path.relpath(path)}"))
        for s in out:
            print(f"   {s['session_id']} {s['report_label']:<45} {s['summary']} "
                  f"abort={sum(r['status'] == 'abort' for r in s['reps_detail'])}")
        if not args.check:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
                f.write("\n")


if __name__ == "__main__":
    main()
