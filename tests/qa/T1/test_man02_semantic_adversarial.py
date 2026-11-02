"""T1 (tester độc lập) — MAN-02: tấn công tầng 2 (semantic) của WP2.

Mục tiêu: "schema pass" không được là "install-ready" khi còn TBD/runner
chưa pin/dependency chưa duyệt/revoked/task_verified thiếu evidence — và
đặc biệt dò các GÓC bị bỏ sót trong ``_semantic.py`` (ví dụ: revoked không
override các cờ khác, exact-match dependency không có khoan nhượng
case/whitespace, hỗn hợp nhiều lỗi cùng lúc, boundary mode-switch).

Viết ĐỘC LẬP với ``tests/unit/manifest/test_semantic_tier.py`` của dev.
"""

from __future__ import annotations

from namios_core.errors import ErrorCode
from namios_core.validation import SemanticContext
from namios_manifest._builder import build_manifest
from namios_manifest.validator import ManifestValidatorImpl

from ._qa_fixtures import baseline_manifest, mutate


def _ctx(
    approved: frozenset[str] = frozenset(),
    pinned: frozenset[str] = frozenset(),
    revoked: frozenset[str] = frozenset(),
) -> SemanticContext:
    return SemanticContext(
        approved_dependency_ids=approved, pinned_runner_hashes=pinned, revoked_ids=revoked
    )


def _semantic(raw: dict) -> object:
    validator = ManifestValidatorImpl()
    assert validator.validate_schema(raw).ok is True, "fixture phải pass schema trước"
    m = build_manifest(raw)
    return validator.validate_semantic(m, _ctx())


def test_revoked_app_with_otherwise_perfect_manifest_still_blocked() -> None:
    """Revoked PHẢI override mọi thứ khác — thử một manifest "hoàn hảo"
    (không TBD, không dependency thiếu) nhưng ``id`` nằm trong
    ``revoked_ids``. Không được vì "mọi điều kiện khác đều ok" mà lọt qua."""

    raw = mutate(baseline_manifest())
    validator = ManifestValidatorImpl()
    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx(revoked=frozenset({raw["id"]})))

    assert result.install_ready is False
    assert any(e.code == ErrorCode.E_REVOKED.value for e in result.errors)


def test_revoked_status_field_without_id_in_revoked_set_also_blocked() -> None:
    """Hai đường dẫn tới ``revoked`` (``id`` trong ``ctx.revoked_ids`` HOẶC
    ``compatibility.status == 'revoked'``) — kiểm tra đường thứ hai độc
    lập, không phụ thuộc ``ctx.revoked_ids`` có chứa id hay không."""

    raw = mutate(baseline_manifest())
    raw["compatibility"]["status"] = "revoked"

    validator = ManifestValidatorImpl()
    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())  # revoked_ids RỖNG cố ý

    assert result.install_ready is False
    assert any(e.code == ErrorCode.E_REVOKED.value for e in result.errors)


def test_dependency_id_with_trailing_whitespace_not_leniently_matched() -> None:
    """Dependency ``"dotnet-48-x64 "`` (có khoảng trắng cuối) KHÔNG được
    coi là khớp ``"dotnet-48-x64"`` trong approved set — exact-match tuyệt
    đối, không strip() ngầm (nếu có strip ngầm ở đâu đó sẽ là lỗ hổng cho
    phép bypass allowlist bằng biến thể chuỗi)."""

    raw = mutate(baseline_manifest())
    raw["runtime"]["dependency_profile_ids"] = ["dotnet-48-x64 "]

    validator = ManifestValidatorImpl()
    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx(approved=frozenset({"dotnet-48-x64"})))

    assert result.install_ready is False
    assert any(e.code == ErrorCode.E_SEMANTIC_DEPENDENCY.value for e in result.errors)


def test_dependency_id_case_variant_not_leniently_matched() -> None:
    """Biến thể hoa/thường của dependency_id đã duyệt KHÔNG được tự khớp
    (approve-list phải case-sensitive tuyệt đối, tránh nhầm hai profile
    khác nhau thành một)."""

    raw = mutate(baseline_manifest())
    raw["runtime"]["dependency_profile_ids"] = ["DOTNET-48-X64"]

    validator = ManifestValidatorImpl()
    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx(approved=frozenset({"dotnet-48-x64"})))

    assert result.install_ready is False
    assert any(e.code == ErrorCode.E_SEMANTIC_DEPENDENCY.value for e in result.errors)


