# Deep Technical · Chapter 52 — Idempotency & Deduplication

> ต่อจาก Ch51 · re-ingest ไฟล์เดิม/แก้นิดเดียว ต้องไม่พังหรือ duplicate · บทนี้: content-hash id, near-dup, ทำไม re-run ปลอดภัย

---

## 52.0 ปัญหา — ทำซ้ำในโลกจริง

```
- sync vault ทุกวัน → ไฟล์เดิมส่วนใหญ่ไม่เปลี่ยน → embed ซ้ำ = เปลือง (Ch44 embed แพง)
- แก้ไฟล์ 1 บรรทัด → ควร re-embed แค่ chunk ที่เปลี่ยน ไม่ใช่ทั้งไฟล์
- crash แล้ว resume (Ch51 §51.6) → บาง chunk ทำไปแล้ว → ทำซ้ำต้องไม่ duplicate
```
→ ต้องการ **idempotency**: ทำ N ครั้ง = ทำครั้งเดียว (ผลเท่ากัน)

---

## 52.1 ⭐ content-addressed id — หัวใจ idempotency

id ของ chunk = hash ของ content (ไม่ใช่ auto-increment):
```
chunk_id = hash(source_file + chunk_index + content)   เช่น SHA-256 → hex
→ content เดิม → id เดิม → upsert (Ch45) แทนที่ตัวเดิม (ไม่สร้างใหม่)
→ content เปลี่ยน → id ใหม่ → chunk ใหม่ (เก่า tombstone)
```
- **ผล**: re-ingest ไฟล์เดิม → id เดิมทุก chunk → upsert = no-op เชิงข้อมูล → ไม่ duplicate, ไม่ต้อง re-embed ถ้าเช็ค id ก่อน
- นี่คือหลัก content-addressing (เหมือน git blob hash) → deterministic, idempotent

---

## 52.2 skip unchanged — ประหยัด embed

```
ก่อน embed (Ch51 §51.3): เช็ค chunk_id มีใน index แล้วไหม
  มีแล้ว + content hash ตรง → skip (ไม่ embed ซ้ำ, ประหยัด Ch44)
  ไม่มี / hash ต่าง → embed + upsert
```
- แก้ไฟล์ 1 บรรทัด → chunk ส่วนใหญ่ hash เดิม (skip) → embed แค่ chunk ที่โดน → เร็ว
- **file-level shortcut**: เก็บ file mtime/hash → ไฟล์ไม่เปลี่ยน → ข้ามทั้งไฟล์ (ไม่ต้อง chunk ด้วยซ้ำ)

---

## 52.3 near-duplicate detection

exact dup (hash ตรง) ง่าย · **near-dup** (เนื้อหาคล้ายมากแต่ไม่ตรงเป๊ะ) ยากกว่า:
```
ตัวอย่าง: โน้ต 2 อันเนื้อหา 95% เหมือน (copy-paste แก้นิดหน่อย)
→ ค้นเจอทั้งคู่ (ซ้ำใน result, เปลือง top-k, Ch11)
```
วิธีจับ:
```
1. embedding similarity: cos(a,b) > 0.98 → near-dup (ใช้ vector ที่มีอยู่แล้ว!)
2. MinHash / SimHash: fingerprint ข้อความ → เทียบเร็ว (ไม่ต้อง embed)
3. dedup ตอน index หรือตอน return (filter result ที่คล้ายกันเกิน)
```
- **ARRA**: dedup result ตอน return (ถ้า 2 chunk cos>0.98 → เก็บอันคะแนนสูง) → result สะอาด

---

## 52.4 idempotency ของทั้ง pipeline

```
parse:  deterministic (ไฟล์เดิม → text เดิม)
chunk:  deterministic (Ch12 กติกาเดิม → chunk เดิม → id เดิม §52.1)
embed:  ~deterministic (โมเดลเดิม → vector เดิม, เว้น fp non-determinism เล็กน้อย)
upsert: idempotent by id (Ch45 replace)
→ ทั้ง pipeline idempotent → re-run กี่ครั้งก็ผลเดียว (Ch51 resumable ปลอดภัย)
```
- ⚠️ **embedding version**: ถ้าเปลี่ยนโมเดล (Ch53) → vector เดิมของ id เดิมจะไม่ compatible → ต้อง migration (Ch53)

---

## 52.5 tombstone + idempotent = แก้/ลบ สะอาด

```
แก้ chunk: content เปลี่ยน → id ใหม่ → upsert ใหม่ + tombstone id เก่า (Ch45)
ลบไฟล์: tombstone ทุก chunk_id ของไฟล์นั้น (query by source_file)
re-add ไฟล์เดิม: id เดิมกลับมา → upsert (revive/replace) → สอดคล้อง
```

---

## 52.6 เชื่อม ARRA

```
chunk_id = hash(source+index+content) (§52.1) → idempotent upsert (Ch45)
skip unchanged (§52.2) → sync vault รายวัน embed แค่ที่เปลี่ยน (ประหยัด Ch44)
dedup result cos>0.98 (§52.3) → top-k สะอาด (Ch11)
→ re-ingest ปลอดภัย, sync เร็ว, ไม่มี duplicate หลอน result
```

---

## สรุป Ch52
```
idempotency: ทำ N ครั้ง = ครั้งเดียว → re-ingest/resume ปลอดภัย (Ch51)
⭐ content-addressed id = hash(source+index+content) → content เดิม=id เดิม → upsert แทนที่ (เหมือน git)
skip unchanged: เช็ค hash ก่อน embed → แก้ 1 บรรทัด embed แค่ chunk ที่โดน (ประหยัด Ch44)
near-dup: cos>0.98 (ใช้ vector ที่มี) / MinHash → dedup result สะอาด (Ch11)
ทั้ง pipeline deterministic → idempotent (⚠️ ยกเว้นเปลี่ยนโมเดล → migration Ch53)
tombstone+id → แก้/ลบ/re-add สะอาด (Ch45)
```
**ถัดไป Ch53:** embedding versioning & migration — เปลี่ยนโมเดล embedder แล้ว vector เก่าใช้ไม่ได้, dual-write, backfill, zero-downtime model swap
---
*grounded: content-addressing (git blob) · MinHash/SimHash · near-dup dedup · เชื่อม Ch11/12/44/45/51/53 · /loop deep iter 2026-07-16*
