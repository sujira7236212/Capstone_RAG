"""Cases for eval/make_split.py (docs/eval_v6_plan.md E5): document ids, groups, a
deterministic stratified assignment, and locking - a later round must never move a
document that already has a side. Plain asserts so it runs without pytest:

    python eval/test_make_split.py
"""
import collections
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_split import assign, collect_units, doc_id, split_of  # noqa: E402

failed = 0


def check(name, got, expected):
    global failed
    if got != expected:
        failed += 1
        print(f"FAIL  {name}\n  got: {got}\n  exp: {expected}")


# --- doc_id ---------------------------------------------------------------------------
check("windows path + part suffix",
      doc_id(r"C:\Users\HP\Documents\RAG_SYSTEM\data\squat\knee_valgus\Bell2013.pdf [part 3/12]"),
      "squat/knee_valgus/Bell2013.pdf")
check("relative path", doc_id("data/lunge/KritzCroninHume2009BodyweightlungeSCJ.pdf"),
      "lunge/KritzCroninHume2009BodyweightlungeSCJ.pdf")
check("url entry", doc_id(r"C:\x\data\push-up\urls.txt (https://www.nasm.org/a/push-up)"),
      "https://www.nasm.org/a/push-up")
check("wayback url kept whole",
      doc_id("data/squat/urls.txt (https://web.archive.org/web/2020/https://blog.nasm.org/squat-form)"),
      "https://web.archive.org/web/2020/https://blog.nasm.org/squat-form")

# --- groups: the correction follows the 2018 paper --------------------------------------
v18 = "squat/knee_varus/Lorenzetti2018_HowToSquat_StanceFootAngle_BMCSSMR.pdf"
v20 = "squat/knee_varus/Lorenzetti2020_Correction_HowToSquat_BMCSSMR.pdf"
docs = {v18: {"split": "test"}}
check("group member resolves to group side", split_of(f"C:/r/data/{v20} [part 1/1]", docs), "test")
check("unknown document has no side", split_of("data/squat/new.pdf", docs), None)


def window(source, items):
    return {"source": source, "core_principles": [{"text": t, "applies_to_fault": tags} for t, tags in items]}


with tempfile.TemporaryDirectory() as tmp:
    os.makedirs(os.path.join(tmp, "squat"))
    with open(os.path.join(tmp, "squat", "a_curated.json"), "w", encoding="utf-8") as f:
        json.dump([window(f"C:/r/data/{v18} [part 1/2]", [("x", ["knee_varus"]), ("y", [])]),
                   window(f"C:/r/data/{v20}", [("z", ["knee_varus", "knee_valgus"])])], f)
    units = collect_units(tmp)
check("group collected as one unit", sorted(units), [v18])
check("group counts merged", units[v18]["rule:knee_varus"], 2)
check("exercise label counts every item", units[v18]["exercise:squat"], 3)

# --- assignment -------------------------------------------------------------------------
rules = ["a", "b", "c", "d"]
synthetic = {}
for i in range(40):
    c = collections.Counter({"exercise:e": 3})
    c[f"rule:{rules[i % 4]}"] += 1 + i % 3
    if i % 7 == 0:
        c["rule:rare"] += 1
    synthetic[f"doc{i:02d}"] = c

first = assign(synthetic, {})
check("every document gets a side", len(first), 40)
check("deterministic", assign(synthetic, {}), first)
n_test = sum(s == "test" for s in first.values())
check("document ratio near 30%", 9 <= n_test <= 15, True)
for l in ["rule:a", "rule:b", "rule:c", "rule:d", "rule:rare"]:
    tot = sum(c[l] for c in synthetic.values())
    tst = sum(c[l] for u, c in synthetic.items() if first[u] == "test")
    check(f"{l} test share near 30% ({tst}/{tot})", 0.15 <= tst / tot <= 0.45, True)

# --- locking: a later round adds documents, never moves old ones ------------------------
grown = dict(synthetic)
for i in range(40, 52):
    grown[f"doc{i:02d}"] = collections.Counter({"exercise:e": 2, "rule:rare": 2})
later = assign(grown, first)
check("only new documents assigned", sorted(later), [f"doc{i:02d}" for i in range(40, 52)])
check("old documents untouched", all(u not in later for u in first), True)
merged = {**first, **later}
tot = sum(c["rule:rare"] for c in grown.values())
tst = sum(c["rule:rare"] for u, c in grown.items() if merged[u] == "test")
check(f"new documents pull a rule back towards 30% ({tst}/{tot})", 0.2 <= tst / tot <= 0.4, True)

print("all passed" if not failed else f"{failed} failed")
sys.exit(1 if failed else 0)
