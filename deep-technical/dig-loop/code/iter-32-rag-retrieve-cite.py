"""Dig-loop 32/50 — RAG: retrieve (threshold + source) -> generate (ground + cite + abstain).

Grounded in book/09-rag-cite.md §9.2 (two rules beginners miss: (1) ANN
always returns top-k EVEN with nothing relevant -- must gate on a threshold,
never feed junk to the LLM; (2) attach `source` to every retrieved chunk so
the LLM can cite it) and §9.4/§9.5 (real result: in-vault query gets a
grounded, cited answer; out-of-vault query gets 0 results past threshold ->
"ไม่พบข้อมูลเรื่องนี้ใน vault ครับ" -- abstain, never fed to the LLM at all).
Runnable standalone (stdlib only):  python iter-32-rag-retrieve-cite.py

The "generate" step here is a deterministic stand-in (no real LLM call) that
mechanically grounds+cites from the retrieved context -- enough to prove the
RAG PIPELINE's shape (retrieve->threshold->cite->abstain), which is the
actual point, not simulating language generation itself.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math

VAULT = [
    {"id": "d1", "source": "workshop-plan.md",
     "text": "Workshop วันที่ 26 กรกฎาคม ต้องเตรียมโน้ตบุ๊กติดตั้ง Python และ Jupyter ล่วงหน้า",
     "vec": [0.90, 0.10, 0.0, 0.0]},
    {"id": "d2", "source": "coffee-notes.md",
     "text": "สูตรกาแฟ cold brew: กาแฟ 100g น้ำ 1L แช่ 18 ชั่วโมง",
     "vec": [0.0, 0.95, 0.0, 0.0]},
    {"id": "d3", "source": "budget-2026.md",
     "text": "งบประมาณโครงการปีหน้าต้องขออนุมัติเพิ่มอีก 15%",
     "vec": [0.0, 0.0, 0.95, 0.0]},
]

THRESHOLD = 0.45   # book/09 §9.2's abstain threshold


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def retrieve(query_vec, threshold=THRESHOLD, k=3):
    """Rule 1 (§9.2): score, THEN drop anything below threshold. ANN always
    returns top-k -- gating happens here, not inside the search itself."""
    scored = [(doc, cosine(query_vec, doc["vec"])) for doc in VAULT]
    scored.sort(key=lambda x: -x[1])
    return [(doc, s) for doc, s in scored[:k] if s >= threshold]


def build_context(results):
    """Rule 2 (§9.2): every chunk carries its `source` for citation."""
    return [f"[{doc['source']}] {doc['text']}" for doc, _ in results]


def generate(query_text, results):
    """Deterministic stand-in for an LLM: ground + cite + abstain (§9.5's
    3-line prompt: ห้ามเดา / อ้างอิงไฟล์ / บอกว่าไม่พบ)."""
    if not results:
        return "ไม่พบข้อมูลเรื่องนี้ใน vault ครับ"
    context = build_context(results)
    best_doc, best_score = results[0]
    return f"{best_doc['text']} ({best_doc['source']})"


def rag_answer(query_text, query_vec, threshold=THRESHOLD):
    results = retrieve(query_vec, threshold)
    return generate(query_text, results), results


# --- query 1: clearly in-vault (workshop) -----------------------------------
q1_text = "workshop วันไหน แล้วต้องเตรียมอะไรบ้าง"
q1_vec = [0.88, 0.12, 0.0, 0.0]
answer1, results1 = rag_answer(q1_text, q1_vec)
print(f"Q: {q1_text}")
print(f"🤖 {answer1}")

# --- query 2: clearly out-of-vault (stock prices) ---------------------------
q2_text = "ราคาหุ้นวันนี้เป็นยังไง"
q2_vec = [0.0, 0.0, 0.0, 0.0]   # shares nothing with any doc axis
answer2, results2 = rag_answer(q2_text, q2_vec)
print(f"\nQ: {q2_text}")
print(f"🤖 {answer2}")
print(f"   (retrieval returned {len(results2)} chunks past threshold -- LLM never even sees the vault)")

# --- query 3: the "closest available ≠ related" trap (iter-09) -------------
q3_text = "เงินเฟ้อปีนี้เป็นยังไงบ้าง"
q3_vec = [0.05, 0.05, 0.15, 0.90]   # mostly noise (4th axis) with a faint budget lean (iter-09's "lonely word" pattern)
low_threshold_results = retrieve(q3_vec, threshold=0.0)     # no gating at all
high_threshold_results = retrieve(q3_vec, threshold=THRESHOLD)
print(f"\nQ: {q3_text}")
print(f"  threshold=0.0  -> {[d['source'] for d,_ in low_threshold_results]}  (junk slips through!)")
print(f"  threshold={THRESHOLD} -> {[d['source'] for d,_ in high_threshold_results]}  (correctly filtered)")

# --- asserts -----------------------------------------------------------------
# 1. in-vault query must retrieve the correct doc AND cite its real source
assert results1[0][0]["source"] == "workshop-plan.md", "the workshop query must retrieve workshop-plan.md"
assert "workshop-plan.md" in answer1, "the generated answer must cite the real source filename"

# 2. out-of-vault query must retrieve ZERO chunks past threshold -- the LLM
#    must never be fed anything to hallucinate from
assert len(results2) == 0, "an out-of-vault query must retrieve 0 chunks above threshold"
assert answer2 == "ไม่พบข้อมูลเรื่องนี้ใน vault ครับ", "with 0 retrieved chunks, the system must abstain exactly"

# 3. without a threshold, a weak/irrelevant match CAN slip through (junk) --
#    proving the threshold gate is what actually prevents bad grounding
assert len(low_threshold_results) > 0, "with no threshold gate, even a weak match must be returned (the real risk)"
assert low_threshold_results[0][1] < THRESHOLD, \
    "the weak match that slips through at threshold=0 must genuinely score below the real threshold"

# 4. with the real threshold applied, that same weak match must be filtered out
assert len(high_threshold_results) == 0, \
    "with the threshold applied, the weak/irrelevant match must be correctly rejected"

# 5. every context line built for the LLM must contain its source in brackets
#    (citation format from §9.2 rule 2)
ctx = build_context(results1)
assert all(line.startswith("[") and "]" in line for line in ctx), \
    "every context chunk fed to generate() must carry a [source.md] citation prefix"

print("\n✓ all self-checks passed — retrieve+threshold+cite; 0 chunks past threshold = abstain, never feed junk to the LLM.")
