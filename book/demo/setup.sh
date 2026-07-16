#!/usr/bin/env bash
# ChromaDB Workshop Demo — Full Setup
# ใช้ uv (เร็ว) หรือ fallback เป็น python3 -m venv + pip
set -euo pipefail
cd "$(dirname "$0")"

echo "== ARRA Oracle Workshop · ChromaDB Demo Setup =="

if command -v uv >/dev/null 2>&1; then
  echo "[1/2] สร้าง venv + ติดตั้ง chromadb ด้วย uv..."
  uv venv --python 3.12 .venv 2>/dev/null || uv venv .venv
  uv pip install --python .venv/bin/python chromadb
else
  echo "[1/2] สร้าง venv + ติดตั้ง chromadb ด้วย pip..."
  python3 -m venv .venv
  .venv/bin/pip install --quiet --upgrade pip
  .venv/bin/pip install --quiet chromadb
fi

echo "[2/2] ทดสอบ import..."
.venv/bin/python -c "import chromadb; print('chromadb', chromadb.__version__, 'พร้อมใช้ ✓')"

echo ""
echo "เสร็จ! รันเดโม:  .venv/bin/python demo1_first_search.py"
