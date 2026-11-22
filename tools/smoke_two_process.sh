#!/usr/bin/env bash
# Smoke hai tiến trình (PRD-0 mục G; v1.2 Ticket-03): gather cập bến ghi kho cá thể -> quan đọc kho,
# so CHÍNH XÁC id, kind, fresh của snapshot quán tick 0 với file (sau lần hao ở bước gather).
# Dùng: bash tools/smoke_two_process.sh <thư-mục-bằng-chứng>   (trong WSL/Linux, cần python3)
set -eu
out_dir="${1:-docs/proof/phase-1}"
cd "$(dirname "$0")/.."
mkdir -p "$out_dir"
cmd=$(python3 -c 'import json;print(json.load(open("game.contract.json"))["headless_cmd"])')
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
echo '{"gather":{"hold":[{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"bong_sung","fresh":100},{"id":"I3","kind":"bong_sung","fresh":100}],"random_fish":false,"monsters":[]}}' > "$tmp/dock.json"
echo '{"frames":[{"tick":0,"interact":true}]}' > "$tmp/dock-inputs.json"
log="$out_dir/two-process.txt"
{
  echo "# Smoke hai tiến trình — commit $(git rev-parse --short HEAD)"
  echo "\$ $cmd --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json"
  $cmd --mode gather --seed 42 --scenario "$tmp/dock.json" --inputs "$tmp/dock-inputs.json" --ticks 1 \
       --out "$tmp/gather.jsonl" --inventory-out "$tmp/catch.json"
  echo "exit=$?"
  echo "--- catch.json"; cat "$tmp/catch.json"
  echo "--- gather.jsonl"; cat "$tmp/gather.jsonl"
  echo "\$ $cmd --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl"
  $cmd --mode quan --seed 42 --inventory "$tmp/catch.json" --ticks 0 --out "$tmp/quan.jsonl"
  echo "exit=$?"
  echo "--- quan.jsonl"; cat "$tmp/quan.jsonl"
  echo "--- so khớp"
  python3 - "$tmp/catch.json" "$tmp/quan.jsonl" <<'PY'
import json, sys
inv = json.load(open(sys.argv[1]))
snap = json.loads(open(sys.argv[2]).readline())
items = inv["items"]
stock = snap["stock"]
print("file kho :", json.dumps(items, ensure_ascii=False))
print("quan tick0:", json.dumps(stock, ensure_ascii=False))
print("KẾT QUẢ:", "KHỚP" if stock == items else "LỆCH")
sys.exit(0 if stock == items else 1)
PY
} > "$log" 2>&1
tail -n 3 "$log"
echo "→ đã lưu $log"
