---
name: ARRA Oracle — Second Brain Workshop System
description: Dark, proof-first visual system for the ARRA Oracle Second Brain workshop deck, poster, handout and book
colors:
  bg: "#0a0b10"
  panel: "#12141c"
  panel-2: "#171a24"
  chip: "#0e1420"
  line: "#23273a"
  ink: "#eef0f7"
  ink-soft: "#a2a8bd"
  ink-faint: "#5c6178"
  gold: "#ffcf4a"
  blue: "#5b9dff"
  cyan: "#7fd4ff"
  green: "#52d98a"
  amber: "#f8a860"
  rose: "#ff7bab"
  red: "#ff6b6b"
  violet: "#b79dff"
typography:
  display:
    fontFamily: '"Noto Sans Thai","IBM Plex Sans Thai","Sarabun","Thonburi",system-ui,-apple-system,sans-serif'
    fontSize: "clamp(34px, 6.2vw, 70px)"
    fontWeight: 800
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  headline:
    fontFamily: '"Noto Sans Thai","IBM Plex Sans Thai","Sarabun","Thonburi",system-ui,-apple-system,sans-serif'
    fontSize: "clamp(27px, 4.8vw, 52px)"
    fontWeight: 800
    lineHeight: 1.12
    letterSpacing: "-0.015em"
  body:
    fontFamily: '"Noto Sans Thai","IBM Plex Sans Thai","Sarabun","Thonburi",system-ui,-apple-system,sans-serif'
    fontSize: "clamp(18px, 2.5vw, 27px)"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: 'ui-monospace,"SF Mono","JetBrains Mono",Menlo,monospace'
    fontSize: "11px"
    fontWeight: 700
    letterSpacing: "0.08em"
rounded:
  xs: "3px"
  sm: "6px"
  md: "8px"
  lg: "16px"
  pill: "999px"
spacing:
  xs: "7px"
  sm: "12px"
  md: "16px"
  lg: "22px"
components:
  card:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "22px"
  pill:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.pill}"
    padding: "7px 15px"
  badge-good:
    backgroundColor: "{colors.green}"
    textColor: "#0d1310"
    rounded: "{rounded.sm}"
    padding: "3px 9px"
  box-good:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.green}"
    rounded: "{rounded.lg}"
    padding: "22px"
  box-warn:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.amber}"
    rounded: "{rounded.lg}"
    padding: "22px"
---

# Design System: ARRA Oracle — Second Brain Workshop System

## 1. Overview

**Creative North Star: "The Proof Terminal"**

Everything on screen reads like it came off an instrument, not a slide deck. The background is near-black with a barely-there blue-violet tilt — a room lit by monitors, not daylight — and text sits in two typefaces with one strict rule between them: the Thai humanist sans carries argument and narrative, the monospace carries anything that IS a measurement (a number, a command, a timestamp, a filename). Eight accent hues exist, and every one of them is a fixed status, never a decoration — gold marks the number that is the proof, green marks what was verified, amber marks what wasn't yet, rose marks the assumption that turned out wrong.

This system explicitly rejects the SaaS-marketing toolkit: no cream/beige backgrounds, no gradient text, no hero-metric templates, no eyebrow-over-every-section reflex, no 01/02/03 scaffolding unless the content is a real sequence. It was built for a room that includes doctors, professors, and grad students with zero code background sitting next to developers — so the surface has to read as *precise*, not as *insider*.

**Key Characteristics:**
- Near-black, blue-violet-tinted void, never true `#000` or a warm neutral
- Flat by construction — depth comes from panel layering + a 1px border, never a shadow
- Eight semantic accents, each locked to one meaning across every artifact
- Mono type is the tell for "this is data"; Thai sans is the tell for "this is argument"
- `clamp()` display type with negative letter-spacing and `text-wrap: balance`, already in place

## 2. Colors

Near-black neutrals carry almost the whole surface; the eight accents appear only where they mean something specific.

### Primary
- **Proof Gold** (`#ffcf4a`): the one color that marks evidence — the number in an eyebrow, a highlighted quote, the leading edge of a reading-progress bar, a comparison arrow. If more than one thing on a screen is gold, nothing is.

