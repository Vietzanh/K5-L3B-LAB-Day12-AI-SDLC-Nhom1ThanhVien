# TEAM

**Tên nhóm:** Nhom1ThanhVien  **Số người:** 1  (khớp `team_size` trong `game.contract.json`)

> Nhóm chỉ có **1 thành viên** vì em đến lớp muộn, không kịp ghép nhóm nên phải làm một mình.
> Một người kiêm mọi module và mọi vai; việc "chia việc" thực hiện bằng cách giao từng lát cho agent AI riêng
> trên nhánh riêng, tôi review rồi gộp (xem thỏa thuận bên dưới và `AGENTS.md`).

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Vietzanh | Vietzanh | `sim/gather`, `sim/quan`, `client/ui`, `qa` | PO, Integrator, QA lead, Scrum/Release | — (agent AI làm lát, người review) |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: hỏi giảng viên / "Anh Năm hàng xóm" trên lab board; mọi câu hỏi và trả lời ghi vào `docs/clarify.md`.
- Khi bất đồng về thiết kế (người ↔ agent, hoặc hai agent): PRD/ticket thắng; mơ hồ thì ghi `clarify.md`, chọn giả định đơn giản nhất và ghi ADR nếu ảnh hưởng hợp đồng.
- Khi vướng quá 10 phút: dừng, ghi vào `docs/standup.md` cột "Vướng gì", hỏi giảng viên hoặc cắt phạm vi; không để lỡ hạn tag.
- Giờ standup giữa phase: phút 20 và phút cuối trước khi gắn tag của mỗi phase (một dòng trong `docs/standup.md`).
- Cách đọc code: mọi thay đổi do agent viết đều được người đọc lại diff trước khi gộp; ghi chỗ AI sai vào `docs/ai-usage-log.md`.
- Cách làm việc với Git: mỗi lát một nhánh ngắn `p<phase>/<lat>` → test xanh qua WSL → gộp vào `main`; chỉ Vietzanh gắn tag, sau khi chạy skill `phase-check`.
