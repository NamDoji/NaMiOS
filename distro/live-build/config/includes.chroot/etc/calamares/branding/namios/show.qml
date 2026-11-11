// NaMiOS — slideshow QML hiển thị trong màn hình "Phase 2 — Install" của
// Calamares (lúc file đang được copy lên đĩa). Viết lại 10/11/2026 theo
// phong cách "Windows 11 Setup" (nền tối thương hiệu, một câu tiêu đề lớn +
// một câu phụ, khung đẹp/chuyên nghiệp) — chữ CHÍNH tiếng Anh, chữ PHỤ (nhỏ
// hơn, mờ hơn) tiếng Việt, đúng yêu cầu 10/11/2026.
//
// Cấu trúc đối chiếu TRỰC TIẾP với mã nguồn THẬT của Calamares (không đoán):
//   - `import calamares.slideshow 1.0` nạp module QML riêng của Calamares,
//     cài bởi gói `calamares` tại .../qml/calamares/slideshow/{qmldir,
//     Presentation.qml,Slide.qml,...} — xem qmldir: "Presentation 1.0
//     Presentation.qml" / "Slide 1.0 Slide.qml".
//   - `Presentation` (Presentation.qml) là một `Item` có các property CÓ
//     THẬT: `textColor`/`titleColor`/`fontFamily` (áp dụng cho mọi Slide con
//     qua `parent.textColor`/`parent.titleColor`/`parent.fontFamily` khai
//     trong Slide.qml), `currentSlide`, `slides` (mảng tự dò các con có
//     `isSlide: true` lúc `Component.onCompleted`), `activatedInCalamares`
//     (Calamares C++ set true khi trang slideshow thật sự hiển thị),
//     `goToNextSlide()/goToPreviousSlide()`. KHÔNG có hàm `onActivate()/
//     onLeave()` định nghĩa sẵn trong Presentation.qml — hai hàm này do
//     NGƯỜI DÙNG (NaMiOS) tự khai báo trên root object; Calamares (API v2,
//     xem `slideshowAPI: 2` trong branding.desc) gọi chúng bằng
//     QMetaObject::invokeMethod nếu tồn tại — đây là "V2 loading" đã ghi chú
//     ngay trong Presentation.qml gốc.
//   - `Slide` (Slide.qml) tự chiếm một "vùng nội dung" cố định bên trong
//     Presentation: x = 5% chiều rộng, y = 20% chiều cao, width = 90%,
//     height = 70% — nghĩa là 20% trên cùng và 10% dưới cùng của khung LUÔN
//     TRỐNG theo quy ước gốc. NaMiOS dùng đúng hai vùng trống này cho dải
//     nhấn màu đỏ son phía trên + chấm chỉ-số-slide phía dưới (xem dưới),
//     không chồng lên nội dung slide.
//
// AN TOÀN KÍCH THƯỚC CHỮ — KHÔNG dựa vào các property nội bộ của Slide.qml
// (`baseFontSize`/`titleFontSize`) vì đó là scope riêng của FILE Slide.qml,
// không chắc được các Text con khai trong FILE NÀY (show.qml) nhìn thấy
// không-cần-tiền-tố qua biên file QML (không có engine Qt/QML thật trong môi
// trường soạn để tự kiểm — xem CLAUDE.md "Môi trường build hiện tại"). Thay
// vào đó, mọi cỡ chữ tính theo `presentation.height * hệ_số` — CÙNG kiểu
// tham chiếu qua `id: presentation` mà bản show.qml TRƯỚC đã dùng cho
// `presentation.width` (đã chứng minh hoạt động được, vì `id` là global
// trong toàn document QML, không phụ thuộc biên file).
//
// verified_on_host: NO — chưa mở Calamares thật để xác nhận bằng mắt (môi
// trường soạn không có qemu/live-build, xem CLAUDE.md). Theo tài liệu
// Calamares, nếu QML này lỗi cú pháp thì khung "exec" vẫn tiếp tục cài đặt
// (slideshow chỉ là panel phụ, không phải bước cài) — nhưng cấu trúc
// Presentation/Slide/onActivate/onLeave đã đối chiếu TRỰC TIẾP với mã nguồn
// thật ở trên, không phải suy đoán.
//
// SPDX-FileCopyrightText: 2026 NaMiOS (Đỗ Chí Cường, Đỗ Bảo Nam)
// SPDX-License-Identifier: GPL-3.0-or-later

