---
name: slide-deck-qa
description: >
  ตรวจ quality ของ HTML slide deck (presentation) — serve ผ่าน http (แก้ปัญหา file://),
  snapshot ทุกสไลด์ที่ projector res (1920×1080) ด้วย playwright แล้วตรวจ 4 อย่างต่อสไลด์:
  WCAG contrast, overflow (เนื้อหาล้นจอโดนตัด), broken image / 404, + รูป snapshot ให้ดูด้วยตา.
  Use when: "ตรวจสไลด์", "deck qa", "presentation qa", "slide deck audit", "snapshot ทุกสไลด์",
  "preview deck ยังไง", "สไลด์ล้นจอ/รูป 404", หรือก่อนขึ้นเวที present. คู่กับ notebook-qa (อันนั้น Jupyter,
  อันนี้ slide deck). ไม่ใช่สำหรับ design mockup (ใช้ artifact-design) หรือรีวิวเนื้อหา/pedagogy (ใช้ /workflows review).
metadata:
  type: reference
---

# slide-deck-qa — ตรวจ HTML slide deck ก่อนขึ้นเวที

> 2 ชั้น: **visual audit** (สคริปต์นี้ — contrast/overflow/404 ต่อสไลด์) + **content review** (workflow 4 lens ด้านล่าง)

## ทำไมต้อง serve ผ่าน http (ไม่ใช่ file://)
เปิด deck ผ่าน `file://` เจอปัญหา: (1) hash-navigation warning (สไลด์ที่ใช้ `location.hash`),
(2) รูป/asset relative path **404**, (3) fetch/บาง API ถูก block. → serve ผ่าน http แก้หมด.

## Preview เร็ว
```bash
python3 -m http.server 8080 --directory <โฟลเดอร์ deck>
# เปิด http://localhost:8080/deck.html
```
**ทำ deck ให้ portable (แนะนำ):** ฝังรูปเป็น `data:` URI (base64) → ไฟล์เดียวจบ ไม่มี 404 ทั้ง file:// และตอนแชร์.
รูปที่ยัง 404 = ยังไม่ save เข้า `img/` → ฝัง data-URI หรือ save ไฟล์ให้ครบก่อน present.

## Visual audit (snapshot ทุกสไลด์ + ตรวจ 4 อย่าง)
```bash
pip install playwright && python -m playwright install chromium   # ครั้งเดียว
python ~/.claude/skills/slide-deck-qa/scripts/deck_audit.py <deck.html | http://...> [--slides N] [--key ArrowRight]
```
- start http server ให้เอง (ถ้าให้ path), ขับ keyboard nav ทีละสไลด์, snapshot ที่ **1920×1080 (projector res)**
- ต่อสไลด์: WCAG contrast (ทุก text จริง) · overflow (เนื้อหาล้นจอ = โดนตัดตอน present) · broken `<img>` + network 404
- ผล: `deck-shots/slide_NN.png` (ดูด้วยตา) + `deck-shots/deck_report.json`
- ปรับ nav key/selector: `--key Space` หรือ `PWDECK_SEL='.reveal .slides section'` (reveal.js), default `.slide` + `ArrowRight`

**เปิดรูป `deck-shots/slide_*.png` ดูจริงเสมอ** — audit เช็คสี/overflow/404 แต่ไม่เช็ค layout สวย/ตัวชนกัน.

## Content review (เนื้อหา/การสอน/เสียง/ความถูกต้อง) — ใช้ /workflows
สไลด์ที่ผ่าน visual แล้ว ยังต้องรีวิว "เนื้อหา" — รัน multi-agent review 4 lens อิสระ:
- **design** (typography/ความหนาแน่น/hierarchy) · **pedagogy** (arc/อธิบาย jargon ก่อนใช้)
- **thai voice** (อ่านลื่น/สรรพนามคงเส้น) · **accuracy** (ตัวเลข/ข้ออ้าง ตรงแหล่งจริงไหม)
→ synthesize เป็น fix list เรียง impact. (pattern นี้จับ "สไลด์ mental-model ที่ขาด", "jargon ไม่อธิบาย",
"ตัวเลข framing ไม่ขนาน" ที่ visual audit มองไม่เห็น)

## workflow ครบชุด ก่อนขึ้นเวที
1. serve http + เปิดดูเอง (นำทางจริง)
2. `deck_audit.py` → แก้ contrast/overflow/404 จน 0
3. /workflows 4-lens content review → apply fix
4. ซ้อมจริงบน projector res
