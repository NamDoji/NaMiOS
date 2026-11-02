"""Validator tầng 2 (ngữ nghĩa) ECO-002/003/006/007."""

from __future__ import annotations

from tests.unit.eco._fixtures import ALL_PASS_STEPS, steps_with

from namios_eco.status import PublishedStatus
from namios_eco.validator import (
    FORBIDDEN_EXECUTABLE_KEYS,
    validate_no_executable_keys,
    validate_no_official_claim_text,
    validate_official_url,
    validate_status_matches_workflow,
    validate_status_transition,
    validate_usability_claim,
)
from namios_eco.workflow import StepOutcome, WorkflowStep, WorkflowStepName

# -- validate_official_url ---------------------------------------------------


def test_https_official_url_accepted() -> None:
    assert validate_official_url("https://thuedientu.gdt.gov.vn/") == []


def test_http_official_url_accepted() -> None:
    assert validate_official_url("http://csdl.moet.gov.vn/Default.aspx") == []


def test_javascript_scheme_rejected() -> None:
    errors = validate_official_url("javascript:alert(1)")
    assert errors and errors[0].code == "E_SOURCE_POLICY"


def test_file_scheme_rejected() -> None:
    errors = validate_official_url("file:///etc/passwd")
    assert errors and errors[0].code == "E_SOURCE_POLICY"


def test_url_missing_domain_rejected() -> None:
    errors = validate_official_url("https://")
    assert errors


def test_url_with_embedded_credentials_rejected() -> None:
    """Chống kiểu URL đánh lừa domain 'co-quan.gov.vn@trang-gia.example'."""

    errors = validate_official_url("https://co-quan.gov.vn@trang-gia.example/")
    assert errors and any("xác thực" in e.message_vi or "@" in e.message_vi for e in errors)


# -- validate_usability_claim (GATE tuyệt đối) -------------------------------


def test_claim_usable_for_downloadable_only_rejected() -> None:
    errors = validate_usability_claim(PublishedStatus.DOWNLOADABLE_ONLY, claimed_usable=True)
    assert errors and errors[0].code == "E_ECO_USABILITY_CLAIM"


def test_claim_usable_for_launches_only_rejected() -> None:
    errors = validate_usability_claim(PublishedStatus.LAUNCHES_ONLY, claimed_usable=True)
    assert errors and errors[0].code == "E_ECO_USABILITY_CLAIM"


def test_claim_not_usable_for_downloadable_only_accepted() -> None:
    assert validate_usability_claim(PublishedStatus.DOWNLOADABLE_ONLY, claimed_usable=False) == []


def test_claim_usable_for_workflow_verified_accepted() -> None:
    assert validate_usability_claim(PublishedStatus.WORKFLOW_VERIFIED, claimed_usable=True) == []


# -- validate_status_matches_workflow ----------------------------------------


def test_claim_workflow_verified_without_evidence_rejected() -> None:
    steps = steps_with(
        {
            WorkflowStepName.SUBMIT_OR_EXPORT: WorkflowStep(
                WorkflowStepName.SUBMIT_OR_EXPORT, StepOutcome.PASS, evidence_ref=None
            )
        }
    )
    errors = validate_status_matches_workflow(PublishedStatus.WORKFLOW_VERIFIED, steps)
    assert errors and errors[0].code == "E_EVIDENCE_MISSING"


def test_claim_workflow_verified_with_full_evidence_accepted() -> None:
    errors = validate_status_matches_workflow(PublishedStatus.WORKFLOW_VERIFIED, ALL_PASS_STEPS)
    assert errors == []


def test_claim_partial_workflow_never_blocked_by_this_check() -> None:
    """Hàm này chỉ canh workflow_verified; claim thấp hơn thực tế không bị chặn ở đây."""

    errors = validate_status_matches_workflow(PublishedStatus.PARTIAL_WORKFLOW, ALL_PASS_STEPS)
    assert errors == []


