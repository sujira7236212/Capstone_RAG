# แผน integrate RAG feedback เข้า MU-Capstone-Application

**สถานะ:** กำลังทำ · เขียนเมื่อ 2026-10-25 · ความคืบหน้าดู §8
**branch:** RAG_SYSTEM `app-integration` (แตกจาก `rule-change-v6`) · แอป `integrate-rag-system` (user ยืนยันว่าใช้ branch ได้)
**ที่มา:** ตรวจ `~/Documents/MU-Capstone-Application` (README, CLAUDE.md, CONTEXT.md, `docs/HANDOVER.md` §3, ADR-0007, `docs/DEPLOY.md`, `lib/analysis/`, `lib/save-and-analyse.ts`, `lib/set.ts`, migration `knowledge_base`) เทียบกับ pipeline ใน repo นี้ (`test_rag_compare.py`, `ingest.py`, `embedding_config.py`, `error_taxonomy.py`, `mock_data/build_mock_sessions.py`)
**แทนที่:** `docs/integration_plan.md` ที่ [`future_user_health_profile.md`](future_user_health_profile.md) อ้างถึง (ไฟล์นั้นไม่มีอยู่จริง)

---

## 0. สรุปคำตอบ 3 ข้อ

1. **integrate ยังไง และทำที่ repo ไหน:** ตัวระบบ RAG + feedback ทั้งหมดอยู่ที่ **RAG_SYSTEM (repo นี้)** โดยห่อเป็น Python service (`POST /feedback`) ที่รับ `FeedbackInput` ของแอปแล้วตอบ `{ feedback }` · ฝั่ง **MU-Capstone-Application** แก้แค่ไฟล์เดียวคือ `lib/analysis/feedback.ts` ให้เป็น HTTP client และแก้ test, env, เอกสาร, migration ของตาราง KB · เหตุผล: CLAUDE.md ของแอปห้ามเขียน LLM call / RAG / vector search ในแอป และ ADR-0007 (2026-09-30) ตัดสินแล้วว่า feedback เป็น Python service ที่แอปเรียกผ่าน localhost · ขั้นตอนอยู่ §4
2. **ประวัติบาดเจ็บ/โรคประจำตัว แก้ที่ repo นี้ได้ไหม:** ได้เกือบทั้งหมด (query, KB, prompt, safety gate อยู่ใน service) · แอปส่ง `profile.medical_history` (free text, บังคับกรอก, "none" ได้) มาให้ตั้งแต่วันนี้แล้ว · **ไม่ขวางการ integrate** ถ้าออกแบบ contract ให้เพิ่ม field แบบ optional ได้ · ที่ต้องแตะแอปคือถ้าอยากได้ข้อมูลแบบมีโครงสร้าง (รหัสโรค, ข้างที่บาดเจ็บ, สถานะ) · และมีข้อเท็จจริงสำคัญ: CLAUDE.md ของแอปถือว่า medical history เป็น invariant ("It feeds the LLM so advice is safe") ดังนั้นขั้นต่ำต้องทำตั้งแต่ integrate รอบแรก · รายละเอียด §6
3. **หลัง integrate ถ้าต้องแก้ curate / ingest / prompt / RAG:** แก้ที่ RAG_SYSTEM ทั้งหมด → eval ที่นี่ → deploy service ใหม่ · แอปไม่ต้องแก้ ยกเว้นเปลี่ยน contract (input/output) · ตารางว่าแก้อะไรที่ไหนอยู่ §7

---

## 1. สิ่งที่แอปมีอยู่แล้ว (จากการตรวจ)

