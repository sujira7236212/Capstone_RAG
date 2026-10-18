# ผลทดสอบ feedback: RAG vs no-RAG (baseline v14) — เนื้อหาสำหรับสไลด์

> 2026-10-03 · branch `rule-change-v6` · ข้อมูลจาก `compare_output/compare_result_v14_<ท่า>.json/.md`
> รูปทั้งหมดสร้างด้วย `python eval/plot_rag_vs_norag.py` → `docs/figures/rag_vs_norag/` (3840×2160, 16:9)
> ตัวเลขทุกตัวนับจากไฟล์ผล ไม่มีการเรียก API ใหม่ และ **ยังไม่มี judge** ตัดสินว่าฝั่งไหน "ดีกว่า"

---

## สไลด์ 1 — ทดสอบอย่างไร

**ข้อความหลัก:** ทั้งสองฝั่งได้ prompt เดียวกัน โมเดลเดียวกัน ข้อมูลผู้ใช้ชุดเดียวกัน ต่างกันแค่ RAG ได้ "ตำรา" แนบไปด้วย

| | RAG | no-RAG |
|---|---|---|
| system prompt | v14 (ตัวเดียวกัน) | v14 (ตัวเดียวกัน) |
| context | ข้อความจาก KB v6 ที่ค้นตามท่าผิด (6–9 ชิ้นต่อกฎ) | "No external context provided." |
| โมเดล | `gemini-3.5-flash-lite` @ 0.7 | เหมือนกัน |

- ข้อมูลทดสอบ: mock 20 session = 4 ท่า × (ท่าผิดทีละกฎ 12 กฎ + session ผิดหลายกฎ + session ไม่มีท่าผิด)
- แต่ละ session ขอคำตอบ 3 ครั้ง (temperature 0.7 คำตอบไม่เหมือนกันทุกครั้ง) → **60 คำตอบต่อฝั่ง รวม 120**
- prompt มีกติกา grounding: **ห้ามใส่ตัวเลข (องศา, %, ผลวิจัย) ที่ไม่มีใน context** — ใช้กับทั้งสองฝั่ง

---

## สไลด์ 2 — RAG ให้ตัวเลขที่ตรวจที่มาได้ (ข้อได้เปรียบหลัก)

รูป: `1_number_sources.png`

**ข้อความหลัก:** ตัวเลขที่ตรวจย้อนไปเจอใน KB ได้: **RAG 31 ครั้ง · no-RAG 1 ครั้ง**

- นับทุก "ตัวเลข+หน่วย" ในคำตอบ (องศา, %, วินาที, เซ็ต …) แล้วจัดตามที่มา
  - **มีที่มาจาก KB** = ค่าเดียวกัน หน่วยชนิดเดียวกัน อยู่ใน context ของ session นั้น
  - **จำนวน rep · คะแนน** = ตัวเลขจาก JSON ของผู้ใช้ (ทั้งสองฝั่งเท่ากัน 33 / 34)
  - **ไม่มีที่มา** = ไม่อยู่ทั้งใน JSON และ context
- ตัวเลขจาก KB ที่ RAG ใช้: เข่าหน้างอ 90–100° (lunge) · ศีรษะ แขน ลำตัวหนัก ≈ 55% ของน้ำหนักตัว · งอศอก 90° (push-up) · ไหล่เลื่อน ≈ 20° เมื่อล้า (curl)
- **พูดตรง ๆ:** ตัวเลขไม่มีที่มายังเยอะทั้งสองฝั่ง (38 vs 42) ส่วนใหญ่เป็นจังหวะ/น้ำหนัก เช่น "ค้างล่าง 2 วินาที" "ลดน้ำหนัก 10%" เพราะ KB มีเรื่องปริมาณการฝึกแค่ 4 item ทั้ง KB → RAG ช่วยได้เฉพาะเรื่องที่ KB มี

---

## สไลด์ 3 — ตัวอย่าง: RAG อธิบาย "ทำไมสำคัญ" ได้เจาะจงกว่า

