"""``namios_dotnet`` — phân tích TĨNH file PE/.NET (NET-001/NET-002).

KHÔNG BAO GIỜ thực thi file đầu vào để nhận diện. Thu thập PE
architecture/CLR metadata bằng struct parsing thuần + đọc
``.runtimeconfig.json``/``.deps.json`` đi kèm (nếu có) để suy ra
TargetFramework/phụ thuộc. Trả kết quả gồm ``confidence``, ``evidence``,
``unknown_dependencies``, ``suggested_mode`` — LUÔN kèm nhắc rằng đây chỉ là
gợi ý, không phải chứng nhận chạy (xem ``types.STATIC_ANALYSIS_DISCLAIMER_VI``).

An toàn (NET-001/NET-004): giới hạn kích thước đọc, giới hạn số
section/data-directory, không crash trên PE dị dạng, dùng
``namios_security`` (FD-based) cho mọi lượt mở file thật — xem
``_io.py``/``pe_format.py`` cho chi tiết.

Owner module: chỉ sửa trong ``src/namios_dotnet/``, ``tests/unit/dotnet/``,
``fixtures/dotnet/`` (quy tắc chống giẫm chân M1-INTERFACES §0). Package này
tự được ``[tool.setuptools.packages.find] where=["src"]`` nhận diện — KHÔNG
cần sửa ``pyproject.toml``.
"""

from __future__ import annotations

from namios_dotnet._errors import DotnetAnalysisError, MalformedPeError
from namios_dotnet.analyzer import DotnetAnalyzer
from namios_dotnet.types import (
    STATIC_ANALYSIS_DISCLAIMER_VI,
    ClrHeaderInfo,
    DotnetAnalysisResult,
    EvidenceItem,
    PeArchitecture,
    PeKind,
    SidecarInfo,
)

__all__ = [
    "DotnetAnalyzer",
    "DotnetAnalysisError",
    "MalformedPeError",
    "DotnetAnalysisResult",
    "PeArchitecture",
    "PeKind",
    "ClrHeaderInfo",
    "SidecarInfo",
    "EvidenceItem",
    "STATIC_ANALYSIS_DISCLAIMER_VI",
]
