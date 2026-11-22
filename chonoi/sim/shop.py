"""Shop cuối Ngày (Ticket-02 mục 2 "Shop và nâng cấp", v1.1 mục 4.5 "Shop").

Mỗi bước: đồng hồ (phase_tick+1, còn lại −1) -> MỘT lệnh `buy` của frame (trước cạnh shop_done, kể cả bước cuối)
-> cạnh `shop_done` -> shop_end(done); hết max_ticks bước hoạt động -> shop_end(time).
Mua: trừ money (giữ earned/điểm), cấp vừa mua ghi vào `upgrades` (đã mua); hiệu lực từ Ngày kế (active_upgrades).
"""

from ..inventory import views_by_id

UPGRADE_FIELD = {"oxygen": "oxygen_max_s", "hp": "hp_max"}


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, tuning, stock, upgrades, money, earned, reputation):
        self.cfg = tuning["shop"]
        self.stock = [dict(it) for it in stock]  # v1.2: cá thể dư sau ca (không hao tươi trong Shop)
        self.upgrades = upgrades  # map dùng chung với DayGame (cấp đã mua)
        self.money = money
        self.earned = earned
        self.reputation = reputation
        self.time_left_ticks = int(self.cfg["max_ticks"])
        self.phase_tick = 0
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {"stock": views_by_id(self.stock)}

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        if inp.buy is not None:
            self._buy(inp.buy, events)
        if inp.pressed("shop_done"):
            self._finish("done", events)
        elif self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    def _buy(self, action, events):
        levels = self.cfg["upgrades"].get(action)
        if levels is None:
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        nxt = self.upgrades.get(action, 0) + 1
        if nxt > len(levels):
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = levels[nxt - 1]["price"]
        if self.money < price:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.money -= price
        self.upgrades[action] = nxt
        events.append(("bought", {"upgrade": action, "level": nxt, "price": price, "money": self.money}))

    def _finish(self, reason, events):
        self.done, self.reason = True, reason
        events.append(("shop_end", {"reason": reason}))


def upgrade_value(tuning, kind, level, base):
    """Giá trị có hiệu lực của nâng cấp `kind` ở `level` (0 = cơ sở)."""
    if level <= 0:
        return base
    return tuning["shop"]["upgrades"][kind][level - 1][UPGRADE_FIELD[kind]]
