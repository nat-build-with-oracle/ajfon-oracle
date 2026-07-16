# Deep Technical · Chapter 31 — A/B Testing & Online Eval

> ต่อจาก Ch30 · Ch6 = offline metric (มี ground truth) · แต่ retrieval จริงวัดจาก **behavior ผู้ใช้** ด้วย · บทนี้: online eval

---

## 31.0 offline ไม่พอ

offline (Ch6): recall@k บน labeled set · แต่:
- labeled set ไม่ครอบคลุม query จริงทั้งหมด
- "relevant" ที่ label ≠ สิ่งที่ผู้ใช้อยากได้จริงเสมอ
→ ต้องวัดจาก behavior จริง (online) เสริม

---

## 31.1 Implicit feedback — สัญญาณจากพฤติกรรม

ไม่ต้องให้ผู้ใช้ rate — ดูจากการกระทำ:
```
- click      → ผลนี้ดูน่าสนใจ (weak positive)
- dwell time → เปิดอ่านนาน = เกี่ยวจริง (strong positive)
- reformulate query → ผลไม่ดี ต้องค้นใหม่ (negative signal)
- copy/cite → ใช้จริง (strong positive)  ← ARRA: usage_count++ (Ch13!)
- skip อันบน คลิกอันล่าง → อันบนไม่ดี (pairwise signal)
```
- **noisy**: click ≠ relevant เสมอ (position bias — คนคลิกอันบนเพราะอยู่บน ไม่ใช่เพราะดี)
- ARRA `usage_count`/`last_accessed_at` (Ch13) = implicit feedback ที่ feed กลับ heat → **online learning loop**

---

## 31.2 Interleaving — เทียบ 2 ranker บน traffic เดียว

A/B ปกติแบ่งผู้ใช้ 2 กลุ่ม (variance สูง) · **interleaving** ผสมผลจาก 2 ranker ในลิสต์เดียวให้ผู้ใช้เดียวกัน:
```
Team-Draft Interleaving:
  ranker A, B ผลัดกัน "draft" ผลเข้าลิสต์รวม (เหมือนเลือกทีม)
  ผู้ใช้คลิกอันไหน → ให้เครดิต ranker ที่ draft อันนั้น
  นับ credit → ranker ไหนชนะ
```
- sensitive กว่า A/B มาก (ผู้ใช้เดียวเทียบตรง ลด variance) → ต้องการ traffic น้อยกว่าเพื่อ significance

---

## 31.3 A/B test statistics

เทียบ metric (เช่น click-through, dwell) ระหว่าง control vs treatment:
```
H₀: ไม่ต่าง · H₁: treatment ดีกว่า
two-sample t-test / z-test:
        μ_treatment − μ_control
z  =  ──────────────────────────
         √(σ²_t/n_t + σ²_c/n_c)
p-value < 0.05 → reject H₀ (มั่นใจว่าต่างจริง ไม่ใช่ noise)
```
- **sample size**: ต้องมากพอจับ effect เล็ก · effect เล็ก + traffic น้อย = ไม่ significant (แม้ต่างจริง)
- **ระวัง peeking**: ดูผลระหว่างทางแล้วหยุดเมื่อ significant = false positive สูง → ตั้ง sample size ล่วงหน้า/ใช้ sequential test

---

## 31.4 Guardrail metrics — อย่าดูแค่ metric เป้า

optimize recall อาจทำ latency พัง · ต้องมี **guardrail**:
```
เป้า:      recall@10, nDCG ↑
guardrail: latency p99 ต้องไม่เกิน X, cost ไม่เกิน Y, error rate คงที่
```
- treatment ที่ recall ดีขึ้น 2% แต่ p99 พุ่ง 3× = ไม่ ship (Ch6 §6.7)

---

## 31.5 Online learning loop (เชื่อม Ch13 heat)

```
query → retrieve → ผู้ใช้ใช้ doc X
   → usage_count[X]++, last_accessed[X]=now   (§31.1 implicit)
   → heat[X] ↑ (Ch13)
   → ครั้งหน้า X ขึ้นง่ายขึ้น (ถ้าเกี่ยว)
```
= ระบบเรียนจากการใช้จริง **แบบ online** โดยไม่ต้อง retrain โมเดล · นี่คือ "brain โตไปกับคุณ" เชิงกลไก (Ch13 §13.5)
- **ระวัง feedback loop** (Ch13 §13.6): heat ดันของฮิต → ถูกเห็น/ใช้อีก → ฮิตขึ้น → ต้อง decay + exploration (บางที show ของใหม่ที่ heat ต่ำ เพื่อเก็บ feedback)

---

## 31.6 ARRA context

- ARRA เป็น single-user (second brain) → A/B แบบ traffic เยอะทำยาก · แต่ **implicit feedback (usage/heat) ใช้ได้เต็ม** (Ch13)
- eval หลักของ ARRA = offline benchmark (Ch20) + implicit heat · ไม่ต้อง A/B infra ใหญ่แบบ search engine
- interleaving/A/B = สำหรับตอนเทียบ config (hybrid weight, k, reranker on/off) ถ้าอยาก tune อย่างเข้มงวด

---

## สรุป Ch31
```
offline (Ch6) + online (behavior): click/dwell/reformulate/cite = implicit feedback (noisy, position bias)
interleaving (team-draft) = เทียบ 2 ranker บน user เดียว, sensitive กว่า A/B
A/B stats: z-test, p<0.05, ระวัง peeking + sample size + guardrail (latency/cost)
online learning: usage→heat (Ch13) = เรียนจากการใช้ ไม่ต้อง retrain · ระวัง feedback loop
ARRA single-user: implicit heat เต็ม, A/B ไว้ tune config
```
**ถัดไป Ch32:** caching — result cache, embedding cache, semantic cache, invalidation ตอน index update, heat-as-cache
---
*grounded: implicit feedback/position bias (Joachims) · team-draft interleaving (Radlinski 2008) · A/B stats · เชื่อม Ch6/13/20 · /loop deep iter 2026-07-14*
