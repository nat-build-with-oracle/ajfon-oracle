# QA Skills — เครื่องมือตรวจ quality ที่ใช้สร้างหนังสือ + สไลด์เล่มนี้

เครื่องมือ 2 ตัวที่ใช้ verify งานก่อนเผยแพร่ (ธีม **"วัด อย่าเดา"**) — ติดตั้งเป็น Claude Code skill
ที่ `~/.claude/skills/` ด้วย · vendor สำเนาไว้ที่นี่เพื่อ version control + แชร์

## notebook-qa
ตรวจ HTML ที่ render จาก Jupyter (nbconvert):
- ธีมเข้าถึงได้ระดับ token (`--jp-*`, light + dark) + code wrap + hover motion
- snapshot ทุกหน้า (playwright) + คำนวณ WCAG contrast ทุก text element จริง
- เกิดจากงานจริง: จับ 1056 contrast fail ที่ static analysis มองไม่เห็น → แก้เหลือ 0

## slide-deck-qa
ตรวจ HTML slide deck (presentation):
- snapshot ทุกสไลด์ที่ projector res (1920×1080) + contrast + overflow (ล้นจอ) + broken image/404
- serve ผ่าน http ให้เอง (แก้ปัญหา `file://`)
- **contrast checker แม่น**: composite alpha (tinted glass pill), parse gradient stops,
  เช็ค own-direct-text (ข้าม wrapper ที่ child คนละสี) — พัฒนา 4 รอบจาก feedback การใช้งานจริง

## ใช้ยังไง
```bash
pip install playwright && python -m playwright install chromium   # ครั้งเดียว
python slide-deck-qa/scripts/deck_audit.py <deck.html>
python notebook-qa/scripts/contrast_audit.py                       # (ดู SKILL.md แต่ละตัว)
```
ดูรายละเอียดใน `SKILL.md` ของแต่ละ skill
