# Deep Technical · Chapter 49 — OS Page Cache & mmap (deep)

> ต่อจาก Ch48 · Ch47 §47.3 เกริ่น mmap · บทนี้ลงลึก page fault, prefetch, madvise, working set — ทำไม heat (Ch13) ทำงานร่วม page cache

---

## 49.0 mmap คืออะไรจริงๆ (ระดับ OS)

```
mmap(fd) → map ไฟล์เข้า virtual address space ของ process
เข้าถึง ptr[i] เหมือน array → ไม่มี read() syscall ต่อครั้ง
OS จัดการ: page ไหนอยู่ RAM (resident), page ไหนยังบนดิสก์
```
- page = หน่วยของ memory (มัก 4KB) · เวกเตอร์ 1024×4 = 4KB = พอดี 1 page

---

## 49.1 page fault — กลไกโหลด lazy

```
เข้าถึง ptr[i] ที่ page ยังไม่ resident:
1. CPU raise page fault (hardware trap)
2. OS kernel: หา page บนดิสก์ → อ่านเข้า RAM → update page table
3. resume — โปรแกรมทำต่อเหมือนไม่มีอะไร (แต่ช้า ~100µs ครั้งนั้น)

minor fault: page อยู่ RAM แล้ว (cache) แค่ map → เร็ว (~ns)
major fault: ต้องอ่านดิสก์ → ช้า (SSD 100µs, HDD 10ms)
```
- **latency spike (Ch44 p99)** มักมาจาก major fault (query แตะ doc เย็นที่ swap ออก)

---

## 49.2 ⭐ page cache = LRU ฟรีที่ align กับ heat (Ch13)

OS เก็บ page ที่อ่านล่าสุดใน RAM (page cache) · evict แบบ LRU-ish เมื่อ RAM เต็ม:
```
doc ยอดฮิต (Ch13 usage_count สูง) → ถูกค้นบ่อย → page อยู่ RAM เสมอ (hot, minor fault)
doc เย็น (ไม่ถูกแตะนาน) → page evict → บนดิสก์ (major fault ถ้าค้นเจอ)
```
- **นี่คือความสวยงาม**: retrieval heat (Ch13, application-level LRU/LFU) **สอดคล้องกับ OS page cache (kernel-level LRU)** โดยไม่ตั้งใจ → doc ร้อนเร็วสองชั้น (logic + memory)
- ไม่ต้องเขียน cache เอง → OS ทำให้ (คู่กับ semantic cache Ch32 ที่ต้องเขียนเอง)

---

## 49.3 prefetch / readahead

OS เดาว่าจะอ่าน page ถัดไป → โหลดล่วงหน้า:
```
sequential access (columnar scan Ch47) → OS เห็น pattern → readahead → prefetch → เร็ว
random access (HNSW graph hop Ch47) → เดายาก → prefetch พลาด → fault เยอะ
```
- **นี่คือเหตุผลลึกอีกชั้น** ที่ columnar (Ch47) เร็ว: sequential → OS prefetch ช่วย · random → ไม่ช่วย

---

## 49.4 madvise — บอก OS ว่าจะใช้ยังไง

โปรแกรมบอกใบ้ OS ได้ผ่าน `madvise()`:
```
MADV_SEQUENTIAL: "จะอ่านเรียง" → OS readahead เยอะ (scan Ch47)
MADV_RANDOM:     "จะอ่านสุ่ม" → OS ไม่ readahead (ประหยัด, HNSW)
MADV_WILLNEED:   "จะใช้เร็วๆ นี้" → OS prefetch ตอนนี้ (warm index ก่อน query แรก, ลด p99 Ch44)
MADV_DONTNEED:   "ไม่ใช้แล้ว" → evict ได้ (คืน RAM)
```
- library (Faiss/LanceDB) ใช้ madvise จูน pattern การอ่าน index → performance โดยไม่ต้อง copy เข้า RAM เอง

---

## 49.5 working set — RAM เท่าไรพอ

```
working set = set ของ page ที่ถูกแตะบ่อยในช่วงเวลาหนึ่ง
ถ้า working set พอดี RAM → fault น้อย (ส่วนใหญ่ minor) → เร็ว
ถ้า working set > RAM → thrashing (fault เยอะ, swap ตลอด) → ช้ามาก
```
- **heat (Ch13) ทำ working set เล็ก**: query จริงกระจุกที่ doc ร้อนไม่กี่ % → working set << corpus → index ใหญ่กว่า RAM ได้ ถ้า hot subset พอดี RAM (คู่กับ DiskANN Ch48)
- power-law ของ access (ค้น doc บางตัวบ่อยมาก) → RAM แค่พอ hot set = ครอบ query ส่วนใหญ่

---

## 49.6 เชื่อม ARRA

```
LanceDB mmap index (Ch47) → OS page cache (§49.2) = heat-aware ฟรี (สอดคล้อง Ch13)
columnar (Ch47) → sequential → OS prefetch (§49.3) ช่วย → scan เร็ว
warm index: MADV_WILLNEED ตอน start (§49.4) → query แรกไม่ major-fault → p99 ดี (Ch44)
working set เล็ก (heat power-law §49.5) → RAM พอดี hot set → corpus > RAM ได้โดยไม่ thrash
```
- **สรุป: OS ทำงานหนักให้ ARRA ฟรี** — page cache/prefetch/mmap = performance ที่ไม่ต้องเขียนเอง

---

## สรุป Ch49
```
mmap: map ไฟล์เป็น array, OS จัดการ page (4KB) resident/on-disk (ไม่ read() ต่อครั้ง)
page fault: minor (RAM, ns) vs major (ดิสก์, 100µs) → major = p99 spike (Ch44)
⭐ page cache = LRU ฟรี align กับ heat (Ch13): doc ร้อน→RAM, เย็น→ดิสก์ (สองชั้น logic+kernel)
prefetch: sequential (columnar Ch47) OS ช่วย, random (HNSW) ไม่ช่วย → ลึกอีกชั้นทำไม columnar เร็ว
madvise: SEQUENTIAL/RANDOM/WILLNEED(warm)/DONTNEED → จูน pattern การอ่าน
working set: hot subset พอดี RAM → corpus>RAM ได้ (heat power-law) ไม่ thrash
```
**ถัดไป Ch50:** numerical precision — fp32/fp16/bf16/int8 ใน embedding+distance, error accumulation, ทำไม normalize สำคัญเชิงตัวเลข
---
*grounded: mmap/page fault (OS) · madvise(2) · working set (Denning) · power-law access · เชื่อม Ch13/32/44/47/48 · /loop deep iter 2026-07-16*
