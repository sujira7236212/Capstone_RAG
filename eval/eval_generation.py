"""Score the GENERATION side of a compare_output/*.md report.

eval/eval_retrieval.py answers "did the right chunks reach the context". This script
answers the question after that one: given those chunks, did the model turn them into
coaching, or did it hand the research paper to the user. Two numbers, both deterministic,
both re-runnable on a report that already exists - no LLM call, no re-generation:

    unglossed jargon   - clinical/biomechanical terms in the feedback with no everyday
                         meaning given in the same sentence. Measures the Translation rule.
    longest shared     - longest run of words shared between the Retrieved KB Context and
    word n-gram          the feedback for the same exercise. Measures Grounding rule part 2
                         ("the wording is never fixed") - i.e. sentence copying.

They exist because an external judge rated the v9 no-RAG side the better coaching, and
"it sounds clinical" was not something two people could argue about with numbers. Splitting
the symptom in two settled it: v9 was not choosing hard words, it was copying Context
sentences intact. The fix went into the prompt (v10), and these numbers are how the fix was
confirmed - see docs/kb_quality_assessment.md and the SYSTEM_PROMPT v10 comment.

The WITHOUT RAG side is scored too, on purpose. It never saw the Context, so its shared
n-gram is the chance floor for this report - the length two independent texts about squats
hit by coincidence. A RAG n-gram near that floor means no copying; one far above it is
copying, whatever the absolute number looks like.

Usage:
    python eval/eval_generation.py compare_output/compare_result_v10.md
    python eval/eval_generation.py compare_output/compare_result_v9.md --show-hits
    python eval/eval_generation.py compare_output/compare_result_v{9,10}.md --out eval_gen.md
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DEFAULT_TERMS = os.path.join("eval", "jargon_terms.json")

# Section boundaries. Only these four headings and the `## Exercise:` line end a section:
# the feedback itself contains `### Progress Tracking`, `### Error Breakdown`,
# `### Next Session Plan` AND horizontal rules (`---`, `***`), so a parser that splits on
# every `### ` or on `---` truncates the answer at its first internal heading and reports
# roughly half the real jargon count. That is not hypothetical - it is how the first
# hand-run of this metric under-counted v9 as 10 instead of 18.
EXERCISE_RE = re.compile(r"^## Exercise:\s*(.+?)\s*$", re.M)
SECTION_RE = re.compile(
    r"^### (Retrieval metrics|Retrieved KB Context|WITH RAG|WITHOUT RAG)\b.*$", re.M)

SIDES = ("WITH RAG", "WITHOUT RAG")


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------

def parse_report(text):
    """-> [{"exercise", "Retrieval metrics", "Retrieved KB Context", "WITH RAG", ...}]"""
    exercises = []
    starts = [(m.start(), m.group(1)) for m in EXERCISE_RE.finditer(text)]
    for n, (pos, name) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(text)
        body = text[pos:end]
        block = {"exercise": name}
        heads = [(m.start(), m.end(), m.group(1)) for m in SECTION_RE.finditer(body)]
        for i, (_, hend, kind) in enumerate(heads):
            stop = heads[i + 1][0] if i + 1 < len(heads) else len(body)
            block[kind] = body[hend:stop].strip()
        exercises.append(block)
    return exercises


def _strip_fences(text):
    """The context is written inside a ```text fence; the feedback is not."""
    return re.sub(r"^```\w*$", "", text or "", flags=re.M)


def error_names(metrics_section):
    """Error names from the Retrieval metrics table's first column.

    These come from the session JSON and the prompt orders the model to reproduce them
    exactly ("use the name that rep actually carries in this session's data"), so a term
    inside one - "Knee valgus" - must never be counted as unflagged jargon. Reading them
    from the report keeps the metric self-contained: no second file to keep in sync.
    """
    names = []
    for line in (metrics_section or "").splitlines():
        if not line.startswith("|"):
            continue
        cell = line.split("|")[1].strip()
        if not cell or cell.startswith("---") or cell == "error_type":
            continue
        names.append(cell)
    return names


# ---------------------------------------------------------------------------
# metric 1: unglossed jargon
# ---------------------------------------------------------------------------

def _term_pattern(term):
    """Match the term with any spacing/hyphenation and a plural/adjectival tail:
    'plantar flexor' also matches 'plantar-flexors', 'femoral' matches 'femorally'."""
    body = r"[\s\-]+".join(re.escape(w) for w in term.split())
    return re.compile(rf"\b{body}(?:s|es|ly)?\b", re.I)


def _sentences(text):
    """Split on line breaks first, then on sentence enders. Markdown bullets are their own
    unit already, and the rule being measured is 'in the same sentence'."""
    out = []
    for line in re.split(r"\n+", text or ""):
        line = re.sub(r"^\s*[*\-\d.()a-z]{1,6}\s+", "", line).strip()
        if not line:
            continue
        out.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip())
    return out


