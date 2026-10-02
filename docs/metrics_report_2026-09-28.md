# รายงานผลการวัด: ทุก metric ที่วัดมาแล้ว

**รวบรวมเมื่อ:** 28 กันยายน 2026 · **ช่วงข้อมูล:** 8–26 กันยายน 2026
**ที่มาของตัวเลข:** รวบรวมจากรายงานที่รันไว้แล้วใน `compare_output/` และ `docs/` ไม่ได้รันอะไรใหม่ (ไฟล์ต้นทางอยู่ท้ายแต่ละหัวข้อ)

---

## สรุปสั้น: ค่าล่าสุดของแต่ละ metric

ค่าปัจจุบันของระบบ: KB `kb_gemini_curated_v5`, embedding `gemini-embedding-2`, การค้นแบบ R4 (multi-query), prompt v11

| กลุ่ม | metric | ค่าล่าสุด | ทิศที่ดี | วัดเมื่อ |
|---|---|---|---|---|
| Retrieval · golden set | fault ที่ได้ mistake ถูก ≥ 1 (hit) | **10/10** | สูง | 26 ก.ย. (R4) |
| | precision (good / kept) | **0.48** ⚠️ | สูง | 26 ก.ย. (R4) |
| | bad (chunk ของอาการอื่นที่ติดป้ายว่าเป็นอาการนี้) | **0** | ต่ำ | 26 ก.ย. (R4) |
| Retrieval · relevance pool | recall micro (ceiling) | **0.16** (0.21), ได้ 66 จาก 411 facts | สูง | 26 ก.ย. (R4) |
| | recall macro | **0.27** | สูง | 26 ก.ย. (R4) |
| | pool-precision (relevant / kept) | **0.80** (65 จาก 81 chunks) | สูง | 26 ก.ย. (R4) |
| | ctx wrong_fault | **6** | ต่ำ | 26 ก.ย. (R4) |
| | miss by reason | quota 210 · rank 108 · margin 17 · tag_filter 10 · tag_spelling 0 | — | 26 ก.ย. (R4) |
| Generation · อัตโนมัติ | unglossed jargon (รวม 4 ท่า) | **1 คำ** | ต่ำ | 22 ก.ย. (prompt v10) |
| | longest shared n-gram กับ context | **9 คำ** (no-RAG floor = 6) | ใกล้ floor | 22 ก.ย. (prompt v10) |
| Generation · LLM judge | win rate 4 ด้าน + overall, sign test | **ยังไม่ได้วัด** | — | G1 รออนุมัติ |

⚠️ precision 0.48 **ไม่ได้แปลว่าการค้นแย่ลง** `must_hit` ในชุดเฉลยยังเขียนตามถ้อยคำของ KB v4 chunk ที่ถูกแต่ใช้คำต่างจึงถูกนับเป็น neutral (ดูหัวข้อ 2.4)

---

## ข้อควรรู้ก่อนอ่านตัวเลข

1. **เทียบข้ามช่วงไม่ได้:** ตัวเลขช่วง MiniLM (8–12 ก.ย.) กับช่วง Gemini (14 ก.ย. เป็นต้นไป) ใช้ระยะคนละสเกล และชุดเฉลยถูกแก้ระหว่างทาง ให้เทียบภายในช่วงเดียวกันเท่านั้น
2. **ตัวเลขทั้งหมดเป็นของ taxonomy 10 อาการเดิม:** ระบบ 1 เปลี่ยนเป็น 12 กฎแล้ว (แผน `docs/rule_change_v6_plan.md`) ตัวเลขในรายงานนี้จึงใช้เป็น baseline ของ KB v6 ตรง ๆ ไม่ได้ ต้องวัดใหม่
3. **ฝั่ง retrieval วัดครบ ฝั่งคำตอบยังวัดน้อย:** มีแค่ metric ด้านลบ (ศัพท์ยาก, การลอก) ยังไม่มีตัวเลขว่าคำตอบ "ดีกว่า" (G1 ยังไม่ได้รัน)

