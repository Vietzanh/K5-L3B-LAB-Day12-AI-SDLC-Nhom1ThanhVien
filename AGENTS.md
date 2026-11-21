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
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` (mở địa chỉ in ra; WASD, E, Space, R)

## Yêu cầu (đọc trước khi code)
- PRD/ticket từng phase: `docs/prd/phase_<n>.md` (chép từ lab board). Chỉ làm đúng phase đang mở.
- Chỗ mơ hồ: ghi `docs/clarify.md`, không bịa.

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì ghi lý do trong commit.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.
- Unit test của nhóm: `tests/test_<module>_rules.py`, chạy qua headless hoặc gọi thẳng `GatherSim`/`QuanSim`.

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

## Skills / hooks của nhóm (`.agents/skills/`)
- `run-smoke` — chạy toàn bộ test qua WSL, lưu bằng chứng `docs/proof/phase-<n>/smoke.txt`. Dùng sau mỗi lát và trước khi gộp/gắn tag.
- `phase-check` — kiểm checklist bắt buộc của phase (test, AC, bằng chứng, nhật ký, retro/ADR/members, cây sạch) rồi in lệnh gắn tag. Dùng trước mỗi hạn tag.
