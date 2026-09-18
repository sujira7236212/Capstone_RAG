"""Measure how well a KB collection covers the faults the pose checker can raise.

Reproduces the section-2 table of docs/kb_quality_assessment.md so it can be re-run
every time the KB changes, instead of being an ad-hoc one-off. For every fault in
error_taxonomy.py it reports, per item_kind, how many chunks sit within USABLE_DISTANCE
and the best distance found - the two numbers that decide whether the feedback model
has anything real to cite for that fault.

Query modes (both are printed side by side by default):
    raw       - the fault name exactly as the upstream sends it ("Butt wink"), i.e. what
                retrieval would see with no taxonomy layer at all
    expanded  - the taxonomy's descriptive query for that fault
Comparing the two answers "does the taxonomy layer actually buy anything for this
fault?" without spending a single LLM call.

Usage:
    python kb_coverage.py                              # default: kb_gemini_curated_v4, raw+expanded
    python kb_coverage.py --query-mode expanded

Note: --collection only compares collections in the same database as
embedding_config.get_connection() - local and Gemini collections sit in separate
databases (DATABASE_URL_LOCAL vs DATABASE_URL) and can't be queried in the same run.
Prefix `EMBEDDING_MODE=local` to point this whole script at the local database instead.
"""
import argparse
import os
from collections import Counter

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from error_taxonomy import all_faults
import embedding_config

load_dotenv()

# Same bar as the assessment: beyond this the chunk is no longer about the fault.
USABLE_DISTANCE = 0.40
PROBE_K = 40


def chunk_counts(engine, collection):
    q = text("""
        SELECT e.cmetadata->>'exercise_id', e.cmetadata->>'item_kind', count(*)
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
        WHERE c.name = :name
        GROUP BY 1, 2
    """)
    with engine.connect() as s:
        rows = s.execute(q, {"name": collection}).fetchall()
    counts = Counter()
    for ex, kind, n in rows:
        counts[(ex, kind)] = n
    return counts


def source_counts(engine, collection):
    q = text("""
        SELECT count(DISTINCT e.cmetadata->>'source')
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
        WHERE c.name = :name
    """)
    with engine.connect() as s:
        return s.execute(q, {"name": collection}).scalar()


def fault_coverage(vectorstore, exercise_id, query):
    out = {}
    for kind in ("mistake", "finding"):
        hits = vectorstore.similarity_search_with_score(
            query, k=PROBE_K,
            filter={"exercise_id": exercise_id, "item_kind": {"$in": [kind]}},
        )
        usable = sum(1 for _, d in hits if d <= USABLE_DISTANCE)
        best = hits[0][1] if hits else None
        out[kind] = (usable, best)
    return out


def _cell(usable, best):
    best_s = f"{best:.3f}" if best is not None else "—"
    flag = "" if usable >= 3 else (" ⚠️" if usable > 0 else " 🔴")
    return f"{usable} ({best_s}){flag}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", action="append",
                    help=f"collection to measure (repeatable). Default: {embedding_config.default_collection()}")
    ap.add_argument("--query-mode", choices=["raw", "expanded", "both"], default="both",
                    help="raw = fault name as sent by upstream; expanded = taxonomy query; both = side by side")
    args = ap.parse_args()
    collections = args.collection or [embedding_config.default_collection()]
    modes = ["raw", "expanded"] if args.query_mode == "both" else [args.query_mode]

    connection = embedding_config.get_connection()
    engine = create_engine(connection)

    from langchain_postgres.vectorstores import PGVector
    embeddings = embedding_config.get_embeddings()

    # --- table 1: size per exercise / kind ---
    exercises = ["squat", "lunge", "push-up", "bicep-curl"]
    print(f"\n## Chunks per exercise (principle / mistake / finding)  — sources\n")
    header = "| exercise | " + " | ".join(collections) + " |"
    print(header)
    print("|---|" + "---|" * len(collections))
    per_coll = {c: chunk_counts(engine, c) for c in collections}
    for ex in exercises:
        cells = []
        for c in collections:
            cc = per_coll[c]
            tot = sum(n for (e, _), n in cc.items() if e == ex)
            cells.append(f"{tot} ({cc[(ex,'principle')]} / {cc[(ex,'mistake')]} / {cc[(ex,'finding')]})")
        print(f"| {ex} | " + " | ".join(cells) + " |")
    cells = [f"{sum(per_coll[c].values())} — {source_counts(engine, c)} sources" for c in collections]
    print("| **total** | " + " | ".join(cells) + " |")

    # --- table 2: per-fault coverage, one column pair per (collection, mode) ---
    print(f"\n## Usable chunks per fault (cosine distance ≤ {USABLE_DISTANCE}), best distance in brackets\n")
    col_labels = []
    for c in collections:
        for m in modes:
            tag = c if len(modes) == 1 else f"{c} [{m}]"
            col_labels.append(f"{tag} mistake | {tag} finding")
    print("| exercise | fault | " + " | ".join(col_labels) + " |")
    print("|---|---|" + "---|---|" * (len(collections) * len(modes)))
    stores = {
        c: PGVector(embeddings=embeddings, collection_name=c, connection=connection, use_jsonb=True)
        for c in collections
    }
    for exercise_id, code, entry in all_faults():
        cells = []
        for c in collections:
            for m in modes:
                query = code if m == "raw" else entry["query"]
                cov = fault_coverage(stores[c], exercise_id, query)
                for kind in ("mistake", "finding"):
                    cells.append(_cell(*cov[kind]))
        print(f"| {exercise_id} | {code} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
