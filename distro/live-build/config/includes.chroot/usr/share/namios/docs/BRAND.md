# NaMiOS — Bộ nhận diện "Đông Sơn" v3.0 (brand core: màu + logo + KDE theme)

**Status:** `verified_on_host: NO`. Mọi màu/SVG dưới đây được viết/kiểm tra bằng
công cụ offline (`python3 -c "import json;json.load(...)"` cho JSON,
`xml.dom.minidom` cho SVG, `configparser` cho `.colors`/`kdeglobals`, và tính
tay/bằng script contrast ratio theo công thức WCAG 2.x cho các cặp màu quan
trọng) — CHƯA có bản boot KDE Plasma thật nào xác nhận hiển thị đúng. Không có
`git commit`/push nào được thực hiện cho đợt sửa này.

**Phạm vi sửa đổi (wave "brand core", 11/11/2026):** CHỈ 6 nhóm tài sản —
palette + logo gốc + KDE color-scheme + kdeglobals accent + desktoptheme colors
+ 2 file QML palette — theo đúng danh sách sở hữu dưới đây. KHÔNG đụng
sddm/plymouth/look-and-feel/calamares/icons/apps/docs khác (các wave khác sở
hữu các phần đó; họ đọc màu TỪ `brand.json`/các file này nhưng không bị sửa ở
đây).

**Nguồn:** bộ kit "Đông Sơn" do chủ thương hiệu cung cấp, đã nằm sẵn trong kho
mã ở `branding/kit/NaMi_Brand_DongSon_v1/` (xem `README.md`,
`05_design_tokens/tokens.json`, `06_implementation/PLACEMENT_MAP.md` trong đó).
Bộ này THAY THẾ "Sen Việt" v2.0 (09/11/2026, đỏ son/vàng trên mực đêm) — bản
Sen Việt v2.0 và "Sen bừng sáng" v1.0 cũ hơn vẫn còn nguyên trong kho mã, không
xoá, chỉ không còn là bản runtime đang dùng.

---

## 1. AUTHORITATIVE PALETTE — 6 mã gốc "NaMiOS v3 Đông Sơn"

Đây là nguồn màu DUY NHẤT cho bộ nhận diện (brand/logo). Mọi màu khác xuất
hiện trong các file dưới đây (xám trung tính, xanh lá "thành công", vàng cam
"cảnh báo"...) là màu CHỨC NĂNG của lớp token UI riêng
(`branding/design-system/tokens.json`), KHÔNG thuộc palette này, KHÔNG bị đổi
bởi wave này.

| Vai trò | Tên | Hex | RGB |
|---|---|---|---|
| Nền tối/chính | navy | `#092D4F` | `9,45,79` |
| **Signature accent** — KDE highlight/selection/focus/progress (mã "sang trọng" chủ lực) | gold | `#DEA93E` | `222,169,62` |
| Action/attention/destructive/error | vermilion | `#D64C3E` | `214,76,62` |
| Secondary/support accent | teal | `#278F8D` | `39,143,141` |
| Nền sáng/nội dung | ivory | `#FFF9EF` | `255,249,239` |
| Trắng | white | `#FFFFFF` | `255,255,255` |

Quy tắc tương phản gốc (đo bằng công thức WCAG, không làm tròn lạc quan):

| Cặp | Tỷ lệ | Dùng được cho |
|---|---|---|
| navy / ivory hoặc white | 13.4:1 / 14.0:1 | Chữ thường mọi cỡ |
| gold / navy (2 chiều) | 6.57:1 | Chữ + nền + viền trên nền TỐI |
| **white / gold** | **2.13:1** | **KHÔNG DÙNG** — chữ trắng trên nền vàng kim KHÔNG đọc được |
| vermilion / white hoặc ivory | 4.23:1 / 4.04:1 | Chữ LỚN/đậm, nút, icon — KHÔNG đủ cho chữ thường nhỏ (cần 4.5:1) |
| teal / white hoặc ivory | 3.89:1 / 3.71:1 | Link/icon cỡ vừa — KHÔNG đủ cho chữ thường nhỏ |
| vermilion / navy | 3.31:1 | Chỉ chữ lớn/đậm (≥18pt hoặc 14pt bold) hoặc đối tượng đồ hoạ (viền, icon) |

→ Hệ quả thiết kế bắt buộc: **nền vàng kim luôn đi với CHỮ NAVY ĐẬM, không
bao giờ chữ trắng**; vermilion/teal gốc chỉ dùng an toàn cho chữ LỚN/nút/icon,
không dùng làm chữ thường nhỏ trên nền sáng hay nền tối.

## 2. Sắc độ phụ trợ (derived — KHÔNG phải 1 trong 6 mã gốc)

