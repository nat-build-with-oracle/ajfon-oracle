# Deep Technical · Chapter 36 — Matryoshka Embeddings & Dimensionality

> ต่อจาก Ch35 · Ch1 §1.7 บอกมิติเยอะ = แม่นแต่แพง · จะได้ทั้งแม่นและถูกได้ไหม? · บทนี้: Matryoshka + dim reduction

---

## 36.0 dilemma: มิติเยอะ vs ถูก

```
1024-dim: แม่น แต่ storage 4KB/vec, cosine ช้ากว่า (Ch1 §1.7)
256-dim:  ถูก/เร็ว แต่แม่นน้อยลง
```
ปกติเลือกครั้งเดียวตอน train · **Matryoshka** ให้ "เลือกได้ตอน runtime"

---

## 36.1 ⭐ Matryoshka Representation Learning (MRL)

ฝึกให้เวกเตอร์ **prefix ก็ใช้ได้** — เหมือนตุ๊กตาแม่ลูกดก (Matryoshka):
```
v = [v₁...v₆₄ | v₆₅...v₁₂₈ | ...v₂₅₆ | ...v₅₁₂ | ...v₁₀₂₄]
      ↑ ใช้ 64 ก็ได้ผลดี   ↑ 128 ดีขึ้น   ...  ↑ 1024 ดีสุด
```
loss: เทรน InfoNCE (Ch2) ที่**หลายความยาว prefix พร้อมกัน**:
```
L = Σ  L_InfoNCE( v[:m] )      m ∈ {64, 128, 256, 512, 1024}
   m
```
→ บังคับให้ข้อมูลสำคัญสุด "อัด" ไว้มิติต้นๆ → ตัดหางทิ้งได้โดยเสียคุณภาพน้อย

---

## 36.2 Truncation — ใช้แค่ prefix

```
v_full = embed(text)          # 1024-dim
v_small = v_full[:256]        # ตัดใช้ 256 แรก → re-normalize
cos(q[:256], d[:256])         # ค้นด้วยมิติน้อย = เร็ว/ประหยัด 4×
```
- MRL ทำให้ `v[:256]` ยังดี (ต่าง full ~1-2%) · ไม่ใช่ Matryoshka = ตัดแล้วพัง
- storage/compute ลดเป็นสัดส่วนมิติ

---

## 36.3 Adaptive Retrieval — coarse-to-fine (2 ชั้น)

ใช้ Matryoshka ทำ retrieval 2 ระดับ:
```
1. coarse: ค้นด้วย 256-dim (เร็ว/index เล็ก) → candidate top-1000
2. fine:   rerank candidate ด้วย 1024-dim (แม่น) → top-10
```
= เหมือน quantization recall-recovery (Ch8 §8.5) แต่ใช้ "มิติ" แทน "precision"
- ได้ recall ใกล้ full-dim ที่ speed/storage ของ low-dim สำหรับ stage 1

---

## 36.4 PCA / Dimensionality Reduction (post-hoc)

ถ้าโมเดลไม่ใช่ Matryoshka → ลดมิติภายหลังด้วย PCA:
```
1. รวบรวมเวกเตอร์ทั้งหมด → covariance matrix
2. หา eigenvector ที่ variance สูงสุด k ตัว (principal components)
3. project เวกเตอร์ลง k มิติ:  v' = Wₖᵀ v
```
- keep variance มากสุดใน k มิติ → เสียข้อมูลน้อยสุด (ในเชิง linear)
- **แลก**: ต้อง fit PCA บน corpus (ไม่ generalize เท่า Matryoshka ที่เทรนมา) · เวกเตอร์ใหม่ต้อง project ด้วย W เดิม

---

## 36.5 เชื่อม quantization (Ch8)

2 แกนลดขนาด — **ใช้ร่วมกันได้**:
```
dimensionality (Matryoshka/PCA): ลดจำนวนมิติ (1024→256)
quantization (Ch8):              ลด precision ต่อมิติ (float32→int8/1bit)
รวม: 256-dim + int8 = 256 bytes (จาก 4096) = บีบ 16×  แล้วยัง recall ดี
```
→ adaptive: coarse (256-dim binary, เร็วสุด) → fine (1024-dim float, แม่นสุด)

---

## 36.6 ARRA context

- bge-m3 dimensions ผ่าน KNOWN_DIMS (Ch1: 1024) · ถ้าเป็น Matryoshka-capable → ตัดใช้ 256/512 ได้ตอน scale (Ch25)
- 35k docs = ไม่ต้องลดมิติ (140MB จิ๊บ) · Matryoshka/PCA = โอกาสตอนโต 1M+ (storage/latency เริ่มสำคัญ)
- **decision**: อย่าลดมิติก่อนจำเป็น (เสีย recall ฟรีๆ) · ทำเมื่อ storage/latency เป็นคอขวดจริง (Ch24/25)

---

## สรุป Ch36
```
Matryoshka (MRL): เทรนหลาย prefix พร้อมกัน → ตัดหางใช้ได้ (v[:256] ยังดี)
truncation: ใช้ prefix → เร็ว/ประหยัดตามสัดส่วนมิติ
adaptive: coarse 256-dim → fine 1024-dim rerank (เหมือน Ch8 แต่ใช้มิติ)
PCA: ลดมิติ post-hoc (keep variance) แต่ต้อง fit corpus
รวมกับ quantization (Ch8): dim × precision = บีบทวีคูณ
ARRA 35k ไม่ต้องลด · = โอกาสตอน 1M+ (Ch25)
```
**ถัดไป Ch37:** negative sampling theory ลึก — in-batch negatives, cross-batch, ANCE, ทฤษฎีทำไม hard negatives สำคัญ (gradient analysis)
---
*grounded: Matryoshka (Kusupati 2022) · PCA · เชื่อม Ch1 §1.7 (dim), Ch8 (quant), Ch25 (scale), Ch2 (InfoNCE) · /loop deep iter 2026-07-14*
