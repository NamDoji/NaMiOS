"""``namios_manchieu.display`` — logic THUẦN Python (không PySide6, không
``subprocess``) đọc/hiểu output của ``kscreen-doctor -o`` và dựng chuỗi
``output.<id>.<setting>`` cần truyền cho ``kscreen-doctor`` để áp 1 trong 4
chế độ hiển thị kiểu Windows "Win+P" (Nhân đôi/Mở rộng/Chỉ màn hình này/Chỉ
màn hình ngoài). Test được hoàn toàn bằng text mẫu — xem ``tests/unit/manchieu/``.

NGUỒN XÁC NHẬN (không suy đoán định dạng): đã đọc trực tiếp mã nguồn thật
``libkscreen`` (nhánh phát hành ``v6.3.4`` — đúng phiên bản gói ``kscreen``
khai trong ``0100-desktop-kde.list.chroot``), file
``src/doctor/doctor.cpp::showOutputs()``. Vài điểm KHÔNG hiển nhiên nếu chỉ
đoán từ tài liệu:

1. ``kscreen-doctor -o``/``--outputs`` LUÔN in mã màu ANSI (xanh/đỏ/vàng/xanh
   dương) cho các từ trạng thái — ``QTextStream`` ghi thẳng ra stdout, KHÔNG
   kiểm tra ``isatty()`` trước khi in màu. Nghĩa là output đọc được qua
   ``subprocess``/``run_argv`` (không phải TTY) VẪN chứa các chuỗi
   ``\\x1b[01;32m`` v.v. — ``strip_ansi()`` dưới đây BẮT BUỘC phải chạy trước
   khi parse, nếu không mọi so khớp chuỗi (``"enabled"``, ``"priority "``...)
   sẽ KHÔNG khớp vì bị cắt giữa bởi escape code.
2. Mỗi "cài đặt" gửi cho ``kscreen-doctor`` có cú pháp
   ``output.<name-or-id-or-uuid>.<setting>[.<value>]`` — module này LUÔN
   dùng **ID số** (``output->id()``) làm ``<name-or-id-or-uuid>``, KHÔNG dùng
   tên connector (``eDP-1``, ``HDMI-A-1``...), để tránh mọi rủi ro tên chứa
   dấu chấm/khoảng trắng phá vỡ cú pháp phân tách-bằng-chấm của chính
   ``kscreen-doctor`` (xem ``Doctor::parseOutputArgs`` dùng
   ``op.split(QLatin1Char('.'))``).
3. Nhiều "cài đặt" trong CÙNG một lần gọi ``kscreen-doctor`` được áp dụng
   ATOMIC (một lần ``applyConfig()`` ở cuối) — vì vậy mọi hàm dựng lệnh ở đây
   trả về MỘT danh sách token để gọi ``kscreen-doctor`` ĐÚNG MỘT LẦN cho mỗi
   lần đổi chế độ, không gọi rời từng cài đặt (tránh trạng thái lỡ-dở giữa
   hai lần gọi, vd tắt màn ngoài xong mới bật màn trong — có thể có một
   khoảng đen ngắn giữa hai lệnh nếu gọi rời).

KHÔNG tự chế giả định về độ phân giải "giống nhau" giữa hai màn hình ở chế độ
Nhân đôi — module này CHỈ đặt CÙNG toạ độ gốc (0,0) cho cả hai (đúng cơ chế
"overlap = nhân đôi" mà các công cụ kiểu xrandr/kscreen dùng); nếu độ phân
giải hai màn khác nhau, phần chênh lệch có hiển thị đúng pixel-perfect hay
không phụ thuộc compositor/backend thật — CHƯA kiểm chứng trên phần cứng
thật (xem ``usr/share/namios/docs/MAY-CHIEU.md`` §Giới hạn trung thực)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

__all__ = [
    "ModeInfo",
    "OutputInfo",
    "DisplayError",
    "DisplayPlan",
    "MODE_MIRROR",
    "MODE_EXTEND",
    "MODE_INTERNAL_ONLY",
    "MODE_EXTERNAL_ONLY",
    "ALL_MODES",
    "MODE_LABELS_VI",
    "NO_OUTPUTS_MESSAGE",
    "NO_EXTERNAL_MESSAGE",
    "NO_INTERNAL_MESSAGE",
    "strip_ansi",
    "classify_output",
    "parse_outputs",
    "pick_displays",
    "build_argv_tokens",
    "describe_plan",
    "plan",
]

# ---------------------------------------------------------------------------
# Hằng số chế độ — 4 nút tương đương Windows Win+P.
# ---------------------------------------------------------------------------
MODE_MIRROR = "mirror"
MODE_EXTEND = "extend"
MODE_INTERNAL_ONLY = "internal_only"
MODE_EXTERNAL_ONLY = "external_only"
ALL_MODES = (MODE_MIRROR, MODE_EXTEND, MODE_INTERNAL_ONLY, MODE_EXTERNAL_ONLY)

MODE_LABELS_VI: dict[str, str] = {
    MODE_MIRROR: "Nhân đôi",
    MODE_EXTEND: "Mở rộng",
    MODE_INTERNAL_ONLY: "Chỉ màn hình này",
    MODE_EXTERNAL_ONLY: "Chỉ màn hình ngoài",
}

#: Thông báo THÂN THIỆN khi không đủ màn hình để chọn chế độ — nguyên văn
#: theo đặc tả (KHÔNG giả vờ thành công/KHÔNG đoán khác đi).
NO_EXTERNAL_MESSAGE = (
    "Chưa thấy màn hình ngoài — cắm cáp HDMI/VGA/USB-C vào máy chiếu rồi bấm Làm mới."
)
NO_INTERNAL_MESSAGE = (
    "Không tìm thấy màn hình trong máy (eDP/LVDS) trên máy này — công cụ này dành cho "
    "máy tính xách tay có 1 màn hình trong + máy chiếu/màn hình ngoài."
)
NO_OUTPUTS_MESSAGE = (
    "Không đọc được màn hình nào từ kscreen-doctor — hãy bấm Làm mới hoặc kiểm tra lại máy."
)

#: Tiền tố tên connector — DÙNG CHỮ HOA để so khớp không phân biệt hoa/thường.
_INTERNAL_NAME_PREFIXES = ("EDP", "LVDS", "DSI")
_EXTERNAL_NAME_PREFIXES = ("HDMI", "DP", "DVI", "VGA", "USB")

#: Giá trị chuỗi loại output mà ``kscreen-doctor`` in ra (khớp đúng
#: ``Doctor::showOutputs()::typeString`` — xem docstring module) — dùng làm
#: TÍN HIỆU PHỤ khi tên connector không khớp tiền tố nào ở trên (vd backend
#: lạ đặt tên khác thường).
_INTERNAL_TYPE_STRINGS = frozenset({"Panel"})
_EXTERNAL_TYPE_STRINGS = frozenset({"HDMI", "VGA", "DVI", "DVII", "DVIA", "DVID", "DisplayPort"})

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Bỏ mọi mã màu ANSI — BẮT BUỘC trước khi parse, xem điểm (1) ở
    docstring module (``kscreen-doctor -o`` luôn in màu, không kiểm tra TTY)."""

    return _ANSI_RE.sub("", text)


