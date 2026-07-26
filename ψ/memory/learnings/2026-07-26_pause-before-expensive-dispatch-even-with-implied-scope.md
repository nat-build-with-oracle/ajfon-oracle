---
pattern: A user's original request can imply the full scope of a task without that being the same as confirming an expensive, irreversible-feeling step within it — pause at the pipeline's natural checkpoint and get fresh confirmation before spawning a large multi-agent dispatch.
date: 2026-07-26
source: rrr: ajfon-oracle
concepts: [multi-agent-orchestration, scope-confirmation, background-agents, workflow-tool]
---

# Pause before expensive dispatch, even with implied scope

"Help me write a book, full story of our journey" implies the whole pipeline — outline,
draft, render, publish. It would have been easy to read that as blanket authorization
and go straight from outline to spawning 15 parallel drafting agents. That's a real
commitment (time, tokens, and — this being workshop morning — attention that could be
needed elsewhere), and the *implied* scope in the original request is not the same
strength of authorization as a fresh, explicit "yes, proceed" at the specific point
where the expensive step actually happens.

The pipeline this session was following already defines a natural checkpoint (outline →
prism review) for exactly this reason. Using it — showing the outline, running a quick
self-check, then asking a direct go/no-go before the dispatch — turned an assumed yes
into a confirmed one, at negligible cost (one question, answered immediately).

**How to apply**: when a task naturally has a cheap-to-produce artifact (outline, plan,
draft-of-drafts) before its expensive stage (parallel dispatch, irreversible write,
public publish), always surface that artifact and confirm before crossing into the
expensive part — regardless of how clearly the original request seemed to authorize the
whole thing. The pause costs one turn; skipping it risks a large wasted commitment if
the assumption was wrong.

Related: a second, smaller instance of "wrong tool for resuming an agent" this same
session — `Agent()` with a reused `name` spawned a fresh duplicate instead of resuming
the original; `SendMessage({to: name})` is the correct way to resume a named background
agent. Distinct lesson, adjacent context — see the full retro at
`/opt/Code/github.com/laris-co/ajfon-oracle/ψ/memory/retrospectives/2026-07/26/09.47_book-pipeline-launch-workshop-morning.md`.
