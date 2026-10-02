"""Check eval/rule_cards.json - the eval v6 answer key (docs/eval_v6_plan.md E1).

Two kinds of check, both deterministic, no LLM call:

    structure   - every field the judge and the renderer need is there, the anchor counts
                  meet the plan (relevant >= 5, wrong_fault >= 5 of which >= 2 from a
                  sibling rule, irrelevant >= 3), every depends_on names a real open
                  question, and the cards cover exactly the rules the system-1 spec lists.
    n-gram      - no anchor shares a run of MIN_NGRAM words or more with the KB. The
                  anchors must be written from the rule, not lifted from the KB; a long
                  shared run means the answer key borrowed the KB's wording, which is the
                  leakage the plan exists to remove.

The KB text is read by this script only. It prints the shared words (which are the
anchor's own words) and never the KB passage around them, so running it does not expose
KB content to whoever is writing anchors.

With --queries it also checks the Q-spec queries in error_taxonomy.py (eval_v6_plan.md
E2): their keys must be exactly the spec's rules, and each query must share fewer than
MIN_NGRAM words in a row with the KB and with every card's anchors (a query built from
the anchors would score well on them because it already holds the answer).

Usage:
    python eval/check_rule_cards.py
    python eval/check_rule_cards.py --kb curated_data_v5 --min-ngram 5
    python eval/check_rule_cards.py --skip-ngram          # structure only
    python eval/check_rule_cards.py --queries             # + Q-spec in error_taxonomy.py
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from eval_generation import shared_spans, word_tokens  # noqa: E402

CARDS = os.path.join(HERE, "rule_cards.json")
SPEC = os.path.join(ROOT, "docs", "system1", "RULES_AND_FSM_CONDENSED.md")
KB_DEFAULT = os.path.join(ROOT, "curated_data_v5")
MIN_NGRAM = 5

MIN_COUNTS = {"relevant": 5, "wrong_fault": 5, "irrelevant": 3}
MIN_SIBLING = 2
RELEVANT_INFO_KEYS = ("appearance", "causes", "consequences", "fixes", "correct_form")
SPEC_EXERCISES = {"Squat": "squat", "Push-up": "push-up", "Lunge": "lunge", "Bicep curl": "bicep-curl"}
# Word tokens never contain "|", so it breaks a shared run at every KB string boundary.
BOUNDARY = "|"


def spec_rules(path=SPEC):
    """{exercise_id: [rule name, ...]} from the spec's summary index table."""
    rules = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 4 and cells[0] in SPEC_EXERCISES:
                rules[SPEC_EXERCISES[cells[0]]] = [r.strip() for r in cells[3].split(",")]
    return rules


def _pair(obj, where, errors):
    if not isinstance(obj, dict) or not str(obj.get("en", "")).strip() or not str(obj.get("th", "")).strip():
        errors.append(f"{where}: needs non-empty 'en' and 'th'")


def check_structure(data, spec):
    errors = []
    cards = data.get("cards", [])
    seen_ids = set()
    current = {}                                       # (exercise, rule name) -> concept_id
    for card in cards:
        cid = card.get("concept_id", "?")
        if cid in seen_ids:
            errors.append(f"{cid}: duplicate concept_id")
        seen_ids.add(cid)
        for key in ("card_version", "exercise_id", "rule_names", "cue", "measures", "definition",
                    "includes", "excludes", "relevant_info", "anchors", "open_questions", "approval"):
            if key not in card:
                errors.append(f"{cid}: missing '{key}'")
        if not card.get("rule_names"):
            errors.append(f"{cid}: rule_names is empty")
            continue
        current[(card["exercise_id"], card["rule_names"][0])] = cid

        _pair(card.get("definition"), f"{cid}.definition", errors)
        for field in ("includes", "excludes"):
            for i, item in enumerate(card.get(field, [])):
                _pair(item, f"{cid}.{field}[{i}]", errors)
        for key in RELEVANT_INFO_KEYS:
            _pair(card.get("relevant_info", {}).get(key), f"{cid}.relevant_info.{key}", errors)

        oq_ids = {q.get("id") for q in card.get("open_questions", [])}
        for q in card.get("open_questions", []):
            _pair(q, f"{cid}.open_questions.{q.get('id')}", errors)
        for field in ("includes", "excludes"):
            for item in card.get(field, []):
                if "depends_on" in item and item["depends_on"] not in oq_ids:
                    errors.append(f"{cid}.{field}: depends_on {item['depends_on']} is not an open question")

        anchors = card.get("anchors", {})
        anchor_ids = set()
        for label, need in MIN_COUNTS.items():
            items = anchors.get(label, [])
            if len(items) < need:
                errors.append(f"{cid}: {len(items)} {label} anchors, need >= {need}")
            for a in items:
                aid = a.get("id")
                if aid in anchor_ids:
                    errors.append(f"{cid}: duplicate anchor id {aid}")
                anchor_ids.add(aid)
                if not a.get("text", "").strip() or not a.get("th", "").strip():
                    errors.append(f"{cid}.{aid}: needs non-empty 'text' and 'th'")
                if "depends_on" in a and a["depends_on"] not in oq_ids:
                    errors.append(f"{cid}.{aid}: depends_on {a['depends_on']} is not an open question")
                if label == "wrong_fault" and not a.get("fault"):
                    errors.append(f"{cid}.{aid}: wrong_fault anchor needs 'fault'")

    # Coverage against the spec, and siblings must be real rules of the same exercise.
    for ex, names in spec.items():
        for name in names:
            if (ex, name) not in current:
                errors.append(f"spec rule {ex}/{name} has no card with rule_names[0] == '{name}'")
    spec_pairs = {(ex, n) for ex, names in spec.items() for n in names}
    for pair, cid in current.items():
        if pair not in spec_pairs:
            errors.append(f"{cid}: rule_names[0] '{pair[1]}' is not a {pair[0]} rule in the spec")
    for card in cards:
        cid, ex = card.get("concept_id"), card.get("exercise_id")
        siblings = [a for a in card.get("anchors", {}).get("wrong_fault", []) if a.get("sibling")]
        need = min(MIN_SIBLING, len(spec.get(ex, [])) - 1)
        if len(siblings) < need:
            errors.append(f"{cid}: {len(siblings)} sibling wrong_fault anchors, need >= {need}")
        for a in siblings:
            if (ex, a.get("fault")) not in current or a.get("fault") == card["rule_names"][0]:
                errors.append(f"{cid}.{a.get('id')}: sibling fault '{a.get('fault')}' is not another {ex} rule")
    return errors


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def kb_tokens(kb_dir):
    """Every string in every JSON file under kb_dir, tokenised, with a boundary between strings."""
    tokens, n_files = [], 0
    for dirpath, _, files in os.walk(kb_dir):
        for name in sorted(files):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(dirpath, name), encoding="utf-8") as f:
                data = json.load(f)
            n_files += 1
            for s in _strings(data):
                tokens.extend(word_tokens(s))
                tokens.append(BOUNDARY)
    return tokens, n_files


