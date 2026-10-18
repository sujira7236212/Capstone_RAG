"""Slide figures for the RAG vs no-RAG baseline (prompt v14, KB v6, 2026-10-03).

Everything is recomputed from the reports that already exist - no LLM call:

    compare_output/compare_result_v14_<exercise>.json   number sources, leaked keys
    compare_output/compare_result_v14_<exercise>.md     jargon + copying (eval_generation.py)
    compare_output/compare_result_v9.md / _v10.md       copying history

and writes three 16:9 PNGs (3840x2160) to docs/figures/rag_vs_norag/:

    1_number_sources.png   every number+unit in the answers, by where it can be traced to
    2_side_effects.png     unglossed jargon, leaked error_type keys, numbers with no source
    3_copying_history.png  longest word run copied from the context, v9 -> v10 -> v14

"Number + unit" = a value followed by seconds/sets/reps/degrees/%/cm/... ("90 to 100 degrees",
"two-second pause", "55%"). It is traced to:
    KB      - the same value with the same kind of unit appears in that session's context
    data    - "N reps" with N in the session JSON, or a % equal to one of its scores (includes
              advice such as "stop two reps early" - it is a rep count, not a KB fact)
    none    - neither; under the grounding rule both sides should state no such number
              (no-RAG gets the same system prompt with "No external context provided.")

Same Plotly + Kaleido setup as plot_query_expansion.py (matplotlib cannot shape Thai).

    python eval/plot_rag_vs_norag.py            # figures + a markdown table on stdout
"""
import json
import os
import re
import sys

import plotly.graph_objects as go

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import eval_generation as eg  # noqa: E402
from error_taxonomy import all_faults  # noqa: E402
from plot_query_expansion import (EDGE, EXP, FONT, INK, INK_2, INK_3, LINE, LINE_STRONG, MONO,  # noqa: E402
                                  PAD, RAW, Canvas, H, W)

EXERCISES = ("squat", "push-up", "lunge", "bicep-curl")
OUT_DIR = os.path.join(ROOT, "docs", "figures", "rag_vs_norag")
FOOTNOTE = ("baseline 3 ต.ค. 2026 · prompt v14 + KB v6 · gemini-3.5-flash-lite @ 0.7 · "
            "20 session (mock) × 3 คำตอบ × 2 ฝั่ง = 120 คำตอบ · นับจากไฟล์ผล ไม่มี judge")
NONE_C = "#d98c3f"  # numbers with no source

NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
             "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15, "twenty": 20,
             "thirty": 30, "forty": 40, "forty-five": 45, "sixty": 60, "ninety": 90}
UNIT = (r"(?:seconds?|secs?|minutes?|mins?|sets?|reps?|repetitions?|inch(?:es)?|cm|"
        r"centimet(?:er|re)s?|degrees?|°|%|percent|times|weeks?|days?|kg|lbs?|pounds?|"
        r"breaths?|counts?|steps?|fingers?|fist)")
NUM = r"(\d+(?:\.\d+)?|" + "|".join(sorted(NUM_WORDS, key=len, reverse=True)) + r")"
SPEC = re.compile(r"\b" + NUM + r"(?:\s*(?:-|to|–)\s*" + NUM + r")?[\s-]*" + UNIT, re.I)
UNIT_FAMILY = (("time", r"second|sec|minute|min"), ("angle", r"degree|°"), ("pct", r"%|percent"),
               ("length", r"inch|cm|centimet|finger|fist"), ("load", r"kg|lb|pound"))


def _value(token):
    token = token.lower()
    return float(NUM_WORDS[token]) if token in NUM_WORDS else float(token)


def _family(unit_text):
    for name, pat in UNIT_FAMILY:
        if re.search(pat, unit_text):
            return name
    return "count"


def _specifics(text):
    """[(match text, [values], unit family)] for every number+unit in text."""
    out = []
    for m in SPEC.finditer(text):
        vals = [_value(m.group(1))] + ([_value(m.group(2))] if m.group(2) else [])
        out.append((m.group(0), vals, _family(m.group(0).lower())))
    return out


