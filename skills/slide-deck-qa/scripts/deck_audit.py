"""
Slide-deck QA — snapshot ทุกสไลด์ที่ projector res + ตรวจ 4 อย่างต่อสไลด์:
  1. WCAG contrast (ทุก text element จริง)
  2. overflow — เนื้อหาล้น viewport (โดนตัดตอน present)
  3. image 404 / broken (network + <img> naturalWidth)
  4. รูป snapshot ให้ดูด้วยตา (shots/slide_NN.png)

รัน:  python deck_audit.py <URL หรือ path>  [--slides N] [--key ArrowRight] [--w 1920 --h 1080]
ต้อง serve ผ่าน http (ไม่ใช่ file://) — สคริปต์ start server ให้เองถ้าให้ path

env: PWDECK_KEY (ปุ่มเปลี่ยนสไลด์, default ArrowRight) · PWDECK_SEL (selector นับสไลด์, default '.slide')
"""
import sys, os, json, subprocess, time, socket, threading, http.server, functools
from pathlib import Path
from playwright.sync_api import sync_playwright

args = sys.argv[1:]
target = next((a for a in args if not a.startswith('--')), None)
if not target:
    print("usage: python deck_audit.py <deck.html | http://...> [--slides N] [--key ArrowRight]"); sys.exit(1)
def opt(name, d):
    return args[args.index(name)+1] if name in args else d
N_MAX  = int(opt('--slides', '80'))
KEY    = opt('--key', os.environ.get('PWDECK_KEY', 'ArrowRight'))
SEL    = os.environ.get('PWDECK_SEL', '.slide')
W, H   = int(opt('--w','1920')), int(opt('--h','1080'))
OUT = Path('deck-shots'); OUT.mkdir(exist_ok=True)

