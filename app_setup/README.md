# Files for running the feedback service beside the app

What a teammate needs to run `python -m service` on their own machine, so they do not have to
ask for them. The steps are in MU-Capstone-Application `docs/FEEDBACK_SETUP.md`.

- `kb_dump.sql.gz`: collection `kb_gemini_curated_v6b` (2197 chunks, vectors included), a
  data-only `pg_dump` of `langchain_pg_collection` and `langchain_pg_embedding` taken from the
  app's local Supabase on 2026-10-28. Loaded into the app's Postgres, where the migration
  `kb_langchain_tables` has created the two tables.
- `gemini-embedding-2.json`: the query vector cache (`rag_core/query_cache.py`). Copied to
  `.cache/query_vectors/`, it lets a request retrieve without calling Google. It lives here and
  not in `.cache/` (ignored) because the service rewrites the cache when it embeds a new query.

Both change only when the collection or the queries change (a new curation round, a different
`KB_COLLECTION`, new query templates). Make them again with the commands at the end of
`docs/FEEDBACK_SETUP.md` and commit them over these; each new dump adds about 34 MB to the history.
