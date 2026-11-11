// NaMiOS — Plasma "Splash Screen" (ksplashqml), goi Plasma/LookAndFeel
// "org.namios.sen". Day la man hinh chay NGAY SAU KHI dang nhap SDDM, trong
// luc desktop Plasma con dang tai (KHAC voi SDDM = man dang nhap, va KHAC
// voi Plymouth = splash som truoc khi dang nhap — ca 3 la BA theme rieng,
// xem usr/share/sddm/themes/namios/ + usr/share/plymouth/themes/namios/).
//
// HOP DONG ky thuat ksplashqml (doc tu hieu biet ve ma nguon plasma-workspace
// ksplash/ksplashqml — KHONG co build host/boot that de doi chieu truc tiep,
// xem verified_on_host o duoi):
//   1. Engine ksplashqml tao MOT QQuickView toan man hinh cho MOI man hinh
//      (multi-monitor), goi setResizeMode(QQuickView::SizeRootObjectToView)
//      TRUOC khi setSource() nap file nay. Hieu ung: view TU DAT lai
//      width/height cua CHINH root item (Rectangle duoi day) moi khi kich
//      thuoc man hinh thay doi — vi vay root KHONG duoc gan width/height co
//      dinh (vd "1920/1080" nhu sddm Main.qml, vi sddm-greeter dung co che
//      resize KHAC). Moi item con neo theo "parent"/"root.width"/"root.height"
//      se tu dong dung kich thuoc man hinh THAT — day CHINH LA cach
//      "sized to the screen" duoc hien thuc, khong phai gan so cung.
//   2. Engine goi rootObject()->setProperty("stage", n) voi n chay 1..6 khi
//      cac moc khoi dong session (ksmserver/kded/kwin/plasmashell san sang...)
//      lan luot bao qua D-Bus (giao dien org.kde.KSplash, ham setStage(int)).
//      File QML PHAI co mot property ten CHINH XAC "stage" (kieu int) de
//      engine gan gia tri vao — KHONG duoc doi ten property nay.
//   3. Package duoc tim qua KPackage: Theme=org.namios.sen trong
//      [KSplash] cua ksplashrc duoc dung lam "path" cho
//      KPackage::Package("Plasma/LookAndFeel"); KPackageStructure cho loai
//      nay dinh nghia khoa "splashmainscript" = contents/splash/Splash.qml
//      (ten file CHINH XAC, phan biet hoa/thuong) — day la ly do file nay
//      PHAI nam dung duong dan contents/splash/Splash.qml duoi thu muc
//      org.namios.sen (khop dung Id trong metadata.json).
//
// QUYET DINH THIET KE co chu dich (giong huong da chon cho SDDM Main.qml —
// xem usr/share/sddm/themes/namios/Main.qml dong 16-34):
//   - KHONG dung Kirigami/PlasmaComponents/QtQuick.Controls — tu ve
//     Rectangle/Image/Text/Row thuan QtQuick 2.15, giam phu thuoc module +
//     giam rui ro duoi phien ban Qt Quick Controls style khac nhau.
//   - KHONG dung Qt5Compat.GraphicalEffects / ShaderEffect (khong blur/
//     dropshadow GPU) — an toan duoi QT_QUICK_BACKEND=software (QEMU/TCG
//     khong GPU, cung ly do da ghi trong Main.qml + Background.qml cua
//     theme SDDM "namios").
//   - Anh logo lay TU TRONG package nay (contents/images/, copy tu
//     usr/share/namios-branding/logo/NaMiOS_Symbol_Color.svg) — KHONG tham
//     chieu duong dan tuyet doi /usr/share/namios-branding/... nhu badge nho
//     trong sddm Main.qml — vi ksplashqml chay trong tien trinh/ngu canh
//     rieng, khong dam bao moi duong dan tuyet doi ben ngoai package deu
//     "resolve" an toan nhu mong doi; dong goi logo CUNG VOI theme la cach
//     chac chan nhat (dung huong dan nhiem vu).
//   - NaMiOS_Symbol_Color.svg duoc chon (khong dung ban PNG) vi chinh file
//     SVG nay tu ghi trong comment nguon: "No gradients or filters: reliable
//     at OS boot and print" — hinh hoc don gian (chi <path fill="...">, khong
//     filter/gradient SVG) nen rui ro render thap, VA QtQuick Image doc SVG
//     qua plugin qtsvg ma toan bo Plasma/KDE da phu thuoc cung (icon theme
//     he thong deu la SVG) — khong them goi moi.
//
// MAU: lay THANG tu usr/share/namios-branding/logo/brand.json (nguon mau DUY
// NHAT toan OS) — KHONG qua lop config rieng nhu sddm theme.conf, vi goi
// Plasma/LookAndFeel splash KHONG co co che tuong tu "config.*" cua SDDM
// (ksplashqml khong doc theme.conf) — gia tri hex ghi THANG trong QML la
// chu dich, khong phai thieu fallback.
//   - Nen: nga am (sen quy khong dat nen den/navy — QD Cuong 09/11/2026,
//     xem docs/design/DESIGN-SYSTEM.md §1 "sen khong dat tren nen den") —
//     DUNG CHINH 2 ma gradient nga am ma Plymouth theme "namios" da dung
//     (BackgroundStartColor/BackgroundEndColor trong namios.plymouth) de
//     splash Plasma "noi tiep" dung mau voi splash Plymouth som hon trong
//     cung luot khoi dong — mot nhan dien lien tuc Plymouth(ngà ấm)
//     -> SDDM(mực đêm, anh nen rieng) -> Plasma splash(ngà ấm lai).
//   - Chu/logo/progress: do son #C93643 (brand.json "son"), chu chinh mực
//     đêm #182E3B (brand.json "chu_muc"/token text.primary sang), nen thanh
//     tien trinh #E3D6C2 (dung gia tri border.subtle cua token sang, DESIGN-
//     SYSTEM.md §1.2) — KHONG dung mau xanh KDE nao.
//
// verified_on_host: NO — CHUA chay qua ksplashqml/boot KDE Plasma that. Rui
// ro cao nhat can xac nhan khi co build host + may/VM boot duoc:
//   (1) KPackage thuc co phan giai dung Theme=org.namios.sen (ten thu muc +
//       Id metadata.json) ra dung file nay khong (khong loi "theme khong ton
//       tai", khong roi ve Breeze mac dinh);
//   (2) SizeRootObjectToView co lam Rectangle goc dung kich thuoc man hinh
//       THAT tren moi do phan giai (khong bi 0x0 hay cat mep);
//   (3) Image doc NaMiOS_Symbol_Color.svg qua duong dan tuong doi
//       "../images/..." co thanh cong trong dung tien trinh ksplashqml
//       (khac tien trinh Dolphin/Plasma shell thong thuong) khong;
//   (4) property "stage" co thuc su duoc engine gan 1..6 (khong phai mot con
//       so khac/khong chay) — neu khong, thanh tien trinh se dung yen o 0,
//       van AN TOAN (khong trang/khong loi) nhung khong dong vi hoat dong.
// Thiet ke co loi du phong: moi gia tri mau la literal (khong phu thuoc
// context property ben ngoai co the "undefined"), stage mac dinh 0 (thanh
// tien trinh rong, khong NaN/am), Image co opacity khoi dong 0 + chi hien ro
// sau introAnimation — neu anh khong tai duoc (status != Ready) item Image
// chi la mot vung trong trong bo cuc, KHONG lam vo layout hay chan chu/thanh
// tien trinh phia duoi.

