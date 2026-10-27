"""Embed every query the feedback service can send, once, into rag_core/query_cache.py's file.

    python tools/fill_query_cache.py --dry-run   # list them, no call
    python tools/fill_query_cache.py             # embed the missing ones (paid, about 40 short texts)

The queries: each rule's taxonomy query in each QUERY_PROFILE template, and GENERAL_QUERY for
each exercise name the app sends (MU-Capstone-Application migration 20260910084100_exercises,
`exercises.name`; the adapter falls back to the id when the name is empty). Only texts not
already in the file are embedded, so a re-run after a taxonomy change costs only the new ones.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))

import embedding_config  # noqa: E402
from error_taxonomy import ERROR_TAXONOMY, all_faults  # noqa: E402
from rag_core.query_cache import CachedEmbeddings  # noqa: E402
from rag_core.retrieval import DEFAULT_CONFIG, GENERAL_QUERY  # noqa: E402

APP_EXERCISE_NAMES = ["Squat", "Push-up", "Lunge", "Bicep curl"]


def all_queries(cfg=DEFAULT_CONFIG):
    queries = [t.format(q=entry["query"]) for _, _, entry in all_faults() for t in cfg.query_profile.values()]
    names = APP_EXERCISE_NAMES + list(ERROR_TAXONOMY)  # the ids, for an input without a name
    queries += [GENERAL_QUERY.format(name=n) for n in names]
    return list(dict.fromkeys(queries))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cache = CachedEmbeddings(embedding_config.get_embeddings())
    queries = all_queries()
    missing = [q for q in queries if q not in cache]
    print(f"{len(queries)} queries, {len(queries) - len(missing)} cached, {len(missing)} to embed -> {cache.path}")
    if args.dry_run:
        for q in missing:
            print("  " + q)
        return
    for i, q in enumerate(missing, 1):
        cache.embed_query(q)
        print(f"  {i}/{len(missing)} {q[:70]}")
    print(f"Done, {len(cache)} vectors in the cache")


if __name__ == "__main__":
    main()
