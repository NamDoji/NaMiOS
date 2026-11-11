# NaMiOS — Hệ thiết kế giao diện (Design System) · PRA-036/037/039/040

> **CẬP NHẬT 11/11/2026 — hợp nhất "một nguồn sự thật" (wave "design-system
> consolidation", Team 1).** Trước bản này, repo có **3 bộ số token lệch nhau**
> (D0 RUBY navy §1 gốc dưới đây · PL12 `design/tokens.json` 07/11 · Sen Việt
> `branding/design-system/tokens.json` 09/11) cùng tự xưng "nguồn sự thật". Bản
> này **thay toàn bộ nội dung §1–§3/§5/§9 bằng giá trị Sen Việt v2 đang THỰC SỰ
> CHẠY trên các asset đã đóng gói** (đối chiếu trực tiếp `usr/share/color-schemes/
> NaMiOS.colors`, `usr/share/plasma/desktoptheme/NaMiOS-Sen/**`,
> `usr/share/aurorae/themes/NaMiOSLotus/**`, `usr/share/sddm/themes/namios/**`,
> `etc/calamares/branding/namios/**`, `config/bootloaders/**` — tất cả đã dùng
> đúng brand.json v2 từ 09-10/11), KHÔNG phải chọn theo lý thuyết. Mục "PL12" ở
> cuối file **giữ nguyên các mã neo PL12.1–PL12.7** (nhiều file khác tham chiếu
> thẳng tới các mã này — xem `docs/adr/ADR-0016-design-system-integration.md`,
> `docs/backlog/UX12-backlog.md`, `docs/l10n/TERMINOLOGY-REVIEW.md`,
> `docs/roadmap/WINDOWS-FEATURE-PARITY.md`) nhưng nội dung đã RÚT GỌN thành con
> trỏ trỏ vào §1–§10 phía trên — không còn số liệu trùng/lệch ở hai nơi.
>
> **Nguồn màu/logo DUY NHẤT vẫn là** `usr/share/namios-branding/logo/brand.json`
> (mực đêm `#122A3A`, vàng tâm `#F2C66D`, vàng nước `#BC8A43`, đỏ cánh
> `#AB2430→#E56365`, đỏ đài `#92212E`, đỏ son `#C93643`). **Lớp token máy đọc
> được chi tiết hơn** (đã đo WCAG, sinh ra `.colors`/`components.css`) là
> `branding/design-system/tokens.json` — bảng dưới đây là bản tóm tắt + diễn
> giải vai trò của chính file đó, không phải một con số thứ ba. Ngôn ngữ hình
> ảnh dạng CSS (icon squircle kiểu iOS/iPadOS + kính mờ + dock) =
> `branding/style/namios.css` (xem `branding/style/demo.html`).
>
> **CẢNH BÁO NGUỒN CŨ — KHÔNG DÙNG CHO MÀU:** `design/tokens.json` (PL12-v1,
> 07/11/2026) vẫn còn bảng màu RUBY `#a21f46`/nền navy `#0a1322` — bảng đó
> **lỗi thời từ trước khi đổi nhận diện sang Sen Việt v2 (09/11/2026)** và
> KHÔNG khớp bất kỳ asset đã đóng gói nào (đối chiếu: không file `.colors`,
> theme Plasma, SDDM, Calamares, GRUB, Plymouth nào trong repo dùng `#a21f46`).
> Các phần KHÔNG-màu của file đó (spacing/control/icon/motion) vẫn dùng được
> làm tham khảo bổ sung — xem ghi chú "lệch cần đồng bộ" ở từng mục. Xem thêm
> `docs/design/CONSISTENCY-AUDIT.md` cho audit đầy đủ theo từng surface.

> **Phạm vi D0:** đây là **đặc tả hệ thiết kế + từ vựng** để 5 màn hình chính dùng
> CHUNG một ngôn ngữ hình ảnh, KHÔNG sao chép tài sản Microsoft (SYS-006/PRA-018).
> Mockup trong `docs/design/mockups/` minh hoạ các token này. `verified_on_boot: NO`
> cho tới khi dựng KDE thật trên ISO.

## 1. Thương hiệu + màu (PRA-036) — Sen Việt v2

Màu thương hiệu = **ĐỎ SON `#C93643`** (brand.json, thay RUBY `#a21f46` của bản
D0 gốc 07/11 — xem khung cảnh báo ở đầu file). Nền **ngà ấm** cho vùng nội dung
sáng (sen quý không đặt trên nền đen — quyết định 09/11/2026), nền **mực đêm**
cho desktop/chế độ tối. Nguồn số liệu: `branding/design-system/tokens.json` →
`color.light`/`color.dark` (đã đo tương phản WCAG 2.2, xem `color.contrast_table`
trong file đó); giá trị dưới đây là bảng đã **hợp nhất bản chỉnh WCAG** — không
còn phân biệt "gốc vs đã chỉnh" như bản PL12.2 cũ, giá trị dưới đây là chốt thật.

### 1.1 Bảng màu thương hiệu gốc (brand.json)

| Tên | Hex | Vai trò |
| --- | --- | --- |
| `son` | `#C93643` | Đỏ son — nhận diện/nhấn/nền nút chính |
| `canh_dark` | `#AB2430` | Đỏ cánh đậm — gradient logo |
| `canh` | `#CF3540` | Đỏ cánh |
| `canh_light` | `#E56365` | Đỏ cánh nhạt — chữ/nhấn trên nền tối |
| `dai` | `#92212E` | Đỏ đài — chữ đỏ an toàn trên nền sáng (≥7.5:1) |
| `vang_tam` | `#F2C66D` | Vàng tâm — chữ/nhấn trên nền tối |
| `vang_nuoc` | `#BC8A43` | Vàng nước — trang trí/icon trên nền sáng |
| `muc_dem` | `#122A3A` | Mực đêm — nền desktop/dialog tối |
| `chu_muc` | `#182E3B` | Chữ mực — chữ chính trên nền sáng |

### 1.2 Token ngữ nghĩa (sáng/tối) — nguồn: `branding/design-system/tokens.json`

| Token | Vai trò | Sáng | Tối |
| --- | --- | --- | --- |
| `surface.base` | Nền desktop/trang/dialog | `#F5F2EB` | `#122A3A` |
| `surface.card` | Panel/card/dialog nổi | `#FFFFFF` | `#1B3748` |
| `surface.subtle` | Nền chìm nhẹ (chip, hàng chẵn) | `#EDE6D8` | `#16303F` |
| `text.primary` | Chữ chính | `#182E3B` | `#F8F5EE` |
| `text.secondary` | Chữ phụ/metadata | `#52646B` | `#C9D3D6` |
| `brand.red` | Nhận diện/nhấn/nền nút | `#C93643` | `#E56365`* |
| `brand.red-deep` | Chữ đỏ an toàn / nền nút tối | `#92212E` | `#C93643` |
| `brand.gold` | Trang trí/icon | `#BC8A43` | `#F2C66D` |
| `brand.gold-soft` | Nhấn trang trí | `#F2C66D` | `#BC8A43` |
| `action.primary` | Nút hành động chính (teal) | `#006E72` | `#65D7C8` |
| `action.hover` | Hover/pressed của action | `#005A5E` | `#7CE0D3` |
| `status.success` | Đã xong | `#127A52` | `#59C798` |
| `status.warning` | Chú ý/một phần | `#965300` | `#F6BB68` |
| `status.error` | Lỗi/chặn | `#B4232B` | `#FF8B8F` |
| `status.info` | Trung tính/chưa xác định | `#1F5E70` | `#9DB3BC` |
| `focus.ring` | Viền focus bàn phím ≥2px | `#006E72` | `#65D7C8` |
| `border.subtle` | Viền/chia — CHỈ trang trí | `#D9CDB7` | `#2E4A5B` |
| `border.strong` | Viền mang nghĩa (≥3:1) | `#8C8068` | `#657F90` |
| `link`† | Liên kết văn bản | `#0B63CE` | `#6FB0EF` |

\* `brand.red` ở nền TỐI (`#E56365`) làm **chữ thường** KHÔNG đạt 4.5:1 (xem §5)
— chỉ dùng làm nhấn/chữ lớn/icon hoặc nền nút (với `red-deep` làm chữ an toàn
hơn). † Token `link` không có trong `branding/design-system/tokens.json`
("Sen Việt") — kế thừa từ `design/tokens.json` (PL12), vẫn hợp lệ vì không
xung đột giá trị với bộ Sen Việt, luôn kèm gạch chân/weight khác với `focus`
(không chỉ dựa màu, UX12-004).

**Trạng thái phải khớp từ vựng trung thực** (PRA-032): `status.success` = đã
xác nhận; `status.warning` = một phần/đang chờ; `status.error` = thất bại/chặn;
`status.info` = **chưa kiểm** (KHÔNG tô xanh "đạt" khi chưa có bằng chứng).

**Lệch cần đồng bộ (ghi nhận, chưa sửa — ngoài phạm vi file ảnh của team này):**
`design/tokens.json` (PL12) giữ một bộ `status.*`/`brand.*` khác hẳn (ruby
`#a21f46`, success tối `#3fae72`, error sáng `#c23127`...) — **không khớp** bảng
trên và **không khớp** bất kỳ asset đã đóng gói nào đã đối chiếu (xem khung cảnh
báo ở đầu file + `docs/design/CONSISTENCY-AUDIT.md` mục "design/tokens.json").
Khuyến nghị nhóm sở hữu file đó (UX12/PL12) đồng bộ lại theo bảng 1.2 ở một đợt
riêng.

## 2. Typography (PRA-036/039)

- Phông UI: **Noto Sans** (mặc định thật đang dùng — đủ dấu tiếng Việt Unicode).
  Fallback: DejaVu Sans, Liberation Sans, sans hệ thống. Mono: **Noto Sans Mono**
  (đường dẫn file, mã lỗi, correlation_id, log, terminal). KHÔNG dùng phông
  thương mại Windows (Calibri/Times New Roman...); không chép phông vào ISO
  (PRA-018). **Be Vietnam Pro** (OFL) là lớp nâng cấp thẩm mỹ **CÓ ĐIỀU KIỆN**
  — chỉ dùng khi nhóm thiết kế xác nhận glyph tiếng Việt (dấu, ư/ơ/đ) đạt chất
  lượng trên máy pilot thật; cho tới lúc đó Noto Sans là mặc định thật sự.
- Thang cỡ chữ chốt (dp @100%, nguồn `branding/design-system/tokens.json` →
  `typography.scale_dp`, khớp số cũ của §2 bản D0 gốc ở hero/h1/h2/h3):

| Mức | Cỡ (dp) | Dòng cao (dp) | Trọng lượng | Dùng cho |
| --- | --- | --- | --- | --- |
| `hero` | 32 | 40 | 600 (semibold) | Màn hình chào/hero |
| `h1` | 28 | 36 | 600 | Tên trang |
| `h2` | 22 | 30 | 600 | Tiêu đề mục |
| `h3` | 18 | 26 | 600 | Nhóm trường |
| `body` | 16 | 24 | 400 (regular) | Nội dung chính |
| `body-sm` | 15 | 22 | 400 | Nội dung dày |
| `label` | 14 | 20 | 500 (medium) | Nhãn trường/nút |
| `caption` | 13 | 18 | 400 | Chú thích phụ, chỉ trên nền tương phản tốt |
| `code` | 14 | 20 | 400 (mono) | Mã lỗi/log |

- Dòng cao chung: **1.4–1.6**. Số/tiền/ngày định dạng VN: `1.234.567 ₫`,
  `06/11/2026`, `08:25`. Số tabular khi phông hỗ trợ (bảng tiền/tiến trình).
- Zoom: hỗ trợ **100/115/130/150/200%**, mỗi mức phải **reflow** (không cắt nội
  dung/nút — WCAG 2.2 SC 1.4.4). KHÔNG viết HOA toàn bộ câu thông báo.

**Lệch cần đồng bộ:** `design/tokens.json` (PL12) có một thang chữ khác
(`h1:24, h2:20, h3:16-18, body:14-16`) — đây là **bản nháp sớm hơn** (07/11),
bị thang chữ ở bảng trên (khớp đúng §2 bản D0 gốc) thay thế. Khuyến nghị đồng
bộ số ở `design/tokens.json` theo bảng trên ở đợt cập nhật kế tiếp.

## 3. Spacing, bo góc, bóng, control, icon

- Thang spacing (px/dp, mọi nguồn đồng ý): `4 · 8 · 12 · 16 · 24 · 32 · 48`
  (bội số 4, nhịp chính 8). Panel padding 16; group gap 16/24.

### 3.1 HAI thang bo góc — có chủ đích, phạm vi khác nhau (điểm hợp nhất chính của bản 11/11)

Trước bản này, repo có **3 con số bo góc khác nhau** (8/12/12/999 ở §3 gốc ·
6/10/16 ở `design/tokens.json` PL12 · 8/12/16/999 ở `branding/design-system/
tokens.json`) không ai giải thích vì sao khác — đọc như trôi lệch ngẫu nhiên.
Đối chiếu trực tiếp asset đã đóng gói cho thấy **thực ra có đúng 2 thang, mỗi
thang dùng nhất quán cho một lớp bề mặt khác nhau**; bản này đặt tên + chốt
phạm vi cho cả hai, không đổi giá trị nào đang chạy trên theme đã QA:

| Thang | Giá trị (dp) | Dùng cho | Asset thật đang dùng |
| --- | --- | --- | --- |
| **A — UI component radius** | sm 8 / md 12 / lg 16 / pill 999 | Nút, ô nhập, select, chip, card, dialog **trong app** | `branding/design-system/components.css` (`--r-sm/md/lg/pill`), preview HTML |
| **B — Desktop-shell radius** ("squircle") | sm 10 / md 14 / lg 20 / xl 28 / icon ~22.37% | Panel/dock/tooltip/dialog **của chính desktop shell** (Plasma FrameSvg) + viền cửa sổ (Aurorae) + icon app | `usr/share/plasma/desktoptheme/NaMiOS-Sen/{widgets,dialogs}/*.svg` (28=xl cho panel/dialog, 14=md cho tooltip), `usr/share/aurorae/themes/NaMiOSLotus/decoration.svg` (10=sm cho góc cửa sổ), `branding/style/namios.css` (`--r-sm/md/lg/xl`, nguồn của thang B)

**Quy tắc chọn thang:** component **bên trong** một app (nút Lưu, ô tìm kiếm
trong dialog cài đặt) → thang A. Khung **của desktop/shell** (panel taskbar,
viền cửa sổ, tooltip hover icon, dock) → thang B. Thang B cố ý lớn hơn (kiểu
iPadOS) để phân biệt "khung hệ điều hành" khỏi "nội dung app" — đây là lựa chọn
thẩm mỹ đã áp dụng thật trên theme đã đóng gói, không phải lỗi cần thống nhất
về 1 số. `design/tokens.json` (PL12, 6/10/16) là **bản nháp thứ ba, không khớp
asset nào** — superseded bởi thang A, nên bỏ không dùng.

### 3.2 Bóng/elevation — cũng hai thang, cùng logic 3.1

| Thang | sm/1 | md/2 | lg/3 | Dùng cho |
| --- | --- | --- | --- | --- |
| **A — UI component** (sáng) | `0 1px 2px rgba(18,42,58,.10)` | `0 4px 12px rgba(18,42,58,.12)` | `0 12px 32px rgba(18,42,58,.18)` | Card/dialog/toast trong app |
| **A — UI component** (tối) | `0 1px 2px rgba(0,0,0,.35)` | `0 4px 12px rgba(0,0,0,.40)` | `0 12px 32px rgba(0,0,0,.50)` | nt, nền tối |
| **B — Desktop-shell glass** | `0 1px 2px rgba(5,16,28,.28)` | `0 6px 18px rgba(5,16,28,.30)` | `0 18px 48px rgba(5,16,28,.40)` | Panel/dock/launcher kính mờ (`--sh-1/2/3` trong `namios.css`) |

Giá trị cũ "panel nổi `0 8 24 rgba(4,10,22,.35)`" ở bản D0 gốc là **tiền thân**
của 2 thang trên (gộp chung trước khi tách theo lớp bề mặt) — không dùng riêng
nữa, đã thay bằng bảng trên.

### 3.3 Control, icon

- Chiều cao control: compact **36** / mặc định **40** / lớn **44** (dp); vùng
  click tối thiểu **40×40dp**, không nhỏ hơn vùng nhìn thấy; đủ cách giữa nút
  nguy hiểm (Xoá) và nút an toàn (Huỷ). Ô nhập: 40–44dp.
- Icon: 16 (nhỏ) / **24 (mặc định)** / 32 (lớn) dp, nét `stroke 1.9dp`, đầu/góc
  bo, `currentColor`; nếu không phân biệt ở 16px thì có biến thể symbolic giản
  lược. Nguồn: `branding/icons-system-v1/` (25 icon hạt giống, tự vẽ — KHÔNG
  dùng logo/icon hãng thứ ba, PRA-018). Toolbar 48–56dp (mặc định 52); sidebar
  224–280dp (mặc định 256, không chiếm hết vùng nội dung ở 1366×768); dialog
  400–560dp (nhỏ 400/vừa 480/lớn 560).

## 4. Trạng thái bắt buộc mỗi thành phần tương tác (PRA-036)

Mọi nút/ô nhập/mục danh sách PHẢI có đủ: **default · hover · focus (viền `focus.
ring` ≥2px, KHÔNG chỉ đổi màu) · active · disabled · error**. Thông báo lỗi nêu
**nguyên nhân quan sát được + việc cần làm** (PRA-039), không chỉ "Đã xảy ra
lỗi". Hai hiện thực tham chiếu thật đã có đủ các trạng thái này:
`branding/design-system/components.css` (12 component: Button/Field/Select/
Checkbox/Dialog/Toast/Progress/DeviceCard/ConnectionStepper/ErrorCard/
AIPlanCard) và `usr/share/aurorae/themes/NaMiOSLotus/*.svg` (nút cửa sổ: active/
hover/pressed/inactive/hover-inactive/pressed-inactive).

## 5. Tương phản + tiếp cận (PRA-040)

- Tương phản chữ/nền ≥ **4.5:1** (chữ thường), ≥ **3:1** (chữ lớn/icon/thành
  phần UI không-chữ) — mức WCAG 2.2 AA. Toàn bộ cặp ở bảng §1.2 đã **đo và đạt**
  mục tiêu tương ứng (xem `branding/design-system/tokens.json` →
  `color.contrast_table`, công thức WCAG 2.2 relative-luminance), **trừ 3 ngoại
  lệ đã biết, có quy tắc dùng an toàn**:
  1. `brand.red` làm **chữ thường trên nền tối** (`#E56365`/`#122A3A` = 4.45:1,
     trên card 3.74:1) → KHÔNG đạt 4.5:1, chỉ dùng làm nhấn/chữ lớn/icon (≥3:1)
     hoặc nền nút đặc (chữ trắng).
  2. `brand.red` làm chữ trên nền sáng (`#C93643`/`#F5F2EB` = 4.59:1) → **sát
     ngưỡng**; ưu tiên `brand.red-deep` (`#92212E`, ≥7.5:1) cho chữ đỏ quan
     trọng.
  3. `brand.gold` trên nền sáng (`#BC8A43`/card = 3.06:1) → chỉ đạt mức UI/chữ
     lớn (≥3:1), KHÔNG dùng làm chữ thường cỡ nhỏ trên nền sáng. Ở nền tối,
     `#F2C66D` đạt ≥7.7:1, dùng chữ được.
  - `border.subtle` (cả 2 mode) chỉ đạt ~1.2–1.5:1 — KHÔNG đạt 3:1 non-text
    (WCAG 1.4.11). Hợp lệ CHỈ KHI ranh giới control còn được thể hiện bằng cách
    khác (fill, bóng, focus-ring) — không phải cách DUY NHẤT nhận biết biên. Khi
    viền phải mang nghĩa, dùng `border.strong` (≥3:1).
- **Không truyền thông tin chỉ bằng màu**: trạng thái luôn kèm **nhãn chữ +
  icon** (vd "● Đã xác nhận", "▲ Một phần", "■ Chưa kiểm").
- Điều hướng bàn phím đầy đủ (Tab/Shift+Tab/Enter/Esc), focus thấy rõ (viền
  ≥2px bằng `focus.ring`, ≥3px ở chế độ tương phản cao, offset 2dp); hỗ trợ
  screen reader (nhãn cho mọi icon); phóng to **125–200%** không vỡ layout; cỡ
  chữ chỉnh được. Mục tiêu phát hành: **WCAG 2.2 AA** cho UI chính.

## 6. Layout + responsive (PRA-036)

- Mốc nhỏ nhất **1366×768**; đẹp cả màn lớn (≥1920, test matrix 1366×768 /
  1920×1080 / 2560×1440). Mockup vẽ ở khung `1600×1000`.
- Khung chung (shell) mọi màn hình: **taskbar dưới** (nút Bắt đầu trái · ô Tìm
  kiếm · app ghim · khay phải: VN·Telex / Wi‑Fi / loa / pin / đồng hồ
  `06/11/2026`) + **cửa sổ** có title-bar (nút ◯–▢–✕ tự vẽ) + nội dung.
- Chip "chế độ chạy" (Native / Web / Wine / VM / Remote) hiển thị ở chỗ **dễ
  thấy nhưng không quá tải** (PRA-037) — màu `status.info`, có nhãn chữ.

## 7. Năm màn hình chính + từ vựng chung (PRA-036/039)

Tất cả dùng cùng component (nút, thẻ, chip trạng thái, badge chế độ) + **từ vựng**:

| Màn hình | Nội dung chính | Bất biến trung thực thể hiện |
| --- | --- | --- |
| **Màn hình chính** (Desktop) | Taskbar + menu Bắt đầu (nhóm việc Văn phòng/Thuế/Kế toán/Bảo hiểm/Giáo dục/Hành chính) + icon + cửa sổ app | SmartAI là bong bóng phụ trợ (tắt vẫn dùng được) |
| **Ứng dụng** (Apps) | Danh mục app theo nhóm + badge chế độ chạy + trạng thái | "đã tải/mở được" ≠ "dùng được"; app chưa kiểm ghi **Chưa kiểm** |
| **Thiết bị** (Devices) | Máy in/scan/đa chức năng/Wi‑Fi/Bluetooth; **in·scan·copy·fax RIÊNG** từng dòng | copy **Chưa kiểm** dù in+scan ĐẠT (PRA-001) |
| **Mạng** (Network) | Wi‑Fi/Ethernet/VPN; trạng thái + lỗi cụ thể | mỗi lỗi một thông điệp riêng (PRA-029), không "khởi động router" chung |
| **SmartAI** (Bảng tác vụ) | "Tôi muốn làm gì" · tiến độ · bước chặn · quyền đã cấp · nguồn kết quả · nút Hoàn tác | "đã gửi hàng đợi" → "máy báo xong" → "**bạn** xác nhận đã nhận" (PRA-032/038) |

## 8. Từ vựng tiếng Việt chuẩn (PRA-039) — tránh thuật ngữ máy ở luồng phổ thông

| Dùng (phổ thông) | KHÔNG dùng ở luồng phổ thông |
| --- | --- |
| Bắt đầu · Tìm kiếm · Tệp của tôi · Máy này · Thùng rác | Start · Explorer · My PC |
| Mở · Lưu · In · Hủy · Cài đặt · Mặc định | Open/Save/Print trần không dịch |
| Đã gửi hàng đợi in · Máy báo in xong · Bạn đã nhận bản in | "completed" (trạng thái máy) |
| Đã ký · Đã nộp · Cổng đã trả biên nhận | gộp "đã nộp" = "xong" |
| Chạy kiểu: Máy Việt / Web / Thử-Wine / Máy ảo Windows / Máy Windows từ xa | prefix · COM · runtime · P/Invoke |
| Chưa kiểm · Một phần · Đạt · Thất bại · Bị chặn | "tương thích" khi mới discovery |

Thuật ngữ kỹ thuật (`prefix/COM/runtime/.NET`) chỉ xuất hiện trong mục **"Chi tiết cho
kỹ thuật viên"** (PRA-038), không ở luồng người dùng phổ thông. Glossary mở rộng
(55 thuật ngữ, không đổi bảng này) ở `design/glossary.vi.json` — xem PL12.7.

## 9. Icon (PRA-036/018)

Mọi biểu tượng là **vector tự vẽ** (SVG), KHÔNG dùng icon/logo Microsoft hay bộ
icon có giấy phép hạn chế. Style: nét đơn giản (stroke 1.9dp), bo nhẹ, 2 tông
(nền + đỏ son nhấn). Mỗi icon có nhãn chữ đi kèm (PRA-040). Kích cỡ + nguồn:
xem §3.3. Icon **app** (launcher, taskbar) dùng khung squircle thang B (§3.1) +
gradient 2 điểm theo `branding/style/namios.css` (`.nm-icon`), KHÁC với icon
**trong nội dung UI** (menu/list/button) dùng khung vuông/không-khung +
`currentColor` theo `branding/icons-system-v1/`.

## 10. Chuyển động (Motion) — mới tách thành mục riêng (trước ở PL12.3/elevation)

- Thời lượng: `fast 120ms · base 180ms · slow 220ms`. Easing:
  `cubic-bezier(0.2, 0, 0, 1)`. Chỉ thể hiện quan hệ trạng thái/cửa sổ, không
  trang trí.
- `prefers-reduced-motion: reduce` → tắt animation/transition/blur **ngay**,
  không cần khởi động lại; thay bằng đổi trạng thái tức thì (đã hiện thực ở
  `branding/design-system/components.css` cuối file).
- Chế độ giảm trong suốt: tắt hiệu ứng nền mờ (blur) khi ảnh hưởng đọc chữ/hiệu
  năng (máy yếu/không GPU).
- **Lệch cần đồng bộ:** `design/tokens.json` (PL12) ghi khoảng `120–250ms` và
  tự nhận là "giả thuyết ban đầu, chưa đo trên máy yếu" — tương thích với thang
  trên (120/180/220 nằm trong khoảng đó) nên KHÔNG coi là xung đột, chỉ là mức
  đo thô hơn; chưa cần sửa.

---

## PL12 — Mở rộng: Phụ lục 12 (UX12-001..048)

> **Phạm vi:** mục này giữ các mã neo PL12.1–PL12.7 vì nhiều file khác tham
> chiếu trực tiếp (`design/glossary.vi.json`, `design/tokens.json`,
> `docs/adr/ADR-0016-design-system-integration.md`,
> `docs/backlog/UX12-backlog.md`, `docs/l10n/TERMINOLOGY-REVIEW.md`,
> `docs/roadmap/WINDOWS-FEATURE-PARITY.md`, `docs/roadmap/
> NANG-CAP-NHU-CAU-NGUOI-DUNG.md`). Bản 11/11/2026 đã **gộp số liệu màu/chữ/
> spacing/radius/motion vào §1–§10 phía trên** — mục dưới đây từ nay chỉ còn
> vai trò **con trỏ + trạng thái**, không lặp lại số đã hợp nhất, tránh tái tạo
> hai nguồn lệch.

### PL12.1 Typography — đã gộp vào §2

Nội dung (Be Vietnam Pro có điều kiện, thang chữ dp, text-scale 100–200%) nay ở
**§2** phía trên. Không còn nội dung riêng ở đây.

### PL12.2 Token màu — đã gộp vào §1/§5

Bảng màu + tương phản đã đo (3 token từng "chỉnh WCAG" ở bản cũ: `--err`/
`--ok`/`--warn`) nay là giá trị chốt thẳng ở **§1.2**, caveat tương phản ở
**§5**. Không còn bảng "gốc vs đã chỉnh" riêng — giá trị trong §1/§5 ĐÃ là bản
chỉnh, không cần đối chiếu ngược bản gốc ruby D0 nữa (bản ruby D0 chỉ còn giá
trị lịch sử, xem khung cảnh báo đầu file).

### PL12.3 Spacing/radius/control — đã gộp vào §3

Hai thang bo góc (A/B) + hai thang bóng (A/B) + control/icon/toolbar/sidebar/
dialog nay ở **§3.1–§3.3**. Đây là lần đầu tiên tài liệu **đặt tên + chốt phạm
vi** cho 2 thang bo góc, thay vì để 3 con số (8/12/12/999 · 6/10/16 · 8/12/16/
999) trôi không giải thích.

### PL12.4 Phím tắt (UX12-019..024)

Registry đầy đủ (27 action: 9 hệ thống + 4 cửa sổ + 14 ứng dụng/app, mỗi action
có `action_id/scope/default_combo/priority/overridable/p_level`) nằm ở
`design/keyboard-shortcuts.json`. Đối chiếu thủ công: không có 2 action
scope=system nào trùng `default_combo` (9 action hệ thống đang bật, 1 action
`smartai_invoke` để `enabled:false` chờ audit xung đột IME). Ba xung đột tiềm
ẩn đã ghi ở `known_conflicts` trong file đó. Bộ phát hiện xung đột CI (UX12-019)
**chưa được dựng** — đối chiếu "không trùng" ở trên là một lần thủ công, không
phải gate CI.

### PL12.5 Hình nền có quyền (UX12-025..032)

`design/wallpaper-manifest.json` khai cấu trúc dữ liệu cho bộ sưu tập ảnh THẬT
"Việt Nam qua từng vùng đất" (mục tiêu 12–18 ảnh) — **hiện có 0 ảnh thật trong
manifest này**, cả 3 mục đều PLACEHOLDER với `rights_evidence: "chưa có"`.
**Lưu ý phân biệt (đã có cờ đỏ ở `docs/roadmap/NANG-CAP-NHU-CAU-NGUOI-DUNG.md`,
chưa đóng):** repo hiện có **25 thư mục** ở
`usr/share/wallpapers/NaMiOS-01..25` — đây là một lô hình nền **khác**, không
thuộc manifest ảnh-thật ở trên; nguồn gốc/quyền của 25 ảnh đó **chưa được đối
chiếu trong phạm vi wave này** (ngoài phạm vi token hình ảnh — xem roadmap để
theo dõi). Không mục nào trong `wallpaper-manifest.json` được phép đóng gói ISO
cho tới khi có bằng chứng cấp phép thật + hội đồng biên tập ký duyệt.

### PL12.6 Accessibility WCAG 2.2 AA

Mục tiêu đã nêu lại ở **§5**: tương phản, bàn phím, phóng chữ, giảm chuyển động
(**§10**). Test tự động + thủ công với screen reader và 200% text, lỗi P0 chặn
release — **chưa thực hiện**, cần desktop NaMiOS thật (`blocked-infra`, xem
`docs/backlog/UX12-backlog.md`).

### PL12.7 Quy tắc tiếng Việt (glossary + văn phong)

`design/glossary.vi.json` bổ sung 55 thuật ngữ (34 phổ thông + 21 chuyên ngành)
giải thích cho Help/tra cứu, **không thay đổi** bảng "Dùng/Không dùng" đã chốt ở
**§8**. Văn phong bổ sung: ngày giờ Việt Nam, không viết HOA toàn câu, tránh
tiếng Anh kỹ thuật khi có từ phổ thông, mã lỗi cố định cho đội kỹ thuật.