def _is_glossed(sentence, start, end, markers, window):
    """Glossed when an explanation marker follows the term within `window` characters of
    the same sentence, or when the term itself is the parenthetical after plain words -
    'your lower back rounds (lumbar flexion)' needs no further translation."""
    after = sentence[end:end + window]
    if any(m.search(after) for m in markers):
        return True
    before, behind = sentence[:start], sentence[end:]
    return before.rfind("(") > before.rfind(")") and ")" in behind


def unglossed_jargon(text, vocab, markers, window):
    """-> [(term, sentence)] one entry per unglossed occurrence.

    `vocab` is one list of (term, pattern, flag) sorted longest phrase first, allowed and
    flagged terms together, and a matched character range is consumed by whichever entry
    claims it first. Both parts matter. Longest-first means 'posterior pelvic tilt' is one
    hit rather than three overlapping ones. One combined list means the allowed word 'hip'
    cannot swallow the first three letters of 'hip extensors' and hide the jargon behind an
    allowance - which is exactly what a two-pass version did, silently dropping every
    '<allowed joint> <latin muscle>' phrase in the report.
    """
    hits = []
    for sentence in _sentences(_strip_fences(text)):
        taken = []
        for term, pat, flag in vocab:
            for m in pat.finditer(sentence):
                if any(m.start() < e and s < m.end() for s, e in taken):
                    continue
                taken.append((m.start(), m.end()))
                if flag and not _is_glossed(sentence, m.start(), m.end(), markers, window):
                    hits.append((term, sentence))
    return hits


# ---------------------------------------------------------------------------
# metric 2: longest shared word n-gram
# ---------------------------------------------------------------------------

def word_tokens(text):
    """Lowercase words only. Markdown, punctuation and casing are not what is being
    measured - a copied sentence re-bulleted is still a copied sentence."""
    return re.findall(r"[a-z0-9]+", _strip_fences(text).lower())


def shared_spans(answer, context, min_len):
    """All maximal word runs shared by the two token lists, longest first, de-overlapped
    on the answer side. -> [(length, "the shared words")]

    Classic longest-common-substring DP, but iterated over the positions where each word
    actually occurs in the context instead of the full n x m grid: the context runs ~1.5k
    tokens against a ~700-token answer, and only the matches matter.
    """
    where = defaultdict(list)
    for j, w in enumerate(context):
        where[w].append(j)

    runs = []           # (length, answer_end_index)
    prev = {}
    for i, w in enumerate(answer):
        cur = {}
        for j in where.get(w, ()):
            cur[j] = prev.get(j - 1, 0) + 1
        # A run is maximal when it is not carried forward by the next answer word.
        for j, ln in prev.items():
            if ln >= min_len and cur.get(j + 1, 0) <= ln:
                runs.append((ln, i - 1))
        prev = cur
    for j, ln in prev.items():
        if ln >= min_len:
            runs.append((ln, len(answer) - 1))

    out, used = [], []
    for ln, end in sorted(set(runs), reverse=True):
        start = end - ln + 1
        if any(start <= u_end and u_start <= end for u_start, u_end in used):
            continue
        used.append((start, end))
        out.append((ln, " ".join(answer[start:end + 1])))
    return out


# ---------------------------------------------------------------------------
# scoring + rendering
# ---------------------------------------------------------------------------

def build_vocab(spec, extra_allowed=()):
    """One longest-phrase-first list of (term, pattern, flag_it) - see unglossed_jargon."""
    allowed = list(spec["allowed_bare"]) + list(extra_allowed)
    entries = [(t, False) for t in allowed] + [(t, True) for t in spec["needs_gloss"]]
    entries.sort(key=lambda e: len(e[0]), reverse=True)
    return [(t, _term_pattern(t), flag) for t, flag in entries]


def load_terms(path):
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    markers = [re.compile(m, re.I) for m in spec["gloss_markers"]]
    return spec, markers


def session_error_names(mock_path):
    """{report block name -> [error_type, ...]} for both sessions in the comparison.

    The key must be whatever test_rag_compare.py put in the `## Exercise:` heading, which
    is `report_label` when the session file carries one - mock_sessions_per_fault.json runs
    one session per fault, so three of them are called Squat and keying on the exercise name
    would collapse them onto whichever came last.

    The previous session's errors count too: the prompt tells the model to credit a fault
    the user has cleared, so "you wiped out knee valgus" is the instructed wording even
    though 'Knee valgus' appears nowhere in this session's retrieval table. Scoring it as
    the model reaching for a latin word would punish obedience.
    """
    if not mock_path or not os.path.exists(mock_path):
        return {}
    with open(mock_path, encoding="utf-8") as f:
        mocks = json.load(f)
    out = {}
    for mock in mocks:
        names = {e["error_type"] for r in mock.get("reps_detail", []) for e in r.get("errors", [])}
        names.update(mock.get("historical_comparison", {}).get("previous_common_errors", []))
        key = mock.get("report_label") or mock.get("name") or mock.get("exercise_id")
        out[key] = sorted(names)
    return out


