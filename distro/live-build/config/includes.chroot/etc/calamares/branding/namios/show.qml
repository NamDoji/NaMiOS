// NaMiOS — slideshow QML hiển thị trong màn hình "Phase 2 — Install" của
// Calamares (lúc file đang được copy lên đĩa). Mô phỏng đúng cấu trúc QML
// gốc của Calamares (import calamares.slideshow 1.0; Presentation { Slide
// {...} }; onActivate()/onLeave() cho API v2) — đối chiếu trực tiếp với
// src/branding/default/show.qml của chính dự án Calamares (tra cứu
// 09/11/2026, xem SPDX gốc bên dưới để biết cấu trúc tham khảo).
//
// Nội dung CHỈ 3 câu tiếng Việt ngắn, không có logic phức tạp/binding rủi ro
// — nếu QML này lỗi, theo tài liệu Calamares thì khung "exec" vẫn tiếp tục
// cài đặt (slideshow chỉ là panel phụ, không phải bước cài), nhưng CHƯA
// được xác nhận bằng mắt trên một lần cài thật (verified_on_host: NO).
//
// SPDX-FileCopyrightText: 2026 NaMiOS (Đỗ Chí Cường, Đỗ Bảo Nam)
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    id: presentation

    function nextSlide() {
        presentation.goToNextSlide();
    }

    Timer {
        id: advanceTimer
        interval: 6000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: nextSlide()
    }

    Slide {
        Image {
            id: namiosLogo
            source: "logo.png"
            width: 140; height: 140
            fillMode: Image.PreserveAspectFit
            anchors.centerIn: parent
        }
        Text {
            anchors.horizontalCenter: namiosLogo.horizontalCenter
            anchors.top: namiosLogo.bottom
            anchors.topMargin: 16
            text: "Chào mừng đến với NaMiOS — đang cài đặt máy tính của bạn..."
            wrapMode: Text.WordWrap
            width: presentation.width
            horizontalAlignment: Text.Center
        }
    }

    Slide {
        centeredText: qsTr(
            "Bộ gõ tiếng Việt, Soạn thảo/Bảng tính/Trình chiếu và Trung tâm phần mềm đã có sẵn — không cần cài thêm gì khi mở máy lần đầu.")
    }

    Slide {
        centeredText: qsTr(
            "Sau khi cài xong, máy sẽ khởi động vào màn hình đăng nhập SDDM bình thường — bạn đăng nhập bằng tài khoản vừa tạo ở bước trước.")
    }

    // API v2: onActivate()/onLeave() (xem Calamares Wiki "Deploy
    // Configuration" + default/show.qml). Luôn quay về slide đầu khi mở lại.
    function onActivate() {
        presentation.currentSlide = 0;
    }

    function onLeave() {
    }
}
