# NaMiOS — Windows 11 Look & Feel Parity (WINDOWS11-PARITY)

> **Loại tài liệu:** đặc tả thiết kế/UX có ưu tiên, implementable, grounded trên repo thật —
> ánh xạ **giao diện/cảm giác Windows 11** sang **KDE Plasma 6** cho NaMiOS. Đối tượng: người
> Việt ít rành kỹ thuật, quen Windows (chủ dự án gửi ảnh Windows 11 làm tham chiếu đích).
> **Vai trò người soạn:** senior product/UX designer (chất lượng "đội thiết kế world-class"
> nhưng **TRUNG THỰC** về điều KDE Plasma 6 làm được và KHÔNG làm được).
> **Ngày:** 2026-11-11 · **Phạm vi file:** CHỈ viết tài liệu này (spec). **KHÔNG sửa
> config/theme** — vòng sau mới hiện thực. **READ-ONLY** trừ file này. Không `git commit`/push.

## 0. Quy ước đọc (bắt buộc)

- **`verified_on_host: NO` cho TOÀN BỘ tài liệu này.** Môi trường soạn là container headless,
  không có desktop KDE Plasma thật/không GPU (ADR 0011 "Bối cảnh môi trường hiện tại"). Mọi
  "CURRENT STATE" lấy từ **bằng chứng repo** (file + khoá đã đọc), KHÔNG phải quan sát boot.
  "Build không lỗi" KHÔNG suy ra "giống Windows 11 trên máy thật".
- **Ranh giới sở hữu trí tuệ (LIC-004 / ADR 0011 §3 — ràng buộc cứng):** NaMiOS **được** bắt
  chước **bố cục + luồng thao tác + cảm giác** của Windows 11. NaMiOS **TUYỆT ĐỐI KHÔNG**:
  chép icon/font/âm thanh/hoạt ảnh độc quyền Microsoft (Segoe Fluent, logo Start, boot sound,
  Mica blur assets); gọi menu là "Start Menu"; đặt nhãn ổ Linux là `C:` (ngoài Wine); tuyên bố
  "giống Windows 100%". **Parity = gợi cảm giác (evoke), KHÔNG phải pixel-clone.** Chỗ chạm
  ranh giới có ghi **[IP]**.
- **Ràng buộc kỹ thuật trên hết (không đổi dù "đẹp hơn" đòi hỏi):** NaMiOS phải **chạy được
  trên máy yếu/không GPU** — hiện thực bằng `kwinrc [Compositing] Enabled=false` +
  `OpenGLIsUnsafe=true` mặc định, chỉ bật compositing khi phát hiện GPU thật
  (`usr/local/bin/namios-auto-compositing.sh`, `systemd-detect-virt`). **Hệ quả lớn nhất cho
  tài liệu này:** mọi thứ "Fluent/Mica" (kính mờ, trong suốt, bóng mềm, animation mượt) là
  **hiệu ứng OpenGL compositing** → **mặc định TẮT** trên máy không GPU/VM. Đây là đánh đổi
  đúng đắn đã chốt, KHÔNG phải lỗ hổng.
- **Lịch sử rủi ro boot thật (không nhẹ hoá):** viền cửa sổ riêng (Aurorae) + desktoptheme
  từng **nghi** gây treo màn đăng nhập dưới QEMU/TCG (build `dfbbf3c`); Wayland cũng có lịch
  sử treo riêng (`23d774a`, `386f89d`). Chưa bisect tách bạch. Mọi đề xuất bật các lớp này
  đều gắn caveat "phải boot-test đúng kịch bản từng treo trước khi coi là đạt".
- **Thang chấm:** **Trạng thái** = Done / Partial / TODO. **Effort** = S (vài ngày/1 wave) ·
  M (1–2 tuần) · L (nhiều tuần, **cần phần cứng/build host thật**). **Loại thay đổi** = *static
  config an toàn* (sửa file `/etc/skel`, fail-safe KConfig) vs *cần tinh chỉnh trên máy thật*
  (GPU/EDID/boot-test, không mô phỏng được).
- **Không trùng lặp:** tài liệu này **tập trung LOOK & FEEL** (vẻ ngoài taskbar/menu/cửa sổ/
  vật liệu). Phần **hành vi/phím tắt/nghiệp vụ** đã có ở `docs/specs/UX-WINDOWS-FAMILIAR.md`,
  `docs/roadmap/WINDOWS-FEATURE-PARITY.md`, `docs/design/MODERN-FUTURE-UX.md` — chỗ chồng lấn
  chỉ dẫn chiếu, không chép lại.

