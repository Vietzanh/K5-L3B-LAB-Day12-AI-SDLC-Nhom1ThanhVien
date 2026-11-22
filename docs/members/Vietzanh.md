# Vietzanh — phản tư cá nhân (≤ 200 từ)

> Làm một mình (đến lớp muộn), kiêm PO, Integrator, QA lead, Release; mỗi lát giao cho agent AI rồi tự duyệt.

- **Tôi đã làm:** kickoff + 2 skill (`f8db75c`); Phase 1 luật lặn/quán (`c5fc0fb`, `c27796d`, `0c0722d`); Phase 2 cá bơi, Cá Sấu, vòng Ngày, Shop, pause, HUD (`9ebe61d`, `ff74ed2`, `1997a93`, `487399b`); Phase 3 ADR-0001 + kho cá thể độ tươi (`df7113d`…`25af46a`); Phase 4 bench/soak/release (`5b25801`, `939151b`).
- **Tôi đã review:** đọc lại diff của AI từng lát trước khi gộp, đối chiếu PRD; dùng `phase-check` trước mỗi tag.
- **AI sai ở đâu, tôi phát hiện thế nào:** ghi "đã hỏi giảng viên" khi chưa hỏi (tôi từ chối thay đổi); cho Cá Sấu chạm ngay bước vừa hết lùi (đọc lại theo PRD); làm tròn `fresh` trong JSONL (test bàn giao so chính xác); tính `avg_fps` lệch với `measured_s` đã ghi (test P4).
- **Điều tôi học được:** với AI, thứ đáng tin là test hộp đen theo từng biên của đặc tả và bằng chứng chạy thật, không phải lời AI nói "đã xong"; đổi hợp đồng cần ADR + bảng tác động trước khi sửa code.
