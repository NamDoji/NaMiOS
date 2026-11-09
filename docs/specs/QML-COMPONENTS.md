# NaMiOS — 3 component QML tuỳ biến (ErrorCard · ConnectionStepper · AIPlanCard)

**Trạng thái:** `specified` (mã QML có thật trong repo; **chưa** dựng/boot trên
KDE Plasma 6 / Qt6 thật → chưa `partial`, chưa `completed`). Theo quy ước
`docs/STATUS-U13-KIEM-KE.md`: *không có artifact chạy trên máy thật thì vẫn là
`specified`.*
**Ngày:** 2026-11-09 · **Năng lực:** roadmap A1 (hiện thực 3 component cần custom
QML trong `docs/adr/ADR-0016-design-system-integration.md`) + nối token Sen Việt
vào bộ màu KDE sống.

> **Vì sao là 3 component này:** ADR 0016 (bảng ánh xạ 12 component) kết luận 8/12
> component **mappable** thẳng sang control Qt/Kirigami có sẵn (chỉ chỉnh màu/bo
> góc), còn **ConnectionStepper, ErrorCard, AIPlanCard** là **custom QML** vì
> không có control chuẩn tương đương và/hoặc mang nghiệp vụ NaMiOS (mã lỗi,
> correlation_id, SmartAI). Tài liệu này hiện thực đúng 3 cái đó.

---

## 0. Tệp tạo trong hạng mục này

| Tệp | Vai trò |
| --- | --- |
| `distro/.../usr/share/namios/qml/SenVietPalette.qml` | `QtObject` bảng màu Sen Việt (sáng/tối) — **nguồn màu duy nhất** cho các component, HEX đồng bộ `tokens.json`. |
| `distro/.../usr/share/namios/qml/SenVietButton.qml` | Nút áp bảng màu (primary teal / brand đỏ son / danger / secondary / ghost), cao 40dp, focus ring ≥2px. |
| `distro/.../usr/share/namios/qml/ErrorCard.qml` | **Component 1** — thẻ lỗi bind phong bì sự kiện. |
| `distro/.../usr/share/namios/qml/ConnectionStepper.qml` | **Component 2** — dãy bước pipeline kết nối. |
| `distro/.../usr/share/namios/qml/AIPlanCard.qml` | **Component 3** — kế hoạch ≤3 bước của SmartAI. |
| `distro/.../usr/share/namios/qml/Gallery.qml` | Trang preview/gallery dựng cả 3 với dữ liệu mẫu (sáng + tối). |
| `branding/design-system/make-colorscheme.py` | Sinh `color-schemes/NaMiOS.colors` từ `tokens.json` (token → theme KDE). |

Đường dẫn cài trong ISO: `/usr/share/namios/qml/*.qml`.
Thư mục đơn, các component gọi nhau theo **tên tệp** (QML tự phân giải component
cùng thư mục, không cần `qmldir`).

---

## 1. Ánh xạ component → spec design-system

### 1.1 ErrorCard ↔ EVENT-ERROR-CONTRACT §6 + components-preview.html §10

ErrorCard hiển thị **MỘT phong bì sự kiện** (`docs/specs/EVENT-ERROR-CONTRACT.md`
§2). Bind trực tiếp các trường catalog + runtime:

| Trường hợp đồng (§2) | Thuộc tính QML | Ghi chú |
| --- | --- | --- |
| `result` (success/failure/unknown) | `result` | Dòng kết quả nói RÕ **THÀNH CÔNG / THẤT BẠI / CHƯA XÁC ĐỊNH** + glyph (✓/✕/?), không chỉ màu. |
| `phase` (bản tiếng Việt) | `phaseLabel` | Ẩn khi "chưa xác định". |
| `cause_code` | `causeCode` | Render **mono**; là định danh, không dịch. `*-000` ⇒ tự coi là chưa xác định. |
| `correlation_id` | `correlationId` | Render **mono**, cạnh mã lỗi. |
| `message_vi` | `messageVi` | Câu thông báo tiếng Việt. |
| `evidence` (đã che) | `evidenceText` | Chỉ hiện trong panel "Chi tiết kỹ thuật" (chỉ đọc). |
| `default_confidence` | `confidence` | Chip "Mức chắc chắn: cao/vừa/thấp". |
| lịch sử cùng `correlation_id` | `historyModel` | `[{ time, text }]`, mở bằng nút "▸ Lịch sử". |

