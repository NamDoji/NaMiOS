"""Phân loại một đoạn văn bản lỗi (tiếng Việt/tiếng Anh trộn lẫn) về một
MẢNG hệ thống (subsystem) — bước đầu tiên của ``AssistantEngine.ask`` để thu
hẹp phạm vi tìm trong KB ngoại tuyến + cho online backend biết ngữ cảnh.

Thuật toán CỐ Ý đơn giản (đếm từ khoá xuất hiện trong văn bản, không NLP/
không mô hình): dễ kiểm chứng, không phụ thuộc mạng/model, chạy tức thời.
Đây KHÔNG phải bộ phân loại chính xác tuyệt đối — chỉ là một GỢI Ý (hint) để
xếp hạng kết quả KB, không phải quyết định cuối cùng (``KnowledgeBase.find_matches``
vẫn quét toàn bộ entry, subsystem chỉ cộng thêm điểm ưu tiên)."""

from __future__ import annotations

__all__ = ["SUBSYSTEM_KEYWORDS", "classify_subsystem"]


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
        "nmcli", "networkmanager",
    ),
    "display": (
        "màn hình", "display", "monitor", "resolution", "độ phân giải",
        "kwin", "wayland", "x11", "nvidia", "amdgpu", "gpu", "hdmi",
        "displayport", "card đồ hoạ", "card đồ họa",
    ),
    "wine": (
        "wine", "winetricks", "prefix", ".exe", ".dll", "app windows",
        "ứng dụng windows", "phần mềm windows", "vcruntime", "msvcp",
    ),
    "office": (
        "namioffice", "libreoffice", "writer", "calc", "impress", "docx",
        "xlsx", "pptx", "tài liệu", "document", "font", "times new roman",
        "khoá", "lock",
    ),
    "print": (
        "in ", "máy in", "printer", "cups", "print", "hàng đợi", "queue",
        "scan", "máy quét", "scanner",
    ),
    "ime": (
        "gõ tiếng việt", "fcitx", "unikey", "telex", "vni", "bộ gõ",
        "input method", "ime ", "dấu tiếng việt",
    ),
    "update": (
        "cập nhật", "update", "apt ", "dpkg", "apt-get", "gói phần mềm",
        "package", "upgrade", "nâng cấp",
    ),
    "audio": (
        "âm thanh", "audio", "sound", "loa", "speaker", "mic", "micro",
        "microphone", "pipewire", "pulseaudio", "tai nghe", "headphone",
    ),
    "storage": (
        "ổ đĩa", "ổ cứng", "disk", "storage", "dung lượng", "no space",
        "usb", "ntfs", "mount", "phân vùng", "partition", "thùng rác",
        "trash",
    ),
}


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
