"""ECO-007 — tìm theo tên phổ thông, có/không dấu, không phân biệt hoa/thường."""

from __future__ import annotations

from tests.unit.eco._fixtures import make_entry

from namios_eco.search import fold_vn, search_services


def test_fold_vn_strips_diacritics_and_casefolds() -> None:
    assert fold_vn("Khai Thuế") == "khai thue"
    assert fold_vn("ĐĂNG NHẬP") == "dang nhap"
    assert fold_vn("đăng nhập") == "dang nhap"


def _entries():
    return (
        make_entry(id="thue.etax", purpose="Khai thuế hộ kinh doanh", provider="Tổng cục Thuế"),
        make_entry(
            id="bhxh.hoso",
            purpose="Lập hồ sơ bảo hiểm xã hội",
            provider="BHXH Việt Nam",
            agency="BHXH Việt Nam",
            dependencies=(),
            account_condition="Không cần token, chỉ cần tài khoản thường",
        ),
        make_entry(
            id="giaoduc.hocba",
            purpose="Nhập điểm học bạ điện tử",
            provider="Bộ GDĐT",
            dependencies=(),
        ),
    )


def test_search_with_diacritics() -> None:
    hits = search_services(_entries(), "khai thuế")
    assert [h.entry.id for h in hits] == ["thue.etax"]


def test_search_without_diacritics() -> None:
    hits = search_services(_entries(), "khai thue")
    assert [h.entry.id for h in hits] == ["thue.etax"]


def test_search_case_insensitive() -> None:
    hits = search_services(_entries(), "HOC BA")
    assert [h.entry.id for h in hits] == ["giaoduc.hocba"]


def test_search_by_provider() -> None:
    hits = search_services(_entries(), "bhxh")
    assert [h.entry.id for h in hits] == ["bhxh.hoso"]


def test_search_empty_query_returns_nothing() -> None:
    assert search_services(_entries(), "   ") == ()


def test_search_no_match_returns_empty() -> None:
    assert search_services(_entries(), "khong co gi khop ca") == ()


def test_search_limit_respected() -> None:
    hits = search_services(_entries(), "a", limit=1)
    assert len(hits) <= 1


def test_requires_account_or_token_true_when_dependencies_present() -> None:
    hits = search_services(_entries(), "khai thue")
    assert hits[0].requires_account_or_token is True


def test_requires_account_or_token_false_when_marked_not_required() -> None:
    hits = search_services(_entries(), "bao hiem xa hoi")
    assert hits[0].requires_account_or_token is False
