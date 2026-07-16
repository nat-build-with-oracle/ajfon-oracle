# Deep Technical · Chapter 33 — Graph & Temporal Memory

> ต่อจาก Ch32 · vector = "ความคล้าย" · แต่ความรู้มี **ความสัมพันธ์** (A causes B) และ **เวลา** (เข้าใจ X เมื่อ พ.ค.) · บทนี้: graph + temporal

---

## 33.0 ข้อจำกัดของ vector ล้วน

vector จับ "คล้าย" แต่ไม่จับ:
- **relation**: "metformin *รักษา* เบาหวาน" — vector รู้ว่า 2 คำใกล้กัน แต่ไม่รู้ "ความสัมพันธ์แบบไหน"
- **multi-hop**: "ยาที่ A แพ้ → ใช้รักษาโรคอะไรได้บ้าง" — ต้องเดินหลายก้าว
- **temporal**: "ตอน พ.ค. เข้าใจเรื่องนี้แค่ไหน" — vector ไม่มีมิติเวลา (Ch ajfon use-case: time-travel)

---

## 33.1 Knowledge Graph construction

```
text → entity extraction → (nodes: metformin, เบาหวาน, HbA1c)
     → relation extraction → (edges: metformin −[รักษา]→ เบาหวาน,
                                      metformin −[ลด]→ HbA1c)
```
- ใช้ LLM/NER แตก triple (subject, relation, object) จากเอกสาร
- เก็บเป็นกราฟ (Neo4j/edge list) · แต่ละ node/edge อาจมี embedding ด้วย (hybrid graph+vector)

---

## 33.2 Graph retrieval — multi-hop

```
query "ยาลด HbA1c ที่รักษาเบาหวานด้วย"
  → หา node "HbA1c" → เดิน edge [ลด]⁻¹ → {metformin, ...}
  → filter node ที่มี edge [รักษา]→เบาหวาน → metformin
```
- **multi-hop reasoning**: เดินหลาย edge = ตอบคำถามที่ vector เดี่ยวตอบไม่ได้
- graph traversal (BFS/DFS) + vector บน node = **GraphRAG**

---

## 33.3 ⭐ Temporal reasoning (asOf — ARRA มีจริง)

Ch ajfon use-case: "พ.ค. เข้าใจ X แค่ไหน vs ตอนนี้" · ต้อง query ความรู้ **ณ เวลาหนึ่ง**:
```
search(query, asOf='2026-05-01')
  → filter doc ที่ created_at ≤ asOf  (Ch26 metadata)
  → ค้นเฉพาะความรู้ที่มี ณ ตอนนั้น
```
- = literature-review-over-time ของตัวเอง (Ch ecosystem/ajfon)
- **bi-temporal**: valid-time (ความรู้เกี่ยวกับเมื่อไร) vs transaction-time (จดเมื่อไร) — Zep/Graphiti ทำ (data pack)
- ARRA: `last_accessed_at`/`created_at` (Ch13/26) → asOf filter ทำได้บน metadata (ไม่ต้อง full graph)

---

## 33.4 GraphRAG trade-offs (data pack — อ้างตรง)

จาก Ch6/data-pack:
```
- Zep/Graphiti: 63.8% LongMemEval vs mem0 49% → graph ชนะ TEMPORAL/multi-hop
- แต่ GraphRAG แพ้ vanilla RAG 13.4% บน single-hop Natural Questions
- graph latency ~2.3× vector · Zep per-conversation graph > 600k tokens (Ch3 §3.7)
```
→ **graph ไม่ได้ชนะเสมอ**: ชนะเมื่อ multi-hop/temporal · แพ้เมื่อ single-hop (แพงกว่า ช้ากว่า ไม่คุ้ม)

---

## 33.5 เมื่อไหร่ใช้ graph

```
ใช้ vector: "หา doc คล้าย" (single-hop, ส่วนใหญ่)
ใช้ graph:  multi-hop reasoning, temporal, "ความสัมพันธ์เชิงโครงสร้าง"
hybrid:     vector หา entry point → graph เดินต่อ (best of both)
```
- **ARRA ปัจจุบัน = vector+FTS (ไม่มี graph)** · เหมาะกับ second-brain ที่ query ส่วนใหญ่ = "หาโน้ตที่เกี่ยว" (single-hop)
- temporal (asOf) ทำได้บน metadata โดยไม่ต้อง full graph → คุ้มกว่า
- graph = โอกาสต่อยอด (advanced) ถ้าต้องการ reasoning ข้ามหลาย memory

---

## 33.6 vector vs graph — ตารางสรุป

| | Vector | Graph |
|---|---|---|
| จับ | ความคล้าย | ความสัมพันธ์ + โครงสร้าง |
| query | single-hop เก่ง | multi-hop/temporal เก่ง |
| latency | เร็ว | ~2.3× ช้ากว่า |
| storage | เวกเตอร์ | node+edge (โต) |
| construction | embed (ง่าย) | extract triple (LLM, แพง/error) |
| single-hop NQ | ✅ | แพ้ 13.4% |
| ARRA | ✅ ใช้ | ยังไม่ใช้ (asOf บน metadata แทน) |

---

## สรุป Ch33
```
vector จับคล้าย แต่ไม่จับ relation/multi-hop/temporal
graph: extract triple → traverse multi-hop (GraphRAG)
temporal (asOf): filter created_at → literature-review-over-time (ARRA ทำบน metadata)
GraphRAG: ชนะ temporal/multi-hop, แพ้ single-hop 13.4% + ช้า 2.3× (อย่าใช้พร่ำเพรื่อ)
ARRA = vector+FTS (single-hop เป็นหลัก) + asOf metadata · graph = โอกาสต่อยอด
```
**ถัดไป Ch34:** sparse retrieval ลึก — SPLADE (learned sparse + expansion), inverted index, sparse-dense hybrid
---
*grounded: GraphRAG (Microsoft) · Zep/Graphiti (data-pack, bi-temporal) · Ch6/data-pack benchmarks · Ch ajfon (asOf/time-travel), Ch13/26 (metadata time) · /loop deep iter 2026-07-14*
