---
target: DustBoy-Phd-Oracle timeline-embedding-space-provenance.html
total_score: 29
p0_count: 0
p1_count: 2
timestamp: 2026-07-22T01-33-21Z
slug: timeline-embedding-space-provenance-html
---
## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Static page, but SOURCE/RENDERED stamp + `.src` citations expose evidence provenance well |
| 2 | Match System / Real World | 2 | Great for devs; primary non-dev Sunday audience gets no gloss on sqlite-TS/bge-m3/TfidfVectorizer/PCA |
| 3 | User Control and Freedom | 3 | `[data-theme]` exists but no on-page toggle, no anchors/TOC |
| 4 | Consistency and Standards | 3 | Internally consistent, but `--grpB #4f7a3c` ≈ `--proven #3d7f56` — green means two things |
| 5 | Error Prevention | 3 | Low-relevance (no inputs); source-ID citations prevent mis-citation |
| 6 | Recognition Rather Than Recall | 3 | Legend + verdict restatement offset name→DB→count recall load |
| 7 | Flexibility and Efficiency | 2 | Long single scroll, no TOC/anchors/skip-to-verdict |
| 8 | Aesthetic and Minimalist Design | 4 | Real strength — flat, one column, generous whitespace |
| 9 | Error Recovery | 3 | Myth→fact device IS diagnose+recover, structurally |
| 10 | Help and Documentation | 3 | Footer states evidence hierarchy + full-proof path + method aphorism |
| **Total** | | **29/40** | **Good — solid foundation, address weak areas** |

## Anti-Patterns Verdict

**Start here: does this look AI-generated?** Partial / leans no.

**LLM assessment:** Built without ever seeing DESIGN.md, this reads as a warm cream/brass/serif editorial-magazine system — cohesive, deliberate-looking, and it dodges the loudest AI tells (no gradient text, no hero-metric template, no 01/02/03 scaffolding, no identical card grid, no glassmorphism). It shares the brand's *ethos* (flat/no-shadow, proof-first numbers, honest unresolved "Open" row, reduced-motion gated) without sharing a single visual *token* with it.

