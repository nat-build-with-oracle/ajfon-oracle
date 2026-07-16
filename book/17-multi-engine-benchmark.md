# บทพิเศษ 2 (Extras) — Multi-Engine Benchmark: เทียบ embedder อย่าง honest

> ภาคพิเศษ · notebook `ch17_multi_engine_benchmark.ipynb` · เกิดจากคำถามจริงของ arra-oracle-v3 ("ควรมีหลาย engine ไหม?")

เป้าคือ **ฝึกทำ benchmark ให้เป็น** — เข้าใจทุก engine ไม่ใช่แค่เลือกตัวเดียว

## X.1 Golden Set แบบ honest (กัน engine bias)
กับดัก: label เฉลยจาก output ของ engine ตัวเดียว = circular (ฝัง bias เข้า ground truth)
วิธีถูก **pooled judgment** (TREC/BEIR, deep-technical Ch39): ตัดสิน relevant จากการ **อ่าน corpus**
อนุญาตหลาย relevant ต่อ query (ไม่งั้น recall เพี้ยน)

## X.2 Metric — Recall@k vs nDCG@10
$$\text{DCG@}k=\sum_{i=1}^{k}\frac{rel_i}{\log_2(i+1)}\qquad \text{nDCG@}k=\frac{DCG@k}{IDCG@k}$$
- **Recall@k = ประตู**: relevant ติด top-k ที่ feed LLM ไหม (เพดานคุณภาพ RAG)
- **nDCG@10 = ลำดับ**: lost-in-the-middle (Ch75) — วางถูกที่ไหม

## X.3 ⭐ ผลวัดจริง — single vs triple-RRF
```
engine              Recall@5   nDCG@10
bge-m3                 1.000     0.972
triple-RRF            0.929     0.791   ← แย่ลง!
```
**บทเรียนทองคำ**: fuse ranker ที่อ่อนกว่า+correlated (nomic/qwen3 อ่อนไทยกว่า bge-m3) **ดึงตัวเก่งลง**
เพราะ RRF ถ่วงทุก ranker เท่ากัน → "มีเยอะ ≠ ดีกว่า" (พิสูจน์ด้วยตัวเลข ไม่ใช่เดา)

## X.4 หลักที่ได้
- fusion ช่วยเมื่อ ranker เก่งพอทุกตัว + พลาดคนละแบบ (independent) — ไม่ใช่ correlated
- ตัวชี้ขาด = **วัด fused vs best-single บน golden เอง** ไม่มีเลขวิเศษ
- **มุมการศึกษา**: การมีหลาย engine ให้เทียบ = เห็นว่าทำไม bge-m3 ชนะไทย, ทำไม fusion ไม่ช่วย — คุณค่าที่ production-only มองไม่เห็น

*fork ใส่ Thai golden set จริงได้ (เปลี่ยน CORPUS+GOLDEN) · grounded: deep-technical Ch6/39/75 · คู่ ch11*
