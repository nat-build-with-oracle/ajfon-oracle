# Deep Technical · Chapter 44 — Query Latency Optimization

> ต่อจาก Ch43 · Ch3 = ANN เร็วเชิง algorithm · บทนี้: **ทำให้ค้นเร็วในระดับ engineering** — budget, SIMD, batching, early termination, p99 tail

---

## 44.0 latency budget — แยกส่วนก่อน optimize

query ครั้งหนึ่งใน ARRA (hybrid, Ch4) ประกอบด้วย:
```
1. embed query     ~30-80ms   ← เรียก embedder (Ollama/CF, Ch4 timeout 30s)  ★ตัวใหญ่สุด
2. vector search    ~1-10ms    ← ANN (Ch3) บน N docs
3. FTS5 (BM25)      ~1-5ms     ← inverted index (Ch34)
4. RRF merge        <1ms       ← รวมคะแนน (Ch4/11)
5. rerank (opt)     ~50-200ms  ← cross-encoder top-k (Ch18)  ★ตัวใหญ่ที่สอง
─────────────────────────────
รวม: ~35-100ms (no rerank) · ~85-300ms (with rerank)
```
- **กฎ optimize**: วัดก่อน (Ch23 histogram) → โจมตีตัวใหญ่สุด · ที่นี่ = **embed + rerank** ไม่ใช่ ANN

---

## 44.1 embed คือคอขวด — วิธีลด

embedding เป็น network call (Ch4) → ช้าสุด · ลดได้:
```
1. cache query embedding (Ch32 §32.2) — query ซ้ำ → ข้าม embed
2. local embedder (Ollama บนเครื่อง) < network (Gemini/CF cloud RTT)
3. batch หลาย query (Ch44 §44.3)
4. โมเดลเล็กลง (bge-m3 → เล็กกว่า) trade recall (Ch43 rate-distortion)
5. quantize embedder (int8 inference) — เร็วขึ้น เสีย quality นิด
```
- **ที่ ARRA**: fallback chain (Ch4) เลือก provider เร็วสุดที่ available → local Ollama เป็น floor latency

---

## 44.2 ⭐ SIMD — เร่ง distance ระดับ CPU

cosine/dot (Ch1) = loop คูณสะสม → CPU ทำทีละ lane ได้หลายตัวพร้อมกัน:
```
scalar:  for i: dot += a[i]*b[i]        1 มัลติ/รอบ
SIMD:    AVX-512 → 16 float32/รอบ       16× throughput
         โหลด a[0..15], b[0..15] → FMA (fused multiply-add) → รวม
```
- library เร็ว (Faiss, LanceDB core) เขียน distance ด้วย SIMD intrinsic / auto-vectorize
- int8 (Ch8) SIMD ยิ่งเร็ว (VNNI: 64 int8/รอบ) → ทำไม quantize เร็วขึ้นจริง
- **ARRA (LanceDB, Ch4)**: distance ทำใน Rust core (SIMD) ไม่ใช่ JS → เร็วโดยไม่ต้องเขียนเอง

---

## 44.3 Batching — throughput vs latency

query หลายอันมาพร้อมกัน → embed/search รวม batch:
```
1 query:    1 GPU call → 30ms → 1 result   (33 qps)
32 batch:   1 GPU call → 50ms → 32 results (640 qps)   ← throughput 19×!
```
- GPU/matrix ทำ batch เกือบฟรี (Ch10) → throughput พุ่ง
- **trade**: latency ต่อ query เพิ่มนิด (รอ batch เต็ม) → dynamic batching (รอ ≤5ms หรือ batch เต็ม แล้วยิง)
- เหมาะ server หลาย user · ARRA single-user local ไม่ค่อยได้ประโยชน์ตรงนี้ (แต่ ingest หลายไฟล์ = batch ได้, Ch4 batchSize 50)

---

## 44.4 Early termination — หยุดเมื่อพอ

ANN ไม่ต้องดูทุก candidate ถ้ามั่นใจ top-k แล้ว:
```
IVF (Ch3):  ดู nprobe cluster แรก → ถ้า top-k คะแนนห่างมากจาก cluster ถัดไป → หยุด
HNSW (Ch17): greedy หยุดเมื่อ neighbor ไม่ดีขึ้น (ef ควบคุม)
```
- trade recall (Ch3): หยุดเร็ว = อาจพลาด · ef/nprobe = knob latency↔recall
- **threshold ตัด**: ถ้า caller ขอแค่ score > 0.7 → หยุดเมื่อ candidate ต่ำกว่า (ไม่ค้นต่อ)

---

## 44.5 ⭐ p99 tail — ตัวที่ user รู้สึก

average latency โกหก · **p99 (Ch23 §23.4) คือที่ user เจอตอนแย่**:
```
avg 40ms ฟังดูดี · แต่ p99 = 800ms → 1% ของ query ช้า 20× → user รู้สึก "บางทีมันช้า"
```
สาเหตุ tail:
```
- cold cache (query แรก, Ch32) · embedder cold start
- fallback ทำงาน (provider หลักล่ม → ลอง Gemini, Ch4) → +RTT
- GC pause / CPU contention (Ch23)
- corpus segment ใหญ่ (index ไม่ balanced)
```
- **แก้ tail**: timeout + fallback เร็ว (Ch4 sticky, ไม่ retry ตัวที่ล่มซ้ำ) · warm cache · pre-load index
- **วัด**: p50/p95/p99 แยก (Ch23) ไม่ใช่ average อย่างเดียว

---

## 44.6 checklist optimize latency (สรุปปฏิบัติ)

```
1. วัดก่อน (histogram p50/p95/p99, Ch23) — หาคอขวดจริง
2. cache query embed + semantic cache (Ch32) — ตัด embed ซ้ำ
3. local embedder floor (Ollama) — ตัด network RTT
4. SIMD/quantize distance (Ch8) — ได้ฟรีจาก LanceDB Rust core
5. tune ef/nprobe (Ch3/17) — latency↔recall knob
6. rerank เฉพาะ top-k เล็ก (Ch18) — อย่า rerank เยอะ
7. เฝ้า p99 ไม่ใช่ average — tail คือที่ user รู้สึก
```

---

## สรุป Ch44
```
budget: embed (~30-80ms) + rerank (~50-200ms) = คอขวด, ไม่ใช่ ANN (~1-10ms)
embed ลด: cache/local/batch/quantize · SIMD: AVX 16 float/รอบ (int8 ยิ่งเร็ว) → LanceDB Rust ฟรี
batching: throughput 19× (trade latency/query) — server หลาย user
early termination: หยุด ANN เมื่อพอ (ef/nprobe knob) — trade recall
⚠️ p99 tail = ที่ user รู้สึก (avg โกหก) — cold cache/fallback/GC → warm+sticky fallback
วัดก่อน optimize (Ch23) → โจมตีตัวใหญ่สุด
```
**ถัดไป Ch45:** streaming / incremental index — เพิ่ม/ลบ doc โดยไม่ rebuild, index freshness, tombstone, compaction
---
*grounded: SIMD (AVX-512/VNNI) · Faiss/LanceDB Rust core · dynamic batching · p99 tail (tail-at-scale, Dean 2013) · เชื่อม Ch1/3/4/8/17/18/23/32 · /loop deep iter 2026-07-16*
