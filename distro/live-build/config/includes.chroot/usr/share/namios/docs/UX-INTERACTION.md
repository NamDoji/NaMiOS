# NaMiOS — Lớp tương tác "ít chạm" kiểu macOS trên nền Windows-11 (UX-INTERACTION)

- **Wave:** macOS-style "few-touch" interaction layer, 10/11/2026 (giao việc ưu tiên cao nhất của Cuong).
- **Nền tảng không đổi:** visual Windows-11-hiện-đại đã có (taskbar dưới, Kickoff, panel nổi kính mờ,
  theme NaMiOS-Sen, Aurorae đang HOÃN BẬT — xem comment trong `kwinrc`/`plasmarc`, KHÔNG đụng).
- **verified_on_boot: NO cho TOÀN BỘ file này.** Môi trường dựng không có desktop session KDE Plasma
  (container headless — xem ADR 0011). Mọi dòng dưới đây là cấu hình đã viết + đã đối chiếu tài liệu/
  nguồn KWin công khai, CHƯA phải hành vi đã quan sát trên máy thật. Người cầm ISO lên máy/VM thật
  (ưu tiên phiên Wayland thật, không phải X11, vì mục 2 chỉ hoạt động trên Wayland) phải bấm thử từng
  dòng rồi điền lại checklist ở cuối file.

## 1. File đã sửa / đã tạo

| File | Loại thay đổi |
| --- | --- |
| `etc/skel/.config/kwinrc` | Thêm khoá vào `[Plugins]` + thêm section mới `[Effect-overview]` |
| `etc/skel/.config/kglobalshortcutsrc` | Thêm section mới `[org.kde.krunner.desktop]` |
| `etc/skel/.config/kdeglobals` | **KHÔNG sửa** — xem mục 4 "Vì sao không đụng kdeglobals" |
| `usr/share/namios/docs/UX-INTERACTION.md` | File này (mới) |

## 2. Overview — "Mission Control" kiểu macOS (kwinrc)

| Khoá | Giá trị | Lý do 1 dòng |
| --- | --- | --- |
| `[Plugins] overviewEnabled` | `true` | Bật effect Overview của KWin 6 (xem toàn bộ cửa sổ + desktop ảo + gõ tìm kiếm ngay trong lưới — tương đương Mission Control). Đây là khoá CHUẨN effect-loader đọc cho plugin id `overview` (đối chiếu nhiều dump kwinrc Plasma 6 + lệnh tham chiếu chính thức `kwriteconfig6 --group Plugins --key overviewEnabled`). |
| `[Effect-overview] BorderActivate` | `7` | Gán Overview vào **đúng 1** hot corner (góc **trên-trái**), theo enum `ElectricBorder` của KWin (`ElectricTop=0 … ElectricTopLeft=7 … ElectricNone=9`). CHỈ 1 góc — không gán cả 4 — để tránh kích hoạt nhầm, đúng yêu cầu đặc tả wave này. |

**Cử chỉ 4-ngón vuốt lên trên touchpad (Wayland):** KHÔNG có khoá kwinrc nào được thêm cho việc này
vì — theo nhiều nguồn cộng đồng KWin độc lập đối chiếu được — cử chỉ 4-ngón lên/xuống của hiệu ứng
Overview trên Wayland là hành vi **gắn cứng (hard-coded) trong chính effect**, không đọc qua
`kcm_touchpad` và không có khoá cấu hình nào trong `kwinrc` để gán/đổi. Cử chỉ này tự hoạt động khi
`overviewEnabled=true` **và** phiên đang chạy **Wayland** (không chạy trên X11). Không bịa thêm khoá
giả cho mục này — xem TODO ở mục 5.

**Plasma 6 đã BẬT Overview + hot-corner top-left SẴN theo mặc định** kể cả không có 2 dòng trên — các
dòng này chỉ **chốt tường minh** (chống việc một bản cập nhật tương lai đổi mặc định mà không ai biết),
không phải bật từ con số 0.

**Rollback:** xoá dòng `overviewEnabled=true` (hoặc đổi `false`) và/hoặc xoá hẳn section
`[Effect-overview]` — KWin rơi về mặc định build-in, không crash.

## 3. KRunner kiểu Spotlight — Meta+Space (kglobalshortcutsrc)

| Khoá | Giá trị | Lý do 1 dòng |
| --- | --- | --- |
| `[org.kde.krunner.desktop] _launch` | `Meta+Space␉Alt+Space␉Alt+F2,Alt+Space␉Alt+F2,KRunner` | Thêm **Meta+Space** làm phím tắt mở KRunner (tìm kiếm toàn cục kiểu Spotlight), **giữ nguyên** `Alt+Space`/`Alt+F2` cũ (KHÔNG xoá — tránh phá vỡ thói quen người dùng Linux sẵn có). (`␉` = tab thật trong file, không phải ký tự hiển thị.) |