| เรื่อง | ในแอป | ไฟล์ |
|---|---|---|
| จุดเสียบ | `writeFeedback(input: FeedbackInput): Promise<FeedbackOutput>` ตอนนี้เป็น stub (รอ 1.5 s แล้วต่อข้อความจาก input + quote medical history) | `lib/analysis/feedback.ts` |
| contract | `FeedbackInput = { profile, exercise: { id, name, rules }, workout: { target_reps, target_sets, rest_seconds, earlier_sets }, set: SetSummary & { attempts }, history }` · `FeedbackOutput = { feedback: string }` · `HISTORY_WORKOUTS = 5` | `lib/analysis/contracts.ts` |
| ผู้เรียก | `analyseSet` บน Next.js server หลัง similarity · ส่ง similarity มาด้วยถ้าสำเร็จ (ไม่สำเร็จ = null) · เขียนผลลง `sets.llm_feedback` | `lib/save-and-analyse.ts` |
| attempt | `outcome` = `correct` / `incorrect` / `abandoned` · `violations[]` = `{ rule, message, priority, scope, state, value, threshold }` · `state` = engine state (ตัวเล็ก) ของ frame แรกที่กฎ fire · `similarity` 6 ค่า (`overall` + 5 region) | `lib/set.ts`, ADR-0003 |
| output ที่แอปคาด | ภาษาอังกฤษ plain text "a few short paragraphs" · **ไม่ render markdown** · ขึ้นบรรทัดใหม่เห็นแค่หน้า detail · History โชว์ 4 บรรทัดแรก · ความยาวไม่จำกัดแต่ "keeping it short is up to the component" | HANDOVER §3 Output |
| ตอนล้ม | throw `Error` ข้อความอ่านได้ → หน้าจอโชว์ "Feedback failed:" + ปุ่ม Retry (ไม่ score similarity ซ้ำ) · set ถูก save ไปก่อนแล้วเสมอ | HANDOVER §3 |
| ผู้ใช้รอ | ผู้ใช้รอที่หน้า set-complete · ถ้า rest timer เริ่ม set ต่อไปก่อน ข้อความยังลงที่ set เดิม | HANDOVER §3 |
| KB | ตาราง `knowledge_base (id, exercise_id, content, embedding extensions.vector untyped, created_at)` ว่าง · ไม่มีสิทธิ์ผ่าน API · component ต่อ DB ตรง · ตั้ง dimension + hnsw ตอน integrate | migration `20260910155350_knowledge_base.sql` |
| deploy | Google Cloud VM: Next.js + Supabase self-hosted + Python service 2 ตัว (similarity, feedback) คุยกันทาง localhost · ยังไม่เคยซ้อม | `docs/DEPLOY.md` |
| กติกาทีม | ทำบน `main` ไม่สร้าง branch · ไม่เปิด PR · ห้าม em dash ในไฟล์ที่เขียนในแอป · เขียน session log `docs/sessions/YYYY-MM-DD.md` · เปลี่ยน contract ต้องแก้ ADR-0007 และบอก Vern กับ Punnapat | CLAUDE.md, HANDOVER |

**สิ่งที่ตรงกันอยู่แล้ว (ไม่ต้องแปลง):**
- `exercise.id` ของแอป (`squat`, `push-up`, `lunge`, `bicep-curl`) = `exercise_id` ใน KB และ `error_taxonomy.py`
- `violations[].rule` ของแอป = key 12 ตัวใน `error_taxonomy.py` ตรงทุกตัว (`partial_squat`, `knee_valgus`, `knee_varus`, `rounded_back`, `hip_sag_or_pike`, `partial_pushup`, `shallow_lunge`, `excessive_front_knee_flexion`, `forward_trunk_lean`, `straight_back_leg`, `elbow_flare`, `partial_curl`) ตามสัญญาที่ตกลงไว้ 2026-10-02 (error_type = key เป๊ะ)

## 2. ช่องว่างระหว่างสองระบบ

