# Plasma Splash Screen (ksplashqml) — NaMiOS Sen Việt

- **Mốc:** 11/11/2026 — vá lỗ hổng nhận diện cuối cùng trong luồng đăng
  nhập→desktop: ảnh chụp thật trên máy đã cài cho thấy màn hình NGAY SAU KHI
  gõ mật khẩu ở SDDM vẫn là splash **mặc định của KDE** (gradient
  xanh/tím + logo ">" + chữ "Plasma, de KDE") — chưa có theme splash riêng
  nào tồn tại trong repo trước bản này.
- **verified_on_host: NO** — chưa đăng nhập thật qua KDE Plasma để xác nhận
  splash hiển thị đúng thiết kế; container dựng không có `lb build`/boot QEMU
  sẵn trong phiên này. Xem mục 5 cho danh sách rủi ro cụ thể cần boot thật.

## 1. Ba theme khác nhau trên đường khởi động — đừng nhầm

| Giai đoạn | Theme/engine | Nơi ở trong repo |
| --- | --- | --- |
| Trước khi vào GRUB/initramfs load xong | **Plymouth** (`namios`, plugin two-step) | `usr/share/plymouth/themes/namios/` |
| Màn đăng nhập (gõ mật khẩu) | **SDDM** (`namios`, QML riêng) | `usr/share/sddm/themes/namios/` |
| **Ngay sau khi đăng nhập, lúc desktop đang tải** | **Plasma Splash Screen** (`ksplashqml`, gói `Plasma/LookAndFeel`) — **MỚI DỰNG Ở BẢN NÀY** | `usr/share/plasma/look-and-feel/org.namios.sen/` |

Ba theme này độc lập hoàn toàn với nhau (3 cơ chế kỹ thuật khác nhau: plugin
Plymouth / QML riêng SDDM / gói KPackage `Plasma/LookAndFeel` cho ksplashqml).
Trước bản này, Plymouth + SDDM đã có theme `namios` riêng; **chỉ riêng ô thứ
ba (Plasma splash) là KHÔNG CÓ gì** — ksplashqml rơi về theme `Breeze` mặc
định của KDE, đúng như ảnh chụp máy thật cho thấy.

## 2. File đã tạo (tất cả MỚI — không sửa file nào khác ngoài danh sách này)

| File | Vai trò |
| --- | --- |
| `usr/share/plasma/look-and-feel/org.namios.sen/metadata.json` | Khai báo gói KPackage `Plasma/LookAndFeel`, `KPlugin.Id = "org.namios.sen"` — định dạng Plasma 6 (`metadata.json`, KHÔNG phải `metadata.desktop` cũ). |
| `usr/share/plasma/look-and-feel/org.namios.sen/contents/splash/Splash.qml` | Giao diện splash thật — nền gradient ngà ấm, logo sen đỏ son, tên sản phẩm, thanh tiến trình đỏ son chạy theo `stage`. |
| `usr/share/plasma/look-and-feel/org.namios.sen/contents/images/NaMiOS_Symbol_Color.svg` | Bản sao logo sen (từ `usr/share/namios-branding/logo/NaMiOS_Symbol_Color.svg`) đóng gói **vào trong** package này — Splash.qml không tham chiếu đường dẫn tuyệt đối ra ngoài package, vì tiến trình `ksplashqml` chạy trong ngữ cảnh riêng, không chắc mọi đường dẫn tuyệt đối ngoài package đều "resolve" được như mong đợi. |
| `etc/xdg/ksplashrc` | Đặt `[KSplash] Engine=KSplashQML` + `Theme=org.namios.sen` ở tầng mặc định hệ thống (cascading KConfig, áp dụng cho MỌI user, kể cả user tạo sau). |
| `etc/skel/.config/ksplashrc` | Bản sao cùng nội dung cho HOME mới — khớp đúng cách `etc/skel/.config/plasmarc` + `etc/skel/.config/kdeglobals` đang đặt mặc định desktop theme/colorscheme trong repo này (ship ở CẢ HAI nơi, không chỉ một). |
| `usr/share/namios/docs/SPLASH.md` | Tài liệu này. |

