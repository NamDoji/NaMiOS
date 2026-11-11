# NaMiOS — Audit nhất quán hệ thiết kế (Consistency Audit)

> **Ngày:** 11/11/2026 · **Nhóm:** Team 1 (design-system lead, tiếp nối) ·
> **Phạm vi:** đối chiếu TỪNG surface đã đóng gói với nguồn sự thật đã hợp nhất
> ở `docs/design/DESIGN-SYSTEM.md` (11/11/2026) — màu/brand.json, typography,
> spacing/radius/shadow, motion. `verified_on_host: NO` cho mọi surface dưới
> đây (đối chiếu mã nguồn/giá trị tĩnh, CHƯA boot máy thật — kế thừa trạng thái
> đã ghi ở từng file).
>
> **Quy tắc sở hữu áp dụng cho wave này:** fix trực tiếp CHỈ trong 3 cây asset
> Team 1 sở hữu (`usr/share/plasma/desktoptheme/NaMiOS-Sen/**`,
> `usr/share/color-schemes/**`, `usr/share/aurorae/**`). Mọi phát hiện ở
> surface khác (SDDM/installer/boot/branding CSS) chỉ **ghi nhận + khuyến
> nghị**, không chỉnh file.

## Tóm tắt điểm số theo surface

| Surface | Sở hữu | Trạng thái màu | Trạng thái radius/shadow | Trạng thái font | Việc đã làm |
| --- | --- | --- | --- | --- | --- |
| Boot (GRUB/isolinux) | khác | ĐẠT — đúng brand.json | n/a | Unifont (bắt buộc kỹ thuật) | — |
| Plymouth | khác | ĐẠT — đúng brand.json | n/a | n/a (không có text brand) | — |
| SDDM (login) | khác | GẦN ĐẠT — 2 giá trị gray near-duplicate | n/a | **LỆCH — dùng Inter, không phải Noto Sans** | ghi nhận |
| Installer (Calamares) | khác | ĐẠT — đúng brand.json, đã tự sửa case style: 10/11 | n/a | không ghi đè font | — |
| Desktop panel (Plasma `colors`) | **Team 1** | ĐẠT | n/a | n/a | đã kiểm, không cần sửa |
| Desktop theme (FrameSvg SVG) | **Team 1** | ĐẠT | ĐẠT — đúng thang B đã đặt tên | n/a | đã kiểm, không cần sửa |
| Window theme (Aurorae) | **Team 1** | **2 BUG đã FIX** | ĐẠT — đúng thang B | n/a | **FIXED** |
| Color scheme (`NaMiOS.colors`) | **Team 1** | ĐẠT — sinh tự động từ token | n/a | n/a | đã kiểm, không cần sửa |
| `design/tokens.json` (PL12 data) | khác (UX12 team) | **LỖI THỜI — ruby cũ, không khớp asset nào** | LỆCH — thang nháp thứ 3 (6/10/16) | LỆCH — thang chữ nháp cũ | ghi nhận trong DESIGN-SYSTEM.md |
| `branding/style/namios.css` | khác (branding/style) | nhất quán nội bộ | nguồn của thang B (chính xác) | **Inter xếp trước Noto Sans** | ghi nhận |

---

## 1. Boot — GRUB (`config/bootloaders/grub-pc/live-theme/theme.txt`) + isolinux

**Kiểm tra:** màu `title-color`/`selected_item_color`/`progress_bar.*` đối
chiếu brand.json.

- `title-color: "#182E3B"` = `chu_muc` ✓
- `selected_item_color= "#C93643"` = `son` ✓
- `progress_bar.fg_color = "#C93643"` (son) / `bg_color = "#122A3A"` (muc_dem) /
  `text_color = "#F2C66D"` (vang_tam) ✓
- `label.color = "#BC8A43"` (vang_nuoc, đậm hơn vang_tam để đọc được) ✓

