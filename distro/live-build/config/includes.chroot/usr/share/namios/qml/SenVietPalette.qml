/*
 * NaMiOS — SenVietPalette.qml
 * Bảng màu "Đông Sơn" v3.0 dùng chung cho các component QML (nền navy/ngà,
 * vàng kim, đỏ vermilion, ngọc lam). THAY bộ "Sen Việt" v2.0 (đỏ son/vàng) —
 * 11/11/2026. Giữ nguyên TÊN FILE và TÊN PROPERTY (API không đổi, chỉ đổi giá
 * trị hex) để các component QML khác (ErrorCard, ConnectionStepper, AIPlanCard,
 * Gallery.qml) không phải sửa gì. Giá trị HEX đồng bộ với
 * usr/share/namios-branding/logo/brand.json (AUTHORITATIVE PALETTE Đông Sơn)
 * và usr/share/color-schemes/NaMiOS.colors. Đổi `dark` để chuyển sáng/tối.
 * KHÔNG hardcode màu trong từng component — lấy từ đây.
 *
 * Lưu ý tương phản (đã ĐO WCAG — xem usr/share/namios/docs/BRAND.md mục "Sắc
 * độ phụ trợ" để biết công thức/số đo đầy đủ, không nhắc lại đây):
 *   - chữ đỏ trên nền SÁNG phải dùng brandRedDeep (#A02E22), không dùng brandRed
 *     (#D64C3E trên trắng chỉ ~4.2:1, dưới chuẩn AA chữ thường).
 *   - chữ vàng trên nền SÁNG phải dùng brandGold ở nhánh light (#8B6518,
 *     "gold-deep"), KHÔNG dùng mã gold gốc #DEA93E làm chữ nhỏ trên nền sáng
 *     (chỉ ~2.1:1 — gold gốc CHỈ dùng làm nền/khối/accent trên nền TỐI).
 *   - gold/brandRed ở nền tối chỉ dùng nhấn/chữ lớn/icon, không làm chữ thường nhỏ.
 *
 * TÊN FILE (ghi chú UI polish 12/11/2026, QA n11 — "retire stale SenViet
 * naming"): "SenVietPalette" CHỈ còn là tên lịch sử, giữ nguyên có chủ đích
 * (không phải quên đổi) — nhiều tài liệu ngoài phạm vi sửa của polish này
 * (docs/specs/QML-COMPONENTS.md, docs/release/BRANDING-MAP-OLD-NEW.md,
 * docs/release/QA-UIUX-2026.11.md, usr/share/namios/docs/BRAND.md) tham
 * chiếu đúng tên file này; đổi tên sẽ làm các tài liệu đó trỏ sai mà task
 * này không có quyền sửa lại. Nếu một wave sau có quyền sửa ĐỦ các tài liệu
 * trên cùng lúc, đổi tên hợp lý hơn là "DongSonPalette.qml" + cập nhật 4
 * importer thật trong cùng thư mục (ErrorCard/ConnectionStepper/AIPlanCard/
 * UpdateCenterPL19.qml) + SenVietButton.qml (import gián tiếp qua property
 * "pal"). Nội dung màu bên trong file đã là v3 "Đông Sơn" từ 11/11/2026.
 *
 * verified_on_host: NO — chưa nạp trên KDE Plasma/Qt thật; mới là khai báo QML.
 */
import QtQuick

QtObject {
    id: pal

    // true = nền navy (dark); false = nền ngà ấm (light)
    property bool dark: false

    // Bề mặt (surface)
    readonly property color surfaceBase:   dark ? "#092D4F" : "#FFF9EF"  // nền trang/dialog — navy / ivory (token gốc)
    readonly property color surfaceCard:   dark ? "#0B3965" : "#FFFFFF"  // card/panel nổi — navy-card (suy ra) / white
    readonly property color surfaceSubtle: dark ? "#0A3257" : "#FFF2DB"  // chip/hàng chẵn/ô nền — navy-subtle / ivory-subtle (suy ra)

    // Chữ (text)
    readonly property color textPrimary:   dark ? "#FFF9EF" : "#092D4F"  // ivory / navy (token gốc)
    readonly property color textSecondary: dark ? "#C9D3D6" : "#52646B"  // phụ/metadata — màu chức năng, không đổi
    readonly property color onBrand:       "#FFFFFF"                       // chữ trên nền đỏ vermilion/nút hành động

    // Thương hiệu (brand)
    readonly property color brandRed:      dark ? "#E48A81" : "#D64C3E"  // vermilion — nhấn/nền nút (dark: "vermilion-light" suy ra để đọc được trên navy)
    readonly property color brandRedDeep:  dark ? "#D64C3E" : "#A02E22"  // chữ đỏ an toàn (sáng): "vermilion-deep" suy ra, ~7.2:1 trên trắng
    readonly property color brandGold:     dark ? "#DEA93E" : "#8B6518"  // vàng kim (dark: token gốc, ~6.6:1 trên navy) / "gold-deep" suy ra cho chữ an toàn trên nền sáng (~5.3:1 trên trắng)
    readonly property color goldSoft:      "#DEA93E"                       // vàng kim trang trí — token gốc

    // Hành động chính (teal)
    readonly property color actionPrimary: dark ? "#5FD3D1" : "#278F8D"  // teal-light (suy ra, đọc được trên navy ~7.8:1) / teal token gốc
    readonly property color actionHover:   dark ? "#87DEDD" : "#1F706F"  // biến thể nhạt hơn/đậm hơn khi hover
    readonly property color onAction:      dark ? "#092D4F" : "#FFFFFF"  // chữ trên nền hành động — navy / white

    // Trạng thái (status) — luôn kèm CHỮ + HÌNH, không chỉ màu. KHÔNG thuộc
    // brand.json (lớp màu CHỨC NĂNG riêng, xem lưu ý trong desktoptheme/NaMiOS-Sen/colors) — GIỮ NGUYÊN.
    readonly property color statusSuccess: dark ? "#59C798" : "#127A52"  // đã xong
    readonly property color statusWarning: dark ? "#F6BB68" : "#965300"  // chú ý / một phần
    readonly property color statusError:   dark ? "#FF8B8F" : "#B4232B"  // lỗi/chặn
    readonly property color statusInfo:    dark ? "#9DB3BC" : "#1F5E70"  // trung tính / chưa xác định

    // Tiêu điểm + viền
    readonly property color focusRing:     dark ? "#DEA93E" : "#8B6518"  // ring ≥2px — vai trò "signature accent/focus": gold token gốc trên nền tối, "gold-deep" suy ra trên nền sáng (gold gốc trên trắng chỉ ~2.1:1, KHÔNG đủ 3:1 non-text)
    readonly property color borderSubtle:  dark ? "#2E4A5B" : "#D9CDB7"  // CHỈ trang trí — màu cấu trúc chung, không đổi
    readonly property color borderStrong:  dark ? "#657F90" : "#8C8068"  // viền mang nghĩa (≥3:1) — màu cấu trúc chung, không đổi
}
