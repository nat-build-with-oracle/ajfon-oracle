# บทที่ 9 — RAG: ให้ AI ตอบจากโน้ตของเรา (พร้อมอ้างอิง)

> notebook `ch09_rag_cite.ipynb` — RAG ครบวงจร รวมถึงสิ่งที่สำคัญที่สุด: รู้จักบอก "ไม่พบ"

---

## 9.1 RAG ใน 1 บรรทัด

**Retrieve** โน้ตที่เกี่ยว → ประกอบ context พร้อมแหล่ง → **Generate**: LLM เรียบเรียงตอบ + cite

LLM ไม่ต้องจำความรู้ของเรา — โน้ตคือความจริง LLM คือผู้เรียบเรียง (deep-technical Ch42: memory > parameters)

## 9.2 กติกา 2 ข้อที่มือใหม่พลาด

**ข้อ 1 — threshold**: ANN คืน top-k *เสมอ* แม้ไม่มีอะไรเกี่ยว (สไลด์แผนที่คำ: "ใกล้สุดในบรรดาที่มี")
→ score ต่ำกว่าเกณฑ์ต้อง**ไม่ป้อน LLM** ไม่งั้น LLM ตอบมั่วจากขยะ

**ข้อ 2 — แนบ source ทุกชิ้น**: `[workshop-plan.md] แผน workshop วันที่ 26...`
→ LLM cite ตามได้ → คนตรวจย้อนได้ → เชื่อถือได้

## 9.3 ⚠️ กับดักจริงที่เจอตอนเขียน notebook (บันทึกไว้เพราะทุกคนจะเจอ)

**Chroma default วัดระยะแบบ L2 ไม่ใช่ cosine!** — ตอนใช้ embedding function ของเราเอง
คะแนน `1-distance` ที่ได้คือ 1−L2² (เพี้ยนไปทั้งสเกล: 0.57 จริงแสดงเป็น 0.13)
→ ต้องระบุเองตอนสร้าง collection:

```python
col = client.create_collection('rag_vault', embedding_function=BgeM3(),
                               metadata={'hnsw:space': 'cosine'})
```

ARRA production ก็ระบุชัดแบบเดียวกัน: `.distanceType('cosine')` ใน lancedb.ts
— **อย่าเชื่อ default เรื่อง distance metric** ตรวจเสมอ

## 9.4 ผลรันจริง

```
Q: workshop วันไหน แล้วต้องเตรียมอะไรบ้าง
🤖 Workshop วันที่ 26 กรกฎาคม (workshop-plan.md) และต้องเตรียมอุปกรณ์คือ
   โน้ตบุ๊กติดตั้ง Python และ Jupyter ล่วงหน้า พร้อม... (workshop-plan.md)

Q: ราคาหุ้นวันนี้เป็นยังไง
🤖 ไม่พบข้อมูลเรื่องนี้ใน vault ครับ
   (retrieval คืน 0 ชิ้นหลัง threshold — ไม่ป้อน LLM เลย)
```

- คำตอบแรก: ข้อเท็จจริงถูก + **cite ไฟล์จริง** — verify ได้
- คำตอบสอง: **abstain** — ระบบที่ยอมบอก "ไม่รู้" น่าเชื่อกว่าระบบที่ตอบทุกอย่าง

## 9.5 prompt ที่ใช้ (สั้นแต่ครบ)

```
ตอบคำถามจากบันทึกด้านล่างเท่านั้น ห้ามเดาข้อมูลนอกบันทึก
อ้างอิงชื่อไฟล์ในวงเล็บท้ายประโยคที่ใช้ข้อมูลนั้น เช่น (workshop-plan.md)
ถ้าบันทึกไม่มีคำตอบ ให้บอกว่าไม่พบข้อมูล
```

สามบรรทัด สามหน้าที่: ground (ห้ามเดา) · cite (อ้างไฟล์) · abstain (ยอมรับว่าไม่มี)

## 9.6 เชื่อม ARRA + Claude

ในระบบจริง Claude Code ทำหน้าที่ generate + ตัดสินใจ (จะค้นไหม ค้นกี่รอบ) เอง
ส่วน ARRA คือ retrieve ที่แม่น+เร็ว+แนบ provenance — แบ่งหน้าที่เดียวกับ notebook นี้เป๊ะ
(deep-technical Ch75/80/81: context assembly, adaptive retrieval, abstention)

---

### สรุปบทที่ 9
- RAG = retrieve (threshold + source) → generate (ground + cite + abstain)
- ⚠️ Chroma default = L2 — ระบุ `hnsw:space: cosine` เสมอ (ARRA: distanceType('cosine'))
- พิสูจน์แล้ว: ตอบพร้อม cite ไฟล์จริง + บอก "ไม่พบ" เมื่อถามนอก vault
- prompt 3 บรรทัด: ห้ามเดา · อ้างไฟล์ · ยอมรับว่าไม่มี

*Notebook: `ch09_rag_cite.ipynb` (execute ✅ 4 asserts) · ลึกกว่า: deep-technical Ch42/75/80/81*