def classify_output(name: str, output_type: str = "") -> str:
    """Phân loại một output là ``"internal"`` (màn hình trong máy)/
    ``"external"`` (máy chiếu/màn hình ngoài)/``"unknown"``. Ưu tiên tiền tố
    TÊN connector (đúng yêu cầu: eDP/LVDS = trong máy; HDMI/DP/VGA/USB-C/DVI =
    ngoài — USB-C thật ra xuất hiện dưới tên ``DP-*``/``USB-C-*`` tuỳ driver,
    cả hai tiền tố đều đã liệt); khi tên không khớp tiền tố nào, dùng loại
    (``output->type()`` mà ``kscreen-doctor`` in ra, vd ``"Panel"``) làm tín
    hiệu phụ — KHÔNG đoán mò nếu cả hai đều không khớp (trả ``"unknown"``)."""

    upper_name = name.upper()
    for prefix in _INTERNAL_NAME_PREFIXES:
        if upper_name.startswith(prefix):
            return "internal"
    for prefix in _EXTERNAL_NAME_PREFIXES:
        if upper_name.startswith(prefix):
            return "external"
    if output_type in _INTERNAL_TYPE_STRINGS:
        return "internal"
    if output_type in _EXTERNAL_TYPE_STRINGS:
        return "external"
    return "unknown"


