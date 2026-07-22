---
name: deck-add-slide
description: Add/update a slide in the lit-review-vector-search.html workshop deck and regenerate its reorder-tool thumbnail — the full workflow used to add the provenance-timeline + PCA slides.
installer: create-shortcut
created_at: 2026-07-22T17:03:16+07:00
---

# /deck-add-slide

Add or edit a slide in `artifacts/lit-review-vector-search.html` (the ARRA Oracle
workshop deck) and keep the local `tools/deck-reorder` tool in sync — thumbnail
included. This captures the exact workflow used to add the provenance-timeline
and PCA slides on 2026-07-22.

## Step 0: Init

```bash
date "+🕐 %H:%M %Z" && lsof -nP -iTCP:8766 -sTCP:LISTEN
```

If nothing is listening on 8766, start the tool first: `python3 tools/deck-reorder/server.py &`

## The deck's shape

- **File**: `artifacts/lit-review-vector-search.html` — a single self-contained HTML
  file (dark theme, `--thai` font stack). ~1.9MB because 4 of the slides embed
  real PNGs as base64 `data:` URIs.
- **Slides are DOM order**: each is `<section class="slide[ active][ data-hidden]" data-id="sN">`.
  Display order = physical order in the file. The reorder tool *physically moves*
  these chunks on save — it has no separate `ORDER` array (unlike the ai-party-oracle
  tool this was adapted from).
