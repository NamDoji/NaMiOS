"""SmartAI Doctor theo vùng — chẩn đoán có cấu trúc, trung thực (PRA-028..031).

Bốn "bác sĩ" biến dấu hiệu QUAN SÁT được thành kết luận TẤT ĐỊNH + việc-cần-làm
+ ai-xử-lý, KHÔNG gom mọi lỗi về một câu chung và KHÔNG tự nhận đã sửa:

- **Device Doctor** (PRA-028): 5 fixture (offline / hết giấy / kẹt / VLAN chặn
  mDNS / thiếu backend scan) → 5 kết luận KHÁC nhau; chức năng chưa có (copy) ≠
  "hỏng".
- **Network Doctor** (PRA-029): phân biệt SSID/mật khẩu/IP/portal/DNS/proxy-VPN/
  Internet/máy-in-khác-mạng — mỗi lỗi một việc-cần-làm RIÊNG (không "khởi động lại
  router" cho tất cả).
- **Office Doctor** (PRA-030): TÁI DÙNG ``office_route`` — macro/add-in không bao
  giờ ra web; file nhạy cảm KHÔNG tự upload (cần xác nhận rõ).
- **Windows App Doctor** (PRA-031): giả thuyết CÓ GIỚI HẠN (bắt buộc rollback),
  GUI mở nhưng DB mất → chỉ ``partial_workflow``; token OK mà cổng khóa-Windows →
  vẫn BLOCKED; thử N lần không đạt → DỪNG (không lặp vô hạn).
"""

from __future__ import annotations

from collections.abc import Iterable

from namios_i18n import Lang, t
from namios_pra import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_pra._types import (
    DeviceCapability,
    DeviceFault,
    DeviceFunction,
    DeviceFunctionStatus,
    DeviceSignals,
    Diagnosis,
    Hypothesis,
    NetworkFault,
    NetworkSignals,
    OfficeNeed,
    OfficePreflight,
    OfficeRoute,
    ResolverRole,
)
from namios_pra.device_hub import function_status
from namios_pra.office_route import resolve_office_route
from namios_smartai._types import ErrorCategory

__all__ = [
    "diagnose_device",
    "diagnose_network",
    "office_preflight",
    "bounded_hypotheses",
    "app_workflow_status",
    "next_after_attempts",
]


def _dx(
    domain: str, fault: str, resolver: ResolverRole, *, blocker: bool, terminal: bool = False
) -> Diagnosis:
    """Dựng Diagnosis với cặp i18n key ``<prefix>.<fault>.cause/.next`` theo domain."""

    prefix = {"device": "pra.dev", "network": "pra.net"}[domain]
    return Diagnosis(
        domain=domain,
        fault=fault,
        cause_vi=t(f"{prefix}.{fault}.cause", lang=Lang.VI),
        next_step_vi=t(f"{prefix}.{fault}.next", lang=Lang.VI),
        resolver=resolver,
        is_blocker=blocker,
        is_terminal=terminal,
    )


# --------------------------------------------------------------------------- #
# PRA-028 — Device Doctor                                                       #
# --------------------------------------------------------------------------- #


