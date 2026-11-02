"""ECO-007 — GATE đối kháng cho tìm kiếm: tên có dấu vs không dấu, tên
provider "lạ" (viết tắt/số/nước ngoài, không phải tiếng Việt thuần), hoa/
thường trộn lẫn, và việc tìm kiếm KHÔNG được tự gắn nhãn "ứng dụng chính
thức của NaMiOS" cho kết quả (SearchHit chỉ trả dữ liệu entry gốc,
không tự thêm tuyên bố)."""

from __future__ import annotations

from namios_eco.models import ServiceEntry
from namios_eco.search import fold_vn, search_services
from namios_eco.status import PublishedStatus, WindowsMode


def _entry(**overrides: object) -> ServiceEntry:
    base: dict[str, object] = dict(
        id="qa.entry",
        provider="QA Provider",
        agency=None,
        purpose="purpose",
        official_url="https://example.gov.vn/",
        source_check="test",
        version=None,
        license="test",
        published_os=(),
        dependencies=(),
        account_condition="Không cần token",
        service_cost="free",
        data_sensitivity="cong_khai",
        test_profile="qa",
        last_updated="2026-11-02",
        evidence_source="https://example.gov.vn/",
        published_status=PublishedStatus.NOT_INVENTORIED,
        windows_mode=WindowsMode.WEB_LINUX,
        tested_by_namios=False,
        officially_supported_by_vendor=False,
    )
    base.update(overrides)
    return ServiceEntry(**base)  # type: ignore[arg-type]


def _catalog() -> tuple[ServiceEntry, ...]:
    return (
        _entry(id="thue.htkk", provider="Tổng cục Thuế", purpose="Lập tờ khai thuế hộ kinh doanh"),
        _entry(
            id="ketoan.ts24",
            provider="TS24",  # provider "lạ" — viết tắt chữ hoa + số, không phải tên tiếng Việt
            purpose="Dịch vụ I-VAN giao dịch điện tử BHXH",
        ),
        _entry(
            id="ketoan.misa",
            provider="MISA",  # provider thương hiệu nước ngoài-gốc-Latin viết hoa
            purpose="Phần mềm kế toán đóng gói",
        ),
        _entry(
            id="giaoduc.hocba",
            provider="Bộ GDĐT",
            purpose="Nhập điểm Học Bạ điện tử",  # hoa/thường trộn
        ),
    )


# -- có dấu vs không dấu, cùng kết quả -----------------------------------


def test_search_with_full_diacritics_matches_same_as_without() -> None:
    with_marks = {h.entry.id for h in search_services(_catalog(), "khai thuế")}
    without_marks = {h.entry.id for h in search_services(_catalog(), "khai thue")}
    assert with_marks == without_marks == {"thue.htkk"}


def test_search_partial_diacritics_still_matches() -> None:
    """Người dùng gõ nửa có dấu nửa không (bàn phím lỗi font) — ``fold_vn``
    chuẩn hoá CẢ HAI phía nên vẫn khớp."""

    mixed = {h.entry.id for h in search_services(_catalog(), "hoc ba")}
    assert mixed == {"giaoduc.hocba"}


def test_search_uppercase_lowercase_mixed_query_matches() -> None:
    hits = {h.entry.id for h in search_services(_catalog(), "hỌc BẠ")}
    assert hits == {"giaoduc.hocba"}


# -- tên provider "lạ" (viết tắt/số/thương hiệu nước ngoài) ---------------


def test_search_by_alphanumeric_provider_name_ts24() -> None:
    hits = {h.entry.id for h in search_services(_catalog(), "ts24")}
    assert hits == {"ketoan.ts24"}


def test_search_by_uppercase_latin_brand_provider_misa_case_insensitive() -> None:
    hits_upper = {h.entry.id for h in search_services(_catalog(), "MISA")}
    hits_lower = {h.entry.id for h in search_services(_catalog(), "misa")}
    assert hits_upper == hits_lower == {"ketoan.misa"}


def test_search_provider_substring_does_not_cross_match_unrelated_entries() -> None:
    """Tấn công ngược: tìm 1 ký tự chung ('a') không được kéo TOÀN BỘ
    catalog vào kết quả nếu có giới hạn ``limit`` nhỏ, và danh sách trả về
    PHẢI là tập con thật (không lẫn entry hoàn toàn không khớp)."""

    hits = search_services(_catalog(), "misa", limit=50)
    assert all("misa" in fold_vn(h.entry.provider) for h in hits)


# -- SearchHit không tự gắn tuyên bố "chính thức của NaMiOS" --------------


def test_search_hit_never_injects_official_namios_claim_into_result_text() -> None:
    """Kết quả tìm kiếm chỉ phản chiếu dữ liệu entry gốc — không có đường
    nào trong ``search_services``/``SearchHit`` tự ý thêm cụm "ứng dụng
    chính thức của NaMiOS" vào bất kỳ trường nào của kết quả (ECO-007)."""

    for hit in search_services(_catalog(), "thue"):
        assert "chính thức của namios" not in hit.entry.purpose.casefold()
        assert "chính thức của namios" not in hit.entry.provider.casefold()
