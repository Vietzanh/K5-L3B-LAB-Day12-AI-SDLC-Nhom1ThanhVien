# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Môi trường (QUAN TRỌNG)
- Máy dev là Windows, **không có lệnh `python3`** mà `headless_cmd` trong `game.contract.json` cần → **mọi lệnh Python chạy qua WSL** (Python 3.10), đứng ở gốc repo, thêm tiền tố `wsl -e`:
  `wsl -e bash -lc "PYTHONPATH=tests:. python3 -m unittest discover -s tests -v"`
- **Không** đổi `headless_cmd` sang `python` để chạy được trên Windows (máy chấm dùng `python3`).

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Test + lưu bằng chứng: `bash tools/run_smoke.sh phase-<n>` → `docs/proof/phase-<n>/smoke.txt`
- Kiểm trước khi gắn tag: `python3 tools/phase_check.py <n> [--no-test]`
- Headless: `python3 -m chonoi.headless --mode gather|quan|day [--days 1..5] --seed 1 --ticks 600 --out out.jsonl`
- Chơi: `python3 -m chonoi.live` (vòng 5 Ngày; `--mode gather|quan` chơi riêng một buổi)
- Bench / soak (v1.3): `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` · `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`
- Smoke bằng chứng: `bash tools/smoke_two_process.sh <dir>` (bàn giao kho) · `tools/smoke_day.sh` · `tools/smoke_fresh.sh` · `tools/clean_clone_check.sh`
- Ảnh HUD: `python tools/hud_demo.py --scene gather|warn|quan|shop|menu --port N` (python Windows) rồi Chrome `--headless=new --screenshot` vào `http://127.0.0.1:N/[?theme=high]`

## Yêu cầu (đọc trước khi code)
- PRD/ticket từng phase: `docs/prd/phase_<n>.md` (chép từ lab board). Chỉ làm đúng phase đang mở.
- Chỗ mơ hồ: ghi `docs/clarify.md`, không bịa.

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì ghi lý do trong commit.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.
- Test của nhóm: `tests/test_rules_p1..p3.py`, `tests/test_p4_release.py` — hộp đen qua `headless_cmd`, mỗi test một biên của PRD.
- Contract hiện tại **v1.3** (gameplay v1.2): kho là **cá thể** `{id, kind, fresh}`; nội bộ dùng đơn vị nguyên `u` = 240/điểm (ADR-0001). Không tính ngưỡng/giá trên số đã làm tròn.
- JSONL làm tròn số thực 3 chữ số, **trừ `fresh`** (giữ chính xác để khớp file kho) — xem `docs/clarify.md` #15.
- Quy ước thời gian: "cooldown L đặt ở tick t dùng lại từ t+L" áp cho hồi bắt, mọc lại nút, bất tử.
- Đổi hợp đồng (schema kho, tên sự kiện, thứ tự trong tick): viết ADR + bảng tác động trong `docs/adr/` TRƯỚC khi sửa code.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa ghi ADR/lý do (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi gộp, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md`.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.
- Agent **không tự gắn tag, không push**: người làm việc đó sau khi đọc lại.

## Quy tắc làm việc với agent (nhóm 1 người)
- Nhóm chỉ có 1 người → mỗi **lát** (slice) giao cho **một agent**, làm trên nhánh `p<phase>/<lat>`; agent chỉ sửa file thuộc lát đó.
- Cho agent đọc `docs/prd/phase_<n>.md`, `docs/contracts/README.md` và docstring đầu file sim trước khi code.
- Agent làm xong phải chạy skill `run-smoke` và dán kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại diff trước khi gộp, ghi chỗ AI sai vào `docs/ai-usage-log.md`.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Bài học từ các phase (đọc trước khi sửa)
- P2: Cá Sấu vừa hết recoil không được chạm trong cùng bước (`_recovered`); runner tách `tick`/`sim_tick`/`phase_tick`.
- P3: đổi schema làm đổ test cũ hàng loạt — cập nhật fixture theo bảng tác động, ghi lý do trong commit.
- P4: số liệu xuất phải tính từ đúng giá trị đã ghi (vd. `avg_fps = frames / measured_s` sau làm tròn).

## Skills / hooks của nhóm (`.agents/skills/`)
- `run-smoke` — chạy toàn bộ test qua WSL, lưu bằng chứng `docs/proof/phase-<n>/smoke.txt`. Dùng sau mỗi lát và trước khi gộp/gắn tag.
- `phase-check` — kiểm checklist bắt buộc của phase (test, AC, bằng chứng, nhật ký, retro/ADR/members, cây sạch) rồi in lệnh gắn tag. Dùng trước mỗi hạn tag.