| เรื่อง | RAG_SYSTEM ตอนนี้ | แอป | ต้องทำ |
|---|---|---|---|
| รูปแบบ input | mock session: `summary`, `reps_detail[{rep_no, status, errors[{error_type, state_occurred}], similarity_scores_percent}]`, `historical_comparison` | `FeedbackInput` (§1) | adapter ใน service (§4 A2) |
| สถานะ attempt | `completed` / `abort` · abort ที่มี error นับเป็น `incorrect_reps` | `correct` / `incorrect` / `abandoned` · `totals` แยก `abandoned_attempts` ออกมา | **ตัดสิน D3** |
| state | `state_occurred` ตัวใหญ่ · ถูกตัดออกก่อนส่ง LLM (`HELD_BACK_FIELDS`) | `violations[].state` ตัวเล็ก | map ได้ · คงการตัดออกไว้จนกว่าจะทำ checkpoint แยก · คำถาม §8.1 ข้อ 7 ใน `t3_curation_status.md` ตอบได้จาก `lib/set.ts` + ADR-0003 แล้ว ไม่ต้องรอระบบ 1 |
| ประวัติ | `historical_comparison` = session ก่อนหน้า 1 ครั้ง พร้อม `previous_common_errors` | `history` ≤ 5 workout + `earlier_sets` ของ workout นี้ · **เป็น summary ไม่มี violation** | **ตัดสิน D4** (`previous_common_errors` สร้างจากข้อมูลที่แอปส่งไม่ได้) |
| repair set | ไม่รู้จัก | `kind: "repair"` + set เดิมอยู่ใน `earlier_sets` เลข `set_no` เดียวกัน (REQUIREMENTS 4.5 อยากให้บอกว่ารอบแรกผิดอะไร) | prompt v15 + D4 |
| output | markdown, 5 bullet ต่อ error + plan · ยาว | plain text สั้น ไม่ render markdown | **ตัดสิน D2** + prompt v15 |
| medical history | ไม่ใช้ | บังคับกรอก · invariant ของแอป | prompt v15 ขั้นต่ำ (§6 ระดับ 1) |
| ที่เก็บ KB | ตาราง langchain (`langchain_pg_collection`, `langchain_pg_embedding`, metadata JSONB: `exercise_id`, `item_kind`, `fault_tags`, `source`) ใน Docker `pgvector-db` localhost:5432 | ตาราง `knowledge_base` ใน Postgres ของ Supabase | **ตัดสิน D1** |
| LLM | `gemini-3.5-flash-lite` (Google ปิดตระกูล 3.5 แล้ว รุ่นต่ำสุดคือ 3.6 ตาม `t3_curation_status.md` §5.2) | ไม่สนใจว่าใช้อะไร | **ตัดสิน D5** |
| การรัน | สคริปต์ batch · `sleep 15` หลังทุก call · retry 429 รอ 45 s | ผู้ใช้รออยู่หน้าจอ | service ตัด sleep · timeout ชัด · ล้มแล้ว throw ให้แอปโชว์ Retry |
| ที่อยู่ API key | `.env` ของ repo นี้ | "lives with whichever process calls the model" | อยู่ใน env ของ service เท่านั้น ไม่เข้า Next.js |

## 3. ทำที่ repo ไหน

| repo | ทำอะไร | เหตุผล |
|---|---|---|
| **RAG_SYSTEM** | แยกแกน retrieval + prompt + generate ออกเป็น module · adapter · prompt v15 · feedback service (FastAPI) · ingest เข้า DB ของแอป · eval ทั้งหมด | โค้ดที่ eval กับโค้ดที่รันจริงต้องเป็นชุดเดียวกัน ไม่งั้นผล eval ไม่ได้บอกอะไรเกี่ยวกับของจริง · แอปห้ามมี RAG/LLM ในตัว |
| **MU-Capstone-Application** | `lib/analysis/feedback.ts` → HTTP client · `FEEDBACK_URL` ใน `.env.example` · แทน test ของ stub · แก้ e2e ขั้นสุดท้าย · migration ตาราง KB + pgTAP · ADR-0007, HANDOVER §3, DEPLOY ขั้น 9, README, session log · contract change ถ้ามี | เป็นจุดเสียบที่ HANDOVER ออกแบบไว้ให้ owner เปลี่ยนไฟล์เดียว |

ฝั่งแอปต้องทำบน `main` ตามกติกาทีม และคุยกับ Vern ก่อนแตะ contract / migration (ADR-0007: "tell the other two owners")

## 4. แผนทีละขั้น

### Phase A: RAG_SYSTEM (ยังไม่แตะแอป)

**A1. แยกแกนออกจาก `test_rag_compare.py`**
- ย้าย `retrieve_kb_blocks`, `retrieve_kb_context`, ค่าคงที่ของ gate, `SYSTEM_PROMPT`, `model_payload`, การสร้าง chain ไปไว้ใน package เช่น `rag_core/` (`retrieval.py`, `prompt.py`, `generate.py`)
- `test_rag_compare.py`, `eval/*` import จาก `rag_core` · ไม่เปลี่ยนพฤติกรรม
- ตรวจ: รัน `--context-only` บน mock เดิมแล้ว diff กับผลใน `compare_output/strict_v6b/` ต้องเหมือนกันทุก chunk
- ค่าที่ตอนนี้แก้ผ่าน global (`TAG_MODE`, `QUERIES` ฯลฯ) ทำเป็น config object ส่งเข้าไป ไม่ให้ service กับ eval แย่งกันแก้ global

**A2. adapter `FeedbackInput` → session payload**

