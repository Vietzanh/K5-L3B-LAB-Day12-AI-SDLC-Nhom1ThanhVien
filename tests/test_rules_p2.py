"""Test luật Phase 2 (Ticket-02, Test Contract v1.1) — hộp đen qua headless_cmd."""

import json
import math
import time
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json
from test_rules_p1 import names, run_case, snap_at


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def run_day(scenario=None, inputs=None, ticks=10, days=None, every=10, seed=1):
    with Workdir() as w:
        args = ["--mode", "day", "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("o.jsonl"),
                "--snapshot-every", str(every)]
        if days is not None:
            args += ["--days", str(days)]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), scenario)]
        if inputs is not None:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        code, err = run_headless(*args)
        if code != 0:
            raise AssertionError(f"headless thoát {code}: {err}")
        return read_jsonl(w.path("o.jsonl"))


NO_FISH = {"random_fish": False, "fish": []}
# đi thẳng tới quán: cập bến ở tick 0; ca quán 1 tick
FAST = {"gather": dict(NO_FISH), "quan": {"time_left_ticks": 1}}


class Fish(unittest.TestCase):
    def test_initial_8_schools_on_distinct_spawn_points_deterministic(self):
        g = tuning()["gather"]
        a, _ = run_case("gather", None, ticks=0, seed=5)
        b, _ = run_case("gather", None, ticks=0, seed=5)
        fa = snapshots(a)[0]["fish"]
        self.assertEqual(fa, snapshots(b)[0]["fish"])
        self.assertEqual(len(fa), 8)
        pts = [tuple(f["pos"]) for f in fa]
        self.assertEqual(len(set(pts)), 8)
        for f in fa:
            self.assertIn(f["pos"][0], g["fish_spawn_x"])
            self.assertIn(f["pos"][1], g["fish_spawn_depths"][f["kind"]])

    def test_fish_swim_speed_and_depth_band(self):
        g = tuning()["gather"]
        fish = [{"id": "F1", "kind": "ca_loc", "pos": [50, 14], "heading_deg": 0}]
        rows, _ = run_case("gather", {"fish": fish}, ticks=60, every=60)
        f = snap_at(rows, 60)["fish"][0]
        self.assertAlmostEqual(f["pos"][0], 51.5, places=2)
        self.assertEqual(f["age_ticks"], 60)
        fish = [{"id": "F1", "kind": "ca_keo", "pos": [50, 27.99], "heading_deg": 90}]
        rows, _ = run_case("gather", {"fish": fish}, ticks=30, every=1)
        for s in snapshots(rows):
            lo, hi = g["fish_depths"]["ca_keo"]
            self.assertTrue(lo <= s["fish"][0]["pos"][1] <= hi)
        self.assertGreater(snap_at(rows, 30)["fish"][0]["heading_deg"], 180, "chạm đáy dải thì đảo hướng lên")

    def test_spawn_at_360_and_cap(self):
        rows, _ = run_case("gather", {"player": {"pos": [2, 0]}}, ticks=361, every=361)
        sp = events(rows, "fish_spawned")
        self.assertEqual([e["tick"] for e in sp], [360])
        self.assertEqual(sp[0]["data"]["id"], "F9")
        self.assertEqual(len(snapshots(rows)[-1]["fish"]), 9)

    def test_fixture_fish_still_when_random_off_and_ca_keo_yield_2(self):
        fish = [{"id": "F1", "kind": "ca_keo", "pos": [30, 24]}]
        rows, _ = run_case("gather", {"player": {"pos": [30, 23]}, "fish": fish, "random_fish": False},
                           [{"tick": 5, "catch": True}], ticks=6)
        self.assertEqual(snap_at(rows, 5)["fish"][0]["pos"], [30, 24])
        self.assertEqual(events(rows, "fish_caught")[0]["data"], {"fish_id": "F1", "kind": "ca_keo", "yield": 2})


def croc(pos, wps=None, **kw):
    m = {"id": "M1", "kind": "ca_sau", "pos": pos, "waypoints": wps or [pos, [pos[0] + 4, pos[1]]]}
    m.update(kw)
    return m


