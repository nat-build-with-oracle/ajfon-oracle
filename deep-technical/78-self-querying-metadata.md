# Deep Technical · Chapter 78 — Self-Querying & Metadata Extraction

> ต่อจาก Ch77 · Ch55/60/61 = filter/structured query · บทนี้: LLM แปลง natural query → structured filter อัตโนมัติ + auto-extract metadata ตอน ingest

---

## 78.0 ปัญหา — user พิมพ์ภาษาคน ไม่พิมพ์ filter

```
user: "งานวิจัยเรื่อง vector search ที่เขียนหลังปี 2023"
→ semantic: "vector search" · structured: year > 2023 (Ch61)
→ user ไม่กรอก filter form → ต้อง "แกะ" structured ออกจากภาษาธรรมชาติเอง
```

---

## 78.1 ⭐ self-querying — LLM แกะ query

LLM แปลง natural language → { semantic query + structured filter }:
```
input: "งานวิจัย vector search หลังปี 2023 ในโฟลเดอร์ AI"
LLM output:
  {
    semantic: "vector search research",
    filter: { year: {$gt: 2023}, folder: "AI" }
  }
→ ค้น semantic (vector) + apply filter (Ch55 pre-filter) → ตรงเป๊ะ
```
- LLM รู้ schema metadata (มี field อะไรบ้าง) → map ภาษาคน → field/operator
- นี่คือ query rewriting (Ch57) ที่ output เป็น structured (ไม่ใช่แค่ expand text)

---

## 78.2 schema-aware prompting

```
บอก LLM ว่ามี metadata อะไร:
  fields: { year: int, folder: str, tags: [str], author: str, type: enum }
  operators: $gt $lt $eq $in $contains
→ LLM constrain output ใน schema → ไม่ hallucinate field ที่ไม่มี
```
- ⚠️ validate output: LLM อาจสร้าง filter ผิด format → parse + validate ก่อน apply (กัน error/injection)
- structured output (JSON mode / function calling) → บังคับ format ถูก

---

## 78.3 ⭐ auto-extract metadata ตอน ingest

metadata ดีมาจากไหน? — สกัดตอน ingest (Ch51):
```
doc → LLM extract:
  { title, date (จากเนื้อหา), topics: [...], entities: [...], summary, doc_type }
→ เก็บเป็น metadata (Ch51) → ใช้ filter/facet (Ch61) + self-query (§78.1) ตอนค้น
```
- ต่างจาก metadata explicit (folder/mtime, จากระบบไฟล์) → **derived metadata** (จากเนื้อหา, ต้อง LLM/NER)
- entity/topic extraction → เปิด structured query ที่ไม่มีใน raw file (เช่น "โน้ตที่พูดถึงคนชื่อ X")

---

## 78.4 cost & reliability trade

```
self-query (ค้น): +1 LLM call ต่อ query → latency (Ch44) + cost (Ch70)
  → cache (Ch32) query→structured (query ซ้ำไม่ต้องแกะใหม่)
auto-extract (ingest): +LLM ต่อ doc (one-time, amortize Ch70) → แพงตอน ingest ครั้งเดียว
⚠️ reliability: LLM แกะผิด → filter ผิด → ค้นพลาด → validate + fallback (ถ้าแกะไม่ได้ → semantic ล้วน)
```
- **fallback**: self-query fail → ค้น semantic อย่างเดียว (ไม่ error, degrade gracefully, Ch4 pattern)

---

## 78.5 เชื่อม agentic (Ch35) & conversational (Ch58)

```
self-query = ขั้นหนึ่งของ agentic retrieval (Ch35):
  agent อ่าน query → ตัดสิน (ต้อง filter ไหม? หลาย sub-query ไหม Ch57?) → แกะ structured → ค้น
conversational (Ch58): "อันที่เขียนปีที่แล้ว" → resolve "ปีที่แล้ว"=2025 → filter year=2025
→ LLM ทำ query understanding เต็มรูป (coreference Ch58 + structured extraction Ch78)
```

---

## 78.6 เชื่อม ARRA

```
ARRA ใน Claude Code (Ch15): Claude = LLM ที่แกะ query ให้!
  user natural query → Claude แกะ semantic+filter → เรียก ARRA (hybrid Ch4 + metadata filter Ch55)
  → self-querying ฟรี (Claude ทำ, ARRA รับ structured)
auto-extract (Ch51): ingest → Claude/LLM สกัด topic/entity → metadata → filter ได้
→ ARRA + Claude: Claude=query understanding (self-query+coreference), ARRA=execute (ค้น+filter)
```
- **community**: "ค้นแบบพิมพ์ภาษาคนได้เลยไหม (ไม่ต้องใส่ filter)" → ได้ Claude แกะให้ (self-query)

---

## สรุป Ch78
```
user พิมพ์ภาษาคน (ไม่ใช่ filter form) → ต้องแกะ structured ออกเอง
⭐ self-querying: LLM แปลง NL → {semantic + filter (Ch55/61)} → schema-aware prompt (constrain field/op)
   validate output (กัน hallucinate field/injection) · structured output (JSON/function calling)
⭐ auto-extract ตอน ingest (Ch51): LLM สกัด title/date/topic/entity → derived metadata (จากเนื้อหา)
trade: self-query +LLM/query (cache Ch32) · auto-extract +LLM/doc (amortize Ch70) · ⚠️ validate+fallback semantic
เชื่อม agentic (Ch35)/conversational (Ch58): query understanding เต็ม (coreference+structured)
ARRA+Claude: Claude แกะ query (self-query ฟรี) → ARRA execute (hybrid+filter) — แบ่งหน้าที่
```
**ถัดไป Ch79:** query routing & multi-index — เลือก index/collection ไหนจาก query, router (semantic/keyword classifier), federated search หลายแหล่ง
---
*grounded: self-querying (LangChain SelfQueryRetriever) · schema-aware extraction · derived metadata · structured output · เชื่อม Ch4/15/32/35/44/51/55/57/58/61/70 · /loop deep iter 2026-07-16*
