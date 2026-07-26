"""Dig-loop 03/50 — Proof: normalize → dot product = cosine.

Grounded in deep-technical/08-quantization-and-metric-proofs.md (§8.6).
Runnable standalone (stdlib only):  python iter-03-normalize-then-dot.py

Claim (Ch1 §1.6): if ‖a‖ = ‖b‖ = 1 then a·b = cos θ.
Proof: from a·b = ‖a‖‖b‖cosθ, substitute ‖a‖=‖b‖=1  ⟹  a·b = cosθ.
Why it matters: normalize once at index time → every query is a plain dot
product, no norm division per comparison. This is what LanceDB/FAISS do
internally. Ends with asserts (วัด อย่าเดา / measure, don't guess).
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


a = [3.0, 4.0]       # ‖a‖ = 5
b = [-2.0, 1.0]      # any non-unit vector, different length from a

a_hat = normalize(a)
b_hat = normalize(b)

print("=== before normalize ===")
print(f"a = {a}, ‖a‖ = {norm(a)}")
print(f"b = {b}, ‖b‖ = {norm(b):.4f}")
print("=== after normalize ===")
print(f"â = {[round(x, 4) for x in a_hat]}, ‖â‖ = {norm(a_hat):.10f}")
print(f"b̂ = {[round(x, 4) for x in b_hat]}, ‖b̂‖ = {norm(b_hat):.10f}")
print("=== the claim ===")
print(f"cos(a,b)   = {cosine(a, b):.6f}")
print(f"â · b̂      = {dot(a_hat, b_hat):.6f}   (should match)")

# --- â, b̂ really are unit vectors ------------------------------------------
assert abs(norm(a_hat) - 1.0) < 1e-12, "normalize must produce unit length"
assert abs(norm(b_hat) - 1.0) < 1e-12, "normalize must produce unit length"

# --- THE proof: dot(normalize(a), normalize(b)) == cosine(a, b) ------------
assert abs(dot(a_hat, b_hat) - cosine(a, b)) < 1e-12, \
    "normalized dot product must equal cosine similarity exactly"

# --- scale-invariance sanity: cosine ignores original length already -------
a_2x = [2 * x for x in a]
assert abs(cosine(a, b) - cosine(a_2x, b)) < 1e-12, \
    "cosine must already be scale-invariant before we even normalize"

# --- a second, higher-dim pair (proxy for real embeddings) -----------------
q  = [0.20, 0.11, 0.90, 0.05, 0.31, 0.14, 0.62, 0.08]
d1 = [0.19, 0.09, 0.88, 0.07, 0.29, 0.16, 0.60, 0.10]
q_hat, d1_hat = normalize(q), normalize(d1)
assert abs(dot(q_hat, d1_hat) - cosine(q, d1)) < 1e-9, \
    "identity must hold for arbitrary-dimension vectors, not just the 2D toy"

# --- why bother: dot on raw a,b is NOT cosine (norms not divided out) ------
assert abs(dot(a, b) - cosine(a, b)) > 1e-6, \
    "raw dot product (no normalize) must differ from cosine — that's the whole point"

print("\n✓ all self-checks passed — normalize once, then dot == cosine, exactly.")
