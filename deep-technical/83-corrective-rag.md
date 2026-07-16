# Deep Technical · Chapter 83 — Corrective RAG (CRAG)

> ต่อจาก Ch82 · retrieval แย่ → คำตอบแย่ · CRAG = ประเมิน retrieval แล้ว "แก้" ก่อนป้อน LLM · บทนี้: quality grading, knowledge refinement, fallback to web

---

## 83.0 ปัญหา — retrieval แย่ แต่ยังป้อน LLM

```
retrieval คืน doc ไม่เกี่ยว/บางส่วน (Ch81) → ป้อน LLM ตรงๆ → LLM ตอบจากขยะ
naive RAG: retrieve → generate (ไม่เช็ค quality ระหว่างทาง)
→ ต้องมี "gate" ประเมิน retrieval ก่อน generate → CRAG
```

---

## 83.1 ⭐ CRAG — retrieval evaluator + action

```
retrieve → evaluator ให้เกรด → เลือก action:
  Correct (เกี่ยวชัด):   refine (สกัดส่วนสำคัญ) → generate
  Incorrect (ไม่เกี่ยว):  ทิ้ง → fallback (web search / ค้นใหม่)
  Ambiguous (ก้ำกึ่ง):    ทั้งคู่ (refine + web) → generate
```
- evaluator = lightweight model/LLM ให้ confidence score (Ch81) ต่อ retrieved doc
- action ตามเกรด → ไม่ป้อนขยะเข้า LLM (แก้ที่ retrieval ไม่ใช่หวังให้ LLM ทน)

---

## 83.2 ⭐ knowledge refinement — decompose-then-recompose

```
doc ที่ retrieve มัก มีทั้งส่วนเกี่ยว+ไม่เกี่ยว (1 chunk ยาว)
CRAG refine:
  1. decompose: แตก doc เป็น "knowledge strips" (ประโยค/ย่อหน้าย่อย)
  2. grade แต่ละ strip: เกี่ยว query ไหม (Ch81 relevance score)
  3. recompose: เก็บเฉพาะ strip ที่เกี่ยว → context สะอาด (Ch75 precision)
```
- ตัด noise ระดับ sub-doc (ละเอียดกว่า chunk filter) → LLM ได้เฉพาะที่ตรง

---

## 83.3 web fallback — เมื่อ vault ไม่พอ

```
retrieval ใน vault แย่ (Ch81 ทุก doc cos ต่ำ) → knowledge ไม่มีในเครื่อง
→ CRAG: fallback ค้น web (external) → ได้ knowledge สด/กว้าง
→ combine: vault (ส่วนตัว) + web (ทั่วไป) → คำตอบครบ
```
- เชื่อม federated (Ch79): CRAG เลือก source ตาม quality (vault พอ→vault, ไม่พอ→+web)
- ⚠️ web = ออกนอกเครื่อง (privacy Ch27) → ARRA local: fallback web เป็น opt-in (user ยอม)

---

## 83.4 CRAG vs Self-RAG (Ch80) — ต่างกันยังไง

```
Self-RAG (Ch80): LLM reflect เอง (train มาให้ออก token [Relevant?]) — ผูกกับโมเดล
CRAG:            evaluator แยก (plug-in) ประเมิน retrieval — ใช้กับ LLM อะไรก็ได้
→ CRAG = correction layer ภายนอก (model-agnostic) · Self-RAG = built-in reflection
```
- ใช้ร่วมได้: CRAG แก้ retrieval + Self-RAG reflect generation → 2 gate

---

## 83.5 ต้นทุน & เมื่อไหร่คุ้ม

```
CRAG +: evaluator call (ต่อ retrieve) + web fallback (ถ้า trigger) → latency/cost (Ch70)
คุ้มเมื่อ: retrieval quality ไม่นิ่ง (corpus เล็ก/coverage ไม่ครบ → มั่วบ่อย)
ไม่คุ้ม: retrieval ดีอยู่แล้ว (hybrid+rerank Ch4/18 แม่น) → CRAG แทบไม่ trigger
```
- simple: rerank+threshold (Ch75/81) กัน noise พื้นฐาน · CRAG = ชั้นแก้เชิงรุก (ค้นใหม่/web)

---

## 83.6 เชื่อม ARRA

```
evaluator (§83.1): ARRA score (Ch4/11) + Claude grade → correct/incorrect/ambiguous
refine (§83.2): Claude สกัด strip เกี่ยว (Ch75 precision) — Claude ทำ knowledge refinement เอง
web fallback (§83.3): ARRA (vault) ไม่พอ → Claude ค้น web tool (Ch79 routing) — opt-in privacy (Ch27)
→ CRAG = Claude ประเมิน+แก้ retrieval ARRA (correction layer) โดยธรรมชาติ (Ch80 reflection ต่อยอด)
```
- **community**: "ถ้า vault ไม่มีข้อมูล จะทำไง" → abstain (Ch81) หรือ fallback web (CRAG, ถ้าอนุญาต)

---

## สรุป Ch83
```
naive RAG: retrieve→generate (ไม่เช็ค) → retrieval แย่=คำตอบแย่
⭐ CRAG: evaluator ให้เกรด retrieval → action (Correct→refine, Incorrect→web/ค้นใหม่, Ambiguous→ทั้งคู่)
⭐ knowledge refinement: decompose doc→strips → grade แต่ละ strip (Ch81) → recompose เฉพาะเกี่ยว (Ch75 precision)
web fallback: vault แย่ (Ch81)→ค้น web (federated Ch79) · ⚠️ privacy (Ch27) opt-in
CRAG (evaluator แยก, model-agnostic) vs Self-RAG (Ch80, built-in) → ใช้ร่วม 2 gate ได้
คุ้มเมื่อ retrieval ไม่นิ่ง · retrieval ดีแล้ว (Ch4/18)=แทบไม่ trigger
ARRA+Claude: Claude grade+refine+web fallback = correction layer (Ch80 ต่อยอด)
```
**ถัดไป Ch84:** GraphRAG deep — knowledge graph + community detection + global summarization, ตอบ "ภาพรวม/theme" ที่ vector RAG ทำไม่ได้
---
*grounded: CRAG (Yan 2024) · knowledge refinement (decompose-recompose) · web fallback · vs Self-RAG (Ch80) · เชื่อม Ch4/11/18/27/70/75/79/80/81 · /loop deep iter 2026-07-16*
