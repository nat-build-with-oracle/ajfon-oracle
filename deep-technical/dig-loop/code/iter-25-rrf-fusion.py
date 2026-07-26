"""Dig-loop 25/50 — RRF: why rank fusion beats score fusion, and why k=60.

Grounded in deep-technical/11-rrf-ranking-theory.md §11.2 (scale-invariance
proof: any monotonic transform of raw scores leaves RANK unchanged, so RRF
is immune to score-scale mismatches that break naive score-fusion), §11.3
(k=60's numeric effect: rank1=1/61, rank2=1/62, rank10=1/70, rank100=1/160 --
and the consensus claim: a doc at rank2+rank3 across TWO rankers beats a doc
at rank1 in only ONE), and §11.5 (Kendall tau: low agreement between rankers
= fusion helps MOST).
Runnable standalone (stdlib only):  python iter-25-rrf-fusion.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""


def rrf_score(rank, k=60):
    return 1 / (k + rank)


def rrf_fuse(rank_lists, k=60):
    scores = {}
    for ranks in rank_lists:
        for pos, doc in enumerate(ranks, 1):
            scores[doc] = scores.get(doc, 0) + rrf_score(pos, k)
    return sorted(scores.items(), key=lambda x: -x[1])


# --- §11.3: the exact numeric table from the book ---------------------------
print("=== k=60: RRF contribution by rank ===")
for r in (1, 2, 10, 100):
    print(f"rank {r:>3} -> 1/({60}+{r}) = {rrf_score(r):.5f}")

# --- §11.2: scale-invariance proof -------------------------------------------
# two "raw score" lists for the same 4 docs, wildly different scales
raw_bm25 = {"a": 12.4, "b": 8.1, "c": 3.0, "d": 0.5}          # BM25: [0, inf)
raw_cosine = {"a": 0.91, "b": 0.88, "c": 0.40, "d": -0.2}     # cosine: [-1, 1]

def scores_to_rank(scores):
    return [doc for doc, _ in sorted(scores.items(), key=lambda x: -x[1])]

rank_bm25 = scores_to_rank(raw_bm25)
rank_cosine = scores_to_rank(raw_cosine)
fused_before = rrf_fuse([rank_bm25, rank_cosine])

# apply a wildly different MONOTONIC transform to each score list
raw_bm25_scaled = {d: s * 1000 for d, s in raw_bm25.items()}          # x1000
raw_cosine_scaled = {d: 2.71828 ** s for d, s in raw_cosine.items()}   # exp()

rank_bm25_scaled = scores_to_rank(raw_bm25_scaled)
rank_cosine_scaled = scores_to_rank(raw_cosine_scaled)
fused_after = rrf_fuse([rank_bm25_scaled, rank_cosine_scaled])

print(f"\n=== scale-invariance (§11.2): monotonic transform, same ranking ===")
print(f"RRF fusion BEFORE transform: {[d for d,_ in fused_before]}")
print(f"RRF fusion AFTER  transform: {[d for d,_ in fused_after]}")

# --- §11.3: consensus beats single-ranker rank-1 ----------------------------
consensus_score = rrf_score(2) + rrf_score(3)     # rank2 in list A + rank3 in list B
single_rank1_score = rrf_score(1)                 # rank1 in only ONE list
print(f"\n=== consensus vs single rank-1 (§11.3) ===")
print(f"doc at rank2+rank3 across 2 rankers = {consensus_score:.5f}")
print(f"doc at rank1 in only 1 ranker        = {single_rank1_score:.5f}")
print(f"consensus wins: {consensus_score > single_rank1_score}")


# --- §11.5: Kendall tau -- do two rankers agree? ----------------------------
def kendall_tau(rank_a, rank_b):
    items = rank_a
    pos_a = {d: i for i, d in enumerate(rank_a)}
    pos_b = {d: i for i, d in enumerate(rank_b)}
    concordant, discordant = 0, 0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a_order = pos_a[items[i]] - pos_a[items[j]]
            b_order = pos_b[items[i]] - pos_b[items[j]]
            if a_order * b_order > 0:
                concordant += 1
            elif a_order * b_order < 0:
                discordant += 1
    n = len(items)
    return (concordant - discordant) / (n * (n - 1) / 2)


agreeing_rankers = (["a", "b", "c", "d"], ["a", "b", "c", "d"])       # identical order
disagreeing_rankers = (["a", "b", "c", "d"], ["d", "c", "b", "a"])    # fully reversed
mixed_rankers = (["a", "b", "c", "d"], ["b", "a", "d", "c"])          # BM25 vs vector-like

tau_agree = kendall_tau(*agreeing_rankers)
tau_disagree = kendall_tau(*disagreeing_rankers)
tau_mixed = kendall_tau(*mixed_rankers)

print(f"\n=== Kendall tau: ranker agreement ===")
print(f"identical rankings   -> tau = {tau_agree:.2f}  (fusion adds little, they already agree)")
print(f"fully reversed       -> tau = {tau_disagree:.2f}")
print(f"partially different  -> tau = {tau_mixed:.2f}  (BM25 vs vector: different angles = fusion helps most)")

# --- asserts -----------------------------------------------------------------
# 1. the k=60 table must match the book's exact numbers
assert abs(rrf_score(1) - 1 / 61) < 1e-9 and abs(rrf_score(1) - 0.016393) < 1e-5
assert abs(rrf_score(2) - 1 / 62) < 1e-9
assert abs(rrf_score(10) - 1 / 70) < 1e-9
assert abs(rrf_score(100) - 1 / 160) < 1e-9

# 2. scale-invariance: RRF fusion must be IDENTICAL before and after applying
#    wildly different monotonic transforms to each raw score list
assert fused_before == fused_after, \
    "RRF must produce the EXACT same fused ranking regardless of monotonic score transforms"

# 3. consensus across 2 rankers must beat a single ranker's rank-1 --
#    the book's actual headline numeric claim (§11.3)
assert consensus_score > single_rank1_score, \
    "a doc at rank2+rank3 across two rankers must outscore a doc at rank1 in only one"

# 4. Kendall tau sanity: identical rankings -> tau=1, fully reversed -> tau=-1
assert abs(tau_agree - 1.0) < 1e-9, "identical rank orders must give Kendall tau = 1"
assert abs(tau_disagree - (-1.0)) < 1e-9, "fully reversed rank orders must give Kendall tau = -1"
assert -1.0 <= tau_mixed <= 1.0

# 5. the mixed (realistic BM25-vs-vector) case must show LOWER agreement
#    than identical rankings -- exactly where §11.5 says fusion helps most
assert tau_mixed < tau_agree, "a realistic partially-disagreeing ranker pair must have lower tau than identical rankers"

print("\n✓ all self-checks passed — RRF is scale-invariant, k=60 rewards consensus, low tau = fusion helps most.")
