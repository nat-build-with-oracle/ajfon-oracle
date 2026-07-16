# บทที่ 7 — Hybrid Search: vector อย่างเดียวไม่พอ

> เปิดภาค 3 (ระบบจริง) — สร้าง hybrid engine ด้วยมือทั้งตัวใน notebook `ch07_hybrid_search.ipynb`

---

## 7.1 จุดบอด 2 จุดของ vector (ที่เจอแน่ในโน้ตจริง)

1. **รหัส/ชื่อเฉพาะ**: "PR #2740", "ESP32", "มาตรา 44" — embedding จับความหมายรวม
   แต่ตัวเลข/รหัสเป๊ะๆ อาจ dilute หายในเวกเตอร์ (บทที่ 5: pooling เฉลี่ยทุก token)
2. **คำว่า "ไม่"**: cos("มีน้ำตาล", "ไม่มีน้ำตาล") สูงมาก — ต่างแค่ token เดียว topic กลบ

ทั้งสองอย่างคือความถนัดของ **keyword search** (ตรงเป๊ะ, boolean NOT) ที่โลกใช้มา 40 ปี

## 7.2 BM25 — keyword scoring ใน 20 บรรทัด

สูตรที่ FTS5 (และ search engine แทบทุกตัว) ใช้:

$$\text{BM25}(q,d) = \sum_{t \in q} \text{IDF}(t) \cdot \frac{f(t,d)\,(k_1+1)}{f(t,d) + k_1\left(1-b+b\frac{|d|}{avgdl}\right)}$$

- **IDF**: คำหายาก (เช่น "#2740") ได้น้ำหนักมาก — คำที่มีทุก doc แทบไม่นับ
- **f(t,d) แบบอิ่มตัว**: คำซ้ำ 10 ครั้งไม่ได้แต้ม 10 เท่า (k₁ คุมความอิ่ม)
- **ปรับตามความยาว doc** (b): doc ยาวไม่ได้เปรียบ

notebook เขียนสูตรนี้จริงใน 20 บรรทัด — รันแล้ว "PR #2740" ขึ้นอันดับ 1 ทันที (IDF ของ "#2740" สูงมาก)

## 7.3 ⭐ RRF — รวมสองโลกด้วย "อันดับ" ไม่ใช่คะแนน

ปัญหาถ้ารวมคะแนนตรงๆ: cosine ∈ [-1,1] แต่ BM25 ∈ [0,∞) — **คนละ scale บวกกันไม่ได้**

RRF แก้ด้วยการใช้อันดับ (rank) ซึ่ง scale-free เสมอ:

$$\text{RRF}(d) = \sum_{r} \frac{1}{k + \text{rank}_r(d)}, \qquad k = 60$$

```python
def rrf(rank_lists, k=60):
    scores = {}
    for ranks in rank_lists:
        for pos, doc in enumerate(ranks, 1):
            scores[doc] = scores.get(doc, 0) + 1 / (k + pos)
    return sorted(scores.items(), key=lambda x: -x[1])
```

**หลักฐานเชื่อมกับ production**: fusedScore ใน arra-oracle-v3 = `0.016393` = 1/61 พอดี
— คือ doc ที่ได้อันดับ 1 จาก ranker เดียว (1/(60+1)) · สูตรใน notebook กับใน production คือตัวเดียวกัน

## 7.4 ผลรันจริง (จาก notebook)

```
Q: "PR #2740"          → BM25 จับเป๊ะ · RRF top-1 = โน้ต PR #2740 ✓ (fused 0.0328 = 1/61+1/61 ชนะทั้งคู่)
Q: "บอร์ดสำหรับสอน IoT" → vector จับความหมาย (ESP32/ไมโครคอนโทรลเลอร์) · RRF ✓
```

hybrid ไม่ใช่ "เผื่อเหนียว" — มันชนะเพราะ**สองระบบถนัดคนละเขต** แล้ว RRF ปล่อยให้แต่ละตัวเด่นในเขตตัวเอง

## 7.5 k=60 มาจากไหน

งานวิจัย (Cormack 2009) พบว่า k=60 robust ข้าม dataset:
- k เล็ก → อันดับต้นถ่วงแรงมาก (เชื่อ top-1 สุดๆ)
- k ใหญ่ → เฉลี่ยแบนราบ
- 60 = จุดสมดุลที่ใช้ได้แทบทุกงานโดยไม่ต้อง tune (ARRA ก็ใช้ค่านี้)

## 7.6 เชื่อม ARRA

```
ARRA hybrid = FTS5 (BM25 จริง, SQLite) + LanceDB (vector) + RRF k=60
mode ให้เลือก: hybrid (default) / fts / vector — ตรงกับที่เพิ่งสร้างเองทั้งตัว
```
ต่างแค่ scale: ARRA ใช้ inverted index จริง (เร็วระดับหมื่น doc) แทน loop Python — สูตรเดียวกันเป๊ะ

---

### สรุปบทที่ 7
- vector พลาด: รหัสเป๊ะ + negation → BM25/keyword ถนัดพอดี → hybrid
- BM25 = IDF × ความถี่อิ่มตัว × ปรับความยาว (เขียนเอง 20 บรรทัดใน notebook)
- ⭐ RRF ใช้อันดับ (scale-free) k=60 — สูตรตรงกับ ARRA production (1/61 = 0.016393 พิสูจน์แล้ว)
- hybrid ชนะเพราะสองระบบถนัดคนละเขต

*Notebook: `ch07_hybrid_search.ipynb` (execute ✅ 3 asserts) · ลึกกว่า: deep-technical Ch4/11/34/56/60*
