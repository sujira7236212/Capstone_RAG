"""Cases for curator.normalize_ocr_degrees(), one per artefact shape found in
kb_local_curated_v4 (docs/kb_quality_assessment.md 7.3) plus the false positive that
the first draft of the fix would have mangled. Plain asserts so it runs without pytest:

    python data_pipeline/test_normalize_ocr_degrees.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curator import normalize_ocr_degrees

CASES = [
    # glued "8" for the degree sign, with the LLM's gloss in parentheses
    ("Flexing at the spine before 1208 (120 degrees) of hip flexion when squatting",
     "Flexing at the spine before 120 degrees of hip flexion when squatting"),
    # "(noted as ...)" annotations
    ("defined as 90 degrees (noted as 900 in text) of elbow flexion.",
     "defined as 90 degrees of elbow flexion."),
    ("between 0 and 135 degrees (noted as 135 /C176) and extension is between 0 and 15 degrees (noted as 15/C176).",
     "between 0 and 135 degrees and extension is between 0 and 15 degrees."),
    # "(text states '...')" annotations
    ("5 squats to 90 degrees (text states '90 8') of flexion while lifting heels off the floor.",
     "5 squats to 90 degrees of flexion while lifting heels off the floor."),
    # raw glyph name, with and without the +/- that also came out as a digit
    ("reported to be 95 6 27/C176 of flexion.", "reported to be 95 ± 27° of flexion."),
    ("A 2/C176 increase in extension", "A 2° increase in extension"),
    ("trunk flexion by up to 4.5/C176 during squatting", "trunk flexion by up to 4.5° during squatting"),
    # must NOT change: "denoted as" is not an OCR note, and a plain number is not an artefact
    ("conditions denoted as SE-SE and SF-SE at 35%, 70%, and 100% exertion levels.",
     "conditions denoted as SE-SE and SF-SE at 35%, 70%, and 100% exertion levels."),
    ("Knee flexion of 108 degrees was recorded.", "Knee flexion of 108 degrees was recorded."),
    ("Squat to 90 degrees of flexion.", "Squat to 90 degrees of flexion."),
]


def main():
    failed = 0
    for raw, expected in CASES:
        got = normalize_ocr_degrees(raw)
        if got != expected:
            failed += 1
            print(f"FAIL\n  in:  {raw}\n  got: {got}\n  exp: {expected}")
    print(f"{len(CASES) - failed}/{len(CASES)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
