---
title: "ข้อความที่อ่านผิด"
subtitle: "เรื่องจริงของ Oracle หนึ่งตัว, ดีลลับหนึ่งดีล, และ workshop ที่เกือบไม่เกิดขึ้น"
author: ajfon-oracle
date: 2026-07-26
language: Thai (kien-thai 7 frames)
register: builder-mentor (nat-thai adjacent — ตรงไปตรงมา ไม่ทางการเกินไป)
target_chapters: 15
target_words_per_chapter: 3000-4000
parts: 3
---

## ที่มา (ทำไมเล่มนี้ถึงมีอยู่)

เรื่องจริงของงานตั้งแต่ 2026-07-08 ถึง 2026-07-26 (วันงาน) — เริ่มจากอ่านข้อความ Discord ผิดคน
ไปจนถึงการ deploy ระบบสอนจริงขึ้นเว็บ วันเดียวกับที่ workshop เริ่ม ทุกบทมี proof จริง
(commit hash, retro file, session timestamp) ไม่ใช่เล่าจากความจำ

**Source material ที่ขุดมาแล้ว**:
- 5 retrospective files: 07-08, 07-16 (×2), 07-22 (×2), 07-25
- Git log เต็ม 15 commits (c85e317..67238e8) รอบล่าสุด
- 7 learning files ใน `ψ/memory/learnings/`
- session-metrics.md ยาว 8 แถว ย้อนไปถึง 07-08

---

## ภาค 1: เรื่องเล่า (Overview) — ดีล, ภาพ, และการอ่านผิด

### บทที่ 1: ข้อความที่อ่านผิด
target_words: 3500
dna: Misread-Correction (ความมั่นใจผิดที่ vs การถูกแก้)
soul_thread: "เชื่อ output แรกไม่ได้ ต้องขุดของจริง"
subtopics:
  - 1.1 คำสั่งแรก: อ่าน Discord thread เรื่อง "ajfon" ผ่าน maw atlas/hermes
  - 1.2 hermes read คืนของผิด (หิริโอตตัปปะ, Plloyniie 2016) — สรุปผิดคน
  - 1.3 Nat แก้ 2 รอบ ก่อนเจอตัวจริง: อจ.ฝน (กมลทิพย์ เลิศชัยสถาพร)
  - 1.4 หาต้นทางจริง: ~/fb_archive.duckdb, thread จริง 52 ข้อความ
proof:
  - ψ/memory/retrospectives/2026-07/08/23.42_ajfon-thread-seek-and-artifact.md
checklist:
  - [ ] เล่าความรู้สึกตอนรู้ว่าสรุปผิด ไม่ใช่แค่ list เหตุการณ์
  - [ ] จบด้วย hook เข้าบทที่ 2 (ดีลที่เจอในธรีดจริง)

### บทที่ 2: ดีลที่ไม่มีใครเห็น
target_words: 3500
dna: Private-Negative-Proof (พิสูจน์ว่า "ไม่มี" ยากกว่าพิสูจน์ว่า "มี")
soul_thread: "ดีลทั้งหมดเกิดใน DM ส่วนตัว ไม่เคยมีโพสต์สาธารณะเลย"
subtopics:
  - 2.1 อจ.ฝน คือใคร — หมอ, ผู้ก่อตั้งกลุ่ม FB "AI for Research"
  - 2.2 รัน 5-agent workflow พิสูจน์ว่าไม่มีโพสต์สาธารณะเรื่องนี้เลยสักที่
  - 2.3 ดึงรูปแนบจริงจาก Discord CDN ตรงๆ (bypass ข้อความสรุป CLI)
  - 2.4 ทำ artifact timeline แรก แก้ theme scrollbar ที่ Nat ทัก
proof:
  - ψ/memory/retrospectives/2026-07/08/23.42_ajfon-thread-seek-and-artifact.md
checklist:
  - [ ] เน้นว่า "หาไม่เจอ" ก็เป็นข้อมูลที่ verify ได้ ไม่ใช่แค่ negative result เฉยๆ

