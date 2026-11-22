"""Vòng Ngày (`--mode day`, Ticket-02 mục 2 + v1.1 mục 4.5 "Đổi pha").

Mỗi Ngày: day_start -> day_plan -> phase_start(gather) | gather ... gather_end -> phase_start(quan) cùng tick
| quan ... quan_end -> phase_start(shop) cùng tick | shop ... shop_end -> days_completed+1, Ngày kế (hoặc hết).
Tiền, earned, uy tín, cấp nâng cấp giữ qua Ngày; oxy/Máu hồi đầy theo cấp đang áp dụng; kho dư bỏ sau Shop.
Pha mới chỉ chạy gameplay từ bước sau (đổi pha xảy ra cuối bước).
"""

import copy

from ..contract import recipe_total
from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim, upgrade_value


class DayGame:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.streams = streams
        self.ids = ids
        self.days = days
        d = scenario.get("day", {})
        self.money = d.get("money", 0)
        self.earned = d.get("earned", self.money)
        self.reputation = float(d.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(d.get("upgrades", {}))
        self.active_upgrades = dict(self.upgrades)
        overrides = {e["day"]: e for e in d.get("day_plan", [])}
        self.plans = []
        for e in tuning["day_plan"]:
            src = overrides.get(e["day"], e)
            self.plans.append({"dishes": dict(src["dishes"]), "ingredients": recipe_total(src["dishes"], tuning["menu"])})
        self.gather_tpl = scenario.get("gather", {})
        self.quan_tpl = scenario.get("quan", {})
        self.day = 1
        self.days_completed = 0
        self.cur = None
        self.done = False
        self.reason = None

    @property
    def plan(self):
        return self.plans[(self.day - 1) % len(self.plans)]  # soak: D1–D5 lặp ở Ngày 6–10

    @property
    def phase(self):
        return self.cur.phase

    def initial_events(self):
        events = []
        self._start_day(events)
        return events

    def _start_day(self, events):
        self.active_upgrades = dict(self.upgrades)  # chỉ khi dựng Ngày mới mới sao cấp đã mua
        g = self.tuning["gather"]
        hp_max = upgrade_value(self.tuning, "hp", self.active_upgrades.get("hp", 0), g["hp_max"])
        oxy = upgrade_value(self.tuning, "oxygen", self.active_upgrades.get("oxygen", 0), g["oxygen_max_s"])
        events.append(("gather", self.day, "day_start", {}))
        events.append(("gather", self.day, "day_plan", {"dishes": self.plan["dishes"],
                                                        "ingredients": self.plan["ingredients"]}))
        tpl = copy.deepcopy(self.gather_tpl)
        if self.day > 1 and tpl.get("hold"):  # v1.2: Ngày kế cấp id mới theo thứ tự mảng, giữ kind/fresh ban đầu
            tpl["hold"] = [dict(it, id=self.ids.new("I")) for it in tpl["hold"]]
        self.cur = GatherSim(self.tuning, tpl, self.streams, self.ids, day=self.day,
                             hp_max=hp_max, oxygen_max_s=oxy, money=self.money, earned=self.earned,
                             reputation=self.reputation)
        events.append(("gather", self.day, "phase_start", {}))

    def step(self, inp):
        cur, day = self.cur, self.day
        events = [(cur.phase, day, name, data) for name, data in cur.step(inp)]
        if not cur.done:
            return events
        if cur.phase == "gather":
            self.cur = QuanSim(self.tuning, copy.deepcopy(self.quan_tpl), self.streams, self.ids,
                               inventory=cur.inventory_items(), dishes=list(self.plan["dishes"]),
                               money=self.money, earned=self.earned, reputation=self.reputation)
            events.append(("quan", day, "phase_start", {}))
        elif cur.phase == "quan":
            self.money, self.earned, self.reputation = cur.money, cur.earned, cur.reputation
            self.last_shift = {"shift_earned": cur.shift_earned}
            self.cur = ShopSim(self.tuning, cur.stock, self.upgrades, self.money, self.earned, self.reputation)
            events.append(("shop", day, "phase_start", {}))
        else:  # shop đóng: Ngày hoàn tất
            self.money = cur.money
            self.days_completed += 1
            if self.days_completed >= self.days:
                self.done, self.reason = True, "days_complete"
            else:
                self.day += 1
                self._start_day(events)
        return events

    def snapshot(self) -> dict:
        s = self.cur.snapshot()
        s.update({"day": self.day, "day_plan": {"dishes": self.plan["dishes"], "ingredients": self.plan["ingredients"]},
                  "upgrades": dict(sorted(self.upgrades.items())),
                  "active_upgrades": dict(sorted(self.active_upgrades.items()))})
        return s
