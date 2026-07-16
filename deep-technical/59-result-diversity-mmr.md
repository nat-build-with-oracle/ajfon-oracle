# Deep Technical · Chapter 59 — Result Diversity (MMR)

> ต่อจาก Ch58 · top-k ที่ similar สุดอาจ **ซ้ำกันเอง** (redundant) · บทนี้: MMR balance relevance vs diversity, ทำไม top-k หลากหลายดีกว่า

---

## 59.0 ปัญหา — top-k ซ้ำกันเอง

```
query "วิธีลดน้ำหนัก" → top-5 ทั้งหมดพูดเรื่อง "ควบคุมอาหาร" คล้ายๆ กัน
→ ผู้ใช้ได้มุมเดียว 5 ครั้ง (ออกกำลังกาย/นอน/ยา หายไป)
```
- pure relevance (Ch1 cos สูงสุด) → doc คล้าย query มาก **มักคล้ายกันเองด้วย** → redundant
- **RAG (Ch42)**: context ซ้ำ = เปลือง token, LLM ได้ข้อมูลแคบ → ตอบไม่รอบด้าน

---

## 59.1 ⭐ MMR — Maximal Marginal Relevance

เลือก doc ทีละตัว โดยชั่งน้ำหนัก "relevant กับ query" vs "ต่างจากที่เลือกไปแล้ว":
```
MMR = argmax [ λ·sim(d, query) − (1−λ)·max sim(d, dⱼ) ]
       d∉S                              dⱼ∈S
```
- `sim(d, query)`: relevant แค่ไหน (Ch1)
- `max sim(d, dⱼ)`: คล้ายที่เลือกไปแล้ว (S) แค่ไหน → ลงโทษถ้าซ้ำ
- `λ`: คุมสมดุล — λ=1 relevance ล้วน (เดิม), λ=0 diversity ล้วน

---

## 59.2 กลไก MMR ทีละสเต็ป

```
S = {} (ที่เลือกแล้ว)
1. เลือก doc relevant สุดก่อน (d1) → S={d1}
2. รอบถัดไป: แต่ละ candidate คิด λ·rel − (1−λ)·(คล้าย d1 สุด)
   → เลือกตัวที่ relevant พอ แต่ ต่าง จาก d1 → d2
3. ทำต่อจนได้ k ตัว → S หลากหลาย
```
- **greedy**: เลือกทีละตัว, แต่ละครั้งดู trade relevance↔diversity กับ S ปัจจุบัน

---

## 59.3 λ ควรเท่าไร

```
λ สูง (0.7-0.9):  เน้น relevance (diversity นิดหน่อย) — คำถามเจาะจง (อยากคำตอบตรง)
λ กลาง (0.5):     สมดุล — สำรวจหัวข้อกว้าง
λ ต่ำ (0.2-0.3):  เน้น diversity — brainstorm, อยากหลายมุม
```
- **default ~0.5-0.7** · ปรับตามงาน (research=ต่ำ diversity, fact lookup=สูง relevance)

---

## 59.4 diversity กับ RAG context (สำคัญ)

```
LLM context จาก retrieval (Ch42): อยากได้ข้อมูล "ครอบคลุม" ไม่ใช่ซ้ำ
→ MMR ก่อนป้อน context → LLM เห็นหลายแง่ → ตอบรอบด้าน + ประหยัด token (ไม่ซ้ำ)
```
- นี่คือเหตุผล MMR นิยมใน RAG pipeline (ไม่ใช่แค่ search UI)
- ต่อจาก dedup (Ch52): dedup ตัดซ้ำเป๊ะ · MMR ลดซ้ำเชิงความหมาย (คนละระดับ)

---

## 59.5 ต้นทุน MMR

```
MMR = k รอบ × เทียบ candidate กับ S → O(k × candidates × dim)
บน top-N candidate เล็ก (เช่น rerank top-50 → MMR เลือก 10) → ถูก
ไม่ทำบนทั้ง corpus (แพง) → ทำหลัง ANN/rerank บน shortlist
```
- pipeline: ANN (Ch3) → rerank (Ch18) → **MMR diversify** (Ch59) → top-k สุดท้าย

---

## 59.6 เชื่อม ARRA

```
hybrid+rerank (Ch4/18) → shortlist relevant → MMR (§59.5) diversify → context/result
near-dup dedup (Ch52) ตัดซ้ำเป๊ะ + MMR ลดซ้ำความหมาย → result สะอาด+รอบด้าน
RAG context (Ch42): MMR → Claude เห็นหลายมุม → ตอบครบ (community: "ได้คำตอบรอบด้าน")
λ ปรับได้: fact lookup สูง, research ต่ำ (§59.3)
```
- ARRA default อาจไม่เปิด MMR (relevance ตรงพอ) · เปิดเมื่อ RAG อยากได้ context กว้าง

---

## สรุป Ch59
```
ปัญหา: top-k relevant สุด มักซ้ำกันเอง (redundant) → มุมเดียว, เปลือง token RAG
⭐ MMR = argmax[λ·sim(d,q) − (1−λ)·max sim(d,dⱼ∈S)] → relevant แต่ต่างจากที่เลือก
greedy ทีละตัว: เลือก relevant สุดก่อน → ถัดไปเลือกที่ relevant+ต่าง
λ: สูง=relevance (fact), กลาง=สมดุล, ต่ำ=diversity (brainstorm)
diversity สำคัญกับ RAG (Ch42): context ครอบคลุม → LLM ตอบรอบด้าน+ประหยัด token
ต้นทุน: ทำบน shortlist หลัง rerank (Ch18) ไม่ใช่ทั้ง corpus
dedup(Ch52)=ซ้ำเป๊ะ + MMR=ซ้ำความหมาย → คนละระดับ เสริมกัน
```
**ถัดไป Ch60:** negative/exclusion queries — "X แต่ไม่เอา Y", negation ใน embedding (ทำไม vector จับ "ไม่" ยาก), boolean + vector
---
*grounded: MMR (Carbonell & Goldstein 1998) · diversity in RAG · เชื่อม Ch1/3/4/18/42/52 · /loop deep iter 2026-07-16*
