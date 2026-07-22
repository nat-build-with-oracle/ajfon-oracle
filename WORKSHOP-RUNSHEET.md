# Workshop Runsheet — ARRA Oracle Second Brain for Research

**Sunday 26 July 2026, 09:00–12:00 (GMT+7), live via Zoom**

The master minute-by-minute plan. Merges Hermes Oracle's original 5-block
curriculum draft (from the "training aj Fon" Discord thread) with the two real
decks already built — Deck B for concepts, Deck A for proof — plus concrete
demo cues. Every block cites the exact slide to show. See
`WORKSHOP-TIMELINE.md` for how we got here.

## The two decks, resolved

- **Deck B** = `artifacts/workshop-deck.html` (17 slides) — core concepts curriculum. Open standalone: `open artifacts/workshop-deck.html`
- **Deck A** = `artifacts/lit-review-vector-search.html` (9 slides) — real recovered-image proof + provenance. Present via the reorder tool: `python3 tools/deck-reorder/server.py`, then **▶ Present (local)**
- Neither replaces the other. They run as two separate browser tabs, switched between at the cues below.

## Demo data — Nat's own PhD corpus, not generic papers

**Decided and locked**: live demos use Nat's own real, already-verified research
corpus — the PM2.5 / satellite-AOD / DustBoy-sensor literature already proven
this session (บ๊องแบ๊ง's 12 papers + Orz's 17 papers, both code-backed — see
`artifacts/timeline-embedding-space-provenance.html`). **Not** generic
medical/education papers, even though the audience includes doctors —
Hermes's original draft suggested medical papers to match the audience, but
that was overruled: demoing with unfamiliar material to flatter the audience
would be faking expertise Nat doesn't have live on camera. Real domain,
real authority.

## Privacy guardrail for any live Hermes/memory demo

Hermes Oracle itself flagged this in the original draft, and it still stands:
**do not demo a raw memory dump** (Hermes's own conversation history contains
private threads — the อาจารย์ฝน negotiation itself lives in there). Any live
"watch it recall context" demo should use either (a) the already-public
DustBoy/embedding-space material, or (b) a freshly-seeded demo session created
just for the workshop with no prior private history in it. Never open Hermes's
real accumulated memory live on a 300-person Zoom call.

---

## BLOCK 1 — Opening & Live Demo (09:00–09:30 · 30 min)

