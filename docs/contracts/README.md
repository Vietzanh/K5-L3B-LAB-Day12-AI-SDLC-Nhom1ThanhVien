# Hợp đồng tích hợp (Contract v1.0 — Phase 1)

Chốt ở kickoff Phase 1. Đổi hợp đồng: ghi ADR trong `docs/adr/` và cập nhật file này.

## 1. File kho (PRD-0 mục G) — `gather --inventory-out` → `quan --inventory`

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

- Đúng một khóa gốc `items`; giá trị là object `kind → số nguyên ≥ 0`. Kind vắng = 0; bên ghi **bỏ** khóa có lượng 0, sắp khóa theo kind. Kho rỗng `{"items":{}}`.
- Kind hợp lệ v1.0: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`. Bên đọc từ chối sai schema / kind lạ / số âm / không nguyên → **mã 2**.
- Ghi **đúng một lần** khi có `gather_end` (ngất ghi rỗng), nội dung khớp `gather_end.data.inventory`; chạm `--ticks` trước thì **không** tạo/ghi đè. Ghi file tạm cùng thư mục rồi `os.replace` (nguyên tử).
- Trần giỏ không áp lên kho quán. Ví dụ hợp lệ: [`inventory.sample.json`](inventory.sample.json).

## 2. Giao diện `sim/*` ↔ `client/ui`

- UI **chỉ đọc** snapshot (cùng trường với dòng `snapshot` của JSONL, mục E) qua `GET /state` của `chonoi.live`, kèm `meta` (= tuning của mode) và `events` gần nhất.
- UI **gửi vào** đúng trạng thái phím: `POST /input {"move":[a,b],"interact":bool,"catch":bool}`; sim tự lấy cạnh lên. `POST /restart` chơi lại.
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
