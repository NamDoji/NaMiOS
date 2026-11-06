"""Adversarial QA — bẻ gãy các cổng trung thực D0 của ``namios_pra`` (Phụ lục 06).

Mục tiêu: PHÁ các bất biến trung thực PRA-001/016/017/022/023/032. Không sửa
``src/``. Một file test duy nhất, assert chuẩn, không mạng/không sleep.

Phát hiện (ĐÃ VÁ): 1 lỗ hổng trung thực THẬT ở ``dotnet_classify`` — trait gắn-Windows
(``com``/``webview2``) trước đây chỉ khớp chính xác chữ-thường-đã-trim; biến thể hoa/
khoảng-trắng (``"COM"``, ``" com "``, ``"WebView2"``) LỌT qua, bị coi là lành → route
``NATIVE_LINUX`` thay vì hạ ``WINE`` = over-claim mà PRA-023 (E_PRA_DOTNET_OVERCLAIM)
phải chặn. Đã vá bằng ``_norm_traits`` (``.strip().lower()``, cùng hợp đồng
``progress.py``); test case/khoảng-trắng giờ là REGRESSION GUARD (pass, không còn xfail).
"""

from __future__ import annotations

import itertools

from namios_pra import (
    DeviceCapability,
    DeviceFunction,
    DeviceFunctionStatus,
    DotnetKind,
    DotnetRoute,
    FidelityIssue,
    FidelitySeverity,
    OfficeNeed,
    OfficeRoute,
    PrintStage,
    SignSubmitStage,
    can_copy,
    classify_dotnet,
    fidelity_gate,
    function_status,
    is_fidelity_blocked,
    is_supported,
    print_received,
    print_stage_from_cups,
    resolve_office_route,
    sign_submitted_done,
)

F = DeviceFunction
S = DeviceFunctionStatus
N = OfficeNeed
OR = OfficeRoute
K = DotnetKind
R = DotnetRoute
P = PrintStage
SS = SignSubmitStage
Sev = FidelitySeverity


def _cap(**funcs: DeviceFunctionStatus) -> DeviceCapability:
    return DeviceCapability(
        device_id="dev", model="MFP-X", functions={F[k.upper()]: v for k, v in funcs.items()}
    )


# ---------------------------------------------------------------------------
# D1 — Device Hub (PRA-001): "in được + scan được" KHÔNG suy ra "copy được".
# ---------------------------------------------------------------------------


def test_d1_can_copy_only_when_copy_works() -> None:
    # copy=WORKS là trường hợp DUY NHẤT True.
    assert can_copy(_cap(copy=S.WORKS)) is True
    # Mọi mức copy khác → False.
    for st in (S.UNTESTED, S.PARTIAL, S.BLOCKED):
        assert can_copy(_cap(copy=st)) is False, st
    # copy không khai (absent) → False.
    assert can_copy(_cap()) is False


def test_d1_print_scan_works_never_implies_copy() -> None:
    # Nghiệm thu lõi: in+scan WORKS mà copy vắng/partial/blocked/untested → KHÔNG copy.
    for copy_variant in (dict(), dict(copy=S.UNTESTED), dict(copy=S.PARTIAL), dict(copy=S.BLOCKED)):
        cap = _cap(print=S.WORKS, scan=S.WORKS, **copy_variant)
        assert is_supported(cap, F.PRINT) is True
        assert is_supported(cap, F.SCAN) is True
        assert can_copy(cap) is False, copy_variant


def test_d1_is_supported_true_only_for_works() -> None:
    for st in (S.UNTESTED, S.WORKS, S.PARTIAL, S.BLOCKED):
        cap = _cap(print=st)
        assert is_supported(cap, F.PRINT) is (st is S.WORKS), st


