"""Dig-loop 27/50 — Complementary-recall diagnostic: will fusion even help?

Grounded in book/17-multi-engine-benchmark.md §X.4 ("fusion ช่วยเมื่อ ranker
เก่งพอทุกตัว + พลาดคนละแบบ (independent) -- ไม่ใช่ correlated" -- and "ตัวชี้ขาด
= วัด fused vs best-single บน golden เอง ไม่มีเลขวิเศษ") plus iter-25's Kendall
tau idea and iter-26's real correlated-failure result. This builds the actual
PRE-CHECK: before ever running RRF, look at which queries each ranker gets
right/wrong. If their FAILURES don't overlap (complementary), fusion has real
headroom (union/oracle recall clears either alone). If failures overlap
heavily (correlated, like iter-26's nomic/qwen3), fusion has nothing to gain.
Runnable standalone (stdlib only):  python iter-27-complementary-recall.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""

# --- pair 1: BM25 vs vector (iter-24's real pair -- each misses a DIFFERENT
#     query: vector misses "PR #2740", BM25 misses the semantic IoT query) --
complementary_pair = {
    "q1": {"bm25": True, "vector": True},
    "q2": {"bm25": True, "vector": True},
    "q3": {"bm25": True, "vector": True},
    "q4": {"bm25": False, "vector": True},   # BM25 misses this one
    "q5": {"bm25": True, "vector": False},   # vector misses this one
}

# --- pair 2: nomic vs qwen3 (iter-26's real pair -- both weak on Thai,
#     fail the SAME 2 queries because they share the same root weakness) ----
correlated_pair = {
    "q1": {"nomic": True, "qwen3": True},
    "q2": {"nomic": True, "qwen3": True},
    "q3": {"nomic": True, "qwen3": True},
    "q4": {"nomic": True, "qwen3": True},
    "q5": {"nomic": False, "qwen3": False},   # BOTH miss this one
    "q6": {"nomic": False, "qwen3": False},   # BOTH miss this one too
}


def recall(pair_data, engine):
    hits = sum(1 for q in pair_data if pair_data[q][engine])
    return hits / len(pair_data)


def oracle_union_recall(pair_data, engines):
    """If we could magically always pick whichever engine got it right --
    the theoretical ceiling any fusion method could ever reach."""
    hits = sum(1 for q, res in pair_data.items() if any(res[e] for e in engines))
    return hits / len(pair_data)


def complementary_score(pair_data, engines):
    """The diagnostic: of all queries where AT LEAST ONE engine is wrong,
    what fraction are 'complementary' (exactly one wrong) rather than
    'correlated' (both wrong)? High = fusion has headroom. Low/zero = it
    doesn't -- computed WITHOUT ever running RRF."""
    any_wrong = [q for q, res in pair_data.items() if not all(res[e] for e in engines)]
    if not any_wrong:
        return 1.0   # no failures at all -- trivially "complementary" (nothing to fix)
    exactly_one_wrong = sum(
        1 for q in any_wrong
        if sum(1 for e in engines if not pair_data[q][e]) == len(engines) - 1
    )
    return exactly_one_wrong / len(any_wrong)


print("=== pair 1: BM25 vs vector (complementary failures) ===")
r_bm25 = recall(complementary_pair, "bm25")
r_vector = recall(complementary_pair, "vector")
r_union1 = oracle_union_recall(complementary_pair, ["bm25", "vector"])
score1 = complementary_score(complementary_pair, ["bm25", "vector"])
print(f"recall(bm25)={r_bm25:.3f}  recall(vector)={r_vector:.3f}  oracle-union={r_union1:.3f}")
print(f"complementary score = {score1:.3f}  -> fusion has headroom (union clears both singles)")

print("\n=== pair 2: nomic vs qwen3 (correlated failures) ===")
r_nomic = recall(correlated_pair, "nomic")
r_qwen3 = recall(correlated_pair, "qwen3")
r_union2 = oracle_union_recall(correlated_pair, ["nomic", "qwen3"])
score2 = complementary_score(correlated_pair, ["nomic", "qwen3"])
print(f"recall(nomic)={r_nomic:.3f}  recall(qwen3)={r_qwen3:.3f}  oracle-union={r_union2:.3f}")
print(f"complementary score = {score2:.3f}  -> fusion has NO headroom (union == either single)")

print(f"\nbook/17's real lesson: fusion helps only when misses are independent, "
      f"not correlated -- checkable BEFORE running RRF at all")

# --- asserts -----------------------------------------------------------------
# 1. oracle union recall must never be LOWER than either single engine's recall
assert r_union1 >= max(r_bm25, r_vector)
assert r_union2 >= max(r_nomic, r_qwen3)

# 2. pair 1 (complementary): oracle union must be STRICTLY better than either
#    single engine -- real headroom for fusion to exploit
assert r_union1 > max(r_bm25, r_vector), \
    "complementary failures must give a real oracle-union improvement over either single engine"

# 3. pair 2 (correlated): oracle union must EQUAL the best single engine --
#    no headroom exists, no fusion method can do better than the best single
assert r_union2 == max(r_nomic, r_qwen3), \
    "correlated failures must give NO oracle-union improvement -- fusion cannot possibly help here"

# 4. the complementary score must correctly distinguish the two cases: high
#    for pair 1, near-zero for pair 2
assert score1 > 0.5, "the BM25-vs-vector pair must score as clearly complementary"
assert score2 < 0.2, "the nomic-vs-qwen3 pair must score as clearly correlated (little to no complementarity)"
assert score1 > score2, "complementary score must be higher for the genuinely complementary pair"

# 5. this diagnostic must be computable from success/failure PATTERNS alone,
#    with no dependency on ever having run an actual RRF fusion
assert isinstance(score1, float) and isinstance(score2, float)

print("\n✓ all self-checks passed — check complementary vs correlated failure BEFORE fusing; the diagnostic predicts it.")
