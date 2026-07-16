# Deep Technical · Chapter 8 — Quantization & Distance-Metric Proofs

> ต่อจาก Ch7 · 2 เรื่อง: (A) บีบเวกเตอร์ให้เล็กลง (quantization) โดยเสีย recall น้อยสุด · (B) พิสูจน์คณิตที่ Ch1-3 อ้างไว้แบบเป็นทางการ

---

# ส่วน A — Quantization

## 8.1 ทำไม: memory คือคอขวดเงียบ

1024-dim float32 = 1024 × 4 bytes = **4 KB/vector**
- 35,164 docs → 140 MB (ยังไหว)
- 1M docs → 4 GB · 100M → 400 GB (RAM ไม่พอ)

HNSW (Ch3) ต้องเก็บเวกเตอร์ใน RAM → quantization = ลด footprint แลก recall

---

## 8.2 Scalar Quantization (SQ) — float32 → int8

แต่ละมิติ: map ช่วง [min, max] ลงเป็น 256 ระดับ (int8):
```
q(xᵢ) = round( (xᵢ − min) / (max − min) × 255 )
x̂ᵢ  = min + q(xᵢ)/255 × (max − min)      (dequantize)
```
- บีบ 4× (4 bytes → 1 byte) · error ต่อมิติ = ครึ่งของ step size
- เร็ว, recall เสียน้อย (~1-2%) · เป็น "quantization ระดับเริ่มต้น" ที่คุ้มสุด

---

## 8.3 Product Quantization (PQ) — ลึกกว่า Ch3

หั่นเวกเตอร์ D มิติเป็น m subvector (D/m มิติต่อชิ้น) · แต่ละ subspace มี **codebook** ของ 256 centroid (เรียนด้วย k-means):
```
x = [ x⁽¹⁾ | x⁽²⁾ | … | x⁽ᵐ⁾ ]         m subvectors
PQ(x) = ( c₁, c₂, …, cₘ )              cⱼ = index ของ centroid ใกล้สุดใน subspace j (8-bit)
```
เก็บแค่ m bytes (เช่น m=8 → 8 bytes = บีบ 512× จาก 4KB)

**Asymmetric Distance Computation (ADC)** — คำนวณ distance โดยไม่ต้อง decompress:
```
d(q, x)² ≈ Σ  ‖ q⁽ʲ⁾ − codebook_j[cⱼ] ‖²
          j=1..m
```
precompute ตาราง `q⁽ʲ⁾ ↔ ทุก centroid` (256×m) ครั้งเดียวต่อ query → หลังจากนั้นแค่ **lookup + บวก** (เร็วมาก) · นี่คือทริคที่ทำให้ค้น billion-vector ได้

---

## 8.4 Binary Quantization (BQ) — สุดขั้ว 32×

แต่ละมิติ → 1 bit (`xᵢ > 0 ? 1 : 0`) → 1024-dim = 1024 bits = 128 bytes (บีบ 32×)
```
distance = Hamming(a, b) = popcount(a XOR b)      ← นับ bit ต่าง
```
- เร็วมหาศาล (XOR + popcount = 1-2 CPU cycle) · recall เสียเยอะ → ใช้เป็น **coarse filter** แล้ว rerank full-precision
- pipeline: BQ คัดหยาบ top-1000 → SQ/full rerank top-10 (§8.7)

---

## 8.5 Recall Recovery — quantize แล้วยัง recall สูง

หลัก: **ค้นด้วยของบีบ (เร็ว) → จัดอันดับด้วยของเต็ม (แม่น)**
```
1. quantized search → candidates 10× ที่ต้องการ (over-fetch)
2. คำนวณ exact distance บน full-precision เฉพาะ candidates
3. เรียงใหม่ → top-k
```
= จ่าย full-precision แค่ไม่กี่ตัว → เร็วเกือบเท่า quantized แต่ recall เกือบเท่า exact · (ARRA reranker Ch4 §4.5 เป็น special case ของ pattern นี้)

---

# ส่วน B — Distance-Metric Proofs

## 8.6 พิสูจน์: normalize → dot product = cosine

**อ้าง (Ch1 §1.6)**: ถ้า `‖a‖=‖b‖=1` แล้ว `a·b = cos θ`

**พิสูจน์**: จาก `a·b = ‖a‖‖b‖cos θ` (นิยาม dot, Ch1 §1.2)
```
‖a‖=1, ‖b‖=1  ⟹  a·b = 1·1·cos θ = cos θ    ∎
```
→ ระบบจึง **normalize เวกเตอร์เป็น unit ก่อน** แล้วใช้ dot product ตรงๆ (ไม่ต้องหาร norm ทุก query) = เร็วกว่า · LanceDB/FAISS ทำแบบนี้ภายใน

## 8.7 พิสูจน์: `‖a−b‖² = 2 − 2cosθ` (Euclidean↔cosine บน unit sphere)

**อ้าง (Ch1 §1.6)**: unit vectors → Euclidean เป็นฟังก์ชันลดของ cosine
```
‖a − b‖² = (a−b)·(a−b)
         = a·a − 2(a·b) + b·b
         = ‖a‖² − 2(a·b) + ‖b‖²
         = 1 − 2cosθ + 1                (‖a‖=‖b‖=1, a·b=cosθ)
         = 2 − 2cosθ                    ∎
```
→ cos θ ↑ ⟹ ‖a−b‖ ↓ · **การเรียงลำดับด้วย cosine กับ Euclidean บน unit sphere = เหมือนกันเป๊ะ** → ANN index ที่รองรับแค่ Euclidean (L2) ใช้แทน cosine ได้ ถ้า normalize ก่อน

## 8.8 cosine distance เป็น metric จริงไหม? (triangle inequality)

`cosine_distance = 1 − cos θ` **ไม่ใช่ metric แท้** — ละเมิด triangle inequality บางกรณี
- แต่ **angular distance** `θ = arccos(cos θ)` เป็น metric (สอด triangle inequality)
- และบน unit sphere `‖a−b‖ = √(2−2cosθ)` (จาก §8.7) เป็น metric แท้ (Euclidean)

**เชิงปฏิบัติ**: ANN ส่วนใหญ่ต้องการแค่ "เรียงลำดับถูก" ไม่ต้องเป็น metric สมบูรณ์ → cosine distance ใช้ได้ · แต่ HNSW บาง implement สมมติ triangle inequality เพื่อ prune → เลยนิยม normalize + L2 (metric แท้) แทน (สอดกับ §8.7)

---

## สรุป Ch8
```
Quantization: SQ (int8, 4×) · PQ (codebook+ADC, 512×) · BQ (1-bit Hamming, 32×)
Recall recovery: quantized coarse → full-precision rerank
Proofs: unit vectors → a·b=cosθ · ‖a−b‖²=2−2cosθ (cosine↔L2 บน sphere)
        cosine distance ไม่ใช่ metric แท้ → normalize+L2 ปลอดภัยกว่า
```
**ถัดไป Ch9:** tokenizer ลึก — SentencePiece/BPE, การแบ่งคำไทย (ไม่มี space), vocab, subword regularization, ผลต่อ embedding คุณภาพ

---
*grounded: PQ/ADC (Jégou 2011) · binary quant + Hamming · vector normalization (FAISS/LanceDB internals) · metric-space theory · เชื่อม Ch1 §1.6 · /loop deep iter 2026-07-13*
