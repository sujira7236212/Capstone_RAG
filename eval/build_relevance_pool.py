"""Build eval/relevance_pool.json: for every golden fault, a wide candidate pool of KB chunks
labelled relevant / wrong_fault / irrelevant by an LLM judge.

golden_chunks.json can only say "at least one must_hit pattern reached the context" - it
cannot say how much relevant material the gate LEFT BEHIND, because it only lists what a
person picked out of the top-14 per (fault, kind). This file is the denominator for
recall: eval/eval_retrieval.py --pool reads it and reports, per fault, how many relevant
facts made it into the context and why the rest did not (quota / margin / tag filter /
rank - see test_rag_compare._search's `trace`).

Candidates per fault are deliberately gathered WITHOUT the gate's own restrictions, so
the pool is not biased toward what the current gate already finds:
  (a) every chunk whose fault_tags names this fault - including spelling variants like
      "|knee_valgus|" that the gate's LIKE '%|knee valgus|%' filter never matches;
  (b) the top-40 of several queries, filtered on exercise_id only (no kind, no tag).

The judge sees the fault name + the taxonomy's description of it and labels each chunk:
  relevant    - about THIS fault in THIS exercise: what it looks like, how to spot it,
                what it causes / why it matters, how to correct or prevent it (incl. a
                correct-form principle that directly fixes it), or a number that applies.
  wrong_fault - about a different fault, a different exercise variant, or advice that
                would push the lifter further INTO this fault / contradict its fix. These
                mislead if shown under this fault's label.
  irrelevant  - neither: study protocol, sample details, general info not tied to it.

Resumable: labels already in --out are reused (keyed by exercise, fault, chunk text), so an
interrupted run or a later KB addition only pays for the new chunks. A spot-check report is
written next to it for the human half of the check (plan: LLM judge + human sampling).

    python eval/build_relevance_pool.py
    python eval/build_relevance_pool.py --fault squat/butt\\ wink --judge gemini-3.5-flash
"""
import argparse
import json
import os
import random
import re
import sys
import time
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))

import embedding_config
from error_taxonomy import resolve

JUDGE_MODEL = "gemini-3.8-flash"
# Bump when JUDGE_PROMPT changes: labels from an older prompt are not reused.
# v2 (2026-09-25): v1 downgraded sentences that did not name the exercise, called "low back
# sags" a different fault from hip sag, and marked general-but-applicable consequences irrelevant.
JUDGE_PROMPT_VERSION = 2
DENSE_K = 40
BATCH = 20
LABELS = ("relevant", "wrong_fault", "irrelevant")


def _norm_tags(fault_tags):
    """'|knee_valgus|butt wink|' -> {'knee valgus', 'butt wink'} (spelling-insensitive)."""
    return {t.strip().replace("_", " ").lower() for t in (fault_tags or "").split("|") if t.strip()}


def fetch_tagged(engine, collection, exercise_id, code):
    """Every chunk of this exercise whose (normalised) fault_tags include `code`."""
    import sqlalchemy as sa
    q = sa.text("""
        select e.document, e.cmetadata
        from langchain_pg_embedding e join langchain_pg_collection c on c.uuid = e.collection_id
        where c.name = :c and e.cmetadata->>'exercise_id' = :ex
          and coalesce(e.cmetadata->>'fault_tags', '') <> ''""")
    out = []
    with engine.connect() as cx:
        for document, meta in cx.execute(q, {"c": collection, "ex": exercise_id}):
            if code in _norm_tags(meta.get("fault_tags")):
                out.append((meta.get("text") or document, meta))
    return out


def queries_for(code, exercise_id):
    r = resolve(code, exercise_id)
    name = code
    return r["query"], [
        r["query"],
        f"{name} during the {exercise_id}",
        f"Why {name} matters in the {exercise_id}: which joint or muscle takes the extra load and what it risks",
        f"How to correct {name} in the {exercise_id}: cues, setup changes, drills and correct form",
    ]


