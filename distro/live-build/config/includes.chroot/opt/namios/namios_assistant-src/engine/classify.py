"""Phân loại một đoạn văn bản lỗi (tiếng Việt/tiếng Anh trộn lẫn) về một
MẢNG hệ thống (subsystem) — bước đầu tiên của ``AssistantEngine.ask`` để thu
hẹp phạm vi tìm trong KB ngoại tuyến + cho online backend biết ngữ cảnh.

Thuật toán CỐ Ý đơn giản (đếm từ khoá xuất hiện trong văn bản, không NLP/
không mô hình): dễ kiểm chứng, không phụ thuộc mạng/model, chạy tức thời.
Đây KHÔNG phải bộ phân loại chính xác tuyệt đối — chỉ là một GỢI Ý (hint) để
xếp hạng kết quả KB, không phải quyết định cuối cùng (``KnowledgeBase.find_matches``
vẫn quét toàn bộ entry, subsystem chỉ cộng thêm điểm ưu tiên).

``SUBSYSTEM_DISPLAY_NAMES`` + ``subsystem_display_name()`` thêm ở đợt nâng cấp
11/11/2026 (Wave "chatbot mạnh hơn") — dùng để HIỂN THỊ tên mảng bằng chữ cho
người dùng đọc (vd dòng "Đã phát hiện: mảng mạng" ở ``engine/offline_backend.py``)
thay vì lộ ra id kỹ thuật thô (``"network"``). Tách khỏi KB nội dung vì đây là
nhãn CHROME (cố định, không đổi theo entry) — cùng tinh thần phân tách
chrome/nội dung đã ghi ở docstring ``_i18n.py``."""

from __future__ import annotations

from typing import Literal

from namios_assistant.engine.knowledge_base import fold_accents

__all__ = [
    "SUBSYSTEM_KEYWORDS",
    "SUBSYSTEM_DISPLAY_NAMES",
    "classify_subsystem",
    "subsystem_display_name",
    "CatalogIntent",
    "INSTALL_REQUEST_KEYWORDS",
    "DRIVER_REQUEST_KEYWORDS",
    "classify_catalog_intent",
]


