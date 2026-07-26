"""Dig-loop 16/50 — Recall vs latency: measure, don't assume "ANN is faster".

Grounded in book/06-ann-search-at-scale.md §6.4-6.5 (REAL measured numbers on
20,000 random vectors): brute force (numpy) = 2.9ms/query, 5/5 recall;
HNSW ef=200 = 12.6ms/query, 4-5/5 recall -- brute force WON on both speed AND
correctness at this scale. Lesson: graph traversal overhead (many small hops,
Python-level bookkeeping) can beat a single vectorized numpy matmul only once
N is large enough that O(N) truly dominates O(log N) -- and personal-vault
scale (10k-100k) often isn't there yet.
Runnable standalone (uses numpy, stdlib otherwise):
    python iter-16-hnsw-recall-latency.py

Builds on iter-15's single-layer NSW graph + bounded best-first search, but
this time the point is WALL-CLOCK TIME, not recall -- reproducing book/06's
actual "brute force still wins" result at this scale.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import heapq
import time
import numpy as np

rng = np.random.default_rng(9)
N, DIM, M = 20_000, 32, 6


def normalize_rows(X):
    return X / np.linalg.norm(X, axis=1, keepdims=True)


vectors = normalize_rows(rng.normal(size=(N, DIM)))


def brute_force_topk(qvec, k=5):
    scores = vectors @ qvec
    return np.argsort(-scores)[:k]


def greedy_search(qvec, graph, entry, ef, exclude=None):
    def sim(i):
        return float(vectors[i] @ qvec)

    visited = {entry}
    frontier = [(-sim(entry), entry)]
    heapq.heapify(frontier)
    results = [(sim(entry), entry)]

    while frontier:
        neg_s, node = heapq.heappop(frontier)
        s = -neg_s
        worst = results[-1][0] if len(results) >= ef else float("-inf")
        if s < worst and len(results) >= ef:
            break
        for nb in graph[node]:
            if nb in visited:
                continue
            visited.add(nb)
            nb_s = sim(nb)
            heapq.heappush(frontier, (-nb_s, nb))
            results.append((nb_s, nb))
            results.sort(key=lambda t: -t[0])
            if len(results) > ef:
                results = results[:ef]

    return [i for _, i in results if i != exclude]


def build_nsw_graph(n, M, ef_construction):
    graph = {0: []}
    for i in range(1, n):
        entry = 0 if i <= M else int(rng.integers(0, i))
        cands = greedy_search(vectors[i], graph, entry, ef_construction, exclude=i)
        neighbors = cands[:M] if cands else [entry]
        graph[i] = list(neighbors)
        for nb in neighbors:
            graph[nb].append(i)
    return graph


print(f"=== building single-layer NSW graph, N={N} (matches book/06's scale) ===")
t0 = time.perf_counter()
graph = build_nsw_graph(N, M=M, ef_construction=10)
build_time = time.perf_counter() - t0
print(f"build time = {build_time:.2f}s (one-time cost, not per-query)")

query_ids = rng.choice(N, size=25, replace=False)


def time_brute_force():
    best = float("inf")
    for qi in query_ids:
        t0 = time.perf_counter()
        brute_force_topk(vectors[qi], k=5)
        best = min(best, time.perf_counter() - t0)
    return best


def time_graph_search(ef):
    best = float("inf")
    for qi in query_ids:
        entry = int(rng.integers(0, N))
        t0 = time.perf_counter()
        greedy_search(vectors[qi], graph, entry, ef, exclude=int(qi))
        best = min(best, time.perf_counter() - t0)
    return best


t_brute = time_brute_force()
t_graph_ef50 = time_graph_search(ef=50)
t_graph_ef200 = time_graph_search(ef=200)

print(f"\n=== per-query latency, N={N} (this machine; book/06 measured 2.9ms vs 12.6ms) ===")
print(f"brute force (numpy)   -> {t_brute*1000:.3f} ms")
print(f"graph search ef=50    -> {t_graph_ef50*1000:.3f} ms")
print(f"graph search ef=200   -> {t_graph_ef200*1000:.3f} ms")
print(f"\nbook/06's real result: brute force 2.9ms beat HNSW ef=200's 12.6ms")
print("-> at THIS scale, a single vectorized numpy matmul beats many small")
print("   Python-level graph hops -- overhead only pays off past millions")

# --- asserts -----------------------------------------------------------------
# 1. brute force must actually return the exact correct top-5 (sanity)
exact = set(brute_force_topk(vectors[query_ids[0]], k=5).tolist())
assert query_ids[0] in exact, "querying with a corpus vector must find itself in its own top-5"

# 2. the graph search with a wide beam (ef=200) must be SLOWER than brute
#    force at this N -- reproducing book/06's actual "brute force wins" result
assert t_graph_ef200 > t_brute, \
    "graph-based approximate search (ef=200) must be slower than numpy brute force at N=20k (book/06's real finding)"

# 3. widening ef must cost more time (ef=200 slower than ef=50) -- the same
#    recall<->speed trade proven in iter-15, now measured in wall-clock
assert t_graph_ef200 >= t_graph_ef50, \
    "a wider beam (ef=200) must take at least as long as a narrower one (ef=50)"

# 4. brute force latency must be small in absolute terms (numpy SIMD) --
#    sanity bound generous enough to not be machine-flaky
assert t_brute < 0.05, "numpy brute force over 20k x 32-dim vectors must stay well under 50ms"

print("\n✓ all self-checks passed — measure before assuming ANN is faster; at this scale, brute force won.")
