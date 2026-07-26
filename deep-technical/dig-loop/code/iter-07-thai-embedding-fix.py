"""Dig-loop 07/50 — Why English-only embedders collapse Thai (and the fix).

Grounded in book/02-thai-embedding-lesson.md (real demo: query 2/3 wrong with
all-MiniLM-L6-v2, 3/3 right after swapping to bge-m3) and
deep-technical/19-multilingual-alignment.md (shared multilingual concept space;
book/05's real measured result: nomic-embed-text gave two UNRELATED Thai
sentences cosine = 1.000 — total collapse, aka anisotropy).
Runnable standalone (stdlib only):  python iter-07-thai-embedding-fix.py

We can't call a real embedding model here (no network/Ollama dependency
allowed), so this isolates the STRUCTURAL mechanism a toy CAN honestly prove:
tokenizer vocab coverage. A real semantic GAP (book/02 §2.4) additionally
needs contrastive training, which no hash function can fake — that part is
cited from the book's real, already-run numbers instead of re-derived here.
  - "english_only" tokenizer: any non-ASCII (Thai) character maps to a single
    shared [UNK] token — mirrors a tokenizer with zero Thai subwords in vocab.
  - "multilingual" tokenizer: character-bigrams, so Thai text keeps its own
    distinguishing structure — mirrors a SentencePiece vocab trained on Thai.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def cosine(a, b):
    return dot(a, b) / (norm(a) * norm(b))


DIM = 16

def token_vector(token):
    seed = sum((i + 1) * ord(c) for i, c in enumerate(token))
    vals = [((seed * (k + 7)) % 97) / 97 - 0.5 for k in range(DIM)]
    n = math.sqrt(sum(v * v for v in vals)) or 1.0
    return [v / n for v in vals]


def mean_pool(vecs):
    n = len(vecs)
    return [sum(v[d] for v in vecs) / n for d in range(DIM)]


def english_only_tokenize(text):
    """No Thai subwords in vocab -> every non-ASCII char collapses to [UNK]."""
    return [c if ord(c) < 128 else "[UNK]" for c in text if not c.isspace()]


def multilingual_tokenize(text):
    """Toy SentencePiece stand-in: character-bigrams keep Thai structure."""
    chars = [c for c in text if not c.isspace()]
    if len(chars) < 2:
        return chars or ["[UNK]"]
    return [chars[i] + chars[i + 1] for i in range(len(chars) - 1)]


def embed(text, tokenizer):
    tokens = tokenizer(text)
    return mean_pool([token_vector(t) for t in tokens])


# --- 6 unrelated, PURE-Thai sentences (no ASCII mixed in), different topics --
thai_sentences = [
    "ประชุมกับอาจารย์เรื่องเวิร์กช็อป",
    "สูตรต้มยำกุ้งน้ำข้น",
    "รายการซื้อของ นม ไข่ ขนมปัง",
    "วิธีสอนนักศึกษาเรื่องการค้นหา",
    "นัดหมายทันตแพทย์วันศุกร์",
    "งบประมาณโครงการปีหน้า",
]

def pairwise_cosines(tokenizer):
    vecs = [embed(s, tokenizer) for s in thai_sentences]
    scores = []
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            scores.append(cosine(vecs[i], vecs[j]))
    return scores


def mean(xs):
    return sum(xs) / len(xs)


def stdev(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


eo_scores = pairwise_cosines(english_only_tokenize)
ml_scores = pairwise_cosines(multilingual_tokenize)

print("=== english_only tokenizer: 6 UNRELATED Thai sentences, all pairs ===")
print(f"cosines = {[round(x, 4) for x in eo_scores]}")
print(f"mean={mean(eo_scores):.4f}  stdev={stdev(eo_scores):.6f}")
print("  -> every pair collapses to the SAME score (real symptom: nomic gave cos=1.000, book/05 §5.1)")

print("\n=== multilingual tokenizer: same 6 sentences, all pairs ===")
print(f"cosines = {[round(x, 4) for x in ml_scores]}")
print(f"mean={mean(ml_scores):.4f}  stdev={stdev(ml_scores):.6f}")
print("  -> pairs spread out — the vocab at least SEES each sentence as distinct")

print("\nreal semantic separation (needs contrastive training, book/02 §2.4, actually run):")
print("  all-MiniLM (english-only)  2/3 queries wrong")
print("  bge-m3 (multilingual)      3/3 queries right — same DB, only embedder swapped")

# --- asserts -----------------------------------------------------------------
# 1. english_only collapses ALL pairs to the identical score (near-zero spread)
#    -- because every Thai sentence becomes nothing but repeated [UNK] tokens,
#    and mean-pooling N copies of one vector returns that same vector always
assert stdev(eo_scores) < 1e-9, \
    "an English-only vocab must give IDENTICAL cosine for every Thai sentence pair (total collapse)"
assert abs(eo_scores[0] - 1.0) < 1e-9, \
    "the collapsed english-only score must be exactly 1.0 — matches book/05's real nomic result"

# 2. multilingual tokenizer must NOT collapse — pairs must show real spread
assert stdev(ml_scores) > 0.05, \
    "a Thai-aware tokenizer must produce a genuine spread of scores, not one flat number"

# 3. multilingual tokenizer's pairwise scores must not all sit at 1.0
assert max(ml_scores) < 0.999, \
    "a Thai-aware tokenizer must not collapse distinct sentences to identical vectors"

# 4. sanity: an identical sentence embedded twice must still be cosine 1.0
#    under EITHER tokenizer (collapse is about losing INFORMATION, not about
#    the embed function itself being broken)
same = thai_sentences[0]
assert abs(cosine(embed(same, multilingual_tokenize), embed(same, multilingual_tokenize)) - 1.0) < 1e-12

print("\n✓ all self-checks passed — zero-Thai-vocab tokenizer flattens everything to one point; a Thai-aware vocab does not.")
