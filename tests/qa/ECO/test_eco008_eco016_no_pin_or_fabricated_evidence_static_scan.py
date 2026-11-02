"""ECO-008/ECO-016 — quét tĩnh mã nguồn ``namios_eco`` (module Python thuần
đang được giao việc): KHÔNG có nơi nào thu thập PIN/token key thật, KHÔNG
có nơi nào tự "bịa" biên nhận/kết quả nộp (hardcode một evidence_ref/
receipt giả rồi coi như pass) để né việc chạy thật hoặc né ghi
``blocked_external_dependency``.

Đây là kiểm tra ĐỘC LẬP ở cấp mã nguồn (không phải ở cấp dữ liệu catalog —
xem ``test_eco006_catalog_real_files_integrity_adversarial.py`` cho phần
đó), để phát hiện sớm nếu một thay đổi code sau này vô tình thêm logic bịa
evidence hoặc field thu PIN."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ECO_SRC_DIR = _REPO_ROOT / "src" / "namios_eco"

#: Cụm/khoá gợi ý "thu PIN/token key thật" trong code xử lý — không nên
#: xuất hiện dưới dạng field/param nào trong namios_eco (module này chỉ mô
#: hình hoá + thẩm định dữ liệu khảo sát, không chạm phần cứng/plugin ký).
_PIN_TOKEN_COLLECTION_MARKERS = (
    "input(",  # không prompt nhập liệu tương tác nào trong module thuần này
    "getpass",
    "pin_code",
    "token_pin",
    "private_key",
)

#: Cụm gợi ý hành vi "tự tạo evidence giả trông như thật" — khác với các
#: GIÁ TRỊ VÍ DỤ trong docstring (``evidence://sandbox/...`` chỉ xuất hiện ở
#: test fixture của dev, không phải trong `src/`).
_FABRICATED_EVIDENCE_MARKERS = (
    "fake_receipt",
    "mock_receipt",
    "dummy_evidence_ref",
    "auto_generate_receipt",
)


def _all_source_files() -> list[Path]:
    files = sorted(_ECO_SRC_DIR.glob("*.py"))
    assert files, f"Không tìm thấy file nguồn nào ở {_ECO_SRC_DIR}"
    return files


def test_eco_source_dir_exists_and_has_files() -> None:
    assert _ECO_SRC_DIR.is_dir()
    assert _all_source_files()


def test_no_pin_or_token_collection_marker_in_eco_source() -> None:
    for path in _all_source_files():
        text = path.read_text(encoding="utf-8").casefold()
        for marker in _PIN_TOKEN_COLLECTION_MARKERS:
            assert marker not in text, (
                f"{path.relative_to(_REPO_ROOT)}: chứa dấu hiệu thu PIN/token "
                f"('{marker}') — ECO-008 cấm tuyệt đối việc tự thu PIN/token key."
            )


def test_no_fabricated_evidence_marker_in_eco_source() -> None:
    for path in _all_source_files():
        text = path.read_text(encoding="utf-8").casefold()
        for marker in _FABRICATED_EVIDENCE_MARKERS:
            assert marker not in text, (
                f"{path.relative_to(_REPO_ROOT)}: chứa dấu hiệu bịa biên nhận "
                f"('{marker}') — ECO-016 cấm tuyệt đối việc bịa biên nhận."
            )


def test_eco_module_never_calls_network_or_subprocess_to_auto_submit() -> None:
    """``namios_eco`` CHỈ mô hình hoá/thẩm định dữ liệu đã có — không tự
    gửi hồ sơ/đăng nhập/mở kết nối ra ngoài (ECO-016 phần "không tự gửi tin/
    liên hệ vendor/đăng nhập"). Quét các API I/O-ra-ngoài phổ biến nhất
    trong Python; module hợp lệ (schema/state machine/validator thuần) thì
    tuyệt đối không cần tới chúng."""

    forbidden_calls = ("urllib.request", "requests.", "httpx.", "subprocess.", "socket.")
    for path in _all_source_files():
        text = path.read_text(encoding="utf-8")
        for marker in forbidden_calls:
            assert marker not in text, (
                f"{path.relative_to(_REPO_ROOT)}: dùng '{marker}' — module "
                "namios_eco không được tự thực hiện I/O ra ngoài/subprocess."
            )