---

## 1. Taskbar (Thanh tác vụ)

**Đích Windows 11:** panel dưới cùng, **icon + nút Bắt đầu CĂN GIỮA**, panel **nổi bo góc**,
**trong suốt kiểu Mica/kính mờ**, hover/active có chỉ báo "pill", khay hệ thống gom nhóm,
đồng hồ góc phải.

### 1.1 Hiện trạng đã có (đọc từ `etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc`)

| Thành phần | Cơ chế KDE (file · khoá/widget) | Trạng thái | Ghi chú trung thực |
| --- | --- | --- | --- |
| Panel dưới cùng | `appletsrc [Containments][1]` `location=4` (BottomEdge) · `formfactor=2` | **Done** (static) | Đúng vị trí Windows. |
| Panel **nổi** (dock) | `[Containments][1][General] floating=1` | **Done** (static) | Giống "floating taskbar". |
| Panel **bo góc** | `desktoptheme NaMiOS-Sen/widgets/panel-background.svg` (9-slice, góc **28px** = thang B "xl", `§3.1 DESIGN-SYSTEM`) | **Done** (static) | SVG đã bo góc 28px. |
| Nút Bắt đầu (Start) | Kickoff `[Applets][2] plugin=org.kde.plasma.kickoff` · `icon=start-here-namios` | **Done** (static) | Icon logo sen NaMiOS thật đã đóng gói (hicolor + NaMiOS-Lotus), KHÔNG placeholder. |
| App ghim + app đang mở | Icon-Only Task Manager `[Applets][3] org.kde.plasma.icontasks` `launchers=…` | **Done** (static) | Dolphin/Firefox/Office/KCalc ghim sẵn. |
| Khay hệ thống | `[Applets][4] org.kde.plasma.systemtray` | **Partial** | Tập applet con KHÔNG khai tường minh — phụ thuộc mặc định Plasma (xem 1.3). |
| Đồng hồ | `[Applets][5] org.kde.plasma.digitalclock` `use24hFormat=2` `dateFormat=regular` | **Done** (static) | 24h + ngày. |
| Độ dày panel (icon cân đối) | `[PlasmaViews][Panel 1] thickness=36` (+ `[Defaults]`) | **Partial** (tin cậy TRUNG BÌNH) | Chưa đối chiếu được `panelview.cpp`; fail-safe: sai thì panel giữ độ dày mặc định, không crash. Đường lui tay: Edit Mode → kéo cạnh. |

### 1.2 Khoảng cách tới Windows 11 — việc cần làm

1. **CĂN GIỮA icon + Start (điểm khác lớn nhất).** Hiện `AppletOrder=2;3;4;5` = Start/tasks
   **căn TRÁI** (kiểu **Windows 10**, không phải Windows 11). Để căn giữa như Win11: chèn
   applet **"Panel Spacer co giãn"** (`org.kde.plasma.panelspacer`, khoá
   `[Configuration][General] expanding=true`) ở **HAI** bên cụm Kickoff+Task Manager, đẩy khay
   hệ thống + đồng hồ về phải. Đây là cách đúng-kiến-trúc (KDE không có khoá "căn giữa taskbar"
   một-chạm như Win11). · **Mechanism:** `appletsrc` thêm 2 applet spacer + đổi `AppletOrder`.
   · **Trạng thái: TODO** · **Effort: S** · **Loại: static config an toàn** · **Risk thấp**
   (Plasma có thể renumber applet lần đăng nhập đầu — bình thường; verify bằng mắt).
   *Lưu ý UX:* nhiều người Việt vẫn quen Win10 (Start trái). Cân nhắc để **căn giữa là mặc
   định** (đúng đích Win11) nhưng cho đổi về trái dễ dàng; KHÔNG khoá cứng.
2. **Chỉ báo hover/active "pill" kiểu Win11.** Win11 vẽ gạch/pill dưới app đang chạy, hover
   sáng nhẹ. Icon-Only Task Manager có indicator mặc định nhưng kiểu chấm/gạch Plasma, **không
   phải pill Win11**. · **Mechanism:** phần lớn do **desktoptheme** vẽ (`NaMiOS-Sen` FrameSvg
   `tasks`/hover) — chưa có asset `widgets/tasks.svg` riêng trong theme (chỉ có background/
   panel-background/tooltip). · **Trạng thái: TODO** · **Effort: M** · **Loại: static (vẽ SVG
   theme)** nhưng **nhìn thấy đầy đủ chỉ khi compositing bật** (hover-fade cần GPU).
