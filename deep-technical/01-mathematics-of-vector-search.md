# Deep Technical · Chapter 1 — คณิตศาสตร์ของ Vector Search

> ARRA Oracle · deep-dive series · /loop vector-teaching (deep mode)
> ลงลึกทั้งสมการและโค้ดจริง · grounded ใน `arra-oracle-v3/src/vector/*`
> เป้าหมาย: จาก "ค้นด้วยความหมาย" ระดับ intuition → ลงถึงพีชคณิตเชิงเส้นที่ทำงานจริง

---

## 1.0 ภาพรวม: vector search คือปัญหาเรขาคณิต

Full-text search ถามว่า *"เอกสารไหนมีคำนี้"* — เป็นปัญหา **string matching**
Vector search ถามว่า *"เอกสารไหนมีความหมายใกล้ที่สุด"* — เป็นปัญหา **nearest-neighbor ในปริภูมิเวกเตอร์**

ทุกอย่างในบทนี้ตอบคำถามเดียว: **"ใกล้" วัดยังไงด้วยตัวเลข?**

---

## 1.1 Embedding = จุดในปริภูมิ n มิติ

Embedding model แปลงข้อความ `t` เป็นเวกเตอร์ `v ∈ ℝⁿ`:

```
embed : Text → ℝⁿ
embed("งานวิจัยเบาหวาน") = v = (v₁, v₂, …, vₙ)
```

ค่า `n` (จำนวนมิติ) ขึ้นกับโมเดล — จากโค้ดจริง `KNOWN_DIMS` ใน `embeddings.ts`:

| model | n (มิติ) |
|---|---|
| all-MiniLM-L6-v2 | 384 |
| nomic-embed-text | 768 |
| bge-m3 | 1024 |
| qwen3-embedding:0.6b | 1024 |
| qwen3-embedding:4b | 2560 |
| qwen3-embedding:8b | 4096 |

แต่ละมิติ **ไม่ได้แปลว่าอะไรตรงๆ** (ไม่ใช่ "มิติที่ 5 = ความเป็นการแพทย์") — มันคือทิศทางนามธรรมที่โมเดลเรียนรู้มา สิ่งที่มีความหมายคือ **ตำแหน่งสัมพัทธ์** ระหว่างเวกเตอร์ ไม่ใช่ค่าสัมบูรณ์ของแต่ละแกน

**หลักการฝัง (จะลงลึกใน Chapter 2):** โมเดลถูกฝึกให้ข้อความที่ความหมายใกล้กัน → เวกเตอร์ชี้ไปทิศทางใกล้กัน (มุมระหว่างเวกเตอร์แคบ) นี่คือเหตุผลที่เราสนใจ **มุม** ไม่ใช่ระยะทางแบบยุคลิด

---

## 1.2 Dot product (ผลคูณจุด) — รากฐาน

สำหรับ `a, b ∈ ℝⁿ`:

```
        n
a · b = Σ  aᵢ bᵢ  =  a₁b₁ + a₂b₂ + … + aₙbₙ
       i=1
```

**ความหมายเชิงเรขาคณิต** — ทฤษฎีบทสำคัญที่ทุกอย่างต่อยอดมาจากนี้:

```
a · b = ‖a‖ ‖b‖ cos θ
```

โดย `θ` = มุมระหว่างเวกเตอร์ `a` กับ `b` · **นี่คือสะพานเชื่อมพีชคณิต (Σaᵢbᵢ) กับเรขาคณิต (มุม)**

- ถ้า `a` กับ `b` ชี้ทิศเดียวกัน → θ=0 → cos θ=1 → dot สูงสุด
- ถ้าตั้งฉาก → θ=90° → cos θ=0 → dot=0
- ถ้าทิศตรงข้าม → θ=180° → cos θ=−1 → dot ต่ำสุด

**ตัวอย่างเลขจริง** (`a=(1,2,3)`, `b=(4,5,6)`):
```
a · b = 1·4 + 2·5 + 3·6 = 4 + 10 + 18 = 32
```