#: Mảng hệ thống -> danh sách từ khoá (VI + EN trộn chung, so khớp substring
#: không phân biệt hoa/thường) hay xuất hiện trong lỗi thuộc mảng đó. Thêm
#: mảng mới: thêm một dòng ở đây + gắn ``subsystem`` tương ứng trong KB
#: (``kb/starter_kb.json``) — hai nơi này độc lập, không bắt buộc khớp 1-1
#: (một entry KB có thể đúng dù subsystem không nằm trong danh sách đoán được).
#:
#: THỨ TỰ các mảng ở đây CÓ Ý NGHĨA: khi hai mảng khớp cùng số từ khoá, mảng
#: khai báo TRƯỚC thắng (``classify_subsystem`` dùng so sánh ``>`` chặt). Vài
#: cặp cố ý xếp để phá hoà hợp lý: ``screenshot`` ĐỨNG TRƯỚC ``display`` để
#: "chụp màn hình" không bị nuốt về mảng màn hình (cả hai cùng chứa "màn
#: hình"); ``wine`` đứng trước ``software`` để "cài phần mềm windows" ưu tiên
#: chạy-app-Windows thay vì cài-app-thường.
SUBSYSTEM_KEYWORDS: dict[str, tuple[str, ...]] = {
    "boot": (
        "grub", "boot", "khởi động", "plymouth", "splash", "black screen",
        "màn hình đen", "bios", "uefi", "mbr", "initramfs",
    ),
    "network": (
        "wifi", "wi-fi", "mạng", "network", "dns", "ip ", "ethernet",
        "vpn", "proxy", "modem", "router", "rfkill", "ping", "internet",
        "nmcli", "networkmanager", "địa chỉ ip", "cáp mạng", "dây mạng",
        "cable unplugged", "quên mật khẩu wifi", "kết nối wifi", "wi fi",
        "kết nối mạng", "vào mạng", "bắt wifi", "nối wifi", "mạng không dây",
        "không có internet", "mất mạng",
    ),
    # ĐẶT TRƯỚC "display": "chụp màn hình" chứa "màn hình" nên nếu display đi
    # trước sẽ thắng hoà sai (xem ghi chú thứ tự ở trên).
    "screenshot": (
        "chụp màn hình", "chụp ảnh màn hình", "ảnh chụp màn hình",
        "chụp hình màn hình", "chụp lại màn hình", "screenshot", "screen shot",
        "print screen", "prtsc", "prt sc", "spectacle", "chụp vùng màn hình",
    ),
    "display": (
        "màn hình", "display", "monitor", "resolution", "độ phân giải",
        "kwin", "wayland", "x11", "nvidia", "amdgpu", "gpu", "hdmi",
        "displayport", "card đồ hoạ", "card đồ họa", "máy chiếu",
        "projector", "nhân đôi", "mở rộng", "trình chiếu", "chiếu màn hình",
        "usb-c", "vga", "chữ quá nhỏ", "chữ quá to", "chữ nhỏ", "chữ to",
        "phóng to giao diện", "tỉ lệ hiển thị", "tỷ lệ hiển thị", "scaling",
        "màn hình thứ hai", "màn hình ngoài", "màn hình phụ",
    ),
    "wine": (
        "wine", "winetricks", "prefix", ".exe", ".dll", "app windows",
        "ứng dụng windows", "phần mềm windows", "vcruntime", "msvcp",
        "chạy phần mềm windows", "cài phần mềm windows", "mở file exe",
        "chạy file exe", "cài app windows", "nrun", "chương trình windows",
        "game windows",
    ),
    "office": (
        "namioffice", "libreoffice", "writer", "calc", "impress", "docx",
        "xlsx", "pptx", "tài liệu", "document", "font", "times new roman",
        "khoá", "lock",
    ),
    "print": (
        # LƯU Ý: không dùng từ khoá đơn "in " (không dấu phân cách rõ) — nó
        # là substring của rất nhiều từ không liên quan tới in ấn ("pin",
        # "nhìn", "xin", "tin"...) nên bị đổi thành các cụm từ dài hơn, đặc
        # trưng hơn (phát hiện lúc thêm mảng "power" có "pin" làm từ khoá —
        # 11/11/2026).
        "máy in", "printer", "cups", "print", "hàng đợi", "queue",
        "scan", "máy quét", "scanner", "driver máy in", "quét tài liệu",
        "bản in", "mực in", "giấy kẹt", "kẹt giấy", "lệnh in", "đang in",
        "in tài liệu", "không in được", "in ra giấy", "in bị lỗi",
        "thêm máy in", "cài máy in", "kết nối máy in",
    ),
    "ime": (
        "gõ tiếng việt", "fcitx", "unikey", "telex", "vni", "bộ gõ",
        "input method", "ime ", "dấu tiếng việt", "kiểu gõ", "bật dấu",
        "tắt dấu", "gõ không dấu", "gõ dấu", "ngôn ngữ bàn phím",
        "đổi ngôn ngữ bàn phím", "bàn phím tiếng việt", "layout bàn phím",
        "kiểu bàn phím", "keyboard language", "đổi ngôn ngữ", "chuyển ngôn ngữ",
        "bật tiếng việt", "chuyển bộ gõ", "cài bộ gõ",
    ),
    # Cài/gỡ PHẦN MỀM THƯỜNG (App Center/Discover) — tách khỏi "update" (chỉ
    # cập nhật) và khỏi "wine" (app Windows). Đặt SAU "wine" để "cài phần mềm
    # windows" ưu tiên mảng wine.
    "software": (
        "cài phần mềm", "cài đặt phần mềm", "cài ứng dụng", "cài app",
        "gỡ phần mềm", "gỡ cài đặt", "gỡ ứng dụng", "xoá phần mềm",
        "xóa phần mềm", "xoá ứng dụng", "xóa ứng dụng", "uninstall",
        "install app", "app center", "cửa hàng ứng dụng", "kho ứng dụng",
        "trung tâm ứng dụng", "discover", "tải phần mềm", "remove software",
    ),
    "update": (
        "cập nhật", "update", "apt ", "dpkg", "apt-get", "gói phần mềm",
        "package", "upgrade", "nâng cấp", "held broken", "bị giữ lại",
        "bản cập nhật", "kiểm tra cập nhật", "trung tâm cập nhật",
        "cập nhật hệ thống", "update center",
    ),
    "security": (
        "an toàn", "bảo mật", "quét virus", "virus", "mã độc", "malware",
        "tường lửa", "firewall", "trung tâm an toàn", "bảo vệ máy",
        "diệt virus", "phần mềm độc hại", "antivirus", "nhiễm độc",
    ),
    # Đặt TRƯỚC "storage": "usb token" chứa "usb"; muốn chữ-ký-số ưu tiên
    # mảng dịch vụ công.
    "services": (
        "dịch vụ công", "chữ ký số", "ký số", "usb token", "chứng thư số",
        "cổng dịch vụ công", "vneid", "định danh điện tử", "thuế điện tử",
        "bảo hiểm xã hội", "hoá đơn điện tử", "hóa đơn điện tử",
        "digital signature", "public service",
    ),
    "calendar": (
        "lịch âm", "âm lịch", "lịch dương", "dương lịch", "xem lịch",
        "ngày âm", "ngày tốt", "lịch vạn niên", "can chi", "tiết khí",
        "ngày lễ", "lunar calendar",
    ),
    "audio": (
        "âm thanh", "audio", "sound", "loa", "speaker", "mic", "micro",
        "microphone", "pipewire", "pulseaudio", "tai nghe", "headphone",
        "âm lượng", "volume", "rè", "không nghe thấy tiếng",
        "chuyển loa", "đổi thiết bị âm thanh", "mất tiếng",
    ),
    "storage": (
        "ổ đĩa", "ổ cứng", "disk", "storage", "dung lượng", "no space",
        "usb", "ntfs", "mount", "phân vùng", "partition", "thùng rác",
        "trash", "rút usb", "an toàn gỡ", "safely remove", "thẻ nhớ",
        "ổ cứng ngoài", "không nhận usb",
    ),
    "files": (
        "quản lý tệp", "trình quản lý tệp", "dolphin", "hiện file ẩn",
        "file ẩn", "tệp ẩn", "sao chép file", "di chuyển file", "đổi tên file",
        "tạo thư mục", "nén file", "giải nén", "file manager", "hidden files",
        "trình quản lý file",
    ),
    "backup": (
        "sao lưu", "backup", "sao lưu dữ liệu", "lưu dự phòng", "dự phòng",
        "phục hồi dữ liệu", "khôi phục dữ liệu", "chép dữ liệu ra ngoài",
        "restore",
    ),
    "login": (
        "đăng nhập", "dang nhap", "login", "sign in", "mật khẩu",
        "mat khau", "password", "quên mật khẩu", "quen mat khau",
        "khoá màn hình", "khoa man hinh", "lock screen", "sddm",
        "tự động đăng nhập", "autologin", "đổi mật khẩu", "tài khoản",
        "thêm người dùng", "thêm tài khoản", "user account",
    ),
    "power": (
        "pin", "nguồn", "nguon", "sạc", "sac", "battery", "charging",
        "charger", "suspend", "ngủ đông", "hibernate", "treo máy khi ngủ",
        "tắt máy", "tat may", "shutdown", "power button", "nút nguồn",
        "không chịu tắt", "tụt pin", "hao pin", "tiết kiệm pin", "chế độ pin",
        "quản lý nguồn",
    ),
    "bluetooth": (
        "bluetooth", "ghép nối", "ghep noi", "pairing", "paired",
        "tai nghe không dây", "loa bluetooth", "chuột bluetooth",
        "bàn phím bluetooth", "kết nối bluetooth",
    ),
    "shortcut": (
        "phím tắt", "tổ hợp phím", "shortcut", "keyboard shortcut", "hotkey",
        "phím nóng", "gán phím", "phím windows", "phím tắt windows",
        "phím tắt kiểu windows",
    ),
}

