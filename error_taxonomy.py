"""Canonical mapping: error_type code (from the pose-checking system) -> retrieval query.

Why this exists as a module and not as a fix to mock_sessions.json:
`error_type` is embedded verbatim as the KB search query, so its wording IS the query.
In production those strings come from the angle-threshold team, not from us. Mapping
here means the retrieval query stays stable and testable no matter what wording the
upstream system sends.

The fault set below is the upstream system's rule set as of 2026-09-28: 12 rules over
4 exercises, keyed by the rule name its rep summary records (`partial_squat`,
`knee_valgus`, ...). Source of truth: docs/rules/system1/RULES_AND_FSM_CONDENSED.md from the
upstream team (the "Form rules" section - metric, threshold, cue). The 2026-09-28 sync
renamed 10 of the 12 rules of 2026-09-25 (`knee_depth` -> `partial_squat`, ...) without
changing what they measure; those names are in LEGACY_CODES. The 2026-09-25 set itself
replaced the 10-fault snapshot of 2026-09-11 (docs/rules/error_type_taxonomy.md section 5).
Old codes that still describe one of these rules live in LEGACY_CODES, because
curated_data/ (v4) and curated_data_v5/ still carry them in `applies_to_fault` and older
mock sessions still send them.

Mapping notes against the 2026-09-11 codes:
- squat "butt wink" maps to rounded_back. The rule itself measures trunk lean ("not
  spine curvature"), but expert Ton named its faults rounded back and arched back, and
  the expert answered (2026-10-01, eval/rule_cards.json squat.back_posture oq1/oq2)
  that both forward trunk lean and butt wink count as this fault.
- push-up "hip sag" became hip_sag_or_pike, which also fires on piked hips.
knee_varus and excessive_front_knee_flexion are new; no older code maps onto them.

The upstream sends `error_type` as the rule name itself, never the on-screen cue or a
Thai label (confirmed 2026-10-02), so there is no alias list. resolve() still ignores
the difference between "_" and " " ("knee valgus" finds knee_valgus).

How each `query` was written (Q-spec, docs/plans/eval_v6_plan.md E2): from the definition,
includes and excludes of the rule's card in eval/rule_cards.json, never from the KB and
never from the card's anchors. Each must share fewer than 5 consecutive words with KB
v5 and with the anchors (eval/check_rule_cards.py --queries). Form: one descriptive
sentence of what the lifter does wrong - a bare label ("Elbow flare") lands roughly
equidistant from every chunk of the exercise - with only positive content, because the
embedding cannot read "not X" and would pull X in. What the rule excludes is the
card's job, not the query's.
"""