3. **Giảm độ dày + canh tỉ lệ icon:** đã thử (`thickness=36`) — **cần tinh chỉnh trên máy
   thật** (tin cậy trung bình, xem 1.1).

### 1.3 Translucency / Mica-like blur của panel

- **Mechanism:** `kwinrc [Plugins] blurEnabled=true` + **`contrastEnabled=true`** (KWin
  "Background Contrast" = tương đương trực tiếp **Acrylic** của Windows: giữ chữ rõ trên nền
  mờ). Panel-background.svg đã dùng navy `#10202E` **fill-opacity 0.72** → sẵn sàng cho hiệu
  ứng kính mờ.
- **Trạng thái: Partial** — khoá đã bật, **nhưng blur/contrast chỉ hiện khi compositing BẬT**.
  `[Compositing] Enabled=false` mặc định → trên máy không GPU/QEMU panel **đặc 72% navy**
  (không mờ nền sau). `namios-auto-compositing.sh` lật `Enabled=true` khi phát hiện GPU thật.
- **Effort: S** (cấu hình đã xong) · **Loại: cần tinh chỉnh trên máy thật** (boot-test GPU) ·
  **Risk perf:** blur là hiệu ứng tốn GPU-fill-rate nhất; **bắt buộc mặc định TẮT khi software
  rendering** (đã đúng). **Caveat no-boot-test:** chưa xác nhận auto-compositing lật cờ an toàn
  trên GPU thật mà KWin không crash.

---

## 2. Start menu (Menu Bắt đầu)

**Đích Windows 11:** lưới app **đã ghim** + nút **"All apps"** + ô **tìm kiếm trên cùng** +
hàng **nguồn/power** dưới cùng; cảm giác gọn, có avatar + nút tắt máy.

| Phương án | Cơ chế KDE | Đạt tới đâu so với Win11 | Trạng thái |
| --- | --- | --- | --- |
| **Kickoff** (đang dùng) | `org.kde.plasma.kickoff` | **Rất gần Win11**: có ô tìm kiếm trên, lưới "Ưa thích" (pinned), tab Ứng dụng (≈ "All apps"), hàng power (tắt/khởi động lại/khoá) + avatar dưới | **Done** (đang là mặc định) |
| Application Dashboard | `org.kde.plasma.kickerdash` | Lưới **toàn màn hình** (giống Start Win8/launchpad) — XA đích Win11 | Không khuyến nghị |
| Kicker (menu cổ điển) | `org.kde.plasma.kicker` | Menu cascade kiểu Win7 — XA Win11 | Không khuyến nghị |

**Kết luận:** **giữ Kickoff** — đây là launcher Plasma gần "cảm giác Win11" nhất mà không cần
app thứ ba. Việc còn lại là **chuốt**, không thay engine:

1. **Lớp "nhóm việc" (Văn phòng/Thuế/Kế toán/Bảo hiểm/Giáo dục/Hành chính)** mà
   `DESIGN-SYSTEM.md §7` + mockup `namios-my-apps-launcher.svg` mô tả — hiện Kickoff hiển thị
   theo category Freedesktop trần. · **Mechanism:** hoặc tuỳ biến category Kickoff, hoặc widget
   riêng `org.namios.workgroups` thêm qua `usr/local/bin/namios-add-widgets.sh` (evaluateScript
   lúc đăng nhập đầu — cơ chế đã chứng minh chạy cho SmartAI). · **TODO · Effort: M · Loại:
   static (widget) nhưng cần verify trên máy thật.**
2. **[IP] Icon nút Bắt đầu riêng** — đã có (`start-here-namios`, logo sen). Không chép logo
   Start Microsoft. **Done.**
3. **Ghim mặc định**: `favorites=…writer/calc/impress/firefox/kcalc/dolphin/gwenview` đã set.
   · **Partial** — tên `.desktop` phải khớp gói cài thật (verify on boot).

**Risk/Loại:** thấp, chủ yếu static config + 1 widget. Không đụng compositing nên chạy cả trên
máy yếu.

---

## 3. Window look (Vẻ ngoài cửa sổ)

**Đích Windows 11:** cửa sổ **bo góc mềm (~8px)**, **bóng đổ nhẹ**, **3 nút điều khiển ở góc
PHẢI** (thu nhỏ `_` · phóng to `▢` · đóng `✕` hover đỏ), title-bar gọn, spacing kiểu Fluent.

### 3.1 Phát hiện quan trọng (phải nói thẳng)

Theme viền cửa sổ đã dựng — **Aurorae `NaMiOSLotus`** (`usr/share/aurorae/themes/NaMiOSLotus/`)
— hiện là **phong cách macOS, KHÔNG phải Windows**:

