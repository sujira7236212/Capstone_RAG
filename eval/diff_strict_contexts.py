"""Block-level diff of two TAG_MODE "strict" context files, offline (step 5, context layer).

    python eval/diff_strict_contexts.py compare_output/strict_v6b/context_v6_strict_lunge.json \
        compare_output/strict_v6b/context_v6b_strict_lunge.json

Sessions are matched by session_id. For each one: byte-identical or not, and the blocks
only in A / only in B (a block = kind + re-label + source + text, the same unit
eval/strict_offline_from_compare.py works on). Also prints, per fault and kind, how many
blocks each side placed, so a target rule's per-kind change can be read off directly.
No embedding, no API call.
"""
import collections
import hashlib
import json
import sys

sys.path.insert(0, "eval")
from strict_offline_from_compare import parse_blocks  # noqa: E402


def load(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return d, {s["payload"]["session_id"]: s for s in d["sessions"]}


def key(b):
    return (b["kind"], b["label"], b["source"], b["text"])


def blocks(ctx):
    return parse_blocks(ctx) if ctx.startswith("[") else []


def diff(path_a, path_b):
    da, sa = load(path_a)
    db, sb = load(path_b)
    assert da["retrieval"]["TAG_MODE"] == db["retrieval"]["TAG_MODE"] == "strict"
    print(f"A = {path_a} ({da['collection']})\nB = {path_b} ({db['collection']})")
    assert sa.keys() == sb.keys(), (sorted(sa), sorted(sb))
    for sid in sa:
        ca, cb = sa[sid]["context"], sb[sid]["context"]
        same = hashlib.sha1(ca.encode()).digest() == hashlib.sha1(cb.encode()).digest()
        print(f"\n== {sid} ({sa[sid]['label']}): {'IDENTICAL' if same else 'CHANGED'}")
        if same:
            continue
        ba, bb = blocks(ca), blocks(cb)
        ka, kb = [key(b) for b in ba], [key(b) for b in bb]
        if not ba or not bb:
            print(f"   A non-block context: {ca[:120]!r}" if not ba else "")
            print(f"   B non-block context: {cb[:120]!r}" if not bb else "")
        counts = collections.defaultdict(lambda: [0, 0])
        for b in ba:
            counts[(b["label"], b["kind"])][0] += 1
        for b in bb:
            counts[(b["label"], b["kind"])][1] += 1
        print("   per fault/kind (A -> B): " + ", ".join(
            f"{l}/{k} {a}->{b}" for (l, k), (a, b) in sorted(counts.items()) if a != b) or "   same counts")
        for tag, only in (("-", [k for k in ka if k not in kb]), ("+", [k for k in kb if k not in ka])):
            for kind, label, source, text in only:
                print(f"   {tag} [{kind} | re: {label} | {source}]\n       {text}")
        if sorted(ka) == sorted(kb):
            print("   same blocks, order differs")


if __name__ == "__main__":
    diff(sys.argv[1], sys.argv[2])
