"""KB retrieval: the gate that decides which chunks reach the prompt.

Moved out of test_rag_compare.py (2026-10-25, docs/plans/app_integration_plan.md A1) so the
eval scripts and the feedback service run the same code. Behaviour is unchanged; what changed
is that the tunables below are DEFAULTS, collected in RetrievalConfig and passed in, instead of
module globals each caller patched.
"""
import re
from dataclasses import dataclass, field

import embedding_config
from error_taxonomy import resolve

# ---------------------------------------------------------------------------
# Retrieval configuration (v8 / Gemini). v6 recalibrated these by reading the 4 mock
# sessions; v7 set them from eval/golden_chunks.json + eval/eval_retrieval.py against
# kb_local_curated_v4 (MiniLM) - full story in docs/kb/kb_quality_assessment.md section 7.
# v8 (2026-09-14) re-sweeps RELATIVE_MARGIN against kb_gemini_curated_v4, now that
# embedding_config.DEFAULT_MODE is "gemini" - section 10. CANDIDATE_K, MAX_PER_KIND and
# NEAR_DUP_JACCARD below are carried over from the MiniLM tuning unverified under
# Gemini; they weren't part of the v8 sweep.
# Re-run `python eval/eval_retrieval.py` after touching any number below.
# ---------------------------------------------------------------------------

# Pool size fetched per (error, item_kind). Deliberately larger than the number of
# chunks we intend to keep: this KB stores the same fact many times over in slightly
# different wording (10 of the top 10 bicep-curl "momentum" hits are paraphrases of one
# sentence), so a raw top-k is mostly redundancy. We over-fetch, then de-duplicate and
# quota down. Raising this alone does NOT add information - it adds paraphrases.
CANDIDATE_K = 12

# Max chunks kept per (error, item_kind) after de-duplication. Kept per-kind rather
# than as one blended budget because mistake-chunks outnumber and out-rank
# finding-chunks for fault-shaped queries, and findings are where the citable numbers
# live - a blended top-k returns 15 mistakes and 0 findings, leaving the model with
# nothing concrete to cite (and therefore prone to inventing one).
# `principle` 3 -> 2 with v7's per-error principle search: the third principle was
# never a second correct one - on the golden set it was the chunk that contradicts the
# fix ("A slight forward lean of the trunk distributes the load evenly" under trunk
# lean, "Perform a partial lunge to 50 degrees" under shallow lunge). 3 -> 2 moved
# principle bad 8 -> 5 and good 13 -> 12 across the 10 faults.
# `consequence` (KB v5): same budget as `finding` - one clear harm-mechanism sentence is
# enough for "why it matters" in the prompt, a second is usually a paraphrase of the first.
MAX_PER_KIND = {"mistake": 3, "finding": 2, "principle": 2, "consequence": 2}

# Hard backstop per kind: beyond this the closest chunk is not about the fault at all,
# and the honest result is an empty column rather than the nearest neighbour. 0.40 is
# the same "usable" bar tools/kb_coverage.py reports against, so the two tools agree on what
# counts as coverage. Kept at 0.40 under Gemini too, but it is currently non-binding:
# gemini-embedding-2's best-hit distances run ~0.02-0.19 on this KB (see RELATIVE_MARGIN
# below), so best + RELATIVE_MARGIN never approaches 0.40 in practice. It stays as a
# backstop for a fault with no real match in the KB at all, same role it played under
# MiniLM (docs/kb/kb_quality_assessment.md section 7.2).
ABS_DISTANCE_CAP = {"mistake": 0.40, "finding": 0.40, "principle": 0.40, "consequence": 0.40}

# Relative gate, applied per kind: keep only hits within this margin of the best hit
# for that kind. Absolute thresholds do not transfer across exercises, but the *gap*
# between a real match and the next-best noise is consistent.
#
# 0.03, re-swept for Gemini (2026-09-14, docs/kb/kb_quality_assessment.md section 10).
# gemini-embedding-2's cosine distances cluster far tighter than MiniLM's - the raw
# <=0.40 pool tools/kb_coverage.py reports is saturated at 40/40 for nearly every fault, so
# ABS_DISTANCE_CAP above stopped discriminating anything and RELATIVE_MARGIN became the
# only real filter. On the golden set (single mode, kb_gemini_curated_v4): 0.10/0.08 ->
# bad 6 / good 26, 0.05 -> bad 6 / good 25, 0.04 -> bad 4 / good 24, 0.03 -> bad 2 /
# good 23, 0.015 -> bad 2 / good 20 (same bad, 3 fewer good), 0.01 -> bad 1 / good 19.
# Picked 0.03: the point where tightening further stops trading away bad and starts
# only trading away good. (The MiniLM value, 0.06, is unrelated - it's tuned to a
# completely different distance scale and stays correct for kb_local_curated_v4.)
RELATIVE_MARGIN = 0.03

# Jaccard token overlap above which two kept chunks are treated as the same fact.
NEAR_DUP_JACCARD = 0.72

