"""Dig-loop 45/50 — Semantic cache: paraphrases hit, versioned keys invalidate.

Grounded in deep-technical/32-caching.md §32.2 (exact result cache: same
query -> same result, but real query traffic paraphrases constantly, so hit
rate is low), §32.3 (semantic cache: query doesn't need to match exactly,
just cos(query_new, query_cached) > threshold -- "ใช้ vector search มา cache
vector search"), and §32.4 (cache invalidation: versioned keys -- bump the
index version on upsert so old cache entries miss instead of returning
stale results).
Runnable standalone (stdlib only):  python iter-45-caching.py

Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import hashlib
import math


def toy_embed(text):
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


def exact_hash(text):
    return hashlib.sha256(text.strip().encode()).hexdigest()[:12]


# --- exact cache: only an IDENTICAL string hits -----------------------------
exact_cache = {}


def exact_cache_get(query):
    return exact_cache.get(exact_hash(query))


def exact_cache_put(query, result):
    exact_cache[exact_hash(query)] = result


# --- semantic cache: cosine similarity decides the hit (§32.3) -------------
semantic_cache = []   # list of (query_text, query_vec, result)
SEMANTIC_THRESHOLD = 0.5


def semantic_cache_get(query, threshold=SEMANTIC_THRESHOLD):
    qvec = toy_embed(query)
    best_sim, best_entry = -1.0, None
    for cached_text, cached_vec, result in semantic_cache:
        sim = cosine(qvec, cached_vec)
        if sim > best_sim:
            best_sim, best_entry = sim, (cached_text, result)
    if best_entry and best_sim > threshold:
        return best_entry[1], best_sim
    return None, best_sim


def semantic_cache_put(query, result):
    semantic_cache.append((query, toy_embed(query), result))


# --- query 1: cache it after a real (simulated) search ----------------------
Q1 = "เบาหวาน รักษา ยังไง"
RESULT_1 = ["doc_diabetes_treatment"]
exact_cache_put(Q1, RESULT_1)
semantic_cache_put(Q1, RESULT_1)

# --- query 2: a real paraphrase (different words, same meaning) ------------
Q2 = "วิธี รักษา เบาหวาน"

exact_hit_2 = exact_cache_get(Q2)
semantic_hit_2, sim_2 = semantic_cache_get(Q2)

print("=== §32.2/§32.3: exact cache vs semantic cache on a paraphrase ===")
print(f"Q1 (cached): \"{Q1}\"")
print(f"Q2 (paraphrase): \"{Q2}\"")
print(f"exact cache hit?    {exact_hit_2 is not None}  <- misses, different string")
print(f"semantic cache hit? {semantic_hit_2 is not None}  (cosine={sim_2:.3f} vs threshold={SEMANTIC_THRESHOLD})")

# --- query 3: a genuinely UNRELATED query -----------------------------------
Q3 = "สูตร กาแฟ cold brew"
semantic_hit_3, sim_3 = semantic_cache_get(Q3)
print(f"\nQ3 (unrelated): \"{Q3}\"")
print(f"semantic cache hit? {semantic_hit_3 is not None}  (cosine={sim_3:.3f})  <- correctly misses")

# --- cache invalidation: versioned keys (§32.4) -----------------------------
index_version = 1
versioned_cache = {}


def versioned_cache_key(query, version):
    return (exact_hash(query), version)


def versioned_cache_put(query, version, result):
    versioned_cache[versioned_cache_key(query, version)] = result


def versioned_cache_get(query, version):
    return versioned_cache.get(versioned_cache_key(query, version))


versioned_cache_put(Q1, index_version, RESULT_1)
hit_before_upsert = versioned_cache_get(Q1, index_version)

# a new, more relevant doc gets upserted -> bump the version
index_version += 1
NEW_RESULT_1 = ["doc_diabetes_treatment_v2", "doc_diabetes_new_guideline"]
hit_after_upsert_same_key = versioned_cache_get(Q1, index_version - 1)   # old version key
hit_after_upsert_new_version = versioned_cache_get(Q1, index_version)     # new version key -- not cached yet

print(f"\n=== §32.4: versioned-key invalidation after an upsert ===")
print(f"cache hit BEFORE upsert (v1): {hit_before_upsert}")
print(f"index upserted -> version bumped to v{index_version}")
print(f"cache hit at NEW version (v{index_version}): {hit_after_upsert_new_version}  <- correctly MISSES, forces fresh search")

# --- asserts -----------------------------------------------------------------
# 1. the exact cache must MISS on a real paraphrase -- proving why exact
#    caching alone has a low hit rate on real (paraphrasing) query traffic
assert exact_hit_2 is None, "exact cache must miss on a paraphrased query (different string, same meaning)"

# 2. the semantic cache must HIT on the same paraphrase -- the entire
#    point of §32.3's trick
assert semantic_hit_2 is not None, "semantic cache must hit on a genuine paraphrase (cosine above threshold)"
assert semantic_hit_2 == RESULT_1, "the semantic cache hit must return the correct cached result"

# 3. the semantic cache must correctly REJECT a genuinely unrelated query --
#    it's similarity-based, not "always hit something"
assert semantic_hit_3 is None, "semantic cache must NOT hit for a genuinely unrelated query"
assert sim_3 < sim_2, "the unrelated query's similarity must be lower than the real paraphrase's similarity"

# 4. versioned-key invalidation must correctly MISS after an upsert bumps
#    the version -- stale results must never be silently served
assert hit_before_upsert == RESULT_1, "the cache must hit correctly before any upsert happens"
assert hit_after_upsert_new_version is None, \
    "after an upsert bumps the index version, the cache at the NEW version must miss (forcing a fresh search)"

# 5. the OLD version's cache entry must still exist (not deleted, just no
#    longer the active key) -- versioning doesn't erase history, it just
#    stops pointing at it (same philosophy as iter-30's time-travel)
assert versioned_cache_get(Q1, 1) == RESULT_1, \
    "the old version's cache entry must remain retrievable by its own version key"

print("\n✓ all self-checks passed — semantic cache hits real paraphrases and rejects unrelated queries; versioned keys prevent stale hits.")
