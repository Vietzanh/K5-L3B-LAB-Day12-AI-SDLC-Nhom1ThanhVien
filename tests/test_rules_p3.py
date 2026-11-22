"""Test luật Phase 3 (Ticket-03 "Mùa Nước Nổi", Test Contract v1.2) — độ tươi, kho cá thể. Hộp đen qua headless_cmd."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json
from test_rules_p1 import cust, inv_counts, items, kinds, names, run_case, snap_at  # noqa: F401
from test_rules_p2 import run_day

NO_WORLD = {"random_fish": False, "fish": [], "monsters": []}


class GatherFreshness(unittest.TestCase):
    def test_threshold_fixture_from_ticket_spoils_on_first_step_once(self):
        """Đúng scenario mẫu của Ticket-03: cá thể bắt đầu fresh 30 -> ươn ở bước đầu, phát một lần."""
        block = {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}
        rows, _ = run_case("gather", block, ticks=1)
        self.assertEqual(events(rows, "spoiled"), [{"type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
                                                    "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}])
        rows, _ = run_case("gather", block, ticks=50)
        self.assertEqual(len(events(rows, "spoiled")), 1)
        self.assertEqual(len(snapshots(rows)[-1]["hold"]), 1, "hàng ươn vẫn chiếm ô")

    def test_hold_decays_half_point_per_second(self):
        rows, _ = run_case("gather", dict(NO_WORLD, hold=items("ca_loc", "bong_sung", fresh=97.5)), ticks=60, every=60)
        self.assertEqual([x["fresh"] for x in snap_at(rows, 60)["hold"]], [97.0, 97.0])

    def test_new_item_fresh_100_and_spoiled_events_by_id(self):
        block = dict(NO_WORLD, player={"pos": [20, 0]}, nodes=[{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}],
                     hold=[{"id": "I7", "kind": "ca_loc", "fresh": 30}, {"id": "I3", "kind": "ca_linh", "fresh": 30}])
        rows, _ = run_case("gather", block, [{"tick": 0, "interact": True}], ticks=2)
        sp = [e["data"]["item_id"] for e in events(rows, "spoiled")]
        self.assertEqual(sp, ["I3", "I7"], "nhiều cá thể cùng vượt ngưỡng: phát theo id")
        h = snap_at(rows, 1)["hold"]
        self.assertEqual(h[-1], {"id": "I8", "kind": "bong_sung", "fresh": 100}, "id mới nối sau I7; hàng mới fresh 100")
        self.assertEqual(snap_at(rows, 2)["hold"][-1]["fresh"], (24000 - 2) / 240)


class InventoryFile(unittest.TestCase):
    def test_handover_smoke_exact_ids_and_freshness(self):
        """Smoke bàn giao của Ticket-03: fresh 100, cập bến frame 0 -> quan --inventory --ticks 0 khớp chính xác."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                                                           "random_fish": False, "monsters": []}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("catch.json")
            code, err = run_headless("--mode", "gather", "--seed", "42", "--scenario", sc, "--inputs", inp, "--ticks", "1",
                                     "--out", w.path("g.jsonl"), "--inventory-out", inv)
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved, {"items": [{"id": "I1", "kind": "ca_linh", "fresh": (24000 - 2) / 240}]})
            end = events(read_jsonl(w.path("g.jsonl")), "gather_end")[0]["data"]
            self.assertEqual(end["inventory"], saved)
            code, err = run_headless("--mode", "quan", "--seed", "42", "--inventory", inv, "--ticks", "0",
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], saved["items"])

    def test_inventory_sorted_by_id_and_spoiled_kept(self):
        block = dict(NO_WORLD, hold=[{"id": "I10", "kind": "ca_loc", "fresh": 20}, {"id": "I2", "kind": "ca_keo", "fresh": 50}],
                     time_left_ticks=1)
        _, inv = run_case("gather", block, ticks=3)
        self.assertEqual([x["id"] for x in inv["items"]], ["I2", "I10"])
        self.assertEqual(inv["items"][1]["fresh"], (20 * 240 - 2) / 240, "hàng ươn vẫn bàn giao")

    def test_bad_inventory_files_exit_2(self):
        bad = [{"items": {"ca_loc": 1}},                                              # kho đếm (v1.0/v1.1)
               {"items": [{"id": "I1", "kind": "ca_loc"}]},                           # thiếu fresh
               {"items": [{"id": "I1", "kind": "ca_lang", "fresh": 50}]},             # kind lạ
               {"items": items("ca_loc") + items("ca_linh")},                         # id trùng
               {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100.01}]},          # fresh ngoài miền
               {"items": [{"id": "", "kind": "ca_loc", "fresh": 50}]}]                # id rỗng
        with Workdir() as w:
            for b in bad:
                p = write_json(w.path("inv.json"), b)
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p,
                                       "--out", w.path("q.jsonl"))
                self.assertEqual(code, 2, b)
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory",
                                          write_json(w.path("ok.json"), {"items": []}), "--out", w.path("q.jsonl"))[0], 0)


