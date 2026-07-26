"""Dig-loop 19/50 — Scalar (int8) and Binary (1-bit) quantization: memory math.

Grounded in deep-technical/08-quantization-and-metric-proofs.md §8.2 (SQ:
float32->int8 per dimension, q(x)=round((x-min)/(max-min)*255), 4x compression,
~1-2% recall loss) and §8.4 (BQ: sign bit per dimension, distance=Hamming
popcount(a XOR b), 32x compression, recall loss is real -> used as a COARSE
filter, then rerank top candidates on full precision, §8.5's pattern again).
Runnable standalone (uses numpy, stdlib otherwise):
    python iter-19-scalar-binary-quant.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import numpy as np

rng = np.random.default_rng(17)
N, DIM = 3000, 128

vectors = rng.normal(size=(N, DIM)).astype(np.float32)


# --- Scalar Quantization: float32 -> int8, per-dimension min/max (§8.2) -----
def sq_encode(X):
    mins = X.min(axis=0)
    maxs = X.max(axis=0)
    span = np.where(maxs > mins, maxs - mins, 1.0)
    codes = np.round((X - mins) / span * 255).astype(np.uint8)
    return codes, mins, span


def sq_decode(codes, mins, span):
    return mins + (codes.astype(np.float32) / 255) * span


# --- Binary Quantization: sign bit per dimension (§8.4) ---------------------
def bq_encode(X):
    return (X > 0)   # boolean array, 1 bit "worth" of info per dim


def hamming_distance(a_bits, B_bits):
    return np.sum(a_bits[None, :] != B_bits, axis=1)


def exact_topk(qvec, X, k=5):
    d2 = ((X - qvec[None, :]) ** 2).sum(axis=1)
    return np.argsort(d2)[:k]


# --- run both quantizations --------------------------------------------------
sq_codes, sq_mins, sq_span = sq_encode(vectors)
sq_dequant = sq_decode(sq_codes, sq_mins, sq_span)

bq_codes = bq_encode(vectors)

original_bytes = DIM * 4
sq_bytes = DIM * 1
bq_bytes = DIM // 8   # 1 bit per dim, packed

print(f"=== compression (dim={DIM}) ===")
print(f"original (float32): {original_bytes} bytes/vector")
print(f"SQ (int8):           {sq_bytes} bytes/vector  ({original_bytes/sq_bytes:.0f}x)")
print(f"BQ (1-bit):          {bq_bytes} bytes/vector  ({original_bytes/bq_bytes:.0f}x)")

query_ids = rng.choice(N, size=30, replace=False)


def sq_topk(qi, k=5):
    qvec_dequant = sq_dequant[qi]   # simulate: query ALSO goes through SQ round-trip
    d2 = ((sq_dequant - qvec_dequant[None, :]) ** 2).sum(axis=1)
    return np.argsort(d2)[:k]


def bq_topk(qi, k=5):
    dists = hamming_distance(bq_codes[qi], bq_codes)
    return np.argsort(dists)[:k]


def bq_coarse_then_rerank(qi, coarse_k=800, final_k=5):
    dists = hamming_distance(bq_codes[qi], bq_codes)
    coarse_ids = np.argsort(dists)[:coarse_k]
    qvec = vectors[qi]
    exact_d2 = ((vectors[coarse_ids] - qvec[None, :]) ** 2).sum(axis=1)
    order = np.argsort(exact_d2)[:final_k]
    return coarse_ids[order]


sq_recall, bq_recall, recovery_recall = 0.0, 0.0, 0.0
for qi in query_ids:
    true5 = set(exact_topk(vectors[qi], vectors, 5).tolist())
    sq_recall += len(set(sq_topk(qi).tolist()) & true5) / 5
    bq_recall += len(set(bq_topk(qi).tolist()) & true5) / 5
    recovery_recall += len(set(bq_coarse_then_rerank(qi).tolist()) & true5) / 5

sq_recall /= len(query_ids)
bq_recall /= len(query_ids)
recovery_recall /= len(query_ids)

print(f"\n=== recall@5 over {len(query_ids)} queries ===")
print(f"SQ (int8, {original_bytes/sq_bytes:.0f}x compressed)          recall@5 = {sq_recall:.3f}")
print(f"BQ (1-bit, {original_bytes/bq_bytes:.0f}x compressed) alone   recall@5 = {bq_recall:.3f}  <- coarse only")
print(f"BQ coarse(800) + exact rerank              recall@5 = {recovery_recall:.3f}  (§8.4/§8.5 pipeline)")

# --- asserts -----------------------------------------------------------------
# 1. compression ratios must match the book's exact math for this shape
assert original_bytes / sq_bytes == 4.0, "SQ must compress float32->int8 by exactly 4x"
assert original_bytes / bq_bytes == 32.0, "BQ must compress float32->1-bit by exactly 32x"

# 2. SQ must have HIGH recall (book: ~1-2% loss) -- fine quantization keeps
#    almost all ranking information
assert sq_recall > 0.85, "SQ (int8) recall must stay high -- only a small quantization step per dim"

# 3. BQ ALONE must have noticeably lower recall than SQ -- 1 bit/dim throws
#    away far more information than 8 bits/dim (book: BQ recall loses a lot)
assert bq_recall < sq_recall, "BQ-alone recall must be clearly worse than SQ (much coarser quantization)"

# 4. the coarse-filter+rerank PIPELINE must recover recall far above BQ alone
#    -- this is the entire point of §8.4/§8.5's "coarse fast, then exact rerank"
assert recovery_recall > bq_recall, "BQ coarse-filter + exact rerank must beat BQ ranking alone"
assert recovery_recall > 0.9, "the recall-recovery pipeline must restore recall close to exact search"

# 5. sanity: SQ codes must be valid uint8, BQ codes must be boolean
assert sq_codes.min() >= 0 and sq_codes.max() <= 255
assert bq_codes.dtype == bool

print("\n✓ all self-checks passed — SQ (4x) keeps recall high; BQ (32x) needs coarse-filter+rerank to stay usable.")
