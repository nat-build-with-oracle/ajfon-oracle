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
import http.server
import json
import mimetypes
import os
import re
import socket
import socketserver
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
            if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
                thumbs_by_id[f.stem] = f.name

    slides = []
    visible_pos = 0
    for aid in ids_in_order:
        chunk = sections_by_id.get(aid, "")
        is_hidden = aid in hidden_set
        if not is_hidden:
            visible_pos += 1
        slides.append({
            "id": aid,
            "pos": None if is_hidden else visible_pos,
            "hidden": is_hidden,
            "label": extract_label(chunk),
            "thumb": thumbs_by_id.get(aid),
            "full": thumbs_by_id.get(aid),  # same image serves both grid + lightbox fallback
        })
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
        if parsed.path != "/save":
            self._send_bytes(404, "text/plain; charset=utf-8", b"not found")
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8") if raw else "null")
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON body: {e}"})
            return

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
