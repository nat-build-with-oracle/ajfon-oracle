"""Dig-loop 26/50 — Triple-RRF can make things WORSE than the best single engine.

Grounded in book/17-multi-engine-benchmark.md §X.3 (real measured result:
bge-m3 alone Recall@5=1.000/nDCG@10=0.972; fusing bge-m3+nomic+qwen3 via RRF
drops to Recall@5=0.929/nDCG@10=0.791 -- WORSE). §X.3/X.4's lesson: RRF
weights every ranker EQUALLY, so two weaker, CORRELATED rankers (both weak
on Thai, so they fail the SAME queries the SAME way) can outvote one
excellent ranker via consensus -- the very mechanism that made fusion WIN in
iter-25 (consensus beats single rank-1) backfires when the "consensus" comes
from correlated mediocrity, not independent strength.
Runnable standalone (stdlib only):  python iter-26-triple-rrf-hurts.py

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


# --- 7 queries: correct doc is always "A"; on 2 queries, two WEAKER,
#     CORRELATED rankers (nomic/qwen3-like) both mistakenly favor "B" --
#     they fail the SAME query the SAME way, because they share the same
#     Thai-embedding weakness (book/05's anisotropy finding, iter-07) --------
QUERIES = {
    "q1": {"strong": ["A", "B", "C"], "weak1": ["A", "B", "C"], "weak2": ["A", "B", "C"]},
    "q2": {"strong": ["A", "B", "C"], "weak1": ["A", "B", "C"], "weak2": ["A", "B", "C"]},
    "q3": {"strong": ["A", "B", "C"], "weak1": ["A", "B", "C"], "weak2": ["A", "B", "C"]},
    "q4": {"strong": ["A", "B", "C"], "weak1": ["A", "B", "C"], "weak2": ["A", "B", "C"]},
    "q5": {"strong": ["A", "B", "C"], "weak1": ["A", "B", "C"], "weak2": ["A", "B", "C"]},
    # correlated-failure queries: strong still nails A, but BOTH weak rankers
    # independently drift toward B (same failure mode, same wrong answer)
    "q6": {"strong": ["A", "C", "B"], "weak1": ["B", "A", "C"], "weak2": ["B", "A", "C"]},
    "q7": {"strong": ["A", "C", "B"], "weak1": ["B", "A", "C"], "weak2": ["B", "A", "C"]},
}
CORRECT_DOC = "A"


def top1_recall(top1_per_query):
    hits = sum(1 for doc in top1_per_query.values() if doc == CORRECT_DOC)
    return hits / len(top1_per_query)


# --- single engine (bge-m3-like: always correct) ----------------------------
strong_top1 = {q: v["strong"][0] for q, v in QUERIES.items()}
strong_recall = top1_recall(strong_top1)

# --- triple-RRF: fuse all three engines equally, per query ------------------
triple_top1 = {}
q6_fused = None
for q, v in QUERIES.items():
    fused = rrf_fuse([v["strong"], v["weak1"], v["weak2"]])
    triple_top1[q] = fused[0][0]
    if q == "q6":
        q6_fused = fused
triple_recall = top1_recall(triple_top1)

# --- dual-RRF: fuse strong + only ONE weak ranker (no correlated pair) -----
dual_top1 = {}
for q, v in QUERIES.items():
    fused = rrf_fuse([v["strong"], v["weak1"]])
    dual_top1[q] = fused[0][0]
dual_recall = top1_recall(dual_top1)

print("=== Recall@1 (top-1 correct) across 7 queries ===")
print(f"strong engine alone (bge-m3-like)     recall = {strong_recall:.3f}")
print(f"triple-RRF (strong + 2 correlated weak) recall = {triple_recall:.3f}  <- WORSE")
print(f"dual-RRF (strong + 1 weak, no pair-up) recall = {dual_recall:.3f}")

print(f"\nbook/17's real measured numbers: bge-m3 alone Recall@5=1.000, "
      f"triple-RRF Recall@5=0.929 (worse)")

print(f"\n=== why q6 flips: exact RRF fused scores ===")
for doc, score in q6_fused:
    print(f"  {doc}: {score:.5f}")

# --- asserts -----------------------------------------------------------------
# 1. the single strong engine must be perfect on this golden set (its own
#    "best single" baseline, matching book/17's bge-m3=1.000)
assert strong_recall == 1.0, "the strong single engine must get every query right on its own golden set"

# 2. triple-RRF (fusing 2 correlated weak rankers alongside the strong one)
#    must score WORSE than the strong engine alone -- book/17's actual finding
assert triple_recall < strong_recall, \
    "triple-RRF must score worse than the best single engine when weak rankers are correlated"

# 3. the exact mechanism: on the correlated-failure query, the wrong doc B's
#    fused RRF score must actually exceed the correct doc A's
q6_scores = dict(q6_fused)
assert q6_scores["B"] > q6_scores["A"], \
    "on a correlated-failure query, two weak rankers' consensus on the WRONG doc must outscore the strong ranker's single correct vote"

# 4. dual-RRF (strong + only ONE weak ranker, no correlated pair-up) must NOT
#    suffer the same failure -- there's no consensus to gang up with
assert dual_recall > triple_recall, \
    "removing the correlated second weak ranker must recover recall vs triple-RRF"
assert dual_recall == 1.0, \
    "fusing with just one weak ranker (no correlated partner) must not flip any query's top-1"

print("\n✓ all self-checks passed — RRF weights every ranker equally; correlated weak rankers can outvote a lone strong one.")
