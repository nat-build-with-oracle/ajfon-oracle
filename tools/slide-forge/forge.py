#!/usr/bin/env python3
"""
Slide Forge — drop images, get a beautiful deck.

Local, offline, stdlib-only. Drop image files into inbox/ (or upload via the
browser), give each an eyebrow/title/caption, click Build, and it renders a
standalone HTML deck in the SAME dark "Proof Terminal" design system as
artifacts/lit-review-vector-search.html — base64-embedded, self-contained,
keyboard-navigable, with the same zoom-lightbox as the real deck.

The AI-describe step: this tool ARRANGES and RENDERS. The vision ("look at the
image, write the caption") is done by Claude — run `forge.py`, drop images,
then ask Claude to "describe the slide-forge inbox images" and it writes
captions.json for you. You can always edit any text in the browser after.

Run:
    python3 forge.py
Then open the printed URL.
"""
import http.server
import json
import base64
import mimetypes
import socket
import socketserver
import html as html_mod
from pathlib import Path
from urllib.parse import urlparse, parse_qs

TOOL_DIR = Path(__file__).resolve().parent
INBOX = TOOL_DIR / "inbox"
CAPTIONS = TOOL_DIR / "captions.json"
OUT_DECK = Path("/opt/Code/github.com/laris-co/ajfon-oracle/artifacts/forged-deck.html")
CANDIDATE_PORTS = [8770, 8771, 8772, 8773, 8780]
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

INBOX.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# State: captions.json = {order: [names], slides: {name: {eyebrow,title,caption}}}
# ---------------------------------------------------------------------------

def load_state():
    imgs = sorted([p.name for p in INBOX.iterdir() if p.suffix.lower() in IMG_EXT])
    state = {"order": [], "slides": {}, "title": "Forged Deck", "subtitle": ""}
    if CAPTIONS.exists():
        try:
            state.update(json.loads(CAPTIONS.read_text(encoding="utf-8")))
        except Exception:
            pass
    # reconcile with what's actually on disk
    state["order"] = [n for n in state.get("order", []) if n in imgs]
    for n in imgs:
        if n not in state["order"]:
            state["order"].append(n)
        state["slides"].setdefault(n, {"eyebrow": "", "title": "", "caption": ""})
    state["slides"] = {n: state["slides"][n] for n in state["order"]}
    return state


def save_state(state):
    CAPTIONS.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def data_uri(name):
    p = INBOX / name
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ---------------------------------------------------------------------------
# Deck rendering — matches lit-review-vector-search.html's design system
# ---------------------------------------------------------------------------

