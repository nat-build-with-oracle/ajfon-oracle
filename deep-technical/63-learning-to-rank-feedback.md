# Deep Technical · Chapter 63 — Learning-to-Rank & Feedback Loops

> ต่อจาก Ch62 · ranking ที่ tune มือ (Ch56/61) มีเพดาน · บทนี้: เรียน ranker จาก signal จริง, implicit feedback, ปิด loop, ทำไม feedback = ระบบที่ดีขึ้นเอง

---

## 63.0 ปัญหา — tune มือไม่ scale

```
Ch56/61: เลือก k, α, weight ด้วยมือ + eval set → ดี แต่:
- signal มีหลายสิบ (vector/heat/recency/facet/...) → tune มือไม่ไหว
- relevance เปลี่ยนตามเวลา/user → static weight ล้าสมัย
→ ให้ "ข้อมูลจริง" สอน ranker แทน (learning-to-rank, LTR)
```

---

## 63.1 signal — explicit vs implicit

```
explicit: user บอกตรงๆ (ให้ดาว, thumbs up/down) — แม่นแต่หายาก (คนขี้เกียจกด)
implicit: พฤติกรรม (คลิก, เปิดอ่านนาน, คัดลอก, ค้นต่อ) — เยอะแต่ noisy
```
- **implicit เป็นทองของ retrieval** (Ch31): user ค้น → คลิกผลอันที่ 3 (ข้าม 1,2) → สัญญาณว่า 3 relevant กว่า 1,2
- ⚠️ **position bias**: อันบนถูกคลิกเพราะ "อยู่บน" ไม่ใช่ "ดีกว่า" → ต้อง debias (Ch63 §63.4)

---

## 63.2 ⭐ LTR — 3 ตระกูล

```
pointwise:  ทำนาย relevance score ต่อ doc (regression) → sort
            ง่าย แต่ไม่เห็น "อันดับเทียบกัน"
pairwise:   เรียนคู่ (docA ควรอยู่เหนือ docB?) → RankNet, LambdaRank
            เห็น relative order → ดีกว่า pointwise สำหรับ ranking
listwise:   optimize ทั้ง list ตรงๆ (nDCG, Ch6) → LambdaMART, ListNet
            ตรงเป้า metric สุด → state-of-art LTR แบบคลาสสิก
```
- **LambdaMART** (gradient-boosted trees + LambdaRank) = แชมป์ LTR ยุคก่อน deep — ยังใช้กันมาก

---

## 63.3 pairwise loss — สมการ (RankNet)

```
สำหรับคู่ (i, j) ที่ i ควรอันดับสูงกว่า j:
  P(i > j) = σ(s_i − s_j) = 1/(1 + e^{−(s_i − s_j)})
  loss = −log P(i > j)          (cross-entropy)
→ ดัน s_i > s_j ตาม signal (คลิก i ไม่คลิก j)
```
- `s` = score จาก model (รับ feature: vector_sim, heat, recency...) → เรียน weight ให้จัดอันดับตรงกับ feedback
- **LambdaRank**: คูณ gradient ด้วย |ΔnDCG| (การสลับคู่นี้กระทบ nDCG เท่าไร) → เน้นคู่ที่สำคัญต่อ metric

---

## 63.4 ⚠️ position bias & counterfactual

```
ปัญหา: user คลิกอันบนเพราะเห็นก่อน (ไม่ใช่เพราะดีกว่า) → feedback เอนเอียง
→ ถ้าเรียนตรงๆ → ระบบยิ่งเชื่อ "อันบน = ดี" → feedback loop เสริมอคติตัวเอง (rich-get-richer)
```
แก้:
```
- inverse propensity weighting (IPW): ถ่วง click ด้วย 1/P(เห็นตำแหน่งนั้น) → debias
- randomization: สลับอันดับสุ่มบ้าง → เก็บ signal ที่ไม่เอนตาม position
- counterfactual LTR: ประเมิน "ถ้าจัดอีกแบบจะดีกว่าไหม" จาก log ที่ debias แล้ว
```
- **สำคัญมาก**: ไม่ debias → ระบบเรียนอคติตัวเอง → dubious loop (Ch63 §63.6)

