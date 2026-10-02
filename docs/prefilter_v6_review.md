# T3a — รายการคัดเอกสารออกทั้งไฟล์ (ให้ user ตรวจ)

> 2026-10-02 · ผู้คัด: Claude · ไฟล์ผล: [`data_pipeline/prefilter_v6.json`](../data_pipeline/prefilter_v6.json) · เกณฑ์: [rule_change_v6_plan.md §T3a](rule_change_v6_plan.md)
> **ตรวจรายการ drop (§2) และ keep ที่ไม่แน่ใจ (§3)** ถ้าจะกลับคำตัดสิน แก้ `decision` ใน JSON ได้เลย ไม่ได้ลบหรือย้ายไฟล์ใน `data/`

## 1. สรุป

| ท่า | หน่วยทั้งหมด | keep | drop | pending |
|---|---|---|---|---|
| bicep-curl | 24 (PDF 20 · URL 4) | 15 | 9 | — |
| lunge | 31 (PDF 28 · URL 3) | 22 | 9 | — |
| push-up | 18 (PDF 12 · URL 6) | 10 | 8 | — |
| squat | 23 (PDF 19 · URL 4) | 22 | 1 | — |
| general | 6 (PDF) | 2 | 4 (P5) | — |
| **รวม** | **102** (PDF 85 · URL 17) | **71** | **31** (27 + P5 4) | **0** |

- อ่าน: ชื่อเรื่อง, abstract, สารบัญ/bookmark, 2 หน้าแรก และค้นคำสำคัญทั้งไฟล์เมื่อยังตัดสินไม่ได้ (ฟิลด์ `read` ของแต่ละหน่วยบอกว่าอ่านส่วนไหน) · URL ดึงด้วย trafilatura แบบเดียวกับ curator ได้ครบทั้ง 17 ตัว
- ไม่ได้เปิด `curated_data_v5/` และไม่ได้เรียก API ที่เสียเงิน
- เหตุผลที่ drop ส่วนใหญ่มี 3 กลุ่ม: (ก) วัดแค่ EMG/แรง/ผลของโปรแกรม ไม่พูดถึงท่าทาง (ข) ตัวแปรที่ศึกษาไม่ใช่กฎของเรา เช่น ความกว้างมือ มุมเท้า (ค) เป็นงานวิธีวัด/โมเดล หรือผลทางคลินิก

## 2. รายการ drop (27)

### bicep-curl (9)
| id | ไฟล์ | เหตุผล |
|---|---|---|
| u000 | A Comparison of Muscle Unit Activation … 40, 60, 80 and 100% of 1RM | หน้า proceedings · abstract ของ curl วัดแค่ EMG ตาม %1RM · abstract อื่นในหน้าไม่เกี่ยว |
| u004 | Biceps Disorder Rehabilitation for the Athlete | ลำดับท่ากายภาพ 11 ท่าส่วนใหญ่ไม่ใช่ curl (pull-up, Xco, air punch) มีแค่ inclined curl |
| u006 | Core Muscle Activation During Unstable Bicep Curl (water-filled tube) | abstract เรื่องอุปกรณ์ไม่เสถียรกับ EMG แกนกลางลำตัว · หน้ามี abstract อื่นไม่เกี่ยว |
| u007 | Distinct muscle growth … preacher and incline biceps curls | ผล hypertrophy ของท่าดัดแปลง 2 ท่า ไม่มีเรื่องท่าผิดของ curl ปกติ |
| u008 | Exertional Rhabdomyolysis … Case Report | รายงานผู้ป่วยกล้ามเนื้อสลาย (ผลทางคลินิก) |
| u010 | … biceps curl on a new machine (eccentric overload, drop setting) | เครื่อง CARE กับดัมเบล: แรง EMG ความล้า · ท่าทางมีแค่เป็นกติกาในการทดสอบ |
| u012 | Unilateral bicep curl hemodynamics (BFR) | ความดันเลือดและชีพจรของ BFR |
| u013 | Neutral vs supinated grip bicep curl (poster) | EMG/แรงบิดบนเครื่อง isokinetic ตามแบบจับ |
| u017 | The Rest-Pause Biceps Curl … Mechanical Responsiveness | โมเดลความเค้น/ความเครียดของกล้ามเนื้อ |

