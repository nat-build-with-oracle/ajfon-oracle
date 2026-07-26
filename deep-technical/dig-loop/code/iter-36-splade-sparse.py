"""Dig-loop 36/50 — SPLADE: learned sparse weights, WITH expansion.

Grounded in deep-technical/34-sparse-retrieval-splade.md §34.1 (SPLADE's
expansion: a term gets a non-zero weight even if it never appears in the
document -- "doc: เบาหวาน metformin" gets weight on "diabetes" too, fixing
BM25's vocabulary-mismatch blind spot: "รถ" != "ยานพาหนะ" for pure lexical
matching) and §34.2-34.3 (scoring is still a sparse dot product over an
INVERTED INDEX -- no ANN needed, reuse the same FTS-style structure as
iter-23/29, just with model-learned weights instead of tf-idf).
Runnable standalone (stdlib only):  python iter-36-splade-sparse.py

The real SPLADE weight comes from an MLM's logits; here expansion terms are
a hand-placed stand-in table (no trained model available), enough to prove
the mechanism: sparse + interpretable (term->weight visible) + expansion
(recovers a vocabulary mismatch BM25 genuinely cannot).
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math
from collections import defaultdict

DOCS = {
    "d1": {"literal": ["ยานพาหนะ", "สี่ล้อ", "วิ่งเร็ว"],
           "expansion": {"รถ": 1.2, "รถยนต์": 0.9}},   # never appear in the text
    "d2": {"literal": ["สูตร", "กาแฟ", "cold", "brew"],
           "expansion": {}},                             # unrelated, no expansion needed
    "d3": {"literal": ["งบประมาณ", "โครงการ", "ปีหน้า"],
           "expansion": {"เงิน": 0.7}},
}

QUERY = "รถ"


def bm25_lexical_score(query_term, doc_id):
    """Pure lexical (Ch7-style BM25): score = 0 unless the term LITERALLY
    appears in the document."""
    return 1.0 if query_term in DOCS[doc_id]["literal"] else 0.0


def splade_weights(doc_id):
    """Combine literal-term weight (saturating, BM25-like) with expansion
    weight -- BOTH are just numbers in the same sparse vector; nothing
    marks one as "real" and the other as "guessed" at scoring time."""
    doc = DOCS[doc_id]
    weights = {}
    for t in doc["literal"]:
        weights[t] = weights.get(t, 0.0) + math.log(1 + 2.0)   # saturating presence weight
    for t, w in doc["expansion"].items():
        weights[t] = weights.get(t, 0.0) + w
    return weights


def splade_score(query_term, doc_id):
    return splade_weights(doc_id).get(query_term, 0.0)


print("=== BM25 (lexical-only) vs SPLADE (learned sparse + expansion) ===")
print(f"Q: '{QUERY}'  (never appears literally in any document)")
for doc_id in DOCS:
    bm25 = bm25_lexical_score(QUERY, doc_id)
    splade = splade_score(QUERY, doc_id)
    print(f"  {doc_id}: BM25={bm25:.2f}   SPLADE={splade:.2f}   "
          f"(literal terms: {DOCS[doc_id]['literal']})")

# --- build a real inverted index over the SPLADE weight vectors -----------
inverted_index = defaultdict(list)
all_weights = {}
for doc_id in DOCS:
    w = splade_weights(doc_id)
    all_weights[doc_id] = w
    for term, weight in w.items():
        inverted_index[term].append((doc_id, weight))

query_posting = inverted_index.get(QUERY, [])
touched_docs = len(query_posting)

print(f"\n=== inverted index lookup for '{QUERY}' (no ANN, no full scan) ===")
print(f"posting list: {query_posting}")
print(f"docs touched = {touched_docs} (out of {len(DOCS)} total in corpus)")

ranked = sorted(query_posting, key=lambda x: -x[1])
print(f"ranked by weight: {ranked}")

# --- asserts -----------------------------------------------------------------
# 1. pure BM25 (lexical) must score ZERO for every doc -- the query term
#    never appears literally anywhere; this is the real vocabulary-mismatch
#    blind spot BM25/FTS5 cannot solve on its own
for doc_id in DOCS:
    assert bm25_lexical_score(QUERY, doc_id) == 0.0, \
        f"pure lexical BM25 must score 0 for '{QUERY}' on {doc_id} -- it never appears literally"

# 2. SPLADE must give a NON-ZERO score to d1 via expansion -- the term
#    "รถ" was never in d1's text, yet the sparse vector carries real weight
assert splade_score(QUERY, "d1") > 0.0, \
    "SPLADE's expansion must give '{}' a non-zero weight on d1 even though it never appears literally".format(QUERY)

# 3. SPLADE must correctly rank d1 above the genuinely unrelated d2 (coffee)
#    and d3 (budget, only weak/no expansion for this term)
assert splade_score(QUERY, "d1") > splade_score(QUERY, "d2"), \
    "SPLADE must rank the car-related doc above the unrelated coffee doc"
assert splade_score(QUERY, "d1") > splade_score(QUERY, "d3"), \
    "SPLADE must rank the car-related doc above the budget doc"

# 4. the inverted index lookup must touch ONLY docs whose sparse vector
#    actually contains the query term as a key -- not the whole corpus
assert touched_docs == 1, "the inverted index posting list for 'รถ' must contain exactly the 1 doc with that weight"
assert touched_docs < len(DOCS), "indexed sparse lookup must touch fewer docs than the full corpus"

# 5. interpretability: d1's weight vector must contain a term with real
#    weight that is NOT among d1's literal tokens -- the defining SPLADE
#    property (expansion), directly visible in the data structure
d1_weights = splade_weights("d1")
expanded_terms = [t for t in d1_weights if t not in DOCS["d1"]["literal"]]
assert len(expanded_terms) > 0 and all(d1_weights[t] > 0 for t in expanded_terms), \
    "d1's sparse vector must contain at least one non-literal (expanded) term with positive weight"

print("\n✓ all self-checks passed — SPLADE stays sparse+indexed (no ANN) but expansion fixes BM25's vocabulary-mismatch blind spot.")
