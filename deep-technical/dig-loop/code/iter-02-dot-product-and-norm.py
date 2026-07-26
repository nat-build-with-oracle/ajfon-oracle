"""Dig-loop 02/50 — Dot product & norm: the algebra↔geometry bridge.

Grounded in deep-technical/01-mathematics-of-vector-search.md (§1.2–1.4).
Runnable standalone (stdlib only):  python iter-02-dot-product-and-norm.py

The one theorem everything else stands on:   a · b = ‖a‖ ‖b‖ cos θ
So cosine is just the dot product with the two lengths divided out.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def angle_deg(a, b):
    cos_t = dot(a, b) / (norm(a) * norm(b))
    cos_t = max(-1.0, min(1.0, cos_t))          # clamp float noise before acos
    return math.degrees(math.acos(cos_t))


a = [1, 2, 3]
b = [4, 5, 6]

print("=== dot product ===")
print(f"a·b = 1·4 + 2·5 + 3·6 = {dot(a, b)}")
print("=== norms ===")
print(f"‖a‖ = √14 ≈ {norm(a):.3f}")
print(f"‖b‖ = √77 ≈ {norm(b):.3f}")
print("=== recover the angle ===")
print(f"cos θ = {dot(a, b) / (norm(a) * norm(b)):.4f}  →  θ ≈ {angle_deg(a, b):.1f}°")

# --- the numbers from the slide -------------------------------------------
assert dot(a, b) == 32, "1·4+2·5+3·6 must be 32"
assert abs(norm(a) - math.sqrt(14)) < 1e-12
assert abs(norm(b) - math.sqrt(77)) < 1e-12
assert abs(norm(a) - 3.742) < 0.001
assert abs(norm(b) - 8.775) < 0.001

# --- THE bridge: a·b == ‖a‖‖b‖cosθ (verify both sides agree) ---------------
lhs = dot(a, b)
rhs = norm(a) * norm(b) * math.cos(math.radians(angle_deg(a, b)))
assert abs(lhs - rhs) < 1e-9, "algebra side must equal geometry side"

# --- geometric edge cases the theorem predicts -----------------------------
same = [1, 0, 0]
orth = [0, 1, 0]
opp  = [-1, 0, 0]
assert abs(angle_deg(same, same) - 0.0)   < 1e-6, "same direction → θ = 0°"
assert abs(angle_deg(same, orth) - 90.0)  < 1e-6, "orthogonal → θ = 90° → dot 0"
assert dot(same, orth) == 0,                        "orthogonal vectors have dot 0"
assert abs(angle_deg(same, opp) - 180.0)  < 1e-6, "opposite → θ = 180°"

# --- why we divide the norms away: dot alone is fooled by length -----------
short = [1, 0]
long  = [10, 0]          # same DIRECTION as short, just 10x longer
assert dot(same[:2], long) > dot(same[:2], short), "raw dot rewards mere length..."
assert abs(angle_deg(same[:2], long) - angle_deg(same[:2], short)) < 1e-9, \
    "...but the ANGLE (and thus cosine) ignores length — that's the point"

print("\n✓ all self-checks passed — a·b = ‖a‖‖b‖cosθ holds; cosine = dot with lengths removed.")