def _payload_numbers(payload):
    """(rep-count numbers, score numbers) of the session JSON."""
    scores = re.findall(r'"(?:overall_score|previous_overall_score|overall)": (\d+)', json.dumps(payload))
    return ({float(x) for x in re.findall(r"\d+(?:\.\d+)?", json.dumps(payload))},
            {float(x) for x in scores})


def load_sessions():
    sessions = []
    for ex in EXERCISES:
        with open(os.path.join(ROOT, "compare_output", f"compare_result_v14_{ex}.json"), encoding="utf-8") as f:
            for s in json.load(f)["sessions"]:
                sessions.append(dict(s, exercise=ex))
    return sessions


def number_sources(sessions):
    """{side: {"kb": n, "data": n, "none": n, "examples": {...}}} over every answer."""
    out = {side: {"kb": 0, "data": 0, "none": 0, "hits": []} for side in ("rag", "no_rag")}
    for s in sessions:
        payload_nums, scores = _payload_numbers(s["payload"])
        # header lines carry source titles, which are full of years and figure numbers
        ctx = "\n".join(l for l in (s["context"] or "").splitlines() if not l.startswith("["))
        ctx_pairs = {(v, fam) for _, vals, fam in _specifics(ctx) for v in vals}
        for side in ("rag", "no_rag"):
            for answer in s[side]:
                for text, vals, fam in _specifics(answer):
                    rep_count = re.search(r"reps?\b|repetitions", text, re.I)
                    if (rep_count and all(v in payload_nums for v in vals)) or \
                            (fam == "pct" and all(v in scores for v in vals)):
                        cls = "data"
                    elif all((v, fam) in ctx_pairs for v in vals):
                        cls = "kb"
                    else:
                        cls = "none"
                    out[side][cls] += 1
                    out[side]["hits"].append((cls, s["label"], text))
    return out


def leaked_keys(sessions):
    keys = sorted({code for _, code, _ in all_faults()})
    pat = re.compile("|".join(re.escape(k) for k in keys))
    return {side: sum(1 for s in sessions for a in s[side] if pat.search(a)) for side in ("rag", "no_rag")}


def generation_scores():
    """eval_generation.py on the v14 reports (per-exercise mock) and on v9/v10."""
    spec, markers = eg.load_terms(os.path.join(ROOT, eg.DEFAULT_TERMS))
    window, min_span = 120, 6
    v14 = []
    for ex in EXERCISES:
        names = eg.session_error_names(os.path.join(ROOT, "mock_data", f"mock_sessions_{ex}.json"))
        v14 += eg.score_report(os.path.join(ROOT, "compare_output", f"compare_result_v14_{ex}.md"),
                               spec, markers, window, min_span, names)
    legacy = eg.session_error_names(os.path.join(ROOT, "mock_data", "mock_sessions.json"))
    history = {}
    for ver in ("v9", "v10"):
        history[ver] = eg.score_report(os.path.join(ROOT, "compare_output", f"compare_result_{ver}.md"),
                                       spec, markers, window, min_span, legacy)
    history["v14"] = v14

    def side(rows, s):
        rows = [r for r in rows if r["base_side"] == s]
        return {"answers": len(rows), "jargon": sum(len(r["hits"]) for r in rows),
                "longest": max(r["longest"][0] for r in rows),
                "spans": sum(len(r["spans"]) for r in rows)}
    return {ver: {s: side(rows, s) for s in eg.SIDES} for ver, rows in history.items()}


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------

def _base_fig(margin):
    fig = go.Figure()
    fig.update_layout(width=W, height=H, margin=margin, paper_bgcolor="white", plot_bgcolor="white",
                      showlegend=False, font=dict(family=FONT, color=INK))
    return fig


