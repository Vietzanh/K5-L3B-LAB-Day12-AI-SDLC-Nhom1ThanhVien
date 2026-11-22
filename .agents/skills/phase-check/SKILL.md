---
name: phase-check
description: Kiểm tra checklist bắt buộc của một phase (test xanh, ma trận AC, bằng chứng, nhật ký AI, standup, retro/ADR/members theo phase, cây sạch) rồi in lệnh gắn tag phase-N. Dùng trước mỗi hạn tag.
---

# phase-check

## Khi nào dùng
Khoảng 10 phút trước hạn tag của mỗi phase (1:00 / 1:55 / 2:30 / 3:00), và lần cuối ngay trước khi gắn tag.

## Cách chạy (qua WSL)
```bash
wsl -e bash tools/run_smoke.sh phase-<n>                 # tạo bằng chứng test trước
wsl -e python3 tools/phase_check.py <n> --no-test        # đã chạy test ở bước trên
```

## Kiểm tra gì
| Phase | Điều kiện |
|---|---|
| mọi phase | test xanh · `docs/verification/phase-n.md` có dòng AC · `docs/proof/phase-n/` có file · `ai-usage-log.md` và `standup.md` có dòng của phase · cây sạch · tag chưa có |
| 2, 4 | `docs/retro.md` mục Phase n đã điền |
| 3 | có ADR `docs/adr/0001-*.md` trở lên (change request) |
| 4 | có `docs/members/<handle>.md` cho mọi người trong `TEAM.md` |

## Sau khi đạt
Script in lệnh `git tag -a phase-n ... && git push origin phase-n` (phase 4 kèm `gh release create v1.0.0`).
**Agent không tự gắn tag/push**: người (Integrator) đọc kết quả rồi tự chạy lệnh.
Hết giờ mà chưa đạt: vẫn gắn tag, ghi trung thực phần chưa đạt trong `docs/verification/phase-n.md`.
