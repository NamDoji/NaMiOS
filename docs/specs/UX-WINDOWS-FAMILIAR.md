# UX-WINDOWS-FAMILIAR — ánh xạ thao tác Windows → NaMiOS

- **Liên quan:** §28 DAC_TA_HE_DIEU_HANH.md (UI-001..007), §8 (VN-001/002), ADR 0011.
- **Chủ đề giao việc:** desktop giống Windows + thao tác quen thuộc (giao 02/11/2026).
- **verified_on_boot: NO cho TOÀN BỘ bảng dưới đây.** Container phát triển hiện tại
  không có desktop session KDE Plasma (xem `docs/_m0_inventory_raw.md` / ADR 0011
  "Bối cảnh môi trường hiện tại"). Mọi dòng trong bảng là **cấu hình đã viết**, chưa
  phải **hành vi đã quan sát trên máy thật**. Người cầm ISO lên VM/USB thật phải tự
  bấm thử từng dòng rồi cập nhật cột "Xác nhận trên máy thật" — KHÔNG suy luận
  "file không lỗi khi build" thành "đã giống Windows".

## 1. Ràng buộc pháp lý (LIC-004, bắt buộc đọc trước khi sửa bảng này)

NaMiOS **được** bắt chước **bố cục và luồng thao tác** (taskbar dưới, nút mở ứng
dụng góc trái, khay hệ thống/đồng hồ góc phải, Alt+Tab, Win+E, Win+D, click-phải,
kéo-thả). NaMiOS **tuyệt đối không** được:

- Sao chép icon, font, âm thanh, hoạt ảnh hay bất kỳ tài sản nhị phân độc quyền
  của Microsoft (logo Start, âm thanh khởi động Windows, bộ icon Segoe Fluent...).
- Dùng tên hiển thị gây nhầm là sản phẩm Microsoft (không gọi menu khởi động là
  "Start Menu", không đặt tên ổ Linux là `C:` ngoài phạm vi prefix Wine).
- Tuyên bố "giống Windows 100%" hoặc "thay thế hợp pháp mọi tính năng Windows".

Mọi icon/nhạc hiệu/hình nền dùng trong cấu hình dưới đây phải là tài nguyên tự
thiết kế của NaMiOS hoặc có giấy phép phân phối lại rõ ràng (ghi nguồn cạnh file).
Xem `distro/live-build/config/includes.chroot/usr/share/namios-branding/README-PLACEHOLDER.md`.

## 2. Bảng ánh xạ chính (UI-001)

| Thao tác Windows | Hành vi mong đợi trên NaMiOS | File cấu hình (nguồn sự thật) | Cơ chế KDE | verified_on_boot | Xác nhận trên máy thật |
| --- | --- | --- | --- | --- | --- |
| Nhấn phím **Win** | Mở menu ứng dụng (Kickoff) | `etc/skel/.config/kwinrc` `[ModifierOnlyShortcuts]` | KWin `ModifierOnlyShortcuts` gọi D-Bus `org.kde.plasmashell` `activateLauncherMenu` | NO | TBD |
| **Win+E** | Mở Dolphin (trình quản lý tệp) | `etc/skel/.config/kglobalshortcutsrc` `[org.kde.dolphin.desktop]` | KGlobalAccel | NO | TBD — tên group phải đối chiếu lại đúng desktop-file-id của gói `dolphin` trong Debian 13 trixie thật |
| **Win+D** | Thu nhỏ toàn bộ cửa sổ (show desktop) | `etc/skel/.config/kglobalshortcutsrc` `[kwin]` khóa `Show Desktop` | KWin global shortcut | NO | TBD |
| **Win+L** | Khóa màn hình | `etc/skel/.config/kglobalshortcutsrc` `[kscreenlocker]` khóa `Lock Session` | kscreenlocker | NO | TBD |
| **Print Screen** | Mở Spectacle (chụp màn hình) | `etc/skel/.config/kglobalshortcutsrc` `[org.kde.spectacle.desktop]` | KGlobalAccel | NO | TBD |
| **Alt+Tab** | Chuyển cửa sổ đang mở | Giữ mặc định KWin (`Walk Through Windows`, ghi lại trong `kglobalshortcutsrc` cho mục đích công bố, không đổi giá trị) | KWin global shortcut | NO | TBD |
| **Ctrl+C / Ctrl+V** | Copy/Paste | KHÔNG cấu hình ở tầng window-manager — đây là shortcut tầng ứng dụng/toolkit (Qt/GTK), không nằm trong `kglobalshortcutsrc`. Giữ mặc định toolkit, không override. | Qt/GTK app-level | N/A | TBD — chỉ cần xác nhận không có app nào bị đè phím này |
| Click-phải mở menu ngữ cảnh | Giữ hành vi chuẩn Dolphin/Plasma/desktop | Không cần file riêng (hành vi mặc định Plasma) | Plasma/KWin | NO | TBD |
| Kéo-thả file | Giữ hành vi chuẩn Dolphin/Plasma | Không cần file riêng | Dolphin/KIO | NO | TBD |
| Double-click mở ứng dụng/thư mục (không phải single-click kiểu KDE mặc định) | `SingleClick=false` | `etc/skel/.config/kdeglobals` `[KDE]` | KDE Frameworks (`KDirModel`/view) | NO | TBD |
| Taskbar dưới màn hình + nút mở ứng dụng + task list + system tray + đồng hồ | 1 panel `location=4` (bottom) chứa Kickoff + Icon-Only Task Manager + System Tray + Digital Clock | `etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc` | Plasma Shell containment | NO | TBD — cấu trúc applet có thể bị Plasma tự ghi đè/renumber ở lần đăng nhập đầu, đó là hành vi bình thường của Plasma, không phải lỗi |

