"""Hợp đồng dữ liệu M0 — Phụ lục 10 (N10-001..060).

Lõi honest-core LÀM-ĐƯỢC-TẠI-CHỖ cho chương trình chuyển đổi Windows → NaMiOS
(dữ liệu/logic thuần, KHÔNG cần thiết bị/pilot thật). TÁI DÙNG (import, KHÔNG
fork): ``namios_odc`` (route_matrix, device_cert/``CertState``/``EvidenceKind``),
``namios_pra`` (device_hub, office_route, dotnet_classify, progress, doctor),
``namios_e08`` (install_txn, depgraph, actuator), ``namios_sys``
(data_authority). Nguyên tắc trung thực xuyên suốt (§5 "không suy diễn"):
"mở GUI được" ≠ "dùng được" ≠ "ký/nộp xong"; thiếu bằng chứng → ``unknown``;
một công việc THIẾT YẾU bị chặn → CẢ MÁY blocked dù mọi app khác ready; đổi
hash/version của app → recipe tự ``needs_retest``, KHÔNG kế thừa nhãn xanh.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from namios_odc import CertState
from namios_pra import DeviceFunction, DotnetKind, PrintStage, SignSubmitStage

__all__ = [
    "MIG_SCHEMA_VERSION",
    # N10-017 — tuyến tương thích
    "CompatRoute",
    # N10-031/043 — trạng thái một workflow test
    "WorkflowTestStatus",
    # N10-007 — ứng dụng khảo sát được
    "AppManifest",
    # N10-006/047 — ngoại vi khảo sát được
    "PeripheralKind",
    "DeviceManifest",
    # N10-012/019/026 — recipe tương thích có thể kiểm toán
    "CompatibilityRecipe",
    # N10-031/043 — một phép thử workflow nghiệp vụ
    "WorkflowTest",
    # N10-043 — bằng chứng sau hành động
    "EvidenceRecord",
    # N10-007 — hồ sơ khảo sát một máy
    "MigrationInventory",
    # re-export tiện dùng (TÁI DÙNG, không fork)
    "CertState",
    "DeviceFunction",
    "DotnetKind",
    "PrintStage",
    "SignSubmitStage",
]

MIG_SCHEMA_VERSION = "1"


# --------------------------------------------------------------------------- #
# N10-017 — Compatibility Broker: 6 tuyến đúng theo Phụ lục 10 §1.3           #
# --------------------------------------------------------------------------- #


class CompatRoute(str, Enum):
    """Tuyến tương thích app Windows → NaMiOS (N10-017). ``UNSUPPORTED`` = chưa
    có tuyến đạt — KHÔNG được gán nhãn khác để che giấu."""

    NATIVE = "native"
    WEB = "web"
    WINE = "wine"
    REMOTE_WINDOWS = "remote_windows"
    VENDOR_PORT = "vendor_port"
    UNSUPPORTED = "unsupported"


# --------------------------------------------------------------------------- #
# N10-031/043 — Trạng thái một phép thử workflow nghiệp vụ                    #
# --------------------------------------------------------------------------- #


class WorkflowTestStatus(str, Enum):
    """Trạng thái một workflow test (mẫu JSON §4, N10-031/043). ``NOT_TESTED``
    là mặc định — KHÔNG mặc định ``PASSED``/xong khi thiếu bằng chứng."""

    NOT_TESTED = "not_tested"
    PASSED = "passed"
    PARTIAL = "partial"
    FAILED = "failed"


# --------------------------------------------------------------------------- #
# N10-007 — AppManifest: ứng dụng Windows khảo sát được trên một máy          #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class AppManifest:
    """Một ứng dụng Windows đã khảo sát (N10-007/030). KHÔNG chứa mật khẩu/
    cookie/khóa riêng (gate ở ``assessor.assess_machine``). ``last_used_days_ago``
    CHỈ có ý nghĩa khi ``usage_opt_in=True`` — nếu không opt-in, trường này PHẢI
    là ``None`` (validator ``schema.validate_app_manifest`` chặn, N10-007)."""

    app_id: str
    name: str = "unknown"
    publisher: str = ""
    version: str = "unknown"
    installer_hash: str = ""  # "sha256:..."
    architecture: str = "unknown"
    file_types: frozenset[str] = frozenset()  # đuôi quan sát được, vd "docx" — KHÔNG lưu path
    essential: bool = False  # công việc BẮT BUỘC theo bản đồ công việc (N10-008/009)
    usage_opt_in: bool = False
    last_used_days_ago: int | None = None


# --------------------------------------------------------------------------- #
# N10-006/047 — DeviceManifest: ngoại vi khảo sát được trên một máy           #
# --------------------------------------------------------------------------- #


class PeripheralKind(str, Enum):
    """Loại ngoại vi theo ma trận N10-047. Mỗi loại có chức năng ĐO riêng —
    không suy loại này từ loại khác (vd có NIC không suy có Wi-Fi)."""

    PRINTER = "printer"
    MFP = "mfp"
    SCANNER = "scanner"
    USB_TOKEN = "usb_token"  # noqa: S105 (tên loại ngoại vi, không phải mật khẩu)
    USB_STORAGE = "usb_storage"
    NETWORK_NIC = "network_nic"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    CAMERA = "camera"
    AUDIO = "audio"
    DOCK = "dock"
    PROJECTOR = "projector"
    UPS = "ups"
    OTHER = "other"


@dataclass(frozen=True)
class DeviceManifest:
    """Một ngoại vi đã khảo sát (N10-006/047). ``claimed_functions`` = chức
    năng NGƯỜI DÙNG/khảo sát KHAI (chưa kiểm) — tái dùng
    ``namios_pra.DeviceFunction``; "nhận thiết bị" ≠ "chức năng dùng được"
    (kiểm thật thuộc ``namios_pra.device_hub``, ngoài phạm vi khảo sát)."""

    device_id: str
    kind: PeripheralKind = PeripheralKind.OTHER
    model: str = "unknown"
    vendor: str = "unknown"
    firmware: str = "unknown"
    connection: str = "unknown"  # usb/network/bluetooth/serial
    claimed_functions: frozenset[DeviceFunction] = frozenset()


# --------------------------------------------------------------------------- #
# N10-012/019/026 — CompatibilityRecipe: recipe tương thích có thể kiểm toán  #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CompatibilityRecipe:
    """Recipe tương thích CÓ THỂ KIỂM TOÁN (N10-026). ``cert_state`` TÁI DÙNG
    state machine ``namios_odc.CertState`` (reported→lab_tested→
    pilot_verified→published, + needs_retest) — không dựng lại máy trạng thái
    thứ hai. Đổi ``installer_hash``/``version`` của app → PHẢI qua
    ``schema.recipe_needs_retest`` để hạ ``cert_state`` (N10-026), không được
    tự giữ nhãn cũ."""

    app_id: str
    version: str
    installer_hash: str = ""
    route: CompatRoute = CompatRoute.UNSUPPORTED
    runner_id: str = ""  # Wine runner được PIN (N10-019) — bắt buộc nếu route=WINE
    env: Mapping[str, str] = field(default_factory=dict)
    permissions: tuple[str, ...] = ()
    test_case_ids: tuple[str, ...] = ()
    limitations_vi: tuple[str, ...] = ()
    update_hold: bool = False
    rollback_to: str = ""
    owner: str = ""
    cert_state: CertState = CertState.REPORTED
    certified_at: str = ""


# --------------------------------------------------------------------------- #
# N10-031/043 — WorkflowTest: một phép thử workflow nghiệp vụ                 #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class WorkflowTest:
    """Một workflow test — ánh xạ 1-1 mẫu JSON §4 phụ lục 10. ``status=PASSED``
    BẮT BUỘC có ``evidence_ids`` không rỗng + ``tested_at`` (validator chặn,
    N10-043) — "đã xong" không chỉ dựa vào exit-code/launch."""

    workflow_id: str
    app_id: str
    app_version: str = "unknown"
    app_hash: str = ""
    route: CompatRoute = CompatRoute.UNSUPPORTED
    environment: Mapping[str, str] = field(default_factory=dict)
    steps: tuple[str, ...] = ()
    status: WorkflowTestStatus = WorkflowTestStatus.NOT_TESTED
    evidence_ids: tuple[str, ...] = ()
    limitations_vi: tuple[str, ...] = ()
    tested_at: str | None = None


# --------------------------------------------------------------------------- #
# N10-043 — EvidenceRecord: bằng chứng sau hành động                         #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EvidenceRecord:
    """Một bằng chứng sau-hành-động cho một ``WorkflowTest`` (N10-043). TÁI
    DÙNG mốc trung thực ``namios_pra.progress`` (``PrintStage``/
    ``SignSubmitStage``) cho tiến trình in/ký — CUPS "completed"/exit-code chỉ
    là ``MACHINE_DONE``, KHÔNG phải bằng chứng đủ. ``independent_check_ok``
    là bằng chứng ĐỘC LẬP ngoài pipeline kỹ thuật (người xem bản in, hash file
    khớp, biên nhận cổng, QA xác nhận nghiệp vụ); ``None`` = chưa kiểm,
    ``False`` = đã kiểm và THẤT BẠI (vd giấy trắng) — khác hẳn "chưa kiểm"."""

    evidence_id: str
    workflow_id: str
    print_stage: PrintStage | None = None
    sign_stage: SignSubmitStage | None = None
    independent_check_ok: bool | None = None
    detail_vi: str = ""


# --------------------------------------------------------------------------- #
# N10-007 — MigrationInventory: hồ sơ khảo sát một máy (chỉ inventory/preview)#
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class MigrationInventory:
    """Hồ sơ khảo sát MỘT máy Windows (N10-007), CHỈ kiểm kê/preview — không
    cài/chạy/sửa gì. ``machine_id`` NÊN là bút danh (pseudonymous).
    ``redacted_fields`` ghi lại các trường đã BỊ LOẠI vì nhạy cảm/thiếu opt-in
    (``assessor.assess_machine`` điền) — rỗng không có nghĩa là "chắc chắn
    sạch", chỉ là "không phát hiện" (fail-closed ở tầng assessor)."""

    machine_id: str
    os_build: str = "unknown"
    opt_in_usage: bool = False
    apps: tuple[AppManifest, ...] = ()
    devices: tuple[DeviceManifest, ...] = ()
    redacted_fields: tuple[str, ...] = ()
    generated_at: str = ""
