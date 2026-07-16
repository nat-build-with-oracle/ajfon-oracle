# Deep Technical · Chapter 45 — Streaming / Incremental Index

> ต่อจาก Ch44 · Ch3/17 = สร้าง index จาก corpus นิ่ง · โลกจริง: doc เพิ่ม/แก้/ลบตลอด (second brain โตทุกวัน) · บทนี้: index ที่ **สด** โดยไม่ rebuild

---

## 45.0 ปัญหา — index กับ corpus ที่ขยับ

```
second brain: เขียนโน้ตใหม่ทุกวัน, แก้เก่า, ลบทิ้ง
ถ้า rebuild index ทุกครั้งที่เพิ่ม 1 doc → ช้ามาก (O(N) ต่อการเพิ่ม)
ต้องการ: เพิ่ม/ลบ doc แบบ incremental + ค้นเจอของใหม่ทันที (freshness)
```

---

## 45.1 insert — เพิ่ม doc เข้า index สด

```
flat (brute force, Ch1):  append เวกเตอร์ต่อท้าย → O(1) เพิ่ม, ค้นเจอทันที (ค้น O(N))
IVF (Ch3):                assign doc → cluster ใกล้สุด → append ใน list นั้น O(1)
                          แต่ centroid ไม่ขยับ → นานๆ ไป cluster เบี้ยว (ต้อง re-train, Ch46)
HNSW (Ch17):              insert = หา neighbor + ต่อ edge → O(log N), ค้นเจอทันที
                          แต่ graph อาจ degrade ถ้า insert เยอะโดยไม่ปรับ
```
- **ARRA (LanceDB, Ch4)**: append doc ได้ incremental · เป็น columnar (Lance format) → เพิ่มเร็ว

---

## 45.2 ⭐ delete — ปัญหาที่ยากกว่า insert

ลบ doc ออกจาก graph/list ตรงๆ = แพง (ต้องซ่อม edge/list) → ใช้ **tombstone**:
```
soft delete: mark doc = deleted (bit flag) → ยังอยู่ใน index แต่ filter ออกตอน return
             O(1) ลบ · แต่ index บวม (deleted ยังกินที่/ถูกไต่ผ่าน)
compaction:  เป็นระยะ → rebuild segment ที่ tombstone เยอะ → คืนที่จริง
```
- **แก้ doc = delete + insert** (tombstone เก่า + append ใหม่) → version ใหม่ค้นเจอ, เก่าถูก filter

---

## 45.3 segment / LSM-style architecture

vector DB ยุคใหม่ยืมแนวคิด LSM-tree (จาก key-value DB):
```
- write → segment เล็กใหม่ (in-memory / ไฟล์เล็ก) → เร็ว
- ค้น = ค้นทุก segment แล้ว merge ผล (Ch3 คล้าย multi-index)
- background: merge segment เล็ก → segment ใหญ่ (compaction) + ล้าง tombstone
```
- **trade**: segment เยอะ → ค้นช้าลง (ต้องแตะหลาย segment) → compaction คุมจำนวน
- LanceDB: dataset = fragments (segment) → append สร้าง fragment ใหม่, compaction รวม

---

## 45.4 freshness vs latency — สอง knob ขัดกัน

```
freshness สูง (ค้นเจอของใหม่ทันที):  ต้อง index ทันทีที่เขียน → write ช้าลง
latency ต่ำ (ค้นเร็ว):               ต้อง segment น้อย/compact → แต่ compaction กิน I/O
```
- **second brain (ARRA)**: freshness สำคัญ (เขียนโน้ตแล้วอยากค้นเจอเลย) · single-user → write ไม่ถี่มาก → append ทันที + compact ตอน idle = พอ
- **ต่างจาก search engine ใหญ่**: batch index รายชั่วโมง (freshness ต่ำได้, latency สำคัญกว่า)

---

## 45.5 retrieval heat กับ incremental (Ch13)

ARRA เก็บ `usage_count`/`last_accessed_at` (Ch13) — เป็น metadata ที่ **update บ่อยกว่าเวกเตอร์**:
```
เวกเตอร์ของ doc: นิ่ง (แก้เมื่อ content เปลี่ยน)
heat metadata:   ขยับทุกครั้งที่ถูกค้นเจอ (usage++)
→ เก็บแยก (Ch13): เวกเตอร์ใน vector store, heat ใน D1/SQLite (update เร็ว ไม่แตะ index)
```
- นี่คือเหตุผลออกแบบ heat แยก store (Ch13/14) — ไม่ต้อง re-index เมื่อ heat เปลี่ยน

---

## 45.6 เชื่อม ARRA (ปฏิบัติ)

```
เขียนโน้ต → embed (Ch4) → append LanceDB fragment (Ch45 §45.1) → ค้นเจอทันที
แก้โน้ต → tombstone เก่า + append ใหม่ (§45.2)
ลบ → tombstone (§45.2)
idle → compaction (รวม fragment + ล้าง tombstone, §45.3)
heat → update D1 แยก (§45.5, Ch13) ไม่แตะ vector index
```
- **implication community**: "เขียนแล้วค้นเจอเลยไหม?" → ได้ (incremental append) · ไม่ต้องรอ rebuild

---

## สรุป Ch45
```
insert: flat/IVF O(1) append, HNSW O(log N) — ค้นเจอทันที (freshness)
⚠️ delete ยากกว่า insert → tombstone (soft delete) + compaction ล้างเป็นระยะ
แก้ doc = delete+insert (version ใหม่ค้นเจอ เก่า filter)
LSM/segment: write→fragment เล็ก, ค้น merge หลาย segment, compaction รวม (trade freshness↔latency)
heat metadata แยก store (Ch13) → update ไม่แตะ index
ARRA: append ทันที + compact idle = freshness ดี (second brain โตทุกวัน)
```
**ถัดไป Ch46:** index rebuild strategies — เมื่อไหร่ต้อง rebuild เต็ม (centroid drift), re-train IVF, blue-green index swap, zero-downtime
---
*grounded: LSM-tree · tombstone/compaction · LanceDB fragments · เชื่อม Ch3/4/13/14/17 · /loop deep iter 2026-07-16*
