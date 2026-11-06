"""Document Broker (ODC-007) — API chung cho File Manager / Open With / tìm kiếm /
SmartAI: ``inspect_document → explain_routes → open_copy/open_original → verify_save``.

Bất biến trung thực:
- Nội dung tài liệu là nguồn KHÔNG tin cậy: KHÔNG tự upload, KHÔNG đổi app mặc định,
  KHÔNG tạo hành động vì chỉ-dẫn nằm trong file (ODC-007/017 — TÁI DÙNG
  ``namios_sys.data_authority``).
- File nhạy cảm KHÔNG mở trên web mặc định; ``auto_upload`` luôn False.
- Mở tài liệu ngoại (DOCX/XLSX/…) → mặc định mở BẢN SAO, bản gốc bất biến, không
  âm thầm chuyển định dạng rồi ghi đè (ODC-006).
- ``verify_save`` TÁI DÙNG fidelity gate: sai dữ liệu nghĩa → chặn lưu/in (ODC-014).
"""

from __future__ import annotations

from collections.abc import Iterable

from namios_odc import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_odc._types import (
    DocFormat,
    DocRouteResult,
    DocSensitivity,
    DocumentMetadata,
    OfficeNeed,
)
from namios_odc.route_matrix import resolve_document_route
from namios_pra import FidelityIssue, fidelity_gate
from namios_sys._types import SourceTrust
from namios_sys.data_authority import authorize

__all__ = [
    "inspect_document",
    "explain_routes",
    "open_as_copy",
    "may_auto_upload",
    "document_instruction_authorized",
    "verify_save",
]

#: Định dạng ngoại (OOXML) — engine cài sẵn (ODF) mở sẽ chuyển đổi → mở BẢN SAO để
#: giữ bản gốc, không ghi đè âm thầm (ODC-006).
_FOREIGN_FORMATS = frozenset(
    {DocFormat.DOCX, DocFormat.XLSX, DocFormat.XLSM, DocFormat.PPTX, DocFormat.DOCM}
)


def inspect_document(
    doc_format: DocFormat,
    needs: Iterable[OfficeNeed] = (),
    *,
    has_macros: bool = False,
    has_signature: bool = False,
    encrypted_or_irm: bool = False,
    missing_fonts: tuple[str, ...] = (),
    external_links: bool = False,
    sensitivity: DocSensitivity = DocSensitivity.UNKNOWN,
) -> DocumentMetadata:
    """Bóc metadata an toàn (ODC-007). Chỉ nhận dấu hiệu quan sát được — KHÔNG thực
    thi nội dung, KHÔNG đọc/suy luận chỉ-dẫn trong file. .xlsm/.docm tự coi là có
    macro (fail-closed) dù caller quên khai."""

    macros = has_macros or doc_format in {DocFormat.XLSM, DocFormat.DOCM}
    return DocumentMetadata(
        doc_format=doc_format,
        needs=frozenset(needs),
        has_macros=macros,
        has_signature=has_signature,
        encrypted_or_irm=encrypted_or_irm,
        missing_fonts=tuple(missing_fonts),
        external_links=external_links,
        sensitivity=sensitivity,
    )


def explain_routes(metadata: DocumentMetadata, **availability: bool) -> DocRouteResult:
    """Giải thích tuyến xử lý (ODC-007/008) — ủy quyền cho route matrix. ``availability``
    = cờ ``bundled_supported``/``web_available``/``windows_vm_available``/…"""

    return resolve_document_route(metadata, **availability)


def open_as_copy(metadata: DocumentMetadata) -> bool:
    """Có nên mở BẢN SAO không (ODC-006). File ngoại hoặc nhạy cảm → True (giữ bản
    gốc bất biến, không âm thầm chuyển định dạng/ghi đè)."""

    return (
        metadata.doc_format in _FOREIGN_FORMATS or metadata.sensitivity is DocSensitivity.SENSITIVE
    )


def may_auto_upload(metadata: DocumentMetadata) -> bool:
    """Có được TỰ ĐỘNG đưa tài liệu lên cloud/web/model ngoài không (ODC-017).
    LUÔN False — mọi lần đưa dữ liệu ra ngoài cần người dùng xác nhận rõ."""

    return False


def document_instruction_authorized(action: str, *, content: str = "") -> bool:
    """Chỉ-dẫn nằm TRONG nội dung tài liệu có được biến thành hành động không
    (ODC-007). KHÔNG — tài liệu là nguồn không tin cậy (TÁI DÙNG
    ``data_authority``: source=DOCUMENT luôn bị từ chối, kể cả khi file 'bảo' làm)."""

    decision = authorize(
        action, source=SourceTrust.DOCUMENT, org_policy_allows=True, content=content
    )
    return decision.allowed


def verify_save(issues: Iterable[FidelityIssue]) -> tuple[bool, str]:
    """Cổng kiểm trước khi LƯU/IN (ODC-014) — TÁI DÙNG fidelity gate PRA-017: bất
    kỳ sai lệch dữ liệu nghĩa (số tiền/công thức/chữ ký) ở mức BLOCKING → chặn,
    dù file mở được."""

    return fidelity_gate(list(issues))