| `FeedbackInput` | payload ที่ prompt อ่าน |
|---|---|
| `exercise.id`, `exercise.name` | `exercise_id`, `name` |
| `set.attempts[i].attempt_no` | `reps_detail[i].rep_no` |
| `outcome` `correct`/`incorrect` → `completed` · `abandoned` → `abort` | `status` |
| `violations` เรียงตาม `priority` (เลขน้อยมาก่อน) → `{ error_type: rule, state_occurred: state.upper() }` | `errors` (ตัวแรก = priority สูงสุด ตามที่ prompt v14 บอก) |
| `attempts[i].similarity?.overall` (null ได้) | `similarity_scores_percent.overall` |
| `set.totals` | `summary` (ตาม D3) |
| `history` / `workout.earlier_sets` | `historical_comparison` (ตาม D4) |
| `profile.medical_history` | ส่วนใหม่ใน prompt v15 (§6) |
| `profile.display_name` | **ไม่ส่งเข้า LLM** (ไม่จำเป็น และลดข้อมูลส่วนบุคคลที่ออกไปนอกเครื่อง) |

- เก็บ fixture: ทำ set จริง 1 ครั้งต่อท่า แล้วดึง `FeedbackInput` ออกมา (log จาก `analyseSet` ชั่วคราว หรือประกอบจากแถวใน Studio ตาม HANDOVER "Trying a replacement") → `tests/fixtures/feedback_input_<ท่า>.json`
- unit test: adapter บน fixture ทุกท่า + set ที่ similarity เป็น null + repair set + set ที่ไม่มี violation

**A3. prompt v15 สำหรับแอป** (checkpoint generation แยก เทียบกับ baseline v14)
- รูปแบบ output ตาม D2 (ค่าเริ่ม: plain text ไม่มี markdown, ไม่กี่ย่อหน้า, ใจความสำคัญอยู่ 4 บรรทัดแรกเพราะ History ตัดตรงนั้น)
- คำศัพท์ตาม CONTEXT.md ของแอป: attempt, correct rep, abandoned attempt (ไม่ใช่ "abort")
- repair set: บอกว่ารอบแรกผิดอะไรและรอบนี้ดีขึ้นหรือไม่
- medical history ระดับ 1 (§6)
- ตรวจ: generate บน mock ที่แปลงผ่าน adapter + fixture จริง → judge เทียบ v14 ตาม `eval_v6_plan.md` + `eval/eval_generation.py`

**A4. เลือก LLM (D5)** · ตั้งผ่าน env (`FEEDBACK_LLM_MODEL`) ไม่ hard-code · รุ่นที่เลือกต้องผ่าน A3 ก่อน

**A5. feedback service**
- FastAPI: `POST /feedback` (body = `FeedbackInput`, ตอบ `{ feedback, version }`) · `GET /health` (เช็ค DB + collection มีแถว)
- bind `127.0.0.1` เท่านั้น · ไม่มี `sleep` · retry 429 ได้ 1 ครั้งสั้น ๆ · timeout รวม < timeout ของแอป
- ล้ม → HTTP 5xx + ข้อความอ่านได้ (แอปเอาไปโชว์หลัง "Feedback failed:")
- `version` = `{ prompt: "v15", collection: "kb_gemini_curated_v6b", llm: "...", commit: "<git sha>" }` ไว้ตามรอยว่า feedback แต่ละอันมาจากเวอร์ชันไหน
- log: เวลา, version, metrics ของ retrieval · **ไม่ log medical history / profile**
- config ทั้งหมดผ่าน env: `DATABASE_URL`, `KB_COLLECTION`, `GOOGLE_API_KEY`, `FEEDBACK_LLM_MODEL`
- `service/requirements.txt` แยกเฉพาะที่ service ใช้ (ไม่ต้องลง curator, PDF parser บน VM)

**A6. ที่เก็บ KB (D1)** → ingest เข้า Postgres ของ Supabase local (`postgresql://postgres:postgres@127.0.0.1:54322/postgres`) แล้ว `/health` ต้องผ่าน

### Phase B: MU-Capstone-Application (บน `main`, คุยกับ Vern ก่อน)

**B1. contract (ถ้า D2/D3/D4 ต้องเปลี่ยน)** แก้ `lib/analysis/contracts.ts` + ADR-0007 หัวข้อ "Decided <วันที่>" + บอก Vern และ Punnapat · ตัวที่น่าจะต้องเพิ่ม:
- `SetSummary.violation_counts: Record<string, number>` (rule → จำนวน attempt ที่โดน) สำหรับ D4
- `FeedbackOutput.version?` และคอลัมน์ `sets.feedback_version` (แบบเดียวกับ `engine_version`) ถ้าอยากตามรอยตอน evaluation

**B2. แทน stub** `lib/analysis/feedback.ts` (ตามแบบที่ HANDOVER §2 ให้ไว้กับ similarity):

