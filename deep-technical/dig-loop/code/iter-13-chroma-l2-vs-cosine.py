"""Dig-loop 13/50 — Chroma's default is L2, not cosine (the real bug from book/09).

Grounded in book/09-rag-cite.md §9.3 (real trap hit while writing the RAG
notebook: with a custom embedding_function and no explicit hnsw:space, Chroma
scores as "1 - L2_distance", not "1 - cosine_distance". A real cosine=0.57
match displayed as ~0.13 -- the WHOLE SCALE was wrong).
Runnable standalone (stdlib only):  python iter-13-chroma-l2-vs-cosine.py

This connects directly to iter-04's proven identity for unit vectors:
    ‖a-b‖² = 2 - 2cosθ
so Chroma's buggy "1 - L2²" score simplifies to:
    1 - (2 - 2cosθ) = 2cosθ - 1
a strictly increasing (monotonic) function of cosine -- meaning RANKING order
survives the bug, but the raw SCORE SCALE is wrong. That's exactly why book/09
§9.2's abstain-threshold (0.45) can silently reject a genuinely good match.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def normalize(a):
    n = norm(a)
    return [x / n for x in a]


def cosine(a, b):
    return dot(a, b) / (norm(a) * norm(b))


def sq_euclidean(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def chroma_score_wrong(a, b):
    """hnsw:space left at DEFAULT (L2) -- Chroma reports 1 - distance,
    but distance here is squared L2, not (1 - cosine)."""
    return 1 - sq_euclidean(a, b)


def chroma_score_correct(a, b):
    """hnsw:space explicitly set to 'cosine' -- reports real cosine similarity."""
    return cosine(a, b)


# --- a real match pair, tuned so cosine ~ 0.6 (book/09's real example: 0.57) -
a = normalize([0.9, 0.3, 0.1, 0.2])
b = normalize([0.3, 0.9, 0.2, 0.1])
real_cos = cosine(a, b)

wrong_score = chroma_score_wrong(a, b)
correct_score = chroma_score_correct(a, b)
predicted_wrong = 2 * real_cos - 1   # from the iter-04 identity, derived not measured

print(f"=== one real match pair ===")
print(f"true cosine similarity        = {real_cos:.4f}")
print(f"Chroma score (space=L2, BUG)  = {wrong_score:.4f}")
print(f"Chroma score (space=cosine)   = {correct_score:.4f}")
print(f"predicted via 2cos-1 identity = {predicted_wrong:.4f}  (should match the BUG score)")

# --- book/09 §9.2's real abstain threshold ----------------------------------
THRESHOLD = 0.45
print(f"\n=== abstain threshold = {THRESHOLD} (book/09 §9.2) ===")
print(f"correct score {correct_score:.4f} >= {THRESHOLD}? {correct_score >= THRESHOLD}  (should pass -- real match)")
print(f"wrong score   {wrong_score:.4f} >= {THRESHOLD}? {wrong_score >= THRESHOLD}  (silently rejected!)")

# --- does the L2 bug at least preserve RANKING order? -----------------------
candidates = [
    normalize([0.9, 0.3, 0.1, 0.2]),   # the "b" above, close match
    normalize([0.85, 0.35, 0.05, 0.25]),  # slightly closer
    normalize([0.1, 0.1, 0.9, 0.8]),   # unrelated
]
query = normalize([0.9, 0.3, 0.1, 0.2])
rank_by_cosine = sorted(candidates, key=lambda c: -cosine(query, c))
rank_by_wrong = sorted(candidates, key=lambda c: -chroma_score_wrong(query, c))

print(f"\nranking by TRUE cosine == ranking by BUGGY L2 score? "
      f"{rank_by_cosine == rank_by_wrong}  (monotonic transform preserves order)")

# --- asserts -----------------------------------------------------------------
# 1. the buggy L2-based score must equal 2*cosine - 1 EXACTLY for unit vectors
#    (direct consequence of iter-04's ‖a-b‖²=2-2cosθ identity)
assert abs(wrong_score - predicted_wrong) < 1e-9, \
    "Chroma's default L2 score must equal 2*cosine-1 for unit-normalized vectors"

# 2. the correct (cosine-space) score must just be the real cosine similarity
assert abs(correct_score - real_cos) < 1e-12

# 3. the scale is genuinely different -- wrong score must NOT equal cosine
assert abs(wrong_score - correct_score) > 0.1, \
    "the L2-default score must differ substantially in scale from the true cosine score"

# 4. THE actual production bug: a real match (cosine >= threshold) must get
#    silently rejected under the buggy default, because 2*cos-1 < cos for any
#    cos < 1 -- the L2 default score is ALWAYS <= the cosine score
assert real_cos >= THRESHOLD, "this example must be a genuine match under the correct metric"
assert wrong_score < THRESHOLD, "the same match must fall BELOW threshold under the buggy L2-default score"

# 5. ranking order is preserved (2x-1 is monotonic increasing) even though
#    the absolute scores are wrong -- explains why the bug went unnoticed
#    until someone checked an ABSOLUTE threshold, not just top-k order
assert rank_by_cosine == rank_by_wrong, \
    "monotonic transform must preserve relative ranking despite the wrong absolute scale"

print("\n✓ all self-checks passed — always set hnsw:space='cosine' explicitly; never trust the distance-metric default.")