def _frame(c, title, highlight, subtitle, legend_items=()):
    c.text(PAD, 112, f"<b>{title} <span style='color:{EXP}'>{highlight}</span></b>", 48)
    c.text(PAD, 176, subtitle, 25, INK_2)
    if legend_items:
        legend = "&nbsp;&nbsp;&nbsp;&nbsp;".join(f"{sw}&nbsp;&nbsp;{lab}" for sw, lab in legend_items)
        c.text(W - PAD, 176, legend, 23, INK_2, anchor="right")
    c.hline(H - 64, LINE, 1.5)
    c.text(PAD, H - 26, FOOTNOTE, 18, INK_3)


def _sq(color):
    return f"<span style='color:{color};font-size:34px'>■</span>"


def fig_number_sources(src, path):
    margin = dict(l=330, r=96, t=280, b=250)
    fig = _base_fig(margin)
    c = Canvas(fig, margin)
    segs = (("kb", "มีที่มาจาก KB", EXP), ("data", "จำนวน rep · คะแนน", LINE_STRONG), ("none", "ไม่มีที่มา", NONE_C))
    rows = (("rag", "RAG", "เปิด KB ก่อนตอบ", 1.0), ("no_rag", "no-RAG", "ตอบจากความจำ", 0.0))
    x_max = max(sum(src[s][k] for k, _, _ in segs) for s, *_ in rows) * 1.08
    for side, name, meta, y in rows:
        left = 0
        for key, label, color in segs:
            n = src[side][key]
            fig.add_trace(go.Bar(x=[n], y=[y], base=[left], orientation="h", width=0.56,
                                 marker=dict(color=color, line=dict(color="white", width=3)),
                                 hovertemplate=f"{name} · {label}: {n}<extra></extra>"))
            if n >= 4:
                fig.add_annotation(x=left + n / 2, y=y, xref="x", yref="y", showarrow=False,
                                   text=f"<b>{n}</b>", font=dict(size=40, family=MONO,
                                                                 color="white" if key != "data" else INK))
            left += n
        yc = margin["t"] + (1.55 - y) / 2.1 * c.ph
        c.text(PAD, yc + 2, f"<b>{name}</b>", 36)
        c.text(PAD, yc + 8, meta, 22, INK_3, yanchor="top")
    fig.update_layout(barmode="overlay", bargap=0)
    fig.update_xaxes(range=[0, x_max], visible=False)
    fig.update_yaxes(range=[-0.55, 1.55], visible=False)
    c.text(PAD, H - 196, "<b>ตัวอย่างตัวเลขจาก KB ที่ RAG ใช้:</b> เข่าหน้างอ 90–100° (lunge) · "
                         "ศีรษะ แขน ลำตัว ≈ 55% ของน้ำหนักตัว · งอศอก 90° (push-up) · ไหล่เลื่อน ≈ 20° เมื่อล้า (curl)",
           22, INK_2)
    c.text(PAD, H - 150, "<b>ตัวเลขไม่มีที่มา</b> ส่วนใหญ่เป็นจังหวะ/น้ำหนัก เช่น \"ค้าง 2 วินาที\" \"ลดน้ำหนัก 10%\" — "
                         "ทั้งสองฝั่งพอ ๆ กัน เพราะ KB แทบไม่มีปริมาณการฝึก (4 item ทั้ง KB)",
           22, INK_2)
    _frame(c, "ตัวเลขที่ตรวจที่มาได้จาก KB:", f"RAG {src['rag']['kb']} ครั้ง · no-RAG {src['no_rag']['kb']} ครั้ง",
           "ตัวเลข+หน่วย (องศา, %, วินาที, เซ็ต …) ในคำตอบทั้งหมด 60 คำตอบต่อฝั่ง แยกตามที่มา",
           [(_sq(c_), lab) for _, lab, c_ in segs])
    fig.write_image(path, scale=2)


