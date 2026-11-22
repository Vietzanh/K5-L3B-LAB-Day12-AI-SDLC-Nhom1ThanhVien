"""Test cửa sổ chơi trực tiếp (chonoi.live). Chỉ dành cho starter Python: nhóm đổi ngôn ngữ thì xóa file này."""

import json
import time
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read()


def _post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


class LiveServerTest(unittest.TestCase):
    def test_state_input_and_clean_stop(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("gather", tuning, {}, 1, menu=False), port=0)  # cổng ngẫu nhiên
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            code, body = _get(base + "/state")
            self.assertEqual(code, 200)
            st = json.loads(body)
            self.assertIn("tick", st)
            self.assertEqual(st["mode"], "gather")
            self.assertEqual(st["player"]["pos"], [2, 0])
            self.assertEqual(_post(base + "/input", {"move": [1, 0], "interact": False, "catch": False}), 200)
            self.assertEqual(_post(base + "/input", {"move": [5, 0]}), 400)
            code, html = _get(base + "/")
            self.assertEqual(code, 200)
            self.assertIn(b"<canvas", html)
            deadline = time.time() + 3
            while time.time() < deadline:
                st2 = json.loads(_get(base + "/state")[1])
                if st2["tick"] > st["tick"] + 3 and st2["player"]["pos"][0] > st["player"]["pos"][0]:
                    break
                time.sleep(0.05)
            self.assertGreater(st2["tick"], st["tick"], "mô phỏng phải chạy nền")
            self.assertGreater(st2["player"]["pos"][0], st["player"]["pos"][0], "input phải tác động tới sim")
        finally:
            server.stop()
        self.assertFalse(server.game._thread.is_alive())
        self.assertFalse(server._thread.is_alive())


class LiveDayScreens(unittest.TestCase):
    def test_menu_intro_screens_hold_sim_and_continue(self):
        tuning = load_contract()["tuning"]
        g = LiveGame("day", tuning, {"gather": {"random_fish": False}}, 1, days=1)
        self.assertEqual(g.screen, "menu")
        g._tick_once()
        self.assertEqual(g.session.tick, 0, "màn hình đang hiện: sim không chạy")
        g.cont()
        self.assertEqual(g.screen, "day_intro")
        g.cont()
        self.assertIsNone(g.screen)
        g.set_input({"interact": True})  # đứng ở bến: cập bến ngay
        g._tick_once()
        self.assertEqual(g.session.sim.phase, "quan")
        self.assertEqual(g.screen, "evening_intro")
        st = json.loads(g.state_json())
        self.assertEqual((st["screen"], st["phase"], st["day"]), ("evening_intro", "quan", 1))
        g.set_input({"pause": True})
        g.cont()
        g._tick_once()
        self.assertEqual(json.loads(g.state_json())["state"], "paused")


if __name__ == "__main__":
    unittest.main()
