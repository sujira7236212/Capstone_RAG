# Error Type Taxonomy — เปลี่ยน `error_type` จาก "คำสั่งแก้ไข" เป็น "ชื่ออาการที่ผิด"

**สถานะ:** §1–§4 คือประวัติ (2026-09-08) — ชุด code 10 ตัวใน §3 เป็นชุดที่**เดา**ขึ้นก่อนเห็นกฎจริง
**2026-09-11:** ได้ inventory กฎจริงของระบบ 1 แล้ว → `error_taxonomy.py` และ `mock_sessions.json` ถูกจัดใหม่ตาม **§5** (ชุด §3 ถูกแทนที่ทั้งหมด)

---

## 1. ปัญหา

`retrieve_kb_context()` ใน `test_rag_compare.py` เอาค่า `error_type` ไปประกอบเป็น query แล้ว embed ตรง ๆ
ดังนั้น **ถ้อยคำของ `error_type` คือ query ของระบบ RAG โดยตรง** ไม่ใช่แค่ label สำหรับแสดงผล

ตอนนี้ `error_type` ใน mock ปนกัน 2 แบบ:

| แบบ | ตัวอย่าง | ความหมายเชิง embedding |
|---|---|---|
| **คำสั่งแก้ไข (instruction)** | `Keep back straight`, `Knees behind toes`, `Back not straight`, `Not full extension` | ใกล้กับ chunk ที่พูดถึง **ท่าที่ถูก** (`core_principles`) |
| **ชื่ออาการที่ผิด (fault)** | `Heels lifting off ground`, `Using momentum`, `Swinging torso` | ใกล้กับ chunk ที่พูดถึง **ข้อผิดพลาด** (`common_mistakes`) |

แต่ตอนที่มี error ระบบกรองให้เหลือเฉพาะ `item_kind ∈ {mistake, finding}` — คือไปหาใน "โซนของข้อผิดพลาด"
ด้วย query ที่เขียนแบบ "ท่าที่ถูก" จึงไม่มีทางเจอตัวที่ตรงจริง

## 2. หลักฐาน (วัดจริงด้วย all-MiniLM-L6-v2 บน `curated_data/` ทั้ง 2,519 items)

ค่าที่แสดงคือ cosine distance ของ chunk ที่ใกล้ที่สุดในกลุ่ม `mistake`/`finding` (ยิ่งน้อยยิ่งดี; ระบบตัดที่ 0.38)

| `error_type` ปัจจุบัน | distance | chunk ที่ได้ | ชื่ออาการที่ผิด (เสนอ) | distance | chunk ที่ได้ |
|---|---|---|---|---|---|
| `Keep back straight` (squat) | **0.574** | "Forcing a standardized, straight-foot stance…" ❌ ไม่เกี่ยว | `Lumbar flexion (rounded lower back) during the squat` | **0.228** | "Lumbar flexion (butt wink) at the bottom of the squat." ✅ |
| `Back not straight` (lunge) | **0.491** | "Leaning the torso forward or backward" ~ | `Spinal flexion (rounding the back) during the lunge` | **0.034** | "Spinal flexion (rounding the back) during the lunge." ✅ ตรงเป๊ะ |
| `Not full extension` (bicep) | **0.670** | "Failing to start the repetition with the elbow in full extension." (ตรงแต่ระยะไกลเกินเกณฑ์) | `Failing to reach full elbow extension at the bottom of the curl` | **0.296** | chunk เดียวกัน ✅ ผ่านเกณฑ์ |
| `Using momentum` (bicep) | **0.385** | "Using momentum to lift free weights…" (เกือบตกเกณฑ์) | `Using momentum / swinging the body to lift the weight` | **0.156** | "Swinging the body or using momentum to lift the weight." ✅ |
| `Heels lifting off ground` (squat) | **0.069** ✅ | "Heels lifting off the ground during the movement." | *(เป็นชื่ออาการอยู่แล้ว — ไม่ต้องแก้)* | — | — |