6 mã gốc không đủ để vừa làm "khối màu nổi bật" vừa làm "chữ thường đọc được"
ở MỌI vị trí (vd vermilion gốc trên trắng chỉ 4.23:1, dưới chuẩn AA 4.5:1 cho
chữ thường). Bản "Sen Việt" v2.0 cũ đã có đúng tiền lệ này ("đài" `#92212E`
đậm hơn "sơn" `#C93643` làm riêng cho vai chữ) — v3 tiếp tục tiền lệ đó, suy ra
bằng cách đổi **lightness** (HSL) của đúng 1 trong 6 mã gốc, giữ nguyên
hue/saturation, rồi đo lại contrast cho tới khi đạt ≥ AA. Các sắc độ này CHỈ
dùng trong `usr/share/color-schemes/NaMiOS.colors`,
`usr/share/plasma/desktoptheme/NaMiOS-Sen/colors`, và
`usr/share/namios/qml/SenVietPalette.qml` — KHÔNG đưa vào `brand.json` (file
đó giữ nguyên đúng 6 mã gốc cho mọi nơi đọc trực tiếp, xem mục 4).

| Tên | Hex | RGB | Suy từ | Dùng khi | Contrast đo được |
|---|---|---|---|---|---|
| vermilion-deep | `#A02E22` | `160,46,34` | vermilion, L 54%→38% | Chữ đỏ (lỗi/nhấn) trên nền SÁNG | 7.22:1 trên trắng, 6.89:1 trên ivory |
| vermilion-light | `#E48A81` | `228,138,129` | vermilion, L 54%→70% | Chữ đỏ (lỗi) trên nền TỐI (navy) | 5.50:1 trên navy |
| gold-deep | `#8B6518` | `139,101,24` | gold, L 56%→32% | Chữ vàng/focus-ring trên nền SÁNG | 5.29:1 trên trắng, ~5.0:1 trên ivory |
| navy-subtle | `#0A3257` | `10,50,87` | navy, L 17%→19% | Panel/hàng-chẵn tầng giữa trên nền TỐI | (nền, không áp dụng contrast-chữ) |
| navy-card | `#0B3965` | `11,57,101` | navy, L 17%→22% | Card nổi tầng cao trên nền TỐI | (nền) |
| ivory-subtle | `#FFF2DB` | `255,242,219` | ivory, L 97%→93% | Chip/ô nền tầng giữa trên nền SÁNG | (nền) |
| teal-light | `#5FD3D1` | `95,211,209` | teal, L 36%→60% | Link/action text trên nền TỐI (navy) | 7.82:1 trên navy |
| teal-deep | `#1F706F` | `31,112,111` | teal, L 36%→28% | Trạng thái :hover của action trên nền SÁNG | (đậm hơn teal gốc, dùng cho hover, không phải vai chữ-tối-thiểu) |

## 3. Tài sản logo — bản MASTER

Nguồn chuẩn = SVG. `brand.json` (mục 4) khai báo CHÍNH XÁC file nào là master
cho mỗi vai trò; danh sách dưới đây để tiện đối chiếu khi mở trực tiếp thư mục
`usr/share/namios-branding/logo/`:

- **`NaMiOS_Symbol_Color.svg`** — MASTER biểu tượng độc lập (mặt trống đồng,
  đầy đủ màu). Đây là file mà `brand.json.symbol` trỏ tới, và cũng là file
  Splash.qml của KDE (wave khác sở hữu) đang `Image.source` tới.
- `NaMiOS_Logo_Master_Outlined.svg` — MASTER logo ngang nền sáng, chữ
  **"NaMiOS"** đầy đủ (không chỉ "NaMi" — xem lưu ý tên sản phẩm dưới đây) hai
  màu: "NaMi" navy, "OS" vermilion.
- `NaMiOS_Logo_Master_Outlined_Dark.svg` — bản nền tối của file trên: nền navy
  đổ đầy, "NaMi" ivory, "OS" gold.
- `NaMiOS_App_Icon_Master.svg` — MASTER app icon: squircle navy (rx=108/512,
  đồng bộ quy ước icon kiểu iOS/iPadOS đã dùng cho NaMiOS-Lotus) chứa biểu
  tượng trống đồng thu nhỏ scale 0.78125 + margin ~56px mỗi phía (nhiều hơn
  clear-space tối thiểu 0.15× đường kính yêu cầu trong kit).
- `NaMiOS_Logo_Master_Stacked.svg` — **MỚI thêm**, logo xếp dọc (biểu tượng
  trên, chữ "NaMiOS" dưới), chưa từng có file tương đương trước đây.