### lunge (9)
| id | ไฟล์ | เหตุผล |
|---|---|---|
| u030 | ACL/Meniscal injury alters patellofemoral kinematics … single-leg lunge | ภาพถ่ายข้อเข่าผู้ป่วย ACL ไม่มีเรื่องความลึก ลำตัว หรือขาหลัง |
| u031 | Altered movement strategy after ACL injury | ประเมินการ lunge ด้วย knee valgus/pelvic drop ซึ่งไม่ใช่กฎของ lunge |
| u033 | Changes in lower limb muscle activity … ankle abduction | EMG ตามมุมเท้า · มุมเท้าไม่ใช่กฎ |
| u035 | VMO/VL EMG Activity Ratio … Partial Lunge | อัตรา EMG ภายใต้แรงต้านทิศต่าง ๆ สำหรับเข่าเจ็บ |
| u036 | Foot Progression Angle and Stance Width … Forward Lunge | EMG ตามมุมเท้าและความกว้างท่ายืน · ความลึก/ลำตัวเป็นแค่ cue คุมการทดลอง |
| u039 | Automatic identification of events during the lunge | งานวิธีแบ่งช่วงการเคลื่อนไหวจากข้อมูล kinematic |
| u040 | Exhaustion of the Gluteus Medius … Knee Adduction Moment (thesis 123 หน้า) | ภาระ KAM/ข้อเข่าเสื่อมเมื่อก้นล้า · KAM ไม่ใช่กฎของ lunge |
| u042 | Muscle injury and pain … (thesis Jönhagen 2005) | เรื่องหลักคือ hamstring บาดเจ็บ วิ่ง นวด · บท lunge คืองานเดียวกับ u043 ที่ keep ไว้แล้ว |
| u046 | Foot Posture, Dorsiflexion ROM … Drop-Landing Task | งานกระโดดลง · lunge มีแค่เป็นชื่อการทดสอบข้อเท้า |

### push-up (8)
| id | ไฟล์ | เหตุผล |
|---|---|---|
| u061 | 10-week suspension and traditional push-up training | ผลของโปรแกรมฝึก 10 สัปดาห์ |
| u062 | A Rigid-Body Pendulum Model for Plyometric Push-Up | โมเดลคำนวณเวลาลอยตัว/กำลัง |
| u063 | Upper Body Muscle Activations … Various Type Of Push-up (abstract) | EMG ตามตำแหน่งมือ · abstract อื่นในหน้าไม่เกี่ยว |
| u064 | Narrow-base vs Shoulder-width Push-up in Gymnast | ผู้ทดสอบ 1 คน · ความกว้างมือไม่ใช่กฎ |
| u065 | Core Muscle Activity during Physical Fitness Exercises (SR 2020) | ตาราง EMG แกนกลางลำตัวของหลายท่า push-up เป็นแค่แถวเดียว |
| u066 | Medial-lateral position of hand … muscle synergy | ความกว้างมือไม่ใช่กฎ |
| u067 | ProQuestDocuments-2026-09-03 | abstract: การหมุนข้อมือ/แขนกับ EMG |
| u068 | Systematic Review of Core Muscle Activity (2013) | EMG กล้ามเนื้อแกนกลางลำตัวชั้นลึก ไม่มีเรื่องท่า push-up |

### squat (1)
| id | ไฟล์ | เหตุผล |
|---|---|---|
| u082 | Effect of hip adductor (Squat) — thesis 134 หน้า | EMG ของ VMO/VL ขณะบีบสะโพกเข้าระหว่างสควอท ไม่มีเรื่องท่าผิด |

## 3. keep ที่ไม่แน่ใจ (10) — ถ้าเห็นว่าควรตัดบอกได้