**Ba nút** (§6.2) phát tín hiệu, KHÔNG tự chạy state-change:

| Nút (l10n_key) | Tín hiệu QML | Bên nối vào |
| --- | --- | --- |
| Thử lại (`ui.errorcard.retry`) | `retryRequested()` | chạy lại chẩn đoán **read-only** (`namios-chan-doan`). |
| Chi tiết kỹ thuật (`ui.errorcard.details`) | `detailsRequested()` + mở panel evidence | chỉ đọc, evidence **đã che bí mật** (§2.2). |
| Nhờ SmartAI giải thích (`ui.errorcard.ask_ai`) | `askSmartAIRequested()` | `namios-smartai --explain <cause_code>` (cổng chính sách + xác nhận + undo nằm ở SmartAI, KHÔNG ở ErrorCard). |

Bất biến đã tôn trọng ở lớp UI: `result ∈ {failure, unknown}` ⇒ hiện phase + mã +
evidence; `causeCode` kết thúc `-000` ⇒ "CHƯA XÁC ĐỊNH", không bịa nguyên nhân.

### 1.2 ConnectionStepper ↔ EVENT-ERROR-CONTRACT §3 + preview §9

Generic cho cả 3 họ pipeline (component không hardcode mạng):

- MẠNG: `radio → ssid → auth → ip → dns → portal`
- MÁY IN: `discovery → backend → queue → device → scan`
- BLUETOOTH: `service → discover → pair → profile`

`steps = [{ title, detail, status }]`, `status ∈ done | active | failed |
pending`. Mỗi bước có **HÌNH** (✓ xong / ✕ thất bại / ⋯ đang chạy / số thứ tự) +
**CHỮ trạng thái** ("— xong/thất bại/đang chạy/chờ") — chỉ rõ **bước đầu tiên
thất bại** như yêu cầu §C ("lỗi xác định tại bước nào"). Đường nối dọc đổi màu
theo tiến độ (success/error/info/viền).

### 1.3 AIPlanCard ↔ UPDATE-CENTER-UI §5 + preview §11

`planSteps = [{ title, evidence, confidence, needsPermission }]`, confidence ∈
`cao | vừa | thấp`. Ràng buộc đã mã hoá:

- **Kẹp còn tối đa 3 bước** (`_steps = planSteps.slice(0,3)`) — bất biến SmartAI.
- Mỗi bước có **bằng chứng** + **chip mức chắc chắn** (chữ + viền màu, không chỉ màu).
- Bước cần quyền gắn nhãn "🔒 (cần mật khẩu)" — **xin phép**; không tự đổi cấu hình.
- **Disclaimer** cố định: "SmartAI không tự ý đổi cấu hình/quyền. Mọi thay đổi hệ
  thống có thể **hoàn tác** bằng Timeshift."
- Tín hiệu `declineRequested()` ("Không, để tôi tự làm") và `runStepRequested(int)`
  ("Làm bước 1") — hành động thật đi qua Update Service/cổng chính sách, không ở card.

---

## 2. Bảng màu + token → theme KDE

