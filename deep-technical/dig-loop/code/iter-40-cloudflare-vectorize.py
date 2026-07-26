"""Dig-loop 40/50 — Vectorize's eventual consistency: upsert != instantly queryable.

Grounded in deep-technical/14-vectorize-d1-edge-internals.md §14.4 (Vectorize
upsert is EVENTUALLY consistent -- async index build -- unlike LanceDB local
which is read-after-write; "implication: bulk index แล้วต้องรอ index settle
ก่อนวัด parity") and §14.5 (LanceDB local vs Vectorize edge comparison table:
consistency is the key structural difference, everything else being adapter-
pattern-hidden, iter-31/§14.3).
Runnable standalone (stdlib only):  python iter-40-cloudflare-vectorize.py

This demo builds two tiny vector stores sharing the same interface (adapter
pattern) but differing in EXACTLY this one property, to make the "you must
wait for settle before measuring parity" warning concrete and provable.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


class LocalVectorStore:
    """LanceDB-style: read-after-write, always consistent (§14.5)."""
    def __init__(self):
        self._index = {}

    def upsert(self, doc_id, vector):
        self._index[doc_id] = vector   # visible to query() immediately

    def query(self, qvec, k=3):
        scored = [(doc_id, cosine(qvec, v)) for doc_id, v in self._index.items()]
        return sorted(scored, key=lambda x: -x[1])[:k]


class EdgeVectorStore:
    """Vectorize-style: upsert lands in a PENDING queue -- not visible to
    query() until settle() runs (§14.4's "async index build")."""
    def __init__(self):
        self._index = {}
        self._pending = {}

    def upsert(self, doc_id, vector):
        self._pending[doc_id] = vector   # NOT visible yet

    def settle(self):
        """Simulates waiting for CF's async index build to finish."""
        self._index.update(self._pending)
        self._pending.clear()

    def query(self, qvec, k=3):
        scored = [(doc_id, cosine(qvec, v)) for doc_id, v in self._index.items()]
        return sorted(scored, key=lambda x: -x[1])[:k]


# --- both stores start with the same 3 pre-existing docs -------------------
EXISTING_DOCS = {
    "d1": [0.1, 0.1, 0.9],
    "d2": [0.9, 0.1, 0.1],
    "d3": [0.1, 0.9, 0.1],
}

local_store = LocalVectorStore()
edge_store = EdgeVectorStore()
for doc_id, vec in EXISTING_DOCS.items():
    local_store.upsert(doc_id, vec)
    edge_store.upsert(doc_id, vec)
edge_store.settle()   # pretend these were already settled long ago

# --- NOW: upsert a brand-new, highly relevant doc into BOTH stores ---------
NEW_DOC_VEC = [0.95, 0.05, 0.05]
QUERY_VEC = [0.9, 0.1, 0.1]   # should clearly match the new doc AND d2

local_store.upsert("new_doc", NEW_DOC_VEC)
edge_store.upsert("new_doc", NEW_DOC_VEC)

# --- query IMMEDIATELY, before Vectorize's index has had time to settle ----
local_immediate = local_store.query(QUERY_VEC, k=3)
edge_immediate = edge_store.query(QUERY_VEC, k=3)

print("=== querying IMMEDIATELY after upsert ===")
print(f"LocalVectorStore (read-after-write): {local_immediate}")
print(f"EdgeVectorStore  (eventual consistency): {edge_immediate}")
print(f"'new_doc' found in local?  {'new_doc' in [d for d, _ in local_immediate]}")
print(f"'new_doc' found in edge?   {'new_doc' in [d for d, _ in edge_immediate]}  <- missing! (still pending)")

# --- now settle the edge store and query again ------------------------------
edge_store.settle()
edge_after_settle = edge_store.query(QUERY_VEC, k=3)

print(f"\n=== after calling settle() (waiting for index build) ===")
print(f"EdgeVectorStore (settled): {edge_after_settle}")
print(f"'new_doc' found now?      {'new_doc' in [d for d, _ in edge_after_settle]}")

print(f"\nreal implication (§14.4): measuring drift/parity (iter-39) RIGHT AFTER a bulk")
print(f"upsert to Vectorize would show FALSE degradation -- not real embedding drift,")
print(f"just eventual-consistency lag. Wait for settle() before trusting the numbers.")

# --- asserts -----------------------------------------------------------------
# 1. LocalVectorStore must show read-after-write consistency -- the new doc
#    is queryable IMMEDIATELY after upsert, no waiting needed
assert "new_doc" in [d for d, _ in local_immediate], \
    "LocalVectorStore (LanceDB-style) must show the new doc immediately after upsert"

# 2. EdgeVectorStore must NOT show the new doc immediately -- this IS the
#    real eventual-consistency gotcha the book warns about
assert "new_doc" not in [d for d, _ in edge_immediate], \
    "EdgeVectorStore (Vectorize-style) must NOT show the new doc before settle() -- eventual consistency"

# 3. after settle(), the edge store MUST show the new doc -- consistency
#    catches up, it's just delayed, not broken
assert "new_doc" in [d for d, _ in edge_after_settle], \
    "EdgeVectorStore must show the new doc AFTER settle() completes"

# 4. the settled edge store's top-3 must now MATCH the local store's top-3
#    exactly -- proving this is purely a timing issue, not a real difference
#    in the underlying data or algorithm
local_ids = [d for d, _ in local_immediate]
edge_settled_ids = [d for d, _ in edge_after_settle]
assert set(local_ids) == set(edge_settled_ids), \
    "once settled, edge and local stores must agree on the same top-3 -- confirming it was ONLY a consistency delay"

# 5. both stores must implement the SAME interface (adapter pattern, §14.3/
#    iter-31) -- caller code (upsert/query calls above) never branched on
#    which store it was talking to
assert hasattr(local_store, "upsert") and hasattr(local_store, "query")
assert hasattr(edge_store, "upsert") and hasattr(edge_store, "query")

print("\n✓ all self-checks passed — Vectorize's eventual consistency is real; measure parity AFTER settle(), never right after bulk upsert.")