# ---- serve local file over http (file:// breaks hash-nav + relative img) ----
url, httpd = target, None
if not target.startswith('http'):
    p = Path(target).resolve()
    root, page = p.parent, p.name
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    httpd = http.server.HTTPServer(('127.0.0.1', port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}/{page}"
    print(f"serving {root} → {url}")

CONTRAST_JS = r"""() => {
  function lum(c){const[r,g,b]=c.map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});return .2126*r+.7152*g+.0722*b}
  function ratio(a,b){const[L1,L2]=[lum(a),lum(b)].sort((x,y)=>y-x);return(L1+.05)/(L2+.05)}
  function parseA(s){const m=s.match(/rgba?\(([^)]+)\)/);if(!m)return null;const p=m[1].split(',').map(parseFloat);const a=p.length>=4?p[3]:1;return[p[0],p[1],p[2],a]}
  function parse(s){const c=parseA(s);return c&&c[3]>0?c.slice(0,3):null}
  function over(fg,bg,a){return[a*fg[0]+(1-a)*bg[0], a*fg[1]+(1-a)*bg[1], a*fg[2]+(1-a)*bg[2]]}
  function stops(img){ if(!img||img==='none')return[]; const out=[],re=/rgba?\([^)]+\)|#[0-9a-fA-F]{3,8}/g;let m;
    while((m=re.exec(img))){let c=m[0];
      if(c[0]==='#'){let h=c.slice(1);if(h.length===3)h=[...h].map(x=>x+x).join('');out.push([parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)]);}
      else{const c2=parse(c);if(c2)out.push(c2);}}
    return out; }
  // bg(): ⭐ composite alpha ทุกชั้นทับกันจนถึงพื้นทึบ (แก้ tinted pill: rgba(สีtext,.1) ≠ สีtext ดิบ)
  function bg(el){
    const layers=[]; let e=el, base=null, grad=null, image=false;
    while(e){const st=getComputedStyle(e);
      const c=parseA(st.backgroundColor);
      if(c&&c[3]>0){ if(c[3]>=1){base=c.slice(0,3);break;} layers.push(c); }   // กึ่งโปร่ง → เก็บไว้ composite
      const gs=stops(st.backgroundImage); if(gs.length){grad=gs;break;}          // gradient = พื้น
      if(st.backgroundImage&&st.backgroundImage.includes('url(')){image=true;break;}
      e=e.parentElement;}
    if(image)return{image:true};
    if(grad)return{grad, layers};                                                // composite layers บน grad ทีหลัง
    if(!base)base=[20,20,19];                                                     // default slide bg เข้ม
    for(let i=layers.length-1;i>=0;i--)base=over(layers[i],base,layers[i][3]);    // composite back→front
    return{solid:base};}
  const vis=[...document.querySelectorAll('.slide')].find(s=>getComputedStyle(s).display!=='none'&&getComputedStyle(s).opacity!=='0')||document.body;
  const out=[],skip=[];
  for(const el of vis.querySelectorAll('p,li,td,th,h1,h2,h3,h4,span,a,code,pre,div')){
    if(el.offsetParent===null)continue;
    // ⭐ เช็คเฉพาะ own direct text (ข้าม wrapper ที่ text อยู่ใน child คนละสี — child ถูกเช็คแยก)
    let own=''; for(const n of el.childNodes) if(n.nodeType===3) own+=n.textContent;
    const t=own.trim(); if(!t)continue;
    const st=getComputedStyle(el),fg=parse(st.color);if(!fg)continue;
    const sz=parseFloat(st.fontSize),bold=parseInt(st.fontWeight)>=700,large=sz>=24||(sz>=18.66&&bold);
    const need=large?3:4.5, b=bg(el);
    if(b.image){skip.push({tag:el.tagName,reason:'image-bg',text:t.slice(0,38)});continue;}
    // gradient → composite layers กึ่งโปร่งบนแต่ละ stop แล้วเอา contrast แย่สุด (conservative)
    let bgs;
    if(b.grad){ bgs = b.grad.map(stop=>{ let base=stop; for(let i=(b.layers||[]).length-1;i>=0;i--)base=over(b.layers[i],base,b.layers[i][3]); return base; }); }
    else bgs = [b.solid];
    const worst = Math.min(...bgs.map(c=>ratio(fg,c)));
    if(worst<need) out.push({tag:el.tagName,ratio:Math.round(worst*100)/100,need,text:t.slice(0,38),bg:b.grad?'gradient':'solid'});
  }
  // overflow: เนื้อหาล้น viewport
  const de=document.documentElement, of={x:de.scrollWidth>innerWidth+2, y:vis.scrollHeight>innerHeight+2};
  // broken <img>
  const broken=[...document.querySelectorAll('img')].filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src);
  return {contrast:out, skipped:skip, overflow:of, broken};
}"""

report=[]; total_c=total_of=total_404=0
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(viewport={'width':W,'height':H}, device_scale_factor=1)
    page = ctx.new_page()
    net404=[]
    page.on('response', lambda r: net404.append(r.url) if r.status>=400 else None)
    page.goto(url, wait_until='networkidle')
    n = page.eval_on_selector_all(SEL, "els=>els.length") or 1
    n = min(n, N_MAX)
    print(f"slides: {n} · viewport {W}x{H}")
    for i in range(n):
        page.wait_for_timeout(250)
        page.screenshot(path=str(OUT/f"slide_{i+1:02d}.png"))
        r = page.evaluate(CONTRAST_JS)
        seen=set(); cfails=[c for c in r['contrast'] if (c['text'],c['tag']) not in seen and not seen.add((c['text'],c['tag']))]
        rec={'slide':i+1,'contrast_fails':cfails,'skipped':r.get('skipped',[]),'overflow':r['overflow'],'broken_img':r['broken']}
        report.append(rec)
        total_c+=len(cfails); total_of+=int(r['overflow']['x'] or r['overflow']['y']); total_404+=len(r['broken'])
        flag=[]
        if cfails: flag.append(f"{len(cfails)} contrast")
        if r['overflow']['x'] or r['overflow']['y']: flag.append("OVERFLOW")
        if r['broken']: flag.append(f"{len(r['broken'])} broken-img")
        if r.get('skipped'): flag.append(f"{len(r['skipped'])} image-bg (ดูตา)")
        print(f"  slide {i+1:>2}: {' · '.join(flag) if flag else 'ok'}")
        page.keyboard.press(KEY)
    br.close()
if httpd: httpd.shutdown()

net404=sorted(set(u for u in net404 if not u.endswith('/favicon.ico')))
print(f"\n=== รวม: contrast {total_c} · overflow {total_of} สไลด์ · broken-img {total_404} · network 404: {len(net404)} ===")
for u in net404[:10]: print("  404:", u)
json.dump({'slides':report,'network_404':net404}, open('deck-shots/deck_report.json','w'), ensure_ascii=False, indent=1)
print(f"snapshot ทุกสไลด์ → deck-shots/slide_*.png · รายงาน → deck-shots/deck_report.json")
