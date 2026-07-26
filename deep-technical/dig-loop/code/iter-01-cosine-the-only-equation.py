"""Dig-loop 01/50 — Cosine similarity: the only equation.

Grounded in book/04-cosine-the-only-equation.md + deep-technical/01.
Runnable standalone (stdlib only):  python iter-01-cosine-the-only-equation.py

Teaches: cos(A,B) = (A·B)/(‖A‖‖B‖) — by hand, then the same 5-line function on a
higher-dim vector. Ends with asserts (book philosophy: วัด อย่าเดา / measure, don't guess).
"""
import math


def cosine(a, b):
    """The whole thing: multiply, add, divide. No AI in here."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


# --- 2D world: axes = [cat-ness, car-ness] ---------------------------------
cat    = [0.9, 0.1]
kitten = [0.85, 0.15]
car    = [0.1, 0.95]

c_cat_kit = cosine(cat, kitten)
c_cat_car = cosine(cat, car)

print("=== 2D by hand ===")
print(f"cos(cat, kitten) = {c_cat_kit:.4f}   (near 1 → almost same meaning)")
print(f"cos(cat, car)    = {c_cat_car:.4f}   (near 0 → nearly orthogonal)")

# --- properties every learner should verify --------------------------------
# 1. identical vectors → exactly 1
assert abs(cosine(cat, cat) - 1.0) < 1e-12, "self-similarity must be 1"
# 2. cosine is symmetric
assert abs(cosine(cat, car) - cosine(car, cat)) < 1e-12, "must be symmetric"
# 3. scale-invariant: doubling a vector's length changes nothing
cat_2x = [2 * x for x in cat]
assert abs(cosine(cat, kitten) - cosine(cat_2x, kitten)) < 1e-12, "must be scale-invariant"
# 4. bounded in [-1, 1]
for v in (c_cat_kit, c_cat_car):
    assert -1.0 <= v <= 1.0, "cosine must lie in [-1, 1]"
# 5. the hand-computed numbers from the slide
assert abs(c_cat_kit - 0.998) < 0.005, "kitten should be ~0.998"
assert abs(c_cat_car - 0.214) < 0.005, "car should be ~0.214"
# 6. meaning ordering: kitten is closer to cat than car is
assert c_cat_kit > c_cat_car, "kitten must rank above car"

# --- same function, higher dimension (nothing changes) ---------------------
# A tiny deterministic 8-dim pair standing in for real bge-m3 1024-dim vectors.
q  = [0.20, 0.11, 0.90, 0.05, 0.31, 0.14, 0.62, 0.08]
d1 = [0.19, 0.09, 0.88, 0.07, 0.29, 0.16, 0.60, 0.10]   # "same topic"
d2 = [0.80, 0.70, 0.05, 0.66, 0.10, 0.90, 0.04, 0.71]   # "different topic"
print("\n=== same function, 8D (proxy for 1024D) ===")
print(f"cos(q, d1) = {cosine(q, d1):.4f}   (same topic)")
print(f"cos(q, d2) = {cosine(q, d2):.4f}   (different topic)")
assert cosine(q, d1) > cosine(q, d2), "same-topic doc must win — the whole point of vector search"

print("\n✓ all self-checks passed — cosine needs only multiply, add, divide.")
