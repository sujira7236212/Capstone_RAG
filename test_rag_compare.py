import os
import json
import warnings
from dataclasses import replace

from dotenv import load_dotenv

import embedding_config
from rag_core.generate import GENERATION_ERROR, LLM_TEMPERATURE, build_chain, render_input
from rag_core.prompt import SYSTEM_PROMPT, model_payload
from rag_core.retrieval import DEFAULT_CONFIG, metrics_table, open_vectorstore, retrieve_kb_context

warnings.filterwarnings("ignore")

load_dotenv()

# The retrieval gate, the system prompt and the chain live in rag_core/ (2026-10-25,
# docs/plans/app_integration_plan.md A1) so the feedback service runs the same code. This file
# is the batch runner: mock sessions in, a RAG vs no-RAG report out.

LLM_MODEL = "gemini-3.5-flash-lite"
DEFAULT_COLLECTION = embedding_config.default_collection()

# v4 = KB rebuilt after docs/kb/kb_quality_assessment.md: 4 off-topic sources removed,
# 17 new form/biomechanics papers curated under the tightened is_relevant, chunks
# tagged with applies_to_fault. Kept separate from v3 so the two can be compared with
# the same query code. As of 2026-09-14, kb_gemini_curated_v4 carried the same
# curated_data content re-embedded with Gemini (embedding_config.DEFAULT_MODE) -
# kb_local_curated_v4 (MiniLM) stays available as a fallback/comparison collection.
#
# v5 (2026-09-18, docs/kb/kb_quality_assessment.md section 11) is now DEFAULT_COLLECTION:
# curated_data_v5 re-ingested, golden set updated with v5 phrasing, and curator.py's
# fault-tagging bug (variant-specific/hypertrophy statements tagged onto the generic
# fault code) fixed and patched into the existing data. Golden set: 10/10 hit,
# precision 0.62, bad 1 - better than v4's 8/10 / 0.33 / bad 1 on every axis. The
# RELATIVE_MARGIN/CANDIDATE_K/MAX_PER_KIND/ABS_DISTANCE_CAP numbers below are still the
# ones swept against v4 (section 10.4) - not yet re-swept for v5, though the golden-set
# result above says they still work well.
#
# v6 (2026-10-03) is DEFAULT_COLLECTION now: KB v6 under the 12-rule taxonomy
# (docs/progress/t3_curation_status.md). The gate numbers above are still the v4 sweep, not yet
# measured on v6 (eval_v6_plan E6).
#
# v6b (2026-10-25) is DEFAULT_COLLECTION now: v6 + curation rounds 3 and 4
# (docs/kb/tag_coverage_v6b_2026-10-24.md). v6 is kept unchanged as the reference.



def generate_feedback_compare(session_data, use_rag=True, collection_name=DEFAULT_COLLECTION,
                              raw_query=False, samples=1, generate=True, cfg=DEFAULT_CONFIG):
    """Returns (feedback_texts, context_used, metrics) so the caller can log exactly what
    the model was given - v5 returned only the text, which is why verifying a suspected
    hallucination meant re-running the whole script with an ad-hoc print statement.

    `samples`: how many answers to generate from the same context (checkpoint G1 - at
    temperature 0.7 one answer per session cannot tell a retrieval change from sampling
    noise). Retrieval runs once; `feedback_texts` is a list of `samples` strings. A failed
    call yields a string starting with GENERATION_ERROR in its slot, not an exception.

    `generate=False` (--context-only): retrieval only, no LLM call - returns ([], context,
    metrics). The only paid call left is the query embedding.

    `cfg`: the retrieval gate settings (rag_core.retrieval.RetrievalConfig)."""
    metrics = []
    if use_rag:
        vectorstore = open_vectorstore(collection_name)
        all_error_types = set()
        for rep in session_data.get("reps_detail", []):
            errors = rep.get("errors", [])
            for error in errors:
                all_error_types.add(error.get("error_type"))

        exercise_name = session_data.get("name") or session_data.get("exercise_id", "")
        context, metrics = retrieve_kb_context(
            vectorstore, session_data.get("exercise_id"), exercise_name, all_error_types,
            raw_query=raw_query, cfg=cfg,
        )
    else:
        context = "No external context provided."

    if not generate:
        return [], context, metrics

    rag_chain = build_chain(context, LLM_MODEL)
    payload = render_input(session_data)

    import time

    def one_call():
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = rag_chain.invoke(payload)
                print(f"Call successful, sleeping 15s to respect rate limits...")
                time.sleep(15)
                return response
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if attempt < max_retries - 1:
                        print(f"Rate limit hit. Sleeping for 45 seconds before retry {attempt+1}/{max_retries}...")
                        time.sleep(45)
                        continue
                return f"{GENERATION_ERROR}: {e}"

    return [one_call() for _ in range(samples)], context, metrics


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
    d = DEFAULT_CONFIG  # the gate's defaults; see rag_core/retrieval.py for each one
    ap.add_argument("--tag-mode", choices=["prefer", "strict", "union"], default=d.tag_mode,
                    help=f"how fault_tags combine with semantic search, see TAG_MODE (default: {d.tag_mode})")
    ap.add_argument("--kind-pool", choices=["split", "single"], default=d.kind_pool,
                    help=f"per-kind quotas or one shared budget, see KIND_POOL (default: {d.kind_pool})")
    ap.add_argument("--queries", choices=["fault", "profile"], default=d.queries,
                    help=f"taxonomy query only, or what/why/fix per fault, see QUERIES (default: {d.queries})")
    ap.add_argument("--hybrid", action=argparse.BooleanOptionalAction, default=d.hybrid,
                    help=f"add BM25 next to vector search, see HYBRID (default: {d.hybrid})")
    ap.add_argument("--rerank", action=argparse.BooleanOptionalAction, default=d.rerank,
                    help=f"cross-encoder gate instead of RELATIVE_MARGIN, see RERANK (default: {d.rerank})")
    ap.add_argument("--samples", type=int, default=1,
                    help="answers generated per session and side from the same context (default 1); "
                         "every answer also goes to the JSON written next to the report, which "
                         "eval/judge_pairwise.py reads")
    ap.add_argument("--context-only", action="store_true",
                    help="retrieve and write the context + metrics for every session, generate no "
                         "answers (no LLM call on either side; implies --skip-no-rag, samples 0)")
    args = ap.parse_args()
    if args.samples < 1:
        ap.error("--samples must be >= 1")
    if args.context_only:
        args.skip_no_rag = True
        args.samples = 0
    return args


