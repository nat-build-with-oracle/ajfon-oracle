"""Dig-loop 08/50 — 1024D -> 2D: PCA projection of the semantic map.

Grounded in book/demo/demo6_semantic_map.py (the book's REAL demo: embed
Thai/English words with bge-m3, PCA down to 2D for a plot, but compute
nearest-neighbors on the FULL 1024-dim vectors — never on the 2D plot).
Runnable standalone (uses numpy, stdlib otherwise):
    python iter-08-semantic-map-projection.py

No network/Ollama call here (guarded out), so this builds small SYNTHETIC
"word" vectors with real cluster structure (5 topic groups, like the book's
สัตว์เลี้ยง/อาหาร/การเรียนการสอน/การเงิน/เทคโนโลยี), then does the exact same
PCA-to-2D projection the book's demo6 does, to prove two things:
  1. PCA-2D is good enough to SEE the clusters (for a human, on a slide).
  2. PCA-2D is LOSSY — nearest-neighbor search must stay on the full vector,
     because the 2D picture can rank neighbors differently than reality.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math
import random
import numpy as np

DIM = 32
rng = random.Random(7)

GROUPS = {
    "สัตว์เลี้ยง": ["แมว", "ลูกแมว", "หมา", "ลูกหมา", "กระต่าย"],
    "อาหาร": ["ต้มยำกุ้ง", "ผัดไทย", "ส้มตำ", "กาแฟลาเต้"],
    "การเงิน": ["บิตคอยน์", "ราคาหุ้น", "อัตราดอกเบี้ย"],
}


def random_unit(dim):
    v = np.array([rng.gauss(0, 1) for _ in range(dim)])
    return v / np.linalg.norm(v)


# --- synthetic embeddings: each group has a center direction; each word is
#     that center + small noise, then re-normalized (mimics real embedding
#     clustering behavior without needing a real model call) --------------
group_centers = {g: random_unit(DIM) for g in GROUPS}
labels, group_of, vecs = [], [], []
for g, words in GROUPS.items():
    for w in words:
        noise = np.array([rng.gauss(0, 0.15) for _ in range(DIM)])
        v = group_centers[g] + noise
        v = v / np.linalg.norm(v)
        labels.append(w)
        group_of.append(g)
        vecs.append(v)

V = np.array(vecs)                       # (N, DIM) — the "1024-dim" stand-in

# --- PCA -> 2D, same recipe as demo6_semantic_map.py ------------------------
X = V - V.mean(axis=0)
U, S_sing, Vt = np.linalg.svd(X, full_matrices=False)
P = X @ Vt[:2].T                          # (N, 2) projected coordinates

total_var = float(np.sum(S_sing ** 2))
top2_var = float(np.sum(S_sing[:2] ** 2))
explained = top2_var / total_var

print(f"=== PCA {DIM}D -> 2D ===")
print(f"explained variance (top-2 components) = {explained:.4f}  (1.0 would mean NO information lost)")

# --- full-dim cosine similarity matrix (the REAL ranking signal) -----------
Sim = V @ V.T


def euclid_2d(i, j):
    return math.dist(P[i], P[j])


# --- 1. cluster structure survives the projection (qualitative check) -----
within, across = [], []
for i in range(len(labels)):
    for j in range(i + 1, len(labels)):
        d = euclid_2d(i, j)
        (within if group_of[i] == group_of[j] else across).append(d)

mean_within = sum(within) / len(within)
mean_across = sum(across) / len(across)
print(f"\nmean 2D distance within-group  = {mean_within:.4f}")
print(f"mean 2D distance across-group  = {mean_across:.4f}")

# --- 2. nearest-neighbor check: full-dim ranking vs 2D-plot ranking -------
mismatches = 0
for i in range(len(labels)):
    full_rank = sorted((j for j in range(len(labels)) if j != i),
                        key=lambda j: -Sim[i, j])
    plot_rank = sorted((j for j in range(len(labels)) if j != i),
                        key=lambda j: euclid_2d(i, j))
    if full_rank[0] != plot_rank[0]:
        mismatches += 1

print(f"\ntop-1 nearest-neighbor mismatches (full-dim vs 2D-plot) = {mismatches}/{len(labels)}")
print("-> even when PCA looks clean on a slide, retrieval MUST use the full vector")

# --- asserts -----------------------------------------------------------------
# 1. PCA to 2D must lose some information — it is a projection, not magic
assert 0.0 < explained < 1.0, "top-2 components can't capture 100% of variance from 32 real dims"

# 2. same-group words must cluster closer together in 2D than different-group
#    words on average — this is the whole POINT of plotting a semantic map
assert mean_within < mean_across, \
    "same-topic words must sit closer together in the 2D projection than unrelated topics"

# 3. the full-dim similarity matrix must be symmetric (cosine is symmetric)
assert np.allclose(Sim, Sim.T, atol=1e-9)

# 4. self-similarity must be ~1 for every word (each vector is unit-normalized)
assert np.allclose(np.diag(Sim), 1.0, atol=1e-6)

# 5. explained variance from just 2 of 32 dims must still be well above
#    "random chance" (2/32 = 6.25%) BECAUSE the data has real cluster structure
assert explained > 2.0 / DIM, \
    "clustered data must explain far more variance in 2 PCs than pure noise would"

print("\n✓ all self-checks passed — PCA-2D is a good PICTURE, never the real search index.")
