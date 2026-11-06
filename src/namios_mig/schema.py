"""Validator hợp đồng MIG + vòng đời recipe có thể kiểm toán (N10-026).

Hai lỗi trung thực cốt lõi chặn ở đây: (a) ``usage_last_30_days`` chỉ được ghi
khi ``usage_opt_in=True`` (N10-007, không âm thầm thu thập hành vi dùng máy);
(b) ``WorkflowTest.status=PASSED`` PHẢI có evidence + ngày kiểm (N10-043,
"đã xong" không dựa vào launch/exit-code). Vòng đời chứng nhận recipe TÁI
DÙNG ``namios_odc.device_cert`` state machine (``advance``/``publish``) —
không dựng lại máy trạng thái thứ hai (N10-026).
"""

from __future__ import annotations

from dataclasses import replace

from namios_core.validation import ValidationError
from namios_i18n import Lang, t
from namios_mig import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_mig._errors import MigErrorCode
from namios_mig._types import (
    AppManifest,
    CompatibilityRecipe,
    CompatRoute,
    DeviceManifest,
    EvidenceRecord,
    MigrationInventory,
    WorkflowTest,
    WorkflowTestStatus,
)
from namios_odc import CertState, EvidenceKind
from namios_odc.device_cert import advance, can_publish, publish

__all__ = [
    "validate_app_manifest",
    "validate_device_manifest",
    "validate_recipe",
    "validate_workflow_test",
    "validate_evidence_record",
    "validate_inventory",
    "recipe_needs_retest",
    "promote_recipe",
    "publish_recipe",
]


def validate_app_manifest(app: AppManifest) -> list[ValidationError]:
    """Điều kiện cấu trúc cho ``AppManifest`` (N10-007). Rỗng = đủ điều kiện."""

    errors: list[ValidationError] = []
    if not app.app_id.strip():
        errors.append(
            ValidationError(
                code=MigErrorCode.E_MIG_APP_NO_ID.value,
                path="app_id",
                message_vi=t("mig.schema.app_no_id", lang=Lang.VI),
            )
        )
    if not app.usage_opt_in and app.last_used_days_ago is not None:
        errors.append(
            ValidationError(
                code=MigErrorCode.E_MIG_USAGE_NO_OPTIN.value,
                path="last_used_days_ago",
                message_vi=t("mig.schema.usage_no_optin", lang=Lang.VI),
            )
        )
    return errors


def validate_device_manifest(device: DeviceManifest) -> list[ValidationError]:
    """Điều kiện cấu trúc cho ``DeviceManifest`` (N10-006/047)."""

    if not device.device_id.strip():
        return [
            ValidationError(
                code=MigErrorCode.E_MIG_DEVICE_NO_ID.value,
                path="device_id",
                message_vi=t("mig.schema.device_no_id", lang=Lang.VI),
            )
        ]
    return []


def validate_recipe(recipe: CompatibilityRecipe) -> list[ValidationError]:
    """Điều kiện cấu trúc cho ``CompatibilityRecipe`` (N10-012/019/026).

    - Thiếu ``app_id``/``version`` → lỗi (không khớp được app nào).
    - ``route=WINE`` mà thiếu ``runner_id`` → lỗi (Wine runner PHẢI được pin,
      N10-019 — không "wine chung chung").
    - ``cert_state=PUBLISHED`` mà thiếu test case/owner → lỗi (N10-026: công
      bố PHẢI có bằng chứng + người chịu trách nhiệm, không công bố rỗng).
    """

    errors: list[ValidationError] = []
    if not recipe.app_id.strip():
        errors.append(
            ValidationError(
                code=MigErrorCode.E_MIG_RECIPE_NO_APP.value,
                path="app_id",
                message_vi=t("mig.schema.recipe_no_app", lang=Lang.VI),
            )
        )
    if not recipe.version.strip():
        errors.append(
            ValidationError(
                code=MigErrorCode.E_MIG_RECIPE_NO_VERSION.value,
                path="version",
                message_vi=t("mig.schema.recipe_no_version", lang=Lang.VI),
            )
        )
    if recipe.route is CompatRoute.WINE and not recipe.runner_id.strip():
        errors.append(
            ValidationError(
                code=MigErrorCode.E_MIG_RECIPE_NO_RUNNER.value,
                path="runner_id",
                message_vi=t("mig.schema.recipe_no_runner", lang=Lang.VI),
            )
        )
    if recipe.cert_state is CertState.PUBLISHED:
        if not recipe.test_case_ids:
            errors.append(
                ValidationError(
                    code=MigErrorCode.E_MIG_RECIPE_PUBLISH_NO_TEST.value,
                    path="test_case_ids",
                    message_vi=t("mig.schema.recipe_publish_no_test", lang=Lang.VI),
                )
            )
        if not recipe.owner.strip():
            errors.append(
                ValidationError(
                    code=MigErrorCode.E_MIG_RECIPE_PUBLISH_NO_OWNER.value,
                    path="owner",
                    message_vi=t("mig.schema.recipe_publish_no_owner", lang=Lang.VI),
                )
            )
    return errors


