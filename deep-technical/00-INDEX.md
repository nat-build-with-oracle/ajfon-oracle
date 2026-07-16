# ARRA Oracle — Vector Search Deep-Technical Reference

> ลงลึกทั้งสมการและโค้ดจริง · grounded ใน arra-oracle-v3/src/vector/* + PR จริง + citation งานวิจัย
> เขียนผ่าน /loop deep mode (Nat: "ลงลึกโค้ด+สมการ เป็นร้อยหน้าก็ถูก") · 2026-07-13

## Part I — Foundations (คณิต)
- **Ch1** Mathematics — dot product, norm, cosine similarity/distance, proofs
- **Ch8** Quantization & metric proofs — SQ/PQ/BQ, normalize→dot=cosine, ‖a−b‖²=2−2cosθ

## Part II — Embeddings (โมเดล)
- **Ch2** Embeddings & contrastive training — pipeline, InfoNCE, asymmetric
- **Ch9** Tokenization — BPE/SentencePiece, Thai segmentation, chunking-relevant limits
- **Ch10** Self-attention internals — Q/K/V, softmax(QKᵀ/√dk)V, multi-head, positional
- **Ch16** Efficient attention — FlashAttention, linear, sparse
- **Ch19** Multilingual alignment — cross-lingual space, Thai→English retrieval
- **Ch21+** Positional encoding deep (roadmap)

## Part III — Indexing & Retrieval (ANN)
- **Ch3** ANN indexing — IVF, PQ, HNSW, LanceDB
- **Ch17** HNSW construction — insert, layer assignment, O(log n) proof
- **Ch12** Chunking strategy — fixed/semantic/parent-child

## Part IV — ARRA System (โค้ดจริง)
- **Ch4** Code & hybrid scoring — adapter pattern, fallback chain, RRF (k=60), reranker
- **Ch11** RRF & ranking theory — scale-invariance proof, Kendall τ, confidence-weighted
- **Ch13** Retrieval heat model — recency/frequency, LRU+LFU, consolidation
- **Ch18** Cross-encoder reranker — architecture, loss, 2-stage pipeline, distillation
- **Ch15** MCP transport — stdio/HTTP/embedded, graceful degradation

## Part V — Edge & Ops
- **Ch5** Cloudflare edge embeddings — Workers AI, drift
- **Ch14** Vectorize + D1 internals — managed ANN, privacy trade-off
- **Ch6** Benchmark methodology — recall@k, MRR, nDCG, drift, latency
- **Ch20** Eval harness code — benchmark.ts, metric code, CI-as-contract

## Part VI — bge-m3 deep
- **Ch7** Multi-functionality — dense/sparse/ColBERT, BM25, MaxSim

*status: 20 chapters · ~2,400 lines · ต่อเนื่องจนถึงร้อยหน้า*
