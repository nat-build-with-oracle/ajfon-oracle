# Deep Technical · Chapter 58 — Conversational / Multi-Turn Retrieval

> ต่อจาก Ch57 · ARRA อยู่ใน Claude Code (บทสนทนา) → query ไม่ได้มาโดดๆ · บทนี้: coreference, context carry-over, ค้นในบทสนทนาต่อเนื่อง

---

## 58.0 ปัญหา — query พึ่งบริบทก่อนหน้า

```
user: "PR #2740 เรื่องอะไร"
assistant: (ตอบเรื่อง drift benchmark)
user: "แล้ว มัน แก้ยังไง"    ← "มัน" = PR #2740 (ต้องรู้จากบริบท)
```
ถ้า embed "แล้วมันแก้ยังไง" ตรงๆ → ไร้บริบท → ค้นมั่ว · ต้อง **resolve** ก่อน

---

## 58.1 ⭐ coreference resolution

แทนสรรพนาม/อ้างอิงด้วยของจริงจากบริบท:
```
"แล้วมันแก้ยังไง" + history → rewrite → "PR #2740 แก้ drift benchmark ยังไง"
→ embed query ที่ resolve แล้ว → ค้นตรง
```
- ทำด้วย: LLM rewrite (ให้ history + query → standalone query) — เป็น query rewriting (Ch57 §57.4) แบบพึ่ง context
- **standalone query**: query ที่เข้าใจได้โดยไม่ต้องดู history → embed แล้วค้นได้ถูก

---

## 58.2 context carry-over — เอาบริบทเข้า retrieval

```
วิธี A (query rewrite, §58.1): รวม history → standalone query → embed 1 อัน
วิธี B (concat):               embed [history ล่าสุด + query] รวม → แต่ noise เยอะ (history ยาว)
วิธี C (weighted):             embed query หลัก + embed context → รวม weighted (query เด่น)
```
- **A ดีสุดปกติ**: สะอาด (LLM สกัดเฉพาะที่เกี่ยว) · B/C เสี่ยง context ท่วม query

---

## 58.3 topic shift — รู้เมื่อบริบทเปลี่ยน

```
user คุยเรื่อง A ยาว → เปลี่ยนไปเรื่อง B ("เอาล่ะ เปลี่ยนเรื่อง...")
→ ถ้ายัง carry-over context A → ค้นเรื่อง B เพี้ยน (A ปน)
→ ต้อง detect topic shift → reset context (ไม่ carry A)
```
- signal: query ใหม่ similar ต่ำกับ history (vector Ch1!) → น่าจะเปลี่ยนเรื่อง → ลด carry-over
- meta: cosine(query_ใหม่, context_เก่า) ต่ำ → topic shift

---

## 58.4 retrieval history เป็น context เอง

```
สิ่งที่ค้นเจอก่อนหน้าในบทสนทนา = บริบท (อาจไม่ต้องค้นซ้ำ)
user ถามต่อยอด doc ที่เพิ่งค้นเจอ → ใช้ doc นั้นเลย (cache Ch32) ไม่ต้องค้นใหม่
→ conversational cache: จำ doc ที่ดึงมาในเทิร์นก่อน
```
- ARRA ใน Claude Code: context window ถือ doc ที่ค้นเจอแล้ว → ต่อยอดได้โดยไม่ query ซ้ำ (Ch32 หลักการ)

---

## 58.5 multi-turn + agentic (เชื่อม Ch35)

```
บทสนทนายาว + agent (Ch35): แต่ละเทิร์น agent อาจ retrieve หลายรอบ (ReAct)
→ conversational retrieval ซ้อน agentic retrieval:
   เทิร์นนี้ query อะไร (จาก dialog) → agent ตัดสิน retrieve กี่รอบ (Ch35)
```
- ARRA = tool ที่ Claude เรียก (Ch15/35) · Claude ถือ dialog + ตัดสินใจ resolve+retrieve → conversational logic อยู่ที่ Claude, ARRA แค่ค้นให้ตรง

---

## 58.6 เชื่อม ARRA

```
ARRA ใน Claude Code (Ch15): Claude ถือ dialog → resolve coreference (§58.1) → query standalone → เรียก ARRA
topic shift (§58.3): Claude รู้บริบทเปลี่ยน → query ใหม่สะอาด
conversational cache (§58.4): doc ในcontext window → ต่อยอดไม่ query ซ้ำ
→ ARRA ไม่ต้องจัดการ dialog เอง — Claude ทำ (แบ่งหน้าที่ชัด: Claude=บริบท, ARRA=ค้น)
```
- **community**: "ถามต่อเนื่องแบบคุยได้ไหม" → ได้ เพราะ Claude resolve บริบทให้ก่อนเรียก ARRA

---

## สรุป Ch58
```
ปัญหา: query พึ่ง history ("มัน/อันนั้น") → embed ตรงๆ ไร้บริบท → ค้นมั่ว
⭐ coreference: LLM rewrite history+query → standalone query → embed ค้นตรง (Ch57 rewriting)
carry-over: query-rewrite (A, สะอาดสุด) > concat (B) > weighted (C)
topic shift: cosine(query ใหม่, context เก่า) ต่ำ → reset context (ใช้ vector เอง Ch1)
conversational cache: doc ที่เพิ่งค้น = context → ต่อยอดไม่ query ซ้ำ (Ch32)
ARRA+Claude Code: Claude=dialog/resolve, ARRA=ค้น (แบ่งหน้าที่ชัด, Ch15/35)
```
**ถัดไป Ch59:** result diversity (MMR) — top-k ซ้ำกันเอง (redundant) → MMR balance relevance vs diversity, ทำไม top-k ที่หลากหลายดีกว่า
---
*grounded: coreference/query rewriting · topic shift (vector similarity) · conversational RAG · เชื่อม Ch1/15/32/35/57 · /loop deep iter 2026-07-16*
