# Deep Technical · Chapter 81 — Retrieval Confidence & Abstention

> ต่อจาก Ch80 · บางที "ไม่เจอ" คือคำตอบที่ถูก · บทนี้: score threshold, calibration, ทำไม abstain (บอกไม่รู้) สำคัญกว่าตอบมั่ว

---

## 81.0 ปัญหา — ANN คืน top-k เสมอ (แม้ไม่มีอะไรเกี่ยว)

```
query "สูตรทำระเบิด" ใน second brain เรื่องทำอาหาร → ANN ยังคืน top-k!
(ANN หา "ใกล้สุด" เสมอ — แม้ "ใกล้สุด" จะ cos=0.2 = ไม่เกี่ยวจริง)
→ ป้อน LLM → LLM ตอบจาก doc ไม่เกี่ยว → มั่ว (Ch75 noise)
→ ควร abstain: "ไม่มีข้อมูลเรื่องนี้ใน vault"
```

---

## 81.1 ⭐ score threshold — cutoff ความเกี่ยว

```
คืน result เฉพาะที่ score เกิน threshold:
  cos > τ (เช่น 0.5) → เกี่ยวพอ, คืน
  cos ≤ τ → ไม่เกี่ยว, ทิ้ง
  ถ้าไม่มีตัวไหนผ่าน → abstain ("ไม่เจอ")
```
- ⚠️ **τ ตั้งยาก**: ขึ้นกับ embedder (anisotropy Ch43 → cos คู่สุ่มสูง), domain, query type
- **relative threshold**: top-1 score เทียบ top-2 (gap ใหญ่ = มั่นใจ) หรือเทียบ background distribution

---

## 81.2 calibration — score บอกความน่าจะเป็นจริงไหม

```
cos=0.8 หมายถึง "relevant 80%" จริงไหม? → มัก ไม่ (score ไม่ calibrated)
calibration: map raw score → P(relevant) จริง (เช่น Platt scaling, isotonic regression)
  เก็บ (score, จริงเกี่ยวไหม) จาก feedback (Ch63) → fit mapping
→ หลัง calibrate: threshold บน P(relevant) ตีความได้ (0.5 = น่าจะเกี่ยว)
```
- reranker (Ch18 cross-encoder) score มัก calibrate ดีกว่า bi-encoder cos (เห็น interaction)

---

## 81.3 ⭐ ทำไม abstain > ตอบมั่ว

```
second brain / RAG: user เชื่อว่าคำตอบมาจากข้อมูลจริง (grounded, Ch75)
ตอบมั่วจาก doc ไม่เกี่ยว → user เชื่อผิด → เสียหายกว่าไม่ตอบ!
"ไม่พบข้อมูลเรื่องนี้" = คำตอบที่ซื่อสัตย์ + ให้ user รู้ว่าต้องหาที่อื่น
```
- **trust (Ch73)**: ระบบที่ยอมบอก "ไม่รู้" น่าเชื่อกว่าระบบที่ตอบทุกอย่าง (บางอันมั่ว)
- เชื่อม hallucination (Ch42): abstain = ทางเลือกแทน hallucinate เมื่อไม่มี ground

---

## 81.4 abstention strategies

```
1. hard threshold: ไม่มี result > τ → "ไม่เจอ" (§81.1)
2. LLM judge: ให้ LLM ประเมิน "context ตอบ query ได้ไหม" → ถ้าไม่ → abstain (Self-RAG [Supported?] Ch80)
3. coverage check: query มี aspect ที่ retrieval ไม่ครอบ → บอกบางส่วน + ระบุที่ขาด
4. confidence report: ตอบ + บอกระดับมั่นใจ ("พบข้อมูลบางส่วน, ความมั่นใจปานกลาง")
```
- graceful: ไม่ใช่แค่ yes/no → บอกว่ามีแค่ไหน (partial answer + gap)

---

## 81.5 ⚠️ over-abstention — ระวังอีกด้าน

```
threshold สูงไป → abstain บ่อยเกิน → "ไม่เจอ" ทั้งที่มี (false negative)
→ user หงุดหงิด (ระบบขี้เกียจหา)
สมดุล: threshold ที่ balance false-abstain vs false-answer (ตาม cost แต่ละแบบ, Ch74 metric)
```
- domain sensitive: การแพทย์ → abstain ดีกว่าเดา (cost ตอบผิดสูง) · casual → ตอบไว้ก่อน (cost ต่ำ)

---

## 81.6 เชื่อม ARRA

```
threshold (§81.1): ARRA มี score (cos Ch4, rrf fusedScore Ch11, confidenceWeight 0.25) → ตั้ง cutoff ได้
abstain (§81.3): result ต่ำกว่า threshold → Claude บอก "ไม่พบใน vault" (แทนเดา, Ch80 reflection)
calibration (§81.2): reranker (Ch18) ช่วย score น่าเชื่อขึ้น → threshold แม่นขึ้น
→ ARRA + Claude: ARRA ให้ score → Claude ตัดสิน abstain/ตอบ (Self-RAG [Supported?] Ch80)
```
- **community**: "ถ้าไม่มีข้อมูลจะตอบมั่วไหม" → ไม่ (threshold + Claude reflect → บอก "ไม่เจอ") = **ซื่อสัตย์ = เชื่อได้**

---

## สรุป Ch81
```
⚠️ ANN คืน top-k เสมอ (แม้ cos=0.2 ไม่เกี่ยว) → ป้อน LLM → มั่ว → ควร abstain
⭐ score threshold: cos>τ คืน, ไม่มีผ่าน→"ไม่เจอ" · τ ตั้งยาก (anisotropy Ch43) → relative/gap
calibration: raw score→P(relevant) จริง (Platt/isotonic + feedback Ch63) · reranker (Ch18) calibrate ดีกว่า
⭐ abstain > ตอบมั่ว: RAG user เชื่อว่า grounded → มั่ว=เสียหายกว่าไม่ตอบ (trust Ch73, สู้ hallucination Ch42)
strategies: hard threshold / LLM judge (Ch80) / coverage check / confidence report (partial+gap)
⚠️ over-abstention: threshold สูงไป→false negative → balance (domain: การแพทย์ abstain, casual ตอบ)
ARRA+Claude: ARRA score → Claude ตัดสิน abstain (ซื่อสัตย์=เชื่อได้)
```
**ถัดไป Ch82:** multi-hop / iterative retrieval — คำถามต้องหลายก้าว ("เพื่อนร่วมงานของคนที่เขียน PR X คือใคร"), decompose, retrieve-reason-retrieve
---
*grounded: score threshold/calibration (Platt/isotonic) · abstention · Self-RAG [Supported?] (Ch80) · anisotropy (Ch43) · เชื่อม Ch4/11/18/42/43/63/73/74/75/80 · /loop deep iter 2026-07-16*
