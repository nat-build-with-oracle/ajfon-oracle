# Deep Technical · Chapter 74 — A/B Testing Retrieval Quality

> ต่อจาก Ch73 · Ch31 เกริ่น online eval · บทนี้ลงลึก: interleaving, sequential testing, sample size, ทำไม A/B retrieval ต่างจาก A/B ปกติ

---

## 74.0 ทำไม offline eval (Ch20/72) ไม่พอ

```
golden set (Ch72): วัดบน query ที่ label ไว้ → แต่ query จริงหลากหลายกว่า
→ ranker ใหม่ชนะ golden set แต่แพ้ traffic จริง? (golden ไม่ครอบ, Ch39 overfitting)
→ ต้องวัดบน user จริง = A/B test (online)
```
- offline = กรองคร่าว (เร็ว, ปลอดภัย) · online = ตัดสินสุดท้าย (จริง แต่เสี่ยง user เห็นของแย่)

---

## 74.1 A/B พื้นฐาน — split traffic

```
control (A): ranker เดิม | treatment (B): ranker ใหม่
สุ่ม user → A หรือ B → วัด metric (Ch74 §74.2) → เทียบ
สถิติ: t-test/z-test → B ดีกว่า A อย่างมีนัยสำคัญไหม (p-value)
```
- randomize ต่อ user (ไม่ใช่ต่อ query) → user เห็น experience สม่ำเสมอ

---

## 74.2 metric สำหรับ A/B retrieval

```
online (implicit, Ch31/63):
  click-through rate (CTR): คลิกผล / query
  reciprocal rank ของ click: คลิกอันบน = ดี (MRR-style, Ch6)
  dwell time: เปิดอ่านนาน = relevant (ไม่ bounce)
  reformulation rate: ค้นใหม่บ่อย = ไม่เจอ (สัญญาณลบ)
  success: ทำ task สำเร็จ (คัดลอก/ใช้ result)
```
- ⚠️ position bias (Ch63): CTR เอนตามตำแหน่ง → interleaving แก้ (§74.3)

---

## 74.3 ⭐ interleaving — sensitive กว่า A/B

A/B แยก user (A เห็น A, B เห็น B) → ต้อง traffic เยอะ · **interleaving** ผสมในผลเดียว:
```
team-draft interleaving: สลับหยิบผลจาก A และ B → 1 result list ผสม
user คลิก → นับว่าผลนั้นมาจาก A หรือ B → ตัวไหนถูกคลิกมากกว่า = ดีกว่า
```
- **ข้อดี**: user คนเดียวเทียบ A vs B พร้อมกัน (ควบคุม user preference) → **ต้องการ sample น้อยกว่า A/B 10-100×**
- แก้ position bias (team-draft สลับยุติธรรม) → sensitive + เร็ว

---

## 74.4 ⚠️ sample size & significance

```
ต้องการ N เท่าไรถึงเชื่อได้:
  effect size เล็ก (B ดีกว่า A นิดเดียว) → ต้อง N เยอะ (power analysis)
  N ← (z_α + z_β)² × 2σ² / Δ²    (Δ = effect ที่อยากจับ)
→ retrieval effect มัก เล็ก → A/B ต้อง traffic มหาศาล → interleaving (§74.3) ช่วย
```
- ⚠️ **peeking**: ดูผลก่อนครบ N → หยุดตอนดูดี → false positive (multiple testing)
- แก้: fix N ล่วงหน้า หรือ **sequential testing** (§74.5)

---

## 74.5 sequential testing — หยุดเร็วได้อย่างถูกต้อง

```
fixed-N: รอครบ N แล้วดู (ช้าถ้า B ดีชัด, เปลืองถ้า B แย่ชัด)
sequential (SPRT/mSPRT): ดูต่อเนื่อง + หยุดเมื่อมั่นใจ (ควบคุม false positive ถูกต้อง)
→ B ดีชัด → หยุดเร็ว (ship) · B แย่ชัด → หยุดเร็ว (kill) · ก้ำกึ่ง → เก็บต่อ
```
- always-valid p-value → peek ได้โดยไม่ inflate error → เร็ว + ถูกต้อง

---

## 74.6 เชื่อม ARRA (single-user context)

```
ARRA personal (1 user): A/B แบบ crowd ทำไม่ได้ (ไม่มี traffic เยอะ)!
→ แทนด้วย:
  - self-comparison: user ลอง 2 config → รู้สึกอันไหนดี (qualitative)
  - offline golden set ส่วนตัว (Ch72): query ตัวเอง → วัด (เชื่อได้สุดสำหรับ personal)
  - heat trend (Ch13): config ใหม่ทำให้เจอของที่ใช้บ่อยขึ้นไหม
online A/B เต็มรูป (§74.3) = สำหรับ multi-user (ทีม/service) → ARRA edge (Ch14/69)
```
- **บทเรียน**: A/B online = เครื่องมือ scale (มี traffic) · personal → offline eval + self-judge (Ch72)

---

## สรุป Ch74
```
offline (golden Ch72) กรองคร่าว · online A/B = ตัดสินจริงบน user (แต่เสี่ยง)
A/B: split user (ไม่ใช่ query) → metric online (CTR/dwell/reformulation Ch31/63) → t-test
⚠️ position bias (Ch63) → CTR เอน → ⭐ interleaving (team-draft): ผสม A/B ใน list เดียว, sample น้อยกว่า 10-100×
⚠️ sample size: effect retrieval เล็ก → N เยอะ (power analysis) · peeking=false positive
⭐ sequential testing (SPRT): หยุดเร็วถูกต้อง (B ดี→ship, แย่→kill) · always-valid p
ARRA personal: A/B crowd ทำไม่ได้ → offline golden ส่วนตัว (Ch72) + self-judge + heat trend
online A/B = scale tool (multi-user, ARRA edge Ch69)
```
**ถัดไป Ch75:** retrieval for RAG — context assembly, ordering (lost-in-the-middle), token budget packing, ทำไมลำดับ context กระทบคำตอบ LLM
---
*grounded: interleaving (Chapelle/Radlinski) · sequential testing (SPRT/mSPRT) · power analysis · position bias (Ch63) · online metrics (Ch31) · เชื่อม Ch6/13/14/20/31/39/63/69/72 · /loop deep iter 2026-07-16*