**ข้อสรุป:** `error_type` ที่บังเอิญเขียนเป็น "ชื่ออาการ" อยู่แล้ว (`Heels lifting off ground`) ได้ distance 0.069
ส่วนที่เขียนเป็น "คำสั่ง" ได้ 0.49–0.67 คือแย่กว่าประมาณ **7–10 เท่า** — ยืนยันสมมติฐานของคุณเต็ม ๆ

## 3. ตารางแมป (ที่เสนอ)

| exercise | `error_type` เดิม | ชื่ออาการที่ผิด (canonical fault) |
|---|---|---|
| squat | `Keep back straight` | `Lumbar flexion (rounded lower back) during the squat` |
| squat | `Knees behind toes` | `Excessive forward knee translation past the toes` |
| squat | `Heels lifting off ground` | `Heels lifting off the ground during the squat` *(คงเดิม)* |
| lunge | `Back not straight` | `Spinal flexion (rounding the back) during the lunge` |
| lunge | `Front knee past toes` | `Front knee travelling past the toes during the lunge` |
| push-up | `Neck craning forward` | `Cervical protraction (neck craning forward) during the push-up` |
| push-up | `Elbows flaring out` | `Excessive elbow flare (elbows abducting away from the torso)` |
| bicep-curl | `Not full extension` | `Failing to reach full elbow extension at the bottom of the curl` |
| bicep-curl | `Using momentum` | `Using momentum / swinging the body to lift the weight` |
| bicep-curl | `Swinging torso` | `Swinging the torso and hips to assist the curl` |

## 4. ข้อควรระวังเชิงสถาปัตยกรรม (สำคัญกว่าการแก้ mock)

ในระบบจริง `error_type` **ไม่ได้มาจากเรา** — มาจากระบบ 1 (angle threshold) ของอีกทีม
(ดู `docs/integration_plan.md` §4 ข้อ 2: ยังไม่รู้ด้วยซ้ำว่าเป็น enum หรือ free text)

ดังนั้นการแก้เฉพาะ `mock_sessions.json` จะได้ผลแค่ตอนเดโม พอต่อระบบจริงจะพังกลับมาเหมือนเดิม
**สิ่งที่ควรทำคือมี mapping layer ฝั่งเรา:**

```
error_type (code จากทีม 1)  ──► ERROR_TAXONOMY  ──► { retrieval_query, display_th, display_en, phase_hint }
```

- ถ้าทีม 1 ส่ง code ที่รู้จัก → ใช้ `retrieval_query` ที่เรา curate ไว้ (คุณภาพคงที่ ทดสอบซ้ำได้)
- ถ้าส่ง code ที่ไม่รู้จัก → fallback ไปใช้ string ดิบ + log ไว้ให้เติม taxonomy ทีหลัง
- ได้ผลพลอยได้: มีที่เดียวสำหรับเก็บชื่อภาษาไทยที่จะแสดงผู้ใช้ และ mapping ไปยัง `focus_area` / ข้อห้ามด้านสุขภาพ (ดู `docs/future_user_health_profile.md`)

**สถานะ:** ทำแล้วใน [`error_taxonomy.py`](../error_taxonomy.py) (root ของโปรเจกต์ ไม่ใช่ `data_pipeline/` เพราะใช้ตอน query ไม่ใช่ตอนเตรียมข้อมูล)
`retrieve_kb_context()` เรียก `resolve(error_type, exercise_id)` ทุกครั้ง และ log error code ที่ยังไม่มีใน taxonomy ออกมาให้เห็น

---

## 5. กฎจริงของระบบ 1 (2026-09-11) — แทนที่ §3 ทั้งหมด