# ---------------------------------------------------------------------------
# Dữ liệu — mirror đúng tập field cần dùng từ ``Doctor::showOutputs()``.
# KHÔNG mirror toàn bộ ~25 dòng trạng thái (HDR/VRR/DDC-CI/...) — namios-
# manchieu chỉ cần đủ để quyết định enable/disable/position/priority.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ModeInfo:
    mode_id: str
    width: int
    height: int
    refresh: float
    is_current: bool
    is_preferred: bool


@dataclass(frozen=True)
class OutputInfo:
    id: int
    name: str
    uuid: str
    connected: bool
    enabled: bool
    disable_supported: bool
    priority: int
    output_type: str
    geometry: tuple[int, int, int, int] | None  # (x, y, width, height)
    modes: tuple[ModeInfo, ...]

    @property
    def kind(self) -> str:
        return classify_output(self.name, self.output_type)

    @property
    def current_mode(self) -> ModeInfo | None:
        for m in self.modes:
            if m.is_current:
                return m
        return None

    @property
    def effective_width(self) -> int:
        """Chiều rộng dùng để đặt vị trí màn ngoài ở chế độ Mở rộng — ưu
        tiên mode hiện tại, dự phòng ``geometry``, dự phòng CUỐI CÙNG 1920
        (chỉ khi output thật không báo gì cả — hiếm, nhưng KHÔNG để lỗi
        parse làm hỏng luôn việc đổi chế độ)."""

        current = self.current_mode
        if current is not None and current.width > 0:
            return current.width
        if self.geometry is not None and self.geometry[2] > 0:
            return self.geometry[2]
        return 1920


_OUTPUT_HEADER_RE = re.compile(r"^Output:\s+(\d+)\s+(\S+)(?:\s+(\S+))?\s*$", re.MULTILINE)
_ENABLED_RE = re.compile(r"^\t(enabled|disabled|disable unsupported)\s*$", re.MULTILINE)
_CONNECTED_RE = re.compile(r"^\t(connected|disconnected)\s*$", re.MULTILINE)
_PRIORITY_RE = re.compile(r"^\tpriority (\d+)\s*$", re.MULTILINE)
_TYPE_RE = re.compile(
    r"^\t(Unknown|VGA|DVI|DVII|DVIA|DVID|HDMI|Panel|TV|TVComposite|TVSVideo|TVComponent"
    r"|TVSCART|TVC4|DisplayPort|UnmappedOutputType)\s*$",
    re.MULTILINE,
)
_GEOMETRY_RE = re.compile(r"^\tGeometry:\s+(-?\d+),(-?\d+)\s+(\d+)x(\d+)\s*$", re.MULTILINE)
_MODES_LINE_RE = re.compile(r"^\tModes:\s*(.*)$", re.MULTILINE)
_MODE_TOKEN_RE = re.compile(r"(\d+):(\d+)x(\d+)@([\d.]+)(\*)?(!)?")