### Secondary
- **Signal Blue** (`#5b9dff`): structural data references — vectors, embeddings, labeling accents.
- **Bright Cyan** (`#7fd4ff`): active/interactive — code blocks, links, focus rings, the brighter half of the progress-bar gradient.

### Tertiary — status (fixed meaning, never rotated)
- **Measured Green** (`#52d98a`): verified, passed, recommended, live. The only hue allowed to mean "this checked out" (`.box.good`, `.badge.rec`, the live-status chip).
- **Caution Amber** (`#f8a860`): needs more evidence, `[ยังไม่ยืนยัน]`, `.box.warn`.
- **Correction Rose** (`#ff7bab`): a myth that got busted — the wrong premise a claim is being corrected against. This is the hue for a myth→fact panel.
- **Stop Red** (`#ff6b6b`): hard negative — error state, the "before" number in a bad trend.
- **Category Violet** (`#b79dff`): a second independent categorical lane, reserved for when a table genuinely needs two unrelated series in the same view (e.g. an FTS-vs-Vector comparison column) — not a general-purpose 8th color.

### Neutral
- **Void** (`#0a0b10`): body background. Near-black, the barely-there blue-violet tilt is load-bearing — don't flatten it to true black or warm it toward gray.
- **Panel** (`#12141c`) / **Panel-2** (`#171a24`): card and box surfaces, one step apart for layering without a shadow.
- **Chip** (`#0e1420`): the darkest surface — code blocks, tightly-scoped chips.
- **Line** (`#23273a`): every border and divider, always 1px.
- **Ink** (`#eef0f7`): primary text.
- **Ink Soft** (`#a2a8bd`): secondary text, lead paragraphs.
- **Ink Faint** (`#5c6178`): tertiary text — timestamps, footers, metadata tags.

### Named Rules
**The One Proof Rule.** Gold appears only on the number, quote, or delta that IS the evidence — never as general decoration. Multiple gold elements on one screen means the emphasis has already failed.

**The Fixed-Meaning Rule.** Green/amber/rose/red never rotate by row or by artifact. Green always means verified; amber always means unverified/caution; rose always means "this was the wrong assumption"; red always means hard-stop/error. A 9th status meaning becomes a labeled chip, not a new hue.

## 3. Typography

**Display Font:** "Noto Sans Thai" (with "IBM Plex Sans Thai", "Sarabun", "Thonburi", system-ui fallback)
**Body Font:** same Thai stack — there is no separate Latin body face; the Thai stack carries Latin cleanly
**Label/Mono Font:** ui-monospace ("SF Mono", "JetBrains Mono", Menlo, monospace)

**Character:** A Thai-first humanist sans for reading, paired against a strict monospace for anything that is data. The font choice itself tells the reader what kind of sentence they're looking at before they've read a word of it.

### Hierarchy
- **Display** (800, `clamp(34px, 6.2vw, 70px)`, line-height 1.08): the one `h1` per screen — slide title, poster headline. `letter-spacing: -0.02em`, `text-wrap: balance`.
- **Headline** (800, `clamp(27px, 4.8vw, 52px)`, line-height 1.12): `h2` — section titles within a deck or handout. `letter-spacing: -0.015em`, `text-wrap: balance`.
- **Lead/Body** (400, `clamp(18px, 2.5vw, 27px)` for a lead paragraph under a headline; 16–18px for running text, line-height 1.5): the argument. Cap lead paragraphs at 42ch.
- **Label** (700 mono, 11px, `letter-spacing: 0.08–0.1em`, uppercase): badges, tags, footers, timestamps. Never for prose.

### Named Rules
**The Mono-Is-Measured Rule.** If it's monospace, it's a number, a command, a timestamp, or a filename. If it's the Thai sans, it's argument or narrative. Never swap the two — mono prose or sans data both read as a mistake.

## 4. Elevation

