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

import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    id: presentation

    // Màu chữ/font mặc định cho mọi Slide con (Slide.qml đọc
    // `parent.textColor`/`parent.titleColor`/`parent.fontFamily` làm giá trị
    // mặc định riêng của nó — đặt một lần ở đây, không cần lặp lại mỗi Slide).
    textColor:  "#F7F6F1"
    titleColor: "#F2C66D"
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

    // ---- Nền toàn khung, kiểu "Windows 11 Setup" (mực đêm NaMiOS) ----
    // z: -1 để LUÔN ở dưới mọi Slide, bất kể thứ tự khai báo trong file.
    Rectangle {
        anchors.fill: parent
        color: "#122A3A"
        z: -1
    }

    // Dải nhấn đỏ son mỏng trên cùng (gợi phong cách thanh accent của
    // Windows 11 Setup) — nằm trong 20% trên cùng mà Slide.qml luôn để
    // trống, không chồng nội dung slide.
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 6
        color: "#C93643"
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
                width: 9; height: 9; radius: 5
                color: index === presentation.currentSlide ? "#F2C66D" : "#3A4F60"
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
            text: qsTr("Welcome to NaMiOS")
            color: "#F2C66D"
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
            color: "#F7F6F1"
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
            text: qsTr("Chào mừng đến với NaMiOS — máy của bạn đang được cài đặt, chỉ mất vài phút.")
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
            color: "#F2C66D"
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
            color: "#F7F6F1"
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
            text: qsTr("Hệ điều hành miễn phí, không cần bản quyền hay kích hoạt; nền tảng mã nguồn mở bảo mật; tiếng Việt và bộ gõ có sẵn ngay từ đầu.")
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
            color: "#F2C66D"
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
            text: qsTr("NaMiWriter, NaMiSheet, NaMiSlides for office work; NaMiBrowser (Firefox) and NaMiMail (Thunderbird) to browse and email; NaMiMedia to play music and videos.")
            color: "#F7F6F1"
            font.family: "Noto Sans"
            font.pixelSize: presentation.height * 0.036
        }
        Text {
            anchors.top: s3BodyEn.bottom
            anchors.topMargin: 12
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.85
            horizontalAlignment: Text.Center
            wrapMode: Text.WordWrap
            text: qsTr("Soạn thảo, bảng tính, trình chiếu; trình duyệt và email; nghe nhạc, xem video — tất cả đã có sẵn, không cần cài thêm.")
            color: "#B2B9BA"
            font.family: "Noto Sans"
            font.italic: true
            font.pixelSize: presentation.height * 0.030
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
            color: "#F2C66D"
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
            text: qsTr("Once installation finishes, your computer will restart into NaMiOS. Sign in with the account you just created to get started.")
            color: "#F7F6F1"
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
            text: qsTr("Cài đặt xong, máy sẽ khởi động lại vào NaMiOS — đăng nhập bằng tài khoản bạn vừa tạo để bắt đầu.")
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
