// NaMiOS — man hinh dang nhap SDDM, theme "namios" (Theme-Id=namios).
//
// NGUON API: context properties duoi day (config/sddm/userModel/sessionModel/
// screenModel) KHONG phai doan — doc truc tiep tu ma nguon goc
// github.com/KDE/plasma-desktop tag v6.3.6 (duong dan sddm-theme/Main.qml,
// Login.qml, dummydata/{sddm,userModel,sessionModel}.qml), dung dung ban
// Plasma 6.3.6 ma Debian 13 trixie dong goi (xem ghi chu goi trong
// includes.chroot/usr/share/sddm/themes/breeze/theme.conf.user). Cu the:
//   - sddm: login(name,password,sessionIndex), suspend()/reboot()/powerOff(),
//     canSuspend/canReboot/canPowerOff, signal loginSucceeded()/loginFailed().
//   - userModel: role name/realName/icon, property lastIndex/lastUser.
//   - sessionModel: role name, property lastIndex.
//   - screenModel: role geometry (x,y,width,height) — Repeater ve nen tren
//     MOI man hinh (multi-monitor), giong cau truc breeze.
//
// KHAC VOI theme "breeze" that (KDE goc) MOT CACH CHU DICH:
//   - KHONG dung Qt5Compat.GraphicalEffects (DropShadow/blur) — breeze dung
//     DropShadow co dieu kien "visible: !softwareRendering" de tranh loi da
//     biet duoi software rendering (bugs.kde.org/398317), nhung theme nay BO
//     HOAN TOAN hieu ung co shader ngay tu dau (khong chi "an di luc can")
//     -> giam mot lop rui ro GL nua duoi QEMU/TCG khong GPU (xem hook
//     0400-qemu-desktop-autologin.hook.chroot — ly do du an da tung bo QML
//     theme rieng, ghi trong theme.conf.user cua breeze). Thiet ke phang
//     ("kinh mo" bang do mo alpha, khong bang blur GPU) cung dung chinh
//     ngon ngu voi plasma/desktoptheme/NaMiOS-Sen da co san.
//   - KHONG dung Kirigami/PlasmaComponents/PlasmaExtras — tu ve Rectangle/
//     TextInput/Text thuan QtQuick, giam phu thuoc module. Rieng
//     "org.kde.plasma.private.keyboardindicator" (bao Caps Lock) la ngoai le
//     CO Y: day la module KF6 nho, KHONG render GL, VA da duoc chung minh
//     chay duoc trong dung tien trinh sddm-greeter nay (breeze SDDM theme
//     dung chinh module nay trong production tren cung ban Plasma).
//   - Moi chuoi hien thi viet SONG NGU tinh "vi · en" ngay trong QML (theme
//     nay KHONG dang ky TranslationsDirectory/gettext — xem metadata.desktop)
//     de dam bao "VN/EN friendly" khong phu thuoc catalog dich rieng.
//
// MAU/FONT: doc tu includes.chroot/usr/share/sddm/themes/namios/theme.conf
// (config.*) voi fallback cung ngay trong QML phong khi key thieu; nguon mau
// GOC trong theme.conf hien la v3 "Dong Son" (xem wave duoi day) — ban than
// theme.conf/Main.qml KHONG con doc usr/share/namios-branding/logo/brand.json
// (v2 "Sen Viet") nua cho RIENG man hinh nay, vi brand.json van la v2 (brand-
// core dev quan ly, ngoai pham vi nhiem vu nay) va QD 11/11/2026 chi sieu-xi
// (supersede) mau CHO man hinh dang nhap/khoi dong/splash, khong doi brand.json
// toan cuc. Fallback literal duoi day la nguon mau DUY NHAT cho theme nay.
//
// WAVE "DONG SON" 11/11/2026 (nhiem vu rieng giao cho system-screens dev):
//   - 4 mau fallback (cNavy/cSon/cGold/cFg) doi theo bang remap chinh thuc
//     (xem ghi chu day du trong theme.conf cung thu muc).
//   - Anh nen (Background.qml "source") doi sang namios-login-background.png
//     (navy + song teal/gold + bieu tuong trong dong, TU CHUA trong theme,
//     xem theme.conf). Day la ban "reproduce" cua anh kit
//     branding/kit/NaMi_Brand_DongSon_v1/04_system_screens/login-background.png,
//     DA BO 3 dong chu tinh ("NaMi"/"Xin chao"/"Dang nhap de tiep tuc") ma
//     anh kit goc ve san — vi khoi dang nhap THAT (xem mainColumn duoi day)
//     da doi tu anchors.centerIn sang neo DUOI (bottom), nam ngay trong vung
//     anh co dai song, NEU giu nguyen chu tinh cua kit (von nam giua man
//     hinh) se CHONG LEN vung bieu tuong — xem ly do day du trong theme.conf.
//   - Badge thuong hieu goc tren-trai: anh doi tu duong dan ben ngoai
//     /usr/share/namios-branding/logo/NaMiOS_Symbol_Transparent_1024.png
//     (phu thuoc goi wallpaper khac, da ghi nhan rui ro "CAN THEO DOI" o ban
//     truoc) sang 1 file SVG TU CHUA trong chinh theme nay
//     (namios-symbol-badge.svg, chep nguyen ban tu kit nami-symbol-white.svg,
//     sha256 khop manifest.json cua kit) — vua fix dung bieu tuong trong dong
//     v3, vua giam 1 phu thuoc ben ngoai.
//   - Dong ho (Clock) doi tu giua man hinh sang goc tren-phai (doi xung voi
//     badge goc tren-trai) — nhuong cho khoi dang nhap THAT (avatar/mat
//     khau/nut) chuyen xuong 1/3 duoi man hinh (tren vung dai song cua anh
//     nen), tranh de len vung bieu tuong trung tam phia tren (xem ly do day
//     du trong theme.conf).
//
// verified_on_host: NO — CHUA chay qua SDDM/Qt that. Rui ro cao nhat can xac
// nhan bang boot thuc: (1) SDDM co liet "namios" vao danh sach theme va tai
// duoc Main.qml khong loi cu phap/import; (2) userModel/sessionModel tren may
// thuc co dung cac role nhu tren khong (co the lech nho giua cac ban distro);
// (3) duoi che do software rendering (QT_QUICK_BACKEND=software, chi xay ra
// tren nhanh du phong Live/QEMU — xem includes.chroot/etc/sddm.conf.d/
// 10-namios-theme.conf ve ly do theme nay KHONG co hieu luc tren anh Live),
// cac Rectangle/gradient/clip co ve dung nhu mong doi khong; (4) bo cuc moi
// (khoi dang nhap neo duoi, dong ho goc tren-phai) co vua/khong tran tren man
// hinh thap (vd laptop ty le hep) — chi kiem bang tinh toan pixel + xem lai
// anh PNG qua Read tool trong phien lam viec, CHUA xem qua Qt Quick that.
import QtQuick 2.15
import QtQuick.Layouts 1.15
import org.kde.plasma.private.keyboardindicator as KeyboardIndicator