Flat by construction — zero `box-shadow` declarations across the workshop system. Depth is conveyed by panel layering alone: void → panel → panel-2 → chip, each one step darker or more saturated, separated by a single 1px `line` border. The one departure is a subtle top-to-bottom gradient on `.card` (`#141824 → #0f1119`) that reads as a panel catching a little ambient light, not a drop shadow — it never appears with a blurred, offset shadow alongside it.

### Named Rules
**The Flat Instrument Rule.** No shadows, ever. An instrument panel doesn't cast one — it sits flush with the console.

## 5. Components

No distinct button component exists yet in the scanned artifacts — pills and status chips currently fill the CTA/status role. Document what's real; a dedicated button can be added here once one ships.

### Pills
- **Shape:** fully rounded (`999px`)
- **Style:** `1px solid var(--line)` border, panel background at ~53% opacity (`#12141c88`), `7px 15px` padding
- **Use:** status chips, filter-like labels, small inline CTAs

### Cards
- **Corner Style:** `16px` radius
- **Background:** `linear-gradient(180deg, #141824, #0f1119)` — ambient light on a panel, per the Flat Instrument Rule
- **Border:** `1px solid var(--line)`
- **Internal Padding:** `22px`
- **Grid:** `repeat(auto-fit, minmax(220px, 1fr))`, `16px` gap — cards reflow, never fixed-width

### Badges / Tags
- **Badge style:** mono 11px, weight 700, `letter-spacing: 0.08em`, uppercase, `3px 9px` padding, `6px` radius
- **`badge.rec` (recommended):** green fill, near-black (`#0d1310`) text — the one place text sits *on* a saturated fill rather than beside it
- **`.tag`:** ink-faint mono, no fill, right-aligned metadata (timestamps, source labels)

### Status Boxes
- **`.box.good`:** panel background, green heading — "this measured out" (see Fixed-Meaning Rule)
- **`.box.warn`:** panel background, amber heading — "treat this as unverified"
- Both share the card shape (16px radius, 22px padding, 1px line border); only the heading color and semantic weight differ

### Navigation
Not observed in the scanned artifacts (single-scroll decks and posters, no persistent nav). Skip rather than invent.

## 6. Do's and Don'ts

### Do:
- **Do** put a real number, chart, or timestamp behind every claim — gold marks the one that IS the proof (The One Proof Rule).
- **Do** keep green/amber/rose/red locked to their one meaning across every artifact, not just within one slide (The Fixed-Meaning Rule).
- **Do** reserve the mono stack exclusively for data — numbers, commands, timestamps, filenames (The Mono-Is-Measured Rule).
- **Do** stay flat: panel-on-panel layering plus a 1px border, never a box-shadow (The Flat Instrument Rule).
- **Do** hold every artifact — slides, poster, handout — to WCAG AA contrast, the same bar already applied to the book's `html/` output.
- **Do** write the workshop-facing layer in Thai first; keep English only for code, tool names, and terms that shouldn't be translated.

### Don't:
- **Don't** introduce a second dark palette. `artifacts/workshop-deck.html` (`#141413`/`#5c9ded`…) and `artifacts/vector-viz.html` (`#3987e5`/`#199e70`…) each drift to a different system — reconcile toward the tokens above next time either is touched, don't extend either drift.
- **Don't** use cream/beige/sand backgrounds, gradient text (`background-clip: text`), or hero-metric SaaS templates — this is teaching material for researchers and doctors, not a startup landing page.
- **Don't** reach for a tiny uppercase tracked eyebrow above every section by reflex. `.eyebrow` already exists (`arra-workshop-slides.html`, `vector-search-slides.html`) and is fine as an occasional "here's the chapter number" device — but if it starts appearing above *every* section on every new artifact, that's the AI-slop tell PRODUCT.md explicitly rejects.
- **Don't** add 01/02/03 numbered-section scaffolding unless the content is a genuinely ordered sequence.
- **Don't** cycle the 8 accent hues decoratively per-artifact. A color's meaning must survive across the whole system, not reset per slide.
- **Don't** add a drop shadow to a card "for depth" — use panel/panel-2/chip layering instead.
