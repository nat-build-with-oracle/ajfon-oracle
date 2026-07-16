# Deep Technical · Chapter 76 — Chunk vs Document Retrieval

> ต่อจาก Ch75 · Ch12 = วิธี chunk · บทนี้: ปัญหา "ค้น chunk เล็ก (precise) แต่ context อยากได้ doc เต็ม" → parent-child, small-to-big

---

## 76.0 tension — เล็กดีค้น, ใหญ่ดี context

```
chunk เล็ก (1-2 ประโยค): embed แม่น (Ch12, semantic แคบ→cos ตรง) แต่ context ขาด (LLM ได้แค่เศษ)
chunk ใหญ่ (ทั้งหน้า):    context ครบ แต่ embed เจือจาง (Ch43 topic กลบ→cos ไม่ตรง)
→ ขัดกัน: อยาก embed เล็ก (ค้นแม่น) + ป้อน LLM ใหญ่ (context ครบ)
```

---

## 76.1 ⭐ small-to-big (parent-child)

แยก "หน่วยค้น" กับ "หน่วยป้อน LLM":
```
index: chunk เล็ก (child) → embed แม่น → ค้นด้วยตัวนี้
store: parent (chunk ใหญ่/doc เต็ม) ที่ child สังกัด
retrieve:
  1. ค้น child เล็ก (cos แม่น) → เจอ child X
  2. lookup parent ของ X → ป้อน parent (context ครบ) เข้า LLM
→ ค้นแม่น (เล็ก) + context ครบ (ใหญ่) = ได้ทั้งคู่!
```
- เก็บ relation child→parent (metadata, Ch51/12) → lookup เร็ว

---

## 76.2 variants ของ small-to-big

```
sentence-window: ค้น 1 ประโยค → ป้อน ±N ประโยครอบๆ (window) เป็น context
parent-doc:      ค้น chunk → ป้อน doc เต็มที่ chunk อยู่
summary-index:   ค้น summary (embed สรุป) → ป้อน full doc (Ch12 §12 hierarchical)
hypothetical Q:  index "คำถามที่ doc นี้ตอบได้" → ค้น query match คำถาม → ป้อน doc
```
- เลือกตาม granularity: precise lookup (sentence-window) vs full context (parent-doc)

---

## 76.3 ⚠️ merge overlapping parents

```
ค้น child หลายตัว → หลายตัวชี้ parent เดียวกัน → ป้อน parent ซ้ำ (เปลือง context Ch75)
→ dedup parent (Ch52): child A,B,C → parent P (1 ครั้ง) → ป้อน P เดียว
child ติดกัน → parent overlap → merge เป็นช่วงต่อเนื่อง (ไม่ป้อนซ้อน)
```
- เชื่อม Ch75 (token budget): dedup parent → ประหยัด context สำหรับ doc อื่น

---

## 76.4 chunk size revisited (เชื่อม Ch12)

```
small-to-big ปลดล็อก: ไม่ต้องเลือก chunk size เดียวที่ "ค้นก็ดี context ก็ดี" (เป็นไปไม่ได้ Ch76 §76.0)
→ child เล็ก (ค้น) + parent ใหญ่ (context) = แต่ละหน่วยทำหน้าที่ตัวเอง
→ chunk size decision (Ch12) ง่ายขึ้น: child เล็กสุดที่ยัง semantic สมบูรณ์, parent = ขอบเขต context ธรรมชาติ (section/doc)
```

---

## 76.5 cost & complexity trade

```
small-to-big:
  + ค้นแม่น + context ครบ
  − index child เยอะกว่า (1 doc → หลาย child → หลาย embedding, Ch70 storage)
  − ต้องเก็บ+lookup parent relation (metadata)
เทียบ chunk เดียว: ง่ายกว่า แต่ต้อง compromise (ค้นหรือ context อย่างใดอย่างหนึ่ง)
```
- **เมื่อไหร่ใช้**: doc ยาว/มีโครงสร้าง (บทความ, เอกสาร) → คุ้ม · โน้ตสั้น → chunk เดียวพอ

---

## 76.6 เชื่อม ARRA

```
ARRA chunk (Ch12) + metadata (Ch51): เก็บ chunk_index, source_file → มี relation child→parent อยู่แล้ว!
→ small-to-big ทำได้: ค้น chunk (embed แม่น Ch4) → lookup doc/section เต็มจาก source (Ch26 provenance)
dedup parent (Ch52 §76.3) → context สะอาด (Ch75)
→ ARRA: ค้นแม่นระดับ chunk + ป้อน context ระดับ doc = RAG คุณภาพ (Ch75)
```
- **community**: "ค้นเจอประโยคเดียว แต่อยากอ่านทั้งย่อหน้า" → small-to-big (ค้น precise, แสดง/ป้อน context ครบ)

---

## สรุป Ch76
```
tension: chunk เล็ก=ค้นแม่น(Ch12) แต่ context ขาด · ใหญ่=context ครบ แต่ embed เจือจาง(Ch43)
⭐ small-to-big (parent-child): index child เล็ก (ค้น) → lookup parent ใหญ่ (context) → ได้ทั้งคู่
variants: sentence-window / parent-doc / summary-index / hypothetical-Q
⚠️ merge overlapping parents: child หลายตัว→parent เดียว → dedup (Ch52) ประหยัด context (Ch75)
ปลดล็อก chunk size (Ch12): child เล็กสุด semantic สมบูรณ์ + parent = ขอบเขต context ธรรมชาติ
trade: index child เยอะ (Ch70 storage) + parent relation · คุ้มกับ doc ยาว/มีโครงสร้าง
ARRA: chunk+metadata (Ch51) มี relation อยู่แล้ว → small-to-big ได้ (ค้น chunk→ป้อน doc)
```
**ถัดไป Ch77:** hierarchical/recursive retrieval — ค้นหลายชั้น (doc→section→chunk), tree traversal, RAPTOR (cluster+summarize tree), เมื่อ corpus มีโครงสร้างลึก
---
*grounded: small-to-big/parent-child · sentence-window · summary-index · dedup (Ch52) · เชื่อม Ch4/12/26/43/51/70/75 · /loop deep iter 2026-07-16*