- `metadata.desktop` tự mô tả: *"3 nút tròn san hô/vàng/đỏ-son **kiểu macOS**"*.
- `NaMiOSLotusrc [Layout]`: `ButtonWidth=13` (3 nút **tròn 13px**), `TitleAlignment=Left`.
- Vị trí nút (trái/phải) do **`kwinrc [org.kde.kdecoration2]` khoá `ButtonsOnLeft`/
  `ButtonsOnRight`** quyết định (KHÔNG phải do theme Aurorae) — hiện section này **đang bị
  COMMENT TẮT** hoàn toàn trong `kwinrc` (hoãn vì nghi treo đăng nhập `dfbbf3c`), nên KWin
  đang dùng **viền Breeze mặc định** (ở Plasma 6 Breeze vẫn bo góc + nút ở phải — tình cờ đã
  **giống Windows hơn** theme riêng của NaMiOS).

→ **Nghịch lý cần chủ dự án biết:** theme cửa sổ riêng của NaMiOS hiện được thiết kế **giống
macOS**; muốn **cảm giác Windows 11** thì hoặc (a) sửa theme sang kiểu Win, hoặc (b) cứ dùng
Breeze mặc định (đã khá Win-like). `MODERN-FUTURE-UX.md §B` thậm chí khuyến nghị **không**
macOS-hoá (global menu) để giữ "Windows-familiar".

### 3.2 Việc cần làm để đạt "cửa sổ kiểu Windows"

| Việc | Mechanism (file · khoá) | Trạng thái | Effort | Loại / Risk |
| --- | --- | --- | --- | --- |
| **Nút điều khiển ở góc PHẢI** (Win-style) | `kwinrc [org.kde.kdecoration2] ButtonsOnRight=IAX` (I=min, A=max, X=close) · `ButtonsOnLeft=` (rỗng, hoặc `M`=menu) | **TODO** | **S** | *static an toàn* — khoá này KHÔNG đụng OpenGL, fail-safe |
| **Nút kiểu Win (vuông, không tròn macOS)** | Vẽ lại `NaMiOSLotus/{minimize,maximize,restore,close}.svg` (glyph `_ ▢ ✕`, hover close đỏ) + `ButtonWidth` lớn hơn, bỏ bo tròn | **TODO** | **M** | *static (vẽ SVG)*. **[IP]** tự vẽ, KHÔNG chép Segoe Fluent |
| **Title căn trái + cao gọn** | `NaMiOSLotusrc [General] TitleAlignment=Left` (đã có) · `[Layout] TitleHeight=34` (46px tổng) | **Done** (hợp Win) | — | static |
| **Bo góc + bóng** | Aurorae `decoration.svg` góc **10px** (thang B "sm") + `[General] Shadow=true` (đã có); Breeze fallback cũng bo góc Plasma 6 | **Done** (ở cả 2 đường) | — | static — bo góc **không** cần compositing; **bóng mờ đẹp** thì cần |
| **Bật lại viền riêng an toàn** | Bỏ comment `[org.kde.kdecoration2] library=org.kde.kwin.aurorae` + `theme=__aurorae__svg__NaMiOSLotus` trong `kwinrc` | **TODO (chặn)** | **S (sửa)** / **L (bisect)** | **cần tinh chỉnh máy thật** — **Risk cao:** nghi treo đăng nhập `dfbbf3c`, PHẢI bisect tách Aurorae khỏi desktoptheme + boot-test đúng kịch bản QEMU/TCG trước khi bật |

**Quyết định đề xuất:** để đạt **Windows 11 feel**, ưu tiên **sửa NaMiOSLotus thành biến thể
Windows** (nút phải, glyph vuông) **thay vì** giữ nút tròn macOS — nhưng **chỉ bật sau khi
bisect** loại trừ rủi ro treo. Trong lúc chờ, **Breeze mặc định (nút phải, bo góc) đã là đường
Win-like an toàn** — không phải trạng thái "hỏng".

---

## 4. Fluent / Mica materials (Kính mờ · trong suốt · bóng mềm)

**Đích Windows 11:** "Mica" (nền cửa sổ hoà sắc desktop) + "Acrylic" (popup kính mờ) +
chuyển động nhất quán.

