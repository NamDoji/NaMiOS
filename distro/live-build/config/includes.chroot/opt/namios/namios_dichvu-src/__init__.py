"""``namios_dichvu`` — Cổng Dịch vụ Việt + Trung tâm Ký số (VN-2/VN-3,
``docs/roadmap/NEW-FUNCTIONS-DIRECTION.md``). Một launcher trung thực dẫn
người dùng Việt (kế toán/người dân) tới đúng cổng thuế/BHXH/dịch vụ công/
hoá đơn điện tử/ngân hàng, kèm khu vực ký số ưu tiên ký-số-từ-xa.

``catalog``/``envcheck`` là Python thuần (dataclass + ``shutil``/``json``),
test được không cần PySide6/display (cùng quy ước ``namios_assistant.engine``/
``namios_lich.lunar``). ``ui`` (PySide6) + ``__main__`` CHỈ chạy trên desktop
session thật.

Module này KHÔNG import ``namios_essentials``/``namios_eco`` (hai gói đó
CHƯA được đóng gói vào ``/opt/namios`` của ảnh ở thời điểm viết wave này —
xem docstring ``catalog.py``) — tự chứa (self-contained) theo đúng phạm vi
được giao, chỉ dựa vào ``namios_core``/``namios_i18n`` (đã có sẵn trong ảnh,
cùng namios_assistant/namios_antoan đang dùng)."""

from __future__ import annotations

from namios_dichvu import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_dichvu.catalog import (
    AppOption,
    Category,
    ServiceCatalog,
    ServiceEntry,
    fold_vi,
    filter_services,
    load_catalog,
    services_in_category,
)
from namios_dichvu.envcheck import (
    EnvCheckReport,
    Pkcs11ProbeResult,
    probe_pkcs11_slots,
    run_env_check,
)

__all__ = [
    "AppOption",
    "Category",
    "ServiceCatalog",
    "ServiceEntry",
    "fold_vi",
    "filter_services",
    "load_catalog",
    "services_in_category",
    "EnvCheckReport",
    "Pkcs11ProbeResult",
    "probe_pkcs11_slots",
    "run_env_check",
]