def validate_workflow_test(test: WorkflowTest) -> list[ValidationError]:
    """``status=PASSED`` PHẢI có evidence + ngày kiểm (N10-043)."""

    errors: list[ValidationError] = []
    if test.status is WorkflowTestStatus.PASSED:
        has_evidence = any((e or "").strip() for e in test.evidence_ids)
        if not has_evidence:
            errors.append(
                ValidationError(
                    code=MigErrorCode.E_MIG_WORKFLOW_NO_EVIDENCE.value,
                    path="evidence_ids",
                    message_vi=t("mig.schema.workflow_no_evidence", lang=Lang.VI),
                )
            )
        if not (test.tested_at or "").strip():
            errors.append(
                ValidationError(
                    code=MigErrorCode.E_MIG_WORKFLOW_NO_TESTED_AT.value,
                    path="tested_at",
                    message_vi=t("mig.schema.workflow_no_tested_at", lang=Lang.VI),
                )
            )
    return errors


def validate_evidence_record(evidence: EvidenceRecord) -> list[ValidationError]:
    """Một ``EvidenceRecord`` PHẢI mang ít nhất một tín hiệu quan sát được —
    record rỗng (không print/sign/independent_check) không chứng minh gì."""

    errors: list[ValidationError] = []
    if not evidence.evidence_id.strip() or not evidence.workflow_id.strip():
        errors.append(
            ValidationError(
                code=MigErrorCode.E_MIG_EVIDENCE_EMPTY.value,
                path="evidence_id",
                message_vi=t("mig.schema.evidence_empty", lang=Lang.VI),
            )
        )
        return errors
    no_signal = (
        evidence.print_stage is None
        and evidence.sign_stage is None
        and evidence.independent_check_ok is None
    )
    if no_signal:
        errors.append(
            ValidationError(
                code=MigErrorCode.E_MIG_EVIDENCE_EMPTY.value,
                path="evidence_id",
                message_vi=t("mig.schema.evidence_empty", lang=Lang.VI),
            )
        )
    return errors


def validate_inventory(inventory: MigrationInventory) -> list[ValidationError]:
    """Điều kiện cấu trúc cho ``MigrationInventory`` (N10-007); đệ quy xuống
    từng ``AppManifest``/``DeviceManifest``."""

    errors: list[ValidationError] = []
    if not inventory.machine_id.strip():
        errors.append(
            ValidationError(
                code=MigErrorCode.E_MIG_INVENTORY_NO_MACHINE.value,
                path="machine_id",
                message_vi=t("mig.schema.inventory_no_machine", lang=Lang.VI),
            )
        )
    for i, app in enumerate(inventory.apps):
        for err in validate_app_manifest(app):
            errors.append(replace(err, path=f"apps[{i}].{err.path}"))
    for i, device in enumerate(inventory.devices):
        for err in validate_device_manifest(device):
            errors.append(replace(err, path=f"devices[{i}].{err.path}"))
    return errors


def recipe_needs_retest(
    recipe: CompatibilityRecipe, *, current_installer_hash: str, current_version: str
) -> CompatibilityRecipe:
    """Đổi hash/version của app → recipe tự ``needs_retest`` (N10-026).

    So khớp fingerprint hiện tại (từ khảo sát mới) với recipe đã ký; khác →
    trả recipe MỚI với ``cert_state=NEEDS_RETEST`` — KHÔNG kế thừa nhãn cũ
    (dù trước đó đã ``PUBLISHED``). Khớp → trả nguyên recipe."""

    changed = recipe.installer_hash != current_installer_hash or recipe.version != current_version
    if not changed:
        return recipe
    return replace(
        recipe,
        cert_state=CertState.NEEDS_RETEST,
        limitations_vi=(*recipe.limitations_vi, t("mig.recipe.needs_retest", lang=Lang.VI)),
    )


def promote_recipe(recipe: CompatibilityRecipe, evidence: EvidenceKind) -> CompatibilityRecipe:
    """Nâng ``cert_state`` của recipe theo bằng chứng (N10-026). TÁI DÙNG
    ``namios_odc.device_cert.advance`` — cộng đồng/AI (``COMMUNITY_REPORT``/
    ``AI_GUESS``) KHÔNG BAO GIỜ nâng; chỉ ``LAB_TEST``/``PILOT_SIGNOFF``, tuần
    tự lab→pilot, không nhảy cóc."""

    return replace(recipe, cert_state=advance(recipe.cert_state, evidence))


def publish_recipe(recipe: CompatibilityRecipe) -> CompatibilityRecipe:
    """Công bố recipe (N10-026). Chỉ công bố khi ĐỦ điều kiện trạng thái
    (``can_publish`` — phải ``pilot_verified``) VÀ nội dung đạt
    ``validate_recipe`` khi ở trạng thái published (có test case + owner);
    thiếu bất kỳ điều kiện nào → giữ nguyên recipe (fail-closed, không công
    bố rỗng)."""

    if not can_publish(recipe.cert_state):
        return recipe
    candidate = replace(recipe, cert_state=CertState.PUBLISHED)
    if validate_recipe(candidate):
        return recipe
    return replace(recipe, cert_state=publish(recipe.cert_state))
