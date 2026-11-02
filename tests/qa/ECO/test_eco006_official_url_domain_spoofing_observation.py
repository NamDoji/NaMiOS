"""ECO-006 — quan sát GATE (KHÔNG phải defect xác nhận, xem
``qa/evidence-index/ECO/defects.md`` mục "Quan sát/PLAUSIBLE"):
``validate_official_url`` theo đúng docstring hiện tại CHỈ kiểm (a) scheme
http(s) và (b) thông tin xác thực nhúng kiểu ``user@host``. Hàm KHÔNG (và
không thể, vì không nhận "domain kỳ vọng" làm tham số) phát hiện kiểu giả
mạo domain qua subdomain-suffix (``gov.vn`` xuất hiện như một nhãn con của
một domain đăng ký khác, không phải chính domain .gov.vn thật).

Test dưới đây XÁC NHẬN hành vi HIỆN TẠI (pass — không phải lỗi so với lời
hứa trong docstring) và ghi lại rõ gap này để BA/dev cân nhắc có cần thêm
tham số "allowed_domain_suffixes" cho một lớp kiểm domain mạnh hơn không."""

from __future__ import annotations

from namios_eco.validator import validate_official_url


def test_current_scope_catches_embedded_credentials_as_documented() -> None:
    errors = validate_official_url("https://co-quan.gov.vn@trang-gia.example/")
    assert errors  # đúng theo docstring/hành vi dev đã test


def test_subdomain_suffix_domain_spoofing_is_not_caught_by_current_scope() -> None:
    """QUAN SÁT: URL này KHÔNG nhúng credentials (không có ``@``), scheme
    hợp lệ (https) — nên theo đúng phạm vi hiện tại của hàm, KHÔNG trả lỗi.
    Nhưng domain ĐĂNG KÝ thật của URL này là ``phishing-example.com``
    (``dichvucong.gov.vn`` chỉ là một NHÃN CON/subdomain, không phải domain
    chính thức), một kỹ thuật giả mạo domain phổ biến. Phạm vi hiện tại của
    hàm không bắt được trường hợp này — vì hàm không có tham số "domain
    chính thức kỳ vọng" để so khớp registrable-domain thật."""

    spoofed = "https://dichvucong.gov.vn.phishing-example.com/"
    errors = validate_official_url(spoofed)
    assert errors == [], (
        "Hành vi hiện tại: không báo lỗi cho domain giả mạo kiểu subdomain-"
        f"suffix ({spoofed!r}). Đây là quan sát/gap đã biết (xem "
        "defects.md), không phải assertion kỳ vọng sai của test."
    )
