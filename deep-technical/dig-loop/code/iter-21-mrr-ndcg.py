"""Dig-loop 21/50 — MRR (first-hit rank) and nDCG (graded, rank-discounted).

Grounded in deep-technical/06-benchmark-methodology.md §6.3 (MRR = mean of
1/rank of the first relevant doc per query) and §6.4 (nDCG: DCG@k =
sum (2^rel_i - 1) / log2(i+1), normalized by the best-possible ordering's
DCG -- the book's own worked example: rel=[3,2,0,1] -> DCG=9.324, IDCG=9.393,
nDCG=0.993, reproduced here exactly).
Runnable standalone (stdlib only):  python iter-21-mrr-ndcg.py

Also reuses iter-20's "weak vs strong model, 7-query golden set" framing to
show MRR tell the SAME story as recall@k did there (book/11's real MRR:
MiniLM=0.37, bge-m3=1.00 exactly).
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math


def mrr(first_hit_ranks):
    """deep-technical/06 §6.3 -- rank=None means never found -> RR=0."""
    rr_sum = sum((1 / r) if r is not None else 0.0 for r in first_hit_ranks)
    return rr_sum / len(first_hit_ranks)


def dcg(rels):
    """deep-technical/06 §6.4 -- position i (0-indexed) discounted by log2(i+2)."""
    return sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(rels))


def ndcg(rels):
    ideal = sorted(rels, reverse=True)
    idcg = dcg(ideal)
    return dcg(rels) / idcg if idcg > 0 else 0.0


# --- reproduce the book's own worked example EXACTLY (§6.4) ----------------
worked_rels = [3, 2, 0, 1]
worked_dcg = dcg(worked_rels)
worked_idcg = dcg(sorted(worked_rels, reverse=True))
worked_ndcg = ndcg(worked_rels)

print("=== deep-technical/06 §6.4's worked example ===")
print(f"rel = {worked_rels}")
print(f"DCG  = {worked_dcg:.3f}   (book: 9.324)")
print(f"IDCG = {worked_idcg:.3f}  (book: 9.393)")
print(f"nDCG = {worked_ndcg:.3f}  (book: 0.993)")

# --- MRR: same 7-query weak-vs-strong story as iter-20 (recall@k) ----------
# weak model: correct on queries 3,5,6 only (matches book/11's MiniLM ✗✗✓✗✓✓✗
# pattern -- 3 of 7 right), found at ranks 1, 1, 2 respectively
weak_ranks = [None, None, 1, None, 1, 2, None]
# strong model: correct on ALL 7 queries, always at rank 1 (book/11's bge-m3:
# MRR = 1.00 exactly, "เฉลยขึ้นอันดับ 1 เสมอ")
strong_ranks = [1, 1, 1, 1, 1, 1, 1]

weak_mrr = mrr(weak_ranks)
strong_mrr = mrr(strong_ranks)

print(f"\n=== MRR on our 7-query golden set (same framing as iter-20) ===")
print(f"weak model   MRR = {weak_mrr:.3f}")
print(f"strong model MRR = {strong_mrr:.3f}")
print(f"\nbook/11's real measured MRR: MiniLM=0.37, bge-m3=1.00 exactly")

# --- nDCG: rank position matters, not just presence -------------------------
# same 3 relevant docs, ranked in 2 different orders
order_good = [3, 2, 1, 0, 0]     # best doc first
order_bad = [0, 0, 1, 2, 3]      # best doc LAST (buried)
ndcg_good = ndcg(order_good)
ndcg_bad = ndcg(order_bad)

print(f"\n=== nDCG penalizes burying the best result ===")
print(f"best-first  {order_good} -> nDCG = {ndcg_good:.3f}")
print(f"best-last   {order_bad}  -> nDCG = {ndcg_bad:.3f}")

# --- asserts -----------------------------------------------------------------
# 1. our DCG/IDCG/nDCG must match the book's own worked example to 3 decimals
assert abs(worked_dcg - 9.324) < 0.001, "DCG must match deep-technical/06's worked example exactly"
assert abs(worked_idcg - 9.393) < 0.001, "IDCG must match deep-technical/06's worked example exactly"
assert abs(worked_ndcg - 0.993) < 0.001, "nDCG must match deep-technical/06's worked example exactly"

# 2. IDCG must always be >= DCG (the actual ordering can never beat the ideal one)
assert worked_idcg >= worked_dcg, "IDCG (best possible order) must be >= actual DCG"

# 3. our weak/strong MRR must reproduce book/11's real story: strong=1.0
#    exactly (found at rank 1 every time), weak far below
assert strong_mrr == 1.0, "a model that always ranks the relevant doc #1 must have MRR exactly 1.0"
assert weak_mrr < 0.5, "the weak model's MRR must show a real quality gap, matching book/11's MiniLM=0.37"

# 4. nDCG must be in [0, 1] always, and a perfect ordering must score exactly 1.0
assert 0.0 <= worked_ndcg <= 1.0
assert abs(ndcg(sorted(worked_rels, reverse=True)) - 1.0) < 1e-9, \
    "ranking already-ideal order must give nDCG = 1.0 exactly"

# 5. burying the best result must score LOWER than surfacing it first --
#    the whole point of the rank-discount log term (§6.4)
assert ndcg_good > ndcg_bad, "putting the highest-relevance doc first must score higher than burying it last"

print("\n✓ all self-checks passed — MRR rewards a fast first hit; nDCG rewards good docs ranked HIGH, not just present.")
