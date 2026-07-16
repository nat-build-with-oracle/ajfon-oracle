# Deep Technical · Chapter 24 — Cost Model

> ต่อจาก Ch23 · vector search "ราคาเท่าไร" — local vs cloud คิดคนละแบบสิ้นเชิง · บทนี้: แจกแจงต้นทุนจริง

---

## 24.0 3 ก้อนต้นทุน

```
1. Embedding   — แปลงข้อความเป็นเวกเตอร์ (compute-heavy, Ch2/16)
2. Storage     — เก็บเวกเตอร์ + index (Ch3/8)
3. Query       — ค้น (embed query + ANN, เบา)
```
โครงสร้างต้นทุนต่างกันมากระหว่าง **local (fixed)** กับ **cloud (variable)**

---

## 24.1 Local — fixed cost

- **embedding**: ฟรีต่อ request (จ่ายด้วยเครื่อง) · แต่ต้องมี GPU/RAM แรง — bulk index กิน (Ch ecosystem คอขวด)
- **storage**: ดิสก์เครื่อง · 1024-dim float32 = 4KB/vec × 35k = 140MB (ถูกมาก) · 1M = 4GB
- **cost จริง**: ค่าเครื่อง (amortized) + ไฟ + เวลา setup/maintain · **fixed** — embed เท่าไรก็ราคาเดิม
- ✅ คุ้มถ้าใช้เยอะสม่ำเสมอ · ❌ ต้องลงทุน HW ก่อน + maintain เอง

---

## 24.2 Cloud (CF Workers AI) — per-request

- **embedding**: จ่ายต่อ **neuron** (หน่วยคิดเงินของ Workers AI) · bulk index 35k docs = ยิง embed 35k ครั้ง = คิดเงินตามปริมาณ
- **storage (Vectorize)**: จ่ายต่อจำนวน vector เก็บ + query · **D1**: จ่ายต่อ row read/write
- **cost จริง**: variable — ไม่ใช้ = ไม่จ่าย, ใช้เยอะ = จ่ายเยอะ · ไม่ต้องซื้อ GPU
- ✅ ไม่ต้องลงทุน HW, scale อัตโนมัติ · ❌ recurring, แพงถ้า volume สูงมาก + data ออกเครื่อง (Ch14 privacy)

---

## 24.3 Embedding cost — index vs query (สำคัญ)

```
index-time:  embed ทุก doc ครั้งเดียว (+ re-embed ถ้าเปลี่ยนโมเดล) → BULK, แพง
query-time:  embed แค่ query (1 ข้อความสั้น) ต่อการค้น → เบา, ถูก
```
- **key insight** (Ch ecosystem): คอขวด = index-time (bulk) · query-time เบามาก
- **hybrid cost strategy**: index แบบ batch (local/cheap หรือ off-peak) ครั้งเดียว · query-time ยิง CF (เบา, 1/query) → ได้ semantic โดยไม่ต้องมี GPU รันตลอด (แก้ปัญหา Ollama กินเครื่อง โดยไม่จ่าย bulk-embed บน cloud แพง)

---

## 24.4 ตัวอย่างตัวเลขจริง (จาก data pack)

mem0 เผยเอง:
```
naive (dump 100K-token context ทุก query) = $90/เดือน  @ 10k queries/day
mem0 (selective retrieval)                = $1.80/เดือน  @ เท่ากัน
```
→ **retrieval ประหยัด ~50×** เทียบยัด context ทั้งหมด · เพราะส่ง LLM แค่ chunk ที่เกี่ยว ไม่ใช่ทั้ง corpus
- Obsidian+Ollama local: อ้างแทน subscription tool $500+/ปี (จ่ายด้วยเครื่องแทน)

**บทเรียน**: ต้นทุนใหญ่จริงมักไม่ใช่ vector DB — แต่คือ **token ที่ยัดเข้า LLM** · retrieval ที่ดี = ส่งน้อย = ประหยัด LLM cost มหาศาล (นี่คือคุณค่าเชิงเงินของ second brain)

---

## 24.5 Storage cost breakdown

```
vector (float32):  d × 4 bytes/vec       1024-dim = 4KB
  + quantized (Ch8): PQ 8 bytes (512×), BQ 128 bytes (32×), SQ 1KB (4×)
index overhead:    HNSW ~ M×edges (RAM เยอะ) · IVF-PQ (ดิสก์, เบา)
metadata (D1/SQLite): text จริง + FTS5 index
```
→ 35k docs: vectors 140MB + FTS index + metadata = รวมไม่กี่ร้อย MB (เบามาก) · scale ปัญหาเริ่มที่ 1M+ → quantize (Ch8)

---

## 24.6 Query cost anatomy

```
1 query = embed(query)        [CF: 1 neuron call | local: ~ฟรี]
        + ANN search          [O(log n), เบา]
        + rerank top-50       [cross-encoder 50 forward, ถ้าเปิด = แพงสุดใน query]
        + LLM synthesize      [token cost = ก้อนใหญ่สุด ถ้า oracle_ask]
```
→ ในทาง cost, **reranker + LLM synthesis** แพงกว่า vector search เอง · ปิด reranker (Ch18 §18.7) เมื่อไม่ต้องการ precision สูง = ประหยัด

---

## 24.7 สรุปการเลือก (decision)

| สถานการณ์ | เลือก |
|---|---|
| ใช้หนัก สม่ำเสมอ มี HW | local (fixed ถูกกว่าระยะยาว) |
| ใช้เบา/ไม่แน่นอน ไม่อยากลงทุน HW | CF (per-use) |
| แก้ Ollama กินเครื่อง | hybrid: index local/batch + query CF |
| privacy สำคัญ (Ch14) | local (data ในเครื่อง) |
| ต้องประหยัด LLM cost | retrieval ดี → ส่ง token น้อย (สำคัญสุด) |

---

## สรุป Ch24
```
3 ก้อน: embedding (หนัก, index-time bulk เป็นคอขวด) · storage (เบา, quantize ถ้าโต) · query (เบา)
local = fixed (เครื่อง/ไฟ) · CF = variable (per-neuron/vector) + data ออกเครื่อง
hybrid: index batch local + query CF = semantic ไม่ต้อง GPU ตลอด ไม่จ่าย bulk cloud
ต้นทุนใหญ่จริง = token เข้า LLM (mem0 $90→$1.80, 50×) → retrieval ดี = ประหยัด LLM
```
**ถัดไป Ch25:** scaling & sharding — จาก 35k → 1M → 100M docs, partition, distributed ANN, replica

---
*grounded: Ch2/16 (embed cost), Ch8 (quant storage), Ch14 (CF cost), data-pack (mem0 $90/$1.80, Obsidian $500) · เชื่อม Ch ecosystem (index bottleneck) · /loop deep iter 2026-07-13*
