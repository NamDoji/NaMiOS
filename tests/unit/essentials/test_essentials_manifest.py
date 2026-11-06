"""APP11-002/034 — manifest có nguồn + giấy phép phân phối.

Bám nghiệm thu APP11-002 ("mục thiếu nguồn hoặc quyền dùng không xuất hiện ở
ảnh cài chính thức"), APP11-034 ("SBOM và license inventory khớp từng app") và
§5 ("Mọi app phải có owner, nguồn và test date").
"""

from __future__ import annotations

import dataclasses

from namios_essentials import (
    DeliveryType,
    EssentialsManifest,
    Provenance,
    is_shippable,
    may_bundle_binary,
    validate_manifest,
)
from namios_essentials._errors import EssentialsErrorCode

DT = DeliveryType


def _official_web(**overrides: object) -> EssentialsManifest:
    base = dict(
        id="zalo.web",
        title="Zalo Web",
        publisher="Zalo",
        category="lien_lac",
        delivery_type=DT.OFFICIAL_WEB,
        official_url="https://id.zalo.me/",
        owner="namios-essentials-team",
        last_verified="2026-11-06",
    )
    base.update(overrides)
    return EssentialsManifest(**base)  # type: ignore[arg-type]


def _native(**overrides: object) -> EssentialsManifest:
    base = dict(
        id="namios-office",
        title="NaMi Office",
        publisher="NaMiOS",
        category="lam_viec",
        delivery_type=DT.INSTALLED_NATIVE,
        package_source=Provenance(
            source_url="https://repo.namios.vn/office",
            package="namios-office",
            version="1.0",
            sha256="deadbeef",
            signature_ok=True,
            license="MPL-2.0",
            official=True,
        ),
        license="MPL-2.0",
        owner="namios-essentials-team",
        last_verified="2026-11-06",
    )
    base.update(overrides)
    return EssentialsManifest(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# APP11-002 — thiếu nguồn hoặc license → is_shippable=False                     #
# --------------------------------------------------------------------------- #


def test_web_manifest_with_official_url_is_shippable() -> None:
    assert is_shippable(_official_web()) is True
    assert validate_manifest(_official_web()) == ()


def test_web_manifest_without_url_is_not_shippable() -> None:
    m = _official_web(official_url="")
    assert is_shippable(m) is False
    assert EssentialsErrorCode.E_APP11_MANIFEST_NO_SOURCE.value in validate_manifest(m)


def test_native_manifest_without_package_source_is_not_shippable() -> None:
    m = _native(package_source=None)
    assert is_shippable(m) is False
    assert EssentialsErrorCode.E_APP11_MANIFEST_NO_SOURCE.value in validate_manifest(m)


def test_native_manifest_with_untrusted_provenance_is_not_shippable() -> None:
    # provenance_ok (tái dùng namios_e08) đòi official + sha256 + signature_ok.
    bad_source = Provenance(official=False, sha256="x", signature_ok=True)
    m = _native(package_source=bad_source)
    assert is_shippable(m) is False


def test_native_manifest_without_license_is_not_shippable() -> None:
    m = _native(license="")
    assert is_shippable(m) is False
    assert EssentialsErrorCode.E_APP11_MANIFEST_NO_LICENSE.value in validate_manifest(m)


def test_missing_owner_or_test_date_blocks_shippability() -> None:
    # §5: "Mọi app phải có owner, nguồn và test date".
    no_owner = _native(owner="")
    no_date = _native(last_verified=None)
    assert is_shippable(no_owner) is False
    assert is_shippable(no_date) is False
    for m in (no_owner, no_date):
        assert EssentialsErrorCode.E_APP11_MANIFEST_NO_OWNER_OR_TESTDATE.value in validate_manifest(
            m
        )


# --------------------------------------------------------------------------- #
# APP11-034 — phân phối có giấy phép                                           #
# --------------------------------------------------------------------------- #


def test_may_bundle_binary_requires_explicit_permission() -> None:
    assert may_bundle_binary("") is False
    assert may_bundle_binary("proprietary") is False
    assert may_bundle_binary("eula-view-only") is False
    assert may_bundle_binary("MPL-2.0") is True
    assert may_bundle_binary("GPL-3.0") is True


def test_binary_bundled_without_permission_blocks_shippability() -> None:
    m = _native(license="proprietary", binary_bundled=True)
    assert is_shippable(m) is False
    assert EssentialsErrorCode.E_APP11_BUNDLE_WITHOUT_PERMISSION.value in validate_manifest(m)


def test_binary_bundled_with_permission_is_allowed() -> None:
    m = _native(license="MPL-2.0", binary_bundled=True)
    assert EssentialsErrorCode.E_APP11_BUNDLE_WITHOUT_PERMISSION.value not in validate_manifest(m)


# --------------------------------------------------------------------------- #
# E11-01/E11-02 — không có trường mẫu thừa/credential ngầm                      #
# --------------------------------------------------------------------------- #


def test_manifest_has_no_credential_field() -> None:
    # APP11-005: "không kèm cookie, token, tài khoản mẫu" — kiểm CẤU TRÚC, không
    # phải quy ước: dataclass không có field nào tên như vậy để lỡ gán vào.
    field_names = {f.name for f in dataclasses.fields(EssentialsManifest)}
    forbidden = {"password", "cookie", "token", "session_token", "auto_login_account"}
    assert field_names.isdisjoint(forbidden)


def test_offline_defaults_false_even_for_installed_native() -> None:
    # APP11-001/007: offline=True chỉ khi khai THẬT — mặc định luôn False.
    m = EssentialsManifest(
        id="x", title="X", publisher="P", category="c", delivery_type=DT.INSTALLED_NATIVE
    )
    assert m.offline is False
