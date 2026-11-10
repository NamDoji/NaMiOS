"""Thin broker CLI — hợp đồng bash→Python (ADR-0021, PL14 Lớp 4/5).

Đây là GLUE mà trợ lý bash đang ship (``namios-smartai``) sẽ gọi thay vì tự chạy
``argv`` rời: bash phát MỘT yêu cầu JSON, nhận MỘT phản hồi có cấu trúc. Nhờ đó
Tool Broker Python (``src/namios_smartai``) là NGUỒN SỰ THẬT DUY NHẤT về
policy/capability/audit/redaction; bash giữ phần nó làm tốt — hỏi mật khẩu qua
``pkexec`` + hiển thị tiếng Việt + Timeshift undo.

Hợp đồng (ổn định):

    request  = {"intent": str, "tool": str, "args": {..}, "consent": {..}|null}
    response = {"plan": [..≤3..], "result": {status,message_vi,error_code,data},
                "audit_id": str, "status": "success|failed|blocked|partial"}

Bất biến giữ nguyên từ cả hai thân mã:
- plan ≤ 3 bước + mức chắc chắn (bash ``smartai_plan_add`` ⇄ ``_build_plan`` ở đây);
- consent cho hành động đặc quyền: tool GHI/privileged KHÔNG chạy ở CLI này —
  trả phản hồi GATED (chuẩn bị kế hoạch, chờ consent + pkexec), KHÔNG bịa biên
  nhận/side-effect (parity SAI-022 + guardrail bash #1/#3);
- audit: mỗi yêu cầu sinh ``audit_id`` + ghi ``Trace`` (SAI-034, note đã redact);
- chống prompt-injection: ``intent`` là DỮ LIỆU không tin cậy → quét fail-closed
  TRƯỚC khi định tuyến (SAI-019);
- redaction: ``result.data`` đã che bí mật (adapter tự redact; SAI-024).

HONEST: adapter đọc CLI OS THẬT nhưng ở sandbox này suy biến ``tool_unavailable``;
Model Router thật CHƯA nối (CLI nhận ``tool`` tường minh, không tự chọn LLM);
executor ĐẶC QUYỀN (apt/firewall/quarantine) vẫn gated, KHÔNG tự chạy.
"""

from __future__ import annotations

import json
import sys
import uuid
from typing import Any

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._errors import SaiErrorCode
from namios_smartai._types import ToolResult, ToolResultStatus, TraceErrorClass, TraceEvent
from namios_smartai.adapters import ADAPTERS_BY_NAME, ReadOnlyAdapter, run_adapter
from namios_smartai.injection import guard_untrusted
from namios_smartai.observability import Trace

__all__ = [
    "PRIVILEGED_TOOLS",
    "handle_request",
    "main",
]

#: Tool GHI/ĐẶC QUYỀN đã biết (catalog smartai-tools.schema.json): broker CLI
#: CHUẨN BỊ nhưng KHÔNG tự chạy — cần consent + pkexec (gated, honest).
PRIVILEGED_TOOLS: frozenset[str] = frozenset(
    {
        "network.radio_on",
        "network.retry",
        "printer.test_page",
        "printer.clear_queue",
        "printer.restart_service",
        "bluetooth.set_output",
        "bluetooth.restart_service",
        "ime.restart",
        "system.open_timeshift",
        "apt.install",
        "firewall.set",
        "quarantine.apply",
    }
)


def _new_audit_id() -> str:
    return f"sai-{uuid.uuid4().hex[:12]}"


def _result_dict(result: ToolResult) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "message_vi": result.message_vi,
        "error_code": result.error_code,
        "data": dict(result.data),
    }


def _build_plan(adapter: ReadOnlyAdapter | None, tool: str) -> list[dict[str, str]]:
    """Kế hoạch ≤3 bước hữu hình (bất biến bash "tối đa 3 bước")."""

    if adapter is not None:
        plan = [
            {
                "step": "Kiểm công cụ OS khả dụng (chỉ đọc)",
                "risk": "R0",
                "confidence": "cao",
            },
            {
                "step": "Đọc trạng thái thật qua Broker (policy + fail-closed + capability)",
                "risk": adapter.spec.risk.value,
                "confidence": "cao",
            },
            {
                "step": "Che bí mật + trả bằng chứng (KHÔNG tự tuyên bố 'đã xong')",
                "risk": "R0",
                "confidence": "cao",
            },
        ]
    else:
        plan = [
            {
                "step": f"Phân loại tool '{tool}' (đặc quyền/ghi?)",
                "risk": "R0",
                "confidence": "cao",
            },
            {
                "step": "Chuẩn bị consent + pkexec (KHÔNG tự chạy ở broker CLI)",
                "risk": "R3",
                "confidence": "vừa",
            },
        ]
    return plan[:3]


