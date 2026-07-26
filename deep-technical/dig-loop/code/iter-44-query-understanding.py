"""Dig-loop 44/50 — HyDE: embed the FAKE answer, not the short query.

Grounded in deep-technical/29-query-understanding.md §29.0 (query is a WEAK
signal: short, vague vs a long, context-rich document -- asymmetry, Ch2
§2.7) and §29.2 (HyDE trick: have an LLM write a fake, possibly-wrong answer
in DOCUMENT style, then embed THAT instead of the raw short query -- the
fake answer lives in "document space" so it lands closer to the real
document than the query ever could) plus §29.3 (multi-query: generate N
query variants, search each, RRF-fuse -- covers more interpretations).
Runnable standalone (stdlib only):  python iter-44-query-understanding.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math

RAW_QUERY = "เบาหวาน AI"

REAL_DOC = (
    "งานวิจัยนี้ใช้ machine learning วิเคราะห์ค่า HbA1c และภาพถ่าย retinal "
    "เพื่อช่วยแพทย์วินิจฉัยโรคเบาหวานได้แม่นยำและรวดเร็วกว่าวิธีเดิม"
)

# HyDE: an LLM-written FAKE answer -- may be factually imprecise, but it's
# written in the SAME long, technical, document-like STYLE as a real doc
HYDE_FAKE_ANSWER = (
    "AI ใช้ machine learning วิเคราะห์ค่า HbA1c และภาพ retinal image "
    "เพื่อช่วยแพทย์วินิจฉัยเบาหวานได้เร็วขึ้นและแม่นยำขึ้นกว่าการตรวจแบบดั้งเดิม"
)


def toy_embed(text):
    """Word-level hash embedding (iter-05 style)."""
    DIM = 16
    tokens = text.split()
    vecs = []
    for t in tokens:
        seed = sum((i + 1) * ord(c) for i, c in enumerate(t))
        v = [((seed * (k + 7)) % 97) / 97 - 0.5 for k in range(DIM)]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        vecs.append([x / n for x in v])
    return [sum(v[d] for v in vecs) / len(vecs) for d in range(DIM)]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


raw_query_vec = toy_embed(RAW_QUERY)
hyde_vec = toy_embed(HYDE_FAKE_ANSWER)
real_doc_vec = toy_embed(REAL_DOC)

cos_raw_query = cosine(raw_query_vec, real_doc_vec)
cos_hyde = cosine(hyde_vec, real_doc_vec)

print("=== §29.2 HyDE: raw short query vs a fake-but-document-style answer ===")
print(f"raw query:  \"{RAW_QUERY}\"")
print(f"real doc:   \"{REAL_DOC[:50]}...\"")
print(f"cos(raw query, real doc) = {cos_raw_query:.4f}")
print(f"cos(HyDE fake answer, real doc) = {cos_hyde:.4f}  <- closer, even though it may be factually wrong")

# --- multi-query + RRF fuse (§29.3) -----------------------------------------
CORPUS = {
    "d_diabetes": REAL_DOC,
    "d_coffee": "สูตรกาแฟ cold brew กาแฟหยาบแช่เย็นสิบแปดชั่วโมง",
    "d_budget": "งบประมาณโครงการปีหน้าต้องขออนุมัติเพิ่ม",
}
QUERY_VARIANTS = [
    "เบาหวาน AI",                                    # the original, vague query
    "machine learning วินิจฉัยเบาหวาน",                  # variant 1: technical angle
    "HbA1c retinal ตรวจโรค",                          # variant 2: clinical-marker angle
]


def rank_docs(query_text):
    qvec = toy_embed(query_text)
    scores = {doc_id: cosine(qvec, toy_embed(text)) for doc_id, text in CORPUS.items()}
    return sorted(scores, key=lambda d: -scores[d])


def rrf_fuse(rank_lists, k=60):
    scores = {}
    for ranks in rank_lists:
        for pos, doc in enumerate(ranks, 1):
            scores[doc] = scores.get(doc, 0) + 1 / (k + pos)
    return sorted(scores, key=lambda d: -scores[d])


variant_ranks = [rank_docs(q) for q in QUERY_VARIANTS]
fused_rank = rrf_fuse(variant_ranks)

print(f"\n=== §29.3 multi-query: {len(QUERY_VARIANTS)} variants -> RRF fuse ===")
for q, ranks in zip(QUERY_VARIANTS, variant_ranks):
    print(f"  \"{q}\" -> top-1 = {ranks[0]}")
print(f"fused top-1 = {fused_rank[0]}")

# --- asserts -----------------------------------------------------------------
# 1. HyDE's fake answer must score CLOSER to the real doc than the raw
#    short query does -- the entire point of the trick (§29.2)
assert cos_hyde > cos_raw_query, \
    "HyDE's document-style fake answer must land closer to the real doc than the raw short query"

# 2. the gap must be real/substantial, not a rounding artifact
assert cos_hyde - cos_raw_query > 0.1, \
    "the HyDE advantage over the raw query must be a substantial, measurable gap"

# 3. multi-query fusion must correctly identify the diabetes doc as the
#    fused top-1, even though the original vague query alone might not be
#    the strongest signal by itself
assert fused_rank[0] == "d_diabetes", \
    "RRF-fused multi-query search must correctly surface the diabetes doc as top-1"

# 4. at least one query variant must independently rank the diabetes doc
#    #1 -- fusion works by combining REAL signal, not manufacturing it
assert any(ranks[0] == "d_diabetes" for ranks in variant_ranks), \
    "at least one query variant must independently find the correct doc for fusion to combine"

# 5. sanity: cosine values must be valid
assert -1.0 <= cos_raw_query <= 1.0
assert -1.0 <= cos_hyde <= 1.0

print("\n✓ all self-checks passed — HyDE's fake answer beats the raw query by living in 'document space'; multi-query+RRF covers more angles.")
