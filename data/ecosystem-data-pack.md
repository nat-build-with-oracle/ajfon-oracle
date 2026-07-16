# ARRA Oracle Ecosystem — Data Pack (workshop foundation)

> วัตถุดิบสำหรับ workshop "ARRA Oracle Second Brain for Research" (26 ก.ค. 2026)
> รวบรวมโดย workflow `wf_ab4124a8-b40` — 7 Sonnet agents (internal repo + web deep-research)
> เก็บ 2026-07-09 · session 20cf7c44 · **raw material ไม่ใช่สไลด์**
> สถานะ: ✅ ครบแล้ว — 4/7 agent แรก + 2 re-run (agentic-patterns C2 + researcher-workflow C3) สำเร็จ · backend กู้ผ่าน oracle-studio

---

## A. สิ่งที่ระบบเราทำได้จริง (demo-able TODAY, FTS-first)

**Backend API** (`localhost:47778`):
- `/api/search` (modes: **fts** / vector / hybrid) — Ollama เลิกแล้ว → **fts = mode เดียวที่เชื่อถือได้บนเวที**
- `/api/list` (browse) · `/api/stats` · `/api/reflect` (random wisdom) · `/api/learn` (POST — ingest ทีละ entry ไม่ bulk) · `/api/graph` + `/api/map` (knowledge graph) · `/health` (gate 3s timeout)
- ⚠️ **ไม่มี chat/ask-LLM endpoint** — Studio = search+browse+manual-learn ไม่ใช่ chatbot
- source: `oracle-studio/src/api/oracle.ts`, `BackendGate.tsx`

**Studio UI** (React/Vite, `bunx oracle-studio`): thin client, ไม่มี data local, proxy ทุกอย่างไป :47778
- Search page (กล่องเดียว + quick-try chips) · **Playground** (รัน fts/vector/hybrid ขนานเทียบกัน — เดโมดี แต่ **vector จะโชว์ว่าง** เพราะ Ollama เลิก) · Quick-Learn "+" modal · 23 routes

**Skills**: 74 ติดตั้ง local · **11 ตัว demo-worthy** สำหรับ non-tech researcher:
`about-oracle` (opener) · `awaken` (identity ritual) · `trace`/`seek` (find-anything = จุด magic) · `recap`/`rrr`/`forward` (session continuity arc) · `oracle-prism` (multi-perspective) · `oracle-deep-research` (cited web research = wow สุด) · `kien-thai` (เขียนไทยธรรมชาติ) · `oracle-cheatsheet` (ของแจกปิดท้าย)
- profiles จริงใน `arra-oracle-skills-cli/src/profiles.ts`: **minimal=6, standard=12** (full/lab คำนวณ dynamic ไม่ใช่ 25/28 ตายตัว) · marketplace.json = 29 skills
- 💡 talking point: 74 raw → 11 curated = "AI สร้าง command เองได้จน sprawl" → วินัยการ curate

## B. Primers ที่มี + ช่องว่าง

- **ai-library-th.pages.dev**: ไทยเรียบง่าย vision-level — *"AI ที่มีตัวตน มีความจำ และโตไปกับคุณ"* (ใกล้ "second brain" สุด) · hero: *"เขียนจากของจริง...มีแผล มีบทเรียน"* · arc: รู้จัก Oracle → มี Oracle ตัวแรก → ทีม → ข้ามเครื่อง · มี 3 เล่ม (Oracle / Discord Assistant / Vol.3 coming) เขียนโดย "regulus" (Oracle instance)
- **oracle101.vercel.app**: คู่มือเทคนิค **12 บท 3 ส่วน** (Foundation: intro/what-is/architecture/install · Runtime: Brain/Skills-Maw-Plugin/maw commands/advanced · Team&Ops: orchestration/workflow/CMMI/autonomous/troubleshooting) — สำหรับ operator ไม่ใช่ researcher มือใหม่ · ไม่มี screenshot/demo
- **ช่องว่าง**: ทั้งสองไม่พูดคำว่า "agentic AI" เป็น category และไม่มี live demo → **workshop ต้องเติม**: (1) สะพาน category (Oracle = agentic AI ตัวหนึ่ง) (2) live walkthrough จริง (3) on-ramp เฉพาะงานวิจัย

