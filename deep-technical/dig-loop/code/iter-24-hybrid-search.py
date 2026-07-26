"""Dig-loop 24/50 — Hybrid search: vector and keyword each win where the other loses.

Grounded in book/07-hybrid-search.md §7.4 (real result: query "PR #2740" ->
BM25 nails it, vector dilutes the code; query "บอร์ดสำหรับสอน IoT" -> vector
finds the ESP32 doc via meaning, BM25 finds nothing lexically) and
deep-technical/04-arra-code-hybrid-scoring.md §4.0/§4.6 (ARRA's real
architecture: FTS leg + vector leg -> fuse -> hybrid is the DEFAULT mode,
not a fallback -- "สองระบบถนัดคนละเขต").
Runnable standalone (stdlib only):  python iter-24-hybrid-search.py

This is the "two blind spots, one fix" demo -- the RRF math itself (k=60,
the 1/61 proof) is iter-25's job; here the point is just: each single method
misses a DIFFERENT query, and combining beats either alone.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math
from collections import Counter

CORPUS = {
    "d1": "ประชุมทีมเรื่อง PR #2740 แก้ drift harness ให้เสร็จก่อนศุกร์",
    "d2": "ESP32 ไมโครคอนโทรลเลอร์ราคาถูก เหมาะทำโปรเจกต์ระบบฝังตัวเบื้องต้น",
    "d3": "สอนนักศึกษาเรื่อง vector search กับ workshop ครั้งก่อน",
    "d4": "งบประมาณโครงการปีหน้า ต้องขออนุมัติเพิ่ม",
    "d5": "สูตรกาแฟ cold brew กาแฟ 100g น้ำ 1L แช่ 18 ชั่วโมง",
}

# --- toy semantic vectors: [code/dev, iot_hardware, teaching, finance, food] -
DOC_VECS = {
    "d1": [0.90, 0.05, 0.10, 0.05, 0.0],
    "d2": [0.10, 0.95, 0.15, 0.0, 0.0],
    "d3": [0.05, 0.10, 0.90, 0.0, 0.0],
    "d4": [0.0, 0.0, 0.05, 0.95, 0.0],
    "d5": [0.0, 0.0, 0.0, 0.0, 0.95],
}
QUERY_VECS = {
    # mean-pooling "ประชุมทีมเรื่อง PR #2740 แก้ ... ให้เสร็จก่อนศุกร์" dilutes the rare
    # code token among generic teamwork/discussion words -> vector drifts toward
    # the "teaching/discussion" axis instead of the "code" axis (book/07 §7.1)
    "PR #2740": [0.15, 0.0, 0.80, 0.0, 0.0],
    "บอร์ดสำหรับสอน IoT": [0.05, 0.85, 0.30, 0.0, 0.0],  # strong semantic match to d2
}


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def vector_rank(query_text):
    qvec = QUERY_VECS[query_text]
    scores = {d: cosine(qvec, v) for d, v in DOC_VECS.items()}
    return sorted(scores, key=lambda d: -scores[d])


# --- BM25 (same shape as iter-23) ------------------------------------------
def tokenize(text):
    return text.replace("#", " #").split()


docs_tokens = {d: tokenize(t) for d, t in CORPUS.items()}
doc_lens = {d: len(toks) for d, toks in docs_tokens.items()}
avgdl = sum(doc_lens.values()) / len(doc_lens)
N = len(CORPUS)


def idf(term):
    n = sum(1 for toks in docs_tokens.values() if term in toks)
    return math.log((N - n + 0.5) / (n + 0.5) + 1)


def bm25_score(query_terms, doc_id, k1=1.5, b=0.75):
    freq = Counter(docs_tokens[doc_id])
    dl = doc_lens[doc_id]
    total = 0.0
    for t in query_terms:
        f = freq.get(t, 0)
        if f == 0:
            continue
        total += idf(t) * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl))
    return total


def bm25_rank(query_text):
    terms = tokenize(query_text)
    scores = {d: bm25_score(terms, d) for d in CORPUS}
    return sorted(scores, key=lambda d: -scores[d])


# --- RRF fuse (mechanics only -- k=60 math itself is proven in iter-25) ----
def rrf_fuse(rank_lists, k=60):
    scores = {}
    for ranks in rank_lists:
        for pos, doc in enumerate(ranks, 1):
            scores[doc] = scores.get(doc, 0) + 1 / (k + pos)
    return sorted(scores, key=lambda d: -scores[d])


queries = ["PR #2740", "บอร์ดสำหรับสอน IoT"]
expected_top1 = {"PR #2740": "d1", "บอร์ดสำหรับสอน IoT": "d2"}

print("=== each single method's blind spot ===")
results = {}
for q in queries:
    v_rank = vector_rank(q)
    b_rank = bm25_rank(q)
    h_rank = rrf_fuse([b_rank, v_rank])
    results[q] = {"vector": v_rank, "bm25": b_rank, "hybrid": h_rank}
    print(f"\nQ: \"{q}\"  (expected top-1 = {expected_top1[q]})")
    print(f"  vector-only top-1 = {v_rank[0]}   {'✓' if v_rank[0]==expected_top1[q] else '✗ MISSED'}")
    print(f"  BM25-only  top-1 = {b_rank[0]}   {'✓' if b_rank[0]==expected_top1[q] else '✗ MISSED'}")
    print(f"  hybrid(RRF) top-1 = {h_rank[0]}   {'✓' if h_rank[0]==expected_top1[q] else '✗ MISSED'}")

# --- asserts -----------------------------------------------------------------
# 1. vector-only must MISS the exact-code query (its blind spot, book/07 §7.1)
assert results["PR #2740"]["vector"][0] != "d1", \
    "vector-only search must NOT reliably surface the exact-code doc as top-1 (its real blind spot)"

# 2. BM25-only must correctly nail the exact-code query
assert results["PR #2740"]["bm25"][0] == "d1", \
    "BM25 must correctly rank the exact-code document #1 for an exact-code query"

# 3. BM25-only must MISS the semantic IoT query (no lexical overlap: "บอร์ด/IoT" vs "ESP32/ไมโครคอนโทรลเลอร์")
assert results["บอร์ดสำหรับสอน IoT"]["bm25"][0] != "d2", \
    "BM25-only must NOT find the ESP32 doc via pure lexical match (its real blind spot)"

# 4. vector-only must correctly find the ESP32 doc for the semantic query
assert results["บอร์ดสำหรับสอน IoT"]["vector"][0] == "d2", \
    "vector search must correctly surface the semantically related ESP32 doc"

# 5. hybrid (RRF-fused) must get BOTH queries right -- the entire point of
#    combining two systems that are strong in different zones
for q in queries:
    assert results[q]["hybrid"][0] == expected_top1[q], \
        f"hybrid search must correctly rank the right doc #1 for query '{q}'"

print("\n✓ all self-checks passed — vector and BM25 each miss one query alone; hybrid gets BOTH right.")
