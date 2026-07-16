# บทที่ 8 — Ingest ทั้ง Vault: จากโฟลเดอร์โน้ต → Second Brain

> notebook `ch08_ingest_vault.ipynb` — pipeline จริง รันซ้ำได้ไม่พัง

---

## 8.1 จากโน้ตทีละชิ้น → โฟลเดอร์ทั้งใบ

ของจริงคือโฟลเดอร์ .md เป็นร้อยไฟล์ที่**เปลี่ยนทุกวัน** — pipeline ต้องตอบ 3 โจทย์:
1. แตกไฟล์เป็นชิ้นค้นได้ (chunking)
2. รันซ้ำแล้ว**ไม่ duplicate ไม่ embed ซ้ำ** (idempotent — เพราะ sync ทุกวัน)
3. แก้ไฟล์นิดเดียว → จ่ายแค่ส่วนที่เปลี่ยน

## 8.2 Chunking ตามโครงสร้าง markdown

หัวข้อ (`#`, `##`) คือรอยตัดธรรมชาติที่คนเขียนแบ่งความคิดไว้ให้แล้ว:

```python
def chunk_markdown(text, source):
    # ตัดที่ทุกบรรทัดที่ขึ้นต้นด้วย '#' → 1 section = 1 chunk
    # เก็บ heading + source ติดไปเป็น metadata (provenance)
```

1 ไฟล์ → N chunk · แต่ละ chunk รู้ว่าตัวเองมาจากไฟล์ไหน หัวข้ออะไร → ค้นเจอแล้ว**อ้างอิงกลับได้**

## 8.3 ⭐ Content-hash id — หัวใจของ idempotency

```python
def chunk_id(c):
    return hashlib.sha256(f"{c['source']}|{c['heading']}|{c['text']}".encode()).hexdigest()[:16]
```

id = hash ของเนื้อหา (หลักเดียวกับ git):
- เนื้อหาเดิม → id เดิม → upsert ทับตัวเอง = **ไม่ duplicate**
- เช็ค id ก่อน embed → เนื้อหาเดิม**ไม่ต้อง embed ซ้ำ** = ประหยัด (embed คือส่วนที่แพงสุด)
- เนื้อหาเปลี่ยน → id ใหม่ → embed เฉพาะชิ้นนั้น

## 8.4 ผลรันจริง (พิสูจน์ครบสามโจทย์)

```
รอบ 1:            เพิ่ม 5 · ข้าม 0            (ingest ครั้งแรก)
รอบ 2 (รันซ้ำ):    เพิ่ม 0 · ข้าม 5            ← idempotent!
หลังเพิ่ม section: เพิ่ม 1 · ข้าม 5            ← จ่ายเฉพาะส่วนใหม่
ค้น "วิธีชงกาแฟเข้มๆ" → เจอ section ใหม่ทันที   ← freshness
```

## 8.5 provenance — ตอบพร้อมที่มา

ผลค้นทุกชิ้นแนบ `source` + `heading`:

```
Q: ต้องเตรียมอะไรไปสอน
   📄 workshop-plan.md → อุปกรณ์
      โน้ตบุ๊ก ติดตั้ง Python + Jupyter ล่วงหน้า...
```

นี่คือรากของ "คำตอบที่ verify ได้" — บทที่ 9 จะส่งต่อให้ LLM cite ตามนี้

## 8.6 เชื่อม ARRA

ARRA ทำ pipeline เดียวกันนี้ที่ scale จริง: batch embed ครั้งละ 50 + retry 3 ครั้ง + timeout 30s
+ fallback chain (Ollama→Gemini→CF) — โครงเหมือน notebook เป๊ะ แค่เพิ่มความทนทาน
(deep-technical Ch51/52 มีทุกรายละเอียด)

---

### สรุปบทที่ 8
- ingest = chunk (ตาม `#` heading) → content-hash id → idempotent upsert
- รันซ้ำ: เพิ่ม 0 · แก้ไฟล์: จ่ายแค่ chunk ใหม่ · ของใหม่ค้นเจอทันที — พิสูจน์แล้วทั้งสาม
- ทุก chunk มี provenance (ไฟล์+หัวข้อ) → พร้อมส่งให้ LLM cite (บทที่ 9)

*Notebook: `ch08_ingest_vault.ipynb` (execute ✅) · ลึกกว่า: deep-technical Ch12/45/51/52*
