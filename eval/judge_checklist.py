"""Checklist judge for the pairwise eval v2 (docs/plans/pairwise_eval_v2_plan.md sections 3-7).

One judge call reads ONE answer (never two side by side, plan section 4): the session JSON the
generator saw, the answer key for that session (eval/build_answer_key.py: facts, rule_key,
exercise_faults; --no-key leaves facts and rule_key out, plan 6.2), and the 20 items of
eval/checklist_v1.json in a seeded random order (5 on a set with no fault). It answers each item
yes or no with a quote, and per fault where the item is about every fault (review 2026-11-12
item 4). The code never makes or changes a verdict: it checks the reply's form (every item once,
yes/no, a quote where the item needs one and the quote really in the answer, per-fault answers
that agree with the item's answer), asks once more if the form is wrong, and records the call as
invalid if it is still wrong. RAG and no-RAG are compared afterwards, per session.

Judges (docs/plans/judge_selection_2026-11-14.md): groq:openai/gpt-oss-20b, groq:qwen/qwen3.8-27b,
deepinfra:<DeepSeek V4.1 Flash id>; one output file per judge. Never judge answers Qwen wrote
with Qwen. Every call that costs money needs the user's approval with --estimate's numbers.

    python eval/judge_checklist.py estimate --run capture/replay_dev_pilot_v19.json
    python eval/judge_checklist.py run --run capture/replay_dev_pilot_v19.json \\
        --judge groq:openai/gpt-oss-20b --out capture/judge_dev_gptoss.json --max-calls 4
    python eval/judge_checklist.py summarize --run capture/replay_dev_pilot_v19.json \\
        --judgments capture/judge_dev_gptoss.json capture/judge_dev_qwen.json --out report.md

Inputs: a replay run (eval/replay_captured.py: sessions with payload, rag, no_rag, aa) or, with
--units, a JSON list of {"unit": id, "payload": ..., "text": ..., "key_patch": {...}?} (the judge
exam of plan section 6, where key_patch swaps part of the key). Outputs go in capture/, which is
gitignored, because sessions carry the user's data.
"""
import argparse
import hashlib
import json
import math
import os
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "eval"))

import build_answer_key as bak  # noqa: E402

CHECKLIST = os.path.join(ROOT, "eval", "checklist_v1.json")
ANSWER_KEY = os.path.join(ROOT, "eval", "answer_key_v1.json")
# Bump when JUDGE_PROMPT, the checklist or the validation changes: older cached calls are not reused.
JUDGE_PROMPT_VERSION = 2  # 2: field order, one-span quotes, per_fault always (gpt-oss dev pilot 2026-11-14)
SEED = 6613
FORMAT_RETRIES = 1  # plan section 4: ask once more, then invalid
TRANSIENT_RETRIES = 5
CRITERIA = ("accuracy", "comprehensiveness", "professionalism", "feasibility")
GUARD_ITEMS = {"A1", "A2", "A3", "A5", "C1", "C4", "C5", "D5"}  # plan section 7: a high yes rate is expected
BOOTSTRAP = 10_000

