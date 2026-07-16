# Deep Technical · Chapter 38 — Cross-Modal Retrieval

> ต่อจาก Ch37 · paper มีไม่ใช่แค่ text — มี figure, chart, ตาราง, สมการ · ค้นด้วยข้อความ→เจอรูป ได้ไหม? · บทนี้: multimodal

---

## 38.0 ปัญหา: text embedding เห็นแค่ text

bge-m3 (Ch2/7) = text-only · figure/chart ใน paper (Ch26 §26.6 บอกว่ามี insight เข้มข้น) → text embedder เห็นแค่ caption ไม่เห็นรูป · query "กราฟที่ HbA1c ลดตามเวลา" → หา figure จริงไม่ได้ถ้าไม่มี caption ตรง

---

## 38.1 ⭐ CLIP — text + image ในปริภูมิเดียว

CLIP: 2 encoder (image, text) เทรนให้ **รูปกับ caption ที่ตรงกัน → เวกเตอร์ใกล้กัน** (contrastive, Ch2!)
```
image_encoder(รูป) → v_img ∈ ℝⁿ
text_encoder(ข้อความ) → v_txt ∈ ℝⁿ    (ปริภูมิเดียวกัน!)
เทรน: cos(v_img, v_txt_ตรงกัน) สูง, ไม่ตรง ต่ำ  (InfoNCE ข้าม modality)
```
→ query text → embed → cosine กับ image vectors → **ค้นรูปด้วยข้อความ** (เหมือน Ch19 multilingual แต่ข้าม modality แทนภาษา)

---

## 38.2 คณิต — เหมือน cross-lingual (Ch19)

```
align: embed_text("กราฟ HbA1c ลดลง") ≈ embed_image(รูปกราฟนั้น)
cos(v_txt_query, v_img_doc) สูง = รูปตรงกับคำค้น
```
- แนวคิดเดียวกับ Ch19 (shared space) — CLIP align รูป↔ข้อความ, bge-m3 align ไทย↔อังกฤษ · **ทั้งคู่ = contrastive alignment ข้าม domain**
- InfoNCE (Ch2 §2.5) เป็น engine เดียวกัน แค่เปลี่ยน positive pair (รูป,caption แทน query,doc)

---

## 38.3 Multimodal สำหรับงานวิจัย (use-case)

```
ingest paper (Ch26):
  - text chunks → bge-m3 (Ch2)
  - figures/charts → CLIP image encoder → v_img
  - เก็บทั้งคู่ใน index (mixed modality)
ค้น: "กราฟแสดงผลการทดลอง glucose" 
  → embed text → เจอทั้ง text chunk (bge-m3) และ figure (CLIP)
```
- **cite figure**: "ดู Figure 3 [paper, p.5]" → provenance (Ch26 §26.4) ครอบคลุมรูปด้วย
- ตาราง/สมการ: OCR/LaTeX → text · หรือ table-specific encoder

---

## 38.4 ปัญหา: 2 ปริภูมิรวมกันยังไง

CLIP space ≠ bge-m3 space (คนละโมเดล, คนละมิติ) → **รวม index ไม่ได้ตรงๆ**:
```
option A: แยก index (text: bge-m3, image: CLIP) → ค้นทั้งคู่ → RRF fuse (Ch11!)
option B: unified multimodal embedder (เช่น model ที่ embed ทั้ง text+image ในปริภูมิเดียว)
```
- option A = pragmatic (RRF รวม, Ch11) · เหมือน hybrid FTS+vector แต่เป็น text+image
- CLIP text encoder อ่อนกว่า bge-m3 สำหรับ text ล้วน → ใช้ CLIP เฉพาะ image leg

---

## 38.5 ARRA context

- ARRA ปัจจุบัน = text-only (bge-m3) · figure ใน paper → embed caption เท่านั้น (Ch26)
- **โอกาสต่อยอด**: เพิ่ม CLIP image leg → ค้น figure/chart · เป็น adapter อีกตัว (Ch4 pattern) → RRF รวม (Ch11)
- workshop: text-only พอ (นักวิจัยค้นโน้ต/paper เป็นข้อความหลัก) · multimodal = advanced

---

## 38.6 beyond CLIP

- **ColPali/ColBERT-image**: late interaction (Ch7 §7.3) บน image patches → ค้น document รูป (สแกน PDF) โดยไม่ต้อง OCR
- **multimodal LLM embedding**: embed ทั้งหน้า paper (text+figure+layout) เป็นเวกเตอร์เดียว → แก้ปัญหา PDF extraction (Ch26 §26.1)!
- ทิศทางอนาคต: retrieval ที่ "เห็น" เอกสารเหมือนคนอ่าน

---

## สรุป Ch38
```
text embedder เห็นแค่ text → figure/chart หาไม่ได้ (ถ้า caption ไม่ตรง)
CLIP: image+text encoder เทรน contrastive → รูปตรง caption = เวกเตอร์ใกล้ (=Ch19 ข้าม modality)
คณิต = InfoNCE เดียวกัน (positive = รูป,caption)
รวม 2 ปริภูมิ: แยก index + RRF fuse (Ch11) หรือ unified multimodal
ColPali/mLLM embed = ค้นเอกสารรูปโดยไม่ OCR (แก้ Ch26 extraction)
ARRA text-only → CLIP leg = โอกาสต่อยอด (adapter + RRF)
```
**ถัดไป Ch39:** evaluation datasets — BEIR/MTEB, การ eval embedder อย่างเป็นมาตรฐาน, Thai/multilingual benchmark
---
*grounded: CLIP (Radford 2021) · ColPali (2024) · เชื่อม Ch2 (InfoNCE), Ch19 (alignment), Ch11 (RRF fuse), Ch26 (paper figures), Ch4 (adapter) · /loop deep iter 2026-07-14*
