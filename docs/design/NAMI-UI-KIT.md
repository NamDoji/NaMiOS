# NaMi UI Kit — đặc tả thành phần (HIG §6 + §7.2)

> **Loại tài liệu:** đặc tả P1 — thư viện thành phần + trạng thái bắt buộc + mẫu lỗi 5 phần,
> ánh xạ sang **PySide6/Qt 6 / Kirigami** và đối chiếu "app đã có gì / cần gì".
> **Phạm vi file:** chỉ đặc tả. KHÔNG sửa app. `verified_on_host: NO`. Không `git commit`/push.
> **Ngày:** 2026-11-11. Token tham chiếu: `docs/design/nami-tokens.json`.

## 0. Nguyên tắc chung (HIG §6)

- Mọi app hệ thống dùng **cùng component + cùng token**. Mỗi thành phần có API cho: **nhãn tiếng
  Việt, tooltip, accessible name, state, test**.
- Ưu tiên **native toolkit** (Qt Widgets/Quick) để kế thừa **semantic accessibility** sẵn có
  (QAccessible) thay vì tự vẽ. Tự vẽ → phải tự gắn `setAccessibleName/Description`, role, state.
- **Chất liệu:** blur/translucency chỉ ở lớp điều hướng khi GPU + tương phản cho phép; nền nội
  dung đặc. Khi tắt hiệu ứng → nền đặc có thứ bậc (token `surface`/`surface-raised`/`surface-sunken`).
  **Mặc định compositing TẮT** (máy yếu/VM) → KHÔNG được phụ thuộc blur để phân lớp.

## 1. Bảng thành phần + trạng thái + ánh xạ toolkit

| Thành phần | Trạng thái tối thiểu (HIG §6) | Điều kiện đặc biệt | Toolkit (PySide6/Qt/Kirigami) | App đã có / cần |
|---|---|---|---|---|
| **Button** chính/phụ/nguy hiểm | idle, hover, focus, pressed, busy, disabled | nút nguy hiểm câu rõ hành động; **busy không gửi lặp** | `QPushButton` + QSS theo token (`action-primary`/`danger-fill`); busy = `setEnabled(False)`+spinner | **CÓ** QSS brand trong `assistant/branding.py build_stylesheet`; **CẦN** chuẩn hóa 1 widget dùng chung + chống double-submit |
| **Text field / search / password** | empty, focus, valid, error, readonly, disabled | lỗi **ngay cạnh trường**; mật khẩu có xem/ẩn | `QLineEdit` (`setEchoMode`, action xem/ẩn); error = label dưới trường + `setAccessibleDescription` | **CÓ** ô nhập (assistant `input.placeholder`); **CẦN** pattern error-cạnh-trường + toggle mật khẩu dùng chung |
| **Checkbox / radio / switch** | off/on/mixed, focus, disabled | **không** dùng switch cho hành động cần xác nhận lâu | `QCheckBox`/`QRadioButton`/Kirigami `Switch` | **CẦN** component chung |
| **Combobox / list / autocomplete** | mở/đóng, chọn, không kết quả, lỗi | gõ lọc; **mũi tên/Enter/Esc** chạy | `QComboBox(editable)`/`QCompleter` | **CẦN** |
| **Menu / context menu** | mở/đóng, disabled, separator | tên lệnh + phím tắt nhất quán; **không ẩn lệnh chỉ vì không hover** | `QMenu` (+ `QAction` shortcut) | **CÓ** (assistant attach menu: "Dán ảnh…", "Chọn tệp…"); **CẦN** bảng phím tắt nhất quán |
| **Table / list / tree** | chọn, multi-select, sort, filter, empty, loading | bàn phím + cột co giãn; **không mất vị trí khi refresh** | `QTableView`/`QTreeView` + model | **CÓ** (dichvu danh bạ); **CẦN** empty/loading state chuẩn |
| **Tabs / sidebar / breadcrumb** | active, focus, collapsed | đổi kích thước cửa sổ **không mất tính năng** (sidebar→tab ngang khi hẹp) | `QTabWidget`/Kirigami `PageRow` | **CẦN** responsive collapse (breakpoint 1366) |
| **Dialog / sheet / toast** | info, success, warning, error | nút hành động rõ; **toast KHÔNG là nơi duy nhất báo lỗi** | `QDialog`/`QMessageBox` (thay icon/nhãn theo token); toast = Kirigami `InlineMessage`/passive | **CẦN** dialog chuẩn + lịch sử lỗi trong trung tâm thông báo |
| **Progress** | determinate, indeterminate, paused, failed | biết % → hiện **% thật** + tệp/bước đang làm | `QProgressBar` (`setRange(0,0)` cho indeterminate) | **CẦN** nối % THẬT (PackageKit/Calamares), không giả |
| **File picker / permission** | chọn/không chọn, preview, lỗi | phân biệt **đọc / ghi / gửi mạng**; cho hủy | `QFileDialog` + lớp quyền `namios_security.safe_path` | **CÓ** (assistant chọn ảnh); **CẦN** nhãn phân biệt quyền |

