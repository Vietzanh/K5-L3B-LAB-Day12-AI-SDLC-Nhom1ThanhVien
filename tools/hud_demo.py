"""Dựng một cảnh có sẵn trong cửa sổ chơi để chụp HUD làm bằng chứng (không dùng khi chấm).

    python3 tools/hud_demo.py --scene gather|quan|shop|menu [--port 8765] [--seconds 25]

Mở máy chủ `chonoi.live` với fixture dựng sẵn, chạy trong `--seconds` giây rồi tự tắt.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chonoi.contract import load_contract  # noqa: E402
from chonoi.inputs import InputState  # noqa: E402
from chonoi.live import LiveGame, LiveServer  # noqa: E402

DISH = {"order_id": "C2", "dish_id": "goi_bong_sung", "base_price": 40}
SCENES = {
    # lặn sâu gần Cá Sấu M1, oxy thấp, giỏ có hàng -> cảnh báo "Thủy quái!" + oxy nhấp nháy
    "gather": ("day", {"gather": {"player": {"pos": [55, 21], "oxygen_ticks": 300},
                                  "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 95}, {"id": "I2", "kind": "bong_sung", "fresh": 31},
                                           {"id": "I3", "kind": "bong_sung", "fresh": 28}, {"id": "I4", "kind": "ca_linh", "fresh": 70}]}}),
    # quán: một khách sắp giận, một bếp đang nấu, khách đang ăn
    "quan": ("quan", {"player": {"pos": [6, 6]},
                      "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 92}, {"id": "I2", "kind": "ca_loc", "fresh": 40},
                                {"id": "I3", "kind": "ca_loc", "fresh": 25}, {"id": "I4", "kind": "bong_sung", "fresh": 88},
                                {"id": "I5", "kind": "bong_sung", "fresh": 86}, {"id": "I6", "kind": "ca_keo", "fresh": 31},
                                {"id": "I7", "kind": "ca_keo", "fresh": 60}],
                      "customers": [
                          {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "patience_ticks_left": 700},
                          {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "order_status": "assigned"},
                          {"id": "C3", "table_id": "T3", "dish_id": "ca_loc_nuong_trui", "state": "eating",
                           "order_status": "served", "eat_ticks_left": 400, "base_price": 60, "tip": 12}],
                      "stoves": [{"id": "B1", "state": "cooking", "dish": DISH, "cook_ticks_left": 120}]}),
    "shop": ("day", {"day": {"money": 320, "earned": 320}, "gather": {"random_fish": False},
                     "quan": {"time_left_ticks": 1}}),
    "menu": ("day", {}),
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scene", choices=sorted(SCENES), required=True)
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--seconds", type=float, default=25)
    a = p.parse_args()
    mode, sc = SCENES[a.scene]
    tuning = load_contract()["tuning"]
    game = LiveGame(mode, tuning, sc, 42, days=5, menu=(a.scene == "menu"))
    if a.scene == "shop":  # cập bến ngay, ca quán 1 tick -> tới Shop
        s = game.session
        s.step(InputState((0.0, 0.0), {}, {"interact"}))
        s.step(InputState((0.0, 0.0), {}, set()))
        game.screen = None
    server = LiveServer(game, "127.0.0.1", a.port)
    server.start()
    print(server.url, flush=True)
    time.sleep(a.seconds)
    server.stop()


if __name__ == "__main__":
    main()
