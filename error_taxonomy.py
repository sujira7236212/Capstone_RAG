"""Canonical mapping: error_type code (from the pose-checking system) -> retrieval query.

Why this exists as a module and not as a fix to mock_sessions.json:
`error_type` is embedded verbatim as the KB search query, so its wording IS the query.
In production those strings come from the angle-threshold team, not from us. Mapping
here means the retrieval query stays stable and testable no matter what wording the
upstream system sends.

The fault set below is the upstream system's rule set as of 2026-09-25: 12 rules over
4 exercises, keyed by the rule name its rep summary records (`knee_depth`,
`knee_valgus`, ...). Source of truth: docs/system1/RULES_AND_FSM_CONDENSED.md from the upstream team
(the "Form rules" section - metric, threshold, cue). It replaced the 10-rule snapshot
of 2026-09-11 (docs/error_type_taxonomy.md section 5), which itself replaced an earlier
guessed set. Old codes that still describe one of these rules live in LEGACY_CODES,
because curated_data/ (v4) and curated_data_v5/ still carry them in `applies_to_fault`
and older mock sessions still send them.

Two of the 2026-09-11 codes did NOT carry over one-to-one:
- squat "butt wink" (lumbar flexion at the bottom) has no rule now. back_straight
  measures trunk tilt from vertical and the spec says outright it is "trunk lean, not
  spine curvature", so "butt wink" is deliberately absent from LEGACY_CODES.
- push-up "hip sag" became body_alignment, which also fires on piked hips.
knee_varus and front_knee_too_deep are new; no older code maps onto them.

The upstream may send either the rule name or the cue it shows on screen ("Push knees
out"), so each cue is also listed in `aliases`; resolve() matches on either, and
ignores the difference between "_" and " " ("knee valgus" finds knee_valgus).

How to word a `query` (measured on kb_local_curated_v4 with all-MiniLM-L6-v2, see
docs/error_type_taxonomy.md section 5): write it the way the curator writes a
common_mistakes item - "Allowing the ...", "Failing to ...", "Squatting too shallow ..."
- not as a clinical label. A bare label is both too far from the right chunk ("Butt
wink" -> 0.601, "Elbow flare" -> 0.438) and, being short, roughly equidistant from
every chunk of that exercise, so it passes the usable-distance bar on unrelated text
("Partial squat" -> 21 "usable" mistakes, best of which is about heels lifting).

The distances above are MiniLM-specific and stale now that embedding_config.DEFAULT_MODE
is "gemini" (docs/kb_quality_assessment.md section 10) - gemini-embedding-2 puts
everything in a much tighter band (raw labels like "Elbow flare" land around 0.40
instead of MiniLM's 0.438, expanded queries around 0.04 instead of 0.057). The
principle held up under re-measurement (expanded beats raw by the same wide margin),
just not these exact numbers - don't cite them as current.
    "Elbow flare"                                          -> 0.438 (nothing usable)
    "Allowing the elbows to flare outward or drift ..."    -> 0.057 (exact chunk)
"""

