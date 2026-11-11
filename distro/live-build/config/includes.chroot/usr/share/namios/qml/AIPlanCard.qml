/*
 * NaMiOS — AIPlanCard.qml
 * Thẻ KẾ HOẠCH của nAI: TỐI ĐA 3 bước, mỗi bước có bằng chứng + mức chắc
 * chắn (cao / vừa / thấp). nAI chỉ GIẢI THÍCH/ĐỀ XUẤT; mọi thay đổi cấu hình
 * phải XIN PHÉP (qua cổng chính sách) và có HOÀN TÁC (Timeshift). Xem
 * docs/specs/UPDATE-CENTER-UI.md §5 và components-preview.html §11.
 *
 * Ranh giới cứng (ghi ở disclaimer + hành vi UI):
 *   - không tự đổi cấu hình/quyền; bước cần quyền được đánh dấu "cần mật khẩu".
 *   - danh sách bước bị kẹp còn ≤3 (bất biến nAI).
 *
 * verified_on_host: NO — chưa dựng trên Qt/KDE thật; mới kiểm cấu trúc QML thủ công.
 */
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ShadowedRectangle {
    id: plan

    property bool dark: false
    property string headline: ""     // vd "nAI đề xuất 3 bước" (tự tính nếu rỗng)
    property string safetyNote: "Chỉ đọc chẩn đoán · chưa đổi gì"
    property string disclaimer: "nAI không tự ý đổi cấu hình/quyền. Mọi thay đổi hệ thống có thể hoàn tác bằng Timeshift."
    // [{ title, evidence, confidence: "cao"|"vừa"|"thấp", needsPermission: bool }]
    property var planSteps: []

    signal declineRequested()
    signal runStepRequested(int index)

    SenVietPalette { id: pal; dark: plan.dark }

    // Kẹp còn tối đa 3 bước (bất biến nAI)
    readonly property var _steps: (planSteps.length > 3) ? planSteps.slice(0, 3) : planSteps
    readonly property string _headline: headline.length > 0
                                        ? headline
                                        : "nAI đề xuất " + _steps.length + " bước"

    function _confColor(c) {
        switch (c) {
        case "cao": return pal.statusSuccess
        case "vừa": return pal.statusWarning
        default:    return pal.statusInfo   // thấp
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
    Accessible.name: plan._headline

    ColumnLayout {
        id: col
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        spacing: 12

        // Tiêu đề: tia sáng ✦ + headline + chip an toàn
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Rectangle {
                Layout.preferredWidth: 30
                Layout.preferredHeight: 30
                // CONSISTENCY FIX (12/11/2026): radius 15 (hình tròn đầy) KHÔNG khớp
                // đặc tả tham chiếu branding/design-system/components.css .nm-aiplan
                // .spark { border-radius: var(--r-md) } — badge "✦" PHẢI là ô vuông bo
                // (radius.md = 12), KHÁC hình tròn (so với glyph kết quả của ErrorCard,
                // đã đổi sang 50% đúng hướng ngược lại — 2 pattern khác nhau có chủ đích
                // theo đúng components.css, không phải lẫn lộn).
                radius: 12
                color: pal.brandRed
                Text {
                    anchors.centerIn: parent
                    text: "✦"
                    color: "#FFFFFF"
                    font.pixelSize: 16
                }
            }
            Text {
                text: plan._headline
                color: pal.textPrimary
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                radius: 999
                color: pal.surfaceSubtle
                implicitHeight: 24
                implicitWidth: safeText.implicitWidth + 20
                Text {
                    id: safeText
                    anchors.centerIn: parent
                    text: plan.safetyNote
                    color: pal.textSecondary
                    font.pixelSize: 12
                }
            }
        }

        // Danh sách ≤3 bước
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 10
            Repeater {
                model: plan._steps
                delegate: RowLayout {
                    id: planRow
                    required property int index
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 12

                    // Số thứ tự
                    Rectangle {
                        Layout.alignment: Qt.AlignTop
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 26
                        // CONSISTENCY FIX (12/11/2026): radius 8 (squircle) KHÔNG khớp
                        // .nm-aiplan li .n { border-radius: 50% } — số thứ tự bước PHẢI
                        // là hình tròn đầy, 26/2 (kích thước 26 giữ nguyên, khác 24 của
                        // bản CSS — đổi hình dạng, không đổi size, giảm rủi ro layout).
                        radius: 13
                        color: pal.surfaceSubtle
                        border.width: 1
                        border.color: pal.borderSubtle
                        Text {
                            anchors.centerIn: parent
                            text: String(planRow.index + 1)
                            color: pal.textPrimary
                            font.pixelSize: 14
                            font.bold: true
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        Text {
                            Layout.fillWidth: true
                            text: (modelData.title !== undefined ? modelData.title : "")
                                  + ((modelData.needsPermission === true) ? "  🔒 (cần mật khẩu)" : "")
                            color: pal.textPrimary
                            font.pixelSize: 15
                            font.weight: Font.Medium
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: modelData.evidence !== undefined && modelData.evidence.length > 0
                            text: "Bằng chứng: " + (modelData.evidence !== undefined ? modelData.evidence : "")
                            color: pal.textSecondary
                            font.pixelSize: 13
                            wrapMode: Text.WordWrap
                        }
                        // Chip mức chắc chắn (chữ + nền, không chỉ màu)
                        Rectangle {
                            radius: 999
                            color: pal.surfaceSubtle
                            border.width: 1
                            border.color: plan._confColor(modelData.confidence)
                            implicitHeight: 22
                            implicitWidth: confText.implicitWidth + 18
                            Text {
                                id: confText
                                anchors.centerIn: parent
                                text: "Chắc chắn: " + (modelData.confidence !== undefined ? modelData.confidence : "thấp")
                                color: pal.textPrimary
                                font.pixelSize: 12
                                font.weight: Font.Medium
                            }
                        }
                    }
                }
            }
        }

        // Disclaimer ranh giới
        Rectangle {
            Layout.fillWidth: true
            radius: 12
            color: pal.surfaceSubtle
            border.width: 1
            border.color: pal.borderSubtle
            implicitHeight: disc.implicitHeight + 16
            Text {
                id: disc
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.margins: 10
                text: plan.disclaimer
                color: pal.textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
        }

        // Nút: từ chối (ghost) + làm bước 1 (primary)
        Flow {
            Layout.fillWidth: true
            spacing: 8
            SenVietButton {
                pal: pal
                kind: "ghost"
                text: "Không, để tôi tự làm"
                onClicked: plan.declineRequested()
            }
            SenVietButton {
                pal: pal
                kind: "primary"
                text: "Làm bước 1"
                visible: plan._steps.length > 0
                onClicked: plan.runStepRequested(0)
            }
        }
    }
}
