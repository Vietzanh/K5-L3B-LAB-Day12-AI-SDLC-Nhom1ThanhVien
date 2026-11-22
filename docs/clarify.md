# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 kickoff | Lab yêu cầu nhóm 4–6 người, nhưng em đến lớp muộn, không kịp ghép nhóm nên làm **một mình**. | Giả định: làm 1 người; chia việc thể hiện qua lát giao cho agent AI + nhánh riêng + tự review rồi gộp. | Vietzanh |
| 2 | 2026-11-21 kickoff | `tools/check_team.py` báo lỗi "số thành viên phải từ 4 đến 6" khi `team_size = 1`. Có cần sửa script không? | Giả định: **không sửa** script của giảng viên (CI chỉ cảnh báo, không chặn); ghi nhận lỗi này là đã biết. | Vietzanh |
| 3 | 2026-11-21 kickoff | Máy Windows không có lệnh `python3` nên `headless_cmd` lỗi khi chạy test ngoài WSL. Có đổi `headless_cmd` thành `python` không? | **Không đổi** contract (máy chấm dùng `python3`). Mọi lệnh test/headless chạy qua WSL (Python 3.10). | Vietzanh |
| 4 | Phase 1 | Id khách mới dùng tiền tố nào? PRD chỉ nói order_id = id khách. | Giả định `C1, C2…` (khớp fixture mẫu `C1` trong smoke test), cấp tiếp sau hậu tố lớn nhất đã nạp. | Vietzanh |
| 5 | Phase 1 | `base_price`/`tip` của khách đang chờ (chưa chốt) xuất gì trong snapshot? | Giả định `null` tới khi chốt (giá lúc bắt đầu nấu, boa lúc phục vụ). | Vietzanh |
| 6 | Phase 1 | "Chọn đều theo seed" món của khách | Luồng RNG riêng `customers`, `randrange` trên danh sách id món đủ nguyên liệu sắp theo Unicode. | Vietzanh |
