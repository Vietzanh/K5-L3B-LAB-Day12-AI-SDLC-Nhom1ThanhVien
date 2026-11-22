# ADR-0001: Kho cá thể có độ tươi (Change Request "Mùa Nước Nổi", contract v1.2)

- Trạng thái: chấp nhận
- Ngày, người quyết: 2026-11-22, Vietzanh (nhóm 1 người)

## Bối cảnh
Ticket-03 thay kho đếm theo loại (`{"items":{"ca_loc":1}}`) bằng kho cá thể `{"items":[{"id","kind","fresh"}]}`,
thêm hao tươi (giỏ 0.5/s, kho quán 0.25/s), ươn khi fresh < 30, giữ chỗ theo id và giá theo độ tươi.
Ngưỡng 30 và phép floor của giá cần chính xác tuyệt đối; JSONL làm tròn 3 chữ số nên không được tính trên số đã làm tròn.

## Các lựa chọn đã cân nhắc
1. Lưu `fresh` dạng số thực, trừ 0.5/60 mỗi tick — sai số tích lũy, nhánh ở ngưỡng 30 có thể lệch.
2. **Lưu đơn vị nguyên: 240 đơn vị / 1 điểm tươi** (gợi ý của ticket): giỏ −2/tick, quán −1/tick; `fresh = units / 240` chỉ khi xuất.
3. Phân số `Fraction` cho mọi phép tính — chính xác nhưng chậm và rườm rà trong snapshot.

## Quyết định
- Chọn (2). Cá thể nội bộ `{"id","kind","u"}`; đọc fixture/file: `u = fresh × 240`, nếu sát số nguyên (|Δ| < 1e−6) thì làm tròn về nguyên.
  Ươn ⇔ `u < 30 × 240`. Giá chốt `floor(price × Σu / (n × 240 × 100))` tính bằng `Fraction` (chính xác).
- File kho ghi `fresh = u / 240` bằng `repr` đầy đủ của float (đọc lại ra đúng `u`), sắp theo id.
- Id cá thể `I1, I2…` cấp bằng `IdAllocator` dùng chung cho cả lượt (xuyên pha và Ngày).
- Chỉ hỗ trợ schema v1.2 khi `contract_version = 1.2`: kho đếm (object) → mã 2.

## Hệ quả — bảng tác động

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Adapter kho | `chonoi/inventory.py` (đọc/ghi cá thể, chuyển u ↔ fresh, kiểm id/kind/fresh) | thêm `test_rules_p3.Inventory*`; đổi `test_smoke_p1.test_time_ends_gather_and_keeps_hold`, `test_inv_01_gather_writes_inventory_quan_reads_it` (schema mới) | Vietzanh |
| Contract | `game.contract.json` (`1.2`, `freshness`), `chonoi/contract.py` | — | Vietzanh |
| Lặn | `chonoi/sim/gather.py` (giỏ cá thể, hao −2/tick đầu bước, spoiled, lost là cá thể) | đổi các test P1/P2 so `hold`/`lost` dạng chuỗi → so `kind` | Vietzanh |
| Quán | `chonoi/sim/quan.py` (kho cá thể, hao −1/tick, giữ theo id tươi nhất, giữ lại khi ươn, unfulfillable, giá theo tươi) | đổi fixture `stock`/`reserved` trong `test_rules_p1` Quan*; thêm test ngưỡng/giữ lại/giá | Vietzanh |
| day / Shop | `chonoi/sim/day.py` (bàn giao cá thể cùng tick, id mới các Ngày sau), `shop.py` (kho dư là mảng) | `test_rules_p2.Day*` (hold fixture) | Vietzanh |
| Scenario | `chonoi/scenario.py` (hold/stock mảng cá thể, reserved mảng id, id vật lý duy nhất) | thêm test mã 2 | Vietzanh |
| HUD | `chonoi/web/index.html` (thanh tươi trong giỏ, nhãn "ươn", tươi trung bình theo loại ở kho quán) | ảnh `docs/proof/phase-3/` | Vietzanh |

**Thứ tự tích hợp (giữ main chạy được):** adapter kho + contract + test migration → Lặn → Quán → day/Shop → HUD; chỉ gộp vào `main` khi toàn bộ suite xanh trên nhánh `p3/freshness`.
