# Deep Technical · Chapter 2 — Embeddings มาจากไหน (Contrastive Training)

> ต่อจาก Ch1 (คณิตของ cosine) · บทนี้ตอบ: *ทำไมข้อความความหมายใกล้กัน → เวกเตอร์ถึงชี้ทิศใกล้กัน?*
> ไม่ใช่เวทมนตร์ — เป็นผลของ **loss function** ที่จงใจดันให้เป็นแบบนั้น

---

## 2.0 pipeline เต็มของ embed(text) → vector

```
"งานวิจัยเบาหวาน"
   │  (1) tokenize
   ▼
[CLS] งาน ##วิจัย เบา ##หวาน [SEP]        ← token ids
   │  (2) transformer encoder (หลาย layer, self-attention)
   ▼
token vectors: h₀ h₁ h₂ … hₗ  (แต่ละตัว ∈ ℝ¹⁰²⁴)
   │  (3) pooling (รวมเป็นเวกเตอร์เดียว)
   ▼
sentence vector  v ∈ ℝ¹⁰²⁴
   │  (4) L2 normalize (optional แต่ทำบ่อย)
   ▼
v̂ = v/‖v‖   (ความยาว = 1)
```

ARRA Oracle เรียกขั้นนี้ผ่าน `OllamaEmbeddings.embed()` (`src/vector/embeddings.ts`) — ยิง HTTP ไป Ollama `/api/embeddings` เป็น batch (ดูโค้ดจริง §2.6)

---

## 2.1 Tokenization — ข้อความ → เลข

โมเดลไม่เห็น "ตัวอักษร" มันเห็น **token id** · bge-m3 ใช้ tokenizer แบบ **subword** (XLM-RoBERTa/SentencePiece) รองรับ 100+ ภาษา

**ทำไม subword ไม่ใช่ทั้งคำ**: คำในโลกมีอนันต์ (โดยเฉพาะไทยที่ไม่เว้นวรรค) — subword แตกคำเป็นชิ้นที่พบบ่อย เช่น `เบาหวาน → เบา + ##หวาน` · vocab จำกัด (~250k) แต่ครอบคลุมทุกคำได้

**สำคัญกับภาษาไทย**: ไทยไม่มี space → tokenizer ต้องแบ่งเอง · นี่คือเหตุผลที่โมเดล multilingual (bge-m3) จำเป็น — โมเดลอังกฤษล้วนจะ tokenize ไทยได้แย่

---

## 2.2 Transformer encoder — ให้ token "มองกันเอง"

แต่ละ layer ทำ **self-attention**: token แต่ละตัวปรับ representation ตัวเองโดยดู token อื่นทั้งประโยค

```
Attention(Q,K,V) = softmax( QKᵀ / √d_k ) V
```
- `Q,K,V` = projection ของ token vectors (query/key/value)
- `QKᵀ` = ทุก token ถามทุก token ว่า "เกี่ยวกันแค่ไหน" (นี่ก็ dot product อีกแล้ว! — Ch1)
- `/√d_k` = scale กัน gradient ระเบิด
- softmax → น้ำหนัก → ถ่วงรวม V

หลายสิบ layer ซ้อนกัน → token vector สุดท้ายเข้ารหัส "ความหมายในบริบท" · คำว่า "เบา" ในบริบท "เบาหวาน" จะได้เวกเตอร์ต่างจาก "เบา" ในบริบท "เสียงเบา"

---

## 2.3 Pooling — หลาย token vector → เวกเตอร์เดียว

3 วิธีหลัก:
- **CLS pooling**: ใช้เวกเตอร์ของ token `[CLS]` ตัวแรก (BERT ดั้งเดิม)
- **Mean pooling**: เฉลี่ยทุก token vector `v = (1/L)Σhᵢ` (นิยมสุดในโมเดล sentence-embedding)
- **Last-token**: ใช้ token สุดท้าย (โมเดล decoder เช่น qwen3-embedding)

bge-m3 คืน **dense vector** จาก pooling + ยังทำ **sparse** (คำสำคัญแบบ BM25-like) + **ColBERT** (multi-vector) ได้ในตัว — เรียก "multi-functionality" · ARRA ใช้ dense เป็นหลัก (เข้า LanceDB)

---

## 2.4 หัวใจ: ทำไม "ความหมายใกล้ → เวกเตอร์ใกล้"

คำตอบ = **โมเดลถูกฝึกด้วย loss ที่บังคับให้เป็นแบบนั้น** ผ่าน **contrastive learning**:

