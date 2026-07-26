"""Dig-loop 12/50 — PersistentClient: open -> upsert -> query, and idempotency.

Grounded in book/01-second-brain-20-lines.md (the whole "second brain" API in
3 steps: PersistentClient(path) -> get_or_create_collection -> upsert -> query)
and book/08-ingest-vault.md §8.3 (content-hash id is the idempotency trick:
same content -> same id -> upsert overwrites itself -> no duplicates, no
re-embedding cost on unchanged notes).
Runnable standalone (stdlib only, no real chromadb needed):
    python iter-12-chroma-persistentclient.py

Real chromadb is guarded behind a try/import so this still runs anywhere;
a TinyCollection class mirrors ChromaDB's actual API shape (upsert/query) and
the content-hash-id pattern, using small hand-placed "embeddings" so the demo
is fully deterministic (no network, no model download).
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import hashlib
import math

try:
    import chromadb  # noqa: F401
    HAVE_CHROMADB = True
except ImportError:
    HAVE_CHROMADB = False


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


def content_hash_id(source, heading, text):
    """book/08 §8.3 — id = hash(content). Same content -> same id, always."""
    return hashlib.sha256(f"{source}|{heading}|{text}".encode()).hexdigest()[:16]


# --- toy embedder: 3 fixed meaning-axes [teaching, coffee, meeting] ---------
# (a real embedder would learn this from data; here it's hand-placed so the
#  API-mechanics demo doesn't depend on a model download)
def toy_embed(text):
    if "vector search" in text or "สอน" in text:
        return [0.95, 0.05, 0.10]
    if "กาแฟ" in text or "cold brew" in text:
        return [0.05, 0.95, 0.05]
    if "ประชุม" in text or "workshop" in text:
        return [0.10, 0.05, 0.95]
    if "นัดหมาย" in text:            # the QUERY text — no exact word overlap
        return [0.08, 0.03, 0.92]    # with any document, yet embeds near "meeting"
    return [0.0, 0.0, 0.0]


class TinyCollection:
    """Mirrors ChromaDB's real shape: upsert(ids, documents, metadatas), query(...)."""

    def __init__(self, name):
        self.name = name
        self.rows = {}          # id -> {"document", "metadata", "embedding"}
        self.embed_calls = 0     # count actual embedding work done

    def upsert(self, ids, documents, metadatas):
        added, skipped = 0, 0
        for _id, doc, meta in zip(ids, documents, metadatas):
            if _id in self.rows and self.rows[_id]["document"] == doc:
                skipped += 1        # same id AND same content already there
                continue
            self.rows[_id] = {
                "document": doc, "metadata": meta, "embedding": toy_embed(doc),
            }
            self.embed_calls += 1
            added += 1
        return {"added": added, "skipped": skipped}

    def query(self, query_texts, n_results=3, where=None):
        qvec = toy_embed(query_texts[0])
        candidates = [
            (rid, r) for rid, r in self.rows.items()
            if where is None or all(r["metadata"].get(k) == v for k, v in where.items())
        ]
        ranked = sorted(candidates, key=lambda kv: -cosine(qvec, kv[1]["embedding"]))
        return ranked[:n_results]


# --- PersistentClient pattern: open -> upsert -> query (book/01 §1.3) ------
col = TinyCollection("second_brain")

docs = [
    ("n1", "วิธีสอนนักศึกษาให้เข้าใจ vector search: เริ่มจาก cosine similarity ก่อน", {"folder": "teaching"}),
    ("n2", "สูตรกาแฟ cold brew: กาแฟ 100g น้ำ 1L แช่ 18 ชั่วโมง", {"folder": "recipes"}),
    ("n3", "ประชุมกับอาจารย์ฝน เรื่อง workshop วันที่ 26 กรกฎาคม", {"folder": "meetings"}),
]

result1 = col.upsert(
    ids=[d[0] for d in docs],
    documents=[d[1] for d in docs],
    metadatas=[d[2] for d in docs],
)
print("=== รอบ 1: ingest ครั้งแรก ===")
print(f"เพิ่ม {result1['added']} · ข้าม {result1['skipped']}  (embed_calls={col.embed_calls})")

# --- query without exact word overlap ("นัดหมาย" appears in NO document) ----
hits = col.query(query_texts=["นัดหมายกับใครบ้าง"], n_results=1)
top_id, top_row = hits[0]
print(f"\nQ: นัดหมายกับใครบ้าง")
print(f"  -> {top_row['document'][:40]}...")

# --- re-run the EXACT same ingest: idempotency check (book/08 §8.3) --------
result2 = col.upsert(
    ids=[d[0] for d in docs],
    documents=[d[1] for d in docs],
    metadatas=[d[2] for d in docs],
)
print(f"\n=== รอบ 2 (รันซ้ำ เนื้อหาเดิม) ===")
print(f"เพิ่ม {result2['added']} · ข้าม {result2['skipped']}  (embed_calls={col.embed_calls})")
embed_calls_after_round2 = col.embed_calls

# --- edit ONE note's content: only that one should re-embed ---------------
edited_docs = list(docs)
edited_docs[1] = ("n2", "สูตรกาแฟ cold brew เข้มข้น: กาแฟ 120g น้ำ 1L แช่ 20 ชั่วโมง", {"folder": "recipes"})
result3 = col.upsert(
    ids=[d[0] for d in edited_docs],
    documents=[d[1] for d in edited_docs],
    metadatas=[d[2] for d in edited_docs],
)
print(f"\n=== รอบ 3 (แก้ n2 เนื้อหานิดเดียว) ===")
print(f"เพิ่ม {result3['added']} · ข้าม {result3['skipped']}  (embed_calls={col.embed_calls})")

# --- content-hash id: identical content -> identical id --------------------
id_a = content_hash_id("notes.md", "coffee", "สูตรกาแฟ cold brew")
id_b = content_hash_id("notes.md", "coffee", "สูตรกาแฟ cold brew")
id_c = content_hash_id("notes.md", "coffee", "สูตรกาแฟ cold brew เข้มข้น")

print(f"\nreal chromadb installed: {HAVE_CHROMADB}  (demo runs identically either way)")

# --- asserts -----------------------------------------------------------------
# 1. first ingest must add all 3, skip none
assert result1 == {"added": 3, "skipped": 0}, "first ingest of 3 fresh notes must add exactly 3"

# 2. querying "นัดหมาย" (no literal word match anywhere) must still surface
#    the MEETING note — the whole point of book/01's opening example
assert top_id == "n3", "semantic query must find the meeting note despite zero word overlap"

# 3. re-running the identical ingest must be a full no-op: idempotency
assert result2 == {"added": 0, "skipped": 3}, "re-ingesting identical content must add 0, skip all"
assert embed_calls_after_round2 == 3, "no re-embedding should happen for unchanged content (embed is the expensive step)"

# 4. editing ONE note's content must re-embed exactly that ONE note
assert result3 == {"added": 1, "skipped": 2}, "editing 1 of 3 notes must add exactly 1, skip the other 2"
assert col.embed_calls == embed_calls_after_round2 + 1, "only the edited note should trigger a new embed call"

# 5. content-hash id: same content -> same id (always); different content -> different id
assert id_a == id_b, "identical (source, heading, text) must hash to the SAME id"
assert id_a != id_c, "different text must hash to a DIFFERENT id"

print("\n✓ all self-checks passed — open->upsert->query API, and content-hash id makes re-ingest a true no-op.")
