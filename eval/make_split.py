"""Split the KB's source documents into dev and test (docs/plans/eval_v6_plan.md E5).

The unit is a source document (a PDF under data/, or one URL from a urls.txt), never a
chunk: every chunk of a document lands on the same side, so test chunks are never
neighbours of something tuned on dev. Retrieval still searches the whole KB; the split
only decides which pool/kept chunks a score counts.

Stratified by rule, on the curator's tags (user decision 2026-10-03). The plan first said
"by the rule's source folder", but most rule folders hold one file and most tagged items
come from documents outside them. Each document is labelled with its tagged-item count
per rule plus its item count per exercise (so untagged-only pages are balanced too). With
the test document count fixed at RATIO_TEST, assign() picks the test set whose share of
every label is closest to RATIO_TEST (sum of squared gaps), by seeded random starts plus
swap hill-climbing. A greedy per-label pass (iterative stratification) was tried first and
left elbow_flare at 3% test: a few documents hold most of a rule's items, so the split
has to be judged on all labels at once. Tags are curator output, not eval labels or
results, so choosing the split from them leaks nothing.

Adding documents later (docs/progress/t3_curation_status.md section 8.3): documents already in the
split file are locked and keep their side; only new ones are assigned, starting from the
locked counts, so each rule moves back towards RATIO_TEST. Curate the new documents
first (the tags are the input), and never rename or move a file under data/ - its path
is its id, and a renamed file would come back as a new document.

    python eval/make_split.py --dry-run                 # print the split, write nothing
    python eval/make_split.py                           # first split -> eval/split_v6.json
    python eval/make_split.py --round v6b --dry-run     # later: assign only new documents
    python eval/make_split.py --check                   # every source has a side; counts
"""
import argparse
import collections
import datetime
import glob
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from error_taxonomy import ERROR_TAXONOMY  # noqa: E402

SPLIT_FILE = os.path.join(HERE, "split_v6.json")
CURATED_DEFAULT = os.path.join(ROOT, "curated_data_v6")
RATIO_TEST = 0.3
SEED = 20261003
RESTARTS = 200
ITEM_FIELDS = ("core_principles", "common_mistakes", "consequences", "specific_findings")
# Documents that must share a side: the 2020 correction re-reports the 2018 paper's data.
GROUPS = [
    ["squat/knee_varus/Lorenzetti2018_HowToSquat_StanceFootAngle_BMCSSMR.pdf",
     "squat/knee_varus/Lorenzetti2020_Correction_HowToSquat_BMCSSMR.pdf"],
]


def doc_id(source: str) -> str:
    """Stable id for a window's or chunk's `source`: the URL for a urls.txt entry, else
    the path under data/ with forward slashes and no " [part i/n]" suffix."""
    url = re.search(r"\((https?://[^)\s]+)\)", source or "")
    if url:
        return url.group(1)
    path = re.sub(r"\s*\[part \d+/\d+\]\s*$", "", source or "").strip().replace("\\", "/")
    m = re.search(r"(?:^|/)data/(.+)$", path)
    return m.group(1) if m else path


def group_of(did: str) -> str:
    for g in GROUPS:
        if did in g:
            return g[0]
    return did


def split_of(source: str, documents: dict):
    """'dev' / 'test' for a chunk's metadata `source`, given split_v6.json's "documents";
    None if the document has no side (not split yet - run --check)."""
    entry = documents.get(group_of(doc_id(source)))
    return entry["split"] if entry else None


def collect_units(folder: str) -> dict:
    """{unit id: Counter(label -> item count)} over a curated folder. Labels are
    'rule:<code>' (tagged items) and 'exercise:<name>' (all items)."""
    units = collections.defaultdict(collections.Counter)
    for path in sorted(glob.glob(os.path.join(folder, "**", "*.json"), recursive=True)):
        exercise = os.path.relpath(path, folder).split(os.sep)[0]
        with open(path, encoding="utf-8") as f:
            windows = json.load(f)
        for w in windows:
            unit = units[group_of(doc_id(w.get("source", "")))]
            for field in ITEM_FIELDS:
                for item in w.get(field) or []:
                    if not isinstance(item, dict):
                        continue
                    # general/ items are never retrieved (search filters on the
                    # exercise), so they give the split nothing to balance.
                    if exercise != "general":
                        unit[f"exercise:{exercise}"] += 1
                    for code in item.get("applies_to_fault") or []:
                        unit[f"rule:{code}"] += 1
    return dict(units)


def imbalance(test_items: dict, total: dict, ratio_test: float) -> float:
    """Sum over labels of (test share - ratio_test)^2: 0 when every rule and exercise has
    exactly ratio_test of its items in test."""
    return sum((test_items.get(l, 0) / n - ratio_test) ** 2 for l, n in total.items() if n)


