# Deep Technical · Chapter 41 — Dense Retrieval History (BM25 → DPR → bge)

> ต่อจาก Ch40 · เข้าใจ "ทำไม vector search เป็นแบบทุกวันนี้" ต้องรู้วิวัฒนาการ · บทเรียนจากประวัติศาสตร์ IR

---

## 41.0 timeline สั้น

```
1970s-2010s: sparse (TF-IDF → BM25)     — ครองงำ IR หลายทศวรรษ
2013:        word2vec                    — คำ→เวกเตอร์ (แต่ยังไม่ retrieval)
2018:        BERT                         — contextual embedding
2020:        DPR                          — dense retrieval ชนะ BM25 ครั้งแรกอย่างชัด
2020-2024:   ANCE→GTR→E5→GTE→bge-m3       — dense embedder ยุคทอง
```

---

## 41.1 ยุค sparse (BM25) — ทำไมอยู่ยาว

BM25 (Ch7 §7.2, Ch34): แข็งแกร่ง, ไม่ต้อง train, interpretable, scale ดี (inverted index)
- **จุดอ่อน**: vocabulary mismatch — "รถ"≠"ยานพาหนะ" (Ch34) · ไม่รู้ความหมาย
- แต่ **baseline ที่ล้มยาก**: หลาย "neural IR" ยุคแรก (2016-2019) แพ้ BM25! → พิสูจน์ว่า neural retrieval ยาก

---

## 41.2 ⭐ DPR (2020) — จุดเปลี่ยน

Dense Passage Retrieval พิสูจน์ว่า dense **ชนะ BM25 ได้จริง** ถ้าเทรนถูก:
```
- bi-encoder (Ch2): question encoder + passage encoder แยก
- เทรนด้วย in-batch negatives (Ch37 §37.1) บน QA pairs
- ผล: top-20 accuracy ชนะ BM25 หลาย point บน open-domain QA
```
- **สิ่งที่ DPR สอน**: dense ไม่ได้ชนะเพราะ architecture ใหม่ — ชนะเพราะ **เทรนบน (query, relevant) pairs + negatives ดี** (Ch37)
- ก่อน DPR: คนคิดว่า BM25 ล้มไม่ได้ · หลัง DPR: dense retrieval boom

---

## 41.3 วิวัฒนาการหลัง DPR (บทเรียนสะสม)

```
DPR (2020):   in-batch negatives → พิสูจน์ dense เวิร์ก
ANCE (2020):  hard negatives async (Ch37 §37.4) → ดีขึ้นมาก
              บทเรียน: hard negatives สำคัญกว่าที่คิด
GTR (2021):   scale up (T5 encoder) → ใหญ่ = ดีขึ้น
E5 (2022):    weakly-supervised pretraining + prefix (Ch2 §2.7)
              บทเรียน: pretraining data เยอะ + asymmetric prefix
GTE/bge (2023-24): multi-stage (pretrain→contrastive→distill) + multilingual
bge-m3 (2024): M3 (Ch7/19/22) — dense+sparse+colbert, 100+ ภาษา, 8192 ctx
```

---

## 41.4 บทเรียนใหญ่ — data + negatives > architecture

ประวัติศาสตร์ retrieval ชี้ชัด:
```
gain ส่วนใหญ่มาจาก:  training data (เยอะ/หลากหลาย) + hard negatives (Ch37) + distillation (Ch22)
gain ส่วนน้อยจาก:    architecture ใหม่ (encoder เปลี่ยนนิดหน่อย)
```
- นี่คือเหตุผลที่ bge-m3 ดี — ไม่ใช่ architecture มหัศจรรย์ แต่ **recipe** (multilingual data + hard-neg + self-distill, Ch22)
- **implication ARRA/Ch30**: ถ้าจะ fine-tune → ทุ่มที่ **data + negatives** ไม่ใช่ architecture

---

## 41.5 sparse ไม่ตาย — hybrid ชนะ

หลัง dense boom คนคิดว่า BM25 ตาย · **แต่ hybrid (dense+sparse, Ch7/11) ชนะทั้งคู่**:
- dense พลาด exact term (ชื่อเฉพาะ, ตัวเลข) → sparse จับ
- sparse พลาด semantic → dense จับ
- → ARRA ใช้ FTS5(BM25) + vector + RRF (Ch4) = สืบทอดบทเรียนนี้โดยตรง

---

## 41.6 เชื่อม ARRA — ทำไมออกแบบแบบนี้

```
FTS5 (BM25, 40 ปีของ IR ที่พิสูจน์แล้ว)     ← Ch41 §41.1
+ vector (bge-m3, ผล DPR→bge วิวัฒนาการ)    ← Ch41 §41.2-3
+ RRF (รวม 2 โลก, hybrid ชนะ)                ← Ch41 §41.5
+ reranker (cross-encoder, precision)        ← Ch18
= สถาปัตยกรรมที่ตกผลึกจากประวัติศาสตร์ IR ทั้งหมด
```
ARRA ไม่ได้ประดิษฐ์ใหม่ — **ประกอบ best practice ที่พิสูจน์แล้ว** อย่างเข้าใจ

---

## สรุป Ch41
```
BM25 ครองงำ 40 ปี (แข็งแต่ vocabulary mismatch) — neural แพ้ยุคแรก
DPR (2020): dense ชนะ BM25 ครั้งแรก — เพราะ train บน pairs + in-batch neg (ไม่ใช่ architecture)
วิวัฒนาการ: DPR→ANCE(hard neg)→GTR(scale)→E5(prefix)→bge-m3(M3)
บทเรียน: data + hard negatives + distillation > architecture
sparse ไม่ตาย → hybrid (dense+sparse) ชนะ = ARRA design (FTS5+vector+RRF)
```
**ถัดไป Ch42:** retrieval-augmented training — RETRO/REALM (retrieval ตอน pretrain), เทียบ RAG-at-inference, implication กับ memory system
---
*grounded: BM25 (Robertson) · DPR (Karpukhin 2020) · ANCE/E5/GTE/bge วิวัฒนาการ · เชื่อม Ch2/7/11/18/22/30/34/37 (ทั้ง reference มาบรรจบ) · /loop deep iter 2026-07-16*
