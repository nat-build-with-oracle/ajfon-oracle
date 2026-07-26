# Dig-Loop Plan — 50 slide+code deep-dives on the vector-DB demo & teaching

> Source of task: `/loop /goal ... /dig --deep + /trace --deep about our vector database
> demo and teaching, make it to a slide and code — 50 times, 1 per 15m` (Nat, 2026-07-16)
>
> Each iteration N produces TWO deliverables, grounded by digging the repo
> (`book/`, `deep-technical/`, `data/vector-teaching-log.md`, arra-oracle-v3 `src/vector/*`):
> - `slides/iter-NN-<slug>.html` — one self-contained, theme-aware teaching slide
> - `code/iter-NN-<slug>.py`  — runnable code with `assert` self-checks (book philosophy: วัด อย่าเดา)
>
> Progress + what-was-dug is logged in `PROGRESS.md` after each iteration.

## The 50 topics (build in order)

| # | Slug | Focus | Primary sources dug |
|---|------|-------|---------------------|
| 1 | cosine-the-only-equation | cosine sim/dist by hand | book/04, deep-technical/01 |
| 2 | dot-product-and-norm | dot product & L2 norm geometry | deep-technical/01 |
| 3 | normalize-then-dot | proof: normalize→dot=cosine | deep-technical/08 |
| 4 | l2-cosine-identity | ‖a−b‖²=2−2cosθ | deep-technical/08 |
| 5 | tokens-to-vector | sentence→tokens→embedding | book/05, deep-technical/09 |
| 6 | what-1024-dims-mean | dimensions & the space | book/05, deep-technical/02 |
| 7 | thai-embedding-fix | bge-m3 Thai pitfall + fix | book/02, deep-technical/19 |
| 8 | semantic-map-projection | 1024D→2D PCA/UMAP | book/05 |
| 9 | word-clusters | why inflation≈AI≈cat | data/vector-teaching-log |
| 10 | flat-brute-force | exact baseline search | book/06 |
| 11 | metadata-filter | pre vs post filter | book/03 |
| 12 | chroma-persistentclient | collections, upsert, query | book/01, book/08 |
| 13 | chroma-l2-vs-cosine | the hnsw:space gotcha | book/09 |
| 14 | hnsw-intuition | skip-list in high-dim | deep-technical/17 |
| 15 | hnsw-parameters | M, ef_construction, ef_search | deep-technical/17, book/06 |
| 16 | hnsw-recall-latency | recall vs latency benchmark | book/06 |
| 17 | ivf-indexing | coarse quantizer + lists | deep-technical/03 |
| 18 | product-quantization | compress vectors PQ | deep-technical/08 |
| 19 | scalar-binary-quant | memory math SQ/BQ | deep-technical/08 |
| 20 | recall-at-k | measuring ANN quality | book/11, deep-technical/06 |
| 21 | mrr-ndcg | ranking metrics | deep-technical/06 |
| 22 | golden-set | building a golden set | book/11 |
| 23 | fts5-bm25 | keyword search basics | book/07 |
| 24 | hybrid-search | vector + keyword | book/07, deep-technical/04 |
| 25 | rrf-fusion | RRF k=60 scale-invariance | deep-technical/11 |
| 26 | triple-rrf-hurts | ch17 finding | book/17 |
| 27 | complementary-recall | diagnostic | book/17 |
| 28 | lancedb-flat-arrow | columnar flat scan | book/13, deep-technical/03 |
| 29 | lancedb-native-fts | tantivy FTS | book/14 |
| 30 | lancedb-time-travel | versioning | book/15 |
| 31 | chroma-to-lancedb | migration | book/10 |
| 32 | rag-retrieve-cite | RAG pipeline | book/09 |
| 33 | chunking-strategies | fixed/semantic/parent-child | deep-technical/12 |
| 34 | cross-encoder-rerank | 2-stage pipeline | deep-technical/18 |
| 35 | matryoshka-dims | truncatable embeddings | deep-technical/36 |
| 36 | splade-sparse | sparse retrieval | deep-technical/34 |
| 37 | colbert-maxsim | late interaction | deep-technical/07 |
| 38 | multilingual-align | Thai→English retrieval | deep-technical/19 |
| 39 | cloudflare-workers-ai | bge-m3 @ edge | book/16, deep-technical/05 |
| 40 | cloudflare-vectorize | managed ANN REST | book/16, deep-technical/14 |
| 41 | multi-engine-benchmark | bge-m3 vs nomic vs qwen3 | book/17 |
| 42 | pooled-judgment | TREC/BEIR pooling | deep-technical/39 |
| 43 | batch-embed-cure | Ollama bottleneck fix | deep-technical/06 |
| 44 | query-understanding | expansion/rewrite | deep-technical/29 |
| 45 | caching | embed + result cache | deep-technical/32 |
| 46 | cost-model | self-host vs managed | deep-technical/24 |
| 47 | privacy-local-first | local retrieval | book/12 |
| 48 | agentic-retrieval | retrieval loop | deep-technical/35 |
| 49 | monitoring-drift | production drift | deep-technical/23 |
| 50 | second-brain-end-to-end | the full demo | book/01, all |

## Convention
- Slides: single `.slide` section, 1920×1080 safe, light+dark tokens, no external assets.
- Code: `python code/iter-NN-<slug>.py` runs standalone, prints a result, ends with `assert`s.
  Prefer stdlib + numpy; guard heavy deps (chromadb/lancedb/ollama) behind a try/skip so the
  file always runs in CI even without them.
- After each: append a PROGRESS.md row (iteration, topic, files, what-dug, self-check result).
