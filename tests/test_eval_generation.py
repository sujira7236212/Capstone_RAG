"""Guards for the two ways this metric has already been measured wrong by hand.

    python tests/test_eval_generation.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval"))

import eval_generation as eg

REPORT = """# Feedback Comparison: RAG vs NO-RAG

## Exercise: Squat

### Retrieval metrics
| error_type | query sent | mistake best / kept |
|---|---|---|
| Butt wink | posterior pelvic tilt | 0.120 / 3 |

### Retrieved KB Context (RAG run)
```text
[mistake | re: Butt wink | source: kb]
Allowing the spine to flex during a squat compromises back curvature.
```

### WITH RAG
### Progress Tracking
Your score climbed from 73 to 79.

---

### Error Breakdown
* Allowing the spine to flex during a squat compromises back curvature.
* Your hip extensors take the load, and a lordotic lumbar position helps.

### Next Session Plan
1. Brace harder.

### WITHOUT RAG
### Progress Tracking
Nice work.

---

### Next Session Plan
1. Keep it up.

---
"""

SPEC = {
    "needs_gloss": ["hip extensor", "lordotic", "posterior pelvic tilt"],
    "allowed_bare": ["hip", "hips", "lower back"],
    "gloss_markers": [r"\(", "—", r"\bmeaning\b"],
}
MARKERS = [eg.re.compile(m, eg.re.I) for m in SPEC["gloss_markers"]]


def check(label, got, want):
    assert got == want, f"{label}: got {got!r}, want {want!r}"
    print(f"  ok  {label}")


def test_parse_keeps_internal_headings_and_rules():
    """The feedback contains its own `### ` headings and `---` rules. Ending a section at
    either one truncates the answer at 'Progress Tracking' and halves every count taken
    from it - the original by-hand run of this metric under-counted v9 as 10, not 18."""
    block = eg.parse_report(REPORT)[0]
    check("exercise name", block["exercise"], "Squat")
    with_rag = block["WITH RAG"]
    assert "Error Breakdown" in with_rag, "section was cut at its first internal ### heading"
    assert "Brace harder" in with_rag, "section was cut at an internal --- rule"
    assert "WITHOUT RAG" not in with_rag, "section ran past its own end"
    check("both sides parsed", sorted(k for k in block if k in eg.SIDES), ["WITH RAG", "WITHOUT RAG"])
    check("error name read", eg.error_names(block["Retrieval metrics"]), ["Butt wink"])


def test_allowed_term_does_not_shield_jargon():
    """'hip' is allowed bare; 'hip extensors' is not. Consuming the allowed word first
    hides the phrase that contains it."""
    vocab = eg.build_vocab(SPEC)
    hits = eg.unglossed_jargon("Your hip extensors take the load.", vocab, MARKERS, 120)
    check("hip extensor flagged", [t for t, _ in hits], ["hip extensor"])
    check("bare hip allowed", eg.unglossed_jargon("Drive your hips back.", vocab, MARKERS, 120), [])


def test_gloss_detection():
    vocab = eg.build_vocab(SPEC)
    glossed = "This is a posterior pelvic tilt, meaning your tailbone tucks under."
    check("glossed term not flagged", eg.unglossed_jargon(glossed, vocab, MARKERS, 120), [])
    bare = "Keep a neutral, lordotic lumbar position."
    check("bare term flagged", [t for t, _ in eg.unglossed_jargon(bare, vocab, MARKERS, 120)],
          ["lordotic"])
    far = "Keep a lordotic position" + " and stay tight" * 12 + " (arched lower back)."
    check("gloss beyond the window not credited",
          [t for t, _ in eg.unglossed_jargon(far, vocab, MARKERS, 40)], ["lordotic"])


def test_shared_spans():
    block = eg.parse_report(REPORT)[0]
    answer = eg.word_tokens(block["WITH RAG"])
    context = eg.word_tokens(block["Retrieved KB Context"])
    spans = eg.shared_spans(answer, context, 6)
    check("longest copied run", spans[0],
          (11, "allowing the spine to flex during a squat compromises back curvature"))
    check("no-RAG side is the floor",
          eg.shared_spans(eg.word_tokens(block["WITHOUT RAG"]), context, 6), [])
    check("threshold respected", eg.shared_spans(answer, context, 12), [])


def test_multi_sample_report():
    """`test_rag_compare.py --samples N` numbers the headings. Every sample must be kept -
    storing sections by heading name alone would silently score only the last one."""
    multi = REPORT.replace("### WITH RAG\n", "### WITH RAG (sample 1/2)\nFirst answer.\n\n"
                                              "### WITH RAG (sample 2/2)\n")
    block = eg.parse_report(multi)[0]
    check("both samples kept", len(block["samples"]["WITH RAG"]), 2)
    check("first sample is block[side]", block["WITH RAG"], "First answer.")
    assert "Brace harder" in block["samples"]["WITH RAG"][1], "second sample truncated"
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
        tf.write(multi)
    try:
        rows = eg.score_report(tf.name, SPEC, MARKERS, 120, 6, {})
    finally:
        os.remove(tf.name)
    check("one row per sample", [r["side"] for r in rows],
          ["WITH RAG #1", "WITH RAG #2", "WITHOUT RAG"])
    check("jargon counted per sample", [len(r["hits"]) for r in rows], [0, 2, 0])


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            print(name)
            fn()
    print("\nall passed")
