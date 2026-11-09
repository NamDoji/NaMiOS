/*
 * NaMiOS — SenVietButton.qml
 * Nút bấm áp bảng màu "Sen Việt" (dựa trên QtQuick.Controls.Button), dùng chung
 * cho ErrorCard / ConnectionStepper / AIPlanCard. Nhãn tiếng Việt = động từ rõ.
 * Chiều cao 40dp (control.default), bo góc 12 (radius.md), focus ring ≥2px.
 *
 * Thuộc tính:
 *   - pal  : một SenVietPalette (bắt buộc truyền vào để lấy màu theo sáng/tối).
 *   - kind : "primary"(teal) | "brand"(đỏ son) | "danger" | "secondary"(viền) | "ghost".
 *
 * verified_on_host: NO — chưa dựng trên Qt/KDE thật; mới kiểm cấu trúc QML thủ công.
 */
import QtQuick
import QtQuick.Controls as QQC2

QQC2.Button {
    id: ctl

    property var pal
    property string kind: "secondary"

    // Khoảng cách nền tối thiểu 40×40dp (control.min_target_dp)
    implicitHeight: 40
    leftPadding: 16
    rightPadding: 16
    topPadding: 8
    bottomPadding: 8
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus

    // Màu nền theo kind + trạng thái hover/pressed
    readonly property color _bg: {
        switch (kind) {
        case "primary": return (ctl.down || ctl.hovered) ? pal.actionHover : pal.actionPrimary
        case "brand":   return ctl.down ? Qt.darker(pal.brandRed, 1.12) : pal.brandRed
        case "danger":  return ctl.down ? Qt.darker(pal.statusError, 1.12) : pal.statusError
        case "ghost":   return ctl.hovered ? pal.surfaceSubtle : "transparent"
        default:        return ctl.hovered ? pal.surfaceSubtle : pal.surfaceCard // secondary
        }
    }
    // Màu chữ theo kind
    readonly property color _fg: {
        switch (kind) {
        case "primary": return pal.onAction
        case "brand":   return pal.onBrand
        case "danger":  return "#FFFFFF"
        case "ghost":   return pal.actionPrimary
        default:        return pal.textPrimary // secondary
        }
    }
    readonly property bool _hasBorder: kind === "secondary"

    Accessible.role: Accessible.Button
    Accessible.name: ctl.text

    contentItem: Text {
        text: ctl.text
        color: ctl._fg
        font.pixelSize: 14
        font.weight: Font.Medium
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: 12
        color: ctl._bg
        border.width: ctl._hasBorder ? 1 : 0
        border.color: pal.borderStrong

        // Focus ring ≥2px, lệch ra ngoài 2px — KHÔNG chỉ đổi màu nền (WCAG)
        Rectangle {
            anchors.fill: parent
            anchors.margins: -2
            radius: parent.radius + 2
            color: "transparent"
            border.width: 2
            border.color: pal.focusRing
            visible: ctl.visualFocus || ctl.activeFocus
        }
    }
}
