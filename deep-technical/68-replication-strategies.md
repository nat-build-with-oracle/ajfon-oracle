# Deep Technical · Chapter 68 — Replication Strategies

> ต่อจาก Ch67 · replicate ยังไงให้ทั้งเร็วและถูก · บทนี้: leader-follower vs multi-leader vs leaderless, read-repair, conflict resolution (LWW/CRDT)

---

## 68.0 3 topology หลัก

```
single-leader:  1 leader รับ write → replicate ไป follower (read-only)
multi-leader:   หลาย leader รับ write (คนละ region) → sync กันเอง
leaderless:     ทุก node รับ write/read (quorum, Dynamo Ch67)
```
- trade: single = ง่าย/consistent แต่ leader คอขวด · multi/leaderless = scale write แต่ conflict

---

## 68.1 ⭐ single-leader (พบบ่อยสุด)

```
write → leader → append log (WAL Ch64) → replicate log ไป follower → follower apply
read → leader (strong) หรือ follower (eventual, อาจ lag)
```
- **replication lag**: follower ตาม leader ไม่ทัน → read follower เห็นของเก่า (eventual Ch65)
- **read-your-writes**: user เขียนแล้วอ่านทันที → route ไป leader (ไม่ใช่ follower ที่ lag)
- Raft (Ch66) = single-leader + consensus (leader election + quorum commit)

---

## 68.2 multi-leader — write หลายที่

```
region A leader + region B leader → แต่ละ region write local (เร็ว) → async sync ข้าม region
ปัญหา: doc เดียวกันแก้ที่ A และ B พร้อมกัน → conflict (2 version)
```
- เหมาะ geo-distributed (Ch69): write local latency ต่ำ · แต่ต้อง resolve conflict (§68.4)

---

## 68.3 leaderless — quorum read/write

```
write → ส่งทุก replica → รอ W ack (Ch67 tunable)
read → ถามหลาย replica → รอ R response → เอา version ล่าสุด
W + R > N → strong · read เจอ replica ที่มี write ล่าสุดแน่ (overlap)
```
- **read-repair**: read เจอ replica ตอบ version ต่างกัน → update ตัวที่เก่าให้ตรง (ซ่อมตอนอ่าน)
- **anti-entropy**: background เทียบ replica → sync ส่วนต่าง (ซ่อมเชิงรุก, Merkle tree เทียบเร็ว)

---

## 68.4 ⭐ conflict resolution — 2 version ทำไง

multi-leader/leaderless เจอ conflict → ต้องเลือก/รวม:
```
LWW (Last-Write-Wins): เอา version ที่ timestamp ใหม่สุด
  ง่าย แต่ ⚠️ เสียข้อมูล (write เก่าหาย) + ต้อง clock sync (Ch68 §68.5)
CRDT (Conflict-free Replicated Data Type): merge ได้โดยไม่เสียข้อมูล
  ออกแบบ data type ให้ merge deterministic (เช่น set: union, counter: sum)
  → ทุก replica merge แล้วได้ผลเดียว โดยไม่ต้อง coordinate
version vector: track causality (ใครเกิดก่อน/หลัง/พร้อมกัน) → รู้ว่า conflict จริงไหม
```
- vector DB: doc เป็น immutable (Ch45 tombstone+append) → conflict น้อย (ไม่แก้ในที่) → LWW บน metadata พอ

---

## 68.5 ⚠️ clock & causality

```
LWW พึ่ง timestamp → clock ต่าง node ไม่ตรง (clock skew) → LWW เลือกผิด
แก้: logical clock (Lamport) / hybrid logical clock → order เชิง causality ไม่พึ่ง wall-clock เป๊ะ
```
- distributed timestamp ยาก (ไม่มี global clock) → นี่คือเหตุผล CRDT/version-vector ดีกว่า LWW ในระบบซีเรียส

---

## 68.6 replication ของ index (เฉพาะ vector)

```
replicate อะไร?
  option A: replicate raw vectors → แต่ละ replica build index เอง (CPU เยอะ แต่ flexible)
  option B: replicate index ที่ build แล้ว (byte-level) → เร็ว แต่ผูก format/version
```
- immutable fragment (Ch45/64) → replicate fragment (built) → replica แค่ copy ไฟล์ (option B, เร็ว)
- rebuild (Ch46) ทำที่ leader → ship fragment ใหม่ → follower swap (blue-green Ch46 ข้าม node)

---

## 68.7 เชื่อม ARRA

```
ARRA local single-node → ไม่มี replication (1 เครื่อง, Ch65/67) → ไม่มี conflict
Vectorize (Ch14): CF ทำ replication ข้าม region ให้ (น่าจะ leaderless/multi-leader edge)
D1 (Ch14): single-leader (SQLite primary) + read replica ข้าม region (eventual)
immutable fragment (Ch45): conflict น้อย → replicate ง่าย (copy built fragment §68.6)
→ personal ไม่แตะเรื่องนี้ · แต่เข้าใจเมื่อ scale/edge (managed จัดการให้)
```

---

## สรุป Ch68
```
3 topology: single-leader (ง่าย/consistent, leader คอขวด) · multi-leader (geo write local, conflict) · leaderless (quorum, Dynamo)
single-leader: replicate WAL log (Ch64) · lag→follower เก่า · read-your-writes→route leader · Raft=single+consensus
leaderless: W+R>N strong · read-repair (ซ่อมตอนอ่าน) + anti-entropy (Merkle background)
⭐ conflict: LWW (ง่าย/เสียข้อมูล/พึ่ง clock) vs CRDT (merge ไม่เสีย, deterministic) vs version-vector (causality)
⚠️ clock skew → LWW ผิด → logical/hybrid clock (Lamport)
vector: immutable fragment (Ch45) → conflict น้อย, replicate built fragment (copy ไฟล์)
ARRA: single-node ไม่มี replication · Vectorize/D1 managed (edge) จัดการให้
```
**ถัดไป Ch69:** geo-distributed & edge retrieval — ค้นใกล้ user (latency), data locality/residency, Cloudflare edge (Ch5/14) ลึก, CDN-style vector cache
---
*grounded: replication topologies · read-repair/anti-entropy (Dynamo) · CRDT/LWW/version-vector · Lamport clock · immutable fragment (Ch45) · เชื่อม Ch14/45/46/64/65/66/67 · /loop deep iter 2026-07-16*
