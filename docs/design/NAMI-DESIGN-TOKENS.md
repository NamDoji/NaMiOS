# NaMi Design Tokens — v3 "Đông Sơn" semantic layer (HIG §5.1–5.2, §9)

> **Loại tài liệu:** đặc tả P1 (nền tảng) của `docs/design/hig/NaMi-Human-Interface-2026.md`.
> Suy ra lớp **SEMANTIC token** (token theo NGHĨA sử dụng) từ 6 mã AUTHORITATIVE PALETTE
> v3 Đông Sơn, cho **light / dark / high-contrast**, có **đo tương phản WCAG thật**.
> **Phạm vi file:** CHỈ viết tài liệu + `docs/design/nami-tokens.json`. KHÔNG sửa
> `brand.json`, `.colors`, theme, app, config. **`verified_on_host: NO`.** Không `git commit`/push.
> **Ngày:** 2026-11-11.

## 0. Quy ước đọc

- Mọi tỷ lệ tương phản **tính bằng công thức WCAG 2.x** (relative luminance), không ước lượng
  bằng mắt — script offline trong `/tmp/contrast.py`, công thức ghi ở `$meta.contrast_method`
  của `nami-tokens.json`. Số đã đối chiếu khớp với các giá trị đã có trong
  `usr/share/namios/docs/BRAND.md` và `usr/share/color-schemes/NaMiOS.colors`.
- "Pass" nghĩa **đạt ngưỡng WCAG**, KHÔNG nghĩa "đã hiển thị đúng trên desktop thật". Hiển thị
  thật chỉ xác nhận bằng boot KDE Plasma (`docs/releases/boot-evidence`) — chưa có.
- **Nguồn màu NHẬN DIỆN duy nhất** = `usr/share/namios-branding/logo/brand.json` (6 mã Đông Sơn).
  Màu **TRẠNG THÁI** (success/warning xanh-lá/cam) là lớp token CHỨC NĂNG, không thuộc brand.json
  (brand.json không có token xanh-lá) — đúng nguyên tắc đã ghi trong `.colors`/BRAND.md.

## 1. Nguồn: 6 mã AUTHORITATIVE PALETTE + sắc độ phụ trợ

Từ `brand.json` v3.0 (mục `colors`, sau khi hợp nhất 9 khoá cũ về 3 mã) + 2 mã nền
(ivory/white) nêu trong HIG §5.1:

| Vai trò | Token | Hex | RGB |
|---|---|---|---|
| Nền tối/chính · chữ trên nền sáng | `navy` | `#092D4F` | 9,45,79 |
| **Signature accent** (selection/focus/highlight; primary trên nền tối) | `gold` | `#DEA93E` | 222,169,62 |
| Action/attention/destructive (nền nút/icon/chữ lớn) | `vermilion` | `#D64C3E` | 214,76,62 |
| Secondary/support accent (link/icon) | `teal` | `#278F8D` | 39,143,141 |
| Nền sáng/nội dung | `ivory` | `#FFF9EF` | 255,249,239 |
| Surface nổi (card/dialog) light | `white` | `#FFFFFF` | 255,255,255 |

6 mã gốc **không đủ** để vừa làm "khối màu nổi bật" vừa làm "chữ đọc được" ở mọi nền (vd
vermilion trên trắng chỉ 4.23:1 < 4.5). Vì vậy — theo đúng tiền lệ đã có trong BRAND.md —
suy ra **sắc độ phụ trợ** bằng cách đổi **lightness (HSL)** của đúng 1 mã gốc, giữ hue/sat,
rồi **đo lại** tới khi đạt AA. Các mã này CHỈ sống trong lớp token/`.colors`, KHÔNG đưa vào
brand.json:

| Token | Hex | Suy từ | Dùng khi | Đo được |
|---|---|---|---|---|
| `vermilion-deep` | `#A02E22` | vermilion L54→38 | chữ đỏ (lỗi) trên nền SÁNG | 6.89:1/ivory · 7.22:1/white |
| `vermilion-light`| `#E48A81` | vermilion L54→70 | chữ đỏ trên nền TỐI (navy) | 5.50:1/navy |
| `gold-deep` | `#8B6518` | gold L56→32 | chữ vàng / **focus-ring** trên nền SÁNG | 5.05:1/ivory · 5.29:1/white |
| `teal-deep` | `#1F706F` | teal L36→28 | link/chữ teal trên nền SÁNG | 5.56:1/ivory |
| `teal-light`| `#5FD3D1` | teal L36→60 | link/chữ teal trên nền TỐI | 7.82:1/navy |
| `navy-subtle`| `#0A3257` | navy L17→19 | hàng-chẵn/panel sau trên nền TỐI | nền |
| `navy-card` | `#0B3965` | navy L17→22 | **surface-raised** trên nền TỐI | nền |
| `ivory-subtle`| `#FFF2DB` | ivory L97→93 | chip/ô nền chìm trên nền SÁNG | nền |