# How the fault_tags pre-pass (KB v5) combines with plain semantic search - see _search().
#   prefer - tagged pool only whenever it has any hit for the kind, untagged search as a
#            fallback when it is empty (behaviour through R0).
#   union  - both pools, merged, gated on distance adjusted by TAG_BONUS: tagged with this
#            fault -TAG_BONUS, tagged only with other faults +TAG_BONUS, untagged (fault_tags
#            "") unchanged. Most v5 chunks are untagged (the curator tags only items it could
#            pin to one fault), so under `prefer` a fault with a single tagged chunk of a kind
#            hid every untagged chunk of that kind (ablation B0: miss reason tag_filter).
#   strict - prefer, minus the fallback: a kind with no chunk tagged for the fault stays
#            EMPTY instead of searching every chunk of the exercise. A kind that has tagged
#            chunks behaves exactly as under prefer. The fallback pool is the whole exercise,
#            so for a fault the curator tagged thinly it returned other faults' chunks, and the
#            context header still labelled them "re: <fault>" (docs/reports/eval_report_2026-10-20.md
#            section 3.8b: LU-004 straight_back_leg, 8 chunks of which 1 was about the fault).
#            Only applies when the error resolved to a fault code; with no code (unmapped
#            error, --raw-query, flawless session) there is no tag to be strict about and the
#            search is the same as prefer.
# TAG_BONUS = one RELATIVE_MARGIN width: a tagged chunk competes as if it were one margin
# closer, i.e. it survives the gate whenever it is within 2x margin of an untagged best.
# Set before the R1 run, not tuned on it.
# Default strict as of 2026-10-25 (user decision, docs/reports/eval_v6b_context_2026-10-24.md): on v6b
# it differs from prefer only where a fault has no tagged chunk of a kind (straight_back_leg
# finding). Baseline v14 ran under prefer; pass --tag-mode prefer to reproduce it.
TAG_MODE = "strict"
TAG_BONUS = 0.03

# How the kinds share the context budget - see retrieve_kb_blocks().
#   split  - one search, one RELATIVE_MARGIN and one MAX_PER_KIND quota per kind (through R1).
#   single - one search over every requested kind at once (k = CANDIDATE_K per kind, so the
#            same number of candidates is looked at), one margin from the overall best hit,
#            one budget = sum of MAX_PER_KIND over those kinds. Which chunks are ELIGIBLE is
#            unchanged: each kind still applies the fault_tags "prefer" rule on its own (a kind
#            with any chunk tagged for the fault searches only its tagged chunks). Ablation
#            B0/R0: most missed facts were lost to a full per-kind quota (159) or to ranking
#            below the top CANDIDATE_K of their own kind (146), not to the budget as a whole.
KIND_POOL = "split"

# Queries embedded per resolved fault - see _search_multi().
#   fault   - the taxonomy query alone (through R2).
#   profile - QUERY_PROFILE: the taxonomy query ("what") plus one template each for "why it
#             matters" and "how to fix it". The taxonomy query is worded like a curator
#             mistake on purpose (error_taxonomy.py docstring), which keeps mistake chunks
#             closest; consequence/principle chunks answer the other two questions. Templates
#             are generic, not per fault, and were fixed before the R4 run.
# Default "profile" since ablation R4 (vs R0: recall 62 -> 66 facts, wrong_fault 6 = 6, golden
# bad 1 -> 0, pool-precision 0.79 -> 0.80). `--queries fault` restores the R0 behaviour.
QUERIES = "profile"

# Lexical (BM25) signal next to the vector one - see _search_hybrid() and kb_bm25.py.
# Per query, BM25_K keyword hits join the vector top-CANDIDATE_K as candidates. The margin
# still runs on vector distance alone (relevance floor, until a reranker replaces it); BM25
# only changes the ORDER in which margin-passing chunks claim the per-kind quota, by
# BM25_WEIGHT * (bm25 / best bm25 for that query): the strongest keyword match gets one
# RELATIVE_MARGIN width of head start, same reasoning as TAG_BONUS. Fixed before the R5 run.
HYBRID = False
BM25_K = CANDIDATE_K
BM25_WEIGHT = 0.03

# Cross-encoder reranking in place of RELATIVE_MARGIN - see _search_multi() and kb_rerank.py.
# Candidates are unchanged (every query's vector top-CANDIDATE_K per kind); each is scored
# against every query string, best score kept, and the gate becomes score >= RERANK_MIN
# instead of "within RELATIVE_MARGIN of the best distance". Order within the per-kind quota
# follows the score. RERANK_MIN = 0.5 on the sigmoid, i.e. logit 0: the model's own
# relevant / not-relevant boundary, fixed before the R6 run rather than tuned on it.
RERANK = False
RERANK_MIN = 0.5
QUERY_PROFILE = {
    "what": "{q}",
    "why": "Harmful consequences, injury risk and joint stress caused by: {q}",
    "fix": "How to correct it, coaching cues and corrective exercises for: {q}",
}

