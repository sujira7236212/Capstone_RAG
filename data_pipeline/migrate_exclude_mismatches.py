"""One-off migration: retroactively apply the Step 2 exercise-mismatch check to
curated_data/*.json files that were curated before the check existed.

Confirmed real case this fixes: a bicep-curl source window got classified by the
curator as exercise_type="Deadlift and Alpine Skiing" but was still written into
curated_data/bicep-curl/..._curated.json. ingest.py tags all items from a file with
the folder's exercise_id, so this content would be retrievable under bicep-curl
queries. This script moves such windows out to excluded_from_kb/ without calling the
LLM again (no re-curation cost), so re-running ingest.py picks up clean data.

Run this BEFORE re-ingesting into a fresh collection.
"""
import json
import os

from curator import is_exercise_mismatch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURATED_DIR = os.path.join(PROJECT_ROOT, "curated_data")
EXCLUDED_DIR = os.path.join(PROJECT_ROOT, "excluded_from_kb")


def migrate():
    if not os.path.exists(CURATED_DIR):
        print(f"Error: {CURATED_DIR} not found.")
        return

    total_files_touched = 0
    total_windows_excluded = 0

    for root, _dirs, files in os.walk(CURATED_DIR):
        for file in files:
            if not file.endswith(".json"):
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(root, CURATED_DIR)
            folder_exercise_id = "general" if rel_path == "." else rel_path.split(os.sep)[0]

            with open(file_path, "r", encoding="utf-8") as f:
                items = json.load(f)

            kept, mismatched = [], []
            for item in items:
                extracted_type = item.get("exercise_type", "")
                source_label = item.get("source", file_path)
                if is_exercise_mismatch(folder_exercise_id, extracted_type, source_label):
                    mismatched.append(item)
                else:
                    kept.append(item)

            if not mismatched:
                continue

            total_files_touched += 1
            total_windows_excluded += len(mismatched)

            if kept:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(kept, f, indent=2, ensure_ascii=False)
                print(f"Rewrote {file_path}: kept {len(kept)}, excluded {len(mismatched)}")
            else:
                os.remove(file_path)
                print(f"Removed {file_path}: all {len(mismatched)} window(s) were mismatched")

            excluded_dir = os.path.join(EXCLUDED_DIR, rel_path)
            os.makedirs(excluded_dir, exist_ok=True)
            filename_without_ext = os.path.splitext(file)[0]
            excluded_path = os.path.join(excluded_dir, f"{filename_without_ext}_mismatch.json")

            existing = []
            if os.path.exists(excluded_path):
                with open(excluded_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)

            with open(excluded_path, "w", encoding="utf-8") as f:
                json.dump(existing + mismatched, f, indent=2, ensure_ascii=False)
            print(f"  -> wrote {len(mismatched)} mismatched window(s) to {excluded_path}")

    print(f"\nDone. Touched {total_files_touched} curated file(s), excluded {total_windows_excluded} window(s) total.")


if __name__ == "__main__":
    migrate()
