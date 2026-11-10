# NaMiOS — Thói quen Windows trên desktop (WINDOWS-HABITS)

- **Wave:** "Windows user habits" cho người dùng ít rành kỹ thuật (10/11/2026).
- **Trọng tâm:** F5 / chuột-phải → Refresh, + vài thói quen Windows nhỏ khác, chỉ
  làm cái nào xác minh được là THẬT, an toàn, nằm trong phạm vi file được giao.
- **verified_on_host: NO cho TOÀN BỘ file này.** Môi trường dựng không có desktop
  session KDE Plasma (container headless, xem ADR 0011 + `docs/_m0_inventory_raw.md`).
  Mọi kết luận dưới đây đến từ **đọc trực tiếp mã nguồn KDE thật** (invent.kde.org,
  nhánh `master` — tức nhánh phát triển Plasma 6/KF6, không phải suy đoán từ
  trí nhớ) + đối chiếu Debian 13 trixie package tracker, KHÔNG phải quan sát trên
  máy thật. Người cầm ISO lên máy/VM thật phải bấm thử từng dòng ở mục 6 rồi điền
  lại checklist.

## 0. Kết luận chính (đọc trước)

Phần lớn các thói quen Windows được yêu cầu **ĐÃ CÓ SẴN trong Plasma 6 theo mặc
định** — KHÔNG cần thêm cấu hình gì để hoạt động, chỉ cần CHỐT TƯỜNG MINH (pin)
để không bị một bản cập nhật tương lai đổi mặc định mà không ai biết, và tài liệu
hoá rõ bằng chứng. Một phím tắt KHÔNG được thêm (F5 toàn cục) vì rủi ro phá vỡ
hành vi ở mọi app khác — giải thích đầy đủ ở mục 2. Hai món "Thùng rác"/"Máy này"
trên desktop KHÔNG làm trong wave này vì nằm ngoài phạm vi file được giao — giải
thích ở mục 4.

## 1. File đã sửa / đã tạo trong wave này

| File | Loại thay đổi |
| --- | --- |
| `etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc` | Thêm `[Containments][2][General] url=desktop:/` (chốt Folder View) + comment giải thích vì sao Thùng rác/Máy này chưa làm |
| `etc/skel/.config/kglobalshortcutsrc` | Thêm comment giải thích vì sao KHÔNG có entry F5 (không đổi khoá nào) |
| `etc/skel/.config/kwinrc` | **KHÔNG sửa** — không có cơ chế F5/refresh nào thuộc tầng KWin cần chốt |
| `etc/skel/.config/kdeglobals` | **KHÔNG sửa** — đã rà, không có khoá "thói quen Windows" nào còn thiếu mà an toàn/có tài liệu (xem mục 5) |
| `etc/skel/.config/khotkeysrc` | **KHÔNG tạo** — KHotkeys đã khai tử, không được Plasma 6/Debian trixie đọc (xem mục 3) |
| `etc/skel/.config/kglobalaccel` | **KHÔNG tạo** — "kglobalaccel" là tên DAEMON (kglobalaccel6), không phải tên file cấu hình; file cấu hình thật của daemon này CHÍNH LÀ `kglobalshortcutsrc` đã có ở trên. Tạo một file rời tên "kglobalaccel" sẽ là file rác không ai đọc. |
| `usr/local/bin/*refresh*` (helper script) | **KHÔNG tạo** — không có primitive D-Bus/CLI an toàn nào để "vẽ lại icon desktop" ngoài khởi động lại toàn bộ `plasmashell` (rủi ro, bị đặc tả wave này cấm) — xem mục 2.3 |
| `usr/share/namios/docs/WINDOWS-HABITS.md` | File này (mới) |

## 2. F5 / chuột-phải → Refresh

### 2.1 Dolphin (file manager) — F5 = Reload, ĐÃ LÀ mặc định, xác nhận bằng mã nguồn

Đối chiếu trực tiếp `dolphin.git` (`invent.kde.org/system/dolphin`,
`src/dolphinmainwindow.cpp`):

```cpp
QAction *redisplay = KStandardAction::redisplay(this, &DolphinMainWindow::reloadView, actionCollection());
```

`KStandardAction::redisplay` tra bảng `KStandardShortcut::Reload` — đối chiếu
trực tiếp `kconfig.git` (`invent.kde.org/frameworks/kconfig`,
`src/gui/kstandardshortcut.cpp`):

```cpp
{Reload, "Reload", ..., QList<QKeySequence>{Qt::Key_F5, Qt::Key_Refresh}}
```