def _parse_one_block(block: str) -> OutputInfo | None:
    header = _OUTPUT_HEADER_RE.search(block)
    if header is None:
        return None
    output_id = int(header.group(1))
    name = header.group(2)
    uuid = header.group(3) or ""

    enabled_match = _ENABLED_RE.search(block)
    disable_supported = True
    enabled = False
    if enabled_match is not None:
        state_word = enabled_match.group(1)
        if state_word == "disable unsupported":
            disable_supported = False
            enabled = True  # output không tắt được -> coi như luôn bật.
        else:
            enabled = state_word == "enabled"

    connected_match = _CONNECTED_RE.search(block)
    connected = connected_match is not None and connected_match.group(1) == "connected"

    priority_match = _PRIORITY_RE.search(block)
    priority = int(priority_match.group(1)) if priority_match is not None else 0

    type_match = _TYPE_RE.search(block)
    output_type = type_match.group(1) if type_match is not None else ""

    geometry_match = _GEOMETRY_RE.search(block)
    geometry: tuple[int, int, int, int] | None = None
    if geometry_match is not None:
        geometry = (
            int(geometry_match.group(1)),
            int(geometry_match.group(2)),
            int(geometry_match.group(3)),
            int(geometry_match.group(4)),
        )

    modes: list[ModeInfo] = []
    modes_line_match = _MODES_LINE_RE.search(block)
    if modes_line_match is not None:
        for tok in _MODE_TOKEN_RE.finditer(modes_line_match.group(1)):
            modes.append(
                ModeInfo(
                    mode_id=tok.group(1),
                    width=int(tok.group(2)),
                    height=int(tok.group(3)),
                    refresh=float(tok.group(4)),
                    is_current=tok.group(5) == "*",
                    is_preferred=tok.group(6) == "!",
                )
            )

    return OutputInfo(
        id=output_id,
        name=name,
        uuid=uuid,
        connected=connected,
        enabled=enabled,
        disable_supported=disable_supported,
        priority=priority,
        output_type=output_type,
        geometry=geometry,
        modes=tuple(modes),
    )


def parse_outputs(raw_text: str) -> list[OutputInfo]:
    """Parse nguyên văn stdout của ``kscreen-doctor -o``/``--outputs`` (CÓ
    THỂ chứa mã màu ANSI — tự ``strip_ansi`` ở đây, caller không cần tự lo).
    Trả danh sách rỗng nếu không thấy khối ``Output:`` nào (KHÔNG raise —
    caller (``backend.read_outputs``) tự quyết định đó là lỗi gì)."""

    text = strip_ansi(raw_text)
    headers = list(_OUTPUT_HEADER_RE.finditer(text))
    outputs: list[OutputInfo] = []
    for i, header in enumerate(headers):
        start = header.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[start:end]
        info = _parse_one_block(block)
        if info is not None:
            outputs.append(info)
    return outputs


