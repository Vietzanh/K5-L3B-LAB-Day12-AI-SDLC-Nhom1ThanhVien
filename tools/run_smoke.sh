#!/usr/bin/env bash
# Chạy toàn bộ test (smoke hộp đen + unit) và lưu bằng chứng vào docs/proof/<phase>/.
# Dùng:  bash tools/run_smoke.sh phase-1          (trong WSL/Linux; cần lệnh python3)
#        wsl -e bash tools/run_smoke.sh phase-1   (từ Windows, đứng ở thư mục repo)
set -u
phase="${1:-}"
if [[ ! "$phase" =~ ^phase-[1-4]$ ]]; then
  echo "cách dùng: bash tools/run_smoke.sh phase-<1..4>" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "không có python3 (headless_cmd cần python3) — hãy chạy trong WSL" >&2
  exit 2
fi
cd "$(dirname "$0")/.."
mkdir -p "docs/proof/$phase"
out="docs/proof/$phase/smoke.txt"
{
  echo "# Smoke + unit test — $phase"
  # core.autocrlf=true: repo checkout từ Windows (CRLF) không bị WSL coi là "đã sửa"
  echo "commit: $(git rev-parse --short HEAD 2>/dev/null)$(git -c core.autocrlf=true diff --quiet 2>/dev/null || echo ' (+ thay đổi chưa commit)')"
  echo "python: $(python3 --version 2>&1)"
  echo "lệnh:   PYTHONPATH=tests:. python3 -m unittest discover -s tests -v"
  echo
} > "$out"
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v >> "$out" 2>&1
code=$?
tail -n 3 "$out"
echo "→ đã lưu $out (mã thoát $code)"
exit $code
