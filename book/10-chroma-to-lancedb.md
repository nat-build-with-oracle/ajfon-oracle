# บทที่ 10 — เรื่องเล่าจริง: ทำไม ARRA ย้าย ChromaDB → LanceDB

> เปิดภาค 4 (สู่ production) · notebook `ch10_chroma_to_lancedb.ipynb` รันทั้งสองระบบเทียบกันจริง

## 10.1 ประวัติจริงจาก TIMELINE.md ของ ARRA

- **Dec 2025**: ARRA เริ่มด้วย "FTS5 + ChromaDB hybrid" — จุด breakthrough แรก
- **ต่อมา**: ย้าย vector store ไป LanceDB — ไม่ใช่เพราะ Chroma "แย่" แต่เพราะ**บริบทเปลี่ยน**

## 10.2 ผลรันเทียบจริง (corpus 200 chunks เดียวกัน, bge-m3 เดียวกัน)

```
ingest:  Chroma 44 ms · LanceDB 10 ms
query:   Chroma 1.3 ms · LanceDB 2.2 ms
top-1:   ตรงกันเป๊ะ ✓  (สมการเดียวกัน — บทที่ 4)
```

ที่ scale นี้ **ต่างกันไม่มีนัย** — ตัวตัดสินจริงไม่ใช่ความเร็ว

## 10.3 ตัวตัดสินจริง: runtime ของแอป

| | ChromaDB | LanceDB |
|---|---|---|
| runtime | Python-first (ยุคนั้นต้องมี Python sidecar) | Rust core ฝังใน process — JS/TS เรียกตรง |
| storage | ภายใน | Lance columnar + versioned (time-travel) |
| เหมาะกับ | เรียน/prototype Python | ฝังในแอปที่ไม่ใช่ Python |

**ARRA เป็นแอป Bun/TypeScript** → LanceDB ฝังใน runtime ตัวเองได้ ไม่ต้องมี Python sidecar
→ ย้ายเพราะ fit ไม่ใช่เพราะแพ้ benchmark · โปรเจกต์ Python → Chroma คือคำตอบที่ถูกแล้ว

## 10.4 บทเรียนใหญ่ที่สุดของบท

self-check บังคับว่า **top-1 ของสองระบบต้องตรงกัน** — และมันตรงจริง
เพราะทุกอย่างที่เรียนมา (embedding, cosine, hybrid, eval) **ติดตัวคุณ ไม่ติดเครื่องมือ**
DB เปลี่ยนได้เสมอ ความรู้ไม่ต้องเปลี่ยนตาม

*Notebook: `ch10_chroma_to_lancedb.ipynb` (execute ✅) · ลึกกว่า: deep-technical Ch45/64, TIMELINE.md*
