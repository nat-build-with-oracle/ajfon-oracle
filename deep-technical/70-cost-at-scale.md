# Deep Technical · Chapter 70 — Vector DB Cost-at-Scale

> ต่อจาก Ch69 · Ch24 เกริ่น cost model · บทนี้ลงลึก: คำนวณต้นทุนจริงต่อ 1M vector, quantize ประหยัดเท่าไร, local vs cloud break-even

---

## 70.0 3 แกนต้นทุน

```
storage:  เก็บ vector + index + metadata (ต่อ GB-month)
compute:  embed (ingest) + search (query) — CPU/GPU time
egress:   ส่งข้อมูลออก (cloud คิดเงิน bandwidth ขาออก) — มักถูกลืม!
```
- แต่ละแกนโตต่างกันตาม scale → optimize แกนที่แพงสุดของ workload

---

## 70.1 ⭐ storage cost ต่อ 1M vector (คำนวณจริง)

```
1M vec × 1024-dim × 4 bytes (fp32) = 4 GB (raw vectors)
+ index overhead (HNSW graph ~1.5-2×) = ~6-8 GB
+ metadata/text = แล้วแต่ (มัก 1-2× ของ vector)
รวม ~10 GB ต่อ 1M doc

quantize (Ch8):
  int8 (SQ):  4 bytes → 1 byte → vectors 4GB→1GB (4×)
  PQ (Ch8):   → 4GB→256MB (16×+) เสีย recall นิด (rerank fp32 Ch8/48)
```
- **นี่คือเหตุผล quantize คุ้ม at scale**: 100M doc → fp32 400GB vs PQ 25GB (ต่างมหาศาลค่า storage)

---

## 70.2 compute cost — embed vs search

```
embed (ingest, ครั้งเดียวต่อ doc):
  1M doc × embed → GPU time หรือ cloud API (ต่อ 1k token, Ch24)
  batch (Ch51) ลด overhead → แต่ token count คงที่
search (ทุก query, ต่อเนื่อง):
  ANN (Ch3) เร็ว → CPU ถูก · แต่ rerank (Ch18 cross-encoder) แพง (ต่อ query!)
  → rerank เฉพาะ top-k เล็ก (Ch18/44) = คุมต้นทุน query
```
- **embed = one-time (amortize), search = recurring** → query ยอดเยอะ → search cost ครอบงำระยะยาว
- cache (Ch32) ลด search cost (query ซ้ำไม่คำนวณใหม่)

---

## 70.3 ⚠️ egress — ต้นทุนที่ซ่อน

```
cloud vector DB คิด egress (ข้อมูลออก):
  ค้น → ส่ง result (vectors/text) กลับ app → นับ egress
  ย้าย provider / backup ออก → egress ก้อนใหญ่ (vendor lock-in ทางต้นทุน)
```
- **local (ARRA)**: ไม่มี egress (ในเครื่อง) → ประหยัดแกนที่ cloud มักคิดแพง
- ระวัง: cross-region (Ch69) traffic = egress ด้วย → geo ผิดที่ = ค่า bandwidth บาน

---

## 70.4 ⭐ local vs cloud break-even

```
local (ARRA/self-host):
  fixed: เครื่อง (มี GPU?) + ไฟ + เวลา maintain
  marginal: ~0 ต่อ query (ใช้ hardware ตัวเอง)
cloud (Vectorize/Pinecone):
  fixed: ~0 (pay-as-go)
  marginal: ต่อ query + storage GB-month + egress

break-even: query volume ต่ำ → cloud ถูก (ไม่ต้องซื้อเครื่อง)
            query volume สูง/ต่อเนื่อง → local ถูกกว่า (amortize hardware)
```
- **ARRA personal**: corpus เล็ก (Ch48) + query ส่วนตัว → **local ชนะขาด** (เครื่องมีอยู่แล้ว, 0 marginal, 0 egress, privacy)
- cloud คุ้มเมื่อ: spiky traffic, ไม่อยากดูแล infra, global (Ch69)

---

## 70.5 cost optimization checklist

```
1. quantize (Ch8): storage 4-16× ถูกลง (§70.1) — ผลกระทบใหญ่สุดที่ scale
2. cache (Ch32): ลด compute query ซ้ำ
3. rerank เฉพาะ top-k (Ch18): คุม cross-encoder cost ต่อ query
4. local embedder (Ollama): ตัด embed API cost (Ch4 fallback)
5. tier storage (Ch48): hot in RAM, cold on disk/S3 (ถูกกว่า)
6. ระวัง egress (§70.3): keep traffic in-region, local = 0 egress
7. right-size (Ch46/48): personal ไม่ต้อง billion-scale infra (scale-appropriate)
```

---

## 70.6 เชื่อม ARRA

```
ARRA local: storage=ดิสก์ตัวเอง (ถูก), compute=CPU/GPU ตัวเอง (0 marginal), egress=0
  → personal cost ≈ ไฟ + เวลา → ถูกสุดสำหรับ single-user (§70.4)
quantize (Ch8) พร้อมใช้ถ้า corpus โต · cache (Ch32) ลด compute
Vectorize (Ch14): pay-per-use → คุ้มถ้า global/spiky, แต่ personal local ถูกกว่า
→ สอน community: "second brain ส่วนตัว = local คุ้มสุด (ฟรีนอกจากไฟ) + privacy"
```

---

## สรุป Ch70
```
3 แกน: storage (GB-month) · compute (embed one-time + search recurring) · egress (ซ่อน!)
⭐ storage/1M vec: fp32 ~10GB → quantize int8 4× / PQ 16× ถูกลง (คุ้มที่ scale, Ch8)
compute: embed=one-time amortize · search=recurring (query เยอะ→ครอบงำ) → cache+rerank top-k คุม
⚠️ egress: cloud คิดข้อมูลออก (lock-in) · cross-region=egress · local=0
⭐ break-even: query ต่ำ→cloud, สูง/ต่อเนื่อง→local · ARRA personal=local ชนะ (0 marginal/egress+privacy)
optimize: quantize>cache>rerank top-k>local embed>tier>ระวัง egress>right-size
```
**ถัดไป Ch71:** multi-modal retrieval ops — เก็บ/ค้น image+text+audio embedding ร่วมกัน, cross-modal search production, CLIP-style ในระบบจริง
---
*grounded: cost model (storage/compute/egress) · quantize savings (Ch8) · local vs cloud break-even · Vectorize pricing (Ch14/24) · เชื่อม Ch8/18/24/32/46/48/69 · /loop deep iter 2026-07-16*
