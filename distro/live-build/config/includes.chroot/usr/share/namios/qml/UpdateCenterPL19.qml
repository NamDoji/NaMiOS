/*
 * NaMiOS — UpdateCenterPL19.qml
 * PROTOTYPE màn hình "Cài đặt → Cập nhật & bảo mật → NaMiOS" cho Phụ lục 19
 * (đường đi thông báo → 4 chế độ → preflight → tiến trình → sau khởi động).
 * Nguồn nội dung: docs/update/USER-FLOW-PL19.md + docs/specs/update-error-
 * catalog-pl19.json + docs/specs/UPDATE-CENTER-UI.md (PL15). Tái dùng nguyên
 * component chung đã có trong thư mục này: SenVietPalette, SenVietButton,
 * ErrorCard, ConnectionStepper, AIPlanCard — KHÔNG vẽ lại màu/nét riêng. LƯU Ý
 * TÊN (brand rebase 11/11/2026, "UI polish" 12/11/2026): "SenViet*" chỉ còn
 * là TÊN FILE lịch sử — nội dung màu đã là v3 "Đông Sơn" (navy/gold/
 * vermilion) từ SenVietPalette.qml, KHÔNG còn bảng "Sen Việt" v2 (đỏ son/
 * vàng). KHÔNG đổi tên file ở polish này: nhiều tài liệu ngoài phạm vi sửa
 * của task này (docs/specs/QML-COMPONENTS.md, docs/release/
 * BRANDING-MAP-OLD-NEW.md, docs/release/QA-UIUX-2026.11.md) tham chiếu đúng
 * 2 tên file "SenVietPalette.qml"/"SenVietButton.qml" — đổi tên sẽ làm các
 * tài liệu đó trỏ sai mà không có quyền sửa lại chúng trong phạm vi task
 * này; xem ghi chú đầy đủ ở đầu SenVietPalette.qml/SenVietButton.qml.
 *
 * ĐÂY LÀ PROTOTYPE/SPEC — CHƯA NỐI VÀO apt/Update Service/bootloader thật.
 * Mọi phiên bản/dung lượng/%/thời gian trong file này là DỮ LIỆU MẪU
 * (property var tĩnh), không phải bản phát hành có thật (xem §1.1 của
 * USER-FLOW-PL19.md — "KHÔNG đưa số phiên bản/dung lượng giả vào sản phẩm
 * thật"; ở đây chỉ là minh hoạ UI).
 *
 * Bất biến đã tôn trọng ở lớp UI (không được phá khi chỉnh sửa):
 *   - Không có công tắc "Tự động tất cả" bao gồm firmware (§2).
 *   - "Cài ngay" / "Khởi động và cập nhật" không tự coi là "xong"; nút
 *     "Khởi động và cập nhật" CHỈ enabled khi mọi mục preflight Đạt (§4).
 *   - ErrorCard cho UPD-003 KHÔNG có nút "Bỏ qua kiểm tra" — component gốc
 *     chỉ có Thử lại (= thử tải+xác minh lại, không phải bỏ xác minh) /
 *     Chi tiết kỹ thuật / Nhờ nAI giải thích.
 *   - AIPlanCard minh hoạ nAI giải thích UPD-003 không có bước nào gợi ý
 *     bỏ chữ ký/đổi nguồn — xem planSteps bên dưới.
 *   - Thanh tiến trình "Đang tải" có số % thật kèm track; "Đang xác minh" ở
 *     biến thể indeterminate (không bịa % để tránh đứng ở 99% vô hạn).
 *   - prefers-reduced-motion: bật switch "Giảm chuyển động" tắt animation
 *     của thanh indeterminate ngay, không cần khởi động lại.
 *
 * Chạy thử (khi có Qt/KDE): `qml UpdateCenterPL19.qml` hoặc
 * `qml6 UpdateCenterPL19.qml` trong thư mục này.
 *
 * verified_on_host: NO — sandbox KHÔNG có qml/qmllint; mới kiểm cấu trúc
 * thủ công, đối chiếu từng property/signal với 02_HOP_DONG_KY_THUAT.md và
 * UPDATE-CENTER-UI.md. Cần boot KDE/Qt thật để xác nhận hiển thị + chụp ảnh
 * (1366×768 / 1920×1080 / 2560×1440, zoom 100/125/150/200%, bàn phím + screen
 * reader + giảm chuyển động) trước khi coi là U15-D "UI Qt/QML live".
 */
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.ApplicationWindow {
    id: root
    visible: true
    width: 1040
    height: 980
    title: "NaMiOS — Cài đặt ▸ Cập nhật & bảo mật ▸ NaMiOS (PL19, prototype)"

    // ---- Trạng thái demo (KHÔNG nối Update Service thật) ----
    property bool dark: false
    property bool reducedMotion: false
    property int selectedModeIndex: 1        // mặc định pilot: auto_download_ask_install
    property bool pauseEnabled: false
    property string pauseUntilDate: "20/12/2026"
    property bool meteredLimit: true
    property bool chargeOnly: false
    property string quietHoursText: "22:00 – 07:00"

    SenVietPalette { id: pal; dark: root.dark }

    // ---- Dữ liệu mẫu: 4 chế độ (UPDATE-CENTER-UI.md §1) ----
    readonly property var modes: [
        {
            key: "notify",
            name: "Thông báo, tôi tự quyết định",
            machineDoes: "Kiểm tra theo lịch; hiện bản mới + mức khẩn + dung lượng; có nút \"Kiểm tra ngay\". Không tự tải.",
            userNeeds: "Bấm Tải/Cài khi muốn; chọn giờ khởi động lại.",
            restart: "Chỉ khi bạn bấm Cài",
            isDefault: false
        },
        {
            key: "auto_download_ask_install",
            name: "Tự tải, hỏi trước khi cài",
            machineDoes: "Kiểm tra, tự tải khi mạng/ổ đĩa đủ điều kiện, tự xác minh chữ ký/hash. Chưa cài gì.",
            userNeeds: "Chọn Cài ngay hoặc đặt lịch cài; trả lời khi được hỏi trước lúc cài.",
            restart: "Hỏi trước khi cài",
            isDefault: true
        },
        {
            key: "auto_install_safe",
            name: "Tự cài bản an toàn",
            machineDoes: "App + bản vá không cần reboot tự cài sau khi xác thực; OS được staged (chưa chạm hệ thống đang dùng). Firmware không tự cài.",
            userNeeds: "Chọn hoặc chấp nhận lịch khởi động lại cho phần OS.",
            restart: "Có lịch/nhắc cho OS",
            isDefault: false
        },
        {
            key: "auto_scheduled",
            name: "Tự động theo lịch của tôi",
            machineDoes: "Kiểm, tải, cài OS trong đúng cửa sổ giờ đã chọn; tôn trọng giờ yên tĩnh/mạng tính phí/pin.",
            userNeeds: "Một lần: chọn giờ yên tĩnh, mạng tính phí, quyền hoãn khi còn việc chưa lưu.",
            restart: "Chỉ trong cửa sổ đã chọn",
            isDefault: false
        }
    ]

    // ---- Dữ liệu mẫu: checklist trước khi cài (§4) ----
    readonly property var preflightItems: [
        { label: "Dung lượng", detail: "Bản tải + bản staged + vùng rollback — đủ chỗ.", status: "pass", actionLabel: "Xem dung lượng" },
        { label: "Pin / nguồn điện", detail: "Đang cắm sạc, pin 81%.", status: "pass", actionLabel: "Hướng dẫn nguồn" },
        { label: "Mã hóa ổ đĩa", detail: "Ổ đã mở khoá đúng cách cho lần khởi động tiếp theo.", status: "pass", actionLabel: "Xem hướng dẫn mở khoá" },
        { label: "Bootloader / dual-boot", detail: "Đã xác định boot entry an toàn; không chạm hệ điều hành khác.", status: "pass", actionLabel: "Xem chi tiết dual-boot" },
        { label: "Mạng", detail: "Đã tải xong và xác minh hash qua Wi-Fi nhà.", status: "pass", actionLabel: "Xem kết nối" },
        { label: "Ứng dụng / tài liệu chưa lưu", detail: "nDoc đang mở 1 tài liệu chưa lưu (\"Báo cáo tháng 11.odt\").", status: "fail", actionLabel: "Xem ứng dụng cần lưu" },
        { label: "Migration cần backup", detail: "Bản này không đổi cách lưu dữ liệu ứng dụng.", status: "pass", actionLabel: "Sao lưu ngay" }
    ]
    readonly property bool allPreflightPass: preflightItems.every(function (it) { return it.status === "pass" })
    function failedPreflightLabels() {
        var names = []
        for (var i = 0; i < preflightItems.length; i++) {
            if (preflightItems[i].status !== "pass") names.push(preflightItems[i].label)
        }
        return names.join(", ")
    }

    // ---- Dữ liệu mẫu: chuỗi trạng thái UX (§5.1, ConnectionStepper tái dùng) ----
    readonly property var stateSteps: [
        { title: "Đang kiểm tra", detail: "Đã xác thực metadata, đúng kênh/arch/model.", status: "done" },
        { title: "Có bản mới", detail: "NaMiOS 1.1 — khuyến nghị, cần khởi động lại.", status: "done" },
        { title: "Đang tải", detail: "68% · còn khoảng 3 phút (tốc độ đo được gần đây).", status: "active" },
        { title: "Đã xác thực", detail: "Chờ tải xong rồi kiểm chữ ký/hash.", status: "pending" },
        { title: "Sẵn sàng cài / Đang chuẩn bị", detail: "Staged — tệp của bạn chưa đổi.", status: "pending" },
        { title: "Cần khởi động lại", detail: "Sẽ hỏi giờ khởi động lại khi staged xong.", status: "pending" },
        { title: "Đang kiểm tra sau khởi động", detail: "Kernel/đăng nhập/ổ dữ liệu/mạng/UI/dịch vụ update.", status: "pending" },
        { title: "Hoàn tất", detail: "Chỉ tới được từ kiểm tra sau khởi động khi đạt — không có đường tắt.", status: "pending" }
    ]

    // ---- Dữ liệu mẫu: lịch sử (ErrorCard.historyModel) ----
    readonly property var historyEntries: [
        { time: "09/11/2026 08:02", text: "NaMiOS 1.1 — boot health đạt (COMMITTED). Không có lỗi." },
        { time: "02/10/2026 07:40", text: "NaMiOS 1.1-rc — boot health KHÔNG đạt (kernel). Đã tự khôi phục về 1.0 (UPD-008)." },
        { time: "02/10/2026 07:12", text: "Đã xác thực chữ ký + hash, chuyển sang Staged." },
        { time: "01/10/2026 21:05", text: "Tự tải xong 1.1-rc qua Wi-Fi nhà, chưa cài gì (auto_download_ask_install)." }
    ]

    // ---- AIPlanCard: nAI giải thích UPD-003 (không có bước bỏ chữ ký) ----
    readonly property var smartAiPlanForUpd003: [
        { title: "Xem chi tiết kỹ thuật đã che bí mật", evidence: "signature_status=failed ở bước verify.", confidence: "cao", needsPermission: false },
        { title: "Báo sự cố cho đội vận hành NaMiOS", evidence: "Có correlation_id để tra cứu.", confidence: "cao", needsPermission: false },
        { title: "Chờ bản đã ký lại rồi kiểm tra lại", evidence: "Chưa có bản ký lại trong manifest hiện tại.", confidence: "vừa", needsPermission: false }
    ]

    function urgencyColor(level) {
        switch (level) {
        case "khẩn cấp": return pal.statusError
        case "khuyến nghị": return pal.statusWarning
        default: return pal.statusInfo // "thường"
        }
    }

    color: pal.surfaceBase

    QQC2.ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        ColumnLayout {
            id: page
            width: root.width
            x: 0
            spacing: 28

            // ================= Thanh tiêu đề + công cụ xem thử =================
            RowLayout {
                Layout.fillWidth: true
                Layout.margins: 28
                spacing: 16

                ColumnLayout {
                    spacing: 2
                    Text {
                        text: "Cài đặt ▸ Cập nhật & bảo mật ▸ NaMiOS"
                        color: pal.textSecondary
                        font.pixelSize: 13
                    }
                    Text {
                        text: "Cập nhật & bảo mật — NaMiOS"
                        color: pal.textPrimary
                        font.pixelSize: 28
                        font.weight: Font.DemiBold
                    }
                    Text {
                        text: "PROTOTYPE — dữ liệu mẫu, chưa nối Update Service thật (xem docs/update/USER-FLOW-PL19.md)."
                        color: pal.statusWarning
                        font.pixelSize: 13
                        font.italic: true
                    }
                }
                Item { Layout.fillWidth: true }
                SenVietButton { pal: pal; kind: "secondary"; text: "Kiểm tra ngay" }
                ColumnLayout {
                    spacing: 4
                    RowLayout {
                        spacing: 8
                        QQC2.Switch { id: darkSwitch; checked: root.dark; onToggled: root.dark = checked }
                        Text { text: "Giao diện tối"; color: pal.textSecondary; font.pixelSize: 13 }
                    }
                    RowLayout {
                        spacing: 8
                        QQC2.Switch { id: motionSwitch; checked: root.reducedMotion; onToggled: root.reducedMotion = checked }
                        Text { text: "Giảm chuyển động"; color: pal.textSecondary; font.pixelSize: 13 }
                    }
                }
            }

            // ================= 1. Thông báo có bản mới =================
            Kirigami.ShadowedRectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 28
                Layout.rightMargin: 28
                implicitHeight: notifyCol.implicitHeight + 32
                radius: 16
                color: pal.surfaceCard
                border.width: 1
                border.color: pal.borderSubtle
                shadow.size: 16
                shadow.yOffset: 4
                shadow.color: Qt.rgba(0.07, 0.16, 0.22, root.dark ? 0.35 : 0.12)

                ColumnLayout {
                    id: notifyCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 16
                    spacing: 10

                    Text { text: "1. Thông báo có bản mới"; color: pal.textSecondary; font.pixelSize: 13; font.weight: Font.Medium }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text {
                            Layout.fillWidth: true
                            text: "NaMiOS 1.1 đã sẵn sàng."
                            color: pal.textPrimary
                            font.pixelSize: 20
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                        Rectangle {
                            radius: 999
                            color: pal.surfaceSubtle
                            border.width: 1
                            border.color: root.urgencyColor("khuyến nghị")
                            implicitHeight: 26
                            implicitWidth: urgText.implicitWidth + 20
                            Text {
                                id: urgText
                                anchors.centerIn: parent
                                text: "Mức: Khuyến nghị"
                                color: root.urgencyColor("khuyến nghị")
                                font.pixelSize: 13
                                font.weight: Font.Medium
                            }
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Bản này sửa lỗi Wi‑Fi và tăng độ an toàn."
                        color: pal.textPrimary
                        font.pixelSize: 15
                        wrapMode: Text.WordWrap
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        rowSpacing: 4
                        columnSpacing: 24
                        Text { text: "Dung lượng:"; color: pal.textSecondary; font.pixelSize: 13 }
                        Text { text: "1,2 GB (đo từ manifest — không ước lượng)"; color: pal.textPrimary; font.pixelSize: 13 }
                        Text { text: "Cần khởi động lại:"; color: pal.textSecondary; font.pixelSize: 13 }
                        Text { text: "Có — để hoàn tất"; color: pal.textPrimary; font.pixelSize: 13 }
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        SenVietButton { pal: pal; kind: "secondary"; text: "Xem thay đổi" }
                        SenVietButton { pal: pal; kind: "primary"; text: "Cài tối nay" }
                        SenVietButton { pal: pal; kind: "ghost"; text: "Để sau" }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Dữ liệu minh hoạ từ manifest mẫu — không phải bản phát hành thật. \"Để sau\" lưu thông báo, không hỏi lại mỗi lần quét nền; bản vá khẩn vẫn báo dù đã Tạm dừng."
                        color: pal.textSecondary
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // ================= 2. Bốn chế độ cập nhật =================
            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 28
                Layout.rightMargin: 28
                spacing: 12

                Text { text: "2. Bốn chế độ cập nhật"; color: pal.textPrimary; font.pixelSize: 22; font.weight: Font.DemiBold }

                Repeater {
                    model: root.modes
                    delegate: Kirigami.ShadowedRectangle {
                        id: modeCard
                        required property int index
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: modeCol.implicitHeight + 28
                        radius: 16
                        color: pal.surfaceCard
                        border.width: (root.selectedModeIndex === modeCard.index) ? 2 : 1
                        border.color: (root.selectedModeIndex === modeCard.index) ? pal.actionPrimary : pal.borderSubtle
                        shadow.size: 12
                        shadow.yOffset: 3
                        shadow.color: Qt.rgba(0.07, 0.16, 0.22, root.dark ? 0.30 : 0.10)

                        RowLayout {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 14
                            spacing: 14

                            QQC2.RadioButton {
                                Layout.alignment: Qt.AlignTop
                                checked: root.selectedModeIndex === modeCard.index
                                onToggled: if (checked) root.selectedModeIndex = modeCard.index
                                Accessible.name: modeCard.modelData.name
                            }

                            ColumnLayout {
                                id: modeCol
                                Layout.fillWidth: true
                                spacing: 4

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Text {
                                        Layout.fillWidth: true
                                        text: modeCard.modelData.name
                                        color: pal.textPrimary
                                        font.pixelSize: 16
                                        font.weight: Font.DemiBold
                                        wrapMode: Text.WordWrap
                                    }
                                    Rectangle {
                                        visible: modeCard.modelData.isDefault === true
                                        radius: 999
                                        color: pal.brandRed
                                        implicitHeight: 22
                                        implicitWidth: defText.implicitWidth + 16
                                        Text {
                                            id: defText
                                            anchors.centerIn: parent
                                            text: "Mặc định pilot"
                                            color: "#FFFFFF"
                                            font.pixelSize: 11
                                            font.weight: Font.Medium
                                        }
                                    }
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: "Máy tự làm gì: " + modeCard.modelData.machineDoes
                                    color: pal.textPrimary
                                    font.pixelSize: 14
                                    wrapMode: Text.WordWrap
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: "Cần bạn làm gì: " + modeCard.modelData.userNeeds
                                    color: pal.textSecondary
                                    font.pixelSize: 14
                                    wrapMode: Text.WordWrap
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: "Khởi động lại: " + modeCard.modelData.restart
                                    color: pal.textSecondary
                                    font.pixelSize: 13
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "Không có công tắc \"Tự động tất cả\" bao gồm firmware — firmware luôn có xác nhận riêng (model + pin/nguồn + chữ ký). nOffice/nPDF/nAI/driver có vòng đời cập nhật riêng, hiển thị ở tab khác cùng màn hình cha."
                    color: pal.statusWarning
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }

                // Banner "thiết bị do tổ chức quản lý" (minh hoạ)
                Kirigami.ShadowedRectangle {
                    Layout.fillWidth: true
                    implicitHeight: orgCol.implicitHeight + 24
                    radius: 12
                    color: pal.surfaceSubtle
                    border.width: 1
                    border.color: pal.borderSubtle
                    RowLayout {
                        id: orgCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 12
                        Text {
                            Layout.fillWidth: true
                            text: "Thiết bị do tổ chức quản lý (ví dụ minh hoạ) — Phòng CNTT Trường ABC đặt lịch cập nhật; chính sách IT có thể đè chế độ cá nhân khi xung đột."
                            color: pal.textSecondary
                            font.pixelSize: 13
                            wrapMode: Text.WordWrap
                        }
                        SenVietButton { pal: pal; kind: "ghost"; text: "Liên hệ IT" }
                    }
                }
            }

            // ================= 3. Tuỳ chọn cùng màn hình =================
            Kirigami.ShadowedRectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 28
                Layout.rightMargin: 28
                implicitHeight: optCol.implicitHeight + 32
                radius: 16
                color: pal.surfaceCard
                border.width: 1
                border.color: pal.borderSubtle

                ColumnLayout {
                    id: optCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 16
                    spacing: 14

                    Text { text: "3. Tuỳ chọn cùng màn hình"; color: pal.textPrimary; font.pixelSize: 22; font.weight: Font.DemiBold }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        QQC2.Switch { checked: root.pauseEnabled; onToggled: root.pauseEnabled = checked }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Text { text: "Tạm dừng đến ngày…"; color: pal.textPrimary; font.pixelSize: 14; font.weight: Font.Medium }
                            Text {
                                visible: root.pauseEnabled
                                text: "Tạm dừng tới " + root.pauseUntilDate + " — bản vá khẩn vẫn được báo dù đang tạm dừng."
                                color: pal.textSecondary
                                font.pixelSize: 13
                                wrapMode: Text.WordWrap
                            }
                        }
                        SenVietButton { visible: root.pauseEnabled; pal: pal; kind: "secondary"; text: "Đổi ngày" }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        QQC2.Switch { checked: root.meteredLimit; onToggled: root.meteredLimit = checked }
                        Text { Layout.fillWidth: true; text: "Giới hạn tải trên mạng tính phí (metered)"; color: pal.textPrimary; font.pixelSize: 14 }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        QQC2.Switch { checked: root.chargeOnly; onToggled: root.chargeOnly = checked }
                        Text { Layout.fillWidth: true; text: "Chỉ tải khi cắm sạc"; color: pal.textPrimary; font.pixelSize: 14 }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Text { text: "Giờ yên tĩnh:"; color: pal.textPrimary; font.pixelSize: 14; font.weight: Font.Medium }
                        Text { Layout.fillWidth: true; text: root.quietHoursText + " — chỉ chặn khởi động lại tự động, không chặn tải/xác minh ngầm"; color: pal.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap }
                        SenVietButton { pal: pal; kind: "ghost"; text: "Đổi giờ" }
                    }

                    SenVietButton { pal: pal; kind: "secondary"; text: "Kiểm tra lịch sử (xem mục 6 bên dưới)" }
                }
            }

            // ================= 4. Trước khi cài — checklist =================
            Kirigami.ShadowedRectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 28
                Layout.rightMargin: 28
                implicitHeight: pfCol.implicitHeight + 32
                radius: 16
                color: pal.surfaceCard
                border.width: 1
                border.color: pal.borderSubtle

                ColumnLayout {
                    id: pfCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 16
                    spacing: 12

                    Text { text: "4. Trước khi cài"; color: pal.textPrimary; font.pixelSize: 22; font.weight: Font.DemiBold }
                    Text {
                        Layout.fillWidth: true
                        text: "Tệp cá nhân không bị xóa bởi thao tác nâng cấp OS; một số ứng dụng có thể cần chuyển dữ liệu. NaMiOS sẽ kiểm tra bản sao lưu/khả năng khôi phục."
                        color: pal.textPrimary
                        font.pixelSize: 14
                        wrapMode: Text.WordWrap
                    }

                    Repeater {
                        model: root.preflightItems
                        delegate: RowLayout {
                            id: pfRow
                            required property int index
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: 12

                            Rectangle {
                                Layout.alignment: Qt.AlignTop
                                radius: 999
                                color: pal.surfaceSubtle
                                border.width: 1
                                border.color: pfRow.modelData.status === "pass" ? pal.statusSuccess : pal.statusError
                                implicitHeight: 26
                                implicitWidth: pfChip.implicitWidth + 20
                                Text {
                                    id: pfChip
                                    anchors.centerIn: parent
                                    text: (pfRow.modelData.status === "pass" ? "✓ Đạt" : "! Chưa đạt")
                                    color: pfRow.modelData.status === "pass" ? pal.statusSuccess : pal.statusError
                                    font.pixelSize: 12
                                    font.weight: Font.Medium
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Text { text: pfRow.modelData.label; color: pal.textPrimary; font.pixelSize: 14; font.weight: Font.Medium }
                                Text { Layout.fillWidth: true; text: pfRow.modelData.detail; color: pal.textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap }
                            }

                            SenVietButton {
                                visible: pfRow.modelData.status !== "pass"
                                pal: pal
                                kind: "secondary"
                                text: pfRow.modelData.actionLabel
                            }
                        }
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        SenVietButton { pal: pal; kind: "primary"; text: "Cài ngay" }
                        SenVietButton { pal: pal; kind: "secondary"; text: "Cài tối nay" }
                        SenVietButton { pal: pal; kind: "ghost"; text: "Để sau" }
                        SenVietButton {
                            pal: pal
                            kind: root.allPreflightPass ? "brand" : "ghost"
                            enabled: root.allPreflightPass
                            text: "Khởi động và cập nhật"
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: root.allPreflightPass
                              ? "Tất cả mục preflight đều Đạt — có thể khởi động và cập nhật."
                              : "Bị khoá vì chưa đạt: " + root.failedPreflightLabels() + ". \"Cài ngay\" vẫn tải/xác minh/chuẩn bị được; chỉ bước khởi động lại thật bị khoá tới khi mục này Đạt."
                        color: root.allPreflightPass ? pal.statusSuccess : pal.statusWarning
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Lưu ý: \"Cài ngay\" chỉ tải/xác minh/chuẩn bị rồi đề nghị khởi động lại — CHƯA gọi là \"cập nhật xong\". Trạng thái chỉ thành Hoàn tất sau khi qua kiểm tra sau khởi động."
                        color: pal.textSecondary
                        font.pixelSize: 12
                        font.italic: true
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // ================= 5. Tiến trình & trạng thái =================
            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 28
                Layout.rightMargin: 28
                spacing: 14

                Text { text: "5. Trong quá trình nâng cấp — trạng thái & tiến trình"; color: pal.textPrimary; font.pixelSize: 22; font.weight: Font.DemiBold }

                ConnectionStepper {
                    Layout.fillWidth: true
                    dark: root.dark
                    heading: "Trạng thái cập nhật hiện tại (minh hoạ — đang ở bước \"Đang tải\")"
                    steps: root.stateSteps
                }

                Kirigami.ShadowedRectangle {
                    Layout.fillWidth: true
                    implicitHeight: progCol.implicitHeight + 28
                    radius: 16
                    color: pal.surfaceCard
                    border.width: 1
                    border.color: pal.borderSubtle

                    ColumnLayout {
                        id: progCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 16

                        // Thanh tiến trình CÓ số % thật (đang tải)
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            RowLayout {
                                Layout.fillWidth: true
                                Text { Layout.fillWidth: true; text: "Đang tải NaMiOS 1.1"; color: pal.textPrimary; font.pixelSize: 14 }
                                Text { text: "68%"; color: pal.textSecondary; font.pixelSize: 13; font.family: "Noto Sans Mono" }
                            }
                            Rectangle {
                                id: dlTrack
                                Layout.fillWidth: true
                                implicitHeight: 8
                                radius: 4
                                color: pal.surfaceSubtle
                                border.width: 1
                                border.color: pal.borderSubtle
                                Rectangle {
                                    width: parent.width * 0.68
                                    height: parent.height
                                    radius: 4
                                    color: pal.actionPrimary
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                SenVietButton { pal: pal; kind: "ghost"; text: "Tạm dừng tải" }
                                Item { Layout.fillWidth: true }
                                Text { text: "Phần đã tải được giữ để resume, không tải lại từ đầu."; color: pal.textSecondary; font.pixelSize: 12 }
                            }
                        }

                        // Thanh tiến trình INDETERMINATE (đang xác minh — chưa có % thật)
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            RowLayout {
                                Layout.fillWidth: true
                                Text { Layout.fillWidth: true; text: "Đang kiểm tra sau khởi động"; color: pal.textPrimary; font.pixelSize: 14 }
                                Text { text: "—"; color: pal.textSecondary; font.pixelSize: 13; font.family: "Noto Sans Mono" }
                            }
                            Rectangle {
                                id: indetTrack
                                Layout.fillWidth: true
                                implicitHeight: 8
                                radius: 4
                                color: pal.surfaceSubtle
                                border.width: 1
                                border.color: pal.borderSubtle
                                clip: true

                                // Chế độ chuyển động thường: dải chạy lặp vô hạn (chỉ-thị không xác định).
                                Rectangle {
                                    id: indetBar
                                    visible: !root.reducedMotion
                                    width: indetTrack.width * 0.35
                                    height: parent.height
                                    radius: 4
                                    color: pal.actionPrimary
                                    SequentialAnimation on x {
                                        running: !root.reducedMotion
                                        loops: Animation.Infinite
                                        NumberAnimation { from: -indetBar.width; to: indetTrack.width; duration: 1300; easing.type: Easing.InOutQuad }
                                    }
                                }

                                // prefers-reduced-motion: KHÔNG animation — lấp tĩnh, đổi trạng thái tức thì.
                                Rectangle {
                                    visible: root.reducedMotion
                                    anchors.fill: parent
                                    radius: 4
                                    color: pal.surfaceSubtle
                                    opacity: 0.9
                                }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: "Không bịa % khi chưa đo được — hiển thị chạy không-xác-định thay vì đứng ở 99% vô hạn. Giảm chuyển động thì tắt animation, giữ trạng thái tĩnh."
                                color: pal.textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Text {
                                    Layout.fillWidth: true
                                    text: "Không có nút Hủy trong pha chuyển hệ điều hành không an toàn (BOOTING_NEW → HEALTH_CHECK)."
                                    color: pal.statusWarning
                                    font.pixelSize: 12
                                    font.weight: Font.Medium
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }
            }

            // ================= Ví dụ lỗi: UPD-003 (sai chữ ký) =================
            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 28
                Layout.rightMargin: 28
                spacing: 14

                Text { text: "Ví dụ ErrorCard — UPD-003 (sai chữ ký/hash, KHÔNG có nút bỏ qua)"; color: pal.textPrimary; font.pixelSize: 20; font.weight: Font.DemiBold }

                ErrorCard {
                    Layout.fillWidth: true
                    dark: root.dark
                    familyTitle: "Cập nhật NaMiOS"
                    title: "Bản cập nhật không vượt qua kiểm tra bảo mật"
                    result: "failure"
                    phaseLabel: "Xác minh chữ ký (verify)"
                    causeCode: "UPD-003"
                    correlationId: "20261110-091204-7731-2048"
                    messageVi: "NaMiOS đã chặn cài đặt; máy vẫn dùng phiên bản hiện tại. KHÔNG có tuỳ chọn bỏ qua kiểm tra. \"Thử lại\" chỉ tải+xác minh lại từ đầu, không bỏ bước xác minh."
                    evidenceText: "signature_status=failed; khoá ký không khớp danh sách tin cậy (đã che chi tiết nội bộ)."
                    historyModel: []
                }

                AIPlanCard {
                    Layout.fillWidth: true
                    dark: root.dark
                    headline: "nAI giải thích mã UPD-003"
                    safetyNote: "Chỉ đọc mã lỗi + metadata đã lọc · chưa đổi gì"
                    disclaimer: "nAI không tự ý đổi chính sách cập nhật (user_policy), trust root, hoặc bỏ xác minh chữ ký. Đây chỉ là giải thích + đề xuất; mọi hành động cần bạn tự bấm."
                    planSteps: root.smartAiPlanForUpd003
                }
            }

            // ================= 6. Sau khởi động — Lịch sử =================
            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 28
                Layout.rightMargin: 28
                Layout.bottomMargin: 28
                spacing: 14

                Text { text: "6. Sau khởi động — trạng thái hiện tại & lịch sử"; color: pal.textPrimary; font.pixelSize: 22; font.weight: Font.DemiBold }

                Kirigami.ShadowedRectangle {
                    Layout.fillWidth: true
                    implicitHeight: histCol.implicitHeight + 28
                    radius: 16
                    color: pal.surfaceCard
                    border.width: 1
                    border.color: pal.borderSubtle

                    GridLayout {
                        id: histCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        columns: 2
                        rowSpacing: 6
                        columnSpacing: 24
                        Text { text: "Phiên bản thực đang chạy:"; color: pal.textSecondary; font.pixelSize: 13 }
                        Text { text: "NaMiOS 1.1 (đọc từ hệ thống đang chạy)"; color: pal.textPrimary; font.pixelSize: 13 }
                        Text { text: "Ngày cập nhật:"; color: pal.textSecondary; font.pixelSize: 13 }
                        Text { text: "09/11/2026 08:02"; color: pal.textPrimary; font.pixelSize: 13 }
                        Text { text: "Trạng thái kiểm tra:"; color: pal.textSecondary; font.pixelSize: 13 }
                        Text { text: "Đã xác minh — COMMITTED"; color: pal.statusSuccess; font.pixelSize: 13; font.weight: Font.Medium }
                    }
                }

                Text { text: "Nếu bản mới lỗi (minh hoạ ErrorCard UPD-008, kèm Xem lịch sử):"; color: pal.textPrimary; font.pixelSize: 15; font.weight: Font.Medium }

                ErrorCard {
                    Layout.fillWidth: true
                    dark: root.dark
                    familyTitle: "Khởi động lại sau cập nhật"
                    title: "Bản mới không khởi động ổn định — đã khôi phục"
                    result: "failure"
                    phaseLabel: "Kiểm tra sau khởi động (health_check)"
                    causeCode: "UPD-008"
                    correlationId: "20261102-071205-4471-9033"
                    messageVi: "NaMiOS đã quay về phiên bản trước. Tệp cá nhân còn nguyên theo kiểm tra hiện có; xem báo cáo để xác nhận ứng dụng/dữ liệu quan trọng. Không hứa dữ liệu chắc chắn nguyên vẹn nếu chưa kiểm."
                    evidenceText: "health_check: kernel OK; login OK; desktop shell TIMEOUT sau 90s (đã che log nội bộ)."
                    historyModel: root.historyEntries
                }

                Text {
                    Layout.fillWidth: true
                    text: "Nếu tự khôi phục cũng không thành công (RECOVERY_REQUIRED): có đường vào recovery từ boot menu và USB cứu hộ ĐÃ KÝ. Xem tình huống PL19-SIT-07 trong docs/specs/update-error-catalog-pl19.json."
                    color: pal.textSecondary
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
