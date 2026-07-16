# Deep Technical · Chapter 7 — bge-m3 Multi-Functionality (Dense + Sparse + ColBERT)

> ต่อจาก Ch6 · bge-m3 ไม่ได้ให้แค่เวกเตอร์เดียว (dense) — มันทำ **3 โหมด retrieval ในโมเดลเดียว**
> M3 = **Multi-Lingual · Multi-Functionality · Multi-Granularity** · บทนี้ลง Multi-Functionality

---

## 7.0 ทำไม 3 โหมด

- **Dense** (Ch1-4): เวกเตอร์เดียว/ข้อความ → cosine → จับ **ความหมาย** แต่พลาด "คำเป๊ะ" (ชื่อเฉพาะ ตัวเลข)
- **Sparse** (lexical): น้ำหนักต่อคำ → จับ **คำตรง** แบบ BM25 แต่ฉลาดกว่า (โมเดลเรียนน้ำหนัก)
- **ColBERT** (multi-vector): เวกเตอร์ต่อ token → **late interaction** แม่นสุด แต่หนักสุด

bge-m3 ปล่อยทั้ง 3 จาก forward pass เดียว → เลือกใช้/ผสมได้

---

## 7.1 Dense (ทวน) — single-vector semantic

pooling → 1 เวกเตอร์ 1024-dim → cosine (Ch1) · ARRA เก็บตัวนี้ใน LanceDB (Ch3-4) · จับความหมายกว้าง แต่ "diabetes" กับ "เบาหวาน" ใกล้กันได้ แม้สะกดคนละแบบ

---

## 7.2 Sparse / Lexical Weights — BM25 ที่โมเดลเรียนน้ำหนักเอง

**ก่อนอื่น ทวน BM25** (สิ่งที่ SQLite FTS5 ใช้ — Ch4 FTS leg):
```
                              f(t,d) · (k₁+1)
BM25(q,d) = Σ  IDF(t) · ──────────────────────────────────
           t∈q            f(t,d) + k₁·(1 − b + b·|d|/avgdl)
```
- `f(t,d)` = ความถี่คำ t ใน doc d · `IDF(t)` = คำหายาก = สำคัญ
- `k₁` (~1.2) = saturation ความถี่ · `b` (~0.75) = ปรับความยาว doc · `|d|/avgdl` = normalize ความยาว
- = "คำหายากที่โผล่บ่อยใน doc นี้ (แต่ปรับความยาวแล้ว) = เกี่ยว" · **แต่ไม่รู้ความหมาย** — "รถ" กับ "ยานพาหนะ" = คนละคำ ได้ 0

**Sparse ของ bge-m3**: แทนที่จะนับ frequency ดิบ โมเดล **เรียนน้ำหนัก wₜ ต่อ token** (learned term weights):
```
sparse_vector(d) = { token_id → weight }   (ส่วนใหญ่ 0 = "sparse")
score_sparse(q,d) = Σ  w_q(t) · w_d(t)      (dot product บน token ที่ทับกัน)
                   t∈q∩d
```
- โมเดลให้น้ำหนักคำสำคัญสูง คำ stop ต่ำ — โดยเรียนจากข้อมูล ไม่ใช่สูตร BM25 ตายตัว
- ยังต้อง "คำทับกัน" (lexical) → จับ exact term (ชื่อยา ตัวเลข) ได้ · แต่ฉลาดกว่า BM25

---

## 7.3 ColBERT / Multi-Vector — Late Interaction (แม่นสุด)

แทนบีบทั้ง doc เป็น 1 เวกเตอร์ (สูญข้อมูล) → **เก็บเวกเตอร์ต่อ token**:
```
doc  → (d₁, d₂, …, dₘ)     m เวกเตอร์ (1 ต่อ token)
query → (q₁, q₂, …, qₙ)     n เวกเตอร์
```

