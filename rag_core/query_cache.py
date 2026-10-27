"""Query embeddings cached on disk, for the feedback service (2026-10-27).

The KB's vectors are gemini-embedding-2's, so every retrieval embeds its queries with that
paid model. The queries are few and fixed: for each of the 12 rules, its taxonomy query in
the three QUERY_PROFILE templates, plus one general query per exercise for a set with no
fault (rag_core/retrieval.py). tools/fill_query_cache.py embeds all of them once; after that
a request makes no embedding call. A query not in the file (an unmapped rule name, a new
template) is embedded on the spot, logged, and added, so retrieval never changes because
of the cache.

Same layout as kb_rerank.py's: .cache/query_vectors/<model>.json, {query text: vector},
written whole through a temporary file. .cache/ is not committed.
"""
import json
import logging
import os
import threading

from langchain_core.embeddings import Embeddings

log = logging.getLogger("feedback")

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache", "query_vectors")


def model_name(embeddings):
    """GoogleGenerativeAIEmbeddings carries `model`, HuggingFaceEmbeddings `model_name`."""
    return getattr(embeddings, "model", None) or getattr(embeddings, "model_name", None) or type(embeddings).__name__


def cache_path(model):
    return os.path.join(CACHE_DIR, model.replace("/", "__") + ".json")


class CachedEmbeddings(Embeddings):
    """`inner` with embed_query() served from the cache file. Documents are never cached:
    only ingest embeds documents, and it does not go through here."""

    def __init__(self, inner, path=None):
        self.inner = inner
        self.path = path or cache_path(model_name(inner))
        self._lock = threading.Lock()
        try:
            with open(self.path, encoding="utf-8") as f:
                self._vectors = json.load(f)
        except FileNotFoundError:
            self._vectors = {}

    def __len__(self):
        return len(self._vectors)

    def __contains__(self, text):
        return text in self._vectors

    def embed_query(self, text):
        with self._lock:
            vec = self._vectors.get(text)
        if vec is not None:
            return vec
        log.warning("query embedding not cached, calling the embedding model: %s", text[:80])
        vec = self.inner.embed_query(text)
        with self._lock:
            self._vectors[text] = vec
            self._save()
        return vec

    def embed_documents(self, texts):
        return self.inner.embed_documents(texts)

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._vectors, f)
        os.replace(tmp, self.path)
