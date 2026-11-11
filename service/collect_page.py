"""GET /coverage: what the people collecting the 32 sets need to see, so they run nothing by hand.
The counting is eval/replay_captured.py's. Only rows and reasons are shown, no profile or answer.
"""
import calendar
import html
import os
import time

from eval.replay_captured import CELLS_WANTED, build_test_set, read_captures, row_numbers, sets_on_file

SHEET_URL = "https://claude.ai/artifact/2TaAz6JGaKsdeE7AXgdu1L#sheet"  # who took which row, shared by everyone

# Why a set does not count, and what to do about it.
REASONS = {
    "no_similarity": ("similarity ไม่ได้ทำงาน", "เปิด similarity service แล้วกด Retry บนหน้า set นั้น"),
    "stub_similarity": ("แอปไม่เห็น SIMILARITY_URL จึงใช้คะแนนปลอม", "แก้ .env.local, restart npm run dev แล้วทำ set ใหม่"),
    "target_not_10x1": ("ไม่ได้ตั้ง 10 reps × 1 set", "ทำ set ใหม่"),
    "between_patterns": ("สัดส่วนท่าผิดอยู่นอกเกณฑ์ (ต้อง ≥ 70% หรือ 20–40%)", "ทำ set ใหม่"),
    "unknown_rule": ("มีกฎที่ระบบไม่รู้จัก", "แจ้ง Sujira"),
    "unknown_exercise": ("มีท่าที่ระบบไม่รู้จัก", "แจ้ง Sujira"),
    "repair_set": ("เป็น repair set", "ไม่ต้องทำอะไร เก็บไว้รายงานแยก"),
}

STYLE = """
:root { color-scheme: light dark; --line: #8a9a9633; --warn: #c77700; --ok: #1a8a50; }
body { font: 15px/1.6 Tahoma, "Noto Sans Thai", sans-serif; max-width: 760px; margin: 0 auto; padding: 24px 16px 48px; }
h1 { font-size: 1.5rem; margin: 0 0 4px; } h2 { font-size: 1.1rem; margin: 28px 0 8px; }
.count { font-size: 1.15rem; font-weight: 600; } .muted { opacity: .72; font-size: .92rem; }
.links { display: flex; flex-wrap: wrap; gap: 8px; }
.get { display: inline-block; padding: 6px 14px; border: 1px solid currentColor; border-radius: 6px; }
.warn { border-left: 4px solid var(--warn); padding: 8px 12px; background: #c7770018; }
table { border-collapse: collapse; width: 100%; } th, td { text-align: left; vertical-align: top; padding: 6px 8px; border-top: 1px solid var(--line); }
th { font-size: .85rem; opacity: .72; } .ok { color: var(--ok); font-weight: 600; } .no { color: var(--warn); font-weight: 600; }
.scroll { overflow-x: auto; } code { overflow-wrap: anywhere; }
"""


def _when(captured_at):
    try:
        return time.strftime("%d/%m %H:%M", time.localtime(calendar.timegm(time.strptime(captured_at, "%Y-%m-%dT%H:%M:%SZ"))))
    except ValueError:
        return captured_at


def _result(item):
    if item["row"] is None and item["cell"] is None:
        why, todo = REASONS.get(item["reason"], (item["reason"], "แจ้ง Sujira"))
        return f'<span class="no">ไม่นับ</span> {html.escape(why)}<br><span class="muted">{html.escape(todo)}</span>'
    if item["repeat"]:
        return f'แถว #{item["row"]} <span class="muted">มี set ก่อนหน้าแล้ว set นี้เป็นส่วนเกิน ไม่ต้องลบ</span>'
    return f'<span class="ok">แถว #{item["row"]}</span>'


def _page(body):
    return (f'<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="20">'
            f'<title>เช็กการเก็บข้อมูล</title><style>{STYLE}</style></head><body><h1>เช็กการเก็บข้อมูล</h1>{body}</body></html>')


def render(capture_path):
    if not capture_path:
        return _page('<p class="warn"><b>ระบบยังไม่บันทึกอะไรเลย</b> เพิ่มบรรทัด <code>FEEDBACK_CAPTURE=capture/app_requests.jsonl</code> '
                     'ใน <code>.env</code> ของ RAG_SYSTEM แล้วเปิด feedback service ใหม่</p>')
    if not os.path.exists(capture_path):
        return _page('<p>ยังไม่มี set ในเครื่องนี้ ทำ set แรกแล้วหน้านี้จะอัปเดตเอง</p>')

    records, _, bad = read_captures([capture_path])
    test, _, _ = build_test_set(records)
    items = sets_on_file(records)
    rows = row_numbers()
    empty = sorted(n for cell, n in rows.items() if cell not in test)

    body = [f'<p class="count">เครื่องนี้เก็บแล้ว {len(test)}/{CELLS_WANTED} แถว</p>',
            '<p class="muted">นับเฉพาะ set ในเครื่องนี้ แถวที่ยังว่างอาจมีเพื่อนทำแล้ว ให้ดูในตารางบนเว็บ หน้านี้อัปเดตเองทุก 20 วินาที</p>',
            f'<p class="links"><a class="get" href="{SHEET_URL}" target="_blank" rel="noopener">เปิดตารางบนเว็บ</a>'
            '<a class="get" href="/capture.jsonl">ดาวน์โหลดไฟล์สำหรับส่ง</a></p>']
    if bad:
        body.append(f'<p class="warn">มี {bad} บรรทัดในไฟล์ที่อ่านไม่ได้ แจ้ง Sujira</p>')
    body.append('<h2>set ล่าสุดเข้าแถวไหน</h2>')
    if items:
        lines = "".join(f'<tr><td>{html.escape(_when(i["at"]))}</td><td>{html.escape(i["exercise"])}</td><td>{_result(i)}</td></tr>'
                        for i in items)
        body.append(f'<div class="scroll"><table><tr><th>เวลา</th><th>ท่า</th><th>ผล</th></tr>{lines}</table></div>')
    else:
        body.append('<p>ยังไม่มี set ของรอบเก็บนี้</p>')
    if empty:
        body.append(f'<h2>แถวที่เครื่องนี้ยังไม่มี</h2><p>{" · ".join(f"#{n}" for n in empty)}</p>')
    return _page("".join(body))
