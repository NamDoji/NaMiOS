"""Allowlist plan đã duyệt sẵn cho ``PlanPackageInstall``/
``ApplyApprovedPackagePlan`` (CLI-004, SEC-001).

Bất biến bắt buộc: caller KHÔNG BAO GIỜ được truyền tên repository/khóa
GPG/tên package tùy ý — chỉ được truyền ``allowlist_key`` (một chuỗi KHÔNG
diễn giải được thành đường dẫn/URL/lệnh) trỏ tới một ``ApprovedPlanEntry``
ĐÃ được nạp từ cấu hình tĩnh (packaging-time), KHÔNG phải do caller cung cấp
nội dung tại runtime.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from namios_core.helper_types import ApprovedPackagePlan
from namios_helper.errors import StalePlanError, UnknownAllowlistKeyError


@dataclass(frozen=True)
class ApprovedPlanEntry:
    """Một plan cài đặt ĐÃ DUYỆT SẴN, cấu hình tĩnh (packaging-time) — KHÔNG
    phải nội dung caller tự khai tại runtime.

    ``package_refs``: nhãn package cố định (KHÔNG phải chuỗi shell/URL) —
    ví dụ ``("misa-sme-connector",)``. Giữ CHỈ để báo cáo
    ``UpdateStatus.pending`` sau khi apply, KHÔNG dùng để dựng lệnh (không có
    đường nào trong module này gọi ``run_argv``/exec với các nhãn này)."""

    allowlist_key: str
    plan_id: str
    package_refs: tuple[str, ...]


def _compute_signed_digest(entry: ApprovedPlanEntry) -> str:
    """Digest ổn định cho một ``ApprovedPlanEntry`` — dùng để
    ``ApplyApprovedPackagePlan`` phát hiện plan bị sửa đổi/giả mạo giữa lúc
    ``PlanPackageInstall`` trả về và lúc apply (tương tự verify-at-apply của
    WP6, nhưng phạm vi hẹp: chỉ nội dung entry allowlist nội bộ)."""

    payload = "|".join((entry.allowlist_key, entry.plan_id, *entry.package_refs))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class PackagePlanAllowlist:
    """Registry allowlist nội bộ của helper — nguồn DUY NHẤT ánh xạ
    ``allowlist_key`` → plan đã duyệt. KHÔNG có method nào nhận package/repo
    tùy ý từ bên ngoài để thêm vào registry này tại runtime qua D-Bus (thêm
    entry CHỈ qua packaging-time config, ngoài phạm vi API ``SystemHelper``).
    """

    entries: dict[str, ApprovedPlanEntry] = field(default_factory=dict)
    _issued_digests: dict[str, str] = field(default_factory=dict, repr=False)

    def register(self, entry: ApprovedPlanEntry) -> None:
        """Nạp một entry đã duyệt — CHỈ gọi lúc khởi tạo service từ cấu hình
        tĩnh, KHÔNG phải đường API công khai cho D-Bus caller."""

        self.entries[entry.allowlist_key] = entry

    def plan_for(self, allowlist_key: str) -> ApprovedPackagePlan:
        """Tương ứng ``PlanPackageInstall``: tra ``allowlist_key`` trong
        registry, KHÔNG diễn giải chuỗi này thành path/URL/package tự do.
        Key lạ → ``UnknownAllowlistKeyError`` (``E_INPUT_SCHEMA``, exit 2)."""

        entry = self.entries.get(allowlist_key)
        if entry is None:
            raise UnknownAllowlistKeyError(
                f"allowlist_key không nằm trong danh sách đã duyệt: {allowlist_key!r}",
                details={"allowlist_key": allowlist_key},
            )
        digest = _compute_signed_digest(entry)
        self._issued_digests[entry.plan_id] = digest
        return ApprovedPackagePlan(plan_id=entry.plan_id, signed_digest=digest)

    def verify_plan(self, plan: ApprovedPackagePlan) -> ApprovedPlanEntry:
        """Tương ứng bước đầu của ``ApplyApprovedPackagePlan``: kiểm
        ``signed_digest`` khớp đúng plan ĐÃ phát hành bởi ``plan_for`` (chống
        caller tự chế ``plan_id``/digest hoặc tái dùng plan cũ đã đổi nội
        dung allowlist). Sai → ``StalePlanError`` (``E_PLAN_STALE``, exit 6).
        """

        expected = self._issued_digests.get(plan.plan_id)
        if expected is None or expected != plan.signed_digest:
            raise StalePlanError(
                f"Plan {plan.plan_id!r} không khớp bất kỳ plan đã phát hành hợp lệ nào",
                details={"plan_id": plan.plan_id},
            )
        entry = next(
            (e for e in self.entries.values() if e.plan_id == plan.plan_id),
            None,
        )
        if entry is None:
            raise StalePlanError(
                f"Plan {plan.plan_id!r} không còn tồn tại trong allowlist hiện tại",
                details={"plan_id": plan.plan_id},
            )
        return entry