def diagnose_device(
    signals: DeviceSignals,
    *,
    capability: DeviceCapability | None = None,
) -> Diagnosis:
    """Chẩn vì sao chức năng ``signals.requested`` lỗi (PRA-028). TẤT ĐỊNH, mỗi
    fixture một kết luận. Thứ tự: tình trạng không-sửa-được-tại-chỗ trước (offline/
    chức-năng-không-có/khám-phá), rồi lỗi tiêu hao (giấy/kẹt)."""

    func = signals.requested

    # Máy không phản hồi: nguyên nhân gốc, chẩn sâu hơn vô nghĩa.
    if not signals.reachable:
        return _dx("device", DeviceFault.OFFLINE.value, ResolverRole.USER, blocker=False)

    # Copy là chức năng ĐỘC LẬP: NaMiOS không điều khiển nút copy trên máy; nếu
    # chưa kiểm/không có → FUNCTION_ABSENT, KHÔNG kết luận "hỏng" (PRA-001/028).
    if func is DeviceFunction.COPY:
        status = (
            function_status(capability, DeviceFunction.COPY)
            if capability is not None
            else DeviceFunctionStatus.UNTESTED
        )
        if status is not DeviceFunctionStatus.WORKS:
            return Diagnosis(
                domain="device",
                fault=DeviceFault.FUNCTION_ABSENT.value,
                cause_vi=t("pra.dev.function_absent.cause", lang=Lang.VI, func=func.value),
                next_step_vi=t("pra.dev.function_absent.next", lang=Lang.VI),
                resolver=ResolverRole.USER,
                is_blocker=False,
            )

    # Scan nhưng thiếu backend (eSCL/SANE): in vẫn chạy → lỗi riêng của scan.
    if func is DeviceFunction.SCAN and not signals.scan_backend_present:
        return _dx(
            "device", DeviceFault.SCAN_BACKEND_MISSING.value, ResolverRole.VENDOR, blocker=True
        )

    # Có trên mạng nhưng VLAN/firewall chặn mDNS → không tự khám phá (cần IT).
    if signals.on_same_subnet and not signals.mdns_visible:
        return _dx("device", DeviceFault.MDNS_BLOCKED.value, ResolverRole.IT, blocker=True)

    # Lỗi tiêu hao khi in.
    if func is DeviceFunction.PRINT and not signals.paper_ok:
        return _dx("device", DeviceFault.OUT_OF_PAPER.value, ResolverRole.USER, blocker=False)

    if signals.media_jam:
        return _dx("device", DeviceFault.JOB_JAMMED.value, ResolverRole.USER, blocker=False)

    return _dx("device", DeviceFault.HEALTHY.value, ResolverRole.USER, blocker=False)


# --------------------------------------------------------------------------- #
# PRA-029 — Network Doctor                                                      #
# --------------------------------------------------------------------------- #


def diagnose_network(signals: NetworkSignals) -> Diagnosis:
    """Phân biệt lỗi mạng (PRA-029). Mỗi fault có việc-cần-làm RIÊNG; không trả
    'khởi động lại router' cho mọi trường hợp. Chỉ dùng trạng thái kết nối —
    KHÔNG đọc nội dung truy cập."""

    if not signals.ssid_visible:
        return _dx("network", NetworkFault.SSID_NOT_FOUND.value, ResolverRole.USER, blocker=False)

    if not signals.auth_ok:
        return _dx("network", NetworkFault.WRONG_PASSWORD.value, ResolverRole.USER, blocker=False)

    if not signals.has_ip:
        return _dx("network", NetworkFault.NO_IP.value, ResolverRole.IT, blocker=True)

    if signals.captive_portal:
        return _dx("network", NetworkFault.CAPTIVE_PORTAL.value, ResolverRole.USER, blocker=False)

    if not signals.dns_ok:
        return _dx("network", NetworkFault.DNS_ERROR.value, ResolverRole.IT, blocker=True)

    if signals.proxy_required and not signals.proxy_ok:
        return _dx("network", NetworkFault.PROXY_VPN.value, ResolverRole.IT, blocker=True)

    if not signals.internet_ok:
        return _dx("network", NetworkFault.NO_INTERNET.value, ResolverRole.IT, blocker=True)

    if signals.checking_printer and not signals.printer_same_subnet:
        return _dx(
            "network", NetworkFault.PRINTER_OFF_NETWORK.value, ResolverRole.USER, blocker=False
        )

    return _dx("network", NetworkFault.HEALTHY.value, ResolverRole.USER, blocker=False)


# --------------------------------------------------------------------------- #
# PRA-030 — Office Doctor                                                       #
# --------------------------------------------------------------------------- #


