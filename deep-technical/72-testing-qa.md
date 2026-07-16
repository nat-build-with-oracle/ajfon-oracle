# Deep Technical · Chapter 72 — Vector Search Testing & QA

> ต่อจาก Ch71 · retrieval test ต่างจาก test โค้ดปกติ (ผลไม่ deterministic เป๊ะ) · บทนี้: golden set, property-based, regression, สิ่งที่ ARRA test จริง

---

## 72.0 ทำไม test retrieval ยากกว่า test ปกติ

```
โค้ดปกติ: f(2)==4 → assert เป๊ะ (pass/fail ชัด)
retrieval: search("ปวดหัว") → [doc1, doc5, doc3, ...] → "ถูก" คืออะไร?
  - อันดับเปลี่ยนนิดหน่อยยัง OK ไหม?
  - embedder update (Ch53) → ผลเปลี่ยน → test พังหมด?
→ retrieval quality = สถิติ (recall/nDCG Ch6) ไม่ใช่ equality เป๊ะ
```

---

## 72.1 ⭐ golden set — regression หลัก

```
golden set: (query, expected_relevant_doc_ids) ที่ label ไว้ (Ch20/39)
test: run search → วัด recall@k / nDCG (Ch6) → assert >= threshold
เช่น: assert nDCG@10 >= 0.85 (ไม่ใช่ assert result == exact list)
```
- **threshold ไม่ใช่ equality**: ยอมให้อันดับขยับ แต่ quality ต้องไม่ตกใต้ baseline
- run ทุก commit → จับ regression (เปลี่ยนโค้ดแล้ว recall ตก → รู้ทันที, Ch54)

---

## 72.2 unit test — ส่วนที่ deterministic

แม้ผล search เป็นสถิติ แต่หลายส่วน test แบบ exact ได้:
```
✓ cosine(a, b) == expected (Ch1 คณิต — deterministic!)
✓ RRF merge: input ranks → output score (Ch11 สูตรตายตัว)
✓ chunk boundary (Ch12): input text → chunks (กติกาตายตัว)
✓ content-hash id (Ch52): input → id เดิม (idempotent)
✓ fallback chain (Ch4): provider ล่ม → เลือกตัวถัดไป (logic ตายตัว)
```
- **แยก layer**: math/logic → unit test เป๊ะ · quality → golden set สถิติ (§72.1)
- arra-oracle-v3 มี `__tests__/benchmark.ts` (Ch4/20, 30-doc) → regression harness

---

## 72.3 property-based testing

test คุณสมบัติที่ต้องจริงเสมอ (ไม่ใช่ case เฉพาะ):
```
property: search(q) ต้องคืน ≤ k results        (ไม่เกิน limit)
property: doc ที่ query ตรงเป๊ะ (identical) → ต้องติด top-1 (cos=1.0, Ch1)
property: เพิ่ม doc แล้วค้น doc นั้น → ต้องเจอ (freshness Ch45)
property: idempotent — ingest ซ้ำ → result เท่าเดิม (Ch52)
property: filter (Ch55) → ผลทุกตัวต้องผ่าน filter (ไม่มี leak)
```
- generate query สุ่ม → เช็ค property → จับ bug ที่ case-based พลาด (เช่น filter leak Ch55)

---

## 72.4 ⚠️ non-determinism — จัดการยังไง

```
แหล่ง non-determinism:
  - embedder fp (Ch50): บวกลอย → vector ต่างนิดๆ ต่อ run
  - ANN approximate (Ch3): candidate ต่างตาม seed
  - concurrent (Ch65): timing → order
วิธี test:
  - pin seed (ANN, sampling) → reproducible
  - tolerance: assert cos ต่าง < ε (ไม่ใช่ ==)
  - threshold บน metric (§72.1) แทน exact result
```
- อย่า assert exact vector/order (เปราะ) → assert quality/property (ทน)

---

## 72.5 test ชั้นต่างๆ (pyramid)

```
unit (เยอะ, เร็ว):        math/logic deterministic (§72.2)
integration:              pipeline (Ch51) ingest→search end-to-end (corpus เล็ก)
golden/quality (สถิติ):    recall/nDCG บน labeled set (§72.1)
property:                 invariants (§72.3)
canary/online (Ch31):      A/B vs baseline บน traffic จริง (Ch74)
```
- **CI**: unit+integration+golden ทุก commit · online ตอน deploy (Ch53 shadow)

---

## 72.6 เชื่อม ARRA

```
arra-oracle-v3 __tests__/benchmark.ts (Ch4/20): golden set 30-doc → regression
unit: cosine (Ch1), RRF fusedScore 0.016393 (Ch4/11), fallback (Ch4), chunk (Ch12) — deterministic
property: idempotent (Ch52), filter no-leak (Ch55), identical→top-1
drift #2740 (Ch6/69): test local vs edge quality (cross-path regression)
→ test แยกชั้น: logic เป๊ะ + quality สถิติ → มั่นใจ deploy (Ch53 migration ปลอดภัย)
```
- **community**: "รู้ได้ไงว่าค้นแม่น" → golden set + metric (Ch6) วัดได้ ไม่ใช่รู้สึกเอา

---

## สรุป Ch72
```
test retrieval ≠ test ปกติ: quality=สถิติ (recall/nDCG Ch6) ไม่ใช่ equality เป๊ะ
⭐ golden set: (query, relevant ids) → assert nDCG>=threshold (ยอมอันดับขยับ, จับ regression)
unit test ส่วน deterministic: cosine(Ch1)/RRF(Ch11)/chunk(Ch12)/hash(Ch52)/fallback(Ch4) เป๊ะ
property-based: ≤k results, identical→top-1, freshness(Ch45), idempotent(Ch52), filter no-leak(Ch55)
⚠️ non-determinism (fp Ch50/ANN Ch3/concurrent Ch65) → pin seed, tolerance ε, threshold ไม่ exact
pyramid: unit>integration>golden>property>online(A/B Ch74) · CI ทุก commit
ARRA: __tests__/benchmark.ts golden + unit logic + property → deploy มั่นใจ (Ch53)
```
**ถัดไป Ch73:** explainability — ทำไม doc นี้ติด top-k, score breakdown (vector/FTS/rerank contribution), debug relevance, สร้างความเชื่อมั่น
---
*grounded: golden set regression · property-based testing · arra-oracle-v3 __tests__/benchmark.ts (Ch4/20) · non-determinism (Ch3/50/65) · เชื่อม Ch1/3/4/6/11/12/45/50/52/54/55/65 · /loop deep iter 2026-07-16*