---

## 1.3 Norm (ขนาด/ความยาวเวกเตอร์)

L2 norm (Euclidean norm):

```
        ______________       ____________
‖a‖ = √ Σ aᵢ²         = √ a₁² + a₂² + … + aₙ²
```

ตัวอย่าง: `‖a‖ = √(1²+2²+3²) = √14 ≈ 3.742` · `‖b‖ = √(4²+5²+6²) = √77 ≈ 8.775`

norm คือ "ความยาวลูกศร" — และเป็นตัวที่เราจะ **หารทิ้ง** เพื่อให้เหลือแค่ "ทิศทาง"

---

## 1.4 Cosine similarity — จัดสมการใหม่จาก 1.2

จาก `a · b = ‖a‖‖b‖ cos θ` ย้ายข้าง แก้หา `cos θ`:

```
              a · b            Σ aᵢbᵢ
cos θ = ─────────────  = ──────────────────────
          ‖a‖ ‖b‖         √(Σaᵢ²) · √(Σbᵢ²)
```

**นี่คือ cosine similarity** — วัด "ความคล้ายของทิศทาง" โดยไม่สนขนาด

- **ช่วงค่า**: [−1, 1] ทั่วไป · สำหรับ embedding ส่วนใหญ่ค่าเป็นบวก → มักอยู่ [0, 1]
- **ทำไมหาร norm**: เพื่อ **normalize** — เอกสารยาว vs สั้นไม่ควรต่างกันเพราะความยาว ควรต่างเพราะความหมาย · การหาร ‖a‖‖b‖ ลบผลของขนาดออก เหลือแค่มุม

**ตัวอย่างเลขจริง** (ต่อจาก 1.2–1.3):
```
cos θ = 32 / (3.742 × 8.775) = 32 / 32.84 ≈ 0.974
```
→ 0.974 ใกล้ 1 มาก = สองเวกเตอร์นี้ชี้ทิศเกือบเดียวกัน = "ความหมายใกล้กันมาก"

**โค้ดจริง (teaching demo `data/vector-cosine-demo.mjs`)** — ตรงกับสมการ 1:1:
```js
function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];   // Σ aᵢbᵢ           (สมการ 1.2)
    na  += a[i] * a[i];   // Σ aᵢ²  (ใต้ราก ‖a‖)
    nb  += b[i] * b[i];   // Σ bᵢ²  (ใต้ราก ‖b‖)
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb));   // สมการ 1.4
}
```

---

## 1.5 Cosine *distance* — สิ่งที่ LanceDB คืนมาจริง

ในโปรดักชัน ARRA Oracle ใช้ LanceDB (`src/vector/adapters/lancedb.ts`):
```ts
const results = await this.table.search(queryEmbedding)
  .distanceType('cosine')      // ← #2717 unify ให้ทุก path ใช้ cosine
  .limit(fetchLimit).toArray();
// แต่ละ row มี r._distance
```

LanceDB คืน **cosine distance** ไม่ใช่ similarity:

```
cosine_distance = 1 − cosine_similarity
```

- similarity 1.0 (เหมือนกัน) → distance 0.0 (ใกล้สุด)
- similarity 0.0 (ตั้งฉาก) → distance 1.0
- **เรียงผลลัพธ์: distance น้อย → similarity มาก → ตรงกับคำค้นมากสุด** ขึ้นก่อน

