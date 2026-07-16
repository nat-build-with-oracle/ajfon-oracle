# Deep Technical · Chapter 84 — GraphRAG

> ต่อจาก Ch83 · Ch33 เกริ่น graph · บทนี้ลงลึก GraphRAG: knowledge graph + community + global summarization → ตอบ "ภาพรวม/theme" ที่ vector RAG ทำไม่ได้

---

## 84.0 ปัญหา — vector RAG ตอบ global question ไม่ได้

```
"theme หลักของ vault ทั้งหมดคืออะไร" / "สรุปแนวคิดที่เชื่อมโยงทุกโน้ต"
→ vector: ค้น top-k → เห็นแค่ k doc → ไม่เห็นภาพรวมทั้ง corpus (Ch77 RAPTOR แก้บางส่วน)
→ ต้องการโครงสร้างที่จับ "ความสัมพันธ์" ข้าม doc → graph
```

---

## 84.1 ⭐ GraphRAG pipeline (index time)

```
1. entity extraction: LLM สกัด entity จากทุก chunk (คน/สิ่งของ/แนวคิด, Ch78)
2. relationship extraction: LLM สกัดความสัมพันธ์ (A "เขียน" B, X "เกี่ยวกับ" Y)
3. build knowledge graph: node=entity, edge=relationship (ข้าม doc!)
4. community detection: หา cluster ของ node ที่เชื่อมกันแน่น (Leiden algorithm)
5. community summary: LLM สรุปแต่ละ community → "theme" ระดับกลุ่ม
```
- graph เชื่อม fact ข้าม doc (ต่างจาก chunk แยกกัน) → เห็นโครงสร้างความรู้

---

## 84.2 ⭐ community detection — Leiden/Louvain

```
graph → หา community (กลุ่ม node เชื่อมกันหนาแน่น, ห่างกลุ่มอื่น):
modularity Q = (1/2m) Σ [A_ij − (k_i k_j)/2m] δ(c_i, c_j)
  A_ij = edge i,j · k_i = degree · m = total edges · δ = 1 ถ้า community เดียวกัน
→ maximize Q: กลุ่มที่ edge ภายในเยอะกว่าที่คาดจากสุ่ม
```
- hierarchical: community ย่อย → community ใหญ่ (คล้าย RAPTOR tree Ch77 แต่บน graph structure)
- แต่ละ level = abstraction ต่างกัน (detail community ↔ theme ใหญ่)

---

## 84.3 query — local vs global search

```
local search (entity-centric): query ถาม entity เฉพาะ → เริ่มจาก entity node → ไต่ neighbor
  "PR #2740 เกี่ยวกับใครบ้าง" → node PR#2740 → edge → entities รอบๆ
global search (theme): query ถามภาพรวม → ใช้ community summary (§84.1)
  "theme หลัก" → รวม community summaries → map-reduce → คำตอบระดับ corpus
```
- **global = จุดแข็ง GraphRAG**: ตอบ "ภาพรวม" ที่ vector top-k ทำไม่ได้ (เห็นทั้ง corpus ผ่าน summaries)

---

## 84.4 map-reduce over communities (global)

```
global query:
  map: แต่ละ community summary → LLM ตอบ partial (จากมุม community นั้น)
  reduce: รวม partial answers → คำตอบสุดท้าย (ครอบทุก community = ทั้ง corpus)
```
- ครอบคลุมทั้ง corpus (ทุก community มีส่วนร่วม) → comprehensive (ต่างจาก top-k ที่เห็นแค่ k)

---

## 84.5 ⚠️ ต้นทุน GraphRAG — แพงมาก

```
index: LLM extract entity+relationship ทุก chunk + summarize ทุก community
  → LLM calls มหาศาล (Ch70 compute) — แพงกว่า vector index หลายเท่า
maintenance: doc ใหม่ → update graph + re-detect community + re-summarize (Ch46) → แพง incremental
```
- **trade**: ตอบ global/multi-hop (Ch82) ได้ดี แลกกับ index cost สูงมาก
- คุ้มเมื่อ: corpus ต้องการ global insight บ่อย (research synthesis) · ไม่คุ้มถ้าถาม fact เดี่ยว (vector พอ)

---

## 84.6 เชื่อม ARRA

```
ARRA vector/hybrid (Ch4): เก่ง local/fact retrieval (ค้น chunk เกี่ยว) — ครอบ 90% second brain
GraphRAG = ชั้นเสริมถ้าต้องการ global:
  entity extraction (Ch78 auto-metadata) → build graph → community (Claude summarize)
  → ตอบ "theme ของโน้ตทั้งหมด" (global) ที่ vector top-k ทำไม่ได้
ARRA ปัจจุบัน: vector + Claude สรุป top-k (Ch75/77) พอสำหรับ personal
→ GraphRAG = option เมื่อ corpus ใหญ่+ต้องการ synthesis ข้าม doc (scale-appropriate Ch77)
```
- **community**: "ถามภาพรวมทั้ง vault ได้ไหม" → vector+สรุป (เล็ก) พอ · corpus ใหญ่จริง → GraphRAG

---

## สรุป Ch84
```
vector RAG ตอบ global ("theme ทั้ง corpus") ไม่ได้ (เห็นแค่ top-k) → GraphRAG
⭐ index: entity+relationship extract (Ch78)→build KG→community detection→community summary
⭐ community detection: Leiden maximize modularity Q=(1/2m)Σ[A_ij−k_ik_j/2m]δ → กลุ่มเชื่อมแน่น (hierarchical คล้าย RAPTOR Ch77)
query: local (entity node→neighbor) vs global (map-reduce community summaries = ทั้ง corpus)
⚠️ cost มหาศาล (LLM extract ทุก chunk+summarize) — แพงกว่า vector หลายเท่า (Ch70)
คุ้มเมื่อต้องการ global synthesis · fact เดี่ยว=vector พอ (scale-appropriate)
ARRA: vector local เก่ง+Claude สรุป (Ch75/77) พอ personal · GraphRAG=option corpus ใหญ่
```
**ถัดไป Ch85:** knowledge graph + vector hybrid — รวม structured KG traversal กับ semantic vector, เมื่อไหร่ใช้ graph เมื่อไหร่ vector, entity linking
---
*grounded: GraphRAG (Microsoft, Edge 2024) · Leiden/modularity community detection · local/global search · map-reduce summarization · เชื่อม Ch4/33/46/70/75/77/78/82 · /loop deep iter 2026-07-16*
