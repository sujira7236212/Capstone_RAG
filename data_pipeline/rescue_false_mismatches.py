"""Re-evaluate every excluded_from_kb/**/*_mismatch.json window against the current
is_exercise_mismatch() and move the ones that now pass back into curated_data/.

Why: the original mismatch test was a plain folder-name substring check, which rejected
"Dumbbell Curl" under data/bicep-curl/ (and would reject any synonym the LLM chose).
The check now knows exercise aliases and trusts applies_to_fault tags, so windows that
were binned by the old rule can be recovered without another LLM call.

Idempotent: a window that still mismatches stays where it is; a rescued window is
appended to the matching curated file (created if needed) and removed from the
mismatch file (which is deleted when emptied). Off-topic (_offtopic.json) files are
never touched - those were excluded by hand, not by this rule.
"""
import json
import os

from curator import is_exercise_mismatch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURATED_DIR = os.path.join(PROJECT_ROOT, "curated_data")
EXCLUDED_DIR = os.path.join(PROJECT_ROOT, "excluded_from_kb")


def curated_path_for(mismatch_file: str, rel_dir: str) -> str:
    stem = mismatch_file[: -len("_mismatch.json")]
    if stem.endswith("_curated"):
        stem = stem[: -len("_curated")]
    # urls.txt curations are named *_curated_detailed.json, everything else *_curated.json
    name = f"{stem}.json" if stem.endswith("_detailed") else f"{stem}_curated.json"
    return os.path.join(CURATED_DIR, rel_dir, name)


def rescue():
    rescued_total = 0
    for root, _dirs, files in os.walk(EXCLUDED_DIR):
        rel_dir = os.path.relpath(root, EXCLUDED_DIR)
        folder_exercise_id = "general" if rel_dir == "." else rel_dir.split(os.sep)[0]
        for file in files:
            if not file.endswith("_mismatch.json"):
                continue
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                windows = json.load(f)

            still_bad, rescued = [], []
            for w in windows:
                if is_exercise_mismatch(folder_exercise_id, w.get("exercise_type", ""),
                                        w.get("source", path), w.get("applies_to_fault")):
                    still_bad.append(w)
                else:
                    rescued.append(w)
            if not rescued:
                continue

            target = curated_path_for(file, rel_dir)
            existing = []
            if os.path.exists(target):
                with open(target, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                json.dump(existing + rescued, f, indent=2, ensure_ascii=False)

            if still_bad:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(still_bad, f, indent=2, ensure_ascii=False)
            else:
                os.remove(path)

            rescued_total += len(rescued)
            print(f"[{folder_exercise_id}] {file[:70]}: rescued {len(rescued)} window(s) "
                  f"({', '.join(sorted({w.get('exercise_type','') for w in rescued}))}), {len(still_bad)} still excluded")

    print(f"\nDone. Rescued {rescued_total} window(s).")


if __name__ == "__main__":
    rescue()
