# Deep Technical · Chapter 56 — Hybrid Weight Tuning

> ต่อจาก Ch55 · Ch4/11 = RRF รวม dense+sparse · บทนี้: **ปรับน้ำหนัก** dense vs sparse ยังไง, เมื่อไหร่ใครเด่น, tune บน eval (ไม่ใช่เดา)

---

## 56.0 hybrid มี knob ให้ปรับ

```
RRF (Ch11): score = Σ 1/(k + rank_i)  — k คุมว่าอันดับต้นถ่วงแรงแค่ไหน
linear:     score = α·dense + (1−α)·sparse  — α คุมสัดส่วน dense/sparse
weighted RRF: score = Σ wᵢ/(k + rank_i)  — wᵢ ต่อ retriever
```
→ ต้องเลือก k / α / wᵢ · ค่าผิด → hybrid แย่กว่า single retriever ได้!

---

## 56.1 ⭐ ทำไม RRF ไม่ต้องปรับ α (ข้อดี)

linear (α·dense + (1−α)·sparse) มีปัญหา: **score scale ต่างกัน**
```
dense cosine ∈ [−1,1] · BM25 ∈ [0,∞) ไม่ bounded → บวกตรงๆ ไม่ได้ (scale ชน)
→ ต้อง normalize score ก่อน (min-max/z-score) → เปราะ (ขึ้นกับ distribution query นั้น)
```
RRF ใช้ **rank** ไม่ใช่ score → scale-free (Ch11):
```
rank 1,2,3... เหมือนกันทั้ง dense/sparse → รวมได้เลย ไม่ต้อง normalize
→ ทำไม arra-oracle-v3 เลือก RRF (Ch4): robust, ไม่ต้อง tune α ต่อ query
```
- k=60 (Ch4 fusedScore 0.016393=1/61) = ค่ามาตรฐานที่งานวิจัยพบว่า robust ข้าม dataset

---

## 56.2 k ใน RRF — ปรับอะไร

```
k เล็ก (เช่น 10):  อันดับต้นถ่วงแรงมาก (1/11 vs 1/12 ต่างเยอะ) → เชื่อ top rank
k ใหญ่ (เช่น 100): แบนราบ (1/101 vs 1/102 ต่างนิด) → เฉลี่ยหลายอันดับ
k=60:              สมดุล (ค่า default งานวิจัย Cormack 2009)
```
- ปรับ k เมื่อ: retriever หนึ่งน่าเชื่อกว่ามาก (ลด k ให้ top ถ่วงแรง) — แต่มัก k=60 พอ

---

## 56.3 เมื่อไหร่ dense เด่น / sparse เด่น

```
dense (vector) เด่น: query เชิงความหมาย/พาราเฟรส ("วิธีลดน้ำหนัก" ↔ "ควบคุมอาหาร")
                     ภาษาต่างคำเหมือนความหมาย (Ch19 cross-lingual)
sparse (BM25) เด่น:  exact term, ชื่อเฉพาะ, รหัส, ตัวเลข ("ESP32", "error 0x1F", "มาตรา 44")
                     คำหายาก (dense อาจไม่เคยเห็นตอน train, Ch41 OOV)
```
- → **hybrid ชนะเพราะครอบทั้งคู่** (Ch41 §41.5) · น้ำหนักที่ดี = ปล่อยให้แต่ละตัวเด่นในเขตของมัน

---

## 56.4 ⭐ tune บน eval ไม่ใช่เดา

```
1. eval set (Ch20/39): (query, relevant docs) ของ corpus เรา
2. grid/bayesian search: ลอง k ∈ {10,30,60,100}, α ∈ {0.3..0.7}
3. วัด nDCG@10 (Ch6) แต่ละค่า → เลือกที่ชนะ
4. cross-validate: อย่า overfit eval set เล็ก (Ch39 §39.4)
```
- **สำคัญ**: tune บน corpus ตัวเอง — ค่า optimal ต่างกันตาม domain (โน้ตเทคนิค sparse เด่นกว่าโน้ตเล่าเรื่อง)
- ARRA default k=60 = จุดเริ่มที่ดี · tune ต่อถ้ามี eval set (ส่วนใหญ่ default พอ)

---

## 56.5 per-query adaptive weight (ขั้นสูง)

```
บาง query ควรเชื่อ sparse มากกว่า (มีชื่อเฉพาะ) · บางอัน dense (เชิงความหมาย)
→ adaptive: ตรวจ query (มี exact term/รหัสไหม?) → ปรับ weight ต่อ query
เช่น query มี quoted string / ตัวเลข → boost sparse
```
- ซับซ้อนขึ้น · ARRA ใช้ RRF fixed k=60 (robust พอ) · adaptive = optimization ถ้าจำเป็น

---

## 56.6 เชื่อม ARRA

```
RRF k=60 (Ch4 §56.1) → scale-free, ไม่ต้อง tune α ต่อ query → robust default
confidenceWeight 0.25 (Ch4) → ถ่วง signal เพิ่ม (heat Ch13?) บน fused score
dense เด่นความหมาย + sparse เด่น exact (§56.3) → ครอบคำถามหลากหลาย (community)
tune ต่อได้ถ้ามี eval (§56.4) แต่ default พอสำหรับ personal
```

---

## สรุป Ch56
```
hybrid knob: RRF k / linear α / weighted wᵢ — ผิด→แย่กว่า single
⭐ RRF > linear: rank scale-free (dense cos vs BM25 unbounded ชน) → ไม่ต้อง normalize/tune α
k=60: default งานวิจัย (Cormack 2009, ARRA fusedScore 1/61) robust ข้าม dataset
dense เด่น: semantic/paraphrase/cross-lingual · sparse เด่น: exact term/ชื่อ/รหัส/OOV
⭐ tune บน eval corpus เรา (nDCG grid search) ไม่ใช่เดา · cross-validate กัน overfit
adaptive per-query weight = ขั้นสูง (ARRA fixed k=60 robust พอ)
```
**ถัดไป Ch57:** query expansion & rewriting — HyDE, pseudo-relevance feedback, multi-query, ทำไมขยาย query ช่วย recall
---
*grounded: RRF (Cormack 2009, k=60) · arra-oracle-v3 (fusedScore 1/61, confidenceWeight 0.25) · scale-free rank fusion · เชื่อม Ch4/6/11/13/19/20/39/41 · /loop deep iter 2026-07-16*