def gather(vs, engine, collection, g):
    ex, code = g["exercise_id"], g["code"]
    description, queries = queries_for(code, ex)
    pool = {}

    def add(text, meta, via):
        text = (text or "").strip()
        if not text:
            return
        c = pool.setdefault(text, {"text": text, "kind": meta.get("item_kind"),
                                   "fault_tags": meta.get("fault_tags") or "",
                                   "source": meta.get("source", ""), "via": []})
        if via not in c["via"]:
            c["via"].append(via)

    for text, meta in fetch_tagged(engine, collection, ex, code):
        add(text, meta, "tag")
    for i, q in enumerate(queries):
        for doc, _score in vs.similarity_search_with_score(q, k=DENSE_K, filter={"exercise_id": ex}):
            add(doc.metadata.get("text") or doc.page_content, doc.metadata, f"q{i}")
    return description, queries, list(pool.values())


JUDGE_PROMPT = """You are labelling knowledge-base sentences for a retrieval evaluation.

Exercise: {exercise}
Fault: {fault}
Fault description: {description}

For EACH numbered sentence below, decide how it relates to this fault in this exercise:
- "relevant": it is about THIS fault in THIS exercise - what it looks like, how to spot it,
  what it causes or why it matters, how to correct or prevent it (including a correct-form
  principle that directly fixes this fault), or a specific number/threshold that applies to it.
- "wrong_fault": it is about a DIFFERENT fault, a different exercise variant, or it is advice
  that would push the lifter further into this fault or contradict its fix. Shown under this
  fault's label it would mislead.
- "irrelevant": neither - study protocol or sample details, general information not tied to
  this fault, or too vague to help with it.

Judge only the sentence's own content. Be strict: sharing a body part or a keyword with the
fault is not enough for "relevant". But do not be literal:
- Every sentence was extracted from a source about this exercise. A sentence that does not
  name the exercise is still about it - never downgrade it for that reason alone.
- Other wordings of the same fault count as this fault (e.g. "the low back sags" is hip sag
  in a push-up; "tailbone tucks under" is butt wink; "half reps" is partial range of motion).
- A consequence that follows from this fault counts as relevant even if it is stated in
  general terms (e.g. "training only at short muscle lengths gives less muscle growth" is
  why a partial-range curl matters).
- "wrong_fault" is only for a genuinely different fault or variant, or advice that would
  worsen this one - not for a sentence that is merely general or vague (that is "irrelevant").

Sentences:
{items}

Return a JSON array with one object per sentence, in order:
[{{"i": <number>, "label": "relevant" | "wrong_fault" | "irrelevant", "reason": "<max 15 words>"}}]"""


def judge_batch(client, model, g, description, batch):
    from google.genai import types
    items = "\n".join(f"{i}. {c['text']}" for i, c in enumerate(batch, 1))
    prompt = JUDGE_PROMPT.format(exercise=g["exercise_id"], fault=g["code"],
                                 description=description, items=items)
    for attempt in range(5):
        try:
            resp = client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"))
            data = json.loads(resp.text)
            by_i = {int(d["i"]): d for d in data}
            out = []
            for i in range(1, len(batch) + 1):
                d = by_i.get(i)
                if not d or d.get("label") not in LABELS:
                    raise ValueError(f"missing/invalid label for item {i}")
                out.append((d["label"], d.get("reason", "")))
            return out
        except Exception as e:  # rate limit, malformed JSON, missing item -> retry
            wait = 45 if ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)) else 5
            print(f"    judge retry {attempt + 1}/5 in {wait}s: {str(e)[:120]}")
            time.sleep(wait)
    raise RuntimeError("judge failed 5 times on one batch")


def _matches(text, patterns):
    t = text.lower()
    return any(p.lower() in t for p in patterns)


