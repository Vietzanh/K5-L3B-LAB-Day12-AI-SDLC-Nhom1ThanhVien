# Changelog

## Phase 4 — v1.0.0, contract v1.3 (tag `phase-4`, Release `v1.0.0`)
- `bench_cmd` (`python3 -m chonoi.bench --seed --duration --out`): render phần mềm cảnh lặn 1280×720, làm nóng 3 s, xuất avg_fps / p1_low_fps / frames / measured_s / load_ms.
- `soak_cmd` (`python3 -m chonoi.soak --seed --days --out`): N Ngày trong một tiến trình bằng bot tất định, đếm crash.
- `contract_version` 1.3, `run_cmd` mở thẳng vòng 5 Ngày; gameplay/tuning/kho/JSONL giữ như v1.2.
- Sửa: uy tín chạm trần xuất `5.0` (số thực) thay vì `5`.
- Chơi thử ba cảnh báo ở chế độ tương phản cao; LICENSE, CREDITS, release notes; thử clone sạch.

## Phase 3 — contract v1.2 (tag `phase-3`) — Change Request "Mùa Nước Nổi"
- **Breaking — kho cá thể:** file kho đổi từ `{"items":{"ca_loc":1}}` sang `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}` (sắp theo id). Kho đếm cũ → mã 2.
- **Breaking — scenario:** `gather.hold` và `quan.stock` là mảng cá thể `{id, kind, fresh}`; `customers[].reserved` là mảng id cá thể.
  Cập nhật fixture: `"hold": ["ca_loc"]` → `"hold": [{"id":"I1","kind":"ca_loc","fresh":100}]`; `"stock": {"ca_loc": 2}` → hai cá thể `I1`, `I2`; `"reserved": {"ca_loc": 1}` → `"reserved": ["I1"]`.
- **Breaking — JSONL:** `hold`, `stock`, `lost`, `cook_started.items` là cá thể; sự kiện mới `spoiled {item_id, kind, location}`; trường `fresh` xuất đủ chính xác (không làm tròn).
- Độ tươi: giỏ −0.5/s, kho quán −0.25/s, ươn khi < 30 (vẫn chiếm ô, không nấu được); giữ chỗ theo id (tươi nhất), giữ lại khi hàng vừa ươn; giá chốt theo độ tươi trung bình.
- HUD: thanh tươi + nhãn "ươn" trong giỏ, tươi trung bình và số món ươn ở kho quán.

## Phase 2 — contract v1.1 (tag `phase-2`)
- Số chuẩn mới: 6 nguyên liệu (thêm `ca_keo`, `keo_neo`), 6 món, nút N5/N6, 2 bếp/4 bàn.
- Cá bơi 1.5 m/s, đổi hướng mỗi 120 bước, phản xạ mép; 8 đàn đầu ca theo seed, sinh thêm mỗi 360 tick (trần 12).
- Cá Sấu Năm Chèo (M1 từ Ngày 1, M2 từ Ngày 3): tuần tra, đuổi, chạm mất Máu + nửa giỏ, bất tử 90 tick, lùi 60 bước.
- `--mode day` + `--days`: vòng gather → quan → shop, kế hoạch D1–D5, Shop nâng cấp oxygen/hp.
- Pause ở mọi mode; inputs mới `pause`, `shop_done`, `buy`.
- **Breaking:** `fish_initial` là số (8) thay vì danh sách; `--mode day` không còn bị từ chối.
- Cửa sổ chơi: menu chính, DayIntro/EveningIntro/DayResult/Summary, Shop, menu pause, HUD đầy đủ, cảnh báo, tương phản cao (H).

## Phase 1 — contract v1.0 (tag `phase-1`)
- Luật gather: oxy, ngạt, Máu, ngất, hái, bắt cá, cập bến, file kho.
- Luật quán: khách theo lịch, giữ chỗ, kiên nhẫn, bếp/bưng/phục vụ, boa, uy tín, đóng ca.
- Kiểm fixture mâu thuẫn (mã 2), smoke hai tiến trình, HUD tối thiểu.
