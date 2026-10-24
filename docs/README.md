# docs/

| โฟลเดอร์ | เนื้อหา |
|---|---|
| [`plans/`](plans/) | แผนงาน: rule change v6 (แผนหลัก), eval v6, RAG v2 ablation, health profile ในอนาคต |
| [`progress/`](progress/) | สถานะและ handoff (`t3_curation_status.md` = เปิดก่อนเมื่อทำต่อ), สรุป workflow, progress report, session notes |
| [`reports/`](reports/) | ผล eval แต่ละครั้ง (ชื่อไฟล์มีวันที่) |
| [`kb/`](kb/) | ข้อมูลใน KB: prefilter review, tag coverage, KB quality assessment |
| [`rules/`](rules/) | กฎและ taxonomy: error_type taxonomy, rule cards review, สเปกระบบ 1 (`system1/`) |
| [`slides/`](slides/) | สไลด์นำเสนอ |
| [`figures/`](figures/) | รูปที่ `eval/plot_*.py` สร้าง (ใช้ใน slides และ reports) |

โค้ดที่ root ของโปรเจกต์ (ย้ายเมื่อ 2026-10-25):
- root = แกนของ pipeline: `test_rag_compare.py` (generate + retrieval, ไม่ใช่ไฟล์ test), `ingest.py`, `embedding_config.py`, `error_taxonomy.py`, `kb_bm25.py`, `kb_rerank.py`
- `data_pipeline/` = curate · `eval/` = วัดผล · `mock_data/` = mock session + ตัวสร้าง
- `tests/` = test ทั้งหมด (รันทีละไฟล์ `python tests/<ไฟล์>.py`)
- `tools/kb_coverage.py` = ตรวจ KB · `tools/legacy/` = สคริปต์ debug ยุคแรก (collection เก่า `kb_gemini`/`kb_local`)
- `logs/` = log ของ curate/ingest

ผลการรัน `compare_output/` (จัดเมื่อ 2026-10-25):

| โฟลเดอร์ | เนื้อหา |
|---|---|
| `baseline_v14/` | RAG vs no-RAG บน KB v6 prompt v14 ครบ 4 ท่า + smoke v14/v14b/v14c |
| `strict_v6b/` | context v6 strict / v6b strict (ขั้น 2–5) + คำตอบ Groq |
| `ablation/` | ablation B0, R0–R5 + `ablation_log.md` + G1 |
| `retrieval/` | golden set, kb_coverage, relevance pool spot check |
| `history/` | รอบ generate เก่า (v1–v13, local_curated, A/B prompt v7–v8) |

`test_rag_compare.py --out` ใส่โฟลเดอร์ย่อยได้ เช่น `--out baseline_v14/compare_result_v14_squat.md` · ไฟล์ JSON/log ของการรันเก่าเก็บ path เดิมไว้ตามที่รันจริง (ไม่ได้แก้)