session: lunge — ลำตัวโน้มไปหน้า (`forward_trunk_lean`) · ส่วน "Why it matters" ของคำตอบที่ 1

| RAG | no-RAG |
|---|---|
| "Because your upper body makes up **about 55% of your total body weight**, tipping it forward dumps **extra shear stress straight onto your front knee joint** and forces your lower back muscles to work twice as hard …" | "This shifts the work away from your glutes and quads and dumps the load onto your lower back. That steals the muscle growth you came for and leaves you with a sore lower back …" |
| มาจาก KB: "head, arms, and trunk ≈ 55% of body mass" · "leaning forward … increase the shear force at the knee joint" · กล้ามหลังล่างทำงาน 40% vs 20% MVIC (= "twice as hard") | ถูกต้องแต่ทั่วไป ไม่พูดถึงเข่าเลย |

session: lunge — ลงไม่ลึก (`shallow_lunge`)
- RAG: "When your front knee only bends to **80 degrees** instead of sinking deeper into that **90 to 100-degree** sweet spot, the load spikes sharply on your quads …" — มีเป้าหมายเป็นตัวเลขให้ผู้ใช้ทำตาม
- no-RAG: "When you don't drop your hips all the way down, your front quads and glutes miss out on the full stretch …" — ไม่มีเป้าหมายที่วัดได้

**ข้อความหลัก:** เมื่อ KB มีเนื้อหาของกฎนั้น RAG ให้ "เหตุผลที่มีหลักฐาน + เป้าหมายเป็นตัวเลข" ซึ่ง no-RAG ให้ไม่ได้เพราะกติกาห้ามคิดตัวเลขเอง

---

## สไลด์ 4 — ตัวอย่าง: เมื่อ KB ไม่มีเนื้อหา RAG แย่กว่า no-RAG

session: lunge — ขาหลังเหยียดตรง (`straight_back_leg`) · กฎนี้มี item ติดป้ายแค่ 4 ชิ้น (principle อย่างเดียว)

- context ได้ 8 ชิ้น แต่ตรงกฎจริงแค่ 1 ("Lower the rear knee toward the ground") ที่เหลือเป็นเรื่องกฎอื่น: เข่าหน้าเลยปลายเท้า ×2, หมุนเข่า/เท้า ×2, หลังงอ/แอ่น
- RAG คำตอบที่ 2: "This puts extra **rotational twisting stress** straight onto your knee joints …" ← เหตุผลของ "เข่าบิด" ไม่ใช่ "ขาหลังเหยียด"
- no-RAG: "When your back leg stays locked out, your hips and front quad have to shoulder extra strain while your glutes on the back leg switch off …" ← ตรงประเด็นกว่า

**ข้อความหลัก:** RAG ดีได้เท่าที่ KB มี — KB v6 ยังมี data gap 3 กฎ (`straight_back_leg`, `shallow_lunge`, `partial_pushup`) และเมื่อขาด ระบบไม่ได้ context ว่าง แต่ได้เนื้อหาของกฎอื่นมาแทน

---

## สไลด์ 5 — ข้อเสียที่วัดได้

รูป: `2_side_effects.png`

| ตัววัด (60 คำตอบต่อฝั่ง, ยิ่งน้อยยิ่งดี) | RAG | no-RAG |
|---|---|---|
| ศัพท์เทคนิคที่ไม่ได้แปลเป็นภาษาคน | 9 | 4 |
| ชื่อ key หลุดถึงผู้ใช้ (เช่น `partial_curl`) | 2 | 4 |
| ตัวเลขที่ไม่มีที่มา | 38 | 42 |

