# Deep Technical · Chapter 86 — Entity-Centric Retrieval

> ต่อจาก Ch85 · บางคำถามหมุนรอบ "สิ่งของ" ไม่ใช่ "เอกสาร" · บทนี้: index รอบ entity, entity cards, aggregation ต่อ entity, ทำไมบาง domain ต้อง entity-first

---

## 86.0 ปัญหา — chunk-centric ตอบ entity question ไม่ดี

```
"ทุกอย่างที่รู้เกี่ยวกับ PR #2740" → ข้อมูลกระจายหลาย chunk/doc (คนละที่พูดถึง PR นี้)
chunk retrieval: ค้นเจอ chunk ที่พูดถึง PR#2740 บ้าง → แต่ไม่รวมเป็น "ภาพเดียวของ entity"
→ อยากได้ "การ์ดสรุป entity" ที่รวมทุกอย่างเกี่ยว PR#2740
```

---

## 86.1 ⭐ entity card — รวมข้อมูลต่อ entity

```
แทน index chunk อย่างเดียว → สร้าง "entity card" ต่อ entity:
  PR#2740: {
    mentions: [chunk1, chunk5, chunk9],   // ทุกที่ที่พูดถึง
    attributes: { author, date, topic },   // สกัด (Ch78)
    relationships: [→ drift benchmark, → Ch6],  // graph (Ch84/85)
    summary: "..."                          // LLM สรุปรวม
  }
→ ค้นเจอ entity → ได้ภาพครบทันที (ไม่ต้องรวม chunk เอง)
```
- entity card = view รวมต่อ entity (คล้าย materialized view ใน DB)

---

## 86.2 aggregation ต่อ entity

```
"PR ทั้งหมดที่ A เขียน" → aggregate:
  หา entity A → follow relationship "เขียน" → รวม PR ทั้งหมด (group by entity)
"กี่โน้ตพูดถึง vector search" → count mentions ต่อ entity
```
- ต่างจาก chunk retrieval (คืน chunk): entity-centric คืน aggregate (นับ/รวม/สรุปต่อ entity)
- เชื่อม faceted (Ch61): facet = aggregate ต่อ dimension · entity = aggregate ต่อ entity

---

## 86.3 ⭐ dual index — chunk + entity

```
chunk index (Ch3): semantic search (หา passage เกี่ยว) — เดิม
entity index:      หา entity (ชื่อ/attribute) + card (§86.1)
query:
  "PR#2740 คืออะไร" → entity index → card (ครบ)
  "อธิบายเรื่อง drift" → chunk index → passage (detail)
```
- 2 index เสริมกัน (Ch79 multi-index): entity สำหรับ "รู้ทุกอย่างเกี่ยว X", chunk สำหรับ "อธิบาย/detail"

---

## 86.4 เมื่อไหร่ต้อง entity-first

```
entity-centric เด่น: domain ที่ "สิ่งของ" เป็นหลัก
  - CRM (ลูกค้า), product catalog (สินค้า), codebase (function/module)
  - "รู้ทุกอย่างเกี่ยว X" เป็นคำถามหลัก
chunk-centric พอ: domain ข้อความอิสระ (บทความ, โน้ตเล่าเรื่อง)
  - "อธิบาย/หา passage" เป็นหลัก
```
- second brain: ผสม (บาง entity สำคัญ: project, คน, concept) → dual (§86.3)

---

## 86.5 ⚠️ maintenance — entity card ต้อง update

```
chunk ใหม่พูดถึง entity → card ต้อง update (เพิ่ม mention, re-summarize)
→ incremental (Ch45) บน entity: doc ใหม่ → extract entity (Ch78) → update card
⚠️ entity resolution (Ch85 linking): mention ใหม่ = entity เดิมไหม → link ถูก (ไม่งั้น card แตก)
```
- cost: สร้าง+maintain card (LLM summarize, Ch70) → เหมือน RAPTOR/GraphRAG (Ch77/84) แต่ต่อ entity

---

## 86.6 เชื่อม ARRA

```
ARRA chunk (Ch4) + metadata/entity (Ch78): มี entity info อยู่บ้าง
entity card (§86.1): Claude รวม chunk เกี่ยว entity → สรุป (ทำ on-the-fly ตอนถาม, ไม่ต้อง pre-build)
  → "รู้อะไรเกี่ยว PR#2740" → ARRA ค้น chunk ที่ mention → Claude รวมเป็น card (Ch75 assembly)
dual index (§86.3): ARRA metadata filter (Ch55) = entity lookup เบาๆ (by source/tag)
→ ARRA: chunk-centric core + Claude รวม entity on-demand (ไม่ต้อง entity index แยกสำหรับ personal)
```
- **community**: "รวมทุกอย่างเกี่ยวเรื่องหนึ่งได้ไหม" → ARRA ค้น chunk เกี่ยว + Claude สรุปเป็น entity view

---

## สรุป Ch86
```
chunk-centric ตอบ "รู้ทุกอย่างเกี่ยว entity X" ไม่ดี (กระจายหลาย chunk ไม่รวม)
⭐ entity card: รวม mentions+attributes(Ch78)+relationships(Ch85)+summary ต่อ entity (materialized view)
aggregation: group/count/รวม ต่อ entity (≠ คืน chunk) · เชื่อม faceted (Ch61)
⭐ dual index: chunk (semantic passage) + entity (card, "รู้ทุกอย่างเกี่ยว X") เสริมกัน (Ch79)
entity-first เด่น: CRM/catalog/codebase (สิ่งของเป็นหลัก) · chunk พอ: บทความ/เล่าเรื่อง
⚠️ maintenance: card update (incremental Ch45 + entity resolution Ch85) + cost (LLM Ch70)
ARRA: chunk core + Claude รวม entity on-demand (ไม่ต้อง entity index แยก, personal)
```
**ถัดไป Ch87:** temporal & versioned knowledge — fact ที่เปลี่ยนตามเวลา, "ตอนนั้น vs ตอนนี้", bi-temporal, ทำไม second brain ต้องรู้ "เมื่อไหร่จริง"
---
*grounded: entity-centric retrieval · entity cards (materialized view) · dual index (Ch79) · entity resolution (Ch85) · เชื่อม Ch3/4/45/55/61/70/75/77/78/84/85 · /loop deep iter 2026-07-16*
