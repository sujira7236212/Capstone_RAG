"""Render eval/rule_cards.json as one document the expert reads and approves (eval v6 E1).

The expert approves each card as a whole - the definition, what counts and what does not,
and the example sentences with their labels. They do not label KB chunks. Thai comes
first because it is what the expert reads; the English under it is what the LLM judge
will see, so the two must agree.

Usage:
    python eval/render_rule_cards.py                       # -> docs/rules/rule_cards_review.md
    python eval/render_rule_cards.py --out some/file.md
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CARDS = os.path.join(HERE, "rule_cards.json")
OUT = os.path.join(ROOT, "docs", "rule_cards_review.md")

EXERCISE_TH = {"squat": "สควอท", "push-up": "วิดพื้น", "lunge": "ลันจ์", "bicep-curl": "ไบเซ็ปส์เคิร์ล"}
INFO_TH = {"appearance": "ลักษณะ", "causes": "สาเหตุ", "consequences": "ผลเสีย",
           "fixes": "วิธีแก้", "correct_form": "ท่าที่ถูก"}
KIND_TH = {"mistake": "ท่าผิด", "cause": "สาเหตุ", "consequence": "ผลเสีย", "fix": "วิธีแก้",
           "principle": "หลักท่าที่ถูก", "finding": "ผลวิจัย"}
LABELS = [
    ("relevant", "relevant — ช่วยแก้อาการนี้โดยตรง"),
    ("wrong_fault", "wrong_fault — พูดถึงท่าผิดอื่น"),
    ("irrelevant", "irrelevant — ไม่ได้พูดถึงท่าผิดเลย"),
]

INTRO = """\
# Rule card สำหรับอนุมัติ — เฉลยของการประเมิน RAG v6

<!-- สร้างจาก eval/rule_cards.json ด้วย python eval/render_rule_cards.py ห้ามแก้ไฟล์นี้ด้วยมือ -->
ข้อมูลกฎนำมาจาก {spec}

## สิ่งที่ขอให้ผู้เชี่ยวชาญตรวจ

ระบบ 1 ตรวจท่าได้ 12 กฎ card แต่ละใบนิยามว่าเนื้อหาแบบไหนนับว่า**ช่วยแก้อาการนั้น**
ระบบจะให้ LLM หลายค่ายใช้ card เหล่านี้ตัดสินเนื้อหาที่ RAG ดึงมา ดังนั้น card ต้องถูกต้องก่อนเริ่มวัดผล

ขอให้ตรวจ card ละ 4 เรื่อง
1. **นิยาม** ตรงกับอาการที่ต้องการแก้หรือไม่
2. **นับรวม / ไม่นับ** ขีดเส้นแบ่งกับอาการที่คล้ายกันถูกหรือไม่
3. **ประโยคตัวอย่าง** ป้ายกำกับถูกหรือไม่ ป้ายมี 3 แบบ
   - `relevant`: ประโยคช่วยให้ผู้ใช้แก้อาการ**นี้**ได้ (บอกลักษณะ สาเหตุ ผลเสีย วิธีแก้ หรือหลักท่าที่ถูก)
   - `wrong_fault`: ประโยคพูดถึงท่าผิด**อื่น** ซึ่งอาจเป็นกฎอื่นในท่าเดียวกันหรือท่าผิดที่ระบบไม่มีกฎ
   - `irrelevant`: ประโยคไม่ได้พูดถึงท่าผิดเลย เช่น วิธีวิจัย หรือข้อมูลทั่วไปของท่า
4. **คำถามถึงผู้เชี่ยวชาญ** (ถ้ามี) ช่วยเลือกคำตอบ ประโยคหรือข้อที่มีป้าย ⚑ ขึ้นกับคำตอบนั้น

ไม่ต้องตรวจเนื้อหาจากฐานความรู้ ขอแค่อนุมัติ card
ภาษาอังกฤษคือข้อความที่ LLM ใช้จริง ภาษาไทยคือคำแปลของข้อความเดียวกัน ถ้าสองภาษาไม่ตรงกันให้แจ้ง

