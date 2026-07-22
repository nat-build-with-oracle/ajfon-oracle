# Workshop Timeline — ARRA Oracle Second Brain for Research

Full record of how a set of lost research visualizations became the proof-backed
centerpiece of a live public workshop. Two threads, one story: the **technical
thread** (the images themselves — made, lost, recovered, proven) and the
**event thread** (the real, dated, capped, donation-based public workshop they
now teach in). Kept in the repo, not just the vault, so it survives independent
of any one session.

## The event (real, public, dated)

**ARRA Oracle Second Brain for Research** — free online workshop
**Organizer**: Gradpassion ร่วมกับ อ.นัท Nat Weerawan
**Teacher**: อ.นัท Nat Weerawan, ผู้สร้างแนวคิด ARRA Oracle
**Date**: Sunday 26 July 2026, 09:00–12:00 (GMT+7)
**Format**: Live via Zoom; replay via a closed Facebook group
**Audience**: อาจารย์ นักวิจัย นักศึกษา แพทย์ บุคลากรสุขภาพ และผู้สนใจทั่วไป — explicitly not dev-only ("ไม่ต้องเป็นสาย Dev ก็เรียนได้")
**Cost**: Free — donation-based, to any hospital of the attendee's choosing
**Capacity**: 300 seats (Zoom limit) — registration closes early if full
**Registration closes**: 24 July 2026, 20:00 (GMT+7)

**Workflow taught in the class**:
1. Paper → Agent summarizes, tags, stores into Memory
2. Old knowledge retrieved and extended into new ideas / research gaps
3. Research Agent → Writing Agent → Review Agent, chained