if __name__ == "__main__":
    args = parse_args()
    cfg = replace(DEFAULT_CONFIG, tag_mode=args.tag_mode, kind_pool=args.kind_pool, queries=args.queries,
                  hybrid=args.hybrid, rerank=args.rerank)
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
| generation | {"**off** — `--context-only`: context and metrics only, no LLM call" if args.context_only else "on"} |
| samples per session | {args.samples} |
| retrieval gates | {cfg.summary()} |

Retrieval metrics per exercise: `best` = cosine distance of the closest chunk of that kind in the whole
collection (before any gate), `kept` = chunks that passed the relative/absolute gates and de-duplication
and were actually placed in the context.

---

"""

    def sample_heading(side, i):
        # One sample keeps the historical heading. More than one numbers them; the suffix
        # still matches eval/eval_generation.py's section pattern, which scores each sample.
        return f"### {side}\n" if args.samples == 1 else f"### {side} (sample {i}/{args.samples})\n"

    import hashlib
    out_path = os.path.join("compare_output", args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)  # --out may name a subfolder, e.g. baseline_v14/x.md
    # Machine-readable twin of the report: every sample, plus the context and the exact
    # payload the model saw, so eval/judge_pairwise.py never has to parse the markdown back.
    json_path = os.path.splitext(out_path)[0] + ".json"
    run = {
        "report": args.out, "mock": args.mock, "collection": args.collection,
        "raw_query": args.raw_query, "llm": LLM_MODEL, "temperature": LLM_TEMPERATURE,
        "samples": args.samples, "context_only": args.context_only,
        "system_prompt_sha1": hashlib.sha1(SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        "retrieval": {"TAG_MODE": cfg.tag_mode, "KIND_POOL": cfg.kind_pool, "QUERIES": cfg.queries,
                      "HYBRID": cfg.hybrid, "RERANK": cfg.rerank},
        "sessions": [],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Feedback Comparison: RAG vs NO-RAG\n\n")
        f.write(run_config_md)
        f.write("## System Prompt Used\n")
        f.write("```text\n")
        f.write(system_prompt_text + "\n")
        f.write("```\n\n")
        f.write("---\n\n")

        for mock in mocks:
            block_name = mock.get("report_label") or mock["name"]
            print(f"Processing {block_name}...")

            f.write(f"## Exercise: {block_name}\n\n")

            rag_outputs, rag_context, metrics = generate_feedback_compare(
                mock, use_rag=True, collection_name=args.collection, raw_query=args.raw_query,
                samples=args.samples, generate=not args.context_only, cfg=cfg,
            )
            f.write("### Retrieval metrics\n")
            f.write(metrics_table(metrics) + "\n\n")
            # The retrieved context is written into the report on purpose: v5's
            # hallucination finding could only be confirmed by re-running the script with
            # a manual print. Shipping the context next to the output makes every "did it
            # cite something that was actually there?" check a matter of reading one file.
            f.write("### Retrieved KB Context (RAG run)\n")
            f.write("```text\n" + rag_context + "\n```\n\n")
            for i, text in enumerate(rag_outputs, 1):
                f.write(sample_heading("WITH RAG", i))
                f.write(text + "\n\n")

            no_rag_outputs = []
            if not args.skip_no_rag:
                no_rag_outputs, _, _ = generate_feedback_compare(mock, use_rag=False, samples=args.samples)
                for i, text in enumerate(no_rag_outputs, 1):
                    f.write(sample_heading("WITHOUT RAG", i))
                    f.write(text + "\n\n")
            f.write("---\n\n")
            f.flush()

            run["sessions"].append({
                "label": block_name, "exercise_id": mock.get("exercise_id"),
                "payload": model_payload(mock),
                "context": rag_context, "metrics": metrics,
                "rag": rag_outputs, "no_rag": no_rag_outputs,
            })
            # Rewritten after every session so an interrupted run keeps what it paid for.
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(run, jf, ensure_ascii=False, indent=1)

    print(f"Done! Results saved to {out_path} and {json_path}")
