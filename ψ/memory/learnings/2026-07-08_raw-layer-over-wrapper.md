---
pattern: When a fleet CLI wrapper returns wrong/truncated content, drop to the platform's raw API or DB — verify identity before summarizing.
date: 2026-07-08
source: "rrr: ajfon-oracle"
concepts: [maw, hermes, atlas, discord-api, duckdb, verification, tool-trust]
---

# Trust the raw layer, not the convenience wrapper

**Context**: Asked to read a Discord thread via `maw hermes`/`maw atlas`. The first `hermes read` returned stale/aggregated content that didn't even contain the requested subject ("ajfon"). I summarized it anyway and was corrected twice.

**Rule**: When a read-tool's output does not contain the subject you asked for, STOP — cross-check the channel/thread identity (e.g. `atlas threads <guild>`) before writing any summary. Never present convenience-layer output as ground truth.

**Corollary — attachments**: For "bring me the images/attachments" tasks, the fleet CLI wrappers (`atlas read` caps content at 200 chars and drops attachment URLs entirely) cannot deliver. Go straight to the platform REST API:
`curl https://discord.com/api/v10/channels/<id>/messages?limit=100 -H "Authorization: Bot $TOKEN"` → returns real `attachments[].url` CDN links you can download and actually view.

**Corollary — search**: Before a wide grep over a large personal archive, check the obvious named location first (a repo named for the subject), then orchestrate a fan-out workflow. A blind keyword sweep pattern-matches unrelated veins (e.g. `ฝน` = rain, `ต้มเบียร์` = beer) and dumps noise into context.

**Evidence**: Source of truth was `~/fb_archive.duckdb` thread "กมลทิพย์ เลิศชัยสถาพร" (52 msgs); a 5-agent workflow (wf_44e33812-630) proved zero public FB posts exist. Artifact shipped: https://claude.ai/code/artifact/91318ca3-cbcf-43fa-9df3-756be25069fa
