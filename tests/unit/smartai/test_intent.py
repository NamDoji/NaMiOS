"""Test ``namios_smartai.intent`` (SAI-001, Phụ lục 04).

Bao gồm nghiệm thu T01: "cài MISA" thiếu phiên bản/license → ``unknowns``
có "version"/"license", không tự bịa; và bất biến "không tự đoán người
nộp/khoản tiền" cho ``submit_filing``.
"""

from __future__ import annotations

from namios_smartai._types import IntentResult
from namios_smartai.intent import FakeModelProvider, parse_intent


def test_cai_misa_khong_co_phien_ban_can_hoi_them() -> None:
    result = parse_intent("Cài MISA", FakeModelProvider())

    assert result.intent == "install_app"
    assert result.target_app == "misa"
    assert "version" in result.unknowns
    assert "license" in result.unknowns
    assert result.confidence >= 0.6


def test_cai_misa_khong_dau_cho_ket_qua_giong_co_dau() -> None:
    co_dau = parse_intent("Cài MISA", FakeModelProvider())
    khong_dau = parse_intent("cai misa", FakeModelProvider())

    assert khong_dau.intent == co_dau.intent == "install_app"
    assert khong_dau.target_app == co_dau.target_app == "misa"
    assert set(khong_dau.unknowns) == set(co_dau.unknowns)
    assert khong_dau.confidence == co_dau.confidence


def test_nop_to_khai_khong_bia_nguoi_nop_va_so_tien() -> None:
    result = parse_intent("Hôm nay tôi muốn nộp tờ khai", FakeModelProvider())

    assert result.intent == "submit_filing"
    assert "nguoi_nop" in result.unknowns
    assert "so_tien" in result.unknowns
    # Bất biến an toàn: không có trường nào ngầm mang theo người nộp/khoản
    # tiền khi chính các trường đó đang bị đánh dấu chưa rõ.
    assert result.target_data is None
    assert result.required_outcome is None


def test_cau_vo_nghia_la_unknown_va_do_tin_cay_thap() -> None:
    result = parse_intent("qwzx blerg flonk zzzpt", FakeModelProvider())

    assert result.intent == "unknown"
    assert result.confidence < 0.5


def test_fake_model_provider_tat_dinh_khong_ngau_nhien() -> None:
    provider = FakeModelProvider()
    utterance = "Cài MISA phiên bản 2024 bản mới nhất"

    first = provider.interpret(utterance)
    second = provider.interpret(utterance)

    assert first == second


def test_fake_model_provider_tat_dinh_cho_cau_hoi_mo() -> None:
    provider = FakeModelProvider()
    utterance = "Tôi muốn mở Zalo"

    first = provider.interpret(utterance)
    second = provider.interpret(utterance)

    assert first == second
    assert first.intent == "open_app"
    assert first.target_app == "zalo"
    assert first.confidence >= 0.9


def test_in_tai_lieu_nhan_dien_dung_khong_nham_lan_tu_khac() -> None:
    # "minh" chứa chuỗi con "in" — khớp theo RANH GIỚI TỪ để không nhận
    # nhầm thành print_document.
    result = parse_intent("Bạn tên là Minh à", FakeModelProvider())

    assert result.intent == "unknown"


def test_in_tai_lieu_duoc_nhan_dien_dung_khi_la_tu_rieng() -> None:
    result = parse_intent("Tôi muốn in tài liệu Word này", FakeModelProvider())

    assert result.intent == "print_document"
    assert result.target_app == "word"
    assert result.confidence >= 0.9


def test_submit_filing_co_nguoi_nop_va_so_tien_tuong_minh_thi_khong_hoi_lai() -> None:
    result = parse_intent(
        "Tôi là người nộp thuế, nộp tờ khai thuế GTGT số tiền 5000000 vnd", FakeModelProvider()
    )

    assert result.intent == "submit_filing"
    assert "nguoi_nop" not in result.unknowns
    assert "so_tien" not in result.unknowns


def test_parse_intent_giu_nguyen_ket_qua_khi_provider_tra_ve_du_lieu_sach() -> None:
    class _StubProvider:
        def interpret(self, utterance: str) -> IntentResult:
            return IntentResult(intent="open_app", target_app="zalo", confidence=0.9)

    result = parse_intent("bất kỳ", _StubProvider())

    assert result.intent == "open_app"
    assert result.target_app == "zalo"
    assert result.unknowns == ()


def test_parse_intent_xoa_payer_amount_bi_bia_du_da_danh_dau_unknown() -> None:
    """Lớp an toàn SAU provider: dù một provider (giả định là model thật
    sau này) có lỡ "ảo giác" ra target_data/required_outcome, nếu chính nó
    đã đánh dấu payer/amount là unknown thì parse_intent phải xoá sạch,
    không để lọt ra ngoài một giá trị ngầm mang theo người nộp/khoản tiền.
    """

    class _HallucinatingProvider:
        def interpret(self, utterance: str) -> IntentResult:
            return IntentResult(
                intent="submit_filing",
                target_data="Nguyễn Văn A nộp 10.000.000đ",
                required_outcome="Nộp xong tờ khai thay Nguyễn Văn A",
                unknowns=("nguoi_nop", "so_tien"),
                confidence=0.4,
            )

    result = parse_intent("nộp tờ khai", _HallucinatingProvider())

    assert result.target_data is None
    assert result.required_outcome is None
    assert "nguoi_nop" in result.unknowns
    assert "so_tien" in result.unknowns