## C. External landscape (web)

**Memory architectures** (2026 consensus = hybrid, ไม่มีผู้ชนะเดี่ยว):
- files/markdown (โปร่งใส git-auditable zero-infra) vs vector DB (semantic, scale >100k docs) vs knowledge graph (temporal/multi-hop แต่ latency ~2.3x)

**Positioning vs คู่แข่ง:**
- **Notion AI** (Custom Agents, cloud-only, 21k+ agents สร้างแล้ว) · **NotebookLM** (50/300 source limit, เก็บบน Google cloud) — ทั้งคู่ data ออกนอกเครื่อง
- **Obsidian + Smart Connections** = peer ที่ privacy-first ใกล้สุด (local embeddings via Ollama)
- **ARRA Oracle** (markdown source-of-truth + FTS5/vector hybrid) = sweet spot "ไฟล์ under 10k docs, hybrid ตรงกลาง"

**Benchmark (ตัวเลขขัดกันระหว่าง vendor — อย่า cite เดี่ยว):**
- mem0 อ้างเอง 66.9% (2024) → 92.5% (2026) · independent: **Letta plain-filesystem 74%** (บางแหล่ง 83%) ชนะ mem0-graph 68.4-68.5% บน LoCoMo
- Zep/Graphiti 63.8% vs mem0 49.0% (LongMemEval, graph ชนะ temporal) แต่ GraphRAG แพ้ vanilla RAG 13.4% บน single-hop
- full-context baseline 72.9% แต่ 9.87s latency + ~26k tokens vs memory-layer ~1.8-6.9k tokens
- **files/agents ชนะเมื่อ <10,000 docs & <1-2GB** · vector DB ชนะเมื่อ >100k docs
- **60,000+ projects ใช้ markdown AGENTS.md** zero vector infra (Claude Code, Cursor, Copilot)
- LLM instruction-following เพดาน ~150-200 instructions → argument ให้ memory file เล็ก/curated (~30 items)
- cost: mem0 ตัวอย่างเอง $90/mo (dump) vs $1.80/mo (selective) · Obsidian+Ollama local อ้างแทน subscription $500+/ปี

### C2 · Agentic AI patterns — สำหรับสอน generic (re-run, cited)

**นิยามที่สอนได้ (2026)**: agentic AI = ระบบที่รับเป้าหมาย → **วางแผนหลายขั้นเอง → เรียก tool → ปรับตามผลกลางทาง** (มี human steering บ้าง ไม่ใช่ศูนย์) ≠ chatbot ตอบทีละ turn
- 🎯 **ประโยคทองสำหรับกลุ่มวิชาการ**: *"มันคือผู้ช่วยวิจัยระดับ junior ที่คุณยังต้อง supervise ไม่ใช่เพื่อนร่วมงานอิสระ"*
- reality: Gartner คาด 40% enterprise apps มี agent สิ้นปี 2026 · แต่ Forrester: "chasing, few catching" — ส่วนใหญ่ยังเป็น chatbot แปะ tool

**2 building blocks**: (1) **tool-use/function-calling** (โมเดลเรียก search/code/DB กลางการคิด) (2) **orchestrator + workers** (lead วางแผน → แตก subagent ขนาน แต่ละตัว context สด → รวมผล) — Anthropic ใช้ pattern นี้ทำ Research **ชนะ single Opus 90.2%** · map ตรงกับ "PI แตกงานให้ postdoc แล้วรวม" = สื่อกับอาจารย์ได้ทันที