# Nested by exercise_id because a fault name can recur across exercises (the 2026-09-11
# inventory had "Partial range of motion" on push-up AND bicep-curl); a flat dict keyed
# on the code alone cannot represent that.
#
# inner key: the upstream rule name (matched case-insensitively, "_" == " ")
# value:
#   query       - fault-name phrasing sent to the vector store, and the description the
#                 curator shows the LLM when it tags items (data_pipeline/curator.py)
#   aliases     - other strings the upstream may send; the on-screen cue comes first
#   rule_th     - the 2026-09-11 upstream rule's Thai name, where that rule survived
#   display_th  - Thai fault label for the end user
#   focus_area  - joint/region, for future health-profile cross-referencing
#                 (see docs/future_user_health_profile.md)
#   source      - "expert" (defined by the PT consultant) or "web" (fitness-literature
#                 term - no fixed clinical name, so the query must be descriptive)
#
# A query whose meaning did not change keeps its measured wording from 2026-09-11 (see
# the full_rom note). Only back_straight, body_alignment and elbow_away were reworded to
# the new rule's meaning, and knee_varus / front_knee_too_deep are new.
ERROR_TAXONOMY = {
    "squat": {
        "knee_depth": {
            "query": "Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth",
            "aliases": ["Lower to 90 degrees", "quarter squat"],
            "rule_th": "ความลึกของการย่อ",
            "display_th": "ย่อไม่สุด / สควอทตื้น",
            "focus_area": "hip",
            "source": "web",
        },
        "knee_valgus": {
            "query": "Knee valgus: knees caving inward (medial knee displacement) during the squat",
            "aliases": ["Push knees out"],
            "rule_th": "เข่าไม่เลยปลายเท้า",
            "display_th": "เข่าบิดเข้าด้านใน",
            "focus_area": "knee",
            "source": "expert",
        },
        "knee_varus": {
            "query": "Knee varus: pushing the knees too far outward past the feet, often with the toes turned out, during the squat",
            "aliases": ["Keep knees in line"],
            "rule_th": "",
            "display_th": "เข่าบานออกด้านนอก",
            "focus_area": "knee",
            "source": "web",
        },
        "back_straight": {
            "query": "Excessive forward lean of the trunk during the squat: the torso tilting too far forward instead of staying upright",
            "aliases": ["Keep back straight"],
            "rule_th": "มุมของหลัง",
            "display_th": "ลำตัวโน้มไปข้างหน้ามากเกินไป",
            "focus_area": "trunk",
            "source": "expert",
        },
    },
    "push-up": {
        "body_alignment": {
            "query": "Failing to keep the body in a straight line during the push-up: letting the hips sag or piking the hips up",
            "aliases": ["Body not straight", "sagging hips"],
            "rule_th": "แนวลำตัว",
            "display_th": "ลำตัวไม่ตรง (สะโพกตกหรือโด่ง)",
            "focus_area": "lumbar spine",
            "source": "expert",
        },
        "elbow_depth": {
            "query": "Not lowering deep enough: incomplete elbow flexion, failing to reach 90 degrees during the push-up",
            "aliases": ["Lower Your Chest", "half push-up"],
            "rule_th": "มุมการงอศอก",
            "display_th": "ลงไม่สุด / วิดพื้นครึ่งท่า",
            "focus_area": "elbow",
            "source": "web",
        },
    },
    "lunge": {
        "front_knee_too_shallow": {
            "query": "Shallow lunge: step too short, insufficient front knee flexion, front knee not reaching 90 degrees",
            "aliases": ["Lower your front knee", "insufficient front knee flexion"],
            "rule_th": "มุมเข่าหน้า",
            "display_th": "ก้าวสั้นเกินไป เข่าหน้างอไม่พอ",
            "focus_area": "knee",
            "source": "web",
        },
        "front_knee_too_deep": {
            "query": "Lunging too deep: excessive front knee flexion, the front knee bending well past 90 degrees at the bottom of the lunge",
            "aliases": ["Raise your front knee"],
            "rule_th": "",
            "display_th": "ย่อเข่าหน้าลึกเกินไป",
            "focus_area": "knee",
            "source": "web",
        },
        "torso_upright": {
            "query": "Leaning the torso forward, excessive trunk lean during the lunge",
            "aliases": ["Keep Torso Upright"],
            "rule_th": "มุมลำตัว",
            "display_th": "ก้มตัวไปหน้ามากเกินไป",
            "focus_area": "spine",
            "source": "web",
        },
        "back_knee_form": {
            "query": "Insufficient back knee flexion: rear knee not lowering toward the floor during the lunge",
            "aliases": ["Bend your back knee toward the floor"],
            "rule_th": "มุมเข่าหลัง",
            "display_th": "เข่าหลังงอไม่สุด",
            "focus_area": "knee",
            "source": "web",
        },
    },
    "bicep-curl": {
        "elbow_away": {
            "query": "Allowing the upper arm to swing away from the torso during the curl: the elbows drifting forward, flaring outward or moving back instead of staying at the sides",
            "aliases": ["Keep Elbows at Your Sides", "elbow drift"],
            "rule_th": "การขยับข้อศอกด้านข้าง",
            "display_th": "ศอกไม่แนบลำตัว (กาง / ลอยไปหน้า / ไปหลัง)",
            "focus_area": "elbow",
            "source": "web",
        },
        "full_rom": {
            # Reworded 2026-09-11 after eval/eval_retrieval.py showed the old query
            # ("Partial range of motion: not fully extending or fully flexing the elbow
            # (half rep) during the curl") ranked all six correct chunks (0.35-0.46) BELOW
            # four wrong ones - upper arm stationary 0.27, elbow flare 0.31, momentum 0.34 -
            # so the gate kept 0 correct / 3 wrong. The word "elbow" pulled every
            # elbow-related fault; naming the two end positions the way the curator does
            # ("complete arm extension at the bottom", "full elbow flexion at the top")
            # puts the correct chunks at 0.27-0.33 and the nearest wrong one at 0.31 (#4).
            "query": "Failing to achieve complete arm extension at the bottom of the curl and full elbow flexion at the top: partial repetitions with a limited range of motion",
            "aliases": ["Full range of motion", "half rep"],
            "rule_th": "การเหยียด/งอศอกไม่สุด",
            "display_th": "ยกไม่สุดช่วง",
            "focus_area": "elbow",
            "source": "web",
        },
    },
}