DECK_HEAD = """<title>{deck_title}</title>
<style>
  :root {{
    --bg:#0a0b10; --panel:#12141c; --panel2:#171a24;
    --ink:#eef0f7; --ink-soft:#a2a8bd; --ink-faint:#5c6178; --line:#23273a;
    --gold:#ffcf4a; --cyan:#7fd4ff; --green:#52d98a;
    --thai:"Noto Sans Thai","IBM Plex Sans Thai","Sarabun","Thonburi",system-ui,-apple-system,sans-serif;
    --mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,monospace;
  }}
  * {{ box-sizing:border-box; margin:0; }}
  html,body {{ height:100%; }}
  body {{
    background:
      radial-gradient(120% 90% at 50% -20%, #171d33 0%, #0a0b1000 55%),
      radial-gradient(70% 50% at 88% 6%, #241a33 0%, #0a0b1000 60%),
      var(--bg);
    color:var(--ink); font-family:var(--thai); -webkit-font-smoothing:antialiased; overflow:hidden;
  }}
  .deck {{ position:fixed; inset:0; }}
  .slide {{
    position:absolute; inset:0; display:flex; flex-direction:column; justify-content:center;
    padding:clamp(20px,5.5vw,84px);
    opacity:0; visibility:hidden; transform:translateY(14px);
    transition:opacity .4s ease, transform .4s ease, visibility .4s;
  }}
  .slide.active {{ opacity:1; visibility:visible; transform:none; }}
  @media (prefers-reduced-motion:reduce){{ .slide{{ transition:opacity .01s; transform:none; }} }}
  .inner {{ max-width:1080px; width:100%; margin:0 auto; }}
  .eyebrow {{ font-family:var(--mono); font-size:clamp(12px,1.4vw,15px); letter-spacing:0.18em; text-transform:uppercase; color:var(--ink-faint); font-weight:700; margin-bottom:14px; }}
  .eyebrow .n {{ color:var(--gold); }}
  h1 {{ font-size:clamp(32px,5.8vw,66px); font-weight:800; letter-spacing:-0.02em; line-height:1.22; text-wrap:balance; }}
  h2 {{ font-size:clamp(25px,4.4vw,46px); font-weight:800; letter-spacing:-0.015em; line-height:1.14; text-wrap:balance; margin-bottom:6px; }}
  .title-sub {{ font-size:clamp(17px,2.4vw,24px); color:var(--cyan); font-weight:600; margin-top:12px; }}
  .figwrap {{ margin-top:10px; display:flex; flex-direction:column; align-items:center; gap:10px; }}
  .figmat {{ position:relative; border:1px solid var(--line); border-radius:16px; background:var(--panel2); padding:10px; max-width:100%; cursor:zoom-in; }}
  .figmat:hover, .figmat:focus-visible {{ border-color:var(--cyan); }}
  .figmat img {{ display:block; max-width:100%; max-height:min(64vh,660px); width:auto; height:auto; border-radius:8px; }}
  .cap {{ font-family:var(--thai); font-size:clamp(14px,1.7vw,18px); color:var(--ink-soft); text-align:center; max-width:72ch; line-height:1.5; }}
  @media (max-height:700px) {{ .figmat img {{ max-height:52vh; }} }}
  .zoom-hint {{ position:absolute; right:20px; bottom:20px; display:flex; align-items:center; gap:7px; font-family:var(--mono); font-size:11.5px; color:var(--ink-soft); background:#0a0b10cc; border:1px solid var(--line); border-radius:999px; padding:6px 12px; opacity:0; transition:opacity .2s ease; pointer-events:none; }}
  .figmat:hover .zoom-hint {{ opacity:1; }}
  .zoom-hint kbd {{ font-weight:700; color:var(--gold); }}
  .lightbox {{ position:fixed; inset:0; z-index:50; background:#05050acc; backdrop-filter:blur(6px); display:flex; align-items:center; justify-content:center; padding:5vw; opacity:0; visibility:hidden; transition:opacity .28s cubic-bezier(0.22,1,0.36,1); cursor:zoom-out; }}
  .lightbox.active {{ opacity:1; visibility:visible; }}
  .lightbox img {{ max-width:92vw; max-height:92vh; border-radius:10px; border:1px solid var(--line); }}
  .progress {{ position:fixed; top:0; left:0; height:3px; background:linear-gradient(90deg,var(--cyan),var(--gold)); width:0; transition:width .35s ease; z-index:10; }}
  .counter {{ position:fixed; bottom:22px; right:26px; font-family:var(--mono); font-size:13px; color:var(--ink-faint); z-index:10; font-variant-numeric:tabular-nums; }}
  .brand {{ position:fixed; bottom:22px; left:26px; font-family:var(--mono); font-size:12px; color:var(--ink-faint); z-index:10; }}
  .nav-zone {{ position:fixed; top:0; bottom:0; width:22%; z-index:5; cursor:pointer; }}
  .nav-zone.prev {{ left:0; }} .nav-zone.next {{ right:0; }}
  :focus-visible {{ outline:2px solid var(--cyan); outline-offset:3px; }}
</style>

<div class="progress" id="progress"></div>
<div class="deck" id="deck">
"""

DECK_TAIL = """</div>
<div class="lightbox" id="lightbox"><img id="lightboxImg" src="" alt=""></div>
<div class="nav-zone prev" id="navPrev"></div>
<div class="nav-zone next" id="navNext"></div>
<div class="counter" id="counter">1 / {n}</div>
<div class="brand">ARRA Oracle · slide-forge</div>
<script>
  (function(){{
    const slides=[...document.querySelectorAll('.slide')];
    const progress=document.getElementById('progress');
    const counter=document.getElementById('counter');
    const lb=document.getElementById('lightbox'), lbImg=document.getElementById('lightboxImg');
    let i=0, lbOpen=false;
    function show(n){{
      i=Math.max(0,Math.min(slides.length-1,n));
      slides.forEach((s,k)=>s.classList.toggle('active',k===i));
      progress.style.width=((i+1)/slides.length*100)+'%';
      counter.textContent=(i+1)+' / '+slides.length;
    }}
    function openLb(img){{ lbImg.src=img.src; lb.classList.add('active'); lbOpen=true; }}
    function closeLb(){{ lb.classList.remove('active'); lbOpen=false; }}
    document.querySelectorAll('.figmat').forEach(fm=>{{
      const img=fm.querySelector('img'); if(img) fm.addEventListener('click',()=>openLb(img));
    }});
    lb.addEventListener('click',closeLb);
    document.addEventListener('keydown',e=>{{
      if(lbOpen){{ if(e.key==='Escape'||e.key.toLowerCase()==='z'){{closeLb();}} return; }}
      if(['ArrowRight','ArrowDown',' ','PageDown'].includes(e.key)){{e.preventDefault();show(i+1);}}
      else if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){{e.preventDefault();show(i-1);}}
      else if(e.key==='Home')show(0); else if(e.key==='End')show(slides.length-1);
      else if(e.key.toLowerCase()==='z'){{const im=slides[i].querySelector('.figmat img'); if(im){{e.preventDefault();openLb(im);}}}}
    }});
    document.getElementById('navNext').addEventListener('click',()=>show(i+1));
    document.getElementById('navPrev').addEventListener('click',()=>show(i-1));
    let sx=null;
    document.addEventListener('touchstart',e=>{{sx=e.touches[0].clientX;}},{{passive:true}});
    document.addEventListener('touchend',e=>{{if(sx===null)return;const dx=e.changedTouches[0].clientX-sx;if(Math.abs(dx)>45)show(dx<0?i+1:i-1);sx=null;}},{{passive:true}});
    const p=parseInt(new URLSearchParams(location.search).get('p')||location.hash.replace('#',''),10);
    show(!isNaN(p)?p-1:0);
  }})();
</script>
"""