**MaxSim (late interaction)** — แต่ละ query-token หา doc-token ที่ใกล้สุด แล้วรวม:
```
              n
score(q,d) = Σ   max  cos(qᵢ, dⱼ)
             i=1  j=1..m
```
- query token "เบาหวาน" จับคู่กับ doc token ที่ตรงความหมายสุด · ทำทุก query token แล้วรวม
- **"late" interaction**: encode แยก (เหมือน bi-encoder → index ล่วงหน้าได้) แต่ interaction ตอน score (ใกล้ cross-encoder) → กลางระหว่าง bi- และ cross-encoder
- แม่นกว่า dense (ไม่บีบ) · แต่เก็บ m เวกเตอร์/doc = storage เยอะ + compute MaxSim = n×m

---

## 7.4 รวม 3 โหมด (bge-m3 hybrid ในตัว)

```
score = α · dense(q,d) + β · sparse(q,d) + γ · colbert(q,d)
```
- ปรับ α,β,γ ตามงาน · paper bge-m3 แสดงว่ารวมกันชนะแต่ละตัวเดี่ยว
- **dense** จับความหมาย · **sparse** กันพลาดคำเป๊ะ · **colbert** จัดอันดับละเอียด
- นี่คือ hybrid "ในโมเดล" — ต่างจาก hybrid "ในระบบ" ของ ARRA (RRF รวม vector+FTS5, Ch4) ซึ่งเป็นคนละชั้น

---

## 7.5 ARRA ใช้อะไร + ต่อยอดได้ยังไง

ปัจจุบัน ARRA ใช้ **dense** (bge-m3) เข้า LanceDB + **FTS5 (BM25)** เป็น lexical leg → RRF รวม (Ch4)

**โอกาสต่อยอด** (ถ้าจะลึกกว่านี้):
- ใช้ **sparse ของ bge-m3** แทน/เสริม FTS5 BM25 → lexical ที่ฉลาดกว่า (learned weights)
- ใช้ **ColBERT** เป็น rerank stage แทน/เสริม cross-encoder (Ch4 §4.5)
- ทั้งหมดได้จาก forward pass เดียวของ bge-m3 → ไม่ต้องรันหลายโมเดล

→ อธิบายว่าทำไม bge-m3 ถึงเป็น "ตัวหลัก" ของ ARRA: multilingual (ไทย/อังกฤษ) + 3 โหมดในตัว + 1024-dim สมดุล

---

## 7.6 ตารางเทียบ 3 โหมด

| โหมด | จับอะไร | เก็บ | speed | ARRA |
|---|---|---|---|---|
| Dense | ความหมาย | 1 vec/doc | เร็ว | ✅ LanceDB |
| Sparse | คำเป๊ะ (learned) | token→weight | เร็ว | (FTS5 BM25 แทนตอนนี้) |
| ColBERT | ละเอียด (per-token) | m vec/doc | ช้า/หนัก | (reranker แทน) |

---

## สรุป Ch7
```
bge-m3 = 1 โมเดล 3 โหมด (dense/sparse/colbert) จาก forward pass เดียว
  dense: 1 vec, cosine — ความหมาย (ARRA ใช้)
  sparse: learned term weights, dot บน token ทับ — คำเป๊ะฉลาดกว่า BM25
  colbert: per-token vec + MaxSim Σmax cos(qᵢ,dⱼ) — late interaction แม่นสุด
BM25 (FTS5): Σ IDF·f·(k₁+1)/(f+k₁(1−b+b|d|/avgdl))
```
**ถัดไป Ch8:** quantization ลึก (scalar/product/binary), memory-vs-recall tradeoff, และ distance-metric proofs (ทำไม normalize→dot=cosine, triangle inequality ของ cosine distance)

---
*grounded: bge-m3 paper (Chen et al. 2024, M3-Embedding) · BM25 (Robertson & Zaragoza) · ColBERT MaxSim (Khattab & Zaharia 2020) · SQLite FTS5 (ARRA lexical leg) · /loop deep iter 2026-07-13*
