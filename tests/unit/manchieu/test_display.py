"""Test ``namios_manchieu.display`` — logic phân tích ``kscreen-doctor -o``
+ dựng lệnh cho 4 chế độ (Nhân đôi/Mở rộng/Chỉ màn hình này/Chỉ màn hình
ngoài), bằng TEXT MẪU (không gọi subprocess/kscreen-doctor thật — module
``display`` không có ``subprocess`` nào để gọi, xem docstring module).

Dữ liệu mẫu dưới đây dựng theo ĐÚNG định dạng thật của
``Doctor::showOutputs()`` (``libkscreen`` v6.3.4, file ``src/doctor/
doctor.cpp``) — gồm cả mã màu ANSI (``\\x1b[01;32m``...) vì
``kscreen-doctor -o`` LUÔN in màu bất kể có phải TTY hay không (QTextStream
ghi thẳng, không kiểm ``isatty()``). Nếu ``strip_ansi``/``parse_outputs``
không xử lý đúng mã màu này, test dưới đây sẽ FAIL ngay — đây chính là lý
do bộ test được yêu cầu "feed sample kscreen-doctor -o text" thay vì chỉ
feed text đã làm sạch sẵn."""

from __future__ import annotations

import pytest
from namios_manchieu import display

_GREEN = "\x1b[01;32m"
_RED = "\x1b[01;31m"
_YELLOW = "\x1b[01;33m"
_BLUE = "\x1b[01;34m"
_CR = "\x1b[0;0m"


def _tail_block(output_type: str) -> str:
    """Phần đuôi lặp lại ở MỌI output (Scale/Rotation/.../ABM) — nội dung
    không ảnh hưởng tới parser (bị bỏ qua có chủ đích), chỉ thêm để fixture
    thật giống output thật, chứng minh parser KHÔNG vỡ vì các dòng lạ."""

    return (
        f"\t{_YELLOW}Scale: {_CR}1\n"
        f"\t{_YELLOW}Rotation: {_CR}1\n"
        f"\t{_YELLOW}Overscan: {_CR}0\n"
        f"\t{_YELLOW}Vrr: {_CR}incapable\n"
        f"\t{_YELLOW}RgbRange: {_CR}unknown\n"
        f"\t{_YELLOW}HDR: {_CR}incapable\n"
        f"\t{_YELLOW}Wide Color Gamut: {_CR}incapable\n"
        f"\t{_YELLOW}ICC profile: {_CR}incapable\n"
        f"\t{_YELLOW}Color profile source: {_CR}incapable\n"
        f"\t{_YELLOW}Brightness control: {_CR}unsupported\n"
        f"\t{_YELLOW}Color resolution: {_CR}unknown\n"
        f"\t{_YELLOW}Allow EDR: {_CR}unsupported\n"
        f"\t{_YELLOW}Sharpness control: {_CR}unsupported\n"
        f"\t{_YELLOW}Automatic brightness: {_CR}unsupported\n"
        f"\t{_YELLOW}Auto Rotate Policy: {_CR}incapable\n"
        f"\t{_YELLOW}Adaptive backlight modulation: {_CR}unsupported\n"
    )


def _internal_block(enabled: bool = True, priority: int = 1) -> str:
    state = f"{_GREEN}enabled{_CR}" if enabled else f"{_RED}disabled{_CR}"
    return (
        f"{_GREEN}Output: {_CR}1 eDP-1 {{55d6a1e2-0000-0000-0000-000000000001}}\n"
        f"\t{state}\n"
        f"\t{_GREEN}connected{_CR}\n"
        f"\t{_GREEN}priority {_CR}{priority}\n"
        f"\t{_YELLOW}Panel{_CR}\n"
        f"\t{_YELLOW}replication source:{_CR}0\n"
        f"\t{_BLUE}Modes: {_CR} 0:{_GREEN}1920x1080@60.00*{_CR}! 1:1680x1050@59.95 \n"
        f"\t{_YELLOW}Custom modes:{_CR} None\n"
        f"\t{_YELLOW}Geometry: {_CR}0,0 1920x1080\n" + _tail_block("Panel")
    )


