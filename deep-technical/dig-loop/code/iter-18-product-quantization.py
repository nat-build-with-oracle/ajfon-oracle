"""Dig-loop 18/50 — Product Quantization: compress vectors, ANN via lookup.

Grounded in deep-technical/08-quantization-and-metric-proofs.md §8.3 (PQ:
split a vector into m subvectors, quantize each to 1-of-256 codeword via a
per-subspace codebook -- 1024-dim float32 (4KB) -> m bytes; ADC = precompute
query<->codeword distance table once, then just LOOKUP+ADD per candidate,
no real multiply needed) and §8.5 (recall recovery: search on compressed,
rerank top candidates on full precision).
Runnable standalone (uses numpy, stdlib otherwise):
    python iter-18-product-quantization.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import numpy as np

rng = np.random.default_rng(13)
N, DIM = 3000, 32
M_SUBVECTORS = 8            # split DIM into 8 subvectors of 4 dims each
SUB_DIM = DIM // M_SUBVECTORS
CODEBOOK_SIZE = 16          # 16 codewords/subspace (4 bits) -- keeps demo fast;
                            # real PQ commonly uses 256 (8 bits) per §8.3

vectors = rng.normal(size=(N, DIM)).astype(np.float32)


def train_codebooks(X, m, sub_dim, k, iters=10):
    """k-means PER SUBSPACE -- exactly PQ's 'train' step (§8.3)."""
    codebooks = []
    for j in range(m):
        sub = X[:, j * sub_dim:(j + 1) * sub_dim]
        idx = rng.choice(len(sub), size=k, replace=False)
        centroids = sub[idx].copy()
        for _ in range(iters):
            d2 = ((sub[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
            assign = np.argmin(d2, axis=1)
            for c in range(k):
                members = sub[assign == c]
                if len(members) > 0:
                    centroids[c] = members.mean(axis=0)
        codebooks.append(centroids)
    return codebooks


def pq_encode(X, codebooks, m, sub_dim):
    """Each vector -> m codeword indices (the PQ(x) = (c1..cm) of §8.3)."""
    codes = np.zeros((len(X), m), dtype=np.uint8)
    for j, cb in enumerate(codebooks):
        sub = X[:, j * sub_dim:(j + 1) * sub_dim]
        d2 = ((sub[:, None, :] - cb[None, :, :]) ** 2).sum(axis=2)
        codes[:, j] = np.argmin(d2, axis=1)
    return codes


def adc_distance_table(qvec, codebooks, m, sub_dim):
    """Precompute query<->EVERY codeword distance, ONCE per query (§8.3)."""
    tables = []
    for j, cb in enumerate(codebooks):
        qsub = qvec[j * sub_dim:(j + 1) * sub_dim]
        tables.append(((cb - qsub[None, :]) ** 2).sum(axis=1))   # (k,)
    return tables   # m tables of shape (k,)


def adc_search(qvec, codes, codebooks, m, sub_dim, k_results=5):
    """Distance via LOOKUP + ADD only -- no direct multiply against data (§8.3)."""
    tables = adc_distance_table(qvec, codebooks, m, sub_dim)
    approx_d2 = np.zeros(len(codes))
    for j in range(m):
        approx_d2 += tables[j][codes[:, j]]     # pure lookup + accumulate
    return np.argsort(approx_d2)[:k_results], approx_d2


def exact_topk(qvec, X, k=5):
    d2 = ((X - qvec[None, :]) ** 2).sum(axis=1)
    return np.argsort(d2)[:k]


print(f"=== training PQ: {M_SUBVECTORS} subspaces x {CODEBOOK_SIZE} codewords ===")
codebooks = train_codebooks(vectors, M_SUBVECTORS, SUB_DIM, CODEBOOK_SIZE)
codes = pq_encode(vectors, codebooks, M_SUBVECTORS, SUB_DIM)

original_bytes = DIM * 4          # float32
pq_bytes = M_SUBVECTORS * 1       # 1 byte per subvector index (fits in uint8 here)
print(f"original: {original_bytes} bytes/vector  ->  PQ: {pq_bytes} bytes/vector "
      f"({original_bytes / pq_bytes:.0f}x compression)")

query_ids = rng.choice(N, size=30, replace=False)
recall_total = 0.0
for qi in query_ids:
    qvec = vectors[qi]
    true_top5 = set(exact_topk(qvec, vectors, k=5).tolist())
    approx_top5, _ = adc_search(qvec, codes, codebooks, M_SUBVECTORS, SUB_DIM, k_results=5)
    recall_total += len(set(approx_top5.tolist()) & true_top5) / 5
recall = recall_total / len(query_ids)
print(f"\nPQ (ADC) recall@5 over {len(query_ids)} queries = {recall:.3f}")

# --- recall recovery (§8.5): over-fetch with PQ, rerank exact on candidates -
def recall_recovery_search(qvec, over_fetch_k=150, final_k=5):
    coarse_ids, _ = adc_search(qvec, codes, codebooks, M_SUBVECTORS, SUB_DIM, k_results=over_fetch_k)
    exact_d2 = ((vectors[coarse_ids] - qvec[None, :]) ** 2).sum(axis=1)
    order = np.argsort(exact_d2)[:final_k]
    return coarse_ids[order]


recovery_recall_total = 0.0
for qi in query_ids:
    qvec = vectors[qi]
    true_top5 = set(exact_topk(qvec, vectors, k=5).tolist())
    recovered = set(recall_recovery_search(qvec).tolist())
    recovery_recall_total += len(recovered & true_top5) / 5
recovery_recall = recovery_recall_total / len(query_ids)
print(f"PQ + over-fetch(150) + exact rerank recall@5 = {recovery_recall:.3f}  (§8.5 pattern)")

# --- asserts -----------------------------------------------------------------
# 1. real compression ratio must match the book's math exactly for this shape
assert original_bytes / pq_bytes == 16.0, "8 subvectors x 1 byte from a 32-dim float32 vector must compress exactly 16x"

# 2. ADC lookup-table distance must be a genuine APPROXIMATION -- some real
#    quantization error must exist vs the true distance (not accidentally exact)
qvec0 = vectors[query_ids[0]]
_, approx_d2 = adc_search(qvec0, codes, codebooks, M_SUBVECTORS, SUB_DIM, k_results=5)
true_d2 = ((vectors - qvec0[None, :]) ** 2).sum(axis=1)
assert np.mean(np.abs(approx_d2 - true_d2)) > 1e-6, "PQ distance must show real quantization error vs exact distance"

# 3. pure PQ (no rerank) must have imperfect recall -- otherwise this demo
#    isn't actually testing lossy compression
assert recall < 0.95, "raw PQ-only recall must show a measurable quality loss from compression"

# 4. recall-recovery (over-fetch + exact rerank) must beat raw PQ recall --
#    the entire point of §8.5's pattern
assert recovery_recall > recall, "over-fetch + exact-rerank must improve recall over PQ alone"
assert recovery_recall > 0.9, "recall-recovery pattern must restore recall close to exact search"

# 5. codes must actually be valid indices into their own codebook
assert codes.min() >= 0 and codes.max() < CODEBOOK_SIZE

print("\n✓ all self-checks passed — PQ compresses 16x here, ADC is lookup+add, and over-fetch+rerank recovers recall.")