## 2. Semantic tokens — bảng chính thức (3 chế độ)

Danh sách token BẮT BUỘC theo yêu cầu HIG §5.1: `surface`, `surface-raised`, `text-primary`,
`text-secondary`, `action-primary`, `action-primary-text`, `success`, `warning`, `danger`,
`focus-ring`, `border` (+ `accent`, `link`, `surface-sunken`, `danger-fill`, `border-subtle`
để đủ dùng).

### 2.1. Light (nền ngà/trắng, chữ navy)

| Token | Hex | Ghi chú |
|---|---|---|
| `surface` | `#FFF9EF` ivory | nền desktop/trang/dialog |
| `surface-raised` | `#FFFFFF` white | card/panel/dialog nổi |
| `surface-sunken` | `#FFF2DB` ivory-subtle | chip/hàng chẵn/ô nhập nền |
| `text-primary` | `#092D4F` navy | — |
| `text-secondary` | `#52646B` slate | metadata/phụ |
| `action-primary` | `#092D4F` navy | **nền nút chính** |
| `action-primary-text` | `#FFF9EF` ivory | chữ trên nút chính |
| `accent` / `accent-text` | `#DEA93E` gold / `#092D4F` navy | selection/highlight **luôn gold+chữ navy** |
| `link` | `#1F706F` teal-deep | — |
| `success` | `#127A52` | xanh lá "đã xong" |
| `warning` | `#965300` | cam "chú ý/một phần" |
| `danger` | `#A02E22` vermilion-deep | chữ/icon/viền lỗi |
| `danger-fill` | `#D64C3E` vermilion | nền nút Xoá (+ chữ trắng, chỉ chữ LỚN) |
| `focus-ring` | `#8B6518` gold-deep | ≥2px |
| `border` | `#51708A` | viền mang nghĩa (≥3:1) |
| `border-subtle` | `#E3DAC8` | chia nhẹ — CHỈ trang trí (<3:1), phải kèm fill/bóng |

### 2.2. Dark (nền navy, chữ ngà)

| Token | Hex | Ghi chú |
|---|---|---|
| `surface` | `#092D4F` navy | — |
| `surface-raised` | `#0B3965` navy-card | — |
| `surface-sunken` | `#0A3257` navy-subtle | — |
| `text-primary` | `#FFF9EF` ivory | — |
| `text-secondary` | `#C9D3D6` slate-light | — |
| `action-primary` | `#DEA93E` gold | **nền nút chính** (navy sẽ "tàng hình" trên nền navy) |
| `action-primary-text` | `#092D4F` navy | — |
| `accent` / `accent-text` | `#DEA93E` / `#092D4F` | — |
| `link` | `#5FD3D1` teal-light | — |
| `success` | `#59C798` | — |
| `warning` | `#F6BB68` | — |
| `danger` | `#E48A81` vermilion-light | — |
| `danger-fill` | `#D64C3E` vermilion | + chữ trắng |
| `focus-ring` | `#DEA93E` gold | ≥2px |
| `border` | `#5A82AD` | ≥3:1 trên navy |
| `border-subtle` | `#1E4A72` | trang trí |

### 2.3. High-contrast (nền đen, viền trắng, không blur)

| Token | Hex | Token | Hex |
|---|---|---|---|
| `surface` | `#000000` | `success` | `#64E6A6` |
| `surface-raised` | `#0D0D0D` | `warning` | `#FFC24B` |
| `text-primary` | `#FFFFFF` | `danger` | `#FF9C8E` |
| `text-secondary` | `#E6E6E6` | `link` | `#6FE0DE` |
| `action-primary` / text | `#FFD464` / `#000000` | `focus-ring` | `#FFD464` (≥3px) |
| `accent` / text | `#FFD464` / `#000000` | `border` | `#FFFFFF` |

