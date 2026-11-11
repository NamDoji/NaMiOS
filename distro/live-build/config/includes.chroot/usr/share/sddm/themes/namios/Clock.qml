// NaMiOS — dong ho + ngay cho man hinh dang nhap SDDM.
//
// Dung Qt.formatDateTime()/Qt.formatDate() voi cac ma dinh dang locale-aware
// (dddd/MMMM) de TU DONG hien ten ngay/thang theo locale HE THONG cua phien
// greeter (LANG/LC_TIME) — tieng Viet khi he thong dat vi_VN, English khi he
// thong dat en_US, KHONG can bang dich tay. Day la ly do chinh cho yeu cau
// "VN/EN friendly" cua dong ho (khac voi cac label tinh khac trong Main.qml
// dung chuoi song ngu viet san, vi dong ho phu thuoc gio/ngay dong nen
// khong the viet san).
//
// WAVE "DONG SON" 11/11/2026: them property "compact" — Main.qml chuyen dong
// ho tu khoi can-giua-man-hinh (chu gio 64px) ra goc tren-phai nho gon (doi
// xung voi badge "NaMiOS" goc tren-trai), nen can 1 bo kich thuoc chu nho hon
// khi compact=true. Mau mac dinh (fallback) cap nhat tu #F7F6F1 -> #FFF9EF
// (ivory v3) — tuy Main.qml LUON truyen timeColor/dateColor tuong minh nen
// gia tri mac dinh o day hau nhu khong bao gio duoc dung thuc te, van doi
// cho dong bo/sach se voi phan con lai cua theme.
//
// verified_on_host: NO — chua xac nhan dinh dang 'dddd, d MMMM yyyy' ra chu
// tieng Viet dung (vd "Thứ Ba, 10 tháng 11 2026") tren may/QEMU that voi
// locale vi_VN cua ban build nay.
import QtQuick 2.15

Column {
    id: root
    spacing: compact ? 2 : 6

    property date now: new Date()
    property alias timeColor: timeLabel.color
    property alias dateColor: dateLabel.color
    property bool compact: false

    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: root.now = new Date()
    }

    Text {
        id: timeLabel
        anchors.horizontalCenter: parent.horizontalCenter
        text: Qt.formatDateTime(root.now, "HH:mm")
        color: "#FFF9EF" // fg ivory v3 (theme.conf foregroundColor la nguon that)
        font.family: "Inter"
        font.pixelSize: root.compact ? 22 : 64
        font.weight: Font.DemiBold
    }

    Text {
        id: dateLabel
        anchors.horizontalCenter: parent.horizontalCenter
        text: Qt.formatDate(root.now, "dddd, d MMMM yyyy")
        color: "#B7C4CF" // fg-dim
        font.family: "Inter"
        font.pixelSize: root.compact ? 12 : 17
    }
}
