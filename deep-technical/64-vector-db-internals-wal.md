# Deep Technical · Chapter 64 — Vector DB Internals: WAL & Durability

> ต่อจาก Ch63 · เขียน doc แล้วเครื่องดับ ข้อมูลหายไหม? · บทนี้: write-ahead log, crash recovery, durability — ทำไม LanceDB/D1 คงทน

---

## 64.0 ปัญหา — write ไม่ atomic โดยธรรมชาติ

```
upsert 1 doc = หลาย step: เขียน vector + update index + update metadata (Ch45)
ถ้าเครื่องดับกลางคัน (step 2 เสร็จ, step 3 ไม่ทัน):
→ index ชี้ doc ที่ metadata ไม่มี → corrupt (inconsistent state)
```
→ ต้องการ: write **atomic** (สำเร็จหมด หรือ ไม่เกิดเลย) + **durable** (เขียนแล้วไม่หายแม้ดับ)

---

## 64.1 ⭐ WAL — Write-Ahead Log

หลักการ: **เขียน log ก่อน apply จริง**
```
1. เขียน intent ลง log (append-only, sequential=เร็ว Ch47): "จะ upsert doc X"
2. fsync log → ยืนยันลงดิสก์จริง (durable)
3. apply เข้า index/store จริง
4. ถ้าดับหลัง step 2 ก่อน 3 → recovery อ่าน log → replay → apply ต่อ (ไม่หาย)
5. ถ้าดับก่อน step 2 → log ไม่มี → เหมือนไม่เคยเกิด (atomic)
```
- **key insight**: log append sequential (เร็ว, Ch47 prefetch) → commit เร็ว · apply จริง (random, ช้า) ทำ background ได้
- ทุก DB คงทน (Postgres/SQLite/LanceDB) ใช้ WAL หรือ variant

---

## 64.2 fsync — เส้นแบ่งความคงทน

```
write() → อยู่ OS page cache (Ch49) → ยังไม่ถึงดิสก์จริง! (เร็วแต่ไม่ durable)
fsync() → บังคับ flush page → ดิสก์จริง (ช้า ~ms แต่ durable)
```
- **durability = fsync ตรงจุด**: WAL fsync log ก่อน ack → รับประกันไม่หาย
- trade: fsync ทุก write = ช้า → **group commit** (รวมหลาย write fsync ครั้งเดียว, คล้าย batch Ch44/51)

---

## 64.3 crash recovery — replay log

```
เปิด DB หลัง crash:
1. อ่าน WAL จากจุด checkpoint ล่าสุด
2. replay entry ที่ commit แล้วแต่ยังไม่ apply → apply ให้ครบ (redo)
3. entry ที่ไม่ commit (ดับกลาง log) → ทิ้ง (undo/ignore)
4. DB กลับสู่ consistent state → พร้อมใช้
```
- **idempotent replay (Ch52)**: replay ซ้ำต้องได้ผลเดิม → content-addressed id ช่วย (apply ซ้ำ=no-op)
- checkpoint: เป็นระยะ mark "log ถึงจุดนี้ apply ครบแล้ว" → recovery ไม่ต้อง replay ตั้งแต่ต้น

---

## 64.4 ⭐ MVCC — อ่านขณะเขียนได้ (ไม่ block)

Multi-Version Concurrency Control: เก็บหลาย version ของข้อมูล
```
writer สร้าง version ใหม่ (ไม่ทับเก่า) → reader ที่กำลังอ่านเห็น version เก่า (snapshot)
→ reader ไม่ต้องรอ writer (ไม่ lock) · writer ไม่ block reader
→ แต่ละ query เห็น snapshot ณ เวลาเริ่ม (consistent)
```
- **LanceDB (Ch4)**: versioned dataset — เขียน = version ใหม่ (fragment ใหม่ Ch45) → time-travel ได้ (อ่าน version เก่า)
- นี่เชื่อม tombstone/append (Ch45): ไม่ทับที่เก่า → MVCC โดยธรรมชาติ + rollback ได้

---

## 64.5 durability levels — เลือกได้ (trade speed)

```
สูงสุด:  fsync ทุก commit → ไม่หายเลย (ช้าสุด)
กลาง:    group commit (fsync รวม) → หายได้ไม่กี่ ms สุดท้าย (เร็วขึ้น)
ต่ำ:     async (ack ก่อน fsync) → เร็วสุด แต่ crash = หาย window นึง
```
- **เลือกตาม use case**: การเงิน=สูงสุด · second brain (ARRA)=กลาง (import ซ้ำได้ Ch52 ถ้าหาย window เล็ก)
- ARRA: ingest idempotent (Ch51/52) → durability กลางพอ (re-ingest กู้ได้)

---

## 64.6 เชื่อม ARRA

```
LanceDB versioned (Ch4/45) → MVCC (§64.4): อ่าน (ค้น) ขณะ ingest (เขียน) ได้ ไม่ block
                          → time-travel/rollback (version เก่า) = safety
append+fragment (Ch45) = WAL-like durability (write ใหม่ไม่ทับเก่า)
idempotent (Ch52) → replay/re-ingest ปลอดภัย (§64.3)
D1 (Ch14, SQLite): WAL mode → metadata/heat (Ch13) คงทน + concurrent read
```
- **community**: "เขียนโน้ตขณะค้นอยู่ พังไหม" → ไม่ (MVCC) · "เครื่องดับข้อมูลหาย?" → ไม่ (durable write + re-ingest idempotent)

---

## สรุป Ch64
```
write ไม่ atomic โดยธรรมชาติ (หลาย step) → ดับกลาง=corrupt → ต้อง atomic+durable
⭐ WAL: เขียน log ก่อน (append sequential เร็ว) → fsync → apply จริง → recovery replay log
fsync = เส้นแบ่ง durability (page cache Ch49 ไม่ durable จนกว่า fsync) → group commit ลด cost
crash recovery: replay commit-แล้ว-ยังไม่-apply (redo), ทิ้ง uncommitted · idempotent (Ch52) ช่วย
⭐ MVCC: version ใหม่ไม่ทับเก่า → reader เห็น snapshot ไม่ block writer (LanceDB versioned Ch4/45)
durability levels: fsync ทุก commit(ช้า/ปลอด) ↔ async(เร็ว/เสี่ยง) → ARRA กลาง (idempotent กู้ได้)
```
**ถัดไป Ch65:** concurrency & consistency — lock-free, snapshot isolation, eventual vs strong consistency, ค้นขณะ ingest, distributed consistency
---
*grounded: WAL/fsync/group-commit (DB internals) · MVCC · LanceDB versioned dataset (Ch4/45) · D1 SQLite WAL (Ch14) · idempotent (Ch52) · เชื่อม Ch13/14/44/45/47/49/51/52 · /loop deep iter 2026-07-16*
