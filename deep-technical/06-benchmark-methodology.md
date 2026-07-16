# Deep Technical · Chapter 6 — Benchmark & Evaluation Methodology

> ต่อจาก Ch5 · บทนี้: วัด "search ดีแค่ไหน" ยังไงให้เชื่อได้ — เพราะ "รู้สึกว่าดีขึ้น" ไม่ใช่หลักฐาน
> grounded: PR #2740/#2784 (drift harness), data-pack (LoCoMo), src/vector/__tests__/benchmark*.ts

---

## 6.0 ทำไมต้องมี metric (ไม่ใช่ vibe)

เปลี่ยน embedder / index / k ทีนึง คุณภาพ search เปลี่ยน · จะรู้ว่า "ดีขึ้นหรือแย่ลง" ต้องมี **ground truth** (คู่ query→doc ที่ถูก) + **ตัวเลข** · ทุก metric ข้างล่างต้องมี labeled set: query, และ doc ที่ "relevant" (rel=1) vs ไม่ (rel=0)

---

## 6.1 Recall@k — เจอของที่ควรเจอไหม

```
recall@k = (# relevant docs ใน top-k) / (# relevant docs ทั้งหมด)
```
- ตอบ "ของที่เกี่ยว เราดึงมาได้กี่ %"
- retrieval สนใจ recall สูงเป็นหลัก (ดึงมาให้ครบก่อน แล้วค่อย rerank คัด — Ch4 §4.5)
- **ANN recall** (Ch3) เป็น special case: relevant = ผล exact-kNN → วัด "ANN พลาดจาก brute-force แค่ไหน"

ตัวอย่าง: relevant มี 5 doc, top-10 เจอ 4 → recall@10 = 4/5 = 0.8

---

## 6.2 Precision@k — ของที่ดึงมา เกี่ยวกี่ %

```
precision@k = (# relevant ใน top-k) / k
```
- top-10 เจอ relevant 4 → precision@10 = 4/10 = 0.4
- **recall vs precision trade-off**: k ใหญ่ → recall↑ precision↓

---

## 6.3 MRR — Mean Reciprocal Rank (อันดับแรกที่ถูกอยู่ที่เท่าไร)

สำหรับ query q ให้ `rankq` = อันดับของ relevant doc **ตัวแรก**:
```
             1     Q    1
MRR = ───  Σ   ─────────
             Q   q=1  rankq
```
- relevant ตัวแรกอยู่อันดับ 1 → RR=1 · อันดับ 3 → RR=1/3 · ไม่เจอเลย → RR=0
- เหมาะกับงาน "คำตอบเดียว" (เช่น หา doc ที่ตอบคำถามได้) — สนใจว่า "อันแรกที่ถูกโผล่เร็วแค่ไหน"

---

## 6.4 nDCG — Normalized Discounted Cumulative Gain (อันดับสำคัญ + เกรดความเกี่ยว)

metric ทองของ ranking — รับ **เกรดความเกี่ยว** (relᵢ = 0/1/2/3) ไม่ใช่แค่ 0-1 และ **ลงโทษ relevant ที่อยู่อันดับล่าง**

**DCG@k**:
```
           k    2^relᵢ − 1
DCG@k =  Σ    ──────────────
          i=1   log₂(i + 1)
```
- ตัวเศษ `2^relᵢ−1`: เกรดสูง = ได้แต้มเยอะแบบ exponential
- ตัวส่วน `log₂(i+1)`: อันดับล่าง (i มาก) → หารมาก → discount (อันดับ 1 หาร log₂2=1, อันดับ 2 หาร log₂3≈1.58)

**IDCG@k** = DCG ของการเรียง**ที่ดีที่สุดเท่าที่เป็นไปได้** (relevant สูงสุดอยู่บนสุด)

**nDCG@k** = normalize ให้อยู่ [0,1]:
```
nDCG@k = DCG@k / IDCG@k
```
- 1.0 = เรียงสมบูรณ์แบบ · เทียบข้าม query ได้ (normalize แล้ว)

**worked example** (rel = [3,2,0,1] ที่อันดับ 1-4):
```
DCG = (2³−1)/log₂2 + (2²−1)/log₂3 + 0 + (2¹−1)/log₂5
    = 7/1 + 3/1.585 + 0 + 1/2.322
    = 7 + 1.893 + 0.431 = 9.324
IDCG (เรียง rel=[3,2,1,0]) = 7 + 1.893 + 1/2 + 0 = 9.393
nDCG = 9.324/9.393 = 0.993
```

