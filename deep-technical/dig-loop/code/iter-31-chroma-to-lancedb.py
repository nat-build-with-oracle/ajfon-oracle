"""Dig-loop 31/50 — Migrating ChromaDB -> LanceDB: same math, different engine.

Grounded in book/10-chroma-to-lancedb.md (real ARRA history: started with
FTS5+ChromaDB Dec 2025, later moved to LanceDB -- NOT because Chroma was
"bad", but because ARRA is a Bun/TypeScript app and LanceDB's Rust core
embeds directly with no Python sidecar needed. Real measured comparison on
the SAME 200-chunk corpus: ingest Chroma=44ms/LanceDB=10ms, query
Chroma=1.3ms/LanceDB=2.2ms -- "ต่างกันไม่มีนัย" at this scale, top-1 identical)
and deep-technical/04 §4.1 (adapter pattern: swap backend via config, caller
code never changes).
Runnable standalone (stdlib only):  python iter-31-chroma-to-lancedb.py

Book/10's biggest lesson (§10.4): "ทุกอย่างที่เรียนมา (embedding, cosine,
hybrid, eval) ติดตัวคุณ ไม่ติดเครื่องมือ" -- the KNOWLEDGE travels, the tool
is swappable. This demo proves it: two DIFFERENT adapter implementations,
identical top-1 results, identical caller code.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


class VectorStoreAdapter:
    """The common interface (deep-technical/04 §4.1) -- every backend
    implements the SAME shape so caller code never has to change."""
    def upsert(self, rows):
        raise NotImplementedError

    def search(self, query_vec, k=3):
        raise NotImplementedError


class ChromaAdapter(VectorStoreAdapter):
    """Python-first, embedded, dict-of-rows storage (book/10 §10.3)."""
    def __init__(self):
        self._rows = {}

    def upsert(self, rows):
        for r in rows:
            self._rows[r["id"]] = r

    def search(self, query_vec, k=3):
        scored = [(rid, cosine(query_vec, r["vector"])) for rid, r in self._rows.items()]
        return sorted(scored, key=lambda x: -x[1])[:k]


class LanceDBAdapter(VectorStoreAdapter):
    """Rust-core, columnar (iter-28), embeds directly in a non-Python
    runtime -- storage representation differs, but the SAME cosine math."""
    def __init__(self):
        self._ids = []
        self._vectors = []   # columnar: vectors live in their own array

    def upsert(self, rows):
        for r in rows:
            if r["id"] in self._ids:
                idx = self._ids.index(r["id"])
                self._vectors[idx] = r["vector"]
            else:
                self._ids.append(r["id"])
                self._vectors.append(r["vector"])

    def search(self, query_vec, k=3):
        scored = [(rid, cosine(query_vec, vec)) for rid, vec in zip(self._ids, self._vectors)]
        return sorted(scored, key=lambda x: -x[1])[:k]


def get_adapter(backend_name):
    """Config-driven backend selection (like ORACLE_VECTOR_BACKEND env var,
    deep-technical/04 §4.1) -- caller code below never inspects which one."""
    return {"chroma": ChromaAdapter, "lancedb": LanceDBAdapter}[backend_name]()


def run_query(adapter, query_vec, k=3):
    """Backend-agnostic caller: works identically no matter WHICH adapter
    was constructed -- this function contains ZERO backend-specific code."""
    return adapter.search(query_vec, k)


CORPUS = [
    {"id": "n1", "vector": [0.9, 0.1, 0.0]},   # meeting-like
    {"id": "n2", "vector": [0.1, 0.9, 0.0]},   # coffee-like
    {"id": "n3", "vector": [0.0, 0.1, 0.9]},   # finance-like
    {"id": "n4", "vector": [0.85, 0.15, 0.05]},  # meeting-adjacent
]
QUERIES = [
    [0.88, 0.12, 0.0],    # should favor n1/n4 (meeting)
    [0.05, 0.95, 0.0],    # should favor n2 (coffee)
    [0.0, 0.0, 1.0],      # should favor n3 (finance)
]

chroma = get_adapter("chroma")
lancedb = get_adapter("lancedb")
chroma.upsert(CORPUS)
lancedb.upsert(CORPUS)

print("=== same corpus, both backends, same caller function ===")
all_match = True
for q in QUERIES:
    chroma_result = run_query(chroma, q, k=1)
    lancedb_result = run_query(lancedb, q, k=1)
    match = chroma_result[0][0] == lancedb_result[0][0]
    all_match = all_match and match
    print(f"query={q}  chroma top-1={chroma_result[0][0]}  lancedb top-1={lancedb_result[0][0]}  {'✓' if match else '✗'}")

print(f"\nbook/10's real numbers (200 chunks, same bge-m3): "
      f"ingest Chroma=44ms/LanceDB=10ms, query Chroma=1.3ms/LanceDB=2.2ms, top-1 ตรงกันเป๊ะ")
print("real decision driver: runtime fit (Rust-embeddable for Bun/TS), NOT raw speed")

# --- asserts -----------------------------------------------------------------
# 1. every query must produce the IDENTICAL top-1 doc across both backends --
#    the book's actual self-check requirement (§10.4)
for q in QUERIES:
    chroma_top1 = run_query(chroma, q, k=1)[0][0]
    lancedb_top1 = run_query(lancedb, q, k=1)[0][0]
    assert chroma_top1 == lancedb_top1, \
        f"migrating backend must NOT change the top-1 result for query {q}"

assert all_match, "all queries must match between ChromaAdapter and LanceDBAdapter"

# 2. both adapters must implement the SAME interface -- caller code must
#    work with either without any backend-specific branching
assert isinstance(chroma, VectorStoreAdapter) and isinstance(lancedb, VectorStoreAdapter), \
    "both backends must implement the common VectorStoreAdapter interface"

# 3. the caller function must be usable with EITHER adapter, unmodified --
#    verify by calling it generically over both instances in a loop
for adapter in (chroma, lancedb):
    result = run_query(adapter, QUERIES[0], k=2)
    assert len(result) == 2, "run_query must behave identically regardless of which adapter instance is passed"

# 4. re-upserting the SAME row (id already present) must update it, not
#    duplicate it -- correctness must hold on BOTH backends after a repeat write
chroma.upsert([{"id": "n1", "vector": [0.5, 0.5, 0.5]}])
lancedb.upsert([{"id": "n1", "vector": [0.5, 0.5, 0.5]}])
assert len(chroma._rows) == 4, "upserting an existing id on Chroma must update in place, not duplicate"
assert len(lancedb._ids) == 4, "upserting an existing id on LanceDB must update in place, not duplicate"

print("\n✓ all self-checks passed — swap the backend, keep the math: top-1 identical, same caller code either way.")