ที่มา: artifact "คลังชื่ออาการท่าออกกำลังกาย" (`SeniorProject · rule_based/form_rules.py`, expert sources: For Expert.xlsx / For Expert - Non (PT).csv)
ระบบ 1 มี **10 กฎ / 4 ท่า** (3 ชื่ออาการจากผู้เชี่ยวชาญ + 7 จากวรรณกรรมฟิตเนส — หัว artifact เขียน "11 rules" แต่เจ้าของยืนยันว่า 10) — สิ่งที่ยังต้องถามทีมระบบ 1 คือ **string ที่ส่งออกจริงต่อกฎเป็นอะไร** (ชื่อกฎไทย / code / ชื่ออาการอังกฤษ) — `resolve()` รับได้ทั้ง code, `aliases`, และ `query` ไว้รอแล้ว

### 5.1 ตารางกฎ → `error_type` ที่ใช้ใน mock → query ที่ส่งเข้า KB

| exercise | กฎ | `error_type` (เลือก 1 คำ) | คำอื่นใน inventory (`aliases`) | ที่มา | query ใน `error_taxonomy.py` |
|---|---|---|---|---|---|
| squat | มุมของหลัง | `Butt wink` | — | expert | Lumbar flexion (butt wink): posterior pelvic tilt and rounding of the lower back at the bottom of the squat |
| squat | เข่าไม่เลยปลายเท้า | `Knee valgus` | — | expert | Knee valgus: knees caving inward (medial knee displacement) during the squat |
| squat | ความลึกของการย่อ | `Partial squat` | quarter squat | web | Squatting too shallow, thighs not reaching parallel: partial or quarter squat depth |
| push-up | แนวลำตัว | `Hip sag` | sagging hips | expert | Allowing the hips to sag during the push-up |
| push-up | มุมการงอศอก | `Partial range of motion` | half push-up | web | Not lowering deep enough: incomplete elbow flexion, failing to reach 90 degrees during the push-up |
| lunge | มุมลำตัว | `Excessive forward trunk lean` | — | web | Leaning the torso forward, excessive trunk lean during the lunge |
| lunge | มุมเข่าหน้า | `Shallow lunge` | insufficient front knee flexion | web | Shallow lunge: step too short, insufficient front knee flexion, front knee not reaching 90 degrees |
| lunge | มุมเข่าหลัง | `Insufficient back knee flexion` | — | web | Insufficient back knee flexion: rear knee not lowering toward the floor during the lunge |
| bicep-curl | การขยับข้อศอกด้านข้าง | `Elbow flare` | elbow drift | web | Allowing the elbows to flare outward or drift forward away from the body during the curl |
| bicep-curl | การเหยียด/งอศอกไม่สุด | `Partial range of motion` | half rep | web | Failing to achieve complete arm extension at the bottom of the curl and full elbow flexion at the top: partial repetitions with a limited range of motion *(แก้ 2026-09-11 — query เดิม "Partial range of motion: not fully extending or fully flexing the elbow (half rep)…" จัดอันดับ chunk ถูกทั้ง 6 ตัวไว้ใต้ chunk ผิด 4 ตัว ดู kb_quality_assessment §7)* |

`Partial range of motion` ซ้ำ 2 ท่าตาม inventory → `ERROR_TAXONOMY` จึง key ด้วย `(exercise_id, code)` และ `resolve()` ต้องได้ `exercise_id` มาด้วย

### 5.2 code เก่าที่ยังใช้ได้ (`LEGACY_CODES`)

`curated_data/*.json` และ metadata `applies_to_fault` ใน `kb_local_curated_v4` ยังแท็กด้วย code ชุด §3 — 4 ตัวที่ความหมายตรงกับกฎจริงถูกแมปไว้: `keep back straight→butt wink`, `knees behind toes→knee valgus`, `back not straight→excessive forward trunk lean`, `not full extension→bicep-curl/partial range of motion` อีก 6 ตัว (heels lifting, using momentum, swinging torso, neck craning, push-up elbows flaring, front knee past toes) **ไม่มีกฎจริงรองรับ** ถูกตัดออก — tag ของกฎใหม่ 6 ข้อ (knee valgus, partial squat, hip sag, push-up ROM, lunge back knee, bicep elbow flare) จึง**ยังไม่มีใน KB** ถ้าจะใช้ tag เป็นช่องค้นต้อง re-curate