def _external_block(enabled: bool = True, priority: int = 2, x: int = 1920) -> str:
    state = f"{_GREEN}enabled{_CR}" if enabled else f"{_RED}disabled{_CR}"
    return (
        f"{_GREEN}Output: {_CR}70 HDMI-A-1 {{9a111111-0000-0000-0000-000000000070}}\n"
        f"\t{state}\n"
        f"\t{_GREEN}connected{_CR}\n"
        f"\t{_GREEN}priority {_CR}{priority}\n"
        f"\t{_YELLOW}HDMI{_CR}\n"
        f"\t{_YELLOW}replication source:{_CR}0\n"
        f"\t{_BLUE}Modes: {_CR} 0:{_GREEN}1920x1080@60.00*{_CR}! 1:1280x720@60.00 \n"
        f"\t{_YELLOW}Custom modes:{_CR} None\n"
        f"\t{_YELLOW}Geometry: {_CR}{x},0 1920x1080\n" + _tail_block("HDMI")
    )


def _disconnected_dp_block() -> str:
    return (
        f"{_GREEN}Output: {_CR}71 DP-2 \n"
        f"\t{_RED}disabled{_CR}\n"
        f"\t{_RED}disconnected{_CR}\n"
        f"\t{_GREEN}priority {_CR}0\n"
        f"\t{_YELLOW}DisplayPort{_CR}\n"
        f"\t{_YELLOW}replication source:{_CR}0\n"
        f"\t{_BLUE}Modes: {_CR}\n"
        f"\t{_YELLOW}Custom modes:{_CR} None\n"
        f"\t{_YELLOW}Geometry: {_CR}0,0 0x0\n" + _tail_block("DisplayPort")
    )


SAMPLE_TWO_OUTPUTS = _internal_block() + _external_block() + _disconnected_dp_block()
SAMPLE_ONE_OUTPUT_ONLY = _internal_block()


# ---------------------------------------------------------------------------
# strip_ansi
# ---------------------------------------------------------------------------
def test_strip_ansi_removes_all_known_color_codes() -> None:
    raw = f"{_GREEN}Output: {_CR}1 eDP-1\n\t{_GREEN}enabled{_CR}\n"
    cleaned = display.strip_ansi(raw)
    assert "\x1b" not in cleaned
    assert cleaned == "Output: 1 eDP-1\n\tenabled\n"


# ---------------------------------------------------------------------------
# classify_output
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("name", "output_type", "expected"),
    [
        ("eDP-1", "Panel", "internal"),
        ("eDP-2", "", "internal"),
        ("LVDS-1", "", "internal"),
        ("LVDS1", "", "internal"),
        ("DSI-1", "", "internal"),
        ("HDMI-A-1", "HDMI", "external"),
        ("HDMI-1", "", "external"),
        ("DP-1", "DisplayPort", "external"),
        ("DP-2", "", "external"),
        ("VGA-1", "", "external"),
        ("DVI-I-1", "", "external"),
        ("USB-C-1", "", "external"),
        ("Virtual1", "", "unknown"),
        ("Virtual1", "Panel", "internal"),  # type-based fallback khi tên không khớp tiền tố nào
        ("Virtual1", "HDMI", "external"),
    ],
)
def test_classify_output(name: str, output_type: str, expected: str) -> None:
    assert display.classify_output(name, output_type) == expected


