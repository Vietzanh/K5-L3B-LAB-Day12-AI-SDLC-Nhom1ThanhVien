# Ma trận truy vết Phase 2 (Ticket-02, Test Contract v1.1)

Bằng chứng trên commit bàn giao (tag `phase-2`) trong [`docs/proof/phase-2/`](../proof/phase-2/): `smoke.txt` (toàn bộ test), `integration.txt` (smoke gather→quan phút 20), `day.txt` (day 1 Ngày + 3 Ngày có mua), ảnh HUD `hud-*.png` (Chrome headless 1280×720). Test luật: [`tests/test_rules_p2.py`](../../tests/test_rules_p2.py).

| AC | Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P2-01 | `contract_version 1.1`, số chuẩn, 6 nguyên liệu, 6 món, N5/N6, day_plan D1–D5 (ingredients = công thức × suất), shop | Nạp + kiểm tuning khi chạy; so bảng PRD | `game.contract.json`; tổng ô D1–D5 = 9/10/12/9/10 khớp bảng PRD; `test_day_plan_override_recomputes_ingredients` | Đạt |
| AC-P2-02 | 8 đàn đầu ca ở 8 điểm chuẩn khác nhau theo seed; bơi 1.5 m/s trong dải loài, đổi hướng mỗi 120 bước, phản xạ mép; sinh mỗi 360 tick, trần 12 | Test | `Fish.*` | Đạt |
| AC-P2-03 | Cá Sấu: patrol 1 m/s, chase 3 m/s khi d ≥ 10 và ≤ 10 m, hit ≤ 1.5 m: −1 Máu, mất floor(n/2) LIFO, bất tử 90, recoil 60 bước | Test | `Monsters.*` | Đạt |
| AC-P2-04 | Máu 0 do quái → faint(monster) mất toàn bộ giỏ; ngạt xuyên bất tử | Test | `test_monster_faint_drops_rest_and_ends`; `GatherOxygen.*` (P1) | Đạt |
| AC-P2-05 | Quán 2 bếp/4 bàn, khách 120 + 900k vào bàn trống id nhỏ; day chỉ món trong kế hoạch | Test | `QuanV11.*`, `test_day_start_events_and_phase_changes` | Đạt |
| AC-P2-06 | `--mode day`: day_start → day_plan → phase_start(gather) ở tick 0; gather_end → phase_start(quan) cùng tick; quan_end → shop; shop_end → Ngày kế / days_complete; vỏ event có `day` | Test + smoke | `Day.test_day_start_events_and_phase_changes`; `day.txt` | Đạt |
| AC-P2-07 | Shop: mua cấp kế (trừ money, giữ earned/điểm), buy_failed funds/max_level/unknown, tự đóng sau 600 tick; cấp áp từ Ngày kế | Test + smoke 3 Ngày | `test_shop_buy_applies_next_day`, `test_buy_failed_reasons`, `test_shop_auto_closes_after_600_ticks`; `day.txt` (Ngày 2: hp_max 4, oxy 2700) | Đạt |
| AC-P2-08 | Pause: chỉ tăng tick ngoài, sim_tick/phase_tick/timer đứng yên, state paused, resumed chạy gameplay ngay | Test | `Pause.test_pause_freezes_sim_and_resume_runs_same_step` | Đạt |
| AC-P2-09 | Một Ngày headless ≤ 22.200 tick chạy ≤ 20 s | Đo | `test_one_day_runs_fast`; `day.txt` (1.2 s trên WSL) | Đạt |
| AC-P2-10 | Scenario day: cấm quan.stock/reputation, 0 ≤ money ≤ earned, upgrades hợp lệ, day_plan đúng; `--days` 1..5 chỉ với day → mã 2 | Test | `test_day_scenario_errors_exit_2` | Đạt |
| AC-P2-11 | Menu chính, DayIntro (tự chuyển 4 s), EveningIntro, DayResult, Shop, Summary, menu pause; HUD sáng/tối đủ mục, cảnh báo "Thủy quái!" + viền tím, "Hết hơi!", chữ ≥ 18 px | Chụp màn hình cảnh dựng sẵn (`tools/hud_demo.py`) + `test_live` | `hud-menu.png`, `hud-gather.png`, `hud-quan.png`, `hud-shop.png`; `LiveDayScreens` | Đạt một phần: chưa chụp DayIntro/Result/Summary; FPS ≥ 30 chưa đo trên trình duyệt thật (ảnh headless không đo FPS) |
| AC-P2-12 | Smoke tích hợp gather --inventory-out → quan --inventory | Script | `integration.txt` (KHỚP) | Đạt |
| AC-P2-13 | Regression P1 còn hiệu lực với số chuẩn; test đổi có lý do | Chạy toàn bộ suite | `smoke.txt`; lý do đổi test ghi trong commit "Phase 2 lát 1" và "lát 3+4" + chú thích trong test | Đạt |

## Đánh giá ngắn
- Đạt: toàn bộ lõi headless v1.1 + vòng Ngày + HUD chính.
- Chưa đạt: chưa có ảnh các màn intro/kết quả; chưa đo FPS thật; không làm mở rộng (nhóm 1 người không bắt buộc).
- Điều cần chỉnh cho phase sau: kho/giỏ đang là đếm theo loại — Phase 3 đổi sang cá thể, phải tách lớp kho trước.
