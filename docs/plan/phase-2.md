# Kế hoạch Phase 2 (Ticket-02, contract v1.1)

- **Mục tiêu:** thay số chuẩn, chơi trọn vòng Ngày (gather → quan → shop) có menu, pause, HUD; `--mode day` đúng kế hoạch D1–D5; cấp oxygen/hp áp từ Ngày kế.
- **So với Phase 1 (re-planning):** `fish_initial` thành số (8) + cá bơi/sinh; thêm ca_keo, keo_neo, N5/N6; 2 bếp/4 bàn, 6 món; runner phải tách `tick`/`sim_tick`/`phase_tick` (pause, đổi pha) — đã ghi ở "điều cần chỉnh" của verification P1.

| Lát | Việc | AC | Phụ thuộc |
|---|---|---|---|
| 1 | Số chuẩn v1.1 trong `game.contract.json` + kiểm tuning, inputs (`pause`, `shop_done`, `buy`), scenario v1.1 | AC-P2-01, 10 | — |
| 2 | Cá bơi/đổi hướng/phản xạ/sinh; Cá Sấu patrol/chase/hit/recoil; bất tử; ngất do quái | AC-P2-02..04 | lát 1 |
| 3 | Quán 2 bếp/4 bàn/6 món, lọc món theo kế hoạch | AC-P2-05 | lát 1 |
| 4 | `DayGame` + `ShopSim` + pause trong `Session`; client: menu, intro, kết quả, Shop, pause, HUD, cảnh báo | AC-P2-06..09, 11 | lát 1–3 |

- **Thứ tự tích hợp:** lát 1 trước (mọi lát đọc tuning mới) → 2, 3 → 4; phút 20: smoke tích hợp gather→quan (`docs/proof/phase-2/integration.txt`); cuối phase: smoke day 1 Ngày + 3 Ngày có mua (`day.txt`), regression P1.
- **Rủi ro:** thứ tự trong tick của quái/ngạt/hết giờ; JSONL của day (event tick 0 trước snapshot đầu); làm 1 người → HUD làm sau cùng, chụp ảnh bằng Chrome headless làm bằng chứng.
