---
pattern: token-level-theming-over-class-overrides
date: 2026-07-16
source: retrospective 20cf7c44 (ajfon-oracle, vector-book contrast audit)
concepts: [css-custom-properties, design-tokens, dark-mode, wcag-contrast, nbconvert, verification-by-measurement]
---

# Fix theming bugs at the token level, not the class level

## Pattern

When a rendering/theming bug (invisible text, wrong contrast, broken dark mode) traces back
to a system that themes itself through CSS custom properties / design tokens (e.g. Jupyter's
`--jp-*` variables via nbconvert, or any design-system's token cascade), fixing it by overriding
individual CSS classes on top of that cascade will:

1. Appear to work for whichever cases you spot-checked
2. Silently leave every other token-driven element broken
3. Require a second, larger rewrite once the failures are actually measured

## What happened

A Jupyter-notebook-to-HTML book (12 chapters, rendered via `nbconvert`) had a dark-mode bug
where code was invisible. First fix: override pygments CSS classes (`.n`, `.p`, `.o`, etc.)
per-class. This was declared "contrast ผ่าน" (contrast fixed). It wasn't — a later Playwright
pass that actually computed WCAG relative-luminance contrast on every rendered text element,
across all 26 snapshots (12 chapters × light/dark), found 1056 remaining contrast failures:
dark tables with white cells, black code panes, dark-blue paragraph anchors. Root cause:
nbconvert routes ALL colors through `--jp-*` CSS custom properties; the per-class overrides
were fighting that token cascade instead of replacing it. The real fix was a token-level
override script (`apply_theme.py`) controlling `--jp-mirror-editor-*`, `--jp-layout-color*`,
`--jp-content-font-color*`, `--jp-rendermime-table-*`, `--jp-cell-editor-bg`, links, and
prompts for both themes. Re-audit after the token fix: 1056 → 0.

## Rule for any Oracle on any project

- Before patching a rendering/theme bug, check whether the framework themes via CSS custom
  properties (design tokens) rather than plain classes. If it does, override the tokens, not
  the classes that consume them.
- Never declare a contrast/visibility fix "done" from a visual skim. Verify with an automated,
  exhaustive measurement (compute contrast ratio on every rendered text node, or equivalent)
  across every theme variant and every page — the failure count is often orders of magnitude
  larger than what a spot-check would catch (0 found by eye vs 1056 found by instrumented
  audit, in this case).
- If you fix the same visual bug class twice on the same asset, that's the signal you fixed a
  symptom the first time — stop and look one layer down at the underlying cascade/token system
  before applying a third patch.