def handle_request(
    request: dict[str, Any],
    *,
    trace: Trace | None = None,
    runner: Any | None = None,
    now: str | None = None,
    audit_id: str | None = None,
) -> dict[str, Any]:
    """Xử lý MỘT yêu cầu broker (hợp đồng bash→Python). Luôn trả dict phản hồi;
    KHÔNG raise cho lỗi "nghiệp vụ" (fail-closed = trả BLOCKED/FAILED)."""

    trace = trace if trace is not None else Trace()
    audit_id = audit_id or _new_audit_id()

    tool = str(request.get("tool") or "").strip()
    intent = str(request.get("intent") or "")

    def _respond(result: ToolResult, adapter: ReadOnlyAdapter | None) -> dict[str, Any]:
        return {
            "plan": _build_plan(adapter, tool),
            "result": _result_dict(result),
            "audit_id": audit_id,
            "status": result.status.value,
        }

    # 0) Yêu cầu hợp lệ?
    if not tool:
        res = ToolResult(
            status=ToolResultStatus.BLOCKED,
            error_code=SaiErrorCode.E_SAI_TOOL_SCHEMA.value,
            message_vi=t("sai.broker.bad_request", lang=Lang.VI, detail="thiếu 'tool'"),
        )
        return _respond(res, None)

    # 1) CHỐNG PROMPT-INJECTION: 'intent' là nội dung không tin cậy (SAI-019) →
    #    quét TRƯỚC khi làm gì; dính mưu đồ điều khiển → BLOCKED fail-closed.
    if intent:
        blocked = guard_untrusted(intent)
        if blocked is not None:
            trace.record(
                TraceEvent(
                    event_id="broker:injection",
                    plan_id="smartai-broker",
                    action_id=tool,
                    policy_decision="deny",
                    tool=tool,
                    result="blocked",
                    error_class=TraceErrorClass.POLICY,
                    correlation_id=audit_id,
                    note=blocked.message_vi,
                )
            )
            return _respond(blocked, None)

    # 2) Tool GHI/ĐẶC QUYỀN → GATED (chuẩn bị, KHÔNG tự chạy; cần consent+pkexec).
    if tool in PRIVILEGED_TOOLS:
        res = ToolResult(
            status=ToolResultStatus.BLOCKED,
            error_code=SaiErrorCode.E_SAI_CONSENT_REQUIRED.value,
            message_vi=t("sai.broker.gated", lang=Lang.VI, tool=tool),
            data={"gated": True, "requires": ["consent", "pkexec"]},
        )
        trace.record(
            TraceEvent(
                event_id="broker:gated",
                plan_id="smartai-broker",
                action_id=tool,
                policy_decision="deny",
                tool=tool,
                result="blocked",
                error_class=TraceErrorClass.POLICY,
                correlation_id=audit_id,
                note=res.message_vi,
            )
        )
        return _respond(res, None)

    # 3) Adapter read-only đã đăng ký? → chạy THẬT qua broker.
    adapter = ADAPTERS_BY_NAME.get(tool)
    if adapter is None:
        res = ToolResult(
            status=ToolResultStatus.BLOCKED,
            error_code=SaiErrorCode.E_SAI_TOOL_UNKNOWN.value,
            message_vi=t("sai.broker.unknown", lang=Lang.VI, tool=tool),
        )
        return _respond(res, None)

    result = run_adapter(
        adapter, runner=runner, trace=trace, correlation_id=audit_id, now=now
    )
    return _respond(result, adapter)


def main(argv: list[str] | None = None) -> int:
    """Điểm vào dòng lệnh: đọc yêu cầu JSON (tham số đầu hoặc stdin), in phản hồi
    JSON ra stdout. ``namios-smartai`` bash gọi:  ``python3 -m namios_smartai.cli
    '<json>'``  (hoặc pipe JSON qua stdin). Luôn exit 0 (không làm sập phiên)."""

    argv = sys.argv[1:] if argv is None else argv
    raw = argv[0] if argv else sys.stdin.read()
    try:
        request = json.loads(raw) if raw.strip() else {}
        if not isinstance(request, dict):
            raise ValueError("JSON gốc phải là object")
    except (ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "plan": [],
                    "result": {
                        "status": "blocked",
                        "message_vi": t(
                            "sai.broker.bad_request", lang=Lang.VI, detail=str(exc)
                        ),
                        "error_code": SaiErrorCode.E_SAI_TOOL_SCHEMA.value,
                        "data": {},
                    },
                    "audit_id": _new_audit_id(),
                    "status": "blocked",
                },
                ensure_ascii=False,
            )
        )
        return 0

    response = handle_request(request)
    print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