# ---------------------------------------------------------------------------
# Lỗi + lập kế hoạch đổi chế độ.
# ---------------------------------------------------------------------------
class DisplayError(Exception):
    """Không thể lập kế hoạch đổi chế độ — ``message`` là câu THÂN THIỆN,
    hiển thị thẳng cho người dùng (không có "mã lỗi kỹ thuật" nào kèm)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def pick_displays(outputs: Sequence[OutputInfo]) -> tuple[OutputInfo, OutputInfo]:
    """Chọn (internal, external) để vận hành 4 chế độ. Chỉ xét output ĐÃ
    KẾT NỐI (``connected`` — đọc-chỉ, không suy đoán từ output đã cấu hình
    nhưng rút cáp). Nếu có NHIỀU hơn 1 màn ngoài đã kết nối, chọn cái ID NHỎ
    NHẤT (thường là cái kscreen/kernel liệt kê trước) — phiên bản này KHÔNG
    có UI chọn-giữa-nhiều-màn-ngoài, xem hạn chế ghi trong
    ``usr/share/namios/docs/MAY-CHIEU.md``."""

    connected = [o for o in outputs if o.connected]
    if not connected:
        raise DisplayError(NO_OUTPUTS_MESSAGE)
    if len(connected) == 1:
        raise DisplayError(NO_EXTERNAL_MESSAGE)

    internal_candidates = sorted((o for o in connected if o.kind == "internal"), key=lambda o: o.id)
    external_candidates = sorted((o for o in connected if o.kind == "external"), key=lambda o: o.id)

    if not internal_candidates:
        raise DisplayError(NO_INTERNAL_MESSAGE)
    if not external_candidates:
        raise DisplayError(NO_EXTERNAL_MESSAGE)
    return internal_candidates[0], external_candidates[0]


def _token(output_id: int, *parts: str) -> str:
    return "output." + str(output_id) + "." + ".".join(parts)


def build_argv_tokens(mode: str, internal: OutputInfo, external: OutputInfo) -> tuple[str, ...]:
    """Dựng danh sách token ``output.<id>.<setting>`` cho ĐÚNG MỘT lần gọi
    ``kscreen-doctor`` (atomic — xem điểm (3) docstring module). CHỈ dùng
    enable/disable/position/priority — không ép đặt lại mode/độ phân giải."""

    if mode == MODE_MIRROR:
        return (
            _token(internal.id, "enable"),
            _token(internal.id, "position", "0,0"),
            _token(internal.id, "priority", "1"),
            _token(external.id, "enable"),
            _token(external.id, "position", "0,0"),
            _token(external.id, "priority", "2"),
        )
    if mode == MODE_EXTEND:
        return (
            _token(internal.id, "enable"),
            _token(internal.id, "position", "0,0"),
            _token(internal.id, "priority", "1"),
            _token(external.id, "enable"),
            _token(external.id, "position", f"{internal.effective_width},0"),
            _token(external.id, "priority", "2"),
        )
    if mode == MODE_INTERNAL_ONLY:
        return (
            _token(internal.id, "enable"),
            _token(internal.id, "position", "0,0"),
            _token(internal.id, "priority", "1"),
            _token(external.id, "disable"),
        )
    if mode == MODE_EXTERNAL_ONLY:
        return (
            _token(external.id, "enable"),
            _token(external.id, "position", "0,0"),
            _token(external.id, "priority", "1"),
            _token(internal.id, "disable"),
        )
    raise ValueError(f"Chế độ không hợp lệ: {mode!r}")


def describe_plan(mode: str, internal: OutputInfo, external: OutputInfo) -> str:
    """Câu tiếng Việt ngắn giải thích SẮP làm gì — hiển thị trong hộp thoại
    xác nhận TRƯỚC khi gọi kscreen-doctor thật (yêu cầu: "show the user what
    will happen")."""

    if mode == MODE_MIRROR:
        return (
            f"Nhân đôi: {internal.name} và {external.name} sẽ hiện CÙNG nội dung (cùng vị trí)."
        )
    if mode == MODE_EXTEND:
        return (
            f"Mở rộng: {external.name} đặt BÊN PHẢI {internal.name} — kéo cửa sổ qua hai màn hình."
        )
    if mode == MODE_INTERNAL_ONLY:
        return f"Chỉ màn hình này: dùng {internal.name}, TẮT {external.name}."
    if mode == MODE_EXTERNAL_ONLY:
        return (
            f"Chỉ màn hình ngoài: dùng {external.name} (máy chiếu/màn hình ngoài), "
            f"TẮT {internal.name}."
        )
    raise ValueError(f"Chế độ không hợp lệ: {mode!r}")


@dataclass(frozen=True)
class DisplayPlan:
    mode: str
    internal: OutputInfo
    external: OutputInfo
    tokens: tuple[str, ...]
    description_vi: str


def plan(mode: str, outputs: Sequence[OutputInfo]) -> DisplayPlan:
    """Điểm vào DUY NHẤT cho UI/backend: chọn internal/external + dựng token
    + câu mô tả, trong MỘT lần gọi (tránh hai nơi tự chọn ra hai output khác
    nhau giữa lúc hỏi-xác-nhận và lúc-áp-dụng-thật). Raise ``DisplayError``
    (câu thân thiện) nếu không đủ màn hình cho chế độ này."""

    if mode not in ALL_MODES:
        raise ValueError(f"Chế độ không hợp lệ: {mode!r}")
    internal, external = pick_displays(outputs)
    tokens = build_argv_tokens(mode, internal, external)
    description = describe_plan(mode, internal, external)
    return DisplayPlan(
        mode=mode, internal=internal, external=external, tokens=tokens, description_vi=description
    )