def esc(s):
    return html_mod.escape(s or "")


def render_deck(state):
    parts = [DECK_HEAD.format(deck_title=esc(state.get("title") or "Forged Deck"))]
    # optional cover
    if state.get("title") or state.get("subtitle"):
        parts.append(f"""  <section class="slide active">
    <div class="inner">
      <div class="eyebrow"><span class="n">ARRA ORACLE</span> · slide-forge</div>
      <h1>{esc(state.get('title') or 'Forged Deck')}</h1>
      {f'<div class="title-sub">{esc(state["subtitle"])}</div>' if state.get('subtitle') else ''}
    </div>
  </section>
""")
    first = not (state.get("title") or state.get("subtitle"))
    for idx, name in enumerate(state["order"]):
        s = state["slides"][name]
        active = " active" if (first and idx == 0) else ""
        eyebrow = f'<div class="eyebrow">{esc(s.get("eyebrow"))}</div>' if s.get("eyebrow") else ""
        title = f'<h2>{esc(s.get("title"))}</h2>' if s.get("title") else ""
        cap = f'<div class="cap">{esc(s.get("caption"))}</div>' if s.get("caption") else ""
        parts.append(f"""  <section class="slide{active}">
    <div class="inner">
      {eyebrow}
      {title}
      <div class="figwrap">
        <div class="figmat" role="button" tabindex="0" aria-label="zoom"><img src="{data_uri(name)}" alt="{esc(s.get('title') or name)}"><span class="zoom-hint">🔍 <kbd>Z</kbd></span></div>
        {cap}
      </div>
    </div>
  </section>
""")
    n = len(state["order"]) + (1 if not first else 0)
    parts.append(DECK_TAIL.format(n=max(n, 1)))
    return "".join(parts)


# ---------------------------------------------------------------------------
# Editor UI
# ---------------------------------------------------------------------------

def render_editor(state):
    rows = []
    for i, name in enumerate(state["order"]):
        s = state["slides"][name]
        rows.append(f"""
    <div class="card" data-name="{esc(name)}">
      <div class="thumb"><img src="/img/{esc(name)}" alt=""></div>
      <div class="fields">
        <div class="fname">{esc(name)} <span class="pos">#{i+1}</span></div>
        <input class="f-eyebrow" placeholder="eyebrow (มุมบน, เช่น 'ภาพจริง 1/2 · แผนที่ความรู้')" value="{esc(s.get('eyebrow'))}">
        <input class="f-title" placeholder="หัวข้อสไลด์ (h2)" value="{esc(s.get('title'))}">
        <textarea class="f-caption" placeholder="คำบรรยายใต้ภาพ (caption) — ให้ AI ช่วยเขียนได้">{esc(s.get('caption'))}</textarea>
        <div class="rowbtns">
          <button onclick="move('{esc(name)}',-1)">↑ ขึ้น</button>
          <button onclick="move('{esc(name)}',1)">↓ ลง</button>
        </div>
      </div>
    </div>""")
    return EDITOR_HTML.format(
        rows="".join(rows) or '<p class="empty">ยังไม่มีรูป — ลากรูปมาวางด้านบน หรือก็อปไฟล์ไปไว้ใน inbox/</p>',
        deck_title=esc(state.get("title") or "Forged Deck"),
        subtitle=esc(state.get("subtitle")),
    )