---

## 63.5 online vs offline learning

```
offline: เก็บ log → เทรน ranker เป็น batch (รายวัน/สัปดาห์) → deploy → วัด (Ch31 A/B)
         ปลอดภัย (ตรวจก่อน deploy) แต่ช้า (ไม่ทันของใหม่)
online:  update weight ทันทีจาก feedback (bandit/online GD)
         สดแต่เสี่ยง (feedback พิษ/spam → ranker เสียเร็ว)
```
- ส่วนใหญ่ offline + periodic retrain (Ch46 rebuild pattern) · online เฉพาะที่ต้องสดจริง

---

## 63.6 ⭐ ปิด loop — ระบบดีขึ้นเอง (แต่ระวัง)

```
ค้น → user feedback (คลิก/heat Ch13) → เรียน ranker → ค้นดีขึ้น → feedback ดีขึ้น → ...
= virtuous loop (ดีขึ้นเรื่อยๆ)
⚠️ แต่ถ้าไม่ debias (§63.4): เสริมอคติ → vicious loop (แย่ลงเรื่อยๆ, homogenize)
```
- ต้อง: debias + diversity (Ch59 กัน homogenize) + monitor (Ch54 จับ drift) → loop เป็น virtuous

---

## 63.7 ARRA — feedback ที่มีจริง

```
heat (Ch13): usage_count/last_accessed = implicit feedback ที่ ARRA เก็บอยู่แล้ว!
→ doc ถูกค้นเจอ+ใช้บ่อย = signal ว่า relevant → boost (Ch61 รวม signal)
→ นี่คือ LTR แบบเบา (pointwise implicit) ที่ทำงานแล้วใน ARRA
เต็มรูป (pairwise/listwise LTR): overkill สำหรับ personal · heat pointwise พอ
single-user: position bias น้อย (คนเดียว, ไม่มี crowd effect) → debias เบากว่า web search
```
- **community**: "ระบบเรียนรู้จากการใช้ไหม" → ใช่ (heat) · เต็มรูป LTR = สำหรับ multi-user scale

---

## สรุป Ch63
```
tune มือ (Ch56/61) ไม่ scale → LTR: เรียน ranker จาก signal จริง
signal: explicit (ดาว, แม่นแต่น้อย) vs implicit (คลิก/heat Ch13/31, เยอะแต่ noisy)
⭐ LTR 3 ตระกูล: pointwise(regression) < pairwise(RankNet/Lambda) < listwise(LambdaMART, ตรง nDCG)
pairwise loss: P(i>j)=σ(s_i−s_j), loss=−log P · LambdaRank คูณ |ΔnDCG|
⚠️ position bias: คลิกอันบนเพราะเห็นก่อน → ไม่ debias=เรียนอคติตัวเอง (IPW/randomize/counterfactual)
online(สด/เสี่ยง) vs offline(ปลอดภัย/ช้า) → มัก offline+retrain (Ch46)
⭐ ปิด loop: virtuous (debias+diversity Ch59) vs vicious (homogenize) → monitor (Ch54)
ARRA: heat (Ch13)=implicit LTR เบาที่ทำงานแล้ว · single-user bias น้อย · เต็มรูป=multi-user
```
**ถัดไป Ch64:** vector DB internals — WAL (write-ahead log), MVCC, transaction, crash recovery, ทำไม LanceDB/D1 คงทน
---
*grounded: RankNet/LambdaRank/LambdaMART (Burges) · counterfactual LTR (Joachims) · position bias · heat as implicit (Ch13/31) · เชื่อม Ch6/31/46/54/56/59/61/62 · /loop deep iter 2026-07-16*