**Kết luận:** không phát hiện lệch. Đã tự đối chiếu nguồn KHÔNG dựa suy đoán
(comment trong file dẫn trực tiếp mã nguồn `binary_grub_cfg`). Duy nhất một
rủi ro đã tự ghi nhận, không phải lỗi thiết kế: `verified_on_host: NO`, vị trí
chính xác của `title-text` do GRUB gfxmenu tự đặt (không `+ title {}` tường
minh) chưa được xác nhận bằng ảnh chụp thật.

**isolinux/syslinux** (`config/bootloaders/syslinux_common/menu.cfg`): không
khai màu tuỳ biến (giới hạn kỹ thuật — `vesamenu.c32` không hỗ trợ hex thật,
đã ghi rõ trong file). Không có gì để đối chiếu màu ở nhánh này; không phát
hiện lệch (không áp dụng).

## 2. Plymouth (`usr/share/plymouth/themes/namios/namios.plymouth`)

- `BackgroundStartColor=0xfbf8f2` / `BackgroundEndColor=0xefe3d1` = gradient ngà
  ấm chính xác (khớp `ivory-top`/`ivory-bottom` trong
  `branding/design-system/tokens.json`) ✓
- `ProgressBarForegroundColor=0xc93643` = `son` ✓; `ProgressBarBackgroundColor=
  0xe3d6c2` = sắc ngà đậm hơn một chút (trong khoảng `surface.subtle`/
  `border.subtle` — hợp lý cho track bóng mờ dưới progress fill) — không phải
  token chính xác 1:1 nhưng là phối màu trang trí hợp lệ (không mang nghĩa
  trạng thái, không vi phạm §5).

**Kết luận:** không phát hiện lệch cần sửa.

## 3. SDDM (`usr/share/sddm/themes/namios/*`)

### 3.1 Font — LỆCH, đã ghi nhận, KHÔNG sửa (ngoài quyền sở hữu)

- `theme.conf:35` → `fontFamily=Inter`
- `Main.qml:66` → fallback `"Inter"` khi `config.fontFamily` trống
- `Clock.qml:37,47` → hard-code `font.family: "Inter"` (không đọc config, luôn
  Inter bất kể `theme.conf`)

`docs/design/DESIGN-SYSTEM.md` §2 chốt **Noto Sans** là phông UI mặc định thật
đang dùng (Be Vietnam Pro chỉ là lớp nâng cấp có điều kiện); không nơi nào
trong hệ thiết kế liệt kê **Inter** là phông đã duyệt cho hệ thống. Inter là
phông OFL hợp lệ về giấy phép, nhưng việc dùng làm *mặc định thật* ở màn đăng
nhập — bề mặt đầu tiên người dùng thấy — lệch khỏi phông đã chốt.

**Khuyến nghị cho nhóm sở hữu SDDM:** đổi `fontFamily` trong `theme.conf` về
`"Noto Sans"` (fallback `"DejaVu Sans"`), và sửa `Clock.qml:37,47` đọc
`root.brandFont`/`config.fontFamily` thay vì hard-code `"Inter"` (hiện tại
`Clock.qml` không đồng bộ ngay cả với `Main.qml` — `Main.qml` đã có cơ chế đọc
`config.fontFamily`, `Clock.qml` thì không, nên đổi `theme.conf` một mình
KHÔNG đủ sửa đồng hồ).

### 3.2 Màu chữ — gần đạt, 1 cặp near-duplicate đáng ghi nhận

- `theme.conf:33` `foregroundColor=#F7F6F1`, `theme.conf:34`
  `foregroundDimColor=#B7C4CF` — khớp CHÍNH XÁC `--fg`/`--fg-dim` ở
  `branding/style/namios.css:44-45`, **nhưng khác** `dark.text.primary`
  (`#F8F5EE`) / `dark.text.secondary` (`#C9D3D6`) ở
  `branding/design-system/tokens.json:66-67` — chênh 1-11 đơn vị RGB/kênh,
  không thấy bằng mắt nhưng là 2 token khác nhau cho cùng vai trò "chữ chính/
  phụ trên nền tối".

