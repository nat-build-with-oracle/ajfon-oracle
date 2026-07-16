# Deep Technical · Chapter 20 — Eval Harness (code walkthrough)

> ต่อจาก Ch19 · Ch6 ให้สมการ metric · บทนี้ลง **โค้ดจริง**ที่รัน benchmark ใน ARRA
> grounded: src/vector/__tests__/benchmark.ts, benchmark-models.ts, benchmark-models-extended.ts

---

## 20.0 ไฟล์ benchmark จริง

```
src/vector/__tests__/benchmark.ts            — เทียบ adapter (ChromaDB vs LanceDB vs Qdrant)
src/vector/__tests__/benchmark-models.ts     — เทียบ embedding model (nomic/bge-m3/qwen3...)
src/vector/__tests__/benchmark-models-extended.ts — ชุดขยาย
```
รัน: `bun run src/vector/__tests__/benchmark.ts`

---

## 20.1 benchmark.ts — วัดอะไร (จาก header จริง)

```
/**
 * Vector DB Benchmark: ChromaDB vs LanceDB vs Qdrant
 * Compares indexing speed, query latency, filtered queries, and result quality.
 */
```
4 มิติ:
1. **indexing speed** — embed+upsert docs เร็วแค่ไหน (คอขวด bulk, Ch ecosystem)
2. **query latency** — ค้น 1 ครั้งกี่ ms (Ch6 §6.7, ควรวัด p50/p99)
3. **filtered queries** — ค้น + metadata filter (เช่น type=principle)
4. **result quality** — ผลถูกไหม (recall/precision, Ch6)

---

## 20.2 Test corpus (30 docs, ของจริง)

```ts
const DOCS: VectorDocument[] = [
  { id: 'p1', document: 'Nothing is deleted. Create new, do not delete...',
    metadata: { type: 'principle', source_file: 'resonance/nothing-deleted.md' } },
  { id: 'l1', document: 'TypeScript Hono API with SQLite FTS5 for full text search...',
    metadata: { type: 'learning', source_file: 'learnings/hono-fts5.md' } },
  // ... principles(10) + learnings(10) + อื่นๆ = 30
];
```
- corpus เล็ก (30) = เร็ว, ทำ CI ได้ · แต่ต้องมี **query→relevant labels** เพื่อวัด quality (Ch6 §6.0)
- ใช้ข้อมูลจริงของ Oracle (principles/learnings) → representative

---

## 20.3 โครง benchmark (pattern ทั่วไป)

```ts
for (const adapter of [chromadb, lancedb, qdrant]) {
  const store = createVectorStore(adapter);          // factory (adapter pattern Ch4)

  // (1) indexing speed
  const t0 = performance.now();
  await store.addDocuments(DOCS);                     // embed + upsert
  const indexMs = performance.now() - t0;

  // (2) query latency + (4) quality
  for (const { query, relevantIds } of TEST_QUERIES) {
    const t1 = performance.now();
    const results = await store.search(query, k);
    const queryMs = performance.now() - t1;
    const recall = recallAtK(results, relevantIds, k);  // Ch6 §6.1
    const mrr    = reciprocalRank(results, relevantIds); // Ch6 §6.3
    record(adapter, { queryMs, recall, mrr });
  }

  // (3) filtered
  await store.search(query, k, { filter: { type: 'principle' } });
}
```

---

## 20.4 metric ในโค้ด (แปลสมการ Ch6 → JS)

```ts
function recallAtK(results, relevantIds, k) {          // Ch6 §6.1
  const top = results.slice(0, k).map(r => r.id);
  const hit = top.filter(id => relevantIds.has(id)).length;
  return hit / relevantIds.size;
}

function reciprocalRank(results, relevantIds) {        // Ch6 §6.3
  const idx = results.findIndex(r => relevantIds.has(r.id));
  return idx === -1 ? 0 : 1 / (idx + 1);               // 1/rank
}

function ndcgAtK(results, relMap, k) {                 // Ch6 §6.4
  const dcg = results.slice(0, k).reduce((s, r, i) =>
    s + (Math.pow(2, relMap[r.id] ?? 0) - 1) / Math.log2(i + 2), 0);
  const ideal = Object.values(relMap).sort((a,b)=>b-a).slice(0, k)
    .reduce((s, rel, i) => s + (Math.pow(2, rel) - 1) / Math.log2(i + 2), 0);
  return ideal === 0 ? 0 : dcg / ideal;                // DCG/IDCG
}
```
(สมการ Ch6 §6.4 → `Math.log2(i+2)` เพราะ i เริ่ม 0 → rank i+1 → log₂((i+1)+1))

---

## 20.5 drift harness (#2740 — Ch5/6)

```ts
// เทียบ embedder เก่า(Ollama) vs ใหม่(CF) บน corpus เดียวกัน
for (const doc of SAMPLE) {
  const vOld = await ollamaEmbed(doc);
  const vNew = await cfEmbed(doc);
  driftScores.push(1 - cosine(vOld, vNew));            // Ch6 §6.6 embedding drift
}
const meanDrift = mean(driftScores);

// retrieval parity
for (const q of QUERIES) {
  const topOld = searchWith(vOld_index, q, k);
  const topNew = searchWith(vNew_index, q, k);
  parity.push(intersect(topOld, topNew).length / k);   // parity@k
}
// gate: meanDrift < ε AND meanParity > threshold → ปลอดภัยสลับ
```

---

## 20.6 CI integration (ทำไมสำคัญ)

- benchmark เล็ก (30 docs) → รันใน CI ทุก PR ที่แตะ vector → **จับ regression** (เช่น #2717 unify cosine ถ้าพังจะเห็นทันที)
- assertion: `expect(recall).toBeGreaterThan(0.9)` → PR ที่ทำ recall ตก = fail
- นี่คือเหตุผลมี `benchmark-models.ts` เป็น test ไม่ใช่ script เดี่ยว → คุณภาพ retrieval เป็น **contract** ที่ CI บังคับ

---

## 20.7 อ่าน output ยังไง

```
adapter    index(ms)  p50(ms)  p99(ms)  recall@10  mrr   nDCG@10
LanceDB    120        3        12       0.95       0.88  0.91
Qdrant     180        5        20       0.95       0.87  0.90
ChromaDB   200        8        35       0.93       0.85  0.88
```
- ดู trade-off: LanceDB index เร็ว + latency ต่ำ (เหตุผลเป็น default, Ch3 §3.6)
- **อย่าดู mean latency** — ดู p99 (tail, Ch6 §6.7)
- recall เท่ากันแต่ latency ต่าง → เลือกตัวเร็ว

---

## สรุป Ch20
```
benchmark.ts: เทียบ adapter (LanceDB/Qdrant/Chroma) 4 มิติ (index/latency/filter/quality)
corpus 30 docs จริง (principles/learnings) + query→relevant labels
metric ในโค้ด: recallAtK/reciprocalRank/ndcgAtK = สมการ Ch6 แปลเป็น JS
drift harness (#2740): 1−cos(old,new) + parity@k → gate การสลับ CF
CI: recall เป็น contract (expect > 0.9) → จับ regression ทุก PR
```
**ถัดไป Ch21:** positional encoding ลึก (sinusoidal derivation, RoPE rotation math, ทำไม RoPE generalize context ยาว) + ผลต่อ long-doc embedding

---
*grounded: src/vector/__tests__/benchmark.ts (header, 30-doc corpus จริง) · benchmark-models.ts · factory.ts (createVectorStore) · เชื่อม Ch3/4/5/6 · /loop deep iter 2026-07-13*
