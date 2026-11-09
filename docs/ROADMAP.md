# NaMiOS — Lộ trình các bước tiếp theo

**Cập nhật:** 09/11/2026 · **Nguyên tắc (Phụ lục 13):** chưa chạy trên **máy thật** = chưa `completed`. Mọi thứ dưới đây đang ở mức **QEMU/dev**.

## 0. Hiện trạng (1 dòng)

Vòng P0 đã **chạy trong máy ảo** (boot → desktop Việt → Office/Calc → wallpaper/icon Sen Việt nền ngà), các lớp M2/M3/Update-Center/UI-UX **đã dựng ở mức dev**; **chưa có pilot máy thật** nên chưa năng lực nào `completed`.

## 1. Giai đoạn A — Em làm được NGAY (dev, không cần anh)

| # | Việc | Kết quả | Trạng thái |
| --- | --- | --- | --- |
| A1 | **Nối Design System vào desktop thật**: viết QML cho 3 component riêng (ErrorCard, ConnectionStepper, AIPlanCard) + nối màu token vào color-scheme KDE | Giao diện thật giống design system | làm tiếp |
| A2 | **Nối bấm widget SmartAI → công cụ `namios-smartai`** (sau khi xác minh module `plasma5support` khi boot) | Bấm widget mở trợ lý | chờ build xác minh |
| A3 | **U15-C trên VM**: staged deployment + boot-health + tự rollback + fault-injection (giả lập **mất điện** giữa update) | Chứng minh khôi phục khi mất điện (trên VM) | kế tiếp |
| A4 | **Test hợp đồng lỗi (giả lập)**: Wi-Fi/auth/DNS · in/scan · Bluetooth · AI-offline + test localization | Bộ test xanh cho lớp lỗi/SmartAI | kế tiếp |
| A5 | **Hoàn thiện onboarding**: màn Chào mừng chạy-1-lần + hướng dẫn "quen Windows" + chọn hình nền mặc định | Trải nghiệm lần đầu mượt | nhỏ |
| A6 | **ISO tải công khai bản mới** (gộp tất cả) để anh cắm USB thử | Link ISO Sen Việt mới | khi anh cần |

## 2. Giai đoạn B — BẮT BUỘC cần máy thật (anh cấp)

Đây là cổng duy nhất em **không tự làm được**. Theo Phụ lục 13/15, các "cửa" sau chỉ đạt khi chạy phần cứng thật:

| # | Cửa nghiệm thu | Cần thiết bị |
| --- | --- | --- |
| B1 | **M1**: 10 người làm 8 việc (gõ/lưu/tìm/mở/**in**/Wi-Fi/cài app/tắt máy) | 1–5 máy thật + 1 máy in |
| B2 | **M2**: cắt điện giữa update vẫn boot/recovery; restore 10 file đúng hash; tường lửa/AppArmor chặn thật | máy thật (ổ NVMe/SATA, pin) |
| B3 | **M3**: chạy app **.NET/Windows VN thật** (MISA, ký số, token USB) — ghi rõ chạy/một-phần/không | app .NET + USB token |
| B4 | **U15-C/D**: 5 máy pilot chia ring, thu hồi bản, máy offline lâu | 5 máy pilot |
| B5 | **Ngoại vi**: in/scan/fax/Bluetooth/Wi-Fi theo 3–5 model | máy in/MFP + thiết bị BT |

## 3. Giai đoạn C — Cần anh CHỐT (quyết định/đầu vào)

1. **Bản đồ chủ quyền (MAP-01)**: NaMiOS **không tự vẽ**; cần anh cung cấp **nguồn bản đồ hợp lệ + chuyên gia ký duyệt** (Hoàng Sa/Trường Sa/Phú Quốc/Côn Đảo) mới đóng vào ISO.
2. **Hình nền mặc định**: giữ ảnh thương hiệu ngà, hay đổi 1 cảnh VN (Sen Việt/Hạ Long)?
3. **Ảnh wallpaper**: hiện là ảnh AI minh hoạ — nếu anh có ảnh chụp thật/bản quyền thì thay.
4. **Người chốt release** + **nhóm người dùng đầu** (gia đình/giáo viên/văn phòng?) + list 20 app/web kèm phiên bản.

## 4. Đề xuất thứ tự ưu tiên

1. **A1 + A2** (giao diện thật + widget) — để bản demo đẹp & dùng được.
2. **A3** (U15-C khôi phục khi mất điện trên VM) — chứng minh "máy đáng tin".
3. **B1** (anh đưa 1 máy + máy in) — biến QEMU thành bằng chứng máy thật đầu tiên (mốc M1 thật).
4. Rồi cuốn chiếu B2→B5 theo thiết bị anh có.

> Mục tiêu gần nhất: **khép vòng M1 trên 1 máy thật** (anh cắm USB NaMiOS, làm 8 việc cơ bản). Đó là bước biến mọi thứ "chạy trong máy ảo" thành sản phẩm thật cho người Việt.