def fig_side_effects(gen, keys, src, path):
    rag, norag = gen["v14"]["WITH RAG"], gen["v14"]["WITHOUT RAG"]
    panels = (
        ("ศัพท์เทคนิคที่ไม่ได้แปล", "เช่น \"lumbar erector spinae\"", rag["jargon"], norag["jargon"]),
        ("ชื่อ key หลุดถึงผู้ใช้", "เช่น \"partial_curl\"", keys["rag"], keys["no_rag"]),
        ("ตัวเลขที่ไม่มีที่มา", "ผิดกติกา grounding", src["rag"]["none"], src["no_rag"]["none"]),
    )
    margin = dict(l=PAD, r=PAD, t=330, b=190)
    fig = _base_fig(margin)
    c = Canvas(fig, margin)
    gap = 0.06
    width = (1 - gap * 2) / 3
    for i, (name, meta, r, n) in enumerate(panels):
        x0 = i * (width + gap)
        ax = "" if i == 0 else str(i + 1)
        top = max(r, n) * 1.25
        for xi, val, color, lab in ((0, r, EXP, "RAG"), (1, n, RAW, "no-RAG")):
            fig.add_trace(go.Bar(x=[xi], y=[val], width=0.62, marker=dict(color=color, line_width=0),
                                 xaxis=f"x{ax}", yaxis=f"y{ax}", hovertemplate=f"{lab}: {val}<extra></extra>"))
            fig.add_annotation(x=xi, y=val, xref=f"x{ax}", yref=f"y{ax}", yanchor="bottom", showarrow=False, yshift=6,
                               text=f"<b>{val}</b>", font=dict(size=44, family=MONO, color=INK))
        fig.update_layout(**{f"xaxis{ax}": dict(domain=[x0, x0 + width], range=[-0.6, 1.6], tickvals=[0, 1],
                                                ticktext=["RAG", "no-RAG"], tickfont=dict(size=24, color=INK_2),
                                                showline=True, linecolor=LINE_STRONG, linewidth=2, ticks="",
                                                anchor=f"y{ax}"),
                             f"yaxis{ax}": dict(range=[0, top], visible=False, anchor=f"x{ax}")})
        px = margin["l"] + c.pw * x0
        c.text(px, 262, f"<b>{name}</b>", 30)
        c.text(px, 268, meta, 21, INK_3, yanchor="top")
    _frame(c, "ข้อเสียของ RAG:", "ศัพท์ไม่แปลมากกว่าเล็กน้อย ที่เหลือพอ ๆ กัน",
           "นับใน 60 คำตอบต่อฝั่ง · ยิ่งน้อยยิ่งดี · ศัพท์ไม่แปลมาจากศัพท์ใน KB (lunge 6 จาก 9)")
    fig.write_image(path, scale=2)