**KHÔNG** có hook mới nào được tạo — xem mục 3 cho lý do.

## 3. Splash được đặt làm mặc định NHƯ THẾ NÀO — và tại sao KHÔNG cần hook

`ksplashqml` đọc nhóm cấu hình `[KSplash]` (khóa `Engine`/`Theme`) từ chuỗi
cascading chuẩn của KConfig: `~/.config/ksplashrc` đè lên `/etc/xdg/ksplashrc`
(tầng mặc định hệ thống). Bản này ship **cả hai lớp** với cùng giá trị:

```ini
[KSplash]
Engine=KSplashQML
Theme=org.namios.sen
```

Khi `startplasma-x11`/`startplasma-wayland` khởi động session, nó đọc đúng
nhóm này và chạy `ksplashqml org.namios.sen` (hoặc tương đương nội bộ).

**`Theme=org.namios.sen` được ksplashqml phân giải ra file QML như sau** (đối
chiếu từ hiểu biết mã nguồn `plasma-workspace/ksplash` — KPackage, không phải
suy đoán tên khóa):

1. Chuỗi `Theme` được dùng làm **đường dẫn gói** (`package.setPath(theme)`)
   cho `KPackage::Package("Plasma/LookAndFeel")`.
2. `KPackageStructure` của loại gói `Plasma/LookAndFeel` định nghĩa khóa nội
   bộ `splashmainscript` = **`contents/splash/Splash.qml`** (tên file cố
   định, phân biệt hoa/thường) bên trong thư mục gói.
3. KPackage/`QStandardPaths` tìm thư mục gói bằng cách quét thẳng
   `usr/share/plasma/look-and-feel/<Theme>/` trong các data dir chuẩn — **KHÔNG
   cần bước "cài đặt"/đăng ký riêng** (khác hẳn `.desktop`/`KService`, vốn cần
   `kbuildsycoca6`). Vì vậy: chỉ cần thư mục `org.namios.sen/` (khớp đúng tên
   với `KPlugin.Id` trong `metadata.json`, như đã làm ở bước 2 mục trên) tồn
   tại đúng chỗ là ksplashqml tìm thấy ngay — **không có "lệnh set-default"
   tương đương `plymouth-set-default-theme`** cho KSplashQML, nên **không cần
   hook mới** để "kích hoạt" gói này; chỉ cần đặt đúng khóa `ksplashrc` (đã
   làm ở trên) là đủ. Đây khác với Plymouth (cần hook
   `0140-plymouth-theme.hook.chroot` gọi `plymouth-set-default-theme` +
   `update-initramfs`) — hai cơ chế không giống nhau, không nên áp cùng một
   khuôn.

**Cố ý KHÔNG đặt** `kdeglobals [KDE] LookAndFeelPackage=org.namios.sen`:
khóa đó là theme **toàn cục** (ảnh hưởng cả color scheme/desktoptheme/icon
theme/cursor/splash cùng lúc khi đổi qua System Settings > Global Theme) —
đặt khóa đó sẽ **ghi đè** các lựa chọn đã cấu hình riêng rất kỹ (color scheme
`NaMiOS`, desktoptheme `NaMiOS-Sen`, icon theme `NaMiOS-Lotus` — xem
`etc/skel/.config/kdeglobals` + `etc/skel/.config/plasmarc`), vì gói
`org.namios.sen` ở đây **không có** `contents/defaults`/`contents/layout.js`
đầy đủ như một Global Theme thật — nếu bị gán làm `LookAndFeelPackage`, các
phần Global Theme không tự định nghĩa (ví dụ colorscheme) sẽ rơi về giá trị
trống/mặc định KPackage, có thể **xóa mất** cấu hình màu đã chọn. Phạm vi của
gói này CHỈ LÀ phần splash — đúng như yêu cầu nhiệm vụ.

