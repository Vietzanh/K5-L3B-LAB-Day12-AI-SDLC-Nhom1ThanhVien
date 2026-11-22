# Kế hoạch Phase 4 (Ticket-04, contract v1.3, Release v1.0.0)

Nhóm 1 người kiêm cả bốn vai của ticket; mỗi lát giao cho agent, người duyệt và chạy `phase-check`.

| Vai (ticket) | Việc | AC |
|---|---|---|
| Bench/QA | `bench_cmd` (render 1280×720, 3 s làm nóng + 30 s đo), `soak_cmd` (10 Ngày, bot tất định), regression P1–P3, ma trận | AC-P4-01..03, 07 |
| Đóng gói | Thử clone sạch ≤ 3 lệnh (`tools/clean_clone_check.sh`), README yêu cầu môi trường/điều khiển/lệnh, gói zip `git archive` | AC-P4-04, 05 |
| Release/Integrator | contract 1.3, release notes, CHANGELOG theo phase, LICENSE/CREDITS, tag `phase-4` + Release `v1.0.0` cùng commit | AC-P4-05, 06 |
| Điều phối retro | Rà hành động P2, retro cuối, phản tư cá nhân, nhật ký AI | AC-P4-08 |
| (HUD) | Ba cảnh báo + tương phản cao, chơi thử ở chế độ tương phản cao | AC-P4-09 |

Rủi ro: Python chuẩn không có thư viện đồ họa → bench dùng trình render phần mềm (ghi rõ trong release notes); máy không có `gh`/quyền push từ agent → người tự push tag và tạo Release.