| Time | What | Show |
|---|---|---|
| 09:00 | Welcome, who's in the room, donation context (hospital of choice) | — |
| 09:05 | "ทำไมนักวิจัยต้องมี Second Brain" — the problem: notes everywhere, can't find them when it matters | **Deck B slide 2** — จดโน้ตไว้เป็นพันไฟล์ พอถึงเวลา…หาไม่เจอ |
| 09:12 | The one theme of the whole workshop | **Deck B slide 3** — ธีมเดียวของทั้ง workshop |
| 09:15 | 🔴 **LIVE DEMO**: talk to an Oracle that remembers, built in ~20 lines | **Deck B slide 4** — Second Brain ใน 20 บรรทัด (run it live, don't just show the slide) |
| 09:25 | Bridge to Block 2 | — |

**Goal**: everyone sees the wow factor before any theory.

## BLOCK 2 — Core Concepts (09:30–10:00 · 30 min)

| Time | What | Show |
|---|---|---|
| 09:30 | The trap: searching Thai goes wrong first | **Deck B slide 5** — ค้นภาษาไทย เพี้ยน |
| 09:35 | Why: vector DB doesn't understand language, only embeddings | **Deck B slide 6** — vector DB ไม่ได้เข้าใจภาษา |
| 09:40 | What an embedding actually is — sentence → direction in space | **Deck B slide 7** — ประโยค → ทิศทางในพื้นที่ |
| 09:45 | The fix: swap the embedder, not the architecture | **Deck B slide 8** — เปลี่ยนแค่ embedder → ถูก 3/3 (bge-m3, multilingual) |
| 09:50 | The one equation to know | **Deck B slide 9** — Cosine Similarity |
| 09:55 | Oracle vs Notion/Obsidian — verbal comparison (agent reads+writes memory itself; no slide for this specifically, use the whiteboard/verbal) | — |

**Goal**: understand why agent memory ≠ a notebook, and why language matters.

## BLOCK 3 — Use Case A: Research Workflow (10:00–10:45 · 45 min)

This is where the two decks meet — Deck A **is** a real, worked example of
exactly this use case, with genuine data.

| Time | What | Show |
|---|---|---|
| 10:00 | Setup: everyone points their own Oracle at 2-3 real papers (**Nat's own PM2.5/DustBoy corpus** — see demo-data note above, not generic papers) | — |
| 10:10 | Hands-on: paper → agent summarizes + tags (method, population/site, findings, limitations) | — |
| 10:20 | 🔴 **The real thing**: this exact workflow, done for real, at scale — literature review as a map | **Deck A slide "ความรู้ทั้งหมด กางเป็นแผนที่ได้"** (t-SNE, 8 clusters, real) |
| 10:25 | 3 ways people actually built this — no one right answer | **Deck A slide "ไม่มี วิธีเดียวที่ถูก"** (ChromaDB / sqlite+embedding / bge-m3) |
| 10:30 | 🔴 **LIVE DEMO**: semantic search — ask a long question, get a real similarity score back | **Deck A slide "ถามประโยคยาวๆ ได้คะแนนความใกล้เคียง"** |
| 10:35 | Research gap, visible by eye — similarity matrix, concept network, PCA | **Deck A slide "Research gap มองเห็นได้ด้วยตา"** (3-panel) |
| 10:40 | **The credibility moment**: even we almost got this story wrong — here's how it was actually proven | **Deck A slides "ภาพพวกนี้ มาจากไหนกันแน่"** (provenance timeline) **+ "แม้แต่ AI ก็เข้าใจที่มาผิดได้"** (myth vs fact) |

**Goal**: prove the workflow with real, verified data — and use the near-miss
story itself to teach *why* verification matters, live.

## ☕ BREAK (10:45–10:55 · 10 min)

## BLOCK 4 — Use Case B: Knowledge Organization (10:55–11:25 · 30 min)

| Time | What | Show |
|---|---|---|
| 10:55 | How do you trust what the agent retrieves? Real system architecture | **Deck B slide 11** — Hybrid = vector + keyword |
| 11:00 | Connecting the LLM to answer *from your own notes*, with citations, and knowing when to say "I don't know" | **Deck B slide 12** — RAG w/ citations (around line 182) |
| 11:08 | Measuring it properly — golden-set evaluation, not vibes | **Deck B slide 13** — ตัวเลขที่จบทุกข้อสงสัย |
| 11:15 | Counter-intuitive, measured finding: combining 3 engines was *worse* than one good one | **Deck B slide 14** — รวม 3 engine → แย่กว่า bge-m3 เดี่ยว |
| 11:20 | Workshop exercise: everyone builds one Knowledge Node from their own material | — |

**Goal**: Oracle does "connect the dots" better than manual filing — but only
because it's measured, not assumed.

## BLOCK 5 — Use Case C: Multi-Agent Workflow (11:25–11:50 · 25 min)

| Time | What | Show |
|---|---|---|
| 11:25 | Concept: Agent A (Research) → Agent B (Write) → Agent C (Review) | — |
| 11:30 | 🔴 **The realest possible example**: the exact chain that produced today's material — one oracle built the images, another lost then recovered them, another cross-verified the story, this session shipped it into the deck you're looking at right now | Reference Deck A's provenance slide again, narrate the cross-oracle chain from `WORKSHOP-TIMELINE.md` |
| 11:40 | Knowledge stays portable across backends — not locked to one vendor | **Deck B slide 15** — ความรู้ portable ข้ามbackend |
| 11:45 | Q&A | — |

**Goal**: this isn't a hypothetical multi-agent pitch — it's a documented,
provable thing that happened this week, and the receipts are public.

## CLOSING (11:50–12:00 · 10 min)

| Time | What | Show |
|---|---|---|
| 11:50 | Hands-on access, one click | **Deck B slide 16** — เปิดใน Google Colab คลิกเดียว |
| 11:53 | Recap: 3 things to remember | **Deck B slide 17** — 3 อย่างที่จำไว้ |
| 11:56 | Closing thought | **Deck A slide "Literature review ไม่ใช่การอ่านให้ครบทุก paper"** |
| 11:58 | Donation reminder + Discord community invite + thank you | — |

---

## Nat's own prep checklist (things only Nat can do)

- [ ] Pick the specific 2-3 papers from the bongbaeng-12 / Orz-17 corpus to use live (the corpus is chosen; the *specific* papers for the live tag/summarize demo aren't yet)
- [ ] Create a **fresh, empty** Hermes demo session for any live memory-recall demo — do not open real accumulated memory on camera
- [ ] Confirm Zoom link + screen-share setup, test switching between the two deck tabs live
- [ ] Decide the exact wording for the hospital-donation callout at close (accounts are in `WORKSHOP-TIMELINE.md`)
- [ ] Time-box rehearsal: this runsheet is a plan, not a guarantee — one real run-through at 1.5x-talking-speed to see if 3 hours actually holds

## What's already done and verified (nothing left to build here)

- Deck A: 9 slides, `/impeccable`-audited, CSS bugs fixed, thumbnails regenerated, deep-linkable, pushed
- Deck B: 17 slides, already reviewed via a 4-lens workflow (07-16)
- Both decks' content is cross-checked against real provenance — no invented numbers, no unverified claims presented as fact
- Full origin story (`WORKSHOP-TIMELINE.md`) — cross-checked across 2 independent sources, discrepancies flagged not hidden
