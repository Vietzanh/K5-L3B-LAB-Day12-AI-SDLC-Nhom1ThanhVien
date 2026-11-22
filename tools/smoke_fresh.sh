#!/usr/bin/env bash
# Smoke ngưỡng tươi (Ticket-03): scenario mẫu fresh 30 -> spoiled ở tick 1; gather một bước không input.
# Dùng: bash tools/smoke_fresh.sh <thư-mục-bằng-chứng>
set -eu
out_dir="${1:-docs/proof/phase-3}"
cd "$(dirname "$0")/.."
mkdir -p "$out_dir"
cmd=$(python3 -c 'import json;print(json.load(open("game.contract.json"))["headless_cmd"])')
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
echo '{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}' > "$tmp/sc.json"
log="$out_dir/threshold.txt"
{
  echo "# Ngưỡng tươi — commit $(git rev-parse --short HEAD), contract $(python3 -c 'import json;print(json.load(open("game.contract.json"))["contract_version"])')"
  echo "scenario: $(cat "$tmp/sc.json")"
  echo "\$ $cmd --mode gather --seed 1 --scenario sc.json --ticks 1 --out o.jsonl"
  $cmd --mode gather --seed 1 --scenario "$tmp/sc.json" --ticks 1 --out "$tmp/o.jsonl"
  echo "exit=$?"
  grep '"spoiled"' "$tmp/o.jsonl"
  echo "--- hold ở snapshot tick 1:"
  python3 -c "import json,sys;r=[json.loads(l) for l in open(sys.argv[1])];print(json.dumps([x for x in r if x['type']=='snapshot'][-1]['hold']))" "$tmp/o.jsonl"
} > "$log" 2>&1
grep -c spoiled "$log" >/dev/null && echo "→ đã lưu $log"
