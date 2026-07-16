# Deep Technical · Chapter 11 — RRF & Ranking Theory (พิสูจน์)

> ต่อจาก Ch10 · ลงลึก Reciprocal Rank Fusion ที่ ARRA ใช้รวม FTS+vector (Ch4 §4.3) — ทำไมมันเวิร์ก พิสูจน์เชิงทฤษฎี

---

## 11.1 ทวน RRF

```
              1
RRF(d) = Σ  ────────      (r = แต่ละ ranker: FTS, vector; k=60)
        r∈R  k + rankᵣ(d)
```
ARRA พิสูจน์ k=60 จาก `fusedScore 0.016393 = 1/61` (Ch4)

---

## 11.2 พิสูจน์: ทำไม rank fusion ชนะ score fusion

**ปัญหา score fusion**: รวมคะแนนดิบ `α·BM25 + β·cosine`
- BM25 ∈ [0, ∞) · cosine ∈ [0, 1] → สเกลคนละโลก
- ต้อง normalize (min-max/z-score) ซึ่ง **sensitive ต่อ outlier**: 1 doc คะแนน BM25 พุ่ง → กด doc อื่นหมดหลัง normalize

**RRF ใช้แค่ rank (อันดับ)** → **scale-invariant**:

**Claim**: ถ้าแปลงคะแนนของ ranker ด้วยฟังก์ชัน monotonic เพิ่ม `f` ใดๆ (เช่น ×1000, log, exp) → **rank ไม่เปลี่ยน → RRF ไม่เปลี่ยน**

**Proof**: rank ถูกกำหนดโดยการเรียงลำดับ · `f` monotonic เพิ่ม ⟹ `s(a)>s(b) ⟺ f(s(a))>f(s(b))` ⟹ ลำดับเดิม ⟹ `rankᵣ(d)` เดิม ⟹ `Σ 1/(k+rankᵣ(d))` เดิม ∎

→ RRF ไม่แคร์ว่า BM25 หรือ cosine สเกลเท่าไร แคร์แค่ "ใครมาก่อนใคร" · robust โดยไม่ต้อง tune normalization

---

## 11.3 บทบาทของ k — ทำไม 60

`1/(k + rank)`:
- **k เล็ก (→0)**: `1/rank` → อันดับ 1 ได้ 1.0, อันดับ 2 ได้ 0.5 → **หัวลิสต์ครองงำมาก** (winner-take-all)
- **k ใหญ่**: `1/(k+rank)` แบนราบ → อันดับ 1 กับ 10 ต่างกันน้อย → **ให้เครดิตอันดับกลางๆ มากขึ้น**

k=60 (จาก Cormack et al. 2009, TREC): สมดุลที่ทำงานดีข้าม dataset — ให้หัวลิสต์เด่นแต่ไม่ทิ้งอันดับกลาง

**ผลเชิงเลข** (k=60):
```
rank 1  → 1/61  = 0.01639
rank 2  → 1/62  = 0.01613   (ต่างจากอันดับ 1 แค่ 1.6%)
rank 10 → 1/70  = 0.01429
rank 100→ 1/160 = 0.00625
```
→ doc ที่ติด top ของ **2 ranker** (เช่น rank 2 ใน FTS + rank 3 ใน vector) = 0.01613+0.01587 = 0.032 → **ชนะ doc ที่ rank 1 ใน ranker เดียว** (0.01639) · นี่คือหัวใจ: **consensus ข้าม ranker สำคัญกว่าอันดับ 1 ในลิสต์เดียว**

---

## 11.4 RRF = ระบบเลือกตั้ง (Borda-like)

มอง ranker เป็น "ผู้ลงคะแนน" · RRF คล้าย **Borda count** แต่ให้คะแนนแบบ reciprocal (ไม่เชิงเส้น) → ทนต่อ "ผู้ลงคะแนนที่หางลิสต์มั่ว" (อันดับท้ายได้คะแนนน้อยมากอยู่แล้ว) · ทฤษฎี social choice: aggregation แบบนี้ resist manipulation ได้ดี

