# 🔨 Slide Forge

โยนรูป → ได้ deck สวยในดีไซน์เดียวกับ workshop deck (dark "Proof Terminal")
พร้อม caption ที่ AI ช่วยเขียนให้ได้

## ใช้ยังไง

```bash
python3 tools/slide-forge/forge.py
# เปิด URL ที่ปรินต์ออกมา (เช่น http://127.0.0.1:8770/)
```

1. **โยนรูป** — ลากไฟล์รูปมาวางในกล่องบนหน้าเว็บ (หรือก็อปไฟล์ไปไว้ใน `inbox/` ตรงๆ)
   รับ png / jpg / gif / webp วางทีละหลายไฟล์ได้
2. **ใส่ข้อความ** — แต่ละรูปมี 3 ช่อง: eyebrow (มุมบน) / หัวข้อ (h2) / คำบรรยาย (caption)
   - **ให้ AI ช่วยเขียน**: บอก Claude ว่า *"describe the slide-forge inbox images"* →
     AI เปิดดูรูปแล้วเขียน `captions.json` ให้ทุกใบ (นี่คือส่วน "AI บรรยายภาพ")
   - แก้เองในหน้าเว็บได้ตลอด แล้วกด 💾 บันทึกข้อความ
3. **จัดลำดับ** — ปุ่ม ↑↓ ในแต่ละการ์ด
4. **Build** — กด 🔨 Build deck → ได้ไฟล์ `artifacts/forged-deck.html`
   ดู/present ได้เลย (คีย์ลูกศรเลื่อนสไลด์, กด Z ซูมภาพ, เหมือน deck จริง)

## สถาปัตยกรรม — ใครทำอะไร

- **tool (forge.py)** = จัดเรียง + เรนเดอร์ ให้สวยตรงดีไซน์ system + ฝังรูป base64
  (self-contained ไฟล์เดียว ไม่มี dependency ภายนอก)
- **Claude (AI)** = ส่วน vision จริง — เปิดดูรูปแล้วเขียน caption/หัวข้อ
  (Python stdlib เรียก LLM เองไม่ได้ เลยแยกส่วนนี้ให้ AI ทำ ตรงไปตรงมา)

## ไฟล์

- `forge.py` — engine (stdlib ล้วน ไม่ต้องลงอะไร)
- `inbox/` — รูปที่โยนเข้ามา (gitignored)
- `captions.json` — ข้อความแต่ละสไลด์ (gitignored, AI หรือคนแก้ได้)
- output → `artifacts/forged-deck.html`

น้องของ `tools/deck-reorder/` (จัดลำดับ deck ที่มีอยู่แล้ว) — อันนี้ **สร้าง** deck ใหม่จากรูป
