"""Catalog song ngữ riêng của ``namios_antoan`` — đăng ký qua
``namios_i18n.add_catalog`` khi import (đúng quy ước các module khác, xem
``namios_assistant._i18n``). KHÔNG sửa trực tiếp ``namios_i18n/locale/
{vi,en}.json`` (sở hữu bởi ``namios_i18n``).

Nhóm key: ``antoan.ui.*`` (chrome giao diện PySide6, ``ui.py``) +
``antoan.ui.about.*`` (nội dung "Giới thiệu" — giải thích mô hình bảo vệ
Linux + tuyên bố giới hạn trung thực, SEC-1 acceptance criteria)."""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_ABOUT_BODY_VI = """NaMi KHÔNG có một "phần mềm diệt virus" chạy nền 24/7 kiểu Windows —
thay vào đó, Linux tự bảo vệ bằng NHIỀU LỚP cộng lại:

  • Quyền user thường (không chạy hằng ngày bằng quyền quản trị) — một
    chương trình độc hại thường không tự nâng được quyền để phá cả máy.
  • Tường lửa (UFW) chặn kết nối lạ ĐẾN máy bạn.
  • AppArmor giới hạn những gì một ứng dụng CÓ hồ sơ được phép làm.
  • Cập nhật bản vá an toàn tự động — vá lỗ hổng đã biết sớm.
  • Quét virus (ClamAV) THEO YÊU CẦU khi bạn nghi ngờ một tệp/thư mục cụ
    thể — không quét thường trú (xem lý do trong thẻ "Quét virus").
  • Sao lưu (Kup) để có đường phục hồi khi có sự cố, kể cả sự cố không liên
    quan tới virus (ổ cứng hỏng, xoá nhầm, lỗi cập nhật).

TUYÊN BỐ GIỚI HẠN TRUNG THỰC — 7 điều Trung tâm An toàn KHÔNG hứa:

  1. KHÔNG hứa chống được 100% virus/mã độc, kể cả khi ClamAV vừa báo "sạch".
  2. "Quét sạch" KHÔNG phải bằng chứng máy không bị xâm nhập — ClamAV chỉ
     nhận diện mẫu đã biết, không phát hiện được mọi kỹ thuật tấn công.
  3. ClamAV CHỈ quét theo yêu cầu (on-demand) — KHÔNG quét thường trú; một
     tệp độc hại có thể nằm trên đĩa một thời gian trước khi bạn chủ động
     quét nó.
  4. AppArmor KHÔNG phải tường chặn tuyệt đối — chỉ ứng dụng ĐÃ CÓ hồ sơ mới
     bị giới hạn; ứng dụng chưa có hồ sơ riêng vẫn chạy với quyền user bình
     thường.
  5. Tường lửa mặc định chỉ chặn kết nối ĐẾN — không chặn được mã độc đã
     chạy sẵn trên máy tự kết nối RA ngoài (outgoing mặc định cho phép).
  6. Sao lưu KHÔNG tự động nếu bạn chưa từng mở Cài đặt Sao lưu để chọn ổ
     đích — chưa cấu hình thì chưa có bản sao lưu nào để phục hồi.
  7. Cập nhật tự động chỉ áp dụng gói trong nhóm an toàn (-security), KHÔNG
     tự khởi động lại máy — một số bản vá (nhân/thư viện lõi) cần bạn tự
     khởi động lại mới có hiệu lực đầy đủ.

Hãy luôn cẩn trọng khi mở tệp tải về, cắm USB lạ, hoặc chạy ứng dụng Windows
qua Wine — đây là những nguồn phổ biến mang mã không an toàn mà không công
cụ nào chặn được tuyệt đối."""

_ABOUT_BODY_EN = """NaMi does not run a 24/7 "antivirus" background service like Windows —
instead, Linux protects itself through SEVERAL LAYERS working together:

  • Regular user permissions (you don't run as admin day to day) — malware
    usually cannot escalate privileges to take over the whole machine.
  • Firewall (UFW) blocks unsolicited incoming connections.
  • AppArmor restricts what an application WITH a profile is allowed to do.
  • Automatic security patches — known vulnerabilities get patched early.
  • ClamAV virus scan ON DEMAND, when you suspect a specific file/folder —
    not an always-on scan (see the "Virus scan" card for why).
  • Backup (Kup) gives you a recovery path for incidents unrelated to
    viruses too (disk failure, accidental deletion, a bad update).

HONEST LIMITATIONS STATEMENT — 7 things this Security Center never promises:

  1. It does NOT promise to block 100% of viruses/malware, even right after
     ClamAV reports "clean".
  2. A "clean scan" is NOT proof the machine was never compromised — ClamAV
     only recognizes known signatures, not every attack technique.
  3. ClamAV is ON-DEMAND ONLY — no always-on scanning; a malicious file can
     sit on disk for a while before you actively scan it.
  4. AppArmor is NOT an absolute wall — only applications that already have
     a profile are restricted; apps without one run with normal user rights.
  5. The default firewall only blocks INCOMING connections — it cannot stop
     malware already running on the machine from connecting OUT (outgoing
     is allowed by default).
  6. Backups do NOT happen automatically until you open Backup Settings and
     pick a destination — with nothing configured, there is nothing to
     restore from.
  7. Automatic updates only apply security-pocket packages and never reboot
     the machine for you — some patches (kernel/core libraries) only fully
     take effect after you restart.

Always be careful with downloaded files, unknown USB drives, or Windows apps
run through Wine — these are common sources of unsafe code that no tool can
block with absolute certainty."""

