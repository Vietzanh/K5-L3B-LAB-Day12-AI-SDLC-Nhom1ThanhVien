# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 kickoff | Lab yêu cầu nhóm 4–6 người, nhưng em đến lớp muộn, không kịp ghép nhóm nên làm **một mình**. | Giả định: làm 1 người; chia việc thể hiện qua lát giao cho agent AI + nhánh riêng + tự review rồi gộp. | Vietzanh |
| 2 | 2026-11-21 kickoff | `tools/check_team.py` báo lỗi "số thành viên phải từ 4 đến 6" khi `team_size = 1`. Có cần sửa script không? | Giả định: **không sửa** script của giảng viên (CI chỉ cảnh báo, không chặn); ghi nhận lỗi này là đã biết. | Vietzanh |
| 3 | 2026-11-21 kickoff | Máy Windows không có lệnh `python3` nên `headless_cmd` lỗi khi chạy test ngoài WSL. Có đổi `headless_cmd` thành `python` không? | **Không đổi** contract (máy chấm dùng `python3`). Mọi lệnh test/headless chạy qua WSL (Python 3.10). | Vietzanh |
| 4 | Phase 1 | Id khách mới dùng tiền tố nào? PRD chỉ nói order_id = id khách. | Giả định `C1, C2…` (khớp fixture mẫu `C1` trong smoke test), cấp tiếp sau hậu tố lớn nhất đã nạp. | Vietzanh |
| 5 | Phase 1 | `base_price`/`tip` của khách đang chờ (chưa chốt) xuất gì trong snapshot? | Giả định `null` tới khi chốt (giá lúc bắt đầu nấu, boa lúc phục vụ). | Vietzanh |
| 6 | Phase 1 | "Chọn đều theo seed" món của khách | Luồng RNG riêng `customers`, `randrange` trên danh sách id món đủ nguyên liệu sắp theo Unicode. | Vietzanh |
| 7 | Phase 2 | Hướng cá "theo seed": phân bố nào? | Đều trong [0°, 360°), luồng RNG `fish_turn` (đổi hướng) và `fish_spawn` (sinh + hướng ban đầu). | Vietzanh |
| 8 | Phase 2 | 8 đàn đầu ca chọn thế nào? | Lặp đúng thủ tục sinh (trọng số loài chuẩn hóa, điểm cách > 1 m) 8 lần, không phát `fish_spawned`. | Vietzanh |
| 9 | Phase 2 | Ngưỡng độ sâu phát hiện/chạm của Cá Sấu ("d ≥ 10") | Lấy cận dưới `depths` của loài (Cá Sấu 10) để dùng chung cho loài khác. | Vietzanh |
| 10 | Phase 2 | Bất tử 90 tick đặt ở tick t: bị chạm lại từ tick nào? | Từ t + 90, cùng quy ước "cooldown L đặt ở t dùng lại từ t+L" của PRD-0 F. | Vietzanh |
| 11 | Phase 2 | `day.upgrades` khai trong scenario có hiệu lực ngay Ngày 1? | Có: active_upgrades = upgrades lúc dựng Ngày đầu. | Vietzanh |
| 12 | Phase 2 | DayIntro/EveningIntro/DayResult có phải pha headless không? | Không: là màn hình của cửa sổ chơi; khi hiện thì cửa sổ ngừng bước sim (headless chuyển pha thẳng gather→quan→shop như Contract 4.5). | Vietzanh |
