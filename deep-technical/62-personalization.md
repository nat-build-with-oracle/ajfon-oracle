# Deep Technical · Chapter 62 — Personalization

> ต่อจาก Ch61 · ค้นตัวเดียวกัน คนละคนควรได้ผลต่าง (บริบทต่าง) · บทนี้: user context, heat เป็น personalization ชั้นแรก, privacy trade-off

---

## 62.0 ปัญหา — relevance ขึ้นกับ "ใคร"

```
query "transformer":
  วิศวกร ML → อยากได้ neural network architecture
  วิศวกรไฟฟ้า → อยากได้ หม้อแปลงไฟ
→ query เดียว, relevance ต่างตามบริบท user
```
- pure semantic (Ch1) ไม่รู้จัก user → ได้ผลกลางๆ · personalization = ปรับตาม user

---

## 62.1 ⭐ heat (Ch13) = personalization ชั้นแรกฟรี

```
second brain = ของ user คนเดียว → ทุก doc เป็นบริบทของเขาอยู่แล้ว
usage_count/last_accessed (Ch13): doc ที่ user แตะบ่อย → boost
→ นี่คือ personalization โดยธรรมชาติ: "สิ่งที่คุณใช้บ่อย ขึ้นก่อน"
```
- ARRA personal ไม่ต้องสร้าง user profile แยก — corpus ทั้งก้อน = profile ของ user
- heat = implicit signal (Ch31) ของ "อะไรสำคัญกับ user นี้"

---

## 62.2 user context เป็น query augmentation

```
เพิ่มบริบท user เข้า query (Ch57 expansion):
  query "transformer" + context "user เป็น ML engineer, เพิ่งอ่านเรื่อง attention"
  → LLM/retrieval เอนไป ML sense
```
- ARRA ใน Claude Code: dialog history (Ch58) = user context → resolve sense ให้ก่อนค้น
- recent activity (Ch61 recency + Ch13 heat) → บริบทว่า user สนใจอะไรตอนนี้

---

## 62.3 per-user boost / re-ranking

```
final = relevance × f(user_signals)
user_signals: doc user เคยเปิด, folder ที่อยู่บ่อย, topic ที่ค้นบ่อย
→ boost doc ในเขตความสนใจ user
```
- ต่างจาก global ranking (Ch61): เพิ่มแกน "ความเป็นส่วนตัว"
- ⚠️ **filter bubble**: boost มากไป → เห็นแต่ของเดิม (เสีย serendipity/diversity Ch59) → สมดุล

---

## 62.4 ⚠️ privacy trade-off (สำคัญ)

```
personalization ต้องเก็บ user behavior (อะไรค้น/เปิด/สนใจ) → sensitive
cloud personalization: behavior ส่ง server → privacy risk (Ch27)
local (ARRA): behavior อยู่ในเครื่อง → personalize ได้โดยไม่ leak (privacy by design)
```
- **ข้อได้เปรียบ ARRA local (Ch14/27)**: personalize เต็มที่ (รู้ทุกอย่างของ user) โดยข้อมูลไม่ออกเครื่อง
- cloud service ต้อง trade privacy เพื่อ personalize · local ได้ทั้งคู่

---

## 62.5 cold start — user ใหม่ยังไม่มี behavior

```
user เพิ่งเริ่ม → ไม่มี heat/history → personalize ไม่ได้
→ fallback: global relevance (Ch1) ล้วน จนกว่าจะมี signal
→ heat สะสมเร็ว (ใช้ไม่กี่ครั้ง usage_count ก็เริ่มมีผล, Ch13)
```
- second brain โตขึ้น = personalization ดีขึ้นเอง (heat/corpus สะสม)

---

## 62.6 เชื่อม ARRA

```
heat (Ch13) = personalization ฟรี (doc user ใช้บ่อยขึ้นก่อน, §62.1)
dialog context (Ch58) = resolve user sense (§62.2)
local (Ch27) = personalize เต็มที่โดย privacy ปลอด (§62.4) — ข้อได้เปรียบเหนือ cloud
cold start → global relevance → heat สะสมเร็ว (§62.5)
```
- **community**: "ระบบรู้ใจเราขึ้นเรื่อยๆ ไหม" → ใช่ (heat/context สะสม) และ **ข้อมูลไม่ออกเครื่อง** (local)

---

## สรุป Ch62
```
relevance ขึ้นกับ user (transformer = NN vs หม้อแปลง) → personalize
⭐ heat (Ch13) = personalization ชั้นแรกฟรี: second brain=corpus ของ user คนเดียว=profile
user context (Ch58 dialog) → augment query → resolve sense
per-user boost → ⚠️ filter bubble (เสีย diversity Ch59) → สมดุล
⚠️ privacy: personalize ต้องเก็บ behavior → local (ARRA Ch27) personalize เต็มโดยไม่ leak = ได้เปรียบ cloud
cold start → global relevance → heat สะสมเร็ว → ดีขึ้นเอง
```
**ถัดไป Ch63:** learning-to-rank & feedback loops — click/implicit signal → เทรน ranker, online learning, ทำไม feedback ปิด loop สำคัญ
---
*grounded: heat (Ch13) as implicit personalization · filter bubble · privacy-by-design (Ch27) · เชื่อม Ch1/13/27/31/57/58/59/61 · /loop deep iter 2026-07-16*
