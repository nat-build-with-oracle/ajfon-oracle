# Deep Technical · Chapter 65 — Concurrency & Consistency

> ต่อจาก Ch64 · หลายคน/หลาย process อ่านเขียนพร้อมกัน · บทนี้: isolation levels, eventual vs strong consistency, ค้นขณะ ingest, สิ่งที่ vector DB ต้องรับประกัน

---

## 65.0 ปัญหา — พร้อมกันแล้วเห็นอะไร

```
process A: ingest 1000 doc ใหม่ (Ch51)
process B: ค้น ระหว่าง A กำลัง ingest
→ B เห็น doc ครบ? บางส่วน? ไม่เห็นเลย? → ขึ้นกับ isolation/consistency model
```
- vector DB ต้องนิยามชัดว่ารับประกันอะไร (ไม่งั้น result ไม่ predictable)

---

## 65.1 ⭐ isolation levels (จาก DB theory)

```
read uncommitted: เห็น write ที่ยังไม่ commit (dirty read) — อันตราย, ไม่ใช้
read committed:   เห็นเฉพาะ commit แล้ว — แต่ 2 อ่านในเทิร์นเดียวอาจต่าง (non-repeatable)
repeatable read:  อ่านซ้ำได้ผลเดิมในเทิร์น — แต่อาจเจอ phantom (row ใหม่)
snapshot isolation: เห็น snapshot ณ เวลาเริ่ม → consistent ทั้งเทิร์น (MVCC Ch64)
serializable:     เหมือนรันทีละอัน — เข้มสุด, ช้าสุด
```
- **vector search มัก snapshot isolation** (MVCC Ch64): query เห็น index ณ เวลาเริ่ม → ผล consistent แม้มี write พร้อมกัน

---

## 65.2 snapshot isolation ใน vector search

```
query เริ่ม → pin version ปัจจุบัน (Ch64 MVCC) → ค้นบน snapshot นั้น
ingest พร้อมกัน → สร้าง version ใหม่ (fragment ใหม่ Ch45) → query เก่าไม่เห็น (เห็น snapshot เดิม)
query ถัดไป → เห็น version ใหม่ (doc ที่เพิ่ง ingest)
```
- **ผล**: query ไม่เห็น "index ครึ่งๆ กลางๆ" (atomic view) → result สอดคล้อง
- LanceDB (Ch4/64): versioned → snapshot isolation ฟรี

---

## 65.3 ⭐ eventual vs strong consistency

```
strong: เขียนเสร็จ → อ่านทันทีเห็นเลย (read-your-writes)
        ต้อง sync (รอ replica ทุกตัว update) → ช้ากว่า, แต่ถูกต้องเป๊ะ
eventual: เขียนเสร็จ → อ่านอาจยังไม่เห็น (แป๊บนึง) → สุดท้าย converge
        เร็ว/scale แต่ window ที่ไม่ตรง
```
- **single-node (ARRA local)**: strong ง่าย (ไม่มี replica) → เขียนโน้ตแล้วค้นเจอเลย (freshness Ch45)
- **distributed (Vectorize edge Ch14, หลาย region)**: มัก eventual → doc ใหม่ propagate ข้าม region ใช้เวลา

---

## 65.4 freshness vs consistency (เชื่อม Ch45)

```
freshness (Ch45): ค้นเจอของใหม่เร็วแค่ไหน
consistency (Ch65): ค้นแล้วเห็น state ที่ถูกต้อง/สอดคล้องแค่ไหน
→ เกี่ยวกัน: strong consistency + high freshness = เขียนปุ๊บค้นเจอปั๊บ (single-node ทำได้)
             eventual = freshness delayed ข้าม node
```
- ARRA local: ได้ทั้งคู่ (single-node, strong, fresh) — ข้อได้เปรียบ personal (Ch48/62 pattern)

---

## 65.5 lock-free & MVCC (ทำไมไม่ต้อง lock)

```
lock-based: writer lock index → reader รอ → ช้า, contention
MVCC (Ch64): writer สร้าง version ใหม่ → reader อ่านเก่า → ไม่ต้อง lock
→ read-heavy workload (ค้นเยอะกว่าเขียน, ปกติของ retrieval) → MVCC ชนะขาด
```
- vector search = read-heavy (ค้น >> ingest) → MVCC/snapshot เหมาะมาก
- append-only (Ch45) + immutable fragment → lock-free โดยธรรมชาติ (ไม่แก้ที่เก่า = ไม่ต้องกันชน)

---

## 65.6 เชื่อม ARRA

```
LanceDB versioned (Ch64) → snapshot isolation (§65.2): ค้นขณะ ingest → เห็น snapshot สอดคล้อง
single-node local → strong consistency + fresh (§65.3/4): เขียนโน้ตแล้วค้นเจอเลย
read-heavy (ค้น>>เขียน) → MVCC lock-free (§65.5) → ค้นไม่โดน ingest block
D1 (Ch14) WAL mode → concurrent read + single writer (SQLite model)
Vectorize edge (Ch14) → eventual ข้าม region (trade สำหรับ global scale Ch25)
```
- **community**: "หลาย tool/session ใช้ ARRA พร้อมกันได้ไหม" → ได้ (MVCC read-heavy) · "เขียนแล้วเห็นเลย?" → ใช่ (single-node strong)

---

## สรุป Ch65
```
พร้อมกัน → เห็นอะไร ขึ้นกับ isolation/consistency (ต้องนิยามชัด)
⭐ isolation: read-committed < repeatable < snapshot(MVCC) < serializable
vector search มัก snapshot isolation: query เห็น version ณ เวลาเริ่ม (ไม่เห็น index ครึ่งๆ)
⭐ strong (read-your-writes, single-node ARRA) vs eventual (distributed/edge, propagate ช้า)
freshness (Ch45) × consistency: single-node = ทั้งคู่ (เขียนปุ๊บค้นปั๊บ) = ได้เปรียบ personal
MVCC lock-free: writer version ใหม่ ไม่ block reader → read-heavy (retrieval) ชนะขาด
ARRA: snapshot isolation + strong + lock-free (local) · Vectorize eventual (edge scale)
```
**ถัดไป Ch66:** distributed vector DB — sharding + replication, consensus (Raft), เมื่อ corpus/traffic เกิน 1 เครื่อง, coordinate หลาย node
---
*grounded: isolation levels (DB theory) · snapshot isolation/MVCC (Ch64) · eventual vs strong (CAP prelude) · LanceDB versioned · D1 SQLite (Ch14) · เชื่อม Ch14/25/45/48/62/64 · /loop deep iter 2026-07-16*