#: Nhãn hiển thị cho người dùng của mỗi mảng hệ thống (song ngữ) — KHÔNG
#: phải chuỗi UI chrome đi qua ``namios_i18n.t()`` (không có placeholder/số
#: nhiều cần dịch phức tạp), chỉ là một danh từ ngắn nên để cùng chỗ với
#: ``SUBSYSTEM_KEYWORDS`` (một nơi sửa khi thêm mảng mới, xem
#: ``subsystem_display_name()``).
SUBSYSTEM_DISPLAY_NAMES: dict[str, tuple[str, str]] = {
    "boot": ("khởi động", "boot"),
    "network": ("mạng/Wi-Fi", "network/Wi-Fi"),
    "screenshot": ("chụp màn hình", "screenshots"),
    "display": ("màn hình/máy chiếu", "display/projector"),
    "wine": ("chạy phần mềm Windows (nRun)", "running Windows software (nRun)"),
    "office": ("văn phòng (NaMiOffice)", "office suite (NaMiOffice)"),
    "print": ("in ấn/quét tài liệu", "printing/scanning"),
    "ime": ("gõ tiếng Việt/bàn phím", "Vietnamese input/keyboard"),
    "software": ("cài/gỡ phần mềm", "installing/removing software"),
    "update": ("cập nhật hệ thống", "system updates"),
    "security": ("an toàn & bảo mật", "security & safety"),
    "services": ("dịch vụ công & chữ ký số", "public services & digital signature"),
    "calendar": ("lịch (âm/dương)", "calendar (lunar/solar)"),
    "audio": ("âm thanh", "audio"),
    "storage": ("ổ đĩa/USB", "storage/USB"),
    "files": ("quản lý tệp", "file management"),
    "backup": ("sao lưu dữ liệu", "data backup"),
    "login": ("đăng nhập/tài khoản", "login/accounts"),
    "power": ("pin/nguồn điện", "battery/power"),
    "bluetooth": ("Bluetooth", "Bluetooth"),
    "shortcut": ("phím tắt", "keyboard shortcuts"),
}


