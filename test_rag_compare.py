import os
import json
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import warnings

from error_taxonomy import resolve
import embedding_config

warnings.filterwarnings("ignore")

load_dotenv()

# ---------------------------------------------------------------------------
# Retrieval configuration (v8 / Gemini). v6 recalibrated these by reading the 4 mock
# sessions; v7 set them from eval/golden_chunks.json + eval/eval_retrieval.py against
# kb_local_curated_v4 (MiniLM) - full story in docs/kb_quality_assessment.md section 7.
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
# the same "usable" bar kb_coverage.py reports against, so the two tools agree on what
# counts as coverage. Kept at 0.40 under Gemini too, but it is currently non-binding:
# gemini-embedding-2's best-hit distances run ~0.02-0.19 on this KB (see RELATIVE_MARGIN
# below), so best + RELATIVE_MARGIN never approaches 0.40 in practice. It stays as a
# backstop for a fault with no real match in the KB at all, same role it played under
# MiniLM (docs/kb_quality_assessment.md section 7.2).
ABS_DISTANCE_CAP = {"mistake": 0.40, "finding": 0.40, "principle": 0.40, "consequence": 0.40}

# Relative gate, applied per kind: keep only hits within this margin of the best hit
# for that kind. Absolute thresholds do not transfer across exercises, but the *gap*
# between a real match and the next-best noise is consistent.
#
# 0.03, re-swept for Gemini (2026-09-14, docs/kb_quality_assessment.md section 10).
# gemini-embedding-2's cosine distances cluster far tighter than MiniLM's - the raw
# <=0.40 pool kb_coverage.py reports is saturated at 40/40 for nearly every fault, so
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

NO_MATCH_CONTEXT = "No highly relevant knowledge-base entries were found for these specific errors."


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _is_near_duplicate(text, kept_texts):
    """True if `text` restates something already kept (token Jaccard >= NEAR_DUP_JACCARD).

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
        if len(t & o) / len(t | o) >= NEAR_DUP_JACCARD:
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


def _search(vectorstore, query, exercise_id, kind, already_kept, code=None):
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
    which is exactly today's behaviour. Returns (kept, tagged) so callers/metrics can see
    which path served the query.
    """
    base_filter = {"exercise_id": exercise_id, "item_kind": {"$in": [kind]}}
    tagged = False
    hits = []
    if code:
        hits = vectorstore.similarity_search_with_score(
            query, k=CANDIDATE_K,
            filter={**base_filter, "fault_tags": {"$like": f"%|{code}|%"}},
        )
        tagged = bool(hits)
    if not hits:
        hits = vectorstore.similarity_search_with_score(query, k=CANDIDATE_K, filter=base_filter)
    if not hits:
        return [], False
    best = hits[0][1]
    cutoff = min(ABS_DISTANCE_CAP[kind], best + RELATIVE_MARGIN)
    kept = []
    for doc, score in hits:
        if score > cutoff:
            break
        text = _chunk_text(doc)
        if _is_near_duplicate(text, already_kept):
            continue
        kept.append((doc, score))
        already_kept.append(text)
        if len(kept) >= MAX_PER_KIND[kind]:
            break
    return kept, tagged