- ศัพท์ไม่แปลของ RAG มาจากศัพท์ใน KB (lunge 6 จาก 9) — เฉลี่ย 0.15 ต่อคำตอบ
- ข้อบกพร่องที่เจอจากการอ่าน (ไม่ได้นับเป็นตัวเลข):
  - **ยืดตัวเลข:** "nearly double the muscular demand" แต่ KB บอก 0.980 vs 0.717 Nm/BW (≈ 1.4 เท่า เมื่อเทียบกับ 90°)
  - **ส่งสถิติงานวิจัยให้ผู้ใช้:** 1 ใน 3 คำตอบของ `forward_trunk_lean` เขียน "40 ± 29% … 20 ± 15%"
  - **อ่านผลวิจัยผิด:** "ไหล่เลื่อน 20° ที่ 20% ของรอบท่า" ถูกเขียนเป็น "near the bottom of the movement" 1 คำตอบ

---

## สไลด์ 6 — RAG ไม่ลอกประโยคงานวิจัยแล้ว

รูป: `3_copying_history.png`

| รุ่น | คำตอบ RAG ที่วัด | ลอก context ติดกันยาวสุด | จุดที่ลอก ≥ 6 คำ |
|---|---|---|---|
| v9 (ก่อนแก้ prompt) | 4 | 20 คำ | 13 |
| v10 (เพิ่มกติกาห้ามลอก) | 4 | 9 คำ | 3 |
| v14 + KB v6 (ปัจจุบัน) | 60 | 10 คำ | 12 |

- เส้น 6 คำ = ความยาวที่ no-RAG (ซึ่งไม่เห็น context) ซ้ำกับ context ได้โดยบังเอิญ
- v9: Gemini judge ตัดสินว่า no-RAG ดีกว่าเพราะ RAG "อ่านเหมือนงานวิจัย" → สาเหตุคือลอกประโยค → แก้ใน prompt v10
- v14 มีจุดลอก 12 จุด แต่มาจาก 60 คำตอบ (v9 13 จุดจาก 4 คำตอบ) และยาวสุด 10 คำ ซึ่งส่วนใหญ่เป็นวลีเป้าหมายสั้น ๆ

---

## สไลด์ 7 — สรุปและข้อจำกัด

**สรุป**
1. RAG ทำให้ feedback **มีหลักฐานและตัวเลขที่ตรวจที่มาได้** (31 vs 1) โดยเฉพาะส่วน "ทำไมสำคัญ" และเป้าหมายของท่า
2. ส่วน "แก้ยังไง" (cue, drill) สองฝั่งคล้ายกัน เช่น knee valgus ทั้งสองฝั่งแนะนำยางยืดรอบเข่า — LLM รู้วิธีแก้ท่าผิดที่พบบ่อยอยู่แล้ว
3. RAG ดีได้เท่าที่ KB มี: กฎที่ KB ขาด RAG ให้เหตุผลผิดกฎ · KB แทบไม่มีปริมาณการฝึก ตัวเลขจังหวะ/น้ำหนักจึงยังถูกคิดเองทั้งสองฝั่ง
4. ข้อเสียของ RAG มีแต่เล็ก: ศัพท์ไม่แปล 9 vs 4 ใน 60 คำตอบ · ไม่ลอกประโยคแล้ว

**ข้อจำกัด (ควรพูดบนสไลด์)**
- ยังไม่มี judge ตัดสินว่าฝั่งไหน "ดีกว่า" — ตัวเลขทั้งหมดเป็นการนับอัตโนมัติ
- ข้อมูลเป็น mock 20 session ไม่ใช่ผู้ใช้จริง · ตัวเลข "มีที่มา" ตรวจแค่ว่าค่าตรงกับ context ไม่ได้ตรวจว่าใช้ถูกบริบท (ตัวอย่างในสไลด์ 5)
- ตัวนับศัพท์เทคนิคใช้รายการคำที่ทำเอง (`eval/jargon_terms.json`)

**ขั้นต่อไป:** judge 3 ค่าย ตัดสินแบบ blind เทียบกับ rule card (แผน E3–E6 ใน `eval_v6_plan.md`) · curate เอกสารเพิ่มสำหรับ 3 กฎที่ขาด · ปรับ prompt ทีละข้อ (P1–P6)
