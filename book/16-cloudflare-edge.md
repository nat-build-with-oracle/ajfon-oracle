# บทพิเศษ (Extras) — Vector Search ที่ Edge: Cloudflare Workers AI + Vectorize

> ภาคพิเศษ · notebook `ch16_cloudflare_edge.ipynb` · grounded ใน `arra-oracle-v3/src/vector/adapters/cloudflare-vectorize.ts`

บท 1–15 รันในเครื่องเรา · บทนี้เอาแนวคิดเดิม **ขึ้น edge ของ Cloudflare** (300+ เมือง)
โมเดลตัวเดิม (bge-m3, 1024 มิติ) แค่ย้ายที่รัน

## X.1 Embedding ที่ edge — Workers AI
endpoint จริง (cloudflare-vectorize.ts:53):
```
POST https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/baai/bge-m3
```
bge-m3 ตัวเดียวกับ local — รันบน GPU ของ Cloudflare แทน Ollama

## X.2 Vectorize — เก็บ+ค้นเวกเตอร์ที่ edge (v2 REST)
```
POST .../vectorize/v2/indexes/{index}/upsert   # NDJSON, batch ≤1000
POST .../vectorize/v2/indexes/{index}/query    # {vector, topK, returnMetadata}
```
⚠️ index สร้างผ่าน wrangler/dashboard ไม่ใช่ runtime (comment จริง:149)

## X.3 หัวใจ — ความรู้ portable
โมเดล + สมการ (cosine) + hybrid + threshold + RAG — เหมือนกันทุกอย่างระหว่าง local กับ edge
edge เปลี่ยนแค่ **ที่รัน** (เครื่องเรา → 300+ เมือง) กับ **transport** (REST แทน local call)

| | Local (บท 1–15) | Edge (บทนี้) |
|---|---|---|
| embed | Ollama bge-m3 | Workers AI `@cf/baai/bge-m3` |
| store | Chroma/LanceDB | Vectorize v2 |
| เมื่อไหร่ | personal/workshop | global/หลาย user |

เหมือนบท 10 (Chroma↔LanceDB): เปลี่ยน backend ได้ ความรู้ไม่เปลี่ยน

*notebook รันจริงได้ถ้าตั้ง CF_ACCOUNT_ID + CF_API_TOKEN · grounded: deep-technical Ch5/14/69*
