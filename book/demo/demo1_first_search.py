"""
Demo 1 — Second Brain แรกของคุณใน 20 บรรทัด
ChromaDB: pip install เดียว, embedding ในตัว (all-MiniLM-L6-v2), ไม่ต้องมี server

รัน:  .venv/bin/python demo1_first_search.py
"""
import chromadb

# 1) persistent client — ข้อมูลอยู่ในโฟลเดอร์ ./chroma_db (เครื่องเรา, privacy)
client = chromadb.PersistentClient(path="./chroma_db")
col = client.get_or_create_collection("second_brain")

# 2) ใส่โน้ต (upsert = ทำซ้ำได้ไม่ duplicate — idempotent)
col.upsert(
    ids=["n1", "n2", "n3", "n4", "n5"],
    documents=[
        "วิธีสอนนักศึกษาให้เข้าใจ vector search: เริ่มจาก cosine similarity ก่อน",
        "สูตรกาแฟ cold brew: กาแฟ 100g น้ำ 1L แช่ 18 ชั่วโมง",
        "ประชุมกับอาจารย์ฝน เรื่อง workshop วันที่ 26 กรกฎาคม ที่มหาวิทยาลัย",
        "Embedding คือการแปลงข้อความเป็นตัวเลขหลายมิติที่เก็บความหมาย",
        "รายการซื้อของ: นม ไข่ ขนมปัง กาแฟดริป",
    ],
    metadatas=[
        {"folder": "teaching", "year": 2026},
        {"folder": "recipes", "year": 2025},
        {"folder": "meetings", "year": 2026},
        {"folder": "teaching", "year": 2026},
        {"folder": "personal", "year": 2026},
    ],
)

# 3) ค้นด้วยความหมาย — ไม่ต้องมีคำตรงกัน!
for q in ["อยากสอนเรื่อง AI ค้นหา", "เครื่องดื่ม", "นัดหมายกับใครบ้าง"]:
    res = col.query(query_texts=[q], n_results=2)
    print(f"\nQ: {q}")
    for doc, dist in zip(res["documents"][0], res["distances"][0]):
        print(f"   {1-dist:.3f}  {doc[:60]}")

# 4) semantic + filter (Ch55/61: structured + vector พร้อมกัน)
res = col.query(query_texts=["การสอน"], n_results=5, where={"folder": "teaching"})
print(f"\nQ: การสอน (filter: folder=teaching เท่านั้น)")
for doc in res["documents"][0]:
    print(f"   → {doc[:60]}")
