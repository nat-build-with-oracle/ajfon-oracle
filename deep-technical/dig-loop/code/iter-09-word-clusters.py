"""Dig-loop 09/50 — Why "nearest available" isn't the same as "actually related".

Grounded in data/vector-teaching-log.md iter 107 (vector-viz v3, feedback from
อาจารย์: "ทำไมเงินเฟ้อ (inflation) ใกล้ AI/แมว?") — the real fix was a 3-zone
reading scale (>=0.70 green = really close, 0.55-0.70 yellow = loosely related,
<0.55 red = barely related) plus a "lonely word" warning: a word whose BEST
match is still red means nothing in the set is truly related to it — the
top-1 neighbor is just the "least-far" option, not a real match.
Runnable standalone (stdlib only):  python iter-09-word-clusters.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math
import random

rng = random.Random(11)
DIM = 24


def random_unit(dim):
    v = [rng.gauss(0, 1) for _ in range(dim)]
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def scale(a, s):
    return [x * s for x in a]


def normalize(a):
    n = math.sqrt(sum(x * x for x in a))
    return [x / n for x in a]


def cosine(a, b):
    return dot(a, b)  # both already unit-normalized below


def zone(score):
    if score >= 0.70:
        return "green (จริง)"
    if score >= 0.55:
        return "yellow (เกี่ยวอ่อน)"
    return "red (แทบไม่เกี่ยว)"


# --- 4 real clusters (each has several members -> real neighbors exist) ----
GROUPS = {
    "สัตว์เลี้ยง": ["แมว", "ลูกแมว", "หมา", "ลูกหมา"],
    "อาหาร": ["ต้มยำกุ้ง", "ผัดไทย", "ส้มตำ"],
    "เทคโนโลยี": ["ปัญญาประดิษฐ์", "vector search", "embedding"],
}
# --- 1 isolated word: only member of its "cluster" -> no real neighbor ------
LONELY_WORD = "เงินเฟ้อ"   # inflation — the real feedback case

group_centers = {g: random_unit(DIM) for g in GROUPS}
lonely_center = random_unit(DIM)   # its own direction, unrelated to the others

labels, vecs, group_of = [], [], []
for g, words in GROUPS.items():
    for w in words:
        noise = [rng.gauss(0, 0.10) for _ in range(DIM)]
        v = normalize(add(group_centers[g], noise))
        labels.append(w)
        vecs.append(v)
        group_of.append(g)

lonely_noise = [rng.gauss(0, 0.10) for _ in range(DIM)]
lonely_vec = normalize(add(lonely_center, lonely_noise))
labels.append(LONELY_WORD)
vecs.append(lonely_vec)
group_of.append("การเงิน (โดดเดี่ยว)")


def top_match(i):
    best_j, best_s = None, -2.0
    for j in range(len(labels)):
        if j == i:
            continue
        s = cosine(vecs[i], vecs[j])
        if s > best_s:
            best_j, best_s = j, s
    return best_j, best_s


print("=== nearest neighbor + 3-zone reading scale ===")
for i, w in enumerate(labels):
    j, s = top_match(i)
    print(f"{w:>16} -> nearest: {labels[j]:<16} cos={s:.3f}  [{zone(s)}]")

lonely_idx = labels.index(LONELY_WORD)
_, lonely_best = top_match(lonely_idx)

cat_idx = labels.index("แมว")
_, cat_best = top_match(cat_idx)

print(f"\n'{LONELY_WORD}' best match score = {lonely_best:.3f}  -> {zone(lonely_best)}")
print("even though SOMETHING is always ranked #1, a red-zone top-1 means:")
print("  'nearest available in this set' != 'actually related' -- warn, don't trust blindly")

# --- asserts -----------------------------------------------------------------
# 1. a real cluster member (cat) must have a genuinely close neighbor (green zone)
assert cat_best >= 0.70, "a word with real siblings in its cluster must land in the green zone"

# 2. the lonely word's BEST match must land in the red zone (< 0.55) —
#    proving it has no real neighbor in this set at all
assert lonely_best < 0.55, \
    "an isolated word with no true cluster-mate must have its best score in the red zone"

# 3. top-1 always returns SOME answer -- this is exactly the trap: ranking
#    alone can't tell you "no real match exists", only the threshold zone can
_, always_returns = top_match(lonely_idx)
assert always_returns is not None, "nearest-neighbor search always returns a top-1, even for junk"

# 4. the gap between a real cluster match and the lonely word's best match
#    must be substantial -- the whole point of the 3-zone scale
assert cat_best - lonely_best > 0.20, \
    "a real match must clearly outscore a lonely word's best-available match"

# 5. every score must stay in valid cosine range
for i in range(len(labels)):
    _, s = top_match(i)
    assert -1.0 <= s <= 1.0

print("\n✓ all self-checks passed — read the ZONE, not just the rank: red top-1 means no real neighbor exists.")
