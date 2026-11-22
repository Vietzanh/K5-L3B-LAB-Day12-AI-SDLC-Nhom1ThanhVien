# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: viết test hộp đen cho từng biên trước khi gộp → bắt được 2 lỗi thứ tự trong tick (hit ngay sau recoil, mốc bất tử); runner tách `tick`/`sim_tick`/`phase_tick` từ sớm nên pause và đổi pha không phải sửa sim.
- Điều tệ: làm 1 người nên HUD dồn cuối phase; chỉ thấy lỗi bố cục khi chụp ảnh. Nhiều test P1 phải đổi vì số chuẩn mới (cá bơi, 4 bàn) — tốn thời gian ghi lý do.
- 1 hành động cho Phase 3 (người nhận: Vietzanh): trước khi đổi kho sang cá thể, viết bảng tác động + ADR và test migration (kho đếm → mã 2) TRƯỚC khi sửa gather/quán.

## Phase 3 (nhanh — điều rút ra từ lần đổi kho)
- Hành động P2 (bảng tác động + ADR + test migration trước khi sửa) đã làm: 23 test đổ đúng như dự kiến trong bảng tác động, không có test đổ ngoài dự kiến.
- Đơn vị nguyên 240/điểm giúp test ngưỡng 30 và giá floor chính xác tuyệt đối ngay lần đầu.
- Bài học: định dạng xuất (làm tròn 3 chữ số) cũng là một phần hợp đồng — phải đưa vào bảng tác động.

## Phase 4 (cuối)
- **Rà lại hành động Phase 2** ("bảng tác động + ADR + test migration trước khi sửa gather/quán", người nhận Vietzanh): **đã làm một phần**. ADR-0001 và bảng tác động có trước mọi thay đổi code (commit `df7113d` là lát 1); nhưng test migration viết *sau* khi sửa gather/quán chứ không trước — vì làm một mình nên chạy suite để thấy danh sách test đổ rồi mới sửa nhanh hơn. Kết quả vẫn đúng dự kiến: 23 test đổ đều nằm trong bảng tác động.
- **Điều tốt:** test hộp đen cho từng biên trước khi gộp bắt được nhiều lỗi thứ tự trong tick; skill `run-smoke`/`phase-check` giúp không quên bằng chứng nào trước khi gắn tag; chụp HUD bằng Chrome headless biến UI thành bằng chứng kiểm được.
- **Điều tệ:** nhóm 1 người nên không có review chéo thật — chỉ có người đọc lại diff của AI; HUD luôn dồn cuối phase; không làm mở rộng nào; agent không push/tạo Release được nên bước cuối phụ thuộc người.
- **Số liệu:** 29 commit của Vietzanh trên nhánh chính (mọi commit có `Co-Authored-By` AI), 0 commit người khác; cách đọc code: người đọc diff từng lát + test tự động + ảnh HUD (không có PR review vì 1 người); token: không đo được trong phiên Claude Code này (ghi "~?" trong nhật ký AI).
- **Một lần AI sai và cách phát hiện:** khi đổi sang kho cá thể, AI để JSONL làm tròn `fresh` 3 chữ số như mọi số thực, nên `gather_end.inventory` (99.992) lệch file kho (99.99166…). Phát hiện nhờ test bàn giao so chính xác file ↔ event ↔ snapshot quán; quyết định giữ `fresh` chính xác trong JSONL và ghi lý do ở `docs/clarify.md` #15.
- **Nếu làm lại, đổi gì:** viết test migration *trước* khi đổi schema (đúng hành động đã chốt); chụp HUD ngay sau mỗi lát UI thay vì cuối phase; chốt sớm với giảng viên cách chấm khi làm 1 người; dành thời gian cho ít nhất một mở rộng (Cháy món là rẻ nhất).
- **Việc tiếp theo (người nhận Vietzanh):** push `main` + tag `phase-1..4`, tạo Release `v1.0.0` kèm gói zip; quay video demo < 5 phút theo checklist.