---

## 1. KB coverage (`kb_coverage.py`)

**วัดอะไร:** จำนวน chunk ที่อยู่ในระยะใช้งานได้ (cosine distance ≤ 0.40) ต่อ 1 อาการ แยก `mistake` กับ `finding`
**ใช้เมื่อ:** ช่วง MiniLM (KB v3 → v4) · ใช้กับ Gemini ไม่ได้แล้ว เพราะ Gemini ดันทุกอย่างให้อยู่ในระยะ ≤ 0.40 เกือบหมด (แทบทุกอาการได้ 40/40)

> อาการในตารางนี้เป็นชุดเก่าก่อนได้รายชื่อกฎจริง 10 ข้อจากระบบ 1

| ท่า | อาการ | v3 mistake | v3 finding | v4 mistake | v4 finding |
|---|---|---|---|---|---|
| squat | keep back straight | 11 | 5 | 13 | 4 |
| squat | knees behind toes | 19 | 0 🔴 | 19 | 1 ⚠️ |
| squat | heels lifting | 10 | 4 | 13 | 4 |
| lunge | back not straight | 9 | 9 | 12 | 11 |
| lunge | front knee past toes | 10 | 9 | 12 | 9 |
| push-up | neck craning forward | 1 ⚠️ | 0 🔴 | 1 ⚠️ | 0 🔴 |
| push-up | elbows flaring out | 0 🔴 | 0 🔴 | 1 ⚠️ | 0 🔴 |
| bicep-curl | not full extension | 2 ⚠️ | 0 🔴 | **8** | 0 🔴 |
| bicep-curl | using momentum | 10 | 0 🔴 | 6 | 0 🔴 |
| bicep-curl | swinging torso | 9 | 0 🔴 | 8 | 0 🔴 |

**อ่านผล:** v4 สะอาดขึ้น (2,519 → 2,432 chunks) แต่ push-up ยังแทบไม่มี mistake และ bicep-curl ไม่มี finding ที่ใช้กับอาการผิดได้เลย

ที่มา: `docs/kb_quality_assessment.md` §2, §6

---

## 2. Golden set (`eval/eval_retrieval.py`)

**วัดอะไร:** chunk ที่ผ่านด่านคัดกรองเข้า context จริง เทียบกับชุดเฉลยที่คนเขียน (`eval/golden_chunks.json`)

| metric | ความหมาย |
|---|---|
| hit | จำนวนอาการที่ได้ chunk `mistake` ถูกอย่างน้อย 1 ชิ้น |
| good | chunk ที่ตรงกับ pattern `must_hit` |
| bad | chunk ที่ตรงกับ `must_not_hit` คือของอาการอื่นแต่ติดป้ายเป็นอาการนี้ (**ตัวที่สำคัญที่สุด** เพราะเป็นต้นเหตุ hallucination) |
| neutral | ไม่ตรงทั้งสองแบบ |
| precision | good / kept |

มี 2 mode: **single** (10 อาการ วัดทีละอาการ) และ **session** (mock 4 session ที่มีหลายอาการปนกัน)

### 2.1 ช่วง MiniLM บน KB v4 (11–12 ก.ย.)

| ขั้น | single: hit · kept · good · bad · precision | session: hit · kept · good · bad · precision |
|---|---|---|
| baseline gate v6 | 8/10 · 41 · 21 · **14** · 0.51 | 5/6 · 24 · 12 · **9** · 0.50 |
| gate v6 + `--margin 0.10 --cap mistake=0.40` | 8/10 · 33 · 18 · 11 · 0.55 | — |
| 1(a) เขียน query bicep partial ROM ใหม่ | 9/10 · 40 · 24 · **10** · 0.60 | 5/6 · 23 · 14 · **6** · 0.61 |
| 1(c) gate v7 + principle ต่ออาการ | 9/10 · 47 · 33 · **9** · 0.70 | 5/6 · 27 · 20 · **6** · 0.74 |
| 1(b) แก้ OCR องศา ("1208" → "120°") | 9/10 · 47 · 33 · 9 · 0.70 (เท่าเดิมทุกช่อง) | 5/6 · 27 · 20 · 6 · 0.74 |

