"""Dig-loop 41/50 — Honest benchmarking: pooled judgment, not circular labeling.

Grounded in book/17-multi-engine-benchmark.md §X.1 ("กับดัก: label เฉลยจาก
output ของ engine ตัวเดียว = circular (ฝัง bias เข้า ground truth) · วิธีถูก
pooled judgment (TREC/BEIR): ตัดสิน relevant จากการอ่าน corpus, ไม่ใช่จาก engine
เดียว") -- if you build your golden set from engine A's own top results, engine
A will trivially look perfect on ITS OWN golden set, hiding that a genuinely
better engine B exists. This demo makes that paradox concrete and provable.
Runnable standalone (stdlib only):  python iter-41-multi-engine-benchmark.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""

# --- the actual, human-judged ground truth (read the corpus, not an engine) -
TRUE_RELEVANT = {
    "q1": {"doc_correct_1"},
    "q2": {"doc_correct_2"},
    "q3": {"doc_correct_3"},
    "q4": {"doc_correct_4"},
    "q5": {"doc_correct_5"},
}

# --- weak engine (nomic-like): consistently retrieves the WRONG doc,
#     confidently, for every query (mirrors book/05's Thai-anisotropy story) -
WEAK_ENGINE_TOP1 = {
    "q1": "doc_wrong_1",
    "q2": "doc_wrong_2",
    "q3": "doc_wrong_3",
    "q4": "doc_wrong_4",
    "q5": "doc_wrong_5",
}

# --- strong engine (bge-m3-like): genuinely finds the correct doc every time
STRONG_ENGINE_TOP1 = {
    "q1": "doc_correct_1",
    "q2": "doc_correct_2",
    "q3": "doc_correct_3",
    "q4": "doc_correct_4",
    "q5": "doc_correct_5",
}


def recall_at_1(engine_top1, golden):
    hits = sum(1 for q, doc in engine_top1.items() if doc in golden[q])
    return hits / len(golden)


# --- THE TRAP (§X.1): build a "golden set" from the WEAK engine's own
#     outputs -- circular, self-referential, no independent judgment -------
circular_golden_from_weak = {q: {doc} for q, doc in WEAK_ENGINE_TOP1.items()}

weak_on_circular = recall_at_1(WEAK_ENGINE_TOP1, circular_golden_from_weak)
weak_on_honest = recall_at_1(WEAK_ENGINE_TOP1, TRUE_RELEVANT)
strong_on_circular = recall_at_1(STRONG_ENGINE_TOP1, circular_golden_from_weak)
strong_on_honest = recall_at_1(STRONG_ENGINE_TOP1, TRUE_RELEVANT)

print("=== §X.1's trap: golden set built from the WEAK engine's own outputs ===")
print(f"weak engine   recall@1 on circular (self) golden = {weak_on_circular:.2f}  <- looks PERFECT")
print(f"weak engine   recall@1 on HONEST golden           = {weak_on_honest:.2f}  <- actually terrible")
print(f"strong engine recall@1 on circular (weak's) golden = {strong_on_circular:.2f}  <- looks TERRIBLE")
print(f"strong engine recall@1 on HONEST golden            = {strong_on_honest:.2f}  <- actually great")

print(f"\nif you trusted the circular golden set: weak engine (1.00) 'beats' strong engine (0.00)!")
print(f"the honest golden set reveals the TRUE story: strong (1.00) genuinely beats weak (0.00)")

# --- pooled judgment (§X.1): build the golden set from the UNION of what
#     MULTIPLE engines retrieve, not just one -- reduces (but doesn't erase)
#     single-engine bias, and is the real TREC/BEIR methodology -------------
def pooled_candidates(query, engines_top1):
    return {engine_top1[query] for engine_top1 in engines_top1}


pooled_pool = {q: pooled_candidates(q, [WEAK_ENGINE_TOP1, STRONG_ENGINE_TOP1]) for q in TRUE_RELEVANT}
print(f"\n=== pooled candidates per query (union across engines, before human judgment) ===")
for q in pooled_pool:
    print(f"  {q}: pool={pooled_pool[q]}  (a human/reading check then decides which of these are TRULY relevant)")

# --- asserts -----------------------------------------------------------------
# 1. the circular trap must actually happen: the weak engine must look
#    PERFECT when judged against a golden set built from its own outputs
assert weak_on_circular == 1.0, \
    "a golden set built from an engine's own outputs must trivially give that engine perfect recall"

# 2. the same weak engine must score TERRIBLY on the honest, independent
#    golden set -- proving the circular score was fake
assert weak_on_honest == 0.0, \
    "the weak engine must score genuinely poorly against the real, human-judged ground truth"

# 3. the strong engine must score TERRIBLY on the circular (weak-biased)
#    golden set -- the paradox: being RIGHT looks like being WRONG when the
#    ground truth itself is contaminated by the weak engine's own mistakes
assert strong_on_circular == 0.0, \
    "the strong engine must score poorly on a golden set biased toward the weak engine's wrong answers"

# 4. the strong engine must score PERFECTLY on the honest golden set --
#    the real conclusion, hidden by the circular evaluation
assert strong_on_honest == 1.0, \
    "the strong engine must score perfectly against the real, human-judged ground truth"

# 5. the circular evaluation must produce the OPPOSITE ranking from the
#    honest evaluation -- this is exactly why circular labeling is
#    dangerous, not just slightly biased
assert weak_on_circular > strong_on_circular, \
    "circular (self-referential) evaluation must rank the weak engine ABOVE the strong one"
assert strong_on_honest > weak_on_honest, \
    "honest evaluation must rank the strong engine ABOVE the weak one -- the true, correct conclusion"

# 6. pooled candidates must include BOTH engines' answers for every query --
#    the actual mechanism that lets a human catch the weak engine's mistake
for q in TRUE_RELEVANT:
    assert WEAK_ENGINE_TOP1[q] in pooled_pool[q] and STRONG_ENGINE_TOP1[q] in pooled_pool[q], \
        f"the pooled candidate set for {q} must include both engines' top-1 answers for human judgment"

print("\n✓ all self-checks passed — circular golden sets can invert the truth; pooled judgment (read the corpus) is the only honest fix.")
