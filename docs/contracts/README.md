# Hợp đồng tích hợp (Contract v1.2 — Phase 3)

Chốt ở kickoff Phase 1. Đổi hợp đồng: ghi ADR trong `docs/adr/` và cập nhật file này.

## 1. File kho (v1.2, Ticket-03; quyết định: ADR-0001) — `gather --inventory-out` → `quan --inventory`

```json
{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
```

- Đúng một khóa gốc `items`; giá trị là mảng cá thể `{id, kind, fresh}`, **sắp theo id**. Kho rỗng `{"items":[]}`.
- `id` chuỗi duy nhất khác rỗng (`I1, I2…` cấp theo thứ tự vào giỏ, tăng xuyên pha và Ngày); `kind` thuộc 6 nguyên liệu; `fresh` hữu hạn trong [0, 100], ghi đủ chính xác để đọc lại giữ đúng giá trị/nhánh ở ngưỡng 30.
- Bên đọc (contract 1.2) từ chối kho đếm theo loại (object), sai schema, kind lạ, id trùng, fresh ngoài miền → **mã 2**. Quán nhận nguyên số lượng, id, độ tươi (kể cả hàng ươn).
- Ghi **đúng một lần** khi có `gather_end` (ngất ghi rỗng), khớp `gather_end.data.inventory`; chạm `--ticks` trước thì không tạo/ghi đè. Ghi file tạm cùng thư mục rồi `os.replace`.
- `--mode day` bàn giao trong bộ nhớ cùng tick, không hao thêm. Ví dụ hợp lệ: [`inventory.sample.json`](inventory.sample.json).

## 2. Giao diện `sim/*` ↔ `client/ui`

- UI **chỉ đọc** snapshot (cùng trường với dòng `snapshot` của JSONL, mục E) qua `GET /state` của `chonoi.live`, kèm `meta` (= tuning của mode) và `events` gần nhất.
- UI **gửi vào** đúng trạng thái phím: `POST /input {"move":[a,b],"interact","catch","pause","shop_done":bool,"buy":"oxygen"|"hp"}`; sim tự lấy cạnh lên. `POST /continue` đóng màn hình (menu/intro/kết quả), `POST /restart` chơi lại.
- Màn hình (menu, DayIntro, EveningIntro, DayResult, Summary) là trạng thái của cửa sổ: khi hiện thì không bước sim (không đổi JSONL headless).
- Sim không biết gì về UI (không đồng hồ thật, không RNG giao diện) → headless và cửa sổ chạy cùng một lớp sim.

## 3. Sự kiện (tên → `data`)

| Pha | Sự kiện | data | Ai phát → ai nghe |
|---|---|---|---|
| gather | `node_regrown` | `node_id` | sim → HUD |
| gather | `gather` | `node_id,kind,amount` | sim → HUD |
| gather | `hold_full` | `action` (gather/catch), `node_id`/`fish_id`, `required,free` | sim → HUD |
| gather | `fish_caught` | `fish_id,kind,yield` | sim → HUD |
| gather | `dive` / `surface` | `pos` sau di chuyển | sim → HUD |
| gather | `oxygen_empty` / `choke` | `oxygen_ticks:0` / `hp` | sim → HUD |
| gather | `faint` | `cause:"choke",lost,hp:0` (lost LIFO) | sim → HUD |
| gather | `gather_end` | `reason` (time/docked/fainted), `inventory` (theo mục 1) | sim → runner (ghi kho) |
| quan | `customer_arrived` / `no_dish` | `order_id,table_id,dish_id` / `{}` | sim → HUD |
| quan | `cook_started` | `stove_id,order_id,dish_id,items,base_price` | sim → HUD |
| quan | `dish_ready` / `dish_picked` | `stove_id,order_id,dish_id` | sim → HUD |
| quan | `served` | `order_id,table_id,dish_id,patience_ticks_left,base_price,tip` | sim → HUD |
| quan | `paid` | `order_id,table_id,base_price,tip,amount,reason` | sim → HUD |
| quan | `customer_left` | `order_id,table_id,reason,reputation` | sim → HUD |
| quan | `quan_end` | `reason:"time",money,earned,shift_earned,reputation` | sim → runner |
| gather | `fish_spawned` | `id,kind,pos` | sim → HUD |
| gather | `monster_hit` | `monster_id,hp,lost,pos` (lost LIFO, pos người chơi) | sim → HUD |
| gather | `faint` (v1.1) | thêm `cause:"monster"` | sim → HUD |
| day | `day_start` / `phase_start` | `{}` | DayGame → HUD (màn hình intro) |
| day | `day_plan` | `dishes,ingredients` | DayGame → HUD (danh sách Má Tư cần) |
| mọi mode | `paused` / `resumed` | `{}` | Session → HUD |
| shop | `bought` / `buy_failed` | `upgrade,level,price,money` / `action,reason` | ShopSim → HUD |
| shop | `shop_end` | `reason` (done/time) | ShopSim → DayGame |

Vỏ event của `day` có thêm `day`. Event kết thúc pha mang pha cũ; `phase_start` mang pha mới.
| gather/quan | `spoiled` (v1.2) | `item_id,kind,location` (hold/stock), theo id | sim → HUD |