ขั้น 1(c) เพิ่ม principle เข้ามาด้วย ถ้าเทียบเฉพาะ mistake + finding: bad 14 → 10 → **5** โดย good คงที่ 21

**Sweep margin บน MiniLM (single, mistake + finding):**

| RELATIVE_MARGIN | good | bad |
|---|---|---|
| 0.20 (v6) | 24 | 10 |
| 0.10 | 21 | 7 |
| **0.06 (เลือก)** | 21 | 5 |

### 2.2 ย้ายไป Gemini บน KB v4 (14 ก.ย.)

**Sweep margin (single):**

| RELATIVE_MARGIN | kept | good | bad | neutral | precision |
|---|---|---|---|---|---|
| 0.10 / 0.08 | 70 | 26 | 6 | 38 | 0.37 |
| 0.06 | 68 | 25 | 6 | 37 | 0.37 |
| 0.05 | 68 | 25 | 6 | 37 | 0.37 |
| 0.04 | 65 | 24 | 4 | 37 | 0.37 |
| **0.03 (เลือก)** | **62** | **23** | **2** | **37** | **0.37** |
| 0.015 | 53 | 20 | 2 | 31 | 0.38 |
| 0.01 | 51 | 19 | 1 | 31 | 0.37 |

**เทียบ MiniLM กับ Gemini:**

| mode | embedding | hit | kept | good | bad | neutral | precision |
|---|---|---|---|---|---|---|---|
| single | MiniLM v7 | 9/10 | 47 | 33 | 9 | 5 | 0.70 |
| single | **Gemini (margin 0.03)** | 8/10 | 62 | 23 | **2** | 37 | 0.37 |
| session | MiniLM v7 | 5/6 | 27 | 20 | 6 | 1 | 0.74 |
| session | **Gemini** | 4/6 | 38 | 12 | **5** | 21 | 0.32 |

bad ลดลง 78% (9 → 2) แต่ precision ตกเพราะ neutral พุ่ง (5 → 37) ไม่ใช่เพราะ bad เพิ่ม

**หลังถอด grokipedia (84 chunks):** single hit 8/10 · bad 2 → **1** · แต่ principle ของ elbow flare หายเหลือ good 0/3

### 2.3 KB v5 (16–18 ก.ย.)

| ขั้น | hit | precision | bad |
|---|---|---|---|
| v4 (Gemini, baseline) | 8/10 | 0.33 | 1 |
| v5 รอบแรก (ชุดเฉลยยังเป็นถ้อยคำ v4 เลยเป็นตัวเลขหลอก) | 4/10 | 0.12 | — |
| v5 หลังเพิ่มถ้อยคำ v5 ในชุดเฉลย | 10/10 | 0.60 | 5 |
| v5 หลังแก้ tag ผิด 19 item ของ bicep-curl | 10/10 | 0.60 | 1 |
| **v5 หลังถอดเปเปอร์ preacher/incline curl** | **10/10** | **0.62** | **1** |

### 2.4 ระหว่างการทดลองปรับการค้น (25–26 ก.ย.)

| ขั้น | hit · precision · bad |
|---|---|
| B0 | 10/10 · 0.62 · 1 |
| R0 | 10/10 · 0.61 · 1 |
| R1 | 10/10 · 0.49 · **2** |
| R2 | 10/10 · 0.61 · 0 |
| **R4 (ปัจจุบัน)** | **10/10 · 0.48 · 0** |
| R5 | 10/10 · 0.46 · 1 |

precision ของ R4 ตก 0.61 → 0.48 (good 36 → 30, neutral 22 → 33) เพราะ chunk ใหม่ใช้ถ้อยคำไม่ตรง `must_hit` เช่น "Maintain a neutral low back position with a slight lordosis" แทน "…neutral, lordotic lumbar position…" ต้องเพิ่มถ้อยคำในชุดเฉลยก่อนจะใช้ตัวเลขนี้ต่อ

