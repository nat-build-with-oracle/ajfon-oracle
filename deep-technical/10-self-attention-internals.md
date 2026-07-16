# Deep Technical · Chapter 10 — Self-Attention Internals

> ต่อจาก Ch9 (token) · บทนี้ลงเครื่องยนต์ที่แปลง token → contextual vector: **self-attention**
> ทวนจาก Ch2 §2.2 แต่ลงลึกทุกสมการ

---

## 10.0 หน้าที่: ให้ token "ปรับตัวเองตามบริบท"

token "เบา" เริ่มต้นมีเวกเตอร์เดียว (จาก embedding table) · แต่ "เบา" ใน `เบาหวาน` ควรต่างจาก "เบา" ใน `เสียงเบา` · self-attention คือกลไกที่ให้ token ดู token อื่นในประโยคแล้วปรับ representation

---

## 10.1 Q, K, V — สามบทบาทของแต่ละ token

token vector `x` (dim d) ถูก project เป็น 3 บทบาทด้วย weight matrix ที่เรียนมา:
```
Q = X Wᵠ      (Query  — "ฉันกำลังหาอะไร")
K = X Wᵏ      (Key    — "ฉันมีอะไรให้")
V = X Wᵛ      (Value  — "ถ้าเลือกฉัน จะได้ข้อมูลนี้")
```
- `X` = เมทริกซ์ token ทั้งประโยค (n × d) · `Wᵠ,Wᵏ,Wᵛ` = พารามิเตอร์ (d × dₖ)

---

## 10.2 Scaled Dot-Product Attention (สมการหัวใจ)

```
                    Q Kᵀ
Attention(Q,K,V) = softmax( ────── ) V
                     √dₖ
```

**แกะทีละชั้น:**
1. **`Q Kᵀ`** (n×n): ทุก token (query) ทำ **dot product** (Ch1!) กับทุก token (key) → คะแนน "เกี่ยวกันแค่ไหน" · ช่อง `[i,j]` = token i สนใจ token j แค่ไหน
2. **`/√dₖ`**: scale · ถ้า dₖ ใหญ่ dot product มีค่าใหญ่ → softmax อิ่มตัว → gradient เล็ก · หารด้วย √dₖ คุม variance ให้ ~1
3. **`softmax`** (ต่อแถว): แปลงคะแนนเป็นน้ำหนักรวม 1 → "token i แจกความสนใจให้ token อื่นยังไง"
   ```
   softmax(z)ᵢ = e^{zᵢ} / Σⱼ e^{zⱼ}
   ```
4. **`× V`**: ถ่วงน้ำหนัก Value → token i ได้ representation ใหม่ = ผสม value ของ token ที่มันสนใจ

**ตัวอย่าง**: "เบา" (query) ทำ dot กับ "หวาน" (key) ได้คะแนนสูง → softmax ให้น้ำหนัก "หวาน" มาก → representation ใหม่ของ "เบา" ดูดความหมายจาก "หวาน" → กลายเป็น "เบา-ในบริบทเบาหวาน"

---

## 10.3 Multi-Head Attention — หลายมุมมองพร้อมกัน

แทน attention เดียว → ทำ `h` หัวขนาน (เช่น 8-16 หัว) แต่ละหัวมี Wᵠ,Wᵏ,Wᵛ ของตัวเอง:
```
headᵢ = Attention(X Wᵠᵢ, X Wᵏᵢ, X Wᵛᵢ)
MultiHead = Concat(head₁,…,headₕ) Wᴼ
```
- แต่ละหัวเรียน "ความสัมพันธ์คนละแบบ" — หัวนึงจับ syntax, หัวนึงจับ coreference, ฯลฯ
- `dₖ = d/h` (แบ่งมิติต่อหัว) → compute รวมเท่าเดิม

---

## 10.4 Positional Encoding — attention ไม่รู้ลำดับเอง

`softmax(QKᵀ)V` เป็น **permutation-invariant** — สลับลำดับ token ผลเท่าเดิม! แต่ "หมากัดคน" ≠ "คนกัดหมา" → ต้องใส่ตำแหน่ง

- **Absolute (sinusoidal, BERT/original)**: บวกเวกเตอร์ตำแหน่งเข้า input
  ```
  PE(pos,2i) = sin(pos/10000^{2i/d}) ,  PE(pos,2i+1) = cos(...)
  ```
- **RoPE (Rotary, โมเดลใหม่ๆ)**: หมุนเวกเตอร์ Q,K ด้วยมุมตามตำแหน่ง → dot product สะท้อน**ระยะห่างสัมพัทธ์** → generalize context ยาวได้ดีกว่า (เกี่ยวกับ bge-m3 8192 ctx, Ch9 §9.6)

---

## 10.5 โครงชั้นเต็ม (Transformer encoder block)

```
x → [Multi-Head Attention] → +x (residual) → LayerNorm
  → [Feed-Forward (FFN)]    → +  (residual) → LayerNorm  → x'
```
- **residual `+x`**: ให้ gradient ไหลผ่านชั้นลึกได้ (กัน vanishing)
- **LayerNorm**: normalize activation ต่อ token คุม scale
- **FFN**: `max(0, xW₁+b₁)W₂+b₂` — ประมวลผลต่อ token (non-linear, expand→contract)
- ซ้อน L block (bge-m3 ~24 layer) → representation ลึกขึ้นเรื่อยๆ

---

## 10.6 Complexity — ทำไม context ยาวแพง

`QKᵀ` = n×n เมทริกซ์ → **O(n²·d)** ต่อ layer
- n=512 → 260k · n=8192 → 67M (bge-m3 ctx ยาว = แพง quadratic!)
- นี่คือเหตุผลที่ context ยาวมี cost — และทำไม embed doc ยาวหนักกว่า doc สั้นแบบ quadratic (สอด Ch ecosystem: bulk indexing = คอขวด)
- งานวิจัย efficient attention (FlashAttention, linear attention) แก้ตรงนี้

---

## 10.7 เชื่อมกลับ vector search

```
token embedding (คงที่)
  → L ชั้น self-attention → contextual token vectors
  → pooling (Ch2 §2.3) → sentence vector v
  → cosine (Ch1) → search
```
คุณภาพ search **ขึ้นกับ attention จับบริบทดีแค่ไหน** — "เบาหวาน" ได้เวกเตอร์ที่สะท้อน "โรค" (ไม่ใช่ "น้ำหนักเบา"+"รสหวาน") เพราะ attention ผสมบริบทถูก → cosine กับ query การแพทย์จึงสูง

---

## สรุป Ch10
```
Q,K,V = 3 projection ของ token
Attention = softmax(QKᵀ/√dₖ)V  (QKᵀ=dot ทุกคู่, scale, softmax→น้ำหนัก, ×V)
Multi-head = h หัวขนาน จับความสัมพันธ์คนละแบบ
positional (sinusoidal/RoPE) เพราะ attention ไม่รู้ลำดับเอง
block: attention→residual→LN→FFN→residual→LN , ซ้อน ~24 ชั้น
O(n²d) → context ยาวแพง quadratic = คอขวด embed doc ยาว
```
**ถัดไป Ch11:** RRF & ranking theory proofs — ทำไม RRF ทน scale ต่างกัน, k=60 มาจากไหน, การพิสูจน์ rank fusion, และ confidence-weighted variant ของ ARRA

---
*grounded: "Attention is All You Need" (Vaswani 2017) · RoPE (Su 2021) · XLM-R architecture · เชื่อม Ch2/Ch9 · /loop deep iter 2026-07-13*
