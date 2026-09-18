"""Apply curator.normalize_ocr_degrees() to knowledge that was curated before the rule
existed: the curated_data/**/*.json files (what the next ingest reads) and, optionally,
the live rows of a pgvector collection (what retrieval reads today).

Why both: the artefact ("1208", "90 8", "/C176") comes from PDF extraction, so a v5
re-curation from the same PDFs would reproduce it - that is why the rule lives in
curator.py. But v5 is days away and kb_local_curated_v4 is the collection every eval
and A/B report is measured against until then, so its 8 affected rows are patched in
place here rather than left to teach the feedback model to say "1208".

A patched row keeps its id (ingest.py derives ids from the ORIGINAL text, and nothing
else references them) but gets a new embedding: the vector must describe the text the
LLM will actually see, or the distances eval/eval_retrieval.py reports stop meaning
anything. Originals are written to data_pipeline/backups/ before any write.

    python data_pipeline/fix_ocr_degrees.py --dry-run
    python data_pipeline/fix_ocr_degrees.py                                   # curated_data only
    python data_pipeline/fix_ocr_degrees.py --collection kb_local_curated_v4  # + live rows
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curator import normalize_ocr_degrees

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURATED_DIR = os.path.join(PROJECT_ROOT, "curated_data")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
ITEM_FIELDS = ("core_principles", "common_mistakes", "specific_findings")


def fix_curated_files(dry_run):
    changed = []
    for path in sorted(glob.glob(os.path.join(CURATED_DIR, "**", "*.json"), recursive=True)):
        with open(path, encoding="utf-8") as f:
            windows = json.load(f)
        touched = False
        for window in windows:
            for field in ITEM_FIELDS:
                items = window.get(field) or []
                fixed = [normalize_ocr_degrees(i) for i in items]
                for before, after in zip(items, fixed):
                    if before != after:
                        changed.append((os.path.relpath(path, PROJECT_ROOT), before, after))
                        touched = True
                window[field] = fixed
        if touched and not dry_run:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(windows, f, indent=2, ensure_ascii=False)
    return changed


def fix_collection(collection, dry_run):
    from dotenv import load_dotenv
    from sqlalchemy import create_engine, text

    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    engine = create_engine(os.environ["DATABASE_URL_LOCAL"])
    select = text("""
        SELECT e.id, e.document, e.cmetadata
        FROM langchain_pg_embedding e JOIN langchain_pg_collection c ON e.collection_id = c.uuid
        WHERE c.name = :name
    """)
    with engine.connect() as conn:
        rows = conn.execute(select, {"name": collection}).fetchall()

    todo = []
    for row_id, document, meta in rows:
        original = meta.get("text") or document
        fixed = normalize_ocr_degrees(original)
        if fixed != original:
            todo.append((row_id, original, fixed, meta))
    if dry_run or not todo:
        return todo

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(BACKUP_DIR, f"{collection}_ocr_degrees_{stamp}.json")
    with open(backup, "w", encoding="utf-8") as f:
        json.dump([{"id": i, "text": o, "cmetadata": m} for i, o, _, m in todo], f, indent=2, ensure_ascii=False)
    print(f"backup: {backup}")

    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectors = embeddings.embed_documents([fixed for _, _, fixed, _ in todo])

    # Same value bound twice under two names: psycopg infers `document`'s varchar for
    # one use and text for the other and refuses a single parameter with both.
    update = text("""
        UPDATE langchain_pg_embedding
        SET document = :doc,
            cmetadata = jsonb_set(cmetadata, '{text}', to_jsonb(CAST(:doc_meta AS text))),
            embedding = CAST(:vec AS vector)
        WHERE id = :id
    """)
    with engine.begin() as conn:
        for (row_id, _, fixed, _), vec in zip(todo, vectors):
            conn.execute(update, {"doc": fixed, "doc_meta": fixed, "vec": json.dumps(vec), "id": row_id})
    return todo


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--collection", help="also patch the live rows of this pgvector collection")
    ap.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    args = ap.parse_args()

    changed = fix_curated_files(args.dry_run)
    print(f"curated_data: {len(changed)} item(s) {'would change' if args.dry_run else 'changed'}")
    for path, before, after in changed:
        print(f"  {path}\n    - {before}\n    + {after}")

    if args.collection:
        todo = fix_collection(args.collection, args.dry_run)
        print(f"\n{args.collection}: {len(todo)} row(s) {'would change' if args.dry_run else 'patched + re-embedded'}")
        for row_id, before, after, _ in todo:
            print(f"  {row_id[:8]}\n    - {before}\n    + {after}")


if __name__ == "__main__":
    main()
