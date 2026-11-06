"""APP11-001/013 — nhãn phân phối ĐÚNG. Bám E11-01 (Office/IME/PDF offline chạy
được, web shortcut giải thích cần mạng)."""

from __future__ import annotations

from namios_essentials import (
    DeliveryLabel,
    DeliveryType,
    EssentialsManifest,
    delivery_label,
    needs_connection,
    web_label_is_honest,
)

DT = DeliveryType
DL = DeliveryLabel


def _manifest(delivery_type: DeliveryType, *, offline: bool = False) -> EssentialsManifest:
    return EssentialsManifest(
        id="x",
        title="X",
        publisher="P",
        category="c",
        delivery_type=delivery_type,
        official_url="https://example.com/" if delivery_type is not DT.INSTALLED_NATIVE else "",
        offline=offline,
    )


def test_installed_native_label() -> None:
    assert delivery_label(_manifest(DT.INSTALLED_NATIVE)) is DL.INSTALLED


def test_wine_optional_label() -> None:
    assert delivery_label(_manifest(DT.WINE_OPTIONAL)) is DL.WINE_TESTED


def test_official_web_without_offline_needs_connection() -> None:
    # E11-01: web shortcut giải thích CẦN MẠNG khi chưa khai offline thật.
    m = _manifest(DT.OFFICIAL_WEB, offline=False)
    assert delivery_label(m) is DL.NEEDS_CONNECTION
    assert needs_connection(m) is True


def test_official_web_with_offline_declared_is_web_service() -> None:
    m = _manifest(DT.OFFICIAL_WEB, offline=True)
    assert delivery_label(m) is DL.WEB_SERVICE
    assert needs_connection(m) is False


def test_installed_native_never_needs_connection() -> None:
    # E11-01: Office/IME/PDF cài sẵn chạy offline, không phải "cần kết nối".
    assert needs_connection(_manifest(DT.INSTALLED_NATIVE)) is False


def test_official_web_never_labeled_installed_or_wine() -> None:
    # APP11-001 nghiệm thu: official_web KHÔNG BAO GIỜ gán nhãn "cài trên máy"/
    # "qua Wine" dù offline cờ nào.
    for offline in (True, False):
        label = delivery_label(_manifest(DT.OFFICIAL_WEB, offline=offline))
        assert label not in (DL.INSTALLED, DL.WINE_TESTED)


def test_web_label_rejects_misleading_display_text() -> None:
    m = _manifest(DT.OFFICIAL_WEB)
    assert web_label_is_honest(m, "Zalo Web") is True
    assert web_label_is_honest(m, "Zalo đã cài trên máy") is False
    assert web_label_is_honest(m, "Bản Linux của Zalo") is False


def test_web_label_check_not_applicable_to_native() -> None:
    m = _manifest(DT.INSTALLED_NATIVE)
    # Không áp dụng cho native — luôn True dù chữ có 'đã cài' (đúng sự thật).
    assert web_label_is_honest(m, "Đã cài trên máy") is True
