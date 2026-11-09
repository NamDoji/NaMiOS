# ADR 0016 — Tích hợp Design System “Sen Việt” vào toolkit thật (KDE Plasma 6 / Qt6 / QML / Kirigami)

- **Trạng thái:** proposed · **Mức thực thi:** `specified` (có token + preview web chạy được ở dev; **chưa** nối vào desktop KDE thật → chưa `partial`, chưa `completed`).
- **Ngày:** 09/11/2026
- **Năng lực:** `docs/brand-uiux-v1/04_PROMPT_CLAUDE_CODE.md` — **BRANCH A (Design system)**; spec `docs/brand-uiux-v1/03_NaMiOS_Brand_UIUX_Design_System.md` §2, §7.1, §7.3.
- **Liên quan:** ADR 0002 (nền Debian 13 trixie), ADR 0003 (desktop + phiên đồ hoạ), ADR 0011 (giao diện quen thuộc + ranh giới IP — không sao chép Windows/Apple), PL12 (`design/tokens.json`, `docs/design/DESIGN-SYSTEM.md`).
- **Tài sản tạo trong ADR này:**
  - `branding/design-system/tokens.json` — nguồn sự thật token (màu đã **đo** WCAG, typography, spacing, radius, control, focus, motion, breakpoints).
  - `branding/design-system/components.css` — biến CSS sinh từ token + 12 component tự vẽ.
  - `branding/design-system/components-preview.html` — trang preview (Storybook-equivalent), sáng/tối, focus, reduced-motion, nhãn tiếng Việt.
  - `docs/brand-uiux-v1/INVENTORY-BRANCH0.md` — kiểm kê BRANCH 0.

## Bối cảnh

Toolkit thật của NaMiOS **không phải web**. Theo kiểm kê BRANCH 0, desktop là **KDE Plasma 6 trên Qt6**, giao diện viết bằng **QML**; bằng chứng là hai plasmoid QML đã có trong repo: `org.namios.smartai` và `org.namios.workgroups` (`distro/live-build/config/includes.chroot/usr/share/plasma/plasmoids/*/contents/ui/main.qml`). App desktop KDE dùng **Kirigami** (framework UI của KDE trên Qt Quick Controls 2) + **Breeze** (style + màu qua file `.colors`).

Vậy có một **khoảng cách** phải nêu trung thực: BRANCH A sinh ra **token (JSON)** + **preview (HTML/CSS)**. HTML/CSS **không chạy** trên desktop Plasma. Preview chỉ để **duyệt thiết kế, đo tương phản, chốt hành vi trạng thái** trước khi hiện thực bằng QML/Kirigami. ADR này quyết định **cách ánh xạ** token + component sang toolkit thật, và ghi rõ **phần nào còn phải code QML + test máy thật**.

