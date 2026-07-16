# 📖 หนังสือ: Second Brain ด้วย Vector Search — จากสมการถึงระบบจริง

> หนังสือ tool-anchored: ทุกบทมีโค้ดรันได้จริง (ChromaDB → bge-m3 → hybrid → ARRA production)
> แหล่งเนื้อหา: deep-technical/ 86 บท (~9,800 บรรทัด) + เดโมที่รันพิสูจน์แล้วใน book/demo/

---

## คำตอบ 3 คำถามตั้งต้น (research สรุป)

**1. ควรอิงกับ tools ไหม?** → **ควร** — ผู้เรียน (นักวิจัย/นักศึกษา ไม่ใช่ engineer) เรียนรู้จากของที่จับต้องได้
ทฤษฎีทุกบทต้องมีโค้ดรันตาม · หนังสือเดินคู่: แนวคิด (จาก deep-technical) + hands-on (ChromaDB)

**2. ใช้ ChromaDB ดีไหม?** → **ดีสำหรับสอน** ด้วยเหตุผลจริง:
- `pip install chromadb` เดียวจบ — ไม่มี server, ไม่มี Docker (embedded เหมือน SQLite)
- มี embedding ในตัว (เริ่มได้ทันที) + เสียบ embedder เองได้ (บทเรียน bge-m3)
- **ARRA เองก็เริ่มจาก ChromaDB** (TIMELINE.md: Dec 2025 "FTS5 + ChromaDB hybrid = breakthrough")
  → เรื่องเล่าสมบูรณ์: เรียนบน Chroma → เข้าใจว่าทำไม production ย้ายไป LanceDB
- ⚠️ จุดที่ต้องสอนคู่กัน: **default embedder อ่อนไทย** (พิสูจน์แล้ว demo1 คะแนนติดลบ/จับผิด
  → demo2 เสียบ bge-m3 แก้ได้) — นี่แหละคือบทเรียนที่มีค่าที่สุด

**3. full setup + demo?** → เสร็จแล้ว รันพิสูจน์แล้ว:
- `book/demo/setup.sh` — uv venv + chromadb 1.5.9 ✓
- `demo1_first_search.py` — second brain 20 บรรทัด (โชว์ทั้งความสำเร็จและจุดอ่อนไทย) ✓
- `demo2_thai_bge_m3.py` — เสียบ bge-m3 ผ่าน Ollama → ไทยถูกทั้ง 3 query ✓

---

## โครงหนังสือ (4 ภาค · 12 บท · demo ทุกบท)

### ภาค 1 — เห็นมันทำงาน (demo-first, ไม่มีสมการ)
| บท | เนื้อหา | demo | อิง deep-technical |
|----|---------|------|--------------------|
| 1 | Second brain แรกใน 20 บรรทัด | demo1 | Ch1 (แนวคิด) |
| 2 | ทำไมค้นไทยเพี้ยน → embedding model สำคัญกว่า DB | demo1 vs demo2 | Ch19, Ch53 |
| 3 | filter + metadata: ค้นแบบมีเงื่อนไข | demo3 (where filter) | Ch55, Ch61, Ch78 |

### ภาค 2 — เข้าใจว่าทำไม (สมการเข้าเมื่อผู้อ่านเห็นผลแล้ว)
| 4 | cosine similarity: สมการเดียวที่ต้องรู้ | คำนวณมือ + numpy | Ch1, Ch50 |
| 5 | embedding มาจากไหน (contrastive, bge-m3 M3) | เทียบ 3 embedder | Ch2, Ch7, Ch22 |
| 6 | ANN: ค้นล้านโน้ตในมิลลิวินาที (HNSW/IVF) | benchmark เวลาจริง | Ch3, Ch17, Ch44 |

### ภาค 3 — ระบบจริงทำอะไรมากกว่านั้น
| 7 | hybrid: vector อย่างเดียวไม่พอ (FTS+RRF) | FTS5+chroma+RRF | Ch4, Ch11, Ch34, Ch56, Ch60 |
| 8 | chunking + ingest ทั้ง vault | demo ingest โฟลเดอร์ .md | Ch12, Ch51, Ch52, Ch76 |
| 9 | RAG: ต่อ LLM ให้ตอบจากโน้ตเรา (cite ได้) | chroma + Claude/Ollama | Ch75, Ch26, Ch81 |

### ภาค 4 — สู่ production (เรื่องเล่า ARRA จริง)
| 10 | ทำไม ARRA ย้าย Chroma → LanceDB (trade-off จริง) | เทียบ benchmark.ts | Ch45-48, TIMELINE.md |
| 11 | วัดผล: recall@k, golden set, ทำไมห้ามเชื่อความรู้สึก | eval script | Ch6, Ch20, Ch39, Ch72 |
| 12 | privacy + local-first: ทำไม second brain ต้องอยู่เครื่องเรา | — | Ch14, Ch27, Ch62, Ch70 |

---

## หลักการเขียน
- ไทยธรรมชาติ (kien-thai) · โค้ดทุกชิ้นรันได้จริง+พิสูจน์แล้ว · สมการมาหลังเห็นผล
- ทุกบทจบด้วย "เชื่อมกับ ARRA production" (โค้ดจริง src/vector/*)
- ผู้อ่านเป้าหมาย: นักวิจัย/นักศึกษา (workshop 26 ก.ค.) — ไม่ assume พื้น ML
