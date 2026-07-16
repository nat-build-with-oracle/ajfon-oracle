"""
Snapshot ทุกหน้า HTML (light + dark) + คำนวณ WCAG contrast ทุก text element จริง
ผลลัพธ์: book/shots/*.png + รายงาน contrast fail
"""
import sys, glob, os, json
from pathlib import Path
from playwright.sync_api import sync_playwright

import os
BASE = os.environ.get("QA_BASE", "http://localhost:8890")
OUT = Path("shots"); OUT.mkdir(exist_ok=True)

# WCAG relative luminance + contrast ratio (คำนวณจาก computed rgb จริงในเบราว์เซอร์)
CONTRAST_JS = r"""
() => {
  function lum(c) {
    const [r,g,b] = c.map(v => { v/=255; return v<=0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); });
    return 0.2126*r + 0.7152*g + 0.0722*b;
  }
  function ratio(a, b) { const [L1,L2]=[lum(a),lum(b)].sort((x,y)=>y-x); return (L1+0.05)/(L2+0.05); }
  function parse(s){ const m=s.match(/rgba?\(([^)]+)\)/); if(!m) return null;
    const p=m[1].split(',').map(x=>parseFloat(x)); return p.slice(0,3); }
  function _stops(img){if(!img||img==='none')return[];const o=[],re=/rgba?\([^)]+\)|#[0-9a-fA-F]{3,8}/g;let m;while((m=re.exec(img))){let x=m[0];if(x[0]==='#'){let h=x.slice(1);if(h.length===3)h=[...h].map(y=>y+y).join('');o.push([parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)]);}else{const c2=parse(x);if(c2)o.push(c2);}}return o;}
  function bgOf(el){ let e=el; while(e){ const st=getComputedStyle(e); const b=parse(st.backgroundColor); if(b) return b; const g=_stops(st.backgroundImage); if(g.length) return {grad:g}; e=e.parentElement; } return [255,255,255]; }
  const out=[];
  for (const el of document.querySelectorAll('p, li, td, th, h1, h2, h3, h4, span, a, code, pre')) {
    const txt = (el.innerText||'').trim();
    if (!txt || el.children.length > 0 && !['CODE','PRE','SPAN','A'].includes(el.tagName)) continue;
    const st = getComputedStyle(el);
    const fg = parse(st.color); if(!fg) continue;
    const bg = bgOf(el);
    const size = parseFloat(st.fontSize);
    const bold = parseInt(st.fontWeight) >= 700;
    const large = size >= 24 || (size >= 18.66 && bold);
    const r = ratio(fg, bg);
    const need = large ? 3.0 : 4.5;
    if (r < need) {
      out.push({ tag: el.tagName, size: Math.round(size), bold, large,
                 ratio: Math.round(r*100)/100, need, fg: `rgb(${fg.join(',')})`,
                 bg: `rgb(${bg.join(',')})`, text: txt.slice(0,40) });
    }
  }
  return out;
}
"""

_pat = os.environ.get('QA_GLOB', 'html/*.html')
pages = sorted(p.split('/')[-1] for p in glob.glob(_pat))
report = {}

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for scheme in ['light', 'dark']:
        ctx = browser.new_context(color_scheme=scheme, viewport={'width': 1200, 'height': 900},
                                  device_scale_factor=2)
        page = ctx.new_page()
        for f in pages:
            page.goto(f"{BASE}/{f}", wait_until='networkidle')
            page.wait_for_timeout(400)
            name = f.replace('.html', '')
            page.screenshot(path=str(OUT / f"{name}__{scheme}.png"), full_page=True)
            fails = page.evaluate(CONTRAST_JS)
            report.setdefault(f, {})[scheme] = fails
        ctx.close()
    browser.close()

# สรุป
total_fail = 0
print("\n=== CONTRAST AUDIT (WCAG AA) ===")
for f, schemes in report.items():
    for scheme, fails in schemes.items():
        if fails:
            total_fail += len(fails)
            print(f"\n[{scheme}] {f}: {len(fails)} fail")
            seen = set()
            for x in fails:
                key = (x['fg'], x['bg'], x['tag'])
                if key in seen: continue
                seen.add(key)
                print(f"   {x['tag']:5} {x['ratio']:.2f}:1 (need {x['need']}) "
                      f"{x['fg']} on {x['bg']}  \"{x['text']}\"")

print(f"\n=== รวม {total_fail} contrast fail · snapshot {len(pages)*2} ภาพใน shots/ ===")
json.dump(report, open('shots/contrast_report.json', 'w'), ensure_ascii=False, indent=1)