```ts
// Sujira's feedback service (ADR-0007): Python beside the app, reached over localhost.
import type { FeedbackInput, FeedbackOutput } from "./contracts.ts";

const TIMEOUT_MS = 60_000;

export async function writeFeedback(input: FeedbackInput): Promise<FeedbackOutput> {
  const url = process.env.FEEDBACK_URL;
  if (!url) throw new Error("FEEDBACK_URL is not set");
  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  if (!res.ok) throw new Error(`the feedback service answered ${res.status}: ${await res.text()}`);
  return (await res.json()) as FeedbackOutput;
}
```

**B3. env + test**
- `.env.example`: `FEEDBACK_URL=http://127.0.0.1:<port>/feedback` (ไม่มี `NEXT_PUBLIC_`)
- `lib/analysis/stubs.test.ts`: แทน test ของ stub feedback ด้วย test ของ client (mock `fetch`: ตอบ 200, ตอบ 500, timeout)
- `e2e/workout.spec.ts` ขั้นสุดท้ายคาดว่าจะเห็น medical history ตรงตัวอักษร → เปลี่ยนเป็นสิ่งที่ service รับประกันได้ (เช่น มีข้อความ feedback ไม่ว่าง และไม่ขึ้น "Feedback failed") · test นี้ skip อยู่จนกว่าจะมีคลิปจริง

**B4. migration ตาราง KB (ตาม D1)** + pgTAP แบบเดียวกับ `supabase/tests/knowledge_base.test.sql` ว่า `anon`/`authenticated` เข้าไม่ได้ · จากนั้น `npm run db:reset`, `npm run db:types`, `npm run test:db`, `npx supabase db advisors`

**B5. เอกสาร** HANDOVER §3 (ไม่ใช่ stub แล้ว, รันยังไง) · ADR-0007 · DEPLOY ขั้น 9 · README "Status" · `docs/sessions/<วันที่>.md` · ห้าม em dash

### Phase C: ทดสอบรวมบนเครื่อง

1. `npx supabase start` → ingest เข้า 54322 → รัน service → `npm run dev`
2. ทำ set จริง ท่าละ 1 set: ดู `sets.llm_feedback` ใน Studio, หน้า set-complete, summary, History 4 บรรทัดแรก, หน้า detail
3. ปิด service แล้วทำ set → ต้องเห็น "Feedback failed:" + Retry · เปิด service แล้วกด Retry → ได้ข้อความ, similarity ไม่ถูกคิดซ้ำ
4. วัดเวลาที่ผู้ใช้รอ (เป้า: น้อยกว่าเวลาพักขั้นต่ำที่ตั้งได้ ซึ่ง default 60 s)
5. ฝั่งแอป: `npm run lint`, `npx tsc --noEmit`, `npm run test:unit`, `npm run test:db`, `npm run test:e2e`
6. ปิด stack ทุกครั้ง (`npx supabase stop`) ตามกติกาแอป

### Phase D: deploy บน VM (ต่อจาก `docs/DEPLOY.md` ขั้น 9)

- clone repo นี้บน VM ที่ commit/tag ที่ผ่าน Phase C · venv + `service/requirements.txt`
- systemd unit ของ service (restart อัตโนมัติ, env file สิทธิ์ 600)
- ingest เข้า Postgres ของ VM ผ่าน SSH tunnel (ไม่เปิด port DB ออกเน็ต) หรือ dump แถว KB จากเครื่องแล้ว restore
- service ต่อ DB ด้วย role อ่านอย่างเดียวบนตาราง KB · ingest ใช้ role ที่เขียนได้
- `FEEDBACK_URL` ใน env ของ Next.js · `curl /health` หลัง deploy

## 5. เรื่องที่ต้องตัดสินก่อนเริ่ม

