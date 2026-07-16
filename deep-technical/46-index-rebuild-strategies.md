# Deep Technical · Chapter 46 — Index Rebuild Strategies

> ต่อจาก Ch45 · incremental พาไปได้ไกล แต่มีจุดที่ต้อง **rebuild เต็ม** · บทนี้: เมื่อไหร่/ยังไง rebuild โดยไม่ downtime

---

## 46.0 ทำไม incremental ไม่พอตลอด

incremental (Ch45) เก่ง insert/delete แต่ **โครงสร้าง index เสื่อมสะสม**:
```
IVF (Ch3):   centroid ตั้งจาก corpus เก่า → corpus เปลี่ยนแนว → cluster ไม่ balance
             (เช่น เริ่มโน้ตเรื่อง A, ต่อมาเขียนเรื่อง B เยอะ → centroid ไม่ครอบ B)
HNSW (Ch17): insert เยอะ + delete (tombstone) → graph connectivity เสื่อม, recall ตก
segment:     fragment เยอะเกิน (Ch45) → ค้นช้าแม้ compact
```
→ ถึงจุดหนึ่งต้อง **rebuild** เพื่อคืน recall/latency

---

## 46.1 สัญญาณว่าต้อง rebuild (วัดได้)

```
1. recall drop: eval set (Ch20/39) คะแนนตกจาก baseline → index เสื่อม
2. tombstone ratio สูง: deleted/total > threshold (เช่น >30%) → บวม (Ch45 §45.2)
3. latency creep: p99 (Ch44) ไต่ขึ้น → segment/graph เสื่อม
4. centroid imbalance: cluster size เบ้ (บาง cluster ใหญ่มาก) → IVF re-train
```
- **อย่า rebuild ตามอารมณ์** — rebuild เมื่อ metric บอก (Ch23 monitoring)

---

## 46.2 re-train IVF centroid

```
1. sample เวกเตอร์จาก corpus ปัจจุบัน (Ch3: k-means บน sample)
2. คำนวณ centroid ใหม่ (สะท้อน distribution ปัจจุบัน)
3. re-assign ทุก doc → cluster ใหม่
```
- แพง O(N) → ทำเป็นระยะ (ไม่ใช่ทุก insert) · trigger จาก imbalance metric (§46.1)
- HNSW ไม่มี centroid แต่ rebuild graph = insert ใหม่ทั้งหมดตามลำดับดี

---

## 46.3 ⭐ Blue-Green index swap — zero downtime

rebuild ใช้เวลานาน → ห้ามให้ค้นไม่ได้ระหว่างนั้น → สร้าง index ใหม่ข้างๆ แล้วสลับ:
```
1. index เดิม (blue) รับ query ต่อไปตามปกติ
2. background: สร้าง index ใหม่ (green) จาก corpus ปัจจุบัน
3. green พร้อม + validate (recall ผ่าน, Ch20) → atomic swap pointer blue→green
4. drain query เก่าบน blue → ทิ้ง blue
```
- query ไม่มีวินาทีที่ค้นไม่ได้ (atomic pointer swap)
- **delta ระหว่าง build**: doc ที่เขียนช่วง build green → เก็บ log → replay เข้า green ก่อน swap (ไม่ตกหล่น)

---

## 46.4 rebuild ที่ ARRA scale (single-user)

second brain ส่วนตัว corpus ~หมื่น-แสน doc → rebuild ทั้งหมดอาจแค่**วินาที-นาที**:
```
เล็กพอที่ full rebuild = ถูก → ไม่ต้อง blue-green ซับซ้อน
กลยุทธ์: compaction (Ch45) ตอน idle + full rebuild เป็นครั้งคราว (เช่น รายสัปดาห์/เมื่อ recall ตก)
```
- **ต่างจาก billion-scale** (Ch25): ที่นั่น rebuild = ชั่วโมง → blue-green จำเป็น, sharded rebuild ทีละ shard
- **บทเรียน scale-appropriate**: อย่า over-engineer · single-user ARRA ไม่ต้อง infra blue-green ของ Google

---

## 46.5 decision tree (สรุปปฏิบัติ)

```
corpus เล็ก (< แสน, ARRA):
   → append incremental (Ch45) + full rebuild ตอน idle เมื่อ recall/tombstone บอก
   → ง่าย, ถูก, พอ

corpus กลาง-ใหญ่ (ล้าน+):
   → incremental + periodic re-train (IVF centroid) + blue-green swap
   → sharded (Ch25) ถ้าเกิน 1 เครื่อง

trigger rebuild = metric (recall/tombstone/p99/imbalance) ไม่ใช่ตารางตายตัวอย่างเดียว
```

---

## สรุป Ch46
```
incremental เสื่อมสะสม (centroid drift, graph degrade, fragment บวม) → ถึงจุดต้อง rebuild
สัญญาณ: recall drop, tombstone>30%, p99 creep, centroid imbalance (วัด Ch20/23)
re-train IVF: k-means centroid ใหม่จาก corpus ปัจจุบัน → re-assign (O(N), เป็นระยะ)
⭐ blue-green: build green ข้างๆ → validate → atomic swap → zero downtime (replay delta)
ARRA single-user: corpus เล็ก → full rebuild ถูก → ไม่ต้อง blue-green (scale-appropriate)
trigger = metric ไม่ใช่อารมณ์
```
**ถัดไป Ch47:** multi-vector storage layout — เก็บ dense+sparse+colbert (Ch7) ยังไงในดิสก์, columnar vs row, memory-map, cache locality
---
*grounded: IVF re-train (Ch3) · blue-green deploy · LanceDB full-rebuild · scale-appropriate (Ch25) · เชื่อม Ch3/17/20/23/25/45 · /loop deep iter 2026-07-16*