→ **F5 mở lại (reload) thư mục hiện tại trong Dolphin là hành vi KDE/Qt gốc,
không cấu hình gì thêm.** Đây là shortcut tầng ứng dụng (Qt `WindowShortcut`,
scope theo cửa sổ Dolphin đang có focus) — **không** đi qua `KGlobalAccel`/
`kglobalshortcutsrc`, nên không có khoá nào cần thêm vào file cấu hình nào cả.
**Kết luận: CHỈ CẦN XÁC NHẬN, không cần sửa file.**

### 2.2 Desktop — "Refresh Desktop" (F5) CŨNG ĐÃ CÓ SẴN, không phải placebo

NaMiOS dùng containment Desktop `plugin=org.kde.desktopcontainment`
(`etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc`,
`[Containments][2]` — KHÔNG đổi ở wave này, đã đúng từ trước). Đối chiếu trực
tiếp `plasma-desktop.git`
(`containments/desktop/plugins/folder/foldermodel.cpp`):

```cpp
QAction *refresh = new QAction(QIcon::fromTheme(QStringLiteral("view-refresh")), i18n("&Refresh View"), this);
refresh->setShortcut(QKeySequence(QKeySequence::Refresh));   // F5 / Key_Refresh
connect(refresh, &QAction::triggered, this, &FolderModel::refresh);
...
action->setText(m_usedByContainment ? i18n("&Refresh Desktop") : i18n("&Refresh View"));
```

→ Khi `org.kde.desktopcontainment` phục vụ làm **containment của desktop**
(đúng trường hợp NaMiOS), action này đổi nhãn thành **"Refresh Desktop"**, luôn
xuất hiện trong menu chuột-phải desktop, và có shortcut `QKeySequence::Refresh`
= F5 gắn sẵn ở tầng Qt `WindowShortcut` (áp dụng khi cửa sổ/surface desktop
đang active — ví dụ ngay sau khi bấm Meta+D "Show Desktop", hoặc click vào
vùng trống trên desktop). Đây **KHÔNG phải placebo** — bấm F5 khi desktop đang
active sẽ gọi `FolderModel::refresh()` thật (quét lại nội dung `desktop:/`).

Vì action này đã tồn tại SẴN trong chính plugin KDE đang dùng, **không cần
thêm bất kỳ khoá nào** — chỉ cần chốt rõ containment đang ở chế độ Folder View
(mục 2.4) để action này thực sự có bề mặt "icon trên desktop" để refresh.

**Lưu ý trung thực:** hành vi chính xác của Qt `WindowShortcut` khi "desktop"
là một containment Plasma Shell (không phải cửa sổ ứng dụng thông thường) —
tức điều kiện "khi nào desktop được coi là active" — **chưa xác nhận bằng mắt
trên máy thật**. Về lý thuyết (theo mã nguồn + ngữ nghĩa Qt chuẩn) action sẽ
chạy khi desktop/FolderView có focus; đây là phần duy nhất trong mục 2 còn
`verified_on_boot: NO` thực sự cần người cầm máy thật bấm thử (xem checklist
mục 6).

### 2.3 Vì sao KHÔNG thêm một binding F5 toàn cục (KGlobalAccel/khotkeys)

Đã cân nhắc nghiêm túc 3 phương án đặc tả gợi ý và loại cả 3, có lý do kỹ
thuật xác minh được:

| Phương án | Vì sao KHÔNG làm |
| --- | --- |
| Thêm `F5=...` vào `kglobalshortcutsrc` (global shortcut KWin/KGlobalAccel) | F5 đã là `KStandardShortcut::Reload` ở tầng ứng dụng trong **hầu hết app Qt/KDE** (Dolphin, System Settings, Okular, nhiều app KDE khác) và **ngoài KDE** (hầu hết trình duyệt F5=reload trang, LibreOffice Impress F5=bắt đầu trình chiếu). `KGlobalAccel` hoạt động bằng grab phím **toàn hệ thống**; System Settings > Phím tắt tự cảnh báo khi một tổ hợp phím đã dùng ở tầng ứng dụng khác — đúng tín hiệu cho thấy đây là xung đột THẬT, không phải lý thuyết. Gán F5 toàn cục có rủi ro cướp phím này khỏi MỌI app khác đang có focus — đúng loại rủi ro "đừng làm hỏng hệ thống" mà đặc tả wave này yêu cầu tránh, nhân rộng ra hơn cả phạm vi riêng `plasmashell`. |
| Khotkeys (`khotkeysrc`, gán F5 → script/D-Bus) | `KHotkeys` (daemon đọc file này) đã bị khai tử upstream từ trước Plasma 6 — README chính thức của repo (`invent.kde.org/plasma/khotkeys`): *"KHotkeys is no longer maintained. The last maintained version is in the Plasma/5.27 branch."* Repo hiện ở trạng thái **Archived/read-only**. Debian 13 (trixie) **không có gói `khotkeys`** (packages.debian.org/trixie/khotkeys trả lỗi "không có kết quả"). Tạo `khotkeysrc` trong `/etc/skel` sẽ là file **chết** — không daemon nào đọc nó trên hệ Plasma 6 mà NaMiOS dựng — vi phạm trực tiếp nguyên tắc CLAUDE.md "không TODO giả làm chức năng". |
| Script `usr/local/bin/*refresh*` + gán phím gọi "restart/reload plasmashell" | Không có D-Bus method public nào của `org.kde.plasmashell` để "chỉ vẽ lại icon desktop" (đã rà `foldermodel.cpp`: `refresh()` là slot C++ riêng của instance QML, không export D-Bus). Phương án "nuclear" duy nhất là `plasmashell --replace &` (khởi động lại toàn bộ shell) — **đích danh loại rủi ro đặc tả wave này yêu cầu KHÔNG được ship** ("đừng làm hỏng plasmashell"). Vì mục 2.1+2.2 đã cho F5 hoạt động đúng kiểu Windows mà không cần việc này, không có lý do chấp nhận rủi ro đó. |

**Kết luận mục 2:** F5 trên Dolphin và F5 trên Desktop **đã hoạt động kiểu
Windows mà không cần NaMiOS cấu hình gì thêm** — đây là phát hiện chính của
wave này, không phải "chưa làm". Việc "làm" ở đây là xác minh + chốt containment
Folder View (mục 2.4) + viết lại bằng chứng, không phải thêm khoá shortcut.

### 2.4 Chốt containment Desktop = Folder View (hiện icon, giống Windows)

`etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc` đã thêm:

```ini
[Containments][2][General]
url=desktop:/
```

Đối chiếu `plasma-desktop.git`
(`containments/desktop/package/contents/config/main.xml`, kcfg): khoá `url`
mặc định **đã là** `"desktop:/"` — dòng trên chỉ CHỐT TƯỜNG MINH, không đổi
hành vi hiện tại. Đã đối chiếu thêm `ConfigLocation.qml` (hộp thoại "Configure
Desktop..."): 3 lựa chọn hiển thị trong UI (Desktop folder / Activity hiện tại
/ Thư mục khác) đều chỉ là 3 giá trị khác nhau của CÙNG khoá `url` — **Plasma 6
không có một "chế độ Plain Desktop trống icon" riêng** cho plugin
`org.kde.desktopcontainment` mà NaMiOS đang dùng. Nói cách khác: hễ còn dùng
plugin containment này (không đổi, không nằm trong phạm vi wave này), desktop
**luôn** hiện icon file/folder kiểu Windows — không có cách nào vô tình tắt nó
bằng thiếu cấu hình.

## 3. Những thứ KHÔNG tồn tại trên Plasma 6 (placebo/no-equivalent, ghi trung thực)

| Thói quen Windows | Tình trạng trên KDE Plasma 6 | Bằng chứng |
| --- | --- | --- |
| F5/chuột-phải → "Refresh" làm gì đó rõ rệt trên Windows hiện đại | Trên Windows hiện đại (Vista+), Explorer đã live-update qua change notification; F5 phần lớn là **thói quen lịch sử**, không còn luôn cần thiết. KDE Folder View cũng live-update qua `KDirWatch`/inotify. Tức: F5 trên CẢ HAI hệ, với công nghệ hiện đại, phần nhiều là **thói quen tâm lý** hơn là thao tác bắt buộc — nhưng KDE vẫn có action thật để bấm (mục 2.2), không phải vô tác dụng. | Hành vi live-update là kiến thức phổ biến về Explorer/KDirWatch, không phải khoá cấu hình cụ thể cần trích dẫn file. |
| KHotkeys (gán phím → script tuỳ biến kiểu cũ) | **Đã khai tử**, không chạy trên Plasma 6/Debian trixie | README `invent.kde.org/plasma/khotkeys`; repo Archived; không có gói Debian trixie |
| Ctrl+Alt+Del mở Task Manager kiểu Windows | KHÔNG yêu cầu làm trong đặc tả wave này (ghi rõ "NOT required") — không rà thêm | — |

## 4. Để lại cho wave sau (đã nghiên cứu, CHƯA làm — không phải bỏ quên)

