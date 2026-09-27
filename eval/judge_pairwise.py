"""Blind pairwise LLM judge over two `test_rag_compare.py --samples N` runs.

eval/eval_retrieval.py says whether better chunks reached the context; eval_generation.py
says whether the answer copied them or left jargon unexplained. Neither says whether the
answer got BETTER COACHING. This script asks a judge that, the way SportsGPT's experts were
asked (double-blind, four dimensions: Accuracy, Comprehensiveness, Professionalism,
Feasibility), but pairwise: one judge call sees the same session answered by run A and by
run B, in a random order, with nothing that says which run is which, and picks a winner per
dimension plus overall. Pairwise instead of absolute 1-5 because the differences between two
retrieval settings are small, and a judge separates two answers side by side far more
reliably than it places each on a fixed scale (1-5 scores are also collected, secondary).

Pairing: session by `label`, sample i of A against sample i of B. Order per pair is drawn
from Random(f"{seed}|{label}|{i}"), so it does not depend on which sessions are included.
The judge sees the session JSON (what the generator saw, minus the context) and the two
answers - NOT the retrieved context: it differs between the runs and would unblind them.

Sessions whose context is identical in A and B (e.g. the clean session - no fault, so the
query profile does not apply) are reported separately as a CONTROL: any win rate there is
pure sampling noise + judge noise, which is the yardstick for the main number.

Resumable: every judgment is cached in the output JSON, keyed by prompt version, judge
model and the exact texts in their shown order.

    python eval/judge_pairwise.py compare_output/g1_R0.json compare_output/g1_R4.json \\
        --names R0 R4 --out compare_output/g1_pairwise_R0_vs_R4.md
"""
import argparse
import hashlib
import json
import math
import os
import random
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))

# A different model from the generator (test_rag_compare.LLM_MODEL = gemini-3.5-flash-lite),
# so the judge is not grading its own phrasing. Only a Gemini key is configured, so it is
# the same family - see the G1 entry in compare_output/ablation_log.md.
JUDGE_MODEL = "gemini-3.8-flash"
# Bump when JUDGE_PROMPT changes: cached judgments from an older prompt are not reused.
JUDGE_PROMPT_VERSION = 1
CRITERIA = ("accuracy", "comprehensiveness", "professionalism", "feasibility")
# Same marker test_rag_compare.generate_feedback_compare() writes for a failed call.
GENERATION_ERROR = "Error occurred during generation"

JUDGE_PROMPT = """You are a senior strength and conditioning coach reviewing written feedback that an AI
coach produced for one gym session. The reader of the feedback is an everyday gym-goer, not a
clinician or a researcher. Two feedback reports were written for the SAME session data. Compare them.

Session data (JSON) - the reps, errors and scores both reports were given:
{session}
{reference}
<response_1>
{r1}
</response_1>

<response_2>
{r2}
</response_2>

Compare the two on each criterion:
- accuracy - interpretation correctness: each fault is described correctly for this exercise; rep
  numbers, rep counts, scores and error names match the session data; the stated causes and
  consequences are biomechanically correct; no advice that would make the fault worse; no number
  or fact that looks invented or wrong.
- comprehensiveness - inference depth: every fault in this session is covered; it explains why
  the fault happens and why it matters to this lifter, not only what it is; it uses the rep detail
  (which reps, which phase) and the comparison with the previous session.
- professionalism - expert-level specificity: it reads like an experienced coach who knows this
  particular fault - causes, cues and drills specific to it - rather than generic advice that
  would fit any fault or any exercise.
- feasibility - actionability of quantitative details: the lifter could act on it in the next
  session - concrete cues, setup changes that name a variable, drills or regressions with sets,
  reps, tempo, load or a range target, and a way to check it worked. Vague advice ("focus on your
  form") and advice the reader cannot understand are not actionable.

Rules:
- The order of the two responses is random. Do not favour a position.
- Do not favour the longer response. Length counts only where it adds correct, usable content;
  padding and repetition count against it.
- If the session has no errors, the better response credits the clean session and plans how to
  hold the standard; inventing a fault to fix is an accuracy error.
- Use "tie" only when you genuinely cannot separate them on that criterion.
- "overall": which report you would rather hand to this lifter.
- Also score each response 1-5 on each criterion (1 poor, 3 adequate, 5 excellent).

Return JSON only:
{{"accuracy": {{"winner": "1" | "2" | "tie", "reason": "<max 25 words>"}},
  "comprehensiveness": {{...same...}}, "professionalism": {{...same...}}, "feasibility": {{...same...}},
  "overall": {{"winner": "1" | "2" | "tie", "reason": "<max 25 words>"}},
  "scores": {{"1": {{"accuracy": <1-5>, "comprehensiveness": <1-5>, "professionalism": <1-5>, "feasibility": <1-5>}},
             "2": {{...same...}}}}}}"""

