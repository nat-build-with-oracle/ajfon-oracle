#!/usr/bin/env python3
"""
Local, offline, drag-and-drop slide reorder tool for lit-review-vector-search.html.

Adapted from ai-party-oracle's .claude/skills/deck-review/reorder-tool/ —
same static/index.html frontend (unchanged, it's fully generic), different
backend logic because this deck has no `const ORDER = [...]` array. Here,
display order IS physical DOM order of `<section class="slide" data-id="sN">`
blocks, so "reorder" means physically moving those chunks in the file.

Stdlib only. No pip installs, no CDN dependencies.

Run:
    python3 server.py

Then open the printed URL in a browser.
"""
import base64
import html as html_mod
import http.server
import json
import mimetypes
import os
import re
import socket
import socketserver
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TOOL_DIR = Path(__file__).resolve().parent
DECK_PATH = Path("/opt/Code/github.com/laris-co/ajfon-oracle/artifacts/lit-review-vector-search.html")
THUMBS_DIR = TOOL_DIR / "thumbs"

STATIC_DIR = TOOL_DIR / "static"
INDEX_HTML_PATH = STATIC_DIR / "index.html"

CANDIDATE_PORTS = [8765, 8766, 8767, 8768, 8790, 8800]

SECTION_START_RE = re.compile(r'<section class="slide( active)?"( data-hidden)? data-id="([^"]+)">')


# ---------------------------------------------------------------------------
# Deck parsing — order is DOM order, not a separate array
# ---------------------------------------------------------------------------

def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def extract_label(chunk: str) -> str:
    patterns = [
        r"<h1[^>]*>(.*?)</h1>",
        r"<h2[^>]*>(.*?)</h2>",
        r'class="quote"[^>]*>(.*?)</p>',
        r'class="eyebrow"[^>]*>(.*?)</div>',
    ]
    for pat in patterns:
        m = re.search(pat, chunk, re.S)
        if m:
            label = clean_text(m.group(1))
            if label:
                return label
    return ""


def extract_editable_fields(chunk: str):
    """Best-effort eyebrow/title/caption text for the edit-slide UI. Works
    reliably for the single-image "figwrap" slides add_slide() produces;
    for other (card-grid) slide layouts it still finds *a* h2/eyebrow, which
    is harmless to prefill even if editing it only touches that one spot."""
    eyebrow_m = re.search(r'<div class="eyebrow">(.*?)</div>', chunk, re.S)
    title_m = re.search(r"<h2>(.*?)</h2>", chunk, re.S)
    caption_m = re.search(r'<div class="cap">(.*?)</div>', chunk, re.S)
    return {
        "eyebrow": clean_text(eyebrow_m.group(1)) if eyebrow_m else "",
        "title": clean_text(title_m.group(1)) if title_m else "",
        "caption": clean_text(caption_m.group(1)) if caption_m else "",
    }


def parse_deck(html: str):
    """Return (ids_in_order, sections_by_id, hidden_ids) straight from DOM order."""
    starts = list(SECTION_START_RE.finditer(html))
    if not starts:
        raise RuntimeError('No <section class="slide..." data-id="..."> blocks found.')
    sections_by_id = {}
    ids_in_order = []
    hidden_ids = []
    for i, sm in enumerate(starts):
        aid = sm.group(3)
        is_hidden = sm.group(2) is not None
        start = sm.start()
        end = starts[i + 1].start() if i + 1 < len(starts) else len(html)
        sections_by_id[aid] = html[start:end]
        ids_in_order.append(aid)
        if is_hidden:
            hidden_ids.append(aid)
    return ids_in_order, sections_by_id, hidden_ids


def build_slide_data():
    html = DECK_PATH.read_text(encoding="utf-8")
    ids_in_order, sections_by_id, hidden_ids = parse_deck(html)
    hidden_set = set(hidden_ids)

    thumbs_by_id = {}
    if THUMBS_DIR.is_dir():
        for f in THUMBS_DIR.iterdir():
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"):
                thumbs_by_id[f.stem] = f.name

    slides = []
    visible_pos = 0
    for aid in ids_in_order:
        chunk = sections_by_id.get(aid, "")
        is_hidden = aid in hidden_set
        if not is_hidden:
            visible_pos += 1
        slide = {
            "id": aid,
            "pos": None if is_hidden else visible_pos,
            "hidden": is_hidden,
            "label": extract_label(chunk),
            "thumb": thumbs_by_id.get(aid),
            "full": thumbs_by_id.get(aid),  # same image serves both grid + lightbox fallback
        }
        slide.update(extract_editable_fields(chunk))
        slides.append(slide)
    return slides, []  # no such thing as a "dead id" here — every section IS a real slide


