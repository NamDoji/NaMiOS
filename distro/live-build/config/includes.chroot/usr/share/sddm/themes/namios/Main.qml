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
// GOC DUY NHAT = usr/share/namios-branding/logo/brand.json (v2 "Sen Viet").
//
// verified_on_host: NO — CHUA chay qua SDDM/Qt that. Rui ro cao nhat can xac
// nhan bang boot thuc: (1) SDDM co liet "namios" vao danh sach theme va tai
// duoc Main.qml khong loi cu phap/import; (2) userModel/sessionModel tren may
// thuc co dung cac role nhu tren khong (co the lech nho giua cac ban distro);
// (3) duoi che do software rendering (QT_QUICK_BACKEND=software, chi xay ra
// tren nhanh du phong Live/QEMU — xem includes.chroot/etc/sddm.conf.d/
// 10-namios-theme.conf ve ly do theme nay KHONG co hieu luc tren anh Live),
// cac Rectangle/gradient/clip co ve dung nhu mong doi khong.
import QtQuick 2.15
import QtQuick.Layouts 1.15
import org.kde.plasma.private.keyboardindicator as KeyboardIndicator

Item {
    id: root
    width: 1920
    height: 1080

    LayoutMirroring.enabled: Qt.application.layoutDirection === Qt.RightToLeft
    LayoutMirroring.childrenInherit: true

    // ---- mau thuong hieu (fallback cung neu theme.conf thieu key) --------
    readonly property color cNavy: (config.backgroundColor && config.backgroundColor.length > 0) ? config.backgroundColor : "#122A3A"
    readonly property color cSon: (config.accentColor && config.accentColor.length > 0) ? config.accentColor : "#C93643"
    readonly property color cGold: (config.goldColor && config.goldColor.length > 0) ? config.goldColor : "#F2C66D"
    readonly property color cFg: (config.foregroundColor && config.foregroundColor.length > 0) ? config.foregroundColor : "#F7F6F1"
    readonly property color cFgDim: (config.foregroundDimColor && config.foregroundDimColor.length > 0) ? config.foregroundDimColor : "#B7C4CF"
    readonly property string brandFont: (config.fontFamily && config.fontFamily.length > 0) ? config.fontFamily : "Inter"

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
    // CHI ky hieu Sen nho + chu "NaMiOS" — KHONG lap logo lon: anh nen
    // namios-default.png DA CO SAN logo+chu "NaMiOS" can giua (xem hook
    // 0400-qemu-desktop-autologin.hook.chroot, dong comment ve showlogo cua
    // breeze). Badge nho o day chi la dau hieu nhan dien phu, khong chong
    // voi logo chinh trong anh.
    RowLayout {
        anchors { top: parent.top; left: parent.left; margins: 28 }
        spacing: 10
        Image {
            source: "/usr/share/namios-branding/logo/NaMiOS_Symbol_Transparent_1024.png"
            sourceSize.width: 28
            sourceSize.height: 28
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            visible: status === Image.Ready
        }
        Text {
            text: "NaMiOS"
            color: root.cFg
            font.family: root.brandFont
            font.pixelSize: 16
            font.weight: Font.DemiBold
            opacity: 0.92
        }
    }

    // ---- khoi dang nhap, can giua man hinh ---------------------------------
    ColumnLayout {
        id: mainColumn
        anchors.centerIn: parent
        width: Math.min(root.width * 0.86, 440)
        spacing: 30

        Behavior on opacity { NumberAnimation { duration: 220 } }

        Clock {
            Layout.alignment: Qt.AlignHCenter
            timeColor: root.cFg
            dateColor: root.cFgDim
        }

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

                        Rectangle {
                            id: avatarFrame
                            Layout.preferredWidth: 56
                            Layout.preferredHeight: 56
                            radius: width / 2
                            color: Qt.rgba(1, 1, 1, 0.07)
                            border.width: 2
                            border.color: isSelected ? root.cGold : Qt.rgba(1, 1, 1, 0.18)
                            clip: true

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
                                onClicked: {
                                    root.selectedUserName = model.name;
                                    passwordInput.forceActiveFocus();
                                }
                            }
                        }

                        Text {
                            text: (model.realName && model.realName.length > 0) ? model.realName : model.name
                            color: isSelected ? root.cFg : root.cFgDim
                            font.family: root.brandFont
                            font.pixelSize: 15
                            font.weight: isSelected ? Font.DemiBold : Font.Normal

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    root.selectedUserName = model.name;
                                    passwordInput.forceActiveFocus();
                                }
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
                radius: height / 2
                color: Qt.rgba(1, 1, 1, 0.08)
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
                radius: height / 2
                color: Qt.rgba(18 / 255, 42 / 255, 58 / 255, 0.55)
                border.width: 1
                border.color: passwordInput.activeFocus ? root.cSon : Qt.rgba(1, 1, 1, 0.14)

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
                radius: height / 2
                color: loginMouse.pressed ? Qt.darker(root.cSon, 1.15) : root.cSon
                opacity: root.selectedUserName.length > 0 ? 1.0 : 0.55

                Text {
                    anchors.centerIn: parent
                    text: "Đăng nhập · Log In"
                    color: "#FFFFFF"
                    font.family: root.brandFont
                    font.pixelSize: 15
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
                color: root.cSon
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
                    delegate: Text {
                        text: model.name
                        color: root.sessionIndex === index ? root.cGold : root.cFgDim
                        font.family: root.brandFont
                        font.pixelSize: 12
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
    RowLayout {
        anchors { bottom: parent.bottom; right: parent.right; margins: 20 }
        spacing: 14

        Text {
            text: "Ngủ · Sleep"
            color: root.cFgDim
            font.family: root.brandFont
            font.pixelSize: 13
            visible: typeof sddm !== "undefined" && sddm.canSuspend
            MouseArea { anchors.fill: parent; onClicked: sddm.suspend() }
        }
        Text {
            text: "Khởi động lại · Restart"
            color: root.cFgDim
            font.family: root.brandFont
            font.pixelSize: 13
            visible: typeof sddm !== "undefined" && sddm.canReboot
            MouseArea { anchors.fill: parent; onClicked: sddm.reboot() }
        }
        Text {
            text: "Tắt máy · Shut Down"
            color: root.cFgDim
            font.family: root.brandFont
            font.pixelSize: 13
            visible: typeof sddm !== "undefined" && sddm.canPowerOff
            MouseArea { anchors.fill: parent; onClicked: sddm.powerOff() }
        }
    }
}