def assign(units: dict, locked: dict, ratio_test: float = RATIO_TEST, seed: int = SEED,
           restarts: int = RESTARTS) -> dict:
    """Assign every unit not in `locked` ({id: "dev"|"test"}) to a side; returns the new
    assignments only. The test document count is fixed at round(ratio_test * all units)
    (locked ones included); within that, seeded random starts each improved by dev<->test
    swaps until no swap lowers imbalance(). Deterministic for the same arguments."""
    total = collections.Counter()
    for c in units.values():
        total.update(c)
    base = collections.Counter()
    for u, side in locked.items():
        if side == "test" and u in units:
            base.update(units[u])
    todo = sorted(u for u in units if u not in locked)
    if not todo:
        return {}
    n_locked_test = sum(1 for u, s in locked.items() if s == "test" and u in units)
    k = min(max(round(ratio_test * len(units)) - n_locked_test, 0), len(todo))

    def score(test_set):
        c = collections.Counter(base)
        for u in test_set:
            c.update(units[u])
        return imbalance(c, total, ratio_test)

    rng = random.Random(seed)
    best, best_score = None, None
    for _ in range(restarts):
        test = set(rng.sample(todo, k))
        cur = score(test)
        improved = True
        while improved:
            improved = False
            for t in sorted(test):
                for d in todo:
                    if d in test:
                        continue
                    trial = (test - {t}) | {d}
                    s = score(trial)
                    if s < cur - 1e-12:
                        test, cur, improved = trial, s, True
                        break
                if improved:
                    break
        if best_score is None or cur < best_score - 1e-12:
            best, best_score = test, cur
    return {u: ("test" if u in best else "dev") for u in todo}


def report(units: dict, sides: dict) -> str:
    lines = []
    n_test = sum(1 for u in units if sides.get(u) == "test")
    lines.append(f"documents: {len(units)} · dev {len(units) - n_test} · test {n_test} "
                 f"({n_test / max(len(units), 1):.0%})")
    missing = sorted(u for u in units if u not in sides)
    if missing:
        lines.append(f"NO SIDE ({len(missing)}): " + ", ".join(missing))
    lines.append("\n| label | docs dev | docs test | items dev | items test | test share |")
    lines.append("|---|---|---|---|---|---|")
    labels = [f"rule:{c}" for faults in ERROR_TAXONOMY.values() for c in faults]
    labels += sorted({l for c in units.values() for l in c if l.startswith("exercise:")})
    for l in labels:
        d = {s: [u for u in units if sides.get(u) == s and units[u].get(l)] for s in ("dev", "test")}
        n = {s: sum(units[u][l] for u in d[s]) for s in d}
        share = n["test"] / (n["dev"] + n["test"]) if n["dev"] + n["test"] else 0
        lines.append(f"| {l.split(':', 1)[1]} | {len(d['dev'])} | {len(d['test'])} | "
                     f"{n['dev']} | {n['test']} | {share:.0%} |")
    lines.append("\ntest documents:")
    lines += [f"  {u}" for u in sorted(u for u in units if sides.get(u) == "test")]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--curated", default=CURATED_DEFAULT)
    ap.add_argument("--out", default=SPLIT_FILE)
    ap.add_argument("--round", default="v6", help="name recorded on newly assigned documents")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="report the saved split, assign nothing")
    args = ap.parse_args()

    units = collect_units(args.curated)
    data = None
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            data = json.load(f)
    locked = {u: d["split"] for u, d in (data or {}).get("documents", {}).items()}

    gone = sorted(u for u in locked if u not in units)
    if gone:
        print(f"WARNING: {len(gone)} locked documents are not in {args.curated} "
              "(renamed, moved or not curated?): " + ", ".join(gone))

    if args.check:
        if data is None:
            sys.exit(f"no split file at {args.out}")
        print(report(units, locked))
        sys.exit(1 if any(u not in locked for u in units) else 0)

    if data and any(r["name"] == args.round for r in data["rounds"]):
        sys.exit(f"round {args.round!r} already in {args.out}; pass a new --round to add documents")
    new = assign(units, locked, RATIO_TEST, args.seed)
    if not new:
        print("no new documents to assign")
        return
    sides = {**locked, **new}
    print(f"round {args.round}: {len(new)} new documents, {len(locked)} locked\n")
    print(report(units, sides))
    if args.dry_run:
        return

    data = data or {
        "description": "Dev/test split of KB v6 source documents (docs/plans/eval_v6_plan.md E5), "
                       "made by eval/make_split.py. Locked: a document keeps its side in "
                       "every later round. Score test only with --final.",
        "ratio_test": RATIO_TEST,
        "groups": GROUPS,
        "rounds": [],
        "documents": {},
    }
    data["rounds"].append({"name": args.round, "seed": args.seed, "curated": os.path.relpath(args.curated, ROOT),
                           "date": datetime.date.today().isoformat(), "documents_added": len(new)})
    for u in sorted(new):
        data["documents"][u] = {"split": new[u], "assigned_in": args.round}
    data["documents"] = dict(sorted(data["documents"].items()))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
