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
        property var groups: [
            { label: "Văn phòng",  badge: "VP", c1: "#e56365", c2: "#c93643", ink: false },
            { label: "Thuế",       badge: "%",  c1: "#ff8b6c", c2: "#d94d43", ink: false },
            { label: "Kế toán",    badge: "KT", c1: "#ffe1a1", c2: "#e5a53e", ink: true  },
            { label: "Bảo hiểm",   badge: "BH", c1: "#3b82f6", c2: "#1d4ed8", ink: false },
            { label: "Giáo dục",   badge: "GD", c1: "#22c55e", c2: "#15803d", ink: false },
            { label: "Hành chính", badge: "HC", c1: "#c084fc", c2: "#7c3aed", ink: false }
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
                    color: "#f7f6f1"
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
                                        color: modelData.ink ? "#172c3d" : "#ffffff"
                                    }
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.label
                                    color: "#f7f6f1"
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
