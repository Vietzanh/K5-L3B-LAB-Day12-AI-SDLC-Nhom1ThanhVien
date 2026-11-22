"""Soak headless (Ticket-04 mục 2): python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày (gather → quan → shop) trong MỘT tiến trình, điều khiển bằng bot tất định (`Bot`): kế hoạch D1–D5 lặp
ở Ngày 6–10; tiền, tổng thu, uy tín, cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt.
Xuất soak.json: {days, days_completed, crashes, results[{day, earned, reputation, score}] tại lúc Shop đóng, duration_s}.
Đạt khi days_completed = days và crashes = 0. Các trường gameplay tất định theo seed; chỉ duration_s là số đo thật.
"""

import argparse
import json
import math
import sys
import time
import traceback

from .contract import load_contract
from .inputs import InputState
from .runner import Session

MAX_DAY_TICKS = 22_200 * 2  # an toàn: một Ngày không pause tối đa 22.200 tick


class Bot:
    """Bot tất định, chỉ đọc trạng thái sim (không RNG, không đồng hồ). Trả InputState mỗi bước."""

    def __init__(self, tuning):
        self.t = tuning
        self._held = set()

    def _press(self, name, want, edges, held):
        """Tạo cạnh lên: chỉ bấm nếu bước trước chưa giữ nút."""
        if want and name not in self._held:
            edges.add(name)
            held[name] = True
        else:
            held[name] = False

    def act(self, sess) -> InputState:
        sim, phase = sess.sim, sess.sim.phase
        move, want, buy = (0.0, 0.0), set(), None
        if phase == "gather":
            move, want = self._gather(sim, sess.game.plan["ingredients"])
        elif phase == "quan":
            move, want = self._quan(sim)
        else:
            buy, want = self._shop(sim)
        edges, held = set(), {}
        for b in ("interact", "catch", "shop_done"):
            self._press(b, b in want, edges, held)
        self._held = {b for b, v in held.items() if v}
        return InputState(move, held, edges, buy)

    @staticmethod
    def _toward(pos, target, slow_r=0.15):
        dx, dy = target[0] - pos[0], target[1] - pos[1]
        d = math.hypot(dx, dy)
        if d <= slow_r:
            return (0.0, 0.0)
        return (dx / d, dy / d)

    def _gather(self, sim, need):
        g = sim.t
        pos = sim.pos
        usable = {}
        for it in sim.hold:
            if it["u"] >= sim.spoil_u:
                usable[it["kind"]] = usable.get(it["kind"], 0) + 1
        missing = {k: n - usable.get(k, 0) for k, n in need.items() if n - usable.get(k, 0) > 0}
        dock = g["dock_pos"]
        travel = math.dist(pos, dock) / g["swim_speed"] * 60 + 240
        if not missing or sim._free() <= 0 or sim.time_left_ticks < travel:
            if math.dist(pos, dock) <= g["dock_radius"] - 0.5:
                return (0.0, 0.0), {"interact"}
            if pos[1] > g["surface_depth"]:
                return (0.0, -1.0), set()
            return self._toward(pos, dock), set()
        # oxy: dưới nước mà oxy không đủ để nổi lên an toàn -> nổi
        if pos[1] > g["surface_depth"]:
            need_ticks = pos[1] / g["swim_speed"] * 60 + 90
            if sim.oxygen_ticks < need_ticks:
                return (0.0, -1.0), set()
        elif sim.oxygen_ticks < sim.oxygen_max * 0.9:
            return (0.0, 0.0), set()  # ở mặt nước chờ hồi oxy
        targets = []
        for n in sim.nodes:
            if n["regrow_ticks"] == 0 and n["kind"] in missing:
                targets.append((math.dist(pos, n["pos"]), "node", n["id"], n["pos"]))
        for f in sim.fish:
            if f["kind"] in missing and f["pos"][1] <= 22 and \
                    all(math.dist(f["pos"], m["pos"]) > 9 for m in sim.monsters):
                y = int(g["fish_yield"][f["kind"]])
                if y <= sim._free():
                    targets.append((math.dist(pos, f["pos"]), "fish", f["id"], f["pos"]))
        if not targets:
            return self._toward(pos, dock), set()
        _, kind, _, tpos = min(targets, key=lambda x: (x[0], x[2]))
        if kind == "node":
            if pos[1] > g["surface_depth"]:
                return (0.0, -1.0), set()
            if math.dist(pos, tpos) <= g["interact_radius"] - 0.2:
                return (0.0, 0.0), {"interact"}
            return self._toward(pos, [tpos[0], 0.0]), set()
        if math.dist(pos, tpos) <= g["catch_radius"] - 0.3 and pos[1] > g["surface_depth"] and sim.catch_cd_ticks == 0:
            return (0.0, 0.0), {"catch"}
        return self._toward(pos, tpos), set()

    def _quan(self, sim):
        r = sim.t["interact_radius"] - 0.2
        pos = sim.pos
        if sim.hand is not None:
            c = next((c for c in sim.customers if c["id"] == sim.hand["order_id"]), None)
            if c is not None:
                tb = next(t for t in sim.tables if t["id"] == c["table_id"])
                if math.dist(pos, tb["pos"]) <= r:
                    return (0.0, 0.0), {"interact"}
                return self._toward(pos, tb["pos"]), set()
        ready = [s for s in sim.stoves if s["state"] == "ready"]
        if ready and sim.hand is None:
            s = min(ready, key=lambda s: (math.dist(pos, s["pos"]), s["id"]))
            if math.dist(pos, s["pos"]) <= r and self._nearest_is(sim, s):
                return (0.0, 0.0), {"interact"}
            return self._toward(pos, s["pos"]), set()
        if any(c["order_status"] == "reserved" for c in sim.customers):
            idle = [s for s in sim.stoves if s["state"] == "idle"]
            if idle:
                s = min(idle, key=lambda s: (math.dist(pos, s["pos"]), s["id"]))
                if math.dist(pos, s["pos"]) <= r and self._nearest_is(sim, s):
                    return (0.0, 0.0), {"interact"}
                return self._toward(pos, s["pos"]), set()
        return self._toward(pos, [3.5, 6.5]), set()

    @staticmethod
    def _nearest_is(sim, stove):
        d = math.dist(sim.pos, stove["pos"])
        return all(math.dist(sim.pos, o["pos"]) > d for o in sim.stoves if o is not stove)

    def _shop(self, sim):
        levels = sim.cfg["upgrades"]
        for kind in ("hp", "oxygen"):
            nxt = sim.upgrades.get(kind, 0)
            if nxt < len(levels[kind]) and sim.money >= levels[kind][nxt]["price"] + 100:
                return kind, set()  # giữ lại ít nhất 100k
        return None, {"shop_done"}