Lý do chọn “token-trước, preview web, QML-sau” thay vì code thẳng QML:
1. Token JSON là nguồn trung lập, nạp được cho **cả** CSS preview lẫn QML runtime (qua một bước sinh), tránh hardcode màu/font trong từng app (yêu cầu spec 03 §7.1).
2. Preview web mở ở mọi máy, không cần build ISO/boot Plasma → vòng duyệt thiết kế + **đo WCAG** nhanh, trung thực, trước khi tốn công QML.
3. Màu nhấn đã đồng bộ sẵn với `usr/share/color-schemes/NaMiOS.colors` (đỏ son #C93643 + đỏ đài #92212E) → đường nối sang Breeze/Plasma có cơ sở.

## Quyết định

1. **`branding/design-system/tokens.json` là nguồn sự thật** cho nhận diện “Sen Việt v1.0” (nền ngà ấm, đỏ son, vàng, mực). Mọi hiện thực (CSS preview, QML runtime, file `.colors` Breeze) phải **đọc/sinh từ** file này, không tự chế màu.
2. **Ánh xạ sang toolkit thật theo 2 đường:**
   - **Màu/typography/spacing → Breeze + Kirigami Theme.** Token màu → sinh `color-schemes/NaMiOS.colors` (đã có, cần đồng bộ giá trị) + `Kirigami.Theme` để app Qt/QML lấy màu nhất quán. Font Noto Sans + fallback DejaVu (đủ dấu) đặt qua fontconfig, không hardcode trong app.
   - **Component → ưu tiên control Qt/Kirigami sẵn có; chỉ viết QML tùy biến khi cần.** Xem bảng dưới.
3. **Không sao chép asset giao diện Windows/Apple** (ADR 0011). Component là nét tự vẽ.

### Bảng ánh xạ 12 component → Qt/Kirigami

| Component (preview) | Ánh xạ toolkit thật | Loại việc |
|---|---|---|
| **Button** | `QtQuick.Controls.Button` / `Kirigami.Action` + Breeze; chỉ cần đổi màu theo token (primary=teal, brand=đỏ son, danger=error) | **mappable** — tùy biến nhẹ (màu + bo góc) |
| **Field** (ô nhập) | `Controls.TextField` / `Kirigami.FormLayout` + `Kirigami.InlineMessage` cho lỗi | **mappable** — tùy biến nhẹ |
| **Select** | `Controls.ComboBox` | **mappable** — tùy biến nhẹ |
| **Checkbox** | `Controls.CheckBox` (+ `RadioButton`, `Switch`) | **mappable** |
| **Dialog** | `Kirigami.Dialog` / `Kirigami.PromptDialog` / `Controls.Dialog` | **mappable** |
| **Toast** | `Kirigami.InlineMessage` (trong app) **hoặc** thông báo desktop chuẩn `org.freedesktop.Notifications` (spec 03 nguồn [6]) | **mappable** — chọn kênh theo ngữ cảnh |
| **Progress** | `Controls.ProgressBar` (xác định) + `BusyIndicator` (không xác định) | **mappable** |
| **DeviceCard** | `Kirigami.Card` / `Kirigami.AbstractCard` + badge tự vẽ | **mappable** — cần layout card + badge trạng thái |
| **ConnectionStepper** | **Chưa có control chuẩn** → **custom QML** (dãy bước + đường nối + trạng thái done/active/failed). Có thể dựng trên `ListView` + delegate | **custom QML** |
| **ErrorCard** | `Kirigami.Card` + `Kirigami.InlineMessage`; nhưng phần “mã lỗi + correlation_id + Nhờ SmartAI + lịch sử” là nghiệp vụ NaMiOS → **custom QML** bọc quanh | **custom QML** (dùng card làm nền) |
| **AIPlanCard** | **custom QML** — đặc thù SmartAI (tối đa 3 bước, bằng chứng + mức chắc chắn + hoàn tác). Tái dùng/thống nhất với plasmoid `org.namios.smartai` đã có | **custom QML** |

**Tóm tắt:** 8/12 component **mappable** sang control Qt/Kirigami có sẵn (chỉ tùy biến màu/bo góc theo token). 3 component (**ConnectionStepper, ErrorCard, AIPlanCard**) + badge của **DeviceCard** cần **viết QML tùy biến** vì không có control chuẩn tương đương và/hoặc mang nghiệp vụ NaMiOS (mã lỗi, SmartAI).

## Khả năng tiếp cận (accessibility) — ràng buộc bắt buộc khi hiện thực QML

- **Tương phản:** token màu đã **đo** bằng công thức WCAG 2.2 (bảng `color.contrast_table` trong tokens.json). Chữ thường ≥ 4.5:1, UI/chữ lớn ≥ 3:1. Lưu ý đã mã hoá: đỏ son làm **chữ** chỉ ~4.59:1 (ngà) → chữ đỏ dùng **đỏ đài #92212E**; ở nền tối đỏ #E56365 **không đạt** chữ thường → chỉ nhấn/chữ lớn/icon; viền mảnh **không** đạt 3:1 → ranh giới control phải có thêm fill/bóng/focus-ring.
- **Phóng 200%:** layout phải reflow, không raster chữ/nút (WCAG 2.2 SC 1.4.4). Test 100/125/150/200%.
- **Tiêu điểm bàn phím:** focus ring **≥2px** bằng `color.<mode>.focus.ring`, không chỉ đổi màu nền; `Kirigami`/Qt có `activeFocus` + `focusPolicy` — phải bật và style rõ.
- **Giảm chuyển động:** token `motion.reduced_motion.flag=true`; QML phải đọc trạng thái “giảm hiệu ứng” của hệ (Plasma animation speed / `Kirigami.Units` khi reduce) để tắt animation + blur tức thì.
- **Màn tối thiểu 1366×768:** sidebar không chiếm hết nội dung; dialog 400–560dp.
- **Icon có nhãn, screen reader:** `Accessible.name/description` cho mọi control; icon kèm text (spec 03 §2).

## Trung thực về trạng thái (bắt buộc ghi)

- Đây là **lớp design-system + preview**, **CHƯA** nối vào desktop KDE sống. HTML/CSS **không** chạy trên Plasma; là công cụ duyệt thiết kế.
- Màu đã **đo** WCAG (script Python, một lần), **nhưng** `verified_on_hw: NO` — **chưa** xác nhận hiển thị trên **màn hình/desktop thật** (gamma/panel khác với sRGB lý thuyết), **chưa** test người dùng, **chưa** test screen reader thật.
- `color-schemes/NaMiOS.colors` đã có nhưng **giá trị chưa được sinh tự động** từ token này → cần bước đồng bộ, nếu không là 2 nguồn lệch.
- Tồn tại **2 bộ token** (PL12 navy `design/tokens.json` vs Sen Việt ngà `branding/design-system/tokens.json`) → phải hợp nhất ở lần cập nhật `docs/design/DESIGN-SYSTEM.md` kế tiếp (đã ghi trong `$meta.supersedes_note`).

## Hệ quả

- **Tích cực:** một nguồn màu/typography trung lập; preview duyệt nhanh + đo WCAG trước khi tốn công QML; 8/12 component nối thẳng control Qt/Kirigami; màu đã đồng bộ ý tưởng với Breeze `.colors`.
- **Chi phí/nợ:** cần viết (a) bước **sinh** `NaMiOS.colors` + `Kirigami.Theme` + fontconfig từ `tokens.json`; (b) **custom QML** cho 3 component nghiệp vụ; (c) hợp nhất 2 bộ token. Preview CSS và QML là **hai** hiện thực — rủi ro trôi lệch nếu không sinh từ cùng token.

## Bước tiếp theo (chưa làm — ngoài phạm vi lượt này)

1. Viết script sinh: `tokens.json` → `color-schemes/NaMiOS.colors` + bảng màu `Kirigami.Theme` + `fontconfig` (một nguồn, nhiều đích).
2. Hiện thực 12 component bằng QML/Kirigami theo bảng ánh xạ; thống nhất AIPlanCard với plasmoid `org.namios.smartai` sẵn có.
3. Build ISO + boot **máy thật**; test visual 1366×768 / 1920×1080 / 2560×1440 @ 100/125/150/200%; test bàn phím + screen reader + giảm chuyển động (spec 03 §7.6).
4. Hợp nhất `design/tokens.json` (PL12) và `branding/design-system/tokens.json` (Sen Việt) thành một nguồn.
