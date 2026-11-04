"""Sandbox capsule + rollback + supply-chain (SAI-018/020).

Bất biến an toàn (nghiệm thu SAI-018): mọi thử nghiệm thay đổi runtime/registry/
prefix diễn ra trên BẢN SAO capsule có snapshot — KHÔNG đụng bản gốc, KHÔNG
mount home/DB sản xuất/token thật. ``Capsule`` frozen: thao tác trả capsule
MỚI, tham chiếu gốc bất biến. ``rollback`` hoàn nguyên cấu hình + data test,
KHÔNG xóa user data (model này không chứa user data — chỉ là bản sao).

Supply-chain (SAI-020): chỉ nhận nguồn chính thức + có hash; đổi miền/thiếu
hash → không chạy mặc định.
"""

from __future__ import annotations

from dataclasses import replace
from urllib.parse import urlparse

from namios_smartai._types import Capsule

__all__ = [
    "make_capsule",
    "apply_change",
    "rollback",
    "check_supply_chain",
]


def make_capsule(base_id: str, *, capsule_id: str, snapshot_id: str) -> Capsule:
    """Tạo capsule bản sao từ ``base_id`` với snapshot trước-thử."""

    return Capsule(capsule_id=capsule_id, base_id=base_id, snapshot_id=snapshot_id)


def apply_change(capsule: Capsule, change: str) -> Capsule:
    """Ghi MỘT thay đổi (đo được) lên capsule → trả capsule MỚI. Bản gốc
    (tham số) KHÔNG bị đổi (frozen). KHÔNG áp lên capsule đã rollback."""

    if capsule.rolled_back:
        raise ValueError("capsule đã rollback — tạo bản sao mới trước khi thử tiếp")
    return replace(capsule, mutations=(*capsule.mutations, change))


def rollback(capsule: Capsule) -> Capsule:
    """Hoàn nguyên về snapshot: trả capsule với ``rolled_back=True`` +
    ``mutations=()``. KHÔNG xóa user data (không có trong model)."""

    return replace(capsule, mutations=(), rolled_back=True)


def check_supply_chain(
    source_url: str,
    app_hash: str,
    *,
    official_hosts: tuple[str, ...] = (),
) -> list[str]:
    """Kiểm nguồn cài (SAI-020). Trả danh sách vấn đề (rỗng = hợp lệ): URL
    phải https + thuộc host chính thức (nếu có allowlist); phải có hash.
    KHÔNG chạy mặc định khi đổi miền/thiếu hash."""

    problems: list[str] = []
    parsed = urlparse(source_url or "")
    if parsed.scheme != "https" or not parsed.netloc:
        problems.append("source_url không phải https hợp lệ")
    elif official_hosts and parsed.netloc.lower() not in {h.lower() for h in official_hosts}:
        problems.append(f"miền '{parsed.netloc}' không thuộc danh sách nguồn chính thức")
    if not (app_hash or "").strip():
        problems.append("thiếu app_hash để xác thực bộ cài")
    return problems
