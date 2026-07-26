"""Dig-loop 14/50 — HNSW intuition: a skip list, generalized to a graph.

Grounded in deep-technical/17-hnsw-construction.md §17.0 ("HNSW = skip list
บนกราฟ") and §17.2 (layer assignment: l = floor(-ln(uniform(0,1)) * m_L),
m_L = 1/ln(M), giving P(node at layer >= k) ~ M^-k -- an exponential falloff
that is the actual root of O(log n) search).
Runnable standalone (stdlib only):  python iter-14-hnsw-intuition.py

HNSW's real multi-dim navigable-small-world graph is complex to build from
scratch here, but its EXACT layer-assignment math and search-hop-count
behavior is identical to a classic 1D skip list (Pugh 1990) -- the thing
Ch17.0 says HNSW literally generalizes. This demo builds a real skip list
with HNSW's own layer formula, and measures: (1) how few nodes a search
actually visits vs brute force, (2) that visit count grows like log(N) not N,
(3) that the layer population follows the predicted exponential decay.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math
import random


def assign_layer(M, rng):
    """deep-technical/17 §17.2 — the ACTUAL HNSW formula."""
    m_L = 1 / math.log(M)
    return math.floor(-math.log(rng.random()) * m_L)


class SkipNode:
    def __init__(self, key, level):
        self.key = key
        self.forward = [None] * (level + 1)


class SkipList:
    """A real, working skip list using HNSW's layer-assignment formula."""

    def __init__(self, M, rng):
        self.M = M
        self.rng = rng
        self.max_level = 0
        self.head = SkipNode(None, 0)   # sentinel, key=None sorts first
        self.layer_counts = {0: 0}

    def insert(self, key):
        level = assign_layer(self.M, self.rng)
        if level > self.max_level:
            self.head.forward.extend([None] * (level - self.max_level))
            self.max_level = level
        update = [self.head] * (self.max_level + 1)
        cur = self.head
        for i in range(self.max_level, -1, -1):
            while cur.forward[i] is not None and cur.forward[i].key < key:
                cur = cur.forward[i]
            update[i] = cur
        node = SkipNode(key, level)
        for i in range(level + 1):
            node.forward[i] = update[i].forward[i]
            update[i].forward[i] = node
        for lvl in range(level + 1):
            self.layer_counts[lvl] = self.layer_counts.get(lvl, 0) + 1
        return level

    def search(self, key):
        """Greedy descent: exactly the shape of HNSW search (Ch3 §3.5)."""
        cur = self.head
        visits = 0
        for i in range(self.max_level, -1, -1):
            while cur.forward[i] is not None and cur.forward[i].key < key:
                cur = cur.forward[i]
                visits += 1
        found = cur.forward[0] is not None and cur.forward[0].key == key
        if found:
            visits += 1
        return found, visits


def build_and_measure(n, M, seed):
    rng = random.Random(seed)
    sl = SkipList(M, rng)
    keys = list(range(n))
    insert_order = keys[:]
    rng.shuffle(insert_order)   # insertion order shouldn't matter
    for k in insert_order:
        sl.insert(k)

    sample_keys = rng.sample(keys, min(200, n))
    total_visits = 0
    for k in sample_keys:
        found, visits = sl.search(k)
        assert found, f"key {k} must be findable -- correctness first"
        total_visits += visits
    avg_visits = total_visits / len(sample_keys)
    return sl, avg_visits


M = 4
print(f"=== skip list built with HNSW's own layer formula (M={M}) ===")
results = {}
for n in [500, 2_000, 8_000, 32_000]:
    sl, avg_visits = build_and_measure(n, M, seed=n)
    results[n] = avg_visits
    print(f"N={n:>6}  avg hops to find a key = {avg_visits:6.2f}   "
          f"(brute force would need up to N={n})")

print(f"\n=== layer population (should shrink ~1/{M} per layer, §17.2) ===")
sl_big, _ = build_and_measure(20_000, M, seed=99)
for lvl in sorted(sl_big.layer_counts)[:6]:
    print(f"layer {lvl}: {sl_big.layer_counts[lvl]:>6} nodes")

# --- asserts -----------------------------------------------------------------
# 1. average hops must be WAY below N -- the whole point of the layered structure
for n, avg in results.items():
    assert avg < n * 0.2, f"avg hops ({avg}) must be far below brute-force N={n}"

# 2. growth must look like O(log N), not O(N): a 64x increase in N (500->32000)
#    must NOT produce anywhere near a 64x increase in hops
ratio_n = 32_000 / 500
ratio_hops = results[32_000] / results[500]
assert ratio_hops < ratio_n / 4, \
    "hop-count growth must be far slower than linear as N grows 64x"

# 3. layer population must shrink roughly geometrically (~1/M per layer) --
#    check layer 2 has noticeably fewer nodes than layer 0 (not a flat count)
assert sl_big.layer_counts[0] > sl_big.layer_counts.get(2, 0) * 3, \
    "layer 2 must have far fewer nodes than layer 0 (exponential falloff, §17.2)"

# 4. number of levels actually built must roughly track log_M(n), not grow linearly
#    (more nodes -> a few more levels, not thousands more)
sl_small, _ = build_and_measure(500, M, seed=1)
assert sl_big.max_level - sl_small.max_level < 10, \
    "level count must grow logarithmically with N, not explode with more data"

# 5. sanity: every found search must actually return the correct key (already
#    checked inside build_and_measure via assert found, re-stated here for N=8000)
sl8k, _ = build_and_measure(8_000, M, seed=8000)
found, _ = sl8k.search(4321)
assert found, "an existing key must always be found"
found_missing, _ = sl8k.search(999_999)
assert not found_missing, "a key that was never inserted must correctly report not-found"

print("\n✓ all self-checks passed — layered/exponential structure turns O(N) search into O(log N) hops.")