**Registration**: https://forms.gle/Mpb7f1ymVPuum8qK7
**After registering**: message LINE https://lin.ee/xSXARyYD with "ลงเรียน Oracle" + full name
**Learn about ARRA Oracle**: Oracle 101 (https://oracle101.vercel.app/index.html) · "Oracle คืออะไร" (https://ai-library-th.pages.dev/)

**Donation** (optional, any hospital or the Red Cross accepted — https://organdonate.redcross.or.th/donate/money):
- มูลนิธิโรงพยาบาลสงขลานครินทร์ — ธนาคารไทยพาณิชย์ สาขา ม.สงขลานครินทร์ เลขที่ 565-2-09777-0
- มูลนิธิโรงพยาบาลสงขลานครินทร์ — ธนาคารกรุงเทพ สาขา ม.สงขลานครินทร์ เลขที่ 641-0-15655-5
- (transferring by account number qualifies for 2x tax deduction)

Announced via Grad Passion's Facebook page, hashtags `#Gradpassion #ARRAOracle #AIforReserach #AIforProductivity`.

> ⚠️ **Unverified**: the name "Gradpassion" does not appear anywhere in Nat's own
> Facebook DM archive with อาจารย์ฝน (checked by facebook-timeline-oracle, 0 hits
> across the whole archive). Every FB conversation refers to her community as
> "AI for Research" / "AI for Research Community" instead. Either "Gradpassion"
> is a business/page name she operates under that surfaced through a different
> channel (Discord, LINE, email — all outside this archive's 12 July export
> cutoff), or it's a rename that happened after the archive was captured. Not
> contradictory, just not independently confirmed yet — worth a direct check if
> it matters for anything official.

## How this workshop came to be

Source: Nat's own Facebook DM thread with กมลทิพย์ เลิศชัยสถาพร (อาจารย์ฝน) — friends
since 2026-05-04, 61 messages total, retrieved via facebook-timeline-oracle's
`contact_personas` / `friends_combined` archive.

**She reached out first — not Nat.** อาจารย์ฝน is a doctor and founder of the
Facebook community "AI for Research." A member of her own community recommended
Nat's Oracle concept to her; she then contacted Nat directly, unprompted.

**First message** (2026-05-25 07:52:44, paraphrased — not quoted verbatim out of
respect for a private DM): she introduces herself as a doctor and the founder of
"AI for Research," says a community member recommended the Oracle concept to
her, and that she sees an opportunity in it. Four minutes later (07:56:42) she
adds that she'd just joined the Discord and YouTube communities, but that she'd
much rather learn directly from Nat.

**How the date got locked**:
- 2026-06-04 — she proposes organizing "Oracle & Second Brain for Research," an
  online 3-hour workshop, on a Saturday
- 2026-06-06 — she offers three date options: Sat 11 Jul evening, Sat 25 Jul
  evening, or Sun 26 Jul morning/evening
- 2026-06-09 23:22:43 — **Nat replies "น่าจะช่วง 25/26 ก็ดีค้าบ"** — the date is set

Worth noting: Nat kicked off the fleet-wide literature-review exercise (the
first row of the timeline below) exactly **one day** after locking this date —
the workshop-prep work and the workshop commitment are directly connected, not
a coincidence of timing.

## Unified timeline

| Date | Thread | What |
|---|---|---|
| 2026-05-04 | 🎓 event | อาจารย์ฝน (กมลทิพย์ เลิศชัยสถาพร) becomes Facebook friends with Nat |
| 2026-05-25 07:52 | 🎓 event | อาจารย์ฝน sends the first message — introduces herself, a doctor and founder of "AI for Research," recommended by a community member, interested in Oracle |
| 2026-06-04 | 🎓 event | She proposes organizing an "Oracle & Second Brain for Research" online workshop |
| 2026-06-06 | 🎓 event | She offers three date options (11 Jul / 25 Jul / 26 Jul) |
| **2026-06-09 23:22** | 🎓 event | **Nat locks the date**: "น่าจะช่วง 25/26 ก็ดีค้าบ" |
| 2026-06-10 | 🔬 technical | Nat kicks off a fleet-wide literature-review exercise on Discord — "ทุกคนครับ ลิสต์ literature review มาทางนี้" (one day after the date lock — directly connected) |
| 2026-06-10 | 🔬 technical | Fleet builds independent paper vector-DBs as a workshop exercise: มาเฟีย (ChromaDB, claimed 61 papers — later found unverifiable), บ๊องแบ๊ง (sqlite + transformers.js, 12 papers, code-verified), Jizo (bge-m3, claimed 36 — unverifiable), Orz (17 papers, code-verified), SomBo, Vessel |
| 2026-06-11 | 🔬 technical | DustBoy PhD Oracle finds บ๊องแบ๊ง's PCA-scatter + semantic-search images, reposts with credit ("Group A") |
| 2026-06-12 05:21–05:33 | 🔬 technical | DustBoy builds its own t-SNE / similarity-matrix / concept-network / PCA charts ("Group B") from 50 thesis concepts — two rounds, first superseded, second kept |
| 2026-07-21 23:10–23:18 | 🔬 technical | Images found missing (Discord CDN signed URL expired, 5+ weeks later); atlas-oracle recovers the real bytes; digger-oracle commits all 8 images permanently |
| 2026-07-22 | 🔬 technical | DustBoy + ajfon-oracle independently cross-verify the story — correct a real myth (61/40/12 papers were never one corpus; "40" never existed at all) |
| 2026-07-22 | 🔬 + 🎓 merge | Images + corrected provenance timeline shipped into the real workshop deck (`artifacts/lit-review-vector-search.html`) as new slides, alongside the deck's existing content |
| 2026-07-22 | 🔬 technical | `/impeccable audit` run on the deck; a real CSS cascade-ordering bug found and fixed (three instances) plus a design-system color violation; verified by direct measurement, not eyeballing |
| 2026-07-22 | 🔬 technical | Fixes committed (`83e74c8`, `f03af35`) and pushed to `origin/main` |
| — | 🎓 event | Workshop announced publicly via Grad Passion's Facebook page |
| **2026-07-24 20:00** | 🎓 event | **Registration closes** (300-seat cap, or earlier if full) |
| **2026-07-26 09:00–12:00** | 🎓 event | **Workshop live on Zoom** — deck built from this exact provenance story is the teaching material |
| after 2026-07-26 | 🎓 event | Replay available via closed Facebook group |

## Where things stand (as of 2026-07-22)

- Deck: `artifacts/lit-review-vector-search.html` — 9 slides (8 visible + 1 hidden), audited, bug-fixed, pushed
- Provenance proof: `artifacts/timeline-embedding-space-provenance.html` — full cross-oracle verified trace
- Reorder/present tool: `tools/deck-reorder/` (local, `python3 tools/deck-reorder/server.py`)
- Older, separate 17-slide speaker deck also exists untouched: `artifacts/workshop-deck.html` — not yet reconciled with the new one; decide which (or both) gets presented
- Open item: one live full run-through of all 9 slides before the 26th
