# Quán Ăn Chợ Nổi — Nhom1ThanhVien

> Lab Day 12 · AI SDLC. Đề: [`docs/prd/`](docs/prd/) (chép từ [lab board](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)).
> Nhóm **1 thành viên** (đến lớp muộn) — xem [`TEAM.md`](TEAM.md).

Út Sen lặn bắt cá, hái bông trên sông Chín Khúc buổi sáng (`gather`), tối mở quán trên nhà bè của Má Tư (`quan`).
Phần mang về (file kho) quyết định quán bán được món nào.

## Chạy từ clone sạch (macOS / Linux, cần Python ≥ 3.8, không cần cài thêm gì)

```bash
git clone https://github.com/Vietzanh/K5-L3B-LAB-Day12-AI-SDLC-Nhom1ThanhVien.git && cd K5-L3B-LAB-Day12-AI-SDLC-Nhom1ThanhVien
python3 -m chonoi.live --mode gather --inventory-out kho.json     # mở http://127.0.0.1:8000/ — buổi sáng
python3 -m chonoi.live --mode quan --inventory kho.json           # buổi tối, dùng phần vừa mang về
```

Windows: chạy các lệnh trên trong **WSL** (máy Windows không có `python3`).

## Điều khiển

| Phím | Buổi sáng (gather) | Buổi tối (quan) |
|---|---|---|
| WASD / mũi tên | bơi (S/↓ = lặn xuống) | đi lại |
| E | cập bến (trong vòng bến) / hái nút ở mặt nước | nấu ở bếp idle · bưng món chín · phục vụ ở bàn |
| Space | bắt đàn cá gần nhất (chỉ khi dưới nước) | — |
| R | chơi lại | chơi lại |

**HUD sáng:** đồng hồ, thanh oxy (đỏ khi < 25%), Máu ♥, giỏ theo ô + đếm theo loại, hồi chiêu bắt.
**HUD tối:** đồng hồ ca, tiền, uy tín, điểm, kho khả dụng (và phần đang giữ), món + thanh kiên nhẫn tại bàn, trạng thái bếp (đang nấu / CHÍN), món trên tay.

## Luật chính và cách tính điểm

- **Sáng:** dưới nước (d > 0.5 m) mất 1 tick oxy/tick, ở mặt nước hồi 6 tick/tick. Hết oxy dưới nước: mỗi 60 tick mất 1 Máu (ngạt). Máu 0 → ngất, mất toàn bộ giỏ. Hái nút ở mặt nước (mọc lại sau 20 s), bắt đàn cá dưới nước (cá linh ×3, cá lóc ×1, hồi 0.5 s). Giỏ 12 ô. Cập bến hoặc hết 180 s → bàn giao giỏ qua file kho.
- **Tối:** khách đến từ tick 120, mỗi 15 s, chọn món nấu được và giữ nguyên liệu ngay. Nấu → bưng → phục vụ trước khi hết kiên nhẫn (60 s). Ăn 10 s rồi trả tiền; còn ≥ 50% kiên nhẫn lúc giao thì boa `floor(giá × 0.2)` và +0.2 uy tín. Khách bỏ đi: −0.5 uy tín.
- **Điểm** = `earned + 100 × floor(reputation)` (tiền tính bằng nghìn đồng).
- Thực đơn: cá lóc nướng trui (cá lóc ×1, 60k), gỏi bông súng (bông súng ×2, 40k), lẩu cá linh bông điên điển (cá linh ×3 + điên điển ×1, 120k).

## Test và headless

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # toàn bộ test (1 lệnh)
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl [--scenario s.json] [--inputs i.json] [--inventory-out kho.json]
python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out out.jsonl [--inventory kho.json]
bash tools/smoke_two_process.sh docs/proof/phase-1                  # smoke hai tiến trình (kho gather -> quán)
```

- Test Contract và số liệu: [`game.contract.json`](game.contract.json) (`contract_version` 1.0).
- Hợp đồng file kho + danh sách sự kiện: [`docs/contracts/README.md`](docs/contracts/README.md). Ví dụ kho hợp lệ: `{"items":{"bong_sung":2,"ca_loc":1}}`.
- Test của nhóm: [`tests/test_rules_p1.py`](tests/test_rules_p1.py) (hộp đen, từng biên của PRD-0 mục F).

## Cách làm việc (nhóm 1 người + agent AI)

Mỗi lát giao cho một agent trên nhánh `p<phase>/...`, tôi review diff và chạy skill [`run-smoke`](.agents/skills/run-smoke/SKILL.md) trước khi gộp; [`phase-check`](.agents/skills/phase-check/SKILL.md) trước khi gắn tag. Ghi chép: [`docs/verification/`](docs/verification/), [`docs/proof/`](docs/proof/), [`docs/clarify.md`](docs/clarify.md), [`docs/ai-usage-log.md`](docs/ai-usage-log.md), [`docs/retro.md`](docs/retro.md).

## Sáng tạo của nhóm

Chưa có — ưu tiên làm lõi đúng trước.