def retrieve_kb_blocks(vectorstore, exercise_id, exercise_name, error_types, raw_query=False):
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
    """
    kept_texts = []
    blocks = []
    metrics = []
    unknown_codes = []

    def collect(query, kinds, label, code=None):
        for kind in kinds:
            kept, tagged = _search(vectorstore, query, exercise_id, kind, kept_texts, code=code)
            # Best distance is measured on the raw pool, not on `kept`: a query whose
            # closest chunk fails the cap still tells us how far off it was. Probe the
            # SAME pool _search actually kept from (tagged if the tag-filter had hits,
            # untagged otherwise) so `best` describes the pool the gate saw.
            probe_filter = {"exercise_id": exercise_id, "item_kind": {"$in": [kind]}}
            if tagged:
                probe_filter["fault_tags"] = {"$like": f"%|{code}|%"}
            pool = vectorstore.similarity_search_with_score(query, k=1, filter=probe_filter)
            metrics.append({
                "error": label, "kind": kind, "query": query,
                "best": pool[0][1] if pool else None, "kept": len(kept), "tagged": tagged,
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


def retrieve_kb_context(vectorstore, exercise_id, exercise_name, error_types, raw_query=False):
    """Render retrieve_kb_blocks() as the text the system prompt expects. Returns
    (context_text, metrics); see retrieve_kb_blocks for the retrieval policy itself."""
    blocks, metrics = retrieve_kb_blocks(
        vectorstore, exercise_id, exercise_name, error_types, raw_query=raw_query)
    if not blocks:
        return NO_MATCH_CONTEXT, metrics

    lines = []
    for score, doc, kind, label in blocks:
        src = format_source(doc.metadata.get("source", ""))
        lines.append(f"[{kind} | re: {label} | source: {src}]\n{_chunk_text(doc)}")
    return "\n\n".join(lines), metrics


def metrics_table(metrics):
    """Markdown table, one row per error: query sent + best/kept per kind.

    A trailing `*` on a cell marks a tag-filtered hit (KB v5's fault_tags pre-pass found
    something, so `best`/`kept` describe that narrower pool, not the plain semantic one) -
    see _search()'s `tagged` return value. v4 collections never show `*`: every chunk's
    fault_tags is "", so the tag pass always comes back empty and falls back to plain search.
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
            else:
                best = f"{m['best']:.3f}" if m["best"] is not None else "—"
                flag = "*" if m.get("tagged") else ""
                cells.append(f"{best} / {m['kept']}{flag}")
        lines.append(f"| {error} | {row['query']} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


# Single source of truth for the system prompt. v5 kept a second, hand-copied copy in
# __main__ purely to print into the report, which is a quiet way for the documented
# prompt to drift away from the prompt actually sent.
SYSTEM_PROMPT = """You are an expert personal trainer and biomechanics specialist coaching an everyday gym-goer.
Your job is to turn the user's session data and the Knowledge Base context into feedback they can
understand and act on in their very next workout. The reader is not a clinician or a researcher:
they want to know what went wrong, why it matters to them, and exactly what to do about it.
Write the way a good coach talks on the gym floor, not the way a paper reads.

You will receive a JSON structure containing:
1. Current session details (10 reps summary and specific errors).
2. Historical comparison (data from their previous session).

Your tasks:
1. Progress Tracking: Compare their current performance with their previous session. Acknowledge
   any improvements or regressions in their correct rep count, overall score, and which errors
   disappeared or newly appeared.
2. Error Breakdown: for each distinct error in the session, cover these four things in order:
   - What it is, in plain words: describe the fault the way you would point it out to someone
     mid-set. If you use a technical term (e.g. "posterior pelvic tilt"), say what it means in
     everyday language in the same sentence ("your tailbone tucks under and your lower back rounds").
   - Why it matters: which joint or muscle takes the extra load and what that means in practice
     for the user - what they might feel, what it limits, what it risks over time. One or two
     sentences. Base this on the `consequence` entries in the Context when one passes the
     relevance rule below; if none does, keep this to general, non-specific terms.
   - How to fix it: concrete, doable actions rather than a description of ideal form. Give one
     cue to think about during the rep; any setup change that helps (stance, depth, tempo, load,
     a pause); a drill or lighter regression they can practise; and a simple self-check so they
     know it worked - something they can see in a mirror, feel, or notice on a phone video. Use
     `principle` entries from the Context as the basis for the correction.
   - Use the rep detail: if the error clusters in one phase (descending / ascending) or in the
     later reps of the set, say so and tailor the advice to it (e.g. stop the set a rep earlier,
     drop the load, slow the descent).
3. Next Session Plan: close with 2-3 short, prioritised things to do in their next workout.
4. Tone: encouraging, direct, and specific. Short paragraphs and bullets. No filler, no lecture.

How to read the Context: every entry starts with a header line of the form
[<kind> | re: <which error it was retrieved for> | source: <source name>], followed by the
entry text. `kind` is one of: mistake (a known incorrect form), finding (a concrete result
from that source), principle (general correct-form guidance). The source name is for internal
tracking only. Never quote the header line itself back to the user.

No citations in the feedback: do not name any study, author, organisation, URL, document title,
or "the knowledge base", and do not write "according to", "research shows", "as noted in", or
any similar attribution. Use the facts from the Context as plain statements in your own words.
The reader should see coaching, not a literature review.

Relevance rule: the `re:` label says which error an entry was RETRIEVED for, not that it
describes that error - retrieval is approximate and some entries are near misses. Before
using an entry for an error, check that its text plainly describes that error (or, for a
principle, the correct form that fixes it). Ignore an entry entirely - do not use it,
mention it, or reframe it as related - if it describes a different fault or a different
exercise variant, if it is a study protocol or setup detail with no consequence attached,
or if following it would push the user further into the error being discussed. Using fewer
entries accurately is better than using every entry.

Grounding rule: when an entry that passes the relevance rule contains a specific number,
percentage, or joint angle that helps the user (a depth target, a reason the fault matters),
you may state it - without attribution - as part of the explanation or the fix. If no relevant
principle exists for an error, describe the correction in general terms.
Do NOT state any specific number, percentage, joint angle, study finding, sample size, or date
range that does not appear verbatim in the Context below - even if you recognize the fact or
believe it to be true from your own general knowledge. Your own training knowledge must never
substitute for the Context; if a fact is not in the Context, treat it as unavailable. If the
Context has no specifics for a given error, fall back to general accepted coaching principles,
described in general terms only with no invented numbers.

Context from Knowledge Base:
{context}"""


LLM_MODEL = "gemini-3.5-flash-lite"
LLM_TEMPERATURE = 0.7
DEFAULT_COLLECTION = embedding_config.default_collection()

# v4 = KB rebuilt after docs/kb_quality_assessment.md: 4 off-topic sources removed,
# 17 new form/biomechanics papers curated under the tightened is_relevant, chunks
# tagged with applies_to_fault. Kept separate from v3 so the two can be compared with
# the same query code. As of 2026-09-14, kb_gemini_curated_v4 carried the same
# curated_data content re-embedded with Gemini (embedding_config.DEFAULT_MODE) -
# kb_local_curated_v4 (MiniLM) stays available as a fallback/comparison collection.
#
# v5 (2026-09-18, docs/kb_quality_assessment.md section 11) is now DEFAULT_COLLECTION:
# curated_data_v5 re-ingested, golden set updated with v5 phrasing, and curator.py's
# fault-tagging bug (variant-specific/hypertrophy statements tagged onto the generic
# fault code) fixed and patched into the existing data. Golden set: 10/10 hit,
# precision 0.62, bad 1 - better than v4's 8/10 / 0.33 / bad 1 on every axis. The
# RELATIVE_MARGIN/CANDIDATE_K/MAX_PER_KIND/ABS_DISTANCE_CAP numbers below are still the
# ones swept against v4 (section 10.4) - not yet re-swept for v5, though the golden-set
# result above says they still work well.


def generate_feedback_compare(session_data, use_rag=True, collection_name=DEFAULT_COLLECTION,
                              raw_query=False):
    """Returns (feedback_text, context_used, metrics) so the caller can log exactly what
    the model was given - v5 returned only the text, which is why verifying a suspected
    hallucination meant re-running the whole script with an ad-hoc print statement."""
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE, max_retries=1)

    system_prompt = SYSTEM_PROMPT

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Here is the exercise session data:\n{input}\n\nPlease evaluate my performance and tell me what to work on."),
    ])

    metrics = []
    if use_rag:
        connection = embedding_config.get_connection()
        from langchain_postgres.vectorstores import PGVector

        embeddings = embedding_config.get_embeddings()
        vectorstore = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=connection,
            use_jsonb=True,
        )

        all_error_types = set()
        for rep in session_data.get("reps_detail", []):
            errors = rep.get("errors", [])
            for error in errors:
                all_error_types.add(error.get("error_type"))

        exercise_name = session_data.get("name") or session_data.get("exercise_id", "")
        context, metrics = retrieve_kb_context(
            vectorstore, session_data.get("exercise_id"), exercise_name, all_error_types,
            raw_query=raw_query,
        )
    else:
        context = "No external context provided."

    rag_chain = (
        {"context": lambda x: context, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = rag_chain.invoke(json.dumps(session_data, indent=2))
            print(f"Call successful, sleeping 15s to respect rate limits...")
            time.sleep(15)
            return response, context, metrics
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Sleeping for 45 seconds before retry {attempt+1}/{max_retries}...")
                    time.sleep(45)
                    continue
            return f"Error occurred during generation: {e}", context, metrics


def get_mocks(path="mock_data/mock_sessions.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_args():
    import argparse
    ap = argparse.ArgumentParser(
        description="Generate RAG vs no-RAG feedback for every mock session and write a comparison report.")
    ap.add_argument("--mock", default="mock_data/mock_sessions.json",
                    help="session file to run (default: mock_data/mock_sessions.json)")
    ap.add_argument("--raw-query", action="store_true",
                    help="bypass error_taxonomy.py and embed error_type verbatim (A/B control)")
    ap.add_argument("--collection", default=DEFAULT_COLLECTION,
                    help=f"pgvector collection to retrieve from (default: {DEFAULT_COLLECTION})")
    ap.add_argument("--out", default="compare_result.md",
                    help="report filename inside compare_output/")
    ap.add_argument("--skip-no-rag", action="store_true",
                    help="only run the RAG side (halves the LLM calls when the interest is retrieval)")
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    mocks = get_mocks(args.mock)

    system_prompt_text = SYSTEM_PROMPT

    # Generated from the actual run parameters. The previous hand-written status blob
    # drifted from the code (it described v7 while the closing print still said v6);
    # per-version narrative now lives in docs/ and gets written after reading the run.
    run_config_md = f"""## Run configuration

| parameter | value |
|---|---|
| mock file | `{args.mock}` |
| query mode | {"**raw** — `error_type` embedded verbatim, taxonomy bypassed" if args.raw_query else "**taxonomy** — `error_type` resolved through `error_taxonomy.py`"} |
| collection | `{args.collection}` |
| LLM | `{LLM_MODEL}` @ temperature {LLM_TEMPERATURE} |
| no-RAG side | {"skipped" if args.skip_no_rag else "run"} |
| retrieval gates | CANDIDATE_K={CANDIDATE_K}, MAX_PER_KIND={MAX_PER_KIND}, ABS_DISTANCE_CAP={ABS_DISTANCE_CAP}, RELATIVE_MARGIN={RELATIVE_MARGIN}, NEAR_DUP_JACCARD={NEAR_DUP_JACCARD} |

Retrieval metrics per exercise: `best` = cosine distance of the closest chunk of that kind in the whole
collection (before any gate), `kept` = chunks that passed the relative/absolute gates and de-duplication
and were actually placed in the context.

---

"""

    os.makedirs("compare_output", exist_ok=True)
    out_path = os.path.join("compare_output", args.out)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Feedback Comparison: RAG vs NO-RAG\n\n")
        f.write(run_config_md)
        f.write("## System Prompt Used\n")
        f.write("```text\n")
        f.write(system_prompt_text + "\n")
        f.write("```\n\n")
        f.write("---\n\n")

        for mock in mocks:
            exercise_name = mock["name"]
            print(f"Processing {exercise_name}...")

            f.write(f"## Exercise: {exercise_name}\n\n")

            rag_output, rag_context, metrics = generate_feedback_compare(
                mock, use_rag=True, collection_name=args.collection, raw_query=args.raw_query
            )
            f.write("### Retrieval metrics\n")
            f.write(metrics_table(metrics) + "\n\n")
            # The retrieved context is written into the report on purpose: v5's
            # hallucination finding could only be confirmed by re-running the script with
            # a manual print. Shipping the context next to the output makes every "did it
            # cite something that was actually there?" check a matter of reading one file.
            f.write("### Retrieved KB Context (RAG run)\n")
            f.write("```text\n" + rag_context + "\n```\n\n")
            f.write("### WITH RAG\n")
            f.write(rag_output + "\n\n")

            if not args.skip_no_rag:
                no_rag_output, _, _ = generate_feedback_compare(mock, use_rag=False)
                f.write("### WITHOUT RAG\n")
                f.write(no_rag_output + "\n\n")
            f.write("---\n\n")

    print(f"Done! Results saved to {out_path}")
