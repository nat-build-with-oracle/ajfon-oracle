"""Dig-loop 35/50 — Matryoshka embeddings: truncate the prefix, keep the quality.

Grounded in deep-technical/36-matryoshka-dimensionality.md §36.1 (MRL trains
InfoNCE at MULTIPLE prefix lengths simultaneously -- forcing the most
important signal into the FRONT dimensions, so v[:256] from a 1024-dim
Matryoshka vector stays good) and §36.3 (adaptive 2-stage retrieval: coarse
search on truncated dims for speed -> fine rerank candidates on full dims
for accuracy -- the same recall-recovery pattern as quantization, Ch8 §8.5,
but along the DIMENSION axis instead of precision).
Runnable standalone (uses numpy, stdlib otherwise):
    python iter-35-matryoshka-dims.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import numpy as np

rng = np.random.default_rng(23)
N, DIM, TRUNC = 200, 64, 16   # scaled down from 1024/256, same ratio (4x)


def normalize_rows(X):
    return X / np.linalg.norm(X, axis=1, keepdims=True)


def make_vectors(front_loaded):
    """front_loaded=True: MRL-style -- most signal lives in dims[:TRUNC].
    front_loaded=False: ordinary embedding -- signal spread evenly."""
    if front_loaded:
        front = rng.normal(size=(N, TRUNC)) * 3.0      # strong signal, front dims
        tail = rng.normal(size=(N, DIM - TRUNC)) * 0.3  # weak noise, tail dims
        X = np.concatenate([front, tail], axis=1)
    else:
        X = rng.normal(size=(N, DIM))                   # uniform signal, all dims
    return normalize_rows(X)


def truncate_and_renormalize(X, k):
    return normalize_rows(X[:, :k])


def topk_ids(vectors, query, k=5):
    scores = vectors @ query
    return set(np.argsort(-scores)[:k].tolist())


matryoshka_vecs = make_vectors(front_loaded=True)
regular_vecs = make_vectors(front_loaded=False)

matryoshka_query = matryoshka_vecs[7] + rng.normal(scale=0.05, size=DIM)
matryoshka_query = matryoshka_query / np.linalg.norm(matryoshka_query)
regular_query = regular_vecs[7] + rng.normal(scale=0.05, size=DIM)
regular_query = regular_query / np.linalg.norm(regular_query)


def truncation_overlap(vectors, query, k=5):
    full_top = topk_ids(vectors, query, k)
    trunc_vecs = truncate_and_renormalize(vectors, TRUNC)
    trunc_query = truncate_and_renormalize(query[None, :], TRUNC)[0]
    trunc_top = topk_ids(trunc_vecs, trunc_query, k)
    return len(full_top & trunc_top) / k, full_top, trunc_top


mat_overlap, mat_full_top, mat_trunc_top = truncation_overlap(matryoshka_vecs, matryoshka_query)
reg_overlap, reg_full_top, reg_trunc_top = truncation_overlap(regular_vecs, regular_query)

print(f"=== truncate {DIM}D -> {TRUNC}D: does top-5 survive? ===")
print(f"Matryoshka-style (front-loaded signal): overlap = {mat_overlap:.2f}  "
      f"(full={sorted(mat_full_top)}, trunc={sorted(mat_trunc_top)})")
print(f"Regular embedding (signal spread evenly): overlap = {reg_overlap:.2f}  "
      f"(full={sorted(reg_full_top)}, trunc={sorted(reg_trunc_top)})")

# --- adaptive 2-stage: coarse (truncated) -> fine (full-dim rerank) --------
def adaptive_retrieval(vectors, query, coarse_k=30, final_k=5):
    trunc_vecs = truncate_and_renormalize(vectors, TRUNC)
    trunc_query = truncate_and_renormalize(query[None, :], TRUNC)[0]
    coarse_candidates = topk_ids(trunc_vecs, trunc_query, coarse_k)
    candidates = list(coarse_candidates)
    fine_scores = vectors[candidates] @ query
    order = np.argsort(-fine_scores)[:final_k]
    return set(np.array(candidates)[order].tolist())


reg_adaptive_top = adaptive_retrieval(regular_vecs, regular_query)
reg_full_top5, _, _ = (topk_ids(regular_vecs, regular_query, 5), None, None)

print(f"\n=== adaptive 2-stage on the HARD case (regular embedding) ===")
print(f"naive truncated-only top-5 recall vs full  = {reg_overlap:.2f}")
adaptive_overlap = len(reg_adaptive_top & reg_full_top) / 5
print(f"adaptive (coarse-30 -> fine rerank) recall  = {adaptive_overlap:.2f}  <- recovered")

# --- asserts -----------------------------------------------------------------
# 1. Matryoshka-style truncation must preserve top-5 with HIGH overlap
#    (book: "ต่าง full ~1-2%" -- here demand at least 0.8 given the coarser toy scale)
assert mat_overlap >= 0.8, "Matryoshka-style (front-loaded) truncation must preserve most of the top-5"

# 2. Regular embedding truncation must show a REAL degradation -- truncating
#    dims that weren't specially trained to front-load signal must hurt more
assert reg_overlap < mat_overlap, \
    "truncating a regular (non-Matryoshka) embedding must degrade recall more than truncating a Matryoshka one"

# 3. the degradation for regular embeddings must be substantial, not trivial
assert reg_overlap <= 0.6, "regular-embedding truncation must show a clearly worse overlap than the Matryoshka case"

# 4. adaptive 2-stage retrieval must RECOVER much of the lost recall on the
#    hard (regular-embedding) case -- the whole point of coarse-to-fine
assert adaptive_overlap > reg_overlap, \
    "adaptive coarse-to-fine retrieval must beat naive truncated-only search on the regular-embedding case"
assert adaptive_overlap >= 0.8, "adaptive retrieval must recover close to full-dim recall by reranking with full vectors"

# 5. sanity: truncated vectors must actually be shorter (fewer floats stored)
assert truncate_and_renormalize(matryoshka_vecs, TRUNC).shape[1] == TRUNC

print("\n✓ all self-checks passed — Matryoshka front-loads signal so truncation is cheap; adaptive retrieval recovers recall either way.")