// POLISH 10/11/2026 (wave riêng, sau wave dựng khung 4-slide + C/D
// partitioning ở trên) — CHỈ thêm chi tiết thị giác, KHÔNG đổi cấu trúc
// Presentation/Slide/onActivate/onLeave đã có (slideshowAPI 2 giữ nguyên),
// KHÔNG đổi nội dung 4 slide (chữ Anh chính + chữ Việt phụ không đổi):
//   - Nền toàn khung: từ màu phẳng "#122A3A" (mực đêm) sang gradient dọc
//     "#364A58" (đỉnh) → "#122A3A" (đáy) — "#364A58" KHÔNG phải màu bịa mới,
//     đây CHÍNH LÀ giá trị `SidebarBackgroundCurrent` đã tính + kiểm tương
//     phản trong branding.desc (mực đêm sáng thêm 15%) — tái dùng một màu đã
//     được verify WCAG AA cho cả `titleColor`/`textColor` ở trên (branding.desc
//     đã chứng minh `textColor` #F7F6F1 đạt 8.52:1 và `titleColor` #F2C66D đạt
//     5.74:1 trên đúng màu "#364A58" này) — nên mọi điểm nội suy giữa 2 đầu
//     gradient (cả hai đều đã qua kiểm) vẫn an toàn tương phản, không cần tính
//     lại từ đầu.
//   - Một bản logo (logo.png) phóng to, xoay nhẹ, mờ gần hết (opacity 0.05),
//     neo góc dưới-phải và tràn một phần ra ngoài khung — watermark thương
//     hiệu rất nhẹ, kiểu các trình cài đặt cao cấp hay dùng, không chồng chữ
//     (độ mờ quá thấp để ảnh hưởng đọc) và không chiếm layout (anchor tuyệt
//     đối, z nằm dưới mọi Slide).
//   - Chấm chỉ số slide: thêm hiệu ứng "nở ra" (Behavior on width/color) cho
//     chấm ở slide hiện tại — đổi độ rộng + màu mượt khi chuyển slide, vẫn
//     đúng 4 chấm khớp 4 Slide như cũ, không đổi model.
//   - Slide 3 ("Everything you need, already installed"): thêm một hàng 3
//     icon nOffice (Writer/Calc/Impress) bên dưới đoạn chữ Việt — ảnh
//     TÁI DÙNG nguyên bộ icon đã duyệt/đang dùng thật trong icon theme hệ
//     thống (branding/icons/out/namioffice/*_1024.png, resize còn 160x160,
//     KHÔNG vẽ icon mới), minh hoạ đúng 3 app đã nêu tên trong câu chữ ngay
//     phía trên — không thêm chữ/nhãn mới (tránh phình bề mặt dịch), không
//     thêm icon cho nWeb/nMail vì KHÔNG có icon squircle cùng bộ
//     nhận diện cho 2 app đó (icon Firefox/Thunderbird gốc sẽ lệch phong
//     cách) — 2 app đó vẫn được nêu tên ở câu chữ như cũ.
//   - Kích thước/khoảng cách hàng icon dùng SỐ PIXEL CỐ ĐỊNH (không nhân theo
//     `presentation.height`) — ĐÚNG kiểu `s1Logo` (120x120 cố định) đã dùng
//     sẵn trong file này cho ảnh, giữ quy ước cũ: cỡ CHỮ theo tỉ lệ
//     `presentation.height`, cỡ ẢNH theo pixel cố định.
//
// verified_on_host: NO — vẫn chưa mở Calamares thật (môi trường soạn không
// có qemu/live-build/dev-kvm). Gradient/Behavior/anchors âm (bleed góc) đều
// là API lõi của QtQuick 2.0 (Rectangle.gradient, Behavior, NumberAnimation/
// ColorAnimation, Item.rotation) — không phụ thuộc property riêng của
// Slide.qml/Presentation.qml nên không có rủi ro "không thấy được qua biên
// file" đã ghi ở đoạn "AN TOÀN KÍCH THƯỚC CHỮ" phía trên. Rủi ro còn lại duy
// nhất là chiều cao: hàng icon mới ở Slide 3 được neo nối tiếp (anchors.top +
// topMargin) sau đoạn chữ Việt cuối cùng, CÙNG kiểu đã dùng cho mọi khối chữ
// khác trong file — nếu `presentation.height` thực tế nhỏ hơn ước tính, hàng
// icon có thể lấn vào vùng 10% luôn-trống phía dưới (nơi có chấm chỉ số
// slide) mà không có cách tự kiểm bằng mắt ở môi trường soạn này; không phải
// lỗi chặn cài đặt (slideshow chỉ là panel phụ) — cần xem lại trên một lần
// `lb build` + cài thật nếu thấy chật.
//
// POLISH 11/11/2026 (wave "Đông Sơn" — icon+installer dev) — CHỈ đổi màu +
// thêm một lớp ảnh nền, KHÔNG đổi cấu trúc Presentation/Slide/onActivate/
// onLeave, KHÔNG đổi 1 chữ nào trong 4 slide (EN chính + VI phụ giữ nguyên):
//   - Toàn bộ hex thương hiệu remap sang bộ token v3 "NaMiOS Đông Sơn"
//     (branding/kit/NaMi_Brand_DongSon_v1/05_design_tokens/colors.css) theo
//     bảng OLD→NEW: gradient nền "#364A58"→"#122A3A" (v2) → tái dùng ĐÚNG
//     `SidebarBackgroundCurrent`/`SidebarBackground` mới trong branding.desc
//     ("#274664"→"#092D4F", xem comment ở đó — v3 navy sáng 12% về trắng,
//     ĐÃ kiểm lại WCAG cho đúng bộ gold v3 này, không phải 15% như v2 nữa);
//     `titleColor`/chấm-đang-chọn "#F2C66D" (gold v2) → "#DEA93E" (token
//     gold v3, có trong bảng remap chính thức); dải nhấn trên cùng "#C93643"
//     (đỏ son v2) → "#DEA93E" (gold v3 — remap theo đúng nhánh "signature
//     accent" của quy tắc OLD→NEW, vì đây là một dải NHẤN trang trí, không
//     phải nút hành động); `textColor` "#F7F6F1" (gần trắng, không phải
//     token) → đúng token ivory v3 "#FFF9EF". logo.png watermark giữ
//     nguyên cơ chế (chỉ nội dung logo.png đổi sang biểu tượng trống đồng ở
//     bước khác của wave này).
//   - THÊM một lớp ẢNH NỀN mới (z: -3, dưới cả gradient) dùng 2 ảnh hệ thống
//     của brand kit (04_system_screens/installer-{welcome,progress}-
//     1920x1080.png, copy nguyên văn vào bg-welcome.png/bg-progress.png
//     cạnh file này): Slide 1 ("Welcome to NaMiOS") dùng bg-welcome.png,
//     Slide 2-4 dùng bg-progress.png — đúng yêu cầu "dùng nền welcome/
//     progress của kit trong slideshow". KHÔNG dùng toàn độ mờ (cả 2 ảnh
//     kit có sẵn chữ "NaMi"/câu chào baked-in, trùng/chồng với tiêu đề + 2
//     dòng song ngữ EN/VI đã soạn riêng cho từng slide trong file này) —
//     đặt opacity thấp (0.16, cùng bậc với 2 dải sóng teal/gold trang trí đã
//     có sẵn bên trong chính 2 ảnh đó, "opacity .14"/"opacity .10") để ảnh
//     kit chỉ đóng góp HOẠ TIẾT/MÀU SẮC nền (viền tròn trống đồng mờ, dải
//     sóng chim Đông Sơn), không đọc được chữ bên trong — gradient nền vẫn
//     vẽ ĐÈ LÊN TRÊN (z: -2) để đảm bảo tương phản chữ không đổi so với
//     trước (vẫn đúng các tỉ lệ WCAG đã kiểm ở branding.desc, vì gradient
//     chiếm phần lớn độ đục). Chuyển ảnh nền khi đổi slide dùng
//     `Behavior on opacity` (2 Image chồng nhau, không dùng binding đổi
//     `source` trực tiếp — đổi `source` giữa 2 ảnh khác nhau làm Image nạp
//     lại tức thời/giật hình, không mượt được bằng Behavior).
//   - verified_on_host: NO — chưa mở Calamares thật để xem độ mờ/độ tương
//     phản bằng mắt; 2 ảnh PNG 1920x1080 mới nặng ~100KB/ảnh, không rõ ảnh
//     hưởng thời gian nạp trang slideshow trên máy yếu đến đâu (chưa đo).

