# Deep Technical · Chapter 42 — Retrieval-Augmented Training (RETRO / REALM)

> ต่อจาก Ch41 · ทุกอย่างก่อนนี้ = retrieval ตอน **inference** (ค้นแล้วป้อน LLM) · แต่ retrieval ทำตอน **train** ได้ด้วย · บทนี้: RETRO/REALM + implication กับ second brain

---

## 42.0 2 จุดที่ retrieval เข้าโมเดล

```
inference-time (RAG, ที่คุยมาทั้ง reference):
   query → retrieve → ยัด context เข้า LLM → generate
   โมเดล frozen · retrieval เป็น "external memory" ตอนใช้

training-time (RETRO/REALM):
   ระหว่าง pretrain โมเดลก็ retrieve → เรียนที่จะ "ใช้" ความรู้ภายนอก
   โมเดลถูก train ให้พึ่ง retrieval → เก็บ knowledge น้อยลงในพารามิเตอร์
```

---

## 42.1 REALM — retrieval เป็น latent variable

REALM (2020): pretrain LM ที่ retrieve document มาช่วยทำนาย masked token:
```
P(y|x) = Σ  P(y | x, z) · P(z | x)
         z∈docs
```
- `z` = document ที่ retrieve (latent) · โมเดลเรียน **ทั้ง retriever และ reader พร้อมกัน**
- backprop ผ่าน retrieval → retriever ดีขึ้นเพื่อช่วย LM (end-to-end)
- **ท้าทาย**: retrieve จาก corpus ใหญ่ต้อง re-index ระหว่าง train (async, MIPS)

---

## 42.2 ⭐ RETRO — retrieval ตอน pretrain (scale)

RETRO (DeepMind 2021): LM ที่ retrieve chunk ระหว่าง generate ทุกช่วง:
```
- แบ่ง input เป็น chunk (64 tokens)
- แต่ละ chunk retrieve k-NN chunk จาก database ใหญ่ (2 trillion tokens!)
- chunked cross-attention: โมเดล attend ทั้ง input + retrieved chunks
```
- **ผลลัพธ์ที่ช็อก**: RETRO 7.5B พารามิเตอร์ ≈ GPT-3 175B บนบาง task → **retrieval แทนพารามิเตอร์ได้** (25× เล็กกว่า)
- ความรู้ไม่ต้องอยู่ในน้ำหนัก — อยู่ใน database ที่ retrieve ได้

---

## 42.3 implication ใหญ่ — memory > parameters

```
โมเดลใหญ่ = เก็บความรู้ในพารามิเตอร์ (แพง, static, ลืมไม่ได้, hallucinate)
โมเดลเล็ก + retrieval = ความรู้อยู่ข้างนอก (ถูก, update ได้, verifiable, ไม่ hallucinate)
```
→ ทิศทาง AI: **ไม่จำเป็นต้องยัดทุกอย่างในโมเดล** — retrieval ที่ดี = โมเดลเล็กก็ฉลาดได้
- แก้ปัญหา Ch community: hallucination (โมเดลเดาจากพารามิเตอร์) → retrieval ground ในความรู้จริง

---

## 42.4 เชื่อม second brain (ARRA)

ARRA = **inference-time retrieval** (RAG) — โมเดล (Claude) frozen, ARRA เป็น external memory (Ch15):
```
Claude Code (โมเดล) + ARRA (memory ที่ retrieve ได้) 
= โมเดลไม่ต้องจำ knowledge ของคุณ → ARRA จำให้ → retrieve ตอนต้องใช้
```
- นี่คือ **RETRO philosophy ในระดับ product**: ความรู้ส่วนตัวอยู่ใน vault (retrieve ได้) ไม่ใช่ใน weights ของ LLM
- **ข้อดีเทียบ fine-tune LLM ด้วยความรู้ส่วนตัว**: update ง่าย (แค่เพิ่มไฟล์), verifiable (cite, Ch26), ไม่ hallucinate, privacy (data ในเครื่อง, Ch14/27)
- → เหตุผลเชิงหลักการว่าทำไม "second brain แบบ retrieval" ดีกว่า "เทรน LLM ให้จำ"

---

## 42.5 อนาคต — training-time retrieval สำหรับ personal memory?

```
วันนี้: ARRA = RAG (retrieve ตอน inference, โมเดล frozen)
อนาคต: โมเดลเล็ก fine-tune ให้ "ใช้ ARRA memory เก่ง" (RETRO-style personal)
        → personal LLM ที่ retrieve second brain ได้เนียนขึ้น
```
- ยังเป็นทิศทางวิจัย · ARRA ปัจจุบัน RAG พอ (โมเดล general + memory external)

---

## สรุป Ch42
```
retrieval เข้าโมเดล 2 จุด: inference (RAG, ARRA) vs training (RETRO/REALM)
REALM: retrieval เป็น latent, train retriever+reader end-to-end
RETRO: retrieve ตอน pretrain → 7.5B ≈ GPT-3 175B (retrieval แทน parameter 25×)
implication: memory > parameters — โมเดลเล็ก+retrieval = ฉลาด, verifiable, ไม่ hallucinate
ARRA = RETRO philosophy ระดับ product: ความรู้ใน vault (retrieve) ไม่ใช่ weights
  → ดีกว่า fine-tune LLM ด้วยความรู้ส่วนตัว (update/verify/privacy)
```
**ถัดไป Ch43:** embedding compression theory — information bottleneck, ทำไม 1024-dim พอ, intrinsic dimensionality ของภาษา
---
*grounded: REALM (Guu 2020) · RETRO (Borgeaud 2021) · เชื่อม Ch14/15/26/27 (ARRA=external memory), Ch community (hallucination) · /loop deep iter 2026-07-16*