NO_MATCH_CONTEXT = "No highly relevant knowledge-base entries were found for these specific errors."


@dataclass(frozen=True)
class RetrievalConfig:
    """Every tunable above, as one value. The defaults are the module constants; eval scripts
    override fields with dataclasses.replace(), the service builds one at startup. Passed in
    explicitly so two callers in one process can never see each other's settings."""
    candidate_k: int = CANDIDATE_K
    max_per_kind: dict = field(default_factory=lambda: dict(MAX_PER_KIND))
    abs_distance_cap: dict = field(default_factory=lambda: dict(ABS_DISTANCE_CAP))
    relative_margin: float = RELATIVE_MARGIN
    near_dup_jaccard: float = NEAR_DUP_JACCARD
    tag_mode: str = TAG_MODE
    tag_bonus: float = TAG_BONUS
    kind_pool: str = KIND_POOL
    queries: str = QUERIES
    hybrid: bool = HYBRID
    bm25_k: int = BM25_K
    bm25_weight: float = BM25_WEIGHT
    rerank: bool = RERANK
    rerank_min: float = RERANK_MIN
    query_profile: dict = field(default_factory=lambda: dict(QUERY_PROFILE))

    def summary(self):
        """One line of the gate settings, for report headers."""
        return (f"CANDIDATE_K={self.candidate_k}, MAX_PER_KIND={self.max_per_kind}, "
                f"ABS_DISTANCE_CAP={self.abs_distance_cap}, RELATIVE_MARGIN={self.relative_margin}, "
                f"NEAR_DUP_JACCARD={self.near_dup_jaccard}, TAG_MODE={self.tag_mode}"
                + (f", TAG_BONUS={self.tag_bonus}" if self.tag_mode == "union" else "")
                + f", KIND_POOL={self.kind_pool}, QUERIES={self.queries}, HYBRID={self.hybrid}"
                + (f" (BM25_K={self.bm25_k}, BM25_WEIGHT={self.bm25_weight})" if self.hybrid else "")
                + f", RERANK={self.rerank}" + (f" (min {self.rerank_min})" if self.rerank else ""))


DEFAULT_CONFIG = RetrievalConfig()


def open_vectorstore(collection_name):
    """The PGVector store every caller retrieves from: embedding_config's backend and DB."""
    from langchain_postgres.vectorstores import PGVector
    return PGVector(
        embeddings=embedding_config.get_embeddings(),
        collection_name=collection_name,
        connection=embedding_config.get_connection(),
        use_jsonb=True,
    )


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _is_near_duplicate(text, kept_texts, threshold=NEAR_DUP_JACCARD):
    """True if `text` restates something already kept (token Jaccard >= `threshold`).

    Content-level de-duplication, unlike ingest.py's hash-based dedup which only catches
    byte-identical content+metadata pairs - the same sentence extracted from two
    different sources has different metadata and survives that check.
    """
    t = _tokens(text)
    if not t:
        return True
    for other in kept_texts:
        o = _tokens(other)
        if not o:
            continue
        if len(t & o) / len(t | o) >= threshold:
            return True
    return False


def format_source(raw_source):
    """Turn a curator `source` label into something citable in one line.

    Raw values look like an absolute Windows path plus a window marker, e.g.
    'C:/.../data/squat/TheBackSquat.pdf [part 3/22]', or for scraped pages
    'C:/.../data/squat/urls.txt (https://blog.nasm.org/biomechanics-of-the-squat)'.
    Neither is readable as-is. The label is no longer shown to the user (the prompt
    forbids attributions in the feedback) but it stays in the context header so the
    report reader can trace every fact in the output back to its chunk.
    """
    if not raw_source:
        return "knowledge base"
    url = re.search(r"https?://([^\s)]+)", raw_source)
    if url:
        # Some NASM articles only survive on the Wayback Machine; cite the original
        # address, not the archive wrapper.
        return re.sub(r"^web\.archive\.org/web/\d+/https?://", "", url.group(1)).rstrip("/")
    base = re.sub(r"\s*\[part \d+/\d+\]\s*$", "", raw_source).strip()
    base = base.replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r"\.(pdf|txt|json)$", "", base, flags=re.IGNORECASE)


def _chunk_text(doc):
    """ingest.py embeds the bare item text (no header - see ingest.py's item loop) and
    also copies it into metadata["text"]. Read from metadata here rather than
    page_content because RecursiveCharacterTextSplitter's pass 2 could in principle have
    re-split a long item; metadata["text"] is always the untouched original string.
    Falls back to page_content for any chunk that predates the metadata["text"] field."""
    return doc.metadata.get("text") or doc.page_content