**ช่วง "ระบบวัด"** มาจากระบบ 1 ใช้ประกอบการอ่านเท่านั้น ไม่ต้องอนุมัติ
"""


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def flag(item):
    return f" ⚑{item['depends_on']}" if item.get("depends_on") else ""


def render_card(n, card):
    ex = card["exercise_id"]
    rule = card["rule_names"][0]
    older = ", ".join(f"`{r}`" for r in card["rule_names"][1:]) or "—"
    m = card["measures"]
    out = [
        f"## {n}. {EXERCISE_TH.get(ex, ex)} — {card['display_th']} (`{rule}`)",
        "",
        f"`concept_id`: `{card['concept_id']}` · card version {card['card_version']} · ชื่อเดิมของกฎ: {older}",
        "",
        f"**ข้อความบนจอ:** \"{card['cue']}\"",
        "",
        f"**ระบบวัด** ({m['spec_section']}, ตรวจทีละ{'ครั้ง' if m['scope'] == 'rep' else 'เฟรม'}): {m['metric']} "
        f"**แจ้งเมื่อ** {m['fires_when']}" + (f" _{m['note']}_" if m.get("note") else ""),
        "",
        "### นิยาม",
        "",
        card["definition"]["th"],
        "",
        f"> {card['definition']['en']}",
        "",
        "### นับรวม / ไม่นับ",
        "",
        "| | ภาษาไทย | English (LLM ใช้) |",
        "|---|---|---|",
    ]
    for item in card["includes"]:
        out.append(f"| ✅ นับ{flag(item)} | {cell(item['th'])} | {cell(item['en'])} |")
    for item in card["excludes"]:
        out.append(f"| ❌ ไม่นับ{flag(item)} | {cell(item['th'])} | {cell(item['en'])} |")
    out += ["", "### ข้อมูลที่นับว่าเกี่ยวข้อง", "", "| หัวข้อ | ภาษาไทย | English |", "|---|---|---|"]
    for key, th in INFO_TH.items():
        info = card["relevant_info"][key]
        out.append(f"| {th} | {cell(info['th'])} | {cell(info['en'])} |")

    out += ["", "### ประโยคตัวอย่าง", ""]
    for label, heading in LABELS:
        out += [f"**{heading}**", "", "| # | ประโยค | คำแปล | ชนิด |", "|---|---|---|---|"]
        for a in card["anchors"][label]:
            if label == "wrong_fault":
                kind = f"{'กฎพี่น้อง ' if a.get('sibling') else ''}`{a['fault']}`"
            else:
                kind = KIND_TH.get(a.get("kind"), "")
            out.append(f"| {a['id']}{flag(a)} | {cell(a['text'])} | {cell(a['th'])} | {kind} |")
        out.append("")

    if card["open_questions"]:
        out += ["### คำถามถึงผู้เชี่ยวชาญ", ""]
        for q in card["open_questions"]:
            answer = (f"{q['answer']['th']} ({q['answer']['date']})" if q.get("answer")
                      else "________________________")
            out += [f"- **⚑{q['id']}** {q['th']}", f"  _{q['en']}_", f"  คำตอบ: {answer}", ""]

    out += [
        "### การอนุมัติ",
        "",
        "☐ อนุมัติ   ☐ อนุมัติ โดยแก้ตามหมายเหตุ   ☐ ไม่อนุมัติ",
        "",
        "หมายเหตุ / สิ่งที่ต้องแก้: ____________________________________________",
        "",
        "ผู้อนุมัติ: ______________________   วันที่: ______________",
        "",
        "---",
        "",
    ]
    return out


def render(data):
    cards = data["cards"]
    n_anchor = sum(len(v) for c in cards for v in c["anchors"].values())
    n_q = sum(len(c["open_questions"]) for c in cards)
    out = [INTRO.format(spec=f"`{data['source_spec']}`"), "## สรุป", "",
           f"{len(cards)} card · ประโยคตัวอย่าง {n_anchor} ประโยค · คำถามถึงผู้เชี่ยวชาญ {n_q} ข้อ", "",
           "| # | ท่า | กฎ | อาการ | คำถาม |", "|---|---|---|---|---|"]
    for n, c in enumerate(cards, 1):
        out.append(f"| {n} | {EXERCISE_TH.get(c['exercise_id'], c['exercise_id'])} | `{c['rule_names'][0]}` "
                   f"| {c['display_th']} | {len(c['open_questions']) or ''} |")
    out += ["", "---", ""]
    for n, c in enumerate(cards, 1):
        out += render_card(n, c)
    return "\n".join(out).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cards", default=CARDS)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    with open(args.cards, encoding="utf-8") as f:
        data = json.load(f)
    text = render(data)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {os.path.relpath(args.out, ROOT)} ({len(data['cards'])} cards)")


if __name__ == "__main__":
    main()
