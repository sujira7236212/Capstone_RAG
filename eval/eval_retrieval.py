"""Score the retrieval gate against eval/golden_chunks.json.

kb_coverage.py answers "is there anything in the KB for this fault?" by counting the
top-40 pool within 0.40. This script answers the question that actually decides the
feedback quality: of the chunks the gate in test_rag_compare.py PUTS INTO THE CONTEXT
under a fault's label, how many describe that fault (good), how many describe a
different fault (bad - the model will cite them as if they explained this one), and
how many are neutral filler.

Two modes, both run by default:
    single   - every golden fault retrieved on its own, i.e. retrieve_kb_blocks(..., [code]).
               Covers all 10 faults regardless of what the mock sessions contain.
    session  - every session in --mock, retrieved exactly as test_rag_compare.py does it
               (all errors of the session at once, shared de-duplication across errors).
               Scores can differ from single mode because a chunk already kept for one
               error is skipped for the next.

Gate parameters can be overridden from the command line so a retuning is one command
and not an edit-run-diff cycle:
    python eval/eval_retrieval.py --margin 0.10 --cap mistake=0.40,finding=0.38
    EMBEDDING_MODE=local python eval/eval_retrieval.py   # compare against the MiniLM fallback
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))

import test_rag_compare as trc
from error_taxonomy import resolve

# `consequence` (KB v5) is retrieved and put into the context like the other three, so it is
# scored too. The golden-set summary line (hit / precision / bad) is still computed over
# LEGACY_KINDS only, so it stays comparable with every number recorded before 2026-09-25
# (v5: 10/10 · 0.60 · bad 1) - golden_chunks.json has no consequence patterns yet, so
# counting consequence chunks there would only add "neutral" and drag precision down.
KINDS = ("mistake", "finding", "principle", "consequence")
LEGACY_KINDS = ("mistake", "finding", "principle")


def _contains_any(text, patterns):
    t = text.lower()
    return any(p.lower() in t for p in patterns)


def _score_kind(kept_texts, golden, kind):
    """kept_texts: chunk texts the gate kept for this (fault, kind).
    Returns dict with counts + which must_hit patterns were and were not found."""
    must = golden["must_hit"].get(kind, [])
    must_not = golden["must_not_hit"].get(kind, [])
    good, bad, neutral = [], [], []
    for t in kept_texts:
        if _contains_any(t, must_not):
            bad.append(t)
        elif _contains_any(t, must):
            good.append(t)
        else:
            neutral.append(t)
    found = [p for p in must if any(p.lower() in t.lower() for t in kept_texts)]
    return {
        "kept": len(kept_texts), "good": good, "bad": bad, "neutral": neutral,
        "must_total": len(must), "must_found": found,
        "must_missing": [p for p in must if p not in found],
    }


def _blocks_by_label(blocks):
    out = {}
    for score, doc, kind, label in blocks:
        out.setdefault(label, {}).setdefault(kind, []).append((score, trc._chunk_text(doc)))
    return out


def _best(metrics, label, kind):
    for m in metrics:
        if m["error"] == label and m["kind"] == kind:
            return m["best"]
    return None


def evaluate(vs, golden_faults, mocks, modes):
    """Yield one result row per (mode, session/fault, kind)."""
    rows = []
    by_key = {(g["exercise_id"], g["code"]): g for g in golden_faults}

    if "single" in modes:
        for g in golden_faults:
            blocks, metrics = trc.retrieve_kb_blocks(vs, g["exercise_id"], g["exercise_id"], [g["code"]])
            grouped = _blocks_by_label(blocks).get(g["code"], {})
            for kind in KINDS:
                texts = [t for _, t in grouped.get(kind, [])]
                rows.append({
                    "mode": "single", "exercise_id": g["exercise_id"], "code": g["code"],
                    "kind": kind, "best": _best(metrics, g["code"], kind),
                    **_score_kind(texts, g, kind),
                })

    if "session" in modes:
        for mock in mocks:
            ex = mock["exercise_id"]
            errors = sorted({e["error_type"] for r in mock.get("reps_detail", []) for e in r.get("errors", [])})
            if not errors:
                rows.append({"mode": "session", "exercise_id": ex, "code": "(no errors - principle path, not scored)",
                             "kind": "-", "best": None, "kept": 0, "good": [], "bad": [], "neutral": [],
                             "must_total": 0, "must_found": [], "must_missing": []})
                continue
            blocks, metrics = trc.retrieve_kb_blocks(vs, ex, mock.get("name", ex), errors)
            grouped = _blocks_by_label(blocks)
            for err in errors:
                code = resolve(err, ex)["code"]
                g = by_key.get((ex, code))
                if not g:
                    print(f"  [golden] no entry for {ex}/{code} (from error_type '{err}') - skipped")
                    continue
                for kind in KINDS:
                    texts = [t for _, t in grouped.get(err, {}).get(kind, [])]
                    rows.append({
                        "mode": "session", "exercise_id": ex, "code": code, "kind": kind,
                        "best": _best(metrics, err, kind), **_score_kind(texts, g, kind),
                    })
    return rows


def _fmt_best(b):
    return "—" if b is None else f"{b:.3f}"


def render(rows, collection, show_kept):
    """Markdown: one table per mode, then a summary block."""
    out = []
    for mode in ("single", "session"):
        mrows = [r for r in rows if r["mode"] == mode]
        if not mrows:
            continue
        out.append(f"\n### {collection} — mode: {mode}\n")
        out.append("| exercise | fault | kind | best | kept | good | bad | neutral | must_hit found | missing must_hit |")
        out.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in mrows:
            if r["kind"] == "-":
                out.append(f"| {r['exercise_id']} | {r['code']} | | | | | | | | |")
                continue
            found = f"{len(r['must_found'])}/{r['must_total']}" if r["must_total"] else "n/a"
            bad_flag = " 🔴" if r["bad"] else ""
            missing = "; ".join(r["must_missing"]) if r["must_missing"] else ""
            out.append(f"| {r['exercise_id']} | {r['code']} | {r['kind']} | {_fmt_best(r['best'])} | "
                       f"{r['kept']} | {len(r['good'])} | {len(r['bad'])}{bad_flag} | {len(r['neutral'])} | "
                       f"{found} | {missing} |")
        if show_kept:
            out.append("")
            for r in mrows:
                if r["kind"] == "-":
                    continue
                for tag, lst in (("GOOD", r["good"]), ("BAD ", r["bad"]), ("neut", r["neutral"])):
                    for t in lst:
                        out.append(f"    {r['exercise_id']:10s} {r['code']:31s} {r['kind']:8s} {tag}  {t}")

    for mode in ("single", "session"):
        mrows = [r for r in rows if r["mode"] == mode and r["kind"] in LEGACY_KINDS]
        if not mrows:
            continue
        faults = sorted({(r["exercise_id"], r["code"]) for r in mrows})
        hit = sum(1 for f in faults if any(r["good"] for r in mrows
                                            if (r["exercise_id"], r["code"]) == f and r["kind"] == "mistake"))
        kept = sum(r["kept"] for r in mrows)
        good = sum(len(r["good"]) for r in mrows)
        bad = sum(len(r["bad"]) for r in mrows)
        neutral = sum(len(r["neutral"]) for r in mrows)
        bad_faults = sorted({(r["exercise_id"], r["code"]) for r in mrows if r["bad"]})
        out.append(f"\n**{mode} summary ({collection})** — faults with ≥1 correct mistake chunk: "
                   f"**{hit}/{len(faults)}** · context chunks: {kept} = "
                   f"good {good} / bad **{bad}** / neutral {neutral} · "
                   f"precision(good/kept) = {good / kept:.2f}" if kept else
                   f"\n**{mode} summary ({collection})** — nothing kept")
        if bad_faults:
            out.append("  bad chunks under: " + ", ".join(f"{e}/{c}" for e, c in bad_faults))
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Recall against eval/relevance_pool.json (single mode only).
#
# Unit of recall is a FACT, not a chunk: relevant chunks are clustered by the same
# near-duplicate test the gate uses (trc._is_near_duplicate, Jaccard >= NEAR_DUP_JACCARD),
# because the gate drops paraphrases on purpose - losing the 4th restatement of one sentence
# is not a miss. A fact counts as covered when any kept chunk is that chunk or a near-dup.
#
# Every uncovered fact gets the reason its closest member never made it in:
#   tag_spelling - chunk IS tagged with this fault, but spelled so the gate's LIKE filter
#                  misses it ("|knee_valgus|"); the tagged pool was used for its kind.
#   tag_filter   - chunk has no tag for this fault, and the tagged pool was non-empty for its
#                  kind, so the untagged search that would have seen it never ran (TAG_MODE
#                  "prefer" only - under "union" the untagged search always runs).
#   rank         - chunk was eligible for its kind's search but not in the top CANDIDATE_K
#                  (KIND_POOL "single": not in the top CANDIDATE_K * kinds of the shared search).
#   margin       - in the top CANDIDATE_K but past best + RELATIVE_MARGIN.
#   quota        - within the margin but MAX_PER_KIND was already full (KIND_POOL "single":
#                  the shared budget, sum of MAX_PER_KIND).
#   dup          - near-dup of a chunk kept for another fault (session mode only; rare here).
# ---------------------------------------------------------------------------

MISS_REASONS = ("tag_spelling", "tag_filter", "rank", "margin", "quota", "dup")


def _cluster(texts):
    clusters = []
    for t in texts:
        for c in clusters:
            if trc._is_near_duplicate(t, c):
                c.append(t)
                break
        else:
            clusters.append([t])
    return clusters


def _miss_reason(members, chunk_meta, trace_by_text, tagged_by_kind, code):
    traced = [trace_by_text[t] for t in members if t in trace_by_text]
    if traced:
        return min(traced, key=lambda e: e["score"])["reason"]
    reasons = []
    for t in members:
        m = chunk_meta[t]
        if tagged_by_kind.get(m["kind"]) and f"|{code}|" not in (m["fault_tags"] or ""):
            spelled = code in {x.strip().replace("_", " ").lower()
                               for x in (m["fault_tags"] or "").split("|") if x.strip()}
            reasons.append("tag_spelling" if spelled else "tag_filter")
        else:
            reasons.append("rank")
    # The most fixable reason first: a spelling fix recovers it with no retrieval change.
    for r in ("tag_spelling", "rank", "tag_filter"):
        if r in reasons:
            return r
    return "rank"


def evaluate_recall(vs, golden_faults, pool):
    by_key = {(f["exercise_id"], f["code"]): f for f in pool["faults"]}
    out = []
    for g in golden_faults:
        f = by_key.get((g["exercise_id"], g["code"]))
        if not f:
            print(f"  [pool] no entry for {g['exercise_id']}/{g['code']} - recall skipped")
            continue
        trace = []
        blocks, metrics = trc.retrieve_kb_blocks(vs, g["exercise_id"], g["exercise_id"], [g["code"]],
                                                 trace=trace)
        context = [trc._chunk_text(doc) for _, doc, _, label in blocks if label == g["code"]]
        ctx_kinds = [kind for _, _, kind, label in blocks if label == g["code"]]
        label_of = {c["text"]: c["label"] for c in f["chunks"]}
        chunk_meta = {c["text"]: c for c in f["chunks"]}

        def ctx_label(t):
            if t in label_of:
                return label_of[t]
            for pt, lab in label_of.items():
                if trc._is_near_duplicate(t, [pt]):
                    return lab
            return "unlabeled"

        ctx_labels = [ctx_label(t) for t in context]
        trace_by_text = {}
        for e in trace:
            if e["text"] not in trace_by_text or e["score"] < trace_by_text[e["text"]]["score"]:
                trace_by_text[e["text"]] = e
        tagged_by_kind = {m["kind"]: m["tag_exclusive"] for m in metrics if m["error"] == g["code"]}

        clusters = _cluster([c["text"] for c in f["chunks"] if c["label"] == "relevant"])
        covered, missed = 0, []
        for members in clusters:
            if any(t in context or trc._is_near_duplicate(t, context) for t in members):
                covered += 1
            else:
                missed.append((_miss_reason(members, chunk_meta, trace_by_text, tagged_by_kind, g["code"]),
                               members))
        out.append({
            "exercise_id": g["exercise_id"], "code": g["code"],
            "candidates": len(f["chunks"]), "facts": len(clusters), "covered": covered,
            "kept": len(context),
            "ctx": {lab: ctx_labels.count(lab) for lab in ("relevant", "wrong_fault", "irrelevant", "unlabeled")},
            "ctx_kinds": {k: ctx_kinds.count(k) for k in KINDS},
            "missed": missed,
        })
    return out


def render_recall(rows, collection, show_missed):
    out = [f"\n### {collection} — recall vs relevance pool (single mode)\n",
           "`facts` = relevant chunks in the pool after near-dup clustering · `recall` = facts with a chunk "
           "(or near-dup) in the context · ctx columns = judge labels of the chunks actually kept.",
           f"`ceiling` = best recall possible at the current context budget "
           f"(sum(MAX_PER_KIND) = {sum(trc.MAX_PER_KIND.values())} chunks per fault): min(facts, budget) / facts. "
           "Compare recall against it, and compare steps only at the same budget.",
           "",
           "| exercise | fault | candidates | facts | covered | recall | ceiling | kept | ctx relevant | ctx wrong_fault "
           "| ctx irrelevant | ctx unlabeled | " + " | ".join(f"miss: {r}" for r in MISS_REASONS) + " |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|" + "---|" * len(MISS_REASONS)]
    budget = sum(trc.MAX_PER_KIND.values())
    for r in rows:
        rec = r["covered"] / r["facts"] if r["facts"] else 0.0
        ceil = min(r["facts"], budget) / r["facts"] if r["facts"] else 0.0
        miss = [sum(1 for reason, _ in r["missed"] if reason == m) for m in MISS_REASONS]
        c = r["ctx"]
        out.append(f"| {r['exercise_id']} | {r['code']} | {r['candidates']} | {r['facts']} | {r['covered']} | "
                   f"{rec:.2f} | {ceil:.2f} | {r['kept']} | {c['relevant']} | {c['wrong_fault']} | {c['irrelevant']} | "
                   f"{c['unlabeled']} | " + " | ".join(str(x) for x in miss) + " |")
    facts = sum(r["facts"] for r in rows)
    covered = sum(r["covered"] for r in rows)
    kept = sum(r["kept"] for r in rows)
    rel = sum(r["ctx"]["relevant"] for r in rows)
    wrong = sum(r["ctx"]["wrong_fault"] for r in rows)
    scored = [r for r in rows if r["facts"]]
    macro = sum(r["covered"] / r["facts"] for r in scored) / max(1, len(scored))
    ceil_micro = sum(min(r["facts"], budget) for r in rows) / facts if facts else 0.0
    totals = {m: sum(1 for r in rows for reason, _ in r["missed"] if reason == m) for m in MISS_REASONS}
    if facts and kept:
        out.append(f"\n**recall summary ({collection})** — facts covered {covered}/{facts} · "
                   f"recall micro **{covered / facts:.2f}** (ceiling {ceil_micro:.2f}) / macro **{macro:.2f}** · "
                   f"context {kept} chunks: relevant {rel} / wrong_fault **{wrong}** · "
                   f"pool-precision(relevant/kept) = {rel / kept:.2f}")
    else:
        out.append(f"\n**recall summary ({collection})** — nothing to score")
    out.append("  missed facts by reason: " + ", ".join(f"{m} {n}" for m, n in totals.items()))
    out.append("  context by kind: " + ", ".join(f"{k} {sum(r['ctx_kinds'][k] for r in rows)}" for k in KINDS)
               + f" · faults missing a kind: " + ", ".join(
                   f"{k} {sum(1 for r in rows if not r['ctx_kinds'][k])}" for k in KINDS))
    if show_missed:
        out.append("")
        for r in rows:
            for reason, members in r["missed"]:
                out.append(f"    {r['exercise_id']:10s} {r['code']:31s} {reason:12s} {members[0]}")
    return "\n".join(out)


def _parse_kv(s, cast):
    out = {}
    if s:
        for part in s.split(","):
            k, v = part.split("=")
            out[k.strip()] = cast(v)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--collection", action="append", help="repeatable; default trc.DEFAULT_COLLECTION")
    ap.add_argument("--golden", default="eval/golden_chunks.json")
    ap.add_argument("--mock", default="mock_data/mock_sessions.json")
    ap.add_argument("--mode", choices=["single", "session", "both"], default="both")
    ap.add_argument("--margin", type=float, help="override RELATIVE_MARGIN")
    ap.add_argument("--cap", help="override ABS_DISTANCE_CAP, e.g. mistake=0.40,finding=0.38")
    ap.add_argument("--max-per-kind", help="override MAX_PER_KIND, e.g. mistake=3,finding=2")
    ap.add_argument("--tag-mode", choices=["prefer", "union"], help="override TAG_MODE")
    ap.add_argument("--kind-pool", choices=["split", "single"], help="override KIND_POOL")
    ap.add_argument("--show-kept", action="store_true", help="list every kept chunk with its good/bad/neutral tag")
    ap.add_argument("--pool", default="eval/relevance_pool.json",
                    help="relevance pool from eval/build_relevance_pool.py; enables recall (single mode). "
                         "Pass '' to skip.")
    ap.add_argument("--show-missed", action="store_true", help="list every relevant fact the context missed")
    ap.add_argument("--out", help="also write the markdown report to this path")
    args = ap.parse_args()

    if args.margin is not None:
        trc.RELATIVE_MARGIN = args.margin
    trc.ABS_DISTANCE_CAP = {**trc.ABS_DISTANCE_CAP, **_parse_kv(args.cap, float)}
    trc.MAX_PER_KIND = {**trc.MAX_PER_KIND, **_parse_kv(args.max_per_kind, int)}
    if args.tag_mode:
        trc.TAG_MODE = args.tag_mode
    if args.kind_pool:
        trc.KIND_POOL = args.kind_pool

    with open(args.golden, encoding="utf-8") as f:
        golden = json.load(f)["faults"]
    with open(args.mock, encoding="utf-8") as f:
        mocks = json.load(f)
    modes = ["single", "session"] if args.mode == "both" else [args.mode]
    pool = None
    if args.pool and os.path.exists(args.pool):
        with open(args.pool, encoding="utf-8") as f:
            pool = json.load(f)
        report_pool = (f"relevance pool: `{args.pool}` (judge {pool.get('judge')}, built {pool.get('built')}, "
                       f"collection {pool.get('collection')})")
    else:
        report_pool = "relevance pool: none (recall not computed)"
    collections = args.collection or [trc.DEFAULT_COLLECTION]

    import embedding_config
    from langchain_postgres.vectorstores import PGVector
    embeddings = embedding_config.get_embeddings()

    report = [
        "# Retrieval golden-set evaluation",
        "",
        f"gates: CANDIDATE_K={trc.CANDIDATE_K}, MAX_PER_KIND={trc.MAX_PER_KIND}, "
        f"ABS_DISTANCE_CAP={trc.ABS_DISTANCE_CAP}, RELATIVE_MARGIN={trc.RELATIVE_MARGIN}, "
        f"NEAR_DUP_JACCARD={trc.NEAR_DUP_JACCARD}, TAG_MODE={trc.TAG_MODE}"
        + (f", TAG_BONUS={trc.TAG_BONUS}" if trc.TAG_MODE == "union" else "")
        + f", KIND_POOL={trc.KIND_POOL}",
        f"golden: `{args.golden}` · mock: `{args.mock}`",
        report_pool,
        "",
        "`best` = closest chunk of that kind in the whole collection (before the gate). "
        "`good` = kept chunk matching a must_hit pattern, `bad` = matching a must_not_hit pattern "
        "(a different fault, labelled as this one), `neutral` = neither.",
    ]
    for coll in collections:
        vs = PGVector(embeddings=embeddings, collection_name=coll,
                      connection=embedding_config.get_connection(), use_jsonb=True)
        rows = evaluate(vs, golden, mocks, modes)
        report.append(render(rows, coll, args.show_kept))
        if pool and "single" in modes:
            report.append(render_recall(evaluate_recall(vs, golden, pool), coll, args.show_missed))

    text = "\n".join(report)
    print(text)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\nwritten: {args.out}")


if __name__ == "__main__":
    main()
