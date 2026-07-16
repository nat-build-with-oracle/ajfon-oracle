# Deep Technical · Chapter 85 — Knowledge Graph + Vector Hybrid

> ต่อจาก Ch84 · GraphRAG ใช้ graph เต็มตัว · บทนี้: รวม structured KG traversal กับ semantic vector อย่างสมดุล — เมื่อไหร่ graph, เมื่อไหร่ vector, entity linking

---

## 85.0 graph vs vector — จุดแข็งต่างกัน

```
vector (Ch1-83):  semantic similarity (fuzzy, "เกี่ยวข้องกัน")
                  → เก่ง: หา doc คล้ายความหมาย, query กว้าง
graph (Ch84):     explicit relationship (exact, "A เขียน B")
                  → เก่ง: multi-hop (Ch82), เชื่อม fact แน่นอน, structured
→ รวม: vector หา entry point (fuzzy) + graph traverse relationship (exact)
```

---

## 85.1 ⭐ vector-to-graph entry (pattern หลัก)

```
1. vector search: query → semantic → หา entity/node ที่เกี่ยว (entry point)
   "คนที่ทำงาน embedding" → vector หา chunk → entity "A"
2. graph traverse: จาก A → ไต่ relationship (exact)
   A → "ทำงานที่" → team X → "สมาชิก" → B, C
3. รวม: semantic entry (vector) + structured expansion (graph)
```
- vector แก้ปัญหา graph: "เริ่ม traverse ที่ node ไหน" (fuzzy match query→node)
- graph แก้ปัญหา vector: "เชื่อม fact หลายก้าว" (Ch82 multi-hop แต่ structured)

---

## 85.2 ⭐ entity linking — เชื่อม mention → node

```
ปัญหา: doc พูดถึง "อ.นัท", "Nat", "nat_c" → entity เดียวกันไหม?
entity linking: mention (ในข้อความ) → canonical entity (ใน KG)
วิธี: embed mention + context (Ch2) → cos กับ entity embeddings → link ตัวใกล้สุด
      + rule (alias table) + disambiguation (context ช่วยแยก "Apple บริษัท" vs "apple ผลไม้")
```
- vector ช่วย entity linking (semantic match mention→entity) → KG แม่นขึ้น
- ⚠️ ผิด link → graph พัง (fact เชื่อมผิด entity) → verify (Ch72)

---

## 85.3 node embeddings — vector บน graph structure

```
embed node โดยดู graph structure (ไม่ใช่แค่ text):
  node2vec / GraphSAGE: random walk บน graph → เรียน embedding ที่จับ "ตำแหน่งใน graph"
  → node ที่เชื่อมโครงสร้างคล้ายกัน → embedding ใกล้ (แม้ text ต่าง)
```
- ต่างจาก text embedding (Ch2): จับ structural similarity (บทบาทใน graph) ไม่ใช่ semantic
- ใช้: หา node "คล้ายเชิงโครงสร้าง" (เช่น entity ที่มี role คล้ายกัน)

---

## 85.4 query planning — graph หรือ vector ก่อน

```
router (Ch79) ตัดสิน:
  query semantic กว้าง ("เรื่องเกี่ยวกับ X") → vector ก่อน
  query relational ("ใครเชื่อมกับ Y") → graph ก่อน (จาก entity Y)
  query ผสม → vector entry → graph expand (§85.1)
```
- adaptive (Ch80): เลือก strategy ตามชนิดคำถาม

---

## 85.5 ⚠️ complexity trade

```
KG+vector = 2 ระบบ (graph store + vector store) → sync, maintain, query planning ซับซ้อน
  index: build graph (Ch84 แพง) + vector index (Ch3)
  query: route + traverse + rank รวม
→ คุ้มเมื่อ: relationship สำคัญ (multi-hop, structured domain) + มีทรัพยากร
ไม่คุ้ม: fact/semantic ล้วน → vector พอ (Ch4)
```
- scale-appropriate (ย้ำ): personal ARRA → vector พอ · enterprise KG (org chart, product graph) → hybrid คุ้ม

---

## 85.6 เชื่อม ARRA

```
ARRA vector/hybrid (Ch4): semantic retrieval — core
entity linking (§85.2): auto-extract entity (Ch78) + vector match → เชื่อม mention (โน้ตพูดถึงคนเดียวกัน)
vector-to-graph (§85.1): ถ้าสร้าง KG จาก vault → vector entry + graph expand (relationship ข้ามโน้ต)
ARRA ปัจจุบัน: vector + metadata (Ch51) พอ · KG = ชั้นเสริม (relationship ข้าม doc)
→ Claude ทำ graph reasoning (multi-hop Ch82) บน result ARRA โดยไม่ต้อง KG store แยกก็ได้ (lightweight)
```
- **community**: "เชื่อมโยงโน้ตเป็น network ได้ไหม" → entity linking + relationship (KG) · แต่ vector+Claude reasoning พอสำหรับเริ่มต้น

---

## สรุป Ch85
```
graph (exact relationship, multi-hop) vs vector (fuzzy semantic) → รวมจุดแข็ง
⭐ vector-to-graph: vector หา entry node (fuzzy match query→node) → graph traverse (exact expand)
   vector แก้ "เริ่มที่ node ไหน" · graph แก้ "เชื่อม fact หลายก้าว" (Ch82 structured)
⭐ entity linking: mention→canonical node (embed+cos Ch2 + alias + disambiguation) → KG แม่น
node embeddings (node2vec/GraphSAGE): จับ structural similarity (บทบาทใน graph) ≠ semantic
query planning (Ch79/80): semantic→vector, relational→graph, ผสม→vector entry+graph expand
⚠️ complexity: 2 ระบบ sync/maintain → scale-appropriate (personal=vector พอ, enterprise KG=คุ้ม)
ARRA: vector core + entity linking (Ch78) · KG=ชั้นเสริม · Claude reasoning แทน KG store ได้ (lightweight)
```
**ถัดไป Ch86:** entity-centric retrieval — index รอบ entity (ไม่ใช่ chunk), entity cards, aggregation ต่อ entity, ทำไมบาง domain ต้อง entity-first
---
*grounded: vector-to-graph · entity linking (embed+disambiguation) · node2vec/GraphSAGE · query planning (Ch79/80) · เชื่อม Ch1/2/3/4/51/72/78/79/80/82/84 · /loop deep iter 2026-07-16*
