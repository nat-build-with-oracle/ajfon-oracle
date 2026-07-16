"""
ติดตั้ง book-theme แบบ token-level: คุม --jp-* variables ของ nbconvert ทั้งชุด
(nbconvert เดินทุกสีผ่านตัวแปรพวกนี้ → flip ที่ตัวแปร = คุม syntax/table/code/link ครบ)
รันซ้ำได้ (idempotent)
"""
import glob, re

THEME = r"""<style id="book-theme">
/* ===== Super Complete Book — token-level theme (light + dark, WCAG AA) ===== */
:root {
  /* --- typography / layout --- */
  --jp-content-font-family: "Sukhumvit Set","Thonburi","Noto Sans Thai",sans-serif;
  --jp-ui-font-family: var(--jp-content-font-family);
  --jp-content-font-size1: 1.12rem;
  --jp-content-line-height: 1.85;
  --jp-code-font-size: 1rem;
  --jp-code-line-height: 1.65;
  /* --- LIGHT syntax palette (นับ contrast แล้ว ≥4.5 บนพื้นโค้ด #f5f5f5) --- */
  --jp-mirror-editor-keyword-color: #a626a4;     /* keyword ม่วง */
  --jp-mirror-editor-operator-color: #0b7a75;    /* operator teal เข้ม */
  --jp-mirror-editor-punctuation-color: #454138;
  --jp-mirror-editor-variable-color: #1c1b18;
  --jp-mirror-editor-number-color: #0a6b0a;      /* number เขียวเข้ม */
  --jp-mirror-editor-string-color: #b23327;      /* string แดงเข้ม */
  --jp-mirror-editor-comment-color: #4a4a4a;     /* comment เทาเข้ม (ผ่าน 4.5) */
  --jp-content-link-color: #1a63c0;              /* link น้ำเงินเข้มพอ */
  --book-nav-fg: #1a63c0;
}
html { font-size: 20px; }
body { font-family: var(--jp-content-font-family) !important; }
.jp-Notebook { max-width: 980px; margin: 0 auto; padding: 40px 24px 100px !important; }
.jp-RenderedHTMLCommon { font-size: 1.12rem !important; line-height: 1.85 !important; }
.jp-RenderedHTMLCommon p, .jp-RenderedHTMLCommon li { font-size: 1.12rem !important; }
.jp-RenderedHTMLCommon h1 { font-size: 2.3rem !important; font-weight: 700; line-height: 1.3;
  text-wrap: balance; margin: 1em 0 .5em; }
.jp-RenderedHTMLCommon h2 { font-size: 1.65rem !important; margin-top: 2.4em !important;
  padding-bottom: 8px; }
.jp-RenderedHTMLCommon h3 { font-size: 1.3rem !important; }
.jp-InputArea-editor, .highlight, div.highlight { border-radius: 12px !important; overflow-x: hidden !important; }
/* ⭐ wrap โค้ด: แสดงครบทุกบรรทัด copy ได้ ไม่มี scrollbar (คงย่อหน้าด้วย pre-wrap) */
.highlight pre, .jp-OutputArea-output pre, .jp-RenderedText pre {
  white-space: pre-wrap !important; word-break: break-word !important; overflow-wrap: anywhere !important; }
.jp-Cell-inputWrapper, .jp-InputArea, .jp-CodeMirrorEditor { min-width: 0 !important; }
.jp-OutputArea-output pre { border-radius: 10px; padding: 12px 16px !important; }
/* ซ่อน ¶ anchor (contrast ต่ำ + ไม่จำเป็นสำหรับหนังสือ) */
.jp-RenderedHTMLCommon .anchor-link { opacity: 0; }
.jp-RenderedHTMLCommon :hover > .anchor-link { opacity: .5; }
a#book-nav { position: fixed; top: 16px; left: 18px; font-size: .85rem; z-index: 10;
  background: var(--jp-layout-color1); border: 1px solid var(--jp-border-color1);
  padding: 8px 18px; border-radius: 999px; text-decoration: none; color: var(--book-nav-fg); }
/* ===== hover motion (เฉพาะเว็บ · Colab/notebook ไม่กระทบ · เคารพ reduced-motion) ===== */
@media (prefers-reduced-motion: no-preference) {
  .jp-InputArea-editor, .highlight, div.highlight { transition: transform .18s cubic-bezier(.22,1,.36,1), box-shadow .18s ease-out; }
  .jp-InputArea-editor:hover, .highlight:hover, div.highlight:hover {
    transform: translateY(-2px); box-shadow: 0 8px 24px -8px rgba(0,0,0,.28); }
  .jp-RenderedHTMLCommon img { transition: transform .22s cubic-bezier(.22,1,.36,1), box-shadow .22s ease-out; border-radius: 8px; }
  .jp-RenderedHTMLCommon img:hover { transform: scale(1.015); box-shadow: 0 12px 32px -10px rgba(0,0,0,.35); }
  .jp-RenderedHTMLCommon tbody tr { transition: background-color .14s ease-out; }
  .jp-RenderedHTMLCommon tbody tr:hover { background: var(--jp-rendermime-table-row-hover-background, #eef); }
  a#book-nav { transition: transform .16s ease-out, box-shadow .16s ease-out; }
  a#book-nav:hover { transform: translateY(-1px); box-shadow: 0 6px 18px -6px rgba(0,0,0,.3); }
  .jp-RenderedHTMLCommon a { transition: color .12s ease-out; }
}
@media print { html { font-size: 15px; } a#book-nav { display: none; } }

/* ===== DARK: flip token ทั้งชุด (nbconvert อ่านค่าจากตัวแปรพวกนี้) ===== */
@media (prefers-color-scheme: dark) {
  :root {
    /* พื้น + เส้น + ตัวหนังสือ */
    --jp-layout-color0: #1a1a19;  --jp-layout-color1: #1a1a19;
    --jp-layout-color2: #242423;  --jp-layout-color3: #2f2f2d;  --jp-layout-color4: #3a3934;
    --jp-content-font-color0: #f4f3ec; --jp-content-font-color1: #eae9e1;
    --jp-content-font-color2: #c3c2b7; --jp-content-font-color3: #a5a49a;
    --jp-border-color0: #3a3934; --jp-border-color1: #3a3934;
    --jp-border-color2: #45443e; --jp-border-color3: #514f48;
    --jp-content-link-color: #6ba6f5;
    --book-nav-fg: #6ba6f5;
    /* code editor + prompt */
    --jp-cell-editor-background: #242423; --jp-cell-editor-background-color: #242423;
    --jp-cell-inprompt-font-color: #6ba6f5; --jp-cell-outprompt-font-color: #4bbf90;
    --jp-cell-prompt-not-active-font-color: #c3c2b7;
    /* ⭐ syntax palette สว่างพอทุกตัว (contrast ≥4.5 บนพื้นโค้ด #242423) */
    --jp-mirror-editor-variable-color: #ecebe3;   /* ตัวแปร/base — สว่างสุด */
    --jp-mirror-editor-keyword-color: #d9a6f0;    /* keyword ม่วงอ่อน */
    --jp-mirror-editor-operator-color: #7fe0c0;   /* operator เขียวมิ้นต์ */
    --jp-mirror-editor-punctuation-color: #cfcdc2;
    --jp-mirror-editor-number-color: #eccf7d;     /* number เหลือง */
    --jp-mirror-editor-string-color: #f0ad85;     /* string ส้มอ่อน */
    --jp-mirror-editor-comment-color: #a7a59a;    /* comment เทาสว่างพอ (≥4.5) */
    --jp-mirror-editor-error-color: #ff8f8f;
    /* ตาราง + error output พื้นเข้ม */
    --jp-rendermime-table-row-background: #202020;
    --jp-rendermime-table-row-hover-background: #2a2a28;
    --jp-error-color0: #ff8f8f;
  }
  /* กันเคส inline code / td ที่ยังอ่านพื้นสว่างค้าง */
  .jp-RenderedHTMLCommon code { background: #242423 !important; color: #f0c9a0 !important; }
  .jp-RenderedHTMLCommon table, .jp-RenderedHTMLCommon td, .jp-RenderedHTMLCommon th {
    background: #1a1a19 !important; color: #eae9e1 !important; border-color: #3a3934 !important; }
  .jp-RenderedHTMLCommon th { background: #242423 !important; }
  .highlight, div.highlight, .jp-InputArea-editor { background: #242423 !important; }
  .highlight pre { color: #ecebe3 !important; }
  .jp-OutputArea-output, .jp-OutputArea-output pre { background: #242423 !important; color: #eae9e1 !important; }
}
</style>
<a id="book-nav" href="index.html">📗 สารบัญ</a>
"""

n = 0
import sys, os
_dir = sys.argv[1] if len(sys.argv)>1 else 'html'
for f in glob.glob(os.path.join(_dir,'*.html')):
    h = open(f).read()
    h = re.sub(r'<style id="book-theme">.*?</a>\s*', '', h, flags=re.S)
    h = h.replace('</head>', THEME + '\n</head>', 1)
    open(f, 'w').write(h)
    n += 1
print(f'token-level theme → {n} หน้า ✓')