def _search(vectorstore, query, exercise_id, kind, already_kept, cfg, code=None, trace=None):
    """One vector search, with the kind filter pushed INTO the query.

    v5 fetched top-k filtered only on exercise_id and dropped the wrong item_kind
    afterwards in Python. Because `principle` chunks outnumber `mistake` chunks roughly
    3:1 and rank highly for form-related wording, the top-k was routinely all-principle
    and the post-filter emptied it - bicep-curl "Using momentum" returned zero chunks
    while 12 verbatim-relevant mistake chunks sat in the KB unreachable.

    `already_kept` is the running list of chunk texts kept for the WHOLE session, not
    just this query: two different errors on the same session ("Using momentum" and
    "Swinging torso") legitimately match the same KB sentences, and without a shared
    de-duplication list the context ends up restating one fact five times.

    `code`: the resolved fault code (error_taxonomy.resolve()'s "code"), used as a
    tag-filter pre-pass (KB v5). curated_data_v5 tags each item's own
    applies_to_fault, stored per chunk as "fault_tags" ("|code-a|code-b|" or "" - see
    ingest.py); filtering on it first removes wrong-fault neighbours the embedding alone
    cannot separate (the curator already made that judgement once, precisely, per item -
    no reason to re-derive it from cosine distance). If the tagged pool is empty - either
    `code` is None, or this is a kb_gemini_curated_v4 collection where every chunk's
    fault_tags is "" because v4 never tagged per item - fall back to the untagged search,
    which is exactly today's behaviour. That is TAG_MODE "prefer". Under "union" both
    searches always run and are merged, ranked by distance adjusted with TAG_BONUS (see
    TAG_MODE); the gate below then runs on the adjusted distance, while `kept` still
    carries the raw one so context order and metrics stay on the embedding's scale.
    Under "strict" an empty tagged pool (with a `code`) returns nothing instead of falling
    back to the untagged search.
    Returns (kept, tagged): `tagged` = the tag-filtered search had hits, i.e. `code`'s tag
    influenced this kind's result.

    `trace`: optional list; when given, every candidate in the pool is appended with the
    gate's decision for it (kept / quota / margin / dup) so eval/eval_retrieval.py can say
    WHY a relevant chunk never reached the context. Kept set is identical with or without
    it - the loop below only stopped breaking early so later candidates get a reason too.
    """
    base_filter = {"exercise_id": exercise_id, "item_kind": {"$in": [kind]}}
    tagged = False
    hits = []
    if code:
        hits = vectorstore.similarity_search_with_score(
            query, k=cfg.candidate_k,
            filter={**base_filter, "fault_tags": {"$like": f"%|{code}|%"}},
        )
        tagged = bool(hits)
        if cfg.tag_mode == "strict" and not tagged:
            return [], False
    if cfg.tag_mode == "union" and code:
        hits = _union_by_tag(hits, vectorstore.similarity_search_with_score(
            query, k=cfg.candidate_k, filter=base_filter), code, cfg)
    else:
        if not hits:
            hits = vectorstore.similarity_search_with_score(query, k=cfg.candidate_k, filter=base_filter)
        hits = [(doc, score, score) for doc, score in hits]
    if not hits:
        return [], False
    best = hits[0][2]
    cutoff = min(cfg.abs_distance_cap[kind], best + cfg.relative_margin)
    kept = []
    for doc, score, adj in hits:
        text = _chunk_text(doc)
        # Same decisions, same order as the original early-break loop: hits are sorted by
        # (adjusted) distance, so once one is past the cutoff every later one is too.
        if len(kept) >= cfg.max_per_kind[kind]:
            reason = "quota"
        elif adj > cutoff:
            reason = "margin"
        elif _is_near_duplicate(text, already_kept, cfg.near_dup_jaccard):
            reason = "dup"
        else:
            reason = "kept"
            kept.append((doc, score))
            already_kept.append(text)
        if trace is not None:
            trace.append({"kind": kind, "text": text, "score": score, "adj": adj, "reason": reason,
                          "tagged": tagged, "code": code})
        elif reason in ("quota", "margin"):
            break
    return kept, tagged


def _union_by_tag(tagged_hits, plain_hits, code, cfg):
    """TAG_MODE "union": merge the tag-filtered and plain top-k into one list of
    (doc, raw distance, adjusted distance) sorted by adjusted distance. A chunk in both
    lists appears once. Adjustment by the chunk's own fault_tags, not by which list it
    came from - a tagged chunk can rank in the plain top-k too."""
    merged = {}
    for doc, score in list(tagged_hits) + list(plain_hits):
        key = doc.id or (_chunk_text(doc), doc.metadata.get("source"))
        if key in merged:
            continue
        tags = doc.metadata.get("fault_tags") or ""
        if f"|{code}|" in tags:
            adj = score - cfg.tag_bonus
        elif tags.strip("|"):
            adj = score + cfg.tag_bonus
        else:
            adj = score
        merged[key] = (doc, score, adj)
    return sorted(merged.values(), key=lambda h: h[2])


