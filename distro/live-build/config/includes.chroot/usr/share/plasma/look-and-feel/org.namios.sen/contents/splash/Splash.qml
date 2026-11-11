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
//   4. (MOI ghi nhan khi redesign 11/11/2026 — KHONG phai hop dong engine,
//      chi la quan sat thiet ke) ksplashqml KHONG dam bao "stage" chay het
//      1..6 trong moi truong hop (vd mot thanh phan session khoi dong hong/
//      cham bat thuong) — neu "stage" dung yen, mot UI chi dua vao "stage"
//      de hien/dong se nhin "chet" (frozen), dung y nhu issue owner neu ra
//      ("luon phai nhin dang chay"). Vi vay ban redesign nay THEM mot chi
//      bao xoay vo han KHONG phu thuoc "stage" (xem muc "KHOI 'DANG CHAY'"
//      duoi day) — day la lop du phong hien thi, khong thay doi hop dong
//      engine o tren.
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
//   - Chi bao "dang chay" (spinner) CUNG khong dung QtQuick.Shapes/Canvas:
//     ca hai co the chay duoi software backend (Canvas dung QPainter CPU,
//     Shapes co the ep kieu render CPU), nhung van la MODULE/API MOI chua
//     tung dung trong theme nay — giu nguyen tac toi thieu hoa import da
//     chon xuyen suot SDDM + Plasma splash: spinner duoc dung thuan bang
//     8 Rectangle nho (qua Repeater) xoay chung boi MOT RotationAnimation
//     — ca Repeater va RotationAnimation deu la API co san trong chinh
//     module "QtQuick" da import (khong them import nao).
//   - Anh logo + anh watermark hoa van deu lay TU TRONG package nay
//     (contents/images/) — KHONG tham chieu duong dan tuyet doi
//     /usr/share/namios-branding/... nhu badge nho trong sddm Main.qml —
//     vi ksplashqml chay trong tien trinh/ngu canh rieng, khong dam bao
//     moi duong dan tuyet doi ben ngoai package deu "resolve" an toan nhu
//     mong doi; dong goi cung voi theme la cach chac chan nhat.
//   - NaMiOS_Symbol_Color.svg (logo) va trongdong.svg (watermark, file moi
//     o ban redesign nay) deu la SVG hinh hoc don gian (chi
//     <path>/<circle>/<line>/<polygon> voi fill/stroke phang, KHONG
//     gradient/filter SVG) nen rui ro render thap qua plugin qtsvg ma toan
//     bo Plasma/KDE da phu thuoc cung (icon theme he thong deu la SVG) —
//     khong them goi moi.
//
// MAN HINH CHO (waiting screen) — redesign 11/11/2026, 3 thanh phan moi
// theo yeu cau: (a) mot chi bao "dang chay" LUON song dong bat ke "stage";
// (b) dong chu tran an "Vui long cho trong giay lat…"; (c) nen mang dam
// ban sac Viet — hoa van trong dong Dong Son lam watermark mo phia sau.
//   - KHOI "DANG CHAY": item "spinnerRing" + RotationAnimation
//     (loops: Animation.Infinite, running: true khai bao TINH — khong nam
//     trong introAnimation, khong bi onStageChanged dieu khien) — xoay LIEN
//     TUC tu frame dau tien file duoc nap, HOAN TOAN DOC LAP voi "stage".
//     8 Rectangle nho ("tick") xep vong tron qua luong giac
//     Math.sin/Math.cos (JS co san trong QML, khong can import), do mo dan
//     theo index de tao cam giac "duoi sao chay" kieu spinner iOS/Android
//     quen thuoc, mau vang #DEA93E (dung ngon ngu mau voi progressFill — da
//     doi tu do son #C93643 sang vang o wave "Dong Son" 11/11/2026, xem muc
//     "MAU" cuoi file).
//     spinnerRing.opacity CO DINH = 1 (xem ly do o khoi "Thiet ke co loi du
//     phong" cuoi file) — KHAC voi logoImage/productName/productTagline
//     (fade-in theo introAnimation khi stage cham moc dau).
//   - DONG CHU TRAN AN: Text "Vui long cho trong giay lat…" ngay duoi khoi
//     spinner, cung Inter, mau text.secondary — cung CO DINH opacity = 1
//     cho ly do nhu tren.
//   - WATERMARK TRONG DONG: Image doc contents/images/trongdong.svg (file
//     MOI tao o ban redesign nay), can giua man hinh, kich thuoc =
//     Math.min(root.width, root.height) * 0.62 (ty le man hinh, khong so
//     cung), opacity THAP (0.13) de khong lam roi/giam do doc chu-logo phia
//     tren — khai bao TRUOC centerColumn trong thu tu sibling (QtQuick ve
//     theo thu tu khai bao, item sau ve CHONG len item truoc) de dam bao
//     watermark luon nam DUOI logo/chu/spinner/progress bar ve z-order.
//     Hoa van la ngôi sao nhieu canh o tam (mat troi) + cac vong tron dong
//     tam xen cac dai rang-cua/tam-giac + hang chac — lay cam hung Ở MỨC Y
//     TUONG VAN HOA CHUNG tu cac mo-tip dan gian co pho bien tren nhieu mat
//     trong dong Dong Son noi chung (KHONG sao chep/dua tren anh chup bat
//     ky hien vat bao tang cu the nao — cung nguyen tac da ap dung cho goi
//     hinh nen "NaMiOS-23-Trong-Dong-Tia-Nang", xem
//     usr/share/namios/docs/WALLPAPER-PROVENANCE.md muc A.3), ve lai hoan
//     toan bang cong thuc hinh hoc/luong giac rieng cua tai san nay, chi 2
//     mau brand.json "vang_tam"/"vang_nuoc" tren nen trong suot.
//
// MAU: WAVE "DONG SON" 11/11/2026 (nhiem vu rieng giao cho system-screens
// dev — thay nhan dien BOOT/LOGIN/SPLASH tu v2 "Sen Viet" sang v3 "Dong
// Son"). Nguoi giao nhiem vu XAC NHAN RO RANG palette v3 (navy #092D4F lam
// NEN) SIEU-XI (supersede) quyet dinh 09/11/2026 "sen quy khong dat nen den"
// CHI cho 3 diem cham-tram boot/login/splash nay (docs/design/DESIGN-
// SYSTEM.md §1 van dung cho cac mat khac nhu wallpaper desktop mac dinh/
// man hinh About, KHONG doi o day). Van KHONG qua lop config rieng nhu sddm
// theme.conf (ksplashqml khong doc theme.conf) — gia tri hex ghi THANG
// trong QML la chu dich, khong phai thieu fallback.
//   - Nen: navy #092D4F (gradient nhe 2 sac navy de co chieu sau "premium"),
//     THAY nga am 2 sac ma Plymouth theme "namios" TUNG dung — Plymouth
//     (namios.plymouth) CUNG da doi sang navy trong wave nay nen 2 splash
//     van "noi tiep" dung mau: Plymouth(navy) -> SDDM(navy, anh nen rieng)
//     -> Plasma splash(navy) — mot nhan dien lien tuc xuyen suot khoi dong.
//   - Chu chinh: ivory #FFF9EF (thay mực đêm #182E3B — chu toi tren nen
//     navy moi se vo hinh, phai doi sang chu sang). Chu phu/tagline/dong
//     cho: #B7C4CF (dim tren navy, da tinh contrast 7.87:1 dat AA — xem
//     theme.conf cua SDDM cung wave nay, dung chung 1 gia tri cho nhat
//     quan 2 man hinh).
//   - Progress/spinner: VANG #DEA93E (THAY do son #C93643 — yeu cau ro
//     rang cua nhiem vu "progress/spinner in gold"; vang cung la mau
//     "progress/signature accent" chinh thuc cua palette v3).
//   - Track thanh tien trinh: navy nhat hon #163C63 (THAY ivory-tan
//     #E3D6C2 — gia tri cu danh cho nen sang, tren nen navy moi phai la 1
//     khoi navy nhat hon de "hop" ro, dung chung gia tri voi
//     ProgressBarBackgroundColor cua Plymouth/bg_color cua GRUB cung wave
//     nay de 3 diem cham-tram dong bo).
//   - Watermark trong dong (trongdong.svg): doi tu 2 sac vang v2 (#F2C66D/
//     #BC8A43) sang DUY NHAT 1 vang v3 #DEA93E (bang remap chinh thuc gop
//     ca 2 ma cu ve 1 ma moi) — xem ghi chu rieng trong file .svg do.
//
// FONT (UI polish 12/11/2026, QA finding m9): 3 Text con (productName/
// productTagline/waitingText) doi "Inter" -> "Noto Sans" — dong bo voi
// theme SDDM "namios" (theme.conf/Main.qml/Clock.qml, cung sua trong wave
// nay) + installer (etc/calamares/branding/namios/show.qml da dung Noto
// Sans tu truoc) + docs/design/nami-tokens.json (typography.font_family.ui
// = "Noto Sans"). Noto Sans la font DUY NHAT trong anh da xac nhan phu du
// glyph tieng Viet (goi fonts-noto-core/fonts-noto-ui-core); Inter chi la
// mot wave rieng 10/11/2026 tu ghi "Vietnamese coverage chua xac nhan" (xem
// package-lists/0300-fonts.list.chroot). Rollback: doi lai "Inter" o 3 Text
// nay — khong anh huong gradient/mau/animation con lai cua file.
//
// verified_on_host: NO — CHUA chay qua ksplashqml/boot KDE Plasma that. Rui
// ro cao nhat can xac nhan khi co build host + may/VM boot duoc:
//   (1) KPackage thuc co phan giai dung Theme=org.namios.sen (ten thu muc +
//       Id metadata.json) ra dung file nay khong (khong loi "theme khong ton
//       tai", khong roi ve Breeze mac dinh);
//   (2) SizeRootObjectToView co lam Rectangle goc dung kich thuoc man hinh
//       THAT tren moi do phan giai (khong bi 0x0 hay cat mep) — ke ca khi
//       da them nhieu item hon vao centerColumn (spinner + dong chu moi) so
//       voi ban truoc, tren man hinh THAP (vd laptop ty le hep) co the can
//       kiem tra khong bi tran/chong lap voi progressTrack o day man hinh;
//   (3) Image doc NaMiOS_Symbol_Color.svg qua duong dan tuong doi
//       "../images/..." co thanh cong trong dung tien trinh ksplashqml
//       (khac tien trinh Dolphin/Plasma shell thong thuong) khong;
//   (4) property "stage" co thuc su duoc engine gan 1..6 (khong phai mot con
//       so khac/khong chay) — neu khong, thanh tien trinh se dung yen o 0
//       (van AN TOAN), nhung nho co spinner moi (muc (6) duoi) nguoi dung
//       van thay he thong "dang chay" thay vi man hinh dung im hoan toan;
//   (5) Anh watermark moi contents/images/trongdong.svg co doc duoc qua
//       duong dan tuong doi "../images/trongdong.svg" trong dung tien trinh
//       ksplashqml hay khong — CUNG LOAI rui ro voi logo o muc (3), nhung
//       la file HOAN TOAN MOI, chua tung duoc nap qua bat ky tien trinh QML
//       nao (khac logo — da dung lai asset co san tu truoc);
//   (6) RotationAnimation xoay "spinnerRing" (8 Rectangle con qua Repeater)
//       co render muot, khong giat/khong ton CPU dang ke tren may yeu/khong
//       GPU duoi QT_QUICK_BACKEND=software hay khong — ly thuyet an toan
//       (chi 1 property animation xoay CA group, khong phai 8 animation doc
//       lap; cac Rectangle con la hinh khoi phang khong gradient/shadow),
//       nhung CHUA do thuc te tren phan cung yeu/QEMU TCG.
// Thiet ke co loi du phong: moi gia tri mau la literal (khong phu thuoc
// context property ben ngoai co the "undefined"), stage mac dinh 0 (thanh
// tien trinh rong, khong NaN/am), Image (logo + watermark) co opacity khoi
// dong an toan + chi hien ro sau introAnimation (rieng logo) hoac hien ngay
// (watermark, spinner, dong chu cho) — neu anh khong tai duoc (status !=
// Ready) item Image chi la mot vung trong trong bo cuc, KHONG lam vo layout
// hay chan chu/thanh tien trinh phia duoi. Spinner + dong chu "Vui long
// cho…" CO CHU DICH dat opacity = 1 CO DINH (khong rang buoc vao
// logoImage.opacity/introAnimation/"stage") — day la lop du phong THEM moi
// so voi ban truoc: ke ca trong truong hop xau nhat "stage" khong bao gio
// duoc engine gan (rui ro (4) o tren), nguoi dung van thay MOT THU dang
// chuyen dong lien tuc ngay tu frame dau tien, khong con roi vao tinh huong
// "man hinh dung yen hoan toan, khong ro dang chay hay da treo" nhu thiet
// ke cu (truoc ban nay, toan bo UI phu thuoc "stage"/introAnimation deu co
// the khong bao gio hien ra neu "stage" khong duoc gan).

