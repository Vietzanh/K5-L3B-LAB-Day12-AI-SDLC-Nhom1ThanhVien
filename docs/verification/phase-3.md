# Ma trận truy vết Phase 3 (Ticket-03 "Mùa Nước Nổi", Test Contract v1.2)

Phân tích tác động + quyết định đổi schema + thứ tự tích hợp: [ADR-0001](../adr/0001-kho-ca-the-do-tuoi.md).
Bằng chứng trên commit bàn giao (tag `phase-3`) trong [`docs/proof/phase-3/`](../proof/phase-3/): `smoke.txt` (toàn bộ test = regression P1–P2 còn hiệu lực + P3), `handover.txt` (smoke bàn giao kho cá thể qua file), `threshold.txt` (scenario ngưỡng của ticket), `day.txt` (day trên v1.2), ảnh `hud-fresh-*.png`. Test luật: [`tests/test_rules_p3.py`](../../tests/test_rules_p3.py).

| AC | Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P3-01 | `contract_version 1.2`, khối `freshness` {100, 0.5, 0.25, 30} | Nạp + kiểm tuning | `game.contract.json`; `_validate_freshness` | Đạt |
| AC-P3-02 | File kho cá thể `{"items":[{id,kind,fresh}]}` sắp theo id, ghi 1 lần khi gather_end, ngất ghi rỗng, chạm --ticks không ghi; kho đếm / sai schema / kind lạ / id trùng / fresh ngoài miền → mã 2 | Test | `InventoryFile.*`, `test_inv_01_*` (smoke), `test_faint_*` | Đạt |
| AC-P3-03 | Bàn giao qua file: snapshot quán tick 0 khớp chính xác id, kind, fresh với file sau lần hao ở bước gather | Smoke theo ticket | `handover.txt` (KHỚP từng chữ số), `test_handover_smoke_exact_ids_and_freshness` | Đạt |
| AC-P3-04 | Bàn giao trong day cùng tick, không hao thêm; id I1, I2… tăng xuyên pha và Ngày; Ngày kế cấp id mới cho mẫu giỏ | Test | `DayFreshness.test_handover_same_tick_and_ids_continue_across_days` | Đạt |
| AC-P3-05 | Hàng mới fresh 100, hao từ bước sau; giỏ −0.5/s, kho quán −0.25/s (kể cả hàng đang giữ); pause dừng hao | Test | `test_hold_decays_half_point_per_second`, `test_stock_decays_quarter_point_per_second_including_reserved`, `test_new_item_fresh_100_*`; pause: `Pause.*` (P2, timer đứng yên) | Đạt |
| AC-P3-06 | Ươn khi < 30, vẫn chiếm ô, không dùng nấu; `spoiled` đúng một lần khi qua ngưỡng, nhiều cá thể phát theo id | Test + scenario mẫu | `threshold.txt`; `test_threshold_fixture_from_ticket_spoils_on_first_step_once`, `test_spoiled_items_not_cookable` | Đạt |
| AC-P3-07 | Giữ theo id: tươi nhất, hòa theo id; phần giữ vừa ươn → nhả toàn bộ, giữ lại một lần, không đủ → unfulfillable (khách chờ tới hạn) | Test | `test_reserve_freshest_tie_by_id`, `test_reserved_item_spoils_then_rereserve`, `test_reserved_item_spoils_without_replacement_unfulfillable` | Đạt |
| AC-P3-08 | Giá chốt `floor(giá × fresh TB / 100)` lúc bắt đầu nấu; boa trên giá đã chốt; cook_started.items là cá thể sắp theo kind rồi id | Test | `test_price_by_average_freshness_and_tip_on_locked_price` (62k, boa 12k); `test_cook_pick_serve_pay_full_flow` (59k) | Đạt |
| AC-P3-09 | Scenario: hold/stock mảng cá thể, reserved mảng id trỏ hàng chưa ươn đủ công thức không dùng chung → sai là mã 2 | Test | `QuanFixtureErrors.test_contradictions_exit_2`, `test_scenario_reserved_must_be_ids` | Đạt |
| AC-P3-10 | HUD cho thấy độ tươi / hàng ươn | Ảnh Chrome headless | `hud-fresh-gather.png` (thanh tươi + nhãn "ươn" trong giỏ), `hud-fresh-quan.png` (tươi TB theo loại, "⚠ 1 ươn") | Đạt |
| AC-P3-11 | CHANGELOG ghi breaking change + cách cập nhật fixture; regression P1–P2 còn hiệu lực đạt, test đổi có lý do | Đọc lại + chạy suite | `CHANGELOG.md`; commit "Phase 3 lát 1"; `smoke.txt` | Đạt |

## Đánh giá ngắn
- Đạt: toàn bộ lõi v1.2; bàn giao kho chính xác tuyệt đối nhờ đơn vị nguyên 240/điểm.
- Quyết định cần lưu ý: JSONL **không làm tròn** trường `fresh` (xem `docs/clarify.md` #15) để "so chính xác" với file kho.
- Chưa làm mở rộng (dòng lũ, khách đặt trước) — không bắt buộc với nhóm 1 người.
