# Deep Technical · Chapter 48 — Disk vs Memory Index (DiskANN)

> ต่อจาก Ch47 · layout ดีแล้ว แต่ถ้า corpus > RAM ทำไง? · บทนี้: DiskANN, SSD-optimized ANN, quantize-in-RAM

---

## 48.0 ปัญหา — corpus โตเกินแรม

```
1M doc × 1024-dim × 4 bytes = 4 GB      → พอในแรม
100M doc                    = 400 GB     → เกินแรมเครื่องปกติ
1B doc                      = 4 TB       → ต้องดิสก์
```
HNSW (Ch17) อยากได้ทั้ง graph ในแรม (Ch47 §47.4) → ไม่ scale เกินแรม · ต้องกลยุทธ์ดิสก์

---

## 48.1 3 ทางเลือกเมื่อเกินแรม

```
1. quantize ให้พอแรม (Ch8):  บีบ 4 bytes → 1 byte (int8) หรือ PQ → 4GB→512MB
                              → 100M doc พอแรมด้วย PQ · เสีย recall นิด → rerank ด้วย full (Ch8/36)
2. sharding (Ch25):          กระจายหลายเครื่อง, แต่ละเครื่องถือ subset ในแรม
3. disk-based ANN (DiskANN): เก็บ index บน SSD, แรมถือแค่ส่วนย่อ → §48.2
```

---

## 48.2 ⭐ DiskANN — ANN บน SSD

DiskANN (Microsoft) ออกแบบ graph index ที่อยู่บน SSD เป็นหลัก:
```
แรม (เล็ก):  quantized vectors (PQ, Ch8) ของทุก doc — ใช้ nav คร่าวๆ
SSD (ใหญ่):  full-precision vectors + graph adjacency

ค้น:
1. ไต่ graph โดยใช้ PQ ในแรม (ประมาณ distance) → หา candidate
2. อ่าน full vector ของ candidate จาก SSD (ไม่กี่ครั้ง) → distance แม่น → rerank
3. คุมจำนวน SSD read (แพงสุด) ให้น้อย → latency ยอมรับได้ (~ไม่กี่ ms)
```
- **หัวใจ**: minimize SSD random reads (ตัวช้าสุด, Ch47) · PQ-in-RAM นำทาง, full-on-SSD ยืนยัน
- ได้ recall ใกล้ in-memory ที่ scale พันล้าน ด้วยแรมเสี้ยวเดียว

---

## 48.3 quantize-in-RAM + full-on-disk (pattern ทั่วไป)

DiskANN = กรณีเฉพาะของ pattern กว้าง (สอดคล้อง Ch8 §8.7, Ch36 §36.5):
```
แรม: representation ย่อ (PQ/int8/Matryoshka สั้น) → เร็ว, ประมาณ
ดิสก์: representation เต็ม → แม่น, ช้า
ค้น: ย่อคัดคร่าว (แรม) → เต็มยืนยัน (ดิสก์) เฉพาะ candidate
```
- นี่คือ **coarse-to-fine เชิง storage** (คู่กับ coarse-to-fine เชิง compute, Ch8/40)
- หลักเดียวกันทุกที่: ถูก/เร็ว/ประมาณ ก่อน → แพง/ช้า/แม่น ทีหลังเฉพาะที่จำเป็น

---

## 48.4 ARRA — อยู่ตรงไหนของสเปกตรัม

```
second brain ส่วนตัว: หมื่น-แสน doc → 40MB-400MB → พอในแรมสบาย
→ ARRA ไม่ต้อง DiskANN · in-memory (หรือ mmap Ch47) พอ
→ latency ต่ำ (ทุกอย่างในแรม), ไม่ซับซ้อน
```
- **DiskANN จำเป็นเมื่อ**: หลายสิบล้าน doc+ (องค์กร, ทุกคนรวมกัน) → ต่างจาก personal ARRA
- **บทเรียน scale-appropriate (ย้ำ Ch46)**: personal = in-memory · enterprise = quantize/shard/DiskANN → เลือกตามขนาดจริง อย่าเอา infra billion-scale มาใส่ personal

---

## 48.5 Cloudflare Vectorize (Ch14) — managed disk/memory

ARRA edge (Ch5/14) ใช้ Vectorize → CF จัดการ storage tier ให้:
```
เราไม่เห็น disk vs memory — Vectorize จัดการ (น่าจะ quantize + tiered ภายใน)
เราแค่ upsert/query → CF คุม scale (Ch25) + storage (Ch48) หลังบ้าน
→ trade: ควบคุมน้อยลง แต่ไม่ต้องจัดการ DiskANN เอง (managed)
```

---

## สรุป Ch48
```
corpus > RAM: quantize (Ch8, พอแรม) | shard (Ch25) | disk-based (DiskANN)
⭐ DiskANN: PQ-in-RAM นำทาง + full-on-SSD ยืนยัน → minimize SSD reads → billion-scale, แรมน้อย
pattern: quantize-in-RAM + full-on-disk = coarse-to-fine เชิง storage (คู่ Ch8/40 เชิง compute)
ARRA personal (หมื่น-แสน = <400MB) → in-memory/mmap พอ, ไม่ต้อง DiskANN (scale-appropriate)
Vectorize (Ch14) = managed tier → CF จัดการ disk/memory ให้
```
**ถัดไป Ch49:** OS page cache & mmap ลึก — page fault, prefetch, madvise, working set, ทำไม heat (Ch13) ทำงานร่วม page cache
---
*grounded: DiskANN (Subramanya 2019) · PQ (Ch8) · sharding (Ch25) · Vectorize (Ch14) · scale-appropriate (Ch46) · เชื่อม Ch5/8/17/25/36/40/47 · /loop deep iter 2026-07-16*
