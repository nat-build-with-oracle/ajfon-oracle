# Deep Technical · Chapter 25 — Scaling & Sharding

> ต่อจาก Ch24 · ARRA ตอนนี้ 35,164 docs · ถ้าโต 1M / 100M / 1B ต้องทำอะไร · บทนี้: scaling curve + sharding

---

## 25.0 scaling curve — อะไรพังเมื่อไร

```
35k docs      →  Flat (brute-force) ยังไหว, recall 100%          (ARRA ตอนนี้)
100k–1M       →  ต้อง ANN index (IVF/HNSW, Ch3) — brute-force ช้า
1M–10M        →  ต้อง quantize (IVF-PQ, Ch8) — RAM ไม่พอเก็บ full
10M–100M+     →  ต้อง shard (แบ่งหลายเครื่อง) — 1 เครื่องไม่พอ
1B+           →  distributed + tiered storage (hot/cold)
```
**หลัก**: อย่า over-engineer · 35k = Flat ก็พอ (Ch3 §3.7) · เพิ่มความซับซ้อนเมื่อ**ชนเพดานจริง** เท่านั้น

---

## 25.1 เมื่อ RAM ไม่พอ (1M–10M)

1M × 4KB (1024-dim float32) = 4GB แค่เวกเตอร์ + HNSW graph overhead → เกิน RAM เครื่องเล็ก
```
ทางแก้: IVF-PQ (Ch8) — บีบ 512× → 1M × 8 bytes = 8MB (!) codes ใน RAM
        full vectors อยู่ดิสก์ → rerank เฉพาะ candidate (Ch8 §8.5)
```
LanceDB (Ch3 §3.6) ช่วยตรงนี้: Lance columnar บนดิสก์ + mmap → ไม่ต้องโหลดทั้งหมดเข้า RAM ตั้งแต่แรก

---

## 25.2 Sharding strategies (10M+)

แบ่งเวกเตอร์เป็น N shard, แต่ละ shard คนละเครื่อง/พาร์ทิชัน:

**(a) Random/hash sharding** (by-id):
```
shard(doc) = hash(id) mod N
```
- กระจายสม่ำเสมอ · query ต้องยิง **ทุก shard** (scatter) แล้ว merge (gather) → §25.3
- ✅ balance ดี · ❌ ทุก query แตะทุก shard

**(b) Cluster/semantic sharding** (by-centroid):
```
shard(doc) = argmin ‖doc − centroidₛ‖     (k-means routing, คล้าย IVF ระดับเครื่อง)
```
- doc ความหมายคล้ายอยู่ shard เดียวกัน · query ยิงแค่ shard ที่ใกล้ (ไม่ต้องทุกอัน)
- ✅ query แตะน้อย shard · ❌ imbalance (บาง cluster ใหญ่)

**(c) Tenant/type sharding**:
```
shard by doc_type (principle/learning/retro) หรือ per-user
```
- privacy/isolation ดี (ARRA multi-oracle: แต่ละ oracle = shard?) · filter ก่อน = แตะ shard เดียว

---

## 25.3 Distributed ANN — Scatter-Gather

```
query → [router]
          ├→ shard 1: local ANN → top-k₁     (ขนาน)
          ├→ shard 2: local ANN → top-k₂
          └→ shard N: local ANN → top-kₙ
        [gather] merge ทุก top-kᵢ → เรียง global → top-k
```
- **over-fetch ต่อ shard**: ขอ top-k จากแต่ละ shard (ไม่ใช่ top-k/N) เพราะ relevant อาจกระจุก shard เดียว → merge ได้ recall เต็ม
- latency = shard ที่ช้าสุด (tail, Ch6 §6.7) → ต้อง balance + timeout
- นี่คือ pattern เดียวกับ Ch4 hybrid (FTS leg + vector leg = 2 "shard" ในเชิงตรรกะ → RRF gather, Ch11)

---

## 25.4 Replica — scale การอ่าน (read QPS)

```
1 primary (write) → N replica (read)
query → load-balance ไป replica ใดก็ได้
```
- query เยอะ (หลายคนค้น) → เพิ่ม replica · CF D1 (Ch14) ทำ read replica ให้เอง (edge, ใกล้ผู้ใช้)
- **write ยังไป primary** → index update = 1 จุด (eventual propagate ไป replica)

---

## 25.5 Consistency ตอน scale

- **index lag**: upsert แล้ว replica/shard อาจยังไม่เห็น (eventual, Ch14 §14.4) → bulk index ต้องรอ settle ก่อนวัด (Ch6 drift)
- **rebuild cost**: เปลี่ยนโมเดล = re-embed ทุก shard = แพงมากที่ scale → drift benchmark (Ch6 §6.6) สำคัญยิ่งขึ้น (อย่าเปลี่ยนโมเดลพร่ำเพรื่อ)

---

## 25.6 ARRA reality — อย่าเพิ่งกังวล

```
35,164 docs = Flat/IVF พอสบาย · RAM ~140MB · ไม่ต้อง shard
โตถึง ~1M (นับ paper ทั้ง career นักวิจัย?) → IVF-PQ + LanceDB disk = ยังเครื่องเดียว
sharding = ปัญหาของ fleet-scale (หลาย oracle รวม) ไม่ใช่ second-brain คนเดียว
```
→ "second brain ส่วนตัว" ไม่ค่อยชนเพดาน sharding · sweet spot คือ Flat/IVF เครื่องเดียว (Ch3 §3.7, Ch24 privacy)

---

## สรุป Ch25
```
scaling: 35k Flat → 1M IVF-PQ → 10M shard → 1B distributed+tiered (อย่า over-engineer)
RAM เต็ม → IVF-PQ บีบ (Ch8) + LanceDB disk/mmap
shard: hash(balance/scatter-all) · cluster(แตะน้อย/imbalance) · tenant(isolation)
distributed ANN = scatter-gather (over-fetch ต่อ shard) = pattern เดียวกับ hybrid RRF
replica = read scaling (D1 edge) · consistency: index lag + rebuild cost → อย่าเปลี่ยนโมเดลบ่อย
ARRA second-brain: Flat/IVF เครื่องเดียวพอ, sharding = fleet-scale problem
```
**ถัดไป Ch26:** ingest research paper จริง (use-case workshop) — PDF→text→chunk→embed→index→cite pipeline, paper→insight→RQ→writing
---
*grounded: Ch3/8 (index scaling), Ch14 (D1 replica/consistency), Ch4/11 (scatter-gather=hybrid), Ch24 (rebuild cost) · distributed vector search patterns · /loop deep iter 2026-07-13*
