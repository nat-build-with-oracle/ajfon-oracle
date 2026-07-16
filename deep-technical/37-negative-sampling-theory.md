# Deep Technical · Chapter 37 — Negative Sampling Theory

> ต่อจาก Ch36 · Ch2 §2.5 + Ch22 §22.3 เกริ่น negatives · บทนี้ลงทฤษฎี — ทำไม negatives กำหนดคุณภาพ embedding + gradient analysis

---

## 37.0 ทำไม negatives สำคัญกว่าที่คิด

InfoNCE (Ch2 §2.5): positive 1 คู่ + negatives N คู่ · **โมเดลเรียนจากการแยก positive ออกจาก negatives** · ถ้า negatives ง่าย (แยกได้ชัดอยู่แล้ว) → gradient เล็ก → เรียนน้อย · negatives = "ครูที่ตั้งโจทย์" — โจทย์ง่ายไม่เก่ง

---

## 37.1 In-Batch Negatives — ประหยัดสุด

```
batch = [(q₁,d₁), (q₂,d₂), ..., (qB,dB)]
สำหรับ q₁: positive = d₁ · negatives = d₂,...,dB (doc ของ query อื่นใน batch!)
```
- ฟรี — ไม่ต้อง sample เพิ่ม, ใช้ doc ที่อยู่ใน batch อยู่แล้ว
- **batch ใหญ่ = negatives เยอะ = เรียนดีขึ้น** → เหตุผลที่ contrastive ต้องการ batch ใหญ่ (2k-64k)
- แต่ in-batch negatives ส่วนใหญ่ "ง่าย" (random) → ต้องเสริม hard (§37.4)

---

## 37.2 Cross-Batch / Memory Bank

batch เดียวจำกัด GPU → เก็บ embedding จาก batch ก่อนๆ ใน "memory bank":
```
negatives = current batch + queue ของ embedding เก่า (momentum encoder, MoCo)
```
- ได้ negatives เยอะกว่า batch size จริง · แต่ embedding เก่า "stale" (โมเดลเปลี่ยนไปแล้ว) → ใช้ momentum encoder (update ช้า) ให้ consistent

---

## 37.3 ⭐ Gradient Analysis — ทำไม hard negative ให้ gradient ใหญ่

InfoNCE gradient เทียบ negative dⱼ:
```
∂L/∂s(q,dⱼ) = softmax_weight(dⱼ) = exp(s(q,dⱼ)/τ) / Σₖ exp(s(q,dₖ)/τ)
```
- **negative ที่ s(q,dⱼ) สูง (hard, ใกล้ positive)** → softmax weight สูง → **gradient ใหญ่** → โมเดลปรับแรง
- **negative ที่ s ต่ำ (easy, ไกล)** → weight ~0 → gradient ~0 → **ไม่เรียนอะไร**

→ ทฤษฎียืนยัน: **hard negatives ให้ signal การเรียนรู้เกือบทั้งหมด** · easy negatives แทบไร้ค่า (แต่ก็ยังต้องมีเพื่อ normalize)

---

## 37.4 Hard Negative Mining strategies

```
ANCE (Approximate NN Contrastive):
  1. index ด้วยโมเดลปัจจุบัน
  2. retrieve top-k ที่ใกล้ query (แต่ไม่ใช่ positive) = hard negatives
  3. เทรน → โมเดลดีขึ้น → re-index → mine ใหม่ (async)
  → hard negatives "สดใหม่" ตามโมเดลที่ดีขึ้นเรื่อยๆ
```
- BM25 hard negatives: retrieve ด้วย BM25 → คำเหมือนแต่ความหมายต่าง (lexical hard)
- self-mined: จากโมเดลเอง (semantic hard)

---

## 37.5 ⚠️ False Negatives — กับดัก

"hard negative" ที่ retrieve มา บางตัว**จริงๆ relevant** แต่ไม่ถูก label positive:
```
query: "รักษาเบาหวาน"
"hard neg": "การจัดการน้ำตาลในเลือด"  ← จริงๆ relevant! แต่ไม่ใช่ labeled positive
→ ถ้าใช้เป็น negative → สอนโมเดลผิด (ดันของที่ควรใกล้ให้ไกล)
```
- **แก้**: reranker filter (Ch22) ตัดตัวที่คะแนนสูงเกิน (น่าจะ positive) ออกจาก negative pool
- หรือ threshold: negative ต้อง s < บางค่า (ไม่ใกล้เกินไป)

---

## 37.6 Temperature τ interaction (Ch2 §2.5)

```
softmax(s/τ):  τ เล็ก → คม → hard negatives ครองงำ gradient (เรียนเร็ว แต่ sensitive)
               τ ใหญ่ → นุ่ม → negatives ทุกตัวมีส่วน (เสถียร แต่ช้า)
```
- τ กับ hardness ของ negatives **โต้ตอบกัน**: hard neg + τ เล็ก = gradient ระเบิดได้ → tune คู่กัน (bge-m3 τ~0.05)

---

## 37.7 เชื่อม ARRA / retrieval quality

- คุณภาพ embedding ที่ ARRA ใช้ (bge-m3) = ผลของ hard-negative mining + distillation (Ch22) ตอน train
- **ถ้า fine-tune domain ไทย** (Ch30): hard negative mining จาก vault เอง = กุญแจ (retrieve ใกล้-แต่-ผิด → เทรน) · ระวัง false negatives (memory เกี่ยวกันเยอะใน second brain!)
- นี่คือทฤษฎีเบื้องหลัง "ทำไม embedder ดี" — ไม่ใช่ architecture อย่างเดียว แต่ **negatives ที่ใช้เทรน**

---

## สรุป Ch37
```
negatives = signal การเรียน · easy neg แทบไร้ค่า (gradient~0), hard neg = เรียนเกือบทั้งหมด
in-batch (ฟรี, batch ใหญ่ดี) → cross-batch/memory-bank (MoCo momentum)
gradient: ∂L/∂s(q,dⱼ) = softmax weight → hard (s สูง) = gradient ใหญ่ (พิสูจน์)
ANCE: mine hard neg จากโมเดลเอง async · BM25 neg (lexical hard)
⚠️ false negatives (relevant แต่ไม่ label) → reranker filter / threshold
τ × hardness โต้ตอบกัน → tune คู่
```
**ถัดไป Ch38:** cross-modal retrieval — text+image ในปริภูมิเดียว (CLIP), ค้น figure/chart ใน paper, multimodal สำหรับงานวิจัย
---
*grounded: InfoNCE gradient (van den Oord) · in-batch (DPR) · MoCo (He 2020) · ANCE (Xiong 2020) · false-neg (RocketQA) · เชื่อม Ch2/22/30 · /loop deep iter 2026-07-14*
