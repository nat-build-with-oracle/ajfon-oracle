# Deep Technical · Chapter 26 — Ingesting Research Papers (use-case จริง)

> ต่อจาก Ch25 · นี่คือ use-case A ของ workshop (Ch ajfon: "paper → agent สรุป+tag → memory") · บทนี้: pipeline จริงตั้งแต่ PDF ถึง cite กลับ

---

## 26.0 เป้าหมาย pipeline

```
paper.pdf → extract text → chunk → embed → index (+metadata)
   → ค้นเจอด้วยความหมาย → cite กลับหน้า/ย่อหน้าจริง → paper→insight→RQ→writing
```
รวมทุก chapter ก่อนหน้า มาใช้กับ**เอกสารจริงของนักวิจัย**

---

## 26.1 PDF extraction — จุดที่พังบ่อยสุด

PDF ไม่ใช่ text — เป็น layout · ปัญหาจริง:
- **2-column layout**: extractor อ่านข้ามคอลัมน์ → ประโยคพันกัน (ต้อง layout-aware: PyMuPDF/GROBID)
- **ตาราง/สมการ/รูป**: กลายเป็นขยะ (LaTeX/MathML ต้อง handle แยก)
- **header/footer/เลขหน้า**: ปนเข้าเนื้อ → ต้อง strip
- **hyphenation ท้ายบรรทัด**: "diabe-\ntes" → ต้องรวม
- **ไทย**: no-space + PDF encoding เพี้ยน (สระ/วรรณยุกต์หลุด) → ต้อง normalize

→ **garbage in = garbage embedding** · ขั้นนี้สำคัญกว่าที่คิด · GROBID (สำหรับ paper วิชาการ) แยก section/reference ได้ดี

---

## 26.2 Chunking paper (Ch12 applied)

paper มีโครงสร้างชัด → ใช้ **semantic/section-aware** (Ch12 §12.3):
```
chunk ตาม section: Abstract | Intro | Method | Results | Discussion | Refs
  ถ้า section ยาว → recursive (ย่อหน้า → ประโยค)
  overlap เล็ก กันรอยต่อ (Ch12 §12.2)
```
- **1 chunk ควร = 1 finding/claim** (Ch12 §12.0) → query เจาะจง match แม่น
- เก็บ **section label** เป็น metadata → filter ได้ ("ค้นเฉพาะใน Results")
- parent-child (Ch12 §12.5): index ประโยค (child) → คืนย่อหน้า/section (parent) = บริบทครบ

---

## 26.3 Metadata schema (สำหรับ paper)

```json
{
  "id": "paper42-chunk7",
  "document": "ผลการทดลองแสดงว่า...",
  "metadata": {
    "type": "paper",
    "title": "...", "authors": [...], "year": 2024, "doi": "...",
    "section": "Results",
    "page": 5, "chunk_idx": 7,
    "source_file": "papers/smith2024-diabetes.pdf"
  }
}
```
- `page`+`section` = ทำให้ **cite กลับตำแหน่งจริง** (Ch community: provenance สำคัญ)
- `year` → time-travel/asOf filter (Ch ajfon use-case: "พ.ค. เข้าใจ X แค่ไหน")
- filter ก่อน ANN: `year > 2020 AND section = 'Method'`

---

## 26.4 ⭐ Citation-back — จุดขายที่สำคัญสุด (Ch community: citation crisis)

หลังค้นเจอ chunk → คำตอบ**อ้างกลับไฟล์+หน้าจริง**:
```
คำตอบ: "...การรักษาด้วย metformin ลด HbA1c เฉลี่ย 1.5%
        [Smith 2024, Results, p.5 → papers/smith2024-diabetes.pdf]"
```
- ต่างจาก ChatGPT ที่แต่ง citation (Ch3 workshop hook: 1-in-277 fabricated!)
- ARRA: ทุกคำตอบชี้ **chunk จริงที่ verify ได้** เพราะ metadata เก็บ source+page → คลิกเปิดตรวจ
- **นี่คือเหตุผลเชิงเทคนิคที่ "second brain" ปลอดภัยกว่าสำหรับงานวิชาการ** — grounded ในโน้ต/paper จริง ไม่ใช่ generate ลอยๆ

---

## 26.5 paper → insight → RQ → writing (use-case เต็ม)

```
1. ingest papers (§26.1-3) → memory (embed, Ch2 → index, Ch3)
2. ค้นข้าม paper: "gap ระหว่าง method A กับ B" → semantic (Ch4 hybrid)
3. oracle_prism (Ch skill): มอง paper จาก 5 มุม → หา research gap → ปั่น RQ
4. เขียน: draft อ้าง citation จริงจาก memory (§26.4) → kien-thai (ไทยวิชาการ)
5. rrr/forward (Ch skill): session จำ → พรุ่งนี้ต่อได้ (Ch13 heat: paper ที่อ้างบ่อย = ร้อน)
```
= use-case A+B+C ของ ajfon workshop (Ch ajfon timeline) mapped ลงเทคนิคจริง

---

## 26.6 pitfalls เฉพาะ paper

- **citation graph**: paper อ้าง paper → อาจ embed reference list ปนเนื้อ (strip refs หรือ index แยก)
- **figure/table captions**: มักมี insight เข้มข้น → อย่าทิ้ง (index caption แยก)
- **เอกสารเยอะ**: 1 career = พันๆ paper → ยัง Flat/IVF เครื่องเดียวพอ (Ch25 §25.6)
- **สแกน PDF (ภาพ)**: ต้อง OCR ก่อน → ไทย OCR ยัง error → verify

---

## สรุป Ch26
```
pipeline: PDF→extract(layout-aware, ไทย normalize)→chunk(section-aware)→embed→index+metadata
metadata: title/authors/year/section/page → cite-back + asOf filter
citation-back = จุดขายสำคัญสุด: อ้าง chunk จริง (verify ได้) vs ChatGPT แต่ง (1-in-277)
paper→insight→RQ→writing = use-case A/B/C ของ workshop mapped ลงเทคนิค
pitfall: extract คือจุดพัง (garbage in=garbage embed), refs/figures/OCR
```
**ถัดไป Ch27:** security & multi-tenancy — auth, per-oracle isolation, PII handling (เชื่อม artifact-manager privacy), vault encryption
---
*grounded: Ch12 (chunking), Ch2/3 (embed/index), Ch13 (heat), Ch ajfon use-cases A/B/C, Ch community (citation crisis) · GROBID/PyMuPDF · /loop deep iter 2026-07-13*
