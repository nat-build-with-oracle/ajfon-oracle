# Deep Technical · Chapter 15 — MCP Transport (Claude Code → :47778)

> ต่อจาก Ch14 · vector search เก่งแค่ไหนก็ต้อง "ถึงมือ agent" · บทนี้: muninn_search เดินทางจาก Claude Code ไป backend ยังไง
> grounded: src/mcp/server.ts, src/mcp/fts-only-vector-store.ts, ecosystem (3 transports, #2759/#2760)

---

## 15.0 MCP คืออะไร (ในบริบทนี้)

Model Context Protocol = มาตรฐานให้ LLM agent เรียก "tool/data source" ภายนอก · Claude Code เห็น `muninn_search`, `oracle_ask`, `muninn_stats` เป็น MCP tool → เรียกได้เหมือนฟังก์ชัน · backend ARRA เป็น **MCP server** ที่ expose tool เหล่านี้

---

## 15.1 สาม transport (ARRA ship ครบ — Ch ecosystem)

**(1) stdio** — คลาสสิก
```
claude ─ spawn ─→ `bin/arra mcp` (subprocess)
        │   JSON-RPC ผ่าน stdin/stdout
```
- Claude Code รัน process ลูก, คุยผ่าน pipe · ไม่มี network, local เท่านั้น
- config ใน project `.mcp.json` (Ch ecosystem: อยู่ project-local ไม่ใช่ global)

**(2) Streamable HTTP `/mcp`** — ใหม่ (#2760)
```
claude ─ HTTP POST /mcp ─→ backend :47778 (Elysia)
        │   JSON-RPC over HTTP, streamable (SSE-like chunks)
```
- ไม่ต้อง spawn subprocess · หลาย client ต่อ backend เดียว · remote ได้ (ผ่าน CF Worker, Ch5)
- รองรับ **auth** (token) — สำคัญตอน expose

**(3) SSE / legacy** — เดิม (ก่อน Streamable HTTP มาแทน)

→ backend เดียว (`src/server.ts`) เสิร์ฟทั้ง REST + MCP บน :47778 (Ch ecosystem: 1 process 3 หน้าที่)

---

## 15.2 Embedded mode — muninn_search อ่านไฟล์ตรง

จุดที่คนงงบ่อย (Ch ecosystem hardParts): `muninn_search` มี 2 โหมดหน้าตาเหมือนกัน:
```
HTTP mode:     muninn_search → HTTP → :47778 → SQLite/LanceDB
Embedded mode: muninn_search → อ่านไฟล์ vault/DB ตรง (ไม่ผ่าน HTTP server)
```
- embedded เร็วกว่า (ไม่มี network hop) แต่ caller ต้อง**อยู่เครื่องเดียวกับ data**
- อันตราย: ตั้ง env ผิด → embedded ชี้ผิด DB / HTTP ชี้ผิด host **โดยไม่ error** → เงียบๆ ค้นผิดที่ (Ch ecosystem observability bug ตระกูลนี้)

---

## 15.3 Graceful degradation ในชั้น MCP (#2747)

`src/mcp/fts-only-vector-store.ts` (เห็นใน Ch4): ถ้า embedder ล่ม → MCP server สลับเป็น **FTS-only store** → `muninn_search` ยังตอบ (FTS5) ไม่ throw
- นี่คือ Ch4 §4.2 fallback แต่ที่ชั้น MCP → agent ไม่เห็น error เห็นแค่ผล FTS
- surface embedder status แยกจาก search availability (#2759 observability) → agent รู้ว่า "ตอนนี้ semantic ปิด" ได้ถ้าอยากรู้

---

## 15.4 tool surface (ที่ agent เรียกได้)

| tool | ทำอะไร | เบื้องหลัง |
|---|---|---|
| `muninn_search` | ค้น hybrid (semantic+FTS) | Ch4 pipeline |
| `oracle_ask` | ถาม → ตอบพร้อม citation | search + synthesize |
| `muninn_stats` | index มีอะไร (docs, collections) | /api/stats (Ch demo แนะนำโชว์สด) |
| `oracle_learn` | เขียน memory ใหม่ | embed + upsert (Ch2/3) |

→ `muninn_search` = alias ของ oracle_search (Ch ecosystem) · เดโม workshop แนะนำ `muninn_stats` โชว์ "20k docs จริง" (Ch community-ask)

---

## 15.5 auth & remote (expose อย่างปลอดภัย)

- local (:47778) = ไม่ต้อง auth (loopback)
- remote MCP (CF Worker /mcp) = ต้อง token (auth ที่เพิ่งเพิ่ม) · เพราะ expose สู่เน็ต = ใครก็ยิงได้ถ้าไม่มี auth
- Ch ecosystem: "เปิด :47778 สู่ public = ไม่แนะนำ auth ยังบาง" → ใช้ CF Worker + PNA (Studio) แทน

---

## 15.6 เชื่อมภาพรวม (จาก query ถึงผล)

```
Claude Code
  │  เรียก muninn_search("เบาหวานงานวิจัย")
  ▼  (transport: stdio | HTTP /mcp | embedded)
backend :47778
  │  embed query (Ch2, fallback chain Ch4)
  │  hybrid: FTS5 (D1/SQLite) + vector (LanceDB, Ch3)
  │  RRF fuse (Ch11) + heat (Ch13) + rerank (Ch4)
  ▼
ผลลัพธ์ + citation → กลับ Claude Code → agent ใช้ต่อ
```
= ทุก chapter ก่อนหน้ามาบรรจบที่ transport ชั้นนี้

---

## สรุป Ch15
```
MCP = agent เรียก tool (muninn_search/oracle_ask/muninn_stats/oracle_learn)
3 transport: stdio (subprocess/pipe) · Streamable HTTP /mcp (#2760, auth, remote) · SSE(legacy)
embedded vs HTTP: อ่านไฟล์ตรง vs ผ่าน server — ตั้ง env ผิด = ค้นผิดที่เงียบๆ
graceful degradation ชั้น MCP (fts-only-vector-store, #2747) → agent ไม่เจอ error
```
**ถัดไป Ch16:** efficient attention — O(n²) ของ Ch10 แก้ยังไง (FlashAttention IO-aware, linear/sparse attention), ทำไมสำคัญกับ bge-m3 8192 ctx + bulk indexing

---
*grounded: src/mcp/server.ts · src/mcp/fts-only-vector-store.ts (#2747) · ecosystem (3 transports/#2759/#2760/embedded) · MCP spec · เชื่อม Ch2/3/4/11/13/14 · /loop deep iter 2026-07-13*