### 5.3 วัดจริง: ชื่ออาการดิบ vs query ที่ขยาย (`python kb_coverage.py` บน `kb_local_curated_v4`)

ผลเต็ม: `compare_output/kb_coverage_v4_rules_raw_vs_expanded.md` — usable = chunk ที่ distance ≤ 0.40, ในวงเล็บคือ best distance

| exercise | fault | raw mistake | raw finding | expanded mistake | expanded finding |
|---|---|---|---|---|---|
| squat | butt wink | 0 (0.601) 🔴 | 0 (0.779) 🔴 | 13 (0.120) | 3 (0.329) |
| squat | knee valgus | 15 (0.218) | 2 (0.277) | 32 (0.154) | 10 (0.307) |
| squat | partial squat | 21 (0.329) *ผิด* | 8 (0.318) | 1 (0.258) | 1 (0.370) |
| push-up | hip sag | 2 (0.222) | 0 (0.682) 🔴 | 2 (0.133) | 1 (0.357) |
| push-up | partial range of motion | 1 (0.354) | 0 (0.592) 🔴 | 3 (0.168) | 4 (0.264) |
| lunge | excessive forward trunk lean | 1 (0.143) | 0 (0.525) 🔴 | 5 (0.256) | 1 (0.338) |
| lunge | shallow lunge | 1 (0.396) | 0 (0.429) 🔴 | 4 (0.304) | 6 (0.306) |
| lunge | insufficient back knee flexion | 6 (0.347) | 0 (0.402) 🔴 | 10 (0.256) | 12 (0.305) |
| bicep-curl | elbow flare | 0 (0.438) 🔴 | 0 (0.499) 🔴 | 9 (0.057) | 0 (0.442) 🔴 |
| bicep-curl | partial range of motion | 1 (0.303) | 0 (0.661) 🔴 | 9 (0.272) | 1 (0.370) |

**สิ่งที่เรียนรู้:**
1. ชื่ออาการดิบ ๆ **ใช้เป็น query ตรง ๆ ไม่ได้** — ศัพท์คลินิกสั้น ๆ ที่ MiniLM ไม่รู้จัก (`Butt wink` 0.601, `Elbow flare` 0.438) หาอะไรไม่เจอเลย; finding ดิบได้ 0 ใน 8/10 กฎ
2. query สั้นมาก**หลอกตัวชี้วัด**: `Partial squat` ได้ "21 usable" แต่ตัวที่ใกล้สุดคือ *"Lifting heels or toes off the ground"* — query 2 คำอยู่ห่างจากทุก chunk ของท่านั้นเท่า ๆ กัน (~0.33–0.40) จึงผ่านเกณฑ์ทั้งที่ไม่เกี่ยว ต้องดู best-hit content ควบคู่กับจำนวนเสมอ
3. query ที่ได้ผลดีที่สุดคือแบบที่**เขียนเหมือน curator เขียน `common_mistakes`** ("Allowing the …", "Failing to …", "Squatting too shallow …") — `Allowing the elbows to flare outward…` ได้ 0.057 ในขณะที่วลีบรรยายเชิงกายวิภาค ("lumbar hyperextension, loss of neutral body line") ได้ 0.406 กับ chunk เดียวกัน
4. ช่องว่างของ KB ที่เหลือเป็นเรื่อง**เนื้อหา** ไม่ใช่ query: push-up `hip sag` มี mistake แค่ 2 ตัวใน KB, bicep `elbow flare` ไม่มี finding เลย, squat `partial squat` มี finding ที่เกี่ยวจริงตัวเดียว (*"Compressive forces in the knee may be higher in a partial squat"*)

### 5.4 ผลผ่าน pipeline จริง (`test_rag_compare.py`, KB v4, temperature 0.7)