def _search_single(vectorstore, query, exercise_id, kinds, already_kept, cfg, code=None, trace=None):
    """KIND_POOL "single": the gate of _search() run once over all `kinds` together.

    Eligibility per kind is the same as _search() under TAG_MODE "prefer": a kind with any
    chunk tagged for `code` contributes only its tagged chunks, any other kind all of its
    chunks (TAG_MODE "strict": any other kind none, and its MAX_PER_KIND leaves the budget
    with it, so the kinds that do have tagged chunks get exactly the budget they get under
    prefer). That is pushed into ONE query as an $or of per-kind filters, so the kinds then
    compete for one margin (from the overall best hit) and one budget (sum of MAX_PER_KIND
    over `kinds`). The query is embedded once and reused for every probe.

    Returns (kept, tagged_kinds, best_by_kind): kept = [(doc, score, kind)], tagged_kinds =
    the kinds whose tag filter had hits, best_by_kind = closest eligible chunk per kind (the
    per-kind `best` metric, comparable with split mode's).
    """
    if cfg.tag_mode not in ("prefer", "strict") or cfg.queries != "fault" or cfg.hybrid:
        raise ValueError("KIND_POOL 'single' is implemented for TAG_MODE 'prefer'/'strict', QUERIES 'fault', "
                         "no HYBRID only")
    vec = vectorstore.embeddings.embed_query(query)
    kind_filters, tagged_kinds, best_by_kind, eligible = [], set(), {}, []
    for kind in kinds:
        kf = {"item_kind": {"$eq": kind}}
        if code:
            tf = {"$and": [kf, {"fault_tags": {"$like": f"%|{code}|%"}}]}
            probe = vectorstore.similarity_search_with_score_by_vector(
                vec, k=1, filter={"$and": [{"exercise_id": {"$eq": exercise_id}}, tf]})
            if probe:
                tagged_kinds.add(kind)
                kf = tf
        if kind not in tagged_kinds:
            if cfg.tag_mode == "strict" and code:
                best_by_kind[kind] = None
                continue
            probe = vectorstore.similarity_search_with_score_by_vector(
                vec, k=1, filter={"$and": [{"exercise_id": {"$eq": exercise_id}}, kf]})
        best_by_kind[kind] = probe[0][1] if probe else None
        kind_filters.append(kf)
        eligible.append(kind)
    if not kind_filters:
        return [], tagged_kinds, best_by_kind
    hits = vectorstore.similarity_search_with_score_by_vector(
        vec, k=cfg.candidate_k * len(eligible),
        filter={"$and": [{"exercise_id": {"$eq": exercise_id}}, {"$or": kind_filters}]})
    if not hits:
        return [], tagged_kinds, best_by_kind
    budget = sum(cfg.max_per_kind[k] for k in eligible)
    best = hits[0][1]
    kept = []
    for doc, score in hits:
        kind = doc.metadata.get("item_kind")
        text = _chunk_text(doc)
        if len(kept) >= budget:
            reason = "quota"
        elif score > min(cfg.abs_distance_cap[kind], best + cfg.relative_margin):
            reason = "margin"
        elif _is_near_duplicate(text, already_kept, cfg.near_dup_jaccard):
            reason = "dup"
        else:
            reason = "kept"
            kept.append((doc, score, kind))
            already_kept.append(text)
        if trace is not None:
            trace.append({"kind": kind, "text": text, "score": score, "reason": reason,
                          "tagged": kind in tagged_kinds, "code": code})
    return kept, tagged_kinds, best_by_kind


