# Deep Technical · Chapter 54 — Observability & Tracing

> ต่อจาก Ch53 · production retrieval พังยังไงก็ต้องรู้ · บทนี้: log/metric/trace สามชั้น, distributed trace ของ 1 query, debug "ทำไมค้นไม่เจอ"

---

## 54.0 ทำไม retrieval ต้อง observable

```
retrieval พังแบบเงียบ: ไม่ error แต่ผล "แย่ลง" (recall ตก, relevance เพี้ยน)
→ ต่างจาก crash (เห็นชัด) · retrieval quality drop = ต้อง "วัด" ถึงจะรู้ (Ch53 §53.2 mismatch เงียบ)
```
→ observability = เห็นสุขภาพ retrieval ตลอดเวลา ไม่ใช่รอ user บ่น

---

## 54.1 สามชั้น — log / metric / trace

```
log:    เหตุการณ์ดิบ (query text, result ids, error) — debug เจาะจุด
metric: ตัวเลขรวม (qps, latency p50/p99 Ch44, recall, cache hit Ch32) — เห็น trend/alert
trace:  เส้นทาง 1 query ข้าม stage (embed→search→rerank) + เวลาแต่ละช่วง — หาคอขวด
```
- 3 ชั้นเสริมกัน: metric เห็น "ช้าลง" → trace เห็น "stage ไหนช้า" → log เห็น "query อะไร/ทำไม"

---

## 54.2 ⭐ distributed trace ของ 1 query

query เดินผ่านหลาย component (Ch4/44) → trace ผูกด้วย trace_id:
```
trace_id: abc123
├─ span: embed_query        30ms  [provider=ollama, model=bge-m3]
├─ span: vector_search       4ms  [index=lance, nprobe=16, candidates=200]
├─ span: fts_search          3ms  [fts5, terms=5]
├─ span: rrf_merge          <1ms  [k=60, dense=200, sparse=150]
├─ span: rerank             80ms  [cross-encoder, top_k=20]   ← ช้าสุด!
└─ total                   118ms
```
- เห็นทันทีว่า rerank (Ch18) กิน 68% ของเวลา → รู้จะ optimize ตรงไหน (Ch44 §44.0 budget)
- **OpenTelemetry** = มาตรฐาน trace (span, context propagation) → ใช้ได้กับ ARRA backend

---

## 54.3 metric ที่ต้องเฝ้า (retrieval-specific)

```
latency:      p50/p95/p99 ต่อ stage (Ch44) — tail คือที่ user รู้สึก
throughput:   qps, embed/sec (Ch51)
quality:      recall@k / nDCG (Ch6) บน eval set รันเป็นระยะ (online Ch31)
cache:        hit rate (Ch32) — ต่ำ = cache ไม่ช่วย
fallback:     fallback trigger rate (Ch4) — สูง = provider หลักมีปัญหา
heat:         distribution (Ch13) — power-law ปกติไหม
error:        embed timeout rate, parse fail rate (Ch51)
```
- **alert**: p99 > threshold, recall drop > X%, fallback rate spike → เตือนก่อน user เจอ

---

## 54.4 ⭐ debug "ทำไมค้นไม่เจอ" (playbook)

คำถามที่เจอบ่อยสุดใน retrieval — trace ทีละชั้น:
```
1. doc อยู่ใน index ไหม?        → query by id/source (ingest สำเร็จ? Ch51)
2. doc ถูก embed ถูกโมเดลไหม?    → check model tag (Ch53 mismatch?)
3. chunk boundary ตัดคำสำคัญ?    → ดู chunk (Ch12 — คำ query อยู่คนละ chunk?)
4. vector score เท่าไร?          → คำนวณ cos(query, doc) ตรงๆ — ต่ำจริงหรือ rank ตก?
5. FTS จับไหม?                   → exact term match (Ch34 — hybrid ควรช่วย)
6. RRF/rerank กดอันดับ?          → ดู score ก่อน/หลัง merge (Ch11/18)
```
- **เครื่องมือ**: log query→result ids + score → replay ได้ (Ch31 log) → หาจุดที่ doc หาย

---

## 54.5 observability กับ privacy (เชื่อม Ch27)

```
⚠️ log query text = อาจมี PII (second brain = ข้อมูลส่วนตัว)
→ ARRA local: log อยู่ในเครื่อง (ไม่ส่ง cloud) → privacy โดย default (Ch14/27)
→ ถ้า cloud: redact/hash query ใน log, retention สั้น (Ch27)
```
- trace id ไม่ใช่ content → ใช้ผูก trace ได้โดยไม่ log ข้อความจริง (privacy-preserving)

---

## 54.6 เชื่อม ARRA

```
local backend → log/metric ในเครื่อง (privacy Ch27) — debug ได้ไม่ส่งออก
trace 1 query (§54.2) → เห็น embed/rerank เป็นคอขวด (Ch44) → optimize ตรงเป้า
metric recall online (§54.3, Ch31) → จับ quality drop (Ch53 mismatch) ก่อน user บ่น
debug playbook (§54.4) → ตอบ "ทำไมค้นไม่เจอ" อย่างเป็นระบบ (คำถาม community #1)
```

---

## สรุป Ch54
```
retrieval พังเงียบ (quality drop ไม่ crash) → ต้อง observable (วัด ไม่ใช่รอบ่น)
3 ชั้น: log(ดิบ/เจาะ) · metric(รวม/trend/alert) · trace(เส้นทาง query/คอขวด)
⭐ distributed trace: span ต่อ stage + เวลา → เห็น rerank กิน 68% (OpenTelemetry)
metric retrieval: p99(Ch44)/recall(Ch6)/cache(Ch32)/fallback(Ch4)/heat(Ch13)/error → alert
⭐ debug "ค้นไม่เจอ" playbook: index? model? chunk? score? FTS? RRF/rerank? (6 ชั้น)
privacy (Ch27): local log ในเครื่อง / redact+trace_id ไม่ใช่ content
```
**ถัดไป Ch55:** access control at retrieval — multi-tenant filter, row-level security, ทำไม filter ก่อน/หลัง ANN ต่างกัน (pre vs post filtering)
---
*grounded: OpenTelemetry (log/metric/trace) · retrieval debug playbook · เชื่อม Ch4/6/11/12/13/18/27/31/32/34/44/51/53 · /loop deep iter 2026-07-16*
