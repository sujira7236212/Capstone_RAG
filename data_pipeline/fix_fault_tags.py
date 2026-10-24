"""Apply curator.normalize_fault_tags() to knowledge curated before the rule existed: the
curated_data_v5/**/*.json files (what the next ingest reads) and, optionally, the live
rows of a pgvector collection (what retrieval reads today).

18 v5 items were tagged "partial_squat" / "knee_valgus" / "partial range_of_motion", which
the retrieval tag filter (LIKE '%|<code>|%') never matches - ablation step R0
(docs/plans/rag_v2_ablation_plan.md). Only tag metadata changes: applies_to_fault, fault_tags
and window_applies_to_fault. The text is untouched, so the embedding is kept as is.

The row id DOES change. ingest.py derives it from md5(collection :: text + str(metadata))
and skips ids it already has, so a patched row left under its old id would be embedded a
second time the next time curated_data_v5 is ingested into the same collection. Each
patched row is moved to the id that ingest would now compute from the patched file, and
the run ends by checking that every document in the folder maps onto an existing row.
Originals (id, document, cmetadata) are written to data_pipeline/backups/ before any write.

    python data_pipeline/fix_fault_tags.py --dry-run --collection kb_gemini_curated_v5
    python data_pipeline/fix_fault_tags.py                                     # files only
    python data_pipeline/fix_fault_tags.py --collection kb_gemini_curated_v5   # + live rows
"""
import argparse
import contextlib
import glob
import hashlib
import io
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curator import normalize_fault_tags

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
ITEM_FIELDS = ("core_principles", "common_mistakes", "specific_findings", "consequences")
TAG_FIELDS = ("applies_to_fault", "fault_tags", "window_applies_to_fault")


def fix_curated_files(folder, dry_run):
    changed = []
    for path in sorted(glob.glob(os.path.join(folder, "**", "*.json"), recursive=True)):
        exercise_id = os.path.relpath(path, folder).split(os.sep)[0]
        with open(path, encoding="utf-8") as f:
            windows = json.load(f)
        touched = False
        for window in windows:
            for field in ITEM_FIELDS:
                for item in window.get(field) or []:
                    if not isinstance(item, dict):
                        continue
                    before = item.get("applies_to_fault") or []
                    after = normalize_fault_tags(before, exercise_id)
                    if after != before:
                        changed.append((os.path.relpath(path, PROJECT_ROOT), item.get("text", ""), before, after))
                        item["applies_to_fault"] = after
                        touched = True
            before = window.get("applies_to_fault") or []
            after = normalize_fault_tags(before, exercise_id)
            if after != before:
                window["applies_to_fault"] = after
                touched = True
        if touched and not dry_run:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(windows, f, indent=2, ensure_ascii=False)
    return changed


def _normalized_meta(meta):
    """The metadata ingest.py would build if the item's tags had been canonical."""
    exercise_id = meta["exercise_id"]
    tags = normalize_fault_tags(meta.get("applies_to_fault"), exercise_id)
    return {**meta,
            "applies_to_fault": tags,
            "fault_tags": ("|" + "|".join(tags) + "|") if tags else "",
            "window_applies_to_fault": normalize_fault_tags(meta.get("window_applies_to_fault"), exercise_id)}


def _ingest_docs(folder):
    import ingest
    with contextlib.redirect_stdout(io.StringIO()):  # ingest prints one line per file
        return ingest.load_documents_from_folder(folder)


def _ingest_id(collection, doc_text, meta):
    # Same formula as ingest.py main(); str(meta) depends on key order, which is why the
    # id is computed from the loader's dict and never from the (key-sorted) jsonb column.
    return hashlib.md5((collection + "::" + doc_text + str(meta)).encode("utf-8")).hexdigest()


def _key(text, meta):
    return (text, meta.get("exercise_id"), meta.get("source"), meta.get("item_kind"))


def _engine():
    import embedding_config
    from dotenv import load_dotenv
    from sqlalchemy import create_engine

    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    return create_engine(embedding_config.get_connection())