JUDGE_PROMPT = """You are checking written feedback that an AI coach gave one person after one set of a gym
exercise. The reader is an everyday gym-goer, not a clinician or a researcher. You answer a fixed
checklist about this ONE answer, item by item, with yes or no. You do not compare it with any
other answer and you do not grade it on a scale.

How to read the answer: lines starting "Fault <rule key>:" and "Details <rule key>:" open a
fault's entry; the rule key is a label the app replaces with the fault's name, so it is not a
technical term and not an error. Judge the whole answer: content that answers an item counts
wherever it appears, not only under the label that usually holds it. Where an item asks whether a
fault has its own entry, its "Fault <rule key>:" line is the quote.
{key_rules}
How to answer:
- Answer only "yes" or "no". If you do not find what an item asks for, answer by its rule:
  an item that asks whether something is there is "no" when it is missing; an item that asks
  whether nothing is wrong is "yes" when you find nothing wrong.
- Write the fields in this order: "id", "evidence", "per_fault" (only on per_fault items), "answer".
- Quotes: each quote is ONE unbroken stretch copied word for word from the answer. Text from two
  places is two quotes joined with " | " (inside one quote you may skip words with "..."). Add
  nothing around a quote: no extra quote marks, commas or words of your own.
- An item whose "evidence_when" is "yes" needs a quote when you answer yes. One whose
  "evidence_when" is "no" needs a quote when you answer no: quote the words that make it no (for
  example the term left unexplained). Otherwise evidence may be "".
- "Moved to another fault" test: where an item says so, ask whether the text would still be true
  if it were written under another fault of this exercise (exercise_faults). If it would, answer no.
- Items marked "per_fault": fill "per_fault" FIRST, with "yes" or "no" for EVERY rule key of this
  set, also when the item's answer will be no. Then the item's "answer" follows from it: "yes" if
  every fault is "yes", "no" if any fault is "no". A per_fault item without "per_fault" is invalid.
- Do not favour a longer answer. Length counts only where it holds what an item asks for.

Session data (JSON), exactly what the coach was given:
{session}
{key_block}
The checklist (answer every item, once, in any order):
{items}

The answer to check:
<answer>
{answer}
</answer>

Return JSON only, one object per item and nothing else in the list:
{{"items": [{{"id": "<item id>", "evidence": "<quote(s) or empty>",
  "per_fault": {{"<rule key>": "yes" | "no"}}  (only on items marked per_fault),
  "answer": "yes" | "no"}}, ...]}}"""

KEY_RULES = """
The answer key below is for you, not for the coach:
1. `facts` are the true facts of this session. Use them even where you would have counted
   differently.
2. `rule_key` is not complete. Answer "no" on its account only when the answer CONTRADICTS it; a
   fact the key does not mention is not an error.
3. Give no credit for matching the key and take none off for different wording.
4. Open items are judged by their condition and examples only.
5. `exercise_faults` is only for the "moved to another fault" test. The faults of THIS set are
   in facts.faults.
"""
NO_KEY_RULES = """
There is no answer key: count and check the session data yourself.
"""


# --- inputs ----------------------------------------------------------------------------------

def load_checklist(path=CHECKLIST):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_key(path=ANSWER_KEY):
    """The committed key when it exists (plan 5.3: commit it before the test answers), else one
    built now from the cards."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return bak.build()


def units_from_run(run):
    """A replay run -> one unit per answer. `side` stays in the unit for the summary; it is
    never in what the judge sees."""
    out = []
    for s in run["sessions"]:
        for side in ("rag", "no_rag"):
            if s.get(side):
                out.append({"unit": f"{s['label']}|{side}", "label": s["label"], "side": side,
                            "payload": s["payload"], "text": s[side][0]})
        aa = s.get("aa")
        if aa:
            out.append({"unit": f"{s['label']}|aa", "label": s["label"], "side": f"aa:{aa['side']}",
                        "payload": s["payload"], "text": aa["text"]})
    return out


def load_units(run_path=None, units_path=None):
    if units_path:
        with open(units_path, encoding="utf-8") as f:
            return json.load(f)
    with open(run_path, encoding="utf-8") as f:
        return units_from_run(json.load(f))


def faults_of(payload):
    return sorted({v["rule"] for a in payload["set"].get("attempts") or [] for v in a.get("violations") or []})


def items_for(checklist, payload):
    """All 20 on a set with faults; the 5 'clean' items, with A3's clean wording, on a clean set."""
    if faults_of(payload):
        return [dict(i) for i in checklist["items"]]
    out = []
    for i in checklist["items"]:
        if i.get("clean"):
            item = dict(i)
            item["question"] = i.get("clean_question", i["question"])
            item["per_fault"] = False
            out.append(item)
    return out


