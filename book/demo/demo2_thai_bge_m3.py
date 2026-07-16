"""
Demo 2 — แก้ปัญหาภาษาไทยด้วย bge-m3 (embedder เดียวกับ ARRA production)

Demo 1 ใช้ default embedder (all-MiniLM-L6-v2, 384-dim) → อ่อนภาษาไทย (คะแนนติดลบ/จับคู่ผิด)
Demo 2 เสียบ bge-m3 (1024-dim, multilingual 100+ ภาษา) ผ่าน Ollama เข้า ChromaDB
→ บทเรียน: "vector DB ตัวไหน" สำคัญน้อยกว่า "embedding model ตัวไหน"

ต้องมี: Ollama + `ollama pull bge-m3`
รัน:   .venv/bin/python demo2_thai_bge_m3.py
"""
import urllib.request, json
import chromadb
from chromadb.utils.embedding_functions import EmbeddingFunction


class OllamaBgeM3(EmbeddingFunction):
    """เรียก Ollama /api/embed ด้วย bge-m3 (แบบเดียวกับ arra-oracle-v3 embeddings.ts)"""
    def __call__(self, texts):
        req = urllib.request.Request(
            "http://localhost:11434/api/embed",
            data=json.dumps({"model": "bge-m3", "input": list(texts)}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["embeddings"]


NOTES = {
    "n1": ("วิธีสอนนักศึกษาให้เข้าใจ vector search: เริ่มจาก cosine similarity ก่อน", "teaching"),
    "n2": ("สูตรกาแฟ cold brew: กาแฟ 100g น้ำ 1L แช่ 18 ชั่วโมง", "recipes"),
    "n3": ("ประชุมกับอาจารย์ฝน เรื่อง workshop วันที่ 26 กรกฎาคม ที่มหาวิทยาลัย", "meetings"),
    "n4": ("Embedding คือการแปลงข้อความเป็นตัวเลขหลายมิติที่เก็บความหมาย", "teaching"),
    "n5": ("รายการซื้อของ: นม ไข่ ขนมปัง กาแฟดริป", "personal"),
}

client = chromadb.PersistentClient(path="./chroma_db")
col = client.get_or_create_collection("second_brain_bge", embedding_function=OllamaBgeM3())
col.upsert(
    ids=list(NOTES),
    documents=[t for t, _ in NOTES.values()],
    metadatas=[{"folder": f} for _, f in NOTES.values()],
)

print("=== bge-m3 (1024-dim, multilingual) — query ชุดเดียวกับ demo1 ===")
for q in ["อยากสอนเรื่อง AI ค้นหา", "เครื่องดื่ม", "นัดหมายกับใครบ้าง"]:
    res = col.query(query_texts=[q], n_results=2)
    print(f"\nQ: {q}")
    for doc, dist in zip(res["documents"][0], res["distances"][0]):
        print(f"   {1-dist:.3f}  {doc[:60]}")
