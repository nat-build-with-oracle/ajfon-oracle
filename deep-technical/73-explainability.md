# Deep Technical · Chapter 73 — Explainability

> ต่อจาก Ch72 · "ทำไม doc นี้ติด top-k?" — vector search เป็น black box กว่า keyword · บทนี้: score breakdown, debug relevance, สร้างความเชื่อมั่น

---

## 73.0 ปัญหา — vector search อธิบายยาก

```
keyword (FTS Ch34): "เจอเพราะมีคำ 'ปวดหัว' 3 ครั้ง" → อธิบายง่าย
vector: "เจอเพราะ cos=0.83" → 0.83 มาจากไหน? ทำไมสูง? → ตอบยาก (1024 มิติ abstract)
→ user ไม่เชื่อมั่น ("ทำไมได้อันนี้?") · debug ยาก ("ทำไมไม่ได้อันที่ควรได้?")
```

---

## 73.1 ⭐ score breakdown — แยกส่วนคะแนน

hybrid (Ch4) มีหลาย signal → แสดงว่าแต่ละตัวมีส่วนเท่าไร:
```
doc X ติด top-3 เพราะ:
  vector_sim:  0.83  (rank 2 ใน dense)
  fts_bm25:    rank 5 (มีคำ "vector")
  rrf_fused:   0.031 (Ch11: 1/(60+2) + 1/(60+5))
  heat_boost:  ×1.2  (Ch13 ใช้บ่อย)
  recency:     ×0.9  (Ch61 เก่าหน่อย)
  → final rank 3
```
- **แยกให้เห็น**: ตัวไหนดันขึ้น/ดันลง → เข้าใจ + debug (Ch54 playbook)
- ต่อยอด Ch54 (observability): breakdown = explain ต่อ result (ไม่ใช่แค่ trace ต่อ query)

---

## 73.2 term-level attribution (ทำไม cos สูง)

vector abstract → ประมาณว่า "คำไหนใน doc ทำให้ใกล้ query":
```
วิธี: ลบ token ทีละตัวจาก doc → re-embed → ดู cos ตกเท่าไร
     token ที่ลบแล้ว cos ตกมาก = token สำคัญต่อ match
→ "doc นี้ match เพราะคำ 'ไมเกรน' และ 'อาการ'"
```
- แพง (re-embed หลายครั้ง) → ทำเฉพาะตอน debug/explain ไม่ใช่ทุก query
- ColBERT (Ch40): ให้ token-level match ฟรี (MaxSim บอกว่า query token ไหน match doc token ไหน) → explainable กว่า dense!

---

## 73.3 nearest-neighbor เป็นคำอธิบาย

```
"doc X ติดเพราะ similar กับ query" → แสดง doc อื่นที่ similar กับ X ด้วย
→ user เห็น neighborhood → เข้าใจว่า X อยู่ในกลุ่มความหมายไหน
เช่น: query→X, และ X ใกล้ {Y, Z} ที่ชัดเจน → confirm ว่า X เกี่ยวจริง
```
- visualize: project 1024-dim → 2D (UMAP/t-SNE) → เห็น cluster (Ch36 PCA เชิง explain)

---

## 73.4 ⚠️ debug "ทำไมไม่ได้อันที่ควรได้" (เชื่อม Ch54)

explainability สำคัญสุดตอน miss:
```
doc ควรติดแต่ไม่ติด → breakdown ช่วย:
  cos(query, doc) = 0.4 (ต่ำ) → ทำไม? → term-level (§73.2): query คำสำคัญไม่ match
  → อาจ chunk แยกคำ (Ch12) / vocabulary gap (Ch57 expansion ช่วย) / negation (Ch60)
  cos สูงแต่ rank ตก → RRF/rerank กด (Ch11/18 breakdown)
```
- **breakdown = เครื่องมือ debug playbook (Ch54 §54.4)** ที่มีตัวเลขจริงประกอบ

---

## 73.5 explainability สร้างความเชื่อมั่น (trust)

```
user เชื่อระบบเมื่อเข้าใจว่าทำไม → explain = adoption
"เจอเพราะ similar 0.83 + คุณเปิดบ่อย (heat)" > "เจอเพราะ AI" (black box)
```
- **สำคัญกับ second brain**: user ต้องเชื่อว่าระบบไม่พลาดของสำคัญ → explain ช่วย verify
- cite/provenance (Ch26): "มาจากไฟล์ X บรรทัด Y" → explain แหล่ง (คู่กับ explain relevance)

---

## 73.6 เชื่อม ARRA

```
score breakdown (§73.1): vector rank + fts rank + rrf (Ch4/11) + heat (Ch13) + recency (Ch61)
  → แสดงได้เพราะ ARRA เก็บ signal แยก (Ch4 fusedScore, confidenceWeight)
provenance (Ch26): result → source file/chunk → explain แหล่ง
debug (§73.4 + Ch54): cos ต่ำ? rank กด? → breakdown ชี้จุด
→ ARRA อธิบายได้ (ไม่ black box) เพราะ hybrid signal โปร่งใส + metadata (Ch51)
```
- **community**: "เชื่อได้ไงว่าไม่พลาด" → score breakdown + provenance ให้ verify เองได้

---

## สรุป Ch73
```
vector search อธิบายยากกว่า keyword (cos 0.83 มาจากไหน?) → black box → เสีย trust/debug ยาก
⭐ score breakdown: แยก vector/fts/rrf/heat/recency contribution (Ch4/11/13/61) → เห็นตัวไหนดันขึ้น/ลง
term-level attribution: ลบ token → cos ตก = token สำคัญ (แพง, debug only) · ColBERT (Ch40) ฟรี
nearest-neighbor + visualize (UMAP/PCA Ch36) = explain neighborhood
⚠️ debug miss (Ch54): breakdown ชี้ cos ต่ำ (vocab gap Ch57/negation Ch60) หรือ rank กด (RRF/rerank)
explain = trust = adoption · provenance (Ch26) explain แหล่ง คู่ explain relevance
ARRA: hybrid signal โปร่งใส + metadata → อธิบายได้ (ไม่ black box)
```
**ถัดไป Ch74:** A/B testing retrieval quality — online eval, interleaving, sequential testing, ทำไม A/B retrieval ต่างจาก A/B ปกติ, sample size
---
*grounded: score breakdown · term attribution · ColBERT explainability (Ch40) · UMAP/t-SNE viz · provenance (Ch26) · เชื่อม Ch4/11/12/13/18/26/34/36/40/54/57/60/61 · /loop deep iter 2026-07-16*
