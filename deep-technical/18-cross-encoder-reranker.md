# Deep Technical · Chapter 18 — Cross-Encoder Reranker (math)

> ต่อจาก Ch17 · Ch4 §4.5 บอก ARRA มี bge-reranker เป็นชั้นสุดท้าย · บทนี้ลงคณิต+สถาปัตย์ทำไมแม่นกว่า embedding

---

## 18.0 ทวน: bi-encoder vs cross-encoder

```
bi-encoder (embedding, Ch2):
   query → [encoder] → q      แยกกัน (precompute ล่วงหน้าได้)
   doc   → [encoder] → d      → score = cos(q,d)
   เร็ว (index doc ล่วงหน้า) แต่ q กับ d ไม่ "คุยกัน" → หยาบ

cross-encoder (reranker):
   [CLS] query [SEP] doc [SEP] → [encoder] → score  (q,d เข้าด้วยกัน)
   attention ข้าม query↔doc ทุก token → แม่น แต่ทำล่วงหน้าไม่ได้
```

---

## 18.1 สถาปัตยกรรม cross-encoder

```
input:  [CLS] q₁ q₂ … [SEP] d₁ d₂ … [SEP]
        → transformer (self-attention ข้าม q และ d, Ch10)
        → เอา [CLS] vector → linear head → scalar score s(q,d)
```
**หัวใจ**: self-attention (Ch10) ให้ token ของ query "มอง" token ของ doc **โดยตรง** → จับ interaction ละเอียด เช่น "query ถามเรื่อง X, doc พูด X จริงไหม ในบริบทไหน" · bi-encoder ทำไม่ได้เพราะ encode แยก

---

## 18.2 ทำไมแม่นกว่า (เชิงข้อมูล)

bi-encoder บีบ doc เป็น 1 เวกเตอร์**ก่อนเห็น query** → ต้องเดาว่า query จะถามอะไร → เก็บข้อมูลทั่วไป (lossy)
cross-encoder เห็น query+doc พร้อมกัน → focus เฉพาะส่วนที่เกี่ยวกับ query นี้ → ไม่ lossy สำหรับ query นี้

**แต่**: ต้องรัน encoder ใหม่ **ต่อคู่ (q,d)** — 1M docs = 1M forward passes/query → **เป็นไปไม่ได้ที่จะ rerank ทั้ง corpus** → ต้อง retrieve หยาบก่อน (§18.5)

---

## 18.3 Training loss

**Pointwise** (regression/classification): ทำนาย rel score ต่อ (q,d) เดี่ยว
```
L = BCE(σ(s(q,d)), label)      label ∈ {0,1}
```

**Pairwise** (เรียนลำดับ): ให้คู่ (d⁺ relevant, d⁻ irrelevant)
```
L = max(0, margin − s(q,d⁺) + s(q,d⁻))     hinge
   หรือ  −log σ(s(q,d⁺) − s(q,d⁻))          RankNet
```
→ บังคับ `s(q,d⁺) > s(q,d⁻)` (คู่ที่ควรอันดับสูงกว่า)

**Listwise** (optimize ทั้งลิสต์): LambdaRank ปรับ gradient ตาม ΔnDCG (Ch6) → optimize metric ranking ตรงๆ

---

## 18.4 bge-reranker-v2-m3

- base = bge-m3 (Ch7) → multilingual (ไทย/อังกฤษ), 8192 ctx
- fine-tune เป็น cross-encoder ด้วย pairwise/listwise บนคู่ query-doc
- output: relevance score (ใช้เรียง top-N ใหม่)
- ~2.3GB model, รันเป็น Python sidecar :8765 (Ch ecosystem: no JS/Ollama support)

---

## 18.5 Pipeline math — ทำไม 2 ชั้นถึงคุ้ม

```
stage 1 (recall): bi-encoder + ANN → top-50 จาก 35,164 docs
                  cost: 1 embed + ANN O(log n)          (เร็ว)
stage 2 (precision): cross-encoder rerank 50 → top-5
                  cost: 50 forward passes                (แพงแต่แค่ 50)
```
**เทียบ**: rerank ทั้ง 35k = 35k forward = ตาย · rerank แค่ 50 = 50 forward = ไหว
- **สมมติฐานที่ต้องจริง**: relevant ตัวจริงต้องติด top-50 ของ stage 1 (recall@50 สูง) — ถ้า stage 1 พลาด stage 2 ช่วยไม่ได้ · นี่คือเหตุผล stage 1 เน้น **recall** (Ch6 §6.1)
- ตัวเลข: recall@50 ~0.95 + rerank ยก precision@5 จาก ~0.6 → ~0.85 (ตัวอย่าง)

---

## 18.6 Distillation — reranker สอน embedding (loop กลับ Ch2)

cross-encoder แม่นแต่ช้า · embedding เร็วแต่หยาบ → **distill**: ใช้ cross-encoder เป็น "teacher" ให้คะแนน soft label แล้วเทรน bi-encoder (student) เลียน
```
L_distill = KL( student_scores ‖ teacher_scores )
```
→ embedding ดีขึ้นโดยไม่เสีย speed · bge-m3 เอง (Ch7) ก็ใช้ distillation จาก reranker ตอน train (hard-negative mining + distill) → นี่คือ loop: reranker ยกคุณภาพ embedding ที่ retrieve มา rerank อีกที

---

## 18.7 เมื่อไหร่ข้าม reranker

- corpus เล็ก + bi-encoder ดีพอ → ข้ามได้ (ประหยัด 2.3GB model + latency)
- ARRA 35k docs, query ทั่วไป → hybrid+RRF อาจพอ · reranker เปิดเมื่อต้องการ precision สูง (เช่น oracle_ask ที่ต้องแม่น)
- trade: reranker +latency +RAM (2.3GB) แลก precision@k

---

## สรุป Ch18
```
cross-encoder: [CLS] q [SEP] d [SEP] → score, attention ข้าม q↔d → แม่น แต่ทำล่วงหน้าไม่ได้
loss: pointwise(BCE)/pairwise(hinge,RankNet)/listwise(LambdaRank→ΔnDCG)
pipeline: bi-encoder recall top-50 (เร็ว) → cross-encoder rerank top-5 (แพงแต่แค่ 50)
  → ต้อง recall@50 สูง (stage1 พลาด stage2 ช่วยไม่ได้)
distillation: cross-encoder(teacher) → embedding(student) via KL → bge-m3 ใช้จริง
```
**ถัดไป Ch19:** multilingual alignment — ทำไม bge-m3 ค้นไทยเจอ doc อังกฤษได้ (cross-lingual embedding space), การ train แบบ parallel/contrastive ข้ามภาษา

---
*grounded: cross-encoder (Nogueira & Cho 2019, monoBERT) · RankNet/LambdaRank (Burges) · bge-reranker-v2-m3 (BAAI) · services/reranker-py · distillation (Hinton 2015) · เชื่อม Ch2/4/7 · /loop deep iter 2026-07-13*
