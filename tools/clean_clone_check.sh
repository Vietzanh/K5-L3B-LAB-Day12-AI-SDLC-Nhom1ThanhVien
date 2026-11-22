#!/usr/bin/env bash
# Thử từ CLONE SẠCH đúng các lệnh trong README (macOS/Linux): chạy game, test, headless, bench, soak.
# Dùng: bash tools/clean_clone_check.sh <nguồn-repo> <nhánh-hoặc-tag> <file-bằng-chứng>
set -u
src="${1:-.}"; ref="${2:-main}"; log="${3:-docs/proof/phase-4/clean-clone.txt}"
here="$(pwd)"
tmp=$(mktemp -d); trap 'kill $srv 2>/dev/null; rm -rf "$tmp"' EXIT
{
  echo "# Clone sạch — nguồn $ref ($(git -C "$src" rev-parse --short "$ref")), $(uname -s), $(python3 --version)"
  echo "\$ git clone <repo> cho-noi && cd cho-noi        (lệnh 1 + 2)"
  git clone -q --branch "$ref" "$src" "$tmp/cho-noi" 2>&1 && cd "$tmp/cho-noi" && echo "clone OK: $(ls | tr '\n' ' ')"
  echo "\$ python3 -m chonoi.live                        (lệnh 3; ở đây thêm --port 8123 và kiểm /state)"
  python3 -m chonoi.live --port 8123 > "$tmp/live.log" 2>&1 & srv=$!
  for i in $(seq 1 30); do sleep 0.2; python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8123/state',timeout=1)" 2>/dev/null && break; done
  head -1 "$tmp/live.log"
  python3 -c "import json,urllib.request;s=json.load(urllib.request.urlopen('http://127.0.0.1:8123/state'));print('GET /state ->', {k:s[k] for k in ('mode','phase','day','screen','state')})"
  python3 -c "import urllib.request;h=urllib.request.urlopen('http://127.0.0.1:8123/').read();print('GET / ->', len(h), 'byte HTML, có <canvas>:', b'<canvas' in h)"
  kill $srv; wait $srv 2>/dev/null
  echo "\$ PYTHONPATH=tests:. python3 -m unittest discover -s tests"
  PYTHONPATH=tests:. python3 -m unittest discover -s tests 2>&1 | tail -3
  echo "\$ python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out day.jsonl"
  python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out "$tmp/day.jsonl"; echo "exit=$? dòng cuối: $(tail -1 "$tmp/day.jsonl")"
  echo "\$ python3 -m chonoi.bench --seed 42 --duration 2 --out bench.json"
  python3 -m chonoi.bench --seed 42 --duration 2 --out "$tmp/bench.json"; echo "exit=$?"
  echo "\$ python3 -m chonoi.soak --seed 7 --days 2 --out soak.json"
  python3 -m chonoi.soak --seed 7 --days 2 --out "$tmp/soak.json"; echo "exit=$?"
} > "$here/$log" 2>&1
cat "$here/$log"
