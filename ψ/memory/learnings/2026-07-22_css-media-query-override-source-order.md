---
pattern: A CSS @media override that "does nothing" is a source-order bug before it's a caching bug — same selector + equal specificity always resolves to whichever rule appears later in the stylesheet, media query or not
date: 2026-07-22
source: rrr: ajfon-oracle
concepts: [css, cascade, specificity, media-queries, debugging, measure-dont-guess]
---

# A silent CSS override is source-order, not cache

## The pattern

`@media (max-height:700px) { .foo { margin-top: 4px; } }` placed **earlier** in a
stylesheet than an unconditional `.foo { margin-top: 6px; }` placed **later** will
silently lose, 100% of the time the media query matches. Not intermittently, not
"depends on the browser" — deterministically, because CSS resolves ties (equal
selector, equal specificity) by **source position**, and wrapping a rule in
`@media` does not change its position or add specificity. It only adds a
condition for *whether* the rule is in the candidate set at all.

This is easy to miss because a nearby override in the SAME early media-query
block, touching a *different, non-conflicting* property on the same selector
(e.g. `display:none` where no later rule sets `display`), works perfectly — so
the pattern "put short-viewport tweaks in one early block near the top" looks
proven out, right up until one of those tweaks happens to conflict with a
property the base rule also sets.

## How this actually presented

A deck's short-viewport media query (already existing, positioned near the top
of the stylesheet, right after the base `.slide` rules) got a new line added to
handle a new component: `.timeline .text { font-size: 12px; }`. The component's
own base CSS, added later in the file in the normal "components" section, also
set `font-size` for `.timeline .text` (a responsive `clamp()`). Visually,
nothing changed between "before the fix" and "after the fix" — looked exactly
like a stale cache. Two fix attempts (different pixel values each time) were
made and re-tested with zero effect, reinforcing the caching suspicion. A
real cache investigation followed: fresh Chrome profiles, `--incognito`,
cache-busting query params, a "canary" render of an unrelated-but-known-working
override to rule out the media query not firing at all. The canary DID fire —
proving the query matched and the browser wasn't the problem — which is what
finally pointed at the CSS itself instead of the browser.

## The fix

Move the override to *after* the component's base rule in source order (or
raise its specificity, though reordering is cleaner and matches how the
surrounding correctly-working overrides were already positioned). Verified with
a debug overlay reporting `getComputedStyle(el).fontSize` directly — confirmed
the intended value only took effect once source order was fixed, not before.

## The generalizable rule

Before suspecting a cache, a build step, or "the browser is being weird" on any
CSS override that visually does nothing: **grep both rules and check which one
is textually later in the file.** If the later one shares the selector and
specificity, that's the whole bug, and it costs five seconds to rule in or out
— far cheaper than a caching investigation. Only chase caching once source
order is confirmed correct (or use a canary: re-test a different, unrelated,
already-known-working override at the same conditions first — if it fires, the
mechanism works and the bug is your CSS, not the delivery pipeline).