import QtQuick 2.15

Rectangle {
    id: root

    // Nen: KHONG gan width/height — SizeRootObjectToView (xem hop dong #1
    // o tren) tu dat kich thuoc man hinh thuc moi lan resize.
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#FBF8F2" } // nga am sang (khop BackgroundStartColor Plymouth)
        GradientStop { position: 1.0; color: "#EFE3D1" } // nga am dam hon (khop BackgroundEndColor Plymouth)
    }

    // ---- property engine dieu khien: KHONG doi ten, xem hop dong #2 ------
    property int stage: 0

    // Kep an toan: stage tu ksplashqml ly thuyet chi 0..6, nhung neu mot
    // engine/test harness gan gia tri la/am, van khong de progressFraction
    // vuot [0,1] (tranh thanh tien trinh ve qua kho/am).
    readonly property real progressFraction: Math.max(0, Math.min(1, stage / 6))

    onStageChanged: {
        if (stage === 1) {
            introAnimation.restart();
        }
    }

    // ---- khoi logo + ten san pham, can giua man hinh ----------------------
    Column {
        id: centerColumn
        anchors.centerIn: parent
        spacing: 22

        Image {
            id: logoImage
            anchors.horizontalCenter: parent.horizontalCenter
            source: "../images/NaMiOS_Symbol_Color.svg"
            sourceSize.width: 132
            sourceSize.height: 132
            width: 132
            height: 132
            fillMode: Image.PreserveAspectFit
            smooth: true
            asynchronous: true
            opacity: 0 // introAnimation dan hien khi stage dau tien toi (xem duoi)
        }

        Text {
            id: productName
            anchors.horizontalCenter: parent.horizontalCenter
            text: "NaMiOS"
            color: "#182E3B" // brand.json "chu_muc" / token text.primary (sang)
            font.family: "Inter"
            font.pixelSize: 32
            font.weight: Font.DemiBold
            opacity: logoImage.opacity
        }

        Text {
            id: productTagline
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Hệ điều hành cho người Việt"
            color: "#52646B" // token text.secondary (sang)
            font.family: "Inter"
            font.pixelSize: 16
            font.weight: Font.Normal
            opacity: logoImage.opacity
        }
    }

    // ---- fade-in mo dau, kieu introAnimation cua Breeze Splash.qml --------
    // (PropertyAction dat opacity=0 ngay truoc khi NumberAnimation chay, de
    // restart() luon bat dau tu trong suot du onStageChanged bi goi lai).
    SequentialAnimation {
        id: introAnimation
        running: false

        PropertyAction { target: logoImage; property: "opacity"; value: 0 }
        PauseAnimation { duration: 260 }
        NumberAnimation {
            target: logoImage
            property: "opacity"
            to: 1
            duration: 700
            easing.type: Easing.OutCubic
        }
    }

    // ---- thanh tien trinh do son, day dan theo stage 1..6 ------------------
    // Kich thuoc 480x6 + mau nen #E3D6C2 CHINH LA gia tri Plymouth theme
    // "namios" da dung (ProgressBarWidth/Height/BackgroundColor trong
    // namios.plymouth) — tiep tuc dung ngon ngu hinh anh do, khong phai so
    // moi bay ra.
    Rectangle {
        id: progressTrack
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 72
        width: 480
        height: 6
        radius: height / 2
        color: "#E3D6C2"

        Rectangle {
            id: progressFill
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            radius: height / 2
            color: "#C93643" // brand.json "son"
            width: parent.width * root.progressFraction

            Behavior on width {
                NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
            }
        }
    }
}
