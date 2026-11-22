# Quán Ăn Chợ Nổi v1.0.0

Bản phát hành cuối lab Day 12 (AI SDLC) của nhóm **Nhom1ThanhVien** — Test Contract **v1.3**.

## Điểm mới
- **Vòng 5 Ngày** đầy đủ: Má Tư công bố món + nguyên liệu → Lặn & Hái → Mở Quán → Kết quả → Shop nâng cấp.
- **Sông Chín Khúc sống động:** cá linh, cá lóc, cá kèo bơi và sinh thêm theo seed; **Cá Sấu Năm Chèo** tuần tra, đuổi, chạm làm rơi nửa giỏ.
- **Mùa Nước Nổi:** mỗi nguyên liệu có độ tươi, hao dần trong giỏ và trong kho; hàng ươn không nấu được; giá món theo độ tươi.
- **Quán 2 bếp, 4 bàn, 6 món** miền Tây, boa và uy tín.
- **Dễ tiếp cận:** cảnh báo bằng chữ/biểu tượng ("Thủy quái!", "Hết hơi!", "Khách sắp giận!"), chế độ **tương phản cao** (phím H), chữ ≥ 18 px, menu tạm dừng.
- **Đo và kiểm thử:** `bench_cmd` (render 1280×720, ~1100 FPS trung bình), `soak_cmd` (10 Ngày, 0 crash), 101 test tự động.

## Cách chạy (macOS / Linux, Python ≥ 3.8, không cài thêm)
```bash
git clone https://github.com/Vietzanh/K5-L3B-LAB-Day12-AI-SDLC-Nhom1ThanhVien.git
cd K5-L3B-LAB-Day12-AI-SDLC-Nhom1ThanhVien
python3 -m chonoi.live        # mở http://127.0.0.1:8000/
```
Hoặc tải `quan-an-cho-noi-v1.0.0.zip` đính kèm, giải nén rồi chạy lệnh thứ ba trong thư mục vừa giải nén.
Windows: chạy trong WSL. Điều khiển, lệnh test/headless/bench/soak: xem `README.md`.

## Giới hạn đã biết
- Đồ họa là hình khối tạm (Canvas 2D), chưa có âm thanh/nhạc, chưa có phụ đề SFX.
- `bench_cmd` đo **trình render phần mềm** (Python thuần) chứ không phải trình duyệt; FPS trình duyệt có hiển thị góc phải nhưng chưa đo có hệ thống.
- Không làm mở rộng của các ticket (Lao, Vợt, Rắn, Cháy món, Chợ, Sổ tay, Dòng lũ, Khách đặt trước, Bảng xếp hạng) — nhóm 1 người, ưu tiên lõi.
- `load_ms` tính từ lúc nạp module `chonoi.bench`, không gồm thời gian khởi động trình thông dịch.
- Cửa sổ chơi là máy chủ HTTP cục bộ (127.0.0.1) + trình duyệt, không phải ứng dụng desktop riêng.
