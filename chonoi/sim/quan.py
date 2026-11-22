"""Buổi tối — Mở Quán (`quan`). Luật theo PRD-0 mục F "Quán" + Test Contract v1.0.

Nhìn từ trên xuống: vị trí `[x, z]`. Kho `stock` là tồn VẬT LÝ (gồm cả phần khách đang giữ chỗ);
kho khả dụng = tồn vật lý − tổng phần giữ.

Thứ tự một bước:
  1. đồng hồ: phase_tick+1, ca −1; tuổi món ready (+1, chỉ món ready ở đầu bước), nấu −1, ăn −1, kiên nhẫn −1
  2. bếp theo id: nấu xong -> ready (dish_ready)
  3. di chuyển rồi tối đa MỘT interact, chọn theo (khoảng cách, bếp trước bàn, id)
  4. theo id bàn: ăn xong trả tiền rồi rời; còn giờ: hết kiên nhẫn rời (−uy tín); hết ca: trả ngay / rời closing, quan_end
  5. còn giờ: lượt khách theo lịch (bàn trống id nhỏ nhất, món đủ nguyên liệu khả dụng chọn đều theo seed) / no_dish
"""

import math

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left", "eat_ticks_left",
                 "order_status", "reserved", "base_price", "tip"}
STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}