ที่มา: `docs/kb_quality_assessment.md` §7, §9.1, §10, §11 · `compare_output/golden_*.md` · `compare_output/ablation_log.md`

---

## 3. Relevance pool (`eval/eval_retrieval.py --pool`)

**วัดอะไร:** ให้ LLM (`gemini-3.8-flash`, judge prompt v2) ติดป้าย 1,256 candidate ว่าเกี่ยวกับอาการไหน ได้ **411 relevant facts** (หลังรวม near-dup ด้วย Jaccard 0.72) ใช้เป็นตัวหาร

| metric | ความหมาย |
|---|---|
| recall micro / macro | facts ที่ดึงได้ ÷ 411 (micro รวมทุกอาการ, macro เฉลี่ยต่ออาการ) |
| ceiling | recall สูงสุดที่เป็นไปได้ที่งบ 9 chunk ต่ออาการ = 0.21 |
| ctx relevant / wrong_fault | ป้ายของ chunk ที่เข้า context จริง |
| pool-precision | relevant ÷ kept |
| miss by reason | ที่หลุดเพราะอะไร: tag สะกดผิด / tag filter / ไม่ติดอันดับ (rank) / ห่างเกิน margin / โควตาต่อ kind เต็ม (quota) |

**เกณฑ์เก็บขั้น (ต้องผ่านทุกข้อ):** recall ขึ้น · wrong_fault ไม่เพิ่ม · golden bad ไม่เพิ่ม · pool-precision ไม่ตกเกิน 0.05

### 3.1 ผลแต่ละขั้น

| ขั้น | เปลี่ยน | recall micro (ceiling) / macro | facts | ctx relevant / wrong_fault / kept | pool-precision | miss: spelling · filter · rank · margin · quota | ตัดสิน |
|---|---|---|---|---|---|---|---|
| B0 | จุดตั้งต้น | 0.15 (0.21) / 0.26 | 61 | 60 / 6 / 77 | 0.78 | 14 · 10 · 141 · 34 · 151 | baseline |
| R0 | แก้ tag สะกดผิดใน DB | 0.15 (0.21) / 0.26 | 62 | 61 / 6 / 77 | 0.79 | 0 · 10 · 146 · 34 · 159 | ✅ เก็บ |
| R1 | `--tag-mode union` | 0.14 (0.21) / 0.24 | 57 | 56 / 6 / 79 | **0.71** | 0 · 0 · 150 · 34 · 170 | ❌ |
| R2 | `--kind-pool single` | **0.07** (0.21) / 0.10 | 28 | 28 / 2 / 31 | 0.90 | 0 · 10 · 146 · 194 · 33 | ❌ |
| R2 diag | single + margin ต่อ kind (ไม่ใช่ขั้นจริง) | 0.16 (0.21) / 0.29 | 67 | 66 / **9** / 89 | 0.74 | 0 · 10 · 146 · 7 · 181 | ❌ |
| R3 | MMR | — | — | — | — | — | ⏭ ข้าม |
| **R4** | **`--queries profile` (what / why / fix)** | **0.16 (0.21) / 0.27** | **66** | **65 / 6 / 81** | **0.80** | 0 · 10 · 108 · 17 · 210 | ✅ **ปัจจุบัน** |
| R5 | `--hybrid` (BM25) | 0.16 (0.21) / 0.26 | 65 | 64 / **8** / 81 | 0.79 | 0 · 10 · 71 · 17 · 248 | ❌ |
| R6 | `--rerank` | — | — | — | — | — | ⏸ เครื่องไม่พอ |

**chunk ใน context แยกตาม kind:** R0 = mistake 22 / finding 18 / principle 19 / consequence 18 · R2 = 30 / 1 / 0 / 0 (principle และ consequence หายจากทุกอาการ) · **R4 = 25 / 19 / 19 / 18** (ครบทุกอาการ)

### 3.2 Sensitivity ที่จดไว้ (ไม่ได้ใช้ตัดสิน)

