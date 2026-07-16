# Deep Technical · Chapter 28 — Backup & Recovery

> ต่อจาก Ch27 · second brain = ความรู้สะสมทั้งชีวิต · เสียหาย = หายนะ · บทนี้: อะไรต้อง backup, กู้ยังไง
> หลักสำคัญ: **ground truth = markdown vault · index เป็น derived (สร้างใหม่ได้เสมอ)**

---

## 28.0 ชั้นข้อมูล — อะไรคือของจริง

```
markdown vault (ψ/)      ← GROUND TRUTH (Ch4 §4.0) — ของจริง แก้ตรงนี้
   │  embed (Ch2)
   ▼
SQLite/FTS5 + LanceDB     ← DERIVED — สร้างจาก vault ได้เสมอ
```
**หลักทอง**: ถ้า vault ปลอดภัย → index เสียก็ **rebuild ได้** · เลย backup แค่ vault เป็นพอ (index เป็น cache)

---

## 28.1 Index เป็น derived → rebuild ได้ (idempotent)

```
rebuild(vault):
  for doc in vault.markdown_files:
     text = parse(doc)
     vec  = embed(text)          # Ch2 (deterministic ถ้า embedder เดิม)
     index.upsert(id, vec, metadata)
     fts.insert(text)
```
- **idempotent**: รันซ้ำได้ผลเดิม (ถ้า embedder + vault เดิม) → recovery ปลอดภัย
- **caveat**: ถ้าเปลี่ยน embedder (Ollama→CF, Ch5) → เวกเตอร์ต่าง → ไม่ bit-identical แต่ semantic เท่าเดิม (drift, Ch6) → rebuild = re-embed ทั้งชุด
- นี่คือเหตุผล **markdown เป็น source of truth** ไม่ใช่ vector DB — vector DB พังไม่เสียความรู้ แค่ต้อง re-index

---

## 28.2 อะไรต้อง backup (priority)

```
1. vault markdown (ψ/)     ← MUST · ของจริง · text เล็ก, git-able
2. metadata DB (D1/SQLite) ← ควร (usage_count/heat, Ch13 — ไม่อยู่ใน markdown)
3. vector index (LanceDB)  ← optional (rebuild ได้ แต่ backup ประหยัดเวลา re-embed)
```
- vault = git repo → **git = backup + version + nothing-is-deleted** ในตัว (Ch principles)
- **heat/usage** (Ch13) ไม่อยู่ใน markdown → ต้อง backup DB แยก ไม่งั้นเสีย "ความจำการใช้"

---

## 28.3 Nothing-is-Deleted (Ch principle → recovery)

fleet principle #1 (จาก benchmark corpus จริง Ch20): "Nothing is deleted. Create new, do not delete. Git history is sacred."
```
- ไม่ลบ memory → soft-delete/archive (เหมือน HNSW tombstone Ch17 §17.5)
- git ไม่ rewrite history → กู้ทุก state ได้
- artifact-manager: snapshot ทุก deploy (archive/<name>/<timestamp>) — Ch session
```
→ recovery แข็งแรงเพราะ **ไม่มีอะไรหายจริง** — แค่ต้องหาให้เจอ (time-travel, Ch skill)

---

## 28.4 ⭐ Ferry Pattern (noah's craft) — ย้ายข้ามเครื่อง

Ch skill oracle-ferry: ย้าย oracle (vault + session history) ข้าม machine/path · เกี่ยวกับ recovery เพราะ:
```
ferry(oracle, src_host, dst_host):
  1. trace where data REALLY lives (path/encoding — org rename, /opt↔~/Code)
  2. verify path ก่อน trust
  3. cross (rsync/git)
  4. confirm consumer-side (index rebuild-able? /resume เห็น?)  ← "Run it, don't read it"
```
- **path encoding trap**: Claude session dir encode path → ย้าย path = session หาย (Ch oracle-resume-recovery: /opt↔~/Code, github.com doubling)
- **implication vector**: ย้ายเครื่อง → LanceDB path เปลี่ยน → rebuild index บนเครื่องใหม่จาก vault (§28.1) = ปลอดภัยกว่าขน binary index ข้าม arch

---

## 28.5 Disaster scenarios + กู้

| เหตุ | ผล | กู้ |
|---|---|---|
| vector DB corrupt | ค้น semantic พัง | rebuild จาก vault (§28.1) · FTS5 ยังทำงานระหว่างนั้น (Ch4) |
| Ollama/embedder ตาย | ไม่ embed ใหม่ได้ | FTS5 fallback (Ch4) + fix embedder |
| เครื่องพัง | ทั้งระบบ | git clone vault → rebuild index (§28.1-2) |
| เปลี่ยนโมเดล | เวกเตอร์เก่าใช้ไม่ได้ | re-embed ทั้งชุด + drift check (Ch6) |
| ลบผิด | — | git/archive กู้ (nothing-deleted §28.3) |

---

## 28.6 backup checklist

```
□ vault = git repo, push remote (backup + history)
□ metadata DB (heat/usage) snapshot เป็นระยะ
□ vector index: optional snapshot (ประหยัด re-embed) หรือ rebuild-on-demand
□ ทดสอบ rebuild จริง (rebuild จาก vault → recall เท่าเดิม? Ch20 benchmark)
□ ferry: verify path/consumer-side ก่อน trust (Run it, don't read it)
```

---

## สรุป Ch28
```
ground truth = markdown vault · index = derived (rebuild idempotent จาก vault)
backup priority: vault(git) > metadata-DB(heat) > index(optional, rebuildable)
nothing-is-deleted: soft-delete + git history sacred → กู้ทุก state
ferry: ย้ายข้ามเครื่อง → verify path (encoding trap) + rebuild index ปลายทาง
disaster: index พัง→rebuild+FTS floor · เครื่องพัง→git clone+rebuild
```
**ถัดไป Ch29:** query understanding — query expansion, HyDE, multi-query, re-writing, intent (ก่อนถึง embed)
---
*grounded: Ch4 (vault=truth/FTS floor), Ch2 (rebuild), Ch13 (heat backup), Ch6 (verify rebuild), Ch principles (nothing-deleted, benchmark corpus), Ch skill (oracle-ferry/resume-recovery) · /loop deep iter 2026-07-13*
