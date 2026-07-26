# Time-Travel: ARRA Oracle Second Brain Workshop — Full Provenance

**Mode**: --prove --timeline
**Target**: ajfon-oracle (+ cross-oracle: DustBoy-Phd-Oracle, digger-oracle, atlas-oracle, facebook-timeline-oracle, Hermes Gateway)
**Timestamp**: 2026-07-24 08:51 GMT+7

## Claim

That the "ARRA Oracle Second Brain for Research" workshop (Sun 26 Jul 2026,
09:00–12:00) has real, traceable, evidence-backed preparation behind it —
both the human collaboration that produced the invitation, and the technical
material (recovered images, provenance proof, two decks, a full runsheet)
built to teach it — rather than being an assumed or reconstructed narrative.

## Evidence

### Source 1: Facebook DM archive (facebook-timeline-oracle, `fb_own_archive.duckdb`)
- **What**: อาจารย์ฝน (กมลทิพย์ เลิศชัยสถาพร) — doctor, founder of FB community
  "AI for Research" — initiated contact with Nat, unprompted, after a member
  of her own community recommended the Oracle concept to her
- **When**: friends since 2026-05-04; first message 2026-05-25 07:52:44
- **Where**: `contact_personas` / `friends_combined` tables, queried live via
  federation to `06-facebook-timeline` (maw hey, 2026-07-21 23:09–23:12)
- **Confidence**: verbatim (direct DB query result relayed by the oracle)

### Source 2: Discord thread "training aj Fon" (Hermes Gateway, live-read)
- **What**: Nat pasted a screenshot of the same FB conversation into Discord
  for Hermes Oracle to help draft a reply + curriculum. Reveals her 3 offered
  slots (Sat 25 Jul 15:00–18:00 / Sun 26 Jul 09:00–12:00 / Sun 26 Jul
  13:00–16:00), Hermes's drafted reply (recommending Sat 25 Jul), and a full
  5-block 3-hour curriculum outline
- **When**: thread messages dated around 2026-06-04 to 2026-06-09; read live
  2026-07-23 via `maw hermes read 1521898760903458896 20`
- **Where**: guild "nat's ARRA Oracles" (`1500665320501940267`), thread ID
  `1521898760903458896`, 6 messages total
- **Confidence**: verbatim — direct live read of the primary Discord content,
  higher fidelity than Source 1 for the specific date-option wording

### Source 3: Git commits (this repo, highest authority)
| Commit | Date (GMT+7) | What |
|---|---|---|
| `e34610f` | 2026-07-16 13:12 | Deck B (`workshop-deck.html`, 17 slides) shipped, reviewed via 4-lens workflow |
| `fe85ad6` | 2026-07-16 13:46 | GitHub Pages root redirect + `.nojekyll` |
| `5559848` | 2026-07-16 15:07 | QA skills vendored; workshop deck noted |
| `83e74c8` | 2026-07-22 17:00 | Deck A (`lit-review-vector-search.html`) gets provenance timeline slide + PCA panel |
| `f03af35` | 2026-07-22 21:23 | Deck A: reorder-tool deep-link bug fixed; CSS cascade-ordering bug found + fixed (3 instances), verified by direct `getBoundingClientRect`/`getComputedStyle` measurement |
| `ae198bf` | 2026-07-22 23:25 | `WORKSHOP-TIMELINE.md` created — real event logistics + origin story (source 1) |
| `278b5fa` | 2026-07-22 23:31 | Private DM content paraphrased, not quoted verbatim, before push (privacy correction) |
| `2357fc1` | 2026-07-23 00:07 | `WORKSHOP-RUNSHEET.md` created; origin story corrected with source 2; old-vs-new deck question resolved (both used, sequenced) |

All 8 commits confirmed pushed to `origin/main` (verified via `git log origin/main..HEAD` returning empty as of 2026-07-24 08:51).