# --reference union: the entries of BOTH runs' retrieved contexts, headers dropped, de-duplicated
# and shuffled, so the judge can check a specific fact without learning which run saw which
# entry. Added after the G1 smoke run: judged with no reference, a KB-grounded but unfamiliar fix
# (a 2-inch heel lift for knee valgus, straight from an R4 chunk) was called "excessive" and
# "bizarre" and decided every criterion - a judge without the evidence grades against its own
# general knowledge, i.e. against exactly what a no-RAG answer already has.
REFERENCE_BLOCK = """
Reference notes - knowledge-base entries that were retrieved for this session. Either report may
have seen any subset of them; their order is random; some may be irrelevant to this session's
fault. Use them only to check specific facts: advice that agrees with a note is not wrong merely
because it is unusual, and a note can also show a report got something wrong. Do not reward a
report just for using the notes - judge the coaching.
<reference_notes>
{notes}
</reference_notes>
"""


def context_entries(context):
    """Entry texts of a rendered context (test_rag_compare.retrieve_kb_context), headers dropped."""
    out = []
    for block in (context or "").split("\n\n"):
        lines = block.strip().splitlines()
        if lines and lines[0].startswith("[") and lines[0].endswith("]"):
            lines = lines[1:]
        text = " ".join(l.strip() for l in lines).strip()
        # test_rag_compare.NO_MATCH_CONTEXT is a placeholder, not a note
        if text and not text.startswith("No highly relevant knowledge-base entries"):
            out.append(text)
    return out


def reference_notes(ctx_a, ctx_b, seed, label):
    notes = list(dict.fromkeys(context_entries(ctx_a) + context_entries(ctx_b)))
    notes.sort()  # order independent of which run contributed first, before the shuffle
    random.Random(f"{seed}|{label}|notes").shuffle(notes)
    return "\n".join(f"- {n}" for n in notes)


def load_run(path, side):
    with open(path, encoding="utf-8") as f:
        run = json.load(f)
    if side not in ("rag", "no_rag"):
        raise ValueError(f"side must be rag or no_rag, got {side!r}")
    return run, {s["label"]: s for s in run["sessions"]}


def make_pairs(run_a, sess_a, side_a, run_b, sess_b, side_b, seed, reference):
    """[(label, i, text_a, text_b, a_first, same_context, payload, notes)] + list of skip notes.
    `notes` = the reference_notes() text under --reference union, else ""."""
    pairs, skipped = [], []
    for label, sa in sess_a.items():
        sb = sess_b.get(label)
        if sb is None:
            skipped.append(f"{label}: not in B")
            continue
        if sa["payload"] != sb["payload"]:
            raise ValueError(f"{label}: session payload differs between the runs - not the same session")
        # Same context only matters when both sides are RAG answers from their own context.
        same = side_a == side_b == "rag" and sa["context"] == sb["context"]
        notes = reference_notes(sa["context"], sb["context"], seed, label) if reference == "union" else ""
        for i, (ta, tb) in enumerate(zip(sa[side_a], sb[side_b]), 1):
            if ta.startswith(GENERATION_ERROR) or tb.startswith(GENERATION_ERROR):
                skipped.append(f"{label} #{i}: generation error")
                continue
            a_first = random.Random(f"{seed}|{label}|{i}").random() < 0.5
            pairs.append((label, i, ta, tb, a_first, same, sa["payload"], notes))
    return pairs, skipped


def cache_key(model, payload, first, second, notes):
    h = hashlib.sha1()
    for part in (str(JUDGE_PROMPT_VERSION), model, json.dumps(payload, sort_keys=True), notes, "\x00",
                 first, "\x00", second):
        h.update(part.encode("utf-8"))
    return h.hexdigest()


def build_prompt(payload, first, second, notes):
    return JUDGE_PROMPT.format(session=json.dumps(payload, indent=2), r1=first, r2=second,
                               reference=REFERENCE_BLOCK.format(notes=notes) if notes else "")