- **Mechanism (PHẦN LỚN ĐÃ CẤU HÌNH, không phải việc mới):**
  - `kwinrc [Plugins] blurEnabled=true` → **KWin Blur** = Acrylic.
  - `kwinrc [Plugins] contrastEnabled=true` → **Background Contrast** = giữ chữ rõ trên nền mờ
    (lõi của "Acrylic").
  - `scaleEnabled/slideEnabled/slidingpopupsEnabled=true`, `wobbly/cube=false` → chuyển động
    mượt kiểu hiện đại.
  - `kdeglobals [KDE] AnimationDurationFactor=0.6` → rút ~40% thời lượng animation để vẫn mượt
    khi compositing tắt (animation Plasma Quick chạy qua `QPainter` raster/CPU). **Quyết định
    cân bằng perf/premium đã làm đúng**, không cần "sửa".
  - Desktoptheme `NaMiOS-Sen` có file `colors` riêng → panel/systray/Kickoff luôn **nền tối +
    chữ sáng** (ComplementaryColorGroup), độc lập với color-scheme **sáng** của vùng nội dung
    app (`kdeglobals ColorScheme=NaMiOS`) — đúng mô hình "chrome tối / nội dung sáng".
- **"Mica" (nền cửa sổ hoà sắc desktop) — KHÔNG có 1:1 trong KDE.** KDE có **blur phía SAU
  cửa sổ** nhưng KHÔNG có cơ chế "nền cửa sổ lấy mẫu + khử bão hoà hình nền" đúng như Mica.
  Gần nhất = bật blur cho nền cửa sổ/ô nội dung (phải app hỗ trợ vùng mờ). → **gợi cảm giác
  được, KHÔNG sao chép được Mica thật.** (Xem §Giới hạn.)
- **Trạng thái: Partial** (đã cấu hình, chờ boot-test GPU) · **Effort: S** (không cần code) ·
  **Loại: cần tinh chỉnh máy thật.**
- **Risk perf (nói rõ):** blur + contrast là **lớp tốn GPU-fill-rate nhất**. Trên máy yếu/
  không GPU/VM **PHẢI tắt** (đã mặc định `Enabled=false`). KHÔNG bật compositing mặc định cho
  mọi máy chỉ để "đẹp" — sẽ **màn đen / treo** trên máy không GPU (đúng bug lịch sử). Đường
  đúng duy nhất: `namios-auto-compositing.sh` bật **chỉ khi** `systemd-detect-virt` thấy không
  phải VM + có GPU thật. **Caveat no-boot-test:** script này `verified_on_host: NO`.

---

## 5. File manager (Dolphin → cảm giác "File Explorer")

**Đích Windows 11:** thanh địa chỉ breadcrumb + gõ path được, **"This PC" / Quick access**,
ribbon/command-bar.

| Tính năng Win Explorer | Cơ chế Dolphin (file · khoá) | Đạt tới đâu | Trạng thái |
| --- | --- | --- | --- |
| Thanh địa chỉ **gõ path được** | `dolphinrc [General] EditableUrl=true` (Ctrl+L focus) | Đạt — **hơn** Explorer (vừa breadcrumb vừa editable) | **Done** (verify on boot) |
| Breadcrumb | Mặc định Dolphin (click biến thành editable) | Đạt | **Done** |
| Thông tin dung lượng ổ | `dolphinrc [General] ShowSpaceInfo=true` | Đạt | **Done** |
| Panel "Quick access" (Home/Documents/Downloads/Desktop) | Dolphin Places **mặc định tự tính theo `$HOME`** (không cần file) | Đạt phần "thư mục nhanh" | **Done** |
| **Nhóm "This PC" gom ổ đĩa** | `user-places.xbel` — **KHÔNG seed tĩnh được** (`/etc/skel` copy nguyên văn → ghi cứng path sai cho mọi user, `UX-WINDOWS-FAMILIAR.md §6`) | Chưa có nhóm "Máy này" gom ổ | **TODO** — phải sinh lúc đăng nhập đầu (biết `$HOME` thật) qua `namios-welcome`. **Effort: M · Loại: cần first-run, không static** |
| Icon "Máy này"/"Thùng rác" trên desktop | `etc/skel/Desktop/*.desktop` (Link `computer:/`, `trash:/`) đã tạo (`DESKTOP-WINDOWS-LIKE.md §3`) | Đạt (verify) | **Partial** |
| **Ribbon / command bar** | Dolphin có **toolbar + menubar**, KHÔNG có ribbon | **KHÔNG** có 1:1 — Dolphin dùng toolbar gọn, không phải ribbon tab. Gợi được "command bar" bằng toolbar tuỳ biến | **N/A** (xem §Giới hạn) |
| **[IP]** không gọi ổ Linux là `C:` | Repo tuân thủ (`UX-WINDOWS-FAMILIAR.md §3`) | — | **Done** |

