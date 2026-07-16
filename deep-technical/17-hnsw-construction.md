# Deep Technical · Chapter 17 — HNSW Construction & O(log n) Proof

> ต่อจาก Ch16 · Ch3 §3.5 อธิบาย HNSW **search** · บทนี้: สร้างกราฟยังไง + พิสูจน์ทำไม search เป็น O(log n)

---

## 17.0 ทวน: HNSW = skip list บนกราฟ

กราฟหลายชั้น · node = เวกเตอร์ · edge = "เพื่อนบ้านใกล้" · ชั้นบนเบาบาง (กระโดดไกล) ชั้นล่างหนาแน่น (ละเอียด) · search = greedy descent (Ch3)

---

## 17.1 Insert algorithm (สร้างทีละ node)

```
insert(q):
  1. l ← สุ่มชั้นสูงสุดของ q  (§17.2)
  2. ep ← entry point (ชั้นบนสุดของกราฟ)
  3. for lc = top down to l+1:        # navigate ลงมาถึงชั้น l
       ep ← greedy_search(q, ep, ef=1) at layer lc
  4. for lc = min(l, top) down to 0:  # เชื่อม q ที่ทุกชั้น ≤ l
       W ← search(q, ep, efConstruction) at layer lc     # หา candidate
       neighbors ← select_M(W)                            # §17.3
       เชื่อม q ↔ neighbors (สองทาง)
       ถ้า neighbor มี degree > M_max → prune
       ep ← W
```
- `efConstruction` = ขนาด candidate pool ตอนสร้าง (มาก = กราฟดี/สร้างช้า)
- `M` = จำนวน edge ต่อ node ต่อชั้น

---

## 17.2 ⭐ Layer assignment — exponential distribution

ชั้นสูงสุดของแต่ละ node สุ่มจาก **geometric/exponential**:
```
l = floor( −ln(uniform(0,1)) · mₗ )        mₗ = 1/ln(M)
```
→ P(node อยู่ชั้น ≥ k) ลดลงแบบ **exponential** ตาม k
- ชั้น 0: ทุก node (n ตัว)
- ชั้น 1: ~n/M ตัว
- ชั้น 2: ~n/M² ตัว
- ชั้น k: ~n/Mᵏ ตัว

→ จำนวนชั้น ≈ **log_M(n)** · นี่คือรากของ O(log n) (§17.4)

**ทำไม exponential**: เลียน skip list — แต่ละชั้นบนมี node เป็นเศษส่วนคงที่ของชั้นล่าง → กระโดดข้ามระยะทางเป็นสัดส่วนคงที่ต่อชั้น → รวม log ชั้น

---

## 17.3 Neighbor selection heuristic (ไม่ใช่แค่ M ตัวใกล้สุด)

เลือกเพื่อนบ้านแบบฉลาด (ไม่ใช่แค่ top-M nearest):
```
select_neighbors_heuristic(q, C, M):
  result ← []
  for e in sorted(C by distance to q):
     if |result| < M and e "ใกล้ q มากกว่าใกล้ทุกตัวใน result":
        result.add(e)
  return result
```
- **หลีกเลี่ยง cluster ซ้ำ**: ถ้าเลือกแต่ตัวใกล้สุด อาจได้เพื่อนบ้านกระจุกทิศเดียว → กราฟ "ตัน" · heuristic เลือกให้**กระจายทิศ** → กราฟ navigable ดี (ไปถึงทุกที่ได้)
- นี่คือความต่างระหว่าง HNSW ดีกับห่วย — heuristic นี้แหละ

---

## 17.4 พิสูจน์ O(log n) search (sketch)

**Claim**: greedy search เยี่ยม node เฉลี่ย O(log n)

**เหตุผล** (probabilistic):
1. จำนวนชั้น = O(log_M n) (§17.2) — ลงชั้นละครั้ง = O(log n) ระดับ
2. **ต่อชั้น**: greedy เดินไม่กี่ hop ก่อนติด local min แล้วลงชั้นถัดไป · ในกราฟ "navigable small world" ที่สร้างดี จำนวน hop ต่อชั้น = O(1) เฉลี่ย (degree M คงที่ + heuristic กระจายทิศ → แต่ละ hop ตัดระยะได้สัดส่วนคงที่)
3. รวม: O(log n) ชั้น × O(1) hop/ชั้น × O(M·d) ต่อ hop (คำนวณ distance กับ M เพื่อนบ้าน) = **O(M·d·log n)**

→ เทียบ brute-force O(n·d): HNSW ชนะเมื่อ n ใหญ่ (log n ≪ n) · n=1M → log₂ ≈ 20 vs n=1,000,000 = ชนะ 50,000×

**caveat**: "navigable small world" property ต้องสร้างมาดี (§17.3 heuristic) · ถ้ากราฟห่วย → greedy ติด local min → recall ตก (ต้อง efSearch สูงชดเชย)

---

## 17.5 Delete/Update — จุดอ่อนของ HNSW

- **delete ยาก**: ลบ node = ทิ้ง edge → กราฟขาด/ตัน · ส่วนใหญ่ทำ "soft delete" (mark tombstone) แล้ว rebuild เป็นระยะ
- **update = delete + insert** = แพง
- นี่คือเหตุผล ARRA (memory เพิ่ม/แก้บ่อย) อาจเหมาะ **IVF/Flat** (LanceDB, Ch3 §3.6) มากกว่า HNSW ล้วน — insert/update ถูกกว่า, และ 35k docs ยังไม่ต้องการ log-scale ของ HNSW

---

## 17.6 พารามิเตอร์สรุป

| param | ตอน | มาก → | trade |
|---|---|---|---|
| M | build | กราฟแน่น recall↑ | index ใหญ่, build ช้า |
| efConstruction | build | กราฟคุณภาพดี | build ช้า |
| efSearch | search | recall↑ | query ช้า |
| mₗ (1/ln M) | build | (คุมจำนวนชั้น) | — |

---

## สรุป Ch17
```
insert: สุ่มชั้น (exponential) → navigate ลง → เชื่อม M เพื่อนบ้าน (heuristic กระจายทิศ)
layer exponential → จำนวนชั้น O(log_M n) = รากของ O(log n)
proof: O(log n) ชั้น × O(1) hop/ชั้น × O(Md) = O(Md·log n)
delete/update แพง (soft delete + rebuild) → ARRA เล็ก+แก้บ่อย = IVF/Flat เหมาะกว่า
```
**ถัดไป Ch18:** cross-encoder reranker math — สถาปัตย์, loss (pointwise/pairwise/listwise), bge-reranker-v2-m3, ทำไมช้าแต่แม่น, distillation กลับไป embedding

---
*grounded: HNSW (Malkov & Yashunin 2016, การพิสูจน์ navigable small world) · skip list (Pugh 1990) · เชื่อม Ch3 §3.5-3.6, Ch16 · /loop deep iter 2026-07-13*
