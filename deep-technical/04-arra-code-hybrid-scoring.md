# Deep Technical · Chapter 4 — โค้ด ARRA เต็ม + Hybrid Scoring

> ต่อจาก Ch3 · บทนี้ลงโค้ดจริงของ ARRA Oracle: adapter pattern, fallback chain, และ **หัวใจ — hybrid FTS+vector รวมคะแนนด้วย Reciprocal Rank Fusion**
> grounded: `src/vector/fallback-chain.ts`, `src/search/query.ts`, `src/openapi/memory.ts`, `src/mcp/server.ts`

---

## 4.0 สถาปัตยกรรม vector layer (ชั้นๆ)

```
search(query, mode)                         src/search/query.ts   (mode: hybrid|fts|vector)
   │
   ├─ FTS leg   → SQLite FTS5              (คำตรง, ทำงานเสมอ = "floor")
   └─ vector leg
        │  embed(query)                     src/vector/embeddings.ts
        │     └─ EmbeddingFallbackChain     src/vector/fallback-chain.ts
        │           Ollama → Gemini → CF → Remote → None
        │  ANN search                       src/vector/adapters/lancedb.ts (cosine, Ch3)
        ▼
   fuse(fts_results, vector_results)        ← RRF (§4.3) = หัวใจบทนี้
        │
        └─ (optional) rerank                bge-reranker-v2-m3 (§4.5)
```

**หลัก design 2 อย่างที่เห็นในโค้ด:**
1. **FTS5 เป็น floor** — ตอบได้เสมอแม้ vector ล่ม (graceful degradation, `createFtsOnlyVectorStore` ใน mcp/server.ts)
2. **default mode = hybrid** — `if (!normalized) return 'hybrid'` (`src/search/query.ts:28`)

---

## 4.1 Adapter Pattern — เปลี่ยน backend ไม่แตะ caller

`src/vector/adapters/` มีหลาย adapter ที่ implement interface เดียวกัน:
```
adapters/lancedb.ts            (local, default)
adapters/cloudflare-vectorize.ts   (edge)
adapters/qdrant.ts             (external vector DB)
adapters/chroma-mcp.ts         (ChromaDB via MCP)
adapters/proxy.ts              (vector-server แยก process)
adapters/cloudflare-worker.ts  (remote worker)
```
ทุกตัวมี `.search(vec).distanceType('cosine')` แบบเดียวกัน → caller (`src/search/`) ไม่รู้/ไม่สนว่าอยู่ backend ไหน · **สลับด้วย env** (`ORACLE_VECTOR_BACKEND`) ไม่ต้องแก้โค้ด search

> นี่คือเหตุผลที่ย้ายขึ้น Cloudflare Vectorize ได้โดยไม่ rewrite — แค่เปลี่ยน adapter (Ch5)

---

## 4.2 Embedding Fallback Chain — ไม่พึ่ง embedder ตัวเดียว

