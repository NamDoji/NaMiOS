"""Read-only OS tool adapters nối THẬT qua Tool Broker (ADR-0021, PL14 Lớp 5).

M0 (``tools.py``) để executor MOCK cho determinism. Module này là bước M4 đầu
tiên: vài adapter CHỈ-ĐỌC gọi CLI OS thật (NetworkManager/CUPS/rfkill/BlueZ) qua
``subprocess`` **argv tĩnh** (không shell, không ``eval``, không lệnh lấy từ
log/web), phân tích đầu ra thành dữ liệu có cấu trúc, rồi trả ``ToolResult`` —
nhưng CHỈ sau khi đi qua Broker:

    policy.evaluate (SAI-039) → ToolRegistry.invoke fail-closed (SAI-015/040) →
    kiểm lệnh khả dụng → chạy đọc thật → PARSE → REDACT (SAI-024) → Trace (SAI-034).

Bất biến (khớp SMARTAI-TOOL-BROKER.md §1):
- MỌI adapter ở đây READ-ONLY: ``ToolSpec.writes=False`` + RiskTier R0/R1 → policy
  cho chạy KHÔNG cần consent/xác nhận. ``run_adapter`` TỰ fail-closed nếu ai đó
  đưa vào spec có ``writes`` hay risk > R1 (phòng thủ chiều sâu).
- Hành động GHI/ĐẶC QUYỀN (bật radio, reset CUPS, cài gói…) KHÔNG chạy ở đây —
  vẫn gated bởi capability + consent + pkexec trong ``policy.py``/``tools.py``.
- "Đã đọc được trạng thái" ≠ "đã xong việc": adapter chỉ trả BẰNG CHỨNG đã che
  bí mật; Outcome Validator/người dùng mới kết luận.

HONEST (ADR-0021): các lệnh ``subprocess`` nhắm OS/pilot THẬT. Trong sandbox này
các CLI chưa cài → ``run_adapter`` suy biến về ``tool_unavailable`` (trung thực).
Các hàm ``parse_*`` thuần tuý được unit-test với fixture đã bắt sẵn; KHÔNG bịa
side-effect OS. Model Router thật (chọn LLM) VẪN chưa nối — ngoài phạm vi file này.
"""

from __future__ import annotations

import re
import shutil
import subprocess  # noqa: S404  (chỉ chạy argv TĨNH từ catalog; không shell, không input model)
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._errors import SaiErrorCode
from namios_smartai._types import (
    RiskTier,
    ToolCall,
    ToolResult,
    ToolResultStatus,
    ToolSpec,
    TraceErrorClass,
    TraceEvent,
)
from namios_smartai.observability import Trace
from namios_smartai.redaction import redact_bundle
from namios_smartai.tools import DEFAULT_TOOLS, ToolRegistry

__all__ = [
    "CommandResult",
    "ReadOnlyAdapter",
    "ADAPTER_TOOLS",
    "READONLY_ADAPTERS",
    "ADAPTERS_BY_NAME",
    "build_adapter_registry",
    "run_adapter",
    "parse_nmcli_devices",
    "parse_lpstat",
    "parse_rfkill",
    "parse_bluetoothctl_show",
]


# ---------------------------------------------------------------------------
# Hợp đồng chạy lệnh (cho phép tiêm fixture trong test — KHÔNG đụng OS thật)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CommandResult:
    """Kết quả chạy một lệnh đọc (chuẩn hoá để test tiêm được)."""

    returncode: int
    stdout: str = ""
    stderr: str = ""


#: Runner: nhận argv tĩnh + timeout → CommandResult. Mặc định dùng subprocess;
#: test truyền runner giả trả fixture (chạy TOÀN BỘ đường broker mà không cần CLI).
Runner = Callable[[tuple[str, ...], int], CommandResult]


def _default_runner(argv: tuple[str, ...], timeout_s: int) -> CommandResult:
    """Chạy ``argv`` TĨNH (không shell) chỉ-đọc, có timeout. ``FileNotFoundError``
    (thiếu CLI) được ``run_adapter`` xử lý thành ``tool_unavailable``."""

    completed = subprocess.run(  # noqa: S603  (argv tĩnh từ catalog; shell=False mặc định)
        list(argv),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout or "", completed.stderr or "")


