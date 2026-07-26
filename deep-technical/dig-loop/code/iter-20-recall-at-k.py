"""Dig-loop 20/50 — Recall@k: "of everything relevant, how much did we get?"

Grounded in book/11-golden-set-eval.md (real golden-set result: MiniLM
recall@3=0.36, bge-m3 recall@3=0.93, on the SAME 7-query Thai test set) and
deep-technical/06-benchmark-methodology.md §6.1-6.2 (recall@k = relevant-in-
top-k / relevant-total; precision@k = relevant-in-top-k / k; recall<->precision
trade-off as k grows).
Runnable standalone (stdlib only):  python iter-20-recall-at-k.py

This builds its OWN small 7-query golden set (not the book's literal hidden
data, since only pass/fail markers were shown) tuned to land on the same
micro-averaged recall@3 story: a weak ranker landing near 0.36, a strong
ranker near 0.93 -- reproducing the SHAPE of book/11's real finding, with the
book's own numbers cited separately as validated ground truth.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""

# --- a 7-query golden set, 2 relevant docs per query (14 relevant total) ---
GOLDEN = {
    "q1": {"d1", "d4"},
    "q2": {"d2", "d9"},
    "q3": {"d3", "d5"},
    "q4": {"d6", "d10"},
    "q5": {"d7", "d1"},
    "q6": {"d8", "d2"},
    "q7": {"d9", "d3"},
}
TOTAL_RELEVANT = sum(len(v) for v in GOLDEN.values())

# --- weak model's actual top-3 rankings per query (hand-set to reproduce
#     the book's "mostly wrong" story -- finds 5 of 14 relevant instances) --
WEAK_TOP3 = {
    "q1": ["d2", "d4", "d6"],     # hits d4 (1/2)
    "q2": ["d5", "d6", "d7"],     # hits 0/2
    "q3": ["d3", "d1", "d2"],     # hits d3 (1/2)
    "q4": ["d1", "d2", "d3"],     # hits 0/2
    "q5": ["d1", "d2", "d3"],     # hits d1 (1/2)
    "q6": ["d2", "d4", "d5"],     # hits d2 (1/2)
    "q7": ["d9", "d1", "d2"],     # hits d9 (1/2)
}

# --- strong model's actual top-3 rankings -- finds 13 of 14 (misses one) --
STRONG_TOP3 = {
    "q1": ["d1", "d4", "d6"],     # hits both
    "q2": ["d2", "d9", "d3"],     # hits both
    "q3": ["d3", "d5", "d1"],     # hits both
    "q4": ["d6", "d10", "d1"],    # hits both
    "q5": ["d7", "d1", "d2"],     # hits both
    "q6": ["d8", "d2", "d1"],     # hits both
    "q7": ["d9", "d1", "d2"],     # hits d9 only (misses d3) -- 1 total miss
}


def recall_at_k(golden, results):
    """deep-technical/06 §6.1: (# relevant in top-k) / (# relevant total),
    micro-averaged across ALL queries (sum hits / sum relevant)."""
    total_hits = 0
    total_relevant = 0
    for q, relevant in golden.items():
        topk = set(results[q])
        total_hits += len(relevant & topk)
        total_relevant += len(relevant)
    return total_hits / total_relevant


def precision_at_k(golden, results, k):
    total_precision = 0.0
    for q, relevant in golden.items():
        topk = results[q][:k]
        hits = len(set(topk) & relevant)
        total_precision += hits / k
    return total_precision / len(golden)


weak_recall = recall_at_k(GOLDEN, WEAK_TOP3)
strong_recall = recall_at_k(GOLDEN, STRONG_TOP3)

print(f"=== our own 7-query golden set ({TOTAL_RELEVANT} relevant total) ===")
print(f"weak model   recall@3 = {weak_recall:.3f}")
print(f"strong model recall@3 = {strong_recall:.3f}")
print(f"\nbook/11's real measured numbers (different corpus, same formula):")
print(f"  MiniLM  recall@3 = 0.36, MRR = 0.37 (wrong on 4/7 queries)")
print(f"  bge-m3  recall@3 = 0.93, MRR = 1.00 (right on all 7)")

# --- recall vs precision trade-off as k grows (deep-technical/06 §6.2) -----
# widen the strong model's results to top-5 by padding with 2 more (irrelevant)
STRONG_TOP5 = {q: v + ["dX", "dY"] for q, v in STRONG_TOP3.items()}
recall_k3 = recall_at_k(GOLDEN, STRONG_TOP3)
recall_k5 = recall_at_k(GOLDEN, STRONG_TOP5)   # same hits, same recall (extra picks are irrelevant)
precision_k3 = precision_at_k(GOLDEN, STRONG_TOP3, 3)
precision_k5 = precision_at_k(GOLDEN, STRONG_TOP5, 5)

print(f"\n=== recall vs precision as k grows (same result set, k=3 -> k=5) ===")
print(f"recall@3={recall_k3:.3f}  precision@3={precision_k3:.3f}")
print(f"recall@5={recall_k5:.3f}  precision@5={precision_k5:.3f}  (more slots, same hits -> precision drops)")

# --- asserts -----------------------------------------------------------------
# 1. recall@k formula sanity: a hand-computed toy case
toy_golden = {"q": {"a", "b", "c", "d", "e"}}     # 5 relevant
toy_results = {"q": ["a", "x", "b", "y", "z"]}    # top-5, hits a and b only (2/5 within top-5, but recall counts ALL of top-k list regardless of k value passed)
assert recall_at_k(toy_golden, toy_results) == 2 / 5, "recall@k must equal (relevant found) / (relevant total)"

# 2. our weak/strong models must land close to book/11's real headline story
#    (a weak model far below 0.5, a strong model far above 0.9)
assert weak_recall < 0.45, "weak model must show a real recall gap, matching book/11's MiniLM finding"
assert strong_recall > 0.85, "strong model must show near-complete recall, matching book/11's bge-m3 finding"
assert strong_recall > weak_recall + 0.4, "the gap between weak and strong must be substantial (0.36 vs 0.93 in the book)"

# 3. recall must never exceed 1.0 or go negative
assert 0.0 <= weak_recall <= 1.0
assert 0.0 <= strong_recall <= 1.0

# 4. recall must be non-decreasing as k grows (adding more slots can only
#    find MORE relevant docs, never fewer) -- deep-technical/06 §6.2
assert recall_k5 >= recall_k3, "recall@k must never decrease as k grows"

# 5. precision must NOT increase when k grows without finding more hits --
#    the real recall<->precision trade-off (same numerator, bigger denominator)
assert precision_k5 <= precision_k3, "precision@k must drop (or stay same) as k grows with no new hits"

print("\n✓ all self-checks passed — recall@k = coverage of the relevant set; grows with k, trades off against precision.")