- **Hidden slides**: `data-hidden` attribute + excluded from the JS `slides` array
  (`document.querySelectorAll('.slide:not([data-hidden])')`). The visible-slide
  count feeds `<div class="counter" id="counter">1 / N</div>` — that N is a static
  fallback string, **update it by hand** whenever the visible slide count changes
  (JS overwrites it on load via `show(0)`, but the raw HTML value should still be
  correct so there's no flash of a wrong number).

## Design-system components already in the CSS — reuse, don't reinvent

| Class | Use |
|---|---|
| `.eyebrow` (`<span class="n">…</span>` for the gold bit) | small mono label above the h2 |
| `h1` / `h2` + `.accent-{cyan,green,amber,gold,rose,red,violet}` | headline with one highlighted phrase |
| `.cards` / `.card` / `.card.hl` | 3-up card grid (`.hl` = highlighted/gold-bordered card) |
| `.callout` | green-bordered highlight box, one per slide max |
| `.figwrap` / `.figmat` (`.sm` modifier) / `.cap` | image + zoomable lightbox + caption |
| `.fig2` / `.fig2cap` | side-by-side image grid — CSS is `repeat(auto-fit,minmax(240px,1fr))` so it silently handles 2 **or 3** images, no CSS change needed to add a 3rd |
| `.ptl` / `.pev` / `.pev.warn` / `.pts` / `.pwho` / `.ptxt` | vertical dated timeline (added 2026-07-22 for the provenance slide) — `.warn` swaps the dot+timestamp to red for a "bad news" event |
| `.quote` | big closing-slide statement |

## Adding a new text-only slide

1. Pick a new `data-id` that doesn't collide (`grep -n 'data-id=' artifacts/lit-review-vector-search.html`).
2. Insert the `<section class="slide" data-id="sN">…</section>` block at the
   physical position you want it to appear (order = DOM order) using Edit with a
   short, unique anchor — e.g. right before the `<!-- 7 · Closing -->` comment.
3. Compose from the components table above. Keep Thai body text in `.ptxt`/`.d`/`.lead` (uses `--ink-soft`), keep one highlight color per slide max.
4. Update the counter fallback (`1 / N`) if this changed the *visible* slide count.

## Adding an image to a slide

**Never paste base64 through Edit** — a real PNG here runs 300–500KB of base64,
far too large for an Edit `old_string`/`new_string` and it'll blow the request up
for nothing. Instead, splice it with a small Python script (stdlib `base64` only):

```python
import base64, os
DECK = "/opt/Code/github.com/laris-co/ajfon-oracle/artifacts/lit-review-vector-search.html"
IMG  = "/path/to/image.png"
html = open(DECK, encoding="utf-8").read()
b64 = base64.b64encode(open(IMG, "rb").read()).decode("ascii")
figmat = ('<div class="figmat sm" role="button" tabindex="0" aria-label="ขยายภาพเต็มจอ">'
          f'<img src="data:image/png;base64,{b64}" alt="…" />'
          '<span class="zoom-hint">🔍 <kbd>Z</kbd></span></div>')
anchor = 'SOME_SHORT_UNIQUE_STRING_ALREADY_IN_THE_FILE'  # e.g. the end of the preceding figmat
assert html.count(anchor) == 1
html = html.replace(anchor, anchor + figmat, 1)
open(DECK, "w", encoding="utf-8").write(html)
```

Before writing an Edit/Read against this file at all, find long lines first —
`awk '{ if (length($0)>2000) print NR": "length($0) }' artifacts/lit-review-vector-search.html`
— and never `Read` those line ranges directly (each embedded image is one giant
line). Read a truncated copy instead if you need to see structure:
`awk '{ if (length($0)>2000) print substr($0,1,150)" ...[TRUNCATED]..."; else print }' deck.html > filtered.html`.

**Verify the right bytes landed** by comparing the base64 string length against
`4/3 × file-size-in-bytes` (± a few hundred for PNG metadata) rather than trusting
captions/alt text — this caught a real mismatch once (a caption said "PCA" while
the embedded bytes were actually a different image).

## Regenerating a thumbnail (do this after ANY slide content change)

The reorder tool shows a real "no thumbnail" placeholder (`.no-thumb`, see
`tools/deck-reorder/static/index.html`) for any `data-id` without a matching
`tools/deck-reorder/thumbs/<id>.png` — new slides always start with no thumb, and
edited slides keep their *stale* old thumb until you regenerate it. Existing
thumbs are `960×540` RGB PNG.

```bash
SCRATCH=$(mktemp -d)
DECK=artifacts/lit-review-vector-search.html
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Find this slide's index in the VISIBLE-slides array (0-based, hidden slides excluded)
# — easiest to just count data-id order in the file, skipping any data-hidden ones.
IDX=4   # example: 5th visible slide

sed "s/show(0);/show($IDX);/" "$DECK" > "$SCRATCH/verify.html"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=960,540 \
  --screenshot="tools/deck-reorder/thumbs/sN.png" \
  "file://$SCRATCH/verify.html"
```

Then confirm the live tool picked it up (no restart needed, it reads fresh every request):

```bash
curl -s http://127.0.0.1:8766/api/slides | python3 -c "
import json,sys
for s in json.load(sys.stdin)['slides']: print(s['id'], s['thumb'])"
```

## Gotchas learned the hard way

- **`file://` vs the real server**: opening the deck HTML directly (double-click,
  drag into a tab) loads it at a `file://…` origin. The "jump back to the reorder
  grid" shortcuts (**E** key, double-Esc) are deliberately gated to
  `location.pathname === '/deck'` and silently do nothing under `file://` — that's
  correct behavior, not a bug, since there's no grid to return to from a bare file.
  Always test/present via the **▶ Present (local)** button on `http://127.0.0.1:8766/`,
  never by opening the file directly.
- **Server reads the deck fresh every request** — no restart needed after editing
  the HTML, just refresh the browser tab.
- **`git commit` should exclude rejected drafts** — this deck went through at
  least one wrong-direction artifact before landing; don't sweep those into the
  same commit as the real deliverable.
- **`@media(max-height:700px)` overrides must come AFTER the base rule they
  override, in source order** — not just "somewhere inside a media query."
  When a media-query rule and a base (non-conditional) rule target the exact
  same selector with equal specificity, CSS breaks the tie by **source
  position**, not by which one is conditional. The deck's original
  `@media(max-height:700px){...}` block sits near the top of the stylesheet
  (right after `.slide`) — adding a new override for `.some-class` there while
  `.some-class`'s base definition lives further down means the override
  **silently loses every time**, no error, no warning, looks identical to a
  caching problem. Put the override block right after the component's own CSS
  instead (see how `.ptl`'s `@media` block sits directly after
  `.ptl .ptxt b {...}`, not up near `.slide`). This bit the timeline slide once
  already — the fix looked right, read right, and did nothing for two full
  iterations before the cause was found.
- **Don't trust a screenshot's "it still looks the same" at face value —
  measure it.** When a fix doesn't seem to take, inject a tiny debug overlay
  instead of re-guessing at CSS values or chasing Chrome cache theories:
  ```python
  debug_script = '''<script>
  window.addEventListener("load", () => setTimeout(() => {
    const inner = document.querySelector(".slide.active .inner");
    const slide = document.querySelector(".slide.active");
    const ir = inner.getBoundingClientRect(), sr = slide.getBoundingClientRect();
    const cs = getComputedStyle(slide);
    const avail = sr.height - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
    const d = document.createElement("div");
    d.style.cssText = "position:fixed;top:0;left:0;background:red;color:white;font-size:18px;padding:10px;z-index:9999;font-family:monospace;white-space:pre;";
    d.textContent = "inner_h=" + ir.height.toFixed(1) + " available_h=" + avail.toFixed(1) + " overflow_by=" + (ir.height-avail).toFixed(1) + "px";
    document.body.appendChild(d);
  }, 300));</script>'''
  # splice into a scratch copy before </body>, open via file://path.html#N
  # (the deck's own deep-link code reads the #N hash, no server needed for this)
  ```
  This turns "looks the same, is it cached?" into an exact pixel number in one
  screenshot — found the real overflow (123px) and confirmed the eventual fix
  (−148px, i.e. 148px to spare) with certainty instead of more guessing.
- **A "canary" rules out caching before you chase it.** If a fix appears to do
  nothing, re-render a DIFFERENT slide whose short-viewport behavior is already
  known-working (e.g. `.cap { display:none }` below 700px) at the same window
  size first. If the canary's known effect shows up, the media query is firing
  and the browser isn't serving stale content — the bug is in your CSS
  (probably the cascade-ordering gotcha above), not the test harness.
