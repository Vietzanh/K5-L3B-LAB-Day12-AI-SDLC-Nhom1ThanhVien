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
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
