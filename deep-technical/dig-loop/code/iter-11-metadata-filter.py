"""Dig-loop 11/50 — Semantic search + metadata filter, together in one query.

Grounded in book/03-filter-metadata.md (real demo3_filter_metadata.py result:
semantic-only search let a DRAFT note and an OLD-YEAR note leak into the top
results; adding a metadata filter for folder=teaching, year=2026, draft=False
cut them out, leaving exactly the 2 notes that actually qualify).
Runnable standalone (stdlib only):  python iter-11-metadata-filter.py

Also demonstrates the §3.6 pitfall: pre-filtering (filter THEN rank) is safe;
naive post-filtering (rank top-k THEN filter) can silently return FEWER
results than actually exist, if a qualifying note doesn't make the initial
semantic top-k window.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


# --- 6-note vault, same shape as book/03's real demo3 ------------------------
# vector dims stand in for topic axes: [teaching, sql, research, finance]
NOTES = [
    {"id": "d1", "text": "แผนสอน vector search สำหรับ workshop",
     "vec": [0.95, 0.10, 0.0, 0.0], "folder": "teaching", "year": 2026, "draft": False},
    {"id": "d2", "text": "แผนสอน vector search ฉบับร่างแรก",
     "vec": [0.94, 0.12, 0.0, 0.0], "folder": "teaching", "year": 2026, "draft": True},
    {"id": "d3", "text": "โน้ตสอน SQL พื้นฐานปีที่แล้ว",
     "vec": [0.93, 0.20, 0.0, 0.0], "folder": "teaching", "year": 2025, "draft": False},
    {"id": "d4", "text": "งานวิจัย vector search เชิงลึก",
     "vec": [0.30, 0.00, 0.90, 0.0], "folder": "research", "year": 2026, "draft": False},
    {"id": "d5", "text": "บันทึกไอเดียสอน: ใช้เดโมก่อนค่อยลงสมการ",
     "vec": [0.80, 0.05, 0.0, 0.30], "folder": "teaching", "year": 2026, "draft": False},
    {"id": "d6", "text": "รายจ่ายเดือนนี้",
     "vec": [0.0, 0.0, 0.0, 1.0], "folder": "personal", "year": 2026, "draft": False},
]
QUERY = [1.0, 0.0, 0.0, 0.0]   # "การสอนเรื่องค้นหาด้วยความหมาย" (teaching-dominant)

WHERE = {"folder": "teaching", "year": 2026, "draft": False}


def matches(note, where):
    return all(note[k] == v for k, v in where.items())


def semantic_rank(notes, query):
    return sorted(notes, key=lambda n: -cosine(n["vec"], query))


def semantic_only_search(notes, query, k):
    return semantic_rank(notes, query)[:k]


def pre_filter_search(notes, query, where, k):
    """SAFE: filter first, then rank the survivors."""
    survivors = [n for n in notes if matches(n, where)]
    return semantic_rank(survivors, query)[:k]


def naive_post_filter_search(notes, query, where, k):
    """PITFALL (§3.6): rank top-k FIRST, filter afterward — can silently
    under-return even when enough qualifying notes exist elsewhere."""
    top_k_window = semantic_rank(notes, query)[:k]
    return [n for n in top_k_window if matches(n, where)]


raw_top3 = semantic_only_search(NOTES, QUERY, 3)
filtered_top3 = pre_filter_search(NOTES, QUERY, WHERE, 3)
naive_top3 = naive_post_filter_search(NOTES, QUERY, WHERE, 3)

print("=== 1) semantic ล้วน (top-3) ===")
for n in raw_top3:
    flag = "  <- draft!" if n["draft"] else ("  <- old year!" if n["year"] != 2026 else "")
    print(f"  {n['text']:<45} cos={cosine(n['vec'], QUERY):.3f}{flag}")

print("\n=== 2) semantic + filter (folder=teaching, year=2026, draft=False) ===")
for n in filtered_top3:
    print(f"  {n['text']:<45} cos={cosine(n['vec'], QUERY):.3f}")

print(f"\n=== 3) pitfall: naive post-filter with a k=2 window ===")
naive_k2 = naive_post_filter_search(NOTES, QUERY, WHERE, 2)
print(f"pre-filter (safe) top-2   -> {[n['id'] for n in pre_filter_search(NOTES, QUERY, WHERE, 2)]}")
print(f"post-filter (naive) top-2 -> {[n['id'] for n in naive_k2]}  <- under-returned!")

# --- asserts -----------------------------------------------------------------
# 1. semantic-only top-3 must leak the draft note AND the old-year note —
#    exactly the real symptom book/03 §3.4 demonstrates
raw_ids = [n["id"] for n in raw_top3]
assert "d2" in raw_ids, "semantic-only search must let the DRAFT note leak into top-3 (unfiltered)"
assert "d3" in raw_ids, "semantic-only search must let the OLD-YEAR note leak into top-3 (unfiltered)"

# 2. pre-filtered search must contain ONLY notes matching the where clause
for n in filtered_top3:
    assert matches(n, WHERE), f"{n['id']} does not satisfy the metadata filter but was returned"

# 3. the filtered result must be EXACTLY {d1, d5} — the two real qualifiers
#    from book/03's demo (แผนสอนจริง + ไอเดียสอน), nothing more, nothing less
assert {n["id"] for n in filtered_top3} == {"d1", "d5"}, \
    "pre-filtered search must return exactly the qualifying notes d1 and d5"

# 4. §3.6 pitfall: a NAIVE post-filter with a tight k window must under-return
#    compared to the safe pre-filter approach, even though the same 2 notes
#    qualify in the full corpus
safe_k2_ids = {n["id"] for n in pre_filter_search(NOTES, QUERY, WHERE, 2)}
naive_k2_ids = {n["id"] for n in naive_k2}
assert len(naive_k2_ids) < len(safe_k2_ids), \
    "naive post-filter (rank-then-filter) with a tight window must return FEWER results than pre-filter"

# 5. filtering must never ADD a note that wasn't semantically ranked at all
assert naive_k2_ids.issubset({n["id"] for n in NOTES})

print("\n✓ all self-checks passed — semantic finds 'related', filter cuts 'ineligible'; filter BEFORE ranking, not after.")
