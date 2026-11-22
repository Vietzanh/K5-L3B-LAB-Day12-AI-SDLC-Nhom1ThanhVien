#!/usr/bin/env bash
# Smoke --mode day: 1 Ngày không input (đo thời gian) + 3 Ngày có mua nâng cấp (kiểm cấp áp từ Ngày kế).
# Dùng: bash tools/smoke_day.sh <thư-mục-bằng-chứng>   (trong WSL/Linux, cần python3)
set -eu
out_dir="${1:-docs/proof/phase-2}"
cd "$(dirname "$0")/.."
mkdir -p "$out_dir"
cmd=$(python3 -c 'import json;print(json.load(open("game.contract.json"))["headless_cmd"])')
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
log="$out_dir/day.txt"
{
  echo "# Smoke day — commit $(git rev-parse --short HEAD), contract $(python3 -c 'import json;print(json.load(open("game.contract.json"))["contract_version"])')"
  echo "\$ $cmd --mode day --seed 42 --days 1 --ticks 22200 --out day1.jsonl"
  start=$(date +%s.%N)
  $cmd --mode day --seed 42 --days 1 --ticks 22200 --out "$tmp/day1.jsonl"
  echo "exit=$? thời gian=$(python3 -c "print(round($(date +%s.%N)-$start,2))") s"
  echo "--- event đổi pha + dòng end"
  python3 - "$tmp/day1.jsonl" <<'PY'
import json, sys
for line in open(sys.argv[1]):
    r = json.loads(line)
    if r["type"] == "end" or (r["type"] == "event" and r["name"] in ("day_start", "day_plan", "phase_start", "gather_end", "quan_end", "shop_end")):
        print(json.dumps(r, ensure_ascii=False))
PY
  echo
  echo '{"day":{"money":700,"earned":700},"gather":{"random_fish":false},"quan":{"time_left_ticks":1}}' > "$tmp/sc.json"
  echo '{"frames":[{"tick":0,"interact":true},{"tick":1,"interact":false},{"tick":2,"buy":"hp"},{"tick":3,"buy":"oxygen","shop_done":true},{"tick":4,"interact":true,"shop_done":false}]}' > "$tmp/in.json"
  echo "\$ $cmd --mode day --seed 7 --days 3 --scenario sc.json --inputs in.json --ticks 10 --snapshot-every 1 --out day3.jsonl"
  echo "  (sc.json: money 700, cập bến ngay, ca quán 1 tick; in.json: tick 2 mua hp, tick 3 mua oxygen + shop_done, tick 4 cập bến Ngày 2)"
  $cmd --mode day --seed 7 --days 3 --scenario "$tmp/sc.json" --inputs "$tmp/in.json" --ticks 10 --snapshot-every 1 --out "$tmp/day3.jsonl"
  echo "exit=$?"
  python3 - "$tmp/day3.jsonl" <<'PY'
import json, sys
for line in open(sys.argv[1]):
    r = json.loads(line)
    if r["type"] == "event" and r["name"] in ("bought", "buy_failed", "shop_end", "day_start"):
        print("event", r["tick"], "Ngày", r["day"], r["name"], json.dumps(r["data"]))
    if r["type"] == "snapshot" and r["tick"] in (3, 4):
        p = r.get("player", {})
        print("snapshot", r["tick"], "Ngày", r["day"], r["phase"], "upgrades", r["upgrades"], "active", r["active_upgrades"],
              "hp_max", p.get("hp_max"), "oxygen_max_ticks", p.get("oxygen_max_ticks"), "money", r["money"])
PY
} > "$log" 2>&1
cat "$log" | grep -E "exit=|snapshot 4"
echo "→ đã lưu $log"
