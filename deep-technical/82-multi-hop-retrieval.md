# Deep Technical · Chapter 82 — Multi-Hop / Iterative Retrieval

> ต่อจาก Ch81 · บางคำถามต้องหลายก้าว (ค้น→อ่าน→ค้นต่อ) · บทนี้: decompose, retrieve-reason-retrieve, ทำไม single-shot ไม่พอ

---

## 82.0 ปัญหา — คำถามที่ single retrieval ตอบไม่ได้

```
"เพื่อนร่วมทีมของคนที่เขียน PR #2740 คือใคร"
→ ต้อง 2 ก้าว: (1) ใครเขียน PR #2740? (2) ทีมของคนนั้นมีใคร?
single retrieval: embed คำถามทั้งอัน → ค้นครั้งเดียว → ไม่มี doc ไหนมีคำตอบครบ (ต้องเชื่อม 2 fact)
```
- multi-hop = คำตอบกระจายหลาย doc ที่ต้อง "เชื่อม" ตามลำดับ

---

## 82.1 ⭐ decompose — แตกคำถามเป็นก้าว

```
LLM แตก: "เพื่อนร่วมทีมของคนเขียน PR #2740"
  → sub-q1: "ใครเขียน PR #2740" → retrieve → "คนชื่อ A"
  → sub-q2: "ทีมของ A มีใคร" (ใช้คำตอบ q1!) → retrieve → "B, C"
  → รวม: "B, C"
```
- แต่ละ hop ใช้คำตอบ hop ก่อน → query ถัดไปพึ่ง context สะสม (Ch58 conversational คล้ายกัน)
- **least-to-most**: แตกจากง่าย→ยาก, แก้ทีละก้อน

---

## 82.2 retrieve-reason-retrieve loop (IRCoT)

```
interleave retrieval กับ reasoning (chain-of-thought):
  1. retrieve ตาม query → context
  2. reason 1 step (CoT) จาก context → รู้ว่า "ยังต้องรู้อะไรอีก"
  3. retrieve เพิ่มตามที่ขาด → context เพิ่ม
  4. loop จนตอบได้
```
- ต่างจาก decompose ล่วงหน้า (§82.1): IRCoT ตัดสิน hop ถัดไป **ระหว่างทาง** (dynamic, ไม่รู้ล่วงหน้าว่ากี่ hop)
- เชื่อม FLARE (Ch80) + ReAct (Ch35): reason → act (retrieve) → observe → reason

---

## 82.3 ⚠️ error propagation

```
hop 1 ผิด → hop 2 ใช้คำตอบผิด → ยิ่งผิด (compound error)
  P(ถูกทั้งหมด) = P(hop1) × P(hop2) × ... → ลดลงเร็วตามจำนวน hop
เช่น 3 hop × 0.9 accuracy = 0.73 (แต่ละก้าวดี แต่รวมตก)
```
- แก้: verify แต่ละ hop (Ch72/81 abstain ถ้า hop ไม่มั่นใจ) · backtrack ถ้า dead-end · จำกัดจำนวน hop (กัน loop)

---

## 82.4 termination — รู้เมื่อพอ

```
เมื่อไหร่หยุด hop:
  - LLM บอก "ตอบได้แล้ว" (มี fact ครบ) → stop
  - max hops (เช่น 5) → กัน infinite loop (Ch80 cost)
  - no new info: retrieve แล้วได้ doc ซ้ำเดิม (Ch52 dedup) → หยุด (ไม่คืบ)
```
- balance: หยุดเร็วไป = ตอบไม่ครบ · ช้าไป = เปลือง (Ch70) + error สะสม (§82.3)

---

## 82.5 เทียบ single-shot — เมื่อไหร่ต้อง multi-hop

```
single-shot พอ: คำถามตรง (fact เดียว, "PR #2740 คืออะไร")
multi-hop จำเป็น: เชื่อม fact ("ของคนที่...ของสิ่งที่...") / เปรียบเทียบ / รวมหลายแหล่ง
→ router (Ch79) / adaptive (Ch80): ตรวจว่าคำถามซับซ้อนไหม → เลือก single vs multi-hop
```
- multi-hop แพงกว่า (หลาย retrieve+reason) → ใช้เมื่อจำเป็น (Ch80 adaptive)

---

## 82.6 เชื่อม ARRA

```
ARRA + Claude (Ch15/35): Claude decompose (§82.1) + reason → เรียก ARRA หลาย hop (ReAct)
  hop 1: Claude เรียก ARRA "ใครเขียน PR #2740" → ได้ A
  hop 2: Claude เรียก ARRA "ทีม A" (ใช้ A จาก hop 1) → ได้ B,C
  → Claude orchestrate multi-hop, ARRA = retrieve แต่ละ hop
verify (Ch81): hop ไม่มั่นใจ → Claude abstain/backtrack (§82.3)
→ multi-hop reasoning อยู่ที่ Claude · ARRA = fast single retrieval ต่อ hop (แบ่งหน้าที่ ย้ำ Ch58/75/79)
```
- **community**: "ถามซับซ้อนเชื่อมหลายเรื่องได้ไหม" → ได้ Claude แตก+ค้นหลายรอบ (multi-hop)

---

## สรุป Ch82
```
บางคำถามเชื่อมหลาย fact → single retrieval ตอบไม่ได้ (ไม่มี doc เดียวมีครบ)
⭐ decompose: LLM แตกเป็น sub-q ตามลำดับ (hop N ใช้คำตอบ hop N-1) · least-to-most
⭐ retrieve-reason-retrieve (IRCoT): interleave CoT+retrieve, ตัดสิน hop ระหว่างทาง (dynamic, FLARE Ch80/ReAct Ch35)
⚠️ error propagation: P(ถูก)=Πhop → ตกเร็ว → verify แต่ละ hop (Ch72/81), backtrack, จำกัด hop
termination: LLM พอ / max hops / no new info (dedup Ch52)
single-shot (fact เดียว) vs multi-hop (เชื่อม fact) → adaptive เลือก (Ch79/80)
ARRA+Claude: Claude decompose+orchestrate multi-hop, ARRA=retrieve ต่อ hop
```
**ถัดไป Ch83:** corrective RAG (CRAG) — ประเมิน retrieval quality → ถ้าแย่ค้นใหม่/ค้น web, self-correction, knowledge refinement
---
*grounded: multi-hop QA · decompose/least-to-most · IRCoT (Trivedi 2022) · error propagation · ReAct (Ch35)/FLARE (Ch80) · เชื่อม Ch15/35/52/58/70/72/75/79/80/81 · /loop deep iter 2026-07-16*
