# บทที่ 12 (บทส่งท้าย) — Privacy & Local-First

> notebook `ch12_privacy_local_first.ipynb` — พิสูจน์ว่าทั้งเล่มข้อมูลไม่เคยออกจากเครื่อง

## 12.1 สิ่งที่เราทำมาตลอดโดยไม่ได้พูดถึง

ทุก endpoint ที่ใช้ทั้ง 12 บท:

```
🔒 embedding (bge-m3)   http://localhost:11434  (Ollama ในเครื่อง)
🔒 LLM (gemma3)         http://localhost:11434
🔒 vector DB            ./chroma_db  (ไฟล์ในเครื่อง — ไม่มี network เลย)
```

โน้ตส่วนตัว งานวิจัยยังไม่ตีพิมพ์ ข้อมูลนักศึกษา — **ไม่มีสักไบต์ที่ออกอินเทอร์เน็ต**

## 12.2 ownership ที่จับต้องได้

สมองที่สอง = โฟลเดอร์เดียว: อยากย้ายเครื่อง copy · อยาก backup zip · อยากลบ ลบทิ้ง
ไม่มี vendor ไม่มี subscription ไม่มี API key หมดอายุ

## 12.3 ต้นทุน (คำนวณใน notebook)

ที่ scale ส่วนตัว cloud ก็ไม่แพง ($ หลักหน่วย/ปี) — **เงินไม่ใช่ประเด็น
privacy กับ ownership ต่างหาก** · ARRA เลือก local-first ด้วยเหตุผลเดียวกัน (D1/R2 เป็นชั้น sync เสริม)

## 12.4 จบเล่ม — สิ่งที่ผู้อ่านทำได้แล้วจริง (พิสูจน์ด้วย self-check ทั้ง 12 บท)

สร้าง second brain 20 บรรทัด → เลือก embedder เป็น (วัดด้วย GAP) → filter → เข้าใจ cosine ถึงระดับคำนวณมือ
→ อ่านแผนที่ความหมายเป็น → รู้จัก O(N)/ANN → สร้าง hybrid เอง → ingest idempotent
→ RAG+cite+abstain → ย้าย DB โดยผลไม่เปลี่ยน → **วัดผลเอง (0.93 vs 0.36)** → ทั้งหมด local 100%

*Notebook: `ch12_privacy_local_first.ipynb` (execute ✅) · ลึกกว่า: deep-technical Ch14/27/62/70*
