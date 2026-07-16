# Deep Technical · Chapter 5 — Cloudflare Edge Embeddings + Vectorize

> ต่อจาก Ch4 · บทนี้: ย้าย embedding จาก "เครื่องแรงในบ้าน (Ollama)" ขึ้น **edge** — ไม่ต้องมี GPU local
> grounded: `src/vector/adapters/cloudflare-vectorize.ts`, `package.json` cloudflare bindings, decision doc `ψ/outbox/2026-07-06_cf-strategy`

---

## 5.0 ทำไมต้องย้าย (สรุปจาก Ch ecosystem)

คอขวดจริง = **embedding ตอน bulk indexing** (embed พันๆ docs = กิน CPU/GPU) · Ollama ต้องรันตลอด กินเครื่อง → Nat สั่งปลดถาวร · ตอนนี้ vector = ปิด, FTS5 ทำงาน (Ch4 §4.2)

**ทางกลับ**: embed บน Cloudflare Workers AI — จ่ายเป็น request ไม่ต้องมี GPU · เก็บ vector บน Cloudflare Vectorize (managed) แทน LanceDB local

---

## 5.1 CloudflareAIEmbeddings — โค้ดจริง

`src/vector/adapters/cloudflare-vectorize.ts`:
```ts
const CF_MODEL = '@cf/baai/bge-m3';   // ตัวเดียวกับ local! (multilingual)
const CF_DIMENSIONS = 1024;           // ตรงกับ bge-m3 local → parity ได้

export class CloudflareAIEmbeddings implements EmbeddingProvider {
  readonly dimensions = CF_DIMENSIONS;
  constructor(config) {
    this.accountId = config.accountId || process.env.CLOUDFLARE_ACCOUNT_ID || '';
    this.apiToken  = config.apiToken  || process.env.CLOUDFLARE_API_TOKEN  || '';
    if (!this.accountId || !this.apiToken) { /* ต้องมี token → นี่คือ #2680 */ }
  }
  // embed → POST REST
  //   https://api.cloudflare.com/client/v4/accounts/{accountId}/ai/run/@cf/baai/bge-m3
}
```

