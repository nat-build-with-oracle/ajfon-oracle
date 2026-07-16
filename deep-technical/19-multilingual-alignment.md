# Deep Technical · Chapter 19 — Multilingual Alignment (ค้นไทย เจอ doc อังกฤษ)

> ต่อจาก Ch18 · จุดขายที่ resonate กับ researcher ไทย (Ch community-ask): ค้นภาษาไทย → เจอ paper อังกฤษ · บทนี้: ทำไมเป็นไปได้เชิงคณิต

---

## 19.0 ปรากฏการณ์

```
query: "การรักษาเบาหวานด้วย AI"  (ไทย)
เจอ:   "AI-driven diabetes management: a review"  (อังกฤษ)
cosine(embed_ไทย, embed_อังกฤษ) สูง  แม้ไม่มีตัวอักษรร่วมกันเลย
```
FTS (Ch4) ทำไม่ได้เด็ดขาด (คนละ script) · vector ทำได้เพราะ **shared multilingual embedding space**

---

## 19.1 Shared embedding space — หัวใจ

โมเดล monolingual: ไทยกับอังกฤษอยู่ "คนละย่าน" ในปริภูมิ → cosine ต่ำเสมอ
โมเดล multilingual (bge-m3): ฝึกให้ **ประโยคความหมายเดียวกันข้ามภาษา → เวกเตอร์ใกล้กัน**
```
embed("แมว")  ≈  embed("cat")  ≈  embed("猫")     (พิกัดใกล้กัน)
```
→ ปริภูมิเป็น "concept space" ที่ภาษาเป็นแค่ทางเข้า ไม่ใช่แกนหลัก

---

## 19.2 ฝึกให้ align ยังไง (3 สัญญาณ)

**(1) Shared subword vocab** (Ch9): SentencePiece เรียนจาก 100+ ภาษา → บาง subword ใช้ร่วม (ตัวเลข ชื่อเฉพาะ คำยืม) = จุดเชื่อมเริ่มต้น

**(2) Parallel/translation pairs — contrastive ข้ามภาษา**:
```
positive: ("การรักษาเบาหวาน", "diabetes treatment")   ← คู่แปล = ความหมายเดียว
negative: ("การรักษาเบาหวาน", "climate change")
```
ใส่เข้า InfoNCE (Ch2 §2.5) → บังคับ `cos(ไทย, อังกฤษแปลตรง)` สูง, `cos(ไทย, อังกฤษไม่เกี่ยว)` ต่ำ → **ดึงคู่แปลให้ทับกันในปริภูมิ**

**(3) Anchor effect**: ภาษา high-resource (อังกฤษ) เป็น "สมอ" · ภาษาอื่นถูกดึงมา align กับอังกฤษ → ทุกภาษาเชื่อมผ่านอังกฤษโดยปริยาย

---

## 19.3 คณิตของ cross-lingual retrieval

หลัง align: `embed` เป็นฟังก์ชันที่ **language-invariant สำหรับความหมายเดียวกัน**:
```
embed(x_th) ≈ embed(translate(x_th) → x_en)     (โดยประมาณ)
```
→ query ไทย `q_th`, doc อังกฤษ `d_en`:
```
cos(embed(q_th), embed(d_en)) ≈ cos(embed(q_en), embed(d_en))
```
= เท่ากับค้นด้วย query ที่แปลเป็นอังกฤษแล้ว **โดยไม่ต้องแปลจริง** · โมเดลแปลให้ในปริภูมิ

**alignment ไม่สมบูรณ์**: `≈` ไม่ใช่ `=` → มี "translation gap" เล็กน้อย → cross-lingual recall มักต่ำกว่า monolingual นิดหน่อย แต่ยังใช้ได้ดี (bge-m3 ออกแบบมาเพื่อสิ่งนี้)

---

## 19.4 ทำไมสำคัญกับ workshop (researcher ไทย)

- นักวิจัยไทยอ่าน paper อังกฤษ แต่คิด/จดโน้ตเป็นไทย → ค้นไทยต้องเจอ paper อังกฤษ = requirement จริง
- FTS อย่างเดียวพลาด 100% (คนละ script) → **ต้องมี vector multilingual** → เหตุผลเชิงเทคนิคว่าทำไม ARRA เลือก bge-m3 (ไม่ใช่ embedder อังกฤษ)
- เดโม: query ไทย → doc อังกฤษ = "อ๋อ" moment สำหรับ audience (Ch community-ask: cross-language เป็นจุดขาย)

---

## 19.5 ข้อจำกัด (พูดตรงๆ)

- **low-resource languages**: ภาษาที่มีข้อมูล train น้อย → align แย่กว่า (ไทยกลาง-สูง พอใช้ได้)
- **script/domain mismatch**: ศัพท์เทคนิคเฉพาะทาง/คำใหม่ที่ไม่มีคู่แปลตอน train → align หลุด
- **code-switching** (ไทยปนอังกฤษในประโยคเดียว, พบบ่อยในไทย!) → bge-m3 จัดการได้ดีเพราะ subword ร่วม + attention (Ch10) แต่ไม่สมบูรณ์
- ยังต้อง **hybrid**: cross-lingual vector + FTS (จับศัพท์เทคนิค/ชื่อเฉพาะที่เขียนอังกฤษตรงๆ) → RRF (Ch11)

---

## 19.6 เชื่อม M3 (Ch7)

bge-m3 = **M**ulti-lingual · **M**ulti-functionality · **M**ulti-granularity
- Ch7 ลง multi-functionality (dense/sparse/colbert)
- บทนี้ลง **multi-lingual** — align 100+ ภาษาในปริภูมิเดียว
- multi-granularity = รองรับ input สั้น (คำ) ถึงยาว (8192 tokens, Ch9)
→ 3M รวมกันคือเหตุผลที่ bge-m3 เป็น "ตัวหลัก" ของ ARRA สำหรับ workshop ไทย

---

## สรุป Ch19
```
multilingual = shared "concept space" ที่ภาษาเป็นทางเข้า ไม่ใช่แกน
align ด้วย: shared subword + parallel-pair contrastive (InfoNCE ข้ามภาษา) + anchor(อังกฤษ)
คณิต: embed(q_th) ≈ embed(q_en) → cos(q_th, d_en) สูง = แปลในปริภูมิ (ไม่ต้องแปลจริง)
สำคัญ: researcher ไทยค้นไทย→เจอ paper อังกฤษ (FTS ทำไม่ได้) → ต้อง bge-m3
ยังต้อง hybrid (vector cross-lingual + FTS ศัพท์เทคนิค)
```
**ถัดไป Ch20:** eval harness code walkthrough — benchmark-models.ts, drift harness structure, การรัน retrieval eval จริง, คำนวณ recall@k/MRR ในโค้ด

---
*grounded: bge-m3 M3 (Chen et al. 2024) · LASER/LaBSE cross-lingual alignment · InfoNCE cross-lingual (Ch2) · Ch7 (M3) · Ch community-ask (cross-language selling point) · /loop deep iter 2026-07-13*
