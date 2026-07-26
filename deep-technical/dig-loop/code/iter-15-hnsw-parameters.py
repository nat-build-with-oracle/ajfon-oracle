"""Dig-loop 15/50 — HNSW's real knobs: M, ef_construction, ef_search.

Grounded in deep-technical/17-hnsw-construction.md §17.1/§17.6 (M = neighbors
per node, efConstruction = build-time candidate pool, efSearch = query-time
candidate pool) and book/06-ann-search-at-scale.md §6.3-6.4 (REAL measured
result on 20,000 random vectors -- the hardest case, no cluster structure:
ef=50 (default-ish) got only 2/5 top-5 correct; ef=200 got 4-5/5, at ~3x the
latency). Lesson: ef is a genuine recall<->speed knob, not just theory.
Runnable standalone (uses numpy, stdlib otherwise):
    python iter-15-hnsw-parameters.py

Builds a simplified single-layer NSW-style graph (HNSW without the
hierarchy -- the hierarchy only helps ROUTE to the right neighborhood
faster; the ef-vs-recall trade-off already appears at a single layer) and
measures recall@5 + node-visits at low vs high ef, reproducing the book's
real qualitative result.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import heapq
import numpy as np

rng = np.random.default_rng(5)
N, DIM, M = 4000, 16, 4


def normalize_rows(X):
    return X / np.linalg.norm(X, axis=1, keepdims=True)


vectors = normalize_rows(rng.normal(size=(N, DIM)))


def brute_force_topk(qi, k):
    scores = vectors @ vectors[qi]
    scores[qi] = -2.0
    return set(np.argsort(-scores)[:k].tolist())


def greedy_candidates(qvec, graph, entry, ef, exclude=None):
    """Bounded best-first search -- the REAL shape of HNSW's search (Ch3
    §3.5): a candidate frontier ordered by distance, and a result set capped
    at `ef`. Stops once the frontier can no longer beat the worst result in
    the current top-ef -- so `ef` genuinely bounds how much of the graph
    gets explored, not just how many results come back."""
    def sim(i):
        return float(vectors[i] @ qvec)

    visited = {entry}
    frontier = [(-sim(entry), entry)]     # min-heap on negative similarity
    heapq.heapify(frontier)
    results = [(sim(entry), entry)]       # sorted desc, capped at ef
    visits = 0

    while frontier:
        neg_s, node = heapq.heappop(frontier)
        s = -neg_s
        worst_in_results = results[-1][0] if len(results) >= ef else float("-inf")
        if s < worst_in_results and len(results) >= ef:
            break   # can't possibly improve the result set anymore
        for nb in graph[node]:
            if nb in visited:
                continue
            visited.add(nb)
            visits += 1
            nb_s = sim(nb)
            heapq.heappush(frontier, (-nb_s, nb))
            results.append((nb_s, nb))
            results.sort(key=lambda t: -t[0])
            if len(results) > ef:
                results = results[:ef]

    ranked = [i for _, i in results if i != exclude]
    return ranked, visits


def build_nsw_graph(M, ef_construction):
    """NSW construction (deep-technical/17 §17.1, single layer): insert one
    node at a time, connect it to the best M candidates found by greedy
    search over the graph built SO FAR."""
    graph = {0: []}
    for i in range(1, N):
        if i <= M:
            entry = 0
        else:
            entry = rng.integers(0, i)
        cands, _ = greedy_candidates(vectors[i], graph, entry, ef_construction, exclude=i)
        neighbors = cands[:M] if cands else [entry]
        graph[i] = list(neighbors)
        for nb in neighbors:
            graph[nb].append(i)   # bidirectional edge
    return graph


print("=== building single-layer NSW graph ===")
graph = build_nsw_graph(M=M, ef_construction=8)
avg_degree = sum(len(v) for v in graph.values()) / N
print(f"N={N}, avg degree={avg_degree:.1f}")


def recall_at_ef(ef, num_queries=30, k=5):
    total_recall, total_visits = 0.0, 0
    query_ids = rng.choice(N, size=num_queries, replace=False)
    for qi in query_ids:
        true_top5 = brute_force_topk(int(qi), k)
        entry = int(rng.integers(0, N))
        found, visits = greedy_candidates(vectors[qi], graph, entry, ef, exclude=int(qi))
        approx_top5 = set(found[:k])
        total_recall += len(approx_top5 & true_top5) / k
        total_visits += visits
    return total_recall / num_queries, total_visits / num_queries


print("\n=== recall@5 vs ef_search (book/06 §6.4's real experiment shape) ===")
recall_low, visits_low = recall_at_ef(ef=5)
recall_mid, visits_mid = recall_at_ef(ef=50)
recall_high, visits_high = recall_at_ef(ef=200)

print(f"ef=5    recall@5={recall_low:.2f}   avg node-visits={visits_low:.1f}")
print(f"ef=50   recall@5={recall_mid:.2f}   avg node-visits={visits_mid:.1f}")
print(f"ef=200  recall@5={recall_high:.2f}   avg node-visits={visits_high:.1f}")
print("\nbook/06's REAL measured numbers (20k vectors, no structure):")
print("  ef~50 (default-ish): 2/5 top-5 correct (~0.40 recall)")
print("  ef=200:              4-5/5 correct (~0.80-1.0 recall), ~3x slower")

# --- asserts -----------------------------------------------------------------
# 1. higher ef must give higher (or equal) recall -- the whole point of the knob
assert recall_mid >= recall_low - 0.05, "ef=50 should not have meaningfully worse recall than ef=10"
assert recall_high >= recall_mid - 0.05, "ef=200 should not have meaningfully worse recall than ef=50"
assert recall_high > recall_low, "the widest beam (ef=200) must beat the narrowest (ef=10) on recall"

# 2. higher ef must visit more nodes -- recall isn't free, it costs search time
assert visits_high > visits_low, "ef=200 must visit more candidate nodes than ef=10 (that's the trade)"
assert visits_mid >= visits_low, "ef=50 must visit at least as many nodes as ef=10"

# 3. recall must always be a valid fraction
for r in (recall_low, recall_mid, recall_high):
    assert 0.0 <= r <= 1.0

# 4. low ef must show a REAL recall gap -- otherwise this demo wouldn't
#    reproduce the book's real "ef too low -> misses half" finding
assert recall_low < 0.6, "ef=5 (narrow beam) must show a REAL recall gap, matching book/06's finding"
assert recall_high > 0.8, "ef=200 (wide beam) must recover strong recall, matching book/06's finding"

print("\n✓ all self-checks passed — ef is a real recall<->speed knob: wider beam = better recall, more visits.")