## 3. File manager (UI-002)

| Yêu cầu | Trạng thái | File | Ghi chú |
| --- | --- | --- | --- |
| Hiện thanh địa chỉ dạng text sửa được (giống Explorer) thay vì breadcrumb | Đã cấu hình | `etc/skel/.config/dolphinrc` `[General] EditableUrl=true` | verified_on_boot: NO — tên khóa `EditableUrl` soạn theo cấu trúc dolphinrc đã biết, PHẢI đối chiếu lại trên Dolphin thật kèm theo phiên bản gói Debian 13 cài được |
| Panel "Places" kiểu This-PC (Home/Documents/Downloads/Desktop + ổ gắn thêm) | **KHÔNG đóng gói sẵn qua `/etc/skel`** — xem mục 6 "Quyết định hoãn" | — | Lý do kỹ thuật ghi rõ bên dưới, không phải thiếu sót bỏ quên |
| Thùng rác (trash) | Giữ hành vi mặc định KIO trash (đã có sẵn khi cài `dolphin` + `kio-extras`), không cần override | — | — |
| Nhãn dung lượng + filesystem trên từng ổ | Giữ hành vi mặc định Dolphin Places panel (tự hiển thị khi mount) | — | TBD xác nhận trên máy thật |
| Không gọi ổ Linux là `C:` | Không có file nào trong bộ này đặt nhãn `C:` cho ổ Linux; `C:` chỉ xuất hiện trong phạm vi prefix Wine (ngoài phạm vi module này) | — | — |

## 4. File liên kết định dạng (UI-003/VN, DATA-001)

`etc/skel/.config/mimeapps.list` đặt mặc định: DOCX/DOC → `libreoffice-writer.desktop`,
XLSX/XLS → `libreoffice-calc.desktop`, PPTX/PPT → `libreoffice-impress.desktop`,
PDF → `org.kde.okular.desktop`. **verified_on_boot: NO** — các desktop-file-id này
phải đối chiếu lại đúng tên thật mà gói Debian 13 trixie cài ra (`libreoffice`,
`libreoffice-l10n-vi` theo `package-lists/0400-office-browser.list.chroot`; `okular`
theo `package-lists/0100-desktop-kde.list.chroot`) — nếu tên sai, `xdg-mime query
default` sẽ không trả về đúng giá trị và ứng dụng mặc định của hệ điều hành (thường
là ứng dụng đầu tiên theo alphabet) sẽ mở thay, cần kiểm tra bằng tay sau khi cài.

