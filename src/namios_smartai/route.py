"""Route Selection (SAI-008) — TÁI DÙNG Compatibility Resolver COMP-025.

SmartAI KHÔNG tự chế logic chọn route: nó ủy quyền cho
``namios_compat.resolve_routes`` (policy + evidence + bản quyền + thiết bị +
mạng quyết định danh sách hợp lệ). AI có thể DIỄN GIẢI phân loại runtime
(``classification``) nhưng KHÔNG được dùng nó để NÂNG route — vd thấy ".NET"
KHÔNG tự gán ``native_linux`` (nghiệm thu SAI-008); chỉ route có chứng cứ
workflow_verified mới được đề xuất, route qua Windows luôn hiện rõ phụ thuộc
Windows.
"""

from __future__ import annotations

from namios_compat._types import ResolveInput, RouteResolution, RuntimeClassification, WorkflowEntry
from namios_compat.resolver import resolve_routes

__all__ = ["select_route"]


def select_route(
    entry: WorkflowEntry,
    inp: ResolveInput,
    *,
    classification: RuntimeClassification | None = None,
) -> RouteResolution:
    """Chọn route cho một workflow (SAI-008).

    ``classification`` (nếu có) chỉ để TRACE/diễn giải — quyết định cuối vẫn do
    resolver (chứng cứ + policy). Không override: một app WPF/WinForms dù phân
    loại ".NET" vẫn KHÔNG được resolver đề xuất ``native_linux`` trừ khi có
    route native đã workflow_verified."""

    # Giữ tham số classification trong chữ ký để tầng gọi (diagnose/CLI) truyền
    # ngữ cảnh nhất quán; cố ý KHÔNG dùng để sửa kết quả resolver (trung thực).
    _ = classification
    return resolve_routes(inp, entry)