def spotcheck(pool, golden_by_key, path, per_fault=5, seed=0):
    """Human half of the check: every disagreement with golden_chunks.json, plus a random
    sample per fault. Golden must_not_hit judged relevant / must_hit judged not relevant are
    the cases most likely to be judge errors (or golden errors) - read those first."""
    rnd = random.Random(seed)
    lines = ["# Relevance pool spot-check", "",
             "Read the disagreements first: they are where the LLM judge and the hand-made golden set",
             "(eval/golden_chunks.json) disagree. Then the random sample per fault. Mark anything wrong",
             "by editing `label` in eval/relevance_pool.json and set `\"checked\": true` on it.", ""]
    for f in pool["faults"]:
        g = golden_by_key.get((f["exercise_id"], f["code"]), {})
        must = [p for ps in g.get("must_hit", {}).values() for p in ps]
        must_not = [p for ps in g.get("must_not_hit", {}).values() for p in ps]
        dis = [c for c in f["chunks"]
               if (_matches(c["text"], must_not) and c["label"] == "relevant")
               or (_matches(c["text"], must) and c["label"] != "relevant")]
        counts = {l: sum(c["label"] == l for c in f["chunks"]) for l in LABELS}
        lines.append(f"## {f['exercise_id']} / {f['code']} — {len(f['chunks'])} candidates · "
                     + " · ".join(f"{k} {v}" for k, v in counts.items()))
        lines.append("")
        if dis:
            lines.append("**Disagreements with golden set**")
            for c in dis:
                lines.append(f"- `{c['label']}` [{c['kind']}] {c['text']}  \n  _judge:_ {c['reason']}")
            lines.append("")
        lines.append("**Random sample**")
        for c in rnd.sample(f["chunks"], min(per_fault, len(f["chunks"]))):
            lines.append(f"- `{c['label']}` [{c['kind']}] {c['text']}  \n  _judge:_ {c['reason']}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--golden", default="eval/golden_chunks.json")
    ap.add_argument("--collection", default=embedding_config.default_collection())
    ap.add_argument("--out", default="eval/relevance_pool.json")
    ap.add_argument("--spotcheck", default="compare_output/retrieval/relevance_pool_spotcheck.md")
    ap.add_argument("--judge", default=JUDGE_MODEL)
    ap.add_argument("--fault", action="append", help="exercise/code, repeatable; default all golden faults")
    args = ap.parse_args()

    import sqlalchemy as sa
    from google import genai
    from langchain_postgres.vectorstores import PGVector

    with open(args.golden, encoding="utf-8") as f:
        golden = json.load(f)["faults"]
    if args.fault:
        wanted = {tuple(x.split("/", 1)) for x in args.fault}
        golden = [g for g in golden if (g["exercise_id"], g["code"]) in wanted]

    previous = {}
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            old = json.load(f)
        for fa in old.get("faults", []):
            if old.get("judge_prompt_version") != JUDGE_PROMPT_VERSION:
                continue
            for c in fa["chunks"]:
                previous[(fa["exercise_id"], fa["code"], c["text"])] = c
        pool = old
    else:
        pool = {"faults": []}

    conn = embedding_config.get_connection()
    engine = sa.create_engine(conn)
    vs = PGVector(embeddings=embedding_config.get_embeddings(), collection_name=args.collection,
                  connection=conn, use_jsonb=True)
    client = genai.Client()

    faults_out = {(f["exercise_id"], f["code"]): f for f in pool["faults"]}
    for g in golden:
        key = (g["exercise_id"], g["code"])
        description, queries, cands = gather(vs, engine, args.collection, g)
        todo = []
        for c in cands:
            p = previous.get((*key, c["text"]))
            if p:
                c.update({k: p[k] for k in ("label", "reason", "checked") if k in p})
            else:
                todo.append(c)
        print(f"{key[0]}/{key[1]}: {len(cands)} candidates, {len(todo)} to judge")
        for i in range(0, len(todo), BATCH):
            batch = todo[i:i + BATCH]
            for c, (label, reason) in zip(batch, judge_batch(client, args.judge, g, description, batch)):
                c["label"], c["reason"] = label, reason
            print(f"  judged {min(i + BATCH, len(todo))}/{len(todo)}")
        faults_out[key] = {"exercise_id": key[0], "code": key[1], "description": description,
                           "queries": queries, "chunks": cands}
        # Write after every fault so an interrupted run keeps what it paid for.
        pool = {"_readme": __doc__.strip().splitlines()[:3],
                "collection": args.collection, "judge": args.judge,
                "judge_prompt_version": JUDGE_PROMPT_VERSION, "built": date.today().isoformat(),
                "dense_k": DENSE_K, "faults": list(faults_out.values())}
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(pool, f, ensure_ascii=False, indent=1)

    golden_all = {(g["exercise_id"], g["code"]): g
                  for g in json.load(open(args.golden, encoding="utf-8"))["faults"]}
    os.makedirs(os.path.dirname(args.spotcheck) or ".", exist_ok=True)
    spotcheck(pool, golden_all, args.spotcheck)
    print(f"written: {args.out}, {args.spotcheck}")


if __name__ == "__main__":
    main()
