"""Dig-loop 34/50 — Cross-encoder reranker: sees query+doc TOGETHER, catches negation.

Grounded in deep-technical/18-cross-encoder-reranker.md §18.0-18.2 (bi-encoder
encodes query and doc SEPARATELY then cosines them -- fast, precomputable,
but "doesn't see" fine interactions like negation; cross-encoder feeds
[CLS] query [SEP] doc [SEP] into ONE encoder pass -- attention crosses
query<->doc directly, catching things bi-encoder can't, but can't be
precomputed) and §18.5 (2-stage pipeline: bi-encoder recall top-50 from the
FULL corpus cheaply, cross-encoder reranks only those 50 -- reranking the
whole corpus would be impossible, but 50 forward passes is fine).
Runnable standalone (stdlib only):  python iter-34-cross-encoder-rerank.py

The real classic bi-encoder blind spot (book/07 §7.1): cos("มีน้ำตาล",
"ไม่มีน้ำตาล") is HIGH because they share almost every token and differ only
by a short negation particle that mean-pooling dilutes away. The first part
below hand-places small toy vectors to make that dilution concrete and
provable; the second part reuses a hash-based embedder over a larger corpus
to prove the 2-stage recall->rerank pipeline's SHAPE.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


# --- 1. the negation blind spot, made concrete with small hand-placed vectors
# axes stand for [coffee-topic, "หวาน"(sweet)-word-presence, negation-marker-drift]
# "sweet" doc shares the query's literal words almost exactly (same direction)
# "unsweet" doc is semantically CORRECT but the negation marker perturbs its
# vector away from the query's direction -- exactly book/07's real symptom.
QUERY_VEC = [0.90, 0.40, 0.0]
SWEET_VEC = [0.90, 0.40, 0.0]      # "กาแฟใส่น้ำตาลหวานมาก" -- WRONG (has sugar)
UNSWEET_VEC = [0.70, 0.30, 0.30]   # "กาแฟไม่ใส่น้ำตาลเลย"   -- RIGHT (no sugar)

DOC_TEXT = {
    "sweet": "กาแฟใส่น้ำตาลหวานมาก",
    "unsweet": "กาแฟไม่ใส่น้ำตาลเลย",
}


def bi_encoder_score(query_vec, doc_vec):
    """Stage 1: fast, precomputable -- query and doc never "meet"; only their
    PRE-COMPUTED vectors are compared."""
    return cosine(query_vec, doc_vec)


def cross_encoder_score(query_text, doc_text, query_vec, doc_vec):
    """Stage 2 stand-in: query and doc are reasoned about TOGETHER (a real
    cross-encoder does this via joint self-attention, Ch10). Here: explicit
    negation-agreement check on the TEXT -- the interaction a bi-encoder's
    precomputed vectors cannot see."""
    base = cosine(query_vec, doc_vec)
    query_negative = "ไม่" in query_text
    doc_negative = "ไม่" in doc_text
    return base + 0.5 if query_negative == doc_negative else base - 0.5


QUERY_TEXT = "อยากได้กาแฟไม่หวาน"

bi_sweet = bi_encoder_score(QUERY_VEC, SWEET_VEC)
bi_unsweet = bi_encoder_score(QUERY_VEC, UNSWEET_VEC)
cross_sweet = cross_encoder_score(QUERY_TEXT, DOC_TEXT["sweet"], QUERY_VEC, SWEET_VEC)
cross_unsweet = cross_encoder_score(QUERY_TEXT, DOC_TEXT["unsweet"], QUERY_VEC, UNSWEET_VEC)

print("=== bi-encoder vs cross-encoder on a negation query ===")
print(f"Q: {QUERY_TEXT}")
print(f"bi-encoder:    sweet doc={bi_sweet:.4f}  unsweet doc={bi_unsweet:.4f}  "
      f"-> top-1={'sweet (WRONG)' if bi_sweet >= bi_unsweet else 'unsweet (right)'}")
print(f"cross-encoder: sweet doc={cross_sweet:.4f}  unsweet doc={cross_unsweet:.4f}  "
      f"-> top-1={'unsweet (right)' if cross_unsweet > cross_sweet else 'sweet (WRONG)'}")


# --- 2. the 2-stage pipeline SHAPE: bi-encoder recall top-50 from a bigger
#     corpus (cheap), cross-encoder reranks ONLY those 50 (expensive but rare)
def toy_embed(text):
    """Word-level hash embedding for the larger filler corpus (iter-05 style)."""
    DIM = 16
    tokens = text.split()
    vecs = []
    for t in tokens:
        seed = sum((i + 1) * ord(c) for i, c in enumerate(t))
        v = [((seed * (k + 7)) % 97) / 97 - 0.5 for k in range(DIM)]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        vecs.append([x / n for x in v])
    return [sum(v[d] for v in vecs) / len(vecs) for d in range(DIM)]


N_CORPUS = 200
corpus_vecs = {"unsweet": UNSWEET_VEC + [0.0] * 13, "sweet": SWEET_VEC + [0.0] * 13}
corpus_text = dict(DOC_TEXT)
for i in range(N_CORPUS - 2):
    filler_text = f"บันทึกทั่วไป เรื่องที่ {i} เกี่ยวกับงานประจำวัน"
    corpus_text[f"filler{i}"] = filler_text
    corpus_vecs[f"filler{i}"] = toy_embed(filler_text)

query_vec_16d = QUERY_VEC + [0.0] * 13
bi_scores = {doc_id: cosine(query_vec_16d, vec) for doc_id, vec in corpus_vecs.items()}
stage1_top50 = sorted(bi_scores, key=lambda d: -bi_scores[d])[:50]

cross_scores = {}
for doc_id in stage1_top50:
    cross_scores[doc_id] = cross_encoder_score(
        QUERY_TEXT, corpus_text[doc_id], query_vec_16d, corpus_vecs[doc_id])
cross_encoder_calls = len(cross_scores)

final_top1 = sorted(cross_scores, key=lambda d: -cross_scores[d])[0]

print(f"\n=== 2-stage pipeline (§18.5), corpus N={N_CORPUS} ===")
print(f"stage1 bi-encoder: scored ALL {N_CORPUS} docs (cheap, precomputable)")
print(f"stage2 cross-encoder: reranked only {cross_encoder_calls} docs (top-50 from stage1)")
print(f"final top-1 after rerank: {final_top1}")

# --- asserts -----------------------------------------------------------------
# 1. the bi-encoder must actually show the classic negation blind spot: the
#    WRONG (sweet) doc must score at least as high as the RIGHT (unsweet) one
assert bi_sweet >= bi_unsweet, \
    "bi-encoder must show the real negation blind spot: sweet doc scores at or above unsweet"

# 2. the cross-encoder must correctly rank the unsweet doc ABOVE the sweet
#    doc -- catching the negation interaction the bi-encoder missed
assert cross_unsweet > cross_sweet, \
    "cross-encoder must correctly rank the negation-matching (unsweet) doc higher"

# 3. stage 1 must touch the FULL corpus (that's what makes it cheap: one
#    embed + cosine per doc, no joint encoding)
assert len(bi_scores) == N_CORPUS, "bi-encoder stage must score every document in the corpus"

# 4. stage 2 must touch ONLY 50 docs, never the full corpus -- the entire
#    point of the pipeline (at real scale -- 35k docs -- reranking everything
#    would be impossible; 50 forward passes is fine)
assert cross_encoder_calls == 50, "cross-encoder reranking must be limited to exactly the top-50 candidates"
assert cross_encoder_calls < N_CORPUS, "cross-encoder must touch far fewer docs than the full corpus"

# 5. precondition (§18.5): the correct doc MUST survive into stage 1's
#    top-50, or stage 2 can't rescue it -- verify it actually does here
assert "unsweet" in stage1_top50, \
    "the correct doc must be present in stage1's top-50 -- if bi-encoder recall misses it, reranking can't help"

# 6. the final pipeline output must be the CORRECT doc -- cross-encoder
#    successfully fixes what bi-encoder alone got wrong
assert final_top1 == "unsweet", "the 2-stage pipeline must produce the correct final answer"

print("\n✓ all self-checks passed — bi-encoder misses negation alone; cross-encoder catches it; pipeline reranks only top-50, not the whole corpus.")