- `compare_output/ab_raw_fault.md` — `--raw-query` (ชื่ออาการดิบ, ข้าม taxonomy)
- `compare_output/ab_taxonomy.md` — เส้นทาง production (query ขยาย) — **ผลแรกบน KB v4**

| exercise | error_type | raw: mistake best / kept | taxonomy: mistake best / kept | สิ่งที่เข้า context จริง |
|---|---|---|---|---|
| squat | Butt wink | 0.601 / **0** | 0.120 / 3 | raw ไม่ได้อะไรเลย; taxonomy ได้ butt-wink ตรง 3 แหล่ง + finding "spinal flexion before 120° hip flexion" |
| squat | Partial squat | 0.329 / 3 | 0.258 / 3 | raw: 3 chunk ที่ผ่านคือ *heels lifting / generic stance / progressing too early* ติดป้าย "Partial squat" ทั้งหมด; taxonomy ได้ "Squatting too shallow…" ตรง แต่ยังปล่อย knee-valgus chunk หลุดมาติดป้ายผิด 1 ตัว |
| lunge | Excessive forward trunk lean | 0.143 / 1 | 0.256 / 3 | ทั้งคู่ได้ chunk ตรง; taxonomy ได้เพิ่ม "Leaning the torso forward or backward" + "Spinal flexion" |
| lunge | Insufficient back knee flexion | 0.347 / 3 | 0.256 / 3 | **KB ไม่มี chunk เรื่อง "เข่าหลังงอไม่พอ" เลย** — ทั้งสองโหมดได้แต่ chunk เรื่องเข่าหลัง*ทั่วไป* (rear knee flexing in stride-stance = อาการ*ตรงข้าม*, knee impacting ground, knee rotating outward) แล้ว LLM เอาไปอธิบายเป็นความเสี่ยงของ fault นี้ — coverage "10 usable" ใน §5.3 หลอก เพราะ MiniLM แยก "insufficient flexion" กับ "flexion" ไม่ออก |
| bicep-curl | Elbow flare | 0.438 / 3 | **0.057** / 2 | raw: *"Swinging the elbows"* จาก case report rhabdomyolysis + "Failing to start from full extension" ติดป้าย Elbow flare; taxonomy ได้ chunk ตรงเป๊ะ 2 แหล่ง |
| bicep-curl | Partial range of motion | 0.303 / 1 | 0.272 / 3 | taxonomy ได้ "Failing to start from full elbow extension" ตรง แต่พ่วง "using momentum" / "upper arm not stationary" มาด้วย (0.27–0.47) → LLM รวม momentum เข้าไปในคำอธิบาย Partial ROM |

**สรุปข้อ 2:** ชื่ออาการที่ upstream ส่ง **ต้องผ่าน taxonomy เสมอ** — ส่งดิบ ๆ ได้ context ที่ผิดแต่ติดป้ายว่าถูก ซึ่งแย่กว่าไม่ได้อะไรเลย (LLM เชื่อ header `re: <error>`) ส่วนช่องโหว่ที่เหลืออยู่หลัง taxonomy คือ (a) relative gate +0.20 / mistake cap 0.55 ยังปล่อย chunk ข้างเคียงหลุดมาติดป้ายผิด และ (b) KB ไม่มีเนื้อหาสำหรับ lunge back-knee — ทั้งสองข้อคือรายการแก้รอบถัดไป (ไม่ใช่รอบนี้)

### 5.5 ไฟล์ที่เปลี่ยนรอบนี้
- `mock_data/mock_sessions.json` — error string ทั้งหมดเปลี่ยนเป็นชุด §5.1 (จำนวน rep/score เท่าเดิม); ชุดเดิมเก็บไว้ที่ `mock_data/mock_sessions_legacy_errors.json`
- `test_rag_compare.py` — รับ `--mock / --raw-query / --collection / --out / --skip-no-rag` และพิมพ์ตาราง retrieval metrics ต่อ exercise ในรายงาน
- `kb_coverage.py` — `--query-mode raw|expanded|both`
