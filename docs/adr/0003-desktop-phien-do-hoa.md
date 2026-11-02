# ADR 0003 — Desktop và phiên đồ họa

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §5.1, §8, §SEC-003/004; requirement VN-002, UX-005

## Bối cảnh

Cần chọn desktop environment và phiên đồ họa (Wayland vs X11) cân bằng giữa trải nghiệm tiếng Việt (bộ gõ), tính năng hiện đại, và khả năng cách ly ứng dụng — đặc biệt khi chạy app Windows qua Wine.

## Quyết định

Tùy biến **KDE Plasma** (Dolphin + thiết lập riêng) bằng gói Debian; **không viết desktop mới**. **Wayland là ứng viên mặc định**; Wine chạy qua **XWayland** khi cần. **X11** chỉ là profile tương thích được gắn nhãn hạn chế cách ly.

## Lý do

- KDE/Qt phù hợp với stack UI riêng (PySide6 Qt Quick, ADR 0006) và có hỗ trợ accessibility/scale.
- Wayland cô lập input/cửa sổ tốt hơn X11; X11/XWayland có rủi ro một client quan sát/điều khiển phiên khác (SEC-004) → chỉ dùng khi buộc phải, kèm hạ nhãn cách ly.

## Hệ quả

- Quyết định cuối Wayland vs X11 phải chờ ma trận kết quả IME/clipboard/màn hình/sandbox.
- Không gọi bất kỳ phiên nào là "an toàn tuyệt đối"; mọi nới policy display phải ghi ngoại lệ + test.

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Host hiện tại là **container headless, không có desktop session**, không có Wine/XWayland.
- → Toàn bộ spike desktop/IME/display thuộc M3 (và một phần M2 cho Wine), hiện **BLOCKED** tại đây. Cần VM Debian 13 có KDE + Fcitx5 + Wine để chạy ma trận.

## Spike cần làm + điều kiện chấp nhận

- **Spike:** Telex/VNI trong Qt/GTK/browser/Wine 32-64bit; clipboard; DPI/scale 125/150/200%; multi-monitor; print; screen sharing; sandbox visibility; quyền display (VN-01, UX-02).
- **Điều kiện chấp nhận:** có bảng kết quả đầy đủ cho Wayland và X11; chọn mặc định dựa trên dữ liệu; mọi ngoại lệ display được ghi và không tuyên bố cách ly tuyệt đối.
