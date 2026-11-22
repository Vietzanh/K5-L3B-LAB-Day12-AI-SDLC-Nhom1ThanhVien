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


PRESS_INTERACT = [{"tick": 0, "interact": True}]


class GatherHarvestCatch(unittest.TestCase):
    """Lát 2: hái, bắt cá, cập bến, ghi kho."""

    def test_harvest_exactly_at_radius_edge_sets_regrow(self):
        block = {"player": {"pos": [20, 0]}, "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [22, 0]}],
                 "fish": []}
        rows, _ = run_case("gather", block, PRESS_INTERACT, ticks=2)
        self.assertEqual(events(rows, "gather")[0], {"type": "event", "tick": 1, "phase": "gather", "name": "gather",
                                                     "data": {"node_id": "N1", "kind": "bong_dien_dien", "amount": 1}})
        s = snap_at(rows, 1)
        self.assertEqual(s["hold"], ["bong_dien_dien"])
        self.assertEqual(s["nodes"][0]["regrow_ticks"], 1200)
        self.assertFalse(s["nodes"][0]["ready"])

    def test_node_regrown_after_1200_ticks_and_harvest_again(self):
        block = {"player": {"pos": [20, 0]}, "fish": [],
                 "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0], "regrow_ticks": 3}]}
        rows, _ = run_case("gather", block, [{"tick": 1, "interact": True}], ticks=6)
        self.assertEqual([e["tick"] for e in events(rows, "node_regrown")], [3])
        self.assertEqual(events(rows, "gather"), [], "bước 1 nút còn regrow 1: chưa hái được")
        rows, _ = run_case("gather", block, [{"tick": 2, "interact": True}], ticks=6)
        self.assertEqual(names(rows), [(3, "node_regrown"), (3, "gather")], "mọc lại rồi hái ngay cùng bước")

    def test_no_harvest_underwater_and_hold_full(self):
        node = [{"id": "N1", "kind": "bong_sung", "pos": [22, 0]}]
        rows, _ = run_case("gather", {"player": {"pos": [22, 1]}, "nodes": node, "fish": []}, PRESS_INTERACT, ticks=2)
        self.assertEqual(events(rows), [])
        rows, _ = run_case("gather", {"player": {"pos": [22, 0]}, "nodes": node, "fish": [], "hold": ["ca_loc"] * 12},
                           PRESS_INTERACT, ticks=2)
        self.assertEqual([e["data"] for e in events(rows)],
                         [{"action": "gather", "node_id": "N1", "required": 1, "free": 0}])
        self.assertEqual(snap_at(rows, 1)["nodes"][0]["regrow_ticks"], 0)

    def test_catch_nearest_tie_by_id_and_cooldown(self):
        fish = [{"id": "F10", "kind": "ca_linh", "pos": [31, 10]}, {"id": "F2", "kind": "ca_loc", "pos": [29, 10]},
                {"id": "F3", "kind": "ca_loc", "pos": [30, 11.5]}]
        inputs = [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": 28, "catch": True},
                  {"tick": 29, "catch": False}, {"tick": 30, "catch": True}]
        rows, _ = run_case("gather", {"player": {"pos": [30, 10]}, "fish": fish}, inputs, ticks=32)
        caught = events(rows, "fish_caught")
        # F2 và F10 cùng cách 1 m -> F2 (id nhỏ, F2 < F10); tick 28 còn hồi chiêu; tick 30 bắt F10
        self.assertEqual([(e["tick"], e["data"]["fish_id"]) for e in caught], [(1, "F2"), (31, "F10")])
        self.assertEqual(caught[0]["data"], {"fish_id": "F2", "kind": "ca_loc", "yield": 1})
        self.assertEqual(snap_at(rows, 1)["player"]["catch_cd_ticks"], 30)

    def test_catch_not_at_surface_and_hold_full_keeps_school(self):
        fish = [{"id": "F1", "kind": "ca_linh", "pos": [30, 1]}]
        rows, _ = run_case("gather", {"player": {"pos": [30, 0]}, "fish": fish}, [{"tick": 0, "catch": True}], ticks=2)
        self.assertEqual(events(rows), [])
        rows, _ = run_case("gather", {"player": {"pos": [30, 1]}, "fish": fish, "hold": ["ca_loc"] * 10},
                           [{"tick": 0, "catch": True}], ticks=2)
        self.assertEqual([e["data"] for e in events(rows)],
                         [{"action": "catch", "fish_id": "F1", "required": 3, "free": 2}])
        s = snap_at(rows, 1)
        self.assertEqual(len(s["fish"]), 1)
        self.assertEqual(s["player"]["catch_cd_ticks"], 0)

    def test_catch_yield_ca_linh_3(self):
        rows, inv = run_case("gather", {"player": {"pos": [30, 5], "oxygen_ticks": 5},
                                        "fish": [{"id": "F1", "kind": "ca_linh", "pos": [31, 5]}], "time_left_ticks": 2},
                             [{"tick": 0, "catch": True}], ticks=5)
        self.assertEqual(snap_at(rows, 1)["hold"], ["ca_linh"] * 3)
        self.assertEqual(inv, {"items": {"ca_linh": 3}})

    def test_dock_has_priority_over_harvest(self):
        block = {"player": {"pos": [4, 0]}, "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [5, 0]}], "fish": []}
        rows, inv = run_case("gather", block, PRESS_INTERACT, ticks=3)
        self.assertEqual(names(rows), [(1, "gather_end")])
        self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
        self.assertEqual(inv, {"items": {}})

    def test_harvest_on_last_step_goes_into_inventory(self):
        block = {"player": {"pos": [20, 0]}, "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}],
                 "fish": [], "time_left_ticks": 1, "hold": ["ca_loc"]}
        rows, inv = run_case("gather", block, PRESS_INTERACT, ticks=5)
        self.assertEqual(names(rows), [(1, "gather"), (1, "gather_end")])
        self.assertEqual(inv, {"items": {"bong_sung": 1, "ca_loc": 1}})
        self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], inv)

