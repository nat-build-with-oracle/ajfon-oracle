# Product

## Register

brand

## Users

**Primary — workshop attendees**: "ARRA Oracle Second Brain for Research," a free online workshop (Gradpassion × อ.นัท Nat Weerawan), Sunday 26 July 2026, 09:00–12:00 via Zoom (replay on a closed Facebook group). Audience: อาจารย์ นักวิจัย นักศึกษา แพทย์ บุคลากรสุขภาพ และผู้สนใจทั่วไป — professors, researchers, grad students, doctors, healthcare workers, general public. Explicitly **not** dev-only ("ไม่ต้องเป็นสาย Dev ก็เรียนได้"). Job to be done in the room: watch real workflows — paper → Agent summarizes/tags/stores in Memory → old knowledge retrieved and extended into new ideas/research gaps → Research Agent → Writing Agent → Review Agent. Donation-based (to a hospital of the attendee's choice), registration closed 24 July.

**Secondary — book readers**: "Second Brain ด้วย Vector Search," the companion technical book (17 chapters + 86 deep-technical chapters, runnable Jupyter notebooks, Colab-first, ChromaDB/LanceDB/Cloudflare Edge). More technical, dev-comfortable audience who want to build the system hands-on, not just watch it.

## Product Purpose

Teach a working "Second Brain" research-knowledge system built on vector search / AI agents, proven with runnable, measured evidence rather than claims. One free live workshop (breadth, non-dev-friendly) plus one open technical book (depth, build-it-yourself), both under ARRA Oracle. Success = an attendee or reader leaves able to picture — or actually build — a real paper-organization pipeline, backed by numbers they could reproduce themselves.

## Brand Personality

Editorial / technical-magazine. Rigorous, proof-driven, unhyped — confident because the numbers are real, not because the design is loud. Warm and inclusive at the workshop layer (free, donation-based, explicitly welcomes non-devs, doctors, general public); technically uncompromising at the book layer. Same voice, two altitudes.

## Anti-references

Generic AI-SaaS marketing: cream/beige backgrounds, gradient text, hero-metric templates, tiny uppercase eyebrows on every section, 01/02/03 numbered-section scaffolding, identical icon+heading card grids. This is teaching material for researchers and doctors, not a startup landing page — it should never read as one.

## Design Principles

1. **"วัด อย่าเดา" (measure, don't guess)** — every claim on screen carries a number, and the number should look like it came from a real run (real chart, real screenshot, real timestamp), never decoration.
2. **Non-dev-friendly without dumbing down** — the workshop layer must read clearly to a professor or doctor with zero code background; the book layer is allowed to go deep. Don't flatten one to serve the other.
3. **Proof over hype** — reject the SaaS-marketing toolkit (gradients, hero metrics, eyebrows) in favor of editorial rigor.
4. **One consistent dark-mode-first system** — the real canonical system is already established across 6 of 8 workshop artifacts (`arra-workshop-poster/slides`, `oracle-workshop-handout/slides`, `vector-search-slides/teaching`): near-black blue-violet bg `#0a0b10`, panel layering, 8 semantic accent hues, Thai-first type, mono for data. `artifacts/workshop-deck.html` and `artifacts/vector-viz.html` drift to two different palettes each — reconcile toward the canonical one next time either is touched. See DESIGN.md for the full spec.
5. **Thai-first, bilingual by necessity** — Thai carries workshop-facing material (`"Sukhumvit Set", "Thonburi"` stack already in use); English stays only for code, tool names, and technical terms that shouldn't be translated.

## Accessibility & Inclusion

WCAG AA contrast — already a standing practice for the book (`verify contrast (WCAG AA) ก่อนเผยแพร่`, stated in README). Hold workshop artifacts (slides/posters/handouts) to the same bar, not just the book HTML. Respect `prefers-reduced-motion` on any animated artifact.