# ---------------------------------------------------------------------------
# parse_outputs
# ---------------------------------------------------------------------------
def test_parse_outputs_two_outputs_fields() -> None:
    outputs = display.parse_outputs(SAMPLE_TWO_OUTPUTS)
    assert [o.id for o in outputs] == [1, 70, 71]

    internal = outputs[0]
    assert internal.name == "eDP-1"
    assert internal.connected is True
    assert internal.enabled is True
    assert internal.disable_supported is True
    assert internal.priority == 1
    assert internal.output_type == "Panel"
    assert internal.kind == "internal"
    assert internal.geometry == (0, 0, 1920, 1080)
    assert internal.current_mode is not None
    assert internal.current_mode.width == 1920
    assert internal.current_mode.height == 1080
    assert internal.current_mode.is_preferred is True
    assert internal.effective_width == 1920

    external = outputs[1]
    assert external.name == "HDMI-A-1"
    assert external.kind == "external"
    assert external.connected is True
    assert external.priority == 2

    dp = outputs[2]
    assert dp.name == "DP-2"
    assert dp.connected is False
    assert dp.enabled is False
    assert dp.kind == "external"


def test_parse_outputs_empty_text_returns_empty_list() -> None:
    assert display.parse_outputs("") == []
    assert display.parse_outputs("khong co gi lien quan o day\n") == []


def test_parse_outputs_disable_unsupported_treated_as_enabled() -> None:
    block = (
        f"{_GREEN}Output: {_CR}1 eDP-1 \n"
        f"\t{_YELLOW}disable unsupported{_CR}\n"
        f"\t{_GREEN}connected{_CR}\n"
        f"\t{_GREEN}priority {_CR}1\n"
        f"\t{_YELLOW}Panel{_CR}\n"
    )
    outputs = display.parse_outputs(block)
    assert len(outputs) == 1
    assert outputs[0].enabled is True
    assert outputs[0].disable_supported is False


# ---------------------------------------------------------------------------
# pick_displays
# ---------------------------------------------------------------------------
def test_pick_displays_success() -> None:
    outputs = display.parse_outputs(SAMPLE_TWO_OUTPUTS)
    internal, external = display.pick_displays(outputs)
    assert internal.name == "eDP-1"
    assert external.name == "HDMI-A-1"


def test_pick_displays_only_one_connected_output_raises_friendly_message() -> None:
    outputs = display.parse_outputs(SAMPLE_ONE_OUTPUT_ONLY)
    with pytest.raises(display.DisplayError) as exc_info:
        display.pick_displays(outputs)
    assert exc_info.value.message == (
        "Chưa thấy màn hình ngoài — cắm cáp HDMI/VGA/USB-C vào máy chiếu rồi bấm Làm mới."
    )


def test_pick_displays_disconnected_external_does_not_count() -> None:
    """eDP-1 (trong máy, connected) + DP-2 (ngoài nhưng ĐÃ RÚT CÁP) — vẫn chỉ
    có 1 output thật sự kết nối -> thông báo "chưa thấy màn hình ngoài",
    KHÔNG được coi DP-2 là màn ngoài sẵn sàng dùng."""

    outputs = display.parse_outputs(_internal_block() + _disconnected_dp_block())
    with pytest.raises(display.DisplayError) as exc_info:
        display.pick_displays(outputs)
    assert exc_info.value.message == display.NO_EXTERNAL_MESSAGE


def test_pick_displays_no_outputs_at_all() -> None:
    with pytest.raises(display.DisplayError) as exc_info:
        display.pick_displays([])
    assert exc_info.value.message == display.NO_OUTPUTS_MESSAGE


def test_pick_displays_no_internal_candidate() -> None:
    """Hai màn hình ngoài kết nối (desktop PC không có panel laptop) -> báo
    đúng "không tìm thấy màn hình trong", không đoán nhầm 1 trong 2 là
    "trong máy"."""

    two_externals = _external_block() + _external_block().replace("70 HDMI-A-1", "71 DP-2")
    outputs = display.parse_outputs(two_externals)
    with pytest.raises(display.DisplayError) as exc_info:
        display.pick_displays(outputs)
    assert exc_info.value.message == display.NO_INTERNAL_MESSAGE