> ⚠️ จุดพลาดที่พบบ่อย (และเหตุผลของ PR #2717 "unify cosine distance scoring"): ถ้าบาง path ใช้ similarity บาง path ใช้ distance แล้วเอามาเรียงปนกัน ผลลัพธ์จะกลับหัว — #2717 บังคับให้ทุก adapter พูดภาษาเดียวกัน

---

## 1.6 ทำไม cosine ไม่ใช่ Euclidean?

Euclidean distance:
```
             ___________
d(a,b) = √ Σ (aᵢ − bᵢ)²
```

**ความต่างที่สำคัญ:**
- Euclidean สนใจ **ขนาด** — เวกเตอร์ยาวต่างกันจะไกลกันแม้ทิศเดียวกัน
- Cosine สนใจแค่ **ทิศทาง** — เหมาะกับ embedding เพราะ "ความหมาย" อยู่ที่ทิศ ไม่ใช่ความยาว

**ข้อเท็จจริงเชิงเลข**: ถ้าเวกเตอร์ถูก **normalize เป็นความยาว 1** (unit vectors) แล้ว การเรียงลำดับด้วย cosine กับ Euclidean **ให้ผลเหมือนกัน** เพราะ:
```
‖a − b‖² = ‖a‖² + ‖b‖² − 2(a·b) = 2 − 2cos θ    (เมื่อ ‖a‖=‖b‖=1)
```
→ Euclidean² เป็นฟังก์ชันลดของ cosine พอดี · หลายระบบเลย normalize ก่อนแล้วใช้ dot product ตรงๆ (เร็วกว่า ไม่ต้องหาร norm ทุกครั้ง)

---

## 1.7 มิติเยอะ (768–4096) — ได้อะไร เสียอะไร

**ได้**: มิติเยอะ = "ที่ว่าง" ให้แยกแยะความหมายละเอียดขึ้น (bge-m3 1024 มิติ แยกความหมายได้ดีกว่า all-MiniLM 384)

**เสีย (curse of dimensionality)**:
- ในมิติสูง ระยะทางระหว่างจุดต่างๆ "เท่ากันหมด" มากขึ้น → ยิ่งมิติสูง cosine ยิ่งต้องการโมเดลที่ดีจริง
- storage/compute โตตามมิติ: 1024-dim float32 = 4KB/vector · 35,164 docs × 4KB ≈ 140MB แค่เวกเตอร์
- ยิ่งมิติเยอะ ยิ่งต้อง ANN index (Chapter 3) เพราะ brute-force ช้า

**trade-off จริงในโค้ด**: qwen3 ให้เลือก 0.6b(1024) / 4b(2560) / 8b(4096) — ใหญ่ขึ้น = แม่นขึ้นแต่ช้า/กินที่ · default ของ ARRA = bge-m3 (1024) สมดุลดีสำหรับ multilingual

---

## 1.8 สรุป Chapter 1 (จาก intuition → สมการ → โค้ด)

```
"ความหมายใกล้กัน"
   → embedding เป็นจุดใน ℝⁿ            (1.1)
   → วัดทิศด้วย dot product            (1.2)  a·b = Σaᵢbᵢ = ‖a‖‖b‖cosθ
   → normalize ด้วย norm               (1.3)  ‖a‖ = √Σaᵢ²
   → cosine similarity                 (1.4)  cosθ = a·b / (‖a‖‖b‖)
   → LanceDB เก็บเป็น cosine distance   (1.5)  dist = 1 − cosθ
   → เรียง distance น้อย→มาก = ผลค้น
```

**ถัดไป — Chapter 2:** embeddings มาจากไหน (contrastive learning, ทำไมความหมายใกล้ → เวกเตอร์ใกล้), tokenization, pooling, การ train bge-m3 แบบ multilingual
**Chapter 3:** ANN indexing (HNSW, IVF-PQ) — ทำไม brute-force O(n·d) ไม่พอ และ LanceDB index ทำงานยังไง
**Chapter 4:** โค้ด ARRA Oracle เต็ม — adapter pattern, fallback chain, hybrid FTS+vector scoring, reranker pipeline

---
*grounded: arra-oracle-v3/src/vector/embeddings.ts (KNOWN_DIMS, OllamaEmbeddings) · src/vector/adapters/lancedb.ts (distanceType cosine) · PR #2717 (unify cosine) · /loop iter (deep) 2026-07-13*