Theo APP-OFF-006 (đã ghi trong `package-lists/0400-office-browser.list.chroot`):
UI khi hiển thị LibreOffice cho người dùng PHẢI gọi là "phần mềm thay thế", KHÔNG
đặt tên hiển thị là Word/Excel/PowerPoint — đây là việc của tầng UI hiển thị tên
ứng dụng (ví dụ App Center `namios-app-center`), không phải của `mimeapps.list`
(file này chỉ quyết định app nào MỞ, không quyết định app xưng tên gì trên UI).

## 5. Tiếng Việt mặc định cho desktop (VN-001)

- Locale hệ thống `vi_VN.UTF-8` + timezone `Asia/Ho_Chi_Minh`: đã cấu hình ở
  `distro/live-build/config/hooks/normal/0100-locale-vi.hook.chroot` (module khác,
  không thuộc phạm vi sửa của việc này) + `--bootappend-live
  locales=vi_VN.UTF-8 timezone=Asia/Ho_Chi_Minh` trong `auto/config`.
- Ngôn ngữ hiển thị **Plasma Shell** (khác với locale hệ thống) đặt qua
  `etc/skel/.config/plasma-localerc` (`[Translations] LANGUAGE=vi:en_US`).
  **Giới hạn THẬT cần ghi rõ:** các gói "KDE l10n" dịch Plasma sang tiếng Việt
  (`kde-l10n-vi` kiểu cũ) đã bị khai tử upstream từ nhiều năm trước; bản dịch tiếng
  Việt của Plasma 6 hiện phụ thuộc catalog dịch trong từng gói riêng lẻ và **có thể
  không đầy đủ hoặc thiếu hẳn** ở Debian 13 trixie. `LANGUAGE=vi:en_US` chỉ đảm bảo
  **ưu tiên** tiếng Việt khi có bản dịch, **tự động rơi về tiếng Anh** khi không có
  — đây không phải lỗi cấu hình, là giới hạn thật của hệ sinh thái dịch Plasma,
  không được báo cáo thành "đã Việt hóa toàn bộ Plasma".
- Bộ gõ tiếng Việt (Fcitx5 + Unikey, Telex/VNI — VN-002): **đã được module khác xử
  lý** tại `distro/live-build/config/hooks/normal/0200-fcitx5-default-im.hook.chroot`
  (ghi `/etc/skel/.config/fcitx5/profile` lúc chạy hook trong chroot). Việc này
  **không tạo thêm file fcitx5 nào** để tránh hai nơi ghi đè nhau (hook 0200 chạy
  SAU khi `includes.chroot` đã copy xong, nên bất kỳ file tĩnh nào việc này tạo tại
  `etc/skel/.config/fcitx5/` sẽ bị hook 0200 ghi đè vô ích). Xem bảng mục 6.

## 6. Quyết định hoãn / không làm trong việc này (ghi rõ lý do kỹ thuật, không phải bỏ quên)

| Việc | Vì sao không làm bằng file tĩnh trong `/etc/skel` |
| --- | --- |
| `user-places.xbel` (ép thêm mục "This PC" group trong Places panel) | `/etc/skel` được **copy y nguyên** sang `/home/<user>` lúc tạo user mới — nội dung file KHÔNG được template lại theo home directory thật. Một `user-places.xbel` tĩnh ghi cứng `file:///root` (hoặc bất kỳ path cố định) sẽ **SAI** cho mọi user thật (home thật là `/home/<tên user>`), vi phạm trực tiếp nguyên tắc "không âm thầm ghi dữ liệu sai" trong CLAUDE.md. Dolphin đã có fallback mặc định tự tính theo `$HOME` của từng user (Home/Desktop/Documents/Downloads/Trash) ngay cả khi KHÔNG có `user-places.xbel` — tức UI-002 phần "Home/Documents/Downloads/Desktop" đã đạt qua default của Dolphin, không cần ghi đè. Muốn thêm nhãn "This PC"/sắp xếp lại nhóm thật sự cần thao tác **lúc đăng nhập lần đầu** (biết `$HOME` thật) — thuộc luồng `namios-welcome` (xem mục 7), không phải file tĩnh đóng gói sẵn. |
| Icon riêng cho Kickoff/launcher, icon ổ đĩa, splash SDDM, nhạc hiệu | Chưa có asset nhị phân thật (xem `usr/share/namios-branding/README-PLACEHOLDER.md`) — KHÔNG tạo file ảnh giả để "cho đủ", giữ TBD đúng quy định CLAUDE.md "không TODO giả làm chức năng". |
| Test UI-001 bấm thử thật (Win/Win+E/Win+D/Win+L/PrintScreen/Alt+Tab) | Cần desktop KDE Plasma thật đang chạy (Wayland/X11 session) — container phát triển này **headless, không có desktop session** (xem `docs/_m0_inventory_raw.md`). Chỉ chạy được khi boot ISO trên VM/USB thật (Spike S-UI-3, ADR 0011). |
| Usability 15 người × 8 tác vụ × 90% (UI-006) | Cần pilot thật với người dùng thật — không thể mô phỏng trong môi trường build. |

