# Deep Technical · Chapter 69 — Geo-Distributed & Edge Retrieval

> ต่อจาก Ch68 · Ch5/14 = Cloudflare edge · บทนี้ลงลึก: ค้นใกล้ user, data residency, CDN-style vector cache, ทำไม edge เปลี่ยนเกม latency

---

## 69.0 ปัญหา — ระยะทาง = latency (แสงมีขีดจำกัด)

```
user ไทย → server สหรัฐ: RTT ~200ms (แค่ speed-of-light + hop) ก่อนเริ่มคำนวณ!
→ query 1 ครั้ง +200ms คงที่ → รู้สึกช้าแม้ backend เร็ว (Ch44)
→ วางของใกล้ user (edge) → RTT ~10-30ms → เร็วขึ้นชัด
```
- edge = รันใกล้ user ทางภูมิศาสตร์ (Ch5 Cloudflare 300+ เมือง)

---

## 69.1 ⭐ อะไรวางที่ edge ได้ (vector search)

```
embed query:   ✓ edge (Workers AI @cf/baai/bge-m3, Ch5/14) — ใกล้ user
vector index:  ⚠️ ใหญ่ → replicate ทุก edge แพง → Vectorize จัดการ tier (Ch14/48)
cache result:  ✓ edge (query ยอดฮิต → cache ที่ edge, Ch32) — CDN-style
rerank:        อาจ edge (เบา) หรือ origin (cross-encoder หนัก Ch18)
```
- pattern: **embed+cache ที่ edge (เร็ว), index ที่ regional (Vectorize managed)** → สมดุล latency/cost

---

## 69.2 CDN-style vector cache

```
CDN cache static asset ใกล้ user · ทำแบบเดียวกับ retrieval result:
query → edge cache (Ch32 semantic cache) hit? → ตอบเลย (ไม่ไป origin)
       miss → origin (regional index) → ตอบ + populate edge cache
```
- query ยอดฮิต (power-law Ch49) → cache ที่ edge ครอบ traffic ส่วนใหญ่ → origin โดนน้อย
- **invalidation**: doc ใหม่ → cache เก่าอาจ stale (eventual Ch67) → TTL สั้น + heat-aware (Ch13)

---

## 69.3 ⭐ data residency / sovereignty

```
กฎหมาย (GDPR, PDPA ไทย): ข้อมูลบาง class ต้องอยู่ในประเทศ/region นั้น
→ vector ของ EU user ต้อง store ใน EU (ไม่ replicate ออก)
→ geo-partition ตาม residency (ไม่ใช่แค่ performance, Ch66 semantic shard)
```
- **conflict กับ edge cache (§69.2)**: cache result ข้าม region อาจละเมิด residency → ต้อง scope cache ตาม region
- second brain (ARRA local): residency = เครื่อง user เอง → compliant โดย default (Ch27 privacy)

---

## 69.4 read-local write-global (geo pattern)

```
query (read): route ไป edge/region ใกล้ user → latency ต่ำ (มัก eventual OK, Ch67)
ingest (write): ไป home region → replicate ออก (async, Ch68 multi-leader)
→ read เร็วทุกที่ · write consistent ที่ home · propagate ตาม eventual
```
- เหมาะ retrieval: read เยอะ (Ch65) ต้องเร็วใกล้ user · write น้อยกว่า ยอม latency home ได้

---

## 69.5 latency budget ข้าม geo (เชื่อม Ch44)

```
same-region:   RTT ~1-5ms
cross-region:  RTT ~50-150ms
cross-continent: RTT ~150-300ms
→ ทุก hop ข้าม region = +RTT → ลด hop (embed+cache edge §69.1) = ลด tail (Ch44 p99)
```
- **1 query ควรจบใน region เดียวถ้าทำได้** — scatter ข้าม continent (Ch66) = tail ระเบิด

---

## 69.6 เชื่อม ARRA

```
ARRA local: latency = 0 network (ในเครื่อง!) → เร็วสุด, residency compliant, no geo complexity
  → personal ไม่ต้องแตะ geo เลย (ข้อได้เปรียบ single-node ย้ำ Ch48/65/67)
ARRA edge (Vectorize Ch14): embed@edge (Workers AI Ch5) + cache@edge (§69.2) + index managed
  → สำหรับ multi-user/global (ทีม, องค์กร) → CF จัดการ geo ให้
drift benchmark (#2740, Ch6): วัด local vs edge → รู้ว่า edge เพี้ยนไหม (quality ข้าม path)
```
- **บทเรียน**: personal = local (0 latency, compliant) · global = edge (managed) → เลือกตาม scale/ผู้ใช้

---

## สรุป Ch69
```
ระยะทาง=latency (speed-of-light RTT ~200ms ข้ามทวีป) → วางของใกล้ user (edge Ch5)
⭐ edge วางได้: embed (Workers AI) + cache result (CDN-style Ch32) · index=regional managed (Vectorize)
CDN-style cache: query ยอดฮิต (power-law Ch49) cache@edge → origin โดนน้อย · TTL+heat invalidation
⭐ data residency (GDPR/PDPA): vector อยู่ใน region ตามกฎ → geo-partition, scope cache ตาม region
read-local write-global: read ใกล้ user (eventual OK) · write home → replicate (Ch68)
latency budget: 1 query จบใน region เดียว (ลด hop) → ลด tail (Ch44)
ARRA: local=0 network+compliant (personal) · edge=managed geo (global) — scale-appropriate
```
**ถัดไป Ch70:** vector DB cost-at-scale — คำนวณต้นทุนจริง (storage/compute/egress), ต่อ 1M vector, quantize ประหยัดเท่าไร, local vs cloud break-even
---
*grounded: edge latency (speed-of-light RTT) · CDN cache · data residency (GDPR/PDPA) · Vectorize/Workers AI (Ch5/14) · drift #2740 (Ch6) · เชื่อม Ch5/6/13/14/32/44/48/65/66/67/68 · /loop deep iter 2026-07-16*