- **Meta một mình vẫn là mở Kickoff** (`kwinrc [ModifierOnlyShortcuts]`, KHÔNG đổi). Không trùng:
  `ModifierOnlyShortcuts` chỉ kích hoạt khi nhấn **riêng** Meta rồi thả ra mà **không** kèm phím nào
  trong lúc giữ — bấm Meta+Space sẽ huỷ điều kiện đó ngay từ đầu, nên KWin chỉ chạy shortcut KRunner,
  không chạy cả hai cùng lúc. Đây là hành vi chuẩn của KWin `ModifierOnlyShortcuts`, không phải suy
  đoán riêng của wave này.
- **Rủi ro cần xác nhận cao nhất của file này:** tên group desktop-file-id cho KRunner trong
  `kglobalshortcutsrc` **chưa chắc chắn 100%**. Đã đối chiếu nhiều dotfiles KDE thật: đa số dùng tên
  group cũ `[krunner.desktop]`; ít nhất một nguồn khác nói Plasma 6 đã đổi sang kiểu reverse-DNS
  `org.kde.krunner.desktop` (giống hướng đổi tên đã xác nhận đúng cho `dolphin`/`spectacle` trong
  CHÍNH file `kglobalshortcutsrc` này). Đã chọn `org.kde.krunner.desktop` làm **phương án chính** để
  nhất quán với quy ước Plasma 6 dùng trong 2 entry kia — **PHẢI kiểm tra lại trên máy Debian 13
  trixie thật**:
  1. Bấm Meta+Space trên desktop thật.
  2. Nếu KRunner KHÔNG mở: chạy `kreadconfig6 --file kglobalshortcutsrc --group org.kde.krunner.desktop --key _launch` rồi `kreadconfig6 --file kglobalshortcutsrc --group krunner.desktop --key _launch` để xem KWin/krunner thật đang tự đăng ký action ở group nào.
  3. Nếu đúng là group cũ `krunner.desktop`: dời khối cấu hình sang group đó (hoặc gán lại qua System Settings > Shortcuts > KRunner) rồi build lại.
- **Fail-safe:** nếu tên group sai, Meta+Space chỉ không làm gì (không crash, không mất Alt+Space/
  Alt+F2 vì đó là default riêng của KWin/krunner tự đăng ký, độc lập với dòng này).
- **Rollback:** xoá nguyên section `[org.kde.krunner.desktop]` vừa thêm.

## 4. Window snapping / tiling kiểu Windows — giữ nguyên, không cần sửa

`kwinrc [Windows] ElectricBorderMaximize=true` / `ElectricBorderTiling=true` **đã có từ wave trước**
(kéo cửa sổ ra biên màn hình để maximize/tile) — xác nhận lại, giữ nguyên, không đổi giá trị.

**Tiling nâng cao kiểu "giữ Shift khi kéo" (Plasma 6 Custom Tiling editor, Meta+T) — TODO, KHÔNG thêm
khoá:** editor tiling tuỳ biến của Plasma 6 lưu cấu hình vào các section động `[Tiling][<uuid>]` được
chính Plasma **tự sinh UUID lúc người dùng vẽ vùng tile qua GUI** — không có một khoá tĩnh đơn giản
kiểu "bật/tắt chế độ kéo-giữ-Shift" để soạn trước trong `/etc/skel`. Hành vi "giữ Shift khi kéo để
snap vào vùng tile đã vẽ" đã là mặc định của chính trình soạn tiling (Meta+T) khi người dùng tự vẽ
layout — không cần thêm khoá nào ở đây mới có. Không bịa section `[Tiling]` giả với UUID ngẫu nhiên.

## 5. Dialog/xác nhận ít hơn (mục 4 đặc tả) — chủ yếu TODO, nằm NGOÀI 3 file được giao

Đã rà: 2 "nag dialog" phổ biến nhất (macOS hay tắt) có khoá THẬT nhưng **nằm ở file KHÁC, ngoài phạm
vi file được giao sửa cho việc này** (chỉ `kwinrc`/`kglobalshortcutsrc`/`kdeglobals`):