def _sha(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _patched(key_for_session, patch):
    """A deep merge of key_patch into the session key (the swapped-key exam, plan 6.1)."""
    if not patch:
        return key_for_session
    out = json.loads(json.dumps(key_for_session))

    def merge(dst, src):
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                merge(dst[k], v)
            else:
                dst[k] = v
    merge(out, patch)
    return out


def build_prompt(unit, checklist, key, use_key=True, seed=SEED, only=None):
    """(prompt, the items asked in the order shown, the set's rule keys, cache identity).
    `only`: ask just the items of these criteria (--split criterion)."""
    from rag_core.prompt import model_payload
    payload = model_payload(unit["payload"])
    items = [i for i in items_for(checklist, payload) if only is None or i["criterion"] in only]
    random.Random(f"{seed}|{_sha(unit['text'])}").shuffle(items)
    shown = [{k: i[k] for k in ("id", "question", "evidence_when", "per_fault")}
             | ({"moved_to_another_fault_test": True} if i.get("transfer") else {})
             | {"yes_example": i.get("yes_example", ""), "no_example": i.get("no_example", "")}
             for i in items]
    session_key = _patched(bak.key_for_session(key, payload), unit.get("key_patch"))
    if use_key:
        key_block = "\nThe answer key:\n" + json.dumps(session_key, ensure_ascii=False) + "\n"
        rules = KEY_RULES
    else:
        key_block = "\nexercise_faults (for the moved-to-another-fault test only):\n" + json.dumps(
            session_key["exercise_faults"], ensure_ascii=False) + "\n"
        rules = NO_KEY_RULES
    # Compact JSON for the data (about half the tokens of an indented dump), one item per line.
    prompt = JUDGE_PROMPT.format(key_rules=rules, session=json.dumps(payload, ensure_ascii=False),
                                 key_block=key_block,
                                 items="[\n" + ",\n".join(json.dumps(i, ensure_ascii=False) for i in shown) + "\n]",
                                 answer=unit["text"])
    identity = {"v": JUDGE_PROMPT_VERSION, "checklist": checklist.get("checklist_version"),
                "use_key": use_key, "session": _sha(payload), "key": _sha(session_key) if use_key else None,
                "answer": _sha(unit["text"]), "seed": seed}
    if only is not None:
        identity["only"] = sorted(only)
    return prompt, items, faults_of(payload), identity


# --- the reply's form --------------------------------------------------------------------------

def _norm(text):
    text = (text or "").lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().strip('"').strip()


def _strip_wrap(part):
    """A quote with JSON debris around it ('...bottom.",' when a model writes a list of strings
    into one field): drop surrounding quote marks and commas, never words."""
    return re.sub(r'^[\s"“”,]+|[\s"“”,]+$', "", part)


def quote_found(evidence, answer):
    """Every ' | '-joined quote occurs in the answer (case, quote marks and spacing ignored;
    a quote may skip text with '...')."""
    body = _norm(answer)
    parts = [_strip_wrap(p) for p in re.split(r"\s*\|\s*", evidence or "") if _norm(_strip_wrap(p))]
    if not parts:
        return False
    for part in parts:
        pieces = [_norm(x) for x in re.split(r"\.\.\.|…", part) if _norm(x)]
        pos = 0
        for piece in pieces:
            at = body.find(piece, pos)
            if at < 0:
                return False
            pos = at + len(piece)
    return True


def validate(reply, items, faults, answer):
    """(records by id, problems). Checks form only; the verdicts are the judge's."""
    problems = []
    # Qwen on prompt v2 returns the items list bare, without {"items": ...}: same content.
    rows = reply.get("items") if isinstance(reply, dict) else reply if isinstance(reply, list) else None
    if not isinstance(rows, list):
        return {}, ["no 'items' list"]
    by_id = {}
    wanted = {i["id"]: i for i in items}
    for row in rows:
        if row in ("", None, {}):  # empty filler entries in the list carry no verdict
            continue
        if not isinstance(row, dict) or row.get("id") not in wanted:
            problems.append(f"unknown item {row.get('id') if isinstance(row, dict) else row!r}")
            continue
        if row["id"] in by_id:
            problems.append(f"{row['id']} answered twice")
            continue
        item = wanted[row["id"]]
        ans = str(row.get("answer", "")).strip().lower()
        if ans not in ("yes", "no"):
            problems.append(f"{row['id']}: answer {row.get('answer')!r}")
            continue
        evidence = row.get("evidence") or ""
        if ans == item["evidence_when"] and not quote_found(evidence, answer):
            problems.append(f"{row['id']}: {ans} needs a quote from the answer" if not evidence.strip()
                            else f"{row['id']}: quote not in the answer")
            continue
        record = {"answer": ans, "evidence": evidence}
        if item.get("per_fault") and faults:
            pf = row.get("per_fault")
            if not isinstance(pf, dict) or set(pf) != set(faults) \
                    or any(str(v).strip().lower() not in ("yes", "no") for v in pf.values()):
                problems.append(f"{row['id']}: per_fault must answer exactly {faults}")
                continue
            pf = {k: str(v).strip().lower() for k, v in pf.items()}
            if (ans == "yes") != all(v == "yes" for v in pf.values()):
                problems.append(f"{row['id']}: answer {ans} disagrees with per_fault {pf}")
                continue
            record["per_fault"] = pf
        by_id[row["id"]] = record
    missing = [i for i in wanted if i not in by_id]
    if missing and not problems:
        problems.append(f"missing {missing}")
    elif missing:
        problems.append(f"incomplete ({len(missing)} items without a valid answer)")
    return by_id, problems


# --- calling a judge ---------------------------------------------------------------------------

def make_client(spec, reasoning_effort=None, max_tokens=None, min_interval=None):
    import judge_pairwise as jp
    provider, model = jp.parse_judge(spec)
    if provider == "gemini":
        raise SystemExit("Gemini is the generator and the curator: not a judge (plan section 2)")
    client = jp.OpenAICompatClient(provider, model, reasoning_effort, min_interval)
    client.max_tokens = max_tokens
    return client


def _ask(client, prompt, log):
    """(reply, None), or (None, a format problem). Transient errors are retried here; a request
    the provider can never accept stops the run."""
    import judge_pairwise as jp
    for attempt in range(TRANSIENT_RETRIES):
        try:
            return jp.extract_json(client.complete(prompt)), None
        except (json.JSONDecodeError, ValueError) as e:
            return None, f"not JSON: {str(e)[:80]}"
        except Exception as e:  # HTTP, rate limit, timeout
            text = str(e)
            if "json_validate_failed" in text:  # Groq's JSON mode rejected the model's output
                return None, "the provider's JSON check rejected the reply"
            if "413" in text or "Request too large" in text:
                raise SystemExit(f"the request is larger than the provider allows per minute: {text[:300]}\n"
                                 "Use --split criterion and/or a lower --max-tokens.") from None
            if "per day" in text:  # Groq TPD/RPD: waiting a minute never helps; finished answers stay cached
                raise SystemExit(f"the judge's daily limit is used up: {text[:300]}\n"
                                 "Run the same command again later; it resumes from --out.") from None
            limited = any(s in text for s in ("429", "rate limit", "quota"))
            wait = 65 if limited else 5
            numbers = re.search(r"(Limit \d+, Used \d+, Requested \d+|on \w+ per \w+ \(\w+\))", text)
            log(f"    retry {attempt + 1}/{TRANSIENT_RETRIES} in {wait}s: {text[:120]}"
                + (f" ... {numbers.group(0)}" if numbers else ""))
            time.sleep(wait)
    raise RuntimeError("the judge failed on every retry")


def _one_call(client, unit, checklist, key, use_key, seed, only, log):
    prompt, items, faults, _ = build_prompt(unit, checklist, key, use_key, seed, only)
    tries = []
    for _ in range(1 + FORMAT_RETRIES):
        reply, err = _ask(client, prompt, log)
        records, problems = ({}, [err]) if err else validate(reply, items, faults, unit["text"])
        tries.append({"only": sorted(only) if only else None, "problems": problems,
                      "tokens": getattr(client, "tokens", None)}
                     # the raw reply of a failed try, to see why the form was wrong
                     | ({"reply": json.dumps(reply, ensure_ascii=False)[:6000]} if problems and reply is not None else {}))
        if not problems:
            return records, tries
    return None, tries


def judge_unit(client, unit, checklist, key, use_key=True, seed=SEED, log=print, split=None):
    """One answer, one judge: the validated items, or invalid after FORMAT_RETRIES more tries.
    split="criterion": one call per criterion (plan 6.3's remedy for cross-talk, and a smaller
    request where the provider caps tokens per minute); invalid if any of them is."""
    identity = build_prompt(unit, checklist, key, use_key, seed)[3] | ({"split": split} if split else {})
    groups = [(c,) for c in CRITERIA] if split == "criterion" else [None]
    items, tries = {}, []
    for only in groups:
        if only and not build_prompt(unit, checklist, key, use_key, seed, only)[1]:
            continue  # a clean set asks no item of this criterion
        records, t = _one_call(client, unit, checklist, key, use_key, seed, only, log)
        tries += t
        if records is None:
            return {"identity": identity, "valid": False, "items": {}, "tries": tries}
        items.update(records)
    return {"identity": identity, "valid": True, "items": items, "tries": tries}


def _cache_key(judge, identity):
    return _sha({"judge": judge, **identity})


def run(units, checklist, key, judge, out, client, use_key=True, max_calls=None, seed=SEED, log=print, split=None):
    """Judges every unit not yet in `out` (one file per judge); saved after every answer.
    max_calls counts answers (with --split criterion an answer is up to 4 requests)."""
    data = {"judge": judge, "use_key": use_key, "prompt_version": JUDGE_PROMPT_VERSION, "units": {}, "calls": {}}
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        if data["judge"] != judge or data["use_key"] != use_key:
            raise SystemExit(f"{out} holds judge {data['judge']} use_key {data['use_key']}: pick another --out")
    calls = 0
    for unit in units:
        identity = build_prompt(unit, checklist, key, use_key, seed)[3] | ({"split": split} if split else {})
        ck = _cache_key(judge, identity)
        if ck in data["calls"]:
            data["units"][unit["unit"]] = ck
            continue
        if max_calls is not None and calls >= max_calls:
            log(f"stopped at --max-calls {max_calls}")
            break
        calls += 1
        result = judge_unit(client, unit, checklist, key, use_key, seed, log, split)
        data["calls"][ck] = result
        data["units"][unit["unit"]] = ck
        log(f"  {unit['unit']}: {'ok' if result['valid'] else 'INVALID ' + '; '.join(result['tries'][-1]['problems'])[:200]}")
        tmp = out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, out)
    return data, calls