def subsystem_display_name(subsystem: str | None, *, lang_vi: bool = True) -> str | None:
    """Tên hiển thị của ``subsystem`` theo ngôn ngữ (``lang_vi=True`` -> tiếng
    Việt). Trả ``None`` khi ``subsystem`` là ``None`` HOẶC không có trong
    ``SUBSYSTEM_DISPLAY_NAMES`` (vd một bộ KB ngoài tự khai báo mảng lạ không
    có nhãn tương ứng ở đây) — caller tự quyết định bỏ qua dòng hiển thị thay
    vì lộ id kỹ thuật thô ra người dùng."""

    if subsystem is None:
        return None
    names = SUBSYSTEM_DISPLAY_NAMES.get(subsystem)
    if names is None:
        return None
    return names[0] if lang_vi else names[1]


def classify_subsystem(text: str) -> str | None:
    """Đoán mảng hệ thống khớp nhiều từ khoá nhất trong ``text``.

    Trả ``None`` nếu KHÔNG từ khoá nào của bất kỳ mảng nào khớp (văn bản quá
    chung chung/không nhận diện được) — caller (``OfflineKbBackend``) vẫn quét
    toàn bộ KB không cần hint trong trường hợp này, không coi ``None`` là lỗi.
    """

    if not text:
        return None
    # So khớp KHÔNG phân biệt dấu/hoa thường (xem ``fold_accents``): người gặp
    # sự cố thường gõ không dấu ("ket noi wifi", "may in") — vẫn phân loại
    # đúng mảng. Fold cả từ khoá lẫn văn bản để một phía có dấu vẫn khớp phía
    # kia không dấu.
    folded = fold_accents(text)

    best_subsystem: str | None = None
    best_score = 0
    for subsystem, keywords in SUBSYSTEM_KEYWORDS.items():
        score = sum(1 for keyword in keywords if fold_accents(keyword) in folded)
        if score > best_score:
            best_score = score
            best_subsystem = subsystem
    return best_subsystem if best_score > 0 else None