_VI: dict[str, str] = {
    "antoan.ui.window_title": "Trung tâm An toàn — NaMi",
    "antoan.ui.header.title": "Trung tâm An toàn",
    "antoan.ui.header.subtitle": (
        "Xem trạng thái THẬT của máy (cập nhật, tường lửa, AppArmor, quét virus, "
        "sao lưu) và mở đúng công cụ — không có dấu tích xanh giả."
    ),
    "antoan.ui.button.refresh_all": "Làm mới tất cả",
    "antoan.ui.button.refresh": "Làm mới",
    "antoan.ui.button.about": "Giới thiệu",
    "antoan.ui.about.title": "Giới thiệu — mô hình bảo vệ của NaMi",
    "antoan.ui.about.body": _ABOUT_BODY_VI,
    "antoan.ui.about.close": "Đóng",
    "antoan.ui.footer.disclaimer": (
        "NaMi KHÔNG hứa chống được 100% virus/mã độc. Hãy cẩn trọng với tệp "
        "tải về, USB lạ, và app Windows chạy qua Wine."
    ),
    "antoan.ui.status.checking": "Đang kiểm tra…",
    "antoan.ui.status.working": "Đang xử lý…",
    "antoan.ui.card.update.title": "Cập nhật",
    "antoan.ui.card.update.button.open": "Mở Trung tâm cập nhật",
    "antoan.ui.card.firewall.title": "Tường lửa (UFW)",
    "antoan.ui.card.firewall.button.enable": "Bật tường lửa",
    "antoan.ui.card.firewall.button.detail": "Xem chi tiết luật (cần quyền quản trị)",
    "antoan.ui.card.firewall.confirm_enable": (
        "Bật tường lửa (UFW)? Hệ thống sẽ hỏi mật khẩu quản trị. Việc này chặn "
        "kết nối lạ đến máy bạn, không ảnh hưởng kết nối ra ngoài (web, tải "
        "tệp...)."
    ),
    "antoan.ui.card.apparmor.title": "AppArmor",
    "antoan.ui.card.apparmor.button.detail": "Xem chi tiết hồ sơ đang nạp (cần quyền quản trị)",
    "antoan.ui.card.antivirus.title": "Quét virus (ClamAV)",
    "antoan.ui.card.antivirus.button.scan": "Quét thư mục này...",
    "antoan.ui.card.antivirus.button.update_sig": "Cập nhật chữ ký",
    "antoan.ui.card.antivirus.dialog_title": "Chọn thư mục cần quét",
    "antoan.ui.card.antivirus.scanning": "Đang quét — có thể mất vài phút tuỳ số lượng tệp…",
    "antoan.ui.card.backup.title": "Sao lưu (Kup)",
    "antoan.ui.card.backup.button.open": "Mở cài đặt Sao lưu",
    "antoan.ui.dialog.result.title_ok": "Hoàn tất",
    "antoan.ui.dialog.result.title_fail": "Không thực hiện được",
    "antoan.ui.card.not_installed_prefix": "CHƯA CÀI — ",
    "antoan.ui.card.install_hint_prefix": "Cách cài: ",
}

_EN: dict[str, str] = {
    "antoan.ui.window_title": "Security Center — NaMi",
    "antoan.ui.header.title": "Security Center",
    "antoan.ui.header.subtitle": (
        "See the REAL status of this machine (updates, firewall, AppArmor, "
        "virus scan, backup) and open the right tool — no fake green checks."
    ),
    "antoan.ui.button.refresh_all": "Refresh all",
    "antoan.ui.button.refresh": "Refresh",
    "antoan.ui.button.about": "About",
    "antoan.ui.about.title": "About — NaMi's protection model",
    "antoan.ui.about.body": _ABOUT_BODY_EN,
    "antoan.ui.about.close": "Close",
    "antoan.ui.footer.disclaimer": (
        "NaMi does NOT promise to block 100% of viruses/malware. Be careful "
        "with downloaded files, unknown USB drives, and Windows apps run "
        "through Wine."
    ),
    "antoan.ui.status.checking": "Checking…",
    "antoan.ui.status.working": "Working…",
    "antoan.ui.card.update.title": "Updates",
    "antoan.ui.card.update.button.open": "Open Update Center",
    "antoan.ui.card.firewall.title": "Firewall (UFW)",
    "antoan.ui.card.firewall.button.enable": "Enable firewall",
    "antoan.ui.card.firewall.button.detail": "View rule details (needs admin)",
    "antoan.ui.card.firewall.confirm_enable": (
        "Enable the firewall (UFW)? The system will ask for your admin "
        "password. This blocks unsolicited incoming connections; it does not "
        "affect outgoing connections (browsing, downloads...)."
    ),
    "antoan.ui.card.apparmor.title": "AppArmor",
    "antoan.ui.card.apparmor.button.detail": "View loaded profiles (needs admin)",
    "antoan.ui.card.antivirus.title": "Virus scan (ClamAV)",
    "antoan.ui.card.antivirus.button.scan": "Scan this folder...",
    "antoan.ui.card.antivirus.button.update_sig": "Update signatures",
    "antoan.ui.card.antivirus.dialog_title": "Choose a folder to scan",
    "antoan.ui.card.antivirus.scanning": "Scanning — this can take a few minutes depending on file count…",
    "antoan.ui.card.backup.title": "Backup (Kup)",
    "antoan.ui.card.backup.button.open": "Open Backup settings",
    "antoan.ui.dialog.result.title_ok": "Done",
    "antoan.ui.dialog.result.title_fail": "Could not complete",
    "antoan.ui.card.not_installed_prefix": "NOT INSTALLED — ",
    "antoan.ui.card.install_hint_prefix": "How to install: ",
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
