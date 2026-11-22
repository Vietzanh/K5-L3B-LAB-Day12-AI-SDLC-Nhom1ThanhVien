"""Benchmark có render (Ticket-04 mục 1): python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng lõi (độ tươi, cá bơi, Cá Sấu Năm Chèo, nhấp nháy cảnh báo), Út Sen đứng yên ở bến, 1280×720.
Python chuẩn không có thư viện đồ họa, nên khung hình được vẽ bằng **trình render phần mềm** vào framebuffer RGB
1280×720 (nền nước/trời, nút, đàn cá, thủy quái, người chơi, HUD oxy/Máu/giờ, ô giỏ có thanh tươi) — cùng bố cục với
cửa sổ chơi `chonoi/web/index.html`. Mô phỏng chạy 60 tick/s theo đồng hồ thật (bước cố định), vẽ không giới hạn FPS.

Làm nóng 3 s rồi đo `--duration` s. Xuất: avg_fps = frames / measured_s; p1_low_fps = nghịch đảo thời gian TB của
max(1, ceil(1% × frames)) khung chậm nhất; load_ms = từ lúc khởi chạy tiến trình Python (nạp module) tới khung đầu.
`--frame-out x.png` lưu một khung hình đã render (bằng chứng).
"""

import time

T_LAUNCH = time.perf_counter()  # sớm nhất có thể: lúc nạp module

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import struct  # noqa: E402
import sys  # noqa: E402
import zlib  # noqa: E402

from .contract import load_contract  # noqa: E402
from .errors import BadInput  # noqa: E402
from .inputs import InputState  # noqa: E402
from .runner import Session  # noqa: E402

W, H = 1280, 720
TICK_S = 1.0 / 60.0
WARMUP_S = 3.0
KIND_RGB = {"ca_loc": (124, 154, 82), "ca_linh": (214, 230, 242), "ca_keo": (217, 160, 102),
            "bong_dien_dien": (242, 194, 48), "bong_sung": (232, 121, 156), "keo_neo": (143, 207, 107)}
# 7 đoạn cho chữ số đồng hồ: (x, y, w, h) trên lưới 3×5
SEG = {"a": (0, 0, 3, 1), "b": (2, 0, 1, 3), "c": (2, 2, 1, 3), "d": (0, 4, 3, 1), "e": (0, 2, 1, 3),
       "f": (0, 0, 1, 3), "g": (0, 2, 3, 1)}
DIGITS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
          "7": "abc", "8": "abcdefg", "9": "abcdfg"}