def test_d1_fax_and_unknown_default_untested() -> None:
    # fax không khai + máy chỉ in/scan → fax UNTESTED, không hỗ trợ.
    cap = _cap(print=S.WORKS, scan=S.WORKS)
    assert function_status(cap, F.FAX) is S.UNTESTED
    assert is_supported(cap, F.FAX) is False
    # functions rỗng → mọi chức năng UNTESTED, không gì được hỗ trợ.
    empty = DeviceCapability(device_id="d", model="m")
    for f in DeviceFunction:
        assert function_status(empty, f) is S.UNTESTED
        assert is_supported(empty, f) is False
    assert can_copy(empty) is False


def test_d1_copy_works_but_print_scan_blocked_still_copies() -> None:
    # Độc lập theo chiều ngược: copy WORKS vẫn copy được dù in/scan hỏng.
    cap = _cap(print=S.BLOCKED, scan=S.BLOCKED, copy=S.WORKS)
    assert can_copy(cap) is True
    assert is_supported(cap, F.PRINT) is False
    assert is_supported(cap, F.SCAN) is False


# ---------------------------------------------------------------------------
# O1 — Office route (PRA-016): MACRO/ADDIN không bao giờ ra web; SIGN windows-dep.
# ---------------------------------------------------------------------------

_FLAG_COMBOS = list(itertools.product((True, False), (True, False)))  # (native, web)


def test_o1_macro_or_addin_never_web_any_flags() -> None:
    # Dù has_native_support/web_available bật-tắt kiểu gì, có MACRO|ADDIN → KHÔNG web.
    need_sets = [
        [N.MACRO],
        [N.ADDIN],
        [N.EDIT, N.MACRO, N.READ],
        [N.ADDIN, N.EDIT],
        [N.MACRO, N.COLLABORATE],
        [N.MACRO, N.ADDIN, N.READ, N.PRINT],
    ]
    for needs in need_sets:
        for native, web in _FLAG_COMBOS:
            res = resolve_office_route(needs, has_native_support=native, web_available=web)
            assert res.route is not OR.MS365_WEB, (needs, native, web)
            assert res.route is OR.WINDOWS_VM, (needs, native, web)
            assert res.windows_dependent is True, (needs, native, web)
            # Không được rơi về native dù native=True.
            assert res.route is not OR.NATIVE_LINUX, (needs, native, web)


def test_o1_sign_is_windows_dependent_not_web_or_native() -> None:
    # SIGN (kèm/không kèm read) → windows-dependent, không web, không native-for-sign.
    for needs in ([N.SIGN], [N.SIGN, N.READ], [N.SIGN, N.PRINT], [N.SIGN, N.EDIT]):
        for native, web in _FLAG_COMBOS:
            res = resolve_office_route(needs, has_native_support=native, web_available=web)
            assert res.windows_dependent is True, (needs, native, web)
            assert res.route not in (OR.MS365_WEB, OR.NATIVE_LINUX, OR.VIEWER_READONLY), (
                needs,
                res.route,
            )


def test_o1_macro_beats_sign_and_all_else() -> None:
    # Kết hợp mọi nhu cầu + web_available: vẫn Windows VM, không web.
    res = resolve_office_route(
        [N.MACRO, N.SIGN, N.EDIT, N.COLLABORATE, N.READ],
        has_native_support=True,
        web_available=True,
    )
    assert res.route is OR.WINDOWS_VM
    assert res.windows_dependent is True


def test_o1_benign_edit_may_use_web_only_when_no_native() -> None:
    # Kiểm soát-âm: KHÔNG macro/addin + không native + web có → web hợp lệ.
    res = resolve_office_route([N.EDIT], has_native_support=False, web_available=True)
    assert res.route is OR.MS365_WEB
    # Nhưng chỉ cần thêm MACRO là web biến mất ngay.
    res2 = resolve_office_route([N.EDIT, N.MACRO], has_native_support=False, web_available=True)
    assert res2.route is OR.WINDOWS_VM


# ---------------------------------------------------------------------------
# O2 — Fidelity gate (PRA-017): bất kỳ BLOCKING → chặn, bất kể thứ tự/số lượng.
# ---------------------------------------------------------------------------