# Superseded codes that describe the same fault as a current rule, per exercise (the
# 2026-09-11 set reused "partial range of motion" for two different rules). Needed
# because curated_data_v5/ and kb_gemini_curated_v5 (2026-09-11 codes) and curated_data/
# v4 (pre-inventory codes) carry them in `applies_to_fault`, and older mock sessions
# send them. Old codes with no current rule behind them are deliberately absent - "butt
# wink" above all (see module docstring) - so they fall through to the raw-string
# fallback and get logged, which is the signal we want.
LEGACY_CODES = {
    "squat": {
        "partial squat": "knee_depth",       # 2026-09-11
        "knee valgus": "knee_valgus",        # 2026-09-11
        "knees behind toes": "knee_valgus",  # pre-inventory (v4)
    },
    "push-up": {
        "hip sag": "body_alignment",                   # 2026-09-11
        "partial range of motion": "elbow_depth",      # 2026-09-11
    },
    "lunge": {
        "shallow lunge": "front_knee_too_shallow",           # 2026-09-11
        "excessive forward trunk lean": "torso_upright",     # 2026-09-11
        "insufficient back knee flexion": "back_knee_form",  # 2026-09-11
        "back not straight": "torso_upright",                # pre-inventory (v4)
    },
    "bicep-curl": {
        "elbow flare": "elbow_away",               # 2026-09-11
        "partial range of motion": "full_rom",     # 2026-09-11
        "not full extension": "full_rom",          # pre-inventory (v4)
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
    """Match order: code -> alias -> query -> legacy code. `key` is a _match_key().
    Returns (exercise_id, code, entry) or None."""
    faults = ERROR_TAXONOMY.get(exercise_id, {})
    for code, entry in faults.items():
        if key == _match_key(code):
            return exercise_id, code, entry
    for code, entry in faults.items():
        if key in (_match_key(a) for a in entry["aliases"]) or key == _match_key(entry["query"]):
            return exercise_id, code, entry
    for old, code in LEGACY_CODES.get(exercise_id, {}).items():
        if key == _match_key(old):
            return exercise_id, code, faults[code]
    return None


def resolve(error_type: str, exercise_id: str = "") -> dict:
    """Return {query, code, display_th, focus_area, exercise_id, known, raw} for one error_type.

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
        "aliases": [],
        "rule_th": "",
        "display_th": str(error_type),
        "focus_area": "",
        "source": "",
        "exercise_id": ex,
        "known": False,
        "raw": error_type,
    }
