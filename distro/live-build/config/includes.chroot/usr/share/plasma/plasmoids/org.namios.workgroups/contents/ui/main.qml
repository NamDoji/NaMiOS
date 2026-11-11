/*
 * NaMiOS — widget desktop "Theo nhóm việc" (plasmoid Plasma 6).
 * Lưới 2 cột × 6 chip kính mờ bo góc, mỗi chip có badge tròn gradient
 * (màu lấy đúng branding/style/namios.css: .nm-chip + .nm-chip .dot) + nhãn
 * tiếng Việt. Click một chip = hiệu ứng (nhấp nháy viền + co nhẹ) + hiện nhãn
 * "Đã chọn: <nhóm>" phía dưới trong vài giây — MVP, KHÔNG mở ứng dụng thật
 * (tránh over-engineer như yêu cầu).
 *
 * verified_on_boot: NO — cần boot KDE Plasma thật trên ISO để xác nhận QML
 * nạp đúng trên bản Plasma đóng gói trong Debian 13 (trixie). Kính mờ
 * (rgba trong suốt) chỉ thấy rõ khi có nội dung desktop phía sau; dưới
 * QEMU/TCG (compositing tắt) nền sẽ đặc màu thay vì mờ — không phải lỗi.
 */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

PlasmoidItem {
    id: root
    Plasmoid.title: "Theo nhóm việc"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    fullRepresentation: Item {
        id: view
        implicitWidth: 360
        implicitHeight: 256

        // Dữ liệu 6 nhóm việc — màu gradient lấy đúng branding/style/namios.css
        // (đỏ son/coral/gold/app-writer(blue)/app-calc(green)/app-photos(purple)).
        // 09/11/2026: "Văn phòng" đổi từ jade #64c3aa→#168a82 ("Sen bừng sáng"
        // v1.0, jade ĐÃ GỠ BỎ) sang đỏ cánh→đỏ son #e56365→#c93643 (v2 "Sen
        // Việt"). Lưu ý: giờ gần tông với "Thuế" (coral) hơn bản cũ vì bộ màu
        // v2 không còn sắc xanh/ngọc để phân biệt — chấp nhận đánh đổi.
        // 11/11/2026: remap sang NaMiOS v3 "Đông Sơn" — đỏ son/cánh cũ
        // (#e56365/#c93643) → vermilion #D64C3E (vai trò "action": chip =
        // mở nhóm việc); c1 là bản nhạt của vermilion để giữ hiệu ứng
        // gradient sáng→tối như các chip khác. Vẫn gần tông "Thuế" như note
        // cũ — không đổi thêm, ngoài phạm vi (chip khác do wave khác sở hữu).
        property var groups: [
            { label: "Văn phòng",  badge: "VP", c1: "#e2776b", c2: "#d64c3e", ink: false },
            { label: "Thuế",       badge: "%",  c1: "#ff8b6c", c2: "#d94d43", ink: false },
            { label: "Kế toán",    badge: "KT", c1: "#dea93e", c2: "#8b6518", ink: true  },
            { label: "Bảo hiểm",   badge: "BH", c1: "#15466b", c2: "#092d4f", ink: false },
            { label: "Giáo dục",   badge: "GD", c1: "#278f8d", c2: "#1f706f", ink: false },
            { label: "Hành chính", badge: "HC", c1: "#5fd3d1", c2: "#278f8d", ink: true  }
        ]

        Rectangle {
            anchors.fill: parent
            radius: 22
            color: Qt.rgba(0.06, 0.13, 0.18, 0.72)
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.14)

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 8

                Text {
                    Layout.fillWidth: true
                    text: "Theo nhóm việc"
                    color: "#FFF9EF"
                    font.bold: true
                    font.pixelSize: 15
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 8
                    columnSpacing: 8
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    Repeater {
                        model: view.groups

                        delegate: Rectangle {
                            id: chip
                            Layout.fillWidth: true
                            Layout.preferredHeight: 46
                            radius: 14
                            color: mouseArea.containsMouse
                                   ? Qt.rgba(1, 1, 1, 0.11)
                                   : Qt.rgba(1, 1, 1, 0.06)
                            border.width: 1
                            border.color: Qt.rgba(1, 1, 1, 0.08)
                            scale: mouseArea.pressed ? 0.97 : 1.0

                            Behavior on color { ColorAnimation { duration: 120 } }
                            Behavior on scale { NumberAnimation { duration: 90 } }

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                spacing: 10

                                // Badge tròn gradient (tương đương .nm-chip .dot)
                                Rectangle {
                                    Layout.preferredWidth: 26
                                    Layout.preferredHeight: 26
                                    Layout.alignment: Qt.AlignVCenter
                                    radius: 13
                                    gradient: Gradient {
                                        GradientStop { position: 0.0; color: modelData.c1 }
                                        GradientStop { position: 1.0; color: modelData.c2 }
                                    }
                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.badge
                                        font.bold: true
                                        font.pixelSize: 11
                                        color: modelData.ink ? "#092D4F" : "#ffffff"
                                    }
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.label
                                    color: "#FFF9EF"
                                    font.pixelSize: 13
                                    elide: Text.ElideRight
                                }
                            }

                            MouseArea {
                                id: mouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    statusLabel.text = "Đã chọn: " + modelData.label
                                    statusTimer.restart()
                                    flash.restart()
                                }
                            }

                            // Hiệu ứng nhấp nháy viền khi click (MVP, không mở app thật)
                            SequentialAnimation {
                                id: flash
                                PropertyAction { target: chip; property: "border.color"; value: Qt.rgba(1, 1, 1, 0.55) }
                                PauseAnimation { duration: 140 }
                                PropertyAction { target: chip; property: "border.color"; value: Qt.rgba(1, 1, 1, 0.08) }
                            }
                        }
                    }
                }

                Text {
                    id: statusLabel
                    Layout.fillWidth: true
                    Layout.preferredHeight: 16
                    text: ""
                    color: "#b7c4cf"
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                    opacity: text.length > 0 ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: 200 } }
                }
            }
        }

        Timer {
            id: statusTimer
            interval: 1800
            onTriggered: statusLabel.text = ""
        }
    }
}