---

## 11.5 วัด "ranker 2 ตัวเห็นด้วยกันไหม" — Kendall τ

ก่อนรวม ควรรู้ว่า FTS กับ vector เรียงคล้าย/ต่างแค่ไหน:
```
        (concordant pairs) − (discordant pairs)
τ  =   ────────────────────────────────────────
                  n(n−1)/2
```
- concordant = คู่ (a,b) ที่ทั้ง 2 ranker เรียงทางเดียวกัน
- τ=1 เรียงเหมือนกันเป๊ะ · τ=0 ไม่สัมพันธ์ · τ=−1 กลับด้าน
- **insight**: ถ้า FTS กับ vector τ สูง (เห็นด้วยกันมาก) → fusion ได้ประโยชน์น้อย (ซ้ำกัน) · ถ้า τ ต่ำ (เห็นต่าง จับคนละแบบ) → **fusion ได้ประโยชน์สูงสุด** (เสริมกัน) — ซึ่งเป็นเคสจริง (FTS จับคำ, vector จับความหมาย = ต่างมุม)

---

## 11.6 Confidence-Weighted RRF ของ ARRA (derive)

ARRA (Ch4 §4.4): `final = RRF + confidenceWeight·confidence + heat`

มอง confidence/heat เป็น "prior" บน doc:
```
final(d) = Σ 1/(k+rankᵣ(d))  +  0.25·conf(d)  +  heat(d)
```
- **RRF term** = relevance จาก retrieval (bottom-up จาก query)
- **confidence term** = prior ความน่าเชื่อถือของ memory (top-down)
- **heat term** = recency/frequency prior (doc ใช้บ่อย = น่าจะเกี่ยว)

= **Bayesian-flavored ranking**: likelihood (RRF) × prior (conf/heat) → posterior relevance · นี่คือสิ่งที่ทำให้ ARRA เป็น "second brain" (จำ pattern การใช้) ไม่ใช่ search engine เปล่า

**tuning caveat**: 0.25 เป็น hyperparameter — มากไป heat/conf กลบ relevance (doc เก่ายอดนิยมลอยขึ้นทั้งที่ไม่เกี่ยว) · น้อยไป = ไม่ได้ประโยชน์ personalization → ควร validate ด้วย nDCG (Ch6)

---

## 11.7 ทางเลือก: Learned Fusion (LTR)

แทน RRF (unsupervised) → เทรน model ให้เรียนน้ำหนัก fusion (Learning-to-Rank: LambdaMART, listwise):
- input features: BM25 score, cosine, rank ต่างๆ, doc metadata
- optimize nDCG โดยตรง
- **แลก**: แม่นกว่าถ้ามี labeled data เยอะ · แต่ต้อง label + retrain + overfitting risk · RRF ชนะเมื่อ data น้อย/zero-shot → ARRA เลือก RRF (ไม่ต้อง label)

---

## สรุป Ch11
```
RRF scale-invariant (พิสูจน์: monotonic f ไม่เปลี่ยน rank) → robust ไม่ต้อง normalize
k=60 สมดุล head-vs-mid · consensus 2 ranker ชนะ rank-1 ลิสต์เดียว
Kendall τ: ranker ต่างมุม (τ ต่ำ) → fusion ได้ประโยชน์สุด (FTS vs vector = เคสนี้)
ARRA confidence-weighted RRF = likelihood(RRF) × prior(conf/heat) = Bayesian-ish
```
**ถัดไป Ch12:** chunking — หั่นเอกสารยาวยังไงให้ retrieval แม่น (fixed/semantic/overlap/parent-child), และทำไม memory entry ของ ARRA เป็น chunk ธรรมชาติ

---
*grounded: RRF (Cormack, Clarke, Buettcher SIGIR 2009) · Kendall τ · Borda/social choice · LambdaMART (Burges 2010) · เชื่อม Ch4 §4.3-4.4 · /loop deep iter 2026-07-13*
