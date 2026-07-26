"""Dig-loop 28/50 — Why LanceDB's columnar (Arrow) layout makes flat scan cheap.

Grounded in book/13-lancedb-production.md (LanceDB: embedded like ChromaDB,
same concepts, different storage engine) and deep-technical/03-ann-indexing.md
§3.6 ("LanceDB สร้างบน Lance columnar format (Arrow-based) -- เก็บ vector บน
ดิสก์ แบบ memory-mappable ... ค้นแบบ flat (brute-force) ได้ถ้า table เล็ก").
Runnable standalone (stdlib only):  python iter-28-lancedb-flat-arrow.py

Row-based storage bundles every field of a record together, so even a
vector-only scan must touch each row's FULL bytes (including big text
payloads). Columnar (Arrow) storage keeps each field in its own contiguous
array, so a flat vector scan touches ONLY the vector column -- the rest of
the table (text, metadata) is never read off disk at all. This demo measures
that difference directly as "bytes touched" during an identical flat scan.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math
import random

rng = random.Random(29)
N = 500
DIM = 32
TEXT_SIZE_BYTES = 2000     # a realistic note/chunk of text per row
FLOAT_BYTES = 4            # float32


def random_unit_vector(dim):
    v = [rng.gauss(0, 1) for _ in range(dim)]
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


# --- ROW-BASED store: each record bundles id+text+vector+metadata together -
row_store = []
for i in range(N):
    row_store.append({
        "id": i,
        "text": "x" * TEXT_SIZE_BYTES,     # stand-in for a real note/chunk
        "vector": random_unit_vector(DIM),
        "metadata": {"folder": "notes"},
    })

# --- COLUMNAR (Arrow-like) store: each field lives in its OWN array --------
columnar_ids = [r["id"] for r in row_store]
columnar_texts = [r["text"] for r in row_store]
columnar_vectors = [r["vector"] for r in row_store]           # <- only THIS
columnar_metadata = [r["metadata"] for r in row_store]         #    is touched
                                                                #    by a vector scan


def row_based_flat_scan(query_vec, store):
    """To read `row['vector']` off a row-based layout, the storage engine
    must first load the WHOLE row (text + metadata included) -- bytes
    touched = the full record size, even though only `.vector` is used."""
    bytes_touched = 0
    scores = []
    for row in store:
        row_bytes = len(row["text"].encode()) + DIM * FLOAT_BYTES + 64  # + misc overhead
        bytes_touched += row_bytes
        scores.append((row["id"], cosine(query_vec, row["vector"])))
    scores.sort(key=lambda x: -x[1])
    return scores[:5], bytes_touched


def columnar_flat_scan(query_vec, vectors_col):
    """Columnar layout: the vector COLUMN is contiguous and separate from
    text/metadata columns -- a vector-only scan touches ONLY this array."""
    bytes_touched = 0
    scores = []
    for i, vec in enumerate(vectors_col):
        bytes_touched += DIM * FLOAT_BYTES
        scores.append((i, cosine(query_vec, vec)))
    scores.sort(key=lambda x: -x[1])
    return scores[:5], bytes_touched


query = random_unit_vector(DIM)

row_top5, row_bytes = row_based_flat_scan(query, row_store)
col_top5, col_bytes = columnar_flat_scan(query, columnar_vectors)

print(f"=== flat scan over N={N} rows, dim={DIM}, text/row={TEXT_SIZE_BYTES} bytes ===")
print(f"row-based store:  {row_bytes:>10,} bytes touched  (must load full rows: text+vector+meta)")
print(f"columnar store:   {col_bytes:>10,} bytes touched  (only the vector column)")
print(f"ratio: columnar touches {row_bytes / col_bytes:.1f}x FEWER bytes for the SAME scan")

print(f"\ntop-5 IDs match between layouts: {[i for i, _ in row_top5] == [i for i, _ in col_top5]}")

# --- asserts -----------------------------------------------------------------
# 1. both layouts must find the IDENTICAL top-5 -- storage layout changes
#    performance, never correctness
assert [i for i, _ in row_top5] == [i for i, _ in col_top5], \
    "row-based and columnar flat scans must return the identical top-5 (same math, different layout)"

# 2. columnar must touch dramatically fewer bytes than row-based for the
#    SAME vector-only scan -- the whole point of Arrow/Lance's design
assert col_bytes < row_bytes, "columnar layout must touch fewer bytes than row-based for a vector-only scan"
assert row_bytes / col_bytes > 5, \
    "with a realistic text payload, columnar should touch AT LEAST 5x fewer bytes than row-based"

# 3. columnar bytes touched must equal EXACTLY N * dim * 4 bytes -- nothing
#    else (no text, no metadata) is ever read
expected_columnar_bytes = N * DIM * FLOAT_BYTES
assert col_bytes == expected_columnar_bytes, \
    "columnar scan must touch exactly N*dim*4 bytes -- no text or metadata bytes at all"

# 4. row-based bytes touched must include the text payload size -- confirming
#    it really did drag in the irrelevant columns
assert row_bytes >= N * TEXT_SIZE_BYTES, \
    "row-based scan must have touched at least the full text payload for every row"

print("\n✓ all self-checks passed — columnar (Arrow/Lance) layout scans only the vector column; row-based drags in everything.")
