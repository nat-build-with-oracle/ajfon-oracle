# Deep Technical · Chapter 14 — Cloudflare Vectorize + D1 (Edge Data Plane)

> ต่อจาก Ch13 · Ch5 บอกว่า edge-native = Workers AI (embed) + Vectorize (vector) + D1 (docs) · บทนี้ลง 2 ตัวหลังลึก

---

## 14.0 ภาพรวม: data plane ย้ายจากเครื่องขึ้น edge

```
local (เดิม):   Bun ─ SQLite (docs) ─ LanceDB (vectors) ─ Ollama (embed)
edge (ใหม่):    Worker ─ D1 (docs) ─ Vectorize (vectors) ─ Workers AI (embed)
```
`ORACLE_STORAGE_BACKEND=d1`, `ORACLE_VECTOR_BACKEND=cloudflare-vectorize` (package.json, Ch5)

---

## 14.1 D1 — SQLite ที่ edge

D1 = **SQLite** ของ Cloudflare (รันบน Durable Object / storage layer):
- ภาษาเดียวกับ local (SQLite) → migration schema ตรงไปตรงมา — ตารางเดิม (documents, FTS5) ย้ายได้
- **FTS5 support**: D1 รองรับ FTS5 → **lexical leg (Ch4) ทำงานบน edge ได้** (BM25 ยังอยู่)
- distributed read replicas → อ่านใกล้ผู้ใช้ · write ไป primary
- limits: ขนาด DB + query time มี cap (managed) → เหมาะ metadata/docs ไม่ใช่ blob ใหญ่

**สำคัญ**: D1 = SQLite ⟹ **FTS5 floor (Ch4 §4.0) ยังทำงานที่ edge** → แม้ Vectorize ล่ม ก็ degrade เป็น FTS5 ได้เหมือน local (graceful degradation architecture ยกมาทั้งชุด)

---

## 14.2 Vectorize — managed ANN index

Vectorize = vector database ของ CF (แทน LanceDB):
- เก็บ `(id, vector, metadata)` · ทำ ANN (Ch3) ให้เอง — เราไม่ต้อง build/tune index เอง
- query: ส่ง query vector → คืน top-k ตาม metric ที่ตั้ง (cosine/euclidean/dot-product)
- **dimension ต้อง fix ตอนสร้าง index** = 1024 (ตรงกับ bge-m3, Ch5 CF_DIMENSIONS) → เปลี่ยนโมเดล = สร้าง index ใหม่
- metadata filtering: filter ก่อน/หลัง ANN (เช่น เฉพาะ doc_type=learning)

---

## 14.3 upsert / query flow (เทียบ local)

**Index (ingest)**:
```
1. embed(text) → vector           Workers AI @cf/baai/bge-m3  (Ch5)
2. Vectorize.upsert({id, vector, metadata})
3. D1.insert(documents row)        (metadata/text จริง)
```
**Query**:
```
1. embed(query) → qvec            Workers AI
2. matches = Vectorize.query(qvec, topK, filter)
3. D1.select docs โดย matches.ids  → เอา text จริง
4. + FTS5 leg (D1) → RRF fuse (Ch4/11)
```

→ `cloudflare-vectorize.ts` (Ch5) มี adapter ที่ห่อ REST/binding พวกนี้ให้ interface เดียวกับ LanceDB → **caller ไม่รู้ว่าอยู่ edge หรือ local** (adapter pattern, Ch4 §4.1)

---

## 14.4 Vectorize internals (ที่รู้เชิงสถาปัตยกรรม)

- index แบบ ANN (คล้าย HNSW/IVF ตระกูล Ch3) — CF จัดการ construction/serving เอง
- **eventual consistency** ในการ upsert: เพิ่ง upsert อาจยังไม่ query เจอทันที (async index build) → ต่างจาก LanceDB local ที่ write-then-read เห็นเลย · **implication**: bulk index แล้วต้องรอ index settle ก่อนวัด parity (Ch6 drift)
- **limits**: จำนวน vector/index, dimension, metadata size มี cap (managed tier) → ต้องเช็คกับปริมาณ 35k+ docs

---

## 14.5 เทียบ LanceDB (local) vs Vectorize (edge)

| | LanceDB (local) | Vectorize (edge) |
|---|---|---|
| ที่อยู่ | ดิสก์เครื่อง (Lance columnar) | CF managed |
| index | เรา build/tune (IVF-PQ) | CF จัดการ |
| consistency | read-after-write ทันที | eventual |
| embed | ต้องมี embedder local/remote | Workers AI ในตัว |
| cost | เครื่อง (fixed) | per-op (variable) |
| data | อยู่ในเครื่อง 100% (privacy) | อยู่ CF cloud ⚠️ |
| offline | ✅ | ❌ ต้องเน็ต |

**⚠️ ประเด็น privacy สำคัญ**: จุดขายหลักของ ARRA คือ "data อยู่ในเครื่อง 100%" (Ch positioning) · ย้ายขึ้น Vectorize = data ออกไป CF → **ขัดจุดขาย** · trade-off จริง: edge เร็ว/ไม่ต้อง GPU แต่เสีย privacy story → อาจใช้ **hybrid**: sensitive vault = local, sharable = edge

---

## 14.6 เชื่อม migration path (Ch5)

```
1. ได้ CLOUDFLARE_API_TOKEN (#2680)
2. สร้าง Vectorize index (dim=1024, cosine)
3. bulk: embed docs ด้วย Workers AI → upsert Vectorize + D1
4. รอ index settle (eventual consistency §14.4)
5. drift benchmark (Ch6 §6.6): parity@k เทียบ local
6. ผ่าน → route ORACLE_VECTOR_BACKEND=cloudflare-vectorize
```
= ~1 team-session validation ที่ Ch5 พูดถึง

---

## สรุป Ch14
```
D1 = SQLite@edge → docs + FTS5 floor (graceful degradation ยกมาได้)
Vectorize = managed ANN → upsert(id,vec,meta)/query(qvec,topK,filter), dim fix 1024
eventual consistency (ต่าง LanceDB read-after-write) → รอ settle ก่อนวัด parity
adapter pattern ซ่อน local-vs-edge จาก caller
⚠️ privacy trade-off: edge เร็ว/no-GPU แต่ data ออกเครื่อง → ขัดจุดขาย → hybrid
```
**ถัดไป Ch15:** MCP transport — muninn_search เดินทางจาก Claude Code ไป backend :47778 ยังไง (stdio vs Streamable HTTP /mcp), embedded mode, auth

---
*grounded: package.json bindings (D1/Vectorize/AI) · src/vector/adapters/cloudflare-vectorize.ts · Cloudflare D1/Vectorize architecture · เชื่อม Ch3/Ch4/Ch5/Ch6 · /loop deep iter 2026-07-13*
