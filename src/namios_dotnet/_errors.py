"""Exception nội bộ của ``namios_dotnet`` (NET-001/NET-002).

Phân tách rõ hai loại lỗi:

- ``DotnetAnalysisError``: lỗi THAO TÁC (không mở được file an toàn, path
  không hợp lệ, vượt giới hạn kích thước cứng). Lỗi này được phép thoát khỏi
  API công khai (``DotnetAnalyzer.analyze``) vì caller không thể tiếp tục mà
  không biết — mang theo ``code`` (``namios_core.errors.ErrorCode``) để map
  exit code (M1-INTERFACES §2/§3).
- ``MalformedPeError``: lỗi NỘI DUNG (PE dị dạng/cụt/offset vô lý). Lỗi này
  KHÔNG BAO GIỜ thoát khỏi API công khai — tầng ``analyzer`` luôn bắt và biến
  thành ``DotnetAnalysisResult`` với ``kind=MALFORMED``/``confidence=0.0``,
  đúng yêu cầu "PE dị dạng → trả kết quả low-confidence, KHÔNG crash".
"""

from __future__ import annotations

from dataclasses import dataclass

from namios_core.errors import ErrorCode

__all__ = ["DotnetAnalysisError", "MalformedPeError"]


@dataclass
class DotnetAnalysisError(Exception):
    """Lỗi thao tác (I/O/an toàn đường dẫn) khi phân tích .NET/PE."""

    code: ErrorCode
    reason_vi: str

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"Lỗi phân tích .NET ({self.code.value}): {self.reason_vi}"


@dataclass
class MalformedPeError(Exception):
    """PE dị dạng/cụt/offset vô lý — tín hiệu NỘI BỘ cho tầng ``pe_format``/
    ``analyzer``; KHÔNG map ra exit code, KHÔNG thoát khỏi API công khai."""

    reason_vi: str

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"PE dị dạng: {self.reason_vi}"