## 4. Thiết kế Splash.qml

- **Hợp đồng kỹ thuật ksplashqml** (ghi đầy đủ trong comment đầu file
  `Splash.qml`): root `Rectangle` KHÔNG gán `width`/`height` cố định — engine
  dùng `QQuickView::SizeRootObjectToView`, tự đặt kích thước root item theo
  đúng màn hình thật mỗi lần resize (đây là cách "sized to the screen" được
  hiện thực, không phải số cứng `1920x1080` như theme SDDM — SDDM-greeter
  dùng cơ chế resize khác). `property int stage` (mặc định `0`) là property
  DUY NHẤT engine ghi vào (`setProperty("stage", n)`, `n` chạy 1→6 theo các
  mốc khởi động session) — không đổi tên property này.
- **Màu nền:** gradient ngà ấm `#FBF8F2 → #EFE3D1` — **đúng hai mã màu**
  `BackgroundStartColor`/`BackgroundEndColor` mà theme Plymouth `namios` đã
  dùng (`usr/share/plymouth/themes/namios/namios.plymouth`), để splash Plasma
  "nối tiếp" đúng nhận diện với splash Plymouth sớm hơn trong cùng lượt khởi
  động, thay vì bịa một cặp màu mới. Tuân thủ quy tắc "sen quý không đặt nền
  đen" (`docs/design/DESIGN-SYSTEM.md` §1) — **không dùng xanh/tím KDE**.
- **Logo:** `NaMiOS_Symbol_Color.svg` (hoa sen 7 cánh đỏ son, tâm vàng — bản
  SVG hình học đơn giản, không gradient/filter, tự ghi trong file nguồn là
  "reliable at OS boot") căn giữa màn hình, 132×132dp, fade-in bằng
  `SequentialAnimation` khi `stage` chạm mốc đầu tiên — cùng cấu trúc
  `introAnimation` của `Splash.qml` gốc trong `org.kde.breeze`
  (`PropertyAction` đặt `opacity=0` → `PauseAnimation` → `NumberAnimation`
  fade tới 1).
- **Chữ:** "NaMiOS" (32px, Inter DemiBold, màu mực đêm `#182E3B`) + "Hệ điều
  hành cho người Việt" (16px, Inter Regular, màu `#52646B`) — đúng phông +
  màu token `text.primary`/`text.secondary` sáng của `DESIGN-SYSTEM.md` §1.2.
- **Thanh tiến trình:** 480×6dp — đúng kích thước `ProgressBarWidth`/
  `ProgressBarHeight` của Plymouth theme `namios` — nền `#E3D6C2` (token
  `border.subtle` sáng),
  phần đã đầy màu đỏ son `#C93643`, rộng = `parent.width × (stage / 6)` với
  `Behavior on width` (220ms, easing OutCubic) — tăng dần mượt theo từng mốc
  `stage` thật, không phải thanh chạy vô hạn giả.
- **Không dùng** Kirigami/PlasmaComponents/QtQuick.Controls, không
  `Qt5Compat.GraphicalEffects`/`ShaderEffect` — giữ đúng nguyên tắc "không
  phụ thuộc GPU/shader" đã chọn cho theme SDDM `namios` (an toàn dưới
  `QT_QUICK_BACKEND=software`, QEMU/TCG không GPU).
- **Không** còn chữ/logo "KDE"/"Plasma"/"Breeze" nào trong file này.

## 5. Kiểm tra cú pháp đã làm được trong sandbox này — và rủi ro CHƯA xác nhận

**`qmllint`/`qmllint6` KHÔNG có sẵn** trong container dựng này (không có
`qt6-declarative-dev`, không có mạng để `apt install`). Đã thay bằng:

1. **Đối chiếu thủ công từng dòng** với hợp đồng kỹ thuật `ksplashqml` thật
   (`SizeRootObjectToView`, `setProperty("stage", n)`, khóa KPackage
   `splashmainscript` → `contents/splash/Splash.qml`) — ghi lại ngay trong
   comment đầu `Splash.qml`, không phải chỉ ở tài liệu này.
