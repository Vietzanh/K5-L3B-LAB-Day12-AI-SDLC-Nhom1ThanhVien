"""Vòng tick (Contract B, mô hình tick) + pause (v1.1 mục 4.2) + nhiều pha (`day`).

Thứ tự ghi: [event tick 0 của day] -> snapshot tick 0 -> với mỗi bước: event (theo thứ tự xử lý) rồi snapshot
(nếu tới lượt hoặc lượt kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`tick` là số bước ngoài (luôn tăng); `sim_tick` chỉ tăng khi gameplay chạy (không tăng lúc pause);
`phase_tick` là đồng hồ của pha hiện tại (về 0 khi đổi pha).

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`).
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DayGame
from .sim.gather import GatherSim
from .sim.quan import QuanSim


class SingleGame:
    """Một pha chạy độc lập (`gather` hoặc `quan`): bọc sim cho cùng giao diện với DayGame."""

    def __init__(self, sim):
        self.cur = sim
        self.mode = sim.mode
        self.day = None

    @property
    def phase(self):
        return self.cur.phase

    @property
    def done(self):
        return self.cur.done

    @property
    def reason(self):
        return self.cur.reason

    def initial_events(self):
        return []

    def step(self, inp):
        return [(self.cur.phase, None, name, data) for name, data in self.cur.step(inp)]

    def snapshot(self):
        return self.cur.snapshot()


def build_game(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "day":
        return DayGame(tuning, scenario, streams, ids, days)
    if mode == "gather":
        return SingleGame(GatherSim(tuning, scenario, streams, ids))
    return SingleGame(QuanSim(tuning, scenario, streams, ids, inventory=inventory))


class Session:
    """Một lượt chơi: dựng game, bước từng tick (có pause), lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.game = build_game(mode, tuning, scenario, seed, inventory, days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False
        self.initial_rows = [self._row(*e) for e in self.game.initial_events()]

    @property
    def sim(self):
        """Sim của pha hiện tại."""
        return self.game.cur

    @property
    def done(self) -> bool:
        return self.game.done

    def _score(self, sim):
        return sim.earned + self.tuning["score"]["reputation_multiplier"] * math.floor(sim.reputation)

    def _row(self, phase, day, name, data):
        row = {"type": "event", "tick": self.tick, "phase": phase}
        if self.mode == "day":
            row["day"] = day
        row.update({"name": name, "data": data})
        return row

    def snapshot(self) -> dict:
        sim = self.sim
        state = "finished" if self.done else ("paused" if self.paused else "playing")
        s = {"type": "snapshot", "tick": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
             "phase": sim.phase, "phase_tick": sim.phase_tick, "state": state,
             "time_left_ticks": sim.time_left_ticks, "money": sim.money, "earned": sim.earned,
             "reputation": sim.reputation, "score": self._score(sim)}
        s.update(self.game.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        pre = []
        if inp.pressed("pause"):
            if not self.paused:  # vào pause: chỉ tăng tick ngoài, phát paused
                self.paused = True
                self.tick += 1
                return [self._row(self.sim.phase, self.game.day, "paused", {})]
            self.paused = False  # thoát pause: phát resumed rồi chạy gameplay ngay trong bước này
            pre.append((self.sim.phase, self.game.day, "resumed", {}))
        elif self.paused:  # còn pause: bỏ qua cạnh hành động và buy; đồng hồ/timer đứng yên
            self.tick += 1
            return []
        events = pre + self.game.step(inp)
        self.tick += 1
        self.sim_tick += 1
        return [self._row(*e) for e in events]

    def end_row(self) -> dict:
        sim = self.sim
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": self.mode,
               "state": "finished" if self.done else "playing",
               "reason": self.game.reason if self.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": self._score(sim)}
        if self.mode == "day":
            row["days_completed"] = self.game.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None,
        days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.initial_rows:  # day: day_start, day_plan, phase_start ở tick 0
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