**Đánh giá:** không phải lỗi nghiêm trọng (cả 2 cặp đều đạt WCAG AA thoải mái
trên nền mực đêm), nhưng là cùng một dạng trôi lệch "thang shell vs thang
component" đã đặt tên ở `DESIGN-SYSTEM.md` §3.1 cho radius/shadow — chỉ riêng
màu chữ chính/phụ tối thì CHƯA được đặt tên chính thức là 2 thang riêng.
**Khuyến nghị:** ở lần cập nhật kế tiếp, hoặc (a) thêm `--fg`/`--fg-dim` của
`namios.css` thành "Thang C — Desktop-shell text" được đặt tên tương tự §3.1,
hoặc (b) đổi `namios.css:44-45` dùng đúng `#F8F5EE`/`#C9D3D6` để gộp về 1 cặp.
Không tự quyết ở wave này vì `namios.css`/SDDM không thuộc 3 cây asset được
giao sửa trực tiếp.

### 3.3 Màu accent/vàng — ĐẠT

`accentColor=#C93643` (son), `goldColor=#F2C66D` (vang_tam) khớp brand.json
chính xác. `backgroundColor=#122A3A` (muc_dem) khớp, có fallback chống màn đen
đã tự ghi nhận tốt trong `Background.qml`.

## 4. Installer (Calamares — `etc/calamares/branding/namios/branding.desc`)

- Khối `style:` (dòng 114-118): `SidebarBackground #122a3a` (muc_dem),
  `SidebarText #f7f6f1`, `SidebarTextCurrent #f2c66d` (vang_tam),
  `SidebarBackgroundCurrent #364a58` (tính từ muc_dem +15% về trắng, có công
  thức ghi rõ). Đúng case schema thật của Calamares (đã tự sửa 10/11/2026, ghi
  chú rõ lý do + đối chiếu mã nguồn).