| # | เรื่อง | ทางเลือก | แนะนำ |
|---|---|---|---|
| D1 | ที่เก็บ KB | **A.** ใช้ตาราง langchain เดิม แต่ย้ายไปอยู่ใน Postgres ของ Supabase · **B.** ใช้ตาราง `knowledge_base` ของแอป (เพิ่ม `metadata jsonb` หรือคอลัมน์ `item_kind`, `fault_tags`, `source`, `collection`) แล้วเขียน retrieval เป็น SQL เอง · **C.** คง Docker `pgvector-db` แยกไว้บน VM | **A** สำหรับรอบแรก: โค้ด retrieval เหมือนตอน eval ทุกบรรทัด · แก้ ADR-0007 ว่า `knowledge_base` ไม่ถูกใช้ (หรือลบ) · ข้อควรระวัง: (1) langchain สร้างตารางใน `public` ซึ่ง Supabase ให้สิทธิ์ `anon`/`authenticated` อัตโนมัติ = **อ่าน KB ผ่าน API ได้** ต้องให้ migration ของแอปสร้างตารางไว้ก่อน + revoke + เปิด RLS แบบ `knowledge_base` (หรือใช้ schema แยกถ้า `PGVector` รองรับ ต้องลองก่อน) (2) `npm run db:reset` ล้างข้อมูล ต้อง ingest ใหม่ทุกครั้ง → ทำสคริปต์ re-ingest · B ทำทีหลังได้ถ้ารายงานต้องใช้ตาราง `knowledge_base` แต่ต้องพิสูจน์ด้วย golden retrieval ว่าได้ chunk เดิม |
| D2 | รูปแบบ output | plain text สั้นตาม contract ตอนนี้ · หรือให้แอป render markdown (งาน UI ของ Vern) | plain text ก่อน ไม่ต้องแก้แอป |
| D3 | นับ attempt | ใช้ความหมายของแอป (abandoned แยก, incorrect = ทำครบแต่ผิด) · หรือแปลงเป็นแบบ mock (abort มี error = incorrect) | **ความหมายของแอป** เพราะผู้ใช้เห็นตัวเลขจากแอปบนหน้าจอเดียวกัน ถ้า feedback นับต่างกันจะขัดกันเอง → prompt v15 |
| D4 | ข้อมูลเทียบ session ก่อน | เพิ่ม `violation_counts` ใน `SetSummary` (contract change) · หรือเทียบแค่ตัวเลข totals/similarity ไม่บอกว่า error ไหนหายไป | เพิ่ม `violation_counts` (ข้อมูลอยู่ใน `sets.attempts` แล้ว คำนวณใน `analyseSet` ได้) |
| D5 | LLM | รุ่น Gemini ที่ยังให้บริการ · Groq (มี `eval/generate_groq.py`) | ตัดสินจาก A3 · ต้องมี SLA/quota พอสำหรับช่วง evaluation |
| D6 | PDPA | consent ข้อ 3 ของแอป ("storing the profile including medical history") ไม่ได้บอกว่าส่งให้ผู้ให้บริการ LLM ภายนอก | ถามทีม/อาจารย์ · ถ้าต้องแก้ข้อความ = bump `CONSENT_VERSION` ใน `lib/consent.ts` (ผู้ใช้ต้อง consent ใหม่) |

## 6. ข้อ 2: ประวัติบาดเจ็บ / โรคประจำตัว

**แก้ที่ repo นี้ได้ไหม:** ได้ · 4 จุดใน [`future_user_health_profile.md`](future_user_health_profile.md) §4 (retrieval query ต่อ condition, KB กลุ่ม contraindication/modification, prompt section, safety gate แบบ deterministic) อยู่ใน service ทั้งหมด · ส่วนที่ไม่ได้อยู่ที่นี่คือ **ข้อมูลผู้ใช้** (data model ใน §3 ของไฟล์นั้น) ซึ่งต้องอยู่ใน Postgres ของแอป ไม่ใช่ repo นี้

**แบ่งเป็น 2 ระดับ:**

| ระดับ | ทำเมื่อไหร่ | input | แก้ที่ RAG_SYSTEM | แก้ที่แอป |
|---|---|---|---|---|
| 1. ขั้นต่ำ | **ตอน integrate** (invariant ของแอป) | `profile.medical_history` free text ที่มีอยู่แล้ว | prompt v15: section "User health notes" + กติกา (ไม่วินิจฉัย, ไม่แนะนำสิ่งที่ขัดกับข้อมูลนี้, ถ้าเกี่ยวกับข้อต่อที่ท่านี้ใช้ให้แนะนำปรึกษาผู้เชี่ยวชาญ, "none" = ไม่พูดถึง) · test ด้วย fixture ที่มีประวัติ เช่น "broken left leg 2024" (ตัวอย่างใน REQUIREMENTS) | ไม่มี |
| 2. เต็ม | เฟสถัดไป หลัง retrieval quality นิ่ง | ข้อมูลมีโครงสร้าง: condition code, injury (ส่วน, ข้าง, สถานะ), mobility limitation | taxonomy ของ condition · `likely_physical_causes` ต่อ fault · query สายที่ 2 · curate เอกสาร clinical (`item_kind` ใหม่) → collection ใหม่ · safety gate ก่อน/หลัง LLM · eval ชุดใหม่ (ต้องมีผู้เชี่ยวชาญอนุมัติ rule) | migration (คอลัมน์ใหม่ใน `profiles` หรือตาราง `user_health_profile` + RLS + pgTAP) · ฟอร์ม profile/Settings · ข้อความ consent + `CONSENT_VERSION` · field ใหม่ใน `FeedbackInput` + ADR-0007 |