# Nested by exercise_id because a fault name can recur across exercises (the 2026-09-11
# inventory had "Partial range of motion" on push-up AND bicep-curl); a flat dict keyed
# on the code alone cannot represent that.
#
# inner key: the upstream rule name (matched case-insensitively, "_" == " ")
# value:
#   query       - fault-name phrasing sent to the vector store, and the description the
#                 curator shows the LLM when it tags items (data_pipeline/curator.py)
#   focus_area  - joint/region, for future health-profile cross-referencing
#                 (see docs/plans/future_user_health_profile.md)
#   source      - "expert" (defined by the PT consultant) or "web" (fitness-literature
#                 term - no fixed clinical name, so the query must be descriptive)
ERROR_TAXONOMY = {
    "squat": {
        "partial_squat": {
            "query": "Squatting too shallow: stopping the descent early in a half or quarter squat, so the thighs stay well above parallel and the knees never reach a 90-degree bend",
            "focus_area": "hip",
            "source": "web",
        },
        "knee_valgus": {
            "query": "Knees caving in as the lifter squats: one or both knees collapsing inside the feet while lowering or rising (dynamic knee valgus, medial knee displacement)",
            "focus_area": "knee",
            "source": "expert",
        },
        "knee_varus": {
            "query": "Knees splaying outward during the squat: driving the knees apart until they track outside the little toes in a V shape, often with the toes turned out too much",
            "focus_area": "knee",
            "source": "web",
        },
        "rounded_back": {
            # Ton's fault order first (rounded, then arched), then the forward lean the
            # rule actually measures. Butt wink and the lean both count (oq2, oq1).
            "query": "Losing a straight back during the squat: the upper back hunching, the lower back rounding as the pelvis tucks under at the bottom (butt wink), the lower back over-arching, or the torso tipping too far forward",
            "focus_area": "spine",
            "source": "expert",
        },
    },
    "push-up": {
        "hip_sag_or_pike": {
            "query": "Failing to hold a straight plank line in the push-up: the hips sagging toward the floor with the lower back arching, or the hips piking up toward the ceiling",
            "focus_area": "lumbar spine",
            "source": "expert",
        },
        "partial_pushup": {
            "query": "Push-ups that stop too high: lowering only partway, so the chest stays far from the floor",
            "focus_area": "elbow",
            "source": "web",
        },
    },
    "lunge": {
        "shallow_lunge": {
            # Step length left out until the card's lunge oq1 is answered.
            "query": "Lunging too shallow: dipping only slightly, so the front knee stays far from a 90-degree bend and the front thigh stays well above parallel",
            "focus_area": "knee",
            "source": "web",
        },
        "excessive_front_knee_flexion": {
            # A short step and the knee travelling past the toes are left out until the
            # card's oq1/oq2 for this rule are answered.
            "query": "Sinking too deep in the lunge: the hips dropping below the level of the front knee, so the front knee folds far past 90 degrees and takes extra load",
            "focus_area": "knee",
            "source": "web",
        },
        "forward_trunk_lean": {
            "query": "Leaning the upper body forward during the lunge: bending at the hips so the chest drops toward the front thigh instead of the torso staying upright",
            "focus_area": "spine",
            "source": "web",
        },
        "straight_back_leg": {
            "query": "Keeping the rear leg too straight in the lunge: the back knee failing to bend and drop toward the floor at the bottom, with the body pushed forward onto the front leg",
            "focus_area": "knee",
            "source": "web",
        },
    },
    "bicep-curl": {
        "elbow_flare": {
            "query": "Letting the upper arm move away from the torso while curling: the elbows swinging forward, flaring out to the sides or drifting behind the body",
            "focus_area": "elbow",
            "source": "web",
        },
        "partial_curl": {
            # The 2026-09-11 query was reworded to the curator's own phrasing after an eval
            # on v5 (leakage, docs/plans/eval_v6_plan.md section 1); this one is written from the
            # card. It still avoids the word "elbow", which pulled elbow_flare chunks.
            "query": "Curling through only part of the range: not straightening the arm at the bottom, or not bringing the weight all the way up at the top (half repetitions)",
            "focus_area": "elbow",
            "source": "web",
        },
    },
}

# Superseded codes that describe the same fault as a current rule, per exercise (the
# 2026-09-11 set reused "partial range of motion" for two different rules). Needed
# because curated_data_v5/ and kb_gemini_curated_v5 (2026-09-11 codes) and curated_data/
# v4 (pre-inventory codes) carry them in `applies_to_fault`, older mock sessions send
# them, and data/ subfolders are still named after the 2026-09-25 rules
# (data/lunge/front_knee_too_deep/). Old codes with no current rule behind them are
# deliberately absent, so they fall through to the raw-string fallback and get logged,
# which is the signal we want.
LEGACY_CODES = {
    "squat": {
        "knee_depth": "partial_squat",       # 2026-09-25
        "back_straight": "rounded_back",     # 2026-09-25
        "partial squat": "partial_squat",    # 2026-09-11
        "knee valgus": "knee_valgus",        # 2026-09-11
        "butt wink": "rounded_back",         # 2026-09-11 (expert, 2026-10-01)
        "knees behind toes": "knee_valgus",  # pre-inventory (v4)
    },
    "push-up": {
        "body_alignment": "hip_sag_or_pike",            # 2026-09-25
        "elbow_depth": "partial_pushup",                # 2026-09-25
        "hip sag": "hip_sag_or_pike",                   # 2026-09-11
        "partial range of motion": "partial_pushup",    # 2026-09-11
    },
    "lunge": {
        "front_knee_too_shallow": "shallow_lunge",                 # 2026-09-25
        "front_knee_too_deep": "excessive_front_knee_flexion",     # 2026-09-25
        "torso_upright": "forward_trunk_lean",                     # 2026-09-25
        "back_knee_form": "straight_back_leg",                     # 2026-09-25
        "shallow lunge": "shallow_lunge",                          # 2026-09-11
        "excessive forward trunk lean": "forward_trunk_lean",      # 2026-09-11
        "insufficient back knee flexion": "straight_back_leg",     # 2026-09-11
        "back not straight": "forward_trunk_lean",                 # pre-inventory (v4)
    },
    "bicep-curl": {
        "elbow_away": "elbow_flare",                  # 2026-09-25
        "full_rom": "partial_curl",                   # 2026-09-25
        "elbow flare": "elbow_flare",                 # 2026-09-11
        "partial range of motion": "partial_curl",    # 2026-09-11
        "not full extension": "partial_curl",         # pre-inventory (v4)
    },
}


