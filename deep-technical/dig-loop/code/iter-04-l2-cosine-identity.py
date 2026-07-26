"""Dig-loop 04/50 — Proof: ‖a−b‖² = 2 − 2cosθ on the unit sphere.

Grounded in deep-technical/08-quantization-and-metric-proofs.md (§8.7).
Runnable standalone (stdlib only):  python iter-04-l2-cosine-identity.py

Claim (Ch1 §1.6): for unit vectors (‖a‖=‖b‖=1), squared Euclidean distance
is a decreasing function of cosine similarity:
    ‖a−b‖² = ‖a‖² − 2(a·b) + ‖b‖² = 1 − 2cosθ + 1 = 2 − 2cosθ
So on the unit sphere, ranking by cosine and ranking by Euclidean (L2)
give the IDENTICAL order — an ANN index that only supports L2 can stand in
for cosine, as long as vectors are normalized first.
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


a = normalize([3.0, 4.0])
b = normalize([-1.0, 2.0])

cos_theta = cosine(a, b)
lhs = sq_euclidean(a, b)
rhs = 2 - 2 * cos_theta

print("=== unit vectors ===")
print(f"â = {[round(x, 4) for x in a]}  (‖â‖={norm(a):.10f})")
print(f"b̂ = {[round(x, 4) for x in b]}  (‖b̂‖={norm(b):.10f})")
print("=== the identity ===")
print(f"cos θ           = {cos_theta:.6f}")
print(f"‖a−b‖²  (LHS)   = {lhs:.6f}")
print(f"2 − 2cosθ (RHS) = {rhs:.6f}")

# --- both sides really are unit vectors ------------------------------------
assert abs(norm(a) - 1.0) < 1e-12
assert abs(norm(b) - 1.0) < 1e-12

# --- THE identity: ‖a−b‖² == 2 − 2cosθ --------------------------------------
assert abs(lhs - rhs) < 1e-12, "squared L2 distance must equal 2 - 2cos(theta) exactly"

# --- monotonic: higher cosine → smaller L2 distance (same ordering) --------
pairs = [
    normalize([1.0, 0.0]),
    normalize([0.9, 0.1]),
    normalize([0.0, 1.0]),
    normalize([-1.0, 0.0]),
]
ref = normalize([1.0, 0.0])
by_cosine = sorted(pairs, key=lambda v: -cosine(ref, v))
by_l2     = sorted(pairs, key=lambda v: sq_euclidean(ref, v))
assert by_cosine == by_l2, "ranking by cosine and by L2 must be IDENTICAL on the unit sphere"

# --- edge cases the identity predicts ---------------------------------------
same = normalize([1.0, 1.0])
assert abs(sq_euclidean(same, same) - 0.0) < 1e-12, "identical unit vectors -> L2=0, cos=1 -> 2-2*1=0"
opp = normalize([-1.0, -1.0])
assert abs(sq_euclidean(same, opp) - 4.0) < 1e-9, "opposite unit vectors -> cos=-1 -> 2-2*(-1)=4"
orth_a, orth_b = normalize([1.0, 0.0]), normalize([0.0, 1.0])
assert abs(sq_euclidean(orth_a, orth_b) - 2.0) < 1e-12, "orthogonal unit vectors -> cos=0 -> 2-2*0=2"

# --- higher dimension sanity (proxy for real embeddings) --------------------
q  = normalize([0.20, 0.11, 0.90, 0.05, 0.31, 0.14, 0.62, 0.08])
d1 = normalize([0.19, 0.09, 0.88, 0.07, 0.29, 0.16, 0.60, 0.10])
assert abs(sq_euclidean(q, d1) - (2 - 2 * cosine(q, d1))) < 1e-9, \
    "identity must hold for arbitrary-dimension unit vectors, not just the 2D toy"

print("\n✓ all self-checks passed — on the unit sphere, L2 ranking == cosine ranking.")
