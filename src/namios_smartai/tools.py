"""Tool Broker SmartAI M0 (SAI-015/016/040, Phụ lục 04).

Tool Broker là CỔNG DUY NHẤT giữa kế hoạch (``ToolCall`` do AI đề xuất) và
hành động thật. AI chỉ phát ra ACTION CÓ CẤU TRÚC — không có root shell,
không build chuỗi lệnh, không ``eval``/``subprocess``. Mọi tool phải đăng ký
trước (``ToolSpec``); registry FAIL-CLOSED: mọi vi phạm (tool lạ, thiếu
tham số, path/URL ngoài phạm vi, capability thiếu/hết hạn/sai phạm vi) trả
về ``ToolResult(BLOCKED, ...)`` — KHÔNG bao giờ ``raise`` cho các lỗi
"chính sách" này (chỉ bug lập trình mới raise).

M0: các "executor" dưới đây là MOCK — không có side-effect thật (không I/O
hệ thống, không mạng thật). Phần được test ở đây là HÀNH VI BROKER (validate
+ fail-closed theo đúng thứ tự); phần "chạy thật" nối dây ở pha sau."""

from __future__ import annotations

import os
from collections.abc import Sequence
from datetime import date, datetime, time

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._errors import SaiErrorCode
from namios_smartai._types import (
    RISK_ORDER,
    CapabilityToken,
    RiskTier,
    ToolCall,
    ToolResult,
    ToolResultStatus,
    ToolSpec,
)

__all__ = ["DEFAULT_TOOLS", "ToolRegistry"]


#: Danh bạ tool SAI-015 của M0. Mỗi tool khai báo risk/scope riêng — Broker
#: chỉ cho chạy đúng những gì khai báo, không suy diễn thêm.
DEFAULT_TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(name="inspect_app", risk=RiskTier.R0),
    ToolSpec(name="check_source", risk=RiskTier.R0, network_scope="official_only"),
    ToolSpec(name="preflight", risk=RiskTier.R0),
    ToolSpec(name="open_official_url", risk=RiskTier.R0, network_scope="official_only"),
    ToolSpec(name="request_vendor_help", risk=RiskTier.R0),
    ToolSpec(
        name="run_test",
        risk=RiskTier.R1,
        filesystem_scope="capsule",
        retry_safe=True,
        rollback_class="snapshot",
    ),
    ToolSpec(name="capture_sanitized_log", risk=RiskTier.R1),
    ToolSpec(name="compare_artifacts", risk=RiskTier.R1),
    ToolSpec(
        name="create_capsule",
        risk=RiskTier.R2,
        writes=True,
        filesystem_scope="capsule",
        rollback_class="snapshot",
    ),
    ToolSpec(
        name="install_test",
        risk=RiskTier.R2,
        required_params=("source_hash",),
        writes=True,
        filesystem_scope="capsule",
        rollback_class="snapshot",
    ),
    ToolSpec(
        name="rollback",
        risk=RiskTier.R1,
        writes=True,
        rollback_class="reversible",
    ),
)


def _parse_iso(value: str) -> datetime | None:
    """Parse ISO-8601 date hoặc datetime; ``None`` nếu không parse được."""

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.combine(date.fromisoformat(value), time.min)
        except ValueError:
            return None


def _expired(expires_at: str | None, now: str | None) -> bool:
    """``True`` nếu capability đã quá hạn tại ``now`` (SAI-016).

    Không có ``now`` → không đánh giá được hạn → coi như còn (caller chủ
    động không truyền thời điểm). Có ``now`` nhưng chuỗi hạn/``now`` không
    parse được → coi như hết hạn (bảo thủ, fail-closed)."""

    if not expires_at or not now:
        return False
    exp = _parse_iso(expires_at)
    nw = _parse_iso(now)
    if exp is None or nw is None:
        return True
    return nw > exp


def _has_dotdot(path: str) -> bool:
    """``True`` nếu một thành phần path là ``..`` (traversal) — luôn từ
    chối, bất kể ``allowed_paths`` có được cấu hình hay không."""

    normalized = path.replace("\\", "/")
    return ".." in normalized.split("/")


def _path_within(path: str, allowed_paths: tuple[str, ...]) -> bool:
    """Prefix check AN TOÀN trên path đã chuẩn hoá (không dùng chuỗi shell,
    không ``eval``) — ``path`` phải NẰM TRONG một trong ``allowed_paths``."""

    norm = os.path.normpath(path)
    for allowed in allowed_paths:
        allowed_norm = os.path.normpath(allowed)
        if norm == allowed_norm or norm.startswith(allowed_norm + os.sep):
            return True
    return False


def _blocked(error: SaiErrorCode, key: str, **params: object) -> ToolResult:
    return ToolResult(
        status=ToolResultStatus.BLOCKED,
        error_code=error.value,
        message_vi=t(key, lang=Lang.VI, **params),
    )