**ทางลัดของระดับ 2 ที่ไม่ต้องแก้แอป:** ให้ service แปลง free text → condition code เอง (LLM extraction หรือ keyword) · ข้อดีคือแอปไม่ต้องแก้เลย · ข้อเสียคือแปลงพลาดได้ ดังนั้น safety gate ต้องตั้งค่าเริ่มเป็นฝั่งปลอดภัย (อ่านไม่ออก/ไม่รู้จัก = เตือนทั่วไป + แนะนำปรึกษา ไม่ใช่ปล่อยผ่าน) · ใช้เป็นขั้นกลางได้

**มีผลต่อการ integrate ไหม:** ไม่ขวาง ถ้าทำ 3 อย่างนี้ตั้งแต่รอบแรก:
1. adapter อ่าน `medical_history` ตั้งแต่วันแรก (ระดับ 1)
2. field ใหม่ในอนาคตเพิ่มแบบ **optional** (`health?: {...}`) service รุ่นใหม่อ่านได้ทั้ง input แบบเก่าและใหม่ แอปกับ service จึง deploy แยกกันได้
3. service ส่ง `version` กลับมา เพื่อให้รู้ว่า feedback ไหนเขียนก่อน/หลังมีระบบสุขภาพ

สิ่งที่จะบังคับให้แอปต้องแก้แน่นอน: อยากได้ข้อมูลแบบมีโครงสร้างจากผู้ใช้ · ข้อความ consent เปลี่ยน · อยากให้ UI แสดง "ควรปรึกษาผู้เชี่ยวชาญ" เป็นกล่องแยก (ต้องมี field แยกใน output)

## 7. ข้อ 3: หลัง integrate แล้ว ถ้าต้องแก้

หลักการ:
- **ทุกอย่างที่เป็น "สมอง" ของ feedback แก้ที่ RAG_SYSTEM** → eval ที่นี่ → deploy service ใหม่ · แอปไม่รู้ตัว
- **KB แต่ละรุ่นเป็น collection ใหม่เสมอ** (ไม่เติมทับ ตามกติกาเดิมใน `t3_curation_status.md` §8.3) · สลับรุ่นด้วย env `KB_COLLECTION` · ถอยกลับ = ชี้ชื่อเดิม
- **แอปต้องแก้ก็ต่อเมื่อ contract เปลี่ยน** (ต้องการข้อมูลใหม่จากแอป หรือรูปแบบ output ใหม่)

| สิ่งที่แก้ | แก้ที่ | ตรวจก่อน deploy | deploy | แอปต้องแก้? |
|---|---|---|---|---|
| curate เอกสารเพิ่ม | RAG_SYSTEM `data_pipeline/curator.py` + batch ใหม่ใน `curation_batches_v6.json` | `tag_coverage.py` · grep `FOLDER MISMATCH` | ingest เป็น collection ใหม่ (เช่น `kb_gemini_curated_v6c`) เข้า DB ของ VM → `--context-only` + golden retrieval → เปลี่ยน `KB_COLLECTION` → restart service | ไม่ |
| แก้ ingest (chunking, metadata) | RAG_SYSTEM `ingest.py` | `eval/eval_retrieval.py` golden set บน collection ใหม่ | เหมือนข้างบน | ไม่ (ถ้า D1 = B และเปลี่ยนคอลัมน์ ต้องมี migration ในแอป) |
| เปลี่ยน embedding model | RAG_SYSTEM `embedding_config.py` | ingest ใหม่ทั้งหมด + sweep gate ใหม่ (`RELATIVE_MARGIN`, `ABS_DISTANCE_CAP` ผูกกับ model) | collection ใหม่ + deploy service | ไม่ (D1 = A) · มี migration ถ้า D1 = B และ dimension เปลี่ยน |
| แก้ prompt | RAG_SYSTEM `rag_core/prompt.py` (bump เลข version) | generate บน mock + fixture จริง → judge เทียบรุ่นก่อน | `git pull` บน VM ที่ tag ใหม่ → restart | ไม่ (ยกเว้นเปลี่ยนรูปแบบ output → D2) |
| แก้ retrieval (gate, TAG_MODE, query profile, reranker) | RAG_SYSTEM `rag_core/retrieval.py`, `error_taxonomy.py` | golden retrieval + `--context-only` diff | เหมือน prompt | ไม่ |
| เปลี่ยน LLM | env `FEEDBACK_LLM_MODEL` | A3 รอบใหม่ | แก้ env → restart | ไม่ |
| แอปเพิ่ม/เปลี่ยนกฎ (Vern export `rule_logic_<sha>`) | ถ้าเป็นกฎใหม่: RAG_SYSTEM `error_taxonomy.py` + rule card + curate | key ใหม่ต้อง resolve ได้ (ไม่งั้นตกไปใช้ข้อความดิบเป็น query) | ตาม curate | ไม่ แต่ **ต้องรู้ล่วงหน้า** → ขอให้ Vern แจ้งเมื่อชื่อกฎเปลี่ยน |
| ต้องการข้อมูลใหม่จากแอป (เช่น ค่ามุมต่อ rep, health) | ทั้งสอง repo | adapter test + ADR-0007 | แอปก่อน (field optional) แล้ว service | ใช่ |