- `NaMiOS_Symbol_White.svg` / `NaMiOS_Symbol_Black.svg` — **MỚI thêm**, bản
  đơn sắc trắng/đen (đen = mực `#101820`, không phải `#000000` tuyệt đối, dễ
  chịu hơn khi in) cho vật liệu chỉ in 1 màu.
- `NaMiOS_Symbol_DarkBackground.svg` — **MỚI thêm**, giống bản màu đầy đủ
  nhưng đổi vành/nét phụ từ navy sang ivory để còn nhìn thấy trên nền sẫm.
- `NaMiOS_Symbol_Small.svg` — **MỚI thêm**, bản giản lược cho icon 16–32px
  (kit khuyến nghị dùng bản này dưới 48px, bản đầy đủ sẽ nhoè ở cỡ đó).

**Xác nhận: đã thay toàn bộ hình học SEN (7 cánh hoa + đài + nhuỵ) bằng hình
học TRỐNG ĐỒNG ĐÔNG SƠN** (2 vành đồng tâm, hoa văn tia "mặt trời" ở tâm, 4
điểm tia 4 hướng, 2 dải hoa văn sóng trên/dưới) ở cả 4 file master đang có
sẵn trong repo (`NaMiOS_Symbol_Color.svg`, `NaMiOS_Logo_Master_Outlined.svg`,
`NaMiOS_Logo_Master_Outlined_Dark.svg`, `NaMiOS_App_Icon_Master.svg`) — không
còn path nào vẽ hình hoa sen trong các file này.

**Lưu ý tên sản phẩm:** kit gốc chỉ viết chữ "NaMi" trên các lockup (xem
`branding/kit/NaMi_Brand_DongSon_v1/01_logo_svg/nami-lockup-*.svg`). TẤT CẢ
lockup trong `usr/share/namios-branding/logo/` ở bài sửa này đều viết đủ
**"NaMiOS"** (tspan 2 màu: phần gốc + "OS" nhấn accent) — KHÔNG đổi tên hệ
điều hành thành "NaMi".

## 4. `brand.json` — màu mới

Giữ ĐÚNG shape/keys cũ (ứng dụng Python đọc trực tiếp 9 khoá trong `colors`
không bị vỡ). Giá trị:

```json
{
  "name": "NaMiOS",
  "mark_name": "Đông Sơn",
  "version": "3.0",
  "light_lockup": "NaMiOS_Logo_Master_Outlined.svg",
  "dark_lockup": "NaMiOS_Logo_Master_Outlined_Dark.svg",
  "symbol": "NaMiOS_Symbol_Color.svg",
  "app_icon": "NaMiOS_App_Icon_Master.svg",
  "small_app_icon": "NaMiOS_App_Icon_1024.png",
  "colors": {
    "son": "#D64C3E",
    "canh_dark": "#D64C3E",
    "canh": "#D64C3E",
    "canh_light": "#D64C3E",
    "dai": "#D64C3E",
    "vang_tam": "#DEA93E",
    "vang_nuoc": "#DEA93E",
    "muc_dem": "#092D4F",
    "chu_muc": "#092D4F"
  }
}
```

9 khoá cũ (5 sắc đỏ `son/canh/canh_dark/canh_light/dai` + 2 sắc vàng
`vang_tam/vang_nuoc` + `muc_dem`/`chu_muc`) GIỮ TÊN nhưng giờ chỉ còn ánh xạ
về đúng **2 mã**: `#D64C3E` (vermilion) cho mọi khoá đỏ, `#DEA93E` (gold) cho
2 khoá vàng, `#092D4F` (navy) cho `muc_dem`/`chu_muc`. Lý do không dùng
vermilion-deep/gold-deep (mục 2) ở đây: đã grep toàn bộ `opt/namios/*/branding.py`
— các khoá này chỉ được dùng làm NỀN/VIỀN (`border-bottom`, `background-color`
của frame/badge), không dùng làm chữ thường nhỏ, nên không cần sắc độ phụ trợ;
nếu sau này có consumer MỚI dùng các khoá này làm chữ, họ cần tự áp
vermilion-deep/gold-deep ở lớp của họ (brand.json vẫn chỉ giữ 6 mã gốc, không
lẫn sắc độ phụ trợ vào nguồn màu nhận diện chính).

## 5. Đối chiếu file đã sửa

