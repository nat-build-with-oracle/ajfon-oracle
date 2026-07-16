# Deep Technical · Chapter 16 — Efficient Attention (แก้ O(n²))

> ต่อจาก Ch15 · Ch10 §10.6 บอกว่า self-attention = O(n²·d) → context ยาวแพง (bge-m3 8192!) · บทนี้: แก้ยังไง

---

## 16.0 ทวนปัญหา

```
QKᵀ = n×n เมทริกซ์ → O(n²·d) compute + O(n²) memory
n=8192 → 67M ช่อง × d → embed doc ยาว = คอขวด (Ch ecosystem: bulk indexing หนัก)
```
2 มิติที่แพง: **compute** (คูณ) และ **memory** (เก็บเมทริกซ์ n×n)

---

## 16.1 FlashAttention — IO-aware (ไม่ลด compute แต่ลด memory IO)

**Insight**: bottleneck จริงบน GPU ไม่ใช่ FLOPs แต่คือ **การอ่าน/เขียน memory** (HBM ช้ากว่า SRAM มาก) · attention มาตรฐานเขียนเมทริกซ์ n×n ลง HBM แล้วอ่านกลับ = IO ระเบิด

**FlashAttention**: ไม่ materialize เมทริกซ์ n×n เต็มเลย
```
- แบ่ง Q,K,V เป็น block (tiling) ที่ใส่ SRAM ได้
- คำนวณ attention ทีละ block, สะสมผลด้วย "online softmax"
- ไม่เขียน n×n ลง HBM → IO ลดจาก O(n²) เหลือ ~O(n²/M) (M=SRAM size)
```

**Online softmax** (หัวใจ — คำนวณ softmax แบบ streaming ไม่ต้องเห็นทั้งแถว):
```
รักษา running max m และ running sum ℓ
เจอ block ใหม่ → update:  m_new = max(m, block_max)
                         ℓ_new = ℓ·e^{m−m_new} + Σe^{x−m_new}
                         rescale ผลสะสมด้วย e^{m−m_new}
```
- ได้ softmax ที่ถูกต้องเป๊ะ (ไม่ approximate!) แต่ไม่ต้อง buffer ทั้งแถว → memory O(n) ไม่ใช่ O(n²)
- **exact, เร็วขึ้น 2-4×, memory เชิงเส้น** → ทำ context ยาว (8192+) practical

---

## 16.2 Linear Attention — ลด compute เป็น O(n)

FlashAttention ยัง O(n²) compute (แค่ IO ดีขึ้น) · Linear attention ลด **compute** ด้วย kernel trick:
```
softmax(QKᵀ)V  ≈  φ(Q) (φ(K)ᵀ V)
```
- แทน `(QKᵀ)V` [ทำ n×n ก่อน = O(n²)] → `Q(KᵀV)` [ทำ d×d ก่อน = O(n·d²)]
- **associativity**: จับกลุ่มใหม่ → n²→n (linear ใน n!)
- แลก: `φ` (feature map) approximate softmax → คุณภาพลดบ้าง · เหมาะ context ยาวมากที่ยอม approximate

**complexity**: O(n·d²) แทน O(n²·d) → เมื่อ n ≫ d (context ยาว) = ชนะมาก

---

## 16.3 Sparse / Local Attention — attention ไม่ต้องดูทุกคู่

ไม่ใช่ทุก token ต้องสนใจทุก token · จำกัดให้ดูแค่บางส่วน:
- **local/sliding window**: token ดูเพื่อนบ้าน ±w เท่านั้น → O(n·w)
- **strided/dilated**: ดูทุกๆ k token → จับ long-range แบบเบาบาง
- **global tokens**: บาง token (เช่น [CLS]) ดูทุกตัว, ที่เหลือ local → BigBird/Longformer
- แลก: อาจพลาด dependency ไกลบางคู่ · เหมาะงานที่ context locality สูง

---

## 16.4 ทำไมสำคัญกับ ARRA

- **bge-m3 8192 ctx**: ยาวได้เพราะ efficient attention (FlashAttention ทำให้ train/infer context ยาว practical) → embed paper/note ยาวได้ในทีเดียว (ลดความจำเป็น chunk, Ch12)
- **bulk indexing** (คอขวด): embed พันๆ docs · efficient attention = แต่ละ embed เร็วขึ้น → index เร็วขึ้น
- **query-time เบาอยู่แล้ว** (1 query สั้น) → efficient attention ช่วย index-time เป็นหลัก (ตรงกับ Ch ecosystem: คอขวด = indexing ไม่ใช่ serving)

---

## 16.5 ตารางเทียบ

| วิธี | compute | memory | exact? |
|---|---|---|---|
| Vanilla | O(n²d) | O(n²) | ✅ |
| FlashAttention | O(n²d) | **O(n)** | ✅ (exact!) |
| Linear | **O(nd²)** | O(nd) | ❌ approx |
| Sparse/Local | O(nwd) | O(nw) | ❌ (จำกัด scope) |

→ production ส่วนใหญ่ใช้ **FlashAttention** (exact + เร็ว) เป็น default · linear/sparse เมื่อ context ยาวสุดขั้ว

---

## สรุป Ch16
```
O(n²) ของ attention (Ch10) แก้ได้:
  FlashAttention: tiling + online softmax → memory O(n), exact, 2-4× เร็ว (IO-aware)
  Linear: kernel trick Q(KᵀV) → compute O(nd²), approximate
  Sparse/local: จำกัด scope → O(nw)
→ ทำให้ bge-m3 8192 ctx + bulk indexing practical (index-time bottleneck)
```
**ถัดไป Ch17:** HNSW construction ลึก — สร้างกราฟยังไง (layer assignment แบบ exponential, neighbor selection heuristic), พิสูจน์ O(log n) search

---
*grounded: FlashAttention (Dao et al. 2022) · Linear attention (Katharopoulos 2020) · Longformer/BigBird · เชื่อม Ch10 §10.6, Ch12, Ch ecosystem (bulk-index bottleneck) · /loop deep iter 2026-07-13*
