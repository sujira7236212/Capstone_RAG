"""TAG_MODE "strict" (plan step 1 / item A): a kind with no chunk tagged for the fault stays
empty instead of falling back to every chunk of the exercise; a kind that has tagged chunks
behaves exactly as under "prefer". Runs offline against an in-memory fake vector store.

    python tests/test_tag_mode_strict.py

The heavy imports of test_rag_compare.py and rag_core (dotenv, langchain) are stubbed only when they are
not installed, so this runs both in the project venv and in a bare Python with numpy.
"""
import contextlib
import importlib
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _stub_if_missing(name, **attrs):
    try:
        importlib.import_module(name)
    except ImportError:
        mod = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(mod, k, v)
        sys.modules[name] = mod


_dummy = type("Dummy", (), {"__init__": lambda self, *a, **k: None})
_stub_if_missing("dotenv", load_dotenv=lambda *a, **k: None)
_stub_if_missing("langchain_google_genai", ChatGoogleGenerativeAI=_dummy)
_stub_if_missing("langchain_core")
_stub_if_missing("langchain_core.prompts", ChatPromptTemplate=_dummy)
_stub_if_missing("langchain_core.runnables", RunnablePassthrough=_dummy)
_stub_if_missing("langchain_core.output_parsers", StrOutputParser=_dummy)
_stub_if_missing("langchain_core.documents", Document=_dummy)

import test_rag_compare as trc  # noqa: E402
from dataclasses import replace  # noqa: E402

from rag_core import retrieval as rt  # noqa: E402

EX = "lunge"
KINDS = ("mistake", "finding", "consequence", "principle")


class Doc:
    def __init__(self, text, kind, dist, tags="", ex=EX):
        self.id = text
        self.page_content = text
        self.dist = dist
        self.metadata = {"text": text, "item_kind": kind, "fault_tags": tags, "exercise_id": ex,
                         "source": f"src/{kind}.pdf"}


def _match(doc, f):
    for key, cond in f.items():
        if key == "$and":
            if not all(_match(doc, c) for c in cond):
                return False
        elif key == "$or":
            if not any(_match(doc, c) for c in cond):
                return False
        else:
            val = doc.metadata.get(key)
            if not isinstance(cond, dict):
                cond = {"$eq": cond}
            for op, arg in cond.items():
                if op == "$eq" and val != arg:
                    return False
                if op == "$in" and val not in arg:
                    return False
                if op == "$like" and arg.strip("%") not in (val or ""):
                    return False
    return True


class FakeStore:
    """Distance is a property of the chunk (Doc.dist), the same for every query - enough to
    exercise the gate, and it makes the expected kept sets obvious."""
    collection_name = "fake"

    def __init__(self, docs):
        self.docs = docs
        self.calls = []
        self.embeddings = types.SimpleNamespace(embed_query=lambda q: q)

    def similarity_search_with_score(self, query, k, filter):
        self.calls.append(filter)
        hits = sorted((d for d in self.docs if _match(d, filter)), key=lambda d: d.dist)
        return [(d, d.dist) for d in hits[:k]]

    similarity_search_with_score_by_vector = similarity_search_with_score


class FakeCorpus:
    """kb_bm25.corpus() stand-in for HYBRID: same distances, no lexical signal."""
    def __init__(self, docs):
        self.docs = docs

    def distances(self, vec, idx):
        import numpy as np
        return np.array([self.docs[i].dist for i in idx])

    def bm25(self, text, idx):
        import numpy as np
        return np.zeros(len(idx))


# LU-004-shaped KB: `back` (straight_back_leg) has tagged chunks for `principle` only; the
# other three kinds hold only chunks tagged for `knee` (knee_valgus) or untagged ones - those
# are what the prefer fallback used to pull in under "re: back".
DOCS = [
    Doc("Keep a soft bend in the rear knee throughout the lunge.", "principle", 0.10, "|back|"),
    Doc("Bend the back knee so it travels toward the floor.", "principle", 0.12, "|back|"),
    Doc("Letting the knee cave inward during the lunge.", "mistake", 0.11, "|knee|"),
    Doc("Knee drifting past the toes and twisting.", "mistake", 0.12, "|knee|"),
    Doc("Leaning the trunk far forward over the front leg.", "mistake", 0.13, ""),
    Doc("Valgus collapse increases ACL strain.", "consequence", 0.10, "|knee|"),
    Doc("Knee valgus angle rose 8 degrees under load.", "finding", 0.10, "|knee|"),
    Doc("Squeeze the glute to keep the knee over the second toe.", "principle", 0.11, "|knee|"),
    Doc("A squat stance mistake unrelated to lunges.", "mistake", 0.05, "|back|", ex="squat"),
]


def config(**kw):
    return replace(rt.DEFAULT_CONFIG, **kw)


@contextlib.contextmanager
def fake_taxonomy():
    old = rt.resolve
    rt.resolve = lambda e, ex: {"known": e in ("back", "knee"), "code": e, "query": f"query for {e}"}
    try:
        yield
    finally:
        rt.resolve = old


