"""NaMi Migration Assessor (N10-007) — chỉ kiểm kê/preview, KHÔNG cài/sửa/chạy.

Nhận dữ liệu khảo sát THÔ (form nhập tay hoặc công cụ chạy trên Windows theo
quyền được cấp) → dựng ``MigrationInventory`` bằng cách đọc WHITELIST trường đã
khai trong ``AppManifest``/``DeviceManifest`` — trường lạ (kể cả mật khẩu/
cookie/khóa riêng) KHÔNG BAO GIỜ được copy vào dataclass, chỉ được ĐÁNH DẤU
trong ``rejected_fields`` để người review biết công cụ thu thập thô đã cố gửi
gì. ``last_used_days_ago`` (sử dụng 30 ngày) CHỈ giữ khi ``opt_in_usage=True``
ở cấp máy — thiếu opt-in thì bị loại dù input có khai (N10-007).

TÁI DÙNG ``namios_sys.data_authority`` (N10-007/014 + §5): nội dung thu thập
được (tên bookmark, ghi chú, tên file…) là DỮ LIỆU không tin cậy — chỉ-dẫn
nằm trong đó KHÔNG BAO GIỜ tự trở thành hành động của assessor.

TÁI DÙNG ``namios_e08.install_txn`` cho N10-012 (chuyển dữ liệu ứng dụng có
giao dịch): export/import/đối-chiếu app data được mô hình hoá lại đúng state
machine check-source→snapshot→apply→function-test→commit/rollback — không
dựng một state machine giao dịch thứ hai.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from namios_core.validation import ValidationError
from namios_e08 import InstallResult
from namios_e08.install_txn import run_install_transaction
from namios_mig import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_mig._types import AppManifest, DeviceManifest, MigrationInventory, PeripheralKind
from namios_mig.schema import validate_inventory
from namios_sys import SourceTrust
from namios_sys.data_authority import authorize

__all__ = [
    "SECRET_FIELD_MARKERS",
    "AssessmentResult",
    "assess_machine",
    "assessment_instruction_authorized",
    "migrate_app_data",
]

#: Tên trường bị coi là nhạy cảm (N10-007 "Không thu mật khẩu/cookie/khóa
#: riêng") — so khớp theo SUBSTRING đã chuẩn hoá (lower, bỏ ``_``/``-``).
#: Cố ý fail-closed/rộng: thà loại nhầm một trường vô hại còn hơn lọt bí mật.
SECRET_FIELD_MARKERS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "pwd",
        "cookie",
        "session",
        "secret",
        "privatekey",
        "apikey",
        "credential",
        "pin",
    }
)

#: Trường ĐƯỢC PHÉP đọc vào ``AppManifest`` — whitelist, không copy trường lạ.
_APP_ALLOWED_KEYS: frozenset[str] = frozenset(
    {
        "app_id",
        "name",
        "publisher",
        "version",
        "installer_hash",
        "architecture",
        "file_types",
        "essential",
        "last_used_days_ago",
    }
)

#: Trường ĐƯỢC PHÉP đọc vào ``DeviceManifest`` — whitelist.
_DEVICE_ALLOWED_KEYS: frozenset[str] = frozenset(
    {"device_id", "kind", "model", "vendor", "firmware", "connection"}
)


def _normalize(name: str) -> str:
    return name.strip().lower().replace("_", "").replace("-", "")


def _is_secret_field(name: str) -> bool:
    norm = _normalize(name)
    return any(marker in norm for marker in SECRET_FIELD_MARKERS)


def _scan_secret_paths(value: Any, prefix: str, out: list[str]) -> None:
    """Quét đệ quy TOÀN BỘ cấu trúc thô tìm tên trường nhạy cảm — kể cả nằm
    sâu trong app/device con — để ``rejected_fields`` phản ánh đúng những gì
    input THỬ gửi lên, không chỉ top-level."""

    if isinstance(value, Mapping):
        for key, val in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if _is_secret_field(str(key)):
                out.append(path)
            _scan_secret_paths(val, path, out)
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            _scan_secret_paths(item, f"{prefix}[{i}]", out)


def _str_frozenset(value: Any) -> frozenset[str]:
    if isinstance(value, (list, tuple, set, frozenset)):
        return frozenset(str(v) for v in value)
    return frozenset()


def _build_app(
    raw: Mapping[str, Any], *, index: int, opt_in: bool, rejected: list[str]
) -> AppManifest:
    last_used_raw = raw.get("last_used_days_ago")
    last_used: int | None = None
    if last_used_raw is not None:
        if opt_in:
            try:
                last_used = int(last_used_raw)
            except (TypeError, ValueError):
                last_used = None
        else:
            rejected.append(f"apps[{index}].last_used_days_ago (no opt-in)")
    return AppManifest(
        app_id=str(raw.get("app_id", "")),
        name=str(raw.get("name", "unknown")),
        publisher=str(raw.get("publisher", "")),
        version=str(raw.get("version", "unknown")),
        installer_hash=str(raw.get("installer_hash", "")),
        architecture=str(raw.get("architecture", "unknown")),
        file_types=_str_frozenset(raw.get("file_types")),
        essential=bool(raw.get("essential", False)),
        usage_opt_in=opt_in,
        last_used_days_ago=last_used,
    )


def _enum_or_default(value: Any, enum_cls: type, default: Any) -> Any:
    try:
        return enum_cls(str(value))
    except ValueError:
        return default


def _build_device(raw: Mapping[str, Any]) -> DeviceManifest:
    return DeviceManifest(
        device_id=str(raw.get("device_id", "")),
        kind=_enum_or_default(raw.get("kind", "other"), PeripheralKind, PeripheralKind.OTHER),
        model=str(raw.get("model", "unknown")),
        vendor=str(raw.get("vendor", "unknown")),
        firmware=str(raw.get("firmware", "unknown")),
        connection=str(raw.get("connection", "unknown")),
    )


@dataclass(frozen=True)
class AssessmentResult:
    """Kết quả chạy assessor trên MỘT máy (N10-007). ``rejected_fields`` =
    đường dẫn các trường ĐÃ BỊ LOẠI (nhạy cảm hoặc thiếu opt-in) — KHÔNG trường
    nào trong đó từng được copy vào ``inventory``. ``errors`` = lỗi cấu trúc
    còn lại sau khi dựng inventory (vd thiếu ``app_id``)."""

    inventory: MigrationInventory
    rejected_fields: tuple[str, ...]
    errors: tuple[ValidationError, ...]

    @property
    def has_rejected_secrets(self) -> bool:
        return any("no opt-in" not in f for f in self.rejected_fields)


def assess_machine(raw: Mapping[str, Any]) -> AssessmentResult:
    """Dựng ``MigrationInventory`` từ dữ liệu khảo sát THÔ (N10-007).

    CHỈ đọc/biến đổi dữ liệu (kiểm kê/preview) — không mở kết nối, không cài,
    không sửa máy nguồn. Mọi trường KHÔNG nằm trong whitelist của
    ``AppManifest``/``DeviceManifest`` bị bỏ qua khi dựng dữ liệu; trường có
    TÊN nhạy cảm (mật khẩu/cookie/khóa riêng…) ở BẤT KỲ độ sâu nào trong input
    được ghi nhận vào ``rejected_fields`` để review, dù whitelist vốn đã không
    đọc chúng — phòng trường hợp whitelist tương lai mở rộng vô ý."""

    rejected: list[str] = []
    _scan_secret_paths(raw, "", rejected)

    opt_in = bool(raw.get("opt_in_usage", False))

    apps_raw = raw.get("apps", ())
    apps: list[AppManifest] = []
    if isinstance(apps_raw, Sequence) and not isinstance(apps_raw, (str, bytes)):
        for i, app_raw in enumerate(apps_raw):
            if isinstance(app_raw, Mapping):
                apps.append(_build_app(app_raw, index=i, opt_in=opt_in, rejected=rejected))

    devices_raw = raw.get("devices", ())
    devices: list[DeviceManifest] = []
    if isinstance(devices_raw, Sequence) and not isinstance(devices_raw, (str, bytes)):
        for dev_raw in devices_raw:
            if isinstance(dev_raw, Mapping):
                devices.append(_build_device(dev_raw))

    inventory = MigrationInventory(
        machine_id=str(raw.get("machine_id", "")),
        os_build=str(raw.get("os_build", "unknown")),
        opt_in_usage=opt_in,
        apps=tuple(apps),
        devices=tuple(devices),
        redacted_fields=tuple(sorted(set(rejected))),
        generated_at=str(raw.get("generated_at", "")),
    )
    errors = tuple(validate_inventory(inventory))
    return AssessmentResult(
        inventory=inventory, rejected_fields=inventory.redacted_fields, errors=errors
    )


def assessment_instruction_authorized(action: str, *, content: str) -> bool:
    """Chỉ-dẫn nằm trong dữ liệu THU THẬP được (tên bookmark/ghi chú/tên file
    trên máy Windows) có thành hành động của assessor không (N10-007/014).

    TÁI DÙNG ``namios_sys.data_authority.authorize`` — LUÔN ``False``: dữ liệu
    khảo sát được coi là ``SourceTrust.DOCUMENT`` (không tin cậy), bất kể nội
    dung trông có vẻ là lệnh hợp lý thế nào ("xóa backup", "tắt firewall")."""

    return authorize(
        action, source=SourceTrust.DOCUMENT, org_policy_allows=True, content=content
    ).allowed


def migrate_app_data(
    *, source_ok: bool, snapshot_ok: bool, apply_ok: bool, reconciliation_ok: bool
) -> InstallResult:
    """Chuyển dữ liệu một ứng dụng CÓ GIAO DỊCH (N10-012). TÁI DÙNG
    ``namios_e08.install_txn.run_install_transaction`` — cùng state machine
    check-nguồn→snapshot→apply→kiểm→commit/rollback, ở đây ``reconciliation_ok``
    đóng vai "kiểm chức năng sau cài" = đối chiếu tổng tiền/số chứng từ/
    attachments trên dữ liệu giả (N10-012 nghiệm thu); sai một khoản → rollback,
    KHÔNG để nửa vời."""

    return run_install_transaction(
        source_ok=source_ok,
        snapshot_ok=snapshot_ok,
        apply_ok=apply_ok,
        function_ok=reconciliation_ok,
    )
