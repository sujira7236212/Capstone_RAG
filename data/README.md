# `data/` — เอกสารต้นฉบับของ KB

โฟลเดอร์นี้เก็บเอกสารต้นฉบับ (PDF งานวิจัย, ไฟล์ข้อความ, รายการ URL) ที่ใช้สร้าง KB
`data_pipeline/curator.py` อ่านไฟล์ที่นี่แล้วเขียนผลลง `curated_data_v6/` และ `excluded_from_kb_v6/`
รายละเอียดแต่ละรอบ curate อยู่ใน [`docs/t3_curation_status.md`](../docs/t3_curation_status.md) §0
และผลตรวจรายไฟล์อยู่ใน [`docs/prefilter_v6_review.md`](../docs/prefilter_v6_review.md)

## 1. สถานะของไฟล์ดูจากโฟลเดอร์

ไฟล์ 1 ไฟล์ผ่าน 3 สถานะตามลำดับ ตำแหน่งของไฟล์บอกว่ามันอยู่สถานะไหน

| โฟลเดอร์ | สถานะ | curator ทำอะไรกับมัน |
|---|---|---|
| `data/<ท่า>/…` | **ใหม่** ยังไม่ได้ตรวจ prefilter | อ่านและ curate ตามปกติ |
| `data/checked/<ท่า>/…` | **checked** ตรวจ prefilter แล้ว (มี entry ใน `prefilter_v6.json`) แต่ยังไม่ได้ curate | อ่านได้ **แต่ใช้ id เดิม** `data/<ท่า>/…` (ดู §2) |
| `data/picked/<ท่า>/…` | **picked** curate แล้ว ผลอยู่ใน `curated_data_v6/` | **ไม่อ่านเลย** ข้ามทั้งโฟลเดอร์ |

- **checked** มีทั้งไฟล์ที่ผล prefilter เป็น `keep` (รอเข้า batch รอบถัดไป) และ `drop` (ตัดทิ้ง ไม่ curate)
  ไฟล์ `drop` ยังอยู่ที่นี่เพื่อให้ตามไปดูเหตุผลใน `prefilter_v6.json` ได้ curator ข้ามให้เองเพราะอยู่ใน skip-list
- **picked** คือไฟล์ที่ถูก "เลือก" เข้า KB แล้ว curator ข้ามโฟลเดอร์นี้เพราะถ้าเดินเข้าไป
  จะเข้าใจว่า `picked` เป็นชื่อท่า แล้ว curate ซ้ำ

## 2. id ของไฟล์คือ `data/<ท่า>/…` เสมอ

KB อ้างถึงเอกสารด้วย path ตอนที่มันอยู่ใน `data/<ท่า>/…` (ฟิลด์ `source` ใน curated JSON, KB v6,
`eval/split_v6.json`, `prefilter_v6.json`, `curation_batches_v6.json`) ตอนย้ายไฟล์ไป `checked/` หรือ `picked/`
**ไม่ได้แก้ id เหล่านี้** ดังนั้น

- ไฟล์จริงของ id `data/lunge/x.pdf` อยู่ที่ `data/lunge/x.pdf`, `data/checked/lunge/x.pdf` หรือ `data/picked/lunge/x.pdf`
- `checked/` **โปร่งใส**: curator ตัด `checked/` ออกจาก path ก่อนใช้ทำ skip-list, batch, ที่เก็บผล และ `source`
  (`logical_rel()` และ `locate_source()` ใน `curator.py`)
- `picked/` ไม่ถูกค้นใน `locate_source()` ถ้ารัน batch เก่าซ้ำ curator จะหยุดเพราะหาไฟล์ไม่เจอ ไม่ curate ซ้ำ
- **ห้ามเปลี่ยนชื่อไฟล์** และห้ามย้ายไฟล์ข้ามท่าหรือข้ามโฟลเดอร์ย่อย เพราะ id จะเปลี่ยนและต้อง curate ใหม่
  (ย้ายระหว่าง `data/` → `checked/` → `picked/` โดยคงโครงเดิมได้ เพราะ id ไม่เปลี่ยน)