| File | Vai trò | Đã sửa |
|---|---|---|
| `usr/share/namios-branding/logo/brand.json` | Nguồn màu nhận diện DUY NHẤT | `colors` 9 khoá → 2 mã mới; `mark_name`/`version`/`date`/`previous_mark`/`jade_removed_note` cập nhật lịch sử |
| `usr/share/namios-branding/logo/NaMiOS_Symbol_Color.svg` | Master biểu tượng | Thay hình sen → trống đồng (màu đã đúng v3 sẵn từ kit) |
| `usr/share/namios-branding/logo/NaMiOS_Logo_Master_Outlined.svg` | Master logo ngang sáng | Thay hình + chữ "NaMi"+"OS" 2 màu navy/vermilion |
| `usr/share/namios-branding/logo/NaMiOS_Logo_Master_Outlined_Dark.svg` | Master logo ngang tối | Thay hình + chữ "NaMi"+"OS" 2 màu ivory/gold |
| `usr/share/namios-branding/logo/NaMiOS_App_Icon_Master.svg` | Master app icon | Squircle navy + trống đồng thu nhỏ |
| `usr/share/namios-branding/logo/NaMiOS_Logo_Master_Stacked.svg` | **Mới** — lockup xếp dọc | Tạo mới từ kit |
| `usr/share/namios-branding/logo/NaMiOS_Symbol_White.svg` | **Mới** — đơn sắc trắng | Tạo mới từ kit |
| `usr/share/namios-branding/logo/NaMiOS_Symbol_Black.svg` | **Mới** — đơn sắc đen | Tạo mới từ kit |
| `usr/share/namios-branding/logo/NaMiOS_Symbol_DarkBackground.svg` | **Mới** — bản cho nền tối | Tạo mới từ kit |
| `usr/share/namios-branding/logo/NaMiOS_Symbol_Small.svg` | **Mới** — bản giản lược <48px | Tạo mới từ kit |
| `usr/share/color-schemes/NaMiOS.colors` | KColorScheme ứng dụng (sáng) | Decoration/Selection → gold; Selection chữ trắng→navy; ForegroundActive/Negative → vermilion-deep; Link/Visited → teal |
| `etc/skel/.config/kdeglobals` | Accent mặc định user mới | `AccentColor` 201,54,67 → 222,169,62 (gold) |
| `usr/share/plasma/desktoptheme/NaMiOS-Sen/colors` | Màu mặc định Plasma::Theme (tối) | Nền → navy/navy-subtle; ForegroundActive/Decoration/Visited → gold; ForegroundNegative → vermilion-light; Link → teal |
| `usr/share/namios/qml/SenVietPalette.qml` | Token màu QML cho ErrorCard/ConnectionStepper/AIPlanCard | Toàn bộ surface/text/brand/action/focus → v3; status giữ nguyên (lớp khác) |
| `usr/share/namios/qml/Gallery.qml` | Trang preview | Nền sáng/tối đổi sang ivory/navy; tiêu đề "Sen Việt"→"Đông Sơn" |
| `usr/share/namios/docs/BRAND.md` | Tài liệu này | Mới |

## 6. Việc CHƯA làm / rủi ro còn mở

- `verified_on_host: NO` cho toàn bộ — chưa boot KDE Plasma thật để xem màu
  hiển thị đúng (đặc biệt `[Colors:Selection]` đổi chiều sáng/tối chữ, cần xem
  bằng mắt).
- `NaMiOS_App_Icon_1024.png`, `NaMiOS_Logo_Dark_2400.png`,
  `NaMiOS_Logo_Light_2400.png`, `NaMiOS_Favicon.ico`,
  `NaMiOS_Symbol_Transparent_1024.png` — các PNG/ICO raster trong cùng thư mục
  logo **CHƯA được tái xuất** từ SVG mới (ngoài phạm vi yêu cầu của wave này —
  chỉ SVG). `usr/share/sddm/themes/namios/Main.qml` (wave khác sở hữu) đang
  dùng trực tiếp `NaMiOS_Symbol_Transparent_1024.png` — ảnh đó VẪN LÀ hình sen
  cũ cho tới khi có người xuất lại PNG từ `NaMiOS_Symbol_Color.svg`/
  `NaMiOS_Symbol_White.svg` mới.
- `branding/design-system/make-colorscheme.py` (script sinh `NaMiOS.colors`
  tự động) vẫn đọc token CŨ — file `.colors` ở đây đã sửa TAY trực tiếp theo
  v3; nếu chạy lại script đó mà chưa cập nhật nguồn token, file sẽ bị ghi đè
  mất các thay đổi này.
- `opt/namios/*/branding.py` (NaMiOS Assistant/An toàn/Dịch vụ/Màn chiếu) có
  hằng số dự phòng CỨNG (`_FALLBACK_COLORS`) khớp `brand.json` v2.0 — các file
  đó do wave khác sở hữu, KHÔNG được sửa ở đây; hằng số dự phòng sẽ lệch với
  `brand.json` v3.0 mới cho tới khi wave sở hữu các file đó tự đồng bộ lại.
