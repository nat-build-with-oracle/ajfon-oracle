# บทที่ 3 — ค้นแบบมีเงื่อนไข: semantic + metadata พร้อมกัน

> "หาโน้ตเรื่องการสอน **เฉพาะปีนี้ ที่ไม่ใช่ฉบับร่าง**" — ครึ่งแรกคือความหมาย ครึ่งหลังคือเงื่อนไข

---

## 3.1 คำถามจริงไม่ได้มีแต่ความหมาย

คำค้นในชีวิตจริงมักเป็นลูกผสม:

- "งานวิจัย vector search ~~ทั้งหมด~~ **หลังปี 2023**"
- "โน้ตประชุม **ในโฟลเดอร์งาน** ที่พูดถึง embedding"
- "แผนสอน **ที่ไม่ใช่ draft**"

ส่วนที่เป็น *ความหมาย* ("งานวิจัย vector search") ให้ vector จัดการ
ส่วนที่เป็น *เงื่อนไขเป๊ะๆ* (ปี > 2023, folder = งาน, draft = false) ให้ **metadata filter** จัดการ

## 3.2 metadata — ป้ายกำกับที่ติดตอน upsert

ตั้งแต่บทที่ 1 เราติด metadata ให้ทุกโน้ตอยู่แล้ว:

```python
col.upsert(
    ids=["d1"],
    documents=["แผนสอน vector search สำหรับ workshop เดือนกรกฎาคม"],
    metadatas=[{"folder": "teaching", "year": 2026, "draft": False}],
)
```

metadata เป็นอะไรก็ได้ที่เป็น str / int / float / bool — โฟลเดอร์ ปี แท็ก สถานะ ผู้เขียน

## 3.3 `where` — เงื่อนไขตอน query

```python
col.query(
    query_texts=["การสอนเรื่องค้นหาด้วยความหมาย"],   # ← ความหมาย (vector)
    where={"$and": [                                  # ← เงื่อนไข (metadata)
        {"folder": {"$eq": "teaching"}},
        {"year":   {"$eq": 2026}},
        {"draft":  {"$eq": False}},
    ]},
    n_results=3,
)
```

operator ที่ใช้ได้: `$eq` `$ne` `$gt` `$gte` `$lt` `$lte` `$in` `$nin` และประกอบด้วย `$and` / `$or`

## 3.4 ผลจริง (จาก demo3 — รันพิสูจน์แล้ว)

vault ทดลอง 6 โน้ต: แผนสอนจริง, แผนสอน draft, โน้ต SQL ปี 2025, งานวิจัย, ไอเดียสอน, รายจ่าย

```
1) semantic ล้วน:
   แผนสอน vector search สำหรับ workshop     ← ✓
   แผนสอน vector search ฉบับร่างแรก          ← ปน draft มา
   โน้ตสอน SQL พื้นฐานปีที่แล้ว               ← ปนปีเก่ามา

2) + filter (teaching ∧ 2026 ∧ ¬draft):
   แผนสอน vector search สำหรับ workshop     ← ✓
   บันทึกไอเดียสอน: ใช้เดโมก่อนค่อยลงสมการ    ← ✓ (draft กับปีเก่าหายไปตามสั่ง)
```

semantic หาของ "เกี่ยว" — filter ตัดของ "ไม่เข้าเงื่อนไข" — สองอย่างทำงานพร้อมกันใน query เดียว

## 3.5 โบนัส: filter ด้วยเนื้อหา (`where_document`)

```python
col.query(query_texts=[...], where_document={"$contains": "เดโม"})
```

บังคับว่าผลลัพธ์ต้อง *มีคำนี้จริงๆ* ในเนื้อหา — เป๊ะแบบ Ctrl+F ผสมกับความหมายแบบ vector
(นี่คือรูปแบบอย่างง่ายของ "hybrid search" — เวอร์ชันเต็มรอบทที่ 7)

## 3.6 ⚠️ กับดักที่ควรรู้ก่อนใช้จริง

filter เข้มมาก (เหลือผ่านไม่กี่ %) + ขอ n_results เยอะ → ผลอาจว่างผิดคาด
เบื้องหลังมีเรื่อง "กรองก่อนหรือหลังค้น" (pre vs post filtering) ที่ระบบแต่ละตัวทำไม่เหมือนกัน
— ฉบับลึกอยู่ deep-technical Ch55 · ระดับใช้งาน: **จำไว้ว่า filter เข้ม = ผลน้อยเป็นเรื่องปกติ อย่าตกใจ**

## 3.7 เชื่อมกับของจริง

- ARRA Oracle เก็บ metadata แบบเดียวกันนี้ทุก chunk (source_file, folder, timestamp)
  → คำถามอย่าง "ค้นเฉพาะโน้ตปีนี้ในโฟลเดอร์ X" ตอบได้เพราะโครงนี้
- ยิ่งไปกว่านั้น: ไม่ต้องเขียน `where` เองด้วยซ้ำ — LLM (Claude) แปลงภาษาคน
  "โน้ตสอนปีนี้ที่เสร็จแล้ว" → structured filter ให้อัตโนมัติ (self-querying, deep-technical Ch78)

---

### สรุปบทที่ 3
- คำค้นจริง = ความหมาย (vector) + เงื่อนไข (metadata filter) — ใช้พร้อมกันใน query เดียว
- ติด metadata ตั้งแต่ upsert: folder / year / draft / อะไรก็ได้ str-int-float-bool
- `where` + `$and`/`$or`/`$gt`/... · `where_document` + `$contains` = hybrid อย่างง่าย
- filter เข้ม → ผลน้อยเป็นปกติ (เบื้องหลัง: pre/post filtering, Ch55)

*โค้ด: `book/demo/demo3_filter_metadata.py` (รันพิสูจน์แล้ว) · ลึกกว่า: deep-technical Ch55/61/78*