def _search_multi(vectorstore, vecs, exercise_id, kind, already_kept, cfg, code=None, trace=None, texts=None):
    """QUERIES "profile": the per-kind gate of _search() fed by several queries.

    `vecs` = [query embedding]. Each query runs its own top-CANDIDATE_K search over the same
    eligible pool (fault_tags "prefer": tagged chunks only if the kind has any; "strict":
    tagged chunks only, nothing if the kind has none). Raw distances
    are not comparable across queries - the taxonomy query is phrased like the chunks and
    sits far closer than a template - so every candidate is scored by its distance above
    THAT query's best hit, taking the smallest over the queries it came back for. The gate
    then runs on that: within RELATIVE_MARGIN (i.e. inside the margin of at least one
    query), MAX_PER_KIND quota, near-dup. With a single query this is exactly _search().
    `kept` carries the raw distance of the query the chunk was closest to relative to its best.

    RERANK: same candidates, but the margin test and the order are replaced by the
    cross-encoder score of each chunk against `texts` (the query strings behind `vecs`),
    best over the queries - see RERANK.

    Returns (kept, tagged, best): best = smallest raw distance over the queries.
    """
    base_filter = {"exercise_id": exercise_id, "item_kind": {"$in": [kind]}}
    filt = base_filter
    if code and vectorstore.similarity_search_with_score_by_vector(
            vecs[0], k=1, filter={**base_filter, "fault_tags": {"$like": f"%|{code}|%"}}):
        filt = {**base_filter, "fault_tags": {"$like": f"%|{code}|%"}}
    tagged = filt is not base_filter
    if cfg.tag_mode == "strict" and code and not tagged:
        return [], False, None
    merged = {}
    for vec in vecs:
        hits = vectorstore.similarity_search_with_score_by_vector(vec, k=cfg.candidate_k, filter=filt)
        if not hits:
            continue
        q_best = hits[0][1]
        for doc, score in hits:
            rel = score - q_best
            if score > cfg.abs_distance_cap[kind]:
                rel = float("inf")
            key = doc.id or (_chunk_text(doc), doc.metadata.get("source"))
            if key not in merged or rel < merged[key][2]:
                merged[key] = (doc, score, rel)
    if not merged:
        return [], False, None
    best = min(score for _, score, _ in merged.values())
    if cfg.rerank:
        # RERANK replaces the margin: gate on the cross-encoder's score (best over `texts`),
        # order by it. ABS_DISTANCE_CAP stays as the backstop (rel is inf past it).
        import kb_rerank
        cands = list(merged.values())
        rr = kb_rerank.max_scores(texts, [_chunk_text(doc) for doc, _, _ in cands])
        ranked = sorted(((doc, score, rel, r) for (doc, score, rel), r in zip(cands, rr)),
                        key=lambda h: (-h[3], h[1]))
    else:
        ranked = [(doc, score, rel, None) for doc, score, rel in sorted(merged.values(), key=lambda h: (h[2], h[1]))]
    kept = []
    for doc, score, rel, rr in ranked:
        text = _chunk_text(doc)
        if len(kept) >= cfg.max_per_kind[kind]:
            reason = "quota"
        elif (rr < cfg.rerank_min or rel == float("inf")) if cfg.rerank else rel > cfg.relative_margin:
            # under RERANK "margin" = below RERANK_MIN, i.e. the relevance gate either way
            reason = "margin"
        elif _is_near_duplicate(text, already_kept, cfg.near_dup_jaccard):
            reason = "dup"
        else:
            reason = "kept"
            kept.append((doc, score))
            already_kept.append(text)
        if trace is not None:
            trace.append({"kind": kind, "text": text, "score": score, "rel": rel, "rerank": rr,
                          "reason": reason, "tagged": tagged, "code": code})
    return kept, tagged, best


def _search_hybrid(vectorstore, texts, vecs, exercise_id, kind, already_kept, cfg, code=None, trace=None):
    """HYBRID: _search_multi() over kb_bm25's in-memory corpus, with BM25 as a second signal.

    Same eligible pool (fault_tags "prefer"/"strict" per kind), same vector candidates (top-CANDIDATE_K
    per query, exact cosine distance), same margin test on the vector distance above each
    query's best. Added: each query's top-BM25_K keyword hits join the candidates, and the
    order that fills the quota is (distance above best) - BM25_WEIGHT * normalised BM25,
    minimum over queries. With BM25_K = 0 and BM25_WEIGHT = 0 this is _search_multi().
    Returns (kept, tagged, best) like _search_multi().
    """
    import numpy as np
    import kb_bm25
    corp = kb_bm25.corpus(vectorstore.collection_name, exercise_id)
    idx = [i for i, d in enumerate(corp.docs) if d.metadata.get("item_kind") == kind]
    tagged = False
    if code:
        tagged_idx = [i for i in idx if f"|{code}|" in (corp.docs[i].metadata.get("fault_tags") or "")]
        if tagged_idx:
            idx, tagged = tagged_idx, True
        elif cfg.tag_mode == "strict":
            return [], False, None
    if not idx:
        return [], False, None
    idx = np.array(idx)
    merged = {}  # corpus index -> [raw distance of the rel-argmin query, rel, order key, bm25]
    best = None
    for text, vec in zip(texts, vecs):
        dist = corp.distances(vec, idx)
        lex = corp.bm25(text, idx)
        q_best, lex_max = float(dist.min()), float(lex.max())
        best = q_best if best is None else min(best, q_best)
        cand = set(np.argsort(dist, kind="stable")[:cfg.candidate_k].tolist())
        if cfg.bm25_k and lex_max > 0:
            cand |= {j for j in np.argsort(-lex, kind="stable")[:cfg.bm25_k].tolist() if lex[j] > 0}
        for j in cand:
            score = float(dist[j])
            rel = score - q_best if score <= cfg.abs_distance_cap[kind] else float("inf")
            key = rel - (cfg.bm25_weight * lex[j] / lex_max if lex_max > 0 else 0.0)
            m = merged.setdefault(int(idx[j]), [score, rel, key, float(lex[j])])
            if rel < m[1]:
                m[0], m[1] = score, rel
            m[2] = min(m[2], key)
            m[3] = max(m[3], float(lex[j]))
    kept = []
    for i, (score, rel, key, lex) in sorted(merged.items(), key=lambda kv: (kv[1][2], kv[1][0])):
        doc = corp.docs[i]
        text = _chunk_text(doc)
        if len(kept) >= cfg.max_per_kind[kind]:
            reason = "quota"
        elif rel > cfg.relative_margin:
            reason = "margin"
        elif _is_near_duplicate(text, already_kept, cfg.near_dup_jaccard):
            reason = "dup"
        else:
            reason = "kept"
            kept.append((doc, score))
            already_kept.append(text)
        if trace is not None:
            trace.append({"kind": kind, "text": text, "score": score, "rel": rel, "bm25": lex,
                          "reason": reason, "tagged": tagged, "code": code})
    return kept, tagged, best


