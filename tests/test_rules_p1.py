"""Test luật Phase 1 của nhóm (hộp đen qua headless_cmd). Mỗi test dựng fixture nhỏ cho đúng một biên của PRD-0 mục F.

Chạy: PYTHONPATH=tests:. python3 -m unittest discover -s tests -v   (trên Windows: qua WSL)
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def run_case(mode, block, inputs=None, ticks=10, seed=1, every=1, extra=()):
    """Chạy headless với scenario {mode: block}; trả (rows, file kho hoặc None)."""
    with Workdir() as w:
        args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("o.jsonl"),
                "--snapshot-every", str(every)]
        if block is not None:
            args += ["--scenario", write_json(w.path("sc.json"), {mode: block})]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        inv = None
        if mode == "gather":
            args += ["--inventory-out", w.path("inv.json")]
        code, err = run_headless(*args, *extra)
        if code != 0:
            raise AssertionError(f"headless thoát {code}: {err}")
        rows = read_jsonl(w.path("o.jsonl"))
        try:
            with open(w.path("inv.json"), encoding="utf-8") as f:
                inv = json.load(f)
        except OSError:
            pass
        return rows, inv


def names(rows):
    return [(r["tick"], r["name"]) for r in events(rows)]


def snap_at(rows, tick):
    return {r["tick"]: r for r in snapshots(rows)}[tick]


DEEP = {"player": {"pos": [50, 10]}, "nodes": [], "fish": []}


class GatherOxygen(unittest.TestCase):
    """Lát 1: oxy, ngạt, Máu, ngất, dive/surface."""

    def test_dive_and_surface_events(self):
        rows, _ = run_case("gather", {"player": {"pos": [20, 0]}, "fish": []},
                           [{"tick": 0, "move": [0, 1]}, {"tick": 30, "move": [0, -1]}], ticks=80)
        dv = events(rows, "dive")
        sf = events(rows, "surface")
        self.assertEqual(len(dv), 1)
        self.assertEqual(len(sf), 1)
        self.assertGreater(dv[0]["data"]["pos"][1], 0.5)
        self.assertLessEqual(sf[0]["data"]["pos"][1], 0.5)
        self.assertLess(dv[0]["tick"], sf[0]["tick"])

    def test_oxygen_drains_underwater_and_refills_at_surface(self):
        rows, _ = run_case("gather", dict(DEEP, player={"pos": [50, 10], "oxygen_ticks": 100}), ticks=5)
        self.assertEqual(snap_at(rows, 5)["player"]["oxygen_ticks"], 95)
        rows, _ = run_case("gather", {"player": {"pos": [50, 0], "oxygen_ticks": 1796}, "fish": []}, ticks=2)
        self.assertEqual(snap_at(rows, 1)["player"]["oxygen_ticks"], 1800, "mặt nước +6/tick, kẹp ở tối đa")

    def test_oxygen_empty_then_first_choke_at_t_plus_59(self):
        rows, _ = run_case("gather", dict(DEEP, player={"pos": [50, 10], "oxygen_ticks": 1}), ticks=130)
        self.assertEqual([e["tick"] for e in events(rows, "oxygen_empty")], [1])
        chokes = events(rows, "choke")
        self.assertEqual([e["tick"] for e in chokes], [60, 120])
        self.assertEqual([e["data"]["hp"] for e in chokes], [2, 1])
        self.assertEqual(snap_at(rows, 59)["player"]["zero_oxy_ticks"], 59)
        self.assertEqual(snap_at(rows, 60)["player"]["zero_oxy_ticks"], 0)

    def test_surfacing_on_choke_step_prevents_choke(self):
        block = {"player": {"pos": [50, 0.505], "vel": [0, -4], "oxygen_ticks": 0, "zero_oxy_ticks": 59},
                 "fish": []}
        rows, _ = run_case("gather", block, [{"tick": 0, "move": [0, -1]}], ticks=3)
        self.assertEqual(events(rows, "choke"), [])
        self.assertEqual(snap_at(rows, 1)["player"]["oxygen_ticks"], 6)
        self.assertEqual(snap_at(rows, 1)["player"]["zero_oxy_ticks"], 0)

    def test_faint_drops_hold_lifo_and_writes_empty_inventory(self):
        block = dict(DEEP, player={"pos": [50, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                     hold=["ca_loc", "bong_sung", "ca_linh"])
        rows, inv = run_case("gather", block, ticks=10)
        self.assertEqual(names(rows), [(1, "choke"), (1, "faint"), (1, "gather_end")])
        faint = events(rows, "faint")[0]["data"]
        self.assertEqual(faint, {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0})
        end = events(rows, "gather_end")[0]["data"]
        self.assertEqual(end, {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(inv, {"items": {}})
        self.assertEqual(rows[-1]["reason"], "fainted")


if __name__ == "__main__":
    unittest.main()
