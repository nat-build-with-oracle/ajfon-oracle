# Deep Technical · Chapter 50 — Numerical Precision (fp32/fp16/bf16/int8)

> ต่อจาก Ch49 · Ch8 quantize เพื่อประหยัดที่ · บทนี้: precision กระทบ **ความถูกต้องเชิงตัวเลข** ของ embedding+distance — error accumulation, ทำไม normalize สำคัญ

---

## 50.0 floating point — เก็บเลขจริงยังไง

```
float = sign × mantissa × 2^exponent
fp32: 1 sign + 8 exp + 23 mantissa = 32 bit → ~7 หลักนัยสำคัญ
fp16: 1 + 5 + 10           = 16 bit → ~3 หลัก, range แคบ (±65504)
bf16: 1 + 8 + 7            = 16 bit → ~2 หลัก, range เท่า fp32 (8 exp)
```
- **bf16 vs fp16**: bf16 แลก mantissa (ความละเอียด) เพื่อ exponent (range) → ML ชอบ bf16 (ไม่ overflow ตอน train)

---

## 50.1 precision ใน embedding pipeline

```
embedder inference: มัก fp16/bf16 (GPU เร็ว, Ch44) → embedding ออกมา ~fp16 precision
เก็บ (Ch8):        fp32 (4B) หรือ quantize int8/PQ
distance (Ch1):    คำนวณ fp32 (สะสม error น้อย)
```
- embedding จาก fp16 inference → precision ~3 หลักก็พอ (ความหมายไม่ต้อง 7 หลัก) → ทำไม quantize (Ch8) เสีย recall น้อย

---

## 50.2 ⭐ error accumulation ใน dot product

cosine/dot (Ch1) = บวกสะสม 1024 พจน์ → error ลอยสะสม:
```
dot = Σ aᵢbᵢ   (1024 พจน์)
fp16 สะสม: แต่ละบวก ปัดเศษ → 1024 ครั้ง → error สะสมใหญ่ขึ้น
fp32 สะสม: error ต่อครั้งเล็กกว่ามาก → ปลอดภัยกว่า
```
- **กฎปฏิบัติ**: เก็บ quantize ได้ (int8) แต่ **สะสม distance ใน fp32** (upcast ตอนคูณ) → ได้ทั้งประหยัดที่ + แม่นพอ
- SIMD (Ch44): int8 multiply → int32 accumulate (VNNI ทำให้) → ไม่ overflow, ไม่เสีย precision ตอนสะสม

---

## 50.3 ทำไม normalize สำคัญเชิงตัวเลข (ไม่ใช่แค่ math)

Ch1 บอก normalize → cosine = dot · แต่เชิงตัวเลขมีผลอีก:
```
เวกเตอร์ normalize (‖v‖=1) → ทุก component อยู่ [-1,1] → magnitude คุมได้
→ dot ของ normalized → อยู่ [-1,1] → ไม่ overflow, error คุมได้
เวกเตอร์ไม่ normalize → magnitude ต่างกันมาก → dot ใหญ่/เล็กสุดขั้ว → fp16 overflow/underflow เสี่ยง
```
- → normalize (Ch1 §1.5) = ทั้ง semantic (ตัดความยาว) **และ numerical stability** (คุม range) → ทำไม embedder ปล่อย normalized output

---

## 50.4 catastrophic cancellation

```
subtract เลขใกล้กัน → เสียหลักนัยสำคัญ
เช่น distance L2: ‖a-b‖² = ‖a‖²+‖b‖²−2⟨a,b⟩
    ถ้า a≈b → ‖a‖²+‖b‖² ≈ 2⟨a,b⟩ → ลบกันเหลือค่าเล็ก → error สัมพัทธ์พุ่ง
```
- → คำนวณ L2 ตรงๆ (Σ(aᵢ-bᵢ)²) ปลอดภัยกว่าสูตรกระจาย เมื่อ precision ต่ำ
- cosine (normalized dot) เสถียรกว่า L2 ในแง่นี้ → อีกเหตุผลนิยม cosine (Ch1)

---

## 50.5 precision กับ quantization (เชื่อม Ch8)

```
fp32 → int8 (Ch8 SQ): map [min,max] → [-128,127] → เสีย ~precision ระดับ 1/256
     recall ตกนิด เพราะ embedding ทน (semantic ไม่ต้องละเอียด, §50.1)
PQ (Ch8):  แทน sub-vector ด้วย centroid id → error = ระยะถึง centroid
     rerank ด้วย fp32 (Ch8/48) → คืน precision ตอนสุดท้าย
```
- pattern เดิม (Ch8/48): **ค้นด้วย low-precision (เร็ว/ประหยัด) → ยืนยันด้วย fp32 (แม่น)**

---

## 50.6 เชื่อม ARRA / ปฏิบัติ

```
bge-m3 → normalized embedding (§50.3) → cosine เสถียร + ‖v‖=1
LanceDB distance: Rust core fp32 accumulate (§50.2) → แม่นแม้ input quantize
cosine > L2 เชิง numerical (§50.4) → ARRA ใช้ cosine (Ch4 distanceType('cosine'))
quantize เก็บ + fp32 สะสม (§50.2/50.5) → ประหยัด+แม่น
```
- **implication**: ไม่ต้องกลัว quantize (Ch8) — embedding ทน low-precision (semantic), แค่สะสม distance fp32

---

## สรุป Ch50
```
fp32(7หลัก)/fp16(3หลัก,range แคบ)/bf16(range เท่า fp32, ML ชอบ)/int8(Ch8)
embedding ทน low-precision (semantic ไม่ต้อง 7 หลัก) → quantize เสีย recall น้อย
⭐ error accumulation: dot 1024 พจน์ → เก็บ int8 ได้ แต่ "สะสม fp32" (upcast) → ประหยัด+แม่น
normalize = numerical stability ด้วย (คุม range [-1,1] ไม่ overflow) ไม่ใช่แค่ semantic
catastrophic cancellation: L2 สูตรกระจายเสี่ยง → cosine เสถียรกว่า → อีกเหตุผลใช้ cosine
pattern: low-precision ค้น (เร็ว) → fp32 ยืนยัน (แม่น) = เดิมจาก Ch8/48
```
**ถัดไป Ch51:** batch ingest pipeline — embed หลายพัน doc, chunking (Ch12) + batch (Ch4 batchSize 50) + retry, throughput, idempotency
---
*grounded: IEEE 754 (fp32/fp16) · bfloat16 · error accumulation · catastrophic cancellation · เชื่อม Ch1/4/8/44/48 · /loop deep iter 2026-07-16*
