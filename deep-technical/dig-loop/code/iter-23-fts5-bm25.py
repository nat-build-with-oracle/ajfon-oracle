"""Dig-loop 23/50 — BM25: keyword scoring in ~20 lines (what FTS5 runs).

Grounded in book/07-hybrid-search.md §7.1-7.2 (vector's blind spots: exact
codes like "PR #2740" get diluted by mean-pooling, and negation like "ไม่มี
น้ำตาล" barely moves cosine -- BM25/keyword search is exactly what's strong
where vector is weak) and §7.4 (real result: query "PR #2740" -> BM25 nails
it at rank 1 because IDF("#2740") is huge).
Runnable standalone (stdlib only):  python iter-23-fts5-bm25.py

Implements the real BM25 formula from scratch -- no RRF/hybrid fusion here
(that's iter-25); this iteration is just the keyword-scoring half.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math
from collections import Counter

CORPUS = {
    "d1": "ประชุมทีมเรื่อง PR #2740 แก้ drift harness ให้เสร็จก่อนศุกร์",
    "d2": "แผนสอน workshop เดือนกรกฎาคม เตรียมโน้ตบุ๊กและ Python",
    "d3": "งบประมาณโครงการปีหน้า ต้องขออนุมัติเพิ่ม",
    "d4": "ประชุมทีมเรื่องงบประมาณและแผนงานทีมเดือนหน้า",
    "d5": "สอนนักศึกษาเรื่อง vector search กับ workshop ครั้งก่อน",
}


def tokenize(text):
    return text.replace("#", " #").split()


docs_tokens = {doc_id: tokenize(text) for doc_id, text in CORPUS.items()}
doc_lens = {doc_id: len(toks) for doc_id, toks in docs_tokens.items()}
avgdl = sum(doc_lens.values()) / len(doc_lens)
N = len(CORPUS)


def idf(term):
    """book/07 §7.2 -- rare term (appears in few docs) gets a HIGH weight."""
    n_containing = sum(1 for toks in docs_tokens.values() if term in toks)
    return math.log((N - n_containing + 0.5) / (n_containing + 0.5) + 1)


def bm25_score(query_terms, doc_id, k1=1.5, b=0.75):
    toks = docs_tokens[doc_id]
    freq = Counter(toks)
    dl = doc_lens[doc_id]
    score = 0.0
    for t in query_terms:
        f = freq.get(t, 0)
        if f == 0:
            continue
        numerator = f * (k1 + 1)
        denominator = f + k1 * (1 - b + b * dl / avgdl)
        score += idf(t) * (numerator / denominator)
    return score


def bm25_rank(query_text, k=3):
    query_terms = tokenize(query_text)
    scores = {doc_id: bm25_score(query_terms, doc_id) for doc_id in CORPUS}
    return sorted(scores.items(), key=lambda x: -x[1])[:k]


print("=== BM25: query 'PR #2740' (rare exact code) ===")
for doc_id, s in bm25_rank("PR #2740"):
    print(f"  {doc_id}  score={s:.3f}  \"{CORPUS[doc_id][:35]}...\"")

print(f"\nIDF('#2740') = {idf('#2740'):.3f}   (appears in 1/{N} docs -- rare, big weight)")

print("\n=== term-frequency saturation: repeating a word doesn't scale linearly ===")
toks_1x = tokenize("สอบ")
toks_10x = tokenize(" ".join(["สอบ"] * 10))
docs_tokens["_test1x"] = toks_1x
docs_tokens["_test10x"] = toks_10x
doc_lens["_test1x"] = len(toks_1x)
doc_lens["_test10x"] = len(toks_10x)
score_1x = bm25_score(["สอบ"], "_test1x")
score_10x = bm25_score(["สอบ"], "_test10x")
print(f"1 occurrence  -> score={score_1x:.3f}")
print(f"10 occurrences -> score={score_10x:.3f}  (NOT 10x the 1-occurrence score)")

# --- asserts -----------------------------------------------------------------
# 1. the doc containing the exact rare code must rank #1 for that query --
#    book/07's real finding ("PR #2740 ขึ้นอันดับ 1 ทันที")
top_doc, top_score = bm25_rank("PR #2740")[0]
assert top_doc == "d1", "the document containing the exact rare code 'PR #2740' must rank #1"

# 2. a term appearing in EVERY doc must have IDF near zero -- tested on an
#    isolated toy corpus so it doesn't disturb the main corpus's IDF values
def idf_isolated(term, toks_by_doc):
    n_docs = len(toks_by_doc)
    n_containing = sum(1 for toks in toks_by_doc.values() if term in toks)
    return math.log((n_docs - n_containing + 0.5) / (n_containing + 0.5) + 1)


universal_corpus = {"u1": ["สวัสดี", "แมว"], "u2": ["สวัสดี", "หมา"], "u3": ["สวัสดี", "รถ"]}
assert idf_isolated("สวัสดี", universal_corpus) < 0.2, \
    "a term present in EVERY document must carry almost no discriminative weight"

# 3. term-frequency must be SATURATING, not linear -- 10 occurrences must
#    score less than 10x a single occurrence
assert score_10x < score_1x * 10, "BM25 term frequency must saturate, not scale linearly with repetition"
assert score_10x > score_1x, "more occurrences must still score at least somewhat higher than fewer"

# 4. the rare-code document's score for its OWN exact query must exceed a
#    generic document that shares no query terms at all
_, d5_score = [(d, s) for d, s in bm25_rank("PR #2740", k=5) if d == "d5"][0]
assert top_score > d5_score, "the exact-match document must clearly outscore an unrelated document"

print("\n✓ all self-checks passed — IDF rewards rare exact terms; term frequency saturates; the code query nails rank #1.")