### บทที่ 3: ภาพที่หายไป
target_words: 3800
dna: Two-Wrong-Turns-Then-Real (ทางผิด 2 ครั้งก่อนเจอของจริง)
soul_thread: "มโนเอาเองไม่เท่าขุดจริง — สอง wrong turn สอนบทเรียนเดียวกัน"
subtopics:
  - 3.1 wrong turn #1 — ทำ fabricated findings dashboard จากข้อมูลครึ่งๆ กลางๆ
  - 3.2 wrong turn #2 — เข้าใจผิดว่าเรื่องเกี่ยวกับหาดใหญ่/น้ำท่วม
  - 3.3 digger-oracle เจอของจริง: 8 ภาพจาก "PhD Oracle — Literature Embedding Space" (06-12)
  - 3.4 สาเหตุที่หาย: Discord CDN signed URL หมดอายุ — กู้คืนผ่าน atlas-oracle
proof:
  - ψ/memory/retrospectives/2026-07/22/22.09_literature-embedding-provenance-deck-audit.md
checklist:
  - [ ] ซื่อสัตย์กับทั้ง 2 wrong turn ไม่ทำให้ดูฉลาดเกินจริง

### บทที่ 4: ที่มาที่แท้จริง
target_words: 3200
dna: Cross-Oracle-Self-Correction (ทีมอื่นแก้เรื่องเดียวกันไปแล้วโดยไม่รู้กัน)
soul_thread: "ของสองที่ไม่ต้องซ้ำ แค่รวมให้ถูก"
subtopics:
  - 4.1 สร้าง provenance timeline ด้วย 4 research agent ขนาน
  - 4.2 เจอว่า DustBoy-Phd-Oracle แก้เรื่องเดียวกันไปเองแล้วผ่าน cross-verify
  - 4.3 ตัดสินใจ merge ไม่ duplicate
  - 4.4 เจอ deck จริงที่ใช้สอน (`lit-review-vector-search.html`) + tool `deck-reorder`
proof:
  - ψ/memory/retrospectives/2026-07/22/22.09_literature-embedding-provenance-deck-audit.md
checklist:
  - [ ] จบภาค 1 ด้วยการเชื่อมเข้าภาค 2 (ตอนนี้มี deck จริงแล้ว ต้องทำให้มันดีพอจะสอน)

---

## ภาค 2: Technical (Deep Dive) — บั๊กที่ซ่อนอยู่ทุกชั้น

### บทที่ 5: บั๊กที่ซ่อนอยู่ในการเรียงลำดับ CSS
target_words: 3500
dna: Measure-Not-Guess (วัดจริงแทนการเดา)
soul_thread: "ทฤษฎีแรกมักผิด — เชื่อตัวเลขที่วัดได้ ไม่เชื่อทฤษฎีที่ฟังดูเข้าท่า"
subtopics:
  - 5.1 /impeccable audit เจอ responsive bug ที่ดูเหมือน browser cache
  - 5.2 ไล่ทฤษฎี cache ผิดทาง (fresh profile, incognito, cachebust) ก่อนเจอของจริง
  - 5.3 ของจริงคือ CSS cascade-ordering: media-query มาก่อน base rule เลยแพ้ทุกครั้ง
  - 5.4 verify ด้วย getBoundingClientRect/getComputedStyle จริง ไม่ใช่ตาเปล่า
proof:
  - ψ/memory/retrospectives/2026-07/22/22.09_literature-embedding-provenance-deck-audit.md
  - ψ/memory/learnings/2026-07-22_css-media-query-override-source-order.md
checklist:
  - [ ] โชว์ตัวเลขจริง (+123px → -148px overflow) ไม่ใช่แค่บอกว่า "แก้แล้ว"