class SoftRenderer:
    """Vẽ cảnh gather vào bytearray RGB 1280×720 bằng phép gán lát theo hàng (nhanh trong Python thuần)."""

    def __init__(self, tuning):
        g = tuning["gather"]
        self.g = g
        self.X, self.D = g["bounds"]["x"][1], g["bounds"]["d"][1]
        top, bottom, sky = 96, 96, 6
        self.s = min((W - 20) / (self.X + 4), (H - top - bottom) / (self.D + sky + 1))
        self.ox = (W - self.s * (self.X + 4)) / 2 + 2 * self.s
        self.oy = top + sky * self.s
        self.fb = bytearray(W * H * 3)
        self._rows = {}
        self.bg = self._background(top, sky)

    def _row(self, rgb):
        r = self._rows.get(rgb)
        if r is None:
            r = self._rows[rgb] = bytes(rgb) * W
        return r

    def _background(self, top, sky):
        fb = bytearray(W * H * 3)
        dark = self._row((16, 22, 28))
        skyc = self._row((246, 215, 195))
        y_sky0, y_w0, y_w1 = top, int(self.oy), int(self.oy + self.D * self.s)
        x0, x1 = int(self.ox), int(self.ox + self.X * self.s)
        for y in range(H):
            o = y * W * 3
            if y_sky0 <= y < y_w0:
                fb[o:o + W * 3] = skyc
            else:
                fb[o:o + W * 3] = dark
            if y_w0 <= y < y_w1:  # dải nước: gradient phù sa đậm dần theo độ sâu
                t = (y - y_w0) / max(1, y_w1 - y_w0)
                c = (int(90 + (29 - 90) * t), int(169 + (59 - 169) * t), int(160 + (58 - 160) * t))
                fb[o + x0 * 3:o + x1 * 3] = self._row(c)[:(x1 - x0) * 3]
        return bytes(fb)

    def rect(self, x, y, w, h, rgb):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(W, int(x + w)), min(H, int(y + h))
        if x1 <= x0 or y1 <= y0:
            return
        row = self._row(rgb)[:(x1 - x0) * 3]
        fb, stride, off = self.fb, W * 3, x0 * 3
        for yy in range(y0, y1):
            o = yy * stride + off
            fb[o:o + len(row)] = row

    def ellipse(self, cx, cy, rx, ry, rgb):
        ry_i = max(1, int(ry))
        for dy in range(-ry_i, ry_i + 1):
            half = rx * math.sqrt(max(0.0, 1 - (dy / ry) ** 2))
            if half >= 0.5:
                self.rect(cx - half, cy + dy, 2 * half, 1, rgb)

    def digit(self, ch, x, y, sz, rgb):
        for seg in DIGITS.get(ch, ""):
            sx, sy, sw, sh = SEG[seg]
            self.rect(x + sx * sz, y + sy * sz, sw * sz, sh * sz, rgb)

    def sx(self, x):
        return self.ox + x * self.s

    def sy(self, d):
        return self.oy + d * self.s

    def frame(self, snap, frame_no):
        self.fb[:] = self.bg
        s = self.s
        blink = (frame_no // 15) % 2 == 0
        # bến
        dp = self.g["dock_pos"]
        self.rect(self.sx(dp[0] - 1.5), self.sy(-0.7), 3 * s, 0.9 * s, (141, 110, 75))
        # nút hái
        for n in snap["nodes"]:
            c = KIND_RGB.get(n["kind"], (200, 200, 200))
            if not n["ready"]:
                c = tuple(v // 3 for v in c)
            self.ellipse(self.sx(n["pos"][0]), self.sy(n["pos"][1]), 0.9 * s, 0.45 * s, c)
        # đàn cá
        for f in snap["fish"]:
            cx, cy = self.sx(f["pos"][0]), self.sy(f["pos"][1])
            c = KIND_RGB.get(f["kind"], (200, 200, 200))
            self.ellipse(cx, cy, 0.9 * s, 0.45 * s, c)
            tail = -1 if math.cos(math.radians(f["heading_deg"])) >= 0 else 1
            self.rect(cx + tail * 1.2 * s - 0.2 * s, cy - 0.3 * s, 0.4 * s, 0.6 * s, c)
        # thủy quái
        for m in snap["monsters"]:
            c = (178, 107, 255) if m["state"] != "recoil" else (110, 70, 150)
            self.ellipse(self.sx(m["pos"][0]), self.sy(m["pos"][1]), 1.6 * s, 0.6 * s, c)
        # Út Sen
        p = snap["player"]
        self.ellipse(self.sx(p["pos"][0]), self.sy(p["pos"][1]), 0.6 * s, 0.6 * s, (255, 138, 61))
        # HUD: đồng hồ (7 đoạn), thanh oxy, Máu
        secs = math.ceil(snap["time_left_ticks"] / 60)
        txt = f"{secs // 60}{secs % 60:02d}"
        for i, ch in enumerate(txt):
            self.digit(ch, 16 + i * 22 + (10 if i >= 1 else 0), 14, 4, (232, 238, 242))
        self.rect(32, 18, 4, 4, (232, 238, 242))  # dấu ":"
        self.rect(32, 26, 4, 4, (232, 238, 242))
        frac = p["oxygen_ticks"] / max(1, p["oxygen_max_ticks"])
        low = frac < 0.25
        self.rect(140, 14, 240, 26, (0, 0, 0))
        self.rect(140, 14, int(240 * frac), 26, ((255, 107, 107) if blink else (122, 29, 29)) if low else (79, 195, 247))
        for i in range(p["hp_max"]):
            self.rect(400 + i * 26, 16, 20, 20, (255, 107, 129) if i < p["hp"] else (70, 40, 50))
        # ô giỏ + thanh độ tươi
        cap, sz, y0 = snap["hold_capacity"], 36, H - 86
        for i in range(cap):
            x0 = 16 + i * (sz + 4)
            self.rect(x0, y0, sz, sz, (50, 56, 62))
            if i < len(snap["hold"]):
                it = snap["hold"][i]
                self.rect(x0 + 3, y0 + 3, sz - 6, sz - 6, KIND_RGB.get(it["kind"], (200, 200, 200)))
                fr = it["fresh"]
                self.rect(x0 + 3, y0 + sz - 7, (sz - 6) * fr / 100, 4, (255, 255, 0) if fr < 30 else (123, 211, 137))
        # viền tím khi thủy quái gần (hiệu ứng cảnh báo mặc định)
        if any(math.dist(m["pos"], p["pos"]) <= 12 for m in snap["monsters"]) and p["pos"][1] >= 10:
            for (x, y, w, h) in ((0, 0, W, 8), (0, H - 8, W, 8), (0, 0, 8, H), (W - 8, 0, 8, H)):
                self.rect(x, y, w, h, (178, 107, 255))
        return self.fb

    def save_png(self, path):
        raw = b"".join(b"\x00" + bytes(self.fb[y * W * 3:(y + 1) * W * 3]) for y in range(H))

        def chunk(tag, data):
            c = struct.pack(">I", len(data)) + tag + data
            return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(png)


def p1_low(frame_times):
    n = max(1, math.ceil(0.01 * len(frame_times)))
    worst = sorted(frame_times, reverse=True)[:n]
    return n / sum(worst) if sum(worst) > 0 else 0.0


def run_bench(seed, duration, frame_out=None, clock=time.perf_counter):
    tuning = load_contract()["tuning"]
    renderer = SoftRenderer(tuning)
    still = InputState((0.0, 0.0), {}, set())  # Út Sen đứng yên ở bến
    sess = Session("gather", tuning, {}, seed)
    frame_no = 0
    renderer.frame(sess.snapshot(), frame_no)
    t_first = clock()
    load_ms = (t_first - T_LAUNCH) * 1000.0
    sim_clock, last = 0.0, t_first
    times, measuring, t_meas0 = [], False, None
    while True:
        now = clock()
        sim_clock += now - last
        steps = 0
        while sim_clock >= TICK_S and steps < 5:  # bước cố định 60 Hz, tối đa 5 bước/khung
            if sess.done:  # hết ca (180 s) thì dựng lại cảnh
                sess = Session("gather", tuning, {}, seed)
            sess.step(still)
            sim_clock -= TICK_S
            steps += 1
        renderer.frame(sess.snapshot(), frame_no)
        frame_no += 1
        end = clock()
        if not measuring and end - t_first >= WARMUP_S:
            measuring, t_meas0 = True, end
        elif measuring:
            times.append(end - last_end)
            if end - t_meas0 >= duration:
                break
        last_end = end
        last = now
    measured = round(end - t_meas0, 6)  # avg_fps tính từ đúng measured_s đã ghi (frames / measured_s)
    if frame_out:
        renderer.save_png(frame_out)
    return {"avg_fps": round(len(times) / measured, 3), "p1_low_fps": round(p1_low(times), 3),
            "frames": len(times), "measured_s": measured, "load_ms": round(load_ms, 1)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--frame-out", dest="frame_out")
    try:
        a = p.parse_args(argv)
    except SystemExit:
        return 2
    if not (0 < a.duration <= 3600):
        sys.stderr.write("--duration phải trong (0, 3600]\n")
        return 2
    try:
        res = run_bench(a.seed, a.duration, a.frame_out)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    try:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, separators=(",", ":"))
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