class Monsters(unittest.TestCase):
    def test_default_layout_day1_only_m1(self):
        rows, _ = run_case("gather", None, ticks=0)
        self.assertEqual([m["id"] for m in snapshots(rows)[0]["monsters"]], ["M1"])

    def test_patrol_1ms_to_waypoint(self):
        rows, _ = run_case("gather", dict(NO_FISH, monsters=[croc([60, 24])]), ticks=60, every=60)
        m = snap_at(rows, 60)["monsters"][0]
        self.assertAlmostEqual(m["pos"][0], 61.0, places=3)
        self.assertEqual((m["state"], m["target_idx"]), ("patrol", 1))

    def test_hit_loses_half_hold_lifo_invuln_recoil(self):
        block = dict(NO_FISH, player={"pos": [50, 20]}, monsters=[croc([50.5, 20])],
                     hold=["ca_loc", "bong_sung", "ca_linh", "ca_keo", "keo_neo"])
        rows, _ = run_case("gather", block, ticks=100, every=1)
        hits = events(rows, "monster_hit")
        # bất tử 90 đặt ở tick 1 -> bị chạm lại được từ tick 1 + 90 = 91 (cùng quy ước "cooldown L đặt ở t dùng lại từ t+L")
        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[1]["tick"], 91)
        self.assertEqual((hits[0]["tick"], hits[0]["data"]),
                         (1, {"monster_id": "M1", "hp": 2, "lost": ["keo_neo", "ca_keo"], "pos": [50, 20]}))
        s1 = snap_at(rows, 1)
        self.assertEqual((s1["player"]["invuln_ticks"], s1["hold"]), (90, ["ca_loc", "bong_sung", "ca_linh"]))
        m1 = s1["monsters"][0]
        self.assertEqual((m1["state"], m1["state_ticks_left"], m1["recoil_dir"]), ("recoil", 60, [1, 0]))
        self.assertAlmostEqual(snap_at(rows, 2)["monsters"][0]["pos"][0] - m1["pos"][0], 2 / 60, places=3)
        self.assertEqual(snap_at(rows, 61)["monsters"][0]["state"], "patrol")

    def test_no_chase_when_player_shallow(self):
        rows, _ = run_case("gather", dict(NO_FISH, player={"pos": [50, 9]}, monsters=[croc([50, 12])]), ticks=30)
        self.assertEqual(events(rows, "monster_hit"), [])
        self.assertEqual(snapshots(rows)[-1]["monsters"][0]["state"], "patrol")

    def test_monster_faint_drops_rest_and_ends(self):
        block = dict(NO_FISH, player={"pos": [50, 20], "hp": 1}, monsters=[croc([50.5, 20])],
                     hold=["ca_loc", "bong_sung", "ca_linh"])
        rows, inv = run_case("gather", block, ticks=5)
        self.assertEqual(names(rows), [(1, "monster_hit"), (1, "faint"), (1, "gather_end")])
        self.assertEqual(events(rows, "monster_hit")[0]["data"]["lost"], ["ca_linh"])
        self.assertEqual(events(rows, "faint")[0]["data"], {"cause": "monster", "lost": ["bong_sung", "ca_loc"], "hp": 0})
        self.assertEqual(inv, {"items": {}})