2. **Kiểm cân bằng cú pháp bằng script** (bóc comment `//`/`/* */` + nội dung
   chuỗi `"..."` trước khi đếm, tránh đếm nhầm dấu ngoặc trong văn bản): dấu
   `{}`/`()`/`[]` đều cân bằng về 0, không có điểm nào âm (không đóng dư) ở
   bất kỳ vị trí nào trong file. Đã xác nhận `import QtQuick 2.15` đúng cú
   pháp, property `stage` tồn tại đúng kiểu `int`, 2 `GradientStop` đúng cặp.

**Rủi ro CHƯA xác nhận (`verified_on_host: NO`) — cần boot KDE Plasma thật**:

1. KPackage có thực sự phân giải `Theme=org.namios.sen` ra đúng
   `Splash.qml` này không (không lỗi "theme không tồn tại", không rơi về
   `Breeze` mặc định).
2. `SizeRootObjectToView` có đặt đúng kích thước root `Rectangle` trên MÀN
   HÌNH THẬT (không bị 0×0 hay cắt mép) ở các độ phân giải khác 1920×1080.
3. `Image` có đọc được `../images/NaMiOS_Symbol_Color.svg` qua đường dẫn
   tương đối, đúng tiến trình `ksplashqml` (khác tiến trình Dolphin/Plasma
   Shell thông thường đã test SVG nhiều lần trong repo này).
4. Property `stage` có thực sự được engine gán 1→6 hay không — nếu không,
   thanh tiến trình đứng yên ở 0 (vẫn AN TOÀN về mặt hiển thị — không trắng/
   không lỗi — chỉ là không có cảm giác "đang tải").
5. Cơ chế cascading `/etc/xdg/ksplashrc` dưới `~/.config/ksplashrc` của từng
   user — có user nào tự có `~/.config/ksplashrc` riêng đè lên không (không
   áp dụng cho ảnh mới cài, nhưng cần nhớ nếu debug trên máy đã dùng qua).

## 6. Audit — các mặt còn hiện thương hiệu KDE/Breeze/"Plasma" khác (báo cáo,
   KHÔNG tự sửa trong phạm vi nhiệm vụ này — chỉ sở hữu các file ở mục 2)

Đã rà soát luồng đăng nhập→desktop (grep toàn bộ `includes.chroot` cho chuỗi
hiển thị + đối chiếu hiểu biết về các khung KDE Frameworks liên quan). Kết
quả — liệt kê TRUNG THỰC, không giấu:

1. **Viền cửa sổ (window decoration) — ĐÃ BIẾT, KHÔNG PHẢI PHÁT HIỆN MỚI.**
   `etc/skel/.config/kwinrc` có sẵn section `[org.kde.kdecoration2]` đặt
   decoration riêng `NaMiOSLotus` (Aurorae SVG) **nhưng đang bị comment tạm**
   (dòng 56-65, do nhóm sở hữu file đó hoãn bật vì nghi ngờ treo đăng nhập
   dưới QEMU/TCG, chưa boot-test loại trừ được — xem comment đầy đủ trong
   chính file). Hệ quả: viền cửa sổ hiện rơi về decoration mặc định của KWin
   (họ "Breeze" — bo góc hiện đại theo ghi chú của họ, không phải chữ "KDE"
   hiện ra, nhưng là ngôn ngữ hình ảnh khác biệt). Đây là quyết định đã có
   chủ đích + kế hoạch bật lại, không phải việc bỏ sót — nêu lại ở đây chỉ để
   đủ cho câu hỏi audit, KHÔNG đụng vào (không thuộc phạm vi sở hữu nhiệm vụ
   này: "KHÔNG đụng ... file của theme khác").