**Tổng:** Dolphin đã cho cảm giác Explorer ở phần lõi (địa chỉ + Quick access). Thiếu thật sự
= **nhóm "This PC" gom ổ** (first-run, không static) + **ribbon không map 1:1** (chấp nhận
dùng toolbar).

---

## 6. Settings (KDE System Settings → cảm giác "Windows Settings")

**Đích Windows 11:** một nơi, **nhóm theo việc** + **ô tìm kiếm** đầu trang.

- **CURRENT STATE:** đã có **`usr/local/bin/namios-control-panel`** — hub đặt tên kiểu Windows
  **8 mục** (Accounts/Display/Network/Devices/Personalization/Time & Language/Apps/Update) +
  **8 launcher** `usr/share/applications/namios-cpl-*.desktop` map sang KCM thật
  (`kcm_users`/`kcm_kscreen`/`kcm_networkmanagement`…); mỗi mục mở `kcmshell6`/`systemsettings`.
  Depends-chain apt đã xác nhận các gói KCM chắc chắn có mặt (`CONTROL-PANEL.md §2`).
  `namios-welcome` lo onboarding chọn vài mặc định. → **Partial (gần đủ).**
- **GAP so với Win11:**
  1. **Chưa có "landing Cài đặt" một trang nhóm-theo-việc + ô tìm-KHÔNG-DẤU** (ADR 0011 §6 yêu
     cầu tìm không dấu kiểu "mang" → "Mạng"). Hiện là hub `kdialog` 8 nút + 8 launcher rời,
     chưa phải mặt tiền tìm kiếm thống nhất. · **TODO · Effort: M · Loại: static (script/QML) +
     cần verify boot.**
  2. **Gói `systemsettings` chưa khai tường minh** trong `package-lists/` (đi kèm transitive +
     `print-manager` Depends cứng vào nó — nên thực tế có mặt, nhưng nên khai rõ). · **TODO ·
     Effort: S** (ngoài phạm vi file này — thuộc package-lists).
- **Risk:** thấp. Script `namios-control-panel` luôn `exit 0`, fail-safe, không tự xin quyền
  (polkit/KCM tự hỏi).

---

## 7. Notification Center / Action Center · Widgets · Snap Layouts · Virtual Desktops

| Tính năng Win11 | Cơ chế KDE tương đương | Đạt tới đâu / Khác biệt | Trạng thái · Effort · Loại |
| --- | --- | --- | --- |
| **Action Center** (Win+A: Wi‑Fi/âm/độ sáng 1 chạm) | **System Tray** chứa `plasma-nm`/`plasma-pa`/brightness/battery applet | KDE **KHÔNG có widget "Quick Settings" tách riêng** như Win11; systray **chính là** nơi đó. Việc đúng = **gom nhóm + đặt tên "Cài đặt nhanh" tiếng Việt**, KHÔNG xây panel mới | **TODO · S · static (gom cụm) + verify** |
| **Notification Center** (Win+N: lịch sử + lịch) | Popup thông báo của systray + **lịch trong popup Digital Clock** | KDE **tách**: thông báo ở systray, lịch ở đồng hồ (Win11 gộp). Có DND mặc định | **Partial.** Thiếu `plasmanotifyrc` mặc định (DND khi trình chiếu, lịch sử hợp lý) · **TODO · S · static** |
| **Widgets** (Win+W: bảng widget) | **Plasma widgets** (trên desktop/panel; thêm qua `namios-add-widgets.sh`) | KDE **mạnh hơn** (widget đặt bất kỳ đâu) nhưng **không có "bảng widget trượt" 1 phím** như Win11 — mô hình khác | **Partial** (SmartAI/workgroups đã dùng cơ chế này) |
| **Snap Layouts** (rê chuột lên nút phóng to → menu bố cục) | **Quick Tile** (`kwinrc`/`kglobalshortcutsrc` Meta+Mũi-tên) + **Electric Border Tiling** (`[Windows] ElectricBorderTiling=true`) + **Custom Tiling** (Meta+T) | Kéo-biên chia đôi/góc **Done**; **nhưng flyout "chọn bố cục khi hover nút maximize" KHÔNG có 1:1** — KWin Custom Tiling là editor khác UX | **Partial** (snap cơ bản Done; flyout: **không map**, xem §Giới hạn) |
| **Virtual desktops + Task View** (Win+Tab) | **KWin Virtual Desktops** + **Overview** (`[Plugins] overviewEnabled=true`, Meta+W/Meta+Tab, hot-corner trên-trái `[Effect-overview] BorderActivate=7`) | Đạt tốt; Overview ≈ Task View. Pager widget cho hàng desktop | **Done** (verify on boot; cử chỉ 4-ngón cần Wayland) |

