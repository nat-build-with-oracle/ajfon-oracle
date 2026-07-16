# Deep Technical · Chapter 67 — CAP Theorem for Vector Search

> ต่อจาก Ch66 · distribute แล้วเจอกฎเหล็ก: เลือกได้แค่ 2 ใน 3 ตอน partition · บทนี้: CAP, PACELC, ทำไม vector DB เลือกต่างกัน

---

## 67.0 CAP — เลือก 2 ใน 3

```
C (Consistency):        ทุก node เห็นข้อมูลเดียวกัน ณ เวลาเดียว (Ch65 strong)
A (Availability):       ทุก request ได้ response (ไม่ error/timeout)
P (Partition tolerance): ระบบทำงานต่อได้แม้ network ขาด (node คุยกันไม่ได้)
```
- **ทฤษฎี**: เมื่อเกิด partition (P เกิดจริงในระบบ distributed) → เลือกได้แค่ **C หรือ A** ไม่ได้ทั้งคู่

---

## 67.1 ⭐ ทำไมเลือกทั้ง C+A ไม่ได้ตอน partition

```
network ขาด: node1 | node2 (คุยกันไม่ได้)
write มาที่ node1:
  ถ้าเลือก C: node1 ต้องรอ sync node2 → sync ไม่ได้ (ขาด) → ปฏิเสธ write (เสีย A)
  ถ้าเลือก A: node1 รับ write เลย → node2 ไม่รู้ → 2 node ต่างกัน (เสีย C)
→ ต้องเลือก: CP (consistent, ปฏิเสธตอนขาด) หรือ AP (available, ยอม inconsistent ชั่วคราว)
```
- P หลีกเลี่ยงไม่ได้ (network ขาดเกิดจริง) → สงครามจริงคือ **C vs A**

---

## 67.2 CP vs AP สำหรับ vector search

```
CP (เลือก consistency):
  quorum write (Raft Ch66) → partition แยก minority → minority ปฏิเสธ (unavailable)
  เหมาะ: ข้อมูลต้องตรงเป๊ะ (financial, ไม่ยอมเห็นของเก่า)

AP (เลือก availability):
  ทุก replica รับ query/write → partition ก็ตอบได้ → eventual consistency (Ch65)
  เหมาะ: retrieval! ค้นเจอ "ของเกือบล่าสุด" ยอมรับได้ (ไม่ต้องเป๊ะวินาที)
```
- **vector search มักเอนไป AP**: recall เห็น doc ช้าไปแป๊บ ยอมได้ (ดีกว่าค้นไม่ได้เลย) → availability สำคัญกว่า strict consistency

---

## 67.3 ⭐ PACELC — ส่วนขยายที่จริงกว่า

CAP พูดแค่ตอน partition · **PACELC** พูดตอนปกติด้วย:
```
if Partition: เลือก A หรือ C   (เหมือน CAP)
Else (ปกติ):  เลือก L หรือ C   (Latency vs Consistency)
```
- **ประเด็นสำคัญ**: แม้ไม่มี partition ก็ยังแลก — strong consistency = รอ sync = latency สูง
- vector search: มัก **PA/EL** (partition→available, else→latency) → เร็ว+พร้อมใช้ ยอม consistency หลวม

---

## 67.4 tunable consistency (ไม่ต้องเลือกตายตัว)

```
quorum อ่าน/เขียน ปรับได้ (Dynamo-style):
  W = จำนวน replica ที่ต้อง ack ตอนเขียน · R = ตอนอ่าน · N = replica ทั้งหมด
  W + R > N → strong (อ่านเจอ write ล่าสุดแน่)   เช่น N=3, W=2, R=2
  W + R ≤ N → eventual (เร็วกว่า, อาจอ่านเก่า)    เช่น W=1, R=1
```
- **ปรับต่อ operation**: write สำคัญ → W สูง · read ทั่วไป → R=1 (เร็ว)
- vector: ingest อาจ W=1 (เร็ว, eventual) · query R=1 (เร็ว) → เอน, ยอม eventual (§67.2)

---

## 67.5 CAP กับ retrieval quality (มุมเฉพาะ)

```
vector search "ผิดนิดหน่อย" ทนได้กว่า DB ธุรกรรม:
  - ค้นได้ top-k ที่ recall 95% แทน 100% → ยังมีประโยชน์ (ANN เองก็ approximate! Ch3)
  - doc ใหม่ยังไม่ propagate (eventual) → ค้นเจอในไม่กี่วินาที → ทนได้
→ retrieval โดยธรรมชาติ "approximate + eventual-friendly" → AP เข้ากันดี
```
- ต่างจาก bank balance (ต้องเป๊ะ) → vector search มี "ความคลาดเคลื่อนที่ยอมรับได้" ในตัว (Ch3 ANN)

---

## 67.6 เชื่อม ARRA

```
ARRA local single-node (Ch65): ไม่มี partition (1 เครื่อง) → C+A ครบ (CAP ไม่บังคับเลือก)
  → personal ได้ทั้ง strong+available+fresh (ข้อได้เปรียบ ย้ำ Ch65)
Vectorize edge (Ch14, distributed): AP/eventual (§67.2) → global available, doc propagate ข้าม region
  → เหมาะ retrieval (approximate-friendly §67.5)
tunable: ถ้าต้องการ ปรับ consistency ได้ (§67.4) แต่ default eventual พอ
```
- **บทเรียน**: single-node หลบ CAP ได้ (ไม่มี P) → อีกเหตุผล personal single-node เรียบง่าย+แรง (Ch48/65)

---

## สรุป Ch67
```
CAP: partition เกิดจริง (P บังคับ) → เลือก C หรือ A ไม่ได้ทั้งคู่
⭐ partition: CP (รอ sync, ปฏิเสธ=unavailable) vs AP (รับเลย, eventual inconsistent)
vector search เอน AP: ค้นเจอของเกือบล่าสุดยอมได้ > ค้นไม่ได้เลย (availability สำคัญกว่า)
⭐ PACELC: partition→A/C, else→Latency/C (แม้ปกติก็แลก) · vector มัก PA/EL (เร็ว+พร้อม)
tunable consistency: W+R>N=strong, ≤N=eventual (ปรับต่อ op, Dynamo)
retrieval approximate โดยธรรมชาติ (ANN Ch3) → eventual/AP เข้ากันดี (ทนคลาดเคลื่อน)
ARRA: single-node หลบ CAP (ไม่มี P) → C+A+fresh ครบ · Vectorize=AP edge
```
**ถัดไป Ch68:** replication strategies deep — leader-follower vs multi-leader vs leaderless, read-repair, anti-entropy, conflict resolution (CRDT/LWW)
---
*grounded: CAP (Brewer/Gilbert-Lynch) · PACELC (Abadi) · Dynamo quorum (W+R>N) · ANN approximate (Ch3) · เชื่อม Ch3/14/48/65/66 · /loop deep iter 2026-07-16*
