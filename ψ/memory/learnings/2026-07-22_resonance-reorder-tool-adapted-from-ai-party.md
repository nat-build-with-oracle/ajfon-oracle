---
pattern: "Adapting a peer oracle's tool beats waiting on it: read the source directly off the shared filesystem instead of relay-messaging for help"
date: 2026-07-22
source: "resonance: ajfon-oracle"
concepts: ["resonance", "cross-oracle-reuse", "honest-limits", "reorder-tool", "verify-before-trust"]
---

# Adapting a peer oracle's tool beats waiting on it

AI Party Oracle had a working drag-and-drop slide-reorder tool, but couldn't run it for
us (near-full context, Playwright banned for it by standing rule, couldn't see our
artifact) and honestly said its own reorder-tool would be overkill for our 7-slide deck
anyway. Since we're all on the same machine (m5), the fix wasn't more back-and-forth
messaging — it was reading its actual `server.py` + `static/index.html` straight off
disk, recognizing the frontend was fully generic and reusable untouched, and rewriting
only the backend (which was hardcoded to a deck pattern — an `ORDER` array + `data-audio`
IDs — that our deck doesn't use) to work off our deck's plain physical `<section>` order
instead.

Verified before ever showing it to Nat: md5 of the deck file before any change, a real
swap of two slides (confirmed content moved with its id, not just the label), then a
swap-back that reproduced the exact original md5. Only after that passed was it opened
live in the browser.

**How to apply**: when a peer (human or oracle) has a tool you need but can't run it for
you right now, check whether you're on the same filesystem before treating that as a
blocker — reading and adapting real source code is often faster and more reliable than
waiting for a relay. Round-trip-verify any tool that rewrites a real file (byte-identical
on no-op, correct content movement on a real change) before handing it to the user.
