"""
Demo 4 — cosine similarity คำนวณมือ (ไม่มี library ยกเว้น math)
พิสูจน์ว่า "ความใกล้ของความหมาย" = สมการบรรทัดเดียว
แล้วเทียบกับ embedding จริงจาก bge-m3

รัน:  .venv/bin/python demo4_cosine_by_hand.py
"""
import math, urllib.request, json


def cosine(a, b):
    """สมการเดียวของทั้งเล่ม: cos = (A·B) / (|A| |B|)"""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


# ---- ส่วนที่ 1: เวกเตอร์ของเล่น 2 มิติ (วาดบนกระดาษได้) ----
print("=== 1) ของเล่น 2 มิติ: [ความเป็นแมว, ความเป็นรถ] ===")
cat = [0.9, 0.1]      # "แมว"
kitten = [0.85, 0.15] # "ลูกแมว"
car = [0.1, 0.95]     # "รถยนต์"
print(f"   cos(แมว, ลูกแมว) = {cosine(cat, kitten):.4f}   ← ใกล้ 1 = ความหมายใกล้")
print(f"   cos(แมว, รถยนต์) = {cosine(cat, car):.4f}   ← ใกล้ 0 = ไม่เกี่ยวกัน")

# ---- ส่วนที่ 2: embedding จริงจาก bge-m3 (1024 มิติ) — สมการเดิมเป๊ะ ----
def embed(texts):
    req = urllib.request.Request(
        "http://localhost:11434/api/embed",
        data=json.dumps({"model": "bge-m3", "input": texts}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["embeddings"]


print("\n=== 2) embedding จริง bge-m3 (1024 มิติ) — ฟังก์ชัน cosine ตัวเดิม ===")
texts = ["แมวนอนบนโซฟา", "ลูกแมวหลับอยู่บนเก้าอี้", "ราคาน้ำมันดีเซลปรับขึ้นวันนี้"]
vecs = embed(texts)
print(f"   มิติจริง: {len(vecs[0])}")
print(f"   cos(แมวนอนโซฟา, ลูกแมวหลับเก้าอี้) = {cosine(vecs[0], vecs[1]):.4f}")
print(f"   cos(แมวนอนโซฟา, ราคาน้ำมันดีเซล)   = {cosine(vecs[0], vecs[2]):.4f}")
print("\n   → ประโยคแมว 2 ประโยค ไม่มีคำซ้ำกันเลย แต่ cosine สูงกว่าชัดเจน")
print("   → นี่คือทั้งหมดที่ vector database ทำ: เก็บเวกเตอร์ + หา cosine สูงสุด")
