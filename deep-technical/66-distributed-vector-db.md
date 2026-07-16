# Deep Technical · Chapter 66 — Distributed Vector DB

> ต่อจาก Ch65 · Ch25 เกริ่น sharding · บทนี้ลงลึก: shard + replicate, consensus (Raft), scatter-gather query, เมื่อ 1 เครื่องไม่พอ

---

## 66.0 ทำไมต้อง distribute

```
1 เครื่องมีเพดาน: RAM (Ch48), CPU (qps), disk → เกิน = ต้องหลายเครื่อง
เหตุ: corpus ใหญ่ (พันล้าน vec, Ch48) หรือ traffic สูง (qps เกิน 1 node)
→ กระจาย: sharding (แบ่งข้อมูล) + replication (สำเนากันล่ม)
```
- ARRA personal ไม่ถึง (Ch48) · แต่เข้าใจไว้เผื่อ scale องค์กร (ทุกคนรวมกัน)

---

## 66.1 ⭐ sharding — แบ่ง corpus

```
แบ่ง N doc → S shard (แต่ละ shard ~N/S doc, พอ 1 เครื่อง)
2 วิธี:
  random/hash shard: doc → shard = hash(id) % S → balance ดี, แต่ query ต้องถามทุก shard
  semantic shard:    doc → shard ตาม cluster (Ch3 centroid) → query ถามเฉพาะ shard ใกล้
```
- **trade**: hash = balance แต่ scatter กว้าง · semantic = query แคบ แต่ hotspot เสี่ยง (cluster ยอดฮิต)
- ส่วนใหญ่ hash (balance สำคัญกว่า, ANN แต่ละ shard เร็วอยู่แล้ว)

---

## 66.2 scatter-gather query

```
query มา → coordinator:
1. scatter: ส่ง query ไปทุก shard (parallel)
2. แต่ละ shard: ANN local → top-k ของตัวเอง
3. gather: รวม top-k จากทุก shard → merge → global top-k
```
- **ต้อง over-fetch**: แต่ละ shard ส่ง top-k (ไม่ใช่ top-k/S) เพราะ top global อาจกระจุก shard เดียว
- latency = ช้าสุดของ shard (Ch44 tail) → straggler 1 ตัวถ่วงทั้ง query → timeout+partial result

---

## 66.3 replication — กันล่ม + scale read

```
แต่ละ shard มี replica (สำเนา R ชุด):
- fault tolerance: 1 replica ล่ม → replica อื่นรับต่อ (ไม่เสีย shard นั้น)
- read scaling: query กระจายไป replica หลายตัว → qps เพิ่ม (read-heavy Ch65)
```
- write ต้อง sync replica → consistency (Ch65): sync ทุกตัว (strong, ช้า) vs async (eventual, เร็ว)

---

## 66.4 ⭐ consensus — Raft (write ตรงกันทุก replica)

replica ต้องเห็น write ลำดับเดียวกัน (ไม่งั้น diverge) → **consensus protocol**:
```
Raft: เลือก leader → leader รับ write → replicate ไป follower → commit เมื่อ majority ack
- majority (quorum): N/2+1 → ทน node ล่มได้ (N−1)/2 ตัว
- leader ล่ม → election เลือก leader ใหม่ (term++)
- log replication: entry เรียงลำดับ (คล้าย WAL Ch64) → ทุก replica replay ได้ผลเดียว
```
- **CAP prelude (Ch67)**: quorum = เลือก consistency + partition-tolerance (แลก availability ตอน split)

---

## 66.5 rebalancing — เพิ่ม/ลด node

```
เพิ่ม shard (corpus โต): ต้องย้าย doc บางส่วนไป shard ใหม่ → rebalance
  consistent hashing: ลด doc ที่ต้องย้าย (แค่ส่วนติด shard ใหม่) แทน rehash ทั้งหมด
node ล่มถาวร: replica ของ shard นั้น promote + สร้าง replica ใหม่ที่ node อื่น
```
- rebalance = ย้ายข้อมูล (แพง I/O) → ทำ background + throttle (ไม่กระทบ query)

---

## 66.6 ARRA — Vectorize คือ distributed ที่ managed

```
ARRA local (LanceDB): single-node (Ch48/65) — personal ไม่ต้อง distribute
Vectorize (Ch14): CF จัดการ shard/replica/consensus ให้ (managed distributed)
  → เราแค่ upsert/query, CF ทำ scatter-gather + replication หลังบ้าน
  → trade: ควบคุมน้อย (ไม่เห็น shard) แต่ไม่ต้อง run Raft เอง
D1 (Ch14): SQLite + CF replication (read replica ข้าม region)
```
- **บทเรียน scale-appropriate (Ch46/48 ย้ำ)**: personal=single-node · องค์กร/edge=distributed (managed ดีกว่า self-host Raft)

---

## สรุป Ch66
```
1 เครื่องเพดาน (RAM/qps/disk) → distribute: shard (แบ่ง) + replicate (สำเนา)
⭐ sharding: hash (balance, scatter กว้าง) vs semantic (query แคบ, hotspot เสี่ยง) → มัก hash
scatter-gather: query → ทุก shard parallel → merge global top-k (over-fetch, tail=straggler Ch44)
replication: fault tolerance + read scaling (Ch65 read-heavy) · write sync(strong)/async(eventual)
⭐ Raft consensus: leader+quorum(N/2+1) → write ลำดับเดียว, ทนล่ม (N−1)/2 · log replication (WAL Ch64)
rebalancing: consistent hashing ลด doc ย้าย · background+throttle
ARRA: local single-node (personal) · Vectorize=managed distributed (CF ทำ shard/Raft ให้) — scale-appropriate
```
**ถัดไป Ch67:** CAP theorem for vector search — consistency vs availability ตอน network partition, ทำไม vector DB เลือกต่างกัน, PACELC
---
*grounded: sharding/scatter-gather · Raft consensus (Ongaro 2014) · consistent hashing · Vectorize managed (Ch14) · เชื่อม Ch3/14/25/44/46/48/64/65 · /loop deep iter 2026-07-16*
