/*
 * NaMiOS — SenVietPalette.qml
 * Bảng màu "Sen Việt" v1.0 dùng chung cho các component QML (nền ngà ấm, đỏ son,
 * đỏ đài, vàng, mực). Giá trị HEX đồng bộ với branding/design-system/tokens.json
 * (color.light / color.dark) và với usr/share/color-schemes/NaMiOS.colors.
 * Đổi `dark` để chuyển sáng/tối. KHÔNG hardcode màu trong từng component — lấy từ đây.
 *
 * Lưu ý tương phản (đã ĐO WCAG trong tokens.json, không nhắc lại đây):
 *   - chữ đỏ trên nền SÁNG phải dùng brandRedDeep (#92212E), không dùng brandRed.
 *   - gold/brandRed ở nền tối chỉ dùng nhấn/chữ lớn/icon, không làm chữ thường nhỏ.
 *
 * verified_on_host: NO — chưa nạp trên KDE Plasma/Qt thật; mới là khai báo QML.
 */
import QtQuick

QtObject {
    id: pal

    // true = nền mực đêm (dark); false = nền ngà ấm (light)
    property bool dark: false

    // Bề mặt (surface)
    readonly property color surfaceBase:   dark ? "#122A3A" : "#F5F2EB"  // nền trang/dialog
    readonly property color surfaceCard:   dark ? "#1B3748" : "#FFFFFF"  // card/panel nổi
    readonly property color surfaceSubtle: dark ? "#16303F" : "#EDE6D8"  // chip/hàng chẵn/ô nền

    // Chữ (text)
    readonly property color textPrimary:   dark ? "#F8F5EE" : "#182E3B"  // mực / ngà
    readonly property color textSecondary: dark ? "#C9D3D6" : "#52646B"  // phụ/metadata
    readonly property color onBrand:       "#FFFFFF"                       // chữ trên nền đỏ son

    // Thương hiệu (brand)
    readonly property color brandRed:      dark ? "#E56365" : "#C93643"  // đỏ son — nhấn/nền nút
    readonly property color brandRedDeep:  dark ? "#C93643" : "#92212E"  // đỏ đài — chữ đỏ an toàn (sáng)
    readonly property color brandGold:     dark ? "#F2C66D" : "#BC8A43"  // vàng
    readonly property color goldSoft:      "#F2C66D"                       // vàng tâm (trang trí)

    // Hành động chính (teal)
    readonly property color actionPrimary: dark ? "#65D7C8" : "#006E72"
    readonly property color actionHover:   dark ? "#7CE0D3" : "#005A5E"
    readonly property color onAction:      dark ? "#0C2230" : "#FFFFFF"

    // Trạng thái (status) — luôn kèm CHỮ + HÌNH, không chỉ màu
    readonly property color statusSuccess: dark ? "#59C798" : "#127A52"  // đã xong
    readonly property color statusWarning: dark ? "#F6BB68" : "#965300"  // chú ý / một phần
    readonly property color statusError:   dark ? "#FF8B8F" : "#B4232B"  // lỗi/chặn
    readonly property color statusInfo:    dark ? "#9DB3BC" : "#1F5E70"  // trung tính / chưa xác định

    // Tiêu điểm + viền
    readonly property color focusRing:     dark ? "#65D7C8" : "#006E72"  // ring ≥2px
    readonly property color borderSubtle:  dark ? "#2E4A5B" : "#D9CDB7"  // CHỈ trang trí
    readonly property color borderStrong:  dark ? "#657F90" : "#8C8068"  // viền mang nghĩa (≥3:1)
}