def judge(client, model, payload, first, second, notes):
    from google.genai import types
    prompt = build_prompt(payload, first, second, notes)
    for attempt in range(5):
        try:
            resp = client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"))
            data = json.loads(resp.text)
            for c in CRITERIA + ("overall",):
                if str(data[c]["winner"]) not in ("1", "2", "tie"):
                    raise ValueError(f"bad winner for {c}: {data[c]['winner']!r}")
                data[c]["winner"] = str(data[c]["winner"])
            for pos in ("1", "2"):
                for c in CRITERIA:
                    if int(data["scores"][pos][c]) not in range(1, 6):
                        raise ValueError(f"bad score {pos}/{c}")
            return data
        except Exception as e:  # rate limit, malformed JSON, missing field -> retry
            wait = 45 if ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)) else 5
            print(f"    judge retry {attempt + 1}/5 in {wait}s: {str(e)[:120]}")
            time.sleep(wait)
    raise RuntimeError("judge failed 5 times on one pair")


def unblind(judgment, a_first):
    """Judge positions '1'/'2' -> 'A'/'B'/'tie' per criterion, and scores per run."""
    pos = {"1": "A" if a_first else "B", "2": "B" if a_first else "A", "tie": "tie"}
    out = {c: pos[judgment[c]["winner"]] for c in CRITERIA + ("overall",)}
    out["scores"] = {pos[p]: {c: int(judgment["scores"][p][c]) for c in CRITERIA} for p in ("1", "2")}
    out["first_won"] = judgment["overall"]["winner"] == "1" if judgment["overall"]["winner"] != "tie" else None
    return out