## 3. ขั้นตอนเมื่อเพิ่มเอกสารใหม่

1. วางไฟล์ไว้ที่ `data/<ท่า>/` หรือ `data/<ท่า>/<กฎ>/` (ดู §4)
2. ตรวจ prefilter → เพิ่ม entry ใน `data_pipeline/prefilter_v6.json` (keep หรือ drop) + บันทึกใน `prefilter_v6_review.md`
3. ย้ายไฟล์ไป `data/checked/` โดยคงโครงโฟลเดอร์เดิม
4. ใส่ไฟล์ `keep` ลง batch ใน `curation_batches_v6.json` แล้วรัน curator (คำสั่งใน `t3_curation_status.md` §2)
5. curate เสร็จ → ย้ายจาก `data/checked/` ไป `data/picked/` โดยคงโครงเดิม
6. ingest + `python eval/make_split.py --round <รอบ>` ตาม `t3_curation_status.md` §8.3

## 4. โครงโฟลเดอร์ย่อย

```
data/
├── <ท่า>/                  bicep-curl · lunge · push-up · squat
│   ├── <กฎ>/               key ของกฎใน error_taxonomy.py เช่น knee_valgus, torso_upright, elbow_away
│   │                       = เอกสารที่หามาเพื่อกฎนั้นโดยเฉพาะ
│   ├── *.pdf / *.txt       เอกสารของท่านั้นโดยรวม
│   └── urls.txt            URL หนึ่งบรรทัดต่อหนึ่งหน้า (curator ดึงเนื้อหาหลักของหน้าเว็บ)
├── general/                เอกสารที่ครอบคลุมหลายท่า (feedback_and_cueing, injury, range_of_motion)
│                           curator แยก item ไปเขียนที่ curated_data_v6/<ท่า>/general__<ชื่อ>_curated.json
├── checked/                โครงเดียวกับด้านบน
└── picked/                 โครงเดียวกับด้านบน
```

- ชื่อโฟลเดอร์ชั้นแรก (หลังตัด `checked/`) คือ `exercise_id` ที่ curator และ `ingest.py` ใช้
- curator อ่านแค่ `.pdf`, `.txt` และ `urls.txt` ไฟล์ชนิดอื่น (เช่นหน้า Google Scholar `.html` ใน `checked/push-up/`
  ที่เก็บไว้เป็นหลักฐานการค้น และ README นี้) ถูกข้าม
- `urls.txt` ของท่าเดียวกันอาจแยกอยู่หลายที่: URL ที่ curate แล้วอยู่ใน `picked/<ท่า>/urls.txt`
  URL ที่ตรวจแล้วแต่ยังไม่ curate อยู่ใน `checked/<ท่า>/urls.txt`
- git ไม่เก็บโฟลเดอร์ว่าง โฟลเดอร์กฎที่ยังไม่มีไฟล์ใน `data/<ท่า>/` จึงไม่มีใน repo สร้างเองได้เมื่อจะวางไฟล์

## 5. จำนวนไฟล์ (2026-10-21, นับ `.pdf` + `.txt`)

| | bicep-curl | lunge | push-up | squat | general | รวม |
|---|---|---|---|---|---|---|
| picked | 8 | 15 | 6 | 10 | 1 | 40 |
| checked | 13 | 18 | 11 | 10 | 5 | 57 |
| ใหม่ (`data/<ท่า>/`) | – | 2 | 2 | – | 2 | 6 |

## 6. ที่ยังไม่อยู่ใน git

- `excluded_from_kb/` — ไฟล์ต้นฉบับที่ตัดออกจาก KB รุ่นเก่า
- `data_duplicates/` — สำเนาที่ไบต์เหมือนกันหรือเป็นเปเปอร์เดียวกัน ดึงออกมาเพื่อไม่ให้ curate ซ้ำ

เอกสารในโฟลเดอร์นี้ส่วนใหญ่เป็นงานวิจัยของบุคคลที่สาม ลิขสิทธิ์เป็นของผู้เขียนหรือสำนักพิมพ์แต่ละราย
