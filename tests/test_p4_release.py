"""Test Phase 4 (Ticket-04, Test Contract v1.3): bench_cmd, soak_cmd, manifest. Chạy qua lệnh khai trong game.contract.json."""

import json
import math
import os
import shlex
import subprocess
import unittest

from helpers import ROOT, Workdir

from chonoi.bench import p1_low


def manifest():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


def run_cmd(key, *args):
    p = subprocess.run([*shlex.split(manifest()[key]), *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stderr


class Manifest(unittest.TestCase):
    def test_contract_13_declares_bench_and_soak(self):
        m = manifest()
        self.assertEqual(m["contract_version"], "1.3")
        for k in ("build_cmd", "run_cmd", "headless_cmd", "bench_cmd", "soak_cmd"):
            self.assertTrue(isinstance(m.get(k), str) and m[k], k)
        self.assertIn("freshness", m["tuning"], "gameplay/tuning giữ như v1.2")


class Bench(unittest.TestCase):
    def test_bench_json_five_fields(self):
        with Workdir() as w:
            code, err = run_cmd("bench_cmd", "--seed", "42", "--duration", "0.5", "--out", w.path("bench.json"))
            self.assertEqual(code, 0, err)
            with open(w.path("bench.json"), encoding="utf-8") as f:
                b = json.load(f)
        self.assertEqual(set(b), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        self.assertIsInstance(b["frames"], int)
        self.assertGreater(b["frames"], 0)
        self.assertGreaterEqual(b["measured_s"], 0.5)
        self.assertAlmostEqual(b["avg_fps"], b["frames"] / b["measured_s"], delta=0.05)
        self.assertLessEqual(b["p1_low_fps"], b["avg_fps"] + 0.01)
        self.assertGreater(b["load_ms"], 0)

    def test_bench_bad_args_exit_2(self):
        with Workdir() as w:
            self.assertEqual(run_cmd("bench_cmd", "--seed", "42", "--duration", "0", "--out", w.path("b.json"))[0], 2)
            self.assertEqual(run_cmd("bench_cmd", "--seed", "x", "--duration", "1", "--out", w.path("b.json"))[0], 2)

    def test_p1_low_definition(self):
        times = [0.01] * 198 + [0.05, 0.1]  # 200 khung -> ceil(2) = 2 khung chậm nhất: TB 0.075 s
        self.assertAlmostEqual(p1_low(times), 1 / 0.075, places=6)
        self.assertAlmostEqual(p1_low([0.02] * 50), 50.0, places=6)  # max(1, ceil(0.5)) = 1 khung
        self.assertEqual(max(1, math.ceil(0.01 * 50)), 1)


class Soak(unittest.TestCase):
    def test_soak_days_complete_no_crash_deterministic(self):
        out = []
        with Workdir() as w:
            for i in (1, 2):
                code, err = run_cmd("soak_cmd", "--seed", "7", "--days", "3", "--out", w.path(f"s{i}.json"))
                self.assertEqual(code, 0, err)
                with open(w.path(f"s{i}.json"), encoding="utf-8") as f:
                    out.append(json.load(f))
        a, b = out
        self.assertEqual(set(a), {"days", "days_completed", "crashes", "results", "duration_s"})
        self.assertEqual((a["days"], a["days_completed"], a["crashes"]), (3, 3, 0))
        self.assertEqual([r["day"] for r in a["results"]], [1, 2, 3])
        for r in a["results"]:
            self.assertEqual(set(r), {"day", "earned", "reputation", "score"})
            self.assertEqual(r["score"], r["earned"] + 100 * math.floor(r["reputation"]))
        a.pop("duration_s"), b.pop("duration_s")
        self.assertEqual(a, b, "các trường gameplay lặp lại theo seed")

    def test_soak_bad_args_exit_2(self):
        with Workdir() as w:
            self.assertEqual(run_cmd("soak_cmd", "--seed", "7", "--days", "0", "--out", w.path("s.json"))[0], 2)


if __name__ == "__main__":
    unittest.main()