## 3. Quyết định thiết kế quan trọng (có cơ sở số, không cảm tính)

1. **Vì sao `action-primary` = navy ở LIGHT nhưng gold ở DARK?**
   Gold là signature accent, nhưng **gold trên ivory chỉ 2.04:1** → *silhouette* của nút gold
   trên nền ngà KHÔNG đạt 3:1 (WCAG SC 1.4.11, viền/khối UI) → nút "biến mất" khỏi nền. Navy
   trên ivory = 13.37:1 → nút navy rõ tuyệt đối. Ở DARK thì ngược lại: navy trên navy tàng
   hình, gold trên navy = 6.57:1 → gold là lựa chọn đúng. Đây là lý do mode-dependent, đã đo.
   Gold vẫn giữ vai **accent selection/focus** ở cả hai chế độ (đúng vai trong KDE `.colors`).

2. **Vì sao `focus-ring` = gold-deep ở LIGHT, gold ở DARK?** Cùng lý do (1): gold gốc 2.04:1
   trên ivory < 3:1 → focus-ring phải dùng gold-deep (5.05:1). Trên navy, gold gốc 6.57:1 đủ.

3. **Vì sao `danger` khác `danger-fill`?** Chữ/icon lỗi cần ≥4.5:1 → `danger` = vermilion-deep
   (light) / vermilion-light (dark). Nền nút "Xoá" dùng vermilion gốc + chữ trắng = 4.23:1,
   chỉ hợp lệ cho **chữ nút LỚN/đậm** (ngưỡng 3:1), KHÔNG cho chữ thường nhỏ.

4. **`border-subtle` KHÔNG đạt 3:1** (có chủ đích, chỉ trang trí) → ranh giới control bắt buộc
   có thêm **fill/bóng/focus-ring**, không được chỉ dựa vào viền mảnh (HIG §6 "chất liệu").

## 4. Bảng tương phản đã đo (trích — đầy đủ 36 cặp trong `nami-tokens.json`)

```
LIGHT
  PASS 13.37  text-primary navy / surface ivory          (>=4.5)
  PASS  5.91  text-secondary slate / surface ivory        (>=4.5)
  PASS 13.37  action-primary-text ivory / action navy     (>=4.5)
  PASS  6.57  accent-text navy / gold selection           (>=4.5)
  FAIL  2.04  gold silhouette / ivory   <-- CHỦ ĐÍCH: không dùng gold làm nền nút trên light
  PASS  5.05  focus-ring gold-deep / ivory                (>=3 UI)
  PASS  4.97  border / ivory                              (>=3 UI)
  PASS  6.89  danger vermilion-deep / ivory               (>=4.5)
  PASS  5.10/5.67  success/warning / ivory                (>=4.5)
DARK
  PASS 13.37  text-primary ivory / navy                   (>=4.5)
  PASS  6.57  action-primary-text navy / gold             (>=4.5)
  PASS  5.50  danger vermilion-light / navy               (>=4.5)
  PASS  3.49  border #5A82AD / navy                       (>=3 UI)
  PASS  6.70/8.15  success/warning / navy                 (>=4.5)
HIGH-CONTRAST (nhắm >=7 chữ / >=4.5 UI)
  PASS 21.00  white / black        PASS 14.85  gold-bright #FFD464 / black
  PASS 13.41  success  PASS 13.07  warning  PASS 10.40  danger  PASS 13.39  link
```

**Tổng kết: 35/36 cặp PASS. Cặp FAIL duy nhất (gold/ivory 2.04:1) là CHỦ ĐÍCH** — nó chính là
bằng chứng số để KHÔNG dùng gold làm nền nút/silhouette trên nền sáng; gold ở light chỉ dùng
làm **nền selection có chữ navy** (6.57:1) hoặc chuyển sang **gold-deep** khi cần làm chữ/viền.

## 5. Thang phi-màu (space / radius / type / motion)

- **space (dp):** 4, 8, 12, 16, 24, 32 · nhịp 8 · panel padding 16. Không dùng giá trị ngoài thang.
- **radius (dp):** sm 8 (chip/nút nhỏ) · md 12 (button/input/select) · lg 16 (card/panel/dialog) ·
  pill 999. Không bo mọi khối giống nhau.
