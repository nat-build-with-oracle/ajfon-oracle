"""
แทรก matplotlib static viz cell เข้าทุก notebook — รูปจากข้อมูลจริงของแต่ละบท
วางก่อน cell สุดท้าย (แบบฝึก) · idempotent (ลบ viz เก่าที่มี marker ก่อนแทรกใหม่)
"""
import json, glob

MARK = "# @@VIZ@@"   # marker กัน insert ซ้ำ
FONT = (
"import matplotlib, matplotlib.pyplot as plt\n"
"from matplotlib import font_manager as _fm\n"
"_av={f.name for f in _fm.fontManager.ttflist}\n"
"for _f in ['Thonburi','Loma','Sarabun','Noto Sans Thai','TH Sarabun New']:\n"
"    if _f in _av: matplotlib.rcParams['font.family']=_f; break\n"
"matplotlib.rcParams['axes.unicode_minus']=False\n"
)

VIZ = {
"ch01_second_brain_20_lines.ipynb": ("## 📊 เห็นภาพ — query ไทยยังอ่อน (ปริศนาของบทนี้)\n",
FONT +
"qs=['นัดหมายกับใครบ้าง','อยากสอนเรื่อง AI ค้นหา','เครื่องดื่ม']\n"
"sc=[1-col_th.query(query_texts=[q],n_results=1)['distances'][0][0] for q in qs]\n"
"plt.figure(figsize=(7,3.4))\n"
"c=['#1baf7a' if s>0.3 else '#e34948' for s in sc]\n"
"plt.barh(qs[::-1],sc[::-1],color=c[::-1]); plt.axvline(0,color='#888',lw=1)\n"
"plt.title('บทที่ 1 — คะแนน top-1 ของ query ไทย (default embedder)')\n"
"plt.xlabel('cosine  ·  แดง = ต่ำ/ติดลบ = ปัญหา → บทที่ 2 แก้'); plt.tight_layout(); plt.show()\n"),

"ch02_fix_thai_bge_m3.ipynb": ("## 📊 เห็นภาพ — MiniLM vs bge-m3 (query ไทยชุดเดียวกัน)\n",
FONT + "import numpy as np\n"
"qs=list(QUERIES)\n"
"def _t1(c,q):\n    r=c.query(query_texts=[q],n_results=1); return 1-r['distances'][0][0]\n"
"mini=[_t1(col_default,q) for q in qs]; bge=[_t1(col_bge,q) for q in qs]\n"
"x=np.arange(len(qs)); w=0.35; plt.figure(figsize=(8,4))\n"
"plt.bar(x-w/2,mini,w,label='MiniLM (แถม)',color='#e34948')\n"
"plt.bar(x+w/2,bge,w,label='bge-m3',color='#1baf7a')\n"
"plt.axhline(0,color='#888',lw=.8); plt.xticks(x,qs,rotation=12,ha='right')\n"
"plt.ylabel('cosine top-1'); plt.legend(); plt.title('บทที่ 2 — bge-m3 ยกคะแนนขึ้นบวกทุก query')\n"
"plt.tight_layout(); plt.show()\n"),

"ch03_filter_metadata.ipynb": ("## 📊 เห็นภาพ — filter ตัดอะไรออก\n",
FONT + "Q='การสอนเรื่องค้นหาด้วยความหมาย'\n"
"res=col.query(query_texts=[Q],n_results=6)\n"
"docs=res['documents'][0]; metas=res['metadatas'][0]; sc=[1-d for d in res['distances'][0]]\n"
"passed=[m['folder']=='teaching' and m['year']==2026 and not m['draft'] for m in metas]\n"
"c=['#1baf7a' if p else '#c9c7bf' for p in passed]; lb=[d[:20] for d in docs]\n"
"plt.figure(figsize=(8,4)); plt.barh(lb[::-1],sc[::-1],color=c[::-1])\n"
"plt.title('บทที่ 3 — เขียว = ผ่าน filter (teaching ∧ 2026 ∧ ¬draft)')\n"
"plt.xlabel('cosine'); plt.tight_layout(); plt.show()\n"),

"ch04_cosine_by_hand.ipynb": ("## 📊 เห็นภาพ — เวกเตอร์ 2 มิติ (static ของ playground)\n",
FONT + "cat=[0.9,0.1]; kitten=[0.85,0.15]; car=[0.1,0.95]\n"
"plt.figure(figsize=(5,5)); ax=plt.gca()\n"
"for v,nm,cl in [(cat,'แมว','#2a78d6'),(kitten,'ลูกแมว','#1baf7a'),(car,'รถยนต์','#e34948')]:\n"
"    ax.annotate('',xy=v,xytext=(0,0),arrowprops=dict(arrowstyle='-|>',color=cl,lw=2.5))\n"
"    ax.text(v[0]*1.03,v[1]*1.03,nm,color=cl,fontsize=13,fontweight='bold')\n"
"ax.set_xlim(0,1.1); ax.set_ylim(0,1.1); ax.set_aspect('equal'); plt.grid(alpha=.3)\n"
"ax.set_xlabel('แกน: ความเป็นแมว'); ax.set_ylabel('แกน: ความเป็นรถ')\n"
"ax.set_title(f'บทที่ 4 — cos(แมว,ลูกแมว)={cosine(cat,kitten):.2f}  ·  cos(แมว,รถ)={cosine(cat,car):.2f}')\n"
"plt.tight_layout(); plt.show()\n"),

"ch07_hybrid_search.ipynb": ("## 📊 เห็นภาพ — RRF fused score (Q: PR #2740)\n",
FONT + "q='PR #2740'; vr=vector_rank(q); br,_=bm25_rank(q); fused=rrf([vr,br])[:5]\n"
"lb=[DOCS[i][:22] for i,_ in fused]; sc=[s for _,s in fused]\n"
"plt.figure(figsize=(8,4)); plt.barh(lb[::-1],sc[::-1],color='#2a78d6')\n"
"plt.title(f'บทที่ 7 — RRF รวม vector+BM25 (Q: {q})'); plt.xlabel('RRF fused score')\n"
"plt.tight_layout(); plt.show()\n"),

"ch08_ingest_vault.ipynb": ("## 📊 เห็นภาพ — idempotent ingest (รันซ้ำไม่ embed ซ้ำ)\n",
FONT + "import numpy as np\n"
"rounds=['รอบ 1','รอบ 2 (ซ้ำ)','หลังแก้ไฟล์']\n"
"add=[added,added2,added3]; skip=[skipped,skipped2,skipped3]\n"
"x=np.arange(3); w=0.4; plt.figure(figsize=(7,4))\n"
"plt.bar(x-w/2,add,w,label='embed ใหม่',color='#1baf7a')\n"
"plt.bar(x+w/2,skip,w,label='ข้าม (idempotent)',color='#c9c7bf')\n"
"plt.xticks(x,rounds); plt.ylabel('จำนวน chunk'); plt.legend()\n"
"plt.title('บทที่ 8 — รันซ้ำ→เพิ่ม 0 · แก้ไฟล์→เพิ่มเฉพาะที่เปลี่ยน'); plt.tight_layout(); plt.show()\n"),

"ch09_rag_cite.ipynb": ("## 📊 เห็นภาพ — threshold คัดของเกี่ยว vs abstain\n",
FONT + "fig,axes=plt.subplots(1,2,figsize=(10,3.6),sharey=True)\n"
"for ax,q in zip(axes,['workshop วันไหน','ราคาหุ้นวันนี้']):\n"
"    res=col.query(query_texts=[q],n_results=4); s=[1-d for d in res['distances'][0]]\n"
"    c=['#1baf7a' if x>=THRESHOLD else '#e34948' for x in s]\n"
"    ax.bar(range(len(s)),s,color=c); ax.axhline(THRESHOLD,ls='--',color='#888')\n"
"    ax.set_title(q); ax.set_xlabel('อันดับผล')\n"
"axes[0].set_ylabel('cosine'); fig.suptitle('บทที่ 9 — เขียว=ผ่าน threshold(ตอบ) · แดง=abstain (ไม่พบ)')\n"
"plt.tight_layout(); plt.show()\n"),

"ch10_chroma_to_lancedb.ipynb": ("## 📊 เห็นภาพ — Chroma vs LanceDB (เวลา, 200 chunks)\n",
FONT + "import numpy as np\n"
"cats=['ingest (ms)','query (ms)']; chroma=[chroma_ingest*1000,chroma_q]; lance=[lance_ingest*1000,lance_q]\n"
"x=np.arange(2); w=0.35; plt.figure(figsize=(7,4))\n"
"b1=plt.bar(x-w/2,chroma,w,label='ChromaDB',color='#eda100')\n"
"b2=plt.bar(x+w/2,lance,w,label='LanceDB',color='#2a78d6')\n"
"plt.bar_label(b1,fmt='%.0f'); plt.bar_label(b2,fmt='%.0f')\n"
"plt.xticks(x,cats); plt.ylabel('ms'); plt.legend()\n"
"plt.title('บทที่ 10 — top-1 ตรงกัน · เวลาต่างกันไม่มีนัยที่ scale นี้'); plt.tight_layout(); plt.show()\n"),

"ch11_golden_set_eval.ipynb": ("## 📊 เห็นภาพ — วัดผลจริง (bge-m3 vs MiniLM)\n",
FONT + "import numpy as np\n"
"metrics=['Recall@3','MRR']; mini=[r_mini,mrr_mini]; bge=[r_bge,mrr_bge]\n"
"x=np.arange(2); w=0.35; plt.figure(figsize=(7,4))\n"
"b1=plt.bar(x-w/2,mini,w,label='MiniLM',color='#e34948')\n"
"b2=plt.bar(x+w/2,bge,w,label='bge-m3',color='#1baf7a')\n"
"plt.bar_label(b1,fmt='%.2f'); plt.bar_label(b2,fmt='%.2f')\n"
"plt.xticks(x,metrics); plt.ylim(0,1.15); plt.legend()\n"
"plt.title('บทที่ 11 — golden set ไทย: bge-m3 ชนะชัดด้วยตัวเลข'); plt.tight_layout(); plt.show()\n"),

"ch12_privacy_local_first.ipynb": ("## 📊 เห็นภาพ — ต้นทุน local vs cloud (1 ปี)\n",
FONT + "labels=['cloud\\n(embed+query/ปี)','local\\n(Ollama)']\n"
"vals=[embed_cost+query_cost, 0.0]\n"
"plt.figure(figsize=(6,3.6)); b=plt.bar(labels,vals,color=['#eda100','#1baf7a'])\n"
"plt.bar_label(b,fmt='$%.2f'); plt.ylabel('USD/ปี')\n"
"plt.title('บทที่ 12 — เงินใกล้กัน · ประเด็นจริงคือ privacy + ownership'); plt.tight_layout(); plt.show()\n"),

"ch13_lancedb_second_brain.ipynb": ("## 📊 เห็นภาพ — LanceDB คะแนน top-1 (query ไทย)\n",
FONT + "qs=['นัดหมายกับใครบ้าง','อยากสอนเรื่อง AI ค้นหา','เครื่องดื่ม']; sc=[]\n"
"for q in qs:\n    r=tbl.search(embed_texts([q])[0].tolist()).distance_type('cosine').limit(1).to_pandas()\n    sc.append(1-r.iloc[0]['_distance'])\n"
"plt.figure(figsize=(7,3.4)); plt.barh(qs[::-1],sc[::-1],color='#2a78d6')\n"
"plt.title('บทที่ 13 — LanceDB + bge-m3 (query ไทยทำงานดี)'); plt.xlabel('cosine')\n"
"plt.tight_layout(); plt.show()\n"),

"ch14_lancedb_hybrid_native.ipynb": ("## 📊 เห็นภาพ — LanceDB hybrid อันดับผล (Q: PR #2740)\n",
FONT + "q='PR #2740'; r=hybrid(q,k=5)\n"
"lb=[t[:24] for t in r['text']]; ranks=list(range(len(lb),0,-1))\n"
"plt.figure(figsize=(8,4)); plt.barh(lb[::-1],ranks[::-1],color='#1baf7a')\n"
"plt.title(f'บทที่ 14 — hybrid (FTS+vector+RRF) จัดอันดับ (Q: {q})')\n"
"plt.xlabel('อันดับ (ยาว = ดีกว่า)'); plt.tight_layout(); plt.show()\n"),

"ch15_lancedb_time_travel.ipynb": ("## 📊 เห็นภาพ — row count แต่ละ version (ลบ→restore)\n",
FONT + "tbl.checkout_latest(); vers=tbl.list_versions(); counts=[]\n"
"for v in vers:\n    tbl.checkout(v['version']); counts.append(tbl.count_rows())\n"
"tbl.checkout_latest()\n"
"plt.figure(figsize=(7,3.6))\n"
"plt.step(range(1,len(counts)+1),counts,where='mid',color='#2a78d6',lw=2.5,marker='o',markersize=8)\n"
"plt.xticks(range(1,len(counts)+1),[f\"v{v['version']}\" for v in vers])\n"
"plt.ylabel('จำนวน row'); plt.grid(alpha=.3)\n"
"plt.title('บทที่ 15 — time-travel: เพิ่ม→ลบ→restore (row กลับมา)'); plt.tight_layout(); plt.show()\n"),
}

