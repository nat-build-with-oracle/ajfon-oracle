"""Dig-loop 06/50 — What do 1024 dimensions actually buy you?

Grounded in deep-technical/02-embeddings-and-contrastive-training.md (§2.0 pipeline,
bge-m3 = 1024-dim) and book/05-where-embeddings-come-from.md (KNOWN_DIMS: nomic 768,
bge-m3 1024, qwen3 1024-4096 — dimension count alone did NOT decide GAP quality there).
Runnable standalone (stdlib only):  python iter-06-what-1024-dims-mean.py

No single dimension "means" something human-readable (not dim 5 = "happiness").
What high dimensionality buys is CAPACITY: in high-dim space, random directions
are nearly orthogonal (concentration of measure) — so a model can pack many
independent, unrelated concepts into the same space without them interfering
with each other's cosine similarity. Low-dim space runs out of "room" fast.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math
import random


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def cosine(a, b):
    return dot(a, b) / (norm(a) * norm(b))


def random_unit_vector(dim, rng):
    v = [rng.gauss(0, 1) for _ in range(dim)]
    n = norm(v)
    return [x / n for x in v]


def mean_abs_cosine(dim, num_pairs, rng):
    """Average |cosine| between independently random unit vectors of `dim` dims."""
    total = 0.0
    for _ in range(num_pairs):
        a = random_unit_vector(dim, rng)
        b = random_unit_vector(dim, rng)
        total += abs(cosine(a, b))
    return total / num_pairs


rng = random.Random(42)   # fixed seed: deterministic, reproducible asserts

dims_to_test = [2, 8, 64, 256, 1024]
results = {d: mean_abs_cosine(d, 300, rng) for d in dims_to_test}

print("=== random unit vectors: average |cosine| between unrelated pairs ===")
for d in dims_to_test:
    bar = "#" * int(results[d] * 80)
    print(f"dim={d:>5}  avg|cos|={results[d]:.4f}  {bar}")

print("\n=== why this matters for embeddings ===")
print("2D:    two random directions are often NOT near-orthogonal -> concepts collide")
print("1024D: two random directions are almost always near-orthogonal -> room for")
print("       thousands of independent 'meaning axes' that don't interfere")

# --- asserts -----------------------------------------------------------------
# 1. average |cosine| between random vectors must SHRINK as dimension grows
#    (concentration of measure: variance of cos ~ 1/dim)
for a, b in zip(dims_to_test, dims_to_test[1:]):
    assert results[b] < results[a], \
        f"higher dimension ({b}) must give smaller average |cosine| than lower ({a})"

# 2. at dim=2, random vectors are NOT reliably near-orthogonal (plenty of overlap)
assert results[2] > 0.25, "in 2D, random unit vectors routinely have large |cosine| — little room"

# 3. at dim=1024 (bge-m3's real size), random vectors are almost always near-orthogonal
assert results[1024] < 0.10, "in 1024D, unrelated random directions must be nearly orthogonal"

# 4. the theoretical scaling: avg|cos| for random vectors shrinks roughly like 1/sqrt(dim)
#    check the two extremes are in the right ballpark (order of magnitude, not exact)
ratio = results[2] / results[1024]
expected_ratio = math.sqrt(1024 / 2)
assert ratio > expected_ratio * 0.3, \
    "the 2D-vs-1024D gap should roughly track the sqrt(dim) concentration-of-measure law"

# 5. no single dimension in a real-shaped vector determines similarity —
#    zeroing out any ONE dimension barely changes cosine for a 1024-dim pair
a = random_unit_vector(1024, rng)
b = random_unit_vector(1024, rng)
full_cos = cosine(a, b)
a_dim0_zeroed = a[:]
a_dim0_zeroed[0] = 0.0
partial_cos = cosine(a_dim0_zeroed, b)
assert abs(full_cos - partial_cos) < 0.05, \
    "dropping ONE of 1024 dims must barely move cosine — meaning is distributed, not localized"

print("\n✓ all self-checks passed — 1024 dims ≈ 1024 near-independent axes to spread meaning across.")