def check_ngrams(data, kb, min_len):
    """-> [(concept_id, anchor id, length, shared words)] for every anchor run >= min_len."""
    hits = []
    for card in data["cards"]:
        for label in MIN_COUNTS:
            for a in card["anchors"].get(label, []):
                for ln, words in shared_spans(word_tokens(a["text"]), kb, min_len):
                    hits.append((card["concept_id"], a["id"], ln, words))
    return hits


def anchor_tokens(data):
    """Every anchor of every card, tokenised, with a boundary between anchors."""
    tokens = []
    for card in data["cards"]:
        for label in MIN_COUNTS:
            for a in card["anchors"].get(label, []):
                tokens.extend(word_tokens(a["text"]))
                tokens.append(BOUNDARY)
    return tokens


def check_queries(spec, corpora, min_len):
    """-> (errors, hits). errors: taxonomy keys that differ from the spec. hits:
    [(exercise/rule, corpus name, length, shared words)] for every query run >= min_len."""
    sys.path.insert(0, ROOT)
    from error_taxonomy import ERROR_TAXONOMY

    errors = []
    for ex in sorted(set(spec) | set(ERROR_TAXONOMY)):
        want, got = spec.get(ex, []), list(ERROR_TAXONOMY.get(ex, {}))
        if sorted(want) != sorted(got):
            errors.append(f"error_taxonomy[{ex!r}] keys {got} != spec rules {want}")
    hits = []
    for ex, faults in ERROR_TAXONOMY.items():
        for code, entry in faults.items():
            for name, tokens in corpora:
                for ln, words in shared_spans(word_tokens(entry["query"]), tokens, min_len):
                    hits.append((f"{ex}/{code}", name, ln, words))
    return errors, hits


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cards", default=CARDS)
    ap.add_argument("--kb", default=KB_DEFAULT, help="curated KB folder to compare anchors against")
    ap.add_argument("--min-ngram", type=int, default=MIN_NGRAM)
    ap.add_argument("--skip-ngram", action="store_true")
    ap.add_argument("--queries", action="store_true",
                    help="also check the Q-spec queries in error_taxonomy.py against the KB and the anchors")
    args = ap.parse_args()

    with open(args.cards, encoding="utf-8") as f:
        data = json.load(f)
    spec = spec_rules()
    errors = check_structure(data, spec)
    n_anchors = sum(len(c["anchors"].get(k, [])) for c in data["cards"] for k in MIN_COUNTS)
    print(f"cards: {len(data['cards'])} · anchors: {n_anchors} · spec rules: {sum(map(len, spec.values()))}")
    for e in errors:
        print(f"  STRUCTURE  {e}")

    hits = []
    if not args.skip_ngram:
        kb, n_files = kb_tokens(args.kb)
        hits = check_ngrams(data, kb, args.min_ngram)
        print(f"n-gram vs {os.path.relpath(args.kb, ROOT)} ({n_files} files, {len(kb):,} tokens), "
              f"min {args.min_ngram} words: {len(hits)} hit(s)")
        for cid, aid, ln, words in hits:
            print(f"  NGRAM {ln:>2}  {cid}.{aid}: \"{words}\"")

    if args.queries:
        corpora = [("anchors", anchor_tokens(data))]
        if not args.skip_ngram:
            corpora.insert(0, (os.path.relpath(args.kb, ROOT), kb))
        q_errors, q_hits = check_queries(spec, corpora, args.min_ngram)
        print(f"queries vs {' + '.join(n for n, _ in corpora)}, min {args.min_ngram} words: {len(q_hits)} hit(s)")
        for e in q_errors:
            print(f"  TAXONOMY  {e}")
        for rule, name, ln, words in q_hits:
            print(f"  QNGRAM {ln:>2}  {rule} vs {name}: \"{words}\"")
        errors += q_errors
        hits += q_hits

    sys.exit(1 if errors or hits else 0)


if __name__ == "__main__":
    main()