def cell_md(s): return {"cell_type":"markdown","metadata":{},"source":[s]}
def cell_code(s): return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],
                          "source":[MARK+"\n"]+[l+"\n" for l in s.rstrip("\n").split("\n")]}

n=0
for fn,(md,code) in VIZ.items():
    path=f"notebooks/{fn}"
    nb=json.load(open(path))
    # ลบ viz เก่า (idempotent): เอา code cell ที่มี MARK + markdown ก่อนหน้าออก
    cells=[]
    skip_next_md=False
    old=nb['cells']
    keep=[]
    i=0
    while i<len(old):
        c=old[i]
        if c['cell_type']=='code' and any(MARK in l for l in c.get('source',[])):
            # ลบ markdown '📊 เห็นภาพ' ที่อยู่ก่อนหน้า ถ้ามี
            if keep and keep[-1]['cell_type']=='markdown' and '📊 เห็นภาพ' in ''.join(keep[-1]['source']):
                keep.pop()
            i+=1; continue
        keep.append(c); i+=1
    # แทรกก่อน cell สุดท้าย (แบบฝึก)
    ins=[cell_md(md), cell_code(code)]
    keep[-1:-1]=ins
    nb['cells']=keep
    json.dump(nb,open(path,'w'),ensure_ascii=False,indent=1); json.load(open(path))
    n+=1
print(f"แทรก viz cell → {n} notebooks ✓")
