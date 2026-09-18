"""Single source of truth for which embedding backend the pipeline uses.

Every script that talks to pgvector (ingest.py, kb_coverage.py, eval/eval_retrieval.py,
test_rag_compare.py) used to instantiate HuggingFaceEmbeddings("all-MiniLM-L6-v2") or
GoogleGenerativeAIEmbeddings("gemini-embedding-2") separately, so moving the whole
pipeline between backends meant editing four files in lockstep. This module collapses
that to one flag.

DEFAULT_MODE = "gemini" as of 2026-09-14 (docs/kb_quality_assessment.md section 10):
we're on the paid Gemini tier now, so there's no reason to keep querying the smaller
local MiniLM model. "local" is kept only as a fallback/comparison path - kb_local_curated_v4
and its MiniLM-tuned gate thresholds stay in the local database untouched.
"""
import os

# Override per-invocation with `EMBEDDING_MODE=local python kb_coverage.py` etc. -
# useful for A/B-ing against the MiniLM fallback without editing this file.
DEFAULT_MODE = os.environ.get("EMBEDDING_MODE", "gemini")  # "gemini" | "local"

COLLECTION_NAMES = {
    "gemini": "kb_gemini_curated_v5",
    "local": "kb_local_curated_v4",
}

# gemini-embedding-2 uses a much larger vector space than MiniLM's 384 dims, so cosine
# distances land on a different scale entirely - gate thresholds tuned for one backend
# (test_rag_compare.py RELATIVE_MARGIN / ABS_DISTANCE_CAP) are meaningless for the
# other. See docs/kb_quality_assessment.md section 10 for the Gemini-side re-sweep.


def get_embeddings(mode=DEFAULT_MODE):
    if mode == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def get_connection(mode=DEFAULT_MODE):
    env_var = "DATABASE_URL" if mode == "gemini" else "DATABASE_URL_LOCAL"
    connection = os.environ.get(env_var)
    if not connection:
        raise RuntimeError(f"{env_var} not set in .env for mode={mode!r}")
    return connection


def default_collection(mode=DEFAULT_MODE):
    return COLLECTION_NAMES[mode]