EDITOR_HTML = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Slide Forge</title>
<style>
  :root {{ --bg:#0d0f14; --panel:#161a20; --line:#262b34; --ink:#e8eaf0; --soft:#9aa0ad; --accent:#7fd4ff; --gold:#ffcf4a; --green:#52d98a; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font-family:system-ui,-apple-system,"Segoe UI",sans-serif; }}
  header {{ position:sticky; top:0; z-index:5; background:#0d0f14ee; backdrop-filter:blur(8px); border-bottom:1px solid var(--line); padding:16px 24px; display:flex; align-items:center; gap:16px; flex-wrap:wrap; }}
  h1 {{ font-size:19px; margin:0; }}
  .meta {{ color:var(--soft); font-size:13px; }}
  .spacer {{ flex:1; }}
  button {{ font:inherit; cursor:pointer; border:1px solid var(--line); background:#1b2028; color:var(--ink); border-radius:8px; padding:8px 14px; }}
  button:hover {{ border-color:var(--accent); color:var(--accent); }}
  button.primary {{ background:#173a2a; border-color:#2c6b4a; color:var(--green); font-weight:600; }}
  button.go {{ background:#3a2a17; border-color:#6b4a2c; color:var(--gold); font-weight:600; }}
  main {{ max-width:900px; margin:0 auto; padding:24px; }}
  .deckmeta {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:20px; }}
  .deckmeta input {{ width:100%; }}
  input, textarea {{ font:inherit; background:#10131a; color:var(--ink); border:1px solid var(--line); border-radius:8px; padding:9px 11px; width:100%; }}
  input:focus, textarea:focus {{ outline:none; border-color:var(--accent); }}
  textarea {{ min-height:64px; resize:vertical; line-height:1.5; }}
  #drop {{ border:2px dashed var(--line); border-radius:14px; padding:34px; text-align:center; color:var(--soft); margin-bottom:24px; transition:.15s; }}
  #drop.over {{ border-color:var(--accent); color:var(--accent); background:#111820; }}
  .card {{ display:grid; grid-template-columns:200px 1fr; gap:16px; background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:16px; margin-bottom:16px; }}
  .thumb img {{ width:100%; border-radius:8px; display:block; }}
  .fields {{ display:flex; flex-direction:column; gap:9px; }}
  .fname {{ font-family:ui-monospace,Menlo,monospace; font-size:12px; color:var(--soft); }}
  .pos {{ color:var(--gold); font-weight:700; }}
  .rowbtns {{ display:flex; gap:8px; }}
  .rowbtns button {{ padding:5px 10px; font-size:13px; }}
  .empty {{ color:var(--soft); text-align:center; padding:40px; }}
  .hint {{ color:var(--soft); font-size:12.5px; line-height:1.6; margin-bottom:18px; }}
  .hint code {{ background:#10131a; padding:1px 6px; border-radius:4px; color:var(--gold); }}
  #status {{ font-size:13px; color:var(--green); }}
</style></head><body>
<header>
  <h1>🔨 Slide Forge</h1>
  <span class="meta">โยนรูป → ได้ deck สวยในดีไซน์เดียวกับ workshop</span>
  <span class="spacer"></span>
  <span id="status"></span>
  <button class="primary" onclick="save()">💾 บันทึกข้อความ</button>
  <button class="go" onclick="build()">🔨 Build deck</button>
  <a href="/preview" target="_blank"><button>▶ ดู deck</button></a>
</header>
<main>
  <p class="hint">
    <b>วิธีใช้:</b> 1) ลากรูปมาวางในกล่องด้านล่าง (หรือก็อปไฟล์ไปที่ <code>tools/slide-forge/inbox/</code>) ·
    2) ใส่ eyebrow/หัวข้อ/คำบรรยาย แต่ละรูป — <b>หรือให้ AI ช่วย</b>: บอก Claude ว่า
    "describe the slide-forge inbox images" แล้ว AI จะเขียน caption ให้ทุกใบ ·
    3) กด <b>Build deck</b> → ได้ไฟล์ <code>artifacts/forged-deck.html</code> ดู/present ได้เลย
  </p>
  <div class="deckmeta">
    <input id="deckTitle" placeholder="ชื่อ deck (สไลด์ปก)" value="{deck_title}">
    <input id="deckSub" placeholder="subtitle ปก (optional)" value="{subtitle}">
  </div>
  <div id="drop">📥 ลากรูปมาวางที่นี่ — หรือกดปุ่ม <b>➕ New</b> เพื่อเลือกไฟล์ (png / jpg / gif / webp, หลายไฟล์พร้อมกันได้)
    <div style="margin-top:14px"><button class="go" onclick="document.getElementById('picker').click()">➕ New — เลือกรูป</button></div>
    <input id="picker" type="file" accept="image/*" multiple style="display:none">
  </div>
  <div id="cards">{rows}</div>
</main>
<script>
  const drop=document.getElementById('drop'), cards=document.getElementById('cards'), status=document.getElementById('status'), picker=document.getElementById('picker');
  function flash(t){{ status.textContent=t; setTimeout(()=>status.textContent='',2500); }}
  async function uploadFiles(files){{
    const imgs=[...files].filter(f=>f.type.startsWith('image/'));
    for(const f of imgs){{
      const buf=await f.arrayBuffer();
      const b64=btoa(String.fromCharCode(...new Uint8Array(buf)));
      await fetch('/upload?name='+encodeURIComponent(f.name),{{method:'POST',body:b64}});
    }}
    flash(imgs.length+' รูปเพิ่มแล้ว'); location.reload();
  }}
  picker.addEventListener('change',ev=>uploadFiles(ev.target.files));
  ['dragenter','dragover'].forEach(e=>drop.addEventListener(e,ev=>{{ev.preventDefault();drop.classList.add('over');}}));
  ['dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{{ev.preventDefault();drop.classList.remove('over');}}));
  drop.addEventListener('drop',async ev=>{{
    await uploadFiles(ev.dataTransfer.files);
  }});
  function collect(){{
    const slides={{}}, order=[];
    document.querySelectorAll('.card').forEach(c=>{{
      const n=c.dataset.name; order.push(n);
      slides[n]={{eyebrow:c.querySelector('.f-eyebrow').value,title:c.querySelector('.f-title').value,caption:c.querySelector('.f-caption').value}};
    }});
    return {{order,slides,title:document.getElementById('deckTitle').value,subtitle:document.getElementById('deckSub').value}};
  }}
  async function save(){{ await fetch('/save',{{method:'POST',body:JSON.stringify(collect())}}); flash('บันทึกแล้ว'); }}
  async function build(){{ await save(); const r=await fetch('/build',{{method:'POST'}}); const j=await r.json(); flash('Build เสร็จ → '+j.out); }}
  async function move(name,dir){{ await save(); await fetch('/move?name='+encodeURIComponent(name)+'&dir='+dir,{{method:'POST'}}); location.reload(); }}
</script></body></html>"""


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        print("[forge] " + (a[0] % a[1:]) if a else "")

    def _send(self, status, ctype, body):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            self._send(200, "text/html; charset=utf-8", render_editor(load_state()))
        elif u.path == "/preview":
            self._send(200, "text/html; charset=utf-8", render_deck(load_state()))
        elif u.path.startswith("/img/"):
            name = u.path[5:]
            p = INBOX / name
            if p.is_file() and p.suffix.lower() in IMG_EXT:
                self._send(200, mimetypes.guess_type(str(p))[0] or "image/png", p.read_bytes())
            else:
                self._send(404, "text/plain", b"no")
        else:
            self._send(404, "text/plain", b"no")

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b""
        if u.path == "/upload":
            name = q.get("name", ["img.png"])[0].replace("/", "_").replace("..", "_")
            try:
                (INBOX / name).write_bytes(base64.b64decode(raw))
                self._send(200, "application/json", json.dumps({"ok": True}))
            except Exception as e:
                self._send(400, "application/json", json.dumps({"error": str(e)}))
        elif u.path == "/save":
            try:
                save_state(json.loads(raw.decode("utf-8")))
                self._send(200, "application/json", json.dumps({"ok": True}))
            except Exception as e:
                self._send(400, "application/json", json.dumps({"error": str(e)}))
        elif u.path == "/move":
            name = q.get("name", [""])[0]
            dir_ = int(q.get("dir", ["0"])[0])
            st = load_state()
            if name in st["order"]:
                i = st["order"].index(name)
                j = max(0, min(len(st["order"]) - 1, i + dir_))
                st["order"].insert(j, st["order"].pop(i))
                save_state(st)
            self._send(200, "application/json", json.dumps({"ok": True}))
        elif u.path == "/build":
            st = load_state()
            OUT_DECK.write_text(render_deck(st), encoding="utf-8")
            self._send(200, "application/json", json.dumps({"ok": True, "out": str(OUT_DECK)}))
        else:
            self._send(404, "text/plain", b"no")


class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def pick_port():
    for p in CANDIDATE_PORTS:
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p)); return p
            except OSError:
                continue
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]


def main():
    port = pick_port()
    print(f"🔨 Slide Forge: http://127.0.0.1:{port}/")
    print(f"   Drop images or drop files into: {INBOX}")
    print(f"   Build target: {OUT_DECK}")
    TS(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