import QtQuick 2.15

Rectangle {
    id: root

    // Nen: KHONG gan width/height — SizeRootObjectToView (xem hop dong #1
    // o tren) tu dat kich thuoc man hinh thuc moi lan resize.
    // WAVE "DONG SON" 11/11/2026: doi tu nga am sang navy (khop
    // BackgroundStartColor/EndColor moi cua Plymouth, xem namios.plymouth).
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#0E3A63" } // navy nhat hon (chieu sau "premium")
        GradientStop { position: 1.0; color: "#092D4F" } // navy v3 dam (khop BackgroundEndColor Plymouth)
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

    // ---- watermark hoa van trong dong, can giua MAN HINH, opacity thap,
    // khai bao TRUOC centerColumn de ve o DUOI (z-order), xem muc "MAN HINH
    // CHO" o dau file ---------------------------------------------------
    Image {
        id: trongDongWatermark
        anchors.centerIn: parent
        readonly property real motifSize: Math.min(root.width, root.height) * 0.62
        width: motifSize
        height: motifSize
        sourceSize.width: width
        sourceSize.height: height
        source: "../images/trongdong.svg"
        fillMode: Image.PreserveAspectFit
        smooth: true
        asynchronous: true
        opacity: 0.13
    }

    // ---- khoi logo + ten san pham + chi bao "dang chay" + dong chu cho,
    // can giua man hinh ----------------------------------------------------
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
            text: "NaMi"
            color: "#FFF9EF" // ivory v3 (THAY mực-đêm #182E3B — tren nen navy moi)
            font.family: "Noto Sans"
            font.pixelSize: 32
            font.weight: Font.DemiBold
            opacity: logoImage.opacity
        }

        Text {
            id: productTagline
            anchors.horizontalCenter: parent.horizontalCenter
            text: "NaMi — Hệ điều hành cho người Việt"
            color: "#B7C4CF" // dim tren navy, 7.87:1 (dat AA) — xem ghi chu mau dau file
            font.family: "Noto Sans"
            font.pixelSize: 16
            font.weight: Font.Normal
            opacity: logoImage.opacity
        }

        // ---- chi bao "dang chay": 8 tick xoay vo han, LUON song dong,
        // KHONG phu thuoc stage/introAnimation (xem muc "MAN HINH CHO" dau
        // file) — day la diem khac biet chinh so voi ban cu, giai quyet
        // dung yeu cau "luon phai nhin dang chay, khong phai anh tinh" -----
        Item {
            id: spinnerRing
            width: 40
            height: 40
            anchors.horizontalCenter: parent.horizontalCenter
            opacity: 1 // CO DINH — khong rang buoc logoImage.opacity, xem ghi chu dau file

            readonly property real tickRadius: 15

            Repeater {
                model: 8
                delegate: Rectangle {
                    width: 4
                    height: 9
                    radius: 2
                    color: "#DEA93E" // vang v3 (THAY do-son #C93643 — "progress/spinner in gold")
                    opacity: 1 - index * 0.11 // mo dan tao cam giac "duoi sao chay"
                    x: (spinnerRing.width / 2 - width / 2) + (spinnerRing.tickRadius * Math.sin(index * Math.PI / 4))
                    y: (spinnerRing.height / 2 - height / 2) - (spinnerRing.tickRadius * Math.cos(index * Math.PI / 4))
                    rotation: index * 45 // huong tick doc theo ban kinh (kieu kim dong ho)
                }
            }

            RotationAnimation {
                target: spinnerRing
                property: "rotation"
                from: 0
                to: 360
                duration: 1400
                loops: Animation.Infinite
                running: true // chay NGAY tu frame dau, khong nam trong introAnimation/onStageChanged
            }
        }

        Text {
            id: waitingText
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Vui lòng chờ trong giây lát…"
            color: "#B7C4CF" // dim tren navy — cung mau voi productTagline
            font.family: "Noto Sans"
            font.pixelSize: 15
            font.weight: Font.Normal
            opacity: 1 // CO DINH — xem ghi chu dau file
        }
    }

    // ---- fade-in mo dau, kieu introAnimation cua Breeze Splash.qml --------
    // (PropertyAction dat opacity=0 ngay truoc khi NumberAnimation chay, de
    // restart() luon bat dau tu trong suot du onStageChanged bi goi lai).
    // CHI anh huong logoImage/productName/productTagline (opacity cua chung
    // rang buoc theo logoImage.opacity) — spinnerRing/waitingText KHONG rang
    // buoc vao day, xem ly do o muc "MAN HINH CHO" dau file.
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

    // ---- thanh tien trinh vang, day dan theo stage 1..6 ------------------
    // Kich thuoc 480x6 + mau track #163C63 CHINH LA gia tri Plymouth theme
    // "namios" da dung (ProgressBarWidth/Height/BackgroundColor trong
    // namios.plymouth) — tiep tuc dung ngon ngu hinh anh dong bo, khong phai
    // so moi bay ra. Day la tien trinh THAT theo "stage" (1..6) — khac voi
    // spinnerRing o tren (chi bao "dang chay" chung, luon xoay vo han).
    Rectangle {
        id: progressTrack
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 72
        width: 480
        height: 6
        radius: height / 2
        color: "#163C63" // navy nhat hon (THAY ivory-tan #E3D6C2 — hop voi nen navy)

        Rectangle {
            id: progressFill
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            radius: height / 2
            color: "#DEA93E" // vang v3 (THAY do-son #C93643 — "progress/spinner in gold")
            width: parent.width * root.progressFraction

            Behavior on width {
                NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
            }
        }
    }
}