**R1 `TAG_BONUS`:**

| TAG_BONUS | recall | wrong_fault | pool-precision | golden bad |
|---|---|---|---|---|
| 0.03 (R1) | 57 | 6 | 0.71 | 2 |
| 0.06 | 62 | 5 | 0.78 | 1 |
| 0.10 | 62 | 5 | 0.79 | 1 |

**R5 BM25:**

| BM25_K · WEIGHT | recall | wrong_fault | golden bad | pool-precision |
|---|---|---|---|---|
| 0 · 0 (= R4) | 66 | 6 | 0 | 0.80 |
| 12 · 0 | 66 | 6 | 0 | 0.80 |
| 0 · 0.03 | 65 | 8 | 1 | 0.79 |
| 12 · 0.015 | 65 | 7 | 0 | 0.79 |
| 12 · 0.03 (R5) | 65 | 8 | 1 | 0.79 |

### 3.3 รายอาการ ณ R4 (ปัจจุบัน)

| ท่า | อาการ | facts | ดึงได้ | recall | ceiling | ctx relevant | wrong_fault | irrelevant | miss: rank · margin · quota |
|---|---|---|---|---|---|---|---|---|---|
| squat | butt wink | 41 | 8 | 0.20 | 0.22 | 8 | 0 | 0 | 6 · 1 · 26 |
| squat | knee valgus | 116 | 9 | 0.08 | 0.08 | 9 | 0 | 0 | 55 · 0 · 51 |
| squat | partial squat | 52 | 8 | 0.15 | 0.17 | 8 | 0 | 1 | 9 · 0 · 35 |
| push-up | hip sag | 13 | 5 | 0.38 | 0.69 | 5 | 0 | 2 | 0 · 7 · 1 |
| push-up | partial range of motion | 13 | 5 | 0.38 | 0.69 | 5 | 2 | 1 | 0 · 2 · 6 |
| lunge | excessive forward trunk lean | 42 | 6 | 0.14 | 0.21 | 6 | 2 | 1 | 9 · 0 · 27 |
| lunge | shallow lunge | 56 | 9 | 0.16 | 0.16 | 8 | 0 | 1 | 16 · 0 · 28 |
| lunge | insufficient back knee flexion | 15 | 4 | 0.27 | 0.60 | 4 | 1 | 1 | 0 · 0 · 11 |
| bicep-curl | elbow flare | 5 | 4 | 0.80 | 1.00 | 4 | 1 | 2 | 0 · 0 · 1 |
| bicep-curl | partial range of motion | 58 | 8 | 0.14 | 0.16 | 8 | 0 | 0 | 13 · 7 · 24 |

(back knee มี unlabeled 1 ชิ้น · tag_filter หลุด: knee valgus 1, shallow lunge 3, bicep partial ROM 6)

**อ่านผล:**
- อาการที่มี facts เยอะ (knee valgus 116) recall ชน ceiling แล้ว ตัวกั้นคืองบ 9 chunk ไม่ใช่การค้น
- อาการที่มี facts น้อย (hip sag, push-up ROM, back knee 13–15) ยังห่าง ceiling มาก และเป็นกลุ่มที่มี wrong_fault / irrelevant เข้ามาเติมช่อง
- ตัวกั้นหลักตอนนี้คือ **quota ต่อ kind (210 facts)**

**ข้อจำกัด:** near-dup รวมได้แค่ประโยคที่ถ้อยคำใกล้กันมาก paraphrase จึงนับเป็นหลาย fact recall ที่ได้จึงต่ำกว่าความจริง แต่ยังเทียบระหว่างขั้นได้ เพราะตัวหารเท่ากันทุกขั้น

ที่มา: `compare_output/ablation_log.md` · `compare_output/ablation_{B0,R0,R1,R2,R4,R5}_retrieval.md`

---

## 4. Generation: ตัวเลขอัตโนมัติ (`eval/eval_generation.py`)

