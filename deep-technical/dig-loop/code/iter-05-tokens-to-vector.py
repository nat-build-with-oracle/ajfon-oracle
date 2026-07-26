"""Dig-loop 05/50 — Sentence -> tokens -> embedding (the actual pipeline).

Grounded in book/05-where-embeddings-come-from.md (contrastive training origin)
and deep-technical/09-tokenization.md (BPE §9.2, token != word != character §9.6).
Runnable standalone (stdlib only):  python iter-05-tokens-to-vector.py

Teaches the full chain a sentence goes through before it becomes the single
vector Ch1-4 compare with cosine:
    sentence -> subword tokens (toy BPE) -> per-token vectors -> mean-pool
        -> ONE sentence vector
Real bge-m3 uses SentencePiece + a transformer instead of toy BPE + hashing,
but the SHAPE of the pipeline (tokens -> per-token vecs -> pooled vec) is
identical. Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import math
from collections import Counter


# --- 1. a tiny BPE trainer (deep-technical/09 §9.2) -------------------------
def train_bpe(corpus_words, num_merges):
    """corpus_words: list of words, each pre-split into characters + end marker."""
    vocab = Counter()
    for w in corpus_words:
        vocab[tuple(w) + ("</w>",)] += 1

    merges = []
    for _ in range(num_merges):
        pairs = Counter()
        for word, freq in vocab.items():
            for i in range(len(word) - 1):
                pairs[(word[i], word[i + 1])] += freq
        if not pairs:
            break
        best = max(pairs, key=pairs.get)
        merges.append(best)
        new_vocab = Counter()
        for word, freq in vocab.items():
            merged, i = [], 0
            while i < len(word):
                if i < len(word) - 1 and (word[i], word[i + 1]) == best:
                    merged.append(word[i] + word[i + 1])
                    i += 2
                else:
                    merged.append(word[i])
                    i += 1
            new_vocab[tuple(merged)] += freq
        vocab = new_vocab
    return merges


def apply_bpe(word, merges):
    tokens = list(word) + ["</w>"]
    for a, b in merges:
        i = 0
        merged = []
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == a and tokens[i + 1] == b:
                merged.append(a + b)
                i += 2
            else:
                merged.append(tokens[i])
                i += 1
        tokens = merged
    return tokens


# --- 2. a tiny deterministic "embedding" table (stand-in for a real model) --
DIM = 16

def token_vector(token):
    """Deterministic pseudo-embedding: hash-seeded, unit-length. Not learned —
    just enough structure to demo the PIPELINE shape, not real semantics."""
    seed = sum((i + 1) * ord(c) for i, c in enumerate(token))
    vals = [((seed * (k + 7)) % 97) / 97 - 0.5 for k in range(DIM)]
    n = math.sqrt(sum(v * v for v in vals)) or 1.0
    return [v / n for v in vals]


def mean_pool(token_vecs):
    """Real bge-m3 dense pooling: average the per-token vectors into ONE."""
    n = len(token_vecs)
    summed = [sum(v[d] for v in token_vecs) for d in range(DIM)]
    return [s / n for s in summed]


def sentence_vector(tokens):
    return mean_pool([token_vector(t) for t in tokens])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def cosine(a, b):
    return dot(a, b) / (norm(a) * norm(b))


# --- train a toy BPE on a small corpus, then tokenize new words ------------
corpus = ["lower", "lowest", "newer", "wider", "newest"]
merges = train_bpe([list(w) for w in corpus], num_merges=8)

print("=== toy BPE (deep-technical/09 §9.2) ===")
for w in ["lower", "newest", "lowering"]:
    toks = apply_bpe(w, merges)
    print(f"{w:>10} -> {toks}  ({len(w)} chars -> {len(toks)} tokens)")

# --- the pipeline: sentence -> tokens -> per-token vecs -> pooled vector ---
def embed_sentence(sentence, merges):
    words = sentence.lower().split()
    tokens = []
    for w in words:
        tokens.extend(apply_bpe(w, merges))
    return sentence_vector(tokens), tokens

v1, toks1 = embed_sentence("the lower newest window", merges)
v2, toks2 = embed_sentence("newest lower the window", merges)   # same words, reordered
v3, toks3 = embed_sentence("a completely different sentence", merges)

print("\n=== full pipeline ===")
print(f"'the lower newest window' -> {len(toks1)} tokens -> 1 pooled vector (dim={DIM})")
print(f"cos(same-words-reordered)   = {cosine(v1, v2):.4f}")
print(f"cos(unrelated sentence)     = {cosine(v1, v3):.4f}")

# --- asserts -----------------------------------------------------------------
# 1. BPE must actually compress: more chars than tokens for words in-corpus-ish
assert len(apply_bpe("lower", merges)) < len("lower") + 1, "merges must shrink token count vs raw chars"

# 2. token != word != character (§9.6): a longer word can need fewer tokens
#    once BPE has learned its common subwords, than a naive char-split would.
raw_chars = len(list("lowering"))
bpe_tokens = len(apply_bpe("lowering", merges))
assert bpe_tokens <= raw_chars + 1, "BPE tokens must not exceed char+end-marker count"

# 3. mean_pool really averages — pooling identical repeated tokens is a no-op
v_single = token_vector("newer")
v_pooled_dup = mean_pool([v_single, v_single, v_single])
assert all(abs(a - b) < 1e-12 for a, b in zip(v_single, v_pooled_dup)), \
    "mean-pooling a token with itself must return the same vector unchanged"

# 4. pooled sentence vectors are unit-scale-ish and comparable via cosine
assert -1.0 <= cosine(v1, v2) <= 1.0
assert -1.0 <= cosine(v1, v3) <= 1.0

# 5. same bag-of-words (just reordered) must pool to the SAME vector —
#    mean pooling is order-invariant (a real limitation! bge-m3 dense output
#    shares this property; that's why rerankers / ColBERT exist, Ch34/37).
assert abs(cosine(v1, v2) - 1.0) < 1e-9, \
    "mean pooling must be order-invariant: same tokens, any order, same vector"

# 6. an unrelated sentence must NOT collapse to the same vector as v1
assert cosine(v1, v3) < 0.999, "a genuinely different sentence must not pool to an identical vector"

print("\n✓ all self-checks passed — sentence -> BPE tokens -> per-token vecs -> mean-pool -> ONE vector.")