def retrieve_kb_blocks(vectorstore, exercise_id, exercise_name, error_types, raw_query=False,
                       trace=None, cfg=DEFAULT_CONFIG):
    """Retrieve KB chunks relevant to the session's actual errors (or general principles
    for a flawless session). Returns (blocks, metrics) where blocks is a list of
    (distance, doc, kind, error_label) sorted by distance - the structured form of what
    retrieve_kb_context renders as text. Split out so eval/eval_retrieval.py can score
    exactly the chunks the gate passes without parsing the rendered context back.

    Each error is resolved through error_taxonomy.py into a fault-name query before it is
    embedded, and each (error, kind) pair is searched separately so mistake-chunks and
    finding-chunks each get their own budget.

    `raw_query=True` bypasses the taxonomy and embeds the error_type string exactly as
    received. That is the A/B control for "does the taxonomy layer buy anything": the
    upstream fault names are short labels ("Butt wink", "Elbow flare") and the question is
    whether the descriptive query in error_taxonomy.py finds materially closer chunks.

    `metrics` is one row per (error, kind): the query actually embedded, the best distance
    in the candidate pool, and how many chunks survived the gate. Reported next to the LLM
    output so the retrieval side can be compared across runs numerically - the generation
    side at temperature 0.7 cannot be.

    Every returned chunk carries its kind and a readable source label. The prompt no longer
    asks the model to repeat the source to the user, but the label stays in the header so
    the report reader can trace a fact in the output back to its chunk - v5 passed bare
    sentences with no attribution at all, which made that check impossible.

    `trace`: optional list passed through to _search() - see there. Each entry also gets
    the error label it was retrieved for.

    `cfg`: the gate settings, RetrievalConfig.
    """
    kept_texts = []
    blocks = []
    metrics = []
    unknown_codes = []

    def collect(query, kinds, label, code=None):
        if cfg.kind_pool == "single":
            kind_trace = [] if trace is not None else None
            kept, tagged_kinds, best_by_kind = _search_single(
                vectorstore, query, exercise_id, kinds, kept_texts, cfg, code=code, trace=kind_trace)
            if trace is not None:
                trace.extend({**t, "error": label} for t in kind_trace)
            for kind in kinds:
                metrics.append({
                    "error": label, "kind": kind, "query": query, "best": best_by_kind[kind],
                    "kept": sum(1 for _, _, k in kept if k == kind),
                    "tagged": kind in tagged_kinds, "tag_exclusive": kind in tagged_kinds,
                    "strict_skip": cfg.tag_mode == "strict" and bool(code) and kind not in tagged_kinds,
                })
            for doc, score, kind in kept:
                blocks.append((score, doc, kind, label))
            return
        if (cfg.queries == "profile" or cfg.hybrid or cfg.rerank) and code:
            if cfg.hybrid and cfg.rerank:
                raise ValueError("HYBRID and RERANK are not implemented together")
            texts = [t.format(q=query) for t in cfg.query_profile.values()] if cfg.queries == "profile" else [query]
            vecs = [vectorstore.embeddings.embed_query(t) for t in texts]
            for kind in kinds:
                kind_trace = [] if trace is not None else None
                if cfg.hybrid:
                    kept, tagged, best = _search_hybrid(vectorstore, texts, vecs, exercise_id, kind,
                                                        kept_texts, cfg, code=code, trace=kind_trace)
                else:
                    kept, tagged, best = _search_multi(vectorstore, vecs, exercise_id, kind, kept_texts,
                                                       cfg, code=code, trace=kind_trace, texts=texts)
                if trace is not None:
                    trace.extend({**t, "error": label} for t in kind_trace)
                metrics.append({
                    "error": label, "kind": kind,
                    "query": query + (f" (+{'/'.join(list(cfg.query_profile)[1:])})" if cfg.queries == "profile" else "")
                             + (" [hybrid]" if cfg.hybrid else "") + (" [rerank]" if cfg.rerank else ""),
                    "best": best, "kept": len(kept), "tagged": tagged, "tag_exclusive": tagged,
                    "strict_skip": cfg.tag_mode == "strict" and not tagged,
                })
                for doc, score in kept:
                    blocks.append((score, doc, kind, label))
            return
        for kind in kinds:
            kind_trace = [] if trace is not None else None
            kept, tagged = _search(vectorstore, query, exercise_id, kind, kept_texts, cfg, code=code,
                                   trace=kind_trace)
            if trace is not None:
                trace.extend({**t, "error": label} for t in kind_trace)
            # Best distance is measured on the raw pool, not on `kept`: a query whose
            # closest chunk fails the cap still tells us how far off it was. Probe the
            # SAME pool _search actually kept from (tagged if the tag-filter had hits,
            # untagged otherwise) so `best` describes the pool the gate saw. Under union
            # that is the whole unfiltered pool (raw distance, before TAG_BONUS).
            # `tag_exclusive`: the tag filter shut the untagged chunks out of this kind's
            # search altogether (prefer mode with tagged hits) - eval_retrieval.py's
            # tag_filter miss reason only exists then.
            # `strict_skip`: TAG_MODE "strict" left this kind empty because no chunk of it is
            # tagged for `code` - the pool the gate saw is empty, so `best` is None.
            tag_exclusive = tagged and cfg.tag_mode != "union"
            strict_skip = cfg.tag_mode == "strict" and bool(code) and not tagged
            probe_filter = {"exercise_id": exercise_id, "item_kind": {"$in": [kind]}}
            if tag_exclusive:
                probe_filter["fault_tags"] = {"$like": f"%|{code}|%"}
            pool = [] if strict_skip else vectorstore.similarity_search_with_score(query, k=1, filter=probe_filter)
            metrics.append({
                "error": label, "kind": kind, "query": query,
                "best": pool[0][1] if pool else None, "kept": len(kept), "tagged": tagged,
                "tag_exclusive": tag_exclusive, "strict_skip": strict_skip,
            })
            for doc, score in kept:
                blocks.append((score, doc, kind, label))

    if error_types:
        for error_type in sorted(error_types):
            code = None
            if raw_query:
                query = error_type
            else:
                resolved = resolve(error_type, exercise_id)
                if not resolved["known"]:
                    unknown_codes.append(error_type)
                else:
                    code = resolved["code"]
                query = resolved["query"]
            # `principle` is searched with the same fault query, not a separate "how to
            # fix" phrasing: the KB's principle items are the curator's positive
            # restatement of the mistake ("Keep elbows tucked at the sides" 0.161 for the
            # elbow-flare query), so the fault wording already lands on them. v6 only
            # fetched principles for a flawless session, which left every "how to
            # correct" paragraph ungrounded - identical to the no-RAG output.
            # `code` is None under raw_query (the A/B control bypasses the taxonomy
            # entirely, so there is no resolved code to tag-filter on either).
            collect(query, ("mistake", "finding", "consequence", "principle"), error_type, code=code)
    else:
        collect(
            f"{exercise_name} correct technique and biomechanics",
            ("principle",),
            "general principles",
        )

    if unknown_codes:
        print(f"  [taxonomy] unmapped error_type(s), using raw text as query: {unknown_codes}")

    blocks.sort(key=lambda b: b[0])
    return blocks, metrics


