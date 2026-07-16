# Deep Technical · Chapter 13 — Retrieval Heat Model (จำเหมือนสมอง)

> ต่อจาก Ch12 · Ch4 §4.4 บอกว่า ARRA เติม "retrieval heat" เข้า ranking · บทนี้ลงลึก: heat คำนวณยังไง ทำไมทำให้เป็น "second brain" ไม่ใช่ search engine

---

## 13.0 ปัญหาที่ heat แก้: relevance ไม่พอ

search engine ปกติ: relevance(query, doc) เท่านั้น · แต่ **second brain ของคน**จำเพิ่ม 2 อย่าง:
- อะไรที่**ใช้บ่อย** (frequency) → น่าจะสำคัญ
- อะไรที่**เพิ่งใช้** (recency) → น่าจะยังเกี่ยว

ARRA เก็บ `usage_count` + `last_accessed_at` ต่อ memory (Ch4 openapi/memory.ts) → เอามาถ่วง ranking

---

## 13.1 Recency — exponential decay

"เพิ่งใช้ = ร้อน, นานแล้ว = เย็น" ใช้ **exponential decay**:
```
recency(d) = exp( − λ · Δt )        Δt = now − last_accessed_at
```
- `λ` = decay rate · **half-life** `t½ = ln2/λ` (เวลาที่ความร้อนเหลือครึ่ง)
- ใช้เมื่อวาน (Δt เล็ก) → ~1 · ใช้ปีที่แล้ว (Δt ใหญ่) → ~0
- เลือก half-life ตามโดเมน: งานวิจัยที่ context เปลี่ยนช้า → half-life ยาว (สัปดาห์-เดือน)

**ทำไม exponential ไม่ linear**: การลืมของคน + ความเกี่ยวข้องตามเวลา เป็น multiplicative decay (Ebbinghaus forgetting curve ก็ exponential) → เป็นธรรมชาติกว่า

---

## 13.2 Frequency — log dampening

"ใช้บ่อย = สำคัญ" แต่ **ไม่เชิงเส้น** (doc ที่ใช้ 1000 ครั้งไม่ได้สำคัญกว่า 100 ครั้ง 10 เท่า):
```
frequency(d) = log(1 + usage_count)      ← saturating
```
- log กด diminishing returns (เหมือน IDF/BM25 saturation, Ch7 §7.2)
- กัน doc ยอดฮิตครองงำ

---

## 13.3 รวมเป็น heat

```
heat(d) = w_r · recency(d) + w_f · frequency(d)
        = w_r · exp(−λΔt) + w_f · log(1 + usage_count)
```
เข้า final score (Ch4 §4.4 / Ch11 §11.6):
```
final(d) = RRF(d) + confidenceWeight·conf(d) + heat(d)
```

---

## 13.4 เชื่อมทฤษฎี cache: LRU + LFU

heat = ผสม **recency (LRU)** + **frequency (LFU)** — ตรงกับ cache eviction ที่ดีสุด (เช่น **LFU-with-aging**, ARC):
- LRU เพียว: เพิ่งใช้ = เก็บ (แต่ one-hit wonder ลอย)
- LFU เพียว: ใช้บ่อย = เก็บ (แต่ของเก่าฮิตค้าง ไม่ยอมออก)
- **ผสม + aging (decay)**: ของที่ทั้งบ่อยและใหม่ = ร้อนสุด → ตรงกับ heat ของ ARRA

→ retrieval heat = **นำ eviction policy ของ cache มาใช้เป็น ranking prior** อย่างมีทฤษฎีรองรับ

---

## 13.5 เชื่อมชีววิทยา: memory consolidation

สมองคน: ความจำที่ **ระลึกบ่อย** ถูก consolidate แข็งแรงขึ้น (synaptic) · ที่ไม่ใช้ → จางไป (spaced-repetition/Anki ใช้หลักนี้: ทวนตอนใกล้ลืม → เสริมแรง)

ARRA heat = analog เชิงคำนวณ: doc ที่ retrieval บ่อย/ล่าสุด "แข็งแรง" ในการถูกดึงกลับ · ทุกครั้งที่ค้นเจอแล้วใช้ → `usage_count++`, `last_accessed_at=now` → **loop เสริมแรง** → นี่คือความหมายจริงของ "brain ที่โตไปกับคุณ" (Ch primers: ai-library-th tagline)

---

## 13.6 ความเสี่ยง (ต้อง balance)

- **rich-get-richer**: doc ฮิตยิ่งขึ้นบ่อย → heat สูง → ขึ้นบ่อยขึ้น → feedback loop · ต้อง cap / decay กันผูกขาด
- **cold start**: doc ใหม่ heat=0 → เสียเปรียบ · ต้องให้ RRF (relevance) มีน้ำหนักพอที่ doc ใหม่ที่เกี่ยวจริงยังขึ้นได้
- **staleness**: doc เก่าที่เคยฮิตแต่ล้าสมัย → recency decay ช่วยกดลง (นี่คือเหตุผลต้องมี recency ไม่ใช่ frequency อย่างเดียว)
- tuning: `w_r, w_f, confidenceWeight` ต้อง validate ด้วย nDCG (Ch6) — มากไป personalization กลบ relevance

---

## 13.7 สรุปเชิง algorithm

```python
def final_score(d, query):
    rrf  = sum(1/(60 + rank_r(d)) for r in [fts, vector])   # Ch11
    conf = confidence(d)                                     # prior ความน่าเชื่อ
    recency = exp(-lam * (now - d.last_accessed_at))         # §13.1
    freq    = log(1 + d.usage_count)                         # §13.2
    heat = w_r*recency + w_f*freq                            # §13.3
    return rrf + 0.25*conf + heat
# หลัง retrieve+use:  d.usage_count += 1; d.last_accessed_at = now   ← เสริมแรง (§13.5)
```

---

## สรุป Ch13
```
heat = recency (exp decay, half-life) + frequency (log saturating)
เข้า final = RRF + conf + heat  (likelihood × priors, Ch11)
= LRU+LFU cache policy นำมาเป็น ranking prior
= memory consolidation ของสมอง (ใช้บ่อย→แข็งแรง, retrieve→เสริมแรง)
ระวัง rich-get-richer/cold-start/staleness → recency decay + RRF weight balance
```
**ถัดไป Ch14:** Cloudflare Vectorize + D1 internals — managed ANN บน edge ทำงานยังไง, upsert/query, limits, เทียบ LanceDB

---
*grounded: Ch4 §4.4 (usage_count/last_accessed_at), Ch11 (final score) · exponential decay/Ebbinghaus · LFU-aging/ARC cache · spaced repetition · /loop deep iter 2026-07-13*