- `SidebarText #f7f6f1` — cùng giá trị `--fg` của `namios.css` (không phải
  `dark.text.primary` #F8F5EE của branding/design-system) — **cùng loại
  near-duplicate ghi ở mục 3.2**, không phải lỗi riêng của Calamares.

**Kết luận:** không có lỗi mới; 1 ghi nhận near-duplicate dùng chung với SDDM
(xem khuyến nghị ở 3.2 — áp dụng chung cho mọi nơi dùng `#f7f6f1`/`#b7c4cf`).

## 5. Desktop panel + theme — Plasma `desktoptheme/NaMiOS-Sen` (sở hữu Team 1)

Đối chiếu `usr/share/plasma/desktoptheme/NaMiOS-Sen/colors` (bộ màu riêng của
Plasma::Theme, KHÁC `color-schemes/NaMiOS.colors`) + các SVG FrameSvg
(`widgets/*.svg`, `dialogs/*.svg`, bản `opaque/*` đối ứng):

- Màu: toàn bộ khớp brand.json (son/dai/canh_light/vang_tam/gold_dark/fg/
  fg-dim) theo đúng header đối chiếu trong file `colors`. Bug `ForegroundPositive`
  trùng `ForegroundActive` (màu "thành công" hiện ra màu đỏ) đã được **wave
  trước (10/11/2026) fix** — đã kiểm lại, đúng `89,199,152` (#59C798, status.
  success tối) ở cả 6 nhóm Button/Tooltip/View/Window/Complementary/Header.
  Không còn việc phải làm ở đây.
- Radius: `widgets/background.svg:6`, `widgets/panel-background.svg`,
  `dialogs/background.svg` dùng bo góc 28px (= "Thang B — xl" theo
  `DESIGN-SYSTEM.md` §3.1, đúng `branding/style/namios.css:55 --r-xl: 28px`).
  `widgets/tooltip.svg:5-6` dùng 14px (= Thang B "md", đúng `namios.css:53
  --r-md: 14px`). **Nhất quán đúng theo đúng thang đã đặt tên** — không có gì
  cần sửa; đây CHÍNH LÀ bằng chứng cho thấy 2 thang bo góc không phải lỗi, mà
  là 2 hệ số được dùng có chủ đích, nhất quán trong cùng 1 theme.
- Fallback `opaque/*`: màu đặc `#0B2034` dùng nhất quán cả 3 file
  (`opaque/widgets/background.svg`, `opaque/widgets/panel-background.svg`,
  `opaque/widgets/tooltip.svg`, `opaque/dialogs/background.svg`) khi
  compositing tắt — đã kiểm đủ 4 file, không lệch.

**Việc đã làm:** không cần sửa (đã đạt khi đối chiếu).

## 6. Window theme — Aurorae `NaMiOSLotus` (sở hữu Team 1) — 2 BUG ĐÃ FIX

### 6.1 FIX — `NaMiOSLotusrc:21-26` màu chữ titlebar không khớp token nào

**Trước khi sửa:**
```
ActiveTextColor=23,44,61      # = #172C3D — KHÔNG có trong brand.json
InactiveTextColor=112,125,138 # comment tự nhận "= NaMiOS.colors
                               #   ForegroundInactive" nhưng giá trị THẬT
                               #   trong NaMiOS.colors là 82,100,107
```
Đối chiếu `usr/share/color-schemes/NaMiOS.colors` (mọi nhóm nền sáng, vd dòng
`ForegroundNormal=24,46,59` / `ForegroundInactive=82,100,107`) và
`branding/design-system/tokens.json` `light.text.primary=#182E3B` (24,46,59) /
`light.text.secondary=#52646B` (82,100,107) — 2 giá trị cũ **không trace được
về token nào**, kể cả giá trị mà chính comment trong file tự nhận là đang dùng
lại.

**Đã sửa** (file `usr/share/aurorae/themes/NaMiOSLotus/NaMiOSLotusrc`):
`ActiveTextColor=24,46,59` (chu_muc #182E3B, chữ chính), `InactiveTextColor=
82,100,107` (text.secondary #52646B, khớp đúng NaMiOS.colors). Comment đã viết
lại giải thích rõ trị cũ sai ở đâu + trị mới trace về token nào, để không ai
đổi nhầm lại.

### 6.2 FIX — `minimize.svg` trạng thái hover dùng mã màu bịa, không khớp token vàng

**Trước khi sửa:** `<g id="hover"><circle ... fill="#F2B749"/></g>` — không
khớp `vang_tam #F2C66D` (gold/`--gold`) hay `gold-dark #E5A53E`. So sánh với
`close.svg` (active=coral-dark `#D94D43` → hover=coral `#F26A52` → pressed=
coral-light `#FF8B6C`, ĐÚNG 3 bước dark→base→light của 1 họ token) và
`maximize.svg`/`restore.svg` (active=dai `#92212E` → hover=son `#C93643` →
pressed=canh_light `#E56365`, cũng ĐÚNG 3 bước) — `minimize.svg` là nút DUY
NHẤT lệch khỏi quy tắc 3-bước-đúng-token mà 2 nút khác tuân thủ chính xác.

**Đã sửa:** hover đổi thành `#F2C66D` (vang_tam/`--gold`, đúng bước giữa của
họ vàng `gold-dark→gold→gold-light`). Comment trong file đã ghi lại lý do.

### 6.3 Ghi nhận không sửa — 3 nút cùng tông đỏ (đã tự nhận trong code)

`maximize.svg`/`restore.svg` dùng cùng họ đỏ với `close.svg` (khác nhau sắc độ:
đỏ đài/đỏ son vs san hô) vì bảng màu v2 bỏ ngọc/jade. Chính file đã ghi "nếu cần
phân biệt rõ hơn 3 nút, cân nhắc thêm màu thứ 4 ở một đợt thiết kế sau" — đây là
đánh đổi đã được team trước cân nhắc có chủ đích, không phải trôi lệch; giữ
nguyên, không nằm trong phạm vi "surgical fix" của wave này (sẽ cần quyết định
thêm màu thứ 4 — thay đổi thẩm mỹ, không phải sửa lỗi).

### 6.4 Layout — ĐẠT, khớp `namios.css` 1:1

`NaMiOSLotusrc` border/title/button đo khớp chính xác `.nm-window`/
`.nm-titlebar`/`.nm-lights` trong `branding/style/namios.css` (viền 1px,
titlebar 46px = 6+34+6, nút 13px gap 8px) — đối chiếu từng số, không lệch.

## 7. Color scheme — `usr/share/color-schemes/NaMiOS.colors` (sở hữu Team 1)

Sinh tự động bởi `branding/design-system/make-colorscheme.py` từ
`branding/design-system/tokens.json` — đã chạy lại đối chiếu thủ công toàn bộ
8 nhóm `[Colors:*]` + `[WM]`: mọi `DecorationFocus/DecorationHover=201,54,67`
(son), `ForegroundActive=146,33,46` (dai), `ForegroundLink=0,110,114`
(action.primary teal), `ForegroundPositive/Negative/Neutral` khớp đúng
`status.success/error/warning` sáng. Không phát hiện lệch.

**Việc đã làm:** không cần sửa.

## 8. Cross-cutting — `design/tokens.json` (PL12 data, sở hữu UX12/PL12 team, KHÔNG sửa)

Phát hiện quan trọng nhất của audit này: `design/tokens.json`
(`$meta.version: "pl12-v1"`, 07/11/2026) vẫn giữ **bảng màu RUBY `#a21f46`/nền
navy `#0a1322`** (dòng 111, 121, 137 — `brand_note` còn ghi "KHÔNG đổi giá trị
brand ở file này") — bảng này **lỗi thời từ trước đợt đổi nhận diện Sen Việt v2
(09/11/2026)** và **không khớp bất kỳ asset đã đóng gói nào** đã đối chiếu
trong audit này (boot/plymouth/SDDM/calamares/plasma/aurorae/color-scheme —
tất cả đều dùng đúng son/dai/vang_tam/muc_dem). File này còn bị 1 token khác
tên số liệu khác hẳn `branding/design-system/tokens.json` ở MỌI `status.*`
(ví dụ success tối: `#3fae72` ở đây vs `#59C798` đang chạy thật) và radius
(6/10/16, không khớp asset nào — xem `DESIGN-SYSTEM.md` §3.1).

`design/tokens.json` được tham chiếu bởi `design/glossary.vi.json`,
`design/keyboard-shortcuts.json` (gián tiếp qua cùng thư mục `design/`), và
nhiều mục trong `docs/backlog/UX12-backlog.md` — các tham chiếu đó đều về
**số liệu KHÔNG-màu** (spacing/control/motion/phím tắt), nên không bị ảnh
hưởng trực tiếp bởi bảng màu lỗi thời. Rủi ro thật: bất kỳ ai code QML mới đọc
thẳng `design/tokens.json.color` để lấy `brand` sẽ ra sai màu toàn bộ.

**Khuyến nghị (đã ghi vào `docs/design/DESIGN-SYSTEM.md` §1.2/§2/§3.1, chưa
sửa file):** nhóm sở hữu `design/tokens.json` (UX12/PL12) đồng bộ lại
`color.*`/`typography.type.*`/`radius.*` theo bảng đã hợp nhất ở
`DESIGN-SYSTEM.md` §1.2/§2/§3.1 ở một đợt cập nhật riêng của `design/`. Đây là
đúng mục "Bước tiếp theo #4" đã ghi sẵn trong
`docs/adr/ADR-0016-design-system-integration.md` — audit này xác nhận lại mục
đó vẫn CHƯA đóng, kèm bằng chứng cụ thể hơn (asset nào đang dùng giá trị nào).

## 9. Cross-cutting — `branding/style/namios.css` (sở hữu branding/style, KHÔNG sửa)

- Font stack dòng 47: `"Cantarell", "Inter", "Noto Sans", ...` — xếp Inter
  TRƯỚC Noto Sans trong fallback, dù đây là nguồn mà chính Plasma/Aurorae/SDDM
  tham chiếu "màu DUY NHẤT = brand.json" cho phần màu. Phần FONT của file này
  không có ghi chú "nguồn duy nhất" tương tự, nhưng việc liệt kê Inter/Cantarell
  trước Noto Sans dễ bị đọc nhầm là đã duyệt — nên đây là nguồn khiến SDDM
  chọn Inter làm mặc định (mục 3.1). **Khuyến nghị:** đổi thứ tự thành
  `"Noto Sans", "Inter", "Cantarell", ...` hoặc ghi rõ ở đầu file rằng thứ tự
  này chỉ dành cho mockup/preview web, không phải khuyến nghị font hệ thống.
- Radius/shadow (`--r-sm/md/lg/xl`, `--sh-1/2/3`) = nguồn CHÍNH XÁC của "Thang
  B" đã đặt tên ở `DESIGN-SYSTEM.md` §3.1/§3.2 — không có lỗi, chỉ cần
  `namios.css` tự thêm 1 dòng chú thích trỏ ngược vào §3.1 để người đọc không
  tưởng đây là một thang độc lập thứ 3.

## 10. Tổng kết fix đã áp dụng (surgical, trong 3 cây asset sở hữu)

| # | File | Thay đổi | Rủi ro |
| - | --- | --- | --- |
| 1 | `usr/share/aurorae/themes/NaMiOSLotus/NaMiOSLotusrc` | `ActiveTextColor` 23,44,61→**24,46,59**; `InactiveTextColor` 112,125,138→**82,100,107** | Thấp — chỉ đổi giá trị màu chữ titlebar về đúng token đã audit WCAG sẵn, không đổi layout/kích thước |
| 2 | `usr/share/aurorae/themes/NaMiOSLotus/minimize.svg` | hover `#F2B749`→**`#F2C66D`** | Thấp — 1 ô màu, giữ đúng pattern 3-bước đã dùng ở 2 nút khác |

Không có thay đổi nào trong `usr/share/plasma/desktoptheme/NaMiOS-Sen/**` hay
`usr/share/color-schemes/**` — cả hai đã đối chiếu ĐẠT, không cần sửa.

## 11. Khuyến nghị gửi các team khác (không tự sửa)

1. **SDDM team:** đổi `fontFamily` trong `theme.conf` → `"Noto Sans"`; sửa
   `Clock.qml:37,47` đọc config thay vì hard-code `"Inter"` (xem mục 3.1).
2. **branding/style team:** xếp lại font stack `namios.css:47` (Noto Sans
   trước Inter/Cantarell) hoặc ghi rõ phạm vi "chỉ mockup web" (xem mục 9); ghi
   chú trỏ ngược `--r-*`/`--sh-*` vào `DESIGN-SYSTEM.md` §3.1/§3.2.
3. **UX12/PL12 team (`design/tokens.json`):** đồng bộ `color.*` (bỏ ruby
   `#a21f46`), `typography.type.*`, `radius.*` theo bảng đã hợp nhất ở
   `DESIGN-SYSTEM.md` §1.2/§2/§3.1 (mục 8 ở trên).
4. **Mọi team dùng `#f7f6f1`/`#b7c4cf` (SDDM, Calamares) hoặc `#F8F5EE`/
   `#C9D3D6` (branding/design-system):** quyết định ở đợt sau có gộp 2 cặp gray
   "chữ chính/phụ trên nền tối" near-duplicate này thành 1, hay đặt tên chính
   thức là "Thang C" riêng giống cách §3.1 đã đặt tên cho radius (mục 3.2/4).
5. **Wallpaper rights (đã có cờ đỏ ở nơi khác, nhắc lại ở đây để không lạc
   mất):** `docs/roadmap/NANG-CAP-NHU-CAU-NGUOI-DUNG.md` đã ghi nhận 25 thư
   mục ảnh thật trong `usr/share/wallpapers/` chưa đối chiếu nguồn/quyền với
   `design/wallpaper-manifest.json` (vẫn 0 ảnh thật) — audit này KHÔNG điều
   tra thêm (ngoài phạm vi token hình ảnh), chỉ liên kết lại trong
   `DESIGN-SYSTEM.md` PL12.5 để hai tài liệu không lạc nhau.
