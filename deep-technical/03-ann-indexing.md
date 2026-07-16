# Deep Technical · Chapter 3 — ANN Indexing (หา nearest ให้เร็ว)

> ต่อจาก Ch2 · ตอนนี้เรามี **35,164 เวกเตอร์ × 1024 มิติ** ใน LanceDB · ทุก query ต้องหา top-k ที่ cosine ใกล้สุด
> คำถามบทนี้: จะหายังไง**ไม่ให้ช้า** — และทำไมต้องยอม "ประมาณ" (Approximate)

---

## 3.1 ปัญหา: brute-force O(n·d)

วิธีตรงไปตรงมา (exact kNN): คำนวณ cosine ระหว่าง query กับ**ทุก**เวกเตอร์ แล้วเรียง

```
cost ต่อ query = n × d  multiply-add
              = 35,164 × 1024
              ≈ 36 ล้าน operations ต่อ 1 คำค้น
```

35k docs ยังพอไหว (~ไม่กี่ ms) แต่:
- โต 20k → 1M docs = 1,000 ล้าน ops/query → ช้าเกินโต้ตอบ
- QPS สูง (หลายคนค้นพร้อมกัน) → CPU ระเบิด

**exact kNN = O(n·d) ต่อ query, O(1) memory เพิ่ม** — แม่น 100% แต่ scale ไม่ได้

---

## 3.2 Exact vs Approximate — trade recall แลก speed

**ANN (Approximate Nearest Neighbor)**: ยอมพลาด "เพื่อนบ้านที่แท้จริง" บ้าง แลกกับเร็วขึ้น 10–1000×

วัดคุณภาพด้วย **recall@k**:
```
recall@k = |ผลที่ ANN คืน ∩ ผลจริง (exact) top-k| / k
```
เช่น recall@10 = 0.95 → ใน 10 อันดับแรก ANN ได้ตรงกับ exact 9.5 อัน · **ปรับ knob ได้**: ยอม recall ต่ำลง = เร็วขึ้น

2 ตระกูลใหญ่: **IVF/PQ** (partition + compress) และ **HNSW** (graph)

---

## 3.3 IVF — Inverted File (แบ่งเป็นเซลล์)

**Train**: clustering เวกเตอร์ทั้งหมดด้วย k-means เป็น `nlist` centroids (เช่น 256 เซลล์) · แต่ละเวกเตอร์สังกัดเซลล์ที่ centroid ใกล้สุด

**Search**:
1. หา centroid ที่ใกล้ query สุด `nprobe` เซลล์ (เช่น 8 จาก 256)
2. brute-force เฉพาะเวกเตอร์ใน `nprobe` เซลล์นั้น

```
cost ≈ nlist (หา centroid) + (n/nlist)×nprobe × d
     ≈ 256 + (35164/256)×8 × 1024   ≈ เร็วกว่า brute-force ~30×
```

- **nprobe** = knob: มาก → recall สูง/ช้า · น้อย → เร็ว/พลาด
- ความเสี่ยง: ถ้า true neighbor อยู่เซลล์ข้างเคียงที่ไม่ได้ probe → พลาด (edge effect)

---

## 3.4 PQ — Product Quantization (บีบเวกเตอร์)

ปัญหา: เก็บ 1024-dim float32 = 4KB/vector × 1M = 4GB RAM

**PQ**: หั่นเวกเตอร์ 1024 มิติเป็น `m` ท่อน (เช่น 8 ท่อน × 128 มิติ) · แต่ละท่อน quantize เป็น 1 ใน 256 codeword (8-bit) → เก็บแค่ `m` bytes = **8 bytes/vector** (บีบ 512×!)

**distance ประมาณ**: precompute ตาราง distance query↔codeword → รวมผลต่อท่อน (asymmetric distance computation, ADC)
```
d(q, x) ≈ Σ  d(q_sub_j, codeword[x_j])     ← lookup ไม่ใช่คูณเต็ม
        j=1..m
```

**IVF-PQ** = IVF (แบ่งเซลล์) + PQ (บีบในเซลล์) = ตระกูลที่ scale ไป billion-vector ได้ (FAISS)

trade-off: บีบมาก → เร็ว/ประหยัด RAM แต่ distance เพี้ยน → recall ตก → มักตาม reranking ด้วย full-precision (Ch4)

---

## 3.5 HNSW — Hierarchical Navigable Small World (graph)

