# Deep Technical · Chapter 43 — Embedding Compression Theory

> ต่อจาก Ch42 · Ch1 §1.7 ถามว่ามิติเท่าไรพอ, Ch8/36 บีบเชิงปฏิบัติ · บทนี้ลง**ทฤษฎี** — ทำไม 1024 มิติพอ + anisotropy

---

## 43.0 คำถาม: ภาษาต้องกี่มิติจริงๆ

embedding 1024 มิติ · แต่ "ความหมาย" ของภาษาจริงๆ ใช้กี่ dimension of freedom? → **intrinsic dimensionality**

---

## 43.1 Information Bottleneck

embedding = บีบข้อความ (มิติสูงมาก, ทุก token) ให้เหลือเวกเตอร์เดียว โดยเก็บ "ข้อมูลที่เกี่ยวกับความหมาย":
```
min I(X; Z)  −  β·I(Z; Y)
     ↑ บีบ X→Z ให้เล็ก      ↑ แต่ Z ต้องทำนาย Y (relevance) ได้
```
- `Z` = embedding · เก็บข้อมูลพอทำ retrieval (I(Z;Y) สูง) แต่ทิ้งส่วนเกิน (I(X;Z) ต่ำ)
- มิติน้อยไป → บีบเกิน → เสีย relevance · มิติมากไป → เก็บ noise → curse of dimensionality (Ch1 §1.7)
- **1024 = จุดสมดุล empirical** ที่พอเก็บความหมายหลากหลายโดยไม่ overfit noise

---

## 43.2 Intrinsic Dimensionality

แม้ embedding 1024-dim, เวกเตอร์จริง**ไม่กระจายเต็ม** 1024 มิติ — อยู่บน **manifold มิติต่ำกว่า**:
```
วัดด้วย: PCA (Ch36) — กี่ component อธิบาย variance 95%?
         มักพบว่า ~ไม่กี่ร้อยมิติ อธิบายเกือบหมด
```
- → **Matryoshka (Ch36) เวิร์กเพราะสิ่งนี้** — ข้อมูลอัดในมิติต้นๆ, ตัดหางได้
- → **PCA ลดมิติ (Ch36 §36.4) เวิร์ก** — มี dimension ซ้ำซ้อน
- intrinsic dim ของภาษา << 1024 → มิติส่วนเกินคือ "ที่ว่าง" กันชน + robustness

---

## 43.3 Rate-Distortion — บีบเท่าไรก่อนพัง

ทฤษฎีข้อมูล: บีบ (rate ต่ำ = มิติน้อย/bit น้อย) แลกกับ distortion (คุณภาพ):
```
D(R) = distortion ต่ำสุด ที่ rate R
```
- Ch8 (quantization) + Ch36 (dim) = เดินบน rate-distortion curve
- **sweet spot**: จุดที่ลด rate มากแต่ distortion เพิ่มน้อย (เข่าโค้ง) → เช่น 256-dim int8 (Ch36 §36.5) มัก "คุ้ม" กว่า 1024 float32 สำหรับ recall ที่ยอมรับได้

---

## 43.4 ⭐ Anisotropy — ปัญหาที่ซ่อนอยู่

embedding จาก transformer มักไม่ isotropic (ไม่กระจายทุกทิศเท่ากัน) — **กระจุกใน "กรวย" แคบ**:
```
ผล: cos(a,b) ของคู่สุ่ม สูงผิดปกติ (เช่น 0.6+ ทั้งที่ไม่เกี่ยว)
     → cosine แยกความหมายได้แย่ลง (ทุกอย่างดู "ใกล้" หมด)
```
- สาเหตุ: token ความถี่สูง (stop words) ดึงเวกเตอร์ไปทิศเดียว + training dynamics
- **สำคัญกับ retrieval**: anisotropy ทำ threshold cosine ตั้งยาก (ทุกคู่คะแนนสูง)

---

## 43.5 แก้ anisotropy — whitening / isotropy

```
whitening: transform embedding ให้ covariance = identity (กระจายทุกทิศเท่า)
  z' = W(z − μ),   W = Σ^{−1/2}   (Σ = covariance)
→ cosine หลัง whitening แยกความหมายดีขึ้น
```
- **contrastive learning ช่วยเอง** (Ch2): InfoNCE ดันให้ isotropic ขึ้น (push negatives ออก → กระจาย) → embedder ยุคใหม่ (bge-m3) anisotropy น้อยกว่า BERT ดิบ
- BERT ดิบ (ไม่ contrastive) anisotropy สูง → ทำไม sentence-embedding ต้อง fine-tune contrastive (SBERT) ไม่ใช้ BERT[CLS] ตรงๆ

---

## 43.6 เชื่อม ARRA / ปฏิบัติ

- bge-m3 (contrastive + distill, Ch22) → anisotropy ต่ำ → cosine (Ch1) แยกความหมายได้ดี → ไม่ต้อง whitening เพิ่ม
- **implication threshold**: semantic cache (Ch32 §32.3) threshold 0.95 ตั้งได้เพราะ embedding ดี · ถ้า anisotropy สูง threshold นี้จะ hit มั่ว
- intrinsic dim ต่ำ → Matryoshka/quantize (Ch36/8) ทำได้โดยเสีย recall น้อย = ยืนยันเชิงทฤษฎีว่าทำไมบีบได้

---

## สรุป Ch43
```
information bottleneck: embedding บีบ X→Z เก็บ relevance ทิ้ง noise → 1024 = สมดุล
intrinsic dim << 1024 (manifold มิติต่ำ) → Matryoshka/PCA เวิร์กเพราะสิ่งนี้
rate-distortion: บีบ (dim/bit) แลก distortion → sweet spot ที่เข่าโค้ง
⚠️ anisotropy: embedding กระจุกกรวย → cos คู่สุ่มสูงผิด → แยกยาก
แก้: whitening / contrastive (InfoNCE ดัน isotropic เอง) → bge-m3 ดีอยู่แล้ว
```
**ถัดไป Ch44:** query latency optimization — batching, SIMD, early termination, p99 tail, การ optimize ค้นให้เร็ว
---
*grounded: information bottleneck (Tishby) · anisotropy (Ethayarajh 2019, Gao BERT-flow) · whitening (Su 2021) · intrinsic dim · เชื่อม Ch1/2/8/32/36 · /loop deep iter 2026-07-16*
