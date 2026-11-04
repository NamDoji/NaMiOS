"""Dependency Graph + execute gate (SAI-007).

Mô hình phụ thuộc installer → runtime → COM/service/DB/browser → thiết bị/
token → tài liệu → portal. Mỗi node có ``observed|inferred|unknown`` + nguồn
+ blocker.

Bất biến (nghiệm thu SAI-007): một app MỞ được cửa sổ nhưng thiếu DB (node
``required`` chưa ``observed`` hoặc có ``blocker``) → bước execute BỊ CHẶN,
KHÔNG được coi là hoàn thành. Hàm ở đây chỉ TÍNH toán tất định; diễn giải VI
do ``diagnose`` bọc qua i18n.
"""

from __future__ import annotations

from namios_smartai._types import DependencyGraph, DepNode, NodeStatus

__all__ = ["build_graph", "execute_blockers", "is_execute_blocked"]


def build_graph(workflow_id: str, nodes: tuple[DepNode, ...]) -> DependencyGraph:
    return DependencyGraph(workflow_id=workflow_id, nodes=tuple(nodes))


def execute_blockers(graph: DependencyGraph) -> tuple[str, ...]:
    """Trả mô tả có cấu trúc của các node BẮT BUỘC đang chặn execute: node
    ``required`` mà ``status != observed`` HOẶC có ``blocker``. Rỗng = không
    chặn. (Chuỗi dạng ``node_id|kind|reason`` để ``diagnose`` format VI.)"""

    out: list[str] = []
    for node in graph.nodes:
        if not node.required:
            continue
        if node.blocker:
            out.append(f"{node.node_id}|{node.kind.value}|{node.blocker}")
        elif node.status != NodeStatus.OBSERVED:
            out.append(f"{node.node_id}|{node.kind.value}|{node.status.value}")
    return tuple(out)


def is_execute_blocked(graph: DependencyGraph) -> bool:
    return bool(execute_blockers(graph))
