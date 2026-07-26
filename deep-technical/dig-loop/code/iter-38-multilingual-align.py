"""Dig-loop 38/50 — Multilingual alignment: Thai query finds an English doc.

Grounded in deep-technical/19-multilingual-alignment.md §19.0-19.1 (the real
phenomenon: query "การรักษาเบาหวานด้วย AI" (Thai) finds "AI-driven diabetes
management: a review" (English) with NO shared characters at all -- possible
only because a MULTILINGUAL model trains parallel-pair contrastive pairs so
same-meaning sentences land close REGARDLESS of language; a monolingual
model keeps Thai and English in separate subspaces, cosine stays low) and
§19.3 (translation gap: cross-lingual match is real but slightly weaker than
a same-language exact match -- "≈" not "=").
Runnable standalone (stdlib only):  python iter-38-multilingual-align.py

Also proves §19.0's FTS claim directly: BM25/FTS has ZERO shared tokens
between a Thai query and an English doc, so it can NEVER bridge this gap --
only a shared embedding space can.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


# --- ALIGNED (multilingual) model: same CONCEPT -> near-same vector,
#     regardless of which language the text is written in (§19.1) ----------
ALIGNED_VECS = {
    ("th", "diabetes"): [0.90, 0.10],
    ("en", "diabetes"): [0.87, 0.13],   # near-identical to Thai -- a small "translation gap"
    ("th", "cooking"):  [0.10, 0.90],
    ("en", "cooking"):  [0.13, 0.87],
}

# --- UNALIGNED (monolingual) model: Thai and English occupy COMPLETELY
#     separate subspaces -- same concept, but the languages never meet -----
UNALIGNED_VECS = {
    ("th", "diabetes"): [0.90, 0.10, 0.0, 0.0],
    ("en", "diabetes"): [0.0, 0.0, 0.90, 0.10],   # orthogonal to the Thai one
    ("th", "cooking"):  [0.10, 0.90, 0.0, 0.0],
    ("en", "cooking"):  [0.0, 0.0, 0.10, 0.90],
}

QUERY_TH = "การรักษาเบาหวานด้วย AI"
DOC_EN = "AI-driven diabetes management: a review"


def tokenize(text):
    return text.lower().split()


def bm25_shared_tokens(query, doc):
    return set(tokenize(query)) & set(tokenize(doc))


aligned_cos = cosine(ALIGNED_VECS[("th", "diabetes")], ALIGNED_VECS[("en", "diabetes")])
unaligned_cos = cosine(UNALIGNED_VECS[("th", "diabetes")], UNALIGNED_VECS[("en", "diabetes")])

print("=== cross-lingual retrieval: Thai query, English doc, same TOPIC ===")
print(f"Q (th): {QUERY_TH}")
print(f"D (en): {DOC_EN}")
print(f"aligned (multilingual) model  cos = {aligned_cos:.4f}")
print(f"unaligned (monolingual) model cos = {unaligned_cos:.4f}")

shared = bm25_shared_tokens(QUERY_TH, DOC_EN)
print(f"\nBM25/FTS shared tokens = {shared}  (score would be exactly 0 -- different scripts entirely)")

# --- alignment must be topic-SPECIFIC, not "everything looks the same" ----
aligned_cross_topic = cosine(ALIGNED_VECS[("th", "diabetes")], ALIGNED_VECS[("en", "cooking")])
print(f"\naligned model, MISMATCHED topics (th diabetes vs en cooking) cos = {aligned_cross_topic:.4f}")

# --- translation gap: cross-lingual match is good, but not as perfect as
#     the same language matching itself exactly ------------------------------
same_lang_cos = cosine(ALIGNED_VECS[("th", "diabetes")], ALIGNED_VECS[("th", "diabetes")])
print(f"\nsame-language exact match cos = {same_lang_cos:.4f}  (the ceiling)")
print(f"cross-lingual match cos       = {aligned_cos:.4f}  (real, but slightly below the ceiling -- §19.3's 'translation gap')")

# --- asserts -----------------------------------------------------------------
# 1. the aligned (multilingual) model must give a HIGH cross-lingual match
#    for the SAME concept across Thai and English
assert aligned_cos > 0.9, "an aligned multilingual model must give a high cosine for the same concept across languages"

# 2. the unaligned (monolingual) model must give a near-ZERO match -- the
#    real failure mode described in §19.1 (languages in separate subspaces)
assert unaligned_cos < 0.1, \
    "an unaligned monolingual model must fail to bridge languages -- cosine stays near zero"

# 3. alignment must be a LARGE, measurable difference between the two models
assert aligned_cos - unaligned_cos > 0.8, \
    "the gap between aligned and unaligned cross-lingual cosine must be large and real"

# 4. BM25/FTS must have ZERO shared tokens between the Thai query and English
#    doc -- proving FTS can NEVER solve cross-lingual retrieval on its own
assert len(shared) == 0, "a Thai query and English doc must share ZERO literal tokens (different scripts entirely)"

# 5. alignment must be topic-SPECIFIC: a Thai diabetes query vs an English
#    COOKING doc must score clearly lower than vs the matching diabetes doc
assert aligned_cross_topic < aligned_cos - 0.5, \
    "cross-lingual alignment must not blur DIFFERENT topics together -- mismatched topic must score much lower"

# 6. translation gap: cross-lingual match must be real and strong, but not
#    exceed the same-language ceiling (≈, not =, per §19.3)
assert aligned_cos <= same_lang_cos, "cross-lingual match must not exceed the same-language exact-match ceiling"
assert same_lang_cos - aligned_cos < 0.15, \
    "the translation gap must be small -- cross-lingual match should be close to, not far from, the ceiling"

print("\n✓ all self-checks passed — alignment lets Thai find English by MEANING; FTS never could; alignment respects topic, not just language.")