def render_context(blocks):
    """The text the system prompt expects for retrieve_kb_blocks()' blocks."""
    if not blocks:
        return NO_MATCH_CONTEXT
    lines = []
    for score, doc, kind, label in blocks:
        src = format_source(doc.metadata.get("source", ""))
        lines.append(f"[{kind} | re: {label} | source: {src}]\n{_chunk_text(doc)}")
    return "\n\n".join(lines)


def retrieve_kb_context(vectorstore, exercise_id, exercise_name, error_types, raw_query=False,
                        cfg=DEFAULT_CONFIG):
    """Render retrieve_kb_blocks() as the text the system prompt expects. Returns
    (context_text, metrics); see retrieve_kb_blocks for the retrieval policy itself."""
    blocks, metrics = retrieve_kb_blocks(
        vectorstore, exercise_id, exercise_name, error_types, raw_query=raw_query, cfg=cfg)
    return render_context(blocks), metrics


def metrics_table(metrics):
    """Markdown table, one row per error: query sent + best/kept per kind.

    A trailing `*` on a cell marks a tag-filtered hit (KB v5's fault_tags pre-pass found
    something, so `best`/`kept` describe that narrower pool, not the plain semantic one) -
    see _search()'s `tagged` return value. v4 collections never show `*`: every chunk's
    fault_tags is "", so the tag pass always comes back empty and falls back to plain search.
    Under TAG_MODE "union" `*` only means the tag boosted some chunk; `best` is the plain pool's.
    `strict —` = TAG_MODE "strict" skipped the kind: no chunk of it is tagged for the fault.
    """
    by_error = {}
    for m in metrics:
        row = by_error.setdefault(m["error"], {"query": m["query"]})
        row[m["kind"]] = m
    kinds = ("mistake", "finding", "consequence", "principle")
    lines = ["| error_type | query sent | " + " | ".join(f"{k} best / kept" for k in kinds) + " |",
             "|---|---|" + "---|" * len(kinds)]
    for error, row in by_error.items():
        cells = []
        for kind in kinds:
            m = row.get(kind)
            if not m:
                cells.append("—")
            elif m.get("strict_skip"):
                cells.append("strict —")
            else:
                best = f"{m['best']:.3f}" if m["best"] is not None else "—"
                flag = "*" if m.get("tagged") else ""
                cells.append(f"{best} / {m['kept']}{flag}")
        lines.append(f"| {error} | {row['query']} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