**วัดอะไร:** วัดจากรายงานที่รันไว้แล้ว ไม่เรียก LLM ซ้ำ (ได้ผลเดิมทุกครั้ง)

| metric | ความหมาย |
|---|---|
| unglossed jargon | ศัพท์เทคนิค (ตาม `eval/jargon_terms.json`) ที่ไม่มีคำอธิบายภายใน 120 ตัวอักษร · เช็กแค่ว่ามีคำอธิบาย ไม่ได้เช็กว่าอธิบายถูก |
| longest shared n-gram | จำนวนคำติดกันที่ยาวที่สุดที่ลอกมาจาก context · ฝั่ง no-RAG ไม่เคยเห็น context ตัวเลขของฝั่งนั้นจึงเป็นเส้นฐานความบังเอิญ (chance floor) |
| spans ≥ 6 | จำนวนช่วงที่ลอกยาว ≥ 6 คำ |

### 4.1 รวม 4 ท่า (mock 4 session)

| รายงาน | ฝั่ง | unglossed jargon | longest n-gram | spans ≥ 6 |
|---|---|---|---|---|
| v9 | RAG | **17** | **20** | 13 |
| v9 | no-RAG | 3 | 6 (floor) | 1 |
| **v10** | **RAG** | **1** | **9** | **3** |
| v10 | no-RAG | 0 | 6 (floor) | 1 |

### 4.2 รายท่า

| รายงาน | ท่า | ฝั่ง | คำ | jargon | longest n-gram | spans ≥ 6 |
|---|---|---|---|---|---|---|
| v9 | Squat | RAG | 487 | 8 | 20 | 8 |
| v9 | Squat | no-RAG | 465 | 2 | 6 | 1 |
| v9 | Lunge | RAG | 447 | 7 | 9 | 4 |
| v9 | Lunge | no-RAG | 529 | 1 | 0 | 0 |
| v9 | Push-up | RAG | 185 | 2 | 0 | 0 |
| v9 | Push-up | no-RAG | 206 | 0 | 0 | 0 |
| v9 | Bicep Curl | RAG | 564 | 0 | 6 | 1 |
| v9 | Bicep Curl | no-RAG | 553 | 0 | 0 | 0 |
| v10 | Squat | RAG | 532 | 0 | 6 | 2 |
| v10 | Squat | no-RAG | 575 | 0 | 6 | 1 |
| v10 | Lunge | RAG | 594 | 1 | 9 | 1 |
| v10 | Lunge | no-RAG | 567 | 0 | 0 | 0 |
| v10 | Push-up | RAG | 139 | 0 | 0 | 0 |
| v10 | Push-up | no-RAG | 111 | 0 | 0 | 0 |
| v10 | Bicep Curl | RAG | 526 | 0 | 0 | 0 |
| v10 | Bicep Curl | no-RAG | 543 | 0 | 0 | 0 |

**สิ่งที่เหลือใน v10:** jargon 1 คำคือ "center of mass" (lunge) · n-gram 9 คำคือ "2 to 3 cm short of contacting the ground" ซึ่งเป็นตัวเลขเป้าหมายที่ prompt สั่งให้คงไว้ ยอมรับได้

**หมายเหตุ:** ตอนนับด้วยมือ v9 ได้ 18 คำ ส่วนสคริปต์นับได้ 17 ต่างกันที่รายการศัพท์ ไม่ใช่ที่ตัว parser

ที่มา: `compare_output/generation_v9_vs_v10.md` · `docs/kb_quality_assessment.md` §12

---

## 5. Generation: LLM judge แบบ blind pairwise (`eval/judge_pairwise.py`)

**สถานะ: เครื่องมือเสร็จ ยังไม่มีตัวเลข** (Checkpoint G1 รออนุมัติค่า API: generation 110 ครั้ง + judge 110 ครั้ง) · `compare_output/g1_R0.md` มีแค่ส่วนหัว ยังไม่มีคำตอบ

