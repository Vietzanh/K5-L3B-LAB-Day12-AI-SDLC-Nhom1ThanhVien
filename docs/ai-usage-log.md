# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Vietzanh | Claude Code (Claude Opus 5.5) | Kickoff: phân tích đề, phát hiện `python3` thiếu trên Windows (20/32 test lỗi) → chạy qua WSL (32/32 OK); điền TEAM.md, contract, clarify; viết skill `run-smoke`, `phase-check` và script `tools/run_smoke.sh`, `tools/phase_check.py`; cập nhật AGENTS.md | ~? (điền sau) | AI ghi trong TEAM.md/clarify là "đã hỏi giảng viên" dù chưa hỏi → tôi từ chối thay đổi, AI sửa lại đúng lý do (đến lớp muộn). AI không đọc được PRD trên lab board (dữ liệu nạp lúc chạy) → tôi tự chép PRD vào `docs/prd/`. |
| 1 | Vietzanh | Claude Code (Claude Opus 5.5) | Lát 1–5: luật gather (oxy/ngạt/ngất/hái/bắt), luật quán (khách, giữ chỗ, bếp, phục vụ, boa, đóng ca, kiểm fixture), 29 test luật, HUD, README, smoke hai tiến trình | ~? | AI tự viết fixture test sai 2 lần (ba đàn cá cùng cách 1 m nên kỳ vọng F3 sai; danh sách input bị lặp) — phát hiện khi đọc lại test trước khi chạy, sửa kỳ vọng theo luật hòa theo id. HUD quán vẽ `st.dish` như chuỗi trong khi luật lưu object → phát hiện khi rà client. |
