/*
 * NaMiOS — widget desktop "Hỏi SmartAI" (plasmoid Plasma 6).
 * Glass pill navy + biểu tượng tia sáng san hô + gợi ý mẫu, đúng mockup.
 * verified_on_boot: NO — cần boot KDE Plasma thật trên ISO để xác nhận QML nạp
 * đúng trên bản Plasma đóng gói trong Debian 13 (trixie). Kính mờ chỉ hiện khi
 * KWin compositing bật (máy thật có GPU); dưới QEMU/TCG compositing tắt → nền đặc.
 */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    fullRepresentation: Item {
        implicitWidth: 340
        implicitHeight: 96

        Rectangle {
            anchors.fill: parent
            radius: 22
            color: Qt.rgba(0.06, 0.13, 0.18, 0.72)
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.14)

            RowLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 14

                Rectangle {
                    Layout.preferredWidth: 46
                    Layout.preferredHeight: 46
                    Layout.alignment: Qt.AlignVCenter
                    radius: 23
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#ff8b6c" }
                        GradientStop { position: 1.0; color: "#d94d43" }
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "✦"
                        color: "white"
                        font.pixelSize: 22
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 3
                    Text {
                        text: "Hỏi SmartAI"
                        color: "#f7f6f1"
                        font.bold: true
                        font.pixelSize: 16
                    }
                    Text {
                        text: "“In bảng lương tháng 11”"
                        color: "#b7c4cf"
                        font.pixelSize: 13
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }
            }
        }
    }
}
