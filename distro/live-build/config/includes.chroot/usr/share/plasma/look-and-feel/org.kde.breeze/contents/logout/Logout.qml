// NaMi — màn hình RỜI PHIÊN (Leave / logout-greeter): Ngủ · Ngủ đông · Khởi
// động lại · Tắt máy · Đăng xuất · Huỷ.
//
// LÝ DO FILE NÀY TỒN TẠI (pilot 12/11/2026 — anh Cường boot máy thật rồi gửi
// ảnh màn hình này): bản gốc của theme "breeze" hiện ra NỀN TÍM breeze mặc
// định + CHỮ TIẾNG ANH (Sleep/Hibernate/Restart/Shut Down/Log Out/Cancel) +
// avatar là logo xoáy Debian → KHÔNG mang nhận diện NaMi, không phải tiếng
// Việt. logout-greeter (plasma-workspace) nạp QML từ gói LookAndFeel ĐANG
// ĐẶT TOÀN CỤC; mặc định (khi [KDE]LookAndFeelPackage trống) = "org.kde.breeze"
// — ẢNH PILOT XÁC NHẬN đúng theme breeze đang chạy. Nên ta GHI ĐÈ trực tiếp
// file Logout.qml của breeze (lớp includes.chroot phủ lên gói Debian) để đổi
// màn này sang nhận diện NaMi mà KHÔNG phải đổi LookAndFeelPackage toàn cục
// (đổi toàn cục = rủi ro reset bố cục/màu desktop — các phiên trước đã CỐ Ý
// tránh, xem metadata.json của org.namios.sen).
//
// NGUỒN API (KHÔNG đoán): các property/signal/enum dưới đây đọc trực tiếp từ
// bản gốc breeze Logout.qml tag v6.3.6 (plasma-workspace, lookandfeel/
// org.kde.breeze/contents/logout/Logout.qml — đúng bản Plasma 6.3.6 Debian 13
// trixie đóng gói). logout-greeter TIÊM các context property: sdtype,
// spdMethods{SuspendState,HibernateState}, maysd, canLogout, softwareUpdate-
// Pending, rebootToFirmwareSetup, rebootToBootLoaderMenu, screenGeometry; và
// KẾT NỐI tới các SIGNAL: logoutRequested/haltRequested/haltUpdateRequested/
// suspendRequested(int)/rebootRequested/rebootRequested2(int)/rebootUpdate-
// Requested/cancelRequested/lockScreenRequested/cancelSoftwareUpdateRequested.
// → GIỮ NGUYÊN TOÀN BỘ tên signal + chữ ký + logic hiện/ẩn nút theo bản gốc;
// CHỈ thay LỚP HÌNH (nền Đông Sơn, avatar bo tròn, nút kiểu thẻ Win11) + chữ
// sang tiếng Việt song ngữ. ShutdownType enum lấy từ import
// org.kde.plasma.private.sessions (giống bản gốc).
//
// AN TOÀN RENDER (đồng bộ với SDDM Main.qml của NaMi): KHÔNG dùng shader/
// GraphicalEffects/blur — chỉ Rectangle/gradient/Image/Text thuần QtQuick +
// Kirigami.Icon (chính breeze dùng trong file này trên production) → chạy
// được trên software renderer (QEMU/TCG không GPU). Chuỗi hiển thị viết SONG
// NGỮ "vi · en" thẳng trong QML (không phụ thuộc catalog gettext — đây chính
// là lý do bản gốc ra tiếng Anh: domain plasma_lookandfeel_org.kde.lookandfeel
// không có bản dịch vi được kích hoạt).
//
// verified_on_host: NO — CHƯA chạy qua logout-greeter/Qt thật. Rủi ro cao nhất
// cần boot thật xác nhận: (1) greeter nạp file này không lỗi import/cú pháp;
// (2) các context property (spdMethods/maysd/canLogout/sdtype) tên đúng như
// bản 6.3.6; (3) Kirigami.Icon hiện icon dưới software rendering; (4) 6 nút
// vừa trên màn hình thấp. Nút/đường dẫn hành động giữ y hệt bản gốc nên LOGIC
// tắt/khởi động/đăng xuất không đổi — chỉ lớp nhìn + chữ đổi.

