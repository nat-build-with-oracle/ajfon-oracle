# Deep Technical · Chapter 79 — Query Routing & Multi-Index

> ต่อจาก Ch78 · ระบบจริงมีหลาย index/แหล่ง · บทนี้: router เลือกแหล่งจาก query, federated search, เมื่อไหร่ค้นที่ไหน

---

## 79.0 ปัญหา — ไม่ใช่ทุก query ค้นที่เดียว

```
"โค้ด function embed อยู่ไหน" → ค้น code index
"สรุปประชุมเมื่อวาน" → ค้น notes index
"ราคาหุ้น X" → ไม่ต้องค้น vault เลย → tool อื่น (API)
→ query ต่างชนิด → แหล่งต่าง → ต้อง route
```

---

## 79.1 ⭐ query router — เลือกปลายทาง

```
query → classifier → เลือก index/tool ที่เหมาะ:
  1. rule-based: keyword/pattern ("โค้ด"→code, "ประชุม"→notes)
  2. embedding-based: embed query → cos กับ "คำอธิบายแต่ละ index" → เลือกใกล้สุด (Ch1!)
  3. LLM-based: LLM ตัดสิน (เข้าใจ intent ลึก, +latency/cost)
```
- **embedding router เก๋**: ใช้ vector search เลือก index (meta-retrieval) — embed description ของแต่ละ collection → route ด้วย cos
- fallback: ไม่แน่ใจ → ค้นทุก index แล้ว merge (§79.3)

---

## 79.2 multi-index — ทำไมแยก index

```
แยก index ตาม: modality (Ch71 text/image), domain (code/notes/docs), 
                freshness (hot recent / cold archive), tenant (Ch27)
เหตุผล:
  - embed model ต่าง (code embedder ≠ text, Ch53)
  - filter/retention ต่าง (archive เก็บนาน, hot บ่อย)
  - performance: index เล็กเฉพาะทาง เร็ว+แม่นกว่า index รวมยักษ์
```
- trade: แยก = ต้อง route (§79.1) + อาจ merge · รวม = ง่าย แต่ index ใหญ่+โมเดลเดียว

---

## 79.3 ⭐ federated search — ค้นหลายแหล่ง + รวม

```
query → ค้นหลาย index/แหล่งพร้อมกัน (scatter, คล้าย Ch66) → รวมผล:
  1. ค้นแต่ละแหล่ง → top-k ต่อแหล่ง
  2. normalize score ข้ามแหล่ง (⚠️ scale ต่าง! Ch56) → RRF (rank-based ช่วย)
  3. merge → global top-k
```
- ⚠️ **score ข้ามแหล่งเทียบยาก** (คนละ index/โมเดล) → RRF (Ch11 rank scale-free) = ทางออก (เหมือน hybrid Ch56 แต่ข้าม index)
- federated รวม: vault + web + API + code → คำตอบครบจากหลายโลก

---

## 79.4 routing กับ cost/latency

```
route ถูก → ค้นแหล่งเดียว (เร็ว, ถูก) · route ผิด → พลาด (ค้นผิดที่)
federated (ค้นทุกแหล่ง) → ครบ แต่แพง (หลาย search, Ch70) + latency (straggler Ch44/66)
→ สมดุล: router แม่น → ค้นเจาะจง · ไม่แน่ใจ → federated (recall สำคัญกว่า cost)
```
- adaptive: query ชัด → route เดียว · query กว้าง/กำกวม → federated

---

## 79.5 เชื่อม agentic (Ch35) — router = agent decision

```
agentic retrieval (Ch35): agent ตัดสิน "ค้นที่ไหน กี่ครั้ง" = query routing เป็นส่วนหนึ่ง
  Claude (Ch15): เห็น tool หลายตัว (ARRA, web search, code search) → เลือกเรียกตัวไหน = routing!
→ LLM router โดยธรรมชาติ (Claude ตัดสิน tool) — ไม่ต้องเขียน classifier แยก
```

---

## 79.6 เชื่อม ARRA

```
ARRA เป็น 1 tool ใน Claude Code (Ch15): Claude route ระหว่าง ARRA vs web vs code เอง (§79.5)
ภายใน ARRA: อาจมีหลาย collection (notes/code/docs) → route ด้วย mode (Ch4 hybrid/fts/vector) + filter (Ch55)
federated (§79.3): ARRA + skills-cli + oracle อื่น → รวมผล (fleet ecosystem)
→ Claude=router (เลือก tool/collection), ARRA=execute · RRF (Ch11) รวมข้ามแหล่งถ้าต้อง
```
- **community**: "ระบบรู้ได้ไงว่าจะค้นที่ไหน" → Claude route (เห็น intent) → เรียก tool ที่ใช่ (ARRA/web/code)

---

## สรุป Ch79
```
ไม่ใช่ทุก query ค้นที่เดียว (code/notes/API ต่างแหล่ง) → ต้อง route
⭐ router: rule-based / embedding-based (cos กับ index description, meta-retrieval Ch1) / LLM-based
multi-index แยกตาม modality(Ch71)/domain/freshness/tenant → เล็กเฉพาะทาง เร็ว+แม่น (trade: ต้อง route)
⭐ federated: ค้นหลายแหล่ง (scatter Ch66) → ⚠️ score scale ต่าง → RRF (rank Ch11/56) → merge
routing vs federated: route แม่น=เจาะจง(เร็ว) · ไม่แน่ใจ=federated(ครบ,แพง) → adaptive
agentic (Ch35): Claude เลือก tool = LLM router ฟรี (Ch15)
ARRA: Claude route tool/collection, ARRA execute · RRF รวมข้ามแหล่ง (fleet federated)
```
**ถัดไป Ch80:** adaptive retrieval — decide when to retrieve (ไม่ใช่ทุก query ต้องค้น), self-RAG reflection, retrieve-or-not, active retrieval (FLARE)
---
*grounded: query routing (semantic router) · federated search · RRF cross-source (Ch11/56) · agentic routing (Ch35) · เชื่อม Ch1/4/11/15/27/35/44/53/55/56/66/70/71 · /loop deep iter 2026-07-16*
