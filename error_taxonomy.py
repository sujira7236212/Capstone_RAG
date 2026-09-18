"""Canonical mapping: error_type code (from the pose-checking system) -> retrieval query.

Why this exists as a module and not as a fix to mock_sessions.json:
`error_type` is embedded verbatim as the KB search query, so its wording IS the query.
In production those strings come from the angle-threshold team, not from us. Mapping
here means the retrieval query stays stable and testable no matter what wording the
upstream system sends.

The fault set below is the upstream team's real rule inventory (SeniorProject ·
rule_based/form_rules.py, 10 rules over 4 exercises, snapshot 2026-09-11 - see
docs/error_type_taxonomy.md section 5). It replaced an earlier guessed set of 10 codes;
five of those (heels lifting, using momentum, swinging torso, neck craning, push-up
elbows flaring) have no rule in the real system and were dropped. The ones that do
map to a real rule survive in LEGACY_CODES because curated_data/ and the
kb_local_curated_v4 metadata still carry them in `applies_to_fault`.

The exact string the upstream system emits per rule (Thai rule name? a code? the
English fault name?) is still unconfirmed, which is why every entry also carries
`aliases` and `rule_th`: resolve() matches on any of them.

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

# Nested by exercise_id because the upstream inventory reuses the same fault name for
# two exercises ("Partial range of motion" on push-up AND bicep-curl); a flat dict keyed
# on the code alone cannot represent that.
#
# inner key: error_type as received (matched case-insensitively, whitespace-normalised)
# value:
#   query       - fault-name phrasing sent to the vector store
#   aliases     - other spellings the upstream may send (from the same inventory card)
#   rule_th     - the upstream rule's Thai name (what their form_rules.py calls it)
#   display_th  - Thai fault label for the end user
#   focus_area  - joint/region, for future health-profile cross-referencing
#                 (see docs/future_user_health_profile.md)
#   source      - "expert" (defined by the PT consultant) or "web" (fitness-literature
#                 term - no fixed clinical name, so the query must be descriptive)
ERROR_TAXONOMY = {
    "squat": {
        "butt wink": {
            "query": "Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat",
            "aliases": [],
            "rule_th": "มุมของหลัง",
            "display_th": "หลังค่อม / หลังแอ่น",
            "focus_area": "lumbar spine",
            "source": "expert",
        },
        "knee valgus": {
            "query": "Knee valgus: knees caving inward (medial knee displacement) during the squat",
            "aliases": [],
            "rule_th": "เข่าไม่เลยปลายเท้า",
            "display_th": "เข่าบิดเข้าด้านใน",
            "focus_area": "knee",
            "source": "expert",
        },
        "partial squat": {
            "query": "Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth",
            "aliases": ["quarter squat"],
            "rule_th": "ความลึกของการย่อ",
            "display_th": "ย่อไม่สุด / สควอทตื้น",
            "focus_area": "hip",
            "source": "web",
        },
    },
    "push-up": {
        "hip sag": {
            "query": "Allowing the hips to sag during the push-up",
            "aliases": ["sagging hips"],
            "rule_th": "แนวลำตัว",
            "display_th": "หลังแอ่น",
            "focus_area": "lumbar spine",
            "source": "expert",
        },
        "partial range of motion": {
            "query": "Not lowering deep enough: incomplete elbow flexion, failing to reach 90 degrees during the push-up",
            "aliases": ["half push-up"],
            "rule_th": "มุมการงอศอก",
            "display_th": "ลงไม่สุด / วิดพื้นครึ่งท่า",
            "focus_area": "elbow",
            "source": "web",
        },
    },
    "lunge": {
        "excessive forward trunk lean": {
            "query": "Leaning the torso forward, excessive trunk lean during the lunge",
            "aliases": [],
            "rule_th": "มุมลำตัว",
            "display_th": "ก้มตัวไปหน้ามากเกินไป",
            "focus_area": "spine",
            "source": "web",
        },
        "shallow lunge": {
            "query": "Shallow lunge: step too short, insufficient front knee flexion, front knee not reaching 90 degrees",
            "aliases": ["insufficient front knee flexion"],
            "rule_th": "มุมเข่าหน้า",
            "display_th": "ก้าวสั้นเกินไป เข่าหน้างอไม่พอ",
            "focus_area": "knee",
            "source": "web",
        },
        "insufficient back knee flexion": {
            "query": "Insufficient back knee flexion: rear knee not lowering toward the floor during the lunge",
            "aliases": [],
            "rule_th": "มุมเข่าหลัง",
            "display_th": "เข่าหลังงอไม่สุด",
            "focus_area": "knee",
            "source": "web",
        },
    },
    "bicep-curl": {
        "elbow flare": {
            "query": "Allowing the elbows to flare outward or drift forward away from the body during the curl",
            "aliases": ["elbow drift"],
            "rule_th": "การขยับข้อศอกด้านข้าง",
            "display_th": "ศอกกาง / ศอกลอยไปข้างหน้า",
            "focus_area": "elbow",
            "source": "web",
        },
        "partial range of motion": {
            # Reworded 2026-09-11 after eval/eval_retrieval.py showed the old query
            # ("Partial range of motion: not fully extending or fully flexing the elbow
            # (half rep) during the curl") ranked all six correct chunks (0.35-0.46) BELOW
            # four wrong ones - upper arm stationary 0.27, elbow flare 0.31, momentum 0.34 -
            # so the gate kept 0 correct / 3 wrong. The word "elbow" pulled every
            # elbow-related fault; naming the two end positions the way the curator does
            # ("complete arm extension at the bottom", "full elbow flexion at the top")
            # puts the correct chunks at 0.27-0.33 and the nearest wrong one at 0.31 (#4).
            "query": "Failing to achieve complete arm extension at the bottom of the curl and full elbow flexion at the top: partial repetitions with a limited range of motion",
            "aliases": ["half rep"],
            "rule_th": "การเหยียด/งอศอกไม่สุด",
            "display_th": "ยกไม่สุดช่วง",
            "focus_area": "elbow",
            "source": "web",
        },
    },
}

# Pre-inventory codes that describe the same fault as a real rule. Needed because
# curated_data/*.json and the v4 collection's `applies_to_fault` metadata were tagged
# with these; a future tag-filter channel can translate without re-curating.
# Old codes with no real rule behind them are deliberately absent - they fall through
# to the raw-string fallback and get logged, which is the signal we want.
LEGACY_CODES = {
    "keep back straight": ("squat", "butt wink"),
    "knees behind toes": ("squat", "knee valgus"),
    "back not straight": ("lunge", "excessive forward trunk lean"),
    "not full extension": ("bicep-curl", "partial range of motion"),
}


def _normalise(s: str) -> str:
    return " ".join(str(s or "").lower().split())


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
    """Match order: code -> alias -> query -> legacy code. Returns (exercise_id, code, entry) or None."""
    faults = ERROR_TAXONOMY.get(exercise_id, {})
    if key in faults:
        return exercise_id, key, faults[key]
    for code, entry in faults.items():
        if key in (_normalise(a) for a in entry["aliases"]) or key == _normalise(entry["query"]):
            return exercise_id, code, entry
    legacy = LEGACY_CODES.get(key)
    if legacy and legacy[0] == exercise_id:
        return legacy[0], legacy[1], ERROR_TAXONOMY[legacy[0]][legacy[1]]
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
        hit = _lookup(key, candidate)
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
