"""Mã lỗi ổn định cho ``namios_essentials`` (Phụ lục 11, APP11-001..036)."""

from __future__ import annotations

from enum import Enum

__all__ = ["EssentialsErrorCode"]


class EssentialsErrorCode(str, Enum):
    """Mã lỗi machine-readable (APP11). Trường dữ liệu, giữ nguyên qua i18n."""

    #: Manifest thiếu nguồn (package_source hợp lệ / official_url) — APP11-002.
    E_APP11_MANIFEST_NO_SOURCE = "E_APP11_MANIFEST_NO_SOURCE"
    #: Manifest thiếu license (bắt buộc cho installed_native/wine_optional) — APP11-002/034.
    E_APP11_MANIFEST_NO_LICENSE = "E_APP11_MANIFEST_NO_LICENSE"
    #: Thiếu owner hoặc last_verified (test date) — APP11-002/036 §5.
    E_APP11_MANIFEST_NO_OWNER_OR_TESTDATE = "E_APP11_MANIFEST_NO_OWNER_OR_TESTDATE"
    #: binary_bundled=True nhưng license không cho phép phân phối lại — APP11-034.
    E_APP11_BUNDLE_WITHOUT_PERMISSION = "E_APP11_BUNDLE_WITHOUT_PERMISSION"
    #: Nhãn web shortcut hiển thị sai kiểu "đã cài"/"bản Linux" — APP11-001/036.
    E_APP11_LABEL_MISLEADING = "E_APP11_LABEL_MISLEADING"
    #: Tên miền không nằm trong allowlist chính thức — APP11-003.
    E_APP11_DOMAIN_NOT_ALLOWLISTED = "E_APP11_DOMAIN_NOT_ALLOWLISTED"
    #: Tên miền nghi mạo danh (chứa thương hiệu nhưng không allowlisted) — APP11-003/033.
    E_APP11_DOMAIN_IMPERSONATION_SUSPECTED = "E_APP11_DOMAIN_IMPERSONATION_SUSPECTED"
    #: Ring giữ bản cũ nhưng thiếu hạn (retention_deadline rỗng) — APP11-017.
    E_APP11_RING_RETENTION_NO_DEADLINE = "E_APP11_RING_RETENTION_NO_DEADLINE"
    #: Cổng phát hành P0 chưa đạt (IME/Office/browser/Security Center/rollback) — APP11-036.
    E_APP11_RELEASE_GATE_BLOCKED = "E_APP11_RELEASE_GATE_BLOCKED"
