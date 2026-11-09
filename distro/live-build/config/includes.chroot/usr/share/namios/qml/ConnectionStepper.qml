/*
 * NaMiOS — ConnectionStepper.qml
 * Dãy BƯỚC của một pipeline kết nối, chỉ rõ bước đang THẤT BẠI. Dùng cho mạng
 * (radio → ssid → auth → ip → dns → portal), máy in (discovery → backend → queue
 * → device → scan), Bluetooth (service → discover → pair → profile) — xem
 * docs/specs/EVENT-ERROR-CONTRACT.md §3. Component generic theo danh sách `steps`.
 *
 * Mỗi bước: { title, detail, status } với status ∈ "done" | "active" | "failed" |
 * "pending". Trạng thái luôn kèm HÌNH (✓ / ✕ / ⋯ / số) + CHỮ, không chỉ màu.
 *
 * verified_on_host: NO — chưa dựng trên Qt/KDE thật; mới kiểm cấu trúc QML thủ công.
 */
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ShadowedRectangle {
    id: stepper

    property bool dark: false
    property string heading: "Các bước kết nối"
    // [{ title, detail, status }]  status: done | active | failed | pending
    property var steps: []

    SenVietPalette { id: pal; dark: stepper.dark }

    readonly property int stepCount: steps.length

    function _col(s) {
        switch (s) {
        case "done":   return pal.statusSuccess
        case "failed": return pal.statusError
        case "active": return pal.statusInfo
        default:       return pal.borderStrong
        }
    }
    function _glyph(s, n) {
        switch (s) {
        case "done":   return "✓"
        case "failed": return "✕"
        case "active": return "⋯"
        default:       return String(n)
        }
    }
    function _reached(s) {
        return s === "done" || s === "failed" || s === "active"
    }
    function _statusVi(s) {
        switch (s) {
        case "done":   return "xong"
        case "failed": return "thất bại"
        case "active": return "đang chạy"
        default:       return "chờ"
        }
    }

    implicitWidth: 560
    implicitHeight: col.implicitHeight + 32
    radius: 16
    color: pal.surfaceCard
    border.width: 1
    border.color: pal.borderSubtle
    shadow.size: 16
    shadow.yOffset: 4
    shadow.color: Qt.rgba(0.07, 0.16, 0.22, dark ? 0.35 : 0.12)

    Accessible.role: Accessible.Grouping
    Accessible.name: stepper.heading

    ColumnLayout {
        id: col
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        spacing: 8

        Text {
            Layout.fillWidth: true
            text: stepper.heading
            color: pal.textPrimary
            font.pixelSize: 18
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
        }

        ColumnLayout {
            id: stepList
            Layout.fillWidth: true
            spacing: 0

            Repeater {
                model: stepper.steps
                delegate: RowLayout {
                    id: stepRow
                    required property int index
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 12

                    readonly property string _st: modelData.status !== undefined ? modelData.status : "pending"

                    // Cột dấu + đường nối dọc
                    Item {
                        id: dotCell
                        Layout.preferredWidth: 34
                        Layout.fillHeight: true
                        Layout.minimumHeight: 46

                        // Đường nối (sau dấu); cắt ở đầu/cuối để không thừa
                        Rectangle {
                            width: 2
                            x: (dotCell.width - 2) / 2
                            y: stepRow.index === 0 ? dot.y + dot.height / 2 : 0
                            height: (stepRow.index === stepper.stepCount - 1
                                     ? dot.y + dot.height / 2 : dotCell.height) - y
                            color: stepper._reached(stepRow._st)
                                   ? stepper._col(stepRow._st) : pal.borderSubtle
                            z: 0
                        }

                        Rectangle {
                            id: dot
                            anchors.horizontalCenter: parent.horizontalCenter
                            y: 8
                            width: 28
                            height: 28
                            radius: 14
                            z: 1
                            color: stepper._reached(stepRow._st)
                                   ? stepper._col(stepRow._st) : pal.surfaceCard
                            border.width: stepper._reached(stepRow._st) ? 0 : 2
                            border.color: pal.borderStrong
                            Text {
                                anchors.centerIn: parent
                                text: stepper._glyph(stepRow._st, stepRow.index + 1)
                                color: stepper._reached(stepRow._st) ? "#FFFFFF" : pal.textSecondary
                                font.pixelSize: 14
                                font.bold: true
                            }
                        }
                    }

                    // Nội dung bước
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.topMargin: 6
                        Layout.bottomMargin: 10
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: (modelData.title !== undefined ? modelData.title : "")
                                  + "  — " + stepper._statusVi(stepRow._st)
                            color: pal.textPrimary
                            font.pixelSize: 15
                            font.weight: Font.Medium
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: modelData.detail !== undefined && modelData.detail.length > 0
                            text: modelData.detail !== undefined ? modelData.detail : ""
                            color: stepRow._st === "failed" ? pal.statusError : pal.textSecondary
                            font.pixelSize: 13
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }
    }
}
