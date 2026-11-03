"""Workflow Pack theo ngành (COMP-031, Phụ lục 03): gói metadata + test plan
MẪU (dữ liệu giả) cho sáu nhóm ngành (``Sector``) — thuế, kế toán, BHXH,
giáo dục, hành chính công, ngành dọc.

Một pack KHÔNG BAO GIỜ chứa đăng nhập/cookie/PIN/secret, KHÔNG chứa khóa điều
khiển thực thi (command/argv/script…), và LUÔN giữ đúng 7 nấc ECO-001 theo
thứ tự chuẩn. ``provider_id``/``gateway`` ghi ``unresolved``/``unknown`` khi
chưa khảo sát thật — KHÔNG tự nhận một app thật là "tương thích".

``validate_pack_raw`` thẩm định một dict thô (như vừa load từ JSON) — tái
dùng ``namios_eco.validator.validate_no_executable_keys`` làm lớp chặn khóa
thực thi DUY NHẤT (không định nghĩa lại tập khóa cấm), rồi bổ sung quét
secret + quét cấu trúc 7 nấc riêng của COMP-031.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from namios_compat import _i18n as _i18n  # noqa: F401
from namios_compat._errors import CompatErrorCode
from namios_compat._types import Sector, WorkflowPack, WorkflowPackStep
from namios_core.validation import ValidationError
from namios_eco.validator import FORBIDDEN_EXECUTABLE_KEYS, validate_no_executable_keys
from namios_eco.workflow import WORKFLOW_STEP_ORDER, WorkflowStepName
from namios_i18n import Lang, t

__all__ = [
    "SAMPLE_PACKS",
    "load_sample_packs",
    "pack_to_dict",
    "validate_pack_raw",
]

#: Hai nấc LUÔN dừng trước giao dịch/ký/nộp thật trong mọi pack mẫu (COMP-031
#: "điểm dừng trước giao dịch thật"): đăng nhập thật và nộp/ký/xuất thật.
_STOP_BEFORE_REAL_TRANSACTION_STEPS: frozenset[WorkflowStepName] = frozenset(
    {WorkflowStepName.AUTHENTICATE, WorkflowStepName.SUBMIT_OR_EXPORT}
)

#: Các chuỗi con (viết thường) nhận diện KHÓA mang secret — quét key bất kỳ
#: cấp lồng nào, không phân biệt hoa/thường (COMP-031: pack không bao giờ
#: mang đăng nhập/cookie/PIN/secret).
_SECRET_KEY_SUBSTRINGS: tuple[str, ...] = (
    "password",
    "passwd",
    "pwd",
    "pin",
    "cookie",
    "token",
    "secret",
    "credential",
    "otp",
    "session_id",
    "apikey",
    "api_key",
    "private_key",
)


def _build_steps(
    *,
    role: str,
    artifacts: Mapping[WorkflowStepName, str],
    inputs: Mapping[WorkflowStepName, tuple[str, ...]],
) -> tuple[WorkflowPackStep, ...]:
    """Dựng đúng 7 ``WorkflowPackStep`` theo ``WORKFLOW_STEP_ORDER`` — nguồn
    DUY NHẤT quyết định thứ tự, không lặp lại danh sách tên nấc ở nơi gọi."""

    return tuple(
        WorkflowPackStep(
            name=name,
            role=role,
            expected_artifact=artifacts[name],
            inputs=inputs.get(name, ()),
            stop_before_real_transaction=name in _STOP_BEFORE_REAL_TRANSACTION_STEPS,
        )
        for name in WORKFLOW_STEP_ORDER
    )


_TAX_PACK = WorkflowPack(
    pack_version="1.0",
    sector=Sector.TAX,
    workflow_id="vn.tax.sample_declaration",
    title_vi="Gói mẫu nộp tờ khai thuế điện tử (demo, dữ liệu giả — chưa khảo sát cổng thật).",
    provider_id="unresolved",
    gateway="unknown",
    steps=_build_steps(
        role="kế toán viên",
        artifacts={
            WorkflowStepName.DISCOVER: "danh sách cổng thuế điện tử khả dụng (giả)",
            WorkflowStepName.ACQUIRE: "địa chỉ portal/phần mềm thuế đã xác định (giả)",
            WorkflowStepName.INSTALL_OR_OPEN: "trang nộp tờ khai đã mở (giả)",
            WorkflowStepName.AUTHENTICATE: "phiên demo đã mở — KHÔNG đăng nhập cổng thật",
            WorkflowStepName.EXECUTE: "tờ khai đã điền dữ liệu giả",
            WorkflowStepName.SUBMIT_OR_EXPORT: "tờ khai PDF (giả) — DỪNG trước khi nộp thật",
            WorkflowStepName.VERIFY_RESULT: "biên nhận nộp tờ khai (giả)",
        },
        inputs={
            WorkflowStepName.DISCOVER: ("tên đơn vị giả",),
            WorkflowStepName.ACQUIRE: ("mã số thuế giả",),
            WorkflowStepName.INSTALL_OR_OPEN: ("URL cổng thuế giả",),
            WorkflowStepName.AUTHENTICATE: ("chứng từ giả",),
            WorkflowStepName.EXECUTE: ("số liệu kế toán giả",),
            WorkflowStepName.SUBMIT_OR_EXPORT: ("tờ khai PDF giả",),
            WorkflowStepName.VERIFY_RESULT: ("mã biên nhận giả",),
        },
    ),
    devices=("printer-mock-tax-01", "signing-token-mock-tax-01"),
    notes_vi=(
        "Pack mẫu COMP-031, dữ liệu giả toàn bộ. provider_id/gateway chưa khảo sát "
        "thật → ghi 'unresolved'/'unknown', KHÔNG kết luận app nào tương thích."
    ),
)

_ACCOUNTING_PACK = WorkflowPack(
    pack_version="1.0",
    sector=Sector.ACCOUNTING,
    workflow_id="vn.accounting.sample_ledger_export",
    title_vi="Gói mẫu xuất sổ cái kế toán (demo, dữ liệu giả — chưa khảo sát phần mềm thật).",
    provider_id="unresolved",
    gateway="unknown",
    steps=_build_steps(
        role="kế toán",
        artifacts={
            WorkflowStepName.DISCOVER: "danh sách phần mềm kế toán khả dụng (giả)",
            WorkflowStepName.ACQUIRE: "phần mềm kế toán đã xác định (giả)",
            WorkflowStepName.INSTALL_OR_OPEN: "phần mềm/portal kế toán đã mở (giả)",
            WorkflowStepName.AUTHENTICATE: "phiên demo đã mở — KHÔNG đăng nhập hệ thống thật",
            WorkflowStepName.EXECUTE: "bảng kê bút toán đã lập (giả)",
            WorkflowStepName.SUBMIT_OR_EXPORT: "sổ cái PDF/Excel (giả) — DỪNG trước khi xuất thật",
            WorkflowStepName.VERIFY_RESULT: "đối chiếu số dư sổ cái (giả)",
        },
        inputs={
            WorkflowStepName.DISCOVER: ("tên đơn vị giả",),
            WorkflowStepName.ACQUIRE: ("mã khách hàng giả",),
            WorkflowStepName.INSTALL_OR_OPEN: ("đường dẫn phần mềm giả",),
            WorkflowStepName.AUTHENTICATE: ("chứng từ giả",),
            WorkflowStepName.EXECUTE: ("chứng từ kế toán giả",),
            WorkflowStepName.SUBMIT_OR_EXPORT: ("kỳ kế toán giả",),
            WorkflowStepName.VERIFY_RESULT: ("số dư đối chiếu giả",),
        },
    ),
    devices=("printer-mock-acct-01",),
    notes_vi=(
        "Pack mẫu COMP-031, dữ liệu giả toàn bộ. provider_id/gateway chưa khảo sát "
        "thật → ghi 'unresolved'/'unknown'."
    ),
)

_SOCIAL_INSURANCE_PACK = WorkflowPack(
    pack_version="1.0",
    sector=Sector.SOCIAL_INSURANCE,
    workflow_id="vn.social_insurance.sample_declaration",
    title_vi="Gói mẫu khai báo BHXH điện tử (demo, dữ liệu giả — chưa khảo sát cổng thật).",
    provider_id="unresolved",
    gateway="unknown",
    steps=_build_steps(
        role="cán bộ nhân sự",
        artifacts={
            WorkflowStepName.DISCOVER: "danh sách cổng BHXH điện tử khả dụng (giả)",
            WorkflowStepName.ACQUIRE: "phần mềm/portal BHXH đã xác định (giả)",
            WorkflowStepName.INSTALL_OR_OPEN: "trang khai báo BHXH đã mở (giả)",
            WorkflowStepName.AUTHENTICATE: "phiên demo đã mở — KHÔNG đăng nhập cổng thật",
            WorkflowStepName.EXECUTE: "hồ sơ khai báo lao động đã điền (giả)",
            WorkflowStepName.SUBMIT_OR_EXPORT: "hồ sơ khai báo (giả) — DỪNG trước khi nộp thật",
            WorkflowStepName.VERIFY_RESULT: "biên nhận khai báo BHXH (giả)",
        },
        inputs={
            WorkflowStepName.DISCOVER: ("mã đơn vị BHXH giả",),
            WorkflowStepName.ACQUIRE: ("mã số đơn vị giả",),
            WorkflowStepName.INSTALL_OR_OPEN: ("URL cổng BHXH giả",),
            WorkflowStepName.AUTHENTICATE: ("chứng từ giả",),
            WorkflowStepName.EXECUTE: ("danh sách lao động giả",),
            WorkflowStepName.SUBMIT_OR_EXPORT: ("hồ sơ khai báo giả",),
            WorkflowStepName.VERIFY_RESULT: ("mã biên nhận BHXH giả",),
        },
    ),
    devices=("signing-token-mock-si-01",),
    notes_vi=(
        "Pack mẫu COMP-031, dữ liệu giả toàn bộ. provider_id/gateway chưa khảo sát "
        "thật → ghi 'unresolved'/'unknown'."
    ),
)

_EDUCATION_PACK = WorkflowPack(
    pack_version="1.0",
    sector=Sector.EDUCATION,
    workflow_id="vn.education.sample_enrollment",
    title_vi="Gói mẫu nhập liệu điểm/hồ sơ học sinh trực tuyến (demo, dữ liệu giả).",
    provider_id="unresolved",
    gateway="unknown",
    steps=_build_steps(
        role="giáo viên",
        artifacts={
            WorkflowStepName.DISCOVER: "danh sách hệ thống quản lý học sinh khả dụng (giả)",
            WorkflowStepName.ACQUIRE: "phần mềm/portal nhà trường đã xác định (giả)",
            WorkflowStepName.INSTALL_OR_OPEN: "trang nhập liệu đã mở (giả)",
            WorkflowStepName.AUTHENTICATE: "phiên demo đã mở — KHÔNG đăng nhập hệ thống thật",
            WorkflowStepName.EXECUTE: "bảng điểm/hồ sơ đã nhập dữ liệu giả",
            WorkflowStepName.SUBMIT_OR_EXPORT: "hồ sơ học sinh (giả) — DỪNG trước khi nộp thật",
            WorkflowStepName.VERIFY_RESULT: "xác nhận lưu hồ sơ học sinh (giả)",
        },
        inputs={
            WorkflowStepName.DISCOVER: ("tên trường giả",),
            WorkflowStepName.ACQUIRE: ("mã trường giả",),
            WorkflowStepName.INSTALL_OR_OPEN: ("URL hệ thống trường giả",),
            WorkflowStepName.AUTHENTICATE: ("chứng từ giả",),
            WorkflowStepName.EXECUTE: ("điểm số giả",),
            WorkflowStepName.SUBMIT_OR_EXPORT: ("hồ sơ học sinh giả",),
            WorkflowStepName.VERIFY_RESULT: ("mã xác nhận lưu giả",),
        },
    ),
    devices=("card-reader-mock-edu-01",),
    notes_vi=(
        "Pack mẫu COMP-031, dữ liệu giả toàn bộ. provider_id/gateway chưa khảo sát "
        "thật → ghi 'unresolved'/'unknown'."
    ),
)

_PUBLIC_ADMIN_PACK = WorkflowPack(
    pack_version="1.0",
    sector=Sector.PUBLIC_ADMIN,
    workflow_id="vn.public_admin.sample_public_service",
    title_vi="Gói mẫu nộp hồ sơ dịch vụ công trực tuyến (demo, dữ liệu giả).",
    provider_id="unresolved",
    gateway="unknown",
    steps=_build_steps(
        role="cán bộ hành chính",
        artifacts={
            WorkflowStepName.DISCOVER: "danh sách cổng dịch vụ công khả dụng (giả)",
            WorkflowStepName.ACQUIRE: "cổng dịch vụ công đã xác định (giả)",
            WorkflowStepName.INSTALL_OR_OPEN: "trang nộp hồ sơ đã mở (giả)",
            WorkflowStepName.AUTHENTICATE: "phiên demo đã mở — KHÔNG đăng nhập cổng thật",
            WorkflowStepName.EXECUTE: "hồ sơ dịch vụ công đã điền dữ liệu giả",
            WorkflowStepName.SUBMIT_OR_EXPORT: "hồ sơ (giả) — DỪNG trước khi nộp thật",
            WorkflowStepName.VERIFY_RESULT: "biên nhận hồ sơ dịch vụ công (giả)",
        },
        inputs={
            WorkflowStepName.DISCOVER: ("tên thủ tục giả",),
            WorkflowStepName.ACQUIRE: ("mã thủ tục giả",),
            WorkflowStepName.INSTALL_OR_OPEN: ("URL cổng dịch vụ công giả",),
            WorkflowStepName.AUTHENTICATE: ("chứng từ giả",),
            WorkflowStepName.EXECUTE: ("hồ sơ đính kèm giả",),
            WorkflowStepName.SUBMIT_OR_EXPORT: ("hồ sơ dịch vụ công giả",),
            WorkflowStepName.VERIFY_RESULT: ("mã biên nhận dịch vụ công giả",),
        },
    ),
    devices=("scanner-mock-pa-01",),
    notes_vi=(
        "Pack mẫu COMP-031, dữ liệu giả toàn bộ. provider_id/gateway chưa khảo sát "
        "thật → ghi 'unresolved'/'unknown'."
    ),
)

_VERTICAL_PACK = WorkflowPack(
    pack_version="1.0",
    sector=Sector.VERTICAL,
    workflow_id="vn.vertical.sample_industry_workflow",
    title_vi=(
        "Gói mẫu quy trình chuyên ngành dọc (demo, dữ liệu giả — ngành chưa định danh cụ thể)."
    ),
    provider_id="unresolved",
    gateway="unknown",
    steps=_build_steps(
        role="nhân viên vận hành",
        artifacts={
            WorkflowStepName.DISCOVER: "danh sách phần mềm chuyên ngành khả dụng (giả)",
            WorkflowStepName.ACQUIRE: "phần mềm chuyên ngành đã xác định (giả)",
            WorkflowStepName.INSTALL_OR_OPEN: "phần mềm/portal chuyên ngành đã mở (giả)",
            WorkflowStepName.AUTHENTICATE: "phiên demo đã mở — KHÔNG đăng nhập hệ thống thật",
            WorkflowStepName.EXECUTE: "tác vụ nghiệp vụ chuyên ngành đã thực hiện (giả)",
            WorkflowStepName.SUBMIT_OR_EXPORT: "kết quả tác vụ (giả) — DỪNG trước khi xuất thật",
            WorkflowStepName.VERIFY_RESULT: "xác nhận kết quả tác vụ chuyên ngành (giả)",
        },
        inputs={
            WorkflowStepName.DISCOVER: ("tên ngành dọc giả",),
            WorkflowStepName.ACQUIRE: ("mã phần mềm chuyên ngành giả",),
            WorkflowStepName.INSTALL_OR_OPEN: ("đường dẫn phần mềm giả",),
            WorkflowStepName.AUTHENTICATE: ("chứng từ giả",),
            WorkflowStepName.EXECUTE: ("dữ liệu nghiệp vụ giả",),
            WorkflowStepName.SUBMIT_OR_EXPORT: ("kết quả tác vụ giả",),
            WorkflowStepName.VERIFY_RESULT: ("mã xác nhận kết quả giả",),
        },
    ),
    devices=("barcode-reader-mock-vert-01",),
    notes_vi=(
        "Pack mẫu COMP-031, dữ liệu giả toàn bộ. provider_id/gateway chưa khảo sát "
        "thật → ghi 'unresolved'/'unknown'; ngành dọc cụ thể chưa định danh."
    ),
)

#: Sáu pack mẫu, MỖI ``Sector`` đúng một pack (COMP-031 nghiệm thu).
SAMPLE_PACKS: tuple[WorkflowPack, ...] = (
    _TAX_PACK,
    _ACCOUNTING_PACK,
    _SOCIAL_INSURANCE_PACK,
    _EDUCATION_PACK,
    _PUBLIC_ADMIN_PACK,
    _VERTICAL_PACK,
)


def load_sample_packs() -> tuple[WorkflowPack, ...]:
    """Trả các pack mẫu COMP-031 (dữ liệu giả) — nguồn DUY NHẤT cho CLI/test."""

    return SAMPLE_PACKS


def pack_to_dict(pack: WorkflowPack) -> dict[str, Any]:
    """Serialize ``WorkflowPack`` sang dict thuần JSON-được (enum → ``.value``).

    Xác định (deterministic): cùng ``pack`` luôn ra đúng cùng dict, không phụ
    thuộc thứ tự lặp ngẫu nhiên nào (``steps``/``devices``/``inputs`` đều giữ
    thứ tự ``tuple`` gốc)."""

    return {
        "pack_version": pack.pack_version,
        "sector": pack.sector.value,
        "workflow_id": pack.workflow_id,
        "title_vi": pack.title_vi,
        "provider_id": pack.provider_id,
        "gateway": pack.gateway,
        "steps": [
            {
                "name": step.name.value,
                "role": step.role,
                "expected_artifact": step.expected_artifact,
                "inputs": list(step.inputs),
                "stop_before_real_transaction": step.stop_before_real_transaction,
            }
            for step in pack.steps
        ],
        "devices": list(pack.devices),
        "notes_vi": pack.notes_vi,
    }


def _err(code: str, path: str, message_vi: str) -> ValidationError:
    return ValidationError(code=code, path=path, message_vi=message_vi)


def _required_steps_error() -> ValidationError:
    return _err(
        CompatErrorCode.E_COMPAT_REQUIRED_STEPS.value,
        "steps",
        t("compat.schema.error.required_steps", lang=Lang.VI),
    )


def _validate_required_steps(raw: Mapping[str, Any]) -> list[ValidationError]:
    """Đúng 7 nấc ECO-001 theo ``WORKFLOW_STEP_ORDER``, ĐÚNG thứ tự, không
    thiếu/không trùng/không lạ — tái dùng ``WORKFLOW_STEP_ORDER`` làm nguồn
    DUY NHẤT, không chép lại danh sách tên nấc ở đây."""

    expected = tuple(name.value for name in WORKFLOW_STEP_ORDER)
    steps = raw.get("steps")

    # str/bytes cũng là Sequence — loại trừ tường minh để không coi một
    # chuỗi là "danh sách nấc" hợp lệ.
    if not isinstance(steps, Sequence) or isinstance(steps, (str, bytes)):
        return [_required_steps_error()]

    names: list[str] = []
    for item in steps:
        if not isinstance(item, Mapping):
            return [_required_steps_error()]
        name = item.get("name")
        if not isinstance(name, str):
            return [_required_steps_error()]
        names.append(name)

    if tuple(names) != expected:
        return [_required_steps_error()]
    return []


def _scan_executable_keys_compat(raw: Any, *, path: str = "") -> list[ValidationError]:
    """Quét bổ sung riêng của compat (thông báo rõ COMP-031) trên CÙNG tập
    khóa cấm ``FORBIDDEN_EXECUTABLE_KEYS`` (tái dùng, không định nghĩa lại
    tập khóa) — lớp chặn CHÍNH vẫn là ``validate_no_executable_keys``."""

    errors: list[ValidationError] = []
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            child_path = f"{path}.{key}" if path else str(key)
            if isinstance(key, str) and key.lower() in FORBIDDEN_EXECUTABLE_KEYS:
                errors.append(
                    _err(
                        "E_COMPAT_PACK_EXECUTABLE",
                        child_path,
                        t("compat.schema.error.pack_executable", lang=Lang.VI, field=key),
                    )
                )
            errors.extend(_scan_executable_keys_compat(value, path=child_path))
    elif isinstance(raw, list):
        for idx, item in enumerate(raw):
            errors.extend(_scan_executable_keys_compat(item, path=f"{path}[{idx}]"))
    return errors


def _scan_secrets(raw: Any, *, path: str = "") -> list[ValidationError]:
    """Quét đệ quy mọi key chuỗi ở BẤT KỲ cấp lồng nào; key chứa (không phân
    biệt hoa/thường) một trong các chuỗi con nhạy cảm → lỗi
    ``E_COMPAT_PACK_SECRET`` (COMP-031: pack không bao giờ mang secret)."""

    errors: list[ValidationError] = []
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            child_path = f"{path}.{key}" if path else str(key)
            if isinstance(key, str):
                lowered = key.lower()
                if any(sub in lowered for sub in _SECRET_KEY_SUBSTRINGS):
                    errors.append(
                        _err(
                            CompatErrorCode.E_COMPAT_PACK_SECRET.value,
                            child_path,
                            t("compat.schema.error.pack_secret", lang=Lang.VI, field=key),
                        )
                    )
            errors.extend(_scan_secrets(value, path=child_path))
    elif isinstance(raw, list):
        for idx, item in enumerate(raw):
            errors.extend(_scan_secrets(item, path=f"{path}[{idx}]"))
    return errors


def validate_pack_raw(raw: Mapping[str, Any]) -> list[ValidationError]:
    """Thẩm định cấu trúc + an toàn một Workflow Pack THÔ (như vừa load từ
    JSON), COMP-031: đúng 7 nấc ECO-001 theo thứ tự, KHÔNG khóa thực thi bị
    cấm (tái dùng ``validate_no_executable_keys`` làm lớp chặn chính), KHÔNG
    trường mang secret ở bất kỳ cấp lồng nào. Trả ``[]`` khi sạch."""

    errors: list[ValidationError] = []
    errors.extend(_validate_required_steps(raw))
    errors.extend(validate_no_executable_keys(raw))
    errors.extend(_scan_executable_keys_compat(raw))
    errors.extend(_scan_secrets(raw))
    return errors