Item {
    id: root
    width: 1920
    height: 1080

    LayoutMirroring.enabled: Qt.application.layoutDirection === Qt.RightToLeft
    LayoutMirroring.childrenInherit: true

    // ---- mau thuong hieu v3 "Dong Son" (fallback cung neu theme.conf thieu
    // key — xem bang remap trong theme.conf cung thu muc) --------------------
    readonly property color cNavy: (config.backgroundColor && config.backgroundColor.length > 0) ? config.backgroundColor : "#092D4F"
    readonly property color cSon: (config.accentColor && config.accentColor.length > 0) ? config.accentColor : "#D64C3E"
    readonly property color cGold: (config.goldColor && config.goldColor.length > 0) ? config.goldColor : "#DEA93E"
    readonly property color cFg: (config.foregroundColor && config.foregroundColor.length > 0) ? config.foregroundColor : "#FFF9EF"
    // cFgDim KHONG doi (#B7C4CF) — da tinh lai contrast tren navy v3 moi
    // (#092D4F): 7.87:1, van dat WCAG AA (>=4.5:1), xem ghi chu theme.conf.
    readonly property color cFgDim: (config.foregroundDimColor && config.foregroundDimColor.length > 0) ? config.foregroundDimColor : "#B7C4CF"
    // FONT (UI polish 12/11/2026, QA finding m9): fallback doi "Inter" ->
    // "Noto Sans" dong bo voi theme.conf (fontFamily=Noto Sans) + installer
    // (show.qml) + docs/design/nami-tokens.json (typography.font_family.ui).
    // Noto Sans la font DUY NHAT trong anh da xac nhan phu du glyph tieng
    // Viet (goi fonts-noto-core/fonts-noto-ui-core) — xem ghi chu day du o
    // theme.conf cung thu muc.
    readonly property string brandFont: (config.fontFamily && config.fontFamily.length > 0) ? config.fontFamily : "Noto Sans"

    property string selectedUserName: (typeof userModel !== "undefined" && userModel.lastUser && userModel.lastUser.length > 0) ? userModel.lastUser : ""
    property int sessionIndex: (typeof sessionModel !== "undefined" && sessionModel.lastIndex >= 0) ? sessionModel.lastIndex : 0
    property string notice: ""

    function partsJoin(parts) {
        var out = [];
        for (var i = 0; i < parts.length; i++) {
            if (parts[i] && parts[i].length > 0) out.push(parts[i]);
        }
        return out.join(" • ");
    }

    readonly property string noticeText: partsJoin([
        capsLockState.locked ? "Caps Lock đang bật · Caps Lock is on" : "",
        root.notice
    ])

    function doLogin() {
        if (root.selectedUserName.length === 0) return;
        root.notice = "";
        sddm.login(root.selectedUserName, passwordInput.text, root.sessionIndex);
    }

    Connections {
        target: sddm
        function onLoginSucceeded() {
            mainColumn.opacity = 0;
        }
        function onLoginFailed() {
            root.notice = "Đăng nhập thất bại · Login failed";
            passwordInput.text = "";
            passwordInput.forceActiveFocus();
        }
    }

    KeyboardIndicator.KeyState {
        id: capsLockState
        key: Qt.Key_CapsLock
    }

    // ---- nen: ve tren MOI man hinh (multi-monitor) ------------------------
    Repeater {
        model: screenModel
        Background {
            x: geometry.x
            y: geometry.y
            width: geometry.width
            height: geometry.height
            source: config.background
            backgroundColor: root.cNavy
        }
    }

    // ---- badge thuong hieu goc tren-trai ----------------------------------
    // CHI ky hieu trong dong nho + chu "NaMiOS" — KHONG lap logo lon: anh nen
    // namios-login-background.png DA CO SAN bieu tuong trong dong can giua
    // phia tren (xem theme.conf). Badge nho o day chi la dau hieu nhan dien
    // phu, khong chong voi logo chinh trong anh. Anh badge doi sang
    // namios-symbol-badge.svg (TU CHUA trong theme, ban trang don sac — xem
    // ghi chu dau file ve ly do tach khoi /usr/share/namios-branding/).
    RowLayout {
        anchors { top: parent.top; left: parent.left; margins: 28 }
        spacing: 10
        Image {
            source: "/usr/share/sddm/themes/namios/namios-symbol-badge.svg"
            sourceSize.width: 28
            sourceSize.height: 28
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28
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

    // ---- dong ho goc tren-phai (doi xung voi badge) -------------------------
    // Chuyen tu giua man hinh ra day de nhuong cho khoi dang nhap that (duoi
    // day) chuyen xuong 1/3 duoi man hinh — xem ly do day du dau file.
    Clock {
        anchors { top: parent.top; right: parent.right; margins: 28 }
        timeColor: root.cFg
        dateColor: root.cFgDim
        compact: true
    }

    // ---- khoi dang nhap, neo o 1/3 duoi man hinh (tren vung dai song cua
    // anh nen) — xem ly do doi tu anchors.centerIn trong ghi chu dau file --
    ColumnLayout {
        id: mainColumn
        anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 64 }
        width: Math.min(root.width * 0.86, 440)
        spacing: 18

        Behavior on opacity { NumberAnimation { duration: 220 } }

        // Dong ho da chuyen ra goc tren-phai (xem ghi chu dau file) — khong
        // con dat o day nua, mainColumn gio chi con khoi avatar/mat khau/nut.
        ColumnLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            spacing: 18

            // ---- danh sach nguoi dung (thuong 1-3 tai khoan gia dinh) ----
            ColumnLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 10
                visible: typeof userModel !== "undefined" && userModel.count > 0

                Repeater {
                    id: userRepeater
                    model: typeof userModel !== "undefined" ? userModel : null

                    delegate: RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 10

                        readonly property bool isSelected: root.selectedUserName === model.name

                        Component.onCompleted: {
                            if (root.selectedUserName.length === 0 && index === 0) {
                                root.selectedUserName = model.name;
                            }
                        }

                        // A11Y (QA finding): chọn user chỉ bằng chuột (MouseArea) trước
                        // đây — KHÔNG Tab-reachable. selectUser() dùng chung cho cả
                        // MouseArea.onClicked VÀ Keys.on*Pressed để 2 đường vào (chuột/
                        // bàn phím) luôn làm đúng 1 hành động, không lệch nhau.
                        function selectUser() {
                            root.selectedUserName = model.name;
                            passwordInput.forceActiveFocus();
                        }

                        Rectangle {
                            id: avatarFrame
                            Layout.preferredWidth: 56
                            Layout.preferredHeight: 56
                            radius: width / 2
                            color: Qt.rgba(1, 1, 1, 0.07)
                            // Viền vàng (focus.ring token) khi ĐƯỢC CHỌN hoặc ĐANG FOCUS
                            // bàn phím — dày hơn (3px) lúc focus để phân biệt rõ khỏi viền
                            // "đã chọn" tĩnh (2px), không chỉ đổi màu (WCAG 2.2).
                            border.width: (isSelected || activeFocus) ? 3 : 2
                            border.color: (isSelected || activeFocus) ? root.cGold : Qt.rgba(1, 1, 1, 0.18)
                            clip: true
                            activeFocusOnTab: true
                            Accessible.role: Accessible.Button
                            Accessible.name: (model.realName && model.realName.length > 0) ? model.realName : model.name
                            Keys.onReturnPressed: selectUser()
                            Keys.onEnterPressed: selectUser()
                            Keys.onSpacePressed: selectUser()

                            Image {
                                id: avatarImg
                                anchors.fill: parent
                                source: model.icon ? model.icon : ""
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                                visible: status === Image.Ready
                            }
                            Text {
                                anchors.centerIn: parent
                                visible: !avatarImg.visible
                                text: ((model.realName && model.realName.length > 0) ? model.realName : model.name).toUpperCase().charAt(0)
                                color: root.cFg
                                font.family: root.brandFont
                                font.pixelSize: 22
                                font.weight: Font.DemiBold
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: selectUser()
                            }
                        }

                        Text {
                            text: (model.realName && model.realName.length > 0) ? model.realName : model.name
                            color: isSelected ? root.cFg : root.cFgDim
                            font.family: root.brandFont
                            font.pixelSize: 15
                            font.weight: isSelected ? Font.DemiBold : Font.Normal

                            // Chỉ MouseArea tiện bấm chuột vào tên — KHÔNG thêm tab-stop
                            // thứ hai cho cùng một hành động "chọn user" (avatarFrame đã
                            // là tab-stop chính, tránh Tab phải bấm 2 lần cho 1 user).
                            MouseArea {
                                anchors.fill: parent
                                onClicked: selectUser()
                            }
                        }
                    }
                }
            }

            // ---- du phong: go ten tay khi khong co userModel -------------
            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 220
                Layout.preferredHeight: 40
                radius: 10
                color: Qt.rgba(1, 1, 1, 0.08)
                // Viền vàng khi focus bàn phím — truoc day o nay KHONG co bat ky
                // chi bao focus nao (chi dua vao con tro nhap nhay, kho thay voi
                // nguoi dung low-vision). border.width 0 luc khong focus de khong
                // doi layout/mau khi chua bam vao.
                border.width: usernameInput.activeFocus ? 2 : 0
                border.color: root.cGold
                visible: !(typeof userModel !== "undefined" && userModel.count > 0)

                TextInput {
                    id: usernameInput
                    anchors.fill: parent
                    anchors.margins: 10
                    color: root.cFg
                    font.family: root.brandFont
                    font.pixelSize: 15
                    verticalAlignment: TextInput.AlignVCenter
                    onTextChanged: root.selectedUserName = text
                    Text {
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        text: "Tên đăng nhập · Username"
                        color: root.cFgDim
                        font: usernameInput.font
                        visible: usernameInput.text.length === 0
                    }
                }
            }

            // ---- o mat khau -------------------------------------------------
            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 300
                Layout.preferredHeight: 46
                radius: 10
                color: Qt.rgba(9 / 255, 45 / 255, 79 / 255, 0.55) // navy v3, xem theme.conf
                // focus.ring token yeu cau vien >=2px khi focus (truoc day co dinh
                // 1px cho moi trang thai, khong du do theo spec) — gio day len 2px
                // CHI khi focus, giu 1px luc binh thuong de khong doi layout.
                border.width: passwordInput.activeFocus ? 2 : 1
                border.color: passwordInput.activeFocus ? root.cGold : Qt.rgba(1, 1, 1, 0.14)

                TextInput {
                    id: passwordInput
                    anchors.fill: parent
                    anchors.leftMargin: 18
                    anchors.rightMargin: 18
                    verticalAlignment: TextInput.AlignVCenter
                    echoMode: TextInput.Password
                    color: root.cFg
                    font.family: root.brandFont
                    font.pixelSize: 15
                    focus: true
                    Keys.onReturnPressed: root.doLogin()
                    Keys.onEnterPressed: root.doLogin()

                    Text {
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        text: "Mật khẩu · Password"
                        color: root.cFgDim
                        font: passwordInput.font
                        visible: passwordInput.text.length === 0 && !passwordInput.activeFocus
                    }
                }
            }

            // ---- nut dang nhap ----------------------------------------------
            Rectangle {
                id: loginButton
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 150
                Layout.preferredHeight: 42
                radius: 10
                color: loginMouse.pressed ? Qt.darker(root.cSon, 1.15) : root.cSon
                opacity: root.selectedUserName.length > 0 ? 1.0 : 0.55
                // A11Y (QA finding): nut Dang nhap truoc day CHI co MouseArea, khong
                // Tab-reachable rieng (Enter trong o mat khau van goi duoc doLogin(),
                // nhung ban than NUT khong nhan focus/khong co chi bao). Them focus
                // ring vang 2px, KHONG chi doi mau (WCAG 2.2) — ve DE len tren nen
                // vermilion dac, van dam bao tuong phan ro.
                border.width: activeFocus ? 2 : 0
                border.color: root.cGold
                activeFocusOnTab: true
                Accessible.role: Accessible.Button
                Accessible.name: "Đăng nhập · Log In"
                Keys.onReturnPressed: root.doLogin()
                Keys.onEnterPressed: root.doLogin()
                Keys.onSpacePressed: root.doLogin()

                Text {
                    anchors.centerIn: parent
                    text: "Đăng nhập · Log In"
                    color: "#FFFFFF"
                    font.family: root.brandFont
                    // QA 11/11/2026 (wave "Dong Son"): nut gio nen vermilion
                    // v3 #D64C3E (cSon) — trang (#FFFFFF) tren #D64C3E chi dat
                    // 4.23:1, DUOI nguong AA van ban thuong/nho (4.5:1) nhung
                    // DAT nguong AA van ban "lon" (>=18.66px dam, 3:1). Tang
                    // pixelSize 15->19 (+ giu DemiBold) de du dieu kien "lon",
                    // tranh phai doi mau nut khoi vermilion chinh thuc.
                    font.pixelSize: 19
                    font.weight: Font.DemiBold
                }

                MouseArea {
                    id: loginMouse
                    anchors.fill: parent
                    enabled: root.selectedUserName.length > 0
                    onClicked: root.doLogin()
                }
            }

            // ---- thong bao loi / caps lock -----------------------------------
            Text {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: root.noticeText
                visible: root.noticeText.length > 0
                // QA 11/11/2026 (ban dau, v2): cSon (#C93643) tren nen navy
                // #122A3A = 2.89:1 < WCAG AA 4.5:1 (chu 13px kho doc). Dung do
                // nhat hon #F08A8F = 6.16:1 (dat AA) cho thong bao loi/Caps
                // Lock de doc.
                // QA 11/11/2026 (wave "Dong Son", tinh lai cho navy v3): cSon
                // gio la vermilion #D64C3E, tren navy #092D4F chi dat 3.31:1 —
                // van KHONG du AA nen VAN giu mau thay the #F08A8F (khong doi
                // sang cSon). Da tinh lai #F08A8F tren navy v3: 5.83:1, VAN
                // dat AA — khong can doi hex, chi ghi lai ket qua kiem tra.
                color: "#F08A8F"
                font.family: root.brandFont
                font.pixelSize: 13
            }

            // ---- chon phien dang nhap (chi hien khi >1 phien) ----------------
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 8
                visible: typeof sessionModel !== "undefined" && sessionModel.count > 1

                Repeater {
                    model: typeof sessionModel !== "undefined" ? sessionModel : null
                    // A11Y (QA finding): truoc day la Text{} + MouseArea thuan, khong
                    // Tab-reachable, khong co chi bao focus. Doi sang Item bao ngoai
                    // de co the ve mot vien focus rieng (Text khong co thuoc tinh
                    // border) + nhan Tab/Enter/Space.
                    delegate: Item {
                        id: sessionItem
                        implicitWidth: sessionLabel.implicitWidth + 8
                        implicitHeight: sessionLabel.implicitHeight + 6
                        activeFocusOnTab: true
                        Accessible.role: Accessible.Button
                        Accessible.name: model.name
                        Keys.onReturnPressed: root.sessionIndex = index
                        Keys.onEnterPressed: root.sessionIndex = index
                        Keys.onSpacePressed: root.sessionIndex = index

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: -3
                            radius: 4
                            color: "transparent"
                            border.width: 2
                            border.color: root.cGold
                            visible: sessionItem.activeFocus
                        }

                        Text {
                            id: sessionLabel
                            anchors.centerIn: parent
                            text: model.name
                            color: root.sessionIndex === index ? root.cGold : root.cFgDim
                            font.family: root.brandFont
                            font.pixelSize: 12
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: root.sessionIndex = index
                        }
                    }
                }
            }
        }
    }

    // ---- footer: nguon dien (goc duoi-phai) ---------------------------------
    // A11Y (QA finding): ca 3 dieu khien nguon truoc day la Text{} + MouseArea
    // thuan — khong Tab-reachable, khong co chi bao focus. Dinh nghia 1
    // component noi bo (powerControl) de khong lap code 3 lan, dung chung
    // mau/kieu voi avatarFrame/session selector o tren (vien vang 2px khi
    // activeFocus, Keys.onReturnPressed/EnterPressed/SpacePressed).
    component PowerControl: Item {
        id: ctrl
        property string label: ""
        signal activated()
        implicitWidth: ctrlLabel.implicitWidth + 8
        implicitHeight: ctrlLabel.implicitHeight + 6
        activeFocusOnTab: true
        Accessible.role: Accessible.Button
        Accessible.name: ctrl.label
        Keys.onReturnPressed: ctrl.activated()
        Keys.onEnterPressed: ctrl.activated()
        Keys.onSpacePressed: ctrl.activated()

        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: 4
            color: "transparent"
            border.width: 2
            border.color: root.cGold
            visible: ctrl.activeFocus
        }

        Text {
            id: ctrlLabel
            anchors.centerIn: parent
            text: ctrl.label
            color: root.cFgDim
            font.family: root.brandFont
            font.pixelSize: 13
        }

        MouseArea {
            anchors.fill: parent
            onClicked: ctrl.activated()
        }
    }

    RowLayout {
        anchors { bottom: parent.bottom; right: parent.right; margins: 20 }
        spacing: 14

        PowerControl {
            label: "Ngủ · Sleep"
            visible: typeof sddm !== "undefined" && sddm.canSuspend
            onActivated: sddm.suspend()
        }
        PowerControl {
            label: "Khởi động lại · Restart"
            visible: typeof sddm !== "undefined" && sddm.canReboot
            onActivated: sddm.reboot()
        }
        PowerControl {
            label: "Tắt máy · Shut Down"
            visible: typeof sddm !== "undefined" && sddm.canPowerOff
            onActivated: sddm.powerOff()
        }
    }
}