`EmbeddingFallbackChain` (`fallback-chain.ts`) ห่อ provider หลายตัวเป็นโซ่:
```
Ollama (local) → Gemini (cloud) → Cloudflare AI → RemoteHttp → None(FTS5)
```
คุณสมบัติจากโค้ดจริง:
- **sticky**: ถ้า provider หนึ่งใช้ได้ ก็ใช้ต่อ (ไม่ลองตัวแรกใหม่ทุกครั้ง) — ลด latency
- **backoff**: `initialBackoffMs × backoffFactor^n` (capped `maxBackoffMs`) — provider ล่มแล้วเว้นก่อนลองใหม่
- **onFallback event**: แจ้งเมื่อสลับ provider → observability (#2759)
- **providerStats**: attempts/failures/successes ต่อ provider → เห็นว่าตัวไหนพัง
- ปลายโซ่ = `None` → คืน "ไม่มี vector" → search degrade เป็น FTS5 (ไม่ throw)

**ทำไมสำคัญ**: embedder คือจุดเปราะสุด (Ch ecosystem) · chain ทำให้ระบบ "ไม่ตายทั้งตัวเพราะ embedder ตัวเดียวล่ม" — Ollama ตาย → ลอง Gemini → สุดท้าย FTS5 ยังตอบได้

---

## 4.3 ⭐ Hybrid Scoring — Reciprocal Rank Fusion (RRF)

ปัญหา: FTS คืนคะแนน BM25 (0..∞) · vector คืน cosine distance (0..2) · **สเกลคนละโลก รวมตรงๆ ไม่ได้**

ทางแก้ของ ARRA (เห็นในโค้ดจริง `strategy: 'reciprocal_rank_fusion'`): **ไม่รวมคะแนนดิบ — รวม "อันดับ"**

```
                    1
RRF_score(d) =  Σ  ─────────
               r∈R  k + rankᵣ(d)
```
- `R` = ลิสต์ผลลัพธ์ (FTS list, vector list) · `rankᵣ(d)` = อันดับของ doc d ในลิสต์ r (1 = บนสุด)
- `k` = ค่าคงที่ลดอิทธิพลอันดับต้น (มาตรฐาน = **60**)
- doc ที่ **ติดอันดับดีในหลายลิสต์** → คะแนนรวมสูง

**พิสูจน์จากโค้ดจริง**: `openapi/memory.ts` มีตัวอย่าง `fusedScore: 0.016393`
```
1 / (60 + 1) = 1/61 = 0.016393…   ✓ ตรงเป๊ะ → ยืนยัน k=60, doc อันดับ 1 ในลิสต์เดียว
```

**ทำไม RRF ดีกว่ารวมคะแนนดิบ**:
- ไม่ต้อง normalize สเกล (BM25 vs cosine) — ใช้แค่อันดับ
- robust ต่อ outlier score
- ไม่ต้อง tune น้ำหนักมาก · งานวิจัย (Cormack et al. 2009) แสดงว่า RRF ชนะวิธี fusion ซับซ้อนกว่าบ่อยๆ

---

## 4.4 Confidence-Weighted RRF + Retrieval Heat (ของ ARRA เพิ่มเอง)

ARRA ต่อยอด RRF ธรรมดา (เห็นใน `confidence_weighted_rrf`, `confidenceWeight: 0.25`):
```
final_score(d) = RRF_score(d)
               + confidenceWeight × confidence(d)        (0.25)
               + heat(d)                                 (usage_count, last_accessed_at)
```
- **confidence(d)**: ความมั่นใจของ memory (บาง doc verified มากกว่า)
- **retrieval heat**: doc ที่ถูกเรียกบ่อย/ล่าสุด ดันขึ้น — "memory ที่ใช้บ่อย = น่าจะเกี่ยว" (คล้าย recency+frequency ของสมองคน)
- doc: `"Blends reciprocal-rank fusion with confidence and retrieval heat from usage_count/last_accessed_at"` (openapi/memory.ts:116)

→ นี่คือสิ่งที่ทำให้ ARRA เป็น "second brain" ไม่ใช่แค่ vector DB เปล่า — มันจำว่า**คุณใช้อะไรบ่อย**

---

## 4.5 Reranker — cross-encoder ชั้นสุดท้าย

หลัง RRF ได้ top-N (เช่น 50) → ส่งเข้า **bge-reranker-v2-m3** (`services/reranker-py`, Python sidecar :8765):

**ต่างจาก embedding ยังไง (สำคัญ)**:
- embedding = **bi-encoder**: ฝัง query กับ doc **แยกกัน** แล้ววัด cosine (เร็ว, index ล่วงหน้าได้ แต่หยาบ)
- reranker = **cross-encoder**: ป้อน `[query, doc]` **เข้าโมเดลพร้อมกัน** → attention ข้าม query↔doc เต็ม → คะแนนแม่นกว่ามาก (แต่ช้า ทำ index ล่วงหน้าไม่ได้)

```
pipeline: dense recall (bge-m3, top-50 จาก LanceDB)
          → rerank (cross-encoder ให้คะแนนใหม่)
          → top-5 by cross-encoder score
```
= "หยาบแต่เร็ว" คัดเหลือ 50 → "ละเอียดแต่ช้า" จัดอันดับ 50 ตัวสุดท้าย · best of both

---

## 4.6 mode selection (โค้ดจริง)

`src/search/query.ts`:
```ts
export type SearchMode = 'hybrid' | 'fts' | 'vector';
const SEARCH_MODES = new Set<SearchMode>(['hybrid', 'fts', 'vector']);
// ...
if (!normalized) return 'hybrid';   // default = hybrid
```
- `hybrid` (default): FTS + vector → RRF fuse
- `fts`: FTS5 อย่างเดียว (= สถานะปัจจุบันตอน Ollama retired)
- `vector`: vector อย่างเดียว (debug/เปรียบเทียบ — Playground)

---

## สรุป Ch4
```
adapter pattern → สลับ backend ด้วย env
fallback chain → embedder ล่มไม่ตายทั้งตัว (sticky+backoff, ปลายทาง FTS5)
hybrid scoring → RRF: Σ 1/(k+rank), k=60 (พิสูจน์ด้วย 1/61=0.016393)
   + confidence-weighted + retrieval heat = "second brain"
reranker → cross-encoder จัดอันดับ top-50 ตัวสุดท้าย
```
**ถัดไป Ch5:** Cloudflare Workers AI (@cf/baai/bge-m3) + Vectorize adapter — embed บน edge, ย้าย data plane ขึ้น cloud, drift benchmark

---
*grounded: src/vector/fallback-chain.ts (sticky/backoff/stats) · src/search/query.ts (modes) · src/openapi/memory.ts (RRF confidence heat, fusedScore 0.016393) · services/reranker-py · RRF (Cormack, Clarke, Buettcher 2009) · /loop deep iter 2026-07-13*