# ---------------------------------------------------------------------------
# build_argv_tokens — đúng 4 chế độ, CHỈ dùng enable/disable/position/priority.
# ---------------------------------------------------------------------------
@pytest.fixture()
def two_outputs() -> tuple[display.OutputInfo, display.OutputInfo]:
    outputs = display.parse_outputs(SAMPLE_TWO_OUTPUTS)
    return display.pick_displays(outputs)


def test_build_argv_tokens_mirror(two_outputs) -> None:
    internal, external = two_outputs
    tokens = display.build_argv_tokens(display.MODE_MIRROR, internal, external)
    assert tokens == (
        "output.1.enable",
        "output.1.position.0,0",
        "output.1.priority.1",
        "output.70.enable",
        "output.70.position.0,0",
        "output.70.priority.2",
    )


def test_build_argv_tokens_extend_uses_internal_width(two_outputs) -> None:
    internal, external = two_outputs
    tokens = display.build_argv_tokens(display.MODE_EXTEND, internal, external)
    assert tokens == (
        "output.1.enable",
        "output.1.position.0,0",
        "output.1.priority.1",
        "output.70.enable",
        "output.70.position.1920,0",
        "output.70.priority.2",
    )


def test_build_argv_tokens_internal_only(two_outputs) -> None:
    internal, external = two_outputs
    tokens = display.build_argv_tokens(display.MODE_INTERNAL_ONLY, internal, external)
    assert tokens == (
        "output.1.enable",
        "output.1.position.0,0",
        "output.1.priority.1",
        "output.70.disable",
    )


def test_build_argv_tokens_external_only(two_outputs) -> None:
    internal, external = two_outputs
    tokens = display.build_argv_tokens(display.MODE_EXTERNAL_ONLY, internal, external)
    assert tokens == (
        "output.70.enable",
        "output.70.position.0,0",
        "output.70.priority.1",
        "output.1.disable",
    )


def test_build_argv_tokens_only_uses_ids_never_names(two_outputs) -> None:
    """Token PHẢI dùng ID số (``output.70...``), KHÔNG dùng tên connector
    (``output.HDMI-A-1...``) — xem lý do (tên có thể chứa dấu chấm, phá cú
    pháp phân tách-bằng-chấm của chính kscreen-doctor) trong docstring
    module ``display``."""

    internal, external = two_outputs
    for mode in display.ALL_MODES:
        tokens = display.build_argv_tokens(mode, internal, external)
        joined = " ".join(tokens)
        assert "HDMI-A-1" not in joined
        assert "eDP-1" not in joined


def test_build_argv_tokens_invalid_mode_raises(two_outputs) -> None:
    internal, external = two_outputs
    with pytest.raises(ValueError):
        display.build_argv_tokens("khong-ton-tai", internal, external)


# ---------------------------------------------------------------------------
# plan() — điểm vào gộp (pick + build + describe trong 1 lần).
# ---------------------------------------------------------------------------
def test_plan_returns_consistent_tokens_and_description() -> None:
    outputs = display.parse_outputs(SAMPLE_TWO_OUTPUTS)
    result = display.plan(display.MODE_EXTERNAL_ONLY, outputs)
    assert result.mode == display.MODE_EXTERNAL_ONLY
    assert result.internal.name == "eDP-1"
    assert result.external.name == "HDMI-A-1"
    assert result.tokens == display.build_argv_tokens(
        display.MODE_EXTERNAL_ONLY, result.internal, result.external
    )
    assert "HDMI-A-1" in result.description_vi
    assert "eDP-1" in result.description_vi


def test_plan_raises_display_error_when_not_enough_outputs() -> None:
    outputs = display.parse_outputs(SAMPLE_ONE_OUTPUT_ONLY)
    with pytest.raises(display.DisplayError):
        display.plan(display.MODE_MIRROR, outputs)


def test_plan_invalid_mode_raises_value_error() -> None:
    outputs = display.parse_outputs(SAMPLE_TWO_OUTPUTS)
    with pytest.raises(ValueError):
        display.plan("khong-hop-le", outputs)
