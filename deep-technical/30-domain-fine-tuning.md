# Deep Technical · Chapter 30 — Domain Fine-Tuning (ปรับ embedder เข้า domain)

> ต่อจาก Ch29 · bge-m3 general-purpose · ถ้าอยากแม่นเฉพาะ domain วิจัยไทย → fine-tune · บทนี้: ทำยังไง + เมื่อไหร่ควร/ไม่ควร

---

## 30.0 ทำไม fine-tune — domain gap

general embedder เรียนจากเว็บทั่วไป · domain เฉพาะ (การแพทย์ไทย, กฎหมาย, งานวิจัยเฉพาะทาง) มี:
- ศัพท์เทคนิคที่ general model ไม่เข้าใจความสัมพันธ์ (เช่น "HbA1c" ↔ "น้ำตาลสะสม")
- ความหมายเฉพาะบริบท (คำเดียวกันความหมายต่างในแต่ละ field)
→ general cosine อาจจับ domain-similarity พลาด → fine-tune ดึงปริภูมิให้เข้า domain

---

## 30.1 2 แนวทาง

**(a) Continued pretraining** (MLM ต่อ): เทรน masked-LM ต่อบน domain corpus (ไม่มี label) → โมเดลคุ้นศัพท์ domain · แต่ **ไม่ปรับ retrieval โดยตรง**

**(b) Contrastive fine-tuning** (แนะนำ): เทรนด้วย InfoNCE (Ch2 §2.5) บน **คู่ (query, relevant doc) ของ domain** → ปรับปริภูมิให้ domain-relevant ใกล้กัน · ตรงเป้า retrieval

---

## 30.2 ⭐ สร้าง training pairs จาก corpus ตัวเอง (ไม่ต้อง label มือ)

ปัญหา: ไม่มี labeled (query, doc) ของ domain · ทางแก้ (synthetic):
```
1. เอา doc/chunk จาก vault
2. ให้ LLM แต่ง "query ที่ doc นี้ตอบได้" ต่อ doc → (synthetic query, doc) = positive pair
3. hard negatives: retrieve doc ใกล้ๆ ที่ไม่ใช่ (Ch22 §22.3)
4. เทรน InfoNCE
```
- ARRA มี 35k memory entries = แหล่ง generate pair ได้เลย (self-supervised จาก vault ตัวเอง)
- reranker (Ch18) filter false negatives + ให้ soft label (distill, Ch22)

---

## 30.3 LoRA — fine-tune ประหยัด

full fine-tune bge-m3 (หลายร้อยล้าน param) = แพง/กิน GPU · **LoRA** (Low-Rank Adaptation):
```
W' = W + ΔW,   ΔW = B·A     (A: r×d, B: d×r,  r ≪ d เช่น r=8)
```
- freeze W เดิม · เทรนแค่ A,B (พารามิเตอร์น้อยมาก ~0.1%)
- **rank r ต่ำ**: สมมติว่าการปรับ domain อยู่ใน subspace มิติต่ำ → พอ
- ✅ เทรนเร็ว/GPU น้อย, สลับ adapter ต่อ domain ได้ · ❌ ปรับได้จำกัดกว่า full

---

## 30.4 Evaluation (Ch6 บังคับ)

**ห้าม fine-tune แล้วเชื่อว่าดีขึ้นโดยไม่วัด**:
```
1. hold-out test set (domain queries + relevant) ที่ไม่ได้อยู่ใน train
2. วัด recall@k / nDCG (Ch6) ก่อน vs หลัง fine-tune
3. ระวัง overfitting: ดีขึ้นบน train แต่แย่ลงบน general → catastrophic forgetting
4. drift check (Ch6 §6.6): fine-tuned vs original — parity บน general queries ยังโอเคไหม
```

---

## 30.5 Thai research domain — specifics

- **ศัพท์การแพทย์ไทย-อังกฤษปน** (Ch ajfon audience หมอ): "prescribe ยา", "HbA1c ระดับ" → fine-tune บน code-switching corpus (Ch19 §19.5)
- **paper ไทย + อังกฤษ**: cross-lingual pairs (บทคัดย่อไทย ↔ abstract อังกฤษ) = training signal ฟรี (Ch19 §19.2)
- bge-m3 multilingual base ดีอยู่แล้ว → LoRA เบาๆ บน domain pair มักพอ ไม่ต้อง full

---

## 30.6 เมื่อไหร่ **ไม่ควร** fine-tune

- corpus เล็ก (< พันคู่) → overfitting · bge-m3 general มักพอ
- domain ใกล้ general (ข่าว, บทความทั่วไป) → gain น้อย ไม่คุ้ม
- ไม่มี eval set → fine-tune แบบตาบอด = เสี่ยงแย่ลงโดยไม่รู้
- **หลัก**: เริ่มจาก bge-m3 + hybrid + rerank (Ch4/18) ให้สุดก่อน · fine-tune = ทางเลือกสุดท้ายเมื่อวัดแล้วว่า embedder เป็นคอขวดจริง

---

## 30.7 ARRA reality

ARRA ใช้ bge-m3 general (ยังไม่ fine-tune) · เหมาะแล้วสำหรับ second-brain ทั่วไป · fine-tune = advanced เมื่อมี domain corpus ใหญ่ + eval + คอขวดที่ embedder จริง · workshop ไม่ต้องแตะ (general พอ, Ch19 multilingual จับไทยได้)

---

## สรุป Ch30
```
domain gap → fine-tune: continued-pretrain (คุ้นศัพท์) vs contrastive (ตรง retrieval)
สร้าง pair เอง: LLM แต่ง query ต่อ doc + hard-neg + reranker filter (self-supervised จาก vault)
LoRA: W+BA (r≪d) → เทรนเร็ว/GPU น้อย, สลับ adapter
eval บังคับ (Ch6): recall/nDCG ก่อน-หลัง + กัน overfit/forgetting + drift
ไทย: code-switching + cross-lingual pair · bge-m3 general มักพอ → fine-tune = ทางเลือกสุดท้าย
```
**ถัดไป Ch31:** A/B testing & online eval — วัด retrieval บน traffic จริง (click, dwell, implicit feedback), interleaving, guardrail metrics
---
*grounded: contrastive fine-tune (SBERT/GTE) · synthetic query gen (Doc2Query/InPars) · LoRA (Hu 2021) · เชื่อม Ch2/6/18/19/22 · /loop deep iter 2026-07-13*