# ---------------------------------------------------------------------------
# Save / validate / rewrite — physically reorders <section> chunks
# ---------------------------------------------------------------------------

def validate_new_split(new_order, new_hidden, real_ids):
    if not isinstance(new_order, list) or not all(isinstance(x, str) for x in new_order):
        return "'order' must be a JSON array of strings."
    if not isinstance(new_hidden, list) or not all(isinstance(x, str) for x in new_hidden):
        return "'hidden' must be a JSON array of strings."

    combined = new_order + new_hidden
    real_set = set(real_ids)
    combined_set = set(combined)

    dupes = sorted({x for x in combined if combined.count(x) > 1})
    if dupes:
        return f"Duplicate ids across order+hidden: {', '.join(dupes)}"
    missing = sorted(real_set - combined_set)
    if missing:
        return f"Missing ids that must be present (in order or hidden): {', '.join(missing)}"
    extra = sorted(combined_set - real_set)
    if extra:
        return f"Unexpected ids not in the current real slide set: {', '.join(extra)}"
    if len(combined) != len(real_ids):
        return f"Count mismatch: submitted {len(combined)} ids total, expected {len(real_ids)}."
    return None


def diff_summary(old_order, new_order):
    old_pos = {aid: i for i, aid in enumerate(old_order, start=1)}
    new_pos = {aid: i for i, aid in enumerate(new_order, start=1)}
    moves = []
    for aid in old_order:
        if aid not in new_pos:
            continue
        o, n = old_pos[aid], new_pos[aid]
        if o != n:
            moves.append(f"{aid}: {o}→{n}")
    if not moves:
        return "No change in visible order."
    return "Moved " + ", ".join(moves)


