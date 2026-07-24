# Workshop Prep Pack — วันซ้อม/วันจริง

**สำหรับ อ.นัท · ARRA Oracle Second Brain workshop · อาทิตย์ 26 ก.ค. 09:00–12:00**

รวมทุกอย่างที่ต้องมีติดตัวตอนสอน — demo papers จริง, run-of-show ที่เลือกใช้,
คำตอบ Q&A, และ checklist สุดท้าย ทุกอย่างมาจากของจริง ไม่ใช่ตัวอย่างสมมติ

---

## ⚠️ แก้ให้ตรง: demo ใช้ corpus ไหนกันแน่

ก่อนหน้านี้ runsheet บอกว่า demo ใช้ "บ๊องแบ๊ง 12 + Orz 17 papers" — **ไม่ถูกทั้งหมด**
พอขุดลึกเจอว่ามี 2 คนละชุด:

- **corpus จริงสำหรับ demo = literature review วิทยานิพนธ์ DustBoy เอง = 52 papers**
  (Q1 54%, 6 หมวด: sensor calibration 18 / satellite 14 / Thailand burning 13 /
  health 7 / fusion 4 / QA 5) — **นี่คือของจริงที่ใช้สอน** เพราะเป็นงาน PhD ที่ อ.นัท/DustBoy
  ทำเองจริง มี R²/RMSE จริง มี research gap จริง
- บ๊องแบ๊ง-12 / Orz-17 = vector-DB ที่ fleet ทำเป็น **แบบฝึกหัด** เดือน มิ.ย. — เป็นภาพประกอบใน
  slide ได้ แต่ไม่ใช่ corpus หลักที่ demo สด

**สรุป: สอนจากคอร์ปัส 52 paper ของวิทยานิพนธ์จริง** ตรงกับที่ อ.นัท ย้ำ — ใช้ความเชี่ยวชาญจริง
ไม่ใช่หยิบ paper ที่ไม่คุ้นมามั่ว

---

## Demo papers — หยิบใบไหนขึ้นจอ (เตรียมไฟล์ให้พร้อม)

**ตัวหลัก (ใช้ทุก demo):** `Barkjohn et al. (2021) — US-wide PurpleAir Correction`
- Journal: Atmospheric Measurement Techniques (Q1, IF ~4.0)
- Key: raw PurpleAir สูงเกิน ~40%; correction ลด RMSE 8→3 µg/m³
- Thesis relevance: gold standard — DustBoy R²=0.909 ดีกว่า uncorrected
- ทำไมเลือกใบนี้: เป็น paper อ้างอิงที่ทุกคนในวงการรู้จัก + มีเลขชัด + ผูกกับงานเราตรงๆ

**ตัวสำรอง/เปรียบเทียบ (ถ้าอยากโชว์ความหลากหลาย):**
- `Dejchanchaiwong et al. (2023) — Seasonal Calibration in Thailand` — เคสไทย, ผูก burning season
- `Samae et al. (2025) — DustBoy Precision and Accuracy` — งานของทีมเราเอง (RMSE 3.0–3.1)
- `npj (2024) — ML for Large Networks, India` — ตัวที่ R²=0.999 (ตัวเดียวที่ "แพ้") ใช้เล่า gap ได้ดี

**Research gap ที่โชว์สด (มีของจริง):** §2.7.3 *"satellite–ground sensor network comparison"* —
ยังไม่มีใครเทียบดาวเทียม GEMS กับเครือข่าย low-cost 600+ ตัว → gap นี้กลายเป็น method บทหนึ่ง

**Asset จริงหยิบมาโชว์ได้ (อยู่ใน DustBoy repo, ไม่ต้องสร้างใหม่):**
- `ψ/writing/LITERATURE_REVIEW_PAPERS.md` — 52 การ์ด paper จริง + ตารางเทียบ DustBoy vs โลก
- Deck A (`lit-review-vector-search.html`) — t-SNE/similarity/network/PCA จริง
- timeline artifact — topic embedding map (งานกับ อ.ฝน)

---

## Run-of-show ที่เลือกใช้ (DustBoy's hands-on version)

มี run-of-show 2 เวอร์ชัน — **ใช้ของ DustBoy** เพราะ hands-on กว่า ("ดู→ทำ→คุย" ทุก block)
ไม่ให้ผู้เรียนนั่งฟังยาว เหมาะกับกลุ่มไม่ใช่ dev มากกว่า version แรกที่ merge จาก Hermes draft

| เวลา | นาที | Block | รูปแบบ |
|---|---|---|---|
| 09:00 | 15 | 0 · เปิด + ปัญหาที่ทุกคนเจอ | บรรยาย + poll |
| 09:15 | 30 | 1 · Second brain คืออะไร + set up | บรรยาย + ทำตาม |
| 09:45 | 35 | 2 · Paper → สรุป → Tag → Memory | demo (Barkjohn) + hands-on |
| 10:20 | 10 | ☕ พัก | — |
| 10:30 | 35 | 3 · ดึงกลับมา → หา Research Gap | demo + hands-on (ขายของสุด) |
| 11:05 | 30 | 4 · Research → Writing → Review agent loop | demo + hands-on |
| 11:35 | 15 | 5 · ต่อยอด + เริ่มยังไงพรุ่งนี้ | บรรยาย |
| 11:50 | 10 | 6 · Q&A | ถาม-ตอบ |

