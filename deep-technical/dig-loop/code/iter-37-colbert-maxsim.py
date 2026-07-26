"""Dig-loop 37/50 — ColBERT MaxSim: per-token vectors, late interaction.

Grounded in deep-technical/07-bge-m3-multifunctionality.md §7.3 (instead of
pooling a whole doc into ONE vector, keep a vector PER TOKEN; score via
MaxSim: score(q,d) = Σᵢ max_j cos(qᵢ, dⱼ) -- each query token independently
finds its BEST-matching doc token, then sum. "Late interaction": encoded
separately like a bi-encoder (precomputable), but scored per-token like a
cross-encoder -- middle ground) and §7.6 (trade: more accurate, but m
vectors/doc storage + n×m MaxSim compute cost vs dense's 1 vector + O(1)).
Runnable standalone (stdlib only):  python iter-37-colbert-maxsim.py

Demonstrates dense pooling's real failure mode: a doc that genuinely covers
BOTH query topics at the token level, but whose single mean-pooled vector
gets diluted by unrelated filler tokens -- MaxSim isn't fooled because it
matches each query token independently and ignores the filler via max(),
never averaging it in.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


def mean_pool(vecs):
    dim = len(vecs[0])
    return [sum(v[d] for v in vecs) / len(vecs) for d in range(dim)]


def dense_score(query_tokens, doc_tokens):
    """bi-encoder dense: pool EVERYTHING into one vector each, then cosine."""
    return cosine(mean_pool(query_tokens), mean_pool(doc_tokens))


def maxsim_score(query_tokens, doc_tokens):
    """ColBERT §7.3: each query token independently finds its best doc token."""
    total, comparisons = 0.0, 0
    for q in query_tokens:
        best = max(cosine(q, d) for d in doc_tokens)
        total += best
        comparisons += len(doc_tokens)
    return total, comparisons


# --- 3 axes: [diabetes-topic, exercise-topic, filler-topic] ----------------
QUERY_TOKENS = [
    [1.0, 0.0, 0.0],   # "เบาหวาน"
    [0.0, 1.0, 0.0],   # "ออกกำลังกาย"
]

# doc A: genuinely covers BOTH topics at the token level, but is MOSTLY
# filler tokens (unrelated boilerplate) -- realistic for a long document
DOC_A_TOKENS = [
    [0.95, 0.05, 0.0],   # one token: about diabetes
    [0.05, 0.95, 0.0],   # one token: about exercise
    [0.0, 0.0, 1.0],     # filler
    [0.0, 0.0, 1.0],     # filler
    [0.0, 0.0, 1.0],     # filler
    [0.0, 0.0, 1.0],     # filler
]

# doc B: genuinely irrelevant -- no diabetes or exercise tokens at all
DOC_B_TOKENS = [[0.0, 0.0, 1.0]] * 6

dense_a = dense_score(QUERY_TOKENS, DOC_A_TOKENS)
dense_b = dense_score(QUERY_TOKENS, DOC_B_TOKENS)
maxsim_a, comparisons_a = maxsim_score(QUERY_TOKENS, DOC_A_TOKENS)
maxsim_b, comparisons_b = maxsim_score(QUERY_TOKENS, DOC_B_TOKENS)

print("=== dense (pooled) vs ColBERT MaxSim (per-token) ===")
print(f"doc A (genuinely covers BOTH topics, but mostly filler tokens):")
print(f"  dense score  = {dense_a:.4f}  (diluted by filler in the pooled average)")
print(f"  MaxSim score = {maxsim_a:.4f}  (finds the 2 real tokens, ignores filler)")
print(f"\ndoc B (genuinely irrelevant, all filler):")
print(f"  dense score  = {dense_b:.4f}")
print(f"  MaxSim score = {maxsim_b:.4f}")

print(f"\n=== cost (§7.6): storage + compute ===")
print(f"dense:   1 vector/doc, O(1) cosine per query")
print(f"ColBERT: {len(DOC_A_TOKENS)} vectors/doc, MaxSim did {comparisons_a} cosine comparisons "
      f"(n={len(QUERY_TOKENS)} query tokens x m={len(DOC_A_TOKENS)} doc tokens)")

# --- asserts -----------------------------------------------------------------
# 1. dense pooling must show REAL dilution: doc A's pooled cosine to the
#    query must be noticeably low despite genuinely covering both topics
assert dense_a < 0.5, \
    "dense pooling must be diluted by filler tokens even though doc A truly covers both topics"

# 2. MaxSim must recover strong relevance for doc A -- it independently
#    finds the 2 real matching tokens and ignores the filler via max()
assert maxsim_a > 1.5, \
    "MaxSim must find doc A's 2 genuinely relevant tokens, giving a high combined score"

# 3. MaxSim must score doc A dramatically higher than dense does -- the
#    entire point of NOT pooling into one lossy vector
assert maxsim_a / 2 > dense_a, \
    "MaxSim (normalized per query token) must clearly beat dense's diluted score for doc A"

# 4. both methods must correctly reject the genuinely irrelevant doc B
assert dense_b < 0.2, "dense must correctly score the irrelevant doc B low"
assert maxsim_a > maxsim_b, "MaxSim must rank the genuinely relevant doc A above the irrelevant doc B"

# 5. cost: MaxSim's comparisons must equal exactly n*m (query tokens x doc
#    tokens) -- the real O(n*m) cost the book warns about
n, m = len(QUERY_TOKENS), len(DOC_A_TOKENS)
assert comparisons_a == n * m, "MaxSim must perform exactly n*m cosine comparisons, matching its real cost model"

print("\n✓ all self-checks passed — dense pooling dilutes; per-token MaxSim doesn't, at the cost of n×m storage+compute.")
