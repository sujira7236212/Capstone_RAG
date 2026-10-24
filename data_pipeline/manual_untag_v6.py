"""Remove one fault code from specific curated items, by exact text, after a human review.

The curator's tags are kept as they came out except where a reviewed decision says an item
does not describe that fault. Each decision is listed in data_pipeline/manual_untags_v6.json
(file, kind, exact text, code, reason, date, who approved). Only the tag changes: the item
text is untouched and the window-level applies_to_fault is recomputed as the union of its
items' tags (the same rule the curator uses). Originals go to data_pipeline/backups/ first.
Run before ingest - ingest only adds rows, so a tag fixed after ingest needs a new collection.

    python data_pipeline/manual_untag_v6.py --dry-run
    python data_pipeline/manual_untag_v6.py
"""
import argparse
import json
import os
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = {"mistake": "common_mistakes", "consequence": "consequences",
          "principle": "core_principles", "finding": "specific_findings"}


def dump_like(data, raw):
    """Re-serialise in the file's own style (indent 2, CRLF or LF, unicode as written)."""
    nl = "\r\n" if b"\r\n" in raw else "\n"
    for ensure_ascii in (False, True):
        probe = json.dumps(json.loads(raw.decode("utf-8")), ensure_ascii=ensure_ascii, indent=2).replace("\n", nl)
        if probe.encode("utf-8") == raw or (probe + nl).encode("utf-8") == raw:
            out = json.dumps(data, ensure_ascii=ensure_ascii, indent=2).replace("\n", nl)
            return (out + (nl if raw.endswith(nl.encode()) else "")).encode("utf-8")
    raise SystemExit("cannot reproduce the file's JSON style - refusing to rewrite it")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", default=os.path.join(ROOT, "data_pipeline", "manual_untags_v6.json"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    with open(args.decisions, encoding="utf-8") as f:
        decisions = json.load(f)["decisions"]
    by_file = {}
    for d in decisions:
        by_file.setdefault(d["file"], []).append(d)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for rel, ds in by_file.items():
        path = os.path.join(ROOT, rel)
        raw = open(path, "rb").read()
        data = json.loads(raw.decode("utf-8"))
        for d in ds:
            hits = [it for w in data for it in w.get(FIELDS[d["kind"]], []) if it.get("text") == d["text"]]
            if len(hits) != 1:
                raise SystemExit(f"{rel}: expected exactly 1 {d['kind']} item with that text, found {len(hits)}: {d['text'][:60]}")
            it = hits[0]
            if d["code"] not in it.get("applies_to_fault", []):
                print(f"  already untagged: {d['code']} - {d['text'][:70]}")
                continue
            it["applies_to_fault"] = [c for c in it["applies_to_fault"] if c != d["code"]]
            print(f"  untag {d['code']:20s} {d['kind']:11s} {d['text'][:70]}")
        for w in data:
            w["applies_to_fault"] = sorted({c for f in FIELDS.values() for it in w.get(f, []) for c in it.get("applies_to_fault", [])})
        new = dump_like(data, raw)
        if new == raw:
            print(f"{rel}: no change")
            continue
        if args.dry_run:
            print(f"{rel}: would rewrite (dry run)")
            continue
        bdir = os.path.join(ROOT, "data_pipeline", "backups")
        os.makedirs(bdir, exist_ok=True)
        shutil.copy2(path, os.path.join(bdir, f"manual_untag_{stamp}__{os.path.basename(path)}"))
        open(path, "wb").write(new)
        print(f"{rel}: rewritten (backup in data_pipeline/backups/)")


if __name__ == "__main__":
    main()
