"""
Demo 3 — ค้นแบบมีเงื่อนไข: semantic + metadata filter พร้อมกัน
"โน้ตเรื่องการสอน เฉพาะปี 2026 ที่ไม่ใช่ draft"

รัน:  .venv/bin/python demo3_filter_metadata.py
"""
import urllib.request, json
import chromadb
from chromadb.utils.embedding_functions import EmbeddingFunction


class OllamaBgeM3(EmbeddingFunction):
    def __call__(self, texts):
        req = urllib.request.Request(
            "http://localhost:11434/api/embed",
            data=json.dumps({"model": "bge-m3", "input": list(texts)}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["embeddings"]


client = chromadb.PersistentClient(path="./chroma_db")
col = client.get_or_create_collection("vault_demo3", embedding_function=OllamaBgeM3())

col.upsert(
    ids=[f"d{i}" for i in range(1, 7)],
    documents=[
        "แผนสอน vector search สำหรับ workshop เดือนกรกฎาคม",
        "แผนสอน vector search ฉบับร่างแรก ยังไม่เสร็จ",
        "โน้ตสอน SQL พื้นฐานปีที่แล้ว",
        "สรุปงานวิจัย embedding หลายภาษา",
        "บันทึกไอเดียสอน: ใช้เดโมก่อนค่อยลงสมการ",
        "รายจ่ายเดือนกรกฎาคม ค่ากาแฟ 1,200 บาท",
    ],
    metadatas=[
        {"folder": "teaching", "year": 2026, "draft": False},
        {"folder": "teaching", "year": 2026, "draft": True},
        {"folder": "teaching", "year": 2025, "draft": False},
        {"folder": "research", "year": 2026, "draft": False},
        {"folder": "teaching", "year": 2026, "draft": False},
        {"folder": "finance",  "year": 2026, "draft": False},
    ],
)

Q = "การสอนเรื่องค้นหาด้วยความหมาย"

print("=== 1) semantic ล้วน (ไม่ filter) ===")
res = col.query(query_texts=[Q], n_results=3)
for doc in res["documents"][0]:
    print(f"   {doc[:55]}")

print("\n=== 2) + filter: เฉพาะ teaching ปี 2026 ที่ไม่ใช่ draft ===")
res = col.query(
    query_texts=[Q], n_results=3,
    where={"$and": [
        {"folder": {"$eq": "teaching"}},
        {"year": {"$eq": 2026}},
        {"draft": {"$eq": False}},
    ]},
)
for doc in res["documents"][0]:
    print(f"   {doc[:55]}")

print("\n=== 3) filter ด้วยเนื้อหาเอกสาร (where_document) ===")
res = col.query(query_texts=[Q], n_results=3,
                where_document={"$contains": "เดโม"})
for doc in res["documents"][0]:
    print(f"   {doc[:55]}")
