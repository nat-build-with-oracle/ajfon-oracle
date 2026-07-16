# Deep Technical · Chapter 55 — Access Control & Metadata Filtering

> ต่อจาก Ch54 · Ch27 multi-tenancy เกริ่น · บทนี้ลงลึก **pre vs post filtering** — ทำไมกรอง metadata ก่อน/หลัง ANN ต่างกันมาก (จุดพลาดที่นักพัฒนาเจอบ่อย)

---

## 55.0 ปัญหา — ค้น + กรองพร้อมกัน

```
query: "โครงการ X" + filter: user_id=me AND folder="งานวิจัย" AND date>2025
→ อยาก top-k ที่ทั้ง similar (vector) และ ผ่าน filter (metadata)
→ ANN (Ch3/17) เก่ง similar แต่ไม่รู้ filter → รวมยังไง?
```

---

## 55.1 ⭐ post-filtering — ANN ก่อน, กรองทีหลัง (จุดพลาด)

```
1. ANN หา top-k similar (ไม่สน filter)
2. กรอง k ตัวนั้นด้วย metadata → เหลือที่ผ่าน filter
```
**ปัญหาใหญ่**:
```
ถ้า filter เข้ม (ผ่านแค่ 1%) → top-100 similar อาจไม่มีตัวไหนผ่าน filter เลย!
→ return ว่าง ทั้งที่มี doc ที่ทั้ง similar+ผ่าน filter อยู่ (แต่ไม่ติด top-100)
```
- นี่คือ **bug คลาสสิก**: "ค้นแล้วได้ผลว่าง/น้อยผิดปกติเมื่อใส่ filter" → เพราะ post-filter ตัดหลัง ANN

---

## 55.2 pre-filtering — กรองก่อน, ANN บน subset

```
1. กรอง metadata ก่อน → เหลือ candidate ที่ผ่าน filter
2. ANN/brute-force หา similar ใน subset นั้น
```
- **แม่นกว่า** (ไม่พลาด doc ที่ผ่าน filter) แต่:
```
ถ้า subset ใหญ่ → brute-force ช้า (Ch1) · ANN index ทั้งก้อนใช้ตรงๆ ไม่ได้ (index ไม่รู้ filter)
→ ต้อง ANN ที่รองรับ filter ระหว่างไต่ (filtered search)
```

---

## 55.3 filtered ANN — กรองระหว่างไต่ (ทางออกจริง)

vector DB ยุคใหม่ทำ filter **ระหว่าง** ANN traversal:
```
HNSW (Ch17): ไต่ graph แต่ประเมินเฉพาะ node ที่ผ่าน filter (skip node ไม่ผ่าน)
IVF (Ch3):   ค้น cluster แต่นับเฉพาะ doc ที่ผ่าน filter
→ ได้ top-k ที่ similar+ผ่าน filter จริง โดยไม่ brute-force
```
- **trade**: filter เข้มมาก → ต้องไต่ลึกขึ้น (candidate ผ่านน้อย) → ช้าลง แต่ correct
- บาง engine: filter selectivity สูง (ผ่านน้อย) → fallback เป็น brute-force บน subset (เร็วกว่าไต่ทั้ง graph)

---

## 55.4 selectivity — ตัวตัดสินกลยุทธ์

```
selectivity = สัดส่วน doc ที่ผ่าน filter
สูง (ผ่านเยอะ, เช่น 80%):  post-filter พอ (top-k มักมีตัวผ่าน) — ง่าย/เร็ว
ต่ำ (ผ่านน้อย, เช่น 0.1%): ต้อง pre/filtered-ANN (post-filter จะได้ว่าง §55.1)
```
- **planner**: ประเมิน selectivity → เลือก strategy (เหมือน query planner ใน SQL DB)

---

## 55.5 access control = filter พิเศษ (security-critical)

```
multi-tenant (Ch27): filter user_id/tenant_id = ห้ามพลาด (เห็นข้อมูลคนอื่น = breach)
→ ต้อง pre/filtered (§55.2/3) — post-filter อันตราย: ถ้า logic พลาด อาจ leak
→ enforce ที่ชั้น query (ไม่ trust client) — inject tenant filter เสมอ (server-side)
```
- **ต่างจาก filter ธรรมดา**: access filter ผิด = security breach (ไม่ใช่แค่ผลไม่ครบ) → เข้มกว่า

---

## 55.6 ARRA — single-user แต่ยังมี filter

```
ARRA personal: ไม่มี multi-tenant (คนเดียว) → access control เบา
แต่ยังใช้ filter: folder, tag, date, source (Ch51 metadata) → กรอง scope การค้น
→ selectivity มักสูง (personal corpus เล็ก) → post/filtered พอ
ถ้าขยาย multi-user (แชร์ vault ทีม) → ต้อง pre-filter tenant (§55.5) เข้ม
```

---

## สรุป Ch55
```
ค้น+filter: ANN เก่ง similar ไม่รู้ filter → รวมยังไงคือโจทย์
⚠️ post-filter (ANN ก่อน กรองหลัง): filter เข้ม → top-k ไม่มีตัวผ่าน → ว่างผิด (bug คลาสสิก)
pre-filter (กรองก่อน ANN): แม่น แต่ subset ใหญ่=ช้า
⭐ filtered-ANN (กรองระหว่างไต่): top-k similar+ผ่าน filter จริง (ทางออก) — trade: เข้ม=ไต่ลึก
selectivity ตัดสิน: สูง→post พอ, ต่ำ→ต้อง pre/filtered (เหมือน SQL planner)
access control = filter security-critical → pre/filtered + enforce server-side (Ch27)
ARRA single-user → filter เบา (folder/tag/date), multi-user → tenant pre-filter เข้ม
```
**ถัดไป Ch56:** hybrid weight tuning — ปรับน้ำหนัก dense vs sparse ใน RRF/linear, เมื่อไหร่ dense เด่น/sparse เด่น, tune บน eval
---
*grounded: pre/post/filtered ANN · selectivity planner · multi-tenant security (Ch27) · เชื่อม Ch1/3/17/27/51 · /loop deep iter 2026-07-16*
