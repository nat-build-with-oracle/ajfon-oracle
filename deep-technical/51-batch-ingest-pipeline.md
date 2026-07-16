# Deep Technical · Chapter 51 — Batch Ingest Pipeline

> ต่อจาก Ch50 · ค้นเก่งแค่ไหนก็ไร้ค่าถ้า ingest ไม่เข้า · บทนี้: pipeline เอา doc พันหมื่นชิ้นเข้า index — chunking, batch, retry, throughput

---

## 51.0 ภาพรวม ingest pipeline

```
ไฟล์/โน้ต → parse → chunk (Ch12) → embed (batch, Ch4) → upsert (Ch45) → index
   ↑ แต่ละ stage มี failure mode + throughput knob ของตัวเอง
```
- ingest = ETL สำหรับ vector · ต้องทน error (ไฟล์เสีย, embedder timeout) + เร็ว (หมื่น doc ไม่ควรเป็นชั่วโมง)

---

## 51.1 stage 1 — parse / extract

```
markdown/txt: อ่านตรง
PDF:          extract text (layout ยุ่ง, ตาราง/คอลัมน์) → มัก noisy
code:         เก็บ structure (function boundary, Ch12)
```
- **fail-soft**: ไฟล์ parse ไม่ได้ → log + skip (ไม่ล้มทั้ง batch) · เก็บ error list ให้ review
- normalize: strip control char, unicode NFC (ไทยสระ/วรรณยุกต์, Ch9) → embed ได้เสถียร

---

## 51.2 stage 2 — chunk (Ch12 applied)

```
chunk ตาม Ch12 (semantic/recursive, overlap) → แต่ละ chunk = 1 unit ค้นได้
เก็บ metadata: source_file, chunk_index, char_offset → trace กลับ (Ch26 provenance)
```
- 1 doc → N chunk → N embedding → N row ใน index · relation doc↔chunk เก็บไว้ (rebuild doc จาก chunk ได้)

---

## 51.3 ⭐ stage 3 — batch embed (throughput หัวใจ)

embed เป็นคอขวด (Ch44) → batch สำคัญ:
```
arra-oracle-v3 (Ch4): batchSize=50, attempts=3, timeout=30s
loop:
  for batch of 50 chunks:
    try: embed(batch) → 50 vectors ใน 1 call (Ch44 throughput 19×)
    catch timeout/error: retry (backoff) ≤ 3 → ถ้ายังพัง → dead-letter (skip+log)
```
- **batch size trade**: ใหญ่ = throughput ดี แต่ 1 พัง = เสียทั้ง batch (retry แพง) · 50 = สมดุลที่ ARRA เลือก
- backoff (Ch4 fallback): timeout → รอ exponential → ลองใหม่ → ถ้า provider ล่ม → fallback chain (Ollama→Gemini→CF)

---

## 51.4 stage 4 — upsert (idempotent, ดู Ch52)

```
embed เสร็จ → upsert เข้า vector store (Ch45 append/tombstone)
upsert ไม่ใช่ insert: ถ้า chunk id มีแล้ว → replace (idempotent, Ch52)
→ re-run ingest ไฟล์เดิม ไม่สร้าง duplicate
```

---

## 51.5 throughput math

```
10,000 chunk · embed 50/batch · batch ใช้ 100ms (Ch44)
= 200 batch × 100ms = 20 วินาที (ถ้า serial)
+ parallel batch (Ch44 §44.3, ยิงหลาย batch พร้อม): ÷ concurrency → ~ไม่กี่วินาที
```
- **bottleneck จริง**: embedder rate limit (cloud) หรือ GPU (local) → concurrency คุมไม่ให้ชน rate limit
- ARRA local (Ollama): CPU/GPU เครื่องเดียว → concurrency ต่ำ แต่ไม่มี network/rate limit

---

## 51.6 progress / resumability

```
ingest หมื่น doc พังกลางคัน (เครื่อง sleep, embedder ล่ม) → ห้ามเริ่มใหม่หมด
→ checkpoint: mark chunk ที่ embed+upsert สำเร็จแล้ว
→ resume: ข้าม chunk ที่ทำแล้ว (idempotent upsert Ch52 ช่วย — ทำซ้ำก็ไม่ duplicate)
```
- นี่ทำให้ ingest ใหญ่ทนทาน (crash-safe)

---

## 51.7 เชื่อม ARRA

```
โน้ต/ไฟล์ → parse (fail-soft §51.1) → chunk+meta (Ch12/26) → embed batch 50 (Ch4 §51.3)
→ retry×3+fallback (Ch4) → upsert idempotent (Ch52) → LanceDB append (Ch45)
checkpoint → resume ได้ (§51.6)
```
- **community**: "import โน้ตทั้ง vault (พันไฟล์) นานไหม?" → วินาที-นาที (batch+parallel) · พังก็ resume ได้

---

## สรุป Ch51
```
pipeline: parse → chunk(Ch12) → embed batch(Ch4) → upsert(Ch45) — แต่ละ stage fail-soft
parse: fail-soft (skip+log), normalize NFC (ไทย Ch9)
chunk: 1 doc→N chunk, เก็บ meta (source/offset, Ch26 provenance)
⭐ embed batch: batchSize=50, attempts=3, timeout=30s (ARRA จริง) — throughput หัวใจ, backoff+fallback
upsert idempotent (Ch52) → re-run ไม่ duplicate
throughput: 10k chunk ~วินาที (batch+parallel), bottleneck=rate limit/GPU
resumable: checkpoint → crash-safe (idempotent ช่วย)
```
**ถัดไป Ch52:** idempotency & dedup — content hash id, near-duplicate detection, ทำไม re-ingest ปลอดภัย
---
*grounded: arra-oracle-v3 src/vector (batchSize 50, attempts 3, timeout 30s) · fallback-chain.ts · เชื่อม Ch4/9/12/26/44/45/52 · /loop deep iter 2026-07-16*
