"""Dig-loop 39/50 — Cloudflare Workers AI: same model name, real drift risk.

Grounded in deep-technical/05-cloudflare-edge-embeddings.md §5.4 (same model
name "@cf/baai/bge-m3" running on Cloudflare vs local Ollama can give
NOT-QUITE-IDENTICAL vectors -- different quantization/pooling internals. If
the index was built with one and queries come from the other, "recall ตก
เงียบๆ" -- silently, with no error, just worse results) and the real fix:
drift benchmark -- measure cosine(v_local, v_cf) per doc AND search parity@k
BEFORE trusting a provider swap (~1 team-session validation, not "5 minutes").
Runnable standalone (uses numpy, stdlib otherwise):
    python iter-39-cloudflare-workers-ai.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import numpy as np

rng = np.random.default_rng(32)
N, DIM = 50, 32


def normalize_rows(X):
    return X / np.linalg.norm(X, axis=1, keepdims=True)


# --- "local" (Ollama bge-m3) embeddings for N docs --------------------------
local_vecs = normalize_rows(rng.normal(size=(N, DIM)))

# --- "CF" (Workers AI bge-m3) embeddings: SAME model name, but a small,
#     real perturbation from different quantization/pooling internals ------
cf_perturbation = rng.normal(scale=0.04, size=(N, DIM))   # small, not huge
cf_vecs = normalize_rows(local_vecs + cf_perturbation)


def drift(local_vec, cf_vec):
    return 1 - float(local_vec @ cf_vec)


drifts = [drift(local_vecs[i], cf_vecs[i]) for i in range(N)]
mean_drift = sum(drifts) / N

print(f"=== §5.4 drift benchmark step 1: per-doc embedding drift ===")
print(f"mean drift over {N} docs = {mean_drift:.4f}  (near 0 = vectors look almost identical)")
print(f"max drift = {max(drifts):.4f}, min drift = {min(drifts):.4f}")

# --- search parity: does query-time embedder choice change the answer? ----
query_idx = 7
true_query_vec = local_vecs[query_idx] + rng.normal(scale=0.016, size=DIM)
true_query_vec = true_query_vec / np.linalg.norm(true_query_vec)


def topk(index_vecs, query_vec, k=5):
    scores = index_vecs @ query_vec
    return set(np.argsort(-scores)[:k].tolist())


# scenario A: consistent -- index built AND queried with the SAME embedder
consistent_local_top5 = topk(local_vecs, true_query_vec, k=5)

# scenario B: consistent -- index built AND queried with CF throughout
cf_query_vec = true_query_vec + rng.normal(scale=0.04, size=DIM)
cf_query_vec = cf_query_vec / np.linalg.norm(cf_query_vec)
consistent_cf_top5 = topk(cf_vecs, cf_query_vec, k=5)

# scenario C: THE DANGER -- index was built with local, but query embeds
# through CF now (a real migration-in-progress state) -- MISMATCHED
mismatched_top5 = topk(local_vecs, cf_query_vec, k=5)

parity_consistent = len(consistent_local_top5 & consistent_cf_top5) / 5
parity_mismatched = len(consistent_local_top5 & mismatched_top5) / 5

print(f"\n=== §5.4 drift benchmark step 2: search parity@5 ===")
print(f"consistent (local index + local query) vs (CF index + CF query): parity = {parity_consistent:.2f}")
print(f"MISMATCHED (local index + CF-embedded query):                    parity = {parity_mismatched:.2f}  <- silent recall drop")

print(f"\nlesson (§5.4): '5 นาทีใส่ token' != พร้อมใช้ -- ต้อง validate drift+parity ก่อนสลับจริง")

# --- asserts -----------------------------------------------------------------
# 1. per-doc drift must be small -- same model name really does give
#    NEAR-similar (not wildly different) vectors, matching the real claim
assert mean_drift < 0.05, "mean drift between same-named local/CF embeddings must be small (models are genuinely similar)"
assert mean_drift > 0.0, "drift must be nonzero -- the two providers are NOT byte-identical"

# 2. when index and query embedder are CONSISTENT (both local, or both CF),
#    parity must be reasonably high -- no mismatch, no problem
assert parity_consistent >= 0.6, \
    "using a consistent embedder end-to-end (even if it's a different one throughout) should preserve reasonable parity"

# 3. the MISMATCHED scenario (index built with local, query embedded via CF)
#    must show REAL degradation vs the fully-consistent baseline -- this is
#    the "recall ตกเงียบๆ" danger the book warns about
assert parity_mismatched <= parity_consistent, \
    "mixing index-time and query-time embedders must not improve on using one consistently"

# 4. the mismatch must be a genuinely measurable problem, not negligible --
#    verify at least SOME of the top-5 changed due to the embedder mismatch
assert parity_mismatched < 1.0, \
    "the embedder mismatch must cause at least some real difference in the top-5 results"

# 5. sanity: all vectors involved must be valid unit vectors (normalization
#    step didn't break anything)
assert abs(np.linalg.norm(local_vecs[0]) - 1.0) < 1e-9
assert abs(np.linalg.norm(cf_vecs[0]) - 1.0) < 1e-9

print("\n✓ all self-checks passed — same model name ≠ identical vectors; mismatched index/query embedders silently cost recall.")
