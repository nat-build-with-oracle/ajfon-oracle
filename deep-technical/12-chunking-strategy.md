# Deep Technical · Chapter 12 — Chunking Strategy

> ต่อจาก Ch11 · เอกสารยาว (paper, บทความ) ยาวเกิน 1 เวกเตอร์จะแทนได้ดี · บทนี้: หั่นยังไงให้ retrieval แม่น

---

## 12.0 ทำไมต้อง chunk (2 เหตุผล)

1. **max token limit** (Ch9 §9.6): bge-m3 = 8192 tokens · paper 20 หน้าเกิน → truncate เสียท้าย
2. **สำคัญกว่า — dilution**: บีบเอกสารยาว (หลายหัวข้อ) เป็น **1 เวกเตอร์** = เฉลี่ยความหมายทั้งหมด → "เจือจาง" · query เจาะจงจะ match ได้แย่ เพราะเวกเตอร์เป็น "ค่ากลาง" ของทุกไอเดีย

> หลักการ: **1 chunk ควร = 1 ความคิด** → เวกเตอร์คมชัด → recall ดี

---

## 12.1 Fixed-size chunking (ง่ายสุด)

หั่นทุก N tokens (เช่น 512) :
```
chunk[i] = tokens[i·N : (i+1)·N]
```
- ✅ ง่าย เร็ว คาดเดาได้
- ❌ ตัดกลางประโยค/กลางความคิด → chunk พังความหมาย ("...ผลการทดลองแสดงว่า" | "เบาหวานลดลง...")

---

## 12.2 Overlap — กัน context หลุดรอยต่อ

หั่นแบบเหลื่อม (เช่น N=512, overlap=64):
```
chunk[0] = tokens[0:512]
chunk[1] = tokens[448:960]     ← ซ้ำ 64 tokens กับ chunk[0]
```
- ประโยคที่คร่อมรอยต่อยังอยู่ครบใน chunk ใดchunkหนึ่ง
- แลก: storage เพิ่ม (~overlap/N %) + doc ซ้ำในผลค้น (ต้อง dedup)

---

## 12.3 Semantic / Recursive chunking (ฉลาดกว่า)

หั่นตาม **โครงสร้างความหมาย** ไม่ใช่ตัวเลขดิบ:
```
recursive splitter: ลองหั่นที่ "\n\n" (ย่อหน้า) ก่อน
   ถ้ายังยาวเกิน → หั่นที่ "\n" (บรรทัด)
   ถ้ายัง → หั่นที่ ". " (ประโยค)
   ถ้ายัง → fixed-size
```
- เคารพขอบเขตธรรมชาติ (ย่อหน้า/หัวข้อ) → chunk = หน่วยความคิดจริง
- **semantic chunking ขั้นสูง**: embed ทุกประโยค → ตัดตรงที่ cosine ระหว่างประโยคติดกัน "ตก" (เปลี่ยนหัวข้อ) → ขอบ chunk ตามการเปลี่ยนความหมายจริง (ใช้ Ch1 cosine มาช่วยหั่น!)

---

## 12.4 Chunk size — trade-off พื้นฐาน

| chunk เล็ก (128) | chunk ใหญ่ (1024) |
|---|---|
| เวกเตอร์คม, ระบุตำแหน่งแม่น | บริบทครบ |
| แต่ขาดบริบท (ประโยคเดี่ยวกำกวม) | แต่เจือจาง (หลายไอเดียปนกัน) |
| chunk เยอะ = index ใหญ่ | chunk น้อย = index เล็ก |
| recall เจาะจงดี | recall ภาพรวมดี |

→ ไม่มีคำตอบเดียว · ขึ้นกับ query ทั่วไปเจาะจงแค่ไหน · sweet spot งานวิจัยมักอยู่ **256-512 tokens**

---

## 12.5 Parent-Child / Small-to-Big (best of both)

แก้ trade-off §12.4 ด้วยการ**แยก "หน่วยค้น" กับ "หน่วยส่งให้ LLM"**:
```
ค้นด้วย: child chunk เล็ก (128 tokens) → เวกเตอร์คม → match แม่น
ส่งคืน:  parent chunk ใหญ่ (ย่อหน้า/section ที่ child อยู่) → บริบทครบ
```
- index child (เล็ก, แม่น) แต่ retrieval คืน parent (บริบท) · ได้ทั้ง precision การ match และ context ที่ครบ
- เก็บ mapping child→parent

---

## 12.6 ARRA — memory entry เป็น chunk ธรรมชาติ

ARRA เก็บ memory เป็น **note/entry** (retro, learning, principle, inbox) — แต่ละอันมักเป็น **1 ความคิด/1 บทเรียน อยู่แล้ว** → **ไม่ต้อง chunk มาก** (ต่างจาก RAG ที่ยัด PDF ดิบ)
- 35,164 docs = entries ที่มนุษย์/agent เขียนเป็นหน่วยความหมายไว้แล้ว
- นี่คือข้อได้เปรียบเชิงโครงสร้างของ "second brain แบบ note" เทียบ "RAG แบบ dump PDF": **chunk boundary = ความคิด** โดยธรรมชาติ

**เมื่อไหร่ต้อง chunk ใน ARRA**: ตอน ingest เอกสารภายนอกยาว (paper ที่ผู้เรียนเอามา, Ch4 use-case) → ใช้ recursive/semantic (§12.3) หั่นก่อนเข้า memory

---

## 12.7 เชื่อม pipeline

```
เอกสารยาว → chunk (recursive/semantic, overlap)
          → embed แต่ละ chunk (Ch2)
          → index (Ch3) เก็บ chunk→doc mapping
ค้น: query → top-k chunks → (parent expand §12.5) → RRF/rerank (Ch4)
```

---

## สรุป Ch12
```
chunk เพราะ token limit + dilution (1 vec แทนหลายไอเดีย = เจือจาง)
fixed (ง่าย/ตัดกลาง) → overlap (กันรอยต่อ) → recursive/semantic (ตามโครงสร้าง/cosine)
size trade-off: เล็ก=คม/ขาดบริบท, ใหญ่=บริบท/เจือจาง → sweet 256-512
parent-child: ค้น child เล็ก, คืน parent ใหญ่ = best of both
ARRA: memory entry = chunk ธรรมชาติ (1 note = 1 ความคิด) → ได้เปรียบ RAG-dump
```
**ถัดไป Ch13:** retrieval heat model — usage_count/last_accessed_at ถ่วงน้ำหนักยังไง, recency decay function, และทำไมมันทำให้ ARRA "จำเหมือนสมอง"

---
*grounded: RAG chunking best-practices · recursive/semantic splitting · small-to-big (LlamaIndex) · เชื่อม Ch1 (cosine for semantic split), Ch9 (token limit), Ch4 (memory types) · /loop deep iter 2026-07-13*