# ---------------------------------------------------------------------------
# Khai báo adapter read-only
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ReadOnlyAdapter:
    """Một adapter đọc-trạng-thái. ``command`` là argv TĨNH; ``parse`` thuần tuý
    (không I/O) biến stdout → dict; ``evidence_fields`` = khoá bằng chứng cho
    Outcome Validator."""

    tool: str
    summary_vi: str
    spec: ToolSpec
    command: tuple[str, ...]
    parse: Callable[[str], dict[str, object]]
    evidence_fields: tuple[str, ...] = ()
    timeout_s: int = 20


# ---------------------------------------------------------------------------
# PARSERS — thuần tuý, unit-test bằng fixture (SAI-040 phần "parse đúng")
# ---------------------------------------------------------------------------
def _split_terse(line: str) -> list[str]:
    """Tách một dòng ``nmcli -t`` (phân tách bằng ``:``; ``\\`` escape). Dùng
    bộ tách an toàn thay vì ``str.split`` để không vỡ khi giá trị chứa ``:``."""

    fields: list[str] = []
    buf: list[str] = []
    i = 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line):
            buf.append(line[i + 1])
            i += 2
            continue
        if c == ":":
            fields.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    fields.append("".join(buf))
    return fields


def parse_nmcli_devices(text: str) -> dict[str, object]:
    """Parse ``nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device``.

    Trả ``devices`` (bỏ ``loopback``), ``online`` (có thiết bị != loopback ở
    trạng thái ``connected``), ``device_count``."""

    devices: list[dict[str, str]] = []
    online = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = _split_terse(line)
        parts += [""] * (4 - len(parts))
        device, dtype, state, connection = parts[0], parts[1], parts[2], parts[3]
        if dtype == "loopback":
            continue
        devices.append(
            {"device": device, "type": dtype, "state": state, "connection": connection}
        )
        if state == "connected":
            online = True
    return {"devices": devices, "online": online, "device_count": len(devices)}


def parse_lpstat(text: str) -> dict[str, object]:
    """Parse ``lpstat -p -d`` → ``printers`` (name/state), ``default``, count."""

    printers: list[dict[str, str]] = []
    default: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("printer "):
            rest = line[len("printer ") :]
            name = rest.split(" ", 1)[0]
            state = "unknown"
            if " is " in rest:
                after = rest.split(" is ", 1)[1].strip()
                if after:
                    state = after.split(".", 1)[0].split()[0]
            printers.append({"name": name, "state": state})
        elif line.lower().startswith("system default destination:"):
            default = line.split(":", 1)[1].strip() or None
    return {"printers": printers, "default": default, "printer_count": len(printers)}


def parse_rfkill(text: str) -> dict[str, object]:
    """Parse ``rfkill list`` (block header + Soft/Hard blocked). Trả ``radios``
    + ``radio_count`` + ``any_blocked``."""

    header = re.compile(r"^(\d+):\s*([^:]+):\s*(.+)$")
    radios: list[dict[str, object]] = []
    cur: dict[str, object] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith("soft blocked:"):
            if cur is not None:
                cur["soft_blocked"] = line.split(":", 1)[1].strip().lower() == "yes"
            continue
        if low.startswith("hard blocked:"):
            if cur is not None:
                cur["hard_blocked"] = line.split(":", 1)[1].strip().lower() == "yes"
            continue
        m = header.match(line)
        if m:
            if cur is not None:
                radios.append(cur)
            cur = {
                "id": int(m.group(1)),
                "name": m.group(2).strip(),
                "type": m.group(3).strip(),
                "soft_blocked": None,
                "hard_blocked": None,
            }
    if cur is not None:
        radios.append(cur)
    any_blocked = any(bool(r.get("soft_blocked")) or bool(r.get("hard_blocked")) for r in radios)
    return {"radios": radios, "radio_count": len(radios), "any_blocked": any_blocked}


