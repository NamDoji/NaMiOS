# Gỡ cài đặt phần mềm (namios-go-cai-dat)

Đây KHÔNG phải một app tự viết mới — chỉ là một lối tắt tiếng Việt, dễ thấy
(kiểu "Add/Remove Programs" của Windows), trỏ thẳng vào mục **Đã cài**
(Installed) của **Discover** (`plasma-discover`) — Trung tâm phần mềm đã có
sẵn trên NaMiOS, chính nó lo toàn bộ việc liệt kê + gỡ cài đặt thật qua
PackageKit.

## Cách dùng

Mở **"Gỡ cài đặt phần mềm"** → tìm phần mềm → bấm **Gỡ cài đặt (Uninstall)**
→ nhập mật khẩu → Xong.

Chi tiết từng bước:

1. Mở app **"Gỡ cài đặt phần mềm"** từ menu Start hoặc gõ tìm trong KRunner
   (Meta/Alt+Space).
2. Cửa sổ Discover mở thẳng vào tab **Đã cài** — danh sách mọi phần mềm
   đang có trên máy.
3. Gõ tìm tên phần mềm muốn gỡ trong ô tìm kiếm.
4. Bấm nút **Gỡ cài đặt** (Uninstall) cạnh tên phần mềm đó.
5. Nhập mật khẩu quản trị (mật khẩu đăng nhập của bạn) khi được hỏi — bắt
   buộc vì gỡ phần mềm là thay đổi ảnh hưởng toàn máy, không phải chỉ riêng
   tài khoản của bạn.
6. Xong — phần mềm biến mất khỏi danh sách Đã cài và khỏi menu Start.

## Lưu ý trung thực

- Một số gói **hệ thống/gói nền** (các thành phần lõi của KDE Plasma hoặc
  NaMiOS, ví dụ môi trường desktop, driver, thư viện dùng chung) được
  PackageKit **bảo vệ**: nút Gỡ cài đặt có thể bị mờ/khoá, hoặc Discover báo
  lỗi phụ thuộc nếu gỡ sẽ làm hỏng thành phần khác. Đây là hành vi **an
  toàn**, không phải lỗi — mục đích là tránh người dùng vô tình gỡ nhầm phần
  làm hỏng máy.
- Launcher này không tự xử lý việc cài/gỡ — toàn bộ logic liệt kê, kiểm phụ
  thuộc, gỡ cài đặt là do chính Discover + PackageKit (gói `plasma-discover`,
  `packagekit`, `appstream`, đã khai ở
  `package-lists/0100-desktop-kde.list.chroot`) đảm nhiệm.

**verified_on_host: NO** — chưa chạy thử trên máy/VM Plasma 6 thật. Cần xác
nhận khi có máy thật:

- [ ] `plasma-discover --mode installed` mở đúng tab "Đã cài" (không rơi về
      trang Trình duyệt/Home mặc định).
- [ ] Icon `plasmadiscover` hiển thị đúng (không vỡ icon) sau khi gói
      `plasma-discover` được cài vào ảnh ISO thật.
- [ ] Gỡ thử một phần mềm không-hệ-thống (ví dụ một app vừa cài thêm) — luồng
      nhập mật khẩu PolicyKit hiện ra và gỡ thành công.
- [ ] Thử gỡ một gói lõi hệ thống — xác nhận Discover chặn/báo lỗi phụ thuộc
      đúng như mô tả, không cho gỡ âm thầm gây hỏng máy.
