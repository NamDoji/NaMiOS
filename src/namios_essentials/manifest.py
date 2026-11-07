"""Manifest NaMiOS Essentials có nguồn (APP11-002) + giấy phép phân phối (APP11-034).

TÁI DÙNG ``namios_e08.provenance_ok`` cho nguồn gói native (hash + chữ ký +
official) — KHÔNG dựng lại cơ chế provenance thứ hai (APP11-014). Bất biến
fail-closed (APP11-002 nghiệm thu: "mục thiếu nguồn hoặc quyền dùng không xuất
hiện ở ảnh cài chính thức"): manifest thiếu NGUỒN (``package_source`` hợp lệ cho
``installed_native`` / ``official_url`` cho web+wine) HOẶC thiếu license HOẶC
thiếu owner/ngày kiểm → ``is_shippable=False``. ``binary_bundled=True`` chỉ hợp
lệ khi license cho phép tường minh (APP11-034) — license rỗng/độc quyền mặc
định KHÔNG cho bundle.
"""

from __future__ import annotations

from namios_e08 import provenance_ok
from namios_essentials import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_essentials._errors import EssentialsErrorCode
from namios_essentials._types import DeliveryType, EssentialsManifest

__all__ = ["validate_manifest", "is_shippable", "may_bundle_binary"]

#: ALLOWLIST giấy phép ĐƯỢC PHÉP bundle lại nhị phân kèm ISO (SPDX id chuẩn hoá,
#: APP11-034). FAIL-CLOSED: license KHÔNG nằm trong đây — rỗng, độc quyền, EULA
#: xem-thôi, HOẶC chuỗi lạ/không rõ ("unknown", "all-rights-reserved", EULA
#: riêng…) — đều KHÔNG được bundle. KHÔNG đoán quyền từ license tự do (trước đây
#: dùng denylist → license lạ lọt thành "cho bundle"; đó là lỗ hổng fail-open).
_REDISTRIBUTABLE_LICENSES: frozenset[str] = frozenset(
    {
        "mit",
        "x11",
        "isc",
        "0bsd",
        "zlib",
        "bsl-1.0",
        "ncsa",
        "bsd-2-clause",
        "bsd-3-clause",
        "apache-2.0",
        "mpl-1.1",
        "mpl-2.0",
        "lgpl-2.1",
        "lgpl-2.1-only",
        "lgpl-2.1-or-later",
        "lgpl-3.0",
        "lgpl-3.0-only",
        "lgpl-3.0-or-later",
        "gpl-2.0",
        "gpl-2.0-only",
        "gpl-2.0-or-later",
        "gpl-3.0",
        "gpl-3.0-only",
        "gpl-3.0-or-later",
        "agpl-3.0",
        "agpl-3.0-only",
        "agpl-3.0-or-later",
        "epl-2.0",
        "artistic-2.0",
        "ofl-1.1",
        "cc0-1.0",
        "cc-by-4.0",
        "cc-by-sa-4.0",
        "unlicense",
        "public-domain",
    }
)


def _has_valid_source(m: EssentialsManifest) -> bool:
    """Nguồn có hợp lệ theo ĐÚNG hình thức tích hợp không (APP11-002/014)."""

    if m.delivery_type is DeliveryType.INSTALLED_NATIVE:
        return m.package_source is not None and provenance_ok(m.package_source)
    # official_web / wine_optional: cần URL chính thức khai rõ, không rỗng.
    return bool(m.official_url.strip())


def may_bundle_binary(license_text: str) -> bool:
    """APP11-034: chỉ bundle binary bên thứ ba khi license CHO PHÉP tường minh —
    rỗng/proprietary/eula-view-only mặc định KHÔNG (fail-closed, không đoán quyền)."""

    return license_text.strip().lower() in _REDISTRIBUTABLE_LICENSES


def validate_manifest(m: EssentialsManifest) -> tuple[str, ...]:
    """Trả danh sách mã lỗi vi phạm (rỗng = hợp lệ để xuất ở ảnh cài chính thức).
    KHÔNG raise — caller (``release_gate``) quyết định chặn dòng nào."""

    violations: list[str] = []

    if not _has_valid_source(m):
        violations.append(EssentialsErrorCode.E_APP11_MANIFEST_NO_SOURCE.value)

    # Web shortcut dùng license của chính dịch vụ vendor — NaMiOS không "cấp"
    # license cho dịch vụ bên ngoài, nên không bắt khai license ở đây; native/
    # wine package (có cài đặt binary thật) PHẢI khai license rõ ràng.
    if m.delivery_type is not DeliveryType.OFFICIAL_WEB and not m.license.strip():
        violations.append(EssentialsErrorCode.E_APP11_MANIFEST_NO_LICENSE.value)

    if m.binary_bundled and not may_bundle_binary(m.license):
        violations.append(EssentialsErrorCode.E_APP11_BUNDLE_WITHOUT_PERMISSION.value)

    # §5: "Mọi app phải có owner, nguồn và test date".
    if not m.owner.strip() or not (m.last_verified or "").strip():
        violations.append(EssentialsErrorCode.E_APP11_MANIFEST_NO_OWNER_OR_TESTDATE.value)

    return tuple(violations)


def is_shippable(m: EssentialsManifest) -> bool:
    """APP11-002: thiếu nguồn hoặc license (hoặc owner/test date) → ``False``."""

    return len(validate_manifest(m)) == 0