def run_soak(seed, days):
    tuning = load_contract()["tuning"]
    t0 = time.perf_counter()
    results, crashes, completed = [], 0, 0
    try:
        sess = Session("day", tuning, {}, seed, days=days)
        bot = Bot(tuning)
        limit = MAX_DAY_TICKS * days
        while not sess.done and sess.tick < limit:
            for row in sess.step(bot.act(sess)):
                if row["name"] == "shop_end":  # số liệu tại lúc Shop đóng của Ngày đó
                    g = sess.game
                    results.append({"day": row["day"], "earned": g.earned, "reputation": g.reputation,
                                    "score": g.earned + tuning["score"]["reputation_multiplier"] * math.floor(g.reputation)})
        completed = sess.game.days_completed
    except Exception:  # noqa: BLE001 — soak đếm crash thay vì dừng runner của lớp
        crashes += 1
        sys.stderr.write(traceback.format_exc())
    return {"days": days, "days_completed": completed, "crashes": crashes, "results": results,
            "duration_s": round(time.perf_counter() - t0, 3)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    try:
        a = p.parse_args(argv)
    except SystemExit:
        return 2
    if a.days < 1:
        sys.stderr.write("--days phải ≥ 1\n")
        return 2
    res = run_soak(a.seed, a.days)
    try:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    print(json.dumps({k: res[k] for k in ("days", "days_completed", "crashes", "duration_s")}))
    return 0 if res["crashes"] == 0 and res["days_completed"] == res["days"] else 1


if __name__ == "__main__":
    sys.exit(main())