class QuanV11(unittest.TestCase):
    def test_two_stoves_four_tables_six_dishes(self):
        rows, _ = run_case("quan", None, ticks=0)
        s = snapshots(rows)[0]
        self.assertEqual([x["id"] for x in s["stoves"]], ["B1", "B2"])
        self.assertEqual([x["id"] for x in s["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual(len(tuning()["menu"]), 6)

    def test_customers_fill_tables_by_schedule(self):
        rows, _ = run_case("quan", {"stock": {"ca_loc": 10}}, ticks=2821, every=2821)
        arr = events(rows, "customer_arrived")
        self.assertEqual([(e["tick"], e["data"]["table_id"]) for e in arr],
                         [(120, "T1"), (1020, "T2"), (1920, "T3"), (2820, "T4")])


class Pause(unittest.TestCase):
    def test_pause_freezes_sim_and_resume_runs_same_step(self):
        inputs = [{"tick": 5, "pause": True}, {"tick": 6, "pause": False}, {"tick": 7, "interact": True},
                  {"tick": 10, "pause": True}]
        rows, _ = run_case("gather", dict(NO_FISH), inputs, ticks=12, every=1)
        self.assertEqual(names(rows), [(6, "paused"), (11, "resumed")])
        s8 = snap_at(rows, 8)
        self.assertEqual((s8["state"], s8["sim_tick"], s8["phase_tick"], s8["time_left_ticks"]),
                         ("paused", 5, 5, 10800 - 5))
        s11 = snap_at(rows, 11)
        self.assertEqual((s11["state"], s11["sim_tick"]), ("playing", 6))
        self.assertEqual(rows[-1]["sim_tick"], 7)
        self.assertEqual(rows[-1]["ticks"], 12)


class Day(unittest.TestCase):
    def test_day_start_events_and_phase_changes(self):
        sc = {"gather": dict(NO_FISH, hold=["ca_loc"])}
        inputs = [{"tick": 0, "interact": True}, {"tick": 10801, "shop_done": True}]
        rows = run_day(sc, inputs, ticks=20000, every=5000)
        first = [(r["tick"], r["phase"], r["day"], r["name"]) for r in rows[:3]]
        self.assertEqual(first, [(0, "gather", 1, "day_start"), (0, "gather", 1, "day_plan"),
                                 (0, "gather", 1, "phase_start")])
        self.assertEqual(rows[1]["data"], {"dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
                                           "ingredients": {"bong_sung": 6, "ca_loc": 3}})
        self.assertEqual(rows[3]["type"], "snapshot")
        ev = [(e["tick"], e["phase"], e["name"]) for e in events(rows) if e["name"] in
              ("gather_end", "phase_start", "quan_end", "shop_end")]
        self.assertEqual(ev, [(0, "gather", "phase_start"), (1, "gather", "gather_end"), (1, "quan", "phase_start"),
                              (10801, "quan", "quan_end"), (10801, "shop", "phase_start"), (10802, "shop", "shop_end")])
        end = rows[-1]
        self.assertEqual((end["reason"], end["days_completed"], end["ticks"]), ("days_complete", 1, 10802))
        # quán trong day chỉ phục vụ món của kế hoạch D1
        for e in events(rows, "customer_arrived"):
            self.assertIn(e["data"]["dish_id"], ("ca_loc_nuong_trui", "goi_bong_sung"))

    def test_shop_buy_applies_next_day(self):
        sc = dict(FAST, day={"money": 300, "earned": 300})
        inputs = [{"tick": 0, "interact": True}, {"tick": 2, "buy": "hp", "shop_done": True}]
        rows = run_day(sc, inputs, ticks=3, days=2, every=1)
        b = events(rows, "bought")[0]
        self.assertEqual((b["tick"], b["day"], b["data"]), (3, 1, {"upgrade": "hp", "level": 1, "price": 250, "money": 50}))
        self.assertEqual([e["name"] for e in events(rows) if e["tick"] == 3],
                         ["bought", "shop_end", "day_start", "day_plan", "phase_start"])
        s = snap_at(rows, 3)
        self.assertEqual((s["day"], s["phase"], s["phase_tick"]), (2, "gather", 0))
        self.assertEqual((s["upgrades"], s["active_upgrades"], s["player"]["hp_max"], s["player"]["hp"]),
                         ({"hp": 1}, {"hp": 1}, 4, 4))
        self.assertEqual((s["money"], s["earned"], s["score"]), (50, 300, 600))
        s2 = snap_at(rows, 2)
        self.assertEqual((s2["phase"], s2["upgrades"], s2["active_upgrades"]), ("shop", {}, {}))

    def test_buy_failed_reasons(self):
        cases = [({}, "oxygen", "funds"), ({"money": 1000, "earned": 1000, "upgrades": {"oxygen": 2}}, "oxygen", "max_level"),
                 ({}, "weapon", "unknown")]
        for day, action, reason in cases:
            sc = dict(FAST, day=day)
            rows = run_day(sc, [{"tick": 0, "interact": True}, {"tick": 2, "buy": action}], ticks=3)
            self.assertEqual(events(rows, "buy_failed")[0]["data"], {"action": action, "reason": reason})

    def test_shop_auto_closes_after_600_ticks(self):
        rows = run_day(FAST, [{"tick": 0, "interact": True}], ticks=1000)
        end = events(rows, "shop_end")[0]
        self.assertEqual((end["tick"], end["data"]), (602, {"reason": "time"}))

    def test_one_day_runs_fast(self):
        t0 = time.time()
        rows = run_day(None, None, ticks=22200)
        self.assertEqual(rows[-1]["reason"], "days_complete")
        self.assertEqual(rows[-1]["ticks"], 22200)
        self.assertLess(time.time() - t0, 20)

    def test_day_scenario_errors_exit_2(self):
        bad = [{"quan": {"stock": {"ca_loc": 1}}}, {"quan": {"reputation": 4}}, {"day": {"money": 10}},
               {"day": {"money": 10, "earned": 5}}, {"day": {"upgrades": {"hp": 3}}},
               {"day": {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {"ca_loc": 2}}]}},
               {"river": {}}]
        with Workdir() as w:
            for sc in bad:
                p = write_json(w.path("sc.json"), sc)
                code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--scenario", p,
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, sc)
            for args in (["--mode", "gather", "--days", "2"], ["--mode", "day", "--days", "6"],
                         ["--mode", "day", "--days", "0"]):
                code, _ = run_headless(*args, "--seed", "1", "--ticks", "0", "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, args)

    def test_day_plan_override_recomputes_ingredients(self):
        sc = {"day": {"day_plan": [{"day": 1, "dishes": {"lau_mam": 1}}]}}
        rows = run_day(sc, None, ticks=0)
        self.assertEqual(rows[1]["data"]["ingredients"],
                         {"bong_dien_dien": 1, "ca_keo": 1, "ca_linh": 2, "keo_neo": 1})


if __name__ == "__main__":
    unittest.main()