def estimate(units, checklist, key, use_key=True, out_tokens_per_item=45, split=None):
    """Requests and rough tokens (4 characters a token). No API call."""
    ins, outs = [], []
    for unit in units:
        for only in ([(c,) for c in CRITERIA] if split == "criterion" else [None]):
            prompt, items, _, _ = build_prompt(unit, checklist, key, use_key, only=only)
            if items:
                ins.append(len(prompt) / 4)
                outs.append(len(items) * out_tokens_per_item)
    return {"answers": len(units), "requests": len(ins), "input_tokens": int(sum(ins)),
            "output_tokens": int(sum(outs)), "input_per_request": int(statistics.mean(ins)) if ins else 0,
            "note": "per judge; a format retry adds a request; reasoning tokens are extra"}


# --- summary -----------------------------------------------------------------------------------

def majority(votes):
    """'yes'/'no' by strict majority of the valid votes, None on a tie or no vote (plan section 4:
    two valid votes that disagree drop the item for that answer)."""
    c = Counter(v for v in votes if v in ("yes", "no"))
    if not c:
        return None
    top, n = c.most_common(1)[0]
    return top if n * 2 > sum(c.values()) else None


def fleiss_kappa(table):
    """table: rows of [yes count, no count], every row the same number of raters."""
    rows = [r for r in table if sum(r) >= 2]
    if not rows:
        return None
    n = sum(rows[0])
    rows = [r for r in rows if sum(r) == n]
    N = len(rows)
    p = [sum(r[j] for r in rows) / (N * n) for j in (0, 1)]
    P = [(sum(x * x for x in r) - n) / (n * (n - 1)) for r in rows]
    pe = sum(x * x for x in p)
    return None if pe >= 1 else (statistics.mean(P) - pe) / (1 - pe)


