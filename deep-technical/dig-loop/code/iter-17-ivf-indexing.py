"""Dig-loop 17/50 — IVF: partition into cells, only probe the closest ones.

Grounded in deep-technical/03-ann-indexing.md §3.3 (train: k-means into
`nlist` centroids; search: probe the `nprobe` closest cells, brute-force only
inside them) and §3.7 (nprobe is the recall<->speed knob, same family as
HNSW's efSearch but partition-based instead of graph-based).
Runnable standalone (uses numpy, stdlib otherwise):
    python iter-17-ivf-indexing.py

Builds a real (small) k-means IVF index from scratch: train centroids,
assign vectors to inverted lists, then search by probing only the nprobe
nearest cells -- and measures recall@k + candidates-examined vs nprobe,
including the real "edge effect" from §3.3: a true neighbor sitting just
across a cell boundary gets missed when nprobe is too low.
Ends with asserts (วัด อย่าเดา / measure, don't guess).
"""
import numpy as np

rng = np.random.default_rng(21)
N, DIM, NLIST = 5000, 16, 32


def normalize_rows(X):
    return X / np.linalg.norm(X, axis=1, keepdims=True)


vectors = normalize_rows(rng.normal(size=(N, DIM)))


def kmeans(X, k, iters=15):
    """Minimal k-means -- exactly what IVF's 'train' step does (§3.3)."""
    idx = rng.choice(len(X), size=k, replace=False)
    centroids = X[idx].copy()
    for _ in range(iters):
        sims = X @ centroids.T                      # cosine (unit vectors)
        assign = np.argmax(sims, axis=1)
        for c in range(k):
            members = X[assign == c]
            if len(members) > 0:
                centroids[c] = normalize_rows(members.mean(axis=0, keepdims=True))[0]
    return centroids, assign


def build_ivf(vectors, nlist):
    centroids, assign = kmeans(vectors, nlist)
    lists = {c: np.where(assign == c)[0] for c in range(nlist)}
    return centroids, lists


def ivf_search(qvec, centroids, lists, nprobe, k=5):
    cell_sims = centroids @ qvec
    probe_cells = np.argsort(-cell_sims)[:nprobe]
    candidate_ids = np.concatenate([lists[c] for c in probe_cells]) if len(probe_cells) else np.array([], dtype=int)
    if len(candidate_ids) == 0:
        return np.array([], dtype=int), 0
    cand_sims = vectors[candidate_ids] @ qvec
    order = np.argsort(-cand_sims)[:k]
    return candidate_ids[order], len(candidate_ids)


def brute_force_topk(qvec, k=5):
    scores = vectors @ qvec
    return np.argsort(-scores)[:k]


print(f"=== training IVF: k-means into {NLIST} cells (N={N}, dim={DIM}) ===")
centroids, lists = build_ivf(vectors, NLIST)
cell_sizes = [len(v) for v in lists.values()]
print(f"cell sizes: min={min(cell_sizes)} max={max(cell_sizes)} avg={np.mean(cell_sizes):.1f}")

query_ids = rng.choice(N, size=40, replace=False)


def recall_at_nprobe(nprobe, k=5):
    total_recall, total_examined = 0.0, 0
    for qi in query_ids:
        qvec = vectors[qi]
        true_top = set(brute_force_topk(qvec, k).tolist())
        found, examined = ivf_search(qvec, centroids, lists, nprobe, k)
        total_recall += len(set(found.tolist()) & true_top) / k
        total_examined += examined
    return total_recall / len(query_ids), total_examined / len(query_ids)


print(f"\n=== recall@5 vs nprobe (out of nlist={NLIST}) ===")
r1, e1 = recall_at_nprobe(1)
r4, e4 = recall_at_nprobe(4)
r16, e16 = recall_at_nprobe(16)
r_all, e_all = recall_at_nprobe(NLIST)   # probing every cell == brute force
print(f"nprobe=1   recall@5={r1:.3f}  avg candidates examined={e1:.0f}")
print(f"nprobe=4   recall@5={r4:.3f}  avg candidates examined={e4:.0f}")
print(f"nprobe=16  recall@5={r16:.3f}  avg candidates examined={e16:.0f}")
print(f"nprobe=all recall@5={r_all:.3f}  avg candidates examined={e_all:.0f}  (== brute force)")

# --- edge-effect demo: find a query whose true 2nd-nearest lives in a
#     DIFFERENT cell than its own -- low nprobe should miss it -------------
edge_case_found = False
for qi in query_ids:
    qvec = vectors[qi]
    true_top5 = brute_force_topk(qvec, 5)
    own_cell = np.argmax(centroids @ qvec)
    for nb in true_top5[1:]:
        nb_cell = np.argmax(centroids @ vectors[nb])
        if nb_cell != own_cell:
            found1, _ = ivf_search(qvec, centroids, lists, nprobe=1, k=5)
            if nb not in found1:
                edge_case_found = True
                print(f"\nedge effect: query {qi}'s true neighbor {nb} lives in cell {nb_cell} "
                      f"(query's own cell={own_cell}) -- MISSED at nprobe=1")
                break
    if edge_case_found:
        break

# --- asserts -----------------------------------------------------------------
# 1. recall must improve monotonically as nprobe grows
assert r4 >= r1 - 0.05, "nprobe=4 should not be meaningfully worse than nprobe=1"
assert r16 >= r4 - 0.05, "nprobe=16 should not be meaningfully worse than nprobe=4"
assert r16 > r1, "probing more cells (nprobe=16 vs 1) must improve recall"

# 2. probing ALL cells must recover perfect recall -- IVF with nprobe=nlist
#    degenerates exactly to brute force (§3.7: "Flat (exact) recall 100%")
assert r_all > 0.999, "probing every cell must reconstruct exact brute-force recall (1.0)"

# 3. examined-candidate count must grow with nprobe (the real cost knob)
assert e1 < e4 < e16 < e_all, \
    "candidates examined must strictly increase as nprobe grows from 1 to nlist"

# 4. nprobe=1 must examine FAR fewer candidates than brute force (that's the
#    entire point of partitioning)
assert e1 < e_all / 10, "nprobe=1 must examine far fewer candidates than scanning everything"

# 5. the edge-effect case must be demonstrable: SOME query's true neighbor
#    sits in a different cell and gets missed at nprobe=1
assert edge_case_found, "must be able to demonstrate at least one real edge-effect miss at nprobe=1"

print("\n✓ all self-checks passed — nprobe trades candidates-examined for recall; nprobe=nlist == exact brute force.")
