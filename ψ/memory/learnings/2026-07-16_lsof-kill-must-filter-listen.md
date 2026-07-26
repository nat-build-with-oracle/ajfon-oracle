---
pattern: lsof-kill-must-filter-listen
date: 2026-07-16
source: retrospective 20cf7c44 (ajfon-oracle, closing localhost:8890/8899 dev servers)
concepts: [lsof, process-management, port-cleanup, collateral-damage, tcp-listen-vs-established]
---

# Killing "the process on a port" must filter to LISTEN state, or you kill its clients too

## Pattern

`lsof -ti:PORT` returns the PID of **every process with any socket touching that port** —
the listening server AND every client currently connected to it (ESTABLISHED connections).
Piping that straight into `kill`/`xargs kill` will kill innocent bystander processes that
merely opened a connection to the port, alongside the server you actually meant to stop.

## What happened

Asked to close two local dev servers (`localhost:8890` a Python http.server, `localhost:8899`
a JupyterLab instance), the fix ran:

```sh
lsof -ti:8899 | xargs kill
```

This killed the JupyterLab server as intended, but also killed a `bun server.ts` process
(PID 41037) and a WebKit renderer process that were unrelated — they just happened to hold
open TCP connections to port 8899 (e.g. a browser tab or another local tool that had
connected to it), not processes serving it. The user only asked to close two named ports;
the blast radius silently took out a third, unrelated service. Caught in the same turn by
re-checking `ps` on the killed PIDs, but only after the fact — the collateral kill had
already happened.

## Rule for any Oracle on any project

- Never run `lsof -ti:PORT | xargs kill` (or any bare "find PIDs on this port, kill them"
  one-liner) without restricting to the LISTEN state first:
  `lsof -ti:PORT -sTCP:LISTEN | xargs kill` — this returns only the process(es) actually
  bound/listening on that port, not every client connected to it.
- Before killing anything by port, list what you're about to kill with enough context to
  eyeball it (`ps -p $PID -o pid,command`) — command name mismatches (a `bun` or browser
  process showing up when you expected `python`/`jupyter`) are the tell that the match is
  too broad.
- After any port-based kill, verify twice: (1) the target port is actually closed, and
  (2) nothing else that mattered also died — check sibling services you know are running
  (other servers on the same host) are still alive, not just that the requested ones are gone.
- This generalizes beyond `lsof`: any "kill by resource identifier" shortcut (kill by port,
  by working directory, by parent PID, by name substring) risks matching more than the
  single target the human named. Prefer the most specific filter the tool offers before
  piping into a destructive command.