def gwet_ac1(table):
    """Binary AC1 over rows of [yes, no] counts (raters may differ per row, at least 2)."""
    rows = [r for r in table if sum(r) >= 2]
    if not rows:
        return None
    pa = statistics.mean((sum(x * (x - 1) for x in r)) / (sum(r) * (sum(r) - 1)) for r in rows)
    pi = statistics.mean(r[0] / sum(r) for r in rows)
    pe = 2 * pi * (1 - pi)
    return None if pe >= 1 else (pa - pe) / (1 - pe)


def bootstrap_ci(diffs, n=BOOTSTRAP, seed=SEED):
    import numpy as np
    rng = np.random.default_rng(seed)
    d = np.array(diffs, dtype=float)
    means = d[rng.integers(0, len(d), size=(n, len(d)))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [None] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def collect(units, judgment_files, checklist):
    """unit -> item -> [vote per judge], plus per-fault votes and the invalid count per judge."""
    votes = defaultdict(lambda: defaultdict(list))
    pf_votes = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    invalid = Counter()
    judges = []
    for path in judgment_files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        judges.append(data["judge"])
        for unit in units:
            ck = data["units"].get(unit["unit"])
            call = data["calls"].get(ck) if ck else None
            if not call:
                continue
            if not call["valid"]:
                invalid[data["judge"]] += 1
                continue
            for item, rec in call["items"].items():
                votes[unit["unit"]][item].append(rec["answer"])
                for rule, v in (rec.get("per_fault") or {}).items():
                    pf_votes[unit["unit"]][item][rule].append(v)
    return votes, pf_votes, invalid, judges


def summarize(units, judgment_files, checklist, seed=SEED):
    """The markdown report of plan section 7, for whatever units and judges are given."""
    from scipy import stats
    crit_of = {i["id"]: i["criterion"] for i in checklist["items"]}
    votes, pf_votes, invalid, judges = collect(units, judgment_files, checklist)
    by_unit = {u["unit"]: u for u in units}
    verdict = {u: {item: majority(v) for item, v in items.items()} for u, items in votes.items()}
    dropped = sum(1 for u in verdict.values() for v in u.values() if v is None)

    def score(unit_id, crit=None):
        vals = [v for item, v in verdict.get(unit_id, {}).items()
                if v is not None and (crit is None or crit_of[item] == crit)]
        return sum(v == "yes" for v in vals) / len(vals) * 100 if vals else None

    lines = [f"# Checklist judge summary", "",
             f"judges: {', '.join(judges)} · answers: {len(units)} · items dropped (no majority): {dropped}"
             + (f" · invalid calls: {dict(invalid)}" if invalid else ""), ""]

    pairs = defaultdict(dict)
    for u in units:
        if u.get("side") in ("rag", "no_rag"):
            pairs[u["label"]][u["side"]] = u["unit"]
    fault_pairs, clean_pairs = [], []
    for label, sides in sorted(pairs.items()):
        if "rag" not in sides or "no_rag" not in sides:
            continue
        r, n = score(sides["rag"]), score(sides["no_rag"])
        if r is None or n is None:
            continue
        (fault_pairs if faults_of(by_unit[sides["rag"]]["payload"]) else clean_pairs).append((label, r, n, sides))

    if fault_pairs:
        diffs = [r - n for _, r, n, _ in fault_pairs]
        mean = statistics.mean(diffs)
        lines += ["## Main number: RAG - no-RAG on sessions with a fault", "",
                  f"sessions: {len(diffs)} · mean difference: {mean:+.1f} points ({mean / 5:+.2f} items of 20)"]
        if len(diffs) >= 2:
            lo, hi = bootstrap_ci(diffs, seed=seed)
            verdict_text = ("RAG better" if lo > 0 else "no-RAG better" if hi < 0 else "no difference found")
            lines.append(f"bootstrap 95% CI: [{lo:+.1f}, {hi:+.1f}] -> {verdict_text}")
        wins, losses = sum(d > 0 for d in diffs), sum(d < 0 for d in diffs)
        lines.append(f"win / loss / tie: {wins} / {losses} / {len(diffs) - wins - losses}"
                     + (f" · sign test p = {stats.binomtest(wins, wins + losses).pvalue:.3f}" if wins + losses else ""))
        if any(diffs) and len(diffs) >= 2:
            lines.append(f"Wilcoxon signed-rank p = {stats.wilcoxon(diffs).pvalue:.3f} (supporting only)")
        if len(diffs) < 20:
            lines.append(f"**{len(diffs)} sessions: too few for a conclusion; read as a pilot.**")
        lines += ["", "| criterion | RAG | no-RAG | diff | Wilcoxon p | Holm |", "|---|---|---|---|---|---|"]
        rows, ps = [], []
        for crit in CRITERIA:
            d = [(score(s["rag"], crit), score(s["no_rag"], crit)) for _, _, _, s in fault_pairs]
            d = [(a, b) for a, b in d if a is not None and b is not None]
            diff = [a - b for a, b in d]
            p = stats.wilcoxon(diff).pvalue if len(diff) >= 2 and any(diff) else 1.0
            rows.append((crit, statistics.mean(a for a, _ in d), statistics.mean(b for _, b in d), statistics.mean(diff)))
            ps.append(p)
        for (crit, a, b, diff), p, h in zip(rows, ps, _holm(ps)):
            lines.append(f"| {crit} | {a:.1f} | {b:.1f} | {diff:+.1f} | {p:.3f} | {h:.3f} |")
        a5 = {side: sum(verdict.get(s[side], {}).get("A5") == "no" for _, _, _, s in fault_pairs) for side in ("rag", "no_rag")}
        disc_r = sum(verdict.get(s["rag"], {}).get("A5") == "no" and verdict.get(s["no_rag"], {}).get("A5") == "yes"
                     for _, _, _, s in fault_pairs)
        disc_n = sum(verdict.get(s["no_rag"], {}).get("A5") == "no" and verdict.get(s["rag"], {}).get("A5") == "yes"
                     for _, _, _, s in fault_pairs)
        lines += ["", f"A5 failed: RAG {a5['rag']} · no-RAG {a5['no_rag']}"
                  + (f" · McNemar exact p = {stats.binomtest(disc_r, disc_r + disc_n).pvalue:.3f}" if disc_r + disc_n else "")]
        lines += ["", "| session | RAG | no-RAG | diff |", "|---|---|---|---|"]
        lines += [f"| {label} | {r:.0f} | {n:.0f} | {r - n:+.0f} |" for label, r, n, _ in fault_pairs]

    if clean_pairs:
        lines += ["", "## Clean sessions (reported apart)", ""]
        lines += [f"- {label}: RAG {r:.0f} · no-RAG {n:.0f}" for label, r, n, _ in clean_pairs]

    aa = [(u, by_unit.get(f"{u['label']}|{u['side'].split(':', 1)[1]}")) for u in units if str(u.get("side", "")).startswith("aa:")]
    aa_d = [score(a["unit"]) - score(b["unit"]) for a, b in aa if b and score(a["unit"]) is not None and score(b["unit"]) is not None]
    if aa_d:
        lines += ["", f"## A/A: {len(aa_d)} redraws · mean |diff| {statistics.mean(abs(x) for x in aa_d):.1f}"
                  + (f" · SD {statistics.stdev(aa_d):.1f}" if len(aa_d) >= 2 else "")]

    lines += ["", "## Items", "", "| item | yes rate (both sides) | RAG | no-RAG | % all agree | AC1 | Fleiss k | note |",
              "|---|---|---|---|---|---|---|---|"]
    for item in [i["id"] for i in checklist["items"]]:
        vs = {u: verdict[u].get(item) for u in verdict if verdict[u].get(item) is not None}
        if not vs:
            continue
        rate = sum(v == "yes" for v in vs.values()) / len(vs) * 100
        side_rate = {}
        for side in ("rag", "no_rag"):
            s = [v for u, v in vs.items() if by_unit[u].get("side") == side]
            side_rate[side] = f"{sum(v == 'yes' for v in s) / len(s) * 100:.0f}" if s else "-"
        table = [[votes[u][item].count("yes"), votes[u][item].count("no")] for u in votes if votes[u].get(item)]
        agree = [r for r in table if sum(r) >= 2]
        all_agree = f"{sum(1 for r in agree if 0 in r) / len(agree) * 100:.0f}" if agree else "-"
        ac1, kappa = gwet_ac1(table), fleiss_kappa(table)
        note = ""
        if item not in GUARD_ITEMS and rate >= 90:
            note = "ceiling"
        elif rate <= 10:
            note = "floor"
        if ac1 is not None and ac1 < 0.6:
            note = (note + " AC1<0.6").strip()
        lines.append(f"| {item} | {rate:.0f} | {side_rate['rag']} | {side_rate['no_rag']} | {all_agree} | "
                     f"{'-' if ac1 is None else f'{ac1:.2f}'} | {'-' if kappa is None else f'{kappa:.2f}'} | {note} |")

    pf_rate = defaultdict(lambda: Counter())
    for u, items in pf_votes.items():
        for item, rules in items.items():
            for rule, vs in rules.items():
                m = majority(vs)
                if m:
                    pf_rate[(by_unit[u].get("side"), rule)][m] += 1
    if pf_rate:
        lines += ["", "## Per-fault pass rate (all per-fault items pooled)", "", "| fault | RAG | no-RAG |", "|---|---|---|"]
        for rule in sorted({r for _, r in pf_rate}):
            cells = []
            for side in ("rag", "no_rag"):
                c = pf_rate.get((side, rule))
                cells.append(f"{c['yes'] / (c['yes'] + c['no']) * 100:.0f}% of {c['yes'] + c['no']}" if c else "-")
            lines.append(f"| {rule} | {cells[0]} | {cells[1]} |")

    words = [(len(by_unit[u]["text"].split()), score(u)) for u in verdict if score(u) is not None]
    if len(words) >= 3:
        varies = len({w for w, _ in words}) > 1 and len({s for _, s in words}) > 1
        r = f"{stats.pearsonr([w for w, _ in words], [s for _, s in words]).statistic:.2f}" if varies else "undefined (no spread)"
        side_words = {side: [len(u["text"].split()) for u in units if u.get("side") == side] for side in ("rag", "no_rag")}
        lines += ["", "## Length (supporting only)", "",
                  "words per answer: " + " · ".join(f"{s} {statistics.mean(w):.0f}" for s, w in side_words.items() if w)
                  + f" · correlation of words with score r = {r}"]
    return "\n".join(lines) + "\n"


# --- command line ------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["estimate", "run", "summarize", "prompt"])
    ap.add_argument("--run", help="replay run JSON (eval/replay_captured.py)")
    ap.add_argument("--units", help="a units JSON instead of --run (the judge exam)")
    ap.add_argument("--judge", help="<provider>:<model>, e.g. groq:openai/gpt-oss-20b")
    ap.add_argument("--reasoning-effort", default="low", help="gpt-oss only (default low)")
    ap.add_argument("--max-tokens", type=int, help="cap the reply (DeepSeek: output can balloon)")
    ap.add_argument("--split", choices=["criterion"], help="one request per criterion (plan 6.3; smaller requests "
                                                           "for a provider's tokens-per-minute cap)")
    ap.add_argument("--min-interval", type=float, help="seconds between requests (Groq free tier: 62 with --split)")
    ap.add_argument("--no-key", action="store_true", help="without facts and rule_key (plan 6.2)")
    ap.add_argument("--max-calls", type=int)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", help="run: the judge's JSON (one per judge) · summarize: markdown path")
    ap.add_argument("--judgments", nargs="+", help="summarize: the judges' JSON files")
    args = ap.parse_args()
    if not (args.run or args.units):
        raise SystemExit("--run or --units")
    checklist, key = load_checklist(), load_key()
    units = load_units(args.run, args.units)
    use_key = not args.no_key

    if args.command == "estimate":
        print(json.dumps(estimate(units, checklist, key, use_key, split=args.split), indent=1))
    elif args.command == "prompt":
        print(build_prompt(units[0], checklist, key, use_key, args.seed)[0])
    elif args.command == "run":
        if not args.judge or not args.out:
            raise SystemExit("run needs --judge and --out")
        import judge_pairwise as jp
        judge = jp.judge_id(args.judge, args.reasoning_effort) + (f"#max{args.max_tokens}" if args.max_tokens else "")
        client = make_client(args.judge, args.reasoning_effort, args.max_tokens, args.min_interval)
        data, calls = run(units, checklist, key, judge, args.out, client, use_key, args.max_calls, args.seed,
                          split=args.split)
        valid = sum(1 for c in data["calls"].values() if c["valid"])
        print(f"{calls} calls this time · {valid}/{len(data['calls'])} valid in {args.out}")
    else:
        report = summarize(units, args.judgments or [], checklist, args.seed)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(report)
        print(report)


if __name__ == "__main__":
    main()