2. **Menu "Trợ giúp > Giới thiệu về KDE" (About KDE) trong MỌI ứng dụng KDE**
   (Konsole/Dolphin/Kate/Ark/Gwenview/kcalc...) — mục này + hộp thoại của nó
   (logo bánh răng "K", chữ "KDE is produced by the KDE Community", liên kết
   kde.org) được `KHelpMenu`/`KXmlGuiWindow` trong chính thư viện **KDE
   Frameworks** tự thêm vào mọi app dùng khung đó — KHÔNG thể phủ qua
   `.desktop`/hook như các lớp phủ `Name[vi]` đã làm (hook
   `0130-desktop-names-vi`/`0454-namios-apps-rebrand` chỉ đổi được khóa
   `.desktop`, không đụng vào UI runtime của app). Sửa thật sẽ cần patch
   `libkf6xmlgui` — ngoài phạm vi "không đụng nội tạng KDE" của nhiệm vụ này.
3. **Hộp thoại "Lấy thêm..." (KNewStuff)** — ví dụ chuột-phải Desktop > "Thêm
   tiện ích..." > "Tải thêm tiện ích mới", hoặc Discover khi duyệt hình
   nền/global theme — các hộp thoại này hiển thị chữ "KDE Store"/liên kết
   store.kde.org, baked vào khung `KNewStuff` của KDE Frameworks, cùng loại
   giới hạn như mục 2.
4. **Tên phiên đăng nhập (session) trong bộ chọn phiên của SDDM** — theme
   SDDM `namios` tự viết (`Main.qml`) hiển thị đúng `model.name` từ
   `sessionModel` khi có >1 phiên; tên đó lấy từ các file
   `/usr/share/xsessions/*.desktop` do CHÍNH gói `plasma-workspace`
   (x11/wayland) cài, thường là chuỗi gốc **"Plasma (X11)"/"Plasma
   (Wayland)"** — các file đó KHÔNG nằm trong repo này (không có gì để
   `includes.chroot` đè lên trực tiếp) và KHÔNG nằm trong danh sách đã phủ
   `Name[vi]` của hook `0130`/`0454` (hai hook đó chỉ phủ
   `applications/*.desktop` + `systemsettings/categories/*.desktop`, không
   phủ `xsessions/*.desktop`). Đây là một khoảng trống THẬT, CỤ THỂ, có thể
   vá bằng đúng cơ chế PA-A (shadow `/usr/local/share/xsessions/`) nhóm
   `0130` đang dùng — đề xuất nhóm sở hữu lớp phủ tên đó (`UX12`/l10n) thêm
   2 dòng `Name[vi]` cho 2 id này ở một đợt riêng.
5. **Trang "Giới thiệu hệ thống" (kinfocenter "About System")** — tên/logo
   hệ điều hành ĐÃ đúng NaMiOS (vá qua `os-release LOGO=`/`PRETTY_NAME`, hook
   `0120-namios-branding.hook.chroot`, xác nhận file tĩnh `etc/os-release`
   đã có `NAME`/`PRETTY_NAME` NaMiOS). Cùng trang đó **vẫn đúng** hiện dòng
   "KDE Plasma Version: 6.3.6"/"KDE Frameworks Version: ..." — đây là thông
   tin thành phần kỹ thuật THẬT (giống cách mọi distro Linux khác vẫn hiện
   "Linux kernel: 6.x"), KHÔNG coi là lỗi mạo danh — phù hợp chính sách "không
   bịa/không giấu nguồn" đã áp dụng ở nhiều nơi khác trong repo này. KHÔNG đề
   xuất che dòng này.

**Không tìm thấy** chuỗi hiển thị nào khác giống "Plasma, de KDE" (bản gốc đã
sửa — splash) còn sót trong `includes.chroot` qua grep trực tiếp; các mục 2-4
không nằm trong `includes.chroot` (đến từ chính binary/package KDE đã cài),
nên không grep ra được bằng công cụ — liệt kê từ hiểu biết khung KDE
Frameworks, cần boot thật để xác nhận chữ/hình chính xác trên máy Debian 13
trixie đang dùng.