## 2. Button — đặc tả màu theo token (3 loại × 3 chế độ)

| Loại | Light | Dark | High-contrast |
|---|---|---|---|
| **Chính (primary)** | nền `action-primary` navy `#092D4F` + chữ ivory | nền gold `#DEA93E` + chữ navy | nền `#FFD464` + chữ đen |
| **Phụ (secondary)** | nền `surface-raised` + viền `border` `#51708A` + chữ navy | nền `surface-raised` navy-card + viền `#5A82AD` + chữ ivory | nền đen + viền trắng + chữ trắng |
| **Nguy hiểm (danger)** | nền `danger-fill` vermilion `#D64C3E` + chữ trắng (chỉ chữ **LỚN/đậm**, 4.23:1) | như light + chữ trắng | nền `#FF9C8E` + chữ đen |

- **focus:** ring `focus-ring` (gold-deep light / gold dark / #FFD464 HC) ≥2px (≥3px HC), offset 2dp.
- **busy:** vô hiệu hóa nút + spinner trong-nút; **chống double-submit** (HIG: "busy không gây gửi lặp").
- Nút nguy hiểm (Xoá/Format) **KHÔNG là nút mặc định** (`Enter`); đặt xa nút an toàn.

## 3. Mẫu thông báo lỗi 5 phần (HIG §7.2) — BẮT BUỘC

Mỗi lỗi phải có đủ: **(1)** điều gì không thành công · **(2)** nguyên nhân xác định được HOẶC
giới hạn chẩn đoán (tách "có thể do" với "đã phát hiện") · **(3)** việc người dùng có thể làm ·
**(4)** nút Thử lại / Trợ giúp · **(5)** mã lỗi **sao chép được**.

Quy tắc: không suy đoán nguyên nhân thành sự thật; không bắt chạy lệnh terminal nếu UI tự xử lý
an toàn được; **lỗi cần hành động KHÔNG tự biến mất**, có lịch sử trong trung tâm thông báo; AI
không thay thế thông báo nguồn từ hệ thống.

**Mẫu dùng lại (template):**
```
(1) [Tiêu đề] Không thể {hành động} "{đối tượng}".
(2) [Nguyên nhân] Đã phát hiện: {fact}.  — hoặc —  Có thể do: {hypothesis}.
(3) [Cách xử lý] Bạn có thể: {bước 1} / {bước 2}.
(4) [Nút]  ⟨Thử lại⟩  ⟨Chẩn đoán / Nhờ Trợ lý⟩  ⟨Trợ giúp⟩
(5) [Mã lỗi]  {CODE}  (nút Sao chép)   correlation_id: {id}
```

Ví dụ chuẩn (HIG §7.2): *"Không thể kết nối Wi-Fi 'LopHoc'. Mật khẩu có thể chưa đúng. Nhập lại
mật khẩu hoặc kiểm tra bộ phát."* — nút **Nhập lại**, **Chẩn đoán**.

### 3.1. App ĐÃ theo mẫu này (bằng chứng) + điểm cần bổ sung

Từ `opt/namios/namios_assistant-src/_i18n.py` — **đã có** cấu trúc gần đạt:
- phần (2) nguyên nhân: `assistant.engine.offline.cause_label` = "**Nguyên nhân có khả năng:** {cause}"
  → đã tách "có khả năng" (hypothesis) đúng tinh thần §7.2.
- phần (3) bước xử lý: `steps_label` "**Các bước thử:**", `no_match` liệt kê (1)(2)(3) rõ.
- an toàn/hoàn tác: `rollback_label` "**Hoàn tác/an toàn:** {rollback}".
- trung thực nguồn: ghi rõ *"Đây KHÔNG phải câu trả lời từ AI — chỉ là KB ngoại tuyến"* (AI không
  giả làm nguồn hệ thống — khớp HIG §7.2 câu cuối).

**CẦN bổ sung để đủ 5 phần:**
- (5) **mã lỗi sao chép được + correlation_id** hiển thị trong UI lỗi (hiện `error.engine_unexpected`
  nói "đã ghi lại" nhưng **không hiện mã cho người dùng copy**). `namios_core/errors.py` +
  `envelope.py` đã có cấu trúc mã lỗi → nối ra UI.
- (4) nút **Thử lại / Trợ giúp** tường minh trong mọi dialog lỗi (không chỉ ô chat).
- Lịch sử lỗi: lỗi cần hành động phải vào **trung tâm thông báo**, không mất đi.

## 4. Trạng thái truyền đạt KHÔNG chỉ bằng màu (HIG §9)

Mọi trạng thái (thành công/cảnh báo/lỗi/chưa kiểm tra/bị chặn) = **màu token + CHỮ + ICON/HÌNH**.
Ví dụ: success = `#127A52`/`#59C798` + icon ✓ + chữ "Đã xong"; danger + icon ⚠ + chữ. Lý do:
screen reader + người mù màu + high-contrast. Icon có `accessibleName`.

## 5. Accessibility bắt buộc cho mọi component (HIG §9)

- Toàn bộ thao tác chính **bằng bàn phím**; `Tab` theo mắt đọc; `Esc` đóng khi an toàn; `Enter` =
  nút mặc định (không phải nút nguy hiểm). Không kẹt focus.
- Focus **nhìn rõ** (ring token ≥2px). Screen reader đọc **tên + vai trò + trạng thái + lỗi**
  (Qt: `QAccessible`; QML: `Accessible` attached).
- Hỗ trợ **125/150/200% scaling**, cỡ chữ lớn, high-contrast, reduce transparency, reduce motion.
  Reflow tới 200% không cắt nút/nội dung (WCAG 2.2 SC 1.4.4).
- Vùng bấm **desktop ≥32×32dp**, cảm ứng **≥44×44dp**.

## 6. Mức phủ của toolkit (trung thực)

| Khả năng HIG yêu cầu | Qt/PySide6/Kirigami đáp ứng? |
|---|---|
| Semantic role/name/state | CÓ — QAccessible (Widgets) / Accessible (QML) |
| Focus ring tùy biến | CÓ — QSS `:focus` / `QStyle`; **cần** đảm bảo ≥2px, không bị theme nuốt |
| Reduce motion / transparency | CÓ ở cấp app (đọc cờ) + KWin compositing off; **cần** app tự tôn trọng cờ |
| High-contrast scheme | CÓ cơ chế KColorScheme, **nhưng CHƯA có file HC thật** (mới là token — P2) |
| Announce trạng thái (live region) | **HẠN CHẾ** — Qt announce phụ thuộc platform/AT-SPI; phải boot-test với Orca |
| Translucency/blur | CÓ (KWin) nhưng **mặc định tắt** — không phụ thuộc |

## 7. Việc CẦN (giao P1→P2)

1. Tạo **1 thư viện widget dùng chung** (Button/Field/Dialog/Toast/Progress) đọc `nami-tokens.json`
   thay vì mỗi app tự QSS (hiện `assistant/branding.py` là riêng lẻ).
2. Nối **% tiến trình THẬT** (PackageKit/Calamares) vào Progress — không giả.
3. Hoàn thiện **mẫu lỗi 5 phần** (thêm mã lỗi copy + correlation_id + nút Thử lại/Trợ giúp + lịch sử).
4. Sinh **KColorScheme high-contrast** thật từ token (P2).
5. **Boot-test** screen reader (Orca) + bàn phím + focus ring — CANNOT-VERIFY-WITHOUT-BOOT-TEST.