def score_report(path, spec, markers, window, min_span, by_exercise):
    rows = []
    with open(path, encoding="utf-8") as f:
        blocks = parse_report(f.read())
    for block in blocks:
        context = block.get("Retrieved KB Context", "")
        ctx_tokens = word_tokens(context)
        # Session error names are mandated wording, not the model's vocabulary choice.
        # Prefer the mock file (it also carries the PREVIOUS session's errors); fall back to
        # the report's own metrics table so a report can still be scored on its own.
        names = by_exercise.get(block["exercise"]) or error_names(block.get("Retrieval metrics"))
        vocab = build_vocab(spec, names)
        for side in SIDES:
            answer = block.get(side)
            if answer is None:
                continue
            hits = unglossed_jargon(answer, vocab, markers, window)
            spans = shared_spans(word_tokens(answer), ctx_tokens, min_span) if ctx_tokens else []
            rows.append({
                "report": os.path.basename(path), "exercise": block["exercise"], "side": side,
                "hits": hits, "longest": spans[0] if spans else (0, ""),
                "spans": spans, "words": len(word_tokens(answer)),
            })
    return rows


def render(rows, min_span, show_hits):
    out = ["| report | exercise | side | words | unglossed jargon | longest shared n-gram | "
           f"spans ≥{min_span} | longest match |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        ln, txt = r["longest"]
        txt = (txt[:60] + "…") if len(txt) > 60 else txt
        out.append(f"| {r['report']} | {r['exercise']} | {r['side']} | {r['words']} | "
                   f"{len(r['hits'])} | {ln} | {len(r['spans'])} | {txt or '—'} |")

    out.append("")
    for report in dict.fromkeys(r["report"] for r in rows):
        for side in SIDES:
            srows = [r for r in rows if r["report"] == report and r["side"] == side]
            if not srows:
                continue
            jargon = sum(len(r["hits"]) for r in srows)
            longest = max(r["longest"][0] for r in srows)
            out.append(f"**{report} — {side}**: unglossed jargon **{jargon}** across "
                       f"{len(srows)} exercises · longest shared n-gram **{longest}** words · "
                       f"spans ≥{min_span}: {sum(len(r['spans']) for r in srows)}")

    if show_hits:
        out.append("\n### Evidence\n")
        for r in rows:
            if not r["hits"] and not r["spans"]:
                continue
            out.append(f"**{r['report']} · {r['exercise']} · {r['side']}**")
            for term, sentence in r["hits"]:
                out.append(f"- unglossed `{term}` — {sentence}")
            for ln, txt in r["spans"]:
                out.append(f"- copied {ln} words — \"{txt}\"")
            out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", nargs="+", help="compare_output/*.md report(s) to score")
    ap.add_argument("--terms", default=DEFAULT_TERMS, help=f"vocabulary file (default {DEFAULT_TERMS})")
    ap.add_argument("--mock", default=os.path.join("mock_data", "mock_sessions.json"),
                    help="session file the report was generated from; its error names are "
                         "never counted as jargon (default mock_data/mock_sessions.json)")
    ap.add_argument("--min-span", type=int, default=6,
                    help="shortest shared word run reported as copying (default 6)")
    ap.add_argument("--gloss-window", type=int, default=120,
                    help="characters after a term searched for its explanation (default 120)")
    ap.add_argument("--show-hits", action="store_true",
                    help="list every flagged term with its sentence, and every shared span")
    ap.add_argument("--out", help="also write the markdown to this path")
    args = ap.parse_args()

    os.chdir(ROOT)
    spec, markers = load_terms(args.terms)
    by_exercise = session_error_names(args.mock)
    rows = []
    for path in args.report:
        rows.extend(score_report(path, spec, markers, args.gloss_window, args.min_span, by_exercise))

    text = "\n".join([
        "# Generation-side evaluation",
        "",
        f"terms: `{args.terms}` · sessions: `{args.mock}` · min span: {args.min_span} words · "
        f"gloss window: {args.gloss_window} chars",
        "",
        "`unglossed jargon` = clinical terms with no everyday meaning in the same sentence. "
        "`longest shared n-gram` = longest word run copied from the Retrieved KB Context; the "
        "WITHOUT RAG row never saw that context, so its number is this report's chance floor.",
        "",
        render(rows, args.min_span, args.show_hits),
    ])
    print(text)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\nwritten: {args.out}")


if __name__ == "__main__":
    main()
