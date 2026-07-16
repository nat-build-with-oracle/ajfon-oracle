# Deep Technical · Chapter 71 — Multi-Modal Retrieval Ops

> ต่อจาก Ch70 · Ch38 = ทฤษฎี cross-modal (CLIP) · บทนี้ลง **production**: เก็บ/ค้น image+text+audio ร่วมกันในระบบจริง, ปัญหาที่เจอ

---

## 71.0 ปัญหา — หลาย modality ในระบบเดียว

```
second brain จริง: โน้ต (text) + สกรีนช็อต (image) + ไฟล์เสียง (audio) + PDF (text+image)
→ อยากค้น "รูปที่มีกราฟ vector search" ด้วย text query → ต้อง cross-modal
→ เก็บ/ค้น embedding หลายชนิดร่วมกันยังไง
```

---

## 71.1 ⭐ shared vs separate embedding space

```
shared space (CLIP-style, Ch38):
  text encoder + image encoder → space เดียวกัน → cos(text_vec, image_vec) มีความหมาย
  → ค้น image ด้วย text query ตรงๆ (cross-modal)
separate space (แยกโมเดล):
  text embedder (bge-m3) + image embedder (คนละตัว) → space ต่างกัน
  → cos ข้าม modality ไร้ความหมาย (Ch53 §53.0 เหมือนข้ามโมเดล!)
  → ต้องค้นแยก modality แล้ว merge ผล (ไม่ cross-modal ตรง)
```
- **เลือก**: cross-modal ตรง → ต้อง shared space (CLIP) · ARRA (bge-m3 text) → text-only space

---

## 71.2 modality tag + routing

```
เก็บ: { id, vector, modality:"text"|"image"|"audio", space:"clip"|"bge-m3", ... }
ค้น: query modality → route ไป space ที่ compatible (Ch53 model tag เดียวกัน!)
```
- ต่อยอด Ch53 (model versioning): modality เป็นอีกมิติของ "space compatibility"
- ⚠️ mismatch เงียบ (Ch53 §53.2): ค้น text query ใน image space (dim ตรงบังเอิญ) → มั่ว → validate space tag

---

## 71.3 unified index vs per-modality index

```
unified (shared space): ทุก modality ใน index เดียว (CLIP) → ค้นครั้งเดียวได้ทุก modality
per-modality: index แยกต่อ modality → ค้นแต่ละอัน → merge (RRF Ch11)
```
- shared space → unified (ง่าย, cross-modal ฟรี) · separate → per-modality + merge
- **hybrid modality**: PDF = text + image → chunk แยก modality → เก็บทั้งคู่ (chunk-level modality, Ch12/51)

---

## 71.4 ⚠️ ops ที่ยากขึ้นกับ multi-modal

```
1. preprocessing ต่างกัน: text=tokenize (Ch9) · image=resize/normalize · audio=spectrogram
2. embed cost ต่าง: image/audio embedder หนักกว่า text (Ch70 compute)
3. storage: image vector อาจมิติต่าง (Ch53 dim) → schema รองรับหลาย dim
4. quality eval: cross-modal recall วัดยาก (ต้อง labeled pairs ข้าม modality, Ch39)
```
- multi-modal = pipeline (Ch51) หลายเส้น (ต่อ modality) → orchestrate ซับซ้อนขึ้น

---

## 71.5 audio/video — เพิ่ม temporal

```
audio/video มี "เวลา" → 1 ไฟล์ = หลาย segment (ตาม timestamp)
→ chunk ตามเวลา (Ch12 temporal chunking) → embed แต่ละ segment
→ ค้นเจอ "ช่วงไหนของคลิปพูดเรื่อง X" (segment-level, timestamp metadata)
```
- คล้าย text chunk (Ch12) แต่ boundary = เวลา · metadata เก็บ start/end time (trace กลับ, Ch26)

---

## 71.6 เชื่อม ARRA

```
ARRA ปัจจุบัน: text-centric (bge-m3, Ch4) → โน้ต/เอกสาร text เป็นหลัก
image/PDF: extract text (OCR/caption) → embed เป็น text (Ch51 parse) — practical วันนี้
future cross-modal: เพิ่ม CLIP-space index (Ch38) → ค้นรูปด้วย text ตรง
  → modality tag + separate index (§71.2/3) → merge กับ text (RRF Ch11)
→ เริ่มจาก text (ครอบ 90% second brain) → เพิ่ม modal เมื่อจำเป็น (scale-appropriate)
```
- **community**: "ค้นรูป/เสียงได้ไหม" → วันนี้ผ่าน text (OCR/transcript) · cross-modal ตรง = roadmap (CLIP index เพิ่ม)

---

## สรุป Ch71
```
multi-modal: text+image+audio ในระบบเดียว → ต้องจัดการ space compatibility
⭐ shared space (CLIP Ch38): cross-modal ตรง (cos text↔image มีความหมาย) vs separate: ค้นแยก+merge
modality tag + routing (ต่อยอด Ch53 space compatibility) · ⚠️ mismatch เงียบ → validate space
unified index (shared) vs per-modality+RRF (separate) · PDF=text+image chunk แยก modality
⚠️ ops ยาก: preprocess ต่าง, embed cost ต่าง (Ch70), หลาย dim, eval cross-modal ยาก
audio/video: temporal chunk (segment+timestamp, Ch12/26)
ARRA: text-centric วันนี้ (image/PDF→OCR→text) · cross-modal CLIP=roadmap (scale-appropriate)
```
**ถัดไป Ch72:** vector search testing/QA — unit test retrieval, golden set regression, property-based test, ทำไม test retrieval ต่างจาก test โค้ดปกติ
---
*grounded: CLIP shared space (Ch38) · modality routing (Ch53) · temporal chunking (Ch12) · OCR/caption practical · เชื่อม Ch4/9/11/12/26/38/51/53/70 · /loop deep iter 2026-07-16*
