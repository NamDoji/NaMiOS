"""Office Route Matrix (ODC-008) — chọn tuyến xử lý tài liệu, TÁCH 4 trục trung thực.

"Mở được" ≠ "sửa đúng" ≠ "in đúng" ≠ "chạy macro". Bất biến (nghiệm thu ODC-008/
015/017, test T02/T05): file cần macro/COM/add-in KHÔNG bao giờ gán ``BUNDLED_OFFICE``
hay ``OFFICIAL_WEB`` với nhãn tương thích-đầy-đủ (VBA không chạy trên web; engine
cài sẵn không chạy VBA); ``macro_capable`` chỉ True trên Windows có phép. File nhạy
cảm → tuyến web cần xác nhận rõ, KHÔNG tự upload. ``edit/print_faithful`` của engine
cài sẵn chỉ True khi ĐÃ đo fidelity (thiếu đo → False = "mở được nhưng chưa chứng minh").

TÁI DÙNG ``namios_pra.OfficeNeed`` + gate fidelity; không fork.
"""

from __future__ import annotations

from namios_i18n import Lang, t
from namios_odc import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_odc._types import (
    DocRouteResult,
    DocumentMetadata,
    OfficeMode,
    OfficeNeed,
)

__all__ = ["needs_macro", "resolve_document_route"]

#: Định dạng có macro nhúng (ODC-007) — luôn coi là có nhu cầu macro tiềm năng.
_MACRO_FORMATS = frozenset({"xlsm", "docm"})


def needs_macro(metadata: DocumentMetadata) -> bool:
    """Workflow có cần chạy macro/COM/add-in không (ODC-015). Suy từ nhu cầu KÈM
    dấu hiệu file — file .xlsm/.docm hoặc có macro nhúng tính là có."""

    if metadata.needs & {OfficeNeed.MACRO, OfficeNeed.ADDIN}:
        return True
    return metadata.has_macros or metadata.doc_format.value in _MACRO_FORMATS


def _r(key: str, **kw: object) -> str:
    return t(key, lang=Lang.VI, **kw)


def resolve_document_route(
    metadata: DocumentMetadata,
    *,
    bundled_supported: bool = True,
    bundled_fidelity_verified: bool = False,
    web_available: bool = False,
    windows_vm_available: bool = False,
    windows_remote_available: bool = False,
    wine_tested: bool = False,
) -> DocRouteResult:
    """Chọn tuyến (ODC-008). ``bundled_fidelity_verified`` = ĐÃ đo độ-đúng cho định
    dạng này trên engine cài sẵn (thiếu → không dám nhận sửa/in đúng)."""

    needs = metadata.needs
    wants_macro = needs_macro(metadata)
    read_only = bool(needs) and needs <= {OfficeNeed.READ}
    wants_edit = OfficeNeed.EDIT in needs
    sensitive = metadata.sensitivity.value == "sensitive"

    # 1) Cần CHẠY macro → chỉ Windows có phép mới macro_capable; wine chỉ THỬ (không
    #    nhận macro pass); engine cài sẵn/web KHÔNG được gán macro-đầy-đủ.
    if wants_macro:
        if windows_vm_available:
            return DocRouteResult(
                mode=OfficeMode.LICENSED_WINDOWS_VM,
                openable=True,
                edit_faithful=True,
                print_faithful=True,
                macro_capable=True,
                windows_dependent=True,
                reasons_vi=(_r("odc.route.macro_windows"),),
            )
        if windows_remote_available:
            return DocRouteResult(
                mode=OfficeMode.LICENSED_WINDOWS_REMOTE,
                openable=True,
                edit_faithful=True,
                print_faithful=True,
                macro_capable=True,
                windows_dependent=True,
                reasons_vi=(_r("odc.route.macro_windows"),),
            )
        if wine_tested:
            # Wine = tuyến THỬ theo đúng bản; KHÔNG nhận macro pass (fail-closed).
            return DocRouteResult(
                mode=OfficeMode.TESTED_WINE,
                openable=True,
                edit_faithful=False,
                print_faithful=False,
                macro_capable=False,
                reasons_vi=(_r("odc.route.wine_experimental"), _r("odc.route.macro_unverified")),
            )
        # Không có Windows → phần macro BỊ CHẶN; vẫn mở xem được bản gốc.
        return DocRouteResult(
            mode=OfficeMode.BLOCKED,
            openable=True,
            edit_faithful=False,
            print_faithful=False,
            macro_capable=False,
            reasons_vi=(_r("odc.route.macro_blocked"),),
        )

    # 2) Chỉ XEM → engine cài sẵn (nếu có) hoặc trình xem read-only.
    if read_only:
        if bundled_supported:
            return DocRouteResult(
                mode=OfficeMode.BUNDLED_OFFICE,
                openable=True,
                edit_faithful=False,
                print_faithful=bundled_fidelity_verified,
                macro_capable=False,
                reasons_vi=(_r("odc.route.bundled_view"),),
            )
        return DocRouteResult(
            mode=OfficeMode.READ_ONLY_VIEWER,
            openable=True,
            edit_faithful=False,
            print_faithful=False,
            macro_capable=False,
            reasons_vi=(_r("odc.route.viewer"),),
        )

    # 3) SỬA (không macro) → ưu tiên engine cài sẵn; thiếu → web chính thức (file
    #    nhạy cảm cần xác nhận, không tự upload); thiếu nữa → chặn/viewer.
    if wants_edit or needs:
        if bundled_supported:
            return DocRouteResult(
                mode=OfficeMode.BUNDLED_OFFICE,
                openable=True,
                edit_faithful=bundled_fidelity_verified,
                print_faithful=bundled_fidelity_verified,
                macro_capable=False,
                reasons_vi=(
                    (_r("odc.route.bundled_edit"),)
                    if bundled_fidelity_verified
                    else (_r("odc.route.bundled_edit_unverified"),)
                ),
            )
        if web_available:
            return DocRouteResult(
                mode=OfficeMode.OFFICIAL_WEB,
                openable=True,
                edit_faithful=True,  # engine chính thức
                print_faithful=True,
                macro_capable=False,  # VBA không chạy trên web (ODC-015)
                needs_explicit_consent=sensitive,
                auto_upload=False,
                reasons_vi=(
                    (_r("odc.route.web_sensitive"),) if sensitive else (_r("odc.route.web"),)
                ),
            )
        return DocRouteResult(
            mode=OfficeMode.BLOCKED,
            openable=True,
            edit_faithful=False,
            print_faithful=False,
            macro_capable=False,
            reasons_vi=(_r("odc.route.no_edit_route"),),
        )

    # 4) Không nêu nhu cầu → mặc định xem được (fail-closed, không nhận sửa/in đúng).
    return DocRouteResult(
        mode=OfficeMode.READ_ONLY_VIEWER if not bundled_supported else OfficeMode.BUNDLED_OFFICE,
        openable=True,
        edit_faithful=False,
        print_faithful=False,
        macro_capable=False,
        reasons_vi=(_r("odc.route.viewer"),),
    )
