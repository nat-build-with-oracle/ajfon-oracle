# Deep Technical · Chapter 22 — Distillation & bge-m3 Training Recipe

> ต่อจาก Ch21 · Ch18 §18.6 เกริ่น distillation · บทนี้ลงเต็ม + สูตรฝึก bge-m3 ที่ทำให้ retrieval แม่น

---

## 22.0 ปัญหา: teacher แพง, student เร็ว

- cross-encoder (Ch18) = teacher แม่น แต่ช้า
- bi-encoder (embedding, Ch2) = student เร็ว แต่หยาบ
- **distillation**: ให้ teacher สอน student → student ได้คุณภาพใกล้ teacher ที่ speed ของ student

---

## 22.1 Knowledge Distillation — สมการ

teacher ให้ **soft labels** (distribution) ไม่ใช่ hard label:
```
L_KD = τ² · KL( softmax(z_student/τ) ‖ softmax(z_teacher/τ) )
```
- `z` = logits · `τ` = temperature (>1 → distribution นุ่มขึ้น เผยข้อมูล "อันดับรอง")
- **ทำไม soft ดีกว่า hard**: hard label บอกแค่ "ตัวนี้ใช่" · soft บอก "ตัวนี้ใช่ 0.7, ตัวนั้นก็ใกล้ 0.2, ตัวโน้นไม่เลย 0.01" → student เรียน "โครงสร้างความคล้าย" ที่ teacher เห็น (dark knowledge)
- `τ²` scale gradient ชดเชยการหารด้วย τ

**ในบริบท retrieval**: teacher (cross-encoder) ให้คะแนน (q,dᵢ) ทุกตัวใน batch → student (embedding) เรียนให้ `cos(q,dᵢ)` เรียงตาม teacher

---

## 22.2 Self-Knowledge Distillation ใน bge-m3 (M3 teach กันเอง)

bge-m3 มี 3 output (dense/sparse/colbert, Ch7) — **ให้กันสอนกันเอง**:
```
s_ensemble = w₁·dense + w₂·sparse + w₃·colbert     (teacher = ensemble)
L_self = Σ  KL( sₖ ‖ stopgrad(s_ensemble) )         (แต่ละ mode เรียนตาม ensemble)
        k∈{dense,sparse,colbert}
```
- ensemble (รวม 3 mode) แม่นกว่าตัวเดียว → เป็น teacher · แต่ละ mode เรียนเลียน ensemble
- ผล: dense (ที่ ARRA ใช้) ได้ความรู้จาก sparse+colbert ไปด้วย → dense ตัวเดียวก็แม่นขึ้น
- **นี่คือเหตุผลที่ dense ของ bge-m3 ดีเป็นพิเศษ** — มันซึม lexical (sparse) + fine-grained (colbert) มาตอน train

---

## 22.3 Hard Negative Mining (Ch2 §2.5 ลงลึก)

InfoNCE (Ch2) ต้องมี negatives · **random negatives อ่อน** (ง่ายเกินไป โมเดลไม่เรียนอะไร) · **hard negatives** = ใกล้แต่ผิด:
```
1. embed query + docs ด้วยโมเดลปัจจุบัน
2. retrieve top-k ที่ "ดูใกล้" แต่ไม่ใช่ positive จริง
3. ใช้พวกนี้เป็น hard negatives ใน InfoNCE
```
- ทำให้ boundary คมขึ้น — โมเดลต้องแยก "diabetes treatment" (positive) จาก "diabetes symptoms" (hard neg, ใกล้มาก)
- **risk — false negatives**: บาง "hard negative" จริงๆ relevant แต่ไม่ถูก label → ต้อง filter (เช่น ตัดตัวที่ teacher ให้คะแนนสูงเกินออก)

---

## 22.4 สูตรฝึก bge-m3 เต็ม (รวม Ch2/7/19/22)

```
L_total = L_dense + L_sparse + L_colbert          (InfoNCE ต่อ mode, Ch2)
        + λ · L_self-distill                       (§22.2, mode teach กัน)
data:
  - multilingual pairs (194 ภาษา) → cross-lingual align (Ch19)
  - hard negatives mined + reranker-filtered (§22.3)
  - multi-granularity (สั้น→ยาว 8192, Ch9/21)
```
→ 3 output จาก forward เดียว, ฝึกพร้อมกัน, teach กันเอง = **M3** (Multi-lingual/functionality/granularity)

---

## 22.5 ทำไมสำคัญกับ ARRA (เชิงปฏิบัติ)

- ARRA ใช้ **dense ของ bge-m3** → ได้ประโยชน์จาก self-distillation (dense ซึม sparse+colbert)
- multilingual training → ไทย↔อังกฤษ retrieval (Ch19) ได้ฟรี
- **implication**: ถ้าจะ fine-tune ให้เข้ากับ domain วิจัยไทย → distill จาก reranker บน domain data → dense ดีขึ้นเฉพาะทาง (advanced, ยังไม่ทำใน ARRA)

---

## 22.6 distillation loop กับ retrieval pipeline

```
reranker (Ch18, teacher) ─ distill ─→ embedding (student, Ch2)
                                          │ embed docs → index (Ch3)
query → embedding retrieve top-50 ────────┘
      → reranker rerank top-5 (teacher ใช้จริงตอน serve ด้วย)
```
= teacher (reranker) ทั้ง **สอน** student (offline distill) และ **ตรวจงาน** student (online rerank) → double duty

---

## สรุป Ch22
```
KD: L = τ²·KL(student/τ ‖ teacher/τ) — soft label เผย dark knowledge
bge-m3 self-distill: dense/sparse/colbert เรียนตาม ensemble → dense ซึมทุก mode (เลยดีเป็นพิเศษ)
hard negative mining: retrieve top-k ใกล้-แต่-ผิด → boundary คม (ระวัง false neg)
สูตร: Σ InfoNCE ต่อ mode + self-distill, บน multilingual+hard-neg+multi-gran = M3
ARRA ใช้ dense → ได้ประโยชน์ทั้งหมดฟรี
```
**ถัดไป Ch23:** deployment & monitoring — pm2/Docker/CF Workers, health/observability (#2759), embedder degradation detection, การ operate จริง

---
*grounded: KD (Hinton et al. 2015) · bge-m3 self-distillation (Chen 2024) · hard-negative mining (DPR/RocketQA) · เชื่อม Ch2/7/18/19 · /loop deep iter 2026-07-13*