def fig_copying(gen, path):
    vers = (("v9", "v9", "ก่อนแก้ prompt"), ("v10", "v10", "เพิ่มกติกาห้ามลอก"), ("v14", "v14", "KB v6 (ปัจจุบัน)"))
    margin = dict(l=PAD + 40, r=PAD + 40, t=260, b=200)
    fig = _base_fig(margin)
    c = Canvas(fig, margin)
    floor = 6
    for i, (key, name, meta) in enumerate(vers):
        r = gen[key]["WITH RAG"]
        val = r["longest"]
        fig.add_trace(go.Bar(x=[i], y=[val], width=0.5, marker=dict(color=EXP if key != "v9" else RAW, line_width=0),
                             hovertemplate=f"{name}: {val} คำ<extra></extra>"))
        fig.add_annotation(x=i, y=val, xref="x", yref="y", yanchor="bottom", showarrow=False, yshift=6,
                           text=f"<b>{val}</b> <span style='font-size:26px;color:{INK_2}'>คำ</span>",
                           font=dict(size=48, family=MONO, color=INK))
        fig.add_annotation(x=i, y=0, xref="x", yref="y", yanchor="top", showarrow=False, yshift=-14,
                           text=f"<b>{name}</b> · {meta}<br><span style='color:{INK_3};font-size:20px'>"
                                f"{r['answers']} คำตอบ · ช่วงลอก ≥ 6 คำ {r['spans']} จุด</span>",
                           font=dict(size=26, color=INK))
    fig.add_shape(type="line", xref="paper", yref="y", x0=0, x1=1, y0=floor, y1=floor,
                  line=dict(color=LINE_STRONG, width=3, dash="dash"))
    fig.add_annotation(xref="paper", yref="y", x=0, y=floor, xanchor="left", yanchor="bottom", showarrow=False,
                       text="6 คำ", font=dict(size=22, color=INK_2))
    fig.update_xaxes(range=[-0.6, 2.6], visible=False)
    fig.update_yaxes(range=[0, 24], visible=False)
    _frame(c, "RAG เลิกลอกประโยคงานวิจัยให้ผู้ใช้อ่าน:", f"{gen['v9']['WITH RAG']['longest']} → "
           f"{gen['v14']['WITH RAG']['longest']} คำ",
           "คำที่ติดกันยาวที่สุดที่คำตอบ RAG ซ้ำกับ context · v14 วัดจาก 60 คำตอบ จึงมีโอกาสเจอค่าสูงสุดมากกว่า",
           [(f"<span style='color:{LINE_STRONG};font-size:30px'>- - -</span>",
             "ซ้ำได้โดยบังเอิญ (no-RAG ไม่เห็น context)")])
    fig.write_image(path, scale=2)


def markdown(src, keys, gen):
    rag, norag = gen["v14"]["WITH RAG"], gen["v14"]["WITHOUT RAG"]
    lines = ["| ตัววัด (60 คำตอบต่อฝั่ง) | RAG | no-RAG |", "|---|---|---|",
             f"| ตัวเลขที่มีที่มาจาก KB | {src['rag']['kb']} | {src['no_rag']['kb']} |",
             f"| จำนวน rep · คะแนน | {src['rag']['data']} | {src['no_rag']['data']} |",
             f"| ตัวเลขไม่มีที่มา | {src['rag']['none']} | {src['no_rag']['none']} |",
             f"| ศัพท์เทคนิคไม่แปล | {rag['jargon']} | {norag['jargon']} |",
             f"| key หลุด (คำตอบ) | {keys['rag']} | {keys['no_rag']} |",
             f"| คำลอก context ติดกันยาวสุด | {rag['longest']} | {norag['longest'] or '< 6'} |",
             "", "| รุ่น | คำตอบ RAG | ลอกยาวสุด | ช่วง ≥ 6 คำ | no-RAG ลอกยาวสุด |", "|---|---|---|---|---|"]
    for ver in ("v9", "v10", "v14"):
        r, n = gen[ver]["WITH RAG"], gen[ver]["WITHOUT RAG"]
        lines.append(f"| {ver} | {r['answers']} | {r['longest']} | {r['spans']} | {n['longest'] or '< 6'} |")
    return "\n".join(lines)


def main():
    if os.name == "nt" and not os.environ.get("BROWSER_PATH") and os.path.exists(EDGE):
        os.environ["BROWSER_PATH"] = EDGE
    sessions = load_sessions()
    if len(sessions) != 20:
        raise SystemExit(f"expected 20 v14 sessions, found {len(sessions)}")
    src, keys, gen = number_sources(sessions), leaked_keys(sessions), generation_scores()
    os.makedirs(OUT_DIR, exist_ok=True)
    fig_number_sources(src, os.path.join(OUT_DIR, "1_number_sources.png"))
    fig_side_effects(gen, keys, src, os.path.join(OUT_DIR, "2_side_effects.png"))
    fig_copying(gen, os.path.join(OUT_DIR, "3_copying_history.png"))
    print(markdown(src, keys, gen))
    print(f"\nwrote 3 figures to {OUT_DIR}")


if __name__ == "__main__":
    main()