ไอเดีย: เอาคู่ข้อความ
- **positive pair** (q, k⁺): ความหมายควรใกล้ (เช่น คำถาม + เอกสารที่ตอบได้)
- **negative pairs** (q, k⁻): ความหมายควรไกล (เอกสารสุ่ม/ไม่เกี่ยว)

แล้ว **ดันให้ cos(q,k⁺) สูง, cos(q,k⁻) ต่ำ**

---

## 2.5 InfoNCE loss — สมการที่ปั้น embedding space

```
                    exp( sim(q, k⁺) / τ )
L = − log ─────────────────────────────────────
             Σⱼ  exp( sim(q, kⱼ) / τ )
```
- `sim` = cosine similarity (Ch1!) · `τ` (tau) = temperature (~0.05) ปรับความคมของ softmax
- ตัวเศษ = คะแนนของคู่ที่ควรใกล้ · ตัวส่วน = รวมทุกคู่ (positive + negatives)
- minimize L = ทำให้ positive เด่นเหนือ negatives → **แยกความหมายในปริภูมิ**

**อ่านเป็นภาษาคน**: "จากตัวเลือกทั้งหมด จงเลือกคู่ที่ความหมายตรงกันให้ได้" — ทำซ้ำล้านคู่ → space ที่ระยะ = ความหมาย

**เชื่อมกลับ Ch1**: หลังฝึกเสร็จ `cos(q, doc)` สูง ⟺ ความหมายใกล้ — เพราะ loss จับมันมาผูกกันตอน train · ตอน inference เราแค่คำนวณ cosine (สมการ 1.4) แล้วเชื่อผลได้

**negatives สำคัญมาก**: "hard negatives" (ใกล้แต่ผิด) ทำให้โมเดลคมกว่า random negatives — bge-m3 ใช้ mining hard negatives + distillation จาก reranker

---

## 2.6 โค้ดจริง — embed batch + retry (embeddings.ts)

```ts
async embed(texts: string[], type?: EmbedType): Promise<number[][]> {
  const prepared = texts.map(text => this.prepareText(text, type));
  const embeddings: number[][] = [];
  for (let i = 0; i < prepared.length; i += this.batchSize) {   // batch = 50
    const batch = prepared.slice(i, i + this.batchSize);
    const data = await this.embedBatchWithRetry(batch);          // attempts = 3
    embeddings.push(...data.embeddings);
    if (!this._dimensionsDetected && data.embeddings[0]?.length > 0) {
      this.dimensions = data.embeddings[0].length;               // auto-detect dim จริง
      this._dimensionsDetected = true;
    }
  }
  return embeddings;
}
```
ประเด็น production จริง:
- **batchSize 50** — embed ทีละ 50 ข้อความ (คุม memory/latency) `ORACLE_EMBED_BATCH_SIZE`
- **retry 3 ครั้ง** delay 150ms — embedder ล่มชั่วคราวไม่ทำทั้ง job พัง `ORACLE_EMBED_ATTEMPTS`
- **timeout 30s** `ORACLE_EMBED_TIMEOUT_MS`
- **dimension auto-detect** — ไม่เชื่อ KNOWN_DIMS ตายตัว วัดจากผลจริง (กัน dim mismatch → LanceDB reject)
- **prepareText(text, type)** — bge-m3/e5 ต้องเติม prefix เช่น `query:` / `passage:` (asymmetric) → query กับ document ฝังคนละแบบ สำคัญมากกับ recall

---

## 2.7 Query vs Document เป็นคนละ embed (asymmetric)

โมเดลอย่าง e5/bge เติม instruction ต่างกัน:
- document: `"passage: งานวิจัยเบาหวาน..."`
- query: `"query: เบาหวานรักษายังไง"`

→ ฝังคนละปริภูมิย่อยแต่ align กันตอน train · ถ้าสลับ prefix ผิด recall ตก · `EmbedType` ในโค้ด (`prepareText(text, type)`) จัดการตรงนี้

---

## สรุป Ch2
```
tokenize → transformer(self-attention) → pool → normalize → vector
   แล้ว "ความหมายใกล้=เวกเตอร์ใกล้" มาจาก InfoNCE loss (contrastive) ตอน train
   ตอน inference: แค่ cosine (Ch1) ก็เชื่อได้
```
**ถัดไป Ch3:** ANN indexing — มี 35,164 เวกเตอร์ 1024 มิติ จะหา nearest ยังไงไม่ให้ช้า O(n·d) ทุก query (HNSW graph, IVF-PQ, LanceDB)

---
*grounded: src/vector/embeddings.ts (batch/retry/dim-detect/prepareText) · bge-m3 (BAAI, multilingual/multi-func) · InfoNCE (Oord et al., van den Oord 2018) · /loop deep iter 2026-07-13*
