---
name: run-smoke
description: Chạy toàn bộ test (smoke hộp đen qua headless_cmd + unit) qua WSL và lưu bằng chứng vào docs/proof/phase-N/smoke.txt. Dùng sau mỗi lát code xong, trước khi gộp vào main, và trước khi gắn tag.
---

# run-smoke

## Khi nào dùng
- Agent vừa sửa luật trong `chonoi/sim/*` hoặc test → chạy trước khi báo "xong".
- Trước khi gộp nhánh lát vào `main`, và trước khi gắn tag phase.

## Cách chạy
Máy Windows không có `python3` (mà `headless_cmd` cần) → **luôn chạy qua WSL**, đứng ở gốc repo:

```bash
wsl -e bash tools/run_smoke.sh phase-<n>      # từ PowerShell / Git Bash trên Windows
bash tools/run_smoke.sh phase-<n>             # nếu đã ở trong WSL/Linux
```

## Kết quả
- In 3 dòng cuối (`Ran N tests ... OK` hoặc `FAILED`) và mã thoát (0 = xanh).
- Ghi đầy đủ vào `docs/proof/phase-<n>/smoke.txt` kèm commit hash và phiên bản Python → dùng làm link bằng chứng trong `docs/verification/phase-<n>.md`.

## Quy tắc
- Test đỏ: **sửa luật**, không sửa test cho xanh (nếu test sai thật thì ghi lý do trong commit).
- Không đổi `headless_cmd` sang `python` để "chạy được trên Windows".