**ตามรอยใน evaluation:** ถ้าทำ B1 (`sets.feedback_version`) จะรู้ว่าแต่ละ set ได้ feedback จาก prompt/collection/LLM รุ่นไหน · ถ้าไม่ทำ ต้องจดวันที่ deploy ทุกครั้งแล้วเทียบกับ `created_at` เอง

**ใช้ข้อมูลจริงเป็นชุด eval:** set จริงที่เก็บในแอปแปลงเป็น `FeedbackInput` fixture ได้ (§4 A2) → เพิ่มลงชุด dev ตามกติกา `eval_v6_plan.md` (แบ่ง dev/test ก่อนดูผล)

## 8. checklist

**ที่ตัดสินแล้ว (user, 2026-10-25):** D1 = A · D3 = ความหมายของแอป · D5 = `gemini-3.6-flash` ผ่าน env ไปก่อน · similarity ใช้รูปแบบ `feedback_input_example.json` แต่ไม่แก้ type ในแอป (service รับทั้งสองแบบ) · integrate ด้วย prompt v14 ก่อน แล้วค่อยทำ v15 · D2, D4, D6 เลื่อนไปก่อน (D6 ต้องเสร็จก่อนมีผู้ใช้จริง) · ห้ามเรียก API ที่เสียเงินโดยไม่ถามก่อน

- [ ] ตัดสิน D2, D4, D6
- [x] A1 แยก `rag_core/` (`af3d262`) · context v6b strict lunge/push-up ตรงกับ `compare_output/strict_v6b/` ทุก byte · eval_retrieval ก่อน/หลังตรงกัน 574 บรรทัด · prompt sha1 เดิม
- [~] A2 adapter `rag_core/app_input.py` + test (`d31f371`) · ใช้ example + fixture รูปแบบปัจจุบันของแอป · **ยังขาด fixture จาก set จริงทุกท่า** (ทำตอน Phase C) · `medical_history` ถูกเก็บเป็น `health_notes` แต่ไม่ส่งให้ LLM จนกว่า v15 + D6
- [ ] A3 prompt v15 + judge เทียบ v14
- [~] A4 LLM: `gemini-3.6-flash` + `thinking_level=low` (ค่าเริ่มของโมเดลตอบ v14 ไม่ทันใน 34 s · low ตอบใน 22 s, ทดสอบจริง 1 ครั้ง) · ยังไม่ได้ผ่าน A3
- [x] A5 service `service/` (`d5f26dc`) · `/health` ผ่านกับ v6b ใน Docker (2,197 แถว) · test แบบ mock 20+ กรณี
- [ ] A6 / B4 ตาราง KB ใน Supabase + revoke + pgTAP · ข้อควรรู้: PGVector สร้างตาราง/collection เองตอนเปิด ต้องให้ migration สร้างก่อน และ role อ่านอย่างเดียวบน VM จะเปิดไม่ได้ถ้าไม่ปิดการสร้าง
- [ ] B1 contract change (ถ้ามี) + ADR-0007
- [x] B2–B3 `feedback.ts` เป็น client (ไม่ตั้ง `FEEDBACK_URL` = ใช้ stub เดิม), `.env.example`, `feedback.test.ts` 6 กรณี · unit 92 ผ่าน, tsc, eslint ผ่าน · e2e ยัง skip ตามเดิม
- [~] B5 HANDOVER §3 + `docs/sessions/2026-10-25.md` · ยังไม่แตะ ADR-0007, DEPLOY ขั้น 9, README
- [ ] C ทดสอบรวม (รวมกรณี service ล้ม) · **มีค่าใช้จ่าย ต้องถาม user ก่อน**
- [ ] D deploy VM