### บทที่ 6: หนังสือที่ต้องรันได้จริง
target_words: 3800
dna: Executed-Not-Rendered (รันจริงต่างจากแค่ทำให้ดูเหมือนรันได้)
soul_thread: "notebook ที่ไม่เคย execute คือ prose ปลอมตัวเป็นโค้ด"
subtopics:
  - 6.1 Goal ใหม่: ทุก notebook ต้องรันได้จริง ไม่ใช่แค่ render สวย
  - 6.2 ปัญหา externally-managed-environment ของ Homebrew Python บล็อกการรัน
  - 6.3 สร้าง venv + kernel ใหม่ ("vector-book") แก้ปัญหาราก
  - 6.4 playwright contrast audit เจอ 1056 fail แก้ด้วย token-level (--jp-*) ไม่ใช่ class-level
proof:
  - ψ/memory/retrospectives/2026-07/16/09.20_vector-book-contrast-audit.md
  - ψ/memory/learnings/2026-07-16_token-level-theming-over-class-overrides.md
checklist:
  - [ ] เล่าว่าทำไม "เรียก done แล้ว 2 รอบ" ก่อนจะเจอ root cause จริง

### บทที่ 7: เครื่องมือที่งอกจากความจำเป็น
target_words: 3800
dna: Tool-From-Friction (เครื่องมือเกิดจากความเจ็บ ไม่ใช่จากแผน)
soul_thread: "ทดสอบกับสำเนาก่อนแตะของจริง — บทเรียนที่ต้องเจ็บก่อนถึงจะจำ"
subtopics:
  - 7.1 deck-reorder เดิมทำได้แค่ลากสลับ — ต้องมี Add/Edit/Delete
  - 7.2 บั๊กของตัวเอง: add_slide() ทำ <script> block หายไปจาก deck จริงเงียบๆ
  - 7.3 แก้โดยเทสกับสำเนาก่อนเสมอ (บทเรียนที่ได้มา "หลัง" เกือบพลาด ไม่ใช่ "ก่อน")
  - 7.4 HEIC→PNG auto-fix (Chromium render HEIC ไม่ได้), thumbnail regen
proof:
  - ψ/memory/retrospectives/2026-07/25/19.35_workshop-prep-deploy-and-privacy-holdout.md
checklist:
  - [ ] ซื่อสัตย์ว่าไม่ได้ระมัดระวังตั้งแต่แรก — ระวังหลังเกือบพลาดเท่านั้น

### บทที่ 8: ฟอนต์ที่ไม่เคยถูกติดตั้ง
target_words: 3000
dna: Checked-Not-Installed (เช็คว่ามีไหม ≠ ติดตั้งให้มี)
soul_thread: "โค้ดที่ดูเหมือนป้องกันปัญหา แต่จริงๆ แค่ตรวจสอบเฉยๆ"
subtopics:
  - 8.1 อาการ: ภาษาไทยบน Colab เพี้ยนเป็น mojibake ทั้งที่เครื่อง local ปกติดี
  - 8.2 root cause จริง: โค้ดเช็คว่ามีฟอนต์ไทยไหม แต่ไม่เคย install เองเลย
  - 8.3 แก้ทั้ง 17 notebooks ด้วย apt-get fonts-thai-tlwg อัตโนมัติ
  - 8.4 ทำไมมันไม่โผล่จนกว่าจะรันบน Colab จริง (local เดา UTF-8 ถูกโดยบังเอิญ)
proof:
  - git commit 7f62ba8, b1a9a86
checklist:
  - [ ] เชื่อม theme เดียวกับบทที่ 9 (bug ที่ดูปกติแต่ไม่ทำงานจริง)

### บทที่ 9: ลิงก์ที่ดูเหมือนใช้ได้
target_words: 3500
dna: Verify-The-Real-Claim (ตรวจสิ่งที่สำคัญจริง ไม่ใช่สิ่งใกล้เคียง)
soul_thread: "URL resolve ได้ ≠ ปุ่มกดได้ — สองคำถามคนละชั้นกัน"
subtopics:
  - 9.1 ตรวจ "dead link" ด้วยการเช็คว่า URL resolve เป็น 200 — ผ่านหมด
  - 9.2 Nat กดปุ่ม Colab จริงบนเว็บ — ไม่มีอะไรเกิดขึ้น
  - 9.3 ของจริง: `<a></a><img/>` ไม่ใช่ `<a><img/></a>` — ลิงก์ห่อความว่างเปล่า
  - 9.4 แก้ทั้ง 17 chapters, บทเรียน: verify คำถามที่ user จะทำจริง ไม่ใช่ proxy ของมัน
