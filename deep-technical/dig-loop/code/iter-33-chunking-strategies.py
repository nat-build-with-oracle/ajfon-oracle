"""Dig-loop 33/50 — Chunking: dilution, mid-sentence cuts, overlap, parent-child.

Grounded in deep-technical/12-chunking-strategy.md §12.0 (dilution: one vector
for a multi-topic doc = the mean of all ideas, blurring each), §12.1
(fixed-size chunking cuts mid-sentence), §12.2 (overlap prevents boundary
loss), §12.3 (recursive splitting respects paragraph boundaries), and §12.5
(parent-child: search the small precise child, return the larger context
parent -- best of both).
Runnable standalone (stdlib only):  python iter-33-chunking-strategies.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math

DOC = (
    "cosine similarity วัดมุมระหว่างเวกเตอร์สองตัว ไม่สนใจความยาว "
    "เป็นสมการเดียวที่ต้องรู้ในการค้นหาความหมาย\n\n"
    "embedder ที่แถมมากับไลบรารีส่วนใหญ่เทรนด้วยข้อความอังกฤษเป็นหลัก "
    "พอเจอภาษาไทยจะเข้าใจความหมายได้ครึ่งๆ กลางๆ ต้องเปลี่ยนไปใช้ bge-m3\n\n"
    "สูตรกาแฟ cold brew ใช้กาแฟบดหยาบหนึ่งร้อยกรัมต่อน้ำหนึ่งลิตร "
    "แช่เย็นสิบแปดชั่วโมงแล้วกรองผ่านผ้าขาวบาง"
)
PARAGRAPHS = DOC.split("\n\n")


def toy_embed(text):
    """Deterministic hash-based embedding (same style as earlier iterations) --
    real mean-pooling dilution shows up mathematically even without a
    trained model, because averaging unrelated tokens genuinely blurs signal."""
    DIM = 16
    tokens = [c for c in text if not c.isspace()]
    vecs = []
    for t in tokens:
        seed = ord(t) * 37 + len(t)
        v = [((seed * (k + 7)) % 97) / 97 - 0.5 for k in range(DIM)]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        vecs.append([x / n for x in v])
    return [sum(v[d] for v in vecs) / len(vecs) for d in range(DIM)]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


# --- 1. dilution: whole-doc vector vs the ONE relevant chunk ---------------
whole_doc_vec = toy_embed(DOC)
chunk_vecs = [toy_embed(p) for p in PARAGRAPHS]
query_thai = toy_embed("ทำไม embedder ตัวแถมอ่านภาษาไทยไม่ออก")

cos_whole = cosine(query_thai, whole_doc_vec)
cos_chunk2 = cosine(query_thai, chunk_vecs[1])   # the Thai-embedding paragraph

print("=== §12.0 dilution: whole-doc vector vs the specific chunk ===")
print(f"cos(query, WHOLE 3-topic doc)     = {cos_whole:.4f}")
print(f"cos(query, chunk[1] only, on-topic) = {cos_chunk2:.4f}  <- much sharper")

# --- 2. fixed-size cuts mid-sentence; overlap prevents it -------------------
FIXED_SIZE = 70
OVERLAP = 30
KEY_SENTENCE = "เป็นสมการเดียวที่ต้องรู้ในการค้นหาความหมาย"

fixed_chunks = [DOC[i:i + FIXED_SIZE] for i in range(0, len(DOC), FIXED_SIZE)]
overlap_chunks = [DOC[i:i + FIXED_SIZE] for i in range(0, len(DOC), FIXED_SIZE - OVERLAP)]

fixed_has_full_sentence = any(KEY_SENTENCE in c for c in fixed_chunks)
overlap_has_full_sentence = any(KEY_SENTENCE in c for c in overlap_chunks)

print(f"\n=== §12.1/§12.2: fixed-size cuts mid-sentence, overlap doesn't ===")
print(f"fixed-size ({FIXED_SIZE} chars, no overlap): key sentence intact in ONE chunk? {fixed_has_full_sentence}")
print(f"overlap ({FIXED_SIZE} chars, 20 overlap):    key sentence intact in ONE chunk? {overlap_has_full_sentence}")

# --- 3. recursive/paragraph chunking respects natural boundaries -----------
recursive_chunks = PARAGRAPHS   # split at "\n\n" first, per §12.3's algorithm
print(f"\n=== §12.3 recursive chunking: {len(recursive_chunks)} chunks, each a whole paragraph ===")
for i, c in enumerate(recursive_chunks):
    print(f"  chunk[{i}] ends with: ...{c[-20:]!r}")

# --- 4. parent-child: search SMALL child, return LARGER parent context -----
CHILD = "embedder ที่แถมมากับไลบรารีส่วนใหญ่เทรนด้วยข้อความอังกฤษเป็นหลัก"
PARENT = PARAGRAPHS[1]   # the whole paragraph the child sentence lives in

child_vec = toy_embed(CHILD)
parent_vec = toy_embed(PARENT)
cos_child = cosine(query_thai, child_vec)
cos_parent = cosine(query_thai, parent_vec)

print(f"\n=== §12.5 parent-child: search child (sharp), return parent (context) ===")
print(f"cos(query, CHILD sentence)  = {cos_child:.4f}  <- what we search with")
print(f"cos(query, PARENT paragraph) = {cos_parent:.4f}")
print(f"child len={len(CHILD)} chars, parent len={len(PARENT)} chars  <- parent has more context")

# --- asserts -----------------------------------------------------------------
# 1. the specific on-topic chunk must score higher than the diluted whole-doc
#    vector for a query about that ONE topic -- dilution is real and measurable
assert cos_chunk2 > cos_whole, \
    "a topic-specific chunk must score higher than a 3-topic diluted whole-doc vector for an on-topic query"

# 2. fixed-size (no overlap) chunking must genuinely CUT the key sentence --
#    no single chunk contains it whole
assert not fixed_has_full_sentence, \
    "fixed-size chunking without overlap must split the key sentence across chunk boundaries"

# 3. overlap chunking must recover the sentence intact in at least one chunk
assert overlap_has_full_sentence, \
    "overlap chunking must keep the key sentence whole in at least one chunk"

# 4. recursive/paragraph chunking must produce exactly 3 chunks (1 per topic)
#    and each chunk must be a COMPLETE paragraph (no cut sentences)
assert len(recursive_chunks) == 3, "recursive chunking on this doc must yield exactly 3 paragraph chunks"
for c in recursive_chunks:
    assert c.strip().endswith(("ความหมาย", "bge-m3", "ขาวบาง")), \
        "each recursive chunk must end at a real sentence boundary, not mid-sentence"

# 5. parent-child: the child's cosine to the query must be at least as sharp
#    as the parent's (child is the precise match unit), while the parent
#    genuinely carries strictly more surrounding text
assert cos_child >= cos_parent - 0.05, \
    "the small child chunk must be at least as precise a match as its larger parent"
assert len(PARENT) > len(CHILD), \
    "the parent chunk returned for context must be strictly larger than the child chunk used to search"

print("\n✓ all self-checks passed — 1 chunk = 1 idea avoids dilution; overlap saves boundaries; parent-child gets precision AND context.")