## 7. Phụ thuộc chéo module: `namios-welcome` (UI-005)

Hook `distro/live-build/config/hooks/normal/0300-namios-welcome.hook.chroot` (thuộc
phạm vi việc này) lắp gói ứng dụng `namios-welcome` vào `/opt/namios/namios_welcome`
trong ảnh và tạo wrapper `/usr/bin/namios-welcome`, rồi tự chạy lần đầu đăng nhập
qua `etc/skel/.config/autostart/namios-welcome.desktop`. **Mã nguồn Python thật của
`namios_welcome` (PySide6, theo §5.2 đặc tả) do một luồng việc khác viết** (biến
`src/namios_welcome` hiện CHƯA tồn tại trong repo tại thời điểm viết file này —
`ls src/` không có thư mục này). Vì `config/hooks/*.hook.chroot` chạy **bên trong**
chroot và không có đường dẫn ngược ra ngoài repo host lúc build, cơ chế duy nhất
hợp lệ của `live-build` để đưa mã nguồn thật vào ảnh là qua `includes.chroot`
(copy tĩnh, build-time). Việc này đã dựng sẵn **điểm staging**:

```
distro/live-build/config/includes.chroot/opt/namios/namios_welcome-src/
```

— hiện chỉ có `README-PLACEHOLDER.md` (chưa có mã thật). Hook `0300` sẽ **chủ động
thất bại rõ ràng (`exit 1`, không build giả)** nếu thư mục này chưa được thay bằng
mã nguồn thật (`__init__.py`/`__main__.py`), đúng nguyên tắc CLAUDE.md "không giả
lập để báo đạt". Trước khi build ISO phát hành, người giữ module `namios_welcome`
cần đồng bộ `src/namios_welcome` (repo gốc) vào đúng đường dẫn staging trên trước
khi gọi `scripts/build-iso.sh` (bước đồng bộ đó KHÔNG thuộc phạm vi file nào việc
này được giao sửa — `auto/config` và `scripts/build-iso.sh` không thuộc quyền sửa
của việc này).

Luồng onboarding nội dung thật của `namios-welcome` (chọn cỡ chữ, bộ gõ Telex/VNI,
trình duyệt, app mở DOCX/XLSX/PDF, máy in, nhập dữ liệu từ Windows — UI-005) là mã
Python, **không phải nội dung của việc desktop/UI này** — việc này chỉ lo phần
"đóng gói chạy được lần đầu đăng nhập" (autostart + wrapper), không viết UI đó.

## 8. Checklist xác nhận khi có desktop thật (điền lại khi test, không tự đánh dấu trước)

- [ ] Win mở Kickoff
- [ ] Win+E mở Dolphin
- [ ] Win+D show desktop
- [ ] Win+L khóa màn hình
- [ ] PrintScreen mở Spectacle
- [ ] Alt+Tab chuyển cửa sổ khi IME Fcitx5 đang bật (VN-002 + UI-001 kết hợp)
- [ ] Double-click mở file/folder (không phải single-click)
- [ ] Mở DOCX/XLSX/PPTX/PDF ra đúng LibreOffice/Okular
- [ ] `namios-welcome` tự chạy lần đăng nhập đầu, có nút "không hiện lại"
- [ ] Taskbar dưới cùng có đủ: nút mở app, task list, system tray, đồng hồ
- [ ] Không có icon/âm thanh/font nào trùng tài sản Microsoft (rà bằng mắt + diff asset)