import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    id: presentation

    // Màu chữ/font mặc định cho mọi Slide con (Slide.qml đọc
    // `parent.textColor`/`parent.titleColor`/`parent.fontFamily` làm giá trị
    // mặc định riêng của nó — đặt một lần ở đây, không cần lặp lại mỗi Slide).
    // v3 "Đông Sơn": textColor = token ivory #FFF9EF; titleColor = token
    // gold #DEA93E (xem POLISH 11/11/2026 ở đầu file).
    textColor:  "#FFF9EF"
    titleColor: "#DEA93E"
    fontFamily: "Noto Sans"   // PRA-018/DESIGN-SYSTEM.md §2: không dùng phông
                               // thương mại (Segoe UI...), chỉ Noto Sans.

    function nextSlide() {
        presentation.goToNextSlide();
    }

    Timer {
        id: advanceTimer
        interval: 6500
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: nextSlide()
    }

    // ---- Hoạ tiết nền Đông Sơn, mờ dưới gradient (xem POLISH 11/11/2026
    // ở đầu file) — z: -3, LUÔN dưới cùng. 2 Image chồng nhau (không đổi
    // `source` trực tiếp) để `Behavior on opacity` chuyển mượt khi đổi
    // slide; `welcomeBg` hiện ở Slide 1, `progressBg` hiện ở Slide 2-4.
    Image {
        id: welcomeBg
        source: "bg-welcome.png"
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
        opacity: presentation.currentSlide === 0 ? 0.16 : 0.0
        Behavior on opacity { NumberAnimation { duration: 260 } }
        z: -3
    }
    Image {
        id: progressBg
        source: "bg-progress.png"
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
        opacity: presentation.currentSlide === 0 ? 0.0 : 0.16
        Behavior on opacity { NumberAnimation { duration: 260 } }
        z: -3
    }

    // ---- Nền toàn khung, kiểu "Windows 11 Setup" (navy NaMiOS) ----
    // z: -2 để LUÔN ở dưới mọi Slide (nhưng TRÊN hoạ tiết Đông Sơn, z: -3),
    // bất kể thứ tự khai báo trong file (và dưới cả watermark logo ngay bên
    // dưới, z: -1).
    // Gradient dọc "#274664" (đỉnh, sáng hơn) → "#092D4F" (đáy, navy v3 gốc)
    // — xem comment POLISH 11/11/2026 ở đầu file: "#274664" là màu ĐÃ CÓ
    // SẴN + đã kiểm tương phản trong branding.desc (không bịa màu mới).
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#274664" }
            GradientStop { position: 1.0; color: "#092D4F" }
        }
        z: -2
    }

    // Watermark logo rất mờ, neo góc dưới-phải, tràn một phần ra ngoài khung
    // (anchors âm) + xoay nhẹ — điểm nhấn thương hiệu rất kín đáo, không
    // chồng chữ (opacity 0.05) và không ảnh hưởng layout của Slide (anchor
    // tuyệt đối theo `parent` = Presentation, không theo Slide).
    Image {
        source: "logo.png"
        width: presentation.height * 1.1
        height: width
        fillMode: Image.PreserveAspectFit
        opacity: 0.05
        rotation: -8
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: -width * 0.22
        anchors.bottomMargin: -height * 0.22
        z: -1
    }

    // Dải nhấn vàng (gold v3, token signature-accent) mỏng trên cùng (gợi
    // phong cách thanh accent của Windows 11 Setup) — nằm trong 20% trên
    // cùng mà Slide.qml luôn để trống, không chồng nội dung slide.
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 6
        color: "#DEA93E"
        z: 1
    }

    // Chấm chỉ vị trí slide ở dưới cùng (nằm trong 10% dưới cùng luôn
    // trống) — điểm nhấn "cao cấp" thường thấy ở các trình cài đặt hiện đại.
    // Cố định model: 4 — PHẢI khớp đúng số `Slide { ... }` khai báo dưới
    // đây (không dùng `presentation.slides.length` để tránh phụ thuộc thời
    // điểm property đó được gán trong `Component.onCompleted` của
    // Presentation.qml).
    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: parent.height * 0.035
        spacing: 10
        z: 2

        Repeater {
            model: 4
            Rectangle {
                // Chấm ở slide hiện tại "nở" thành viên thuốc (pill) 22px
                // thay vì chấm tròn 9px — điểm nhấn "cao cấp" hay thấy ở
                // trình cài/app hiện đại. Behavior làm mượt cả đổi độ rộng
                // lẫn đổi màu khi chuyển slide (220ms, cùng nhịp easing).
                width: index === presentation.currentSlide ? 22 : 9
                height: 9; radius: 5
                color: index === presentation.currentSlide ? "#DEA93E" : "#3A4F60"
                Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                Behavior on color { ColorAnimation { duration: 220 } }
            }
        }
    }

    // ================= Slide 1 — Chào mừng =================
    Slide {
        Image {
            id: s1Logo
            source: "logo.png"
            width: 120; height: 120
            fillMode: Image.PreserveAspectFit
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: parent.height * 0.04
        }
        Text {
            id: s1TitleEn
            anchors.top: s1Logo.bottom
            anchors.topMargin: 22
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("Welcome to NaMi")
            color: "#DEA93E"
            font.family: "Noto Sans"
            font.bold: true
            font.pixelSize: presentation.height * 0.065
        }
        Text {
            id: s1BodyEn
            anchors.top: s1TitleEn.bottom
            anchors.topMargin: 14
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.85
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("Setting up your computer — this will only take a few minutes.")
            color: "#FFF9EF"
            font.family: "Noto Sans"
            font.pixelSize: presentation.height * 0.040
        }
        Text {
            anchors.top: s1BodyEn.bottom
            anchors.topMargin: 10
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.85
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("Đang cài NaMi cho bạn… chỉ vài phút nữa là xong.")
            color: "#B2B9BA"
            font.family: "Noto Sans"
            font.italic: true
            font.pixelSize: presentation.height * 0.030
        }
    }

    // ============= Slide 2 — NaMiOS là gì =============
    Slide {
        Text {
            id: s2TitleEn
            anchors.top: parent.top
            anchors.topMargin: parent.height * 0.08
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("A free, modern OS — made for Vietnam")
            color: "#DEA93E"
            font.family: "Noto Sans"
            font.bold: true
            font.pixelSize: presentation.height * 0.058
        }
        Text {
            id: s2BodyEn
            anchors.top: s2TitleEn.bottom
            anchors.topMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.85
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("No license fees, no activation. A secure, open-source foundation, with Vietnamese language and keyboard built in from day one.")
            color: "#FFF9EF"
            font.family: "Noto Sans"
            font.pixelSize: presentation.height * 0.040
        }
        Text {
            anchors.top: s2BodyEn.bottom
            anchors.topMargin: 12
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.85
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("Miễn phí, an toàn, không cần bản quyền. Mặc định tiếng Việt, giờ Việt Nam — gõ chữ Việt được ngay.")
            color: "#B2B9BA"
            font.family: "Noto Sans"
            font.italic: true
            font.pixelSize: presentation.height * 0.030
        }
    }

    // ============= Slide 3 — App có sẵn =============
    Slide {
        Text {
            id: s3TitleEn
            anchors.top: parent.top
            anchors.topMargin: parent.height * 0.08
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("Everything you need, already installed")
            color: "#DEA93E"
            font.family: "Noto Sans"
            font.bold: true
            font.pixelSize: presentation.height * 0.058
        }
        Text {
            id: s3BodyEn
            anchors.top: s3TitleEn.bottom
            anchors.topMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.85
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("nDoc, nSheet, nSlide for office work; nWeb (Firefox) and nMail (Thunderbird) to browse and email; nMedia to play music and videos.")
            color: "#FFF9EF"
            font.family: "Noto Sans"
            font.pixelSize: presentation.height * 0.036
        }
        Text {
            id: s3BodyVi
            anchors.top: s3BodyEn.bottom
            anchors.topMargin: 12
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.85
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("NaMi có sẵn phần mềm soạn thảo, lướt web, email, nghe nhạc, xem video — dùng ngay, không cần cài thêm.")
            color: "#B2B9BA"
            font.family: "Noto Sans"
            font.italic: true
            font.pixelSize: presentation.height * 0.030
        }

        // Hàng icon nOffice (Writer/Calc/Impress) — minh hoạ 3 app đã
        // nêu tên ở s3BodyEn phía trên, tái dùng nguyên icon theme hệ thống
        // đã duyệt (xem comment POLISH 10/11/2026 ở đầu file). Neo nối tiếp
        // sau khối chữ Việt cuối cùng, kích thước/khoảng cách CỐ ĐỊNH theo
        // pixel (đúng quy ước ảnh trong file này — xem s1Logo).
        Row {
            anchors.top: s3BodyVi.bottom
            anchors.topMargin: 22
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 24

            Image {
                source: "app-writer.png"
                width: 56; height: 56
                fillMode: Image.PreserveAspectFit
            }
            Image {
                source: "app-calc.png"
                width: 56; height: 56
                fillMode: Image.PreserveAspectFit
            }
            Image {
                source: "app-impress.png"
                width: 56; height: 56
                fillMode: Image.PreserveAspectFit
            }
        }
    }

    // ============= Slide 4 — Sắp xong =============
    Slide {
        Text {
            id: s4TitleEn
            anchors.top: parent.top
            anchors.topMargin: parent.height * 0.08
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("Almost there")
            color: "#DEA93E"
            font.family: "Noto Sans"
            font.bold: true
            font.pixelSize: presentation.height * 0.065
        }
        Text {
            id: s4BodyEn
            anchors.top: s4TitleEn.bottom
            anchors.topMargin: 20
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.85
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("Once installation finishes, your computer will restart into NaMi. Sign in with the account you just created to get started.")
            color: "#FFF9EF"
            font.family: "Noto Sans"
            font.pixelSize: presentation.height * 0.040
        }
        Text {
            anchors.top: s4BodyEn.bottom
            anchors.topMargin: 12
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.85
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("Cài xong, máy sẽ khởi động lại vào NaMi. Đăng nhập bằng tài khoản bạn vừa tạo là xong!")
            color: "#B2B9BA"
            font.family: "Noto Sans"
            font.italic: true
            font.pixelSize: presentation.height * 0.030
        }
    }

    // API v2 (slideshowAPI: 2 trong branding.desc): Calamares gọi hai hàm
    // này trực tiếp (xem comment đầu file) — KHÔNG cần đăng ký/connect gì
    // thêm. Luôn quay về slide đầu khi mở lại trang slideshow.
    function onActivate() {
        presentation.currentSlide = 0;
    }

    function onLeave() {
    }
}