STOVE = [2, 8]
TABLE = [9, 2]


def cust(**kw):
    c = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
    c.update(kw)
    return c


class QuanCustomers(unittest.TestCase):
    """Lát 3: khách theo lịch, chọn món đủ nguyên liệu, giữ chỗ, kiên nhẫn, no_dish."""

    def test_first_customer_at_tick_120_reserves_recipe(self):
        rows, _ = run_case("quan", {"stock": {"ca_loc": 1}}, ticks=121, every=10)
        arr = events(rows, "customer_arrived")
        self.assertEqual([(e["tick"], e["data"]) for e in arr],
                         [(120, {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})])
        c = snap_at(rows, 120)["customers"][0]
        self.assertEqual((c["order_tick"], c["patience_ticks_left"], c["reserved"], c["order_status"]),
                         (120, 3600, {"ca_loc": 1}, "reserved"))
        self.assertEqual(snap_at(rows, 121)["customers"][0]["patience_ticks_left"], 3599, "giảm từ bước sau")
        self.assertEqual(snap_at(rows, 120)["tables"][0]["customer_id"], "C1")

    def test_no_dish_when_stock_short(self):
        rows, _ = run_case("quan", {"stock": {"bong_sung": 1}}, ticks=121, every=60)
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows)], [(120, {})])
        self.assertEqual(events(rows)[0]["name"], "no_dish")

    def test_no_table_skips_turn(self):
        block = {"stock": {"ca_loc": 2}, "customers": [cust(order_tick=0)]}
        rows, _ = run_case("quan", block, ticks=121, every=60)
        self.assertEqual(events(rows), [])

    def test_patience_zero_leaves_and_lowers_reputation(self):
        block = {"stock": {"ca_loc": 1}, "customers": [cust(patience_ticks_left=2)]}
        rows, _ = run_case("quan", block, ticks=4)
        left = events(rows, "customer_left")
        self.assertEqual([(e["tick"], e["data"]) for e in left],
                         [(2, {"order_id": "C1", "table_id": "T1", "reason": "patience", "reputation": 2.5})])
        self.assertEqual(snap_at(rows, 2)["customers"], [])
        self.assertEqual(snap_at(rows, 2)["stock"], {"ca_loc": 1}, "nhả phần giữ, tồn vật lý giữ nguyên")

    def test_default_reserved_by_order_tick_then_table(self):
        block = {"stock": {"ca_loc": 1}, "customers": [cust(id="C1", table_id="T1", order_tick=5)]}
        rows, _ = run_case("quan", block, ticks=0)
        self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"], {"ca_loc": 1})


