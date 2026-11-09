/*
 * NaMiOS — ErrorCard.qml
 * Thẻ LỖI bind vào MỘT phong bì sự kiện (docs/specs/EVENT-ERROR-CONTRACT.md §2, §6).
 * Hiển thị: kết quả (THÀNH CÔNG / THẤT BẠI / CHƯA XÁC ĐỊNH) + bước lỗi (phase) +
 * message_vi + mã lỗi/correlation_id (mono) + 3 nút (Thử lại / Chi tiết kỹ thuật /
 * Nhờ SmartAI giải thích) + vùng chi tiết (evidence đã che) và lịch sử cùng
 * correlation_id. Nét tự vẽ (ADR 0011), bảng màu Sen Việt.
 *
 * Bất biến hợp đồng đã tôn trọng ở lớp UI:
 *   - result ∈ {failure, unknown} ⇒ hiện phase + cause_code + evidence.
 *   - cause_code kết thúc "-000" ⇔ "CHƯA XÁC ĐỊNH" (không bịa nguyên nhân).
 *   - ErrorCard KHÔNG tự chạy hành động state-change; chỉ Thử lại (read-only),
 *     mở chi tiết (read-only), và chuyển quyền hành động cho SmartAI qua signal.
 *
 * verified_on_host: NO — chưa dựng trên Qt/KDE thật; mới kiểm cấu trúc QML thủ công.
 */
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ShadowedRectangle {
    id: card

    // ---- Dữ liệu phong bì sự kiện (bind từ error-catalog.json + runtime) ----
    property bool dark: false
    property string familyTitle: ""      // tiêu đề họ thiết bị (vd "Máy in")
    property string title: ""            // dòng tiêu đề chính (message ngắn)
    property string result: "failure"    // "success" | "failure" | "unknown"
    property string phaseLabel: ""       // bản tiếng Việt của phase (vd "Phân giải DNS")
    property string causeCode: ""        // vd "NM-PRN-004"
    property string correlationId: ""    // vd "20261109-142233-5312-8471"
    property string messageVi: ""        // message_vi của cause_code
    property string evidenceText: ""     // evidence ĐÃ CHE bí mật (§2.2)
    property string confidence: ""       // "cao" | "vừa" | "thấp" (tuỳ chọn)
    property var historyModel: []        // [{ time, text }] cùng correlation_id

    // ---- Tín hiệu hành động (parent/UI nối vào namios-chan-doan/smartai) ----
    signal retryRequested()
    signal detailsRequested()
    signal askSmartAIRequested()

    // ---- Trạng thái nội bộ ----
    property bool _detailsOpen: false
    property bool _historyOpen: false

    SenVietPalette { id: pal; dark: card.dark }

    // "-000" hoặc result unknown ⇒ chưa xác định
    readonly property bool undetermined: card.result === "unknown"
                                         || card.causeCode.endsWith("-000")
    readonly property string resultText: undetermined ? "CHƯA XÁC ĐỊNH"
                                         : (card.result === "success" ? "THÀNH CÔNG" : "THẤT BẠI")
    readonly property color resultColor: undetermined ? pal.statusInfo
                                         : (card.result === "success" ? pal.statusSuccess : pal.statusError)
    readonly property string resultGlyph: undetermined ? "?"
                                         : (card.result === "success" ? "✓" : "✕")

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
    Accessible.name: (familyTitle ? familyTitle + ": " : "") + resultText + ". " + title

    ColumnLayout {
        id: col
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        spacing: 12

        // Dòng kết quả: HÌNH (glyph) + CHỮ (không chỉ màu)
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
                Layout.alignment: Qt.AlignTop
                radius: 8
                color: card.resultColor
                Text {
                    anchors.centerIn: parent
                    text: card.resultGlyph
                    color: "#FFFFFF"
                    font.pixelSize: 18
                    font.bold: true
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    Layout.fillWidth: true
                    text: card.title
                    color: pal.textPrimary
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    // Nói RÕ kết quả + bước; "-000" thì giấu tên bước cụ thể
                    text: (card.familyTitle ? card.familyTitle + ": " : "")
                          + card.resultText
                          + (card.undetermined
                             ? "  ·  Chưa đủ bằng chứng để chỉ ra bước lỗi"
                             : (card.phaseLabel ? "  ·  Bước lỗi: " + card.phaseLabel : ""))
                    color: card.resultColor
                    font.pixelSize: 14
                    font.weight: Font.Medium
                    wrapMode: Text.WordWrap
                }
            }
        }

        // message_vi
        Text {
            Layout.fillWidth: true
            visible: card.messageVi.length > 0
            text: card.messageVi
            color: pal.textPrimary
            font.pixelSize: 15
            lineHeight: 1.4
            wrapMode: Text.WordWrap
        }

        // Mức chắc chắn (tuỳ chọn)
        RowLayout {
            visible: card.confidence.length > 0
            spacing: 8
            Rectangle {
                radius: 999
                color: pal.surfaceSubtle
                implicitHeight: 24
                implicitWidth: confText.implicitWidth + 20
                Text {
                    id: confText
                    anchors.centerIn: parent
                    text: "Mức chắc chắn: " + card.confidence
                    color: pal.textSecondary
                    font.pixelSize: 13
                }
            }
        }

        // Dòng mã lỗi + correlation_id (mono) — mã là định danh, không dịch
        Text {
            Layout.fillWidth: true
            visible: card.causeCode.length > 0 || card.correlationId.length > 0
            text: "Mã lỗi: " + card.causeCode
                  + (card.correlationId ? "   ·   correlation_id: " + card.correlationId : "")
            color: pal.textSecondary
            font.family: "Noto Sans Mono"
            font.pixelSize: 14
            wrapMode: Text.WrapAnywhere
        }

        // Ba nút (Flow để reflow ở 200%/màn hẹp)
        Flow {
            Layout.fillWidth: true
            spacing: 8
            SenVietButton {
                pal: pal
                kind: "primary"
                text: "Thử lại"
                onClicked: card.retryRequested()
            }
            SenVietButton {
                pal: pal
                kind: "secondary"
                text: card._detailsOpen ? "Ẩn chi tiết kỹ thuật" : "Chi tiết kỹ thuật"
                onClicked: {
                    card._detailsOpen = !card._detailsOpen
                    card.detailsRequested()
                }
            }
            SenVietButton {
                pal: pal
                kind: "brand"
                text: "Nhờ SmartAI giải thích"
                onClicked: card.askSmartAIRequested()
            }
        }

        // Vùng chi tiết kỹ thuật (evidence ĐÃ CHE) — chỉ đọc
        Rectangle {
            Layout.fillWidth: true
            visible: card._detailsOpen
            radius: 12
            color: pal.surfaceSubtle
            border.width: 1
            border.color: pal.borderSubtle
            implicitHeight: detailCol.implicitHeight + 20
            ColumnLayout {
                id: detailCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 10
                spacing: 4
                Text {
                    text: "Bằng chứng đã quan sát (đã che bí mật)"
                    color: pal.textSecondary
                    font.pixelSize: 13
                    font.weight: Font.Medium
                }
                Text {
                    Layout.fillWidth: true
                    text: card.evidenceText.length > 0
                          ? card.evidenceText
                          : "Chưa có bằng chứng — mở Chẩn đoán chỉ đọc để thu thập thêm."
                    color: pal.textPrimary
                    font.family: "Noto Sans Mono"
                    font.pixelSize: 14
                    wrapMode: Text.WrapAnywhere
                }
            }
        }

        // Nút mở Lịch sử (cùng correlation_id)
        SenVietButton {
            pal: pal
            kind: "ghost"
            text: (card._historyOpen ? "▾ Lịch sử" : "▸ Lịch sử")
                  + " (" + card.historyModel.length + " sự kiện cùng correlation_id)"
            visible: card.historyModel.length > 0
            onClicked: card._historyOpen = !card._historyOpen
        }

        // Danh sách lịch sử
        ColumnLayout {
            Layout.fillWidth: true
            visible: card._historyOpen && card.historyModel.length > 0
            spacing: 4
            Repeater {
                model: card.historyModel
                delegate: RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        text: modelData.time !== undefined ? modelData.time : ""
                        color: pal.textSecondary
                        font.family: "Noto Sans Mono"
                        font.pixelSize: 13
                    }
                    Text {
                        Layout.fillWidth: true
                        text: modelData.text !== undefined ? modelData.text : ""
                        color: pal.textPrimary
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }
    }
}
