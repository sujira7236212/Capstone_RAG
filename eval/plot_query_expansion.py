"""Slide figures for the query-expansion A/B (raw error_type name vs error_taxonomy.py query).

Reads the numbers straight from compare_output/kb_coverage_v4_rules_raw_vs_expanded.md
(kb_coverage.py on kb_local_curated_v4, MiniLM, 2026-09-11) so the figures cannot drift
from the report, and writes three 16:9 PNGs (3840x2160) to docs/figures/query_expansion/:

    py_1_distance_mistake.png  best distance per fault, kind = mistake (dumbbell)
    py_2_distance_finding.png  same, kind = finding
    py_3_no_usable_chunk.png   faults with no chunk <= 0.40, raw vs expanded (bars)

Plotly + Kaleido rather than matplotlib: matplotlib does no complex-script shaping, so a
Thai tone mark after an upper vowel lands on top of the vowel and disappears ("ที่" renders
as "ที"). Kaleido exports through Chromium, which shapes Thai correctly. Kaleido needs a
Chromium browser; on Windows without Chrome it is pointed at Edge (BROWSER_PATH).

    pip install plotly kaleido
    python eval/plot_query_expansion.py
"""
import os
import re

import plotly.graph_objects as go

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "compare_output", "kb_coverage_v4_rules_raw_vs_expanded.md")
OUT_DIR = os.path.join(ROOT, "docs", "figures", "query_expansion")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

THRESHOLD = 0.40  # kb_coverage.py "usable" cut-off at the time
X_MAX = 0.80
FOOTNOTE = ("ทดลอง 11 ก.ย. 2026 บน KB v4 + embedding MiniLM · อาการ 10 ข้อชุดเดิมของระบบ 1 · "
            "คำค้นที่ขยายเขียนโดยผู้พัฒนาซึ่งเห็นเนื้อหา KB")

THAI_NAME = {
    ("squat", "butt wink"): "หลังล่างงอ",
    ("squat", "knee valgus"): "เข่าล้มเข้าใน",
    ("squat", "partial squat"): "ย่อไม่ลึก",
    ("push-up", "hip sag"): "สะโพกตก",
    ("push-up", "partial range of motion"): "ลงไม่สุด",
    ("lunge", "excessive forward trunk lean"): "ลำตัวโน้มหน้า",
    ("lunge", "shallow lunge"): "ลันจ์ไม่ลึก",
    ("lunge", "insufficient back knee flexion"): "เข่าหลังงอไม่พอ",
    ("bicep-curl", "elbow flare"): "ศอกกางออก",
    ("bicep-curl", "partial range of motion"): "ยกไม่สุด",
}

FONT = "Leelawadee UI, Tahoma, sans-serif"
MONO = "Consolas, monospace"
INK, INK_2, INK_3 = "#15181d", "#4f5663", "#7d8491"
LINE, LINE_STRONG, ZONE = "#e4e7ec", "#c3c8d0", "#f0f2f5"
RAW, EXP, WORSE = "#86b6ef", "#1c5cab", "#b3261e"

# Canvas in CSS px; exported at scale 2. Plot area = canvas minus these margins.
W, H = 1920, 1080
PAD = 96  # outer gutter for titles, labels and footnote


def load_rows():
    """[(exercise, fault, {"raw_m": (count, dist), "raw_f": ..., "exp_m": ..., "exp_f": ...})]"""
    cell = r"\s*(\d+) \((\d\.\d+)\)[^|]*"
    pat = re.compile(r"^\|\s*([a-z-]+)\s*\|\s*([a-z ]+?)\s*\|" + r"\|".join([cell] * 4) + r"\|\s*$")
    rows = []
    with open(REPORT, encoding="utf-8") as f:
        for line in f:
            m = pat.match(line.strip())
            if not m:
                continue
            g = m.groups()
            vals = [(int(g[i]), float(g[i + 1])) for i in range(2, 10, 2)]
            rows.append((g[0], g[1], dict(zip(("raw_m", "raw_f", "exp_m", "exp_f"), vals))))
    if len(rows) != 10:
        raise SystemExit(f"expected 10 fault rows in {REPORT}, parsed {len(rows)}")
    return rows


class Canvas:
    """Place annotations and shapes in canvas px (from the top-left) on a plotly figure."""

    def __init__(self, fig, margin):
        self.fig, self.m = fig, margin
        self.pw = W - margin["l"] - margin["r"]
        self.ph = H - margin["t"] - margin["b"]

    def x(self, px):
        return (px - self.m["l"]) / self.pw

    def y(self, px):
        return 1 - (px - self.m["t"]) / self.ph

    def text(self, px, py, text, size, color=INK, anchor="left", yanchor="bottom", family=FONT, **kw):
        self.fig.add_annotation(xref="paper", yref="paper", x=self.x(px), y=self.y(py), text=text,
                                showarrow=False, xanchor=anchor, yanchor=yanchor,
                                font=dict(size=size, color=color, family=family), **kw)

    def hline(self, py, color=LINE, width=1.5, x0=PAD, x1=W - PAD):
        self.fig.add_shape(type="line", xref="paper", yref="paper", x0=self.x(x0), x1=self.x(x1),
                           y0=self.y(py), y1=self.y(py), line=dict(color=color, width=width))


