/*
 * NaMiOS — Gallery.qml
 * Trang preview/gallery dựng cả 3 component tuỳ biến (ErrorCard, ConnectionStepper,
 * AIPlanCard) với dữ liệu mẫu, ở cả nền SÁNG (ngà ấm) và TỐI (navy). Màu nền/chữ
 * ở file này lấy TRỰC TIẾP theo hex (không import SenVietPalette.qml) nên khi đổi
 * bộ nhận diện "Đông Sơn" v3.0 (11/11/2026, THAY "Sen Việt" v2.0) phải sửa tay ở
 * đây — đã đồng bộ: nền sáng ngà (#FFF9EF, trước #F5F2EB), nền tối navy (#092D4F,
 * trước #122A3A). Tương đương §9/§10/§11 của
 * branding/design-system/components-preview.html nhưng bằng QML thật. Chạy thử
 * (khi có Qt/KDE): `qml Gallery.qml` hoặc `qml6 Gallery.qml` trong thư mục này.
 *
 * verified_on_host: NO — sandbox KHÔNG có qml/qmllint; mới kiểm cấu trúc thủ công.
 * Cần boot KDE/Qt thật để xác nhận hiển thị (1366×768 / 1920×1080 / 2560×1440,
 * zoom 100/125/150/200%, bàn phím + screen reader + giảm chuyển động).
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2

QQC2.ApplicationWindow {
    id: win
    visible: true
    width: 1200
    height: 900
    title: "NaMiOS — Thư viện QML \"Đông Sơn\" (ErrorCard / ConnectionStepper / AIPlanCard)"

    // Dữ liệu mẫu dùng chung cho 2 cột
    readonly property var sampleSteps: [
        { title: "Bật bộ thu Wi-Fi",          detail: "Phần cứng nhận tốt.",                 status: "done" },
        { title: "Tìm thấy mạng Nha_Tang_2",  detail: "Tín hiệu mạnh.",                      status: "done" },
        { title: "Xác thực mật khẩu",         detail: "Đã vào mạng.",                        status: "done" },
        { title: "Nhận địa chỉ IP",           detail: "Địa chỉ nội bộ hợp lệ.",              status: "done" },
        { title: "Phân giải DNS",             detail: "Chưa phân giải được tên website.",    status: "failed" },
        { title: "Kết nối Internet",          detail: "Chờ bước phía trên.",                 status: "pending" }
    ]
    readonly property var samplePlan: [
        { title: "Mở hàng đợi in và gỡ việc treo", evidence: "CUPS báo job #42 \"processing\" 4 phút.", confidence: "cao", needsPermission: false },
        { title: "Khởi động lại dịch vụ in",       evidence: "backend không phản hồi IPP.",             confidence: "vừa", needsPermission: true },
        { title: "Kiểm tra cáp/nguồn máy in",      evidence: "Chưa đủ dữ liệu phần cứng.",              confidence: "thấp", needsPermission: false }
    ]
    readonly property var sampleHistory: [
        { time: "14:22:33", text: "Chẩn đoán: máy in phản hồi chậm (read-only)." },
        { time: "14:22:51", text: "Nhờ SmartAI giải thích mã NM-PRN-004." },
        { time: "14:23:10", text: "Thử lại 1 lần: kết quả chưa xác định." }
    ]

    QQC2.ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        RowLayout {
            width: win.width
            spacing: 0

            // ---------- CỘT SÁNG (ngà ấm) ----------
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                color: "#FFF9EF"
                implicitHeight: lightCol.implicitHeight + 48

                ColumnLayout {
                    id: lightCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 24
                    spacing: 20

                    Text { text: "SÁNG — nền ngà ấm"; color: "#52646B"; font.pixelSize: 13; font.bold: true }

                    ErrorCard {
                        Layout.fillWidth: true
                        dark: false
                        familyTitle: "Máy in"
                        title: "Máy in đã kết nối nhưng chưa nhận được trang in"
                        result: "unknown"
                        phaseLabel: "Hàng đợi (queue)"
                        causeCode: "NM-PRN-000"
                        correlationId: "20261109-142233-5312-8471"
                        messageVi: "Đã kiểm tra hàng đợi và phản hồi thiết bị, nhưng chưa đủ bằng chứng để kết luận nguyên nhân."
                        evidenceText: "lpstat -o: job 42 đang giữ; lpstat -p: printer idle; (đã che IP nội bộ + /home/<user>)"
                        confidence: "thấp"
                        historyModel: win.sampleHistory
                    }
                    ConnectionStepper {
                        Layout.fillWidth: true
                        dark: false
                        heading: "Kết nối Wi-Fi — dừng ở bước DNS"
                        steps: win.sampleSteps
                    }
                    AIPlanCard {
                        Layout.fillWidth: true
                        dark: false
                        planSteps: win.samplePlan
                    }
                }
            }

            // ---------- CỘT TỐI (mực đêm) ----------
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                color: "#092D4F"
                implicitHeight: darkCol.implicitHeight + 48

                ColumnLayout {
                    id: darkCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 24
                    spacing: 20

                    Text { text: "TỐI — nền mực đêm"; color: "#C9D3D6"; font.pixelSize: 13; font.bold: true }

                    ErrorCard {
                        Layout.fillWidth: true
                        dark: true
                        familyTitle: "Mạng"
                        title: "Đã vào Wi-Fi nhưng không mở được website"
                        result: "failure"
                        phaseLabel: "Phân giải DNS"
                        causeCode: "NM-NET-007"
                        correlationId: "20261109-142501-6120-3391"
                        messageVi: "Máy đã nhận IP và có đường ra, nhưng phân giải tên miền thất bại."
                        evidenceText: "getent hosts example.com → fail; nmcli dev show: DNS trống (đã che)"
                        confidence: "vừa"
                        historyModel: win.sampleHistory
                    }
                    ConnectionStepper {
                        Layout.fillWidth: true
                        dark: true
                        heading: "Kết nối Wi-Fi — dừng ở bước DNS"
                        steps: win.sampleSteps
                    }
                    AIPlanCard {
                        Layout.fillWidth: true
                        dark: true
                        planSteps: win.samplePlan
                    }
                }
            }
        }
    }
}