| Hộp thoại | Khoá thật (tham khảo) | File thật chứa khoá | Vì sao KHÔNG sửa ở đây |
| --- | --- | --- | --- |
| Hỏi xác nhận khi đăng xuất | `[General] confirmLogout=false` | `ksmserverrc` | Không có trong danh sách 3 file được giao sửa cho việc này — để TODO cho wave sau có đúng file trong phạm vi. |
| Hỏi xác nhận khi xoá vào Thùng rác / đổ Thùng rác | `[Confirmations] ConfirmTrash=false` / `ConfirmEmptyTrash` | `kiorc` | Y như trên — **ngoài ra đặc tả gốc cũng yêu cầu GIỮ delete-to-trash**, nên dù có sửa cũng không đổi giá trị này. |

**Giữ nguyên, không đổi (theo đúng yêu cầu "bảo thủ"):**
- `kdeglobals [KDE] SingleClick=false` (double-click để mở, không chuyển single-click) — **không chạm**,
  đã đúng yêu cầu "giữ double-click".
- Hành vi xoá-vào-Thùng-rác mặc định của KIO — không đổi ở tầng nào.

## 6. Vì sao không đụng `kdeglobals`

Đã rà toàn bộ các khoá tương tác (interaction, không phải font/màu — font Inter + màu AccentColor đã
chốt ở wave trước, KHÔNG đụng theo đúng chỉ định) có thể liên quan "ít chạm hơn": không tìm thấy thêm
khoá nào trong `kdeglobals` vừa (a) thật/có tài liệu/đối chiếu được, vừa (b) chưa được wave trước set,
vừa (c) nằm trong phạm vi "tương tác" của đặc tả này (Overview/Spotlight/tiling/dialog). Những khoá
còn thiếu thật sự liên quan ("ít click hơn") đều nằm ở `ksmserverrc`/`kiorc` (xem mục 5) — ngoài 3 file
được giao. Quyết định: **không sửa `kdeglobals`** trong wave này, ghi lại lý do ở đây để minh bạch
(không phải bỏ quên).

## 7. TODO / chưa xác nhận được khoá đúng (không bịa, để trống đúng quy định CLAUDE.md)

- Cử chỉ 4-ngón-vuốt-lên touchpad mở Overview trên Wayland thật — không có khoá để gán, chỉ cần xác
  nhận BẰNG MẮT hiệu ứng nào thực sự chạy (Overview hay Desktop Grid, tuỳ bản KWin) — xem mục 2.
- Tên group `kglobalshortcutsrc` đúng cho KRunner (`org.kde.krunner.desktop` vs `krunner.desktop`) —
  xem mục 3, PHẢI xác nhận bằng `kreadconfig6` trên máy thật.
- Phím tắt mặc định riêng của hiệu ứng Overview (thường là `Meta+W` theo tài liệu công khai) — KHÔNG
  thêm entry `[kwin] Overview=...` vào `kglobalshortcutsrc` vì chưa chắc đúng tên action-id chuỗi
  chính xác (`Overview`/`Toggle Overview`/...) mà không có KWin thật để introspect qua
  `qdbus org.kde.kglobalaccel`; action này tự effect đăng ký khi KWin load effect, không cần ta khai
  tĩnh ở đây — không có rủi ro mất chức năng, chỉ là không "chốt tường minh" được như Overview/KRunner.
  Không trùng Meta+Space (phím W khác phím Space).
- Tiling "giữ Shift khi kéo" của Custom Tiling editor (Meta+T) — xem mục 4, không có khoá tĩnh để
  bật/tắt kiểu này trong `/etc/skel`.
- Giảm dialog đăng xuất/Thùng-rác — xem mục 5, khoá thật nằm ở `ksmserverrc`/`kiorc`, ngoài phạm vi
  file được giao cho việc này.

## 8. Checklist xác nhận trên máy thật (điền khi có desktop, không tự đánh dấu trước)

- [ ] Rê chuột lên góc trên-trái → Overview mở (Wayland VÀ X11 nếu máy chạy X11)
- [ ] Overview KHÔNG tự mở khi rê chuột qua 3 góc còn lại
- [ ] (Wayland) 4 ngón vuốt lên trên touchpad → ghi lại hiệu ứng nào thực sự chạy
- [ ] Bấm Meta (một mình, thả ra ngay) → mở Kickoff, KHÔNG mở KRunner
- [ ] Bấm Meta+Space → mở KRunner, KHÔNG mở Kickoff
- [ ] Bấm Alt+Space và Alt+F2 → vẫn mở KRunner như cũ (chưa bị mất)
- [ ] Nếu Meta+Space không chạy: chạy 2 lệnh `kreadconfig6` ở mục 3, sửa group, build lại
- [ ] Kéo cửa sổ ra biên màn hình → vẫn maximize/tile như trước (không đổi, chỉ xác nhận chưa hỏng)
- [ ] Double-click vẫn mở file/app (chưa chuyển single-click)
