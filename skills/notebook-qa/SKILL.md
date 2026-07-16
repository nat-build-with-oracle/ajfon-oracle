---
name: notebook-qa
description: >
  ตรวจ quality ของหนังสือ/เอกสารที่ render จาก Jupyter notebook (nbconvert HTML) — ใส่ธีมเข้าถึงได้
  (token-level, light+dark) + snapshot ทุกหน้าด้วย playwright + คำนวณ WCAG contrast ทุก text element จริง
  แล้วรายงาน fail จนแก้เหลือ 0. Use when: "ตรวจ contrast", "audit หนังสือ/notebook HTML", "snapshot ทุกหน้า",
  "perfect contrast", "notebook-qa", "book qa", "ธีม nbconvert อ่านไม่ออก dark mode", or verifying rendered
  notebook/HTML pages meet WCAG AA. NOT for design mockups (use artifact-design) or general code review.
metadata:
  type: reference
---

# notebook-qa — Quality gate สำหรับหนังสือ/เอกสารจาก Jupyter notebook

> เกิดจากงานจริง: snapshot จับ 1056 contrast fail ที่ static analysis มองไม่เห็น (dark-mode table พื้นขาว,
> code pre base ดำ, inline code) แล้วแก้เหลือ 0 ด้วยการ **flip design token ระดับ `--jp-*`** ไม่ใช่ override รายคลาส.

## หลักการ (บทเรียนที่ฝังในสคริปต์)
1. **วัด contrast อย่าเดา** — WCAG ratio คำนวณได้ (relative luminance). อย่าเชื่อสายตา, รัน audit.
2. **nbconvert เดินทุกสีผ่าน CSS var `--jp-*`** — แก้ที่ token (light+dark) คุม syntax/table/code/link ครบในที่เดียว.
   Override รายคลาสจะชนกับ media query ของ nbconvert เอง.
3. **screenshot จับสิ่งที่ static ไม่เห็น** — table td พื้นขาวในdark, code overflow crop, ¶ anchor.
4. **idempotent** — สคริปต์ apply_theme รันซ้ำทับได้ (ลบธีมเก่าก่อนแทรกใหม่).

## Workflow

### 0) ต้องมี (ครั้งเดียวต่อ venv)
```bash
uv pip install playwright && python -m playwright install chromium   # (+ pandoc/typst ถ้าจะทำ PDF)
```

### 1) ใส่ธีมเข้าถึงได้ + wrap โค้ด (light+dark, WCAG AA)
```bash
# แก้ path 'html/' ในหัวสคริปต์ให้ตรงโฟลเดอร์ HTML ของโปรเจกต์ก่อนรัน
python ~/.claude/skills/notebook-qa/scripts/apply_theme.py
```
สคริปต์ flip `--jp-mirror-editor-*` (syntax), `--jp-layout-color*`, `--jp-content-font-color*`,
`--jp-rendermime-table-*`, code/table/inline-code, links, prompts + `white-space: pre-wrap` (โค้ด wrap ไม่ scroll)
+ hover motion (เคารพ `prefers-reduced-motion`). ปรับสี/ฟอนต์ในหัวไฟล์ `THEME` ได้.

### 2) Serve + snapshot + audit contrast
```bash
python -m http.server 8890 --directory html &      # nbconvert HTML ต้อง serve (asset/relative path)
python ~/.claude/skills/notebook-qa/scripts/contrast_audit.py
```
สคริปต์เปิด playwright, snapshot ทุกหน้า (light+dark, retina 2×) ลง `shots/` + คำนวณ WCAG contrast
ทุก text element (fg vs bg ที่ไต่ parent จริง) → พิมพ์ fail + เขียน `shots/contrast_report.json`.

### 3) แก้จน 0 fail แล้ว verify ด้วยตา
- fail ส่วนใหญ่แก้ที่ token ใน `apply_theme.py` (step 1) แล้ววน step 2 ใหม่.
- เปิด `shots/<page>__dark.png` / `__light.png` ดูจริง — audit เช็คสี ไม่เช็ค layout/overflow.

## เมื่อไหร่ใช้
- หลัง `jupyter nbconvert --to html` ทุกครั้งที่จะเผยแพร่หนังสือ/เอกสาร notebook.
- เจอ dark mode โค้ด/ตารางอ่านไม่ออก → step 1 แก้ที่ token.
- ต้องการหลักฐาน "perfect contrast" (32 snapshot, 0 fail) ก่อนส่งงาน.

## ปรับใช้กับโปรเจกต์อื่น
- แก้ตัวแปร `BASE`/`OUT`/glob ใน `contrast_audit.py` และ `glob('html/ch*.html')` + `THEME` ใน `apply_theme.py`.
- ธีมเขียนผ่าน `--jp-*` ของ nbconvert (JupyterLab) — ถ้า HTML ไม่ใช่ nbconvert ให้ override selector ตรงๆ แทน.
