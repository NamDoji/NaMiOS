"""Brand/About (OWN-001/OWN-002) — struct/kiểu chỉ dữ liệu, KHÔNG business
logic. Màn About (UI) là M3, chỉ tiêu thụ kiểu này. Xem M1-INTERFACES.md §1b.

Ràng buộc (FACT §26): ``AboutInfo`` KHÔNG được dùng để tuyên bố NaMiOS sở hữu
Debian/Linux/KDE/Wine — chỉ phần tự viết. ``legal_entity`` và trạng thái
trademark/domain giữ UNKNOWN cho tới khi chủ dự án xác lập. WP1 chỉ cung cấp
kiểu + mặc định an toàn (brand + 2 founders); KHÔNG tự điền pháp nhân/nhãn hiệu.
"""

from __future__ import annotations

from dataclasses import dataclass

from namios_core.paths import APP_NAME

#: Brand hiển thị (OWN-001). ``APP_NAME`` (namespace/CLI/path) vẫn là
#: ``namios_core.paths.APP_NAME`` — nguồn duy nhất, re-export ở đây cho tiện.
PRODUCT_NAME = "NaMi"

#: Hai nhà sáng lập/chủ dự án (FACT §26).
FOUNDERS: tuple[str, ...] = ("Đỗ Chí Cường", "Đỗ Bảo Nam")

__all__ = [
    "APP_NAME",
    "PRODUCT_NAME",
    "FOUNDERS",
    "ComponentLicense",
    "AboutInfo",
]


@dataclass(frozen=True)
class ComponentLicense:
    """Giấy phép của một thành phần (vd Debian, KDE Plasma, Wine, phần tự
    viết NaMiOS) + nguồn mở tương ứng."""

    component: str
    license: str
    source_url: str | None


@dataclass(frozen=True)
class AboutInfo:
    """Nội dung màn About (OWN-002)."""

    product_name: str
    version: str
    founders: tuple[str, ...]
    legal_entity: str | None
    licenses: tuple[ComponentLicense, ...]
    source_urls: tuple[str, ...]
    support_contact: str | None
