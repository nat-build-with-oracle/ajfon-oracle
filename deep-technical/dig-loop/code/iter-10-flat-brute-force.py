"""Dig-loop 10/50 — Flat brute-force search: the exact O(N) baseline.

Grounded in book/06-ann-search-at-scale.md (real measured numbers, notebook
ch06_ann_benchmark.ipynb): brute force over 1024-dim vectors hits ~0.03ms at
1k notes, ~0.65ms at 10k, ~8-10ms at 100k — numpy SIMD makes "compare against
EVERY vector" far faster than intuition suggests. Lesson: at personal-vault
scale (10k-100k notes), brute force is fast enough; ANN (iter 14-17) only
earns its keep in the millions.
Runnable standalone (uses numpy, stdlib otherwise):
    python iter-10-flat-brute-force.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import time
import numpy as np

rng = np.random.default_rng(3)
DIM = 128   # scaled down from real 1024 to keep this demo fast; same algorithm


def normalize_rows(M):
    return M / np.linalg.norm(M, axis=1, keepdims=True)


def brute_force_topk(query, matrix, k):
    """Exact search: cosine = dot product on unit-normalized vectors.
    This is ALL of book/06 §6.1-6.2 — sort the full N x 1 score column."""
    scores = matrix @ query          # (N,) — one dot product per row, numpy SIMD
    top_idx = np.argsort(-scores)[:k]
    return top_idx, scores[top_idx]


def brute_force_topk_pure_python(query, matrix_list, k):
    """Reference implementation with NO numpy — cross-check the fast path."""
    scores = [sum(a * b for a, b in zip(row, query)) for row in matrix_list]
    ranked = sorted(range(len(scores)), key=lambda i: -scores[i])
    return ranked[:k], [scores[i] for i in ranked[:k]]


# --- plant a known nearest neighbor so we have ground truth -----------------
N = 20_000
corpus = normalize_rows(rng.normal(size=(N, DIM)))
planted_idx = 777
query = normalize_rows((corpus[planted_idx] + rng.normal(scale=0.05, size=DIM))[None, :])[0]

top5_idx, top5_scores = brute_force_topk(query, corpus, 5)

print(f"=== brute force over N={N}, dim={DIM} ===")
print(f"planted nearest = index {planted_idx}")
print(f"top-5 found     = {list(top5_idx)}")
print(f"top-5 scores    = {[round(s, 4) for s in top5_scores]}")

# --- cross-check the numpy fast path against a pure-python reference --------
small_n = 200
small_corpus = corpus[:small_n]
small_top, small_scores = brute_force_topk(query, small_corpus, 5)
ref_top, ref_scores = brute_force_topk_pure_python(query, small_corpus.tolist(), 5)

# --- real measured timing scaling (book/06 §6.2) ----------------------------
def time_search(n, trials=3):
    sub = corpus[:n]
    best = float("inf")
    for _ in range(trials):
        t0 = time.perf_counter()
        brute_force_topk(query, sub, 5)
        best = min(best, time.perf_counter() - t0)
    return best

t_1k = time_search(1_000)
t_10k = time_search(10_000)
t_20k = time_search(20_000)
print(f"\n=== timing (this machine, not book's numbers, same O(N) shape) ===")
print(f"N=1,000  -> {t_1k*1000:.3f} ms")
print(f"N=10,000 -> {t_10k*1000:.3f} ms")
print(f"N=20,000 -> {t_20k*1000:.3f} ms")

# --- asserts -----------------------------------------------------------------
# 1. exact search must actually find the planted nearest neighbor at rank 0
assert top5_idx[0] == planted_idx, "brute force must return the EXACT nearest neighbor (that's the whole point of exact search)"

# 2. scores must be sorted descending
assert all(top5_scores[i] >= top5_scores[i + 1] for i in range(len(top5_scores) - 1)), \
    "top-k scores must be sorted highest-first"

# 3. all cosine scores in valid range
assert all(-1.0 <= s <= 1.0 for s in top5_scores)

# 4. self-similarity check: a corpus vector queried against itself must score ~1
self_idx, self_scores = brute_force_topk(corpus[42], corpus, 1)
assert self_idx[0] == 42 and abs(self_scores[0] - 1.0) < 1e-6, \
    "querying with a vector that's already IN the corpus must return itself, score=1"

# 5. numpy fast path and pure-python reference must agree (same math, same answer)
assert list(small_top) == list(ref_top), "numpy matmul and naive python dot products must rank identically"
assert all(abs(a - b) < 1e-6 for a, b in zip(small_scores, ref_scores)), \
    "numpy and pure-python cosine scores must match to float precision"

# 6. O(N): time must not DECREASE as N grows (loose monotonicity, not exact
#    linearity — book/06's real lesson is "still fast enough", not "linear
#    to the millisecond" on every machine)
assert t_20k >= t_1k * 0.5, \
    "20x more data should not make search faster — brute force must scale with N, not shrink"

print("\n✓ all self-checks passed — brute force = exact answer, O(N), and numpy makes N=20k feel instant.")
