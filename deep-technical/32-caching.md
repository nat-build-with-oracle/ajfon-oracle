# Deep Technical · Chapter 32 — Caching

> ต่อจาก Ch31 · vector search มีหลายชั้นที่ cache ได้ · บทนี้: cache อะไร, invalidate ยังไง, semantic cache

---

## 32.0 จุดที่ cache ได้ (pipeline Ch4/15)

```
query → embed(query) ──────────── (1) embedding cache
      → ANN search ──────────────── (2) result cache
      → rerank ─────────────────── (3) rerank cache
      → LLM synthesize ─────────── (4) answer cache (แพงสุด)
```

---

## 32.1 Embedding cache — อย่า embed ซ้ำ

```
cache[hash(text)] = vector
```
- **document side**: embed doc ครั้งเดียวตอน index (Ch2) — เป็น cache โดยธรรมชาติ (เก็บใน vector DB)
- **query side**: query ซ้ำ (คนถามเหมือนกัน) → cache vector → ข้าม embed
- key = hash(normalized text) · invalidate เมื่อเปลี่ยน embedder (Ch5 — เวกเตอร์เก่าใช้ไม่ได้)
- ประหยัดสุดตอน embed แพง (CF per-neuron, Ch24)

---

## 32.2 Result cache — query→results

```
cache[hash(query + filter + k)] = [doc_ids...]
```
- query เดิม + index เดิม → ผลเดิม → คืน cache ตรงๆ
- **hit rate**: query จริงมี long-tail (ซ้ำน้อย) → hit rate อาจต่ำ · แต่ "query ยอดฮิต" ซ้ำบ่อย → cache คุ้ม
- TTL สั้น หรือ invalidate ตอน index เปลี่ยน (§32.4)

---

## 32.3 ⭐ Semantic cache — query "คล้าย" ก็ hit

ต่างจาก exact cache: query ไม่ต้องเหมือนเป๊ะ แค่**ความหมายใกล้**:
```
1. embed(query_new)
2. ค้นใน cache ของ query เก่า (ด้วย cosine! Ch1)
3. ถ้า cos(query_new, query_cached) > threshold (เช่น 0.95)
   → คืนผลของ query_cached (ถือว่าเหมือนกัน)
```
- "เบาหวานรักษายังไง" กับ "วิธีรักษาเบาหวาน" → cosine สูง → hit เดียวกัน → ข้าม search/LLM
- **ใช้ vector search มา cache vector search** (recursive!) · threshold สำคัญ: สูงไป=ไม่ hit, ต่ำไป=คืนผิด
- ประหยัดมากตอน LLM synthesis แพง (Ch24 §24.6) — query คล้ายไม่ต้องเรียก LLM ใหม่

---

## 32.4 Cache Invalidation — ปัญหาคลาสสิก

"There are only two hard things: cache invalidation and naming things"

index เปลี่ยน (upsert/delete doc) → cache เก่าอาจผิด:
```
strategy:
- TTL: cache หมดอายุเอง (ง่าย แต่ผลเก่าค้างชั่วคราว)
- versioned key: cache key รวม index_version → upsert = bump version = cache เก่า miss หมด
- selective: รู้ว่า doc ไหนเปลี่ยน → invalidate เฉพาะ query ที่แตะ doc นั้น (ยาก)
```
- ARRA: memory เพิ่มบ่อย (write-heavy) → aggressive invalidation หรือ TTL สั้น · หรือ versioned key ตอน bulk index
- eventual consistency (Ch14) ยิ่งซับซ้อน: edge cache อาจเห็น index เวอร์ชันต่างกัน

---

## 32.5 Heat model = cache policy (เชื่อม Ch13)

Ch13 retrieval heat = LRU+LFU · **นี่คือ cache eviction policy โดยตรง**:
```
ถ้ามอง vector DB เป็น "cache ของความรู้":
  heat สูง (ใช้บ่อย/ล่าสุด) = keep hot (index ใน RAM, priority)
  heat ต่ำ (ไม่ใช้นาน) = evict to cold storage (disk/archive)
→ tiered storage: hot vectors ใน RAM (HNSW), cold บนดิสก์ (Ch25 §25.0 1B+ tier)
```
= heat model (Ch13) ทำ double duty: ranking prior **และ** cache/tier policy

---

## 32.6 ARRA caching reality

- 35k docs = เล็ก → index ทั้งหมดอยู่ RAM/mmap ได้ (ไม่ต้อง tier)
- query cache: single-user → query ซ้ำน้อย → semantic cache คุ้มกว่า exact (query paraphrase)
- **โอกาส**: semantic cache สำหรับ oracle_ask (LLM แพง) → query คล้ายไม่เรียก LLM ซ้ำ = ประหยัด token (Ch24)

---

## สรุป Ch32
```
cache ได้ 4 ชั้น: embedding / result / rerank / answer(แพงสุด)
embedding cache: doc=index-time (ธรรมชาติ), query=hash · invalidate เมื่อเปลี่ยน embedder
semantic cache: query คล้าย (cosine>threshold) → hit เดียวกัน = vector search cache vector search
invalidation: TTL / versioned key / selective (write-heavy ARRA → TTL สั้น)
heat (Ch13) = cache policy: hot RAM, cold disk (tiered, Ch25)
```
**ถัดไป Ch33:** graph & temporal memory — knowledge graph retrieval, temporal reasoning (asOf), เทียบ vector vs graph (Ch data-pack: GraphRAG)
---
*grounded: semantic cache (GPTCache) · cache invalidation · เชื่อม Ch1 (cosine), Ch13 (heat=policy), Ch14 (eventual), Ch24 (LLM cost), Ch25 (tier) · /loop deep iter 2026-07-14*
