# Deep Technical · Chapter 39 — Evaluation Datasets (BEIR / MTEB)

> ต่อจาก Ch38 · Ch6 = สมการ metric, Ch20 = โค้ด eval · บทนี้: **dataset มาตรฐาน**ที่ใช้เทียบ embedder ทั้งวงการ

---

## 39.0 ทำไมต้อง standard benchmark

benchmark ตัวเอง (Ch20, 30-doc) ดีสำหรับ regression · แต่จะรู้ว่า "bge-m3 vs nomic ตัวไหนดีกว่า" ต้อง **dataset ใหญ่ มาตรฐาน** ที่ทุกคนใช้ → เทียบข้ามงานได้

---

## 39.1 BEIR — zero-shot retrieval benchmark

**BEIR** = 18 dataset หลากหลาย domain (scientific, financial, bio-medical, Q&A, fact-check...)
```
เป้า: วัด embedder ที่เทรนบน domain หนึ่ง → ใช้กับ domain อื่นได้แค่ไหน (zero-shot generalization)
metric: nDCG@10 (Ch6 §6.4) เป็นหลัก
```
- **zero-shot สำคัญ**: second brain (ARRA) เจอ domain หลากหลาย (การแพทย์/วิจัย/โน้ตส่วนตัว) → ต้อง embedder ที่ generalize · BEIR วัดตรงนี้
- dataset ตัวอย่าง: NFCorpus (medical), SciFact (fact-check วิทยาศาสตร์), FiQA (finance), TREC-COVID

---

## 39.2 MTEB — Massive Text Embedding Benchmark

**MTEB** = benchmark ครอบคลุมสุด — 8 task types, 58+ datasets, 112 ภาษา:
```
tasks: Retrieval, Reranking, Clustering, Classification, STS (semantic similarity),
       Pair Classification, Summarization, Bitext Mining
```
- ไม่ใช่แค่ retrieval — วัด embedding รอบด้าน (คลัสเตอร์ได้ไหม, จับ similarity ไหม)
- **leaderboard** (HuggingFace): เทียบทุกโมเดล · bge-m3, e5, gte, OpenAI ada แข่งกัน
- retrieval subset = superset ของ BEIR

---

## 39.3 Metric standard — nDCG@10

ทั้ง BEIR/MTEB retrieval ใช้ **nDCG@10** (Ch6 §6.4) เป็นตัวหลัก:
- รับเกรด relevance + ลงโทษอันดับล่าง + normalize → เทียบข้าม dataset ได้
- รอง: recall@100 (Ch6 §6.1), MAP (Ch6 §6.5)

---

## 39.4 ⚠️ Leaderboard overfitting — caveat สำคัญ

```
โมเดลใหม่ๆ อาจ tune ให้ชนะ MTEB โดยเฉพาะ (train บน task คล้าย test)
→ คะแนน leaderboard สูง แต่ generalize จริงไม่เท่า
```
- เหมือน Ch6 §6.8 (vendor benchmark ขัดกัน) — **อย่าเชื่อ leaderboard rank เดียว**
- **ทางที่ถูก**: วัดบน **ข้อมูล/task ของตัวเอง** (Ch6 §6.8, Ch20) · leaderboard = ตัวกรองคร่าวๆ (top-10 น่าจะโอเค) แต่ตัวชนะบน task เรา ต้องวัดเอง

---

## 39.5 Multilingual / Thai benchmarks

- **MTEB multilingual**: มี subset หลายภาษา · bge-m3 ออกแบบมาเด่นตรงนี้ (Ch19)
- **MIRACL**: multilingual retrieval (18 ภาษา รวมภาษาที่ไม่ใช่อังกฤษ) — วัด cross-lingual (Ch19)
- **ไทยเฉพาะ**: benchmark ไทยยังน้อย · Thai STS/retrieval set มีบ้าง (Wongnai, XNLI-th) แต่ไม่ครบเท่าอังกฤษ → **ต้องระวัง**: คะแนนอังกฤษดีไม่การันตีไทยดี → วัดบน corpus ไทยเอง (Ch30 domain)

---

## 39.6 bge-m3 บน benchmark

- bge-m3 เด่นบน **MIRACL/multilingual** (จุดขาย M3, Ch19/22) + BEIR competitive
- dense อย่างเดียวดี · dense+sparse+colbert (Ch7) ดีกว่า
- **สำหรับ ARRA (ไทย+อังกฤษ)**: bge-m3 = เลือกที่สมเหตุผล (multilingual leader) — ยืนยันด้วย benchmark ไม่ใช่แค่เดา

---

## 39.7 สร้าง eval set ของตัวเอง (Ch6/20 applied)

benchmark มาตรฐานไม่มี domain คุณ → สร้างเอง:
```
1. เก็บ query จริงจาก usage (Ch31 implicit) หรือให้ผู้เชี่ยวชาญเขียน
2. label relevant docs (หรือ synthetic + คนตรวจ, Ch30 §30.2)
3. วัด nDCG@10 บน embedder candidates → เลือกตัวชนะบน "งานเราจริง"
```
→ นี่คือ eval ที่เชื่อได้สุดสำหรับ ARRA (มากกว่า MTEB rank)

---

## สรุป Ch39
```
BEIR: 18 dataset, zero-shot generalization (สำคัญกับ second-brain หลาย domain), nDCG@10
MTEB: 8 tasks, 58+ datasets, 112 ภาษา, leaderboard — วัดรอบด้าน
⚠️ leaderboard overfitting → อย่าเชื่อ rank เดียว, วัดบนงานตัวเอง (Ch6/20)
multilingual: MIRACL (cross-lingual, bge-m3 เด่น) · ไทย benchmark ยังน้อย → วัด corpus ไทยเอง
bge-m3 เลือกด้วยหลักฐาน benchmark (multilingual leader) ไม่ใช่เดา
```
**ถัดไป Ch40:** ColBERT late-interaction ลึก — MaxSim math เต็ม, storage per-token, PLAID efficient ColBERT, เมื่อไหร่ชนะ
---
*grounded: BEIR (Thakur 2021) · MTEB (Muennighoff 2022) · MIRACL (2022) · nDCG (Ch6) · เชื่อม Ch19/20/30 · /loop deep iter 2026-07-16*