class QuanFreshness(unittest.TestCase):
    def test_stock_decays_quarter_point_per_second_including_reserved(self):
        block = {"stock": items("ca_loc", "bong_sung"), "customers": [cust()], "random_customers": False}
        rows, _ = run_case("quan", block, ticks=240, every=240)
        self.assertEqual([x["fresh"] for x in snap_at(rows, 240)["stock"]], [99.0, 99.0])

    def test_reserve_freshest_tie_by_id(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 50}, {"id": "I3", "kind": "ca_loc", "fresh": 90},
                 {"id": "I2", "kind": "ca_loc", "fresh": 90}]
        rows, _ = run_case("quan", {"stock": stock}, ticks=121, every=121)
        self.assertEqual(snap_at(rows, 121)["customers"][0]["reserved"], ["I2"])

    def test_spoiled_items_not_cookable(self):
        rows, _ = run_case("quan", {"stock": items("ca_loc", fresh=29)}, ticks=121, every=121)
        self.assertEqual([e["name"] for e in events(rows)], ["no_dish"])

    def test_reserved_item_spoils_then_rereserve(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 30}, {"id": "I2", "kind": "ca_loc", "fresh": 80}]
        rows, _ = run_case("quan", {"stock": stock, "customers": [cust(reserved=["I1"])]}, ticks=1)
        self.assertEqual([(e["tick"], e["name"], e["data"]) for e in events(rows)],
                         [(1, "spoiled", {"item_id": "I1", "kind": "ca_loc", "location": "stock"})])
        c = snap_at(rows, 1)["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("reserved", ["I2"]))

    def test_reserved_item_spoils_without_replacement_unfulfillable(self):
        rows, _ = run_case("quan", {"stock": items("ca_loc", fresh=30), "customers": [cust(patience_ticks_left=5)]},
                           ticks=6)
        c = snap_at(rows, 1)["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"], c["state"]), ("unfulfillable", [], "waiting"))
        self.assertEqual([e["data"]["reason"] for e in events(rows, "customer_left")], ["patience"], "khách chờ tới hạn")

    def test_price_by_average_freshness_and_tip_on_locked_price(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 80}, {"id": "I2", "kind": "bong_dien_dien", "fresh": 60}]
        block = {"player": {"pos": [2, 8]}, "stock": stock, "customers": [cust(dish_id="canh_chua_ca_loc")]}
        rows, _ = run_case("quan", block, [{"tick": 0, "interact": True}], ticks=1)
        cs = events(rows, "cook_started")[0]["data"]
        # sau 1 bước hao: u = 19199 và 14399 -> floor(90 × 33598 / (2 × 240 × 100)) = floor(62.996) = 62
        self.assertEqual(cs["base_price"], 62)
        self.assertEqual([(x["kind"], x["id"]) for x in cs["items"]], [("bong_dien_dien", "I2"), ("ca_loc", "I1")])
        dish = {"order_id": "C1", "dish_id": "canh_chua_ca_loc", "base_price": 62}
        rows, _ = run_case("quan", {"player": {"pos": [9, 2]}, "hand": dish,
                                    "customers": [cust(dish_id="canh_chua_ca_loc", order_status="assigned")]},
                           [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(events(rows, "served")[0]["data"]["tip"], 12, "boa floor(62 × 0.2) trên giá đã chốt")

    def test_scenario_reserved_must_be_ids(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": items("ca_loc"), "customers": [cust(reserved={"ca_loc": 1})]}})
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc,
                                          "--out", w.path("o.jsonl"))[0], 2)


class DayFreshness(unittest.TestCase):
    def test_handover_same_tick_and_ids_continue_across_days(self):
        sc = {"gather": dict(NO_WORLD, hold=items("ca_loc", "bong_sung", fresh=100)), "quan": {"time_left_ticks": 1}}
        inputs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}, {"tick": 2, "shop_done": True},
                  {"tick": 3, "interact": True}]
        rows = run_day(sc, inputs, ticks=4, days=2, every=1)
        g_end = [e for e in events(rows, "gather_end")]
        self.assertEqual([x["id"] for x in g_end[0]["data"]["inventory"]["items"]], ["I1", "I2"])
        q0 = snap_at(rows, 1)
        self.assertEqual((q0["phase"], q0["stock"]), ("quan", g_end[0]["data"]["inventory"]["items"]),
                         "bàn giao cùng tick, không hao thêm")
        d2 = snap_at(rows, 3)
        self.assertEqual((d2["day"], [x["id"] for x in d2["hold"]], [x["fresh"] for x in d2["hold"]]),
                         (2, ["I3", "I4"], [100, 100]), "Ngày kế cấp id mới theo thứ tự mẫu, giữ fresh ban đầu")
        self.assertEqual(snap_at(rows, 2)["phase"], "shop")
        self.assertEqual([x["id"] for x in snap_at(rows, 2)["stock"]], ["I1", "I2"], "kho dư ở Shop là cá thể")


if __name__ == "__main__":
    unittest.main()