def test_wine_mode_with_pinned_hash_but_wrong_runner_id_mismatch_still_requires_hash_check() -> (
    None
):
    """Mode ``wine`` cần runner pin — hash nằm trong ``pinned_runner_hashes``
    nhưng của một runner khác hẳn (``runner_id`` không khớp bối cảnh nào cả)
    vẫn phải được coi hợp lệ theo đúng field đang kiểm (chỉ hash), nhưng
    test này xác nhận hai field độc lập runner_id/runner_sha256 đều được
    validate riêng — không phải chỉ cần 1 trong 2 non-null là qua."""

    raw = mutate(baseline_manifest())
    raw["mode"] = "wine"
    raw["runtime"]["runner_id"] = None
    raw["runtime"]["runner_sha256"] = "c" * 64

    validator = ManifestValidatorImpl()
    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx(pinned=frozenset({"c" * 64})))

    assert result.install_ready is False
    assert any(
        e.code == ErrorCode.E_SEMANTIC_TBD.value and e.path == "runtime.runner_id"
        for e in result.errors
    )


def test_multiple_simultaneous_violations_all_reported_not_just_first() -> None:
    """Khi vi phạm NHIỀU điều kiện cùng lúc (TBD + dependency chưa duyệt +
    revoked), ``errors`` phải chứa ĐỦ cả ba — không được short-circuit chỉ
    báo lỗi đầu tiên rồi bỏ qua phần còn lại (điều này quan trọng để UI/CLI
    báo đủ cho người dùng sửa một lần)."""

    raw = mutate(baseline_manifest())
    raw["mode"] = "wine"
    raw["application"]["build"] = None
    raw["application"]["installer_sha256"] = None
    raw["runtime"]["dependency_profile_ids"] = ["unapproved-dep"]
    raw["compatibility"]["status"] = "revoked"

    validator = ManifestValidatorImpl()
    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    codes = {e.code for e in result.errors}
    assert ErrorCode.E_REVOKED.value in codes
    assert ErrorCode.E_SEMANTIC_TBD.value in codes
    assert ErrorCode.E_SEMANTIC_DEPENDENCY.value in codes
    assert result.install_ready is False


def test_existing_environment_acquisition_skips_build_hash_tbd_check_by_design() -> None:
    """``source.acquisition == "existing_environment"`` CHỦ Ý được coi là
    "không cần cài cục bộ" (``needs_local_install=False``) — xác nhận hành
    vi này đúng như code hiện tại (not a bypass: build/null vẫn chấp nhận),
    đồng thời ghi lại rõ ràng để không ai âm thầm coi đây là lỗ hổng khi
    không phải — ĐÂY LÀ TÀI LIỆU HÓA HÀNH VI, không phải khẳng định an
    toàn tuyệt đối cho mode wine/vm nếu ai đó set runner cũng null."""

    raw = mutate(baseline_manifest())
    raw["source"]["acquisition"] = "existing_environment"
    raw["application"]["build"] = None
    raw["application"]["installer_sha256"] = None

    validator = ManifestValidatorImpl()
    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    assert result.install_ready is True
    assert result.errors == ()


def test_task_verified_status_with_evidence_id_present_string_empty_still_passes_gate_here() -> (
    None
):
    """QUAN TRỌNG (tìm hiểu giới hạn phạm vi WP2): semantic chỉ kiểm tra
    ``evidence_id is None``, KHÔNG kiểm tra evidence_id có rỗng/placeholder
    hay có thật tồn tại trong WP9 hay không (đó là trách nhiệm của
    EvidenceValidator/WP9 — ngoài phạm vi WP2). Test này xác nhận đúng ranh
    giới: evidence_id="" (chuỗi rỗng, rõ ràng không phải ID thật) vẫn
    KHÔNG bị WP2 chặn ở tầng semantic — nếu kỳ vọng khác, đây là một input
    cần WP9's gate xử lý tiếp, không phải lỗi của WP2 riêng lẻ."""

    raw = mutate(baseline_manifest())
    raw["compatibility"]["status"] = "task_verified"
    raw["compatibility"]["evidence_id"] = ""

    validator = ManifestValidatorImpl()
    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    assert result.install_ready is True
    assert result.errors == ()