def parse_bluetoothctl_show(text: str) -> dict[str, object]:
    """Parse ``bluetoothctl show`` (Controller <MAC> + Powered/Discoverable/
    Pairable). MAC bộ điều khiển được redact ở bước sau (``_redact_adapter_data``)."""

    data: dict[str, object] = {
        "controller": None,
        "powered": None,
        "discoverable": None,
        "pairable": None,
    }
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("Controller "):
            tokens = line.split()
            if len(tokens) >= 2:
                data["controller"] = tokens[1]
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key = key.strip().lower()
        val = value.strip().lower() == "yes"
        if key in ("powered", "discoverable", "pairable"):
            data[key] = val
    return data


# ---------------------------------------------------------------------------
# Redaction cho dữ liệu adapter (SAI-024) — pipeline chung + che MAC (parity bash)
# ---------------------------------------------------------------------------
_MAC_RE = re.compile(r"\b([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b")


def _mask_macs(obj: object) -> object:
    if isinstance(obj, str):
        return _MAC_RE.sub("[REDACTED-MAC]", obj)
    if isinstance(obj, Mapping):
        return {k: _mask_macs(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return type(obj)(_mask_macs(v) for v in obj)
    return obj


def _redact_adapter_data(data: dict[str, object]) -> dict[str, object]:
    """Che bí mật trước khi dữ liệu rời tiến trình: pipeline chung
    (``redact_bundle``: secret/PII dãy số) + che MAC (redaction.py không phủ MAC)."""

    redacted = _mask_macs(redact_bundle(data))
    assert isinstance(redacted, dict)
    return redacted


# ---------------------------------------------------------------------------
# DANH BẠ adapter read-only (KHÔNG trộn vào DEFAULT_TOOLS để giữ test M0 nguyên)
# ---------------------------------------------------------------------------
READONLY_ADAPTERS: tuple[ReadOnlyAdapter, ...] = (
    ReadOnlyAdapter(
        tool="network.diagnose",
        summary_vi="Đọc trạng thái mạng (thiết bị/loại/kết nối) — chỉ đọc.",
        spec=ToolSpec(name="network.diagnose", risk=RiskTier.R0),
        command=("nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"),
        parse=parse_nmcli_devices,
        evidence_fields=("online", "device_count"),
    ),
    ReadOnlyAdapter(
        tool="printer.status",
        summary_vi="Liệt kê máy in + trạng thái hàng đợi (CUPS) — chỉ đọc.",
        spec=ToolSpec(name="printer.status", risk=RiskTier.R0),
        command=("lpstat", "-p", "-d"),
        parse=parse_lpstat,
        evidence_fields=("printer_count", "default"),
    ),
    ReadOnlyAdapter(
        tool="radio.status",
        summary_vi="Đọc trạng thái sóng (Wi-Fi/Bluetooth soft/hard block) — chỉ đọc.",
        spec=ToolSpec(name="radio.status", risk=RiskTier.R0),
        command=("rfkill", "list"),
        parse=parse_rfkill,
        evidence_fields=("radio_count", "any_blocked"),
    ),
    ReadOnlyAdapter(
        tool="bluetooth.status",
        summary_vi="Đọc trạng thái bộ điều khiển Bluetooth (powered/pairable) — chỉ đọc.",
        spec=ToolSpec(name="bluetooth.status", risk=RiskTier.R0),
        command=("bluetoothctl", "show"),
        parse=parse_bluetoothctl_show,
        evidence_fields=("powered",),
    ),
)

#: Spec các adapter để nạp vào registry (chỉ read-only, writes=False).
ADAPTER_TOOLS: tuple[ToolSpec, ...] = tuple(a.spec for a in READONLY_ADAPTERS)

ADAPTERS_BY_NAME: dict[str, ReadOnlyAdapter] = {a.tool: a for a in READONLY_ADAPTERS}


def build_adapter_registry() -> ToolRegistry:
    """Registry = DEFAULT_TOOLS (M0) + ADAPTER_TOOLS (read-only thật). Giữ
    nguyên bộ M0 để test SAI-015 không đổi; chỉ bổ sung tool đọc trạng thái."""

    return ToolRegistry(specs=(*DEFAULT_TOOLS, *ADAPTER_TOOLS))


# ---------------------------------------------------------------------------
# Trace helper (SAI-034) — note đã redact khi ghi
# ---------------------------------------------------------------------------
def _record(
    trace: Trace | None,
    adapter: ReadOnlyAdapter,
    *,
    decision: str,
    result: str,
    error_class: TraceErrorClass,
    correlation_id: str | None,
    note: str,
) -> None:
    if trace is None:
        return
    trace.record(
        TraceEvent(
            event_id=f"adapter:{adapter.tool}",
            plan_id="smartai-adapter",
            action_id=adapter.tool,
            policy_decision=decision,
            tool=adapter.tool,
            result=result,
            error_class=error_class,
            correlation_id=correlation_id,
            note=note,
        )
    )


# ---------------------------------------------------------------------------
# run_adapter — đường ĐỌC THẬT đi qua broker, fail-closed từng bước
# ---------------------------------------------------------------------------
def run_adapter(
    adapter: ReadOnlyAdapter,
    *,
    registry: ToolRegistry | None = None,
    runner: Runner | None = None,
    trace: Trace | None = None,
    correlation_id: str | None = None,
    now: str | None = None,
) -> ToolResult:
    """Chạy một adapter đọc-trạng-thái QUA broker.

    Thứ tự fail-closed (mỗi bước hỏng trả ``ToolResult``, không raise, không bịa):
      0) read-only guard (writes/risk) — phòng thủ chiều sâu;
      1) policy.evaluate (SAI-039) — R0/R1 đọc → allow, KHÔNG cần consent;
      2) ToolRegistry.invoke (SAI-015/040) — tool đăng ký? tham số? scope?;
      3) lệnh khả dụng? (thiếu → ``tool_unavailable``, KHÔNG bịa dữ liệu);
      4) chạy đọc thật (argv tĩnh, timeout) — rc≠0/timeout → FAILED trung thực;
      5) PARSE → REDACT (SAI-024) → Trace (SAI-034) → SUCCESS + bằng chứng.
    """

    # Import cục bộ: evaluate/PolicyContext ở policy.py (tránh vòng import ở đỉnh).
    from namios_smartai._types import PolicyContext, PolicyEffect
    from namios_smartai.policy import evaluate

    registry = registry or build_adapter_registry()
    # Runner tiêm (test/pilot-harness) ⇒ caller tự lo "lệnh có thật"; bỏ qua
    # ``shutil.which`` (sandbox này không cài CLI). Runner mặc định (OS thật) thì
    # VẪN kiểm ``which`` để suy biến ``tool_unavailable`` trung thực.
    injected_runner = runner is not None
    runner = runner or _default_runner

    # 0) READ-ONLY GUARD — adapter ghi/đặc quyền KHÔNG được đi đường này.
    if adapter.spec.writes or adapter.spec.risk not in (RiskTier.R0, RiskTier.R1):
        msg = t("sai.adapter.not_readonly", lang=Lang.VI, tool=adapter.tool)
        _record(
            trace,
            adapter,
            decision="deny",
            result="blocked",
            error_class=TraceErrorClass.POLICY,
            correlation_id=correlation_id,
            note=msg,
        )
        return ToolResult(
            status=ToolResultStatus.BLOCKED,
            error_code=SaiErrorCode.E_SAI_TOOL_SCOPE.value,
            message_vi=msg,
        )

    # 1) POLICY GATE — read-only R0/R1 → allow (không consent/xác nhận).
    decision = evaluate(
        PolicyContext(action=adapter.tool, risk=adapter.spec.risk, now=now)
    )
    if decision.effect == PolicyEffect.DENY:
        _record(
            trace,
            adapter,
            decision="deny",
            result="blocked",
            error_class=TraceErrorClass.POLICY,
            correlation_id=correlation_id,
            note=decision.reason_vi,
        )
        return ToolResult(
            status=ToolResultStatus.BLOCKED,
            error_code=SaiErrorCode.E_SAI_POLICY_DENY.value,
            message_vi=decision.reason_vi,
        )

    # 2) BROKER VALIDATE (fail-closed): tool đăng ký? tham số? scope? (read-only
    #    → không cần capability). invoke M0 trả SUCCESS "mock" = ĐÃ QUA kiểm;
    #    adapter mới là nơi lấy dữ liệu THẬT.
    validation = registry.invoke(
        ToolCall(tool=adapter.tool, params={}, risk=adapter.spec.risk), now=now
    )
    if validation.status is not ToolResultStatus.SUCCESS:
        _record(
            trace,
            adapter,
            decision="deny",
            result="blocked",
            error_class=TraceErrorClass.TOOL,
            correlation_id=correlation_id,
            note=validation.message_vi,
        )
        return validation

    # 3) LỆNH KHẢ DỤNG? (sandbox này chưa cài CLI → tool_unavailable trung thực)
    if not injected_runner and shutil.which(adapter.command[0]) is None:
        return _unavailable(adapter, trace, correlation_id)

    # 4) CHẠY ĐỌC THẬT (argv tĩnh, timeout).
    try:
        output = runner(adapter.command, adapter.timeout_s)
    except FileNotFoundError:
        return _unavailable(adapter, trace, correlation_id)
    except subprocess.TimeoutExpired:
        msg = t(
            "sai.adapter.timeout", lang=Lang.VI, tool=adapter.tool, seconds=adapter.timeout_s
        )
        _record(
            trace,
            adapter,
            decision="allow",
            result="failed",
            error_class=TraceErrorClass.TOOL,
            correlation_id=correlation_id,
            note=msg,
        )
        return ToolResult(
            status=ToolResultStatus.FAILED,
            error_code=SaiErrorCode.E_SAI_TOOL_UNAVAILABLE.value,
            message_vi=msg,
            data={"tool_unavailable": False, "timeout": True, "command": adapter.command[0]},
        )

    if output.returncode != 0:
        detail = redact_bundle((output.stderr or "").strip()[:200]) or "(không có thông báo)"
        msg = t(
            "sai.adapter.failed",
            lang=Lang.VI,
            tool=adapter.tool,
            code=output.returncode,
            detail=detail,
        )
        _record(
            trace,
            adapter,
            decision="allow",
            result="failed",
            error_class=TraceErrorClass.TOOL,
            correlation_id=correlation_id,
            note=msg,
        )
        return ToolResult(
            status=ToolResultStatus.FAILED,
            error_code=SaiErrorCode.E_SAI_TOOL_UNAVAILABLE.value,
            message_vi=msg,
            data={"returncode": output.returncode},
        )

    # 5) PARSE → REDACT → Trace → SUCCESS (+ bằng chứng đã che).
    parsed = adapter.parse(output.stdout)
    redacted = _redact_adapter_data(parsed)
    evidence = {k: redacted.get(k) for k in adapter.evidence_fields}
    data: dict[str, object] = {"tool": adapter.tool, "mock": False, "evidence": evidence}
    data.update(redacted)
    _record(
        trace,
        adapter,
        decision="allow",
        result="success",
        error_class=TraceErrorClass.NONE,
        correlation_id=correlation_id,
        note=f"read-only ok; evidence={sorted(evidence)}",
    )
    return ToolResult(
        status=ToolResultStatus.SUCCESS,
        message_vi=t("sai.adapter.ok", lang=Lang.VI, tool=adapter.tool),
        data=data,
    )


def _unavailable(
    adapter: ReadOnlyAdapter, trace: Trace | None, correlation_id: str | None
) -> ToolResult:
    """Đường suy biến TRUNG THỰC khi CLI không có trên máy (SAI-040; ADR-0021):
    KHÔNG bịa dữ liệu, không coi là policy-deny — chỉ báo thiếu công cụ."""

    msg = t("sai.adapter.unavailable", lang=Lang.VI, tool=adapter.tool, command=adapter.command[0])
    _record(
        trace,
        adapter,
        decision="allow",
        result="failed",
        error_class=TraceErrorClass.TOOL,
        correlation_id=correlation_id,
        note=msg,
    )
    return ToolResult(
        status=ToolResultStatus.FAILED,
        error_code=SaiErrorCode.E_SAI_TOOL_UNAVAILABLE.value,
        message_vi=msg,
        data={"tool_unavailable": True, "command": adapter.command[0]},
    )