class QuanService(unittest.TestCase):
    """Lát 4: bếp, bưng, phục vụ, tiền, boa, uy tín, đóng ca."""

    def test_cook_pick_serve_pay_full_flow(self):
        block = {"player": {"pos": STOVE}, "stock": {"ca_loc": 1}, "customers": [cust()]}
        rows, _ = run_case("quan", block, [{"tick": 0, "interact": True}], ticks=2)
        cs = events(rows, "cook_started")[0]
        self.assertEqual((cs["tick"], cs["data"]), (1, {"stove_id": "B1", "order_id": "C1",
                                                         "dish_id": "ca_loc_nuong_trui", "items": ["ca_loc"],
                                                         "base_price": 60}))
        s = snap_at(rows, 1)
        self.assertEqual(s["stock"], {})
        self.assertEqual(s["stoves"][0]["cook_ticks_left"], 360)
        self.assertEqual(s["customers"][0]["order_status"], "assigned")

    def test_dish_ready_and_pick(self):
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        block = {"player": {"pos": STOVE}, "customers": [cust(order_status="assigned")],
                 "stoves": [{"id": "B1", "state": "cooking", "dish": dish, "cook_ticks_left": 2}]}
        rows, _ = run_case("quan", block, [{"tick": 3, "interact": True}], ticks=5)
        self.assertEqual(names(rows), [(2, "dish_ready"), (4, "dish_picked")])
        s = snap_at(rows, 3)
        self.assertEqual((s["stoves"][0]["state"], s["stoves"][0]["ready_ticks"]), ("ready", 1))
        s = snap_at(rows, 4)
        self.assertEqual(s["hand"], dish)
        self.assertEqual(s["stoves"][0]["state"], "idle")

    def _serve(self, patience):
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        block = {"player": {"pos": TABLE}, "hand": dish,
                 "customers": [cust(order_status="assigned", patience_ticks_left=patience)]}
        rows, _ = run_case("quan", block, [{"tick": 0, "interact": True}], ticks=602, every=601)
        return rows

    def test_serve_with_tip_then_paid_after_eating(self):
        rows = self._serve(1801)  # sau bước 1 còn 1800 = 50% -> có boa
        sv = events(rows, "served")[0]
        self.assertEqual((sv["tick"], sv["data"]), (1, {"order_id": "C1", "table_id": "T1",
                                                         "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 1800,
                                                         "base_price": 60, "tip": 12}))
        pd = events(rows, "paid")[0]
        self.assertEqual((pd["tick"], pd["data"]), (601, {"order_id": "C1", "table_id": "T1", "base_price": 60,
                                                           "tip": 12, "amount": 72, "reason": "finished_eating"}))
        s = snap_at(rows, 601)
        self.assertEqual((s["money"], s["earned"], s["reputation"], s["score"]), (72, 72, 3.2, 372))

    def test_serve_below_half_patience_no_tip(self):
        rows = self._serve(1800)  # sau bước 1 còn 1799 < 50%
        self.assertEqual(events(rows, "served")[0]["data"]["tip"], 0)
        self.assertEqual(snap_at(rows, 601)["reputation"], 3.0)

    def test_serve_on_tick_patience_hits_zero_is_valid(self):
        rows = self._serve(1)
        self.assertEqual(names(rows)[0], (1, "served"))
        self.assertEqual(events(rows, "customer_left"), [])

    def test_stove_before_table_on_tie(self):
        block = {"player": {"pos": [5, 5]}, "stock": {"ca_loc": 1}, "customers": [cust()],
                 "stoves": [{"id": "B1", "pos": [5, 6]}], "tables": [{"id": "T1", "pos": [5, 4]}]}
        rows, _ = run_case("quan", block, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(names(rows), [(1, "cook_started")])

    def test_closing_pays_eaters_and_releases_waiters_without_penalty(self):
        block = {"time_left_ticks": 1, "stock": {"ca_loc": 1},
                 "customers": [cust(id="C1", table_id="T1"),
                               cust(id="C2", table_id="T2", state="eating", order_status="served",
                                    eat_ticks_left=300, base_price=60, tip=12, reserved={})],
                 "tables": [{"id": "T1"}]}
        with self.assertRaises(AssertionError):  # T2 chưa có trong preset v1.0 -> mã 2
            run_case("quan", block, ticks=1)
        block["customers"][1]["table_id"] = "T1"
        block["customers"][0]["table_id"] = "T1"
        block["customers"] = [block["customers"][1]]
        rows, _ = run_case("quan", block, ticks=3)
        self.assertEqual(names(rows), [(1, "paid"), (1, "quan_end")])
        self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")
        self.assertEqual(events(rows, "quan_end")[0]["data"], {"reason": "time", "money": 72, "earned": 72,
                                                               "shift_earned": 72, "reputation": 3.2})
        self.assertEqual(rows[-1]["score"], 372)

    def test_closing_waiter_leaves_without_reputation_loss(self):
        rows, _ = run_case("quan", {"time_left_ticks": 1, "stock": {"ca_loc": 1}, "customers": [cust()]}, ticks=3)
        self.assertEqual([e["data"]["reason"] for e in events(rows, "customer_left")], ["closing"])
        self.assertEqual(rows[-1]["reputation"], 3.0)

    def test_leaving_customer_discards_dish_in_hand(self):
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        rows, _ = run_case("quan", {"hand": dish, "customers": [cust(order_status="assigned", patience_ticks_left=1)]},
                           ticks=2)
        self.assertEqual(snap_at(rows, 1)["hand"], None)


class QuanFixtureErrors(unittest.TestCase):
    def _code(self, block):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": block})
            return run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                "--out", w.path("o.jsonl"))[0]

    def test_contradictions_exit_2(self):
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        bad = [
            {"stock": {}, "customers": [cust()]},                                         # giữ quá tồn
            {"stock": {"ca_loc": 2}, "customers": [cust(reserved={"ca_loc": 2})]},         # giữ khác công thức
            {"customers": [cust(order_status="assigned")]},                                # assigned thiếu món
            {"hand": dish, "customers": [cust(order_status="assigned")],
             "stoves": [{"id": "B1", "state": "ready", "dish": dish}]},                    # bếp và tay cùng đơn
            {"customers": [cust(state="eating", order_status="served", eat_ticks_left=5)]},  # thiếu base_price/tip
            {"stock": {"ca_loc": 1}, "customers": [cust(dish_id="pho_bo")]},               # món ngoài phạm vi
            {"stoves": [{"id": "B1", "state": "cooking"}]},                                 # cooking thiếu món/timer
            {"hand": dish},                                                                 # món không có khách
            {"stock": {"ca_loc": -1}},
            {"customers": [cust(patience_ticks_left=-1)]},
        ]
        for b in bad:
            self.assertEqual(self._code(b), 2, b)

    def test_valid_fixture_exit_0(self):
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        ok = {"stock": {"ca_loc": 1}, "hand": dish, "customers": [cust(order_status="assigned")]}
        self.assertEqual(self._code(ok), 0)


if __name__ == "__main__":
    unittest.main()
