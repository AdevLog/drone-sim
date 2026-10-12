#!/usr/bin/env bash
# 執行全部測試。需要：node、python3、playwright（pip install playwright && playwright install chromium）
set -e
cd "$(dirname "$0")"
echo "== 核心計算（node）：輸出需與 baseline 完全相同 =="
fail=0
for f in core/*.js; do
  n=$(basename "$f" .js)
  if node "$f" | diff -q - "core/baseline/$n.txt" >/dev/null; then echo "PASS $n"; else echo "FAIL $n（輸出與 baseline 不同）"; fail=1; fi
done
echo "== 瀏覽器（playwright）=="
cd browser
python3 build.py
node --check inline.js
python3 regress.py | tail -1
python3 deltest.py
python3 origin.py
exit $fail