| id | ไฟล์ | ทำไมยัง keep |
|---|---|---|
| u009 | From Continuous sEMG Signals to Discrete Muscle State Tokens | งานหลักเป็นวิธี sEMG แต่ภาคผนวกนิยาม curl ผิด (งอไหล่มากจนแขนส่วนบนเลื่อนไปหน้า) |
| u014 | Effect of Shoulder Flexion Angles … Isometric Contraction | มุมไหล่กับการทำงานของ biceps เกี่ยวกับตำแหน่งแขนส่วนบนอยู่บ้าง |
| u018 | NASM: 9 Best Arm-Sculpting Exercises (URL) | เป็นเรื่องโปรแกรม hypertrophy มีประโยค full ROM ดีกว่า partial reps |
| u021 | ACE: Building Better Biceps (URL) | เทียบ EMG 8 ท่า มีคำแนะนำของผู้ฝึกบ้าง |
| u043 | Jönhagen 2009 Muscle activation … two lunge exercises | กลไกกล้ามเนื้อของ forward lunge 2 แบบ เนื้อหาท่าทางน้อย |
| u050 | mxn167Sp24 (dissertation AI motion capture) | งาน validation แต่บททบทวนพูดถึงมุมลำตัวและระยะก้าว |
| u071 | Effect of Position on the % Body Mass … Push-up | แรงที่รับตำแหน่งบนเทียบกับล่าง (ศอก ~90°) เกี่ยวกับความลึกทางอ้อม |
| u074 | NASM: Exercise Progressions and Regressions (URL) | การรักษาฟอร์มเมื่อปรับระดับท่า มี push-up regression |
| u100 | Werner2022 Knee Alignment Instructions (knee_valgus/) | งานกระโดดลง ไม่ใช่สควอท แต่ cue เรื่องแนวเข่าใช้ได้ |
| u077 | NASM: Lower Crossed Syndrome (URL) | **เปลี่ยนจาก drop ในรอบตรวจซ้ำ** มีสาเหตุ (นั่งนาน, hip flexor ตึง, ก้น/core อ่อน) และวิธีแก้ (ยืด hip flexor, กระตุ้นก้น, plank แบบเชิงกรานเอียงหลัง) ของหลังแอ่น ซึ่งเป็นส่วน "หลังแอ่น" ของ `hip_sag_or_pike` · แต่ไม่ได้เจาะจง push-up และอาจทำให้ curator ติด tag กว้างเกิน |

## 3.1 ตรวจซ้ำรายการ drop (2026-10-02, user ขอ)

คำถาม: ไฟล์ที่ drop มีเนื้อหาเรื่อง **สาเหตุที่ทำผิด วิธีแก้ หรือวิธีทำท่าที่ถูก** ของแต่ละท่าไหม

วิธี: อ่านข้อความทั้งไฟล์ (ตัดรายการอ้างอิงออก) ดึงทุกประโยคที่มีทั้งคำแนวแนะนำ/สาเหตุ (should, avoid, correct, proper, cue, cause, compensate, maintain, technique, prevent …) และคำเรื่องท่านั้น (เช่น elbow, trunk, depth, hip, plank, valgus) แล้วอ่านทุกประโยคที่ได้ · thesis u040 ข้อความที่ดึงได้คำติดกันเป็นพืด จึงค้นแบบ substring แทน

ผล:
- **เปลี่ยน 1 ไฟล์:** u077 → keep (ดู §3)
- **ยัง drop 27 ไฟล์** — ไม่มีส่วนที่อธิบายสาเหตุหรือวิธีแก้ท่าผิด กรณีที่เจอคำว่าท่าถูกมีแค่ **กติกาในการทดลอง** ไม่ใช่คำแนะนำของผู้เขียนถึงผู้ฝึก และ prompt ของ curator ก็สั่งไม่ให้ใส่ protocol ลง `specific_findings` อยู่แล้ว ("Do not put a study's own methodology/protocol setup … into specific_findings"):
  - u004 (inclined curl ให้แขนส่วนบนตั้งตรง), u008 (ใช้แผ่นล็อกศอกกันศอกแกว่งและให้ ROM ครบ), u010 (ห้ามแอ่นหลัง/งอไหล่ยกน้ำหนัก), u012 (ยืนพิงผนังกันตัวโยก)
  - u031, u036, u040 (lunge: เข่าหน้า ~90°, ลำตัวตั้ง, เข่าหลังไม่แตะพื้น / ลงถึงระดับข้อเท้า)
  - u061 (push-up: หลังตรง, ลึก 90° ถึงนับครั้ง)
