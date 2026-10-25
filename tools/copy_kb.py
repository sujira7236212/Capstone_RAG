"""Copy one KB collection, vectors included, from one Postgres to another. No embedding call.

The app's Supabase Postgres holds the KB the feedback service reads (docs/plans/
app_integration_plan.md D1 = A). Its migration kb_langchain_tables creates the two
langchain tables with no API access; this fills them from the database the KB was ingested
and evaluated in. `npm run db:reset` in the app empties them, so run this again after it.

    python tools/copy_kb.py --to postgresql://postgres:postgres@127.0.0.1:54322/postgres

--from defaults to DATABASE_URL (.env), --collection to embedding_config.default_collection().
A collection of the same name already in the target is replaced. Ends by checking that both
sides hold the same rows, byte for byte.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import psycopg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from psycopg.types.json import Json  # noqa: E402

import embedding_config  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))

COLUMNS = "id, collection_id, embedding, document, cmetadata"
# One digest over every row in id order: same count and same digest = the same collection.
DIGEST = ("SELECT count(*), md5(coalesce(string_agg(e.id || '|' || e.embedding::text || '|' || coalesce(e.document, '')"
          " || '|' || coalesce(e.cmetadata::text, ''), E'\\n' ORDER BY e.id), '')) FROM langchain_pg_embedding e"
          " JOIN langchain_pg_collection c ON c.uuid = e.collection_id WHERE c.name = %s")


def libpq(url):
    """SQLAlchemy URLs (postgresql+psycopg://) -> the plain form psycopg.connect takes."""
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--to", required=True, help="target database URL (the app's Supabase Postgres)")
    ap.add_argument("--from", dest="source", help="source database URL (default: DATABASE_URL)")
    ap.add_argument("--collection", default=embedding_config.default_collection())
    args = ap.parse_args()
    source = args.source or embedding_config.get_connection()

    with psycopg.connect(libpq(source)) as src, psycopg.connect(libpq(args.to)) as dst:
        row = src.execute("SELECT uuid, name, cmetadata FROM langchain_pg_collection WHERE name = %s",
                          (args.collection,)).fetchone()
        if not row:
            sys.exit(f"no collection {args.collection!r} in the source")
        uuid, name, meta = row
        with dst.transaction():
            dst.execute("DELETE FROM langchain_pg_collection WHERE name = %s", (name,))  # chunks cascade
            dst.execute("INSERT INTO langchain_pg_collection (uuid, name, cmetadata) VALUES (%s, %s, %s)",
                        (uuid, name, None if meta is None else Json(meta)))
            with src.cursor().copy(f"COPY (SELECT {COLUMNS} FROM langchain_pg_embedding WHERE collection_id = %s)"
                                   " TO STDOUT", (uuid,)) as out, \
                    dst.cursor().copy(f"COPY langchain_pg_embedding ({COLUMNS}) FROM STDIN") as into:
                for block in out:
                    into.write(block)
        a = src.execute(DIGEST, (name,)).fetchone()
        b = dst.execute(DIGEST, (name,)).fetchone()
    print(f"{name}: source {a[0]} rows md5 {a[1]} · target {b[0]} rows md5 {b[1]}")
    if a != b:
        sys.exit("MISMATCH: the target does not hold the same rows")
    print("identical")


if __name__ == "__main__":
    main()
