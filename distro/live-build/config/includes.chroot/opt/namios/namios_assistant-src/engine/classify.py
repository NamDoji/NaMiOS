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

__all__ = [
    "SUBSYSTEM_KEYWORDS",
    "SUBSYSTEM_DISPLAY_NAMES",
    "classify_subsystem",
    "subsystem_display_name",
]


#: Mảng hệ thống -> danh sách từ khoá (VI + EN trộn chung, so khớp substring
#: không phân biệt hoa/thường) hay xuất hiện trong lỗi thuộc mảng đó. Thêm
#: mảng mới: thêm một dòng ở đây + gắn ``subsystem`` tương ứng trong KB
#: (``kb/starter_kb.json``) — hai nơi này độc lập, không bắt buộc khớp 1-1
#: (một entry KB có thể đúng dù subsystem không nằm trong danh sách đoán được).
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
    ),
    "display": (
        "màn hình", "display", "monitor", "resolution", "độ phân giải",
        "kwin", "wayland", "x11", "nvidia", "amdgpu", "gpu", "hdmi",
        "displayport", "card đồ hoạ", "card đồ họa", "máy chiếu",
        "projector", "nhân đôi", "mở rộng", "trình chiếu", "chiếu màn hình",
        "usb-c", "vga",
    ),
    "wine": (
        "wine", "winetricks", "prefix", ".exe", ".dll", "app windows",
        "ứng dụng windows", "phần mềm windows", "vcruntime", "msvcp",
        "usb token", "chữ ký số", "ký số",
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
    ),
    "ime": (
        "gõ tiếng việt", "fcitx", "unikey", "telex", "vni", "bộ gõ",
        "input method", "ime ", "dấu tiếng việt", "kiểu gõ", "bật dấu",
        "tắt dấu", "gõ không dấu", "gõ dấu",
    ),
    "update": (
        "cập nhật", "update", "apt ", "dpkg", "apt-get", "gói phần mềm",
        "package", "upgrade", "nâng cấp", "cài phần mềm", "cài đặt phần mềm",
        "gỡ phần mềm", "gỡ cài đặt", "uninstall", "install", "discover",
        "held broken", "bị giữ lại", "an toàn máy", "quét virus",
    ),
    "audio": (
        "âm thanh", "audio", "sound", "loa", "speaker", "mic", "micro",
        "microphone", "pipewire", "pulseaudio", "tai nghe", "headphone",
        "âm lượng", "volume", "rè", "không nghe thấy tiếng",
    ),
    "storage": (
        "ổ đĩa", "ổ cứng", "disk", "storage", "dung lượng", "no space",
        "usb", "ntfs", "mount", "phân vùng", "partition", "thùng rác",
        "trash", "rút usb", "an toàn gỡ", "safely remove", "thẻ nhớ",
        "ổ cứng ngoài", "không nhận usb",
    ),
    "login": (
        "đăng nhập", "dang nhap", "login", "sign in", "mật khẩu",
        "mat khau", "password", "quên mật khẩu", "quen mat khau",
        "khoá màn hình", "khoa man hinh", "lock screen", "sddm",
        "tự động đăng nhập", "autologin", "đổi mật khẩu",
    ),
    "power": (
        "pin", "nguồn", "nguon", "sạc", "sac", "battery", "charging",
        "charger", "suspend", "ngủ đông", "hibernate", "treo máy khi ngủ",
        "tắt máy", "tat may", "shutdown", "power button", "nút nguồn",
        "không chịu tắt", "tụt pin", "hao pin",
    ),
    "bluetooth": (
        "bluetooth", "ghép nối", "ghep noi", "pairing", "paired",
        "tai nghe không dây", "loa bluetooth", "chuột bluetooth",
        "bàn phím bluetooth", "kết nối bluetooth",
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
    "display": ("màn hình/máy chiếu", "display/projector"),
    "wine": ("chạy phần mềm Windows (Wine)", "running Windows software (Wine)"),
    "office": ("văn phòng (NaMiOffice)", "office suite (NaMiOffice)"),
    "print": ("in ấn/quét tài liệu", "printing/scanning"),
    "ime": ("gõ tiếng Việt", "Vietnamese input method"),
    "update": ("cập nhật/cài-gỡ phần mềm", "updates/installing software"),
    "audio": ("âm thanh", "audio"),
    "storage": ("ổ đĩa/USB", "storage/USB"),
    "login": ("đăng nhập/tài khoản", "login/accounts"),
    "power": ("pin/nguồn điện", "battery/power"),
    "bluetooth": ("Bluetooth", "Bluetooth"),
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
    lowered = text.lower()

    best_subsystem: str | None = None
    best_score = 0
    for subsystem, keywords in SUBSYSTEM_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_score = score
            best_subsystem = subsystem
    return best_subsystem if best_score > 0 else None
