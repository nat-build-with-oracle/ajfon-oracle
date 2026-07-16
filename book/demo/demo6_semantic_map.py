"""
Demo 6 — Semantic Map: embed คำจริงด้วย bge-m3 → PCA ลง 2D → เห็นกลุ่มความหมาย
คำความหมายใกล้กันจะ "กองอยู่ด้วยกัน" เอง — ไม่มีใครบอกโมเดลว่าคำไหนกลุ่มไหน

รัน:  .venv/bin/python demo6_semantic_map.py > semantic_map.json
"""
import urllib.request, json
import numpy as np

WORDS = {
    "สัตว์เลี้ยง": ["แมว", "ลูกแมว", "หมา", "ลูกหมา", "กระต่าย", "cat", "puppy"],
    "อาหาร": ["ต้มยำกุ้ง", "ผัดไทย", "ส้มตำ", "กาแฟลาเต้", "ชาเขียว"],
    "การเรียนการสอน": ["ประชุมกับอาจารย์", "นัดหมายสัมมนา", "workshop", "สอนนักศึกษา", "งานวิจัย"],
    "การเงิน": ["บิตคอยน์", "ราคาหุ้น", "อัตราดอกเบี้ย", "เงินเฟ้อ"],
    "เทคโนโลยี": ["vector search", "embedding", "ปัญญาประดิษฐ์", "ฐานข้อมูล"],
}


def embed(texts):
    req = urllib.request.Request(
        "http://localhost:11434/api/embed",
        data=json.dumps({"model": "bge-m3", "input": texts}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return np.array(json.load(r)["embeddings"])


labels, groups = [], []
for g, ws in WORDS.items():
    for w in ws:
        labels.append(w)
        groups.append(g)

V = embed(labels)                        # (N, 1024)
V = V / np.linalg.norm(V, axis=1, keepdims=True)

# PCA → 2D (จาก 1024 มิติ ฉายลงกระดาษ)
X = V - V.mean(axis=0)
_, _, Vt = np.linalg.svd(X, full_matrices=False)
P = X @ Vt[:2].T                         # (N, 2)
P = (P - P.min(0)) / (P.max(0) - P.min(0))  # normalize 0..1

# เพื่อนบ้านใกล้สุด 3 อันดับ (cosine บน 1024 มิติเต็ม — ไม่ใช่บน 2D!)
S = V @ V.T
out = []
for i, w in enumerate(labels):
    nb = np.argsort(-S[i])
    nb = [j for j in nb if j != i][:3]
    out.append({
        "w": w, "g": groups[i],
        "x": round(float(P[i, 0]), 4), "y": round(float(P[i, 1]), 4),
        "nb": [{"w": labels[j], "s": round(float(S[i, j]), 3)} for j in nb],
    })

print(json.dumps(out, ensure_ascii=False, indent=1))