def office_preflight(
    needs: Iterable[OfficeNeed],
    *,
    has_native_support: bool = True,
    web_available: bool = False,
    file_has_sensitive_data: bool = False,
) -> OfficePreflight:
    """Preflight Office (PRA-030): chọn tuyến + nêu hậu quả TRƯỚC khi mở web/app
    thay thế. Bất biến: macro/add-in không bao giờ gán web (VBA không chạy web);
    file nhạy cảm KHÔNG tự upload — cần xác nhận rõ. ``auto_upload`` luôn False."""

    need_set = frozenset(needs)
    res = resolve_office_route(
        need_set, has_native_support=has_native_support, web_available=web_available
    )

    warnings: list[str] = []
    needs_consent = False

    if need_set & {OfficeNeed.MACRO, OfficeNeed.ADDIN}:
        warnings.append(t("pra.officedoc.macro_web_blocked", lang=Lang.VI))

    if res.route is OfficeRoute.MS365_WEB and file_has_sensitive_data:
        warnings.append(t("pra.officedoc.sensitive_no_upload", lang=Lang.VI))
        needs_consent = True

    if res.windows_dependent:
        warnings.append(t("pra.officedoc.windows_dep", lang=Lang.VI))

    return OfficePreflight(
        route=res.route,
        windows_dependent=res.windows_dependent,
        warnings_vi=tuple(warnings),
        needs_explicit_consent=needs_consent,
        auto_upload=False,
    )


# --------------------------------------------------------------------------- #
# PRA-031 — Windows App Doctor                                                  #
# --------------------------------------------------------------------------- #


def bounded_hypotheses(
    candidates: Iterable[Hypothesis],
    *,
    max_n: int,
) -> tuple[Hypothesis, ...]:
    """Lọc + giới hạn giả thuyết sửa lỗi (PRA-031). BỎ giả thuyết thiếu rollback
    (không được áp dụng); trả tối đa ``max_n`` (``max_n<=0`` → rỗng)."""

    if max_n <= 0:
        return ()
    valid = [h for h in candidates if h.rollback_vi.strip() and h.test_vi.strip()]
    return tuple(valid[:max_n])


def app_workflow_status(
    *,
    launched: bool,
    triage_category: ErrorCategory,
) -> Diagnosis:
    """Kết luận workflow app Windows TRUNG THỰC (PRA-031). GUI mở ≠ dùng được:
    DB mất → ``partial_workflow`` (không cho sửa dữ liệu thật); cổng khóa-Windows
    → BLOCKED dù token nhận được."""

    if triage_category is ErrorCategory.DB_UNREACHABLE:
        return Diagnosis(
            domain="windows_app",
            fault="partial_workflow",
            cause_vi=t("pra.appdoc.partial_db", lang=Lang.VI),
            next_step_vi=t("pra.appdoc.partial_db.next", lang=Lang.VI),
            resolver=ResolverRole.IT,
            is_blocker=True,
        )

    if triage_category is ErrorCategory.PORTAL_PLUGIN:
        return Diagnosis(
            domain="windows_app",
            fault="portal_blocker",
            cause_vi=t("pra.appdoc.portal_blocker", lang=Lang.VI),
            next_step_vi=t("pra.appdoc.portal_blocker.next", lang=Lang.VI),
            resolver=ResolverRole.VENDOR,
            is_blocker=True,
        )

    # Mặc định: app mở được nhưng chưa đủ bằng chứng workflow → chưa kết luận "dùng
    # được" (fail-closed). Chạy được ≠ hoàn thành.
    return Diagnosis(
        domain="windows_app",
        fault="launched_only" if launched else "unknown",
        cause_vi=t("pra.dev.unknown.cause", lang=Lang.VI),
        next_step_vi=t("pra.dev.unknown.next", lang=Lang.VI),
        resolver=ResolverRole.USER,
        is_blocker=not launched,
    )


def next_after_attempts(
    *,
    failed_count: int,
    max_attempts: int,
) -> Diagnosis | None:
    """Sau mỗi phép thử (PRA-031): đã thử ``failed_count`` lần thất bại trên
    ``max_attempts`` cho phép → DỪNG trung thực (terminal blocker), không lặp vô
    hạn. Chưa tới hạn → trả ``None`` (được thử tiếp)."""

    if max_attempts <= 0 or failed_count >= max_attempts:
        return Diagnosis(
            domain="windows_app",
            fault="terminal_blocker",
            cause_vi=t("pra.appdoc.terminal", lang=Lang.VI, n=failed_count, max=max_attempts),
            next_step_vi=t("pra.appdoc.terminal.next", lang=Lang.VI),
            resolver=ResolverRole.IT,
            is_blocker=True,
            is_terminal=True,
        )
    return None
