# Deep Technical · Chapter 40 — ColBERT Late-Interaction (deep)

> ต่อจาก Ch39 · Ch7 §7.3 + Ch18 เกริ่น ColBERT · บทนี้ลง MaxSim math เต็ม + storage + efficient (PLAID)

---

## 40.0 ตำแหน่งของ ColBERT — ระหว่าง bi- และ cross-encoder

```
bi-encoder (Ch2):   1 vec/doc → cos → เร็ว/หยาบ (index ล่วงหน้าได้)
cross-encoder (Ch18): [q;d] → score → ช้า/แม่น (ทำล่วงหน้าไม่ได้)
ColBERT:            m vec/doc (per-token) → MaxSim → กลาง (index ล่วงหน้าได้ + interaction)
```
= "late interaction" — encode แยก (เหมือน bi) แต่ interaction ตอน score (ใกล้ cross)

---

## 40.1 MaxSim — สมการเต็ม

doc → เวกเตอร์ต่อ token · query → เวกเตอร์ต่อ token:
```
Q = (q₁, ..., qₙ)     n query token vectors
D = (d₁, ..., dₘ)     m doc token vectors
              n
S(Q,D) = Σ   max  ⟨qᵢ , dⱼ⟩
             i=1  j=1..m
```
แต่ละ query token `qᵢ` → หา doc token `dⱼ` ที่ **similar สุด** (max) → รวมทุก query token
- **intuition**: "แต่ละคำในคำถาม ตรงกับคำไหนใน doc ที่สุด" แล้วรวมความตรง
- token vectors normalize → `⟨qᵢ,dⱼ⟩ = cosine` (Ch8 §8.6)

**ทำไม max ไม่ sum**: query token ควร match doc token **ตัวเดียวที่ตรงสุด** (ไม่ใช่เฉลี่ยทุกตัว) → จับ "คำนี้มีใน doc ที่ตำแหน่งไหน" แบบเฉพาะเจาะจง

---

## 40.2 ทำไมแม่นกว่า dense (bi-encoder)

dense บีบทั้ง doc เป็น 1 เวกเตอร์ → เสีย token-level detail
ColBERT เก็บทุก token → query token หา match ระดับคำได้ → **จับ exact term + semantic ระดับ token**
- ตัวอย่าง: query "metformin dosage" → "metformin" match token "metformin", "dosage" match token "500mg/ปริมาณ" → คะแนนสูงเพราะทั้ง 2 term เจอ match ดี
- dense อาจ dilute "dosage" หายในเวกเตอร์รวม

---

## 40.3 Storage — ปัญหาใหญ่

```
dense:   1 vec × 1024-dim × 4 bytes = 4KB/doc
ColBERT: m token × 128-dim (ย่อ) × 4 bytes = m × 512 bytes
         doc 200 tokens → 100KB/doc  (25× ของ dense!)
```
- storage ระเบิด → ต้อง compress: ย่อมิติ token (128 แทน 1024) + quantize (Ch8) per-token
- **PLAID/ColBERTv2**: residual compression + centroid → บีบ ColBERT ลงมากโดยเสีย recall น้อย

---

## 40.4 PLAID — efficient ColBERT retrieval

MaxSim ต่อ (query, doc) = n×m dot → แพงถ้าทำทุก doc · PLAID ทำ 3 stage:
```
1. candidate generation: ใช้ centroid ของ token (คล้าย IVF Ch3) → คัด doc คร่าว
2. centroid interaction: ประมาณ MaxSim ด้วย centroid → คัดต่อ
3. full MaxSim: เฉพาะ candidate สุดท้าย → แม่น
```
= coarse-to-fine (เหมือน Ch8/36) แต่บน token-level · ทำ ColBERT scale ได้

---

## 40.5 ColBERT ใน bge-m3 (Ch7 §7.3)

bge-m3 ปล่อย ColBERT output ได้ (multi-vector) จาก forward เดียว (Ch7):
- ARRA ใช้ dense (Ch4) · **ColBERT = โอกาสเป็น rerank stage** (Ch18 §18.7) แทน/เสริม cross-encoder
- trade: ColBERT rerank เร็วกว่า cross-encoder (interaction เบากว่า) แต่ storage เยอะ

---

## 40.6 เมื่อไหร่ใช้ ColBERT

```
ใช้ dense:   default, storage จำกัด, corpus ใหญ่
ใช้ ColBERT: ต้องการ precision ระดับ token, exact-term-ในบริบท, มี storage
ใช้ cross-encoder: precision สูงสุด, rerank top-N เล็ก (Ch18)
```
- pipeline สมบูรณ์: dense recall → ColBERT rerank กลาง → cross-encoder rerank บนสุด (3 ชั้น)
- ARRA: dense + cross-encoder พอ · ColBERT = advanced middle stage

---

## สรุป Ch40
```
ColBERT = late interaction (encode แยก + interact ตอน score) ระหว่าง bi/cross
MaxSim: S = Σᵢ maxⱼ ⟨qᵢ,dⱼ⟩ — query token หา doc token ตรงสุด แล้วรวม (max ไม่ sum)
แม่นกว่า dense (token detail ไม่ dilute) · storage 25× (per-token) → PLAID/v2 compress
PLAID: centroid coarse → full MaxSim fine (coarse-to-fine token-level)
bge-m3 ให้ ColBERT ฟรี → rerank stage กลาง (ARRA: dense+cross พอ)
```
**ถัดไป Ch41:** dense retrieval history — DPR, การเปลี่ยนจาก sparse (BM25) ยุคเก่าสู่ dense neural, บทเรียนวิวัฒนาการ
---
*grounded: ColBERT (Khattab & Zaharia 2020) · ColBERTv2/PLAID (Santhanam 2021/2022) · bge-m3 (Ch7) · เชื่อม Ch2/8/18/36 · /loop deep iter 2026-07-16*
