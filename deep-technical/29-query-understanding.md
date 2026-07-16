# Deep Technical · Chapter 29 — Query Understanding

> ต่อจาก Ch28 · ก่อนถึง embed(query) มีงานทำได้เยอะ · query สั้น/กำกวมกว่า document เสมอ → ปรับปรุงก่อนค้น = recall ดีขึ้นมาก

---

## 29.0 ปัญหา: query เป็นสัญญาณอ่อน

```
document: ย่อหน้าเต็ม บริบทครบ → เวกเตอร์คม
query:    "เบาหวาน AI" 2-3 คำ กำกวม → เวกเตอร์คลุมเครือ
```
**asymmetry** (Ch2 §2.7): query สั้น doc ยาว → prefix ต่างกัน ยังไม่พอ · ปรับ query ก่อน embed ช่วยได้

---

## 29.1 Query Expansion

เติมคำเกี่ยวข้องเข้า query ก่อน embed:
```
"เบาหวาน" → "เบาหวาน โรคเบาหวาน diabetes น้ำตาลในเลือด HbA1c"
```
- **classic (PRF, pseudo-relevance feedback)**: ค้นรอบแรก → เอา top docs มาดึงคำเด่น → เติม query → ค้นรอบสอง
- **LLM-based**: ให้ LLM แตกคำพ้อง/ศัพท์เทคนิค → ครอบคลุมกว่า
- แลก: expand มากไป → query เบลอ (drift ออกจากเจตนา)

---

## 29.2 ⭐ HyDE — Hypothetical Document Embeddings

trick ฉลาด: แทน embed query สั้น → **ให้ LLM แต่ง "คำตอบสมมติ" ก่อน แล้ว embed คำตอบนั้น**
```
query: "AI ช่วยวินิจฉัยเบาหวานยังไง"
   → LLM แต่ง fake answer: "AI ใช้ ML วิเคราะห์ค่า HbA1c, retinal image...
      ช่วยแพทย์วินิจฉัยเบาหวานเร็วขึ้น..."  (อาจผิดข้อเท็จจริง — ไม่เป็นไร!)
   → embed(fake answer)  ← เวกเตอร์นี้ "หน้าตาเหมือน document" มากกว่า query สั้น
   → ค้นด้วยเวกเตอร์นี้ → match document จริงดีขึ้น
```
**ทำไมเวิร์ก**: fake answer อยู่ในปริภูมิ "document" (ยาว มีศัพท์เทคนิค) → ใกล้ document จริงมากกว่า query สั้น · แก้ asymmetry โดยตรง
- **caveat**: fake answer อาจ hallucinate ทิศทาง → drift · ใช้ดีกับ query ที่ตอบได้เป็นย่อหน้า

---

## 29.3 Multi-Query — หลายมุมแล้ว fuse

```
query → LLM สร้าง N variant:
   "เบาหวาน AI" → ["AI วินิจฉัยเบาหวาน", "machine learning diabetes",
                   "deep learning สำหรับ HbA1c"]
   → ค้นแต่ละ variant → RRF fuse ผล (Ch11!)
```
- ครอบคลุมหลายการตีความ · variant ต่างมุม → fusion ได้ประโยชน์ (Kendall τ ต่ำ, Ch11 §11.5)
- แลก: N เท่าของ query cost

---

## 29.4 Query Rewriting (conversational → standalone)

ในบทสนทนา query พึ่ง context:
```
user: "เบาหวานรักษายังไง"
user: "แล้วผลข้างเคียงล่ะ"   ← "ผลข้างเคียง" ของอะไร? ต้อง rewrite
   → rewrite: "ผลข้างเคียงของการรักษาเบาหวาน"  (standalone)
   → embed ตัว rewrite
```
- สำคัญกับ agent ที่ค้นกลางบทสนทนา (Ch15 muninn_search ถูกเรียกใน session) → ต้อง resolve reference ก่อน

---

## 29.5 Intent Routing (FTS vs vector vs hybrid)

เลือก mode (Ch4 §4.6) ตาม query:
```
query มี exact term (ชื่อยา, DOI, code) → FTS เด่น
query เชิงแนวคิด/กว้าง                    → vector เด่น
default                                   → hybrid (Ch4)
```
- classifier เบาๆ หรือ heuristic (มี quote/ตัวเลข/code → FTS weight สูง)
- ARRA default hybrid (ปลอดภัย) แต่ route ได้ถ้าอยาก optimize

---

## 29.6 pipeline รวม (query-side เต็ม)

```
raw query
  → rewrite (ถ้า conversational, §29.4)
  → intent route (§29.5)
  → [expand §29.1 | HyDE §29.2 | multi-query §29.3]  (เลือกตาม intent)
  → embed (Ch2) → ANN (Ch3) → RRF (Ch11) → rerank (Ch18)
```
→ query understanding = ชั้นก่อน embed ที่ ARRA ยังทำน้อย (default: embed ตรง) · **โอกาส optimize**: เพิ่ม HyDE/multi-query สำหรับ oracle_ask ที่ต้อง recall สูง

---

## สรุป Ch29
```
query = สัญญาณอ่อน (สั้น/กำกวม) vs document ยาว → ปรับก่อน embed
expansion: เติมคำพ้อง/PRF/LLM · HyDE: embed คำตอบสมมติ (อยู่ปริภูมิ doc) แก้ asymmetry
multi-query: N variant → RRF fuse (Ch11) · rewrite: conversational→standalone
intent route: exact→FTS, concept→vector, default hybrid
ARRA ทำน้อย (embed ตรง) → HyDE/multi-query = โอกาส optimize oracle_ask
```
**ถัดไป Ch30:** domain fine-tuning — ปรับ bge-m3 ให้เข้า domain วิจัยไทย (contrastive จาก corpus ตัวเอง, LoRA, eval)
---
*grounded: HyDE (Gao 2022) · query expansion/PRF (IR classic) · multi-query→RRF (Ch11) · เชื่อม Ch2 §2.7 (asymmetry), Ch4 §4.6 (modes), Ch15 · /loop deep iter 2026-07-13*
