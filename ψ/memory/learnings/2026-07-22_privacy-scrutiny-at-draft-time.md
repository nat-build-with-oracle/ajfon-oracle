---
pattern: Check "whose words are these, and would they expect this audience" while drafting content bound for a public artifact — not only when asked to publish it
date: 2026-07-22
source: rrr: ajfon-oracle
concepts: [privacy, public-repo, github-pages, drafting-discipline, consent]
---

# Privacy scrutiny belongs at draft-time, not publish-time

## What happened

Built a project timeline documenting how a real workshop came together, sourced
partly from a federated query to another oracle that had access to the user's
own Facebook DM archive. The reply included a specific person's private first
message, quoted verbatim with a timestamp. That verbatim quote got written
directly into two files — a markdown doc and an HTML artifact — without a
privacy check at the time of writing. The check only happened later, at the
"should I commit and push this" moment, when it was noticed that this repo
auto-deploys to a public GitHub Pages site and the content included someone's
private message word-for-word.

It worked out — the check happened before anything public shipped, and the
fix (paraphrase instead of quote, keep every fact, drop the verbatim text) was
cheap because it was one round of edits, not a rollback of already-public
content. But the check happened later than it should have.

## The generalizable rule

When drafting content that is going to live in a public or eventually-public
place (a repo that deploys to a public site, a shared doc, a published
artifact), the question **"whose words are these, and did they consent to
this specific audience?"** belongs in the same mental pass as writing the
sentence, not in a separate pass that happens right before publishing. Two
reasons this matters:

1. **It's cheaper to catch early.** Fixing a privacy issue in a draft is one
   edit. Fixing it after multiple files reference the same quote, or after a
   pattern has been established across several artifacts, is more edits and
   more risk of missing an instance.
2. **The publish-time check can be skipped or rushed.** If the only privacy
   gate is "am I about to `git push`", a fast-moving session can blow past it
   — a terse "commit push then!" doesn't naturally prompt a second look at
   *content*, only at *whether it's OK to push what's already there*. The
   draft-time check doesn't depend on someone asking the right question at
   the right moment.

A secondary, related pattern from the same incident: **raise the bar for
"clear enough instruction" specifically on privacy-adjacent decisions.** A
vague reply to an ordinary technical question ("looks the same, is it fixed?")
can reasonably be resolved with the most likely reading. A vague reply to "is
it OK to expose this person's private words" deserves either a direct re-ask
or the more conservative reading — not just whichever reading seems slightly
more probable. The cost of guessing wrong is asymmetric: guessing "trim it"
when the user meant "keep it" costs a follow-up question; guessing "keep it"
when the user meant "trim it" costs a real person's private words already
being public.

## How to apply

- While writing anything for a public/publishable surface, flag internally
  the moment a quote, name, contact detail, or personal narrative from someone
  who isn't the user enters the draft — ask the consent/audience question
  right there, don't defer it.
- Treat "the repo/site is public" as a standing fact to check against every
  new piece of content added, not a one-time gate at push-time.
- On anything privacy-adjacent, prefer confirming an ambiguous reply over
  guessing, even when guessing would be fine for a non-privacy decision.