def texts(blocks, label=None):
    return [rt._chunk_text(doc) for _, doc, _, lab in blocks if label is None or lab == label]


def kinds_of(blocks, label):
    return sorted({kind for _, _, kind, lab in blocks if lab == label})


# Every retrieval path that applies fault_tags "prefer": _search, _search_multi,
# _search_hybrid, _search_single.
PATHS = {
    "fault": dict(queries="fault", hybrid=False, kind_pool="split"),
    "profile": dict(queries="profile", hybrid=False, kind_pool="split"),
    "hybrid": dict(queries="profile", hybrid=True, kind_pool="split"),
    "single": dict(queries="fault", hybrid=False, kind_pool="single"),
}


STRICT_FAULT = config(tag_mode="strict", queries="fault", hybrid=False, kind_pool="split")


def run(path, mode, errors, docs=DOCS):
    vs = FakeStore(docs)
    sys.modules["kb_bm25"] = types.SimpleNamespace(
        corpus=lambda name, ex: FakeCorpus([d for d in docs if d.metadata["exercise_id"] == ex]))
    with fake_taxonomy():
        blocks, metrics = rt.retrieve_kb_blocks(vs, EX, "Lunge", errors,
                                                cfg=config(tag_mode=mode, rerank=False, **PATHS[path]))
    return blocks, metrics, vs


def test_strict_empties_untagged_kinds():
    for path in PATHS:
        prefer, _, _ = run(path, "prefer", ["back"])
        strict, metrics, _ = run(path, "strict", ["back"])
        # prefer: fallback fills mistake/finding/consequence with knee/untagged chunks
        assert kinds_of(prefer, "back") == ["consequence", "finding", "mistake", "principle"], (path, prefer)
        # strict: only the kind that has chunks tagged |back|
        assert kinds_of(strict, "back") == ["principle"], (path, strict)
        assert all("|back|" in doc.metadata["fault_tags"] for _, doc, _, _ in strict), path
        skip = {m["kind"]: m["strict_skip"] for m in metrics}
        assert skip == {"mistake": True, "finding": True, "consequence": True, "principle": False}, (path, skip)
        for m in metrics:
            if m["strict_skip"]:
                assert m["kept"] == 0 and m["best"] is None and not m["tagged"] and not m["tag_exclusive"], (path, m)


def test_tagged_kinds_identical_to_prefer():
    for path in PATHS:
        prefer, pm, _ = run(path, "prefer", ["back"])
        strict, sm, _ = run(path, "strict", ["back"])
        pre = [(round(s, 6), rt._chunk_text(d)) for s, d, k, _ in prefer if k == "principle"]
        stc = [(round(s, 6), rt._chunk_text(d)) for s, d, k, _ in strict if k == "principle"]
        assert pre == stc, (path, pre, stc)
        pr = next(m for m in pm if m["kind"] == "principle")
        sr = next(m for m in sm if m["kind"] == "principle")
        assert {k: v for k, v in pr.items() if k != "strict_skip"} == \
               {k: v for k, v in sr.items() if k != "strict_skip"}, (path, pr, sr)


def test_fully_tagged_fault_unchanged():
    # knee has tagged chunks in every kind -> strict == prefer, byte for byte in the context
    for path in PATHS:
        prefer, pm, _ = run(path, "prefer", ["knee"])
        strict, sm, _ = run(path, "strict", ["knee"])
        assert [(s, rt._chunk_text(d), k, l) for s, d, k, l in prefer] == \
               [(s, rt._chunk_text(d), k, l) for s, d, k, l in strict], path
        assert not any(m["strict_skip"] for m in sm), path


def test_no_code_falls_back_like_prefer():
    # unmapped error (no fault code) and the flawless-session query: nothing to be strict about
    for path in ("fault", "single"):
        for errors in (["Some unmapped label"], []):
            prefer, _, _ = run(path, "prefer", errors)
            strict, sm, _ = run(path, "strict", errors)
            assert texts(prefer) == texts(strict) and texts(strict), (path, errors)
            assert not any(m["strict_skip"] for m in sm), (path, errors)


def test_strict_never_runs_untagged_search_for_skipped_kind():
    _, _, vs = run("fault", "strict", ["back"])
    for f in vs.calls:
        if f.get("item_kind", {}).get("$in") in (["mistake"], ["finding"], ["consequence"]):
            assert "fault_tags" in f, f


def test_no_tagged_chunk_at_all_gives_no_match_context():
    docs = [d for d in DOCS if "|back|" not in d.metadata["fault_tags"]]
    vs = FakeStore(docs)
    with fake_taxonomy():
        ctx, metrics = rt.retrieve_kb_context(vs, EX, "Lunge", ["back"], cfg=STRICT_FAULT)
    assert ctx == rt.NO_MATCH_CONTEXT, ctx
    assert all(m["strict_skip"] for m in metrics)


def test_context_header_only_for_tagged_chunks():
    vs = FakeStore(DOCS)
    with fake_taxonomy():
        ctx, _ = rt.retrieve_kb_context(vs, EX, "Lunge", ["back"], cfg=STRICT_FAULT)
    assert "[principle | re: back |" in ctx
    for kind in ("mistake", "finding", "consequence"):
        assert f"[{kind} | re: back |" not in ctx, ctx
    assert "knee cave" not in ctx and "valgus" not in ctx.lower(), ctx


