# Deep Technical · Chapter 34 — Sparse Retrieval Deep (SPLADE)

> ต่อจาก Ch33 · Ch7 §7.2 เกริ่น sparse ของ bge-m3 · บทนี้ลง SPLADE — learned sparse ที่เชื่อม BM25 กับ neural

---

## 34.0 spectrum: BM25 → SPLADE → dense

```
BM25 (Ch7):    น้ำหนักจากสถิติ (tf-idf) · lexical ล้วน · ไม่รู้ความหมาย
SPLADE:        น้ำหนักจากโมเดล + expansion · lexical แต่ neural
dense (Ch2):   เวกเตอร์หนา · ความหมายล้วน · ไม่ interpretable
```
SPLADE = ตรงกลาง — sparse (interpretable, ใช้ inverted index) แต่เรียนน้ำหนัก + เพิ่มคำ

---

## 34.1 SPLADE — สมการ

จาก MLM logits ของแต่ละ token → คำนวณ importance ต่อ vocab term:
```
w_j = Σ  log(1 + ReLU(MLM_logit(token_i, term_j)))
     i∈doc
```
- ต่อ term j ใน vocab → รวม contribution จากทุก token ในเอกสาร
- **ReLU** → ตัดค่าลบ (term ไม่เกี่ยว = 0) → **sparse** (ส่วนใหญ่เป็น 0)
- **log(1+·)** → saturation (เหมือน BM25, Ch7)

**⭐ Expansion — จุดเด่น**: `w_j` ไม่เป็น 0 ได้แม้ term j **ไม่ปรากฏใน doc** — ถ้าโมเดลคิดว่าเกี่ยว
```
doc: "เบาหวาน metformin"
SPLADE weights: {เบาหวาน:2.1, metformin:1.8, diabetes:1.2, น้ำตาล:0.9, ...}
                                              ↑ expansion (ไม่มีในข้อความ แต่โมเดลเติม)
```
→ แก้ปัญหา BM25 (vocabulary mismatch: "รถ"≠"ยานพาหนะ") ในกรอบ sparse

---

## 34.2 Scoring (dot product บน sparse)

```
score(q, d) = Σ  w_q(t) · w_d(t)      (sparse dot, Ch7 §7.2)
             t∈vocab
```
- ทั้ง query และ doc เป็น sparse vector (ส่วนใหญ่ 0) → dot คำนวณเฉพาะ term ที่ทับ
- **ใช้ inverted index ได้!** (ต่างจาก dense ที่ต้อง ANN) → term → posting list ของ doc ที่มี term นั้น (พร้อมน้ำหนัก)

---

## 34.3 Inverted index สำหรับ sparse

```
inverted_index[term] = [(doc_id, weight), ...]
query: หา posting list ของ query terms → accumulate score ต่อ doc → top-k
```
- โครงเดียวกับ FTS5/BM25 (Ch4) แต่ weight มาจากโมเดล (SPLADE) ไม่ใช่ tf-idf
- **ข้อดี**: reuse โครงสร้าง IR ที่ scale ดีอยู่แล้ว (Lucene/inverted index) · ไม่ต้อง ANN
- **ข้อเสีย**: expansion ทำ posting list ยาวขึ้น (doc มี term ที่ไม่ปรากฏ) → index โต + query ช้าลง (มี regularization คุม sparsity)

---

## 34.4 Sparse vs Dense vs Hybrid (สรุป)

| | Sparse (SPLADE) | Dense (Ch2) |
|---|---|---|
| จับ | คำ + expansion | ความหมาย |
| interpretable | ✅ (เห็น term+weight) | ❌ (เวกเตอร์ทึบ) |
| index | inverted (Lucene) | ANN (HNSW/IVF) |
| exact match | ✅ (ชื่อยา/ตัวเลข) | อ่อน |
| paraphrase/semantic | ปานกลาง (expansion) | ✅ |
| storage | posting list | float vectors |

**hybrid (sparse+dense)** ชนะทั้งคู่บ่อย (Ch7 §7.4): sparse จับ exact+expansion, dense จับ semantic ลึก → fuse (RRF, Ch11)

---

## 34.5 เชื่อม ARRA

- ARRA lexical leg = **FTS5/BM25** (Ch4) — sparse แบบ statistical (ไม่ใช่ SPLADE)
- **โอกาสอัปเกรด**: ใช้ **sparse ของ bge-m3** (Ch7 §7.2, learned weights เหมือน SPLADE) แทน/เสริม FTS5 → lexical ที่ฉลาดกว่า (expansion) · ได้จาก forward pass เดียวกับ dense อยู่แล้ว
- แต่ต้อง index รองรับ learned-sparse (weighted inverted) — FTS5 เป็น tf-idf → ต้องปรับ

---

## สรุป Ch34
```
SPLADE: w_j = Σ log(1+ReLU(MLM_logit)) → learned sparse + expansion (term ไม่ในข้อความก็ได้)
แก้ vocabulary mismatch ของ BM25 ในกรอบ sparse (ยังใช้ inverted index)
scoring = sparse dot (term ทับ) · inverted index (reuse Lucene, ไม่ต้อง ANN)
sparse (คำ+expansion, interpretable) vs dense (semantic) → hybrid ชนะ (RRF Ch11)
ARRA: FTS5/BM25 (statistical sparse) → โอกาสอัปเป็น bge-m3 learned-sparse
```
**ถัดไป Ch35:** agentic retrieval loop — agent ค้นซ้ำ, self-query, retrieve-read-reason, iterative refinement (เชื่อม Ch skill /ralph-dig)
---
*grounded: SPLADE (Formal et al. 2021) · learned sparse vs BM25 · bge-m3 sparse (Ch7) · inverted index (Ch4 FTS5) · hybrid (Ch11) · /loop deep iter 2026-07-14*
