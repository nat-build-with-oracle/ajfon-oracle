# Deep Technical · Chapter 80 — Adaptive Retrieval (Self-RAG / FLARE)

> ต่อจาก Ch79 · ไม่ใช่ทุก query ต้องค้น + ไม่ใช่ค้นครั้งเดียวพอ · บทนี้: decide when to retrieve, self-reflection, active retrieval

---

## 80.0 ปัญหา — retrieve เสมอ = เปลือง+ noise

```
query "2+2 เท่าไร" → ค้น vault? ไม่จำเป็น (LLM ตอบเองได้)
query "สรุป PR #2740" → ต้องค้น (LLM ไม่รู้ข้อมูลเฉพาะเรา)
→ ค้นเสมอ = เปลือง (Ch70) + เสี่ยง noise (Ch75 §75.4 doc ไม่เกี่ยว→ตอบแย่)
→ ค้นเมื่อจำเป็น = adaptive
```

---

## 80.1 ⭐ when to retrieve — retrieve-or-not

```
สัญญาณว่าควรค้น:
  - query ถามข้อมูลเฉพาะ/ล่าสุด (นอก parametric knowledge ของ LLM, Ch42)
  - LLM uncertain (low confidence ตอนจะตอบ, §80.3)
  - มี entity/reference ที่ต้อง ground (ชื่อเฉพาะ, PR#, ไฟล์)
ไม่ต้องค้น:
  - common knowledge / คำนวณ / reasoning ล้วน
  - context มีคำตอบแล้ว (conversational cache Ch58)
```
- **Self-RAG**: LLM ออก token พิเศษ [Retrieve] / [No-Retrieve] → ตัดสินเอง (train มาให้ reflect)

---

## 80.2 ⭐ FLARE — active retrieval ระหว่าง generate

แทนค้นครั้งเดียวตอนเริ่ม → ค้น **ระหว่าง** generate เมื่อจะพูดสิ่งที่ไม่มั่นใจ:
```
1. LLM generate ประโยคถัดไป (ชั่วคราว)
2. ถ้า token confidence ต่ำ (จะพูดข้อเท็จจริงที่ไม่มั่นใจ) → หยุด
3. ใช้ประโยคนั้นเป็น query → retrieve → ได้ context
4. generate ใหม่ด้วย context → มั่นใจขึ้น → ต่อ
```
- **anticipatory**: ค้นสิ่งที่ "กำลังจะเขียน" (forward-looking) ไม่ใช่แค่ query ต้น
- เหมาะคำตอบยาว/หลายข้อเท็จจริง (แต่ละส่วนอาจต้อง ground ต่างกัน)

---

## 80.3 confidence signal — วัดความมั่นใจ

```
token probability: LLM logprob ต่ำ = ไม่มั่นใจ (จะ hallucinate) → trigger retrieve
entropy: distribution แบนราบ (หลาย token เป็นไปได้) = uncertain
verbalized: ถาม LLM ตรงๆ "มั่นใจแค่ไหน 0-1" (แต่ calibration ไม่ดีเสมอ)
```
- ⚠️ LLM confidence calibration ไม่สมบูรณ์ (มั่นใจผิดได้) → ใช้เป็น signal ไม่ใช่ ground truth

---

## 80.4 self-reflection loop (Self-RAG เต็ม)

```
retrieve → LLM ประเมิน context: [Relevant?] doc เกี่ยวไหม
        → generate → [Supported?] คำตอบมี doc รองรับไหม (ไม่ hallucinate)
        → [Useful?] ตอบตรงคำถามไหม
ถ้าไม่ผ่าน → retrieve ใหม่ / generate ใหม่ (loop)
```
- reflection = quality gate ในตัว (คล้าย verify Ch72 แต่ runtime) → ลด hallucination (Ch42)

---

## 80.5 ต้นทุน vs คุณภาพ

```
always-retrieve: ง่าย, recall สูง, แต่เปลือง+noise (§80.0)
adaptive (Self-RAG/FLARE): ประหยัด+แม่นขึ้น, แต่ +LLM calls (reflect/confidence) + ซับซ้อน
→ trade: adaptive คุ้มเมื่อ query หลากหลาย (บางอันไม่ต้องค้น) + คำตอบยาว (FLARE)
```
- simple: retrieve เสมอ + rerank+threshold (Ch75) กัน noise = พอสำหรับหลาย use case
- ARRA: Claude ตัดสินค้นหรือไม่ (adaptive โดยธรรมชาติ, §80.6)

---

## 80.6 เชื่อม ARRA

```
ARRA = tool ที่ Claude เรียก (Ch15): Claude ตัดสิน "ค้น ARRA ไหม" = retrieve-or-not (§80.1) ฟรี!
  query common → Claude ตอบเอง (ไม่เรียก ARRA) · query เฉพาะ vault → เรียก ARRA
multi-hop/active (§80.2): Claude เรียก ARRA หลายครั้ง (agentic Ch35) เมื่อต้องข้อมูลเพิ่ม
reflection (§80.4): Claude ประเมิน result ARRA เกี่ยวไหม → ค้นใหม่ถ้าไม่ (Ch35 ReAct)
→ Claude เป็น Self-RAG controller โดยธรรมชาติ · ARRA = retrieval ที่ถูกเรียกแบบ adaptive
```
- **community**: "ระบบค้นทุกครั้งเลยไหม" → ไม่ Claude ตัดสิน (ถามทั่วไปตอบเอง, ถามเฉพาะค้น ARRA)

---

## สรุป Ch80
```
retrieve เสมอ=เปลือง(Ch70)+noise(Ch75) → adaptive: ค้นเมื่อจำเป็น
⭐ retrieve-or-not (Self-RAG): LLM ออก [Retrieve]/[No-Retrieve] · ค้นเมื่อ query เฉพาะ/uncertain/มี entity
⭐ FLARE active: ค้นระหว่าง generate เมื่อ token confidence ต่ำ (anticipatory, forward-looking)
confidence signal: logprob/entropy/verbalized (⚠️ calibration ไม่สมบูรณ์)
self-reflection: [Relevant?][Supported?][Useful?] → loop retrieve/generate ใหม่ (quality gate, ลด hallucination Ch42)
trade: adaptive ประหยัด+แม่น แต่ +LLM calls · simple=retrieve+threshold (Ch75) พอ
ARRA: Claude ตัดสินค้นหรือไม่ (retrieve-or-not ฟรี) = Self-RAG controller (Ch15/35)
```
**ถัดไป Ch81:** retrieval confidence & abstention — เมื่อไหร่ควรบอก "ไม่เจอ/ไม่รู้" แทนตอบมั่ว, score threshold, calibration, ทำไม abstain สำคัญกว่าตอบผิด
---
*grounded: Self-RAG (Asai 2023) · FLARE (Jiang 2023) · confidence/calibration · ReAct reflection (Ch35) · เชื่อม Ch15/35/42/58/70/72/75 · /loop deep iter 2026-07-16*
