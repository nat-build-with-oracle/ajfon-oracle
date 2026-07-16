# บทที่ 13 — ก้าวสู่ Production: LanceDB

> เปิดภาค 5 · notebook `ch13_lancedb_second_brain.ipynb` (execute ✅)

ChromaDB สอนเราครบทุกแนวคิด (บท 1–12) · ตอนนี้ port ไป **LanceDB** — DB ที่ ARRA ใช้จริง
แนวคิดเดิม **ติดตัวมาหมด** เปลี่ยนแค่ API + ได้ของแถมที่ Chroma ไม่มี

## 13.1 เปิด second brain — embedded เหมือนเดิม
```python
db = lancedb.connect('./lance_brain')        # โฟลเดอร์ในเครื่อง ไม่มี server
tbl = db.create_table('second_brain', data=[{'id':.., 'text':.., 'vector':..}, ...])
```

## 13.2 ค้น — ระบุ cosine ชัด (ตรงกับ ARRA lancedb.ts)
```python
tbl.search(qv).distance_type('cosine').limit(2).to_pandas()
```
บทที่ 9 เจอกับดัก "Chroma default = L2" · LanceDB ก็ต้องระบุ `distance_type('cosine')` เอง — **อย่าเชื่อ default เรื่อง metric** (กฎเดิม)

## 13.3 filter — SQL where แทน dict
```python
tbl.search(qv).where("folder = 'teaching'").limit(5)
```
บทที่ 3 ใช้ `where={...}` dict ของ Chroma · LanceDB ใช้ **SQL string** — power เต็ม (`>`, `IN`, `AND`, `LIKE`)

## 13.4 ผลรัน (self-check ✅)
ค้น "นัดหมายกับใครบ้าง" → เจอโน้ตประชุม · filter teaching ไม่รั่ว — **แนวคิดบท 1–3 ทำงานบน LanceDB ทันที**

## 13.5 ต่างจาก Chroma ตรงไหน
| | Chroma (สอน) | LanceDB (production) |
|---|---|---|
| keyword/FTS | เขียน BM25 เอง (บท 7) | **native** → บท 14 |
| versioning | ✗ | **time-travel** → บท 15 |
| runtime | Python-first | Rust core (ฝัง Bun/TS = ARRA) |

*Notebook: `ch13_lancedb_second_brain.ipynb` · ลึกกว่า: deep-technical Ch45/64*
