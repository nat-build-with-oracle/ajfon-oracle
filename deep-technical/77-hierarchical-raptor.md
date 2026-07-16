# Deep Technical · Chapter 77 — Hierarchical / Recursive Retrieval (RAPTOR)

> ต่อจาก Ch76 · parent-child คือ 2 ชั้น · บทนี้: หลายชั้น (tree), RAPTOR (cluster+summarize), ค้นข้ามระดับ abstraction

---

## 77.0 ปัญหา — คำถามคนละระดับ abstraction

```
"metformin ขนาดยาเท่าไร"  → ต้องการ detail (chunk เล็ก, Ch76)
"เอกสารนี้สรุปว่าอะไร"     → ต้องการ overview (ทั้ง doc / หลาย doc)
→ chunk เล็กตอบ detail ได้ แต่ตอบ "ภาพรวม" ไม่ได้ (ไม่มี chunk ไหนเห็นทั้งหมด)
```
- flat chunk (Ch12) ขาด "ระดับสรุป" → ค้นภาพรวมไม่เจอ

---

## 77.1 ⭐ RAPTOR — tree ของ summary

สร้าง tree จาก chunk ล่างขึ้นบน:
```
level 0 (leaf): chunk ต้นฉบับ (Ch12)
   ↓ cluster (Ch36 embedding clustering)
level 1: กลุ่ม chunk ใกล้กัน → LLM summarize → embed summary
   ↓ cluster อีก
level 2: summary ของ summary → ...
   ↓
root: สรุปทั้ง corpus
→ tree: leaf=detail, สูงขึ้น=abstract มากขึ้น
```
- แต่ละ node (ทุกระดับ) embed + index → ค้นเจอได้ทั้ง detail และ summary

---

## 77.2 การค้นบน tree — 2 โหมด

```
collapsed tree (แนะนำ): ทุก node (ทุกระดับ) อยู่ index เดียว → ค้น flat → เจอ node ระดับที่ match
  query detail → เจอ leaf · query ภาพรวม → เจอ summary node (สูง) → ANN เลือกเอง!
tree traversal: เริ่ม root → ลงตาม child ที่ relevant สุด (beam) → ถึง leaf
  โครงสร้างชัด แต่ traversal ผิดชั้น = พลาด (greedy Ch3)
```
- **collapsed มัก win**: ให้ ANN (Ch3) เลือกระดับที่เหมาะเอง (ไม่บังคับ traverse)

---

## 77.3 clustering ที่สร้าง tree (เชื่อม Ch36)

```
cluster chunk: k-means/GMM บน embedding (Ch3/36) → กลุ่ม semantic
soft clustering (GMM): 1 chunk อยู่หลาย cluster ได้ (overlap หัวข้อ) → tree ไม่ตายตัว
แต่ละ cluster → LLM summarize (Ch75 assembly) → node ใหม่ระดับบน
```
- recursive: ทำซ้ำจนเหลือ node น้อย (root) → ความลึก tree = log ของ corpus

---

## 77.4 ⚠️ cost — สร้าง tree แพง

```
RAPTOR build: cluster + LLM summarize ทุก node ทุกระดับ
  N chunk → N/k cluster → N/k LLM summarize call (level 1) → ... → รวมหลาย LLM call
  → ingest แพงกว่า flat chunk มาก (Ch70 compute)
maintenance: doc ใหม่ → cluster เปลี่ยน → re-summarize (Ch46 rebuild) → แพง incremental
```
- **trade**: query ดีขึ้น (ตอบภาพรวมได้) แลกกับ ingest cost สูง → คุ้มเมื่อ corpus ใหญ่+ถามภาพรวมบ่อย

---

## 77.5 เมื่อไหร่ใช้ hierarchical

```
ใช้: corpus ใหญ่/ยาว + คำถามหลายระดับ (detail + summary + cross-doc synthesis)
     เช่น: ค้นงานวิจัยหลายเล่ม → "สรุปแนวโน้มทั้งหมด" (ต้อง summary node)
ไม่ใช้: corpus เล็ก/โน้ตสั้น → flat chunk (Ch12) + small-to-big (Ch76) พอ
```
- scale-appropriate (ย้ำ Ch46/48/70): personal ARRA เล็ก → RAPTOR overkill · องค์กร/research corpus ใหญ่ → คุ้ม

---

## 77.6 เชื่อม ARRA

```
ARRA flat chunk (Ch12) + small-to-big (Ch76) → ครอบ detail + context ระดับ doc
hierarchical (RAPTOR) = ชั้นถัดไปถ้าต้องการ "สรุปข้าม doc":
  cluster chunk (Ch36) → summarize (Claude ทำได้!) → เก็บ summary node เป็น doc พิเศษ
  → collapsed index (§77.2): summary node ปนใน index ปกติ → ค้นเจอเมื่อถามภาพรวม
ARRA ปัจจุบัน: flat พอสำหรับ second brain (ถามภาพรวม → Claude สรุปจาก top-k เอง, Ch75)
→ RAPTOR = optimization เมื่อ corpus ใหญ่จน top-k ไม่พอครอบภาพรวม
```

---

## สรุป Ch77
```
ปัญหา: คำถามคนละระดับ (detail vs ภาพรวม) → flat chunk (Ch12) ตอบภาพรวมไม่ได้ (ไม่มี node สรุป)
⭐ RAPTOR: tree bottom-up — leaf(chunk) → cluster(Ch36) → LLM summarize → node บน → ... → root
ค้น: collapsed tree (ทุก node ใน index เดียว, ANN เลือกระดับเอง) > traversal (greedy เสี่ยงพลาด)
clustering: GMM soft (chunk อยู่หลาย cluster) → recursive summarize → tree ลึก log(N)
⚠️ cost: build แพง (LLM summarize ทุก node) + maintenance (re-summarize, Ch46) → คุ้มเมื่อใหญ่+ถามภาพรวม
scale-appropriate: personal=flat+small-to-big พอ · corpus ใหญ่/research=RAPTOR คุ้ม
ARRA: flat+Claude สรุป top-k (Ch75) พอ · RAPTOR=opt‌ion เมื่อ corpus ใหญ่เกิน top-k
```
**ถัดไป Ch78:** self-querying & metadata extraction — LLM แปลง natural query → structured filter (Ch55) + semantic, auto-extract metadata ตอน ingest
---
*grounded: RAPTOR (Sarthi 2024) · GMM clustering (Ch36) · collapsed tree · recursive summarize · scale-appropriate (Ch46/48/70) · เชื่อม Ch3/12/36/46/70/75/76 · /loop deep iter 2026-07-16*
