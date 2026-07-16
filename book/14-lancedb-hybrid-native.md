# บทที่ 14 — Hybrid ในตัว: LanceDB ทำ FTS + Vector เครื่องเดียว

> notebook `ch14_lancedb_hybrid_native.ipynb` (execute ✅)

บทที่ 7 เราเขียน BM25 เอง 20 บรรทัด + RRF เอง เพราะ Chroma ไม่มี FTS
**LanceDB มี native** (engine tantivy เขียนด้วย Rust)

## 14.1 สร้าง FTS index — คำสั่งเดียว
```python
from lancedb.index import FTS
tbl.create_index('text', config=FTS())      # แทน BM25 20 บรรทัดในบทที่ 7
tbl.search('2740', query_type='fts')          # จับรหัสเป๊ะทันที
```

## 14.2 ⭐ Hybrid — vector + FTS + RRF ในคำสั่งเดียว
```python
from lancedb.rerankers import RRFReranker
tbl.search(query_type='hybrid').vector(qv).text(q).rerank(RRFReranker()).limit(3)
```
RRF ที่เราสร้างเองบทที่ 7 (k=60) → LanceDB รวมให้ในตัว

## 14.3 ผลรัน (self-check ✅)
- FTS ค้น "2740" → เจอ PR #2740 เป๊ะ
- hybrid "PR #2740" → เจอรหัส · hybrid "บอร์ดสำหรับสอน IoT" → เจอ ESP32/ไมโครคอนโทรลเลอร์

## 14.4 บทเรียน
เราเขียน BM25+RRF เองในบทที่ 7 **เพื่อเข้าใจกลไก** · production ใช้ engine ในตัว (เร็ว + scale ระดับล้าน doc)
— เข้าใจก่อน แล้วค่อยใช้ของสำเร็จ = รู้ว่ามันทำอะไรอยู่ข้างใน

*Notebook: `ch14_lancedb_hybrid_native.ipynb` · ลึกกว่า: deep-technical Ch4/11/34/56*
