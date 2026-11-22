# Ma trận truy vết Phase 1 (PRD-0, Test Contract v1.0)

Bằng chứng chạy trên commit bàn giao (tag `phase-1`): [`docs/proof/phase-1/smoke.txt`](../proof/phase-1/smoke.txt) (toàn bộ test), [`docs/proof/phase-1/two-process.txt`](../proof/phase-1/two-process.txt) (smoke hai tiến trình). Test luật: [`tests/test_rules_p1.py`](../../tests/test_rules_p1.py).

| AC | Yêu cầu (PRD-0) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P1-01 | Hợp đồng file kho mục G có schema + ví dụ | Đọc lại; test đọc/ghi kho | `docs/contracts/README.md`; `test_smoke_p1.Integration.*` trong smoke.txt | Đạt |
| AC-P1-02 | Bơi 4 m/s, ramp ≤ 6 tick, chặn mép, hướng mặt | Test hộp đen | `test_smoke_p1.Movement.*` (smoke.txt) | Đạt |
| AC-P1-03 | Oxy −1/+6, oxygen_empty, ngạt mỗi 60 tick (lần đầu t+59), nổi đúng bước thì không ngạt, dive/surface | Test biên | `GatherOxygen.*` (smoke.txt) | Đạt |
| AC-P1-04 | Máu 0 → faint (lost LIFO) → gather_end fainted, kho rỗng | Test + đọc file kho | `test_faint_drops_hold_lifo_and_writes_empty_inventory` | Đạt |
| AC-P1-05 | Hái ở mặt nước, gần nhất trong bán kính (cả mép), mọc lại 1200 tick, hold_full | Test biên | `GatherHarvestCatch.test_harvest_*`, `test_node_regrown_*`, `test_no_harvest_underwater_and_hold_full` | Đạt |
| AC-P1-06 | Bắt cá dưới nước, gần nhất hòa theo id, cả đàn, hồi 30 tick, thiếu chỗ giữ đàn | Test biên | `test_catch_*` | Đạt |
| AC-P1-07 | Cập bến ưu tiên trước hái; hết giờ giữ giỏ; kho ghi đúng 1 lần, không ghi khi chạm --ticks | Test + smoke 2 tiến trình | `test_dock_has_priority_over_harvest`, `test_harvest_on_last_step_goes_into_inventory`, `test_inv_01_*`, two-process.txt (KHỚP) | Đạt |
| AC-P1-08 | Khách từ tick 120 mỗi 900 tick, bàn trống id nhỏ, món đủ nguyên liệu chọn theo seed, giữ chỗ ngay, no_dish | Test | `QuanCustomers.*` | Đạt |
| AC-P1-09 | Hết kiên nhẫn rời, −0.5 uy tín, nhả phần giữ | Test | `test_patience_zero_leaves_and_lowers_reputation` | Đạt |
| AC-P1-10 | Nấu (tiêu phần giữ, chốt giá) → chín → bưng → phục vụ → ăn 600 tick → trả tiền; boa khi ≥ 50% kiên nhẫn, +0.2 uy tín | Test | `QuanService.test_cook_*`, `test_dish_ready_and_pick`, `test_serve_*` | Đạt |
| AC-P1-11 | Đóng ca: khách ăn trả ngay (closing), khách chờ rời không trừ uy tín, quan_end; điểm = earned + 100·floor(uy tín) | Test | `test_closing_*` (score 372) | Đạt |
| AC-P1-12 | Test Contract: CLI, mã 0/1/2, kiểm trước khi ghi, tất định từng byte, fixture mâu thuẫn → 2 | Test | `test_smoke_p1.Contract.*`, `QuanFixtureErrors.*` | Đạt |
| AC-P1-13 | HUD đọc được (sáng: giờ, oxy, Máu, giỏ; tối: kho khả dụng, món, kiên nhẫn, bếp, tay, tiền, uy tín) | Đọc code client + `test_live` (máy chủ chạy, snapshot có đủ trường) | `chonoi/web/index.html`; `test_live` trong smoke.txt | **Đạt một phần**: chưa có ảnh chụp chơi thử bằng trình duyệt |
| AC-P1-14 | README chạy từ clone sạch ≤ 3 lệnh, điều khiển, điểm, lệnh test | Đọc lại README | `README.md` | Đạt (chưa thử trên máy macOS) |

## Đánh giá ngắn
- Đạt: toàn bộ luật lõi headless của hai buổi + bàn giao kho; 29 test luật riêng của nhóm.
- Chưa đạt / còn thiếu: chưa có ảnh chơi thử HUD; chưa làm mở rộng (nhóm 1 người, không bắt buộc).
- Cần chỉnh cho phase sau: tách `phase_tick`/`sim_tick` khỏi `tick` trong runner (pause, đổi pha của `day`).