- **type (dp @100%):** hero 32/40 · h1 28/36 · h2 22/30 · h3 18/26 · body 16/24 · body-sm 15/22 ·
  label 14/20 · caption 12/18 (chỉ chú thích phụ, KHÔNG dùng cho lỗi cần hành động) · code 14/20
  mono. Tối đa 4 cấp heading/màn. line-height 1.4–1.6. Reflow 200% không cắt.
- **font:** Noto Sans (UI) + DejaVu/Liberation fallback, Noto Sans Mono (code). Đủ dấu tiếng Việt,
  cấp phép phân phối (SIL OFL / Bitstream Vera). Gói thực: `fonts-noto-core`, `fonts-noto-ui-core`,
  `fonts-noto-mono`, `fonts-dejavu-core`, `fonts-liberation2` (xác nhận trong `0300-fonts.list.chroot`).
- **control (dp):** desktop target ≥32×32 · touch ≥44×44 · height compact/default/large = 36/40/44.
- **icon (dp):** 16/24/32, stroke 1.9, symbolic currentColor; brand mark đầy đủ chỉ ≥48px.
- **focus:** ring ≥2px (≥3px ở high-contrast), offset 2dp; luôn thấy khi dùng bàn phím, KHÔNG chỉ đổi nền.
- **motion (ms):** fast 120 · base 180 · slow 240 · easing `cubic-bezier(0.2,0,0,1)`. Chỉ diễn tả
  chuyển trạng thái. `prefers-reduced-motion` → tắt animation + blur tức thì. Có chế độ giảm trong suốt
  (máy yếu/không GPU — compositing mặc định TẮT theo `kwinrc`).
- **breakpoints:** min 1024×600 (theo nền tảng)/1366×768 thực dụng; test 1366/1920/2560 × 100/125/150/200%.

## 6. Cách dùng / nối xuống (cho các wave sau — P2+)

| Consumer | File | Việc nối (P2+) |
|---|---|---|
| KColorScheme app | `usr/share/color-schemes/NaMiOS.colors` | đã dùng các mã v3 này; đồng bộ `make-colorscheme.py` để sinh LẠI từ token này (tránh sửa tay bị ghi đè) |
| Plasma desktoptheme | `usr/share/plasma/desktoptheme/NaMiOS-Sen/colors` | như trên |
| QML palette app | `usr/share/namios/qml/SenVietPalette.qml` | map 1-1 sang semantic token |
| PySide6 apps | `opt/namios/*/branding.py` (`_FALLBACK_COLORS`) | cập nhật hằng số dự phòng theo v3; lý tưởng đọc từ token này |
| Prototype/web | `branding/design-system/components.css` + `tokens.json` | hợp nhất 3 nguồn token (xem §7) |

## 7. Nợ kỹ thuật: hợp nhất nguồn token (bắt buộc giải quyết trước P2)

Repo hiện có **3 bộ số token** tự xưng nguồn sự thật — PHẢI gộp về 1:

1. `design/tokens.json` — PL12 ruby `#a21f46`/navy `#0a1322` → **LỖI THỜI**, xóa/đóng băng.
2. `branding/design-system/tokens.json` — "Sen Việt" teal/ivory `#C93643`/`#006E72` → **đã đo WCAG
   kỹ** nhưng palette khác v3 Đông Sơn.
3. **Bộ này** (`docs/design/nami-tokens.json`) — bám đúng v3 Đông Sơn đang chạy trong
   `.colors`/`brand.json`.

Đề xuất: lấy **(3)** làm nguồn ngữ nghĩa, giữ phương pháp đo + cấu trúc máy-đọc của **(2)**, bỏ
**(1)**. Việc này là *điều kiện* để P1 "nền tảng" thực sự thống nhất trước khi mở sang shell/app.

## 8. Giới hạn / chưa làm

- `verified_on_host: NO` — chưa boot KDE Plasma thật để xem màu hiển thị (đặc biệt
  `[Colors:Selection]` nền gold + chữ navy).
- Chưa sinh biến thể **high-contrast** thành file KColorScheme/desktoptheme thật (mới là token);
  KDE có cơ chế color-scheme riêng cho high-contrast — wave P2 phải tạo `.colors` tương ứng.
- Chưa test người dùng (người lớn tuổi/screen reader) — đó là P1 "demo bàn phím + screen reader"
  và P4, cần phần cứng thật.