| metric ที่จะวัด | ความหมาย |
|---|---|
| win rate: Accuracy · Comprehensiveness · Professionalism · Feasibility · overall | เกณฑ์ตาม SportsGPT, judge `gemini-3.8-flash` @ 0 |
| sign test (ตัด tie) | ตัวหลัก = overall ของ 50 คู่ (10 fault session × 5 sample) · ต้อง p < 0.05 |
| control | clean session 5 คู่ context เหมือนกันทั้งสองฝั่ง ควรออกใกล้ 50:50 |
| position check | ผู้ตัดสินเลือกฝั่งซ้ายหรือขวาบ่อยเกินไหม ควรใกล้ 50% |
| reference none / union | รันทั้งแบบผู้ตัดสินไม่เห็นและเห็นหลักฐานจาก KB |

**จาก smoke test (ไม่ใช้ตัดสิน):** knee valgus × 2 sample ผู้ตัดสินที่ไม่เห็นหลักฐานให้ R0 ชนะ 2/2 เพราะมองว่าคำแนะนำ "heel lift 2 นิ้ว" จาก KB "unrealistic" จึงตัดสินใจรันผู้ตัดสินทั้ง 2 แบบ

**ตัวเลขอ้างอิงจากภายนอก (ไม่ใช่ของเรา):** SportsGPT ตัด RAG ออกแล้ว Feasibility ตกจาก 3.9 เหลือ 1.65 ขณะที่ Accuracy แทบไม่ตก

---

## 6. การประเมินด้วยการอ่าน (ไม่ใช่สถิติ)

### 6.1 Prompt v6 → v7 (11 ก.ย., 4 session)

| ตัววัด | v6 | v7 |
|---|---|---|
| ประโยคผิดใน LLM output | 4 (momentum, incline bench, back-knee rotation, "1208") | 0 ประโยคที่ยืนยันผิด / 1 ประโยคแบบ hedge (back-knee เพราะ KB ไม่มีข้อมูล) |
| "วิธีแก้" ที่อ้าง principle จาก KB | 0/3 session | 3/3 session |

### 6.2 RAG vs no-RAG รอบ v13 (26 ก.ย., 11 session, 1 คำตอบต่อ session)

| ผล | อาการ |
|---|---|
| RAG ชนะชัด | squat butt wink, push-up partial ROM, bicep elbow flare |
| RAG ถูกทางแต่ใช้ผลวิจัยผิดเงื่อนไข | lunge shallow lunge |
| RAG ใช้ข้อมูลผิดเงื่อนไข | squat knee valgus (ผลการทดสอบกลายเป็นคำแนะนำ), push-up hip sag (ค่าปกติกลายเป็นผลของอาการ) |
| no-RAG ดีกว่า | squat partial squat |
| เทียบไม่ได้ | lunge trunk lean (no-RAG error ตอนเรียก API) |

คำตอบแค่ 1 รอบต่อ session ที่ temperature 0.7 ใช้ได้เป็นตัวอย่างประกอบเท่านั้น สรุปเป็นสถิติไม่ได้

ที่มา: `docs/kb_quality_assessment.md` §7.3–7.4 · `docs/progress_report_2026-09-14_to_26.md` §6

---

## 7. สิ่งที่ยังไม่ได้วัด

| รายการ | สถานะ |
|---|---|
| G1 (LLM judge R0 vs R4) | เครื่องมือพร้อม รออนุมัติค่า API |
| `eval_generation.py` บนรายงาน v11 / v12 / v13 | ยังไม่ได้รัน (ไม่เสียค่า API รันได้ทันที) |
| R6 reranker | เครื่องโหลดโมเดลไม่ได้ (RAM 5.9 GB) |
| golden precision ที่ถูกต้องสำหรับ R4 | ต้องเพิ่มถ้อยคำในชุดเฉลยก่อน |
| metric ว่าตัวเลขในคำตอบ (เลข rep, คะแนน) ตรงกับ session JSON | ยังไม่มี ตอนนี้ตรวจด้วยตา |
| ทุก metric บน KB v6 (12 กฎ) | รอ user ยืนยันกฎและชื่ออาการ |
