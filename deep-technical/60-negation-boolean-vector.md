# Deep Technical · Chapter 60 — Negation & Boolean + Vector

> ต่อจาก Ch59 · "X แต่ไม่เอา Y" — vector จับ negation แย่มาก · บทนี้: ทำไม embedding "ไม่เข้าใจไม่", boolean + vector รวมกัน

---

## 60.0 ปัญหา — embedding จับ "ไม่" ไม่เก่ง

```
query A: "อาหารมีน้ำตาล"
query B: "อาหารไม่มีน้ำตาล"
→ cos(A, B) สูงมาก! (ต่างแค่ "ไม่" คำเดียว, ส่วนใหญ่เหมือน)
→ vector แยกไม่ค่อยออก → ค้น "ไม่มีน้ำตาล" อาจได้ doc "มีน้ำตาล"
```
- **รากปัญหา**: embedding จับ "หัวข้อ/ความหมายรวม" (topic) → negation เป็นรายละเอียดเล็กที่กลบ

---

## 60.1 ทำไม dense อ่อน negation (เชิงลึก)

```
embedding = เฉลี่ย/รวม signal ของทุก token (Ch2/10 pooling)
"ไม่" = 1 token ในหลายสิบ → contribution เล็ก → กลบด้วย topic words
attention (Ch10) อาจจับ "ไม่" ได้บ้าง แต่ pooling รวมทำให้เจือจาง
```
- งานวิจัยยืนยัน: embedder ยุคปัจจุบันยัง**อ่อน negation/antonym** (จับ "ร้อน" ใกล้ "เย็น" เพราะ topic เดียวกัน = อุณหภูมิ)

---

## 60.2 ⭐ ทางแก้ 1 — boolean + vector (hybrid ช่วย)

```
"เอา X ไม่เอา Y" → แยก:
  vector: ค้น X (semantic)
  boolean/FTS (Ch34): filter OUT doc ที่มี term Y (NOT Y)
→ vector หา relevant + boolean บังคับ exclude → แก้ negation ที่ vector พลาด
```
- **FTS5 (Ch34) รองรับ NOT**: `X NOT Y` → exact exclusion ที่ vector ทำไม่ได้
- นี่คือ **อีกเหตุผลที่ hybrid (Ch41) จำเป็น** — boolean logic ที่ dense ขาด

---

## 60.3 ทางแก้ 2 — negative vector (subtract)

```
concept algebra (Ch2 word2vec สืบทอด):
  query_vec = vec("อาหาร") − β·vec("น้ำตาล")
  → ดันออกจากทิศ "น้ำตาล"
```
- ได้ผลบ้าง (ทิศทางถูก) แต่ **เปราะ** (β เท่าไร? subtract มากไป = เพี้ยน) · ไม่ reliable เท่า boolean (§60.2)

---

## 60.4 ทางแก้ 3 — query understanding แยกเจตนา (Ch57/58)

```
LLM parse: "อาหารคลีนไม่มีน้ำตาล" →
  { positive: ["อาหารคลีน", "สุขภาพ"], negative: ["น้ำตาล", "หวาน"] }
→ vector ค้น positive + filter/rerank ลงโทษ negative
```
- ให้ LLM (ที่เข้าใจ negation) แปลงเป็น structured query → แล้วค่อยค้น → แม่นสุด (แต่ +LLM call)

---

## 60.5 boolean + vector — สถาปัตยกรรม

```
query → parse → { semantic: "...", must: [...], must_not: [...], filter: {...} }
       ↓
  vector search (semantic) ∩ FTS must/must_not (Ch34) ∩ metadata filter (Ch55)
       ↓
  RRF/rerank (Ch11/18) → result
```
- นี่คือ query engine เต็มรูป: vector (fuzzy) + boolean (exact/negation) + filter (scope) รวมกัน
- ARRA hybrid (Ch4) มี vector+FTS → boolean negation ทำได้ผ่าน FTS NOT

---

## 60.6 เชื่อม ARRA / community

```
"ค้น X ไม่เอา Y" → vector อย่างเดียวพลาด (§60.0) → ใช้ FTS NOT (Ch34) เสริม (§60.2)
→ อีกเหตุผลที่ ARRA เป็น hybrid ไม่ใช่ vector ล้วน (Ch41)
สอน community: "vector ไม่เข้าใจคำว่าไม่ดีนัก → ใช้ FTS/keyword ช่วยกรองออก"
  = insight สำคัญ (คนคิดว่า vector เก่งทุกอย่าง แต่ negation คือจุดอ่อนจริง)
```

---

## สรุป Ch60
```
⚠️ embedding จับ "ไม่" แย่: cos("มีน้ำตาล","ไม่มีน้ำตาล") สูง (ต่างแค่ 1 token, topic กลบ)
ราก: pooling เฉลี่ย token → "ไม่" เจือจาง · embedder อ่อน negation/antonym (ร้อน≈เย็น)
⭐ แก้ 1: boolean+vector — FTS NOT (Ch34) exclude term ที่ vector พลาด → hybrid จำเป็น (Ch41)
แก้ 2: negative vector subtract (เปราะ, β ยาก)
แก้ 3: LLM parse เจตนา (positive/negative) → structured query (แม่นสุด, +LLM)
สถาปัตยกรรม: vector(fuzzy) ∩ boolean(exact/NOT) ∩ filter(scope) → query engine เต็ม
สอน: vector ไม่เข้าใจ "ไม่" → keyword/FTS ช่วยกรอง (insight คนมักเข้าใจผิด)
```
**ถัดไป Ch61:** faceted & structured + vector — ผสม SQL/structured filter กับ vector, time-decay, geo, numeric range + semantic
---
*grounded: negation ใน dense embedding (งานวิจัย antonym) · FTS5 NOT (Ch34) · concept algebra (Ch2) · เชื่อม Ch2/10/11/18/34/41/55/57 · /loop deep iter 2026-07-16*
