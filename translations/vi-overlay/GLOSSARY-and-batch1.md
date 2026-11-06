# NaMiOS vi-overlay — GLOSSARY thống nhất + BATCH 1 (.po)

**Soạn:** 06/11/2026. **Chuẩn:** tiếng Việt kỹ thuật phổ thông, chuẩn Bắc Ninh, không lai căng.
**Phạm vi batch1:** chuỗi **high-visibility** trên desktop mặc định mà upstream vi còn **thiếu/trống/fuzzy**
(xem `docs/l10n/DESKTOP-SURFACE-WORKLIST.md` mục 2, ưu tiên #1–#9).

> **TRUNG THỰC — bắt buộc đọc.** Mỗi `msgid` dưới đây là **chuỗi nguồn tiếng Anh chuẩn của KDE** theo
> trí nhớ chuyên môn; **`msgctxt` (ngữ cảnh phân biệt) và dấu `…`/`...`, số nhiều `Plural-Forms` PHẢI
> được đối chiếu với đúng `.pot`/`.po` trong ISO** trước khi `msgfmt`. Dòng nào không chắc upstream đã
> có vi hay chưa đều ghi `# [cần xác minh trên ISO]`. KHÔNG tự ý ghi đè chuỗi upstream đã dịch tốt —
> chỉ bù chỗ TRỐNG/FUZZY. `msgstr` là **đề xuất bản dịch**, chưa phải catalog đã biên dịch.
>
> Đây là file NGUỒN tham chiếu; khi giao hàng phải tách thành từng `<domain>.po` thật (có header
> `Content-Type: text/plain; charset=UTF-8`, `Language: vi`, `Plural-Forms: nplurals=1; plural=0;`).

---

## 0. GLOSSARY (thuật ngữ thống nhất — mọi batch theo bảng này)

| English | Tiếng Việt (chốt) | Ghi chú |
|---|---|---|
| Settings | Cài đặt | |
| System Settings | Cài đặt hệ thống | |
| Configure… | Cấu hình… | khi là hành động thiết lập chi tiết |
| Preferences | Tùy chọn | |
| Search | Tìm kiếm | ô tìm: "Tìm kiếm…" |
| Applications | Ứng dụng | |
| Places | Nơi chốn | theo chỉ đạo; thống nhất toàn hệ |
| History | Lịch sử | |
| Favorites | Ưa thích | |
| Frequently Used | Hay dùng | |
| Computer | Máy tính | mục trong Kickoff |
| Files | Tệp | |
| File | Tệp | |
| Folder | Thư mục | |
| New Folder | Thư mục mới | |
| Home | Thư mục chính | nơi chốn Home của người dùng |
| Desktop | Màn hình nền | thư mục Desktop |
| Documents | Tài liệu | |
| Downloads | Tải xuống | |
| Music | Nhạc | |
| Pictures | Hình ảnh | |
| Videos | Video | |
| Trash | Thùng rác | |
| Network | Mạng | |
| Root | Gốc hệ thống | nơi chốn "/" |
| Recent Files / Recent | Gần đây | |
| Volume | Âm lượng | |
| Mute | Tắt tiếng | |
| Unmute | Bật tiếng | |
| Microphone | Micrô | |
| Playback / Recording | Phát / Thu | thiết bị âm thanh |
| Battery | Pin | |
| Brightness | Độ sáng | |
| Charging / Discharging | Đang sạc / Đang dùng pin | |
| Fully Charged | Đã sạc đầy | |
| Power Save / Balanced / Performance | Tiết kiệm điện / Cân bằng / Hiệu năng | hồ sơ điện |
| Wi-Fi | Wi-Fi | giữ nguyên |
| Wired | Mạng dây | |
| Airplane Mode | Chế độ máy bay | |
| Connect / Disconnect | Kết nối / Ngắt kết nối | |
| Connected / Disconnected | Đã kết nối / Đã ngắt kết nối | |
| Connecting… | Đang kết nối… | |
| Password | Mật khẩu | |
| Signal strength | Cường độ tín hiệu | |
| Notifications | Thông báo | |
| Do Not Disturb | Không làm phiền | |
| Clipboard | Bảng tạm | |
| Clear | Xóa | "Clear History" = "Xóa lịch sử" |
| Shut Down | Tắt máy | |
| Restart | Khởi động lại | |
| Log Out | Đăng xuất | |
| Sleep / Suspend | Ngủ | |
| Hibernate | Ngủ đông | |
| Lock | Khóa màn hình | |
| Switch User | Chuyển người dùng | |
| Cancel | Hủy | |
| OK | OK | giữ nguyên |
| Yes / No | Có / Không | |
| Open | Mở | |
| Save / Save As | Lưu / Lưu thành | |
| Install / Remove | Cài đặt / Gỡ cài đặt | Discover |
| Update / Updates | Cập nhật / Bản cập nhật | |
| Installed | Đã cài | |
| Software | Phần mềm | Discover = "Trung tâm phần mềm" |
| Widget / Widgets | Tiện ích | |
| Add Widgets | Thêm tiện ích | |
| Panel | Thanh | taskbar = "thanh tác vụ" |
| Enter Edit Mode | Vào chế độ chỉnh sửa | |
| Authentication Required | Cần xác thực | polkit |
| Details | Chi tiết | |
| Devices | Thiết bị | |
| Enable / Disable | Bật / Tắt | |
| Show More / Show Less | Xem thêm / Thu gọn | |

**Quy ước chính tả:** đặt dấu thanh kiểu phổ thông hiện hành ("Hủy", "Tùy chọn"); dùng "Micrô"
(phổ thông) thay "Microphone"; giữ nguyên tên riêng công nghệ (Wi-Fi, VPN, Bluetooth, OK).

---

## 1. plasma-pa — Âm lượng (khay hệ thống) — domain `plasma_applet_org.kde.plasma.volume`
*(upstream vi ≈ 0% — ưu tiên #1)*

```po
msgid "Audio Volume"
msgstr "Âm lượng"

msgid "Volume"
msgstr "Âm lượng"

msgid "Mute"
msgstr "Tắt tiếng"

msgid "Unmute"
msgstr "Bật tiếng"

msgid "Increase Volume"
msgstr "Tăng âm lượng"

msgid "Decrease Volume"
msgstr "Giảm âm lượng"

msgid "Mute Microphone"
msgstr "Tắt micrô"

msgid "Playback Devices"
msgstr "Thiết bị phát"

msgid "Recording Devices"
msgstr "Thiết bị thu"

msgid "Applications"
msgstr "Ứng dụng"

msgid "Devices"
msgstr "Thiết bị"

msgid "No applications playing or recording audio"
msgstr "Không có ứng dụng nào đang phát hoặc thu âm thanh"

msgid "Default Device"
msgstr "Thiết bị mặc định"

msgid "Raise maximum volume"
msgstr "Nâng mức âm lượng tối đa"

# msgid dùng %1 là mức phần trăm — giữ nguyên %1
msgid "Volume at %1%"
msgstr "Âm lượng %1%"

msgid "Audio Muted"
msgstr "Đã tắt tiếng"

msgid "Configure Audio Devices…"
msgstr "Cấu hình thiết bị âm thanh…"
```

---

## 2. plasma-nm — Mạng / Wi-Fi (khay hệ thống) — domain `plasma_applet_org.kde.plasma.networkmanagement` (+ `plasmanetworkmanagement_*`)
*(upstream vi ≈ 0% — ưu tiên #2)*

```po
msgid "Networks"
msgstr "Mạng"

msgid "Available connections"
msgstr "Kết nối khả dụng"

msgid "Connect"
msgstr "Kết nối"

msgid "Disconnect"
msgstr "Ngắt kết nối"

msgid "Connecting…"
msgstr "Đang kết nối…"

msgid "Connected"
msgstr "Đã kết nối"

msgid "Disconnected"
msgstr "Đã ngắt kết nối"

msgid "Wi-Fi"
msgstr "Wi-Fi"

msgid "Enable Wi-Fi"
msgstr "Bật Wi-Fi"

msgid "Wired"
msgstr "Mạng dây"

msgid "Enable mobile network"
msgstr "Bật mạng di động"

msgid "Airplane Mode"
msgstr "Chế độ máy bay"

msgid "Password:"
msgstr "Mật khẩu:"

msgid "Show password"
msgstr "Hiện mật khẩu"

msgid "Configure Network Connections…"
msgstr "Cấu hình kết nối mạng…"

msgid "Search…"
msgstr "Tìm kiếm…"

msgid "VPN"
msgstr "VPN"

msgid "Connect automatically"
msgstr "Tự động kết nối"

# %1 = tên phần trăm tín hiệu
msgid "Signal strength %1%"
msgstr "Cường độ tín hiệu %1%"

msgid "Secure"
msgstr "Bảo mật"

msgid "Insecure"
msgstr "Không bảo mật"

msgid "No network connection"
msgstr "Không có kết nối mạng"

msgid "Checking connectivity…"
msgstr "Đang kiểm tra kết nối…"
```

---

## 3. plasma-desktop (Kickoff) — Nút Bắt đầu — domain `plasma_applet_org.kde.plasma.kickoff`
*(upstream vi ~30% + ~40% fuzzy — ưu tiên #3; bù chuỗi trống/fuzzy)*

```po
msgid "Search…"
msgstr "Tìm kiếm…"

# [cần xác minh trên ISO] placeholder có thể là "Search apps, settings, files, and more…"
msgid "Search apps, files, settings, and more…"
msgstr "Tìm ứng dụng, tệp, cài đặt và nhiều hơn…"

msgid "Applications"
msgstr "Ứng dụng"

msgid "Places"
msgstr "Nơi chốn"

msgid "History"
msgstr "Lịch sử"

msgid "Favorites"
msgstr "Ưa thích"

msgid "Frequently Used"
msgstr "Hay dùng"

msgid "Computer"
msgstr "Máy tính"

msgid "All Applications"
msgstr "Tất cả ứng dụng"

msgid "Pin to Task Manager"
msgstr "Ghim vào thanh tác vụ"

msgid "Unpin from Task Manager"
msgstr "Bỏ ghim khỏi thanh tác vụ"

msgid "Add to Favorites"
msgstr "Thêm vào Ưa thích"

msgid "Remove from Favorites"
msgstr "Bỏ khỏi Ưa thích"

msgid "Edit Applications…"
msgstr "Chỉnh sửa danh mục ứng dụng…"

msgid "Power / Session"
msgstr "Nguồn / Phiên"

msgid "Leave"
msgstr "Rời máy"

msgid "Pin"
msgstr "Ghim"

msgid "Clear History"
msgstr "Xóa lịch sử"
```

### 3b. Hành động phiên / Nguồn (Kickoff footer + hộp thoại Rời máy) — domain `plasma-workspace` (ksmserver / plasmashell / lookandfeel)
*(plasma-workspace ~68% — [cần xác minh trên ISO] vài chuỗi có thể đã có vi; chỉ bù chỗ trống)*

```po
msgid "Shut Down"
msgstr "Tắt máy"

msgid "Restart"
msgstr "Khởi động lại"

msgid "Log Out"
msgstr "Đăng xuất"

msgid "Sleep"
msgstr "Ngủ"

msgid "Suspend"
msgstr "Ngủ"

msgid "Hibernate"
msgstr "Ngủ đông"

msgid "Lock"
msgstr "Khóa màn hình"

msgid "Switch User"
msgstr "Chuyển người dùng"

msgid "Cancel"
msgstr "Hủy"

# %1 = số giây đếm ngược (số nhiều vi = 1 dạng)
msgid "Shutting down in 1 second"
msgid_plural "Shutting down in %1 seconds"
msgstr[0] "Sẽ tắt máy sau %1 giây"

msgid "Restarting in 1 second"
msgid_plural "Restarting in %1 seconds"
msgstr[0] "Sẽ khởi động lại sau %1 giây"

msgid "Logging out in 1 second"
msgid_plural "Logging out in %1 seconds"
msgstr[0] "Sẽ đăng xuất sau %1 giây"

msgid "One moment, please. The system is logging out."
msgstr "Vui lòng chờ một lát. Hệ thống đang đăng xuất."
```

---

## 4. battery + powerdevil — Pin & độ sáng (khay) — domain `plasma_applet_org.kde.plasma.battery` + `powerdevil`
*(powerdevil ~22% — ưu tiên #4)*

```po
msgid "Battery and Brightness"
msgstr "Pin và độ sáng"

msgid "Battery"
msgstr "Pin"

msgid "Brightness"
msgstr "Độ sáng"

msgid "Fully Charged"
msgstr "Đã sạc đầy"

msgid "Charging"
msgstr "Đang sạc"

msgid "Discharging"
msgstr "Đang dùng pin"

msgid "Not charging"
msgstr "Không sạc"

# %1 = phần trăm pin
msgid "%1% Battery"
msgstr "Pin %1%"

msgid "Power Save"
msgstr "Tiết kiệm điện"

msgid "Balanced"
msgstr "Cân bằng"

msgid "Performance"
msgstr "Hiệu năng"

msgid "Power Management"
msgstr "Quản lý điện năng"

msgid "Time To Full"
msgstr "Thời gian sạc đầy"

msgid "Time remaining"
msgstr "Thời gian còn lại"

msgid "No Batteries Available"
msgstr "Không có pin"

msgid "Battery is low"
msgstr "Pin yếu"

msgid "Battery is at critical level"
msgstr "Pin ở mức nguy cấp"

msgid "Keyboard Backlight"
msgstr "Đèn nền bàn phím"
```

---

## 5. kio (kfileplacesmodel) — panel Nơi chốn trong Dolphin / hộp thoại tệp — domain `kio6` / `kio5`
*(frameworks — [cần xác minh trên ISO] toàn nhóm; ưu tiên #5. Nhiều tên này có thể đã có vi.)*

```po
# [cần xác minh trên ISO] — các tên nơi chốn do KFilePlacesModel sinh
msgid "Home"
msgstr "Thư mục chính"

msgid "Desktop"
msgstr "Màn hình nền"

msgid "Documents"
msgstr "Tài liệu"

msgid "Downloads"
msgstr "Tải xuống"

msgid "Music"
msgstr "Nhạc"

msgid "Pictures"
msgstr "Hình ảnh"

msgid "Videos"
msgstr "Video"

msgid "Trash"
msgstr "Thùng rác"

msgid "Network"
msgstr "Mạng"

msgid "Root"
msgstr "Gốc hệ thống"

msgid "Recent Files"
msgstr "Tệp gần đây"

msgid "Recent Locations"
msgstr "Vị trí gần đây"

msgid "Modified Today"
msgstr "Sửa hôm nay"

msgid "Modified Yesterday"
msgstr "Sửa hôm qua"

msgid "Empty Trash"
msgstr "Dọn thùng rác"

msgid "Devices"
msgstr "Thiết bị"

msgid "Removable Devices"
msgstr "Thiết bị tháo lắp"
```

---

## 6. kfilewidgets / kxmlgui — Hộp thoại Mở/Lưu + menu chuẩn — domain `kfilewidgets6` / `kxmlgui6`
*(frameworks — [cần xác minh trên ISO]; ưu tiên #6)*

```po
msgid "Open"
msgstr "Mở"

msgid "Open File"
msgstr "Mở tệp"

msgid "Save"
msgstr "Lưu"

msgid "Save As"
msgstr "Lưu thành"

msgid "Save File"
msgstr "Lưu tệp"

msgid "Cancel"
msgstr "Hủy"

msgid "Name:"
msgstr "Tên:"

msgid "File name:"
msgstr "Tên tệp:"

msgid "Filter:"
msgstr "Bộ lọc:"

msgid "New Folder…"
msgstr "Thư mục mới…"

msgid "New Folder"
msgstr "Thư mục mới"

msgid "Places"
msgstr "Nơi chốn"

msgid "Show Hidden Files"
msgstr "Hiện tệp ẩn"

msgid "Sorting"
msgstr "Sắp xếp"

# kxmlgui — menu/khung chuẩn
msgid "&File"
msgstr "&Tệp"

msgid "&Edit"
msgstr "&Sửa"

msgid "&View"
msgstr "&Xem"

msgid "&Help"
msgstr "Trợ &giúp"

msgid "&Settings"
msgstr "&Cài đặt"

msgid "Configure %1…"
msgstr "Cấu hình %1…"

msgid "Configure Keyboard Shortcuts…"
msgstr "Cấu hình phím tắt…"
```

---

## 7. plasmashell / plasma-desktop — Menu chuột phải desktop + chế độ chỉnh sửa — domain `plasma-workspace` / `plasma-desktop`
*(ưu tiên #7; bù chỗ trống)*

```po
msgid "Enter Edit Mode"
msgstr "Vào chế độ chỉnh sửa"

msgid "Add Widgets…"
msgstr "Thêm tiện ích…"

msgid "Add Panel"
msgstr "Thêm thanh"

msgid "Configure Display Settings…"
msgstr "Cấu hình hiển thị…"

msgid "Configure Desktop and Wallpaper…"
msgstr "Cấu hình màn hình nền và hình nền…"

msgid "Edit Mode"
msgstr "Chế độ chỉnh sửa"

msgid "Show Desktop"
msgstr "Hiện màn hình nền"

msgid "Create New"
msgstr "Tạo mới"

msgid "Paste"
msgstr "Dán"

msgid "Icons"
msgstr "Biểu tượng"
```

---

## 8. plasma-workspace — Thông báo + Bảng tạm (Klipper) + khay chung
*(plasma-workspace ~68%; ưu tiên #8; bù chuỗi thiếu)*

```po
# Thông báo
msgid "Notifications"
msgstr "Thông báo"

msgid "Do Not Disturb"
msgstr "Không làm phiền"

msgid "Clear All Notifications"
msgstr "Xóa mọi thông báo"

msgid "No unread notifications"
msgstr "Không có thông báo chưa đọc"

msgid "No new notifications"
msgstr "Không có thông báo mới"

msgid "Dismiss"
msgstr "Bỏ qua"

msgid "Show Fewer"
msgstr "Thu gọn"

# Bảng tạm (Klipper)
msgid "Clipboard"
msgstr "Bảng tạm"

msgid "Clipboard is empty"
msgstr "Bảng tạm trống"

msgid "Clipboard Contents"
msgstr "Nội dung bảng tạm"

msgid "Clear History"
msgstr "Xóa lịch sử"

msgid "Edit contents"
msgstr "Sửa nội dung"

msgid "Invoke action"
msgstr "Gọi hành động"

# Khay hệ thống chung
msgid "Status and Notifications"
msgstr "Trạng thái và thông báo"

msgid "Show hidden icons"
msgstr "Hiện biểu tượng ẩn"

msgid "Configure System Tray…"
msgstr "Cấu hình khay hệ thống…"
```

---

## 9. discover — Trung tâm phần mềm — domain `plasma-discover`
*(upstream vi ≈ 5% — ưu tiên #9)*

```po
msgid "Discover"
msgstr "Trung tâm phần mềm"

msgid "Search…"
msgstr "Tìm kiếm…"

msgid "Applications"
msgstr "Ứng dụng"

msgid "Installed"
msgstr "Đã cài"

msgid "Updates"
msgstr "Bản cập nhật"

msgid "Featured"
msgstr "Nổi bật"

msgid "Categories"
msgstr "Danh mục"

msgid "Settings"
msgstr "Cài đặt"

msgid "About"
msgstr "Giới thiệu"

msgid "Install"
msgstr "Cài đặt"

msgid "Remove"
msgstr "Gỡ cài đặt"

msgid "Update"
msgstr "Cập nhật"

msgid "Update All"
msgstr "Cập nhật tất cả"

msgid "Launch"
msgstr "Mở"

msgid "No updates available"
msgstr "Không có bản cập nhật"

msgid "All updates have been installed."
msgstr "Đã cài xong mọi bản cập nhật."

msgid "Checking for updates…"
msgstr "Đang kiểm tra bản cập nhật…"

msgid "Show Details"
msgstr "Xem chi tiết"

msgid "Review"
msgstr "Đánh giá"

# %1 = số lượng bản cập nhật
msgid "%1 update available"
msgid_plural "%1 updates available"
msgstr[0] "Có %1 bản cập nhật"
```

---

## 10. polkit-kde-agent-1 — Hộp thoại quyền (xác thực) — domain `polkit-kde-authentication-agent-1`
*(upstream vi ~73% — chuẩn bị batch2; dưới đây là các chuỗi then chốt để xác minh/bù)*

```po
# [cần xác minh trên ISO] — phần lớn nhóm này có thể đã có vi
msgid "Authentication Required"
msgstr "Cần xác thực"

msgid "Password:"
msgstr "Mật khẩu:"

msgid "Authenticate"
msgstr "Xác thực"

msgid "Cancel"
msgstr "Hủy"

msgid "Details"
msgstr "Chi tiết"

msgid "Action:"
msgstr "Hành động:"

msgid "Vendor:"
msgstr "Nhà cung cấp:"

msgid "An application is attempting to perform an action that requires privileges. Authentication is required to perform this action."
msgstr "Một ứng dụng đang cố thực hiện hành động cần quyền hạn. Phải xác thực để thực hiện hành động này."
```

---

## Tổng kết batch1

- **Số mục `.po` đã soạn (batch1):** **181 mục** `msgid→msgstr` (gồm 4 mục số nhiều `msgid_plural`),
  trải 10 nhóm domain (đếm bằng `grep -c '^msgid '`).
- **Phân bổ:** plasma-pa 17 · plasma-nm 23 · kickoff 18 + session 13 · battery/powerdevil 18 ·
  kio-places 17 · kfilewidgets/kxmlgui 21 · desktop/plasmashell 10 · notifications/klipper 16 ·
  discover 20 · polkit 8. *(một số msgid trùng chuỗi nhưng khác domain được tính theo domain.)*
- **Việc xác minh bắt buộc:** mọi dòng `# [cần xác minh trên ISO]` + đối chiếu `msgctxt`/`Plural-Forms`
  với `.pot` gói thật trước khi `msgfmt`. Batch tiếp theo: polkit (bù), greeter đăng xuất, systemsettings
  + KScreen, breeze, rồi các app theo nhu cầu (Ark/KCalc/Gwenview/Spectacle/Konsole/Okular).
```