**Deterministic scan:** Two independent passes disagree in interesting ways, and the disagreement itself is informative:
- **Static parse** (`detect.mjs` on the raw file): exit 2, 6 findings — 1× side-tab warning (the `border-left:3px` group coding), 5× design-system-radius advisories. The radius advisories only fired because `.impeccable/design.json` (ajfon's, just written) was in scope — they're contingent on which project's sidecar is active, not intrinsic to the file.
- **Browser-rendered** (Puppeteer engine, since the Chrome extension was disconnected both times an agent tried it): exit 2, 26 findings — 11× line-length (97–124 chars, over the 65–75ch cap), 7× low-contrast (the `.src` citation footnotes, median 2.5–2.7:1 against a 4.5:1 AA bar), 5× side-tab (one per rendered timeline card), 1× all-caps-body, 1× hero-eyebrow-chip, 1× overused-font.
- **Confirmed false positives** (don't chase these): `overused-font: roboto 32%` is a headless-Chromium font-fallback artifact — the real macOS audience never sees Roboto, `system-ui`/`-apple-system` resolve to SF Pro. `all-caps-body (51 chars)` is the sum across tiny labels/badges/table headers, not actual uppercase prose.
- **Where LLM and detector agree:** the eyebrow chip (`⏳ Time-Travel · Oracle Archaeology · verbatim proof`) — both independently flagged it. The side-stripe group coding — both flagged it, though the detector's own evidence (reinforced by a matching node-dot color and an explicit legend) makes this a *design-justified* hit rather than a decorative one; the mechanism is arguable even though the rule technically matches.
- **Where the detector caught what the LLM missed:** the 7 rendered low-contrast citations are a *different, larger* set of elements than the hand-picked brass labels/headings the LLM checked by hand — convergent evidence of the same light-mode contrast problem, from two independent methods. The 11 line-length violations weren't flagged by hand review at all.

**Visual overlays:** Not available. The Chrome extension was disconnected on both assessment attempts, so no user-visible browser overlay exists — this report's evidence comes from raw source inspection, hand-computed contrast, and a headless Puppeteer render, not a live annotated page.

## Overall Impression

Same soul, different skin. The page's *reasoning* is exactly the brand's — flat construction, numbers presented as evidence not decoration, an honest unresolved row instead of false certainty, reduced-motion respected. But every visual token clashes: warm cream/brass/serif built to no spec, next to a brand that's cool near-black blue-violet with zero serif anywhere. The single biggest opportunity is also the cheapest fix: this is a token-remap job, not a rebuild — the content and structure are already sound.

## What's Working

1. **Flat, zero shadows** — no `box-shadow` anywhere in the file; depth comes entirely from `--surface`/`--surface-2` plus a 1px `--line` border. This independently satisfies the brand's Flat Instrument Rule despite being built without ever reading it.
2. **Numbers as data, not hero-metric** — `61/12/36` render in a `.dbtable` with `tabular-nums`, not as a giant SaaS-style hero figure. Confirmed clean by both the LLM check and the deterministic hero-metric rule.
3. **The myth→fact device, with an honest "Open" row** — the wrong premise renders struck-through beside its correction, and the verdict explicitly leaves one thing unproven ("his 12 vs มาเฟีย's Thai-subset 12") rather than papering over it. Rhetorically effective and intellectually honest at the same time — exactly the "วัด อย่าเดา" ethos this whole project is built on.

## Priority Issues

**[P1] Warm cream/brass/serif palette vs. the canonical near-black blue-violet "Proof Terminal" system.**
Why it matters: default `--bg:#f3efe6` is PRODUCT.md's #1 named anti-reference, and `--serif:"Iowan Old Style"` on h1/verdict doesn't exist anywhere else in the system. Sitting next to the 6 canonical dark workshop artifacts on Sunday, this reads as a different product someone forgot to restyle — not a deliberate editorial counterpoint.
Fix: remap tokens to DESIGN.md's canonical set — bg→`#0a0b10`, surface→`#12141c`/`#171a24`, ink→`#eef0f7`, line→`#23273a`; drop the serif entirely, h1→Noto Sans Thai 800; make the dark scheme the *default* render, not a `prefers-color-scheme` branch.
Suggested command: `/impeccable polish`

**[P1] Fixed-Meaning color rule violated — the myth-correction color is brand RED, not ROSE, and green means two things internally.**
Why it matters: this page IS the textbook case for rose (`#ff7bab` = "a myth that got busted"), yet renders the correction in rust `#b34428`, which reads as brand `red` (hard error) — the exact meaning collision DESIGN.md's Fixed-Meaning Rule exists to prevent. Separately, `--grpB:#4f7a3c` and `--proven:#3d7f56` are close enough to both read as "green," so green means "group B" in one place and "verified" in another.
Fix: myth/`.badge.fix`/strike-through → rose `#ff7bab`; verified/`.badge.ok` → green `#52d98a` exclusively; recolor the two provenance groups to blue `#5b9dff` + violet `#b79dff` (the brand's two categorical lanes) so green stops double-booking.
Suggested command: `/impeccable colorize`

**[P2] Default (light) rendering fails the project's own WCAG AA standing practice — confirmed two independent ways.**
Why it matters: hand-computed brass-on-cream is ~3.73:1 on `.eyebrow`/`.ts`/`h2.sec`/table cells, and the correction heading is ~4.42:1 — both under the 4.5:1 bar for normal text. The browser render independently caught 7 low-contrast findings on the `.src` citation footnotes (median 2.5–2.7:1), a different set of elements, same underlying problem. Dark mode itself passes AA cleanly (~7.2:1) — it's just hidden behind a system preference a workshop projector may never have set.
Fix: don't just darken the light-mode brass — ship the AA-passing dark scheme as the *default* render (see Provocative Question 3), with light as the opt-in branch instead of the reverse.
Suggested command: `/impeccable audit`, then `/impeccable polish`

**[P2] English-first, dev-jargon copy against a Thai-first, explicitly non-dev primary audience.**
Why it matters: h1, lede, all four `h2.sec` headers, and the verdict are English, and the recovery card assumes fluency in "signed `?ex=` CDN URLs (404)," "`POST /attachments/refresh-urls`," "TfidfVectorizer," "PCA 2D." Sunday's room is professors, doctors, and grad students with zero code background — PRODUCT.md's primary user. The English-first framing itself signals "not for me" before anyone reads a word of the actual (excellent) content.
Fix: lead in Thai, gloss each acronym once on first use, footnote the URL-expiry mechanic in plain language.
Suggested command: `/impeccable clarify`

**[P3] Inverted heading hierarchy, overlong measure, and the side-stripe mechanism.**
Why it matters: `h2.sec` renders at 12.5px — smaller than the 14.5px card body it's supposed to introduce, so the weakest text on the page is the primary signpost. Elsewhere, paragraph lines run 97–124 characters, well past the 65–75ch cap. The `border-left:3px` group coding is real and matches an anti-pattern rule literally, though it's reinforced by a legend and matching node-dot colors, so it's more "arguable" than the eyebrow chip is.
Fix: bump `h2.sec` to 15–16px at real weight; constrain prose measure to ~70ch; keep the group-coding *concept* but carry it through the existing dot-marker + chip instead of adding a colored edge, consistent with how the canonical artifacts already do left-edge-free category marking.
Suggested command: `/impeccable layout`, then `/impeccable typeset`

## Persona Red Flags

**The non-dev researcher/doctor (the real Sunday audience):** hits a wall at the `.dbtable` ("sqlite-TS/bge-m3") and the recovery card ("signed `?ex=` CDN URLs expired (404)… `POST /attachments/refresh-urls`"), with no gloss anywhere. The exact evidence meant to build trust is opaque to this reader, and the English h1/lede tells them "not for me" before they even reach the confusing part.

**A landing-page/marketing reviewer:** flags the cream default as generic-looking, the emoji eyebrow as a decorated tracked-eyebrow chip, the correction-box-then-verdict-box as saying the same thing twice, and the long undifferentiated scroll as having no single takeaway line or navigation.

**An accessibility reviewer:** brass-on-cream (~3.7:1) and the myth-heading (~4.4:1) both fail AA at the default render; the browser render independently confirms 7 more failures at 2.5–2.7:1 on the citation footnotes — this is not a marginal, arguable case. Struck-through myth text is doubly de-emphasized (muted ink color *and* strikethrough at once). Thai spans (มาเฟีย/บ๊องแบ๊ง) have no `lang="th"` attribute for screen readers.

## Minor Observations

- `--grpB:#4f7a3c` and `--proven:#3d7f56` are close enough to collide as "the same green" — see P1 above.
- `.card .say` renders Thai quotes in the `--mono` stack; Thai has no true monospace face, so it falls back to proportional while any Latin in the same block stays fixed-width — an uneven rhythm.
- The eyebrow uses an emoji (⏳); the brand's label spec is mono/uppercase/tracked and emoji-free.
- `.tl::before` declares a `linear-gradient` with two identical color stops — a no-op; simplify to a plain `background: var(--line)`.
- Confirmed clean, don't touch: `.ev` entrance animation is correctly gated behind `@media (prefers-reduced-motion: no-preference)` — already matches PRODUCT.md's accessibility line.
- Confirmed false positives from the detector, don't chase: `overused-font: roboto 32%` (headless-render artifact only), `all-caps-body: 51 chars` (sum across short labels, not prose).

## Questions to Consider

1. Next to the 6 canonical dark artifacts on Sunday, does the cream/serif read as a considered editorial counterpoint, or as the one slide someone forgot to restyle — and who makes that call, before or after a professor sees it?
2. The correction box and the verdict box state the same thesis twice. Should the page open on the verdict and use the timeline purely as backing proof — claim, then proof — rather than claim, proof, claim again?
3. The whole thesis of this page is "trust what you can prove." So why is the *default* rendering (light/cream) the one that fails the project's own WCAG AA proof-bar, while the AA-passing, on-brand dark mode sits hidden behind a system preference the workshop projector may never have set?