def _issue(sev: FidelitySeverity, field: str = "x") -> FidelityIssue:
    return FidelityIssue(field=field, severity=sev, detail_vi="d")


def test_o2_any_blocking_blocks_regardless_of_order_and_count() -> None:
    cases = [
        [_issue(Sev.BLOCKING)],
        [_issue(Sev.INFO), _issue(Sev.BLOCKING)],
        [_issue(Sev.BLOCKING), _issue(Sev.INFO)],
        [_issue(Sev.INFO), _issue(Sev.INFO), _issue(Sev.BLOCKING), _issue(Sev.INFO)],
        [_issue(Sev.BLOCKING, "amount"), _issue(Sev.BLOCKING, "pages")],
    ]
    for issues in cases:
        assert is_fidelity_blocked(issues) is True, issues
        ok, _reason = fidelity_gate(issues)
        assert ok is False, issues


def test_o2_info_only_or_empty_passes() -> None:
    for issues in ([], [_issue(Sev.INFO)], [_issue(Sev.INFO), _issue(Sev.INFO, "font")]):
        assert is_fidelity_blocked(issues) is False, issues
        ok, _reason = fidelity_gate(issues)
        assert ok is True, issues


def test_o2_gate_and_predicate_are_consistent() -> None:
    for issues in (
        [],
        [_issue(Sev.INFO)],
        [_issue(Sev.BLOCKING)],
        [_issue(Sev.INFO), _issue(Sev.BLOCKING)],
    ):
        ok, _ = fidelity_gate(issues)
        assert ok is (not is_fidelity_blocked(issues)), issues


# ---------------------------------------------------------------------------
# N1 — .NET classify (PRA-022/023): WPF/WinUI/WinForms/legacy → WINDOWS_ONLY;
#      unknown → UNKNOWN; cross-platform native trừ khi có trait gắn-Windows.
# ---------------------------------------------------------------------------

_TRAIT_SETS_FOR_WINDOWS_ONLY = [
    (),
    ("pinvoke",),
    ("vcpp",),
    ("com",),  # ngay cả trait gắn-Windows cũng KHÔNG hạ xuống native.
    ("webview2", "com"),
    ("none",),
]


def test_n1_windows_only_kinds_never_native_regardless_of_traits() -> None:
    for kind in (K.WPF, K.WINUI, K.WINFORMS, K.FRAMEWORK_LEGACY):
        for traits in _TRAIT_SETS_FOR_WINDOWS_ONLY:
            c = classify_dotnet(kind, traits=traits)
            assert c.route is R.WINDOWS_ONLY, (kind, traits)
            assert c.route is not R.NATIVE_LINUX, (kind, traits)


def test_n1_unknown_kind_is_unknown_route_never_native() -> None:
    for traits in ((), ("com",), ("pinvoke",), ("webview2",)):
        c = classify_dotnet(K.UNKNOWN, traits=traits)
        assert c.route is R.UNKNOWN, traits
        assert c.route is not R.NATIVE_LINUX, traits


def test_n1_cross_platform_benign_traits_go_native() -> None:
    for kind in (K.MODERN, K.CONSOLE, K.ASPNET):
        for traits in ((), ("pinvoke",), ("vcpp",), ("none",), ("pinvoke", "vcpp")):
            c = classify_dotnet(kind, traits=traits)
            assert c.route is R.NATIVE_LINUX, (kind, traits)


def test_n1_cross_platform_windows_trait_downgrades_to_wine() -> None:
    for kind in (K.MODERN, K.CONSOLE, K.ASPNET):
        for traits in (("com",), ("webview2",), ("com", "webview2"), ("pinvoke", "com")):
            c = classify_dotnet(kind, traits=traits)
            assert c.route is R.WINE, (kind, traits)
            assert c.route is not R.NATIVE_LINUX, (kind, traits)


