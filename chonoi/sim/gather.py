"""Buổi sáng — Lặn & Hái (`gather`). Luật theo PRD-0 mục F + Ticket-02 (v1.1) + Ticket-03 (v1.2, độ tươi).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Thứ tự một bước (v1.1 mục 4.5):
  1. đồng hồ, hồi bắt, giảm bất tử, hồi nút (node_regrown), hao tươi hàng có sẵn trong giỏ (spoiled theo id)
  2. bơi + chặn mép (dive/surface), oxy theo d cuối bước, ngạt (choke) -> Máu 0: faint + gather_end
  3. Cá Sấu theo id (recoil / patrol / chase), rồi tối đa MỘT hit -> Máu 0: faint + gather_end
  4. interact: bến trước, rồi hái (chỉ ở mặt nước)
  5. catch: đàn gần nhất theo vị trí cá TRƯỚC khi bơi (chỉ dưới nước, hết hồi)
  6. hết giờ -> gather_end(time); còn giờ: cá bơi, sinh thêm theo lịch
"""

import math

from ..ids import sort_by_id
from ..inventory import SCALE, inventory_doc, to_units, view
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


def _ticks(seconds):
    return int(round(seconds * TICK))


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, hp_max=None, oxygen_max_s=None,
                 money=0, earned=0, reputation=None):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.day = day
        self.hp_max = int(hp_max if hp_max is not None else t["hp_max"])
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = _ticks(oxygen_max_s if oxygen_max_s is not None else t["oxygen_max_s"])
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        fr = tuning["freshness"]
        self.fresh_initial = to_units(fr["initial"])
        self.decay = int(round(fr["gather_decay_per_s"] * SCALE / TICK))
        self.spoil_u = fr["spoiled_below"] * SCALE
        # giỏ: cá thể {id, kind, u} theo thứ tự nhặt (cuối mảng là mới nhất)
        self.hold = [{"id": it["id"], "kind": it["kind"], "u": to_units(it["fresh"])} for it in scenario.get("hold", [])]
        for it in self.hold:
            ids.reserve(it["id"])
        self.duration = _ticks(t["duration_s"])
        self.time_left_ticks = scenario.get("time_left_ticks", self.duration)
        self.phase_tick = 0
        # nút: scenario THAY THẾ danh sách mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        for n in self.nodes:
            ids.reserve(n["id"])
        # đàn cá: random_fish=false tắt cá mặc định, bơi và sinh (cá fixture đứng yên)
        self.fish_active = scenario.get("random_fish", True)
        if "fish" in scenario:
            self.fish = [self._fish(f["id"], f["kind"], f["pos"], f.get("heading_deg", 0), f.get("age_ticks", 0))
                         for f in scenario["fish"]]
            for f in self.fish:
                ids.reserve(f["id"])
        else:
            self.fish = []
            if self.fish_active:
                for _ in range(int(t["fish_initial"])):
                    self._spawn_fish(None)
        # thủy quái: scenario thay danh sách; không khai -> bố trí đúng Ngày
        mons = t["monsters"]
        if "monsters" in scenario:
            src = scenario["monsters"]
        else:
            src = [m for m in mons["spawns"] if m["from_day"] <= day]
        self.monsters = [self._monster(m) for m in src]
        for m in self.monsters:
            ids.reserve(m["id"])
        self.money = money
        self.earned = earned
        self.reputation = reputation if reputation is not None else tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- dựng thực thể -----------------------------------------------------------
    @staticmethod
    def _fish(fid, kind, pos, heading, age):
        return {"id": fid, "kind": kind, "pos": [float(c) for c in pos], "heading_deg": float(heading),
                "age_ticks": int(age)}

    @staticmethod
    def _monster(m):
        return {"id": m["id"], "kind": m["kind"], "pos": [float(c) for c in m["pos"]],
                "waypoints": [[float(c) for c in w] for w in m["waypoints"]],
                "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                "state_ticks_left": m.get("state_ticks_left", 0),
                "recoil_dir": [float(c) for c in m["recoil_dir"]] if m.get("recoil_dir") is not None else None}

    # --- giao diện cho runner -------------------------------------------------------
    def inventory_items(self) -> list:
        """Cá thể trong giỏ (nội bộ, có `u`) để ghi file kho / bàn giao trong day."""
        return [dict(it) for it in self.hold]

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": [view(it) for it in self.hold], "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"],
                      "age_ticks": f["age_ticks"]} for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": m["pos"], "state": m["state"],
                          "target_idx": m["target_idx"], "waypoints": m["waypoints"],
                          "state_ticks_left": m["state_ticks_left"], "recoil_dir": m["recoil_dir"]}
                         for m in sort_by_id(self.monsters)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ, hồi bắt, bất tử, hồi nút
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        for it in sort_by_id(self.hold):  # hàng có sẵn ở đầu bước; hàng mới hao từ bước sau
            before = it["u"]
            it["u"] = max(0, before - self.decay)
            if before >= self.spoil_u > it["u"]:
                events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"}))
        # 2. bơi + chặn mép, so phía mặt nước đầu/cuối bước
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif now_surface and not was_surface:
            events.append(("surface", {"pos": list(self.pos)}))
        # oxy theo d CUỐI bước
        if now_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + int(self.t["oxygen_refill_per_tick"]))
            self.zero_oxy_ticks = 0
        else:
            before = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if before > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                    self.zero_oxy_ticks = 0
                    self.hp -= 1  # ngạt xuyên bất tử, không làm rơi hàng
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        self._faint("choke", events)
                        return events
        # 3. thủy quái theo id, rồi tối đa một hit
        self._update_monsters()
        if self._monster_hit(events):
            return events
        # 4. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if self._at_surface():
                self._harvest(events)
        # 5. bắt cá
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not self._at_surface():
            self._catch(events)
        # 6. hết giờ; còn giờ thì cá bơi và sinh thêm
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        if self.fish_active:
            self._swim_fish()
            if self.phase_tick % int(self.t["fish_spawn_ticks"]) == 0 and len(self.fish) < int(self.t["fish_max"]):
                self._spawn_fish(events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _nearest(self, coll, radius):
        """Thực thể gần nhất trong bán kính (tính cả đúng mép), hòa theo id."""
        best = None
        for e in sort_by_id(coll):
            dd = math.dist(self.pos, e["pos"])
            if dd <= radius and (best is None or dd < best[0]):
                best = (dd, e)
        return best[1] if best else None

    def _harvest(self, events):
        node = self._nearest([n for n in self.nodes if n["regrow_ticks"] == 0], self.t["interact_radius"])
        if node is None:
            return
        amount = int(self.t["node_yield"])
        if self._free() < amount:
            events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                         "required": amount, "free": self._free()}))
            return
        self._add(node["kind"], amount)
        node["regrow_ticks"] = _ticks(self.t["regrow_s"])
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": amount}))

    def _catch(self, events):
        fish = self._nearest(self.fish, self.t["catch_radius"])
        if fish is None:
            return  # không có đàn trong tầm: không sự kiện, không hồi chiêu
        y = int(self.t["fish_yield"][fish["kind"]])
        if self._free() < y:
            events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                         "required": y, "free": self._free()}))
            return
        self._add(fish["kind"], y)
        self.fish = [f for f in self.fish if f["id"] != fish["id"]]
        self.catch_cd_ticks = _ticks(self.t["catch_cooldown_s"])
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": y}))

    def _add(self, kind, n):
        for _ in range(n):
            self.hold.append({"id": self.ids.new("I"), "kind": kind, "u": self.fresh_initial})

    def _free(self) -> int:
        return int(self.t["hold_capacity"]) - len(self.hold)

    def _drop_lifo(self, n):
        """Bỏ n món cuối giỏ (nhặt sau mất trước); trả mảng theo thứ tự bỏ."""
        lost = []
        for _ in range(min(n, len(self.hold))):
            lost.append(view(self.hold.pop()))
        return lost

    def _faint(self, cause, events):
        """Máu 0: bỏ toàn bộ phần còn lại theo LIFO, faint rồi gather_end(fainted) với kho rỗng."""
        lost = self._drop_lifo(len(self.hold))
        self.hp = 0
        events.append(("faint", {"cause": cause, "lost": lost, "hp": 0}))
        self._finish("fainted", events)

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": inventory_doc(self.hold)}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])

    # --- đàn cá: bơi và sinh -----------------------------------------------------
    def _swim_fish(self):
        t = self.t
        step = t["fish_speed"] / TICK
        xlo, xhi = t["fish_x"]
        turn = self.rng.get("fish_turn")
        for f in sort_by_id(self.fish):
            if (f["age_ticks"] + 1) % int(t["fish_turn_ticks"]) == 0:
                f["heading_deg"] = turn.uniform(0.0, 360.0)
            a = math.radians(f["heading_deg"])
            vx, vd = math.cos(a) * step, math.sin(a) * step
            dlo, dhi = t["fish_depths"][f["kind"]]
            nx, fx = self._reflect(f["pos"][0], vx, xlo, xhi)
            nd, fd = self._reflect(f["pos"][1], vd, dlo, dhi)
            if fx or fd:
                vx, vd = (-vx if fx else vx), (-vd if fd else vd)
                f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360
            f["pos"] = [nx, nd]
            f["age_ticks"] += 1

    @staticmethod
    def _reflect(p, v, lo, hi):
        n = p + v
        if n > hi:
            return 2 * hi - n, True
        if n < lo:
            return 2 * lo - n, True
        return n, False

    def _spawn_fish(self, events):
        """Sinh một đàn ở điểm chuẩn cách mọi đàn đang sống > clearance; loài theo trọng số chuẩn hóa lại."""
        t = self.t
        clear = t["fish_spawn_clearance"]
        valid = {}
        for kind in sorted(t["fish_spawn_depths"]):
            pts = [[float(x), float(d)] for x in t["fish_spawn_x"] for d in t["fish_spawn_depths"][kind]
                   if all(math.dist([x, d], f["pos"]) > clear for f in self.fish)]
            if pts:
                valid[kind] = pts
        if not valid:
            return  # hết điểm: bỏ lượt
        rng = self.rng.get("fish_spawn")
        kinds = sorted(valid)
        total = sum(t["fish_weights"][k] for k in kinds)
        r = rng.random() * total
        kind = kinds[-1]
        for k in kinds:
            r -= t["fish_weights"][k]
            if r < 0:
                kind = k
                break
        pos = valid[kind][rng.randrange(len(valid[kind]))]
        heading = rng.uniform(0.0, 360.0)
        fid = self.ids.new("F")
        self.fish.append(self._fish(fid, kind, pos, heading, 0))
        if events is not None:
            events.append(("fish_spawned", {"id": fid, "kind": kind, "pos": list(pos)}))

    # --- thủy quái ----------------------------------------------------------------
    def _species(self, m):
        return self.t["monsters"]["species"][m["kind"]]

    def _clamp_monster(self, m):
        sp = self._species(m)
        b = self.t["bounds"]
        m["pos"][0] = min(b["x"][1], max(b["x"][0], m["pos"][0]))
        m["pos"][1] = min(sp["depths"][1], max(sp["depths"][0], m["pos"][1]))

    @staticmethod
    def _toward(m, target, dist_step):
        dx, dd = target[0] - m["pos"][0], target[1] - m["pos"][1]
        d = math.hypot(dx, dd)
        if d <= dist_step:
            m["pos"] = [float(target[0]), float(target[1])]
            return True
        m["pos"] = [m["pos"][0] + dx / d * dist_step, m["pos"][1] + dd / d * dist_step]
        return False

    def _update_monsters(self):
        self._recovered = set()  # vừa hết recoil ở bước này: xét phát hiện/chạm từ bước kế
        for m in sort_by_id(self.monsters):
            sp = self._species(m)
            if m["state"] == "recoil":
                step = sp["recoil_dist"] / sp["recoil_ticks"]
                m["pos"] = [m["pos"][0] + m["recoil_dir"][0] * step, m["pos"][1] + m["recoil_dir"][1] * step]
                self._clamp_monster(m)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"], m["state_ticks_left"], m["recoil_dir"] = "patrol", 0, None
                    self._recovered.add(m["id"])
                continue
            deep = self.pos[1] >= sp["depths"][0]
            dist = math.dist(m["pos"], self.pos)
            if m["state"] == "patrol" and deep and dist <= sp["detect_radius"]:
                m["state"] = "chase"
            elif m["state"] == "chase" and (dist > sp["exit_radius"] or not deep):
                m["state"] = "patrol"
            if m["state"] == "chase":
                self._toward(m, self.pos, sp["chase_speed"] / TICK)
                self._clamp_monster(m)
            else:
                wp = m["waypoints"][m["target_idx"]]
                arrived = self._toward(m, wp, sp["patrol_speed"] / TICK)
                self._clamp_monster(m)
                if arrived:
                    m["target_idx"] = 1 - m["target_idx"]

    def _monster_hit(self, events) -> bool:
        """Tối đa một hit mỗi bước (con gần nhất, hòa theo id). Trả True nếu ngất (đã kết thúc buổi)."""
        if self.invuln_ticks > 0:
            return False
        best = None
        for m in sort_by_id(self.monsters):
            if m["state"] == "recoil" or m["id"] in self._recovered:
                continue
            sp = self._species(m)
            d = math.dist(m["pos"], self.pos)
            if self.pos[1] >= sp["depths"][0] and d <= sp["hit_radius"] and (best is None or d < best[0]):
                best = (d, m)
        if best is None:
            return False
        m = best[1]
        mons = self.t["monsters"]
        self.hp -= 1
        lost = self._drop_lifo(math.floor(len(self.hold) * mons["loss_ratio"]))
        self.invuln_ticks = int(mons["invuln_ticks"])
        dx, dd = m["pos"][0] - self.pos[0], m["pos"][1] - self.pos[1]
        n = math.hypot(dx, dd)
        m["state"], m["state_ticks_left"] = "recoil", int(self._species(m)["recoil_ticks"])
        m["recoil_dir"] = [dx / n, dd / n] if n > 0 else [1.0, 0.0]
        events.append(("monster_hit", {"monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos)}))
        if self.hp <= 0:
            self._faint("monster", events)
            return True
        return False
