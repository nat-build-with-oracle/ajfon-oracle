# Deep Technical · Chapter 23 — Deployment & Monitoring

> ต่อจาก Ch22 · จากโมเดล/algorithm → operate จริง · บทนี้: deploy ที่ไหนได้บ้าง + สังเกตสุขภาพยังไง (observability)
> grounded: pm2 (arra-oracle id 31), Docker (ghcr), #2759 observability, ecosystem incident จริง

---

## 23.0 deploy targets (3 แบบ, จาก Ch ecosystem)

```
1. pm2 (local process manager)     ← ที่รันจริงตอนนี้ (id 31, alpha v26.7.5)
2. Docker (ghcr.io/.../http)         ← self-host portable
3. Cloudflare Workers (edge)         ← studio/mcp live, data plane รอ token (Ch5/14)
```

---

## 23.1 pm2 — ที่รันจริง

`arra-oracle` id 31 ใต้ pm2 (Ch ecosystem live check):
```
pm2 start bin/arra -- serve         # หรือ ecosystem.config
pm2 restart arra-oracle             # restart (โค้ดใหม่ = alpha tip)
pm2 logs arra-oracle                # ดู log
pm2 jlist                           # สถานะ JSON (status, restart_time)
```
- **auto-restart** ถ้า crash · เก็บ restart count (ดูใน incident: restart 3 ครั้ง = ตรงกับที่ v3 restart)
- env: `ORACLE_EMBEDDER=none` (ตอน Ollama retired) → FTS5-only (Ch4 §4.2)
- **ข้อจำกัด**: pm2 ไม่ manage Ollama/reranker sidecar → embedder ตายแยกจาก backend (Ch ecosystem hardParts: Ollama = จุดพังที่ไม่มี auto-restart)

---

## 23.2 Docker — portable self-host

`Dockerfile` multi-stage (Ch ecosystem):
```
targets: deps → builder → production (http-server) | mcp-stdio
HEALTHCHECK: curl /api/health
VOLUME: /data
image: ghcr.io/soul-brews-studio/arra-oracle-v3:http
```
- `docker-compose.prod.yml`: bind `127.0.0.1:47778`, `ORACLE_EMBEDDER=none` default (FTS5-only ปลอดภัย)
- **ข้อดี**: reproducible, ยกไป VPS ได้ · **prod default = ไม่มี embedder** (เปิด vector = ต่อ Ollama/CF เอง)

---

## 23.3 ⭐ Observability (#2759) — health vs stats

**ปัญหาจริง (incident ที่เจอ Ch ecosystem)**:
```
/api/stats   → vector_status: "ok"        (อ่าน CACHED state ตอน boot)
/api/health  → embedderStatus: "down"     (LIVE probe, ollama timeout)
                                            ← 2 endpoint ขัดกัน ณ วินาทีเดียว!
```
- **root cause**: stats อ่าน snapshot ตอน boot · health probe สด → ถ้า Ollama ตายหลัง boot, stats ยังโชว์ ok (stale) แต่ health โชว์ down (จริง)
- นี่คือ observability bug ที่ #2759 (runtime embedder observability) แก้ → surface embedder status แยกจาก search availability, ให้ค่า live

**บทเรียน**: monitoring ต้องแยก **cached vs live** ชัด · ค่าที่ stale หลอกให้คิดว่าระบบ healthy ทั้งที่พัง (silent degradation)

---

## 23.4 Embedder degradation detection

```
1. health probe ยิง embedder จริง (embed test string) เป็นระยะ
2. ถ้า timeout/error → mark embedderStatus=down (live)
3. search degrade เป็น FTS5 (Ch4 §4.2 fallback + Ch15 fts-only-vector-store)
4. surface status → agent/UI รู้ว่า "semantic ปิด" (ไม่ใช่แค่ผลว่างเงียบๆ)
```
- **ทำไมสำคัญ**: ตอน incident, search คืน empty ทั้งที่ควร fallback FTS5 — เพราะ server รันโค้ดเก่า (ก่อน #2747) → restart บน alpha แก้ · **โค้ด observability ต้อง deploy ด้วย ไม่ใช่แค่มีใน repo**

---

## 23.5 Graceful restart (zero-downtime-ish)

```
pm2 reload arra-oracle      # reload แทน restart (drain connection ก่อน)
```
- แต่ระวัง: LanceDB/SQLite lock — ต้องปิด handle ให้สะอาด (Ch ecosystem: lancedb-stale-handle test มีจริง)
- eventual consistency ของ Vectorize (Ch14) → หลัง restart edge อาจต้องรอ index settle

---

## 23.6 metrics ที่ควร monitor (production)

```
- /api/health           (embedder/vector/fts live status)
- query latency p50/p99 (Ch6 §6.7)
- embedder fallback rate (Ch4 fallback chain stats → onFallback events)
- index size / doc count (muninn_stats)
- restart count (pm2)     ← พุ่ง = crash loop
- recall on canary queries (rerun benchmark subset, Ch20)
```

---

## 23.7 checklist deploy จริง (สรุป operate)

```
□ backend รัน (pm2/Docker) + health เขียว
□ embedder: none (FTS5) หรือ ต่อ Ollama/CF + drift ผ่าน (Ch5/6)
□ observability: health=live ไม่ใช่ cached (#2759 deployed)
□ graceful degradation: Ollama ตาย → FTS5 (ทดสอบจริง!)
□ backup: vault markdown (ground truth) + DB
□ port 47778 ไม่ expose public โดยไม่มี auth (Ch15)
```

---

## สรุป Ch23
```
deploy: pm2 (รันจริง id 31, auto-restart แต่ไม่ manage Ollama) / Docker (ghcr, FTS5 default) / CF (edge)
observability #2759: health(live) vs stats(cached) เคยขัดกัน → silent degradation → แยก live/cached
embedder degradation: probe → FTS5 fallback + surface status (โค้ดต้อง deploy ไม่ใช่แค่มี)
graceful restart (pm2 reload + handle cleanup) · monitor: health/latency/fallback-rate/recall canary
```
**ถัดไป Ch24:** cost model — local (fixed GPU/power) vs CF (per-neuron), embedding cost index-vs-query, mem0 $90-vs-$1.80, hybrid cost optimization
---
*grounded: pm2 (arra-oracle id 31, alpha) · Dockerfile/docker-compose.prod.yml · #2759 observability · #2747 degrade · ecosystem incident (stats/health mismatch) · lancedb-stale-handle test · /loop deep iter 2026-07-13*