แนวคิดต่างจาก IVF สิ้นเชิง: สร้าง **กราฟ** ที่แต่ละเวกเตอร์ = node เชื่อมกับเพื่อนบ้านใกล้ `M` ตัว · **หลายชั้น** (เหมือน skip list): ชั้นบนเบาบาง (กระโดดไกล), ชั้นล่างหนาแน่น (ละเอียด)

**Search (greedy)**:
1. เริ่มที่ entry point ชั้นบนสุด
2. เดินไป neighbor ที่ใกล้ query ขึ้นเรื่อยๆ จนติด local min
3. ลงชั้นถัดไป ทำซ้ำ จนชั้นล่างสุด
4. เก็บ candidate ด้วย priority queue ขนาด `efSearch`

```
cost ≈ O(log n) hops × M × d      ← log! ไม่ใช่ n
```
- **efSearch** = knob (เหมือน nprobe): มาก → recall สูง/ช้า
- **M** = ระดับการเชื่อม (สร้างครั้งเดียว): มาก → recall ดี/index ใหญ่

**จุดเด่น**: recall สูงมากที่ latency ต่ำ (นิยมสุดใน production) · **จุดอ่อน**: index กิน RAM (เก็บ full vectors + กราฟ), insert/delete แพงกว่า IVF

---

## 3.6 LanceDB ใน ARRA Oracle — ของจริง

`src/vector/adapters/lancedb.ts`:
```ts
const results = await this.table.search(queryEmbedding)
  .distanceType('cosine')     // metric = cosine (Ch1)
  .limit(fetchLimit)
  .toArray();
```
- LanceDB สร้างบน **Lance columnar format** (Arrow-based) — เก็บ vector บนดิสก์ แบบ memory-mappable (ไม่ต้องโหลดทั้งหมดเข้า RAM แบบ HNSW ล้วน)
- index: IVF-PQ เป็นหลัก (`create_index` เลือก `num_partitions` = nlist, `num_sub_vectors` = m ของ PQ) · ค้นแบบ **flat (brute-force)** ได้ถ้า table เล็ก — ARRA 35k docs อาจยังใช้ flat (เร็วพอ, recall 100%)
- **`_distance`** ที่คืนมา = cosine distance (Ch1 §1.5) → เรียงน้อย→มาก

**ข้อดีเชิงสถาปัตยกรรมสำหรับ ARRA**: Lance เก็บบนดิสก์ + mmap → เหมาะกับ "second brain ในเครื่อง" ที่ไม่อยากกิน RAM ทั้งก้อน (ต่างจาก in-memory HNSW ที่ต้องโหลดหมด)

---

## 3.7 knob สรุป (speed ↔ recall)

| index | knob search | เพิ่ม knob → | index size | insert |
|---|---|---|---|---|
| Flat (exact) | — | (recall 100% เสมอ) | เต็ม | ถูก |
| IVF | nprobe | recall↑ speed↓ | เล็ก | ถูก |
| IVF-PQ | nprobe | recall↑ speed↓ | เล็กสุด (บีบ) | กลาง |
| HNSW | efSearch | recall↑ speed↓ | ใหญ่ | แพง |

**หลักเลือกสำหรับงานวิจัยส่วนตัว (ARRA sweet spot)**: docs < 100k → Flat หรือ IVF ก็พอ, recall เต็ม, ไม่ต้อง tune มาก · ถ้าโตเป็นล้าน → IVF-PQ + rerank (Ch4)

---

## สรุป Ch3
```
brute-force O(n·d) ไม่ scale
  → IVF: แบ่งเซลล์ k-means, probe เฉพาะใกล้ (nprobe)
  → PQ: บีบเวกเตอร์เป็น codeword (8 bytes), distance แบบ lookup
  → HNSW: กราฟหลายชั้น, greedy O(log n) hops (efSearch)
  → LanceDB: IVF-PQ บน Lance columnar (disk+mmap) เหมาะ second-brain ในเครื่อง
```
**ถัดไป Ch4:** โค้ด ARRA เต็ม — adapter pattern, fallback chain, hybrid FTS+vector scoring (รวมคะแนน 2 โลกยังไง), bge-reranker pipeline

---
*grounded: src/vector/adapters/lancedb.ts (distanceType/search) · Lance columnar format · HNSW (Malkov & Yashunin 2016) · IVF-PQ (Jégou et al. 2011, FAISS) · /loop deep iter 2026-07-13*
