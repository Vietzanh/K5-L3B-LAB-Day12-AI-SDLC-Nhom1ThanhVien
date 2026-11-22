# Quán Ăn Chợ Nổi — Nhom1ThanhVien

> Lab Day 12 · AI SDLC. Đề: [`docs/prd/`](docs/prd/) (chép từ [lab board](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)).
> Nhóm **1 thành viên** (đến lớp muộn) — xem [`TEAM.md`](TEAM.md).

Út Sen lặn bắt cá, hái bông trên sông Chín Khúc buổi sáng (`gather`), tối mở quán trên nhà bè của Má Tư (`quan`).
Phần mang về (file kho) quyết định quán bán được món nào.

## Chạy từ clone sạch (macOS / Linux, cần Python ≥ 3.8, không cài thêm gì)

```bash
git clone https://github.com/Vietzanh/K5-L3B-LAB-Day12-AI-SDLC-Nhom1ThanhVien.git
cd K5-L3B-LAB-Day12-AI-SDLC-Nhom1ThanhVien
python3 -m chonoi.live            # mở http://127.0.0.1:8000/ — chơi 5 Ngày (sáng lặn, tối mở quán, Shop)
```

Tùy chọn: `--days 1..5`, `--seed N`, `--port N`, chơi riêng một buổi `--mode gather|quan` (`--inventory-out kho.json` / `--inventory kho.json` để nối hai buổi). Windows: chạy trong **WSL**.

## Điều khiển

| Phím | Buổi sáng (gather) | Buổi tối (quan) | Shop |
|---|---|---|---|
| WASD / mũi tên | bơi (S/↓ = lặn xuống) | đi lại | — |
| E | cập bến (trong vòng bến) / hái nút ở mặt nước | nấu ở bếp trống · bưng món chín · phục vụ ở bàn | — |
| Space | bắt đàn cá gần nhất (dưới nước) | — | — |
| 1 / 2 | — | — | mua Bình oxy / Áo phao |
| Enter | tiếp tục ở màn hình intro/kết quả | | xong, sang Ngày mới |
| Esc / P | tạm dừng (M: về menu) | tạm dừng | tạm dừng |
| H | bật/tắt tương phản cao | | |
| R | chơi lại | | |

**HUD sáng:** đồng hồ (đỏ khi ≤ 30 s), thanh oxy (nhấp nháy khi < 25%), Máu ♥, độ sâu, giỏ theo ô (thanh độ tươi, nhãn "ươn") và theo loại, danh sách Má Tư cần (đã lấy/cần), hồi bắt, gợi ý "E: hái …"/"E: cập bến", cảnh báo **"Thủy quái!"** (viền tím) và **"Hết hơi!"**.
**HUD tối:** đồng hồ ca, tiền, uy tín, điểm, kho khả dụng theo loại kèm độ tươi trung bình, phần đang giữ và số món ươn, món + thanh kiên nhẫn tại từng bàn (đỏ khi < 25%, cảnh báo **"Khách sắp giận!"**), tiến độ bếp / CHÍN, món trên tay.

## Luật chính và cách tính điểm

- **Vòng Ngày:** DayIntro (Má Tư đọc món + nguyên liệu cần) → Lặn & Hái → Mở Quán → Kết quả → Shop → Ngày kế (5 Ngày, rồi Tổng kết). Tiền, tổng thu, uy tín, cấp nâng cấp giữ qua Ngày; oxy và Máu hồi đầy; kho dư bỏ sau Shop.
- **Sáng (180 s):** dưới nước (d > 0.5 m) mất 1 tick oxy/tick, mặt nước hồi 6. Hết oxy: mỗi 60 tick mất 1 Máu. Cá Sấu (d ≥ 10) đuổi khi tới gần, chạm: −1 Máu, rơi nửa giỏ (món nhặt sau rơi trước), bất tử 1.5 s. Máu 0 → ngất, mất cả giỏ. Hái nút ở mặt nước (mọc lại 20 s), bắt đàn cá (linh ×3, lóc ×1, kèo ×2). Giỏ 12 ô.
- **Tối (180 s):** 2 bếp, 4 bàn. Khách đến tick 120 rồi mỗi 15 s, chọn món trong kế hoạch còn đủ nguyên liệu và giữ chỗ ngay. Nấu → bưng → phục vụ trước khi hết kiên nhẫn (60 s). Còn ≥ 50% kiên nhẫn lúc giao thì boa `floor(giá × 0.2)` và +0.2 uy tín; khách bỏ đi −0.5 uy tín.
- **Độ tươi (Mùa Nước Nổi):** mỗi nguyên liệu là một cá thể có độ tươi 100 lúc lấy; trong giỏ giảm 0.5/s, trong kho quán 0.25/s. Dưới 30 là **ươn**: vẫn chiếm ô nhưng không nấu được. Khách giữ món tươi nhất; giá món = `floor(giá niêm yết × độ tươi trung bình / 100)`.
- **Shop:** Bình oxy 200k → 45 s, 400k → 60 s; Áo phao 250k → 4 Máu, 500k → 5 Máu; có hiệu lực từ Ngày kế.
- **Điểm** = `earned + 100 × floor(reputation)` (tiền tính bằng nghìn đồng).
- Thực đơn (dữ liệu trong `game.contract.json`): cá lóc nướng trui 60k, gỏi bông súng 40k, lẩu cá linh bông điên điển 120k, canh chua cá lóc 90k, cá kèo nướng muối ớt 70k, lẩu mắm miền Tây 200k.

## Test và headless

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # toàn bộ test (1 lệnh)
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl [--scenario s.json] [--inputs i.json] [--inventory-out kho.json]
python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out out.jsonl [--inventory kho.json]
python3 -m chonoi.headless --mode day --days 5 --seed 1 --ticks 111000 --out out.jsonl [--scenario s.json] [--inputs i.json]
bash tools/smoke_two_process.sh docs/proof/phase-3                  # smoke bàn giao kho cá thể (gather -> quán)
bash tools/smoke_day.sh docs/proof/phase-3                          # smoke day 1 Ngày + 3 Ngày có mua
bash tools/smoke_fresh.sh docs/proof/phase-3                        # ngưỡng tươi 30 (scenario mẫu Ticket-03)
```

- Test Contract và số liệu: [`game.contract.json`](game.contract.json) (`contract_version` 1.2).
- Hợp đồng file kho + danh sách sự kiện: [`docs/contracts/README.md`](docs/contracts/README.md). Ví dụ kho hợp lệ (v1.2): `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`.
- Test của nhóm: [`tests/test_rules_p1.py`](tests/test_rules_p1.py), [`tests/test_rules_p2.py`](tests/test_rules_p2.py), [`tests/test_rules_p3.py`](tests/test_rules_p3.py) (hộp đen, từng biên của PRD). Ảnh HUD: `python3 tools/hud_demo.py --scene gather|quan|shop|menu`.

## Cách làm việc (nhóm 1 người + agent AI)

Mỗi lát giao cho một agent trên nhánh `p<phase>/...`, tôi review diff và chạy skill [`run-smoke`](.agents/skills/run-smoke/SKILL.md) trước khi gộp; [`phase-check`](.agents/skills/phase-check/SKILL.md) trước khi gắn tag. Ghi chép: [`docs/verification/`](docs/verification/), [`docs/proof/`](docs/proof/), [`docs/clarify.md`](docs/clarify.md), [`docs/ai-usage-log.md`](docs/ai-usage-log.md), [`docs/retro.md`](docs/retro.md).

## Sáng tạo của nhóm

Chưa có — ưu tiên làm lõi đúng trước.