| Việc | Cơ chế THẬT đã xác nhận | Vì sao chưa làm ở wave này |
| --- | --- | --- |
| Icon "Thùng rác" (Recycle Bin) trên desktop | Applet `Trashcan`, plugin id `org.kde.plasma.trash` (`plasma-desktop.git applets/trash`, `EnabledByDefault=false`) — CÓ THẬT, có thể ghim vào containment Desktop làm widget | Containment Desktop ở NaMiOS **bỏ qua applet pre-seed tĩnh** trong `plasma-org.kde.plasma.desktop-appletsrc` (đã ghi nhận ở wave trước với `org.namios.smartai`/`org.namios.workgroups` — `activityId` sinh lúc chạy). Cách THẬT duy nhất là thêm vào `usr/local/bin/namios-add-widgets.sh` (gọi `evaluateScript` lúc đăng nhập đầu) — file đó **không thuộc danh sách file được giao sửa** của wave này. |
| Icon "This PC"/Home trên desktop | File `.desktop` kiểu `Type=Link`, `URL=trash:/` hoặc `file:///home/<user>` đặt trong `~/Desktop` | `~/Desktop` nằm **ngoài** phạm vi file được giao (`etc/skel/.config/*` liệt kê + `etc/skel/.local/**` — không bao gồm `etc/skel/Desktop/`). Thêm nữa: `/etc/skel` bị copy **nguyên văn** cho user mới, không template theo `$HOME` thật — một file tĩnh ghi cứng path sẽ SAI cho mọi user (rủi ro đã ghi đúng y hệt ở `docs/specs/UX-WINDOWS-FAMILIAR.md` mục 6, trường hợp `user-places.xbel`). Riêng mục Trash thì KHÔNG cần path riêng (`URL=trash:/` dùng chung cho mọi user) nên AN TOÀN hơn về mặt kỹ thuật — chỉ vướng rào "ngoài phạm vi file được giao", không vướng rào "dữ liệu sai". |

**Khuyến nghị cho người nhận wave sau:** nếu Cuong muốn 2 icon này thật, giao
rõ quyền sửa `usr/local/bin/namios-add-widgets.sh` (thêm applet
`org.kde.plasma.trash`) — đây là đường an toàn nhất, tái dùng đúng cơ chế đã
chạy được cho SmartAI/nhóm việc, không cần đụng `/etc/skel/Desktop`.

## 5. Vì sao không đụng `kdeglobals` / `kwinrc`

- `kdeglobals [KDE] SingleClick=false` (double-click để mở) đã chốt từ wave
  trước, đúng yêu cầu Windows habit — không đổi, không có khoá
  "thói quen Windows" nào khác còn thiếu mà vừa thật/có tài liệu, vừa an toàn,
  vừa thuộc phạm vi "F5/refresh + thói quen nhỏ" của đặc tả này.
- `kwinrc`: không có khoá/section nào ở tầng KWin liên quan tới F5/refresh cần
  chốt — cả 2 action F5 thật (mục 2.1, 2.2) đều là Qt `WindowShortcut` tầng
  ứng dụng/Plasma Shell, không đi qua KWin.

## 6. Checklist xác nhận trên máy thật (điền khi có desktop, không tự đánh dấu trước)

- [ ] Mở Dolphin, bấm F5 → thư mục hiện tại tải lại (quan sát bằng mắt: ví dụ
  tạo file mới từ terminal, bấm F5, file xuất hiện)
- [ ] Click vào vùng trống trên desktop (để desktop có focus), bấm F5 → icon
  desktop tải lại (test: tạo file mới trong `~/Desktop` từ terminal trong lúc
  Plasma đang chạy, bấm F5 trên desktop, icon mới xuất hiện KHÔNG cần chờ
  inotify tự cập nhật)
- [ ] Chuột-phải lên vùng trống desktop → menu có mục "Refresh Desktop"
- [ ] `~/Desktop` tồn tại sẵn cho user mới ngay sau lần đăng nhập đầu (xác
  nhận `xdg-user-dirs` đã tạo đúng, không chỉ trông chờ transitive dependency)
- [ ] F5 trong Firefox/trình duyệt vẫn reload trang bình thường (xác nhận
  KHÔNG có xung đột — đúng như dự đoán ở mục 2.3 vì NaMiOS không gán gì toàn
  cục)
- [ ] F5 trong LibreOffice Impress vẫn bắt đầu trình chiếu bình thường (cùng
  lý do trên)
- [ ] Desktop hiện icon file/folder từ `~/Desktop` ngay khi đăng nhập (xác
  nhận Folder View, không phải desktop trống)