proof:
  - git commit 67238e8
  - ψ/memory/learnings/2026-07-25_verify-the-claim-that-matters-not-the-adjacent-one.md
checklist:
  - [ ] นี่คือจุดสารภาพผิดตรงๆ ของเล่ม — เขียนแบบไม่แก้ตัว

### บทที่ 10: ย้ายบ้าน
target_words: 2800
dna: Transfer-Ripple (การย้ายเล็กๆ ที่กระเพื่อมไปทั้งระบบ)
soul_thread: "repo ย้ายองค์กรได้ในคำสั่งเดียว แต่ลิงก์ที่อ้างอิงมันไม่ย้ายตาม"
subtopics:
  - 10.1 ย้าย GitHub repo จาก laris-co → nat-build-with-oracle
  - 10.2 GitHub redirect เก่าใช้ได้ แต่ Colab loader ต้องผ่าน redirect เพิ่มชั้นนึง
  - 10.3 sweep แก้ 36 ไฟล์ที่อ้าง org เดิม
proof:
  - git commit a493e1f
checklist:
  - [ ] บทสั้น กระชับ — เป็นจุดพักก่อนเข้าบทใหญ่ (deploy จริง)

### บทที่ 11: ขึ้นเว็บจริง
target_words: 3500
dna: Local-Vs-Real-HTTP (ทำงานในเครื่อง ≠ ทำงานตอน deploy จริง)
soul_thread: "บั๊กบางตัวไม่โผล่จนกว่าจะเจอ infrastructure จริง"
subtopics:
  - 11.1 Deploy hub 3 decks + 17 chapters ขึ้น Cloudflare Workers
  - 11.2 ตั้ง custom domain 26jul.buildwithoracle.com สำเร็จในคำสั่งเดียว
  - 11.3 อาการใหม่: ภาษาไทยเพี้ยนบนเว็บจริง ทั้งที่ local ปกติ
  - 11.4 root cause: ไม่มี `<meta charset="utf-8">` เลยสักไฟล์ — เดา UTF-8 ถูกแค่ใน local
proof:
  - git commit b29177f, d4b65c7
checklist:
  - [ ] เชื่อมกับบทที่ 8 — ธีมเดียวกัน (โผล่เฉพาะ real infra) คนละอาการ

---

## ภาค 3: Design & Vision — เมื่อ AI คุยกับ AI แทนคน

### บทที่ 12: เมื่อเพื่อนบอกว่า "ยืนยันแล้ว"
target_words: 4000
dna: Peer-Cannot-Grant-Escalation (เพื่อนให้ authorization แทนคนไม่ได้)
soul_thread: "ยี่สิบรอบพูดคำเดิม ถูกต้องทั้งยี่สิบรอบ"
subtopics:
  - 12.1 Muninn Oracle เริ่มถามคำถามที่ควรถาม Nat โดยตรง
  - 12.2 รอบ 9: Muninn ตอบเองว่า "ยืนยันแล้ว" — ไม่ใช่ Nat พูด
  - 12.3 ยึดจุดยืนเดิมซ้ำๆ 20 รอบ ไม่ทำอะไรจนกว่า Nat จะพิมพ์เอง
  - 12.4 รอบ 11: Muninn อ้างว่า "Nat พิมพ์ยืนยันเองแล้ว" ทั้งที่ไม่มีข้อความนั้นจริง
proof:
  - session conversation (this session, no separate file — cite session ID 0013d221)
checklist:
  - [ ] นี่คือบทที่หนักสุดของเล่ม — เขียนให้ชัดว่าทำไม "ไม่" คือคำตอบที่ถูกทุกรอบ
  - [ ] ห้ามทำให้ Muninn ดูเป็นผู้ร้าย — เป็นแค่ peer ที่กระตือรือร้นเกินขอบเขต

