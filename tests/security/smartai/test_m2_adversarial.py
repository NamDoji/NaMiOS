"""SmartAI M2 — kiểm thử đối kháng tự-sửa có giới hạn (SAI-010/011/012/018/
020/033/041/042). Đây là yêu cầu "Adversarial Evaluation" SAI-032.

Mỗi ``test_attack_N_...`` cố tình CÔNG vào MỘT lời hứa an toàn của tầng M2
(bounded repair / recipe / promotion gate / regression / supply-chain):

(a) bounded repair KHÔNG BAO GIỜ retry vô hạn, KHÔNG BAO GIỜ đụng bản gốc
    capsule, LUÔN rollback mỗi phép thử, và DỪNG CỨNG khi data-wrong/
    missing-license/security/needs-vendor.
(b) recipe candidate CHỈ sinh ra từ một tool-success THẬT — không bao giờ
    bịa.
(c) promotion KHÔNG thể bị giả bằng nhãn ``state`` do AI gán — chỉ evidence
    tool-pass thật + approver + reviewers + business_ok mới tới ``published``;
    evidence quá hạn/giả → ``needs_retest``.
(d) supply-chain từ chối nguồn không chính thức/thiếu hash.
(e) recipe của một kiến trúc KHÔNG tự áp cho kiến trúc khác.
(f) đổi bất kỳ thành phần khóa hồi quy → ``needs_retest``.

Nếu một bất biến thật sự SAI, test này PHẢI FAIL (hoặc ``xfail(strict=True)``
với lý do bắt đầu bằng ``"HOLE:"``) — KHÔNG được sửa ``src/`` từ file này.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from namios_smartai import (
    HARD_STOPS,
    Capsule,
    CompatibilityRecipe,
    RecipeState,
    RegressionKey,
    RepairBudget,
    ToolResultStatus,
    TrialStopReason,
    TrustEvidence,
    apply_regression,
    arch_applies,
    bounded_repair,
    changed_components,
    check_supply_chain,
    is_legitimately_published,
    new_candidate,
    promote,
)
from namios_smartai.recipe import recipe_from_dict

# Định vị console-script `namios` theo môi trường ĐANG chạy — venv local
# (.venv/bin/namios) HAY CI không có .venv (cùng thư mục bin với interpreter /
# trên PATH). Chạy đúng cả `pytest` local lẫn CI.
_NAMIOS_BIN = Path(shutil.which("namios") or (Path(sys.executable).parent / "namios"))


# ---------------------------------------------------------------------------
# Helper executors (TrialExecutor protocol: .run(hypothesis, capsule) ->
# (ToolResultStatus, measured_vi, TrialStopReason)) + helper recipe builder.
# ---------------------------------------------------------------------------


class _AlwaysFailExecutor:
    """Không bao giờ thành công, không bao giờ dừng cứng — mô phỏng mọi ứng
    viên đều sai để kiểm tra budget có chặn retry vô hạn không."""

    def __init__(self) -> None:
        self.received_capsules: list[Capsule] = []

    def run(
        self, hypothesis: str, capsule: Capsule
    ) -> tuple[ToolResultStatus, str, TrialStopReason]:
        self.received_capsules.append(capsule)
        return ToolResultStatus.FAILED, f"thử {hypothesis} vẫn fail", TrialStopReason.NONE


class _HardStopFirstExecutor:
    """Trả hard-stop ngay phép thử ĐẦU — mọi phép thử sau (nếu bị gọi) sẽ bị
    đếm, để chứng minh bounded_repair không "lỡ" chạy tiếp qua dừng cứng."""

    def __init__(
        self, stop: TrialStopReason, *, outcome: ToolResultStatus = ToolResultStatus.FAILED
    ) -> None:
        self.stop = stop
        self.outcome = outcome
        self.calls = 0

    def run(
        self, hypothesis: str, capsule: Capsule
    ) -> tuple[ToolResultStatus, str, TrialStopReason]:
        self.calls += 1
        return self.outcome, "chặn cứng", self.stop


class _NeverSucceedsExecutor:
    """PARTIAL/BLOCKED/FAILED xoay vòng — KHÔNG BAO GIỜ SUCCESS — để kiểm tra
    recipe_candidate không được bịa khi không có tool-success thật."""

    _CYCLE = (ToolResultStatus.FAILED, ToolResultStatus.PARTIAL, ToolResultStatus.BLOCKED)

    def __init__(self) -> None:
        self.calls = 0

    def run(
        self, hypothesis: str, capsule: Capsule
    ) -> tuple[ToolResultStatus, str, TrialStopReason]:
        outcome = self._CYCLE[self.calls % len(self._CYCLE)]
        self.calls += 1
        return outcome, "chưa xong", TrialStopReason.NONE


def _full_recipe(**overrides: object) -> CompatibilityRecipe:
    """Recipe "đủ điều kiện cấu trúc" (source_url+app_hash+rollback+reviewers)
    — dùng làm điểm xuất phát rồi tháo bớt từng điều kiện để dò promotion gate."""

    base: dict[str, object] = dict(
        recipe_id="r-full",
        publisher="vendor-x",
        source_url="https://misa.vn/download/app.exe",
        app_id="misa-app",
        app_version="2024.1",
        app_hash="sha256:deadbeef",
        architecture="x86_64",
        runner="wine",
        runtime="win32",
        rollback="gỡ registry key + xóa prefix capsule",
        changes_system=True,
        reviewers=("qa-reviewer-1",),
        state=RecipeState.EXPERIMENTAL,
    )
    base.update(overrides)
    return CompatibilityRecipe(**base)  # type: ignore[arg-type]


def _tool_pass_evidence(**overrides: object) -> TrustEvidence:
    base: dict[str, object] = dict(
        origin="tool",
        timestamp="2026-11-01T00:00:00",
        version="2024.1",
        fixture_hash="sha256:fixturehash",
        test_result="pass",
        reviewer=None,
        valid_until=None,
    )
    base.update(overrides)
    return TrustEvidence(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Attack 1 — KHÔNG retry vô hạn: 1000 ứng viên, executor luôn FAIL,
# budget max_trials=3 → tối đa 3 trials, không recipe. ``max_steps=1`` cũng
# phải chặn tương tự dù max_trials rộng hơn.
# ---------------------------------------------------------------------------


def test_attack_1_no_infinite_retry_budget_caps_trials() -> None:
    candidates = [f"candidate-{i}" for i in range(1000)]
    executor = _AlwaysFailExecutor()

    outcome = bounded_repair("base-app", candidates, executor, budget=RepairBudget(max_trials=3))

    assert len(outcome.trials) <= 3, f"HOLE: {len(outcome.trials)} trials vượt budget max_trials=3"
    assert outcome.stop_reason in {
        TrialStopReason.ALL_CANDIDATES_FAILED,
        TrialStopReason.BUDGET_EXCEEDED,
    }
    assert outcome.recipe_candidate is None
    assert outcome.status == ToolResultStatus.BLOCKED
    # Thực thi KHÔNG được chạy nhiều hơn 1000 lần (không có đường nào vòng
    # lại); nhưng quan trọng hơn: executor chỉ được gọi tối đa max_trials lần.
    assert executor.received_capsules, "executor phải được gọi ít nhất 1 lần"
    assert len(executor.received_capsules) <= 3

    # max_steps siết chặt hơn cả max_trials — 1 bước là dừng, dù max_trials
    # rộng (budget mặc định 3 trials vẫn phải tôn trọng max_steps=1).
    executor2 = _AlwaysFailExecutor()
    outcome2 = bounded_repair(
        "base-app", candidates, executor2, budget=RepairBudget(max_trials=1000, max_steps=1)
    )
    assert len(outcome2.trials) <= 1, "HOLE: max_steps=1 không chặn được số phép thử"
    assert outcome2.stop_reason == TrialStopReason.BUDGET_EXCEEDED
    assert outcome2.recipe_candidate is None


# ---------------------------------------------------------------------------
# Attack 2 — bản gốc KHÔNG BAO GIỜ bị mutate; mỗi capsule executor nhận được
# là MỚI (base_id giống nhau nhưng capsule_id/snapshot_id khác), có ĐÚNG MỘT
# mutation (chính hypothesis đang thử), và CHƯA rollback tại thời điểm thực
# thi (rollback xảy ra SAU, bounded_repair tự làm — không phải executor).
# Sau cùng mọi Trial trong outcome phải ghi nhận rolled_back=True.
# ---------------------------------------------------------------------------


def test_attack_2_original_never_mutated_each_trial_isolated() -> None:
    executor = _AlwaysFailExecutor()
    candidates = ["fix-a", "fix-b", "fix-c"]

    outcome = bounded_repair("base-app", candidates, executor, budget=RepairBudget(max_trials=3))

    assert len(executor.received_capsules) == 3
    seen_capsule_ids: set[str] = set()
    seen_snapshot_ids: set[str] = set()
    for i, cap in enumerate(executor.received_capsules):
        # base_id không đổi — capsule vẫn "thuộc về" app gốc, nhưng capsule
        # object chính nó là bản sao mới mỗi trial (capsule_id/snapshot_id
        # riêng), KHÔNG tái dùng một capsule đã-mutate xuyên trials.
        assert cap.base_id == "base-app"
        assert cap.capsule_id not in seen_capsule_ids, "HOLE: capsule_id lặp lại giữa các trial"
        assert cap.snapshot_id not in seen_snapshot_ids, "HOLE: snapshot_id lặp lại giữa các trial"
        seen_capsule_ids.add(cap.capsule_id)
        seen_snapshot_ids.add(cap.snapshot_id)

        # ĐÚNG MỘT mutation — chính hypothesis đang thử, không tích lũy từ
        # trial trước (nếu tích lũy, mutations sẽ dài ra theo i).
        assert cap.mutations == (candidates[i],), (
            f"HOLE: capsule trial {i} có mutations={cap.mutations!r}, "
            f"kỳ vọng đúng 1 mutation ({candidates[i]!r}) — nghi ngờ tích lũy "
            "qua các trial hoặc đụng bản gốc."
        )
        # Tại thời điểm executor CHẠY, capsule CHƯA được rollback — rollback
        # là bước SAU, do bounded_repair tự làm, không phải executor.
        assert cap.rolled_back is False

    # Sau khi bounded_repair xong, MỌI Trial ghi nhận rolled_back=True — bản
    # sao đã thử luôn được hoàn nguyên, không "treo" ở trạng thái đã mutate.
    assert len(outcome.trials) == 3
    for trial in outcome.trials:
        assert trial.rolled_back is True, f"HOLE: trial {trial.trial_id} không rollback"


# ---------------------------------------------------------------------------
# Attack 3 — hard stop (DATA_WRONG/MISSING_LICENSE/SECURITY/NEEDS_VENDOR)
# PHẢI dừng ngay phép thử ĐẦU: đúng 1 trial, stop_reason khớp, không recipe,
# status BLOCKED. Đặc biệt: NGAY CẢ khi executor "nói" SUCCESS nhưng kèm
# hard_stop != NONE cùng lúc (adversarial: cố lách qua dừng cứng bằng cách
# giả vờ thành công) — vẫn phải BLOCK, không được publish recipe.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stop",
    [
        TrialStopReason.DATA_WRONG,
        TrialStopReason.MISSING_LICENSE,
        TrialStopReason.SECURITY,
        TrialStopReason.NEEDS_VENDOR,
    ],
)
def test_attack_3_hard_stops_short_circuit_on_first_candidate(stop: TrialStopReason) -> None:
    assert stop in HARD_STOPS
    executor = _HardStopFirstExecutor(stop)
    candidates = ["c1", "c2", "c3", "c4", "c5"]

    outcome = bounded_repair(
        "base-app",
        candidates,
        executor,
        budget=RepairBudget(max_trials=100),
        recipe_factory=lambda h: _full_recipe(recipe_id=f"from-{h}"),
    )

    assert executor.calls == 1, "HOLE: executor bị gọi tiếp qua ứng viên khác sau dừng cứng"
    assert len(outcome.trials) == 1
    assert outcome.stop_reason == stop
    assert outcome.status == ToolResultStatus.BLOCKED
    assert outcome.recipe_candidate is None, "HOLE: có recipe dù đã dừng cứng"


def test_attack_3b_hard_stop_wins_even_if_executor_claims_success() -> None:
    """Cố lách: executor trả SUCCESS *đồng thời* hard_stop=SECURITY (như một
    tool bị injection/giả mạo cố báo "xong" để qua mặt). Dừng cứng PHẢI thắng
    — không được coi đây là một trial thành công, không sinh recipe."""

    executor = _HardStopFirstExecutor(TrialStopReason.SECURITY, outcome=ToolResultStatus.SUCCESS)
    outcome = bounded_repair(
        "base-app",
        ["c1", "c2"],
        executor,
        recipe_factory=lambda h: _full_recipe(recipe_id=f"from-{h}"),
    )

    assert executor.calls == 1
    assert len(outcome.trials) == 1
    assert outcome.stop_reason == TrialStopReason.SECURITY
    assert outcome.status == ToolResultStatus.BLOCKED
    assert (
        outcome.recipe_candidate is None
    ), "HOLE: recipe được sinh ra dù dừng cứng SECURITY — có thể lách bằng 'success giả'"


# ---------------------------------------------------------------------------
# Attack 4 — KHÔNG bịa recipe: executor không bao giờ SUCCESS (FAILED/
# PARTIAL/BLOCKED xoay vòng, không hard stop) + recipe_factory được cấp →
# recipe_candidate PHẢI là None (recipe chỉ sinh từ 1 tool-success THẬT).
# ---------------------------------------------------------------------------


def test_attack_4_no_fabricated_recipe_without_real_success() -> None:
    executor = _NeverSucceedsExecutor()
    candidates = [f"candidate-{i}" for i in range(20)]

    outcome = bounded_repair(
        "base-app",
        candidates,
        executor,
        budget=RepairBudget(max_trials=10, max_steps=20),
        recipe_factory=lambda h: _full_recipe(recipe_id=f"from-{h}"),
    )

    assert outcome.recipe_candidate is None, "HOLE: recipe bịa ra mà không có tool-success thật"
    assert outcome.status == ToolResultStatus.BLOCKED
    assert outcome.stop_reason in {
        TrialStopReason.ALL_CANDIDATES_FAILED,
        TrialStopReason.BUDGET_EXCEEDED,
    }
    for trial in outcome.trials:
        assert trial.outcome != ToolResultStatus.SUCCESS


# ---------------------------------------------------------------------------
# Attack 5 — promotion KHÔNG thể bị giả bằng nhãn ``state``.
#
# 5a. ``recipe_from_dict`` ép ``state=published`` (nhãn ngoài) về
#     ``experimental`` — nhãn tự khai bị bỏ qua hoàn toàn.
# 5b. Một recipe object với ``state=PUBLISHED`` gán TRỰC TIẾP (giả lập "AI
#     ghi đè field") + evidence rỗng → ``is_legitimately_published`` vẫn
#     False — hàm này tính lại từ evidence/approver/business_ok, KHÔNG đọc
#     ``recipe.state``.
# 5c. Quét toàn bộ tổ hợp "lẽ ra phải fail": không evidence / evidence chỉ
#     vendor / chỉ user / tool-pass không approver / có approver không
#     reviewers / có reviewers nhưng business_ok=False / thiếu rollback cấu
#     trúc — KHÔNG tổ hợp nào trong số này được tới PUBLISHED, bất kể
#     ``recipe.state`` ghi gì.
# ---------------------------------------------------------------------------


def test_attack_5a_recipe_from_dict_ignores_self_declared_published_label() -> None:
    raw = {
        "recipe_id": "r-fake",
        "publisher": "ai-itself",
        "source_url": "https://misa.vn/x",
        "app_id": "a",
        "app_version": "1.0",
        "app_hash": "deadbeef",
        "architecture": "x86_64",
        "runner": "wine",
        "runtime": "win32",
        "state": "published",  # nhãn tự khai — PHẢI bị bỏ qua
    }
    recipe = recipe_from_dict(raw)
    assert recipe.state == RecipeState.EXPERIMENTAL, (
        f"HOLE: recipe_from_dict tin nhãn state='published' tự khai, " f"trả về {recipe.state!r}"
    )


def test_attack_5b_object_with_published_state_set_directly_is_not_legit() -> None:
    faked = _full_recipe(state=RecipeState.PUBLISHED)  # giả lập AI ghi đè field trực tiếp
    assert faked.state == RecipeState.PUBLISHED  # field thật sự mang nhãn published...

    # ...nhưng is_legitimately_published PHẢI tính lại từ evidence thật, bỏ
    # qua recipe.state — với evidence rỗng, không thể là published thật.
    assert is_legitimately_published(faked, evidence=()) is False
    state, _ = promote(faked, evidence=())
    assert state != RecipeState.PUBLISHED


def test_attack_5c_every_combination_that_should_fail_never_reaches_published() -> None:
    tool_pass = _tool_pass_evidence()
    vendor_pass = _tool_pass_evidence(origin="vendor")
    user_pass = _tool_pass_evidence(origin="user")

    recipe_ok = _full_recipe()
    recipe_no_rollback = _full_recipe(rollback=None)
    recipe_no_reviewers = _full_recipe(reviewers=())

    # Mỗi recipe bên dưới MANG state=PUBLISHED trực tiếp (mô phỏng AI/kẻ tấn
    # công cố ghi đè field) để chắc chắn is_legitimately_published không bị
    # nhãn đó ảnh hưởng — gate phải tính lại từ evidence+approver+business_ok.
    def faked_published(recipe: CompatibilityRecipe) -> CompatibilityRecipe:
        from dataclasses import replace

        return replace(recipe, state=RecipeState.PUBLISHED)

    should_fail_combinations: list[
        tuple[str, CompatibilityRecipe, tuple[TrustEvidence, ...], str | None, bool]
    ] = [
        ("no_evidence", recipe_ok, (), "approver-1", True),
        ("vendor_only_evidence", recipe_ok, (vendor_pass,), "approver-1", True),
        ("user_only_evidence", recipe_ok, (user_pass,), "approver-1", True),
        ("tool_pass_no_approver", recipe_ok, (tool_pass,), None, True),
        ("approver_but_no_reviewers", recipe_no_reviewers, (tool_pass,), "approver-1", True),
        ("reviewers_but_business_not_ok", recipe_ok, (tool_pass,), "approver-1", False),
        ("structural_gap_missing_rollback", recipe_no_rollback, (tool_pass,), "approver-1", True),
        # tổ hợp rỗng toàn diện: không gì cả
        ("nothing_at_all", recipe_ok, (), None, False),
    ]

    for name, recipe, evidence, approver, business_ok in should_fail_combinations:
        recipe_with_fake_label = faked_published(recipe)
        state, _reason = promote(
            recipe_with_fake_label, evidence=evidence, approver=approver, business_ok=business_ok
        )
        assert state != RecipeState.PUBLISHED, f"HOLE [{name}]: promote() trả PUBLISHED"
        legit = is_legitimately_published(
            recipe_with_fake_label, evidence=evidence, approver=approver, business_ok=business_ok
        )
        assert legit is False, f"HOLE [{name}]: is_legitimately_published trả True"

    # Đối chứng dương: tổ hợp ĐẦY ĐỦ hợp lệ PHẢI tới published — nếu không,
    # bài test trên là vô nghĩa (gate không bao giờ mở được thì không chứng
    # minh được gì về việc nó có "mở sai" hay không).
    legit_state, _ = promote(
        recipe_ok, evidence=(tool_pass,), approver="approver-1", business_ok=True
    )
    assert legit_state == RecipeState.PUBLISHED, "sanity: tổ hợp đầy đủ hợp lệ phải published được"
    assert is_legitimately_published(
        recipe_ok, evidence=(tool_pass,), approver="approver-1", business_ok=True
    )


# ---------------------------------------------------------------------------
# Attack 6 — evidence quá hạn / giả mạo → needs_retest, KHÔNG BAO GIỜ pass.
#
# 6a. ``valid_until`` trong quá khứ so với ``now`` tường minh → NEEDS_RETEST.
# 6b. ``valid_until`` hỏng dạng ("2026-13-99" tháng không tồn tại, "soon"
#     không phải ISO) → coi là quá hạn (không tin), không lọt qua.
# 6c. Ngày không zero-pad ("2026-1-5") trên Python 3.11 này PHẢI raise ở
#     parse (không "trùng khớp nhầm" một ngày khác) → bị coi quá hạn, không
#     được phép "trôi qua" như một ngày còn hạn ("fresh").
# 6d. (xfail HOLE) gọi ``promote``/``is_legitimately_published`` mà KHÔNG
#     truyền ``now`` (mặc định ``None``) — evidence_expired() trả về False
#     vô điều kiện khi thiếu ``now`` (xem ``if not now: return False`` trong
#     promotion.py), nghĩa là evidence với ``valid_until`` đã quá hạn THẬT
#     (năm 2000) vẫn được coi là "còn hạn" và CÓ THỂ publish được nếu caller
#     quên truyền đồng hồ thật — vi phạm lời hứa "evidence quá hạn → luôn
#     needs_retest" một cách vô điều kiện.
# ---------------------------------------------------------------------------


def test_attack_6a_expired_evidence_vs_explicit_now_is_needs_retest() -> None:
    recipe_ok = _full_recipe()
    expired = _tool_pass_evidence(valid_until="2020-01-01")

    state, _reason = promote(
        recipe_ok, evidence=(expired,), approver="approver-1", business_ok=True, now="2026-11-04"
    )
    assert state == RecipeState.NEEDS_RETEST
    assert (
        is_legitimately_published(
            recipe_ok,
            evidence=(expired,),
            approver="approver-1",
            business_ok=True,
            now="2026-11-04",
        )
        is False
    )

    # Đối chứng: cùng evidence nhưng valid_until CÒN hạn (tương lai so với
    # now) → không bị needs_retest vì lý do hạn (có thể published được).
    still_valid = _tool_pass_evidence(valid_until="2030-01-01")
    state2, _ = promote(
        recipe_ok,
        evidence=(still_valid,),
        approver="approver-1",
        business_ok=True,
        now="2026-11-04",
    )
    assert state2 == RecipeState.PUBLISHED


@pytest.mark.parametrize("bad_valid_until", ["2026-13-99", "soon"])
def test_attack_6b_malformed_valid_until_treated_as_expired_not_trusted(
    bad_valid_until: str,
) -> None:
    recipe_ok = _full_recipe()
    malformed = _tool_pass_evidence(valid_until=bad_valid_until)

    state, _ = promote(
        recipe_ok, evidence=(malformed,), approver="approver-1", business_ok=True, now="2026-11-04"
    )
    assert state == RecipeState.NEEDS_RETEST, (
        f"HOLE: valid_until hỏng ({bad_valid_until!r}) không bị coi là quá hạn, " f"state={state!r}"
    )
    assert (
        is_legitimately_published(
            recipe_ok,
            evidence=(malformed,),
            approver="approver-1",
            business_ok=True,
            now="2026-11-04",
        )
        is False
    )


def test_attack_6c_non_zero_padded_date_does_not_slip_through_as_fresh() -> None:
    recipe_ok = _full_recipe()
    # "2026-1-5" không phải ISO-8601 hợp lệ trên Python 3.11 (fromisoformat
    # đòi zero-pad) — PHẢI bị coi là hỏng/quá hạn, không được "trùng khớp
    # nhầm" vào một ngày hợp lệ rồi bị so sánh sai thành "còn hạn".
    bare_date_evidence = _tool_pass_evidence(valid_until="2026-1-5")

    state, _ = promote(
        recipe_ok,
        evidence=(bare_date_evidence,),
        approver="approver-1",
        business_ok=True,
        now="2026-11-04",
    )
    assert (
        state == RecipeState.NEEDS_RETEST
    ), f"HOLE: ngày không zero-pad '2026-1-5' lọt qua như còn hạn, state={state!r}"


def test_attack_6d_omitting_now_silently_bypasses_expiry_check() -> None:
    recipe_ok = _full_recipe()
    # valid_until năm 2000 — quá hạn theo BẤT KỲ đồng hồ thật hợp lý nào.
    clearly_expired = _tool_pass_evidence(valid_until="2000-01-01")

    # `now` KHÔNG được truyền — mô phỏng một caller quên wiring đồng hồ thật.
    state, _reason = promote(
        recipe_ok, evidence=(clearly_expired,), approver="approver-1", business_ok=True
    )
    assert state == RecipeState.NEEDS_RETEST, (
        f"HOLE: thiếu `now` làm evidence quá hạn (valid_until=2000-01-01) "
        f"không bị needs_retest — state thực tế = {state!r}"
    )


# ---------------------------------------------------------------------------
# Attack 7 — supply-chain: http (không TLS), thiếu hash, miền không chính
# thức, và đặc biệt một domain "giống" (lookalike) PHẢI bị từ chối chứ
# không được khớp nhầm theo kiểu "chứa chuỗi con" (substring match).
# ---------------------------------------------------------------------------


def test_attack_7_supply_chain_rejects_unofficial_and_hashless_sources() -> None:
    official = ("misa.vn",)

    # Baseline hợp lệ: https + hash + đúng miền chính thức → không vấn đề.
    assert (
        check_supply_chain("https://misa.vn/app.exe", "sha256:abc", official_hosts=official) == []
    )

    # http (không TLS) → từ chối.
    problems_http = check_supply_chain(
        "http://misa.vn/app.exe", "sha256:abc", official_hosts=official
    )
    assert problems_http, "HOLE: http:// không bị từ chối"

    # Thiếu hash → từ chối.
    problems_no_hash = check_supply_chain("https://misa.vn/app.exe", "", official_hosts=official)
    assert problems_no_hash, "HOLE: thiếu app_hash không bị từ chối"

    # Miền hoàn toàn khác → từ chối.
    problems_other_domain = check_supply_chain(
        "https://totally-random-site.example/app.exe", "sha256:abc", official_hosts=official
    )
    assert problems_other_domain, "HOLE: miền không chính thức không bị từ chối"

    # Domain GIỐNG (lookalike) "misa.vn.evil.com" — chứa "misa.vn" như một
    # tiền tố subdomain giả, cố lách allowlist bằng substring. PHẢI bị từ
    # chối — so khớp phải là EXACT netloc, không phải "contains"/"startswith".
    problems_lookalike = check_supply_chain(
        "https://misa.vn.evil.com/app.exe", "sha256:abc", official_hosts=official
    )
    assert (
        problems_lookalike
    ), "HOLE: domain lookalike 'misa.vn.evil.com' lọt qua allowlist 'misa.vn'"

    # Biến thể lookalike khác: miền chính thức làm SUFFIX ("evil-misa.vn").
    problems_suffix_lookalike = check_supply_chain(
        "https://evil-misa.vn/app.exe", "sha256:abc", official_hosts=official
    )
    assert (
        problems_suffix_lookalike
    ), "HOLE: domain lookalike 'evil-misa.vn' lọt qua allowlist 'misa.vn'"


# ---------------------------------------------------------------------------
# Attack 8 — recipe một kiến trúc KHÔNG tự áp sang kiến trúc khác: x86 không
# áp x86_64; x86_64 không áp arm64; chỉ đúng kiến trúc (case/space chuẩn hoá)
# mới áp được.
# ---------------------------------------------------------------------------


def test_attack_8_recipe_never_crosses_architecture() -> None:
    recipe_x86 = new_candidate(
        "r-x86",
        publisher="p",
        source_url="https://misa.vn/x",
        app_id="a",
        app_version="1.0",
        app_hash="h",
        architecture="x86",
        runner="wine",
        runtime="win32",
    )
    assert arch_applies(recipe_x86, "x86") is True
    assert arch_applies(recipe_x86, "x86_64") is False, "HOLE: recipe x86 tự áp được cho x86_64"
    assert arch_applies(recipe_x86, "arm64") is False

    recipe_x64 = new_candidate(
        "r-x64",
        publisher="p",
        source_url="https://misa.vn/x",
        app_id="a",
        app_version="1.0",
        app_hash="h",
        architecture="x86_64",
        runner="wine",
        runtime="win32",
    )
    assert arch_applies(recipe_x64, "x86_64") is True
    assert arch_applies(recipe_x64, "arm64") is False, "HOLE: recipe x86_64 tự áp được cho arm64"
    assert arch_applies(recipe_x64, "x86") is False

    # Chuẩn hoá hoa/thường/khoảng trắng vẫn phải khớp ĐÚNG kiến trúc, không
    # phải "khớp lỏng" cho phép kiến trúc khác đi qua.
    assert arch_applies(recipe_x64, "  X86_64  ") is True
    assert arch_applies(recipe_x64, "X86") is False


# ---------------------------------------------------------------------------
# Attack 9 — đổi bất kỳ thành phần khóa hồi quy → recipe liên quan chuyển
# needs_retest; khóa giống nhau tuyệt đối → giữ nguyên state.
# ---------------------------------------------------------------------------


def test_attack_9_regression_key_change_forces_needs_retest() -> None:
    recipe = _full_recipe(state=RecipeState.LAB_PASSED)

    old_key = RegressionKey(
        os_build="build-1", model_version="m1", wine_runtime="wine-8.0", app_version="1.0"
    )

    # Đổi wine_runtime (trường hay bị "tiện tay" nâng cấp mà quên retest).
    new_wine = RegressionKey(
        os_build="build-1", model_version="m1", wine_runtime="wine-9.0", app_version="1.0"
    )
    assert "wine_runtime" in changed_components(old_key, new_wine)
    out1 = apply_regression(recipe, old=old_key, new=new_wine)
    assert out1.state == RecipeState.NEEDS_RETEST, "HOLE: đổi wine_runtime không ép needs_retest"

    # Đổi model_version (AI model nâng cấp).
    new_model = RegressionKey(
        os_build="build-1", model_version="m2", wine_runtime="wine-8.0", app_version="1.0"
    )
    assert "model_version" in changed_components(old_key, new_model)
    out2 = apply_regression(recipe, old=old_key, new=new_model)
    assert out2.state == RecipeState.NEEDS_RETEST, "HOLE: đổi model_version không ép needs_retest"

    # Đổi app_version (app nâng cấp bản).
    new_appver = RegressionKey(
        os_build="build-1", model_version="m1", wine_runtime="wine-8.0", app_version="2.0"
    )
    assert "app_version" in changed_components(old_key, new_appver)
    out3 = apply_regression(recipe, old=old_key, new=new_appver)
    assert out3.state == RecipeState.NEEDS_RETEST, "HOLE: đổi app_version không ép needs_retest"

    # Khóa GIỐNG NHAU TUYỆT ĐỐI → không có thành phần đổi → state giữ nguyên
    # (không bị ép needs_retest một cách vô căn cứ).
    identical = RegressionKey(
        os_build="build-1", model_version="m1", wine_runtime="wine-8.0", app_version="1.0"
    )
    out4 = apply_regression(recipe, old=old_key, new=identical)
    assert changed_components(old_key, identical) == ()
    assert out4.state == recipe.state == RecipeState.LAB_PASSED


# ---------------------------------------------------------------------------
# Attack 10 — CLI ``recipe-check`` fail-closed: recipe thiếu
# source_url/app_hash/rollback (changes_system=True) → publishable=False +
# đủ 3 problems; path hỏng/không tồn tại → status error, exit code 2.
# ---------------------------------------------------------------------------


def test_attack_10_cli_recipe_check_fails_closed_on_missing_fields(tmp_path: Path) -> None:
    assert _NAMIOS_BIN.exists(), f"CLI binary không tồn tại: {_NAMIOS_BIN}"

    incomplete = tmp_path / "incomplete_recipe.json"
    incomplete.write_text(
        json.dumps(
            {
                "recipe_id": "r-incomplete",
                "publisher": "someone",
                "app_id": "app-x",
                "app_version": "1.0",
                "architecture": "x86_64",
                "runner": "wine",
                "runtime": "win32",
                "changes_system": True,
                # source_url / app_hash / rollback CỐ Ý thiếu.
            }
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(  # noqa: S603 (binary + args cố định, không có input từ bên ngoài)
        [str(_NAMIOS_BIN), "smartai", "recipe-check", str(incomplete), "--json"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, f"CLI thất bại không mong đợi: {proc.stderr}"
    payload = json.loads(proc.stdout)
    assert payload["status"] == "ok"
    data = payload["data"]
    assert data["publishable"] is False, "HOLE: recipe thiếu field vẫn publishable=True"
    problem_paths = {p["path"] for p in data["problems"]}
    assert problem_paths == {
        "source_url",
        "app_hash",
        "rollback",
    }, f"HOLE: problems không liệt kê đủ 3 path thiếu, thực tế: {problem_paths!r}"


def test_attack_10b_cli_recipe_check_nonexistent_path_errors_exit_2(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist.json"

    proc = subprocess.run(  # noqa: S603 (binary + args cố định, không có input từ bên ngoài)
        [str(_NAMIOS_BIN), "smartai", "recipe-check", str(missing_path), "--json"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert (
        proc.returncode == 2
    ), f"HOLE: path không tồn tại không trả exit code 2 ({proc.returncode})"
    payload = json.loads(proc.stdout)
    assert payload["status"] == "error"
    assert payload["data"] is None
    assert payload["error"]["code"] == "E_INPUT_SCHEMA"


def test_attack_10c_cli_recipe_check_malformed_json_errors_exit_2(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not valid json at all", encoding="utf-8")

    proc = subprocess.run(  # noqa: S603 (binary + args cố định, không có input từ bên ngoài)
        [str(_NAMIOS_BIN), "smartai", "recipe-check", str(malformed), "--json"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 2, f"HOLE: JSON hỏng không trả exit code 2 ({proc.returncode})"
    payload = json.loads(proc.stdout)
    assert payload["status"] == "error"
    assert payload["data"] is None
    assert payload["error"]["code"] == "E_INPUT_SCHEMA"


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-v"]))
