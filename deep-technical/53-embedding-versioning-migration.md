# Deep Technical · Chapter 53 — Embedding Versioning & Migration

> ต่อจาก Ch52 · วันหนึ่งจะเปลี่ยน embedder (โมเดลใหม่ดีกว่า) → vector เก่าใช้ร่วมใหม่ไม่ได้ · บทนี้: dual-write, backfill, zero-downtime model swap

---

## 53.0 ทำไม vector ข้ามโมเดลใช้ร่วมกันไม่ได้

```
embedding = พิกัดใน "space" ของโมเดลนั้นๆ (Ch2)
bge-m3 space ≠ nomic space ≠ openai space
cos(vec_bge, vec_nomic) = ไร้ความหมาย (คนละพิกัด, มิติอาจต่าง 1024 vs 768)
```
→ เปลี่ยนโมเดล = ต้อง **re-embed ทุก doc** ด้วยโมเดลใหม่ (ไม่มีทางลัด convert)

---

## 53.1 embedding version — เก็บ metadata

ทุก vector ต้องรู้ว่ามาจากโมเดล/version ไหน:
```
row: { id, vector, model:"bge-m3", model_version:"1.0", dim:1024, created_at }
```
- arra-oracle-v3 (Ch4): KNOWN_DIMS map (nomic 768, bge-m3 1024, qwen3 1024/2560/4096) → รู้ dim ต่อโมเดล
- query ต้อง embed ด้วย **โมเดลเดียวกับ index** → เก็บ model ใน metadata กัน mismatch

---

## 53.2 ⚠️ mismatch = ผลลัพธ์พัง (เงียบ)

```
index สร้างด้วย bge-m3 (1024) · query embed ด้วย nomic (768)
→ dim ไม่ตรง → error ชัด (ดี, จับได้)
แต่ถ้าบังเอิญ dim ตรง (bge-m3 1024 vs qwen3 1024) →
→ ค้นได้ แต่ผลลัพธ์ "มั่ว" (คนละ space) — ไม่ error, เงียบ, อันตราย!
```
- → **ต้อง validate model match ไม่ใช่แค่ dim match** (Ch4 KNOWN_DIMS เช็ค dim, แต่ model tag สำคัญกว่า)

---

## 53.3 ⭐ migration strategy — dual-write + backfill

เปลี่ยนโมเดลโดยไม่ downtime (คล้าย blue-green Ch46):
```
1. dual-write: doc ใหม่ทุกอัน → embed ทั้งโมเดลเก่า(A) + ใหม่(B) → เก็บทั้งคู่
2. backfill: background re-embed doc เก่าทั้งหมดด้วย B (batch, Ch51)
3. shadow read: query embed ด้วย B → ค้น index B → เทียบผลกับ A (eval Ch20/39)
4. cutover: B ครบ + eval ผ่าน → สลับ query ไป B (atomic, Ch46)
5. cleanup: ทิ้ง vector A (คืนที่)
```
- ไม่มีวินาทีที่ค้นไม่ได้ · เปรียบเทียบ A/B ก่อน commit (ไม่เดา)

---

## 53.4 backfill cost — ประเมินก่อนทำ

```
re-embed N doc = N embed call (Ch44 แพง) → ประเมิน:
100k chunk × 100ms/50-batch = 200 วินาที compute (Ch51 throughput)
+ cloud cost (Ch24): 100k embed × ราคา/1k token
```
- **ARRA personal (หมื่น-แสน)**: backfill = นาที + ถูก → เปลี่ยนโมเดลไม่เจ็บ
- **enterprise (ล้าน+)**: backfill = ชั่วโมง + $$ → วางแผน (off-peak, Ch24 budget)

---

## 53.5 เมื่อไหร่ควรเปลี่ยนโมเดล (คุ้มไหม)

```
เปลี่ยนเมื่อ: โมเดลใหม่ recall ดีขึ้นชัด (วัด eval Ch20/39 บน corpus เรา) คุ้มกับ backfill cost
อย่าเปลี่ยนเพราะ: leaderboard rank สูงกว่านิด (Ch39 overfitting) — วัดบนงานจริงก่อน
```
- **สัญญาณคุ้ม**: โดเมนใหม่ (เพิ่มภาษา), มิติ/speed ดีขึ้นมาก, ราคาถูกลง
- version pin: lock โมเดล+version ใน config → reproducible (ไม่ให้ provider เปลี่ยนใต้เท้าเรา)

---

## 53.6 เชื่อม ARRA

```
metadata model tag (§53.1, Ch4 KNOWN_DIMS) → กัน mismatch เงียบ (§53.2)
เปลี่ยนโมเดล → dual-write+backfill+shadow-eval+cutover (§53.3, คล้าย blue-green Ch46)
ARRA personal → backfill ถูก (§53.4) → ทดลองโมเดลใหม่ได้ไม่เจ็บ
version pin config → reproducible (§53.5)
```
- **community**: "ถ้าโมเดล embedding ดีขึ้นในอนาคต ต้องทำใหม่หมดไหม?" → re-embed (จำเป็น) แต่ automated (dual-write+backfill) + ARRA เล็กพอให้ถูก

---

## สรุป Ch53
```
vector ข้ามโมเดลใช้ร่วมไม่ได้ (คนละ space) → เปลี่ยนโมเดล = re-embed ทุก doc
เก็บ model+version metadata (Ch4 KNOWN_DIMS) → query ต้องใช้โมเดลเดียวกับ index
⚠️ dim ตรงแต่คนละโมเดล = ผลมั่วเงียบ (อันตรายกว่า dim ผิด) → validate model ไม่ใช่แค่ dim
⭐ migration: dual-write → backfill (Ch51) → shadow-eval (Ch20) → atomic cutover (Ch46) → cleanup
backfill cost: ARRA personal=นาที/ถูก, enterprise=ชม/$$ (Ch24) → ประเมินก่อน
เปลี่ยนเมื่อ eval บนงานจริงคุ้ม (ไม่ใช่ leaderboard, Ch39) · version pin=reproducible
```
**ถัดไป Ch54:** observability & tracing — วัดอะไรใน retrieval, distributed trace ของ query, log/metric/trace สามชั้น, debug "ทำไมค้นไม่เจอ"
---
*grounded: arra-oracle-v3 KNOWN_DIMS (nomic 768/bge-m3 1024/qwen3 1024-4096) · dual-write migration · blue-green (Ch46) · เชื่อม Ch2/4/20/24/39/44/46/51 · /loop deep iter 2026-07-16*