def _frame(c, title, highlight, subtitle, legend_items):
    c.text(PAD, 112, f"<b>{title} <span style='color:{EXP}'>{highlight}</span></b>", 48)
    c.text(PAD, 176, subtitle, 25, INK_2)
    # legend, right-aligned on the subtitle line; items are (swatch html, label)
    legend = "&nbsp;&nbsp;&nbsp;&nbsp;".join(f"{sw}&nbsp;&nbsp;{lab}" for sw, lab in legend_items)
    c.text(W - PAD, 176, legend, 23, INK_2, anchor="right")
    c.hline(H - 64, LINE, 1.5)
    c.text(PAD, H - 26, FOOTNOTE, 18, INK_3)


def _base_fig(margin):
    fig = go.Figure()
    fig.update_layout(width=W, height=H, margin=margin, paper_bgcolor="white", plot_bgcolor="white",
                      showlegend=False, font=dict(family=FONT, color=INK))
    return fig


def dumbbell(rows, kind, path):
    raw_key, exp_key = f"raw_{kind}", f"exp_{kind}"
    closer = sum(1 for _, _, v in rows if v[exp_key][1] < v[raw_key][1])
    kind_th = "ลักษณะท่าผิด (mistake)" if kind == "m" else "ผลวิจัย (finding)"
    margin = dict(l=560, r=210, t=220, b=150)
    fig = _base_fig(margin)
    c = Canvas(fig, margin)
    n = len(rows)
    ys = list(range(n))[::-1]  # first fault at the top

    fig.add_shape(type="rect", xref="x", yref="paper", x0=THRESHOLD, x1=X_MAX, y0=0, y1=1,
                  fillcolor=ZONE, line_width=0, layer="below")
    fig.add_shape(type="line", xref="x", yref="paper", x0=THRESHOLD, x1=THRESHOLD, y0=0, y1=1,
                  line=dict(color=LINE_STRONG, width=2.5, dash="dash"), layer="below")

    row_h = c.ph / n
    prev_ex = None
    for y, (ex, fault, v) in zip(ys, rows):
        raw, exp = v[raw_key][1], v[exp_key][1]
        name = fault[0].upper() + fault[1:]
        hover = (f"<b>{name}</b> · {ex}<br>ชื่อดิบ %{{customdata[0]:.3f}} (ผ่านเกณฑ์ {v[raw_key][0]} ชิ้น)"
                 f"<br>คำค้นที่ขยาย %{{customdata[1]:.3f}} (ผ่านเกณฑ์ {v[exp_key][0]} ชิ้น)<extra></extra>")
        fig.add_trace(go.Scatter(x=[raw, exp], y=[y, y], mode="lines", hoverinfo="skip",
                                 line=dict(color=LINE_STRONG, width=5)))
        fig.add_trace(go.Scatter(x=[raw], y=[y], mode="markers", customdata=[[raw, exp]], hovertemplate=hover,
                                 marker=dict(size=26, color="white", line=dict(color=RAW, width=4.5))))
        fig.add_trace(go.Scatter(x=[exp], y=[y], mode="markers", customdata=[[raw, exp]], hovertemplate=hover,
                                 marker=dict(size=26, color=EXP, line=dict(color="white", width=3))))

        top = margin["t"] + (n - 1 - y) * row_h  # canvas px of this row's top edge
        if prev_ex is not None:
            c.hline(top, LINE_STRONG if ex != prev_ex else LINE, 2 if ex != prev_ex else 1.5)
        prev_ex = ex
        mid = top + row_h / 2
        c.text(PAD, mid + 2, f"<b>{name}</b>", 27)
        c.text(PAD, mid + 4, f"{ex} · {THAI_NAME[(ex, fault)]}", 20, INK_3, yanchor="top")
        diff = exp - raw
        worse = diff > 0
        c.text(W - PAD, mid + 2, f"{'+' if worse else '−'}{abs(diff):.3f}", 27, WORSE if worse else INK,
               anchor="right", family=MONO)
        c.text(W - PAD, mid + 4, "ไกลขึ้น" if worse else "ใกล้ขึ้น", 19, WORSE if worse else INK_3,
               anchor="right", yanchor="top")

    fig.update_xaxes(range=[0, X_MAX], tickvals=[i / 10 for i in range(9)], ticktext=[f"{i / 10:.1f}" for i in range(9)],
                     tickfont=dict(size=20, color=INK_3, family=MONO), showgrid=False, zeroline=False,
                     showline=True, linecolor=LINE_STRONG, linewidth=2, ticks="", ticklabelstandoff=10)
    fig.update_yaxes(range=[-0.5, n - 0.5], visible=False)
    c.text(margin["l"] + c.pw * THRESHOLD / X_MAX, H - margin["b"] + 44, "เกณฑ์ใช้ได้ ≤ 0.40", 19, INK_2,
           anchor="center", yanchor="top")

    ring = f"<span style='color:{RAW};font-size:34px'>○</span>"
    dot = f"<span style='color:{EXP};font-size:34px'>●</span>"
    box = f"<span style='color:{LINE_STRONG};font-size:34px'>▭</span>"
    _frame(c, f"คำค้นที่ขยายได้ข้อมูล{kind_th} ที่ใกล้กว่า", f"ใน {closer} จาก 10 อาการ",
           "ระยะ (cosine distance) ของ chunk ที่ใกล้ที่สุด ยิ่งน้อยยิ่งตรง",
           [(ring, "ชื่ออาการดิบ"), (dot, "คำค้นที่ขยาย"), (box, "แถบเทา = เกิน 0.40 ใช้ไม่ได้")])
    fig.write_image(path, scale=2)


