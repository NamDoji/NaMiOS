// NaMi — nút RỜI PHIÊN kiểu thẻ Windows 11 (icon + nhãn), dùng trong
// Logout.qml (màn Leave). Tách thành FILE RIÊNG (không để inline trong
// Logout.qml) vì Qt KHÔNG cho dùng inline component TRƯỚC khi khai báo — file
// cùng thư mục thì QML tự nhận làm "type" (LeaveButton) không ràng buộc thứ
// tự. Tự chứa: KHÔNG tham chiếu id ngoài; màu nhận qua property (mặc định =
// bảng màu v3 "Đông Sơn", khớp Logout.qml/Main.qml).
//
// AN TOÀN RENDER: chỉ Rectangle/Text/ColumnLayout + Kirigami.Icon (chính
// breeze dùng Kirigami trong logout trên production) — không shader/blur, chạy
// được trên software renderer. verified_on_host: NO.
import QtQuick 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.20 as Kirigami

FocusScope {
    id: btn

    property string iconName: ""
    property string label: ""
    property bool accent: false  // true = nút chính (Tắt máy) tô vermilion

    // Bảng màu — mặc định v3 "Đông Sơn" (khớp Logout.qml). Có thể ghi đè.
    property color accentColor: "#D64C3E"
    property color goldColor: "#DEA93E"
    property color fgColor: "#FFF9EF"
    property string fontFamily: "Noto Sans"

    signal activated()

    implicitWidth: 128
    implicitHeight: 118
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: btn.label

    Keys.onReturnPressed: btn.activated()
    Keys.onEnterPressed: btn.activated()
    Keys.onSpacePressed: btn.activated()
    // Trái/phải di chuyển giữa các nút (focus chain tự bỏ qua nút ẩn).
    Keys.onLeftPressed: btn.nextItemInFocusChain(false).forceActiveFocus()
    Keys.onRightPressed: btn.nextItemInFocusChain(true).forceActiveFocus()

    Rectangle {
        id: card
        anchors.fill: parent
        radius: 16
        color: {
            if (btn.accent) {
                return cardMouse.pressed ? Qt.darker(btn.accentColor, 1.18)
                     : (cardMouse.containsMouse ? Qt.lighter(btn.accentColor, 1.05) : btn.accentColor);
            }
            return cardMouse.pressed ? Qt.rgba(1, 1, 1, 0.16)
                 : (cardMouse.containsMouse ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.06));
        }
        border.width: btn.activeFocus ? 2 : 1
        border.color: btn.activeFocus ? btn.goldColor
                    : (btn.accent ? Qt.rgba(1, 1, 1, 0.0) : Qt.rgba(1, 1, 1, 0.14))

        Behavior on color { ColorAnimation { duration: 120 } }

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 12

            Kirigami.Icon {
                Layout.alignment: Qt.AlignHCenter
                source: btn.iconName
                Layout.preferredWidth: 40
                Layout.preferredHeight: 40
                // isMask: true + tô ivory để icon LUÔN hiện rõ trên nền navy
                // tối / nút vermilion, bất kể icon theme vẽ màu hay đơn sắc
                // (đồng nhất kiểu glyph đơn sắc Windows 11).
                color: btn.accent ? "#FFFFFF" : btn.fgColor
                isMask: true
            }
            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.maximumWidth: btn.width - 12
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: btn.label
                color: btn.accent ? "#FFFFFF" : btn.fgColor
                font.family: btn.fontFamily
                font.pixelSize: 12
                font.weight: btn.accent ? Font.DemiBold : Font.Normal
            }
        }

        MouseArea {
            id: cardMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: btn.activated()
        }
    }
}
