# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** chơi được hai buổi `gather` và `quan` đúng lõi PRD-0 + Test Contract v1.0; hai tiến trình headless nối nhau qua file kho; HUD đọc được; README chạy ≤ 3 lệnh.
- **Người làm:** Vietzanh (nhóm 1 người) — mỗi lát giao cho một phiên agent AI, người review diff + chạy `run-smoke`.

| Lát | Việc | AC | Phụ thuộc |
|---|---|---|---|
| 0 | Hợp đồng kho + sự kiện ở `docs/contracts/README.md` | AC-P1-01 | — |
| 1 | `sim/gather.py`: oxy, ngạt, Máu, ngất (LIFO), dive/surface, chặn biên, giỏ | AC-P1-02..04 | lát 0 |
| 2 | `sim/gather.py`: hái nút (hồi mọc), bắt đàn cá (hồi chiêu, hold_full), cập bến, ghi kho | AC-P1-05..07 | lát 1 |
| 3 | `sim/quan.py` + `scenario.py`: khách theo lịch, chọn món đủ nguyên liệu theo seed, giữ chỗ, kiên nhẫn, no_dish, kiểm fixture mâu thuẫn (mã 2) | AC-P1-08..09 | lát 0 (dùng kho mẫu) |
| 4 | `sim/quan.py`: bếp/bưng/phục vụ, boa, trả tiền, uy tín, đóng ca, quan_end | AC-P1-10..11 | lát 3 |
| 5 | HUD (`chonoi/web/index.html`), README, test luật `tests/test_rules_p1.py`, ma trận truy vết | AC-P1-12..13 | lát 1–4 |

- **Thứ tự tích hợp:** 0 → 1 → 2 (smoke kho thật) → 3 → 4 → 5; sau mỗi lát chạy `wsl -e bash tools/run_smoke.sh phase-1`.
- **Rủi ro:** làm 1 người nên không có song song thật → ưu tiên lõi chấm tự động (headless) trước, HUD sau; PRD có nhiều chỗ thứ tự trong tick → viết test cho từng biên (ngạt t+59, hồi chiêu, mép bán kính, phục vụ đúng tick kiên nhẫn 0).
