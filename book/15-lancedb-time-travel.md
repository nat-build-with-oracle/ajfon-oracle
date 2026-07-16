# บทที่ 15 (บทส่งท้าย Production) — Time-Travel: ฟีเจอร์ที่ Chroma ไม่มี

> notebook `ch15_lancedb_time_travel.ipynb` (execute ✅)

LanceDB เก็บ **ทุก version ของข้อมูล** (Lance columnar) → ย้อนเวลาได้
สำคัญกับ second brain: undo การลบผิด · audit "ตอนนั้นรู้อะไร" · reproduce งานวิจัยเก่า

## 15.1 ทุกการแก้ = version ใหม่
```python
tbl.add([...])          # v2
tbl.delete("id='n1'")   # v3 (สมมติลบผิด!)
tbl.list_versions()     # เห็น history ครบ
```

## 15.2 ⭐ ย้อนดู + กู้คืน (undo จริง)
```python
tbl.checkout(v['version'])   # ดู version เก่า
tbl.restore()                # ทำ version นั้นเป็น latest = กู้ข้อมูลที่ลบผิด
```

## 15.3 ผลรัน (self-check ✅)
ลบ n1 ผิด → latest เหลือ n2,n3 → `checkout(v2) + restore()` → **n1 กลับมา** 🎉

## 15.4 ทำไม production เลือกสิ่งนี้
Chroma ลบแล้วหายเลย · LanceDB ย้อนได้ = ปลอดภัยกว่าสำหรับความรู้ที่ทำซ้ำไม่ได้
(deep-technical Ch45 versioning, Ch64 MVCC/WAL)

## 🎓 สรุปภาค Production
เรียนบน Chroma (ง่าย เห็นทุกกลไก บท 1–12) → ย้าย LanceDB ได้ทันที เพราะแนวคิดเดียวกัน
+ ได้ native hybrid (บท 14) + time-travel (บท 15) ของแถมระดับ production

*Notebook: `ch15_lancedb_time_travel.ipynb` · ลึกกว่า: deep-technical Ch45/64*