**3 กลไกความจำ (อย่าปนกัน)**: RAG (ดึง chunk จาก index ตอน query = บรรณารักษ์) vs long-context (ยัดทั้ง corpus เข้า prompt ทุกครั้ง = อ่านทั้งห้องสมุดใหม่, แพง + lost-in-middle) vs **persistent memory** (จำข้าม session = สมุดโน้ตที่จำข้ามสัปดาห์) — production 2026 = RAG + memory ผสม

**5 frameworks อ้างได้**: LangGraph (graph orchestration, leader งาน stateful) · CrewAI (role-based, prototype เร็วสุด) · AutoGen→AG2/MS Agent Framework (event-driven) · Claude Code/Agent SDK (terminal-native, MCP) · OpenAI Responses API (แทน Assistants ที่ sunset 26 ส.ค. 2026) · **MCP = connective tissue ของทั้งหมด**

**⚖️ Reality check (สำคัญ — สอนอย่างซื่อสัตย์)**:
- **~70% ของงาน "multi-agent" จริงๆ single agent ถูก/เร็ว/เชื่อถือกว่า** — คนมักหยิบ multi-agent ก่อนจำเป็น
- reliability compound: 85%/step × 10 steps = **สำเร็จแค่ 19.7%** · cost **10-15x tokens** · latency 3 agent = 6-14s (พัง real-time)
- multi-agent คุ้มเมื่อ **แตกเป็น 3+ strand อิสระขนานกันจริง** (เช่น breadth-first research) — งานพึ่งพากันแน่น (เช่น เขียนโค้ด) single agent ชนะ

**3 analogy ที่ลงกับ non-tech researcher**:
1. **PI-and-lab**: orchestrator = PI วางแผน+แตกงานให้ RA แล้ว integrate+fact-check เอง (ไม่เคยยกความรับผิดชอบสุดท้าย)
2. **RAG=บรรณารักษ์ · long-context=อ่านห้องสมุดใหม่ทุกคำถาม · memory=สมุดโน้ตที่อยู่ข้ามสัปดาห์** (3 อย่างต่างกัน ไม่ใช่ทางเลือกแข่งกัน)
3. **"grad student ที่เร็วมากแต่ literal"** — สร้าง citation ปลอมหน้าตาน่าเชื่อ, ทำตามสั่งเป๊ะเกิน, ต้อง review เหมือน draft ปีหนึ่ง → mental model ที่ดีสุดคือ "เพื่อนร่วมงาน junior ที่ต้องคุม" ไม่ใช่ "ผู้เชี่ยวชาญอิสระ"

*(sources: Anthropic 2026 State of AI Agents + multi-agent-research-system · Forrester · Atlan RAG-vs-memory · Kalvium/Cloud AI/TDS reliability+cost · Alicelabs frameworks)*

### C3 · นักวิจัยใช้ AI จริงยังไง (re-run, cited) — grounding "for Research"

**Pipeline จริง + tool ที่ใช้แต่ละขั้น (2026):**
- **ค้น paper**: Elicit (systematic review, screen หลายร้อย paper) · Consensus ("Consensus Meter" ตอบ yes/no จากหลักฐาน) · SciSpace (explore + Deep Review) · Semantic Scholar (citation graph, ฟรี)
- **อ่าน/จดโน้ต**: **NotebookLM** = hub (ตอบจากเอกสารที่อัปเท่านั้น = ไม่ hallucinate นอก source, 5M+ users) · Zotero + plugin (PapersGPT/Aria/Beaver — แต่ทำได้แค่ per-paper)
- **synthesis/หา gap**: AnswerThis, Anara, Research Agent (สแกนหาช่องว่าง/ความขัดแย้ง)
- **ตั้ง RQ**: tool แนว human-AI collaboration (Socratic partner ไม่ใช่ oracle)
- **เขียน**: pattern "speed-then-quality" — ChatGPT ร่าง outline → Claude ขัด (fabrication ต่ำกว่า, ฟอร์แมตวิชาการดีกว่า)
- **citation**: Zotero + AI auto-tag แต่ **verify สุดท้ายยัง manual**