**จุดพีคของแต่ละ block:**
- Block 0: poll "paper ที่โหลดมายังไม่อ่าน กี่ไฟล์?" → เรียกเสียงหัวเราะ + สร้าง pain
- Block 2: โยน PDF Barkjohn 1 ไฟล์ → agent คืนการ์ด (Journal tier + findings + relevance) → เขียนเข้า memory สด
- Block 3: ถามภาษาคน *"paper ไหนพูดเรื่อง correction ตอน burning season"* → semantic recall + สร้างตารางเทียบ R²=0.909 vs 10 งานโลกสดๆ
- Block 4: เคสจริง 19 มิ.ย. — review agent จับ R²=0.86 ที่มี **leakage** → เลขจริง 0.70 ก่อนขึ้นสอบ (จุดสอน: ต้องมี agent ที่เถียงกับเราได้)

**แผนสำรอง (สำคัญมากสำหรับ 3 ชม.):**
- hands-on ช้า/คนติดตั้งไม่ทัน → มีการ์ด + paper สำเร็จรูปให้ทำตามเลย
- เหลือเวลา → ลงลึก topic embedding map (t-SNE 50 concepts ทำยังไง)
- เวลาน้อย → Block 4 ตัดเหลือ demo อย่างเดียว (ยืดหยุ่นสุด)

---

## Q&A — คำถามฮิตที่ต้องเตรียมคำตอบ

| คำถาม | คำตอบสั้น |
|---|---|
| ต้องจ่ายเงินไหม? | มี ChatGPT Plus / Claude Pro อย่างน้อย 1 อัน (workshop ฟรี) |
| ใช้กับ paper ภาษาไทยได้ไหม? | ได้ — bge-m3 เป็น multilingual, ถามไทยค้น paper อังกฤษได้ (มีสไลด์โชว์) |
| ข้อมูลรั่วไหม? | memory อยู่เครื่องเรา/บัญชีเรา — **แต่ตอน demo สดห้ามเปิด memory จริงที่มีข้อมูลส่วนตัว** |
| เริ่มจากศูนย์ใช้เวลานานไหม? | ก้าวแรก = paper ต่อไปที่อ่าน ย่อเป็นการ์ดโครงเดียว ติด relevance เก็บ แค่นั้น |

---

## 3 ข้อความกลับบ้าน (ปิดท้าย Block 5)

1. **ไม่ต้องเป็น dev** — ทุกอย่างคือ "คุยกับ agent + เก็บโครงให้ดี" ไม่ใช่เขียนโค้ด
2. second brain ไม่ใช่ที่เก็บของ — มันคือ **ความรู้ที่ทำงานต่อได้** (หา gap, เขียน, ตรวจ)
3. เริ่มเล็ก: paper ต่อไปที่อ่าน → ย่อเป็นการ์ดโครงเดียว ติด relevance แล้วเก็บ

---

## Checklist สุดท้าย — เฉพาะ อ.นัท ทำเอง

- [x] เลือก demo paper แล้ว → **Barkjohn 2021** (หลัก) + 3 ตัวสำรอง — เตรียมไฟล์ PDF ให้พร้อมหยิบ
- [ ] เตรียม **PDF Barkjohn 2021** ไว้บน desktop พร้อมลากเข้า agent
- [ ] สร้าง Hermes/agent demo session **ใหม่เอี่ยม** — ห้ามเปิด memory จริงหน้ากล้อง
- [ ] เตรียมการ์ด + paper สำเร็จรูป (แผนสำรองกรณี hands-on ช้า)
- [ ] ทดสอบสลับ 2 deck tab + Zoom screen-share
- [ ] คำพูดปิดเรื่องบริจาคโรงพยาบาล (บัญชีใน WORKSHOP-TIMELINE.md)
- [ ] ซ้อมจับเวลา 1 รอบ — เช็คว่า 3 ชม. พอดี (Block 4 คือตัวตัดได้ถ้าเกิน)

---

## แหล่งข้อมูลเต็ม

- `WORKSHOP-RUNSHEET.md` — runsheet เวอร์ชัน merge-Hermes (ยังใช้อ้างอิง slide-mapping ได้)
- `WORKSHOP-TIMELINE.md` + `WORKSHOP-REPORT.md` — ที่มา + logistics + บัญชีบริจาค
- DustBoy repo `ψ/writing/2026-07-26_workshop-content_*.md` — เนื้อหาต้นฉบับฉบับเต็ม (ที่ prep pack นี้สรุปมา)