def test_n1_windows_trait_case_whitespace_variants_should_downgrade_to_wine() -> None:
    # REGRESSION (N1/PRA-023 — lỗ hổng ĐÃ VÁ): trait gắn-Windows trước đây chỉ khớp
    # 'com'/'webview2' chữ-thường-đã-trim; biến thể hoa/khoảng-trắng LỌT khỏi phép
    # giao tập → MODERN/CONSOLE/ASPNET bị route NATIVE_LINUX thay vì WINE (over-claim
    # native, E_PRA_DOTNET_OVERCLAIM). Vá: dotnet_classify._norm_traits chuẩn-hoá
    # .strip().lower() (cùng hợp đồng progress.py). Kỳ vọng TRUNG THỰC: mọi biến thể
    # của trait gắn-Windows đều phải hạ WINE (fail-closed), KHÔNG nâng NATIVE_LINUX.
    for kind in (K.MODERN, K.CONSOLE, K.ASPNET):
        for variant in ("COM", " com ", "Com", "WebView2", " webview2 ", "\tCOM\n"):
            c = classify_dotnet(kind, traits=(variant,))
            assert c.route is R.WINE, (kind, variant)
            assert c.route is not R.NATIVE_LINUX, (kind, variant)


# ---------------------------------------------------------------------------
# P1 — Progress (PRA-032): "đã nhận bản in"=USER_CONFIRMED; CUPS completed=
#      MACHINE_DONE; nộp xong = RECEIPT_VERIFIED. Không bao giờ over-claim.
# ---------------------------------------------------------------------------


def test_p1_print_received_only_user_confirmed() -> None:
    for stage in PrintStage:
        assert print_received(stage) is (stage is P.USER_CONFIRMED), stage


def test_p1_cups_completed_is_machine_done_not_received() -> None:
    stage = print_stage_from_cups("completed")
    assert stage is P.MACHINE_DONE
    assert stage is not P.USER_CONFIRMED
    assert print_received(stage) is False


def test_p1_cups_case_whitespace_normalized_but_still_not_received() -> None:
    # Chuẩn-hoá hoa/khoảng-trắng của trạng thái ĐÃ-BIẾT là CHẤP NHẬN ĐƯỢC vì nó
    # KHÔNG over-claim nhận-bản-in: 'completed' → MACHINE_DONE (không hơn).
    for raw in ("COMPLETED", " completed ", "Completed", "\tcompleted\n"):
        stage = print_stage_from_cups(raw)
        assert stage is P.MACHINE_DONE, raw
        assert print_received(stage) is False, raw


def test_p1_unknown_empty_none_whitespace_cups_is_unknown() -> None:
    for raw in ("", "   ", "\t", None, "done", "ok", "success", "finished", "100%"):
        stage = print_stage_from_cups(raw)  # type: ignore[arg-type]
        assert stage is P.UNKNOWN, raw
        assert print_received(stage) is False, raw


def test_p1_no_cups_string_ever_yields_user_confirmed() -> None:
    # USER_CONFIRMED chỉ đến từ hành động người dùng — KHÔNG map nào từ CUPS cho ra.
    candidates = [
        "completed",
        "COMPLETED",
        " completed ",
        "processing",
        "printing",
        "queued",
        "pending",
        "held",
        "canceled",
        "cancelled",
        "aborted",
        "stopped",
        "",
        "   ",
        None,
        "user_confirmed",
        "received",
        "done",
    ]
    for raw in candidates:
        assert print_stage_from_cups(raw) is not P.USER_CONFIRMED, raw  # type: ignore[arg-type]


def test_p1_sign_submitted_done_only_receipt_verified() -> None:
    for stage in SignSubmitStage:
        assert sign_submitted_done(stage) is (stage is SS.RECEIPT_VERIFIED), stage
    # Nhấn mạnh các mốc sớm KHÔNG phải "đã nộp xong".
    assert sign_submitted_done(SS.SIGNED) is False
    assert sign_submitted_done(SS.SUBMITTED) is False
