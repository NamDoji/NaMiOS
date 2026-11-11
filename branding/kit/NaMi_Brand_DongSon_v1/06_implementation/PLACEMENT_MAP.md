# Bản đồ thay thế nhận diện từ cài đặt đến sử dụng

| Chặng | Tài sản NaMi | Điểm tích hợp dự kiến | Kiểm tra |
|---|---|---|---|
| Website/tải ISO | logo ngang, favicon | site header, download, metadata | rõ ở mobile, chữ NaMi chính xác |
| ISO boot menu | icon đơn sắc, tên hệ thống | GRUB/systemd-boot theme nếu bản phân phối kiểm soát | boot UEFI/BIOS, Secure Boot không bị phá |
| Chào cài đặt | `installer-welcome` | Calamares/Anaconda/custom installer theo repo thật | nút bắt đầu cài đặt có hành động thật, tiếng Việt |
| Tiến trình cài đặt | `installer-progress` | UI installer | tiến trình phản ánh trạng thái thật, báo lỗi rõ |
| Khởi động | `boot-splash` | Plymouth theme / initramfs | không kéo dài thời gian boot; fallback text hoạt động |
| Đăng nhập | `login-background` | SDDM/GDM/LightDM theo hệ thống | dễ đọc, hỗ trợ nhiều màn hình và độ phân giải |
| Màn hình desktop | `nami-symbol-64/128`, hình nền riêng | desktop shell / menu / dock | icon rõ ở 16–64px; tương phản chế độ tối |
| Trình duyệt | `nami-browser` | launcher riêng của bản phân phối | browser mở đúng ứng dụng; About ghi Firefox nếu là Firefox |
| Cài đặt, cập nhật, AI, kho ứng dụng | icon tương ứng | desktop entry / icon theme | icon ứng dụng không trùng khó phân biệt |
| Thông báo cập nhật | icon `nami-update` | update UI / notification | nguồn ký số, phiên bản, dung lượng, restart rõ ràng |
| Cửa sổ Giới thiệu | `about-background`, logo ngang | About app | phiên bản, giấy phép, nguồn mở và tác giả |
| Tài liệu / PDF / trình chiếu | logo ngang | template, trang bìa | không lẫn với nhãn của bên thứ ba |

## Quy tắc kỹ thuật

1. Xác định DE (KDE/GNOME/XFCE), trình cài đặt, bootloader, display manager và đường dẫn theme trong repo trước khi sửa. Không thay trực tiếp tài sản của gói Firefox hoặc của hãng khác; giữ package upgrade sạch.
2. Đóng gói icon vào gói `nami-branding`, đặt tên namespace `nami-*` theo Freedesktop icon theme. Phân phối hicolor fallback PNG cho 16, 24, 32, 48, 64, 128, 256, 512 và SVG scalable.
3. Đặt desktop entry của **NaMi Trình duyệt** vào gói riêng do NaMi quản lý với `Icon=nami-browser`. Nếu thực thi Firefox, giữ `Exec=firefox %u` hoặc đường dẫn tương ứng đã xác minh; hiển thị nhà cung cấp/trình duyệt gốc ở About, license và tài liệu. Không sửa icon chính thức của Firefox trong gói Firefox; không trình bày là trình duyệt do NaMi viết.
4. Với màn hình boot, tạo theme Plymouth theo cơ chế của distro; thêm fallback khi GPU/driver không hỗ trợ. Không thay đổi firmware splash trên phần cứng của người dùng.
5. Lựa chọn font được cấp phép phân phối (ví dụ Noto Sans nếu giấy phép bản đóng gói cho phép), bảo đảm dấu tiếng Việt và fallback offline. Bộ tài sản không nhúng font.
6. Giao diện cài đặt phải dùng ngôn ngữ tiếng Việt và tiếng Anh; không dùng ảnh chứa nút có vẻ bấm được làm điều khiển thật. Các file trong 04 là bố cục, các control phải là native UI và có accessibility name.
7. Logo hiển thị trong Dark mode, High contrast và màn hình 125/150/200% scaling; phiên bản đơn sắc phải còn nhận diện được.
8. Phiên bản hóa tài sản theo semver, hash vào manifest, gói trong cập nhật đã ký, rollback khi cài lỗi. Không sửa tệp gốc của gói từ bên thứ ba.
9. Trước phát hành: rà soát pháp lý tên NaMi/NaMiOS, quyền logo, giấy phép Firefox, hình nền và font. Thử người dùng ở nhóm tuổi/thiết bị khác nhau.

## Mẫu desktop entry cho launcher sở hữu bởi NaMi

```ini
[Desktop Entry]
Type=Application
Name=NaMi Trình duyệt
Name[en]=NaMi Browser
Comment=Trình duyệt web tích hợp trên NaMi
Exec=firefox %u
Icon=nami-browser
Terminal=false
Categories=Network;WebBrowser;
MimeType=text/html;x-scheme-handler/http;x-scheme-handler/https;
```

Mẫu trên chỉ áp dụng khi hệ thống thực sự cài Firefox và đã xác minh `Exec`, cơ chế default browser, quyền dùng thương hiệu của bản phân phối. Không ghi `Firefox` là do NaMi phát triển.
