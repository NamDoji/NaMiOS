"""Mã lỗi ổn định cho ``namios_odc`` (Phụ lục 07)."""

from __future__ import annotations

from enum import Enum

__all__ = ["OdcErrorCode"]


class OdcErrorCode(str, Enum):
    """Mã lỗi machine-readable (ODC). Trường dữ liệu, giữ nguyên qua i18n."""

    E_ODC_MACRO_OVERCLAIM = "E_ODC_MACRO_OVERCLAIM"  # gán macro-pass cho web/bundled
    E_ODC_AUTO_UPLOAD = "E_ODC_AUTO_UPLOAD"  # tự đưa tài liệu ra ngoài
    E_ODC_DOC_INSTRUCTION = "E_ODC_DOC_INSTRUCTION"  # nghe lệnh trong nội dung tài liệu
    E_ODC_FIDELITY_BLOCK = "E_ODC_FIDELITY_BLOCK"  # sai dữ liệu nghĩa, chặn lưu/in
    E_ODC_CERT_OVERCLAIM = "E_ODC_CERT_OVERCLAIM"  # nâng cert không đủ bằng chứng
    E_ODC_COVERAGE_OVERCLAIM = "E_ODC_COVERAGE_OVERCLAIM"  # catalog coi là đã-hỗ-trợ
