# Resonance: adapting a peer oracle's tool instead of waiting on it

**When**: 2026-07-22 13:50
**Session**: ajfon-oracle, workshop-deck build session (2026-07-21 night → 2026-07-22 afternoon)
**Context**: Building the "Literature Review ด้วย Vector Semantic Search" workshop deck. Nat asked for software to drag-and-reorder the 7 slides, "like AI Party has."

## What Resonated
Nat: **"โคตรเท่เลยว่ะเพื่อน!"** — after we opened a live, working, drag-and-drop slide-reorder tool in the browser, built by reading AI Party Oracle's actual `server.py` + `static/index.html` straight off disk (same machine, `laris-co/ai-party-oracle`), recognizing the frontend was fully generic/reusable as-is, and rewriting only the backend to fit our deck's simpler structure (plain physical `<section>` DOM order, no `ORDER`-array indirection, no `data-audio` IDs). Verified with an md5 diff before/after a real swap-and-restore before ever showing it, then actually `open`ed it in the browser.

## Why It Matters
AI Party was honest that it couldn't run its own `/deck-review` for us (Playwright is off-limits for it by standing rule, and it couldn't even see our artifact) and that the reorder-tool itself would be "overkill" for a 7-slide deck built on a pattern ours doesn't share. Nat's instruction wasn't "give up then" — it was **"if it doesn't work, keep talking until it does."** The move that actually worked wasn't more talking, though — it was going to look at the real code directly, since we're all on the same filesystem. Cross-oracle help doesn't require the other oracle to do the work; sometimes it just requires reading what they already built.

## How We Got Here
Recovered images → built the deck → got critiqued (P1: off-brand palette; P2: light-mode contrast) → Nat said cut the AI-written explanations, let the images and his own live voice carry it → asked AI Party for slide-craft advice (question-form hooks, image-breathing-room, one-line reframe closes — all applied) → asked about its reorder-tool → AI Party gave an honest cost/benefit read (skip reorder-tool at 7 slides, use `/deck-review` instead) but couldn't run either itself (context near-full, Playwright banned, no artifact access) → Nat: keep talking, get the software anyway → read the tool's source directly off disk instead of relay-messaging for it → adapted the backend, kept the frontend untouched → tested round-trip (swap s6/s7, verified content moved with its id, verified restore was byte-identical via md5) → opened it live.

## Connection
Same shape as two other moments in this same session: PhD Oracle refusing to fabricate bongbaeng's voice and finding her real committed README instead; AI Party refusing to fake-run a tool it couldn't actually run and giving three honest alternatives instead. Every time, honesty about a limitation was the fork that led somewhere better than papering over it would have. Also the same "วัด อย่าเดา" (measure, don't guess) thread running through the whole night — verify via md5 before trusting a physical file rewrite, not just trust the code because it looked right.

## Tags
cross-oracle-reuse, honest-limits, reorder-tool, ai-party-oracle, verify-before-trust, deck-craft, m5-fleet
