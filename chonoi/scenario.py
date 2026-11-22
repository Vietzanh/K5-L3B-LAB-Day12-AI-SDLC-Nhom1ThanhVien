"""Nạp và kiểm scenario (Contract D v1.0 + v1.1 mục 4.3).

`gather`/`quan`: trả dict của đúng khối theo mode. `day`: trả dict {day, gather, quan} (gather/quan là mẫu
khởi tạo mỗi Ngày). Kiểm cú pháp, id trùng, bộ đếm âm, giỏ vượt sức chứa, trường lạ, khối sai mode -> mã 2.
Mâu thuẫn mức luật của quán (giữ chỗ, món, khách) kiểm thêm trong `QuanSim._validate_fixture`.
"""

import json
import math

from .contract import FISH_KINDS, INGREDIENTS, NODE_KINDS, validate_plan_entry
from .errors import BadInput
from .inventory import validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}
# Giữ tên cũ cho mã đang import
FISH_KINDS_ALL = FISH_KINDS


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    allowed_roots = {"day", "gather", "quan"} if mode == "day" else {mode}
    if not isinstance(data, dict) or set(data) - allowed_roots:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối {sorted(allowed_roots)}")
    for k, v in data.items():
        if not isinstance(v, dict):
            raise BadInput(f"khối {k} phải là object")
    if mode == "day":
        upgrades = _validate_day(data.get("day", {}), tuning)
        if "gather" in data:
            _validate_block("gather", data["gather"], tuning, upgrades)
        if "quan" in data:
            for k in ("stock", "reputation"):
                if k in data["quan"]:
                    raise BadInput(f"chạy day không nhận quan.{k} (dùng gather.hold / day.reputation)")
            _validate_block("quan", data["quan"], tuning, upgrades)
        return data
    block = data.get(mode, {})
    _validate_block(mode, block, tuning, {})
    return block


def _validate_block(mode, block, tuning, upgrades):
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning, upgrades)
    else:
        _validate_quan(block, tuning)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if not _int(v) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _vec(name, v):
    if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v)):
        raise BadInput(f"{name} phải là [số, số]")


def _pos(name, pos, bounds, axes=("x", "d")):
    _vec(name, pos)
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài miền ({axis} ∈ [{lo}, {hi}])")


def _level_value(tuning, kind, level, base):
    if level <= 0:
        return base
    field = {"oxygen": "oxygen_max_s", "hp": "hp_max"}[kind]
    return tuning["shop"]["upgrades"][kind][level - 1][field]


def _validate_gather(b, tuning, upgrades):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:  # v1.2: mảng cá thể {id, kind, fresh} theo thứ tự vào giỏ
        h = validate_items(b["hold"], INGREDIENTS, "hold")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p:
        _vec("player.vel", p["vel"])
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(_level_value(tuning, "oxygen", upgrades.get("oxygen", 0), g["oxygen_max_s"]) * 60))
    hpmax = _level_value(tuning, "hp", upgrades.get("hp", 0), g["hp_max"])
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= hpmax):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > g["choke_interval_ticks"] - 1:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if set(n) - {"id", "kind", "pos", "regrow_ticks"}:
            raise BadInput(f"nodes.{n['id']}: trường lạ")
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if set(f) - {"id", "kind", "pos", "heading_deg", "age_ticks"}:
            raise BadInput(f"fish.{f['id']}: trường lạ")
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    species = g["monsters"]["species"]
    for m in b.get("monsters", []):
        mid = m["id"]
        if set(m) - MONSTER_KEYS:
            raise BadInput(f"monsters.{mid}: trường lạ {sorted(set(m) - MONSTER_KEYS)}")
        if m.get("kind") not in species:
            raise BadInput(f"monsters.{mid}: kind phải thuộc {sorted(species)}")
        sp = species[m["kind"]]
        mb = {"x": bounds["x"], "d": sp["depths"]}
        _pos(f"monsters.{mid}.pos", m.get("pos"), mb)
        wps = m.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"monsters.{mid}.waypoints phải có đúng 2 điểm")
        for i, w in enumerate(wps):
            _pos(f"monsters.{mid}.waypoints[{i}]", w, mb)
        if m.get("target_idx", 1) not in (0, 1) or isinstance(m.get("target_idx", 1), bool):
            raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
        state = m.get("state", "patrol")
        if state not in ("patrol", "chase", "recoil"):
            raise BadInput(f"monsters.{mid}.state không hợp lệ")
        stl = m.get("state_ticks_left", 0)
        _nonneg_int(f"monsters.{mid}.state_ticks_left", stl)
        rd = m.get("recoil_dir")
        if state == "recoil":
            if stl <= 0 or rd is None:
                raise BadInput(f"monsters.{mid}: recoil cần timer dương và recoil_dir")
            _vec(f"monsters.{mid}.recoil_dir", rd)
            if abs(math.hypot(*rd) - 1) > 1e-6:
                raise BadInput(f"monsters.{mid}.recoil_dir phải là vector đơn vị")
        elif rd is not None or stl:
            raise BadInput(f"monsters.{mid}: chỉ recoil mới có recoil_dir/timer")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:  # v1.2: mảng cá thể (gồm cả phần giữ)
        validate_items(b["stock"], INGREDIENTS, "stock")
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        q = tuning["quan"]
        if not _num(b["reputation"]) or not q["reputation_min"] <= b["reputation"] <= q["reputation_max"]:
            raise BadInput("quan.reputation ngoài miền")
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p:
        _vec("player.vel", p["vel"])
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")


def _validate_day(d, tuning):
    extra = set(d) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    for k in ("money", "earned"):
        if k in d:
            _nonneg_int(f"day.{k}", d[k])
    money, earned = d.get("money", 0), d.get("earned", 0)
    if money > 0 and "earned" not in d:
        raise BadInput("day: có tiền đầu kỳ thì phải khai cả money và earned")
    if money > earned and "earned" in d:
        raise BadInput("day: cần 0 ≤ money ≤ earned")
    if "reputation" in d:
        q = tuning["quan"]
        if not _num(d["reputation"]) or not q["reputation_min"] <= d["reputation"] <= q["reputation_max"]:
            raise BadInput("day.reputation ngoài miền")
    ups = d.get("upgrades", {})
    if not isinstance(ups, dict):
        raise BadInput("day.upgrades phải là object")
    for k, lv in ups.items():
        levels = tuning["shop"]["upgrades"].get(k)
        if levels is None or not _int(lv) or not 0 <= lv <= len(levels):
            raise BadInput(f"day.upgrades.{k} không hợp lệ")
    plan = d.get("day_plan", [])
    if not isinstance(plan, list):
        raise BadInput("day.day_plan phải là mảng")
    seen = set()
    for i, e in enumerate(plan):
        if not isinstance(e, dict) or set(e) - {"day", "dishes", "ingredients"}:
            raise BadInput(f"day.day_plan[{i}]: chỉ có day, dishes, ingredients")
        if not _int(e.get("day")) or not 1 <= e["day"] <= len(tuning["day_plan"]) or e["day"] in seen:
            raise BadInput(f"day.day_plan[{i}].day không hợp lệ hoặc trùng")
        seen.add(e["day"])
        validate_plan_entry(f"day.day_plan[{i}]", e, tuning["menu"])
    return ups