def sign_test(wins, losses):
    """Two-sided exact binomial p for wins vs losses at p=0.5, ties dropped."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, j) for j in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def tally(rows, name_a, name_b):
    lines = [f"| criterion | {name_a} wins | {name_b} wins | tie | sign test p |", "|---|---|---|---|---|"]
    for c in CRITERIA + ("overall",):
        n = Counter(r["result"][c] for r in rows)
        lines.append(f"| {c} | {n['A']} | {n['B']} | {n['tie']} | {sign_test(n['A'], n['B']):.3f} |")
    lines.append("")
    lines.append(f"| mean 1-5 score | {name_a} | {name_b} |")
    lines.append("|---|---|---|")
    for c in CRITERIA:
        ma = sum(r["result"]["scores"]["A"][c] for r in rows) / len(rows)
        mb = sum(r["result"]["scores"]["B"][c] for r in rows) / len(rows)
        lines.append(f"| {c} | {ma:.2f} | {mb:.2f} |")
    return lines


def render(rows, skipped, args, run_a, run_b):
    na, nb = args.names
    out = [f"# Pairwise judge — {na} vs {nb}", "",
           f"A = **{na}** `{args.a}` ({args.side_a}) · B = **{nb}** `{args.b}` ({args.side_b}) · "
           f"judge `{args.judge}` prompt v{JUDGE_PROMPT_VERSION} @ temperature 0 · seed {args.seed} · "
           f"reference notes: **{args.reference}**",
           f"generator A `{run_a['llm']}` @ {run_a['temperature']}, retrieval {run_a['retrieval']} · "
           f"generator B `{run_b['llm']}` @ {run_b['temperature']}, retrieval {run_b['retrieval']}", ""]
    if run_a.get("system_prompt_sha1") != run_b.get("system_prompt_sha1"):
        out += ["**Warning: the two runs used different system prompts.**", ""]
    main = [r for r in rows if not r["same_context"]]
    ctrl = [r for r in rows if r["same_context"]]
    groups = [("Sessions whose context differs (the comparison)", main),
              ("Control — identical context in both runs (noise yardstick)", ctrl)]
    if args.side_a != "rag" or args.side_b != "rag":
        groups = [("All pairs", rows)]
    for title, grp in groups:
        if not grp:
            continue
        out += [f"## {title} — {len(grp)} pairs", ""] + tally(grp, na, nb) + [""]

    decided = [r for r in rows if r["result"]["first_won"] is not None]
    if decided:
        fw = sum(r["result"]["first_won"] for r in decided)
        out += [f"Position check: the response shown first won `overall` in {fw}/{len(decided)} "
                f"decided pairs ({fw / len(decided):.0%}; 50% = no position bias) · "
                f"{na} shown first in {sum(r['a_first'] for r in rows)}/{len(rows)} pairs.", ""]

    out += ["## Per session (overall)", "",
            f"| session | same context | {na} | {nb} | tie | mean overall-criteria score {na} / {nb} |",
            "|---|---|---|---|---|---|"]
    by_label = defaultdict(list)
    for r in rows:
        by_label[r["label"]].append(r)
    for label, grp in by_label.items():
        n = Counter(r["result"]["overall"] for r in grp)
        ma = sum(sum(r["result"]["scores"]["A"].values()) for r in grp) / (len(grp) * len(CRITERIA))
        mb = sum(sum(r["result"]["scores"]["B"].values()) for r in grp) / (len(grp) * len(CRITERIA))
        out.append(f"| {label} | {'yes' if grp[0]['same_context'] else 'no'} | {n['A']} | {n['B']} | "
                   f"{n['tie']} | {ma:.2f} / {mb:.2f} |")
    if skipped:
        out += ["", "Skipped: " + "; ".join(skipped)]

    if args.show_reasons:
        out += ["", "## Judge reasons", ""]
        for r in rows:
            j = r["judgment"]
            who = {"1": na if r["a_first"] else nb, "2": nb if r["a_first"] else na, "tie": "tie"}
            out.append(f"**{r['label']} #{r['sample']}** — overall: {who[j['overall']['winner']]} — "
                       f"{j['overall']['reason']}")
            for c in CRITERIA:
                out.append(f"- {c}: {who[j[c]['winner']]} — {j[c]['reason']}")
            out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a", help="run A: JSON written by test_rag_compare.py")
    ap.add_argument("b", help="run B: JSON written by test_rag_compare.py")
    ap.add_argument("--names", nargs=2, default=("A", "B"), help="display names for A and B")
    ap.add_argument("--side-a", default="rag", help="rag | no_rag (default rag)")
    ap.add_argument("--side-b", default="rag", help="rag | no_rag (default rag)")
    ap.add_argument("--judge", default=JUDGE_MODEL)
    ap.add_argument("--reference", choices=["none", "union"], default="none",
                    help="none: judge sees session + answers only (SportsGPT-style); union: also both runs' "
                         "context entries, shuffled and unlabelled, to check facts against (default none)")
    ap.add_argument("--seed", default="0", help="order-randomisation seed (default 0)")
    ap.add_argument("--session", action="append", help="only this session label (repeatable)")
    ap.add_argument("--max-samples", type=int, help="only the first N samples per session")
    ap.add_argument("--show-reasons", action="store_true", help="append every judge reason to the report")
    ap.add_argument("--out", required=True, help="markdown report; judgments cached in the same stem .json")
    args = ap.parse_args()

    run_a, sess_a = load_run(args.a, args.side_a)
    run_b, sess_b = load_run(args.b, args.side_b)
    if args.session:
        sess_a = {k: v for k, v in sess_a.items() if k in args.session}
    pairs, skipped = make_pairs(run_a, sess_a, args.side_a, run_b, sess_b, args.side_b, args.seed,
                                args.reference)
    if args.max_samples:
        pairs = [p for p in pairs if p[1] <= args.max_samples]

    cache_path = os.path.splitext(args.out)[0] + ".json"
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f).get("judgments", {})

    client = None
    rows = []
    for n, (label, i, ta, tb, a_first, same, payload, notes) in enumerate(pairs, 1):
        first, second = (ta, tb) if a_first else (tb, ta)
        key = cache_key(args.judge, payload, first, second, notes)
        if key not in cache:
            if client is None:
                from google import genai
                client = genai.Client()
            print(f"[{n}/{len(pairs)}] judging {label} #{i}")
            cache[key] = judge(client, args.judge, payload, first, second, notes)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({"judge": args.judge, "judge_prompt_version": JUDGE_PROMPT_VERSION,
                           "judgments": cache}, f, ensure_ascii=False, indent=1)
        rows.append({"label": label, "sample": i, "a_first": a_first, "same_context": same,
                     "judgment": cache[key], "result": unblind(cache[key], a_first)})

    text = render(rows, skipped, args, run_a, run_b)
    print(text)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(f"\nwritten: {args.out} (judgments: {cache_path})")


if __name__ == "__main__":
    main()
