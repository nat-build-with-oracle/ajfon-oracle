# Deep Technical · Chapter 9 — Tokenization (ข้อความ → token ก่อนถึงเวกเตอร์)

> ต่อจาก Ch8 · ก่อน embed ต้อง tokenize · บทนี้ลงลึกว่าโมเดลหั่นข้อความยังไง — และทำไม**ภาษาไทยยากเป็นพิเศษ**

---

## 9.1 ปัญหา: vocab ระเบิด

ถ้าใช้ "1 คำ = 1 token": ภาษามีคำนับล้าน + คำใหม่/สะกดผิด/ชื่อเฉพาะไม่จบ → vocab ใหญ่เกิน + เจอคำนอก vocab (OOV) = แทนด้วย `[UNK]` เสียข้อมูล

ถ้าใช้ "1 ตัวอักษร = 1 token": vocab เล็ก แต่ sequence ยาวมาก + โมเดลต้องเรียนประกอบคำเองทั้งหมด (ยาก)

**ทางกลาง = subword**: หั่นเป็นชิ้นที่พบบ่อย · คำเจอบ่อย = 1 token, คำหายาก = หลายชิ้น · vocab ~30k-250k ครอบคลุมทุกข้อความ

---

## 9.2 BPE — Byte-Pair Encoding (algorithm จริง)

**Train** (เรียน vocab):
```
1. เริ่มจาก vocab = ตัวอักษรเดี่ยวทั้งหมด
2. นับคู่ token ติดกันที่พบบ่อยสุดใน corpus
3. merge คู่นั้นเป็น token ใหม่ เพิ่มเข้า vocab
4. ทำซ้ำจนได้ vocab ตามขนาดที่ตั้ง (เช่น 50k merges)
```
ตัวอย่าง: `l o w e r` → เจอ `e r` บ่อย → merge → `l o w er` → เจอ `l o` บ่อย → `lo w er` …

**Encode** (ตอนใช้): apply merge rules ตามลำดับที่เรียนมา · **byte-level BPE** (GPT) ทำงานบน byte ดิบ → ครอบทุกภาษา/emoji ไม่มี OOV เลย

---

## 9.3 SentencePiece / Unigram LM (ที่ bge-m3/XLM-R ใช้)

bge-m3 ต่อยอด **XLM-RoBERTa** → ใช้ **SentencePiece** (unigram language model):
```
- treat ข้อความเป็น raw stream (รวม space เป็นสัญลักษณ์ ▁ )
- เรียน vocab แบบ probabilistic: แต่ละ subword มี prob
- segment = หา sequence ของ subword ที่ maximize likelihood (Viterbi)
```
ต่างจาก BPE: unigram หา segmentation **ที่น่าจะเป็นสุด** (มี prob) ไม่ใช่ greedy merge → รองรับ **subword regularization** (sample หลาย segmentation ตอน train → robust)

**สำคัญ**: SentencePiece **ไม่ต้องพึ่ง space แบ่งคำ** → เหมาะภาษาที่ไม่เว้นวรรค (ไทย จีน ญี่ปุ่น)

---

## 9.4 ⭐ ภาษาไทย — ทำไมยาก

ไทยไม่มี space ระหว่างคำ: `ไปโรงเรียน` = "ไป โรง เรียน" (3 คำ) แต่เขียนติดกัน

**ปัญหา**:
- tokenizer อังกฤษล้วน (พึ่ง space) จะได้ token ไทยแย่ → embedding ไทยห่วย
- ambiguity: `ตากลม` = "ตา กลม" (round eyes) หรือ "ตาก ลม" (air-dry)? — ต้องดูบริบท

**ทำไม bge-m3 (multilingual/SentencePiece) จัดการได้**:
- เรียน subword จาก corpus 100+ ภาษา รวมไทย → มี subword ไทยที่พบบ่อยใน vocab
- ไม่พึ่ง space — segment จาก likelihood
- self-attention (Ch10) ช่วย disambiguate จากบริบท

→ นี่คือเหตุผลเชิงเทคนิคว่าทำไม ARRA **ต้องใช้ multilingual model** ไม่ใช่ English embedder สำหรับ workshop ไทย (สอดกับ Ch2 §2.1)

---

## 9.5 Special tokens

```
[CLS] (หรือ <s>)  — token แทน "ทั้งประโยค" (ใช้ตอน CLS-pooling, Ch2 §2.3)
[SEP] (หรือ </s>) — คั่น/จบ segment
[PAD]             — เติมให้ batch ยาวเท่ากัน (masked ตอน attention)
[UNK]             — คำนอก vocab (byte-BPE ไม่มีปัญหานี้)
```

---

## 9.6 ผลต่อ retrieval — max length & chunking

โมเดลมี **max sequence length** (bge-m3 = 8192 tokens, ยาวกว่า BERT 512 มาก)
- เอกสารยาวเกิน → **truncate** (เสียท้าย) หรือ **chunk** (หั่นเป็นท่อน embed แยก)
- **chunking strategy** กระทบ recall โดยตรง: chunk เล็ก = ระบุตำแหน่งแม่นแต่เสียบริบท · chunk ใหญ่ = บริบทครบแต่ "เจือจาง" (1 เวกเตอร์แทนหลายไอเดีย)
- ARRA เก็บ memory เป็น note/entry (มักสั้น-กลาง) → ไม่ค่อยชน 8192 · แต่ถ้า embed paper ยาว ต้อง chunk (จะลง Ch12)

**token ≠ คำ ≠ character**: 1 token ไทย ≈ 1-3 ตัวอักษร · ประโยคไทย 100 ตัวอักษร ≈ 40-70 tokens → กะ budget token ต้องเผื่อ

---

## สรุป Ch9
```
subword = ทางกลางระหว่างคำ (vocab ระเบิด) กับตัวอักษร (sequence ยาว)
BPE: greedy merge คู่พบบ่อย · SentencePiece unigram: segment แบบ likelihood (ไทยได้)
ไทยไม่มี space → ต้อง multilingual/SentencePiece (bge-m3) ไม่ใช่ English tokenizer
max 8192 tokens · เอกสารยาว → chunk (กระทบ recall)
```
**ถัดไป Ch10:** self-attention internals — Q/K/V, scaled dot-product, multi-head, positional encoding, ทำไม "เบา" ในบริบทต่างได้เวกเตอร์ต่าง

---
*grounded: XLM-RoBERTa/SentencePiece (Kudo 2018) · BPE (Sennrich 2016) · bge-m3 8192 ctx · Thai word segmentation · เชื่อม Ch2 §2.1 · /loop deep iter 2026-07-13*
