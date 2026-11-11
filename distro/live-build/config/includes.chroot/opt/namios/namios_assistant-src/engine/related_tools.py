"""Ánh xạ "công cụ NaMiOS liên quan" cho câu trả lời của Trợ lý — nút "mở
công cụ liên quan" nhắc tới trong yêu cầu nâng cấp 11/11/2026 (ví dụ: lỗi Wi-Fi
-> gợi ý mở nConnect; lỗi máy chiếu -> gợi ý mở nProjector).

NGUYÊN TẮC CHỐNG BỊA (hard constraint của wave này): registry dưới đây CHỈ
liệt kê ``exec_argv`` đã COPY NGUYÊN VĂN từ dòng ``Exec=`` của một file
``.desktop`` THẬT đang có trong repo (xem ``source_desktop_file`` mỗi mục —
đường dẫn tương đối từ ``distro/live-build/config/includes.chroot/usr/share/
applications/``). KHÔNG đoán thêm cờ/đường dẫn nào không có trong file gốc.
Một mảng hệ thống (subsystem) KHÔNG có công cụ nào xác nhận được thì ĐƠN GIẢN
LÀ KHÔNG có trong ``_DEFAULT_TOOL_ID_BY_SUBSYSTEM`` — ``resolve_related_tools``
trả về rỗng cho trường hợp đó, KHÔNG suy diễn một công cụ gần đúng.

Hai lớp phân giải, ưu tiên entry trước mảng (xem ``resolve_related_tools``):
  1. ``KBEntry.related_tool_id`` (nếu entry tự khai báo id cụ thể, chính xác
     hơn vì tác giả entry biết rõ chỉ công cụ nào mới giải quyết đúng ca này —
     vd lỗi "thêm máy in" trỏ thẳng action "Thêm máy in" của nConnect thay vì
     chỉ mở nConnect ở màn hình mặc định).
  2. ``_DEFAULT_TOOL_ID_BY_SUBSYSTEM.get(entry.subsystem)`` khi entry không tự
     khai báo (áp dụng cho toàn bộ entry khởi điểm trước đợt nâng cấp này,
     vốn không có field ``related_tool_id`` — không cần sửa lại 19 entry cũ)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from namios_assistant.engine.knowledge_base import KBEntry

__all__ = [
    "RelatedTool",
    "RELATED_TOOLS",
    "resolve_related_tools",
    "resolve_related_tool_for_subsystem",
]


@dataclass(frozen=True)
class RelatedTool:
    """Một công cụ NaMiOS thật có thể mở trực tiếp từ câu trả lời."""

    tool_id: str
    label_vi: str
    label_en: str
    #: argv tĩnh (KHÔNG qua shell) — UI dùng ``QProcess.startDetached(argv[0],
    #: list(argv[1:]))``, giống quy ước ``namios_security.run_argv`` (argv
    #: tĩnh, không nội suy input người dùng vào đây).
    exec_argv: tuple[str, ...]
    #: Ghi chú truy vết nguồn thật — KHÔNG dùng lúc runtime, chỉ để người sau
    #: kiểm chứng registry này không bịa (xem docstring module).
    source_desktop_file: str


#: Registry THẬT — mỗi ``exec_argv`` đối chiếu trực tiếp với ``Exec=`` của
#: đúng file ``.desktop`` ghi trong ``source_desktop_file`` (đã đọc lại khi
#: viết module này, 11/11/2026).
RELATED_TOOLS: dict[str, RelatedTool] = {
    "nconnect": RelatedTool(
        tool_id="nconnect",
        label_vi="Kết nối thiết bị (nConnect)",
        label_en="Connect device (nConnect)",
        exec_argv=("/usr/local/bin/namios-ket-noi-thiet-bi",),
        source_desktop_file="namios-ket-noi-thiet-bi.desktop",
    ),
    "nconnect-printer": RelatedTool(
        tool_id="nconnect-printer",
        label_vi="Thêm máy in (nConnect)",
        label_en="Add printer (nConnect)",
        exec_argv=("/usr/local/bin/namios-ket-noi-thiet-bi", "may-in"),
        source_desktop_file=(
            "namios-ket-noi-thiet-bi.desktop (Desktop Action ThemMayIn)"
        ),
    ),
    "nprojector": RelatedTool(
        tool_id="nprojector",
        label_vi="Máy chiếu & Màn hình ngoài (nProjector)",
        label_en="Projector & external display (nProjector)",
        exec_argv=("/usr/bin/namios-manchieu",),
        source_desktop_file="namios-manchieu.desktop",
    ),
    "nwine": RelatedTool(
        tool_id="nwine",
        label_vi="Chạy phần mềm Windows (nRun)",
        label_en="Run Windows software (nRun)",
        exec_argv=("/usr/local/bin/namios-windows-app",),
        source_desktop_file="namios-windows-app.desktop",
    ),
    "nsecurity": RelatedTool(
        tool_id="nsecurity",
        label_vi="Trung tâm An toàn (nSecurity)",
        label_en="Security Center (nSecurity)",
        exec_argv=("/usr/bin/namios-antoan",),
        source_desktop_file="namios-antoan.desktop",
    ),
    "ndiagnostics": RelatedTool(
        tool_id="ndiagnostics",
        label_vi="Chẩn đoán (nDiagnostics)",
        label_en="Diagnostics (nDiagnostics)",
        exec_argv=("/usr/local/bin/namios-chan-doan",),
        source_desktop_file="namios-chan-doan.desktop",
    ),
    "cpl-update": RelatedTool(
        tool_id="cpl-update",
        label_vi="Cập nhật",
        label_en="Update",
        exec_argv=("/usr/local/bin/namios-control-panel", "--category", "update"),
        source_desktop_file="namios-cpl-update.desktop",
    ),
    "cpl-apps": RelatedTool(
        tool_id="cpl-apps",
        label_vi="Ứng dụng (cài/gỡ phần mềm)",
        label_en="Apps (install/remove software)",
        exec_argv=("/usr/local/bin/namios-control-panel", "--category", "apps"),
        source_desktop_file="namios-cpl-apps.desktop",
    ),
    "cpl-network": RelatedTool(
        tool_id="cpl-network",
        label_vi="Cài đặt Mạng",
        label_en="Network settings",
        exec_argv=("/usr/local/bin/namios-control-panel", "--category", "network"),
        source_desktop_file="namios-cpl-network.desktop",
    ),
    "cpl-display": RelatedTool(
        tool_id="cpl-display",
        label_vi="Cài đặt Màn hình & Hiển thị",
        label_en="Display settings",
        exec_argv=("/usr/local/bin/namios-control-panel", "--category", "display"),
        source_desktop_file="namios-cpl-display.desktop",
    ),
    "cpl-devices": RelatedTool(
        tool_id="cpl-devices",
        label_vi="Cài đặt Thiết bị (âm thanh/Bluetooth/máy in)",
        label_en="Device settings (audio/Bluetooth/printer)",
        exec_argv=("/usr/local/bin/namios-control-panel", "--category", "devices"),
        source_desktop_file="namios-cpl-devices.desktop",
    ),
    "cpl-accounts": RelatedTool(
        tool_id="cpl-accounts",
        label_vi="Cài đặt Tài khoản",
        label_en="Account settings",
        exec_argv=("/usr/local/bin/namios-control-panel", "--category", "accounts"),
        source_desktop_file="namios-cpl-accounts.desktop",
    ),
}

#: Công cụ MẶC ĐỊNH theo mảng hệ thống — chỉ dùng khi entry KHÔNG tự khai báo
#: ``related_tool_id`` (xem docstring module). Mảng không liệt kê ở đây (vd
#: ``office``) nghĩa là CHƯA có công cụ NaMiOS xác nhận nào để gợi ý mở —
#: KHÔNG suy đoán.
_DEFAULT_TOOL_ID_BY_SUBSYSTEM: dict[str, str] = {
    "network": "nconnect",
    "print": "nconnect-printer",
    "bluetooth": "nconnect",
    "storage": "nconnect",
    "display": "nprojector",
    "wine": "nwine",
    "update": "cpl-update",
    "audio": "cpl-devices",
    "login": "cpl-accounts",
    "boot": "ndiagnostics",
}


def resolve_related_tool_for_subsystem(subsystem: str | None) -> RelatedTool | None:
    """Công cụ mặc định cho MỘT mảng hệ thống (không cần entry) — dùng khi
    chưa tìm được entry KB nào khớp nhưng vẫn đoán được mảng (xem
    ``OfflineKbBackend.answer`` nhánh "không khớp entry nào")."""

    if subsystem is None:
        return None
    tool_id = _DEFAULT_TOOL_ID_BY_SUBSYSTEM.get(subsystem)
    if tool_id is None:
        return None
    return RELATED_TOOLS.get(tool_id)


def resolve_related_tools(
    entries: Sequence[KBEntry], *, subsystem_hint: str | None = None
) -> tuple[RelatedTool, ...]:
    """Gom công cụ liên quan cho một DANH SÁCH entry đã khớp (giữ thứ tự xuất
    hiện, loại trùng theo ``tool_id`` — 2 entry cùng trỏ một công cụ chỉ hiện
    MỘT nút). Entry không có ``related_tool_id`` lẫn không khớp mảng mặc định
    nào bị bỏ qua êm (không phải lỗi — nhiều mảng/entry chính đáng không có
    công cụ nào để mở, xem docstring module)."""

    resolved: list[RelatedTool] = []
    seen_ids: set[str] = set()

    for entry in entries:
        tool: RelatedTool | None = None
        if entry.related_tool_id:
            tool = RELATED_TOOLS.get(entry.related_tool_id)
        if tool is None:
            tool = resolve_related_tool_for_subsystem(entry.subsystem)
        if tool is not None and tool.tool_id not in seen_ids:
            seen_ids.add(tool.tool_id)
            resolved.append(tool)

    if not resolved:
        fallback = resolve_related_tool_for_subsystem(subsystem_hint)
        if fallback is not None:
            resolved.append(fallback)

    return tuple(resolved)
