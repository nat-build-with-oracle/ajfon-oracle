# Deep Technical · Chapter 35 — Agentic Retrieval Loop

> ต่อจาก Ch34 · retrieval ไม่ต้องเป็น single-shot · agent ค้นซ้ำ อ่าน คิด ค้นใหม่ได้ · เชื่อม Ch skill /ralph-dig, /seek

---

## 35.0 single-shot ไม่พอสำหรับคำถามซับซ้อน

```
single-shot: query → retrieve → answer
   พอสำหรับ "หาโน้ตเรื่อง X"
   ไม่พอสำหรับ "เปรียบเทียบ method A vs B แล้วสรุป gap"
      → ต้องค้น A, ค้น B, อ่าน, หา gap, อาจค้นเพิ่ม
```
agentic = agent คุม loop retrieval เอง (retrieve-read-reason-repeat)

---

## 35.1 Self-Query — agent ตัดสินใจค้นอะไร/ยังไง

แทน user query ตรงๆ → agent แปลงเป็น structured search:
```
user: "งานวิจัยเบาหวานปี 2023 ที่ใช้ deep learning"
agent → { semantic: "deep learning diabetes", filter: {year: 2023, type: paper} }
```
- agent สกัด filter (Ch26 metadata) + semantic ออกจาก natural language → ค้นแม่นขึ้น
- เชื่อม Ch29 (query understanding) แต่ agent ทำ dynamic ตามบริบท

---

## 35.2 ReAct — Retrieve-Read-Reason loop

```
loop:
  Thought:  "ต้องรู้ X ก่อน"
  Action:   search(X)                    ← retrieve (Ch4)
  Observation: [results]                 ← read
  Thought:  "ยังขาด Y, ค้นต่อ"
  Action:   search(Y)
  ...
  Thought:  "พอแล้ว สรุปได้"
  Answer:   synthesize
```
- agent สลับ reasoning ↔ retrieval จนข้อมูลพอ · แต่ละรอบ query ปรับตาม observation ก่อนหน้า
- = /seek ของ ARRA (Ch skill: trace+dig+prove รวม, escalate ตามต้องการ)

---

## 35.3 Query Decomposition

คำถามซับซ้อน → แตกเป็น sub-question:
```
"AI ช่วยลด HbA1c ได้ดีกว่ายาแผนปัจจุบันไหม"
  → sub1: "AI ลด HbA1c ได้เท่าไร" 
  → sub2: "ยาแผนปัจจุบันลด HbA1c ได้เท่าไร"
  → ค้นแต่ละ sub → รวมคำตอบ → เปรียบเทียบ
```
- แต่ละ sub เป็น query ชัด → retrieve แม่นกว่าคำถามใหญ่กำกวม · แล้ว compose

---

## 35.4 Iterative Refinement — ค้นจน "ไม่เจอใหม่"

เชื่อม Ch skill /ralph-dig (loop-until-dry pattern):
```
seen = {}
loop until K รอบติดไม่เจอใหม่:
   results = search(query, ปรับจาก gap รอบก่อน)
   fresh = results − seen
   if fresh ว่าง: dry_count++
   else: dry_count=0; seen += fresh; query = refine(query, fresh)
```
- ครอบคลุมกว่า single-shot (เก็บ tail ที่ query แรกพลาด, Ch community-ask "หาให้ครบ")
- **loop-until-dry**: หยุดเมื่อ K รอบติดไม่มีอะไรใหม่ (ไม่ใช่จำนวนคงที่) — จับ long-tail

---

## 35.5 Retrieval + generation interleave (self-RAG)

agent ตัดสินใจ**เมื่อไรควร retrieve** (ไม่ใช่ retrieve ทุกครั้ง):
```
- คำถามที่รู้อยู่แล้ว → ตอบเลย (ไม่ retrieve, ประหยัด Ch24)
- คำถามที่ต้องหลักฐาน → retrieve + cite (Ch26 §26.4)
- ตอบแล้ว self-critique: "มั่นใจไหม? ต้องหาเพิ่ม?" → retrieve เสริม
```
- ลด retrieval ที่ไม่จำเป็น + เพิ่มตรงที่ต้องการหลักฐาน → คุณภาพ+ประหยัด

---

## 35.6 ARRA agentic skills (เชื่อมของจริง)

```
/trace  → single/smart escalation (Ch skill)
/seek   → trace+dig+prove loop (ReAct-ish, §35.2)
/ralph-dig → loop-until-dry excavator (§35.4), Oracle MCP first
Agent A/B/C (Ch ajfon use-case C): research→writing→review = multi-agent retrieval pipeline
```
- Claude Code (agent) เรียก muninn_search (Ch15) ใน loop = agentic retrieval โดยธรรมชาติ
- **caveat cost** (Ch24/Ch agentic): ทุกรอบ = embed+search+LLM · loop ลึก = แพง → ต้อง budget/stop condition (Ch16 reliability: 85%^n)

---

## สรุป Ch35
```
single-shot ไม่พอคำถามซับซ้อน → agentic loop
self-query (สกัด filter+semantic) · ReAct (retrieve-read-reason repeat = /seek)
decomposition (แตก sub-query) · iterative refine (loop-until-dry = /ralph-dig)
self-RAG (ตัดสินใจเมื่อไรค้น) → ประหยัด + cite ตรงที่ต้อง
ARRA: /trace /seek /ralph-dig + Agent A/B/C = agentic retrieval จริง (ระวัง cost 85%^n)
```
**ถัดไป Ch36:** Matryoshka embeddings + dimensionality reduction — nested dims, adaptive retrieval (coarse low-dim → fine full-dim), PCA
---
*grounded: ReAct (Yao 2022) · self-RAG (Asai 2023) · query decomposition · เชื่อม Ch skill (/seek //ralph-dig), Ch ajfon (Agent A/B/C), Ch16/24 (cost), Ch29 · /loop deep iter 2026-07-14*
