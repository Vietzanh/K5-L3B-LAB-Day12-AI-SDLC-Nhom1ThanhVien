# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | Vietzanh | Kickoff: TEAM.md, contract `team_size=1`, clarify, AGENTS.md (WSL), 2 skill `run-smoke`/`phase-check`; smoke test 32/32 xanh qua WSL | Chép PRD-0 vào `docs/prd/phase_1.md`; viết plan Phase 1; làm lát 1–4 (gather oxy/giỏ, hái/bắt cá, khách quán, nấu/phục vụ) | Đến muộn nên làm 1 mình; `check_team.py` báo lỗi "4–6 người" (chỉ cảnh báo) |
| 1 | Vietzanh | Lát 1–4 xong, 61 test xanh qua WSL, smoke hai tiến trình KHỚP | HUD, README, ma trận truy vết, gắn tag phase-1 | Không có ảnh chơi thử trình duyệt (làm qua CLI) |
| 2 | Vietzanh | Lát 1–3 (số chuẩn, cá, Cá Sấu, quán 2 bếp/4 bàn) + smoke tích hợp phút 20 KHỚP | Lát 4: day, Shop, pause, HUD | Chrome trên Windows không vào được máy chủ trong WSL → chạy `hud_demo.py` bằng python Windows |
| 2 | Vietzanh | 80 test xanh, day 1 Ngày 1.2 s, ảnh HUD | Ma trận truy vết, retro, tag phase-2 | — |
| 3 | Vietzanh | ADR + bảng tác động, adapter kho, gather/quán độ tươi; smoke bàn giao phút 20 KHỚP | Day/Shop cá thể, HUD, tài liệu | 23 test cũ đổ vì schema mới (đã dự kiến trong ADR) |
| 4 | Vietzanh | bench (1106 FPS), soak 10/10, ảnh tương phản cao, clone sạch OK | Release notes, retro, phản tư, tag phase-4 | Agent không push/tạo Release được → bàn giao cho người |