- **u008 อ่านทั้งฉบับ (user ขอ):** ไม่มีการบรรยายท่าผิด สาเหตุ หรือวิธีแก้ของ curl · ส่วนที่พูดถึงท่ามีแค่ protocol (ยืนพิงผนัง, แผ่นล็อกศอกให้ ROM ครบและศอกไม่แกว่ง) · ช่วง discussion บอกว่า full ROM ที่แผ่นล็อกบังคับ *อาจทำให้กล้ามเนื้อเสียหายมากขึ้น* ถ้าตัดออกมาเป็น item จะอ่านเหมือนค้านการทำ full ROM ซึ่งตรงข้ามกับ feedback ของ `partial_curl` · อาการ "เหยียดแขนไม่สุด" ในรายงานเป็นอาการบวมจาก rhabdomyolysis หลังออกกำลังกาย ไม่ใช่ท่าผิด → ยัง drop
- **ข้อสังเกต u082:** แนะนำให้ผู้ป่วยเข่าเจ็บสควอทแค่ ~60° ซึ่งขัดกับ feedback ของ `partial_squat` ถ้าเข้า KB จะกลายเป็นข้อมูลที่สนับสนุนการย่อตื้น จึงยัง drop
- ไฟล์ที่เหลือ (u000, u006, u007, u013, u017, u030, u033, u035, u039, u042, u046, u062–u068) ประโยคที่ได้เป็นวิธีการวัด ผล EMG ข้อจำกัดของงาน หรือคำแนะนำเรื่องโปรแกรม/การฟื้นฟูทั่วไป

## 4. ไฟล์ที่ซ้ำกัน — user ลบแล้ว (2026-10-02)

T2 ไม่ได้จับไว้เพราะไบต์ต่างกัน · user ลบฉบับที่ซ้ำออกจาก `data/` แล้ว และเอาออกจาก `prefilter_v6.json` (หน่วยลดจาก 104 เป็น 102)

| เก็บไว้ | ลบแล้ว | หมายเหตุ |
|---|---|---|
| `squat/Altered_Knee_and_Ankle_Kinemat.pdf` (u081) | `squat/knee_depth/Dill2014_AnkleDorsiflexion_SquatKinematics_JAthlTrain.pdf` | Dill et al. 2014 บทความเดียวกัน |
| `push-up/The_Biomechanics_of_the_Push_up.pdf` (u069) | `push-up/The_Biomechanics_of_the_Push_up_jonathan.pdf` | Contreras et al. ฉบับตีพิมพ์ vs accepted manuscript |

## 5. `general/feedback_and_cueing/` (4) — user ตัดสิน 2026-10-02: ใช้ทำ prompt (P5) อย่างเดียว ไม่เข้า KB

ใส่เป็น `drop` ใน `prefilter_v6.json` (เหตุผลขึ้นต้นว่า "used only for prompt design (P5)") · Claude อ่านทั้ง 4 ไฟล์ก่อนตัดสิน:

| ไฟล์ | เรื่องหลัก | เนื้อหาที่ตรงกับกฎ |
|---|---|---|
| Lincoln2023 | ลำดับฝึก movement pattern + cue | น้อย: push-up "rigid, plank-like form" · cue box squat แก้ส้นเท้าลอย (ไม่ใช่กฎ) |
| Neumann2019 | external vs internal focus (แรง, EMG) | ไม่มี |
| Smith2020 | วิธีสอน + ประเภท feedback | น้อยแต่ตรง: มองพื้น → ลำตัวโน้มหน้า ("eyes forward") · เข่าออกเล็กน้อยตอนลุก · curl "elbows at the ribs" |
| Stien2022 | feedback แบบพูด vs เทคโนโลยี ใน back squat | น้อยมาก: ตาราง cue (ดันสองเท้าเท่ากัน, เกร็ง core, เข่าหมุนออกเล็กน้อย) |

เหตุผลที่ไม่ curate: ได้ item ที่ตรงกฎแค่ไม่กี่ประโยค (บาง cue มีในแหล่งอื่นที่ keep แล้ว) แลกกับความเสี่ยงที่คำแนะนำเชิงการสอนจะถูกจัดเข้า pool ของท่า

## 6. ข้อความสำหรับรายงาน

ก่อน curate มีขั้นคัดเอกสารทั้งไฟล์โดย LLM (Claude) จาก 102 หน่วย (PDF 85, URL 17) ตัดออก 27 หน่วย ด้วยเกณฑ์ว่าไม่มีเนื้อหาเกี่ยวกับท่าทางของ 4 ท่าที่ใช้กับกฎข้อใดข้อหนึ่งได้ (ไม่แน่ใจให้เก็บ) เหตุผลหลักคือวัดแค่การทำงานของกล้ามเนื้อหรือผลของโปรแกรม (n) ศึกษาตัวแปรที่ไม่ใช่กฎของระบบ (n) และเป็นงานวิธีวัดหรือผลทางคลินิก (n) — เติมตัวเลขหลัง user ตรวจเสร็จ · แยกอีก 4 ไฟล์เรื่องวิธีสอน/feedback ไว้ใช้ออกแบบ prompt ไม่เข้า KB (user ตัดสิน)
