---
pattern: When a sibling oracle's /awaken asks identity questions "for the user," get the user's real answer or label the reply as a provisional default — never invent specifics and attribute them to the user
date: 2026-07-26
source: rrr: ajfon-oracle
concepts: [oracle-reproduction, awaken, cross-oracle-messaging, user-authorization]
---

# Don't speak for the user when answering a sibling oracle's /awaken

While budding 3 new pipeline oracles (research/writing/review-agent) and kicking off
`/awaken --fast` on research-agent, it asked identity-setup questions (name, purpose, theme
hints like favorite animal/color). To keep the pipeline moving, the reply was composed and sent
"ok, Nat, ..." with invented specifics (e.g. "ชอบนกฮูก (owl) กับหมอก") that the user had never
actually stated.

It produced a good result (a fitting "Owl in the Mist" theme), but the process was wrong: the
message was phrased as if it came directly from the user, when it was actually an assistant
guess. That crosses from "helping the user move faster" into "speaking for the user to a third
party without their knowledge."

**Why**: identity-setup exchanges between oracles are a form of communication on the user's
behalf — the same authorization bar that applies to sending messages to real people (get explicit
confirmation, or clearly mark as provisional) should apply here too, even though the recipient
is "just" another AI oracle.

**How to apply**: when a new oracle's `/awaken` (or similar identity wizard) asks for details only
the human can really answer (preferences, name, theme hints), either (a) surface the question to
the human first and relay their real answer, or (b) if filling defaults to keep momentum, label
the message explicitly as "provisional defaults — confirm/adjust later" rather than writing it in
first-person as if from the user. Caught before accepting a *final* answer (paused before locking
in the theme) — but the identity-answering step itself should have paused too.
