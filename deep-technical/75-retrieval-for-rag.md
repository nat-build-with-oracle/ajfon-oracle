# Deep Technical · Chapter 75 — Retrieval for RAG (Context Assembly)

> ต่อจาก Ch74 · retrieval เจอ doc แล้ว → ป้อน LLM ยังไงให้ตอบดี · บทนี้: context assembly, lost-in-the-middle, token budget packing

---

## 75.0 retrieval เป็นครึ่งเดียวของ RAG

```
RAG = Retrieval + Generation
retrieval เจอ top-k ดี (Ch1-74) → แต่ยัง LLM ยังไง = อีกครึ่งที่กระทบคำตอบ
→ context assembly: เรียง/ตัด/รวม top-k เป็น prompt context
```
- doc ดีแต่ประกอบ context แย่ → LLM ตอบแย่ (retrieval เปล่าประโยชน์)

---

## 75.1 ⭐ lost-in-the-middle — ตำแหน่งใน context กระทบ

งานวิจัยสำคัญ: LLM ให้ความสำคัญ **ต้นและท้าย** context มากกว่ากลาง:
```
context: [doc1 doc2 doc3 doc4 doc5]
LLM attention:  สูง(ต้น) → ต่ำ(กลาง) → สูง(ท้าย)   (U-shape)
→ doc สำคัญวางกลาง → LLM "มองข้าม" → ตอบพลาดทั้งที่ retrieval เจอ!
```
- **implication**: อย่าเรียง context ตาม rank ดิบ (relevant สุดอยู่ที่ 1 = ต้น ✓ แต่ที่ 3 อยู่กลาง ✗)
- **แก้**: วาง doc relevant สุดที่ **ต้นและท้าย** (relevant สูง→ขอบ, ต่ำ→กลาง)

---

## 75.2 context ordering strategies

```
1. relevance order: rank 1 ต้นสุด → rank k ท้าย (ง่าย แต่ lost-in-middle §75.1)
2. ⭐ reordered (U-shape): relevant สุด→ต้น+ท้าย, รองลงมา→กลาง (สู้ lost-in-middle)
3. chronological: เรียงตามเวลา (ถ้า temporal สำคัญ, Ch61)
4. grouped: doc จาก source เดียวกันติดกัน (coherence)
```
- reorder (U-shape) มัก win สำหรับ QA · แต่ขึ้นกับ task → วัด (Ch74)

---

## 75.3 ⭐ token budget packing

context window จำกัด (เช่น 8k/128k token) → เลือกใส่อะไร:
```
budget = context_limit − prompt_overhead − expected_output
เลือก top-k doc ที่ fit budget:
  greedy: ใส่ rank 1,2,3... จนเต็ม budget
  ⭐ diversity-aware (MMR Ch59): ใส่ relevant + ไม่ซ้ำ → ครอบคลุมใน budget เท่ากัน
  compression: สรุป doc ยาว → ใส่ได้เยอะขึ้น (trade detail)
```
- **trade**: ใส่เยอะ (recall context) vs ใส่น้อยแต่ตรง (precision, ลด noise) → มัก precision ชนะ (Ch75 §75.4)

---

## 75.4 ⚠️ noise ใน context ทำ LLM แย่

```
ใส่ doc ไม่เกี่ยว (rank ต่ำ) เข้า context → LLM สับสน → ตอบแย่ลง (distraction)
→ "more context ≠ better" — irrelevant doc = noise
→ rerank (Ch18) + threshold: ใส่เฉพาะ doc ที่ score เกิน cutoff (ตัดหางที่ไม่มั่นใจ)
```
- **precision > recall สำหรับ RAG context**: 3 doc ตรง > 10 doc ปน noise
- เชื่อม dedup (Ch52) + MMR (Ch59): ตัดซ้ำ+noise → context สะอาด

---

## 75.5 context กับ provenance (Ch26)

```
แต่ละ doc ใน context แนบ source → LLM cite ได้ ("ตาม [ไฟล์ X]...")
→ คำตอบ verifiable (Ch26) → user เชื่อ + ตรวจได้ (Ch73 trust)
format: [source: notes/x.md] <content> → LLM อ้างอิงกลับ
```
- นี่ทำให้ RAG ตอบแบบ grounded + traceable (ต่างจาก LLM เดาเปล่า, Ch42 hallucination)

---

## 75.6 เชื่อม ARRA

```
ARRA (Ch15) เป็น retrieval tool ให้ Claude Code:
  ARRA เจอ top-k (hybrid Ch4) → Claude ประกอบ context เอง (ordering/budget อยู่ที่ Claude)
  → ARRA รับผิดชอบ "เจอ doc ตรง" · Claude รับผิดชอบ "ประกอบ+ตอบ"
rerank (Ch18) + threshold → ARRA ส่ง doc คุณภาพ (precision) → Claude ไม่เจอ noise (§75.4)
provenance (Ch26) → ARRA แนบ source → Claude cite ได้ (§75.5)
→ แบ่งหน้าที่: ARRA=retrieval quality, Claude=context assembly (คู่ Ch58 dialog split)
```
- **community**: "เอา second brain ไปให้ AI ตอบยังไง" → ARRA เจอ+cite, Claude เรียบเรียง → grounded answer

---

## สรุป Ch75
```
RAG = retrieval + generation → context assembly = ครึ่งที่กระทบคำตอบ (doc ดีแต่ประกอบแย่=เสีย)
⭐ lost-in-the-middle: LLM ให้ค่าต้น+ท้าย > กลาง (U-shape) → doc สำคัญกลาง=ถูกมองข้าม
ordering: reorder U-shape (relevant→ขอบ) สู้ lost-in-middle > relevance order ดิบ
⭐ token budget packing: greedy/MMR(Ch59 diversity)/compression fit context limit
⚠️ noise: irrelevant doc=distraction → precision>recall (rerank Ch18+threshold, dedup Ch52)
provenance (Ch26): แนบ source→LLM cite→verifiable (สู้ hallucination Ch42)
ARRA=retrieval quality (เจอ+cite), Claude=context assembly (เรียง+ตอบ) — แบ่งหน้าที่
```
**ถัดไป Ch76:** chunk vs document retrieval — ค้น chunk เล็ก (precise) แต่ context ต้องการ doc เต็ม, parent-child, small-to-big retrieval
---
*grounded: lost-in-the-middle (Liu 2023) · context ordering · token budget · precision>recall RAG · provenance (Ch26) · เชื่อม Ch4/15/18/26/42/52/58/59/61/74 · /loop deep iter 2026-07-16*