def _atomic_write(path: Path, content: str) -> None:
    tmp = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def save_new_order(new_order, new_hidden):
    html = DECK_PATH.read_text(encoding="utf-8")
    ids_in_order, sections_by_id, old_hidden_ids = parse_deck(html)
    old_visible_ids = [a for a in ids_in_order if a not in set(old_hidden_ids)]

    err = validate_new_split(new_order, new_hidden, ids_in_order)
    if err:
        return False, err

    final_order = list(new_order) + list(new_hidden)
    new_hidden_set = set(new_hidden)

    # Rebuild each section chunk with its class/data-hidden attrs reset,
    # `active` reserved for whichever ends up first in final_order.
    chunks = []
    for i, aid in enumerate(final_order):
        chunk = sections_by_id[aid]
        is_first = (i == 0)
        is_hidden = aid in new_hidden_set
        cls = "slide" + (" active" if is_first and not is_hidden else "")
        hidden_attr = " data-hidden" if is_hidden else ""
        new_open_tag = f'<section class="{cls}"{hidden_attr} data-id="{aid}">'
        chunk = SECTION_START_RE.sub(new_open_tag, chunk, count=1)
        chunks.append(chunk)

    # Splice: replace the span from the first section's start to the last
    # section's end with the freshly-ordered chunks, byte-identical elsewhere.
    starts = list(SECTION_START_RE.finditer(html))
    span_start = starts[0].start()
    span_end = len(html)  # last section always runs to EOF-of-deck-div in this file; safe since sections are the last thing before </div>
    new_html = html[:span_start] + "".join(chunks) + html[span_end:]

    summary = diff_summary(old_visible_ids, new_order)
    newly_hidden = sorted(new_hidden_set - set(old_hidden_ids))
    newly_shown = sorted(set(old_hidden_ids) - new_hidden_set)
    if newly_hidden:
        summary += f" | Hidden: {', '.join(newly_hidden)}"
    if newly_shown:
        summary += f" | Un-hidden: {', '.join(newly_shown)}"

    _atomic_write(DECK_PATH, new_html)

    return True, {
        "order": new_order,
        "hidden": new_hidden,
        "dead_appended": [],
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Add slide — append a brand-new <section> built from an uploaded image,
# matching the deck's existing single-image "figwrap/figmat" slide pattern
# (see e.g. data-id="s5"). Image is embedded inline as base64, same as every
# other image in this self-contained deck file — no sibling asset files.
# ---------------------------------------------------------------------------

SECTION_FULL_RE = re.compile(
    r'<section class="slide( active)?"( data-hidden)? data-id="([^"]+)">.*?</section>',
    re.S,
)

def _next_slide_id(ids):
    nums = [int(m.group(1)) for aid in ids if (m := re.match(r"^s(\d+)$", aid))]
    return f"s{(max(nums) + 1) if nums else 1}"


_EXT_MAP = {
    "jpeg": "jpg", "jpg": "jpg", "png": "png", "gif": "gif",
    "webp": "webp", "svg+xml": "svg", "bmp": "bmp",
}

# Formats the browser's FileReader will happily base64-encode but Chromium
# (unlike Safari) cannot actually decode inline — an <img> pointed at one of
# these renders as a broken-image icon both in the reorder grid's thumbnail
# AND in the live deck itself. iPhone photos default to HEIC, so this bites
# constantly. Converted via macOS's built-in `sips` (no pip install — stays
# within this tool's stdlib-only rule) rather than silently accepted broken.
_BROWSER_UNSAFE_SUBTYPES = {"heic", "heif"}


def _convert_to_png_via_sips(raw_bytes: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in"
        dst = Path(tmp) / "out.png"
        src.write_bytes(raw_bytes)
        result = subprocess.run(
            ["sips", "-s", "format", "png", str(src), "--out", str(dst)],
            capture_output=True, text=True,
        )
        if result.returncode != 0 or not dst.is_file():
            raise RuntimeError(f"sips conversion failed: {result.stderr.strip() or result.stdout.strip()}")
        return dst.read_bytes()


def _normalize_image(raw_bytes: bytes, subtype: str):
    """Returns (bytes, ext, subtype) — converts browser-unsafe formats
    (HEIC/HEIF) to PNG via sips, passes everything else through untouched."""
    if subtype in _BROWSER_UNSAFE_SUBTYPES:
        return _convert_to_png_via_sips(raw_bytes), "png", "png"
    ext = _EXT_MAP.get(subtype, re.sub(r"[^a-z0-9]", "", subtype) or "img")
    return raw_bytes, ext, subtype


def add_slide(data_url, eyebrow, title, caption):
    # Accept ANY image/* subtype the browser's FileReader produced, not a
    # hardcoded png/jpg/gif/webp allowlist — a prior version rejected valid
    # drags (e.g. HEIC photos, or other image/* types Chrome still base64s
    # correctly) with a useless "expected .../base64 URL" error that didn't
    # even say what type it actually got.
    m = re.match(r"^data:image/([a-zA-Z0-9.+-]+);base64,(.+)$", data_url, re.S)
    if not m:
        head = data_url[:40] if isinstance(data_url, str) else str(type(data_url))
        return False, f"Not an image data URL (got: {head!r}...)."
    subtype = m.group(1).lower()
    try:
        raw_bytes = base64.b64decode(m.group(2), validate=True)
    except Exception as e:
        return False, f"Invalid base64 image data: {e}"

    try:
        raw_bytes, ext, subtype = _normalize_image(raw_bytes, subtype)
    except Exception as e:
        return False, f"Couldn't convert {subtype} image to a browser-safe format: {e}"
    data_url = "data:image/" + subtype + ";base64," + base64.b64encode(raw_bytes).decode("ascii")

    html_text = DECK_PATH.read_text(encoding="utf-8")
    matches = list(SECTION_FULL_RE.finditer(html_text))
    if not matches:
        return False, "No <section class=\"slide...\"> blocks found — can't locate insertion point."

    ids = [mm.group(3) for mm in matches]
    new_id = _next_slide_id(ids)

    # Humans drop the image only — text is left blank on purpose here and
    # filled in afterwards (by AI or by hand) via edit_slide()/PATCH-style
    # /edit-slide, not at add time.
    safe_eyebrow = html_mod.escape(eyebrow or "")
    safe_title = html_mod.escape(title or "(ยังไม่มีหัวข้อ — รอเติมทีหลัง)")
    safe_caption = html_mod.escape(caption or "")

    new_chunk = f'''<section class="slide" data-id="{new_id}">
    <div class="inner">
      <div class="eyebrow">{safe_eyebrow}</div>
      <h2>{safe_title}</h2>
      <div class="figwrap">
        <div class="figmat" role="button" tabindex="0" aria-label="ขยายภาพเต็มจอ"><img src="{data_url}" alt="{safe_title}" /><span class="zoom-hint">🔍 คลิก หรือกด <kbd>Z</kbd> เพื่อขยายเต็มจอ</span></div>
        <div class="cap">{safe_caption}</div>
      </div>
    </div>
  </section>

  '''

    # Preserve everything between/around the sections BYTE-FOR-BYTE — this
    # deck has non-section content interleaved (HTML comments between slides,
    # a <script> block sitting between the last visible slide and the hidden
    # one). Concatenating only matches[i].group(0) silently drops all of
    # that; splicing on [start-of-first-match : end-of-last-match] instead
    # keeps it untouched and only inserts the new chunk right after it.
    prefix = html_text[: matches[0].start()]
    unchanged_body = html_text[matches[0].start(): matches[-1].end()]
    epilogue = html_text[matches[-1].end():]
    new_html = prefix + unchanged_body + "\n\n  " + new_chunk.rstrip() + epilogue

    _atomic_write(DECK_PATH, new_html)

    thumb_path = THUMBS_DIR / f"{new_id}.{ext}"
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    thumb_path.write_bytes(raw_bytes)

    return True, {"id": new_id, "summary": f"Added new slide {new_id} at the end (visible)."}


def edit_slide(slide_id, eyebrow, title, caption):
    """Rewrite the eyebrow/h2/first-caption text INSIDE one slide's own
    section, leaving the image and every other slide byte-for-byte
    untouched. Only touches a field if it's present in that slide's chunk —
    e.g. a caption-less slide's caption arg is silently ignored rather than
    inventing markup that wasn't there."""
    html_text = DECK_PATH.read_text(encoding="utf-8")
    matches = list(SECTION_FULL_RE.finditer(html_text))
    target = next((mm for mm in matches if mm.group(3) == slide_id), None)
    if target is None:
        return False, f"No slide with id '{slide_id}' found."

    chunk = target.group(0)

    def sub_once(pattern, new_text, text):
        m = re.search(pattern, text, re.S)
        if not m:
            return text, False
        return text[: m.start(1)] + html_mod.escape(new_text) + text[m.end(1):], True

    changed_any = False
    if eyebrow is not None:
        chunk, ok = sub_once(r'<div class="eyebrow">(.*?)</div>', eyebrow, chunk)
        changed_any = changed_any or ok
    if title is not None:
        chunk, ok = sub_once(r"<h2>(.*?)</h2>", title, chunk)
        changed_any = changed_any or ok
    if caption is not None:
        chunk, ok = sub_once(r'<div class="cap">(.*?)</div>', caption, chunk)
        changed_any = changed_any or ok

    new_html = html_text[: target.start()] + chunk + html_text[target.end():]
    _atomic_write(DECK_PATH, new_html)

    return True, {"id": slide_id, "changed": changed_any, "summary": f"Updated text for {slide_id}."}


def delete_slide(slide_id):
    """Permanently remove one <section> — unlike the eye-icon hide (which
    just marks data-hidden and keeps the slide in the file), this actually
    deletes it. Also removes any preceding HTML comment header (e.g.
    "<!-- 8 · Provenance timeline -->") and one trailing blank line, so
    repeated deletes don't leave orphaned comments/gaps behind."""
    html_text = DECK_PATH.read_text(encoding="utf-8")
    matches = list(SECTION_FULL_RE.finditer(html_text))
    target = next((mm for mm in matches if mm.group(3) == slide_id), None)
    if target is None:
        return False, f"No slide with id '{slide_id}' found."
    if len(matches) <= 1:
        return False, "Can't delete the last remaining slide."

    start, end = target.start(), target.end()

    before = html_text[:start]
    comment_m = re.search(r"<!--[^\n]*-->\s*$", before)
    if comment_m:
        start = comment_m.start()

    after = html_text[end:]
    trail_m = re.match(r"[ \t]*\n", after)
    if trail_m:
        end += trail_m.end()

    new_html = html_text[:start] + html_text[end:]
    _atomic_write(DECK_PATH, new_html)

    for ext in ("png", "jpg", "jpeg", "gif", "webp", "svg", "bmp"):
        thumb_path = THUMBS_DIR / f"{slide_id}.{ext}"
        if thumb_path.is_file():
            thumb_path.unlink()

    return True, {"id": slide_id, "summary": f"Deleted slide {slide_id}."}


def regenerate_thumb(slide_id):
    """Re-extract a slide's own inline base64 <img> straight out of the deck
    HTML and write it to thumbs/ — fixes a "no thumbnail" card without
    needing the original upload again, since the deck already has the full
    image embedded (thumb and deck image are the same bytes by design).

    If the embedded image is HEIC/HEIF (browser-unsafe — see _normalize_image),
    this ALSO rewrites the deck's own <img src="..."> to the converted PNG,
    since a HEIC image is broken in the live presentation too, not just the
    thumbnail — a thumb-only fix would leave the real bug in place."""
    html_text = DECK_PATH.read_text(encoding="utf-8")
    matches = list(SECTION_FULL_RE.finditer(html_text))
    target = next((mm for mm in matches if mm.group(3) == slide_id), None)
    if target is None:
        return False, f"No slide with id '{slide_id}' found."
    chunk = target.group(0)

    m = re.search(r'src="data:image/([a-zA-Z0-9.+-]+);base64,([^"]+)"', chunk, re.S)
    if not m:
        return False, f"Slide '{slide_id}' has no inline base64 <img> to regenerate a thumbnail from."

    subtype = m.group(1).lower()
    try:
        raw_bytes = base64.b64decode(m.group(2), validate=True)
    except Exception as e:
        return False, f"Invalid base64 image data in slide: {e}"

    try:
        raw_bytes, ext, new_subtype = _normalize_image(raw_bytes, subtype)
    except Exception as e:
        return False, f"Couldn't convert {subtype} image to a browser-safe format: {e}"

    deck_fixed = False
    if new_subtype != subtype:
        # The deck's own <img src> was pointing at a browser-unsafe format —
        # patch it in place to the converted PNG, same splice-in-place
        # technique as edit_slide() (touches only this slide's own chunk).
        new_data_url = "data:image/" + new_subtype + ";base64," + base64.b64encode(raw_bytes).decode("ascii")
        new_chunk = chunk[: m.start()] + 'src="' + new_data_url + '"' + chunk[m.end():]
        new_html = html_text[: target.start()] + new_chunk + html_text[target.end():]
        _atomic_write(DECK_PATH, new_html)
        deck_fixed = True

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    # Clear any stale thumb under a different extension for this id first,
    # so a format change doesn't leave two files (old ignored, new picked up).
    for old_ext in ("png", "jpg", "jpeg", "gif", "webp", "svg", "bmp", "heic", "heif"):
        old = THUMBS_DIR / f"{slide_id}.{old_ext}"
        if old.is_file() and old_ext != ext:
            old.unlink()

    (THUMBS_DIR / f"{slide_id}.{ext}").write_bytes(raw_bytes)
    summary = f"Regenerated thumbnail for {slide_id} ({ext})."
    if deck_fixed:
        summary += f" Also converted the deck's own image from {subtype} → {new_subtype} (was broken in Chromium)."
    return True, {"id": slide_id, "ext": ext, "deck_fixed": deck_fixed, "summary": summary}


def regenerate_missing_thumbs():
    """Bulk-repair: regenerate every slide currently showing 'no thumbnail'."""
    slides, _ = build_slide_data()
    fixed, failed = [], []
    for s in slides:
        if s["thumb"]:
            continue
        ok, payload = regenerate_thumb(s["id"])
        (fixed if ok else failed).append(s["id"] if ok else {"id": s["id"], "error": payload})
    return True, {"fixed": fixed, "failed": failed, "summary": f"Regenerated {len(fixed)}, failed {len(failed)}."}


# ---------------------------------------------------------------------------
# HTTP server (unchanged from ai-party-oracle's tool, minus /img /audio routes
# — this deck is fully self-contained base64, no sibling assets to serve)
# ---------------------------------------------------------------------------

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "AjfonDeckReorder/1.0"

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.address_string(), fmt % args))

    def _send_json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, status, content_type, data):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            data = INDEX_HTML_PATH.read_bytes()
            self._send_bytes(200, "text/html; charset=utf-8", data)
            return

        if path == "/api/slides":
            try:
                slides, dead_ids = build_slide_data()
            except Exception as e:
                self._send_json(500, {"error": str(e)})
                return
            self._send_json(200, {"slides": slides, "dead_ids": dead_ids})
            return

        if path.startswith("/thumbs/") or path.startswith("/full/"):
            prefix = "/thumbs/" if path.startswith("/thumbs/") else "/full/"
            name = path[len(prefix):]
            if "/" in name or ".." in name or not name:
                self._send_bytes(400, "text/plain; charset=utf-8", b"bad thumbnail name")
                return
            fpath = THUMBS_DIR / name
            try:
                fpath.resolve().relative_to(THUMBS_DIR.resolve())
            except ValueError:
                self._send_bytes(400, "text/plain; charset=utf-8", b"bad thumbnail path")
                return
            if not fpath.is_file():
                self._send_bytes(404, "text/plain; charset=utf-8", b"not found")
                return
            ctype = mimetypes.guess_type(fpath.name)[0] or "application/octet-stream"
            self._send_bytes(200, ctype, fpath.read_bytes())
            return

        if path == "/deck":
            if not DECK_PATH.is_file():
                self._send_bytes(500, "text/plain; charset=utf-8", b"deck file missing")
                return
            self._send_bytes(200, "text/html; charset=utf-8", DECK_PATH.read_bytes())
            return

        self._send_bytes(404, "text/plain; charset=utf-8", b"not found")

    def do_POST(self):
        parsed = urlparse(self.path)

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8") if raw else "null")
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON body: {e}"})
            return

        if parsed.path == "/save":
            if isinstance(body, list):
                new_order, new_hidden = body, []
            elif isinstance(body, dict):
                new_order = body.get("order", [])
                new_hidden = body.get("hidden", [])
            else:
                self._send_json(400, {"error": "Expected a JSON object {order, hidden} or an array."})
                return

            try:
                ok, payload = save_new_order(new_order, new_hidden)
            except Exception as e:
                self._send_json(500, {"error": f"Server error while saving: {e}"})
                return

            if not ok:
                self._send_json(400, {"error": payload})
                return

            self._send_json(200, payload)
            return

        if parsed.path == "/add-slide":
            if not isinstance(body, dict) or not body.get("data"):
                self._send_json(400, {"error": "Expected {data, eyebrow, title, caption}."})
                return

            try:
                ok, payload = add_slide(
                    body.get("data", ""),
                    body.get("eyebrow", ""),
                    body.get("title", ""),
                    body.get("caption", ""),
                )
            except Exception as e:
                self._send_json(500, {"error": f"Server error while adding slide: {e}"})
                return

            if not ok:
                self._send_json(400, {"error": payload})
                return

            self._send_json(200, payload)
            return

        if parsed.path == "/edit-slide":
            if not isinstance(body, dict) or not body.get("id"):
                self._send_json(400, {"error": "Expected {id, eyebrow, title, caption}."})
                return

            try:
                ok, payload = edit_slide(
                    body.get("id"),
                    body.get("eyebrow"),
                    body.get("title"),
                    body.get("caption"),
                )
            except Exception as e:
                self._send_json(500, {"error": f"Server error while editing slide: {e}"})
                return

            if not ok:
                self._send_json(400, {"error": payload})
                return

            self._send_json(200, payload)
            return

        if parsed.path == "/delete-slide":
            if not isinstance(body, dict) or not body.get("id"):
                self._send_json(400, {"error": "Expected {id}."})
                return

            try:
                ok, payload = delete_slide(body.get("id"))
            except Exception as e:
                self._send_json(500, {"error": f"Server error while deleting slide: {e}"})
                return

            if not ok:
                self._send_json(400, {"error": payload})
                return

            self._send_json(200, payload)
            return

        if parsed.path == "/regenerate-thumb":
            if not isinstance(body, dict) or not body.get("id"):
                self._send_json(400, {"error": "Expected {id}."})
                return

            try:
                ok, payload = regenerate_thumb(body.get("id"))
            except Exception as e:
                self._send_json(500, {"error": f"Server error while regenerating thumbnail: {e}"})
                return

            if not ok:
                self._send_json(400, {"error": payload})
                return

            self._send_json(200, payload)
            return

        if parsed.path == "/regenerate-thumbs":
            try:
                ok, payload = regenerate_missing_thumbs()
            except Exception as e:
                self._send_json(500, {"error": f"Server error while regenerating thumbnails: {e}"})
                return

            self._send_json(200, payload)
            return

        self._send_bytes(404, "text/plain; charset=utf-8", b"not found")


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def pick_port():
    for p in CANDIDATE_PORTS:
        if port_is_free(p):
            return p
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    port = pick_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Deck reorder tool running at: {url}")
    print(f"Present (local, always current): {url}deck")
    print(f"Deck file: {DECK_PATH}")
    print(f"Thumbs dir: {THUMBS_DIR}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