def test_multi_fault_session_dedup_shift():
    # LU-005 caveat: under prefer, `back`'s fallback can claim a |knee| chunk first; the shared
    # near-dup list then hides it from `knee`. Strict frees it, so `knee` can gain chunks in a
    # multi-fault session - why the offline strict context for LU-005 is only an estimate.
    docs = [
        Doc("Keep a soft bend in the rear knee throughout the lunge.", "principle", 0.10, "|back|"),
        Doc("Letting the knee cave inward during the lunge.", "mistake", 0.10, "|knee|"),
        Doc("letting the knee cave inward during the lunge", "mistake", 0.11, ""),
    ]
    # "back" sorts before "knee", so back's fallback runs first under prefer
    prefer, _, _ = run("fault", "prefer", ["back", "knee"], docs)
    strict, _, _ = run("fault", "strict", ["back", "knee"], docs)
    assert "Letting the knee cave inward during the lunge." in texts(prefer, "back")
    assert "Letting the knee cave inward during the lunge." not in texts(prefer, "knee")
    assert "Letting the knee cave inward during the lunge." in texts(strict, "knee")
    assert texts(strict, "back") == ["Keep a soft bend in the rear knee throughout the lunge."]


def test_single_budget_excludes_skipped_kinds():
    many = [Doc(f"Rear knee cue number {i} with distinct words w{i} x{i} y{i}.", "principle", 0.10 + i / 1000, "|back|")
            for i in range(6)]
    many += [Doc("Letting the knee cave inward during the lunge.", "mistake", 0.10, "|knee|")]
    prefer, _, _ = run("single", "prefer", ["back"], many)
    strict, _, _ = run("single", "strict", ["back"], many)
    # KIND_POOL "single" shares one budget across kinds. Strict sums MAX_PER_KIND over the
    # kinds that are still searched, so a skipped kind's quota is not handed to the others.
    assert len([b for b in strict if b[2] == "principle"]) == rt.MAX_PER_KIND["principle"], strict
    assert len([b for b in prefer if b[2] == "principle"]) == 6, prefer  # prefer: 9-slot shared budget


def test_metrics_table_marks_strict_skip():
    _, metrics, _ = run("fault", "strict", ["back"])
    table = rt.metrics_table(metrics)
    assert table.count("strict —") == 3, table


def test_union_unchanged_by_strict_branch():
    a, _, _ = run("fault", "union", ["back"])
    assert kinds_of(a, "back") == ["consequence", "finding", "mistake", "principle"]


def test_cli_accepts_strict():
    old = sys.argv
    try:
        sys.argv = ["test_rag_compare.py", "--tag-mode", "strict"]
        assert trc.parse_args().tag_mode == "strict"
        sys.argv = ["test_rag_compare.py"]
        assert trc.parse_args().tag_mode == "strict"  # default since 2026-10-25
        sys.argv = ["test_rag_compare.py", "--tag-mode", "prefer"]
        assert trc.parse_args().tag_mode == "prefer"
    finally:
        sys.argv = old
    assert rt.DEFAULT_CONFIG.tag_mode == "strict"
    src = open(os.path.join(ROOT, "eval", "eval_retrieval.py"), encoding="utf-8").read()
    assert 'choices=["prefer", "strict", "union"]' in src


def test_context_only_flag():
    old = sys.argv
    try:
        sys.argv = ["test_rag_compare.py", "--context-only", "--samples", "3"]
        args = trc.parse_args()
        assert args.context_only and args.skip_no_rag and args.samples == 0
        sys.argv = ["test_rag_compare.py"]
        args = trc.parse_args()
        assert not args.context_only and not args.skip_no_rag and args.samples == 1
    finally:
        sys.argv = old
    # generate=False returns before any LLM call (no-RAG side: no DB needed either)
    texts_, ctx, metrics = trc.generate_feedback_compare({"exercise_id": EX, "reps_detail": []},
                                                         use_rag=False, generate=False)
    assert texts_ == [] and ctx == "No external context provided." and metrics == []


def test_eval_retrieval_miss_reason_and_columns():
    cwd = os.getcwd()
    try:
        sys.path.insert(0, os.path.join(ROOT, "eval"))
        import eval_retrieval as er
    finally:
        os.chdir(cwd)
    meta = {"t": {"kind": "mistake", "fault_tags": "|knee|"}}
    assert er._miss_reason(["t"], meta, {}, {"mistake": False}, "back", {"mistake": True}) == "tag_strict"
    assert er._miss_reason(["t"], meta, {}, {"mistake": True}, "back") == "tag_filter"
    assert er._miss_reason(["t"], meta, {}, {"mistake": False}, "back") == "rank"
    assert "tag_strict" not in er._miss_reasons(config(tag_mode="prefer"))
    assert "tag_strict" in er._miss_reasons(config(tag_mode="strict"))


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            import traceback
            traceback.print_exc()
            print(f"FAIL {name}: {e!r}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
