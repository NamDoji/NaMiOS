"""ECO-007 — GATE đối kháng: cụm bị cấm "ứng dụng chính thức của NaMiOS"
(tả sản phẩm bên thứ ba) phải bị chặn DÙ văn bản được chuẩn hoá Unicode
khác nhau — vì văn bản purpose/mô tả trong catalog có thể đến từ nhiều
nguồn (export Windows, copy-paste trình soạn thảo khác nhau...), không
đảm bảo luôn ở dạng NFC "đẹp".

So sánh đối chứng: ``namios_eco.search.fold_vn`` (CÙNG package) đã giải
đúng bài toán này cho mục đích tìm kiếm (NFD rồi strip tổ hợp dấu rồi NFC +
casefold) — ``validate_no_official_claim_text`` (``validator.py``) KHÔNG
dùng kỹ thuật tương đương, chỉ ``.casefold()`` thô trên chuỗi gốc."""

from __future__ import annotations

import unicodedata

import pytest

from namios_eco.search import fold_vn
from namios_eco.validator import validate_no_official_claim_text

_FORBIDDEN_NFC = "ứng dụng chính thức của NaMiOS cho kế toán."


def test_baseline_nfc_forbidden_phrase_is_caught() -> None:
    """Đối chứng dương: dạng NFC "đẹp" (dev đã test) vẫn đúng — không phải
    test môi trường sai."""

    errors = validate_no_official_claim_text(_FORBIDDEN_NFC, path="purpose")
    assert errors and errors[0].code == "E_ECO_OFFICIAL_CLAIM_FORBIDDEN"


def test_nfd_decomposed_forbidden_phrase_bypasses_gate() -> None:
    """DEFECT: cùng câu văn, chỉ đổi sang Unicode NFD (tổ hợp dấu rời — một
    dạng chuẩn hoá Unicode Việt Nam hợp lệ, không phải ký tự lạ/injection),
    hoàn toàn LỌT QUA ``validate_no_official_claim_text`` — trả về ``[]``
    (không lỗi) dù nội dung hiển thị giống hệt bản NFC đã bị cấm.

    Nếu dòng dưới FAIL (errors rỗng) — đó LÀ bằng chứng defect (xem
    ``qa/evidence-index/ECO/defects.md``), KHÔNG phải test sai: thử lại với
    ``unicodedata.normalize("NFC", ...)`` của cùng chuỗi để xác nhận nó
    hiển thị y hệt bản gốc bị cấm."""

    nfd_text = unicodedata.normalize("NFD", _FORBIDDEN_NFC)
    # Xác nhận đây đúng là "cùng nội dung hiển thị", chỉ khác biểu diễn nội
    # bộ — tránh báo nhầm do tự gõ sai chuỗi.
    assert unicodedata.normalize("NFC", nfd_text) == _FORBIDDEN_NFC

    errors = validate_no_official_claim_text(nfd_text, path="purpose")
    assert errors, (
        "DEFECT: bản NFD của cùng cụm cấm 'ứng dụng chính thức của NaMiOS' "
        "lọt qua validate_no_official_claim_text() — trả về [] (không lỗi) "
        "dù nội dung hiển thị giống hệt bản NFC đã bị chặn đúng."
    )


def test_fold_vn_in_same_package_already_handles_nfd_correctly() -> None:
    """Đối chứng kỹ thuật: ``fold_vn`` (dùng cho search, CÙNG package
    ``namios_eco``) xử lý ĐÚNG trường hợp NFD — chứng minh gap ở
    ``validate_no_official_claim_text`` không phải do Python/unicodedata
    không hỗ trợ, mà do hàm đó không tái dùng kỹ thuật đã có sẵn trong
    package của chính nó."""

    nfd_text = unicodedata.normalize("NFD", "chính thức")
    assert fold_vn(nfd_text) == fold_vn("chính thức") == "chinh thuc"


@pytest.mark.parametrize(
    "word_index",
    [3, 4],
    ids=["before-thuc", "before-cua"],
)
def test_zero_width_space_inside_forbidden_phrase_also_bypasses_gate(
    word_index: int,
) -> None:
    """DEFECT (biến thể thứ hai, CÙNG root cause — thiếu chuẩn hoá trước khi
    so khớp substring): chèn một dấu cách độ rộng không (U+200B, một ký tự
    định dạng KHÔNG hiển thị, KHÔNG phải ký tự lạ/injection nguy hiểm) ngay
    TRƯỚC một từ Ở GIỮA cụm bị cấm ("thức"/"của" — không phải từ đầu cụm) đủ
    để phá vỡ khớp substring liên tục cho CẢ 3 biến thể cụm cấm, trong khi
    văn bản hiển thị cho người đọc (copy ra ngoài, xem trong trình soạn
    thảo) vẫn đọc y hệt "ứng dụng chính thức của NaMiOS" (ZWSP vô hình).

    (Chèn trước các từ ĐẦU cụm — "ứng"/"dụng"/"chính" — KHÔNG bypass được,
    vì khi đó cụm cấm NGẮN HƠN "chính thức của namios" vẫn khớp nguyên vẹn
    từ vị trí 'chính' trở đi, không bị ZWSP chen vào giữa; đã tự kiểm tay
    riêng, không đưa vào bộ parametrize này để tránh test giả-dương không
    minh họa được defect.)"""

    words = _FORBIDDEN_NFC.split(" ")
    words[word_index] = "​" + words[word_index]
    tampered = " ".join(words)

    errors = validate_no_official_claim_text(tampered, path="purpose")
    assert errors, (
        "DEFECT: chèn U+200B (zero-width space, không hiển thị) ngay trước "
        f"'{words[word_index].lstrip(chr(0x200B))}' vẫn lọt qua "
        f"validate_no_official_claim_text(). tampered={tampered!r}"
    )