def fix_collection(collection, folder, dry_run):
    from sqlalchemy import text

    # Target id + metadata for every document, from the folder with tags normalised in
    # memory - so this works whether or not fix_curated_files() has run yet.
    target = {}
    for doc in _ingest_docs(folder):
        meta = _normalized_meta(doc.metadata)
        target.setdefault(_key(doc.page_content, meta), []).append(
            (_ingest_id(collection, doc.page_content, meta), meta))

    engine = _engine()
    select = text("""
        SELECT e.id, e.document, e.cmetadata
        FROM langchain_pg_embedding e JOIN langchain_pg_collection c ON e.collection_id = c.uuid
        WHERE c.name = :name
    """)
    with engine.connect() as conn:
        rows = conn.execute(select, {"name": collection}).fetchall()
        existing = {r[0] for r in conn.execute(text("SELECT id FROM langchain_pg_embedding"))}

    todo = []
    for row_id, document, meta in rows:
        fixed = _normalized_meta(meta)
        if all(fixed.get(k) == meta.get(k) for k in TAG_FIELDS):
            continue
        matches = target.get(_key(document, fixed), [])
        if len(matches) != 1:
            raise SystemExit(f"row {row_id}: {len(matches)} documents in {folder} match it - "
                             "cannot tell which id ingest would give it; nothing written")
        new_id, new_meta = matches[0]
        if new_id != row_id and new_id in existing:
            raise SystemExit(f"row {row_id}: target id {new_id} already exists; nothing written")
        todo.append((row_id, new_id, document, meta, new_meta))
    if dry_run or not todo:
        return todo

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(BACKUP_DIR, f"{collection}_fault_tags_{stamp}.json")
    with open(backup, "w", encoding="utf-8") as f:
        json.dump([{"id": old, "document": d, "cmetadata": m} for old, _, d, m, _ in todo],
                  f, indent=2, ensure_ascii=False)
    print(f"backup: {backup}")

    update = text("""
        UPDATE langchain_pg_embedding
        SET id = :new_id, cmetadata = CAST(:meta AS jsonb)
        WHERE id = :old_id
    """)
    with engine.begin() as conn:
        for old, new, _, _, new_meta in todo:
            conn.execute(update, {"new_id": new, "meta": json.dumps(new_meta, ensure_ascii=False), "old_id": old})
    return todo


def verify_ingest_ids(collection, folder):
    """Every document in the folder must already be a row: a re-ingest would then add nothing."""
    from sqlalchemy import text

    ids = {_ingest_id(collection, d.page_content, d.metadata) for d in _ingest_docs(folder)}
    with _engine().connect() as conn:
        db = {r[0] for r in conn.execute(text("""
            SELECT e.id FROM langchain_pg_embedding e JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = :name"""), {"name": collection})}
    return len(ids), len(db), len(ids - db), len(db - ids)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-folder", default=os.path.join(PROJECT_ROOT, "curated_data_v5"),
                    help="curated JSON folder the collection was ingested from (default: curated_data_v5)")
    ap.add_argument("--collection", help="also patch the live rows of this pgvector collection")
    ap.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    args = ap.parse_args()

    changed = fix_curated_files(args.data_folder, args.dry_run)
    print(f"{os.path.relpath(args.data_folder, PROJECT_ROOT)}: {len(changed)} item(s) "
          f"{'would change' if args.dry_run else 'changed'}")
    for path, item_text, before, after in changed:
        print(f"  {path}\n    {item_text[:90]}\n    - {before}\n    + {after}")

    if args.collection:
        todo = fix_collection(args.collection, args.data_folder, args.dry_run)
        print(f"\n{args.collection}: {len(todo)} row(s) {'would change' if args.dry_run else 'retagged'}")
        for old, new, _, meta, new_meta in todo:
            print(f"  {old[:8]} -> {new[:8]}  {meta.get('fault_tags')!r} -> {new_meta['fault_tags']!r}")
        if not args.dry_run:
            docs, rows, missing, extra = verify_ingest_ids(args.collection, args.data_folder)
            print(f"\nre-ingest check: {docs} documents, {rows} rows, {missing} would be re-embedded, "
                  f"{extra} rows with no document")
            if missing or extra:
                sys.exit(1)


if __name__ == "__main__":
    main()