---

## 6.5 MAP — Mean Average Precision

Average Precision (AP) ต่อ query = เฉลี่ย precision ณ ทุกตำแหน่งที่เจอ relevant:
```
        1              N
AP =  ─────    Σ   precision@i × rel(i)
       R          i=1
```
(R = จำนวน relevant, rel(i)=1 ถ้าอันดับ i relevant) · **MAP** = เฉลี่ย AP ข้าม query ทั้งหมด · จับทั้ง precision และอันดับ

---

## 6.6 ⭐ Drift Benchmark — ของ ARRA เอง (#2740/#2784)

ปัญหาเฉพาะตอนย้าย embedder (Ch5 §5.4): local bge-m3 → CF bge-m3 เวกเตอร์อาจเพี้ยน · drift harness วัด 2 ชั้น:

**(1) Embedding drift** — เวกเตอร์เพี้ยนแค่ไหน:
```
drift(d) = 1 − cos( embed_old(d), embed_new(d) )
mean_drift = (1/N) Σ drift(d)      ← ใกล้ 0 = เหมือนเดิม
```

**(2) Retrieval parity** — ผลค้นเปลี่ยนไหม (สำคัญกว่า):
```
parity@k = (1/Q) Σ  |top_k_old(q) ∩ top_k_new(q)| / k
```
- parity@10 = 0.95 → 95% ของ top-10 ยังเหมือนเดิม = ย้ายปลอดภัย
- ถ้า parity ต่ำ → ต้อง **re-embed ทั้งชุด** ด้วย embedder ใหม่ (index เดิมใช้ไม่ได้)

→ นี่คือ "dry-run" ที่ต้องทำหลังได้ token #2680 ก่อนสลับจริง (~1 team-session)

---

## 6.7 Latency & Throughput — เร็วพอไหม

metric ความเร็ว (วัดเป็น percentile ไม่ใช่ค่าเฉลี่ย — ค่าเฉลี่ยโกหกได้):
- **p50** (median): ครึ่งนึงเร็วกว่านี้
- **p95 / p99**: 95%/99% ของ query เร็วกว่านี้ — **tail latency** สำคัญกับ UX ("ส่วนใหญ่เร็ว แต่ 1% ค้าง 5 วิ" = พัง)
- **QPS** (queries/sec): throughput

ในบริบท ARRA: query-time embed (1 vec) เบา · ANN search เบา (Ch3) · **bulk index = ตัวหนัก** (embed พันๆ) → วัดแยก index-time vs query-time

---

## 6.8 Benchmark landscape (จาก data pack — อ้างอย่างระวัง)

- **LoCoMo** (long conversational memory): Letta filesystem **74%** vs mem0-graph 68.5% — แต่ vendor ตัวเลขขัดกัน ±15 จุด → **ห้าม cite เดี่ยวไม่มี caveat**
- **LongMemEval**: Zep 63.8% vs mem0 49% (graph ชนะ temporal) แต่ GraphRAG แพ้ vanilla RAG 13.4% บน single-hop NQ
- บทเรียน: benchmark ขึ้นกับ **ใครรัน + งานอะไร** → วัดบน**ข้อมูลของเราเอง** (drift/parity §6.6) เชื่อได้กว่า vendor number

---

## สรุป Ch6
```
recall@k (เจอครบไหม) · precision@k (ที่ดึงมาเกี่ยวไหม) · MRR (อันแรกถูกอยู่ไหน)
nDCG = DCG/IDCG, DCG=Σ(2^rel−1)/log₂(i+1) (อันดับ+เกรด)
MAP (precision เฉลี่ยทุกตำแหน่ง relevant)
drift benchmark (#2740): embedding drift 1−cos + retrieval parity@k → gate การย้าย CF
latency p50/p95/p99 (ไม่ใช่ mean) · benchmark vendor เชื่อยาก → วัดบนข้อมูลตัวเอง
```
**ถัดไป Ch7:** bge-m3 multi-functionality ลึก — dense + sparse (lexical weights) + ColBERT (multi-vector) ทำงานยังไง, sparse retrieval math, และ hybrid dense+sparse

---
*grounded: PR #2740/#2784 (drift harness) · src/vector/__tests__/benchmark-models*.ts · data-pack (LoCoMo/LongMemEval) · nDCG (Järvelin & Kekäläinen 2002) · MRR/MAP (IR standard) · /loop deep iter 2026-07-13*