# ---------------------------------------------------------------------------
# Ý ĐỊNH "cài một phần mềm/driver CỤ THỂ" — thêm cho App & Driver Concierge
# (11/11/2026). KHÁC với mảng hệ thống "software"/"print" ở trên: hai mảng đó
# chỉ đoán CHỦ ĐỀ CHUNG của câu hỏi (dùng để xếp hạng KB + gợi ý công cụ liên
# quan); ``classify_catalog_intent`` là tín hiệu RIÊNG, dùng ở
# ``backend.AssistantEngine.ask`` để quyết định có nên thử tra
# ``engine.app_catalog`` (kho app/driver đã kiểm duyệt) hay không.
#
# Cố ý RỘNG ("cài" đơn lẻ cũng tính là install_request): khớp cụm từ ở đây
# chỉ là "có nên THỬ tra catalog", không phải "chắc chắn tìm thấy phương án
# cụ thể" — bước sau (``app_catalog.resolve_app``/``resolve_driver``) mới
# quyết định có trả về phương án nào không; không khớp gì thì
# ``backend`` hiển thị thông báo trung thực, KHÔNG bịa thêm (xem docstring
# ``engine/app_catalog.py``).
CatalogIntent = Literal["install_request", "driver_request"]

#: Cụm từ kích hoạt ý định "muốn cài một phần mềm cụ thể".
INSTALL_REQUEST_KEYWORDS: tuple[str, ...] = (
    "cài giúp", "cài đặt", "cài", "tải", "download", "phần mềm", "app",
)

#: "driver" một mình LUÔN đủ để coi là ý định driver. "máy in" một mình
#: KHÔNG đủ (mảng "print" ở trên đã phủ rất nhiều triệu chứng in ấn khác
#: không liên quan driver, vd kẹt giấy/hàng đợi in) — chỉ tính là ý định
#: driver khi "máy in" đi kèm một trong các cụm gợi ý driver dưới đây.
DRIVER_REQUEST_KEYWORDS: tuple[str, ...] = ("driver",)
_PRINTER_WORD = "máy in"
_DRIVER_PRINTER_HINT_KEYWORDS: tuple[str, ...] = (
    "không nhận", "chưa nhận", "cài driver", "không ra giấy", "không in được",
)


def classify_catalog_intent(text: str) -> CatalogIntent | None:
    """Đoán người dùng có đang muốn CÀI một phần mềm/driver cụ thể không.

    Trả ``None`` nếu không khớp tín hiệu nào — caller giữ nguyên luồng KB/
    online bình thường, hoàn toàn không đụng tới ``engine.app_catalog``.
    Ưu tiên ``"driver_request"`` trước ``"install_request"`` khi cả hai cùng
    khớp (câu hỏi về máy in cụ thể hơn là về cài phần mềm nói chung)."""

    if not text:
        return None
    folded = fold_accents(text)

    has_driver_word = any(fold_accents(keyword) in folded for keyword in DRIVER_REQUEST_KEYWORDS)
    has_printer_word = fold_accents(_PRINTER_WORD) in folded
    has_printer_hint = any(
        fold_accents(hint) in folded for hint in _DRIVER_PRINTER_HINT_KEYWORDS
    )
    if has_driver_word or (has_printer_word and has_printer_hint):
        return "driver_request"

    if any(fold_accents(keyword) in folded for keyword in INSTALL_REQUEST_KEYWORDS):
        return "install_request"

    return None
