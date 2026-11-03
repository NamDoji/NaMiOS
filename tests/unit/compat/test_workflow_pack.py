"""Test COMP-031 (Phụ lục 03) cho ``namios_compat.workflow_pack``.

Trọng tâm nghiệm thu: sáu pack mẫu (một mỗi ``Sector``) đúng 7 nấc ECO-001
theo thứ tự, có điểm DỪNG trước giao dịch thật ở ``authenticate``/
``submit_or_export``, và ``validate_pack_raw`` chặn secret + khóa thực thi +
cấu trúc nấc sai — pack KHÔNG BAO GIỜ tự nhận một app thật là tương thích
(``provider_id``/``gateway`` giữ ``unresolved``/``unknown`` trong mẫu)."""

from __future__ import annotations

import copy
from typing import Any

from namios_compat._errors import CompatErrorCode
from namios_compat._types import Sector, WorkflowPack
from namios_compat.workflow_pack import (
    SAMPLE_PACKS,
    load_sample_packs,
    pack_to_dict,
    validate_pack_raw,
)
from namios_eco.workflow import WORKFLOW_STEP_ORDER, WorkflowStepName

# -- load_sample_packs: một pack mỗi Sector ----------------------------------


def test_load_sample_packs_returns_six_one_per_sector() -> None:
    packs = load_sample_packs()
    assert len(packs) == 6
    assert {pack.sector for pack in packs} == set(Sector)


def test_load_sample_packs_is_sample_packs() -> None:
    assert load_sample_packs() == SAMPLE_PACKS


# -- cấu trúc 7 nấc + điểm dừng trước giao dịch thật -------------------------


def test_every_sample_pack_has_exactly_seven_steps_in_order() -> None:
    for pack in SAMPLE_PACKS:
        assert tuple(step.name for step in pack.steps) == WORKFLOW_STEP_ORDER


def test_authenticate_and_submit_stop_before_real_transaction() -> None:
    for pack in SAMPLE_PACKS:
        by_name = {step.name: step for step in pack.steps}
        assert by_name[WorkflowStepName.AUTHENTICATE].stop_before_real_transaction is True
        assert by_name[WorkflowStepName.SUBMIT_OR_EXPORT].stop_before_real_transaction is True


def test_every_step_has_plausible_role_and_artifact() -> None:
    for pack in SAMPLE_PACKS:
        for step in pack.steps:
            assert step.role.strip() != ""
            assert step.expected_artifact.strip() != ""


# -- provider/gateway chưa khảo sát -------------------------------------------


def test_samples_do_not_claim_a_resolved_real_provider() -> None:
    for pack in SAMPLE_PACKS:
        assert pack.provider_id == "unresolved"
        assert pack.gateway == "unknown"


def test_samples_have_no_credentials_in_devices_or_notes() -> None:
    # "token" bị loại khỏi danh sách: device id "signing-token-mock-*" là
    # THIẾT BỊ ký số (token vật lý), không phải secret — khác với key JSON
    # "token"/"api_key" mà validate_pack_raw mới thật sự quét/chặn.
    forbidden_substrings = ("password", "pwd", "cookie", "secret", "credential")
    for pack in SAMPLE_PACKS:
        haystack = " ".join(pack.devices).lower() + pack.notes_vi.lower()
        for bad in forbidden_substrings:
            assert bad not in haystack


# -- pack_to_dict + validate_pack_raw: sample sạch ---------------------------


def test_pack_to_dict_then_validate_pack_raw_clean_for_every_sample() -> None:
    for pack in SAMPLE_PACKS:
        raw = pack_to_dict(pack)
        assert validate_pack_raw(raw) == []


def test_pack_to_dict_is_deterministic() -> None:
    pack = SAMPLE_PACKS[0]
    assert pack_to_dict(pack) == pack_to_dict(pack)


