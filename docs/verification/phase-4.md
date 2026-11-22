# Ma trận truy vết Phase 4 (Ticket-04, Test Contract v1.3, Release v1.0.0)

Bằng chứng trên commit bàn giao (tag `phase-4`) trong [`docs/proof/phase-4/`](../proof/phase-4/): `smoke.txt` (toàn bộ test = regression P1–P3 + P4), `bench.json` + `bench-frame.png` (khung đã render), `soak.json`, `clean-clone.txt`, ảnh `hc-warn.png`, `hc-quan.png`. Test: [`tests/test_p4_release.py`](../../tests/test_p4_release.py).

| AC | Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P4-01 | `contract_version 1.3`, khai `bench_cmd`, `soak_cmd` ở gốc; gameplay/tuning/kho/JSONL theo v1.2 | Test manifest | `game.contract.json`; `Manifest.test_contract_13_declares_bench_and_soak` | Đạt |
| AC-P4-02 | `bench_cmd --seed 42 --duration 30 --out bench.json`: cảnh sáng lõi (độ tươi, cá bơi, Cá Sấu), Út Sen đứng ở bến, 1280×720, làm nóng 3 s; đủ 5 trường, công thức avg/p1_low | Chạy 30 s + test | `bench.json` = avg 1106.2 FPS, 1% low 619.9 FPS, 33187 khung, 30.0 s, load 199.5 ms; `bench-frame.png`; `Bench.*` | Đạt (render phần mềm, xem giới hạn) |
| AC-P4-03 | `soak_cmd --seed 7 --days 10 --out soak.json`: days_completed = days, crashes = 0, results theo Ngày tại lúc Shop đóng, lặp D1–D5, gameplay tất định | Chạy 10 Ngày + test hai lần cùng seed | `soak.json` (10/10, 0 crash, 5.0 s); `Soak.test_soak_days_complete_no_crash_deterministic` | Đạt |
| AC-P4-04 | Clone sạch chạy bản có giao diện ≤ 3 lệnh trên macOS/Linux; README có môi trường, điều khiển, test, headless, bench | Script clone sạch trên Linux (WSL) | `clean-clone.txt` (clone → cd → `python3 -m chonoi.live`, `/state` trả menu; test 101 OK; headless/bench/soak OK); `README.md` | Đạt (chưa thử trên macOS) |
| AC-P4-05 | Release v1.0.0 có gói chạy được + release notes do nhóm viết (điểm mới, cách chạy, giới hạn) | Đọc lại; tạo gói bằng `git archive` | `docs/release-notes-v1.0.0.md`; `dist/quan-an-cho-noi-v1.0.0.zip` (tạo từ tag, không commit) | **Chờ người push tag + tạo Release trên GitHub** (agent không có `gh`/quyền push) |
| AC-P4-06 | CHANGELOG theo từng phase; rà CREDITS và LICENSE | Đọc lại | `CHANGELOG.md` (P1–P4), `CREDITS.md` (không asset ngoài, công cụ AI), `LICENSE` | Đạt |
| AC-P4-07 | Regression P1–P3 còn hiệu lực đạt | Chạy toàn bộ suite trên main | `smoke.txt` (101 test OK) | Đạt |
| AC-P4-08 | Retro rà hành động P2, chốt việc tiếp theo; phản tư cá nhân đủ người; bằng chứng đóng góp | Đọc lại | `docs/retro.md` (Phase 4), `docs/members/Vietzanh.md`, `git shortlog` | Đạt |
| AC-P4-09 | Cảnh báo bằng chữ/biểu tượng: thủy quái gần, oxy sắp hết, khách sắp giận; chế độ tương phản cao; chơi thử cả ba ở chế độ đó | Ảnh Chrome headless `?theme=high` | `hc-warn.png` ("Thủy quái!" + viền tím, "Hết hơi!", oxy đỏ, Cá Sấu "!"), `hc-quan.png` ("Khách sắp giận!", 😠, thanh kiên nhẫn) | Đạt (ảnh cảnh dựng sẵn, không phải video chơi tay) |

## Đánh giá ngắn
- Đạt: toàn bộ lõi v1.3 chạy được và có bằng chứng; regression P1–P3 xanh.
- Còn lại cho người: push `main` + các tag `phase-1..4`, tạo GitHub Release `v1.0.0` đính kèm gói zip.
- Giới hạn trung thực: bench đo trình render phần mềm Python thuần (không phải FPS trình duyệt); chưa làm mở rộng; chưa thử trên macOS.