### Source 4: Cross-oracle provenance chain (the demo content itself)
- **What**: the literature-embedding-space images (t-SNE, similarity matrix,
  concept network, PCA) that Deck A demonstrates as "real research workflow"
  were built 2026-06-12 by DustBoy PhD Oracle (self-generated, 50 thesis
  concepts, 8 clusters) + บ๊องแบ๊ง (PCA scatter + semantic search, 12
  code-verified papers), lost to an expired Discord CDN URL, recovered
  2026-07-21 by atlas-oracle + digger-oracle, and cross-verified twice
  (DustBoy self-audit + this session's independent agents) on 2026-07-22 —
  correcting a real myth (61/40/12 papers were never one corpus; "40" never
  existed)
- **Where**: `artifacts/timeline-embedding-space-provenance.html` (full trace,
  committed `83e74c8`); origin trace at DustBoy-Phd-Oracle
  `ψ/memory/traces/2026-07-21/1650_time-travel_embedding-space-provenance-CORRECTED.md`
- **Confidence**: verbatim, git-verified, independently cross-checked

### Source 5: Live system state (verified this session)
- **What**: Deck A currently serves 9 total slides (8 visible + 1 hidden),
  all verified end-to-end via headless-browser screenshot on 2026-07-22
  (post-fix) with no rendering regressions
- **Where**: `tools/deck-reorder/server.py` (local, port 8766), confirmed via
  `curl http://127.0.0.1:8766/api/slides` at time of writing (8 visible / 9 total)
- **Confidence**: verbatim, live-checked at proof time, not from memory

## Temporal Map

```
2026-05-04  — อาจารย์ฝน becomes FB friends with Nat
2026-05-25  — she messages first, unprompted, via community referral
2026-06-04  — she proposes an "Oracle & Second Brain for Research" workshop
2026-06-06  — she offers 3 specific slots
2026-06-06  — Nat pastes the chat into Discord; Hermes drafts a reply (Sat 25 Jul) + curriculum
2026-06-09  — Nat's actual reply is vaguer than the draft: "น่าจะช่วง 25/26 ก็ดีค้าบ"
2026-06-10  — (+1 day) Nat kicks off fleet-wide literature-review exercise
2026-06-11  — DustBoy reposts บ๊องแบ๊ง's images, credited ("Group A")
2026-06-12  — DustBoy builds its own t-SNE/similarity/network/PCA charts ("Group B")
     ⋮        (images live on Discord only, un-backed-up)
2026-07-16  — Deck B (17-slide core-concepts curriculum) shipped, 4-lens reviewed
2026-07-21  — images found missing (CDN expiry); atlas + digger recover them
2026-07-22  — provenance cross-verified twice; myth corrected; Deck A gets the
              real images + proof timeline; CSS bugs found and fixed via direct
              measurement; WORKSHOP-TIMELINE.md written
2026-07-23  — origin story corrected via primary Discord source; deck question
              resolved (both decks, sequenced); WORKSHOP-RUNSHEET.md written —
              full 3-hour block-by-block plan, demo data locked to Nat's own
              verified PM2.5/DustBoy corpus (not generic medical papers)
2026-07-24  — (today) registration closes 20:00; this proof written
2026-07-26  — workshop, 09:00–12:00, live on Zoom
```

## Verdict

**PROVEN**

**Confidence**: high
**Evidence sources**: 5 independent sources checked (FB DM archive, live
Discord read via Hermes Gateway, git history, cross-oracle provenance chain,
live system state)
**Key finding**: every major claim in the workshop's preparation traces to a
primary source with a timestamp — the human collaboration (อาจารย์ฝน's
outreach, the date negotiation, the Sat-drafted-vs-Sun-actual discrepancy) and
the technical material (image recovery, verification, both decks, the
runsheet) are independently verifiable, not reconstructed narrative. Where two
sources disagreed (the exact date options, per Source 1 vs Source 2), the
more primary source was preferred and the discrepancy was recorded rather
than smoothed over — consistent across every stage of this preparation.

## What's Missing

- The "Gradpassion" organizer name has zero hits in the FB DM archive itself
  (flagged in `WORKSHOP-TIMELINE.md`) — not resolved, still open
- Whether the HTTP-400 bug in `maw hermes read` (found 2026-07-08, unrelated
  incident) was ever fixed — not determined, no fix commit found
- No record of Nat's *specific* choice of 2-3 demo papers for the live
  tag/summarize exercise — corpus is locked (bongbaeng-12 / Orz-17), specific
  papers are not yet picked (this is Nat's own remaining action, noted in
  `WORKSHOP-RUNSHEET.md`)