- **Màu trong component** lấy từ `SenVietPalette` (đổi `dark: true/false`), HEX
  đồng bộ `branding/design-system/tokens.json` §`color.light`/`color.dark`. Quy
  tắc tương phản đã tôn trọng: chữ đỏ trên nền sáng dùng **đỏ đài `brandRedDeep`
  (#92212E)** chứ không dùng đỏ son; đỏ son chỉ làm nhấn/nền nút chữ trắng.
- **Màu toàn desktop KDE**: `make-colorscheme.py` đọc `tokens.json` và **sinh**
  `distro/.../usr/share/color-schemes/NaMiOS.colors`:
  - Accent/Selection/Decoration = **đỏ son #C93643 (201,54,67)** — khớp
    `kdeglobals` `AccentColor=201,54,67` (script tự kiểm và **không** sửa kdeglobals).
  - `ForegroundActive` = **đỏ đài #92212E (146,33,46)** cho chữ đỏ đạt WCAG.
  - Window/View/Button/Header/Tooltip = **nền ngà ấm** + chữ **mực #182E3B**.
  - `Colors:Complementary` = **bộ TỐI** (color.dark) cho vùng nền tối.

Chạy lại khi đổi token:

```bash
python3 branding/design-system/make-colorscheme.py
```

---

## 3. Cách nhúng (follow-up: SmartAI / Update Center)

Các component là item tái dùng; app Kirigami/Qt nhúng bằng cách đặt vào layout và
bind thuộc tính + nối tín hiệu. Ví dụ ErrorCard trong Update Center (mã `UPD-003`):

```qml
import QtQuick
import "/usr/share/namios/qml" as NM   // hoặc thêm đường dẫn vào QML2_IMPORT_PATH

NM.ErrorCard {
    dark: Kirigami.Theme.colorSet === Kirigami.Theme.Complementary
    familyTitle: "Cập nhật"
    title: catalog["UPD-003"].ui_title_vi
    result: "failure"
    causeCode: "UPD-003"
    correlationId: event.correlation_id
    messageVi: catalog["UPD-003"].cause_vi
    evidenceText: updateService.redact(event.evidence)   // đã che bí mật
    historyModel: auditLog.byCorrelation(event.correlation_id)
    onRetryRequested:   updateService.recheck()          // read-only
    onDetailsRequested: {}                                // panel tự mở
    onAskSmartAIRequested: smartai.explain("UPD-003")     // qua AIPlanCard
}
```

AIPlanCard nhận gợi ý từ SmartAI (sau `--explain`):

```qml
NM.AIPlanCard {
    dark: appIsDark
    planSteps: smartai.plan            // ≤3 bước {title,evidence,confidence,needsPermission}
    onDeclineRequested: {}
    onRunStepRequested: (i) => updateService.run(smartai.plan[i])  // cổng chính sách
}
```

ConnectionStepper nhận trạng thái pipeline từ `namios-chan-doan`:

```qml
NM.ConnectionStepper {
    dark: appIsDark
    heading: "Kết nối Wi-Fi"
    steps: diagnose.networkPhases      // [{title,detail,status}]
}
```

**Khi nối thật còn phải:** bind nhãn theo `l10n_key` (không hardcode câu chữ ở
chỗ dùng), lấy `dark` theo `Kirigami.Theme`, bảo đảm `QML2_IMPORT_PATH` trỏ tới
`/usr/share/namios/qml` (hoặc thêm `qmldir` khi đóng gói thành module).

---

## 4. Trung thực về kiểm chứng (bắt buộc đọc)

- **Chưa chạy trên KDE/Qt thật.** Mọi tệp mang `verified_on_host: NO`. Đây là mã
  QML + bộ màu **đã viết**, chưa boot Plasma, chưa render pixel, chưa test người
  dùng/screen reader thật.
- **qmllint/qml KHÔNG có trong sandbox** hiện tại (đã kiểm: chỉ có `python3`).
  Thay vào đó đã làm **rà cấu trúc thủ công bằng script**: cân bằng
  `{}`/`()`/`[]` (đạt), `import` đúng (`QtQuick`, `QtQuick.Layouts`,
  `org.kde.kirigami as Kirigami`, `QtQuick.Controls as QQC2`), không dùng Plasma
  import khi không cần. **Chưa** phân giải type/thuộc tính bằng trình biên dịch QML.
- **Phải làm khi có máy/ảnh KDE thật** (gate trước khi lên `partial`/`completed`):
  1. `qmllint6 *.qml` (hoặc `qmllint`) với KF6/Kirigami trong import path → 0 lỗi.
  2. `qml6 Gallery.qml` → mở được, render 3 component sáng + tối.
  3. Kiểm **tương phản/HiDPI** trên **1366×768 / 1920×1080 / 2560×1440** ở zoom
     **100/125/150/200%**: không mất nút, text reflow (WCAG 2.2 SC 1.4.4).
  4. **Bàn phím**: Tab tới mọi nút thấy focus ring ≥2px; **screen reader** đọc
     tên · trạng thái · nút (`Accessible.name` đã đặt).
  5. **Giảm chuyển động**: xác nhận không có animation trang trí (hiện không dùng
     animation; nếu thêm, phải đọc `Kirigami.Units`/trạng thái reduce của hệ).
  6. Boot ISO → xác nhận `NaMiOS.colors` áp đúng (nền ngà, nhấn đỏ son) mà không
     phá `AccentColor` kdeglobals.