def no_usable_bars(rows, path):
    def zeros(key):
        return [f for _, f, v in rows if v[key][1] > THRESHOLD]

    # (label, sub-label, raw misses, expanded misses, per-fault note shown next to the bar)
    groups = [
        ("ผลวิจัย (finding)", "ตัวเลข ผลการศึกษา", zeros("raw_f"), zeros("exp_f"),
         {"elbow flare": "Elbow flare: KB ไม่มีผลวิจัยอาการนี้"}),
        ("ลักษณะท่าผิด (mistake)", "ท่าผิดดูเป็นอย่างไร", zeros("raw_m"), zeros("exp_m"), {}),
    ]
    margin = dict(l=560, r=96, t=260, b=170)
    fig = _base_fig(margin)
    c = Canvas(fig, margin)

    bar_w, gap = 0.36, 0.08
    for (name, meta, raw, exp, note), center in zip(groups, (1.0, 0.0)):
        y_raw, y_exp = center + (bar_w + gap) / 2, center - (bar_w + gap) / 2
        for y, vals, color, who in ((y_raw, raw, RAW, "ชื่อดิบ"), (y_exp, exp, EXP, "คำค้นที่ขยาย")):
            listed = ", ".join(f[0].upper() + f[1:] for f in vals) if vals else "—"
            fig.add_trace(go.Bar(x=[max(len(vals), 0.04)], y=[y], orientation="h", width=bar_w,
                                 marker=dict(color=color, line_width=0),
                                 hovertemplate=f"{who}: {len(vals)} อาการ<br>{listed}<extra></extra>"))
            extra = "; ".join(note.get(f, f[0].upper() + f[1:]) for f in vals) if 0 < len(vals) <= 2 else ""
            fig.add_annotation(x=len(vals), y=y, xref="x", yref="y", xanchor="left", showarrow=False, xshift=18,
                               text=f"<span style='font-family:{MONO};font-size:44px;color:{INK}'>{len(vals)}</span>"
                                    f"&nbsp;&nbsp;&nbsp;<span style='font-size:23px;color:{INK_2}'>{who}"
                                    f"{' · ' + extra if extra else ''}</span>")
        # group label in the left margin, vertically centred on the pair
        yc = margin["t"] + (1.6 - center) / 2.2 * c.ph
        c.text(PAD, yc + 2, f"<b>{name}</b>", 32)
        c.text(PAD, yc + 6, meta, 22, INK_3, yanchor="top")

    fig.update_layout(bargap=0)
    fig.update_xaxes(range=[0, 10], tickvals=list(range(0, 11, 2)), tickfont=dict(size=20, color=INK_3, family=MONO),
                     showgrid=True, gridcolor=LINE, gridwidth=1.5, zeroline=False, showline=True,
                     linecolor=LINE_STRONG, linewidth=2, ticks="", ticklabelstandoff=10)
    fig.update_yaxes(range=[-0.6, 1.6], visible=False)

    sq = lambda col: f"<span style='color:{col};font-size:34px'>■</span>"
    _frame(c, "ค้นด้วยชื่อดิบ ไม่เจอผลวิจัยที่ใช้ได้เลยใน", f"{len(groups[0][2])} จาก 10 อาการ",
           "จำนวนอาการ (จาก 10) ที่ไม่มี chunk ไหนผ่านเกณฑ์ระยะ ≤ 0.40 เลย · ยิ่งน้อยยิ่งดี",
           [(sq(RAW), "ชื่ออาการดิบ"), (sq(EXP), "คำค้นที่ขยาย")])
    fig.write_image(path, scale=2)


def main():
    if os.name == "nt" and not os.environ.get("BROWSER_PATH") and os.path.exists(EDGE):
        os.environ["BROWSER_PATH"] = EDGE
    rows = load_rows()
    os.makedirs(OUT_DIR, exist_ok=True)
    dumbbell(rows, "m", os.path.join(OUT_DIR, "py_1_distance_mistake.png"))
    dumbbell(rows, "f", os.path.join(OUT_DIR, "py_2_distance_finding.png"))
    no_usable_bars(rows, os.path.join(OUT_DIR, "py_3_no_usable_chunk.png"))
    print(f"wrote 3 figures to {OUT_DIR}")


if __name__ == "__main__":
    main()
