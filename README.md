# 📚 Second Brain ด้วย Vector Search

> หนังสือสอน vector search แบบ **ลงมือทำ** — จากสมการถึงระบบจริง (ChromaDB · LanceDB · Cloudflare Edge)
> ทุกบทมี Jupyter notebook ที่ **รันได้จริง + มีเซลล์วัดผล** · เปิดใน Google Colab คลิกเดียว
>
> ARRA Oracle · Workshop 26 กรกฎาคม 2026

---

## หนังสือเล่มนี้ต่างจากที่อื่นยังไง

**ทุกคำอ้างในเล่มมีตัวเลขรองรับ ที่คุณรันซ้ำเองได้** — ไม่ใช่ความเห็น เป็นผลจากการรันจริง เช่น:

- default embedder อ่อนภาษาไทย → พิสูจน์ด้วย golden set: `MiniLM recall@3 = 0.36` vs `bge-m3 = 0.93`
- ANN ไม่ได้เร็วกว่าเสมอ → ที่ 20k โน้ต **brute force (2.9ms) ชนะ HNSW (12.6ms)**
- "มีหลาย engine ดีกว่า" → **ไม่จริง**: triple-RRF แย่กว่า bge-m3 เดี่ยว (complementary recall = 0%)

ธีมเดียวของทั้งเล่ม: **"วัด อย่าเดา"**

---

## 🚀 เริ่มเลย — เปิดใน Colab (ไม่ต้องติดตั้งอะไร)

คลิกเปิดบทแรกได้เลย รันบนคลาวด์ฟรี:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/laris-co/ajfon-oracle/blob/main/book/notebooks/ch01_second_brain_20_lines.ipynb)

ทุก notebook ในโฟลเดอร์ [`book/notebooks/`](book/notebooks/) มีปุ่ม **Open in Colab** ที่เซลล์แรก

---

## 📖 สารบัญ (17 บท · 4 ภาค + Extras)

| ภาค | บท |
|-----|-----|
| **1 · เห็นมันทำงาน** | 1 Second Brain 20 บรรทัด · 2 แก้ไทยด้วย bge-m3 · 3 filter + metadata |
| **2 · เข้าใจว่าทำไม** | 4 cosine (สมการเดียว) · 5 embedding มาจากไหน · 6 ANN + scale-appropriate |
| **3 · ระบบจริง** | 7 hybrid (BM25 + RRF) · 8 ingest idempotent · 9 RAG + cite + abstain |
| **4 · Production** | 10 Chroma → LanceDB · 11 golden set + recall/nDCG · 12 privacy & local-first |
| **Production DB** | 13 LanceDB · 14 hybrid ในตัว · 15 time-travel |
| **✨ Extras** | 16 Cloudflare Edge (Workers AI + Vectorize) · 17 multi-engine benchmark |

อ่านแบบเว็บ (มีผลรัน + กราฟในตัว): เปิด [`book/html/index.html`](book/html/) · หรือดาวน์โหลด [PDF](book/pdf/)

---

## 🖥️ รันในเครื่อง (แนะนำ — ได้ privacy + ไม่มี network)

ต้องมี [Ollama](https://ollama.com) + โมเดล embedding:

```bash
ollama pull bge-m3

cd book
uv venv .venv --python 3.12          # หรือ python3 -m venv .venv
uv pip install --python .venv/bin/python jupyterlab chromadb lancedb sentence-transformers scikit-learn matplotlib
.venv/bin/jupyter lab notebooks/
```

notebook ทุกตัวตรวจสภาพแวดล้อมเอง: **เครื่องเรา → Ollama** · **Colab → sentence-transformers** อัตโนมัติ

---

## 📂 โครงสร้าง

```
book/
  01..17-*.md              บทหนังสือ (markdown)
  notebooks/ch01..17.ipynb Jupyter notebook รันได้ + เซลล์วัดผล (self-check assert)
  html/                    เว็บหนังสือ (nbconvert + ธีมเข้าถึงได้ WCAG AA)
  pdf/                     หนังสือเล่มสมบูรณ์ (Sarabun)
  demo/                    สคริปต์เดโมเดี่ยวๆ
deep-technical/            เอกสารทฤษฎีลึก 86 บท (คณิต attention → CAP theorem)
```

---

## เนื้อหาต่อยอด

- **ทฤษฎีลึกทุกหัวข้อ**: [`deep-technical/`](deep-technical/) — 86 บท จากสมการ self-attention ถึง CAP theorem
- **ระบบ production จริง**: ARRA Oracle — ทุก pattern ในเล่มนี้ทำงานจริงในระบบนั้น

---

*เขียนด้วยหลัก "วัด อย่าเดา" · ทุก notebook execute ผ่านจริง + verify contrast (WCAG AA) ก่อนเผยแพร่*
