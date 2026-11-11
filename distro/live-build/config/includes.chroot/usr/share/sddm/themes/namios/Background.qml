// NaMiOS — SDDM Background cho theme "namios".
//
// KHAC VOI Background.qml goc cua theme "breeze" (KDE/plasma-desktop
// sddm-theme/Background.qml, v6.3.6 — da doc truc tiep 10/11/2026): ban goc
// dung mot state-machine (type=="image" ? hien Image : hien Rectangle mau)
// NEN NEU type=="image" MA anh khong tai duoc, Rectangle mau KHONG BAO GIO
// hien -> man hinh den/trong (rui ro da ghi chu trong
// includes.chroot/usr/share/sddm/themes/breeze/theme.conf.user). Ban nay
// BO state-machine do: Rectangle mau LUON anchors.fill lam lop DUOI CUNG;
// Image chi "visible" khi status===Ready, nam CHONG LEN tren — anh thieu/
// hong/duong dan sai => Image khong Ready => van thay mau nen, KHONG BAO
// GIO den. Day la cai thien CHU DICH, khong phai thieu sot.
//
// An toan render: khong dung shader/hieu ung GL nao (khong GraphicalEffects,
// khong ShaderEffect) — Rectangle.gradient la kieu Qt Quick thuan, ve duoc
// tren CA software renderer (QT_QUICK_BACKEND=software, dung cho QEMU/TCG
// khong GPU — xem hook 0400-qemu-desktop-autologin.hook.chroot).
//
// WAVE "DONG SON" 11/11/2026: mau mac dinh + lop phu gradient doi tu navy v2
// (#122A3A) sang navy v3 (#092D4F) — xem ghi chu day du o theme.conf cung
// thu muc (ly do sieu-xi QD "sen khong dat nen den" CHI cho man hinh nay).
//
// verified_on_host: NO.
import QtQuick 2.15

Item {
    id: root

    property alias backgroundColor: base.color
    property alias source: photo.source

    Rectangle {
        id: base
        anchors.fill: parent
        color: "#092D4F" // navy v3 "Dong Son" — gia tri mac dinh khi Main.qml
                          // khong truyen backgroundColor (khong nen xay ra, nhung
                          // khong de trong/undefined).
    }

    Image {
        id: photo
        anchors.fill: parent
        sourceSize.width: parent.width
        sourceSize.height: parent.height
        fillMode: Image.PreserveAspectCrop
        smooth: true
        asynchronous: true
        cache: true
        visible: status === Image.Ready
    }

    // Lop phu gradient mực đêm — tang tuong phan cho chu/dong ho/o mat khau
    // o MOI anh nen bat ke do sang cua anh, khong can shader (an toan cho
    // software rendering). Dam hon o tren/duoi (noi dat chu+footer), nhat
    // hon o giua (noi anh nen "tho" nhat).
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(9 / 255, 45 / 255, 79 / 255, 0.55) }
            GradientStop { position: 0.42; color: Qt.rgba(9 / 255, 45 / 255, 79 / 255, 0.18) }
            GradientStop { position: 1.0; color: Qt.rgba(9 / 255, 45 / 255, 79 / 255, 0.62) }
        }
    }
}
