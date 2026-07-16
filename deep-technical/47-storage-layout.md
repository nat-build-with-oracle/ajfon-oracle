# Deep Technical · Chapter 47 — Multi-Vector Storage Layout

> ต่อจาก Ch46 · rebuild แล้วเก็บยังไงในดิสก์ให้ค้นเร็ว · บทนี้: columnar vs row, memory-map, cache locality — ระดับ byte

---

## 47.0 ทำไม layout สำคัญกับ latency

distance (Ch1) = อ่านเวกเตอร์จากดิสก์/แรม แล้วคูณ · **ถ้า layout แย่ → cache miss → ช้า 100×**:
```
CPU อ่าน RAM ผ่าน cache line (64 bytes) · L1 ~1ns, RAM ~100ns, SSD ~100µs
เวกเตอร์อยู่ติดกัน (sequential) → prefetch เดาถูก → เร็ว
เวกเตอร์กระจัดกระจาย (random) → cache miss ทุกตัว → ช้า
```
→ **layout = ปัจจัยความเร็วที่ algorithm (Ch3) มองข้าม**

---

## 47.1 Row vs Columnar

```
row-major (AoS, array of structs):
   [doc1: vec, text, meta][doc2: vec, text, meta]...
   ดี: อ่าน doc เดียวครบ (ค้นแล้วเอา metadata)
   แย่: scan แค่ vector ทุก doc → โหลด text/meta ที่ไม่ใช้ด้วย (เปลือง bandwidth)

columnar (SoA, struct of arrays):
   [all vecs ติดกัน][all texts][all metas]
   ดี: scan vector ทุก doc → อ่าน vector ล้วน sequential → SIMD (Ch44) + prefetch เต็มที่
   แย่: เอา doc เดียวครบ → กระโดดหลาย column
```
- **vector search = scan vector เยอะ** → **columnar ชนะ** · LanceDB (Ch4) เป็น columnar (Lance format) → นี่คือเหตุผลเชิง layout ที่มันเร็ว

---

## 47.2 ⭐ multi-vector (dense+sparse+colbert) — เก็บยังไง

bge-m3 (Ch7) ให้ 3 แบบ — layout ต่างกัน:
```
dense (1 vec × 1024):        columnar block ต่อเนื่อง → scan/SIMD ตรงๆ (Ch44)
sparse (Ch34, term:weight):  ไม่เก็บ dense array — เก็บ inverted index (term → postings)
                              เพราะส่วนใหญ่เป็น 0 (เก็บเฉพาะ non-zero)
colbert (Ch40, m token vec): ragged (แต่ละ doc token ไม่เท่า) → offset array + flat pool
                              [offsets: doc1@0, doc2@200...][flat: all token vecs]
```
- 3 modality = 3 storage strategy → ทำไม hybrid engine ซับซ้อนกว่า dense-only
- ARRA ใช้ dense เป็นหลัก (Ch4) → layout ตรงไปตรงมา (columnar block)

---

## 47.3 memory-map (mmap) — ดิสก์เหมือนแรม

index ใหญ่กว่าแรม → mmap ให้ OS จัดการ:
```
mmap(index_file) → เข้าถึงเหมือน array ในแรม
OS page cache: page ที่ใช้บ่อย → cache ในแรม · ไม่ใช้ → อยู่ดิสก์
→ ค้น doc ยอดฮิต (Ch13 heat) → page ร้อน → อยู่แรม → เร็ว
→ ค้น doc เย็น → page fault → โหลดจากดิสก์ (ช้าครั้งเดียว แล้ว cache)
```
- **ได้ฟรี**: OS page cache = LRU cache อัตโนมัติ (สอดคล้อง Ch13 heat, Ch32 cache) · ไม่ต้องเขียนเอง
- LanceDB/Faiss รองรับ mmap → index > RAM ได้ (Ch48)

---

## 47.4 cache locality กับ ANN layout

```
IVF (Ch3):   เวกเตอร์ใน cluster เดียวกัน → เก็บติดกันในดิสก์ (cluster-contiguous)
             → ค้น cluster → อ่าน sequential (prefetch friendly) ✓
HNSW (Ch17): graph → neighbor อาจกระจัดกระจายในไฟล์ → random access เยอะ
             → cache miss เยอะกว่า IVF → ทำไม HNSW กิน RAM (อยากได้ทั้ง graph ในแรม)
```
- **trade layout**: IVF ดี disk locality · HNSW ดี recall/speed แต่ต้องการแรม → เลือกตาม RAM budget (Ch48)

---

## 47.5 alignment & padding (ระดับ byte)

```
SIMD (Ch44) เร็วสุดเมื่อเวกเตอร์ align 32/64-byte boundary
1024 × float32 = 4096 bytes → align ดีอยู่แล้ว (หาร 64 ลงตัว)
มิติแปลก (เช่น 768+3 meta) → pad ให้ align → SIMD ไม่สะดุด
```
- library จัดการให้ (LanceDB/Faiss) — แต่เข้าใจไว้ว่าทำไมมิติ "กลม" (768/1024) นิยม

---

## 47.6 เชื่อม ARRA

```
LanceDB columnar (§47.1) → scan vector sequential + SIMD (Ch44) → เร็ว
dense-only layout (§47.2) → ตรงไปตรงมา (ไม่ต้องจัดการ 3 modality)
mmap (§47.3) → index > RAM ได้ + OS page cache = heat-aware ฟรี (Ch13)
→ ARRA ได้ layout performance โดยไม่ต้องเขียน storage engine เอง (ยืน LanceDB)
```

---

## สรุป Ch47
```
layout กระทบ latency 100× (cache line 64B, RAM 100ns vs SSD 100µs) — algorithm มองข้าม
columnar (SoA) ชนะ vector scan (sequential+SIMD) → LanceDB columnar = เหตุผลเชิง layout
multi-vector: dense=columnar block, sparse=inverted index, colbert=ragged offset+flat pool
mmap: ดิสก์เหมือนแรม + OS page cache = LRU ฟรี (สอดคล้อง heat Ch13) → index>RAM ได้
locality: IVF cluster-contiguous (prefetch ดี) vs HNSW random (กิน RAM)
align 64B → SIMD ไม่สะดุด → ทำไมมิติ 768/1024 นิยม
```
**ถัดไป Ch48:** disk vs memory index — เมื่อ corpus > RAM, DiskANN, SSD-optimized ANN, quantize-in-RAM + full-on-disk
---
*grounded: columnar (Lance/Arrow) · mmap/page cache · IVF vs HNSW locality · SIMD alignment · เชื่อม Ch1/3/4/7/13/17/32/34/40/44 · /loop deep iter 2026-07-16*
