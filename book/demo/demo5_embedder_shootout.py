"""
Demo 5 — embedder shootout: 3 โมเดลใน Ollama เจอโจทย์ไทยชุดเดียวกัน
bge-m3 (1024) vs nomic-embed-text (768) vs qwen3-embedding:0.6b (1024)

โจทย์: คู่ประโยค "ควรใกล้" vs คู่ "ไม่ควรใกล้" — โมเดลที่ดีต้องแยก gap ชัด

รัน:  .venv/bin/python demo5_embedder_shootout.py
"""
import math, urllib.request, json


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(x*x for x in b)))


def embed(model, texts):
    req = urllib.request.Request(
        "http://localhost:11434/api/embed",
        data=json.dumps({"model": model, "input": texts}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["embeddings"]


# คู่ทดสอบ: (ประโยค A, ประโยค B, ควรใกล้ไหม)
PAIRS = [
    ("ประชุมกับอาจารย์เรื่องเวิร์กช็อป", "นัดหมายคุยงานสัมมนากับผู้สอน", True),   # ไทย↔ไทย พาราเฟรส
    ("วิธีลดน้ำหนักอย่างปลอดภัย",       "การควบคุมอาหารและออกกำลังกาย",   True),   # ไทย↔ไทย ความหมายเกี่ยว
    ("แมวนอนบนโซฟา",                  "The cat is sleeping on the couch", True),   # ไทย↔อังกฤษ (cross-lingual)
    ("ประชุมกับอาจารย์เรื่องเวิร์กช็อป", "สูตรต้มยำกุ้งน้ำข้น",              False),  # คนละเรื่อง
    ("วิธีลดน้ำหนักอย่างปลอดภัย",       "ราคาบิตคอยน์วันนี้ผันผวน",         False),  # คนละเรื่อง
]

MODELS = ["bge-m3", "nomic-embed-text", "qwen3-embedding:0.6b"]

print(f"{'โมเดล':<24} {'คู่ใกล้ (เฉลี่ย)':>16} {'คู่ไกล (เฉลี่ย)':>16} {'GAP':>8}")
print("-" * 68)
for model in MODELS:
    try:
        sims = []
        for a, b, _ in PAIRS:
            va, vb = embed(model, [a, b])
            sims.append(cosine(va, vb))
        near = [s for s, (_, _, ok) in zip(sims, PAIRS) if ok]
        far = [s for s, (_, _, ok) in zip(sims, PAIRS) if not ok]
        gap = sum(near)/len(near) - sum(far)/len(far)
        print(f"{model:<24} {sum(near)/len(near):>16.3f} {sum(far)/len(far):>16.3f} {gap:>8.3f}")
    except Exception as e:
        print(f"{model:<24} FAILED: {e}")

print("\nGAP = ยิ่งกว้าง ยิ่งแยก 'เกี่ยว/ไม่เกี่ยว' ชัด → threshold ตั้งง่าย ค้นแม่น")