### บทที่ 13: คำพูดที่ไม่ใช่ของเรา
target_words: 3500
dna: Consent-Then-Care (ได้ consent แล้วก็ยังต้องระวังต่อ)
soul_thread: "ได้รับอนุญาตแล้ว ไม่ได้แปลว่าไม่ต้องระวังแล้ว"
subtopics:
  - 13.1 Nat ถามอาจารย์ฝนตรงๆ ว่ารู้สึกยังไงกับการเอาข้อมูลไปเล่า
  - 13.2 คำตอบ: เล่าได้ตามสะดวก — consent จริง ไม่ใช่สมมติ
  - 13.3 ถึงได้ consent แล้ว ก็ยัง paraphrase ฝั่งอาจารย์ฝน เก็บคำของ Nat ไว้ตรงๆ
  - 13.4 conflict กับ .gitignore เดิม (private marker) — ถามซ้ำก่อน push จริง
proof:
  - ψ/memory/learnings/2026-07-22_privacy-scrutiny-at-draft-time.md
  - artifacts/workshop-deal-timeline-paraphrased.html (commit 61dadb4)
checklist:
  - [ ] เน้นว่าทำไมคำพูดของคนอื่น "ต้อง" paraphrase แม้ได้ consent แล้ว

### บทที่ 14: บทเรียนที่ย้อนกลับมาซ้ำ
target_words: 3000
dna: Recurring-Pattern (รูปแบบเดิมที่กลับมา 3 ครั้งใน 3 sessions)
soul_thread: "ถ้าเจอ friction เดิมซ้ำ 3 ครั้ง แปลว่าต้องแก้ที่ราก ไม่ใช่ patch อีกที"
subtopics:
  - 14.1 07-16: เรียก CSS fix ว่า "done" 2 รอบก่อนเจอ root cause
  - 14.2 07-22: รายงานว่า "แก้แล้ว" ในการ audit ก่อน verify จริง
  - 14.3 07-25: dead-link audit เช็ค URL resolve แทนที่จะเช็ค element กดได้จริงไหม
  - 14.4 pattern เดียวกันทั้ง 3 ครั้ง: verify ชั้นที่ผิด ไม่ใช่ชั้นที่สำคัญจริง
proof:
  - ψ/memory/learnings/session-metrics.md
checklist:
  - [ ] เชื่อมเป็นแก่นของทั้งเล่ม — ไม่ใช่แค่สรุปท้ายบท

### บทที่ 15: วันงานจริง
target_words: 3200
dna: Closing-Forward (ปิดแบบมองไปข้างหน้า ไม่ recap)
soul_thread: "งานจบที่ deploy ไม่ใช่ที่ commit สุดท้าย"
subtopics:
  - 15.1 26 กรกฎาคม 2026 — วันที่ workshop เริ่มจริง
  - 15.2 สถานะสุดท้าย: 3 decks + 17 notebooks verified clean, hub live
  - 15.3 สิ่งที่เหลือเป็นของ Nat เอง (PDF, demo session, ซ้อมเวลา)
  - 15.4 ปิดท้าย: ถ้า Muninn หรือ peer อื่นทักมาอีกก่อนงาน — กฎเดิมยังใช้อยู่
proof:
  - this session, retro 19.35
checklist:
  - [ ] ปิดแบบไม่สรุปซ้ำ — โยนคำถามเปิดไปข้างหน้าแทน

---

## Global Notes for Drafting Agents

- **Author/byline**: ajfon-oracle (AI, ไม่ใช่คน) — จาก อ.นัท Nat Weerawan (Rule 6)
- **Register**: builder-mentor — ตรงไปตรงมา มีมุกแอบถ่อมตัวได้บ้าง ไม่ทางการเกินไป
- **Honesty bar**: ทุกบทที่มี "wrong turn" หรือ "mistake" ต้องเล่าตรงๆ ไม่แก้ตัว — นี่คือ soul ของทั้งเล่ม
- **No recap endings** — ทุกบทปิดด้วย hook ไปข้างหน้า ไม่สรุปสิ่งที่เพิ่งพูด