# -- validate_status_transition ----------------------------------------------


def test_same_status_transition_always_allowed() -> None:
    assert (
        validate_status_transition(
            PublishedStatus.PARTIAL_WORKFLOW, PublishedStatus.PARTIAL_WORKFLOW
        )
        == []
    )


def test_not_inventoried_to_workflow_verified_direct_jump_rejected() -> None:
    errors = validate_status_transition(
        PublishedStatus.NOT_INVENTORIED, PublishedStatus.WORKFLOW_VERIFIED
    )
    assert errors and errors[0].code == "E_STATE_CONFLICT"


def test_not_inventoried_to_partial_workflow_allowed() -> None:
    assert (
        validate_status_transition(
            PublishedStatus.NOT_INVENTORIED, PublishedStatus.PARTIAL_WORKFLOW
        )
        == []
    )


def test_revoked_is_terminal_no_outgoing_transition() -> None:
    errors = validate_status_transition(PublishedStatus.REVOKED, PublishedStatus.PARTIAL_WORKFLOW)
    assert errors and errors[0].code == "E_STATE_CONFLICT"


def test_any_published_status_can_transition_to_revoked() -> None:
    """Mọi trạng thái ĐÃ CÔNG BỐ (khác not_inventoried) đều có thể bị thu hồi.
    ``not_inventoried`` KHÔNG đi thẳng sang ``revoked`` — chưa công bố gì thì
    chưa có gì để thu hồi (chỉ có thể unsupported/blocked/... trước)."""

    for status in PublishedStatus:
        if status in (PublishedStatus.REVOKED, PublishedStatus.NOT_INVENTORIED):
            continue
        errors = validate_status_transition(status, PublishedStatus.REVOKED)
        assert errors == [], f"{status} -> revoked phải luôn hợp lệ"


def test_not_inventoried_cannot_jump_straight_to_revoked() -> None:
    errors = validate_status_transition(PublishedStatus.NOT_INVENTORIED, PublishedStatus.REVOKED)
    assert errors and errors[0].code == "E_STATE_CONFLICT"


# -- validate_no_executable_keys ("catalog không điều khiển lệnh") ----------


def test_top_level_command_key_rejected() -> None:
    raw = {"id": "a", "command": ["rm", "-rf", "/"]}
    errors = validate_no_executable_keys(raw)
    assert any(e.code == "E_SEMANTIC_RECIPE" for e in errors)


def test_nested_shell_key_rejected() -> None:
    raw = {"id": "a", "dependencies": [{"shell": "echo hi"}]}
    errors = validate_no_executable_keys(raw)
    assert any(e.code == "E_SEMANTIC_RECIPE" for e in errors)


def test_clean_catalog_entry_has_no_executable_keys() -> None:
    raw = {"id": "a", "provider": "b", "dependencies": ["java-runtime"]}
    assert validate_no_executable_keys(raw) == []


def test_forbidden_keys_constant_covers_common_exec_vectors() -> None:
    for key in ("command", "argv", "shell", "run", "exec", "script"):
        assert key in FORBIDDEN_EXECUTABLE_KEYS


# -- validate_no_official_claim_text (ECO-007) -------------------------------


def test_third_party_official_claim_rejected() -> None:
    errors = validate_no_official_claim_text(
        "Đây là ứng dụng chính thức của NaMiOS cho kế toán.", path="purpose"
    )
    assert errors and errors[0].code == "E_ECO_OFFICIAL_CLAIM_FORBIDDEN"


def test_third_party_official_claim_case_insensitive() -> None:
    errors = validate_no_official_claim_text("ỨNG DỤNG CHÍNH THỨC CỦA NAMIOS", path="purpose")
    assert errors


def test_normal_description_without_claim_accepted() -> None:
    errors = validate_no_official_claim_text(
        "Phần mềm kế toán của MISA, chạy qua Wine.", path="purpose"
    )
    assert errors == []