class ToolRegistry:
    """Tool Broker (SAI-015/040): registry CÓ KIỂU + validate fail-closed
    trước khi "chạy" (M0: mock) một ``ToolCall``."""

    def __init__(self, specs: Sequence[ToolSpec] = DEFAULT_TOOLS) -> None:
        self._specs: dict[str, ToolSpec] = {spec.name: spec for spec in specs}

    def get(self, name: str) -> ToolSpec | None:
        return self._specs.get(name)

    def list(self) -> tuple[ToolSpec, ...]:
        return tuple(sorted(self._specs.values(), key=lambda spec: spec.name))

    def invoke(
        self,
        call: ToolCall,
        *,
        capability: CapabilityToken | None = None,
        now: str | None = None,
        allowed_paths: tuple[str, ...] = (),
        allowed_urls: tuple[str, ...] = (),
    ) -> ToolResult:
        """Chạy một ``ToolCall`` qua Broker.

        Thứ tự kiểm tra (FAIL-CLOSED, mỗi bước trả ``ToolResult`` — không
        bao giờ raise cho lỗi chính sách):
        1) tool có đăng ký không; 2) tham số bắt buộc; 3) phạm vi path/URL;
        4) với tool ``writes`` — capability hợp lệ (còn hạn, chưa thu hồi,
        đủ bậc rủi ro, đúng chủ thể); 5) mock-run thành công."""

        spec = self._specs.get(call.tool)
        if spec is None:
            return _blocked(
                SaiErrorCode.E_SAI_TOOL_UNKNOWN, "sai.tool.error.unknown", tool=call.tool
            )

        missing = [
            name
            for name in spec.required_params
            if name not in call.params or call.params[name] in (None, "")
        ]
        if missing:
            return _blocked(
                SaiErrorCode.E_SAI_TOOL_SCHEMA,
                "sai.tool.error.schema",
                tool=call.tool,
                detail=", ".join(missing),
            )

        scope_error = self._check_scope(spec, call, allowed_paths, allowed_urls)
        if scope_error is not None:
            return scope_error

        if spec.writes:
            cap_error = self._check_capability(spec, call, capability, now)
            if cap_error is not None:
                return cap_error

        return ToolResult(
            status=ToolResultStatus.SUCCESS,
            message_vi=t("sai.tool.ok", lang=Lang.VI, tool=call.tool),
            data={"tool": call.tool, "mock": True},
        )

    @staticmethod
    def _check_scope(
        spec: ToolSpec,
        call: ToolCall,
        allowed_paths: tuple[str, ...],
        allowed_urls: tuple[str, ...],
    ) -> ToolResult | None:
        path = call.params.get("path")
        if path and spec.filesystem_scope != "none":
            path_str = str(path)
            if _has_dotdot(path_str):
                return _blocked(
                    SaiErrorCode.E_SAI_TOOL_SCOPE,
                    "sai.tool.error.scope",
                    tool=call.tool,
                    detail=f"path '{path_str}' chứa '..' (path traversal)",
                )
            if allowed_paths and not _path_within(path_str, allowed_paths):
                return _blocked(
                    SaiErrorCode.E_SAI_TOOL_SCOPE,
                    "sai.tool.error.scope",
                    tool=call.tool,
                    detail=f"path '{path_str}' nằm ngoài allowed_paths",
                )

        url = call.params.get("url")
        if url and spec.network_scope == "official_only":
            url_str = str(url)
            if url_str not in allowed_urls:
                return _blocked(
                    SaiErrorCode.E_SAI_TOOL_SCOPE,
                    "sai.tool.error.scope",
                    tool=call.tool,
                    detail=f"url '{url_str}' nằm ngoài allowed_urls",
                )
        return None

    @staticmethod
    def _check_capability(
        spec: ToolSpec,
        call: ToolCall,
        capability: CapabilityToken | None,
        now: str | None,
    ) -> ToolResult | None:
        if capability is None:
            return _blocked(
                SaiErrorCode.E_SAI_CAP_SCOPE,
                "sai.tool.error.cap_scope",
                tool=call.tool,
                detail="thiếu capability token cho hành động ghi",
            )
        if (
            capability.revoked
            or (capability.one_time and capability.used)
            or _expired(capability.expires_at, now)
        ):
            return _blocked(
                SaiErrorCode.E_SAI_CAP_EXPIRED, "sai.tool.error.cap_expired", tool=call.tool
            )
        if RISK_ORDER[capability.risk_tier] < RISK_ORDER[spec.risk]:
            return _blocked(
                SaiErrorCode.E_SAI_CAP_SCOPE,
                "sai.tool.error.cap_scope",
                tool=call.tool,
                detail=(
                    f"capability bậc {capability.risk_tier.value} thấp hơn "
                    f"yêu cầu {spec.risk.value}"
                ),
            )
        if capability.subject and call.target and capability.subject != call.target:
            return _blocked(
                SaiErrorCode.E_SAI_CAP_SCOPE,
                "sai.tool.error.cap_scope",
                tool=call.tool,
                detail="capability gắn chủ thể khác target của ToolCall",
            )
        return None
