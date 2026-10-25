"""In-memory BM25 + exact cosine over one exercise's chunks, for the hybrid gate in
rag_core/retrieval.py (--hybrid, ablation R5).

Why in Python and not Postgres full-text: ts_rank has no IDF, so "squat" in a squat corpus
weighs as much as "valgus" - it is keyword overlap, not BM25. One exercise is a few hundred
chunks (v5: 348-783), so the whole corpus fits in memory, BM25 is exact, and nothing in the
DB schema or ingest.py has to change.

The corpus is read straight from langchain_pg_embedding (text, metadata, embedding) once per
(collection, exercise_id) and cached for the process. Cosine distance is computed here too,
as 1 - cos, the same quantity PGVector's `<=>` returns, so vector and lexical scores come
from the same rows.
"""
import math
import re
from collections import Counter

import numpy as np
from langchain_core.documents import Document

import embedding_config

# Okapi BM25 with Lucene's defaults and IDF (always positive). Fixed before the R5 run.
K1 = 1.2
B = 0.75

# Function words only - fault vocabulary (knee, hip, depth, ...) is exactly what BM25 is for.
STOPWORDS = set("""
a an and are as at be been being but by can could did do does during for from had has have
how if in into is it its itself may might more most must not of on or should so such than that
the their them then there these they this those through to too under until up was were what
when where which while who why will with within without would you your
""".split())

_CORPORA = {}


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS]


class Corpus:
    """Every chunk of one exercise in one collection: docs, unit embeddings, BM25 stats."""

    def __init__(self, rows):
        self.docs = [Document(page_content=doc, metadata=meta, id=i) for i, doc, meta, _ in rows]
        emb = np.array([e for *_, e in rows], dtype=np.float64)
        self.unit = emb / np.linalg.norm(emb, axis=1, keepdims=True)
        self.tfs = [Counter(tokenize(d.metadata.get("text") or d.page_content)) for d in self.docs]
        self.lens = np.array([sum(tf.values()) for tf in self.tfs], dtype=np.float64)
        self.avglen = float(self.lens.mean()) if len(self.docs) else 0.0
        df = Counter(t for tf in self.tfs for t in tf)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - m + 0.5) / (m + 0.5)) for t, m in df.items()}

    def distances(self, vec, idx):
        v = np.asarray(vec, dtype=np.float64)
        return 1.0 - self.unit[idx] @ (v / np.linalg.norm(v))

    def bm25(self, query, idx):
        terms = [t for t in set(tokenize(query)) if t in self.idf]
        out = np.zeros(len(idx))
        for j, i in enumerate(idx):
            tf, norm = self.tfs[i], K1 * (1 - B + B * self.lens[i] / self.avglen)
            out[j] = sum(self.idf[t] * tf[t] * (K1 + 1) / (tf[t] + norm) for t in terms if t in tf)
        return out


def corpus(collection, exercise_id):
    key = (collection, exercise_id)
    if key not in _CORPORA:
        import psycopg
        from pgvector.psycopg import register_vector
        url = embedding_config.get_connection().replace("postgresql+psycopg://", "postgresql://")
        with psycopg.connect(url) as conn:
            register_vector(conn)
            rows = conn.execute(
                """SELECT e.id, e.document, e.cmetadata, e.embedding
                     FROM langchain_pg_embedding e
                     JOIN langchain_pg_collection c ON c.uuid = e.collection_id
                    WHERE c.name = %s AND e.cmetadata->>'exercise_id' = %s
                    ORDER BY e.id""",
                (collection, exercise_id)).fetchall()
        _CORPORA[key] = Corpus(rows)
    return _CORPORA[key]