def _normalise(s: str) -> str:
    return " ".join(str(s or "").lower().split())


def _match_key(s: str) -> str:
    """_normalise() that also treats "_" as a space: "Knee_Valgus" == "knee valgus"."""
    return _normalise(str(s or "").replace("_", " "))


def _exercise_key(exercise: str) -> str:
    """'Bicep Curl' / 'bicep_curl' / 'bicep-curl' -> 'bicep-curl'."""
    return _normalise(exercise).replace("_", "-").replace(" ", "-")


def faults_for_exercise(exercise_id: str) -> dict:
    """{error_type code: query} for every fault the pose checker can raise on this exercise.

    Used by the curator so it can ask the LLM "which of THESE codes does this mistake
    describe?" - a closed list keeps the tag stable and filterable at retrieval time.
    """
    return {code: e["query"] for code, e in ERROR_TAXONOMY.get(_exercise_key(exercise_id), {}).items()}


def all_faults():
    """Yield (exercise_id, code, entry) for every fault, for coverage tooling."""
    for exercise_id, faults in ERROR_TAXONOMY.items():
        for code, entry in faults.items():
            yield exercise_id, code, entry


def _lookup(key: str, exercise_id: str):
    """Match order: code -> query -> legacy code. `key` is a _match_key().
    Returns (exercise_id, code, entry) or None."""
    faults = ERROR_TAXONOMY.get(exercise_id, {})
    for code, entry in faults.items():
        if key == _match_key(code):
            return exercise_id, code, entry
    for code, entry in faults.items():
        if key == _match_key(entry["query"]):
            return exercise_id, code, entry
    for old, code in LEGACY_CODES.get(exercise_id, {}).items():
        if key == _match_key(old):
            return exercise_id, code, faults[code]
    return None


def resolve(error_type: str, exercise_id: str = "") -> dict:
    """Return {query, code, focus_area, source, exercise_id, known, raw} for one error_type.

    `exercise_id` is required to disambiguate codes shared across exercises; when it is
    empty every exercise is searched, first hit wins. Unknown codes fall back to the raw
    string (still better than nothing) and are flagged so the caller can log them - an
    unknown code means the taxonomy needs a new entry, and that is exactly the signal we
    want when the upstream team changes or adds a rule.
    """
    key = _normalise(error_type)
    ex = _exercise_key(exercise_id)
    candidates = [ex] if ex in ERROR_TAXONOMY else list(ERROR_TAXONOMY)
    for candidate in candidates:
        hit = _lookup(_match_key(key), candidate)
        if hit:
            hit_ex, code, entry = hit
            return {**entry, "code": code, "exercise_id": hit_ex, "known": True, "raw": error_type}
    return {
        "query": str(error_type),
        "code": key,
        "focus_area": "",
        "source": "",
        "exercise_id": ex,
        "known": False,
        "raw": error_type,
    }