**Risk chung mục 7:** thấp về mã, nhưng animation/trong suốt của các popup này **chỉ mượt khi
compositing bật** (khoá vào §4). Thêm applet dùng `namios-add-widgets.sh` **không** cần GPU.

---

## 8. Clock · Fonts · Màu (chi tiết bổ trợ look)

- **Đồng hồ:** `digitalclock use24hFormat=2` (24h) + `dateFormat=regular`. **Done.** (Win11 mặc
  định hiển thị cả giờ + ngày góc phải — khớp.)
- **Font UI:** `kdeglobals [General] font=Inter` (OFL, KHÔNG chép Segoe) + cascade Noto an toàn
  cho glyph tiếng Việt. · **Partial** (glyph dấu tiếng Việt của Inter chưa verify LibreOffice
  thật). **[IP]** không thêm font Microsoft; Carlito/Caladea lo metric-compat Calibri/Cambria.
- **Màu/accent:** color-scheme `NaMiOS` (Đông Sơn v3: navy #092D4F / gold #DEA93E accent /
  vermilion #D64C3E / teal #278F8D / ivory #FFF9EF). Accent = **vàng kim** cho selection/focus/
  hover. Trục "chrome tối / nội dung sáng" đã chốt. **Done** (static).

---

## 9. TOP-10 BACKLOG ưu tiên (implementable, mỗi dòng 1 việc)

> Gate chung: nhiều dòng "verify/boot-test" khoá sau **build host nested-virt** (đòn bẩy #0
> toàn dự án). Chấm **P**(0/1/2) theo tác động cảm-giác-Windows + **Effort** + **Loại**.

| # | Việc | P | Effort | Loại / Risk | Mechanism chính |
| --- | --- | --- | --- | --- | --- |
| 1 | **Căn giữa taskbar kiểu Win11** (2 Panel Spacer co giãn quanh cụm Start+tasks) — khác biệt hình ảnh LỚN nhất với Win10 hiện tại | P1 | S | static an toàn · risk thấp | `appletsrc` thêm `org.kde.plasma.panelspacer expanding=true` ×2 + đổi `AppletOrder` |
| 2 | **Boot-test `namios-auto-compositing.sh` trên GPU thật** để bật Blur+Contrast (Acrylic/kính-mờ) — mã đã sẵn, chỉ thiếu xác nhận | P0 | S | cần máy thật · risk perf (đã fail-safe) | `kwinrc [Plugins] blurEnabled/contrastEnabled` + auto-compositing |
| 3 | **Đưa cửa sổ về kiểu Windows: nút ở góc PHẢI** (`ButtonsOnRight=IAX`) + vẽ lại glyph vuông `_ ▢ ✕` (bỏ nút tròn macOS) | P1 | S (nút phải) / M (glyph) | static · **[IP]** tự vẽ | `kwinrc [org.kde.kdecoration2]` + `NaMiOSLotus/*.svg` |
| 4 | **Bisect + bật an toàn viền cửa sổ riêng** (NaMiOSLotus) tách khỏi desktoptheme trên đúng kịch bản từng treo `dfbbf3c` | P1 | L | cần máy thật · **risk cao (treo đăng nhập)** | bỏ comment `[org.kde.kdecoration2]` sau bisect |
| 5 | **Chỉ báo hover/active "pill" + landing Start "nhóm việc"** (Office/Thuế/Kế toán…) | P1 | M | static (SVG theme + widget) · verify | `NaMiOS-Sen` tasks SVG + `org.namios.workgroups` qua `namios-add-widgets.sh` |
| 6 | **Landing "Cài đặt" nhóm-theo-việc + tìm KHÔNG DẤU** phủ lên 8 mục Control Panel đã có; khai `systemsettings` tường minh | P1 | M | static (script/QML) · verify | mở rộng `namios-control-panel` + package-lists |
| 7 | **Sinh `user-places.xbel` "Máy này" gom ổ + Quick access** lúc đăng nhập đầu (This-PC mental model) | P1 | M | **first-run, không static** (biết `$HOME` thật) · risk thấp | `namios-welcome.apply()` |
| 8 | **`plasmanotifyrc` mặc định + gom cụm "Cài đặt nhanh" tiếng Việt** (Action/Notification Center feel) | P2 | S | static + gom systray · verify | systray grouping + config |
| 9 | **Đo tương phản tiếng Việt (dấu, cỡ nhỏ) trên nền kính mờ** trước khi công bố "đẹp" (nối PL12.2) | P1 | S | cần máy thật (Background Contrast) | WCAG trên blur thật |
| 10 | **Verify lớp look đã viết trên Wayland + X11**: panel bo góc/nổi, bo góc cửa sổ, Overview, snap, địa chỉ Dolphin, 24h clock | P1 | S | cần máy thật · risk thấp | checklist `UX-WINDOWS-FAMILIAR.md §8` |

---

## 10. TRUNG THỰC: điều Windows 11 làm mà KDE Plasma 6 KHÔNG thể khớp 1:1

Không "phủ sơn" — những điểm dưới đây **gợi cảm giác được**, nhưng **không sao chép được đúng**:

1. **Mica thật** (nền cửa sổ lấy mẫu + khử bão hoà hình nền phía sau toàn cửa sổ). KDE có
   **blur sau cửa sổ** nhưng không có cơ chế "material nền cửa sổ hoà sắc desktop" của Win11.
   → gợi bằng blur + chrome tối, không clone.
2. **Snap Layouts flyout** (rê chuột lên nút phóng to → hiện menu các bố cục chia màn hình).
   KDE có Quick Tile (kéo biên / Meta+Mũi-tên) + Custom Tiling (Meta+T editor) — **mạnh nhưng
   UX khác**, không có popup chọn-bố-cục-khi-hover-nút-maximize.
3. **Ribbon / command bar của Explorer** (các tab lệnh dạng ruy-băng). Dolphin dùng toolbar +
   menubar — triết lý khác, không có ribbon.
4. **Gộp Action Center + Notification Center + Widgets board** thành các flyout 1-phím đồng
   nhất (Win+A/N/W). KDE phân tán: systray / popup đồng hồ / widget đặt tự do — **linh hoạt
   hơn** nhưng không giống luồng Win11.
5. **Fluent motion/âm thanh/icon độc quyền** (Segoe Fluent Icons, system sounds, hoạt ảnh
   Start). **[IP] CẤM chép** — NaMiOS phải tự vẽ icon (đã có `branding/icons-system-v1/`), tự
   làm âm thanh. Cảm giác "cao cấp" phải đạt bằng tài sản riêng.
6. **"Mica/Acrylic mọi nơi kể cả máy yếu".** Windows có đường graphics-stack + fallback phần
   cứng rộng; NaMiOS **chủ động tắt compositing trên máy không GPU** (mục tiêu chạy máy yếu).
   → trên máy yếu NaMiOS sẽ **phẳng/đặc hơn** Win11 — đây là **đánh đổi có chủ đích**, không
   phải thiếu sót.
7. **Per-monitor fractional scaling thật-mượt** (Win11 scale hỗn hợp nhiều màn mượt). KDE
   **chỉ đầy đủ trên Wayland** — mà Wayland đang **chủ động ẩn** vì lịch sử treo đăng nhập
   (`MODERN-FUTURE-UX.md §2`). Trên X11 (mặc định) chỉ scale toàn cục một mức.

**Cảnh báo thương hiệu (nhắc lại):** mọi thứ trên là **evoke the feel, don't clone** — bố cục/
luồng/cảm giác được phép; icon/font/âm thanh/hoạt ảnh/tên độc quyền Microsoft thì KHÔNG. Không
gọi là "Start Menu", không nhãn ổ `C:` cho Linux, không tuyên bố "giống Windows 100%".

---

*Nguồn bằng chứng chính (đã đọc trong phiên soạn): `etc/skel/.config/{plasma-org.kde.plasma.
desktop-appletsrc, kwinrc, kglobalshortcutsrc, kdeglobals, plasmarc, dolphinrc, plasma-localerc}`,
`usr/share/plasma/desktoptheme/NaMiOS-Sen/{metadata.json, colors, widgets/panel-background.svg}`,
`usr/share/aurorae/themes/NaMiOSLotus/{metadata.desktop, NaMiOSLotusrc}`,
`usr/share/color-schemes/NaMiOS.colors`, `usr/local/bin/namios-control-panel`,
`usr/share/namios/docs/{DESKTOP-WINDOWS-LIKE.md, WINDOWS-HABITS.md, CONTROL-PANEL.md}`,
`docs/specs/UX-WINDOWS-FAMILIAR.md`, `docs/roadmap/WINDOWS-FEATURE-PARITY.md`,
`docs/design/{MODERN-FUTURE-UX.md, DESIGN-SYSTEM.md}`. verified_on_host: NO cho toàn bộ.*
