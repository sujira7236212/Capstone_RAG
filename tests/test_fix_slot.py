"""FIX_SLOT: one more principle per fault, found by the rule's fix_query. Offline, against an
in-memory store whose distances depend on the query.

    python tests/test_fix_slot.py
"""
import contextlib
import dataclasses
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from error_taxonomy import all_faults  # noqa: E402
from rag_core import retrieval as rt  # noqa: E402

FIX = "fix query for the rule"


class Doc:
    def __init__(self, text, kind, dist, fix_dist=0.30, tags="|back|"):
        self.id = text
        self.dist, self.fix_dist = dist, fix_dist
        self.metadata = {"text": text, "item_kind": kind, "fault_tags": tags, "exercise_id": "lunge", "source": "s.pdf"}


def matches(doc, f):
    for key, cond in f.items():
        if key == "$and":
            if not all(matches(doc, c) for c in cond):
                return False
        elif key == "$or":
            if not any(matches(doc, c) for c in cond):
                return False
        else:
            value = doc.metadata.get(key)
            cond = cond if isinstance(cond, dict) else {"$eq": cond}
            for op, arg in cond.items():
                if (op == "$eq" and value != arg) or (op == "$in" and value not in arg) \
                        or (op == "$like" and arg.strip("%") not in value):
                    return False
    return True


class Store:
    def __init__(self, docs):
        self.docs = docs
        self.embedded = []

        def embed(text):
            self.embedded.append(text)
            return text
        self.embeddings = types.SimpleNamespace(embed_query=embed)

    def similarity_search_with_score_by_vector(self, vec, k, filter):
        distance = (lambda d: d.fix_dist) if vec == FIX else (lambda d: d.dist)
        hits = sorted((d for d in self.docs if matches(d, filter)), key=distance)
        return [(d, distance(d)) for d in hits[:k]]

    similarity_search_with_score = similarity_search_with_score_by_vector


@contextlib.contextmanager
def taxonomy(known=True):
    old = rt.resolve
    entry = {"known": known, "code": "back", "query": "query for back"}
    rt.resolve = lambda e, ex: {**entry, "fix_query": FIX} if known else entry
    try:
        yield
    finally:
        rt.resolve = old


# Two principles fill the quota; the fix sentences are far from the fault query, near the fix one.
DOCS = [
    Doc("Keep the rear shin angled during the descent.", "principle", 0.10),
    Doc("The back knee travels down toward the floor.", "principle", 0.11),
    Doc("Hold a wall and practise the bottom position slowly.", "principle", 0.35, fix_dist=0.12),
    Doc("Stand beside a chair and sit toward it for depth practice.", "principle", 0.36, fix_dist=0.10, tags=""),
    Doc("Twist the torso away to work the obliques harder today.", "principle", 0.37, fix_dist=0.05, tags="|lean|"),
    Doc("Letting the rear leg stay locked.", "mistake", 0.10),
]
FAILED = []


def check(name, got, want):
    if got != want:
        FAILED.append(name)
        print(f"FAIL  {name}: {got!r}, wanted {want!r}")


def run(store=None, errors=("back",), trace=None, **kw):
    cfg = dataclasses.replace(rt.DEFAULT_CONFIG, tag_mode="strict", **kw)
    return rt.retrieve_kb_blocks(store or Store(DOCS), "lunge", "Lunge", set(errors), trace=trace, cfg=cfg)


def principles(blocks):
    return [rt._chunk_text(b[1]) for b in blocks if b[2] == "principle"]


with taxonomy():
    store = Store(DOCS)
    off_blocks, off_metrics = run(store)
    check("off by default", rt.DEFAULT_CONFIG.fix_slot, False)
    check("off: two principles", len(principles(off_blocks)), 2)
    check("off: the fix query is not embedded (a paid call)", FIX in store.embedded, False)
    check("off: no chunk of the slot", "Stand beside a chair and sit toward it for depth practice."
          in principles(off_blocks), False)

    on_blocks, on_metrics = run(fix_slot=True)
    # A set: blocks are sorted by distance, so the slot's chunk can land between the other two.
    check("on: adds one principle, the quota's two stay", set(principles(on_blocks)),
          set(principles(off_blocks)) | {"Stand beside a chair and sit toward it for depth practice."})
    check("on: exactly three", len(principles(on_blocks)), 3)
    check("on: another fault's chunk stays out, though it is the closest",
          any("obliques" in t for t in principles(on_blocks)), False)
    check("on: other kinds are untouched",
          [b[1].id for b in on_blocks if b[2] != "principle"], [b[1].id for b in off_blocks if b[2] != "principle"])
    check("on: the principle metric counts it",
          [m["kept"] for m in on_metrics if m["kind"] == "principle"], [3])

    tagged = principles(run(fix_slot=True, fix_pool="tagged")[0])
    check("pool tagged: only this fault's chunks", "Hold a wall and practise the bottom position slowly." in tagged, True)
    check("pool tagged: no untagged chunk", any("chair" in t for t in tagged), False)

    dup = DOCS + [Doc("Keep the rear shin angled during the descent please.", "principle", 0.39, fix_dist=0.01, tags="")]
    picked = principles(run(Store(dup), fix_slot=True)[0])
    check("a sentence already kept is skipped for the next one", any("chair" in t for t in picked), True)
    check("the restated sentence stays out", any("please" in t for t in picked), False)

    far = [Doc("Keep the rear shin angled.", "principle", 0.10), Doc("Far away chunk here.", "principle", 0.39, fix_dist=0.90)]
    check("past the distance cap: no slot", len(principles(run(Store(far), fix_slot=True)[0])), 1)

    trace = []
    run(fix_slot=True, trace=trace)
    slot = [t for t in trace if t.get("fix_slot")]
    check("trace: the slot's decisions are recorded with the error",
          [t["reason"] for t in slot][:1] + [slot[0]["error"]], ["kept", "back"])

    try:
        run(fix_slot=True, queries="fault")
        check("a config it cannot serve stops", False, True)
    except ValueError:
        pass
    check("summary names it when on", "FIX_SLOT=open" in dataclasses.replace(rt.DEFAULT_CONFIG, fix_slot=True).summary(), True)
    check("summary is unchanged when off", "FIX_SLOT" in rt.DEFAULT_CONFIG.summary(), False)

with taxonomy(known=False):
    check("an unmapped rule has no slot", len(principles(run(fix_slot=True)[0])) <= 2, True)

# A set with no fault: general principles only, no slot.
store = Store(DOCS)
check("a clean set embeds no fix query", (run(store, errors=(), fix_slot=True), FIX in store.embedded)[1], False)

# The real taxonomy
faults = list(all_faults())
check("every rule has a fix_query", [c for _, c, e in faults if not e.get("fix_query")], [])
check("fix queries are distinct", len({e["fix_query"] for _, _, e in faults}), len(faults))
check("a fix_query leaves the fault's definition out", [c for _, c, e in faults if e["query"] in e["fix_query"]], [])

if FAILED:
    print(f"{len(FAILED)} failed")
    sys.exit(1)
print("all passed")