**AI ช่วยจริงตรงไหน**: information overload · "อ่านเมื่อ 6 เดือนก่อน ลืมหมด" · drudgery การ extract ข้อมูลข้าม paper เป็นตาราง

**🔴 ตรงไหนทำร้ายงานวิจัย (กระสุนเด็ดสุด)**:
- **วิกฤต citation ปลอม**: audit 2.5M paper — อัตรา reference ปลอม **1-in-2,828 (2023) → 1-in-277 (ต้นปี 2026)** · แม้แต่ NeurIPS 2025 (peer-reviewed) มี ~100 citation ที่ hallucinate ใน 53 paper
- → guidance ชัด: **cross-verify ทุก ref ใน Scopus/PubMed/WoS · อย่าเชื่อ LLM เป็นแหล่งอ้างอิง**

**💎 ทำไม "second brain ที่จำข้าม session + cite กลับโน้ตตัวเอง" ชนะสำหรับนักวิจัย**:
ทุก tool ข้างบน **ลืม "คุณ" ข้าม session** — Elicit ลืม screening decision เดิม · NotebookLM siloed ต่อ project · ChatGPT/Claude ไม่พกโน้ตสะสมต่อ → ระบบที่ **persist โน้ตคุณเอง + ดึงกลับ semantic เดือนต่อมา + cite กลับ annotation ตัวเอง** แก้ "ลืมที่อ่าน" + "ต้อง derive gap ใหม่จากศูนย์" ตรงจุด · **และ grounded ในโน้ตที่ verify แล้ว ไม่ใช่ web crawl → ลด hallucination เชิงโครงสร้าง** (หลักการเดียวกับที่ NotebookLM ขายเป็นจุดต่าง)

*(sources: Elicit/Consensus/SciSpace comparisons · NotebookLM 2026 · Retraction Watch + Forbes + T&F เรื่อง fabricated citations · CTAIO/Buildin second-brain)*

## D. Positioning — จุดขายที่ยืนได้ (grounded)

1. **Data ไม่ออกนอกเครื่อง 100%** — ต่างจาก Notion/NotebookLM (cloud) · grep/git-auditable
2. **Hybrid FTS+vector = production consensus ปี 2026 จริง** ไม่ใช่ทางเลือก fringe
3. **Session-continuity เดโมได้วันนี้จริง**: recap→rrr→forward = "AI ที่จำคุณได้" พิสูจน์สดผ่าน FTS
4. **kien-thai = fit ภาษาไทยวิชาการจริง** ไม่ใช่ tool อังกฤษ retrofit
5. **วินัย curate (74→11)** = teachable pattern เรื่องกลัว AI sprawl

## E. Gaps / ความเสี่ยง / ต้องเช็คก่อน 26 ก.ค.

- ⚠️ **Vector ใช้ไม่ได้ตอนนี้** (Ollama เลิก) → **ต้องเช็คว่า Playground page ไม่โชว์ vector column ว่าง/พังบนเวที**
- ⚠️ benchmark mem0/Letta/Zep vendor-contested → **ห้าม cite % เดี่ยวไม่มี caveat**
- ⚠️ "25/28 profile" ไม่ตรง repo (minimal=6, standard=12 ยืนยัน) → verify เลขก่อนขึ้นสไลด์
- ⚠️ ต้อง **test `/api/learn` สด 1 POST** ก่อนโชว์ "ingest" บนเวที
- ⚠️ symlink skills (admin-manual, fleet-radar, tile) = cross-repo hack → ตัดออกจากสไลด์ "generic skill"
- ⏳ **ยังขาด** (re-run อยู่): agentic-AI patterns สำหรับสอน generic + researcher AI workflow เฉพาะสาย

---
*Source: workflow wf_ab4124a8-b40 · repos ใน Soul-Brews-Studio + web deep-research · ต่อยอดเป็นสไลด์เมื่อ Nat สั่ง*