import QtQuick 2.15
import QtQuick.Layouts 1.15
import org.kde.coreaddons 1.0 as KCoreAddons
import org.kde.kirigami 2.20 as Kirigami
import org.kde.plasma.private.sessions

Item {
    id: root
    height: (typeof screenGeometry !== "undefined") ? screenGeometry.height : 1080
    width: (typeof screenGeometry !== "undefined") ? screenGeometry.width : 1920

    // ---- signal GIỮ NGUYÊN theo bản gốc breeze v6.3.6 (greeter kết nối) ----
    signal logoutRequested()
    signal haltRequested()
    signal haltUpdateRequested()
    signal suspendRequested(int spdMethod)
    signal rebootRequested()
    signal rebootRequested2(int opt)
    signal rebootUpdateRequested()
    signal cancelRequested()
    signal lockScreenRequested()
    signal cancelSoftwareUpdateRequested()

    // greeter có thể set root.backgroundColor — giữ alias để không vỡ (nền
    // thật là gradient phủ lên trên, xem bgBase/bgGradient).
    property alias backgroundColor: bgBase.color

    function sleepRequested() { root.suspendRequested(2); }
    function hibernateRequested() { root.suspendRequested(4); }

    // ---- bảng màu v3 "Đông Sơn" (đồng bộ SDDM theme.conf/Main.qml) ---------
    readonly property color cNavy: "#092D4F"
    readonly property color cSon: "#D64C3E"   // vermilion "action"
    readonly property color cGold: "#DEA93E"  // vàng "signature/focus"
    readonly property color cFg: "#FFF9EF"     // ivory
    readonly property color cFgDim: "#B7C4CF"
    readonly property string brandFont: "Noto Sans"

    // ---- trạng thái từ greeter (guard typeof cho chắc, mặc định an toàn) ---
    readonly property int sdType: (typeof sdtype !== "undefined") ? sdtype : ShutdownType.ShutdownTypeDefault
    readonly property bool showAllOptions: sdType === ShutdownType.ShutdownTypeDefault
    readonly property bool updatePending: (typeof softwareUpdatePending !== "undefined") && softwareUpdatePending
    readonly property bool maySd: (typeof maysd === "undefined") || maysd
    readonly property bool mayLogout: (typeof canLogout === "undefined") || canLogout
    readonly property bool canSuspend: (typeof spdMethods !== "undefined") && spdMethods.SuspendState
    readonly property bool canHibernate: (typeof spdMethods !== "undefined") && spdMethods.HibernateState

    property real timeout: 30
    property real remainingTime: root.timeout

    property var currentAction: {
        switch (root.sdType) {
        case ShutdownType.ShutdownTypeReboot:
            return () => root.updatePending ? root.rebootUpdateRequested() : root.rebootRequested();
        case ShutdownType.ShutdownTypeHalt:
            return () => root.updatePending ? root.haltUpdateRequested() : root.haltRequested();
        default:
            return () => root.logoutRequested();
        }
    }

    KCoreAddons.KUser { id: kuser }

    SessionsModel {
        id: sessionsModel
        includeUnusedSessions: false
    }

    // Escape = Huỷ (giống bản gốc: QQC2.Action shortcut "Escape"). Dùng chuỗi
    // "Escape" (không dùng StandardKey enum) cho chắc chắn khả dụng.
    Shortcut {
        sequence: "Escape"
        onActivated: root.cancelRequested()
    }

    onRemainingTimeChanged: {
        if (remainingTime <= 0) { (currentAction)(); }
    }

    Timer {
        id: countDownTimer
        running: !root.showAllOptions
        repeat: true
        interval: 1000
        onTriggered: root.remainingTime--
    }

    // ---- NỀN: navy Đông Sơn + gradient mực đêm + trống đồng mờ (watermark) --
    Rectangle {
        id: bgBase
        anchors.fill: parent
        color: root.cNavy
    }
    Rectangle {
        id: bgGradient
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(6 / 255, 32 / 255, 58 / 255, 1.0) }
            GradientStop { position: 0.5; color: Qt.rgba(9 / 255, 45 / 255, 79 / 255, 1.0) }
            GradientStop { position: 1.0; color: Qt.rgba(5 / 255, 26 / 255, 47 / 255, 1.0) }
        }
    }
    // Trống đồng Đông Sơn — dấu nước lớn, rất mờ, canh giữa phía trên avatar.
    Image {
        source: "/usr/share/plasma/look-and-feel/org.namios.sen/contents/images/trongdong.svg"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: -root.height * 0.04
        width: Math.min(root.width, root.height) * 0.56
        height: width
        sourceSize.width: 900
        sourceSize.height: 900
        fillMode: Image.PreserveAspectFit
        opacity: 0.06
        smooth: true
        asynchronous: true
        visible: status === Image.Ready
    }

    // Bấm ra vùng nền trống = Huỷ (giống bản gốc).
    MouseArea {
        anchors.fill: parent
        onClicked: root.cancelRequested()
    }

    // ---- badge thương hiệu góc trên-trái (đồng bộ Main.qml) ----------------
    RowLayout {
        anchors { top: parent.top; left: parent.left; margins: 28 }
        spacing: 10
        Image {
            source: "/usr/share/sddm/themes/namios/namios-symbol-badge.svg"
            sourceSize.width: 26
            sourceSize.height: 26
            Layout.preferredWidth: 26
            Layout.preferredHeight: 26
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            visible: status === Image.Ready
        }
        Text {
            text: "NaMi"
            color: root.cFg
            font.family: root.brandFont
            font.pixelSize: 16
            font.weight: Font.DemiBold
            opacity: 0.92
        }
    }

    // ---- KHỐI GIỮA: avatar + tên + đếm ngược + hàng nút --------------------
    ColumnLayout {
        anchors.centerIn: parent
        spacing: 22
        width: Math.min(root.width * 0.9, 900)

        // --- avatar bo tròn (viền vàng) + tên đầy đủ -----------------------
        ColumnLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 12

            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 104
                Layout.preferredHeight: 104
                radius: width / 2
                color: Qt.rgba(1, 1, 1, 0.06)
                border.width: 2
                border.color: Qt.rgba(222 / 255, 169 / 255, 62 / 255, 0.85) // cGold mờ
                clip: true

                Image {
                    id: faceImg
                    anchors.fill: parent
                    source: kuser.faceIconUrl
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                    visible: status === Image.Ready
                }
                // Dự phòng: không có .face.icon hợp lệ → chữ cái đầu của tên,
                // KHÔNG rơi về icon xoáy Debian.
                Text {
                    anchors.centerIn: parent
                    visible: !faceImg.visible
                    text: (kuser.fullName && kuser.fullName.length > 0 ? kuser.fullName : (kuser.loginName ? kuser.loginName : "N")).toUpperCase().charAt(0)
                    color: root.cFg
                    font.family: root.brandFont
                    font.pixelSize: 40
                    font.weight: Font.DemiBold
                }
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: (kuser.fullName && kuser.fullName.length > 0) ? kuser.fullName : (kuser.loginName ? kuser.loginName : "")
                color: root.cFg
                font.family: root.brandFont
                font.pixelSize: 20
                font.weight: Font.DemiBold
            }
        }

        // --- đếm ngược (chỉ khi greeter mở sẵn 1 hành động, sdtype != Default) ---
        Text {
            Layout.alignment: Qt.AlignHCenter
            horizontalAlignment: Text.AlignHCenter
            opacity: countDownTimer.running ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 250 } }
            color: root.cFgDim
            font.family: root.brandFont
            font.pixelSize: 15
            textFormat: Text.PlainText
            text: {
                var n = root.remainingTime;
                switch (root.sdType) {
                case ShutdownType.ShutdownTypeReboot:
                    return "Khởi động lại sau " + n + " giây… · Restarting in " + n + "s";
                case ShutdownType.ShutdownTypeNone:
                    return "Đăng xuất sau " + n + " giây… · Logging out in " + n + "s";
                default:
                    return "Tắt máy sau " + n + " giây… · Shutting down in " + n + "s";
                }
            }
        }

        // --- cảnh báo còn người dùng khác đăng nhập ------------------------
        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.maximumWidth: 560
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            font.italic: true
            color: root.cFgDim
            font.family: root.brandFont
            font.pixelSize: 14
            textFormat: Text.PlainText
            visible: sessionsModel.count > 1 && (root.sdType !== ShutdownType.ShutdownTypeNone || root.showAllOptions)
            text: "Còn người dùng khác đang đăng nhập. Nếu tắt hoặc khởi động lại, họ có thể mất dữ liệu đang làm dở."
        }

        // --- gợi ý vào firmware / boot loader (khi greeter báo) ------------
        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.maximumWidth: 560
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            font.italic: true
            color: root.cFgDim
            font.family: root.brandFont
            font.pixelSize: 14
            textFormat: Text.PlainText
            visible: (typeof rebootToFirmwareSetup !== "undefined") && rebootToFirmwareSetup
            text: "Khi khởi động lại, máy sẽ vào màn hình thiết lập firmware (BIOS/UEFI)."
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.maximumWidth: 560
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            font.italic: true
            color: root.cFgDim
            font.family: root.brandFont
            font.pixelSize: 14
            textFormat: Text.PlainText
            visible: (typeof rebootToBootLoaderMenu !== "undefined") && rebootToBootLoaderMenu
            text: "Khi khởi động lại, máy sẽ vào trình đơn khởi động (boot loader)."
        }

        // --- HÀNG NÚT hành động (thẻ kiểu Windows 11, icon + nhãn) ----------
        RowLayout {
            id: buttonsRow
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 10
            spacing: 16

            LeaveButton {
                id: sleepBtn
                iconName: "system-suspend"
                label: root.showAllOptions ? "Ngủ · Sleep" : "Ngủ ngay · Sleep now"
                visible: root.canSuspend && root.showAllOptions
                onActivated: root.sleepRequested()
            }
            LeaveButton {
                id: hibernateBtn
                iconName: "system-suspend-hibernate"
                label: root.showAllOptions ? "Ngủ đông · Hibernate" : "Ngủ đông ngay · Hibernate now"
                visible: root.canHibernate && root.showAllOptions
                onActivated: root.hibernateRequested()
            }
            LeaveButton {
                id: restartBtn
                iconName: root.updatePending ? "system-reboot-update" : "system-reboot"
                label: root.updatePending ? "Cập nhật & khởi động lại · Update & restart"
                                          : (root.showAllOptions ? "Khởi động lại · Restart" : "Khởi động lại ngay · Restart now")
                visible: root.maySd && (root.sdType === ShutdownType.ShutdownTypeReboot || root.showAllOptions)
                focus: root.sdType === ShutdownType.ShutdownTypeReboot
                onActivated: root.updatePending ? root.rebootUpdateRequested() : root.rebootRequested()
            }
            LeaveButton {
                id: shutdownBtn
                iconName: root.updatePending ? "system-shutdown-update" : "system-shutdown"
                label: root.updatePending ? "Cập nhật & tắt máy · Update & shut down"
                                          : (root.showAllOptions ? "Tắt máy · Shut down" : "Tắt máy ngay · Shut down now")
                accent: true
                visible: root.maySd && (root.sdType === ShutdownType.ShutdownTypeHalt || root.showAllOptions)
                focus: root.sdType === ShutdownType.ShutdownTypeHalt || root.showAllOptions
                onActivated: root.updatePending ? root.haltUpdateRequested() : root.haltRequested()
            }
            LeaveButton {
                id: logoutBtn
                iconName: "system-log-out"
                label: root.showAllOptions ? "Đăng xuất · Log out" : "Đăng xuất ngay · Log out now"
                visible: root.mayLogout && (root.sdType === ShutdownType.ShutdownTypeNone || root.showAllOptions)
                focus: root.sdType === ShutdownType.ShutdownTypeNone
                onActivated: root.logoutRequested()
            }
            LeaveButton {
                id: cancelBtn
                iconName: "dialog-cancel"
                label: "Huỷ · Cancel"
                onActivated: root.cancelRequested()
            }
        }
    }
}