def _ticks(seconds):
    return int(round(seconds * TICK))


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.duration = _ticks(t["duration_s"])
        self.time_left_ticks = scenario.get("time_left_ticks", self.duration)
        self.phase_tick = 0
        self.patience_full = _ticks(t["patience_s"])
        self.eat_full = _ticks(t["eat_s"])
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.random_customers = scenario.get("random_customers", True)
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [self._customer_defaults(c) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
        self._validate_fixture()
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    # --- dựng fixture -------------------------------------------------------------
    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _customer_defaults(self, c):
        extra = set(c) - CUSTOMER_KEYS
        if extra:
            raise BadInput(f"customers.{c['id']}: trường lạ {sorted(extra)}")
        out = {"id": c["id"], "table_id": c.get("table_id"), "dish_id": c.get("dish_id"),
               "order_tick": c.get("order_tick", 0), "state": c.get("state", "waiting"),
               "patience_ticks_left": c.get("patience_ticks_left", self.patience_full),
               "eat_ticks_left": c.get("eat_ticks_left", 0),
               "order_status": c.get("order_status", "reserved"),
               "reserved": c.get("reserved"), "base_price": c.get("base_price"), "tip": c.get("tip")}
        return out

    def _validate_fixture(self):
        """Mâu thuẫn mức luật trong scenario quán -> BadInput (mã 2), TRƯỚC khi ghi đầu ra."""
        t, menu = self.t, self.menu
        kinds = {k for d in menu.values() for k in d["recipe"]}
        for k, v in self.stock.items():
            if k not in kinds or not _is_int(v) or v < 0:
                raise BadInput(f"stock.{k} không hợp lệ")
        b = t["bounds"]
        for s in self.stoves:
            extra = set(s) - STOVE_KEYS
            if extra:
                raise BadInput(f"stoves.{s['id']}: trường lạ {sorted(extra)}")
            self._check_pos(f"stoves.{s['id']}.pos", s["pos"], b)
            for key in ("cook_ticks_left", "ready_ticks"):
                if not _is_int(s[key]) or s[key] < 0:
                    raise BadInput(f"stoves.{s['id']}.{key} phải là số nguyên không âm")
            if s["state"] not in ("idle", "cooking", "ready"):
                raise BadInput(f"stoves.{s['id']}.state không hợp lệ")
            if s["state"] == "idle" and (s["dish"] is not None or s["cook_ticks_left"] or s["ready_ticks"]):
                raise BadInput(f"stoves.{s['id']}: bếp idle không có món/bộ đếm")
            if s["state"] == "cooking" and (s["dish"] is None or s["cook_ticks_left"] <= 0 or s["ready_ticks"]):
                raise BadInput(f"stoves.{s['id']}: bếp cooking cần món và cook_ticks_left > 0")
            if s["state"] == "ready" and (s["dish"] is None or s["cook_ticks_left"]):
                raise BadInput(f"stoves.{s['id']}: bếp ready cần món")
        for tb in self.tables:
            if set(tb) - {"id", "pos"}:
                raise BadInput(f"tables.{tb['id']}: chỉ có id, pos")
            self._check_pos(f"tables.{tb['id']}.pos", tb["pos"], b)
        # món đang ở bếp / trên tay
        dishes = {}
        holders = [(f"stove {s['id']}", s["dish"]) for s in self.stoves if s["dish"] is not None]
        if self.hand is not None:
            holders.append(("hand", self.hand))
        for where, d in holders:
            self._check_payload(where, d)
            if d["order_id"] in dishes:
                raise BadInput(f"đơn {d['order_id']} nằm ở hai nơi (bếp/tay)")
            dishes[d["order_id"]] = d
        table_ids = {tb["id"] for tb in self.tables}
        by_id = {c["id"]: c for c in self.customers}
        for c in self.customers:
            cid = c["id"]
            if c["table_id"] not in table_ids:
                raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
            if c["dish_id"] not in menu:
                raise BadInput(f"customers.{cid}: dish_id phải thuộc thực đơn")
            for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
                if not _is_int(c[key]) or c[key] < 0:
                    raise BadInput(f"customers.{cid}.{key} phải là số nguyên không âm")
            if c["patience_ticks_left"] > self.patience_full or c["eat_ticks_left"] > self.eat_full:
                raise BadInput(f"customers.{cid}: bộ đếm vượt mức đầy")
            if c["state"] not in ("waiting", "eating") or c["order_status"] not in ORDER_STATUSES:
                raise BadInput(f"customers.{cid}: state/order_status không hợp lệ")
            st = c["order_status"]
            dish = dishes.get(cid)
            if dish is not None and dish["dish_id"] != c["dish_id"]:
                raise BadInput(f"customers.{cid}: món ở bếp/tay không khớp đơn")
            if c["state"] == "eating":
                if st != "served" or c["eat_ticks_left"] <= 0:
                    raise BadInput(f"customers.{cid}: khách eating phải served và còn timer ăn")
                for key in ("base_price", "tip"):
                    if not _is_int(c[key]) or c[key] < 0:
                        raise BadInput(f"customers.{cid}: khách eating phải khai {key} đã chốt")
            else:
                if st == "served":
                    raise BadInput(f"customers.{cid}: đơn served thì khách phải eating")
                if c["eat_ticks_left"]:
                    raise BadInput(f"customers.{cid}: khách chờ không có timer ăn")
            if st == "assigned" and dish is None:
                raise BadInput(f"customers.{cid}: đơn assigned cần đúng một món ở bếp hoặc tay")
            if st != "assigned" and dish is not None:
                raise BadInput(f"customers.{cid}: chỉ đơn assigned mới có món ở bếp/tay")
            if st == "reserved":
                if c["reserved"] is not None and self._norm_reserved(cid, c["reserved"]) != self._recipe(c["dish_id"]):
                    raise BadInput(f"customers.{cid}: phần giữ khác công thức")
            elif c["reserved"] not in (None, {}) and self._norm_reserved(cid, c["reserved"]):
                raise BadInput(f"customers.{cid}: chỉ đơn reserved mới giữ nguyên liệu")
        for oid in dishes:
            if oid not in by_id:
                raise BadInput(f"món của đơn {oid} không có khách")
        tables_used = [c["table_id"] for c in self.customers]
        if len(tables_used) != len(set(tables_used)):
            raise BadInput("hai khách cùng bàn")
        # chuẩn hóa phần giữ; đơn reserved thiếu reserved thì cấp theo (order_tick, id bàn)
        for c in self.customers:
            if c["order_status"] != "reserved":
                c["reserved"] = {}
            elif c["reserved"] is not None:
                c["reserved"] = self._norm_reserved(c["id"], c["reserved"])
        for c in sorted(self.customers, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            if c["reserved"] is None:
                need = self._recipe(c["dish_id"])
                if not self._can_make(need):
                    raise BadInput(f"customers.{c['id']}: kho không đủ để giữ chỗ theo công thức")
                c["reserved"] = need
        for k in set(self.stock) | {k for c in self.customers for k in c["reserved"]}:
            if self._reserved_total(k) > self.stock.get(k, 0):
                raise BadInput(f"phần giữ {k} vượt tồn kho")

    def _check_pos(self, name, pos, b):
        ok = isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                                                              for v in pos)
        if not ok or not (b["x"][0] <= pos[0] <= b["x"][1] and b["z"][0] <= pos[1] <= b["z"][1]):
            raise BadInput(f"{name} nằm ngoài phòng")

    def _check_payload(self, where, d):
        if not isinstance(d, dict) or set(d) != {"order_id", "dish_id", "base_price"}:
            raise BadInput(f"món ở {where} phải là {{order_id, dish_id, base_price}}")
        if d["dish_id"] not in self.menu or not _is_int(d["base_price"]) or d["base_price"] <= 0:
            raise BadInput(f"món ở {where}: dish_id/base_price không hợp lệ")
        if not isinstance(d["order_id"], str):
            raise BadInput(f"món ở {where}: order_id phải là chuỗi")

    def _norm_reserved(self, cid, r):
        if not isinstance(r, dict):
            raise BadInput(f"customers.{cid}.reserved phải là object kind -> số")
        out = {}
        for k, v in r.items():
            if not _is_int(v) or v < 0:
                raise BadInput(f"customers.{cid}.reserved.{k} không hợp lệ")
            if v:
                out[k] = v
        return out

    # --- kho --------------------------------------------------------------------
    def _recipe(self, dish_id):
        return {k: v for k, v in self.menu[dish_id]["recipe"].items() if v > 0}

    def _reserved_total(self, kind):
        return sum((c["reserved"] or {}).get(kind, 0) for c in self.customers)

    def _available(self, kind):
        return self.stock.get(kind, 0) - self._reserved_total(kind)

    def _can_make(self, need):
        return all(self._available(k) >= n for k, n in need.items())

    def _menu_ids(self):
        return sorted(self.menu)  # id món theo mã Unicode

    # --- giao diện cho runner -------------------------------------------------------
    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [self._customer_view(c) for c in sort_by_id(self.customers)],
        }

    @staticmethod
    def _customer_view(c):
        v = {k: c[k] for k in ("id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                               "eat_ticks_left", "order_status")}
        v["reserved"] = {k: c["reserved"][k] for k in sorted(c["reserved"])}
        v["base_price"] = c["base_price"]
        v["tip"] = c["tip"]
        return v

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và timer
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
        # 2. bếp theo id: nấu xong -> ready
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                events.append(("dish_ready", {"stove_id": s["id"], "order_id": s["dish"]["order_id"],
                                              "dish_id": s["dish"]["dish_id"]}))
        # 3. di chuyển rồi tối đa một interact
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        # 4. thanh toán, kiên nhẫn, đóng ca (theo id bàn)
        closing = self.time_left_ticks <= 0
        by_table = {c["table_id"]: c for c in self.customers}
        for tb in self.tables:
            c = by_table.get(tb["id"])
            if c is None:
                continue
            if c["state"] == "eating" and (c["eat_ticks_left"] == 0 or closing):
                self._pay(c, "closing" if c["eat_ticks_left"] > 0 else "finished_eating", events)
            elif c["state"] == "waiting" and closing:
                self._leave(c, "closing", events)
            elif c["state"] == "waiting" and c["patience_ticks_left"] == 0:
                self.reputation = self._clamp_rep(self.reputation + self.t["left_reputation_delta"])
                self._leave(c, "patience", events)
        if closing:
            self.done, self.reason = True, "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
            return events
        # 5. lượt khách theo lịch
        if self.random_customers and self._arrival_due():
            self._arrive(events)
        return events

    # --- tương tác --------------------------------------------------------------
    def _interact(self, events):
        r = self.t["interact_radius"]
        cands = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= r:
                cands.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= r:
                cands.append((d, 1, id_key(tb["id"]), "table", tb))
        if not cands:
            return
        _, _, _, kind, obj = min(cands, key=lambda c: c[:3])
        if kind == "stove":
            if obj["state"] == "idle":
                self._start_cooking(obj, events)
            elif obj["state"] == "ready" and self.hand is None:
                self.hand = obj["dish"]
                events.append(("dish_picked", {"stove_id": obj["id"], "order_id": obj["dish"]["order_id"],
                                               "dish_id": obj["dish"]["dish_id"]}))
                obj["state"], obj["dish"], obj["ready_ticks"], obj["cook_ticks_left"] = "idle", None, 0, 0
        else:
            c = next((c for c in self.customers if c["table_id"] == obj["id"]), None)
            if c and c["state"] == "waiting" and self.hand is not None and self.hand["order_id"] == c["id"]:
                self._serve(c, obj, events)

    def _start_cooking(self, stove, events):
        orders = [c for c in self.customers if c["order_status"] == "reserved"]
        if not orders:
            return
        c = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        items = []
        for k in sorted(c["reserved"]):
            n = c["reserved"][k]
            self.stock[k] = self.stock.get(k, 0) - n
            if self.stock[k] == 0:
                del self.stock[k]
            items.extend([k] * n)
        base = self._locked_price(c)
        c["reserved"], c["order_status"], c["base_price"] = {}, "assigned", base
        stove.update(state="cooking", dish={"order_id": c["id"], "dish_id": c["dish_id"], "base_price": base},
                     cook_ticks_left=_ticks(self.menu[c["dish_id"]]["cook_s"]), ready_ticks=0)
        events.append(("cook_started", {"stove_id": stove["id"], "order_id": c["id"], "dish_id": c["dish_id"],
                                        "items": items, "base_price": base}))

    def _locked_price(self, c):
        return int(self.menu[c["dish_id"]]["price"])

    def _serve(self, c, table, events):
        base = self.hand["base_price"]
        ratio = self.t["tip_min_patience_ratio"]
        tip = math.floor(base * self.t["tip_rate"] + 1e-9) \
            if c["patience_ticks_left"] >= ratio * self.patience_full - 1e-9 else 0
        c.update(state="eating", order_status="served", eat_ticks_left=self.eat_full, base_price=base, tip=tip)
        self.hand = None
        events.append(("served", {"order_id": c["id"], "table_id": table["id"], "dish_id": c["dish_id"],
                                  "patience_ticks_left": c["patience_ticks_left"], "base_price": base, "tip": tip}))

    def _pay(self, c, reason, events):
        amount = c["base_price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self.reputation = self._clamp_rep(self.reputation + self.t["tip_reputation"])
        events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                                "tip": c["tip"], "amount": amount, "reason": reason}))
        self._remove(c)

    def _leave(self, c, reason, events):
        events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"], "reason": reason,
                                         "reputation": self.reputation}))
        self._remove(c)

    def _remove(self, c):
        """Khách rời: nhả phần giữ (xóa khách), bỏ món của đơn ở bếp hoặc trên tay. Nguyên liệu đã dùng không hoàn."""
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == c["id"]:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand is not None and self.hand["order_id"] == c["id"]:
            self.hand = None
        self.customers = [x for x in self.customers if x["id"] != c["id"]]

    def _clamp_rep(self, v):
        return round(min(self.t["reputation_max"], max(self.t["reputation_min"], v)), 6)

    # --- khách mới ----------------------------------------------------------------
    def _arrival_due(self):
        first = int(self.t["first_customer_tick"])
        interval = _ticks(self.t["customer_interval_s"])
        pt = self.phase_tick
        return pt >= first and (pt - first) % interval == 0

    def _dish_candidates(self):
        return [d for d in self._menu_ids() if self._can_make(self._recipe(d))]

    def _arrive(self, events):
        busy = {c["table_id"] for c in self.customers}
        free = [tb for tb in self.tables if tb["id"] not in busy]
        if not free:
            return
        table = free[0]
        cands = self._dish_candidates()
        if not cands:
            events.append(("no_dish", {}))
            return
        dish_id = cands[self.rng.get("customers").randrange(len(cands))]
        cid = self.ids.new("C")
        self.customers.append({"id": cid, "table_id": table["id"], "dish_id": dish_id, "order_tick": self.phase_tick,
                               "state": "waiting", "patience_ticks_left": self.patience_full, "eat_ticks_left": 0,
                               "order_status": "reserved", "reserved": self._recipe(dish_id),
                               "base_price": None, "tip": None})
        events.append(("customer_arrived", {"order_id": cid, "table_id": table["id"], "dish_id": dish_id}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
