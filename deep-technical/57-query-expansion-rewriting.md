# Deep Technical · Chapter 57 — Query Expansion & Rewriting

> ต่อจาก Ch56 · query สั้น/กำกวม → ค้นไม่เจอ · บทนี้: HyDE, pseudo-relevance feedback, multi-query — ขยาย query เพื่อ recall

---

## 57.0 ปัญหา — query กับ doc "ไม่พูดภาษาเดียวกัน"

```
query: "ปวดหัวบ่อย"        (สั้น, ภาษาคนถาม)
doc:   "อาการ migraine เรื้อรัง มักสัมพันธ์กับ..."  (ยาว, ภาษาวิชาการ)
→ dense อาจจับได้บ้าง (Ch2) แต่ vocabulary/length gap ทำ recall ตก
```
→ **query expansion**: ทำ query ให้ "เหมือน doc มากขึ้น" ก่อนค้น

---

## 57.1 ⭐ HyDE — Hypothetical Document Embeddings

ไอเดียพลิก: แทนที่จะ embed query สั้น → **ให้ LLM เขียน "คำตอบสมมติ" ก่อน แล้ว embed คำตอบนั้น**:
```
1. query "ปวดหัวบ่อยทำไง" → LLM สร้าง passage สมมติ:
   "อาการปวดหัวบ่อยอาจเกิดจากความเครียด นอนน้อย ควรพบแพทย์ถ้า..."
2. embed passage สมมตินั้น (ไม่ใช่ query สั้น)
3. ค้นด้วย embedding นั้น → ใกล้ doc จริง (ภาษา/ความยาวใกล้กัน) มากกว่า query สั้น
```
- **ทำไมเวิร์ก**: passage สมมติอยู่ใน "doc space" ไม่ใช่ "query space" → เจอ doc จริงง่ายขึ้น
- ข้อควรระวัง: LLM อาจ hallucinate passage → แต่ใช้แค่ "ทิศทาง embedding" ไม่ใช่คำตอบ → พอทน

---

## 57.2 pseudo-relevance feedback (PRF)

```
1. ค้นรอบแรกด้วย query เดิม → top-k doc (สมมติว่า relevant)
2. ดึงคำเด่นจาก top-k (term ที่ปรากฏบ่อย) → เพิ่มเข้า query
3. ค้นรอบสอง ด้วย query ขยาย → recall ดีขึ้น
```
- **สมมติฐาน**: top-k รอบแรกมี doc ดีปนอยู่ → คำในนั้นช่วยขยาย · เก่าแก่ (Rocchio, sparse IR) แต่ยังใช้ได้
- ⚠️ **query drift**: ถ้า top-k รอบแรกแย่ → ขยายผิดทาง → ยิ่งเพี้ยน (เสี่ยง)

---

## 57.3 multi-query — ถามหลายมุม

```
LLM แตก query เดียว → หลาย query ย่อย/พาราเฟรส:
"ปวดหัวบ่อยทำไง" → ["สาเหตุปวดหัวเรื้อรัง", "วิธีบรรเทาปวดหัว", "เมื่อไหร่ควรพบแพทย์ปวดหัว"]
→ ค้นทุก sub-query → รวมผล (union + RRF Ch11)
```
- ครอบหลายแง่มุม → recall กว้างขึ้น (จับ doc ที่ query เดียวพลาด)
- ต้นทุน: หลาย embed + หลายค้น (Ch44) → trade latency/cost

---

## 57.4 query rewriting — แก้ query ให้ค้นง่าย

```
- expand ตัวย่อ: "รพ." → "โรงพยาบาล"
- แก้พิมพ์ผิด: "ปวดหัวว" → "ปวดหัว"
- normalize: unicode NFC (Ch9), lowercase, strip
- แยกเจตนา: "เทียบ A กับ B" → 2 query (A, B) แล้ว merge
```
- เบากว่า HyDE/multi-query (rule/LLM สั้น) · ทำก่อน embed เสมอ (Ch51 §51.1 normalize)

---

## 57.5 ต้นทุน vs ประโยชน์ (เมื่อไหร่ใช้)

```
query rewriting (normalize):  ถูก, ทำเสมอ (Ch51)
HyDE:                         +1 LLM call (แพง, ~วินาที) → ใช้เมื่อ recall สำคัญกว่า latency
multi-query:                  +N embed+ค้น → ใช้ตอน recall กว้างสำคัญ (research)
PRF:                          +1 ค้นรอบ → ระวัง drift
```
- **ARRA**: normalize เสมอ · HyDE/multi-query = โหมด "ค้นลึก" (research mode) ไม่ใช่ default (latency)
- **hybrid ช่วยลดความจำเป็น**: FTS (Ch34) จับ exact ที่ dense พลาด → บาง gap ปิดโดย hybrid ไม่ต้อง expand

---

## 57.6 เชื่อม ARRA / community

```
query สั้นกำกวม (คำถาม community "ค้นไม่เจอ" Ch54) → expansion ช่วย
default: normalize (Ch51) + hybrid (Ch4) → ครอบส่วนใหญ่
ค้นลึก: HyDE (§57.1) / multi-query (§57.3) เป็น option → recall สูงขึ้น trade latency
→ สอน: "ถ้าค้นไม่เจอ ลองถามให้ยาว/หลายมุม" = manual multi-query (ใช้ได้ทันที ไม่ต้องโค้ด)
```

---

## สรุป Ch57
```
ปัญหา: query สั้น/ภาษาคนถาม ≠ doc ยาว/วิชาการ → vocabulary+length gap → recall ตก
⭐ HyDE: LLM เขียน passage สมมติ → embed passage (อยู่ doc space) → เจอ doc จริงง่ายขึ้น
PRF: ค้นรอบแรก → ดึงคำเด่น top-k → ขยาย query → ค้นรอบสอง (⚠️ drift ถ้ารอบแรกแย่)
multi-query: LLM แตกหลาย sub-query → union+RRF (Ch11) → recall กว้าง (trade cost)
rewriting: expand ตัวย่อ/แก้พิมพ์ผิด/normalize (Ch9/51) — เบา, ทำเสมอ
ARRA: normalize+hybrid default · HyDE/multi-query = research mode · สอน manual multi-query
```
**ถัดไป Ch58:** conversational/multi-turn retrieval — resolve "มัน/อันนั้น" (coreference), context carry-over, ค้นในบทสนทนาต่อเนื่อง
---
*grounded: HyDE (Gao 2022) · PRF/Rocchio · multi-query (RAG-Fusion) · เชื่อม Ch2/4/9/11/34/44/51/54 · /loop deep iter 2026-07-16*