def test_pack_to_dict_serializes_enums_to_plain_values() -> None:
    pack = SAMPLE_PACKS[0]
    raw = pack_to_dict(pack)
    assert raw["sector"] == pack.sector.value
    assert isinstance(raw["sector"], str)
    for step in raw["steps"]:
        assert isinstance(step["name"], str)


# -- validate_pack_raw: secret scan -------------------------------------------


def _valid_raw() -> dict[str, Any]:
    return copy.deepcopy(pack_to_dict(SAMPLE_PACKS[0]))


def test_nested_password_field_rejected_with_secret_code() -> None:
    raw = _valid_raw()
    raw["steps"][0]["password"] = "demo-giả"  # noqa: S105 — dữ liệu test, không phải mật khẩu thật
    errors = validate_pack_raw(raw)
    assert any(e.code == CompatErrorCode.E_COMPAT_PACK_SECRET.value for e in errors)


def test_secret_key_match_is_case_insensitive() -> None:
    raw = _valid_raw()
    raw["devices_meta"] = {"ApiKey": "demo-giả"}
    errors = validate_pack_raw(raw)
    assert any(e.code == CompatErrorCode.E_COMPAT_PACK_SECRET.value for e in errors)


def test_clean_sample_has_no_secret_errors() -> None:
    raw = _valid_raw()
    errors = validate_pack_raw(raw)
    assert all(e.code != CompatErrorCode.E_COMPAT_PACK_SECRET.value for e in errors)


# -- validate_pack_raw: executable key scan ----------------------------------


def test_command_key_rejected_as_executable() -> None:
    raw = _valid_raw()
    raw["steps"][0]["command"] = "rm -rf /"
    errors = validate_pack_raw(raw)
    assert errors
    assert all(e.code != CompatErrorCode.E_COMPAT_REQUIRED_STEPS.value for e in errors)


def test_nested_argv_key_rejected_as_executable() -> None:
    raw = _valid_raw()
    raw["steps"][0]["inputs"] = {"argv": ["echo", "hi"]}
    errors = validate_pack_raw(raw)
    assert errors


# -- validate_pack_raw: required 7-step structure ----------------------------


def test_missing_steps_key_rejected_with_required_steps_code() -> None:
    raw = _valid_raw()
    del raw["steps"]
    errors = validate_pack_raw(raw)
    assert any(e.code == CompatErrorCode.E_COMPAT_REQUIRED_STEPS.value for e in errors)


def test_short_steps_list_rejected_with_required_steps_code() -> None:
    raw = _valid_raw()
    raw["steps"] = raw["steps"][:3]
    errors = validate_pack_raw(raw)
    assert any(e.code == CompatErrorCode.E_COMPAT_REQUIRED_STEPS.value for e in errors)


def test_wrong_step_order_rejected_with_required_steps_code() -> None:
    raw = _valid_raw()
    raw["steps"][0], raw["steps"][1] = raw["steps"][1], raw["steps"][0]
    errors = validate_pack_raw(raw)
    assert any(e.code == CompatErrorCode.E_COMPAT_REQUIRED_STEPS.value for e in errors)


def test_steps_not_a_list_rejected_with_required_steps_code() -> None:
    raw = _valid_raw()
    raw["steps"] = "discover"
    errors = validate_pack_raw(raw)
    assert any(e.code == CompatErrorCode.E_COMPAT_REQUIRED_STEPS.value for e in errors)


def test_clean_sample_has_no_required_steps_errors() -> None:
    raw = _valid_raw()
    errors = validate_pack_raw(raw)
    assert all(e.code != CompatErrorCode.E_COMPAT_REQUIRED_STEPS.value for e in errors)


# -- WorkflowPack dataclass sanity (frozen contract) --------------------------


def test_workflow_pack_instances_are_frozen_dataclasses() -> None:
    pack = SAMPLE_PACKS[0]
    assert isinstance(pack, WorkflowPack)
    try:
        pack.provider_id = "changed"  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("WorkflowPack phải là frozen dataclass")
