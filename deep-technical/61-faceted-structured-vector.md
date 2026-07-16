# Deep Technical · Chapter 61 — Faceted & Structured + Vector

> ต่อจาก Ch60 · โลกจริง query ผสม semantic + structured ("บทความ AI ปี 2024 ที่ยาวกว่า 10 หน้า") · บทนี้: time-decay, numeric range, geo + vector

---

## 61.0 ปัญหา — semantic + structured พร้อมกัน

```
query: "งานวิจัย vector search (semantic) จากปี 2023+ (numeric) ในโฟลเดอร์ AI (facet)"
→ vector: similar · date>2023: numeric filter · folder=AI: exact facet
→ รวม fuzzy (vector) + exact (structured) ยังไง
```
- ต่อยอด Ch55 (filter) + Ch60 (boolean) → เพิ่ม numeric/temporal/geo (structured dimensions)

---

## 61.1 numeric range + vector

```
filter: price ∈ [100,500], date > 2023, length > 10pages
→ pre/filtered-ANN (Ch55): กรอง range ก่อน/ระหว่างไต่ → vector บน subset
→ range filter = metadata index (B-tree บน numeric) + vector (Ch55 filtered)
```
- selectivity (Ch55 §55.4): range แคบ → ผ่านน้อย → filtered-ANN สำคัญ

---

## 61.2 ⭐ time-decay — ใหม่กว่า = ดีกว่า (soft)

หลาย use case: doc ใหม่ควรได้เปรียบ (ข่าว, โน้ตล่าสุด) — **แต่ soft** (ไม่ตัดขาด):
```
final_score = relevance(vector) × decay(age)
decay(age) = exp(−λ·age)     exponential decay
           หรือ 1/(1 + λ·age)  reciprocal
→ doc เก่าไม่ถูกตัด แต่ถูกถ่วงลง → ใหม่+relevant ชนะ
```
- **เชื่อม retrieval heat (Ch13)**: heat = ถูกใช้บ่อย · time-decay = ความสด → รวมเป็น score เดียวได้
- λ คุมความชัน: decay เร็ว (ข่าว) vs ช้า (ความรู้ evergreen)

---

## 61.3 geo + vector (ถ้ามี location)

```
"ร้านกาแฟบรรยากาศดี (semantic) ใกล้ฉัน (geo)"
→ vector: "บรรยากาศดี" · geo: distance(user, shop) < radius
→ score = relevance × geo_decay(distance)  (คล้าย time-decay §61.2)
```
- geo index (R-tree/geohash) + vector → filtered (Ch55) · ARRA personal ไม่ค่อยมี geo แต่หลักเดียวกัน

---

## 61.4 faceted navigation

```
facet = มิติจัดกลุ่ม (folder, tag, type, author, ปี)
UI: ค้น semantic → แสดง facet count ("15 ใน AI, 8 ใน Research") → user drill down
→ vector search + aggregate by facet (group count) → นำทางผลลัพธ์
```
- ต่าง search engine (facet = feature มาตรฐาน) · ARRA เก็บ metadata (Ch51) → facet ได้

---

## 61.5 ⭐ รวม signal หลายแกนเป็น score เดียว

```
final = w₁·vector_sim + w₂·heat(Ch13) + w₃·recency(§61.2) + w₄·boost(facet match)
```
- นี่คือ **ranking function** เต็มรูป (ต่อยอด RRF Ch11 + confidenceWeight Ch4)
- ⚠️ scale (Ch56 §56.1): แต่ละ signal คนละหน่วย → normalize/rank ก่อนรวม (RRF ช่วย)
- tune weight บน eval (Ch56 §56.4) — อย่าเดา

---

## 61.6 เชื่อม ARRA

```
metadata (Ch51): folder/tag/date/source → facet + numeric filter (§61.1/61.4)
heat (Ch13) + recency (§61.2) → doc ที่ทั้ง relevant+ใช้บ่อย+สด ขึ้นก่อน
confidenceWeight 0.25 (Ch4) → 1 ในหลาย signal ที่ถ่วง fused score
→ ARRA รวม vector + structured (date/folder) + heat = ranking หลายแกน
```
- **community**: "ค้นเฉพาะโน้ตปีนี้ในโฟลเดอร์ X ได้ไหม" → ได้ (metadata filter + vector, Ch55/61)

---

## สรุป Ch61
```
query จริง = semantic + structured (numeric/temporal/geo/facet) พร้อมกัน
numeric range: metadata index + filtered-ANN (Ch55), selectivity สำคัญ
⭐ time-decay: score × exp(−λ·age) — ใหม่ได้เปรียบ soft (ไม่ตัด) · รวมกับ heat (Ch13)
geo: distance decay (คล้าย time) + geo index
faceted: vector + aggregate by facet → drill down (metadata Ch51)
⭐ รวม signal: w₁vector+w₂heat+w₃recency+w₄facet → ranking เต็ม (RRF scale-free Ch56, tune eval)
ARRA: metadata filter + heat + recency = ranking หลายแกน
```
**ถัดไป Ch62:** personalization — user context, ทำไม heat (Ch13) เป็น personalization ชั้นแรก, per-user boost, privacy trade-off
---
*grounded: time-decay ranking · numeric/geo filter (Ch55) · faceted search · เชื่อม Ch4/11/13/51/55/56/60 · /loop deep iter 2026-07-16*
