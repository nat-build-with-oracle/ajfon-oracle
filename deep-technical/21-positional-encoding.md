# Deep Technical · Chapter 21 — Positional Encoding (sinusoidal & RoPE)

> ต่อจาก Ch20 · Ch10 §10.4 เกริ่น positional · บทนี้ลงคณิตเต็ม — ทำไม RoPE ทำ context ยาว (bge-m3 8192) ได้ดี

---

## 21.0 ทำไมต้องมี (ทวน)

self-attention `softmax(QKᵀ)V` เป็น **permutation-invariant** (Ch10 §10.4) — สลับ token ผลเท่าเดิม · แต่ลำดับสำคัญ ("หมากัดคน"≠"คนกัดหมา") → ต้องฉีดข้อมูลตำแหน่ง

---

## 21.1 Sinusoidal (absolute) — derivation

original Transformer:
```
PE(pos, 2i)   = sin( pos / 10000^{2i/d} )
PE(pos, 2i+1) = cos( pos / 10000^{2i/d} )
```
บวกเข้า input embedding: `x'ₚₒₛ = xₚₒₛ + PE(pos)`

**ทำไม sin/cos หลายความถี่**: แต่ละมิติ i เป็นคลื่นความถี่ต่างกัน (มิติต่ำ=คลื่นเร็ว, มิติสูง=คลื่นช้า) → ตำแหน่งได้ "ลายนิ้วมือ" เฉพาะ (เหมือนเลขฐาน 2 หลายบิต)

**คุณสมบัติเด็ด — relative position ผ่าน linear**:
```
PE(pos+k) = M_k · PE(pos)     สำหรับเมทริกซ์ M_k (rotation) ที่ขึ้นกับ k เท่านั้น
```
พิสูจน์ (จาก sin/cos angle-addition):
```
sin(θ+φ) = sinθ cosφ + cosθ sinφ
cos(θ+φ) = cosθ cosφ − sinθ sinφ
```
→ PE(pos+k) เขียนเป็น linear combination ของ PE(pos) ได้ → โมเดลเรียน "ห่างกัน k" ได้จาก linear op · นี่คือเหตุผลที่ generalize ระยะห่างที่ไม่เคยเห็นได้ (บ้าง)

---

## 21.2 ⭐ RoPE — Rotary Position Embedding (ที่โมเดลใหม่/bge-m3 ใช้)

แทน**บวก** position เข้า embedding → **หมุน** เวกเตอร์ Q,K ด้วยมุมตามตำแหน่ง

จับคู่มิติเป็น 2D `(x₂ⱼ, x₂ⱼ₊₁)` แล้วหมุนด้วยมุม `pos·θⱼ`:
```
        [ cos(pos·θⱼ)  −sin(pos·θⱼ) ] [ x₂ⱼ  ]
R(pos)  [ sin(pos·θⱼ)   cos(pos·θⱼ) ] [ x₂ⱼ₊₁]        θⱼ = 10000^{−2j/d}
```
apply กับทั้ง Q และ K ก่อนทำ attention

**คุณสมบัติทองของ RoPE** — dot product สะท้อน**ระยะห่างสัมพัทธ์** โดยตรง:
```
⟨ R(m)·qₘ , R(n)·kₙ ⟩ = g(qₘ, kₙ, m−n)
```
คือ dot product ระหว่าง query ตำแหน่ง m กับ key ตำแหน่ง n **ขึ้นกับ (m−n) เท่านั้น** ไม่ใช่ m,n แยก
- **พิสูจน์ intuition**: หมุน 2 เวกเตอร์ด้วยมุม m·θ และ n·θ → มุมระหว่างกันเหลือ (m−n)·θ → dot (=cosine×norm) ขึ้นกับผลต่างมุม = (m−n) · เหมือน §8.6 (dot=cosθ) แต่ θ ตอนนี้ = ระยะห่างตำแหน่ง!

---

## 21.3 ทำไม RoPE extrapolate context ยาว (สำคัญกับ bge-m3 8192)

- absolute PE: เรียน position ≤ max_train_len เท่านั้น → เกินนั้นเจอ position ไม่เคยเห็น → พัง
- RoPE: encode **relative** distance → ตำแหน่ง 5000 กับ 5001 ต่างกัน "1" เหมือน 5 กับ 6 → generalize ระยะที่ยาวกว่า train ได้ดีกว่า (ด้วยเทคนิค NTK-scaling/position interpolation ช่วยเสริม)
- นี่คือเหตุผลเชิงเทคนิคที่ bge-m3 มี **8192 context** (Ch9 §9.6) ได้ → embed เอกสารยาว/หลายย่อหน้าในทีเดียว (ลดความจำเป็น chunk, Ch12)

---

## 21.4 ALiBi (ทางเลือก) — bias ตรงๆ

Attention with Linear Biases: ไม่ encode position ใน embedding เลย → ใส่ bias เชิงเส้นตามระยะห่างใน attention score:
```
attention_score(i,j) += −slope · |i − j|
```
- ยิ่งห่าง → ลบมาก → attention น้อยลง (recency-ish) · extrapolate ดีมาก, ง่าย · แต่ RoPE นิยมกว่าใน embedding models

---

## 21.5 ผลต่อ retrieval quality

- position ดี → attention จับ dependency ระยะไกลถูก (เช่น ประธานต้นย่อหน้า ↔ กริยาท้าย) → embedding สะท้อนโครงสร้างประโยคยาว
- long-doc embedding: RoPE + FlashAttention (Ch16) = embed doc 8192 tokens โดย attention ยัง coherent → เวกเตอร์แทนเอกสารยาวได้ดี (ลด dilution, Ch12 §12.0)
- ภาษาไทย: word order สำคัญ + code-switching → position ช่วย disambiguate ("ตากลม" — ตำแหน่งช่วยแยก, Ch9 §9.4)

---

## สรุป Ch21
```
absolute sinusoidal: PE=sin/cos หลายความถี่, relative ผ่าน linear (angle-addition)
RoPE: หมุน Q,K ด้วย pos·θ → ⟨R(m)q, R(n)k⟩ ขึ้นกับ (m−n) เท่านั้น = relative โดยตรง
  → extrapolate context ยาว (bge-m3 8192) เพราะ encode ระยะห่างไม่ใช่ตำแหน่งสัมบูรณ์
ALiBi: bias −slope·|i−j| ตรงๆ
ผล: embed long-doc coherent (RoPE+FlashAttn) → ลด dilution
```
**ถัดไป Ch22:** distillation & bge-m3 training recipe — knowledge distillation (KL/temperature), self-distillation dense↔sparse↔colbert, hard-negative mining, สูตรฝึกเต็ม

---
*grounded: sinusoidal (Vaswani 2017) · RoPE (Su et al. 2021, RoFormer) · ALiBi (Press 2021) · position interpolation (Chen 2023) · เชื่อม Ch8 §8.6, Ch9, Ch10, Ch16 · /loop deep iter 2026-07-13*
