"""Derive a TAG_MODE "strict" context from a TAG_MODE "prefer" compare_result JSON, offline.

    python eval/strict_offline_from_compare.py compare_output/baseline_v14/compare_result_v14_lunge.json

Strict differs from prefer only for an (error, kind) whose error resolved to a fault code
and whose kind has no chunk tagged for that code (metrics row: tagged False, error not
"general principles"). Under prefer those kinds were filled by the untagged fallback; under
strict they are empty. So the strict context = the prefer context minus the blocks
"[<kind> | re: <error> | ...]" of exactly those pairs. No embedding, no API call.

Exact, not an estimate, when no surviving chunk could have been dropped as a near-dup of a
removed one: (1) the removed fault sorts after every other fault of the session (errors are
retrieved in sorted order, so it could not have taken chunks from them), and (2) within that
fault, no tagged candidate of a later kind is a near-dup of a removed block. (1) is checked
here and reported per session; (2) needs the candidate list and is checked separately
(docs/reports/eval_strict_offline_2026-10-24.md).

Writes compare_output/strict_v6b/context_v6_strict_<exercise>.json: the same session list, context
replaced, metrics marked with strict_skip, generated answers dropped (they were written from
the prefer context).
"""
import hashlib
import json
import os
import re
import sys

KINDS = ("mistake", "finding", "consequence", "principle")
HEADER = re.compile(r"^\[(mistake|finding|consequence|principle) \| re: (.+?) \| source: (.*)\]$", re.M)
NO_CODE_LABELS = {"general principles"}


def parse_blocks(ctx):
    ms = list(HEADER.finditer(ctx))
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(ctx)
        out.append({"kind": m[1], "label": m[2], "source": m[3], "text": ctx[m.end() + 1:end].rstrip("\n")})
    return out


def render(blocks):
    return "\n\n".join(f"[{b['kind']} | re: {b['label']} | source: {b['source']}]\n{b['text']}" for b in blocks)


def sha1(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def derive(path, out_dir="compare_output/strict_v6b"):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    assert d["retrieval"]["TAG_MODE"] == "prefer", d["retrieval"]
    sessions = []
    for s in d["sessions"]:
        ctx = s["context"]
        blocks = parse_blocks(ctx) if ctx.startswith("[") else []
        if blocks:
            assert render(blocks) == ctx, f"{s['payload']['session_id']}: context does not round-trip"
        skip = {(m["error"], m["kind"]) for m in s["metrics"]
                if not m.get("tagged") and m["error"] not in NO_CODE_LABELS}
        kept = [b for b in blocks if (b["label"], b["kind"]) not in skip]
        removed = [b for b in blocks if (b["label"], b["kind"]) in skip]
        new_ctx = render(kept) if (kept or not blocks) else None
        if new_ctx is None:
            from rag_core.retrieval import NO_MATCH_CONTEXT
            new_ctx = NO_MATCH_CONTEXT
        if not blocks:
            new_ctx = ctx
        errors = sorted({m["error"] for m in s["metrics"]})
        skipped_errors = sorted({e for e, _ in skip})
        later = [e for e in errors if e not in skipped_errors and any(e > se for se in skipped_errors)]
        metrics = []
        for m in s["metrics"]:
            m = dict(m)
            m["strict_skip"] = (m["error"], m["kind"]) in skip
            if m["strict_skip"]:
                m.update(best=None, kept=0, tagged=False, tag_exclusive=False)
            metrics.append(m)
        sessions.append({
            "label": s["label"], "exercise_id": s["exercise_id"], "payload": s["payload"],
            "context": new_ctx, "metrics": metrics,
            "context_sha1": sha1(new_ctx), "prefer_context_sha1": sha1(ctx),
            "changed": new_ctx != ctx,
            "strict_skipped": sorted(f"{e}/{k}" for e, k in skip),
            "removed_blocks": removed,
            # faults retrieved AFTER a skipped one could have lost chunks to its fallback
            # (shared near-dup list), so for them the offline context is only an estimate
            "estimate_only_for": later,
        })
    out = {
        "derived_from": os.path.basename(path), "method": "offline: prefer context minus strict-skipped kinds",
        "mock": d["mock"], "collection": d["collection"],
        "retrieval": {**d["retrieval"], "TAG_MODE": "strict"},
        "note": "rag/no_rag answers not carried over - they were generated from the prefer context",
        "sessions": sessions,
    }
    ex = d["sessions"][0]["exercise_id"]
    out_path = os.path.join(out_dir, f"context_v6_strict_{ex}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out_path, out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        out_path, out = derive(p)
        print(f"{p} -> {out_path}")
        for s in out["sessions"]:
            print(f"  {s['payload']['session_id']:18s} changed={s['changed']!s:5s} "
                  f"skipped={s['strict_skipped']} removed={len(s['removed_blocks'])} "
                  f"estimate_only_for={s['estimate_only_for']} sha1 {s['prefer_context_sha1'][:10]} -> {s['context_sha1'][:10]}")
