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

KINDS = ("mistake", "finding", "principle")


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
        mrows = [r for r in rows if r["mode"] == mode and r["kind"] != "-"]
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
    ap.add_argument("--show-kept", action="store_true", help="list every kept chunk with its good/bad/neutral tag")
    ap.add_argument("--out", help="also write the markdown report to this path")
    args = ap.parse_args()

    if args.margin is not None:
        trc.RELATIVE_MARGIN = args.margin
    trc.ABS_DISTANCE_CAP = {**trc.ABS_DISTANCE_CAP, **_parse_kv(args.cap, float)}
    trc.MAX_PER_KIND = {**trc.MAX_PER_KIND, **_parse_kv(args.max_per_kind, int)}

    with open(args.golden, encoding="utf-8") as f:
        golden = json.load(f)["faults"]
    with open(args.mock, encoding="utf-8") as f:
        mocks = json.load(f)
    modes = ["single", "session"] if args.mode == "both" else [args.mode]
    collections = args.collection or [trc.DEFAULT_COLLECTION]

    import embedding_config
    from langchain_postgres.vectorstores import PGVector
    embeddings = embedding_config.get_embeddings()

    report = [
        "# Retrieval golden-set evaluation",
        "",
        f"gates: CANDIDATE_K={trc.CANDIDATE_K}, MAX_PER_KIND={trc.MAX_PER_KIND}, "
        f"ABS_DISTANCE_CAP={trc.ABS_DISTANCE_CAP}, RELATIVE_MARGIN={trc.RELATIVE_MARGIN}, "
        f"NEAR_DUP_JACCARD={trc.NEAR_DUP_JACCARD}",
        f"golden: `{args.golden}` · mock: `{args.mock}`",
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

    text = "\n".join(report)
    print(text)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\nwritten: {args.out}")


if __name__ == "__main__":
    main()