**จุดสำคัญ:**
- ใช้ **โมเดลเดียวกับ local** (`@cf/baai/bge-m3`, 1024 มิติ) → เวกเตอร์ควร "ใกล้เคียง" ของเดิม → migrate ได้โดยไม่ re-embed ทุกอย่าง (ในทางทฤษฎี — ต้องพิสูจน์ด้วย drift, §5.4)
- implement `EmbeddingProvider` เดียวกับ Ollama → **เสียบเข้า fallback chain (Ch4 §4.2) ได้ทันที** = adapter pattern จ่ายผลตรงนี้
- บล็อกที่ **CLOUDFLARE_API_TOKEN** (issue #2680) — โค้ดพร้อม รอ credential ตัวเดียว

---

## 5.2 สองโหมดของ CF (สำคัญ — คนละ runtime)

**โหมด A · Workers AI binding (native, in-worker)**
- โค้ดรันบน CF Worker → เรียก `env.AI.run('@cf/baai/bge-m3', {text})` ผ่าน **binding** (ไม่ผ่าน HTTP ภายนอก)
- `package.json` binding: `"description": "Workers AI binding for edge embeddings..."` + `ORACLE_VECTORIZE` binding
- เร็วสุด (in-datacenter) แต่ต้อง deploy ทั้ง backend เป็น Worker

**โหมด B · Remote API mode (REST จาก Bun origin)**
- Bun origin (เครื่อง/VPS) เรียก CF REST `POST /accounts/{id}/ai/run/{model}` ด้วย API token
- ไม่ต้อง deploy เป็น Worker — เครื่องเดิม + embed ที่ edge
- ช้ากว่าโหมด A (มี network hop) แต่ integrate ง่ายกับ stack ปัจจุบัน

→ `cloudflare-vectorize.ts` มีทั้ง `CloudflareAIEmbeddings` (embed) และ Vectorize adapter (storage) แยกกัน → ผสมได้ (embed CF + เก็บ LanceDB, หรือ embed CF + เก็บ Vectorize)

---

## 5.3 Vectorize — vector storage บน edge

แทน LanceDB local ด้วย **Cloudflare Vectorize** (managed ANN index):
- `ORACLE_VECTOR_BACKEND=cloudflare-vectorize` → "avoid local SQLite/vector files at the edge" (package.json:59)
- Vectorize ทำ ANN (Ch3) ให้เอง — เราแค่ upsert เวกเตอร์ + query
- คู่กับ **D1** (SQLite ของ CF) สำหรับ metadata/documents (`ORACLE_STORAGE_BACKEND=d1`)

**สถาปัตยกรรม edge-native เต็ม**: Workers AI (embed) + Vectorize (vector) + D1 (docs) = ไม่มี data plane ในเครื่องเลย · แต่ = "less-traveled path" (Ch ecosystem: ไม่เคย deploy end-to-end)

---

## 5.4 ⚠️ Drift — ทำไม "ใส่ token 5 นาที" ≠ พร้อมใช้

โมเดลชื่อเดียวกัน (`bge-m3`) แต่ **local Ollama vs CF Workers AI อาจให้เวกเตอร์ไม่เหมือนเป๊ะ**:
- version/quantization ต่างกัน (CF อาจ quantize ต่างจาก Ollama)
- pooling/normalization ต่างกันเล็กน้อย

ถ้า index เดิม (embed ด้วย Ollama) แล้ว query ด้วย CF → เวกเตอร์อยู่คนละ "เฉด" → **recall ตกเงียบๆ**

**ทางแก้ = drift benchmark** (PR #2740/#2784 "bge-m3 drift benchmark harness"):
```
1. เลือก ~100 docs
2. embed ด้วย Ollama (เดิม) และ CF (ใหม่)
3. วัด cosine(v_ollama, v_cf) ต่อ doc  → ถ้าใกล้ 1 = drift ต่ำ = ย้ายได้
4. วัด search parity: query เดิม, top-k เหมือนกันแค่ไหน (recall@k เทียบ)
5. ถ้าผ่าน threshold → สลับ · ถ้าไม่ → ต้อง re-embed ทั้งหมดด้วย CF
```
→ นี่คือเหตุผลว่าหลังได้ token ต้อง **~1 team-session validation** ไม่ใช่สลับทันที

---

## 5.5 cost model (ต่างจาก local สิ้นเชิง)

- **local Ollama**: จ่ายด้วย "เครื่องแรง" (GPU/RAM) + ไฟ · fixed cost, embed เท่าไรก็ได้
- **CF Workers AI**: จ่ายต่อ request (neurons) · variable · bulk index 35k docs = ยิง embed 35k ครั้ง → คิดเงิน แต่ไม่ต้องซื้อ GPU
- **hybrid ที่สมเหตุผล**: embed ครั้งแรก (index) อาจทำ local/batch, ส่วน query-time embed (เบา, 1 ครั้ง/query) ยิง CF → ดีที่สุดของสองโลก

---

## สรุป Ch5
```
CloudflareAIEmbeddings (@cf/baai/bge-m3, 1024d) implement EmbeddingProvider
  → เสียบ fallback chain ได้ (Ch4) · บล็อกที่ token #2680
2 โหมด: Workers AI binding (native) vs Remote API (REST จาก Bun)
Vectorize + D1 = edge-native (ไม่มี data plane ในเครื่อง)
"5 นาที" = เปิดประตู · ต้อง drift benchmark (#2740) + parity ก่อนเชื่อ → ~1 team-session
```
**ถัดไป Ch6:** benchmark methodology — drift, recall@k, MRR, nDCG, LoCoMo, latency percentile · วัดคุณภาพ retrieval ยังไงให้เชื่อได้

---
*grounded: src/vector/adapters/cloudflare-vectorize.ts (CF_MODEL/CF_DIMENSIONS/accountId/apiToken/ai-run REST) · package.json cloudflare bindings (AI/ORACLE_VECTORIZE/D1) · PR #2740 #2784 drift harness · issue #2680 · /loop deep iter 2026-07-13*
