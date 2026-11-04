"""SmartAI M3/M4 — kiểm thử đối kháng quản trị & kiểm soát an toàn
(SAI-014/022/035/037). Đây là yêu cầu "Adversarial Evaluation" SAI-032 áp cho
Kill Switch + Multiuser Administration + Vendor Pack + Submission Idempotency.

Mỗi ``test_attack_N_...`` cố tình CÔNG vào MỘT lời hứa an toàn:

(a) Kill Switch chặn THẬT một target bị tắt + một LỚP bị tắt bằng wildcard —
    không có trick casing/tên biến thể nào bypass được; release block là
    STICKY (không tự xoá).
(b) Leo thang quyền XUYÊN ĐƠN VỊ là KHÔNG THỂ — một principal chỉ sửa/duyệt/
    đọc-log cho ĐÚNG đơn vị của mình, và chỉ khi có MEMBERSHIP thật (role
    không tự đồng nghĩa quyền).
(c) Vendor Pack KHÔNG BAO GIỜ rò rỉ secret/PII, KHÔNG có hàm tự gửi/liên hệ;
    trạng thái hợp tác không thể bị ép thành "vendor_approved" bằng giá trị
    giả.
(d) Một lượt gửi KHÔNG BAO GIỜ tự gửi lại, và chỉ "hoàn thành" khi có biên
    nhận ĐƯỢC KIỂM.

Nếu một bất biến thật sự SAI, test này PHẢI FAIL (hoặc ``xfail(strict=True)``
với lý do bắt đầu bằng ``"HOLE:"``) — KHÔNG được sửa ``src/`` từ file này.
"""

from __future__ import annotations

import sys

import pytest

from namios_smartai import (
    Principal,
    SubmissionStatus,
    SwitchTarget,
    UnitPolicy,
    begin_submission,
    build_vendor_pack,
    can_approve_r3_r4,
    can_edit_policy,
    can_read_logs,
    confirm,
    is_complete,
    is_safe_to_share,
    mark_ambiguous,
    should_auto_resend,
)
from namios_smartai.kill_switch import WILDCARD, KillSwitch

ST = SwitchTarget

# ---------------------------------------------------------------------------
# Attack 1 — Kill switch chặn THẬT một target cụ thể bị tắt; target khác
# trong CÙNG lớp (vd tool khác) không bị ảnh hưởng; enable() hoàn tác đúng.
# ---------------------------------------------------------------------------


def test_attack_1_kill_switch_blocks_disabled_target_only() -> None:
    ks = KillSwitch()

    assert ks.is_enabled(ST.TOOL, "run_test") is True
    assert ks.guard(ST.TOOL, "run_test") is None

    ks.disable(ST.TOOL, "run_test")

    assert ks.is_enabled(ST.TOOL, "run_test") is False
    reason = ks.guard(ST.TOOL, "run_test")
    assert reason is not None, "HOLE: tool bị disable nhưng guard() vẫn trả None (không chặn)"
    assert reason  # lý do không rỗng — caller biết VÌ SAO bị chặn

    # Tool KHÁC trong cùng lớp TOOL không bị "lây" — chỉ đúng tên bị tắt.
    assert ks.is_enabled(ST.TOOL, "preflight") is True
    assert ks.guard(ST.TOOL, "preflight") is None

    # enable() hoàn tác đúng — không để trạng thái "dính" mãi.
    ks.enable(ST.TOOL, "run_test")
    assert ks.is_enabled(ST.TOOL, "run_test") is True
    assert ks.guard(ST.TOOL, "run_test") is None


# ---------------------------------------------------------------------------
# Attack 2 — Wildcard tắt CẢ LỚP: mọi tên dưới AUTO_REPAIR bị chặn, kể cả tên
# chưa từng được disable riêng lẻ. Một enable() chỉ-định cho MỘT tên cụ thể
# KHÔNG được mở khoá trong khi wildcard còn set (wildcard phải THẮNG). Tắt
# một lớp không được "tràn" sang lớp khác (vd MODEL_PROVIDER vẫn bình thường).
# ---------------------------------------------------------------------------


def test_attack_2_wildcard_disables_whole_class_and_dominates_specific_enable() -> None:
    ks = KillSwitch()
    ks.disable(ST.AUTO_REPAIR, WILDCARD)

    for name in ("candidate-1", "fix-registry", "x", "anything-never-seen-before"):
        assert (
            ks.is_enabled(ST.AUTO_REPAIR, name) is False
        ), f"HOLE: wildcard AUTO_REPAIR bật nhưng tên {name!r} vẫn is_enabled=True"
        assert ks.guard(ST.AUTO_REPAIR, name) is not None

    # Cố lách: enable() một tên CỤ THỂ trong khi wildcard còn set — phải
    # KHÔNG mở khoá được (wildcard thắng tuyệt đối, không phải "danh sách
    # loại trừ" lọt qua).
    ks.enable(ST.AUTO_REPAIR, "x")
    assert ks.is_enabled(ST.AUTO_REPAIR, "x") is False, (
        "HOLE: enable() một tên cụ thể đã mở khoá được AUTO_REPAIR dù wildcard "
        "vẫn đang tắt cả lớp — wildcard phải luôn thắng"
    )
    assert ks.guard(ST.AUTO_REPAIR, "x") is not None

    # Tắt một LỚP không được rò rỉ / tràn sang lớp khác hoàn toàn riêng biệt.
    assert ks.is_enabled(ST.MODEL_PROVIDER, "anything") is True
    assert ks.guard(ST.MODEL_PROVIDER, "anything") is None
    assert ks.is_enabled(ST.RELEASE_RING, WILDCARD) is True


# ---------------------------------------------------------------------------
# Attack 3 — Không có trick-tên nào bypass một target đã bị disable: so khớp
# PHẢI là EXACT STRING. Tên biến thể (khoảng trắng/xuống dòng/hoa-thường)
# được coi là MỘT TÊN KHÁC — nghĩa là (1) chúng KHÔNG vô tình bị tắt lây, và
# (2) kẻ tấn công KHÔNG thể gửi biến thể của tên đã-bị-tắt để né guard (vì
# guard luôn đối chiếu đúng chuỗi được truyền — gọi lại CHÍNH XÁC "r1" vẫn bị
# chặn, không có đường "đi vòng" bằng cách đổi chuỗi).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variant", ["r1 ", "R1", "r1\n", " r1", "r1\t"])
def test_attack_3_no_name_trick_bypass_exact_string_match(variant: str) -> None:
    ks = KillSwitch()
    ks.disable(ST.RECIPE, "r1")

    # Target thật sự bị tắt — gọi lại ĐÚNG TÊN "r1" luôn luôn bị chặn, không
    # có cách nào (kể cả thử các biến thể trước) làm nó "tự mở" trở lại.
    assert ks.guard(ST.RECIPE, "r1") is not None
    assert ks.is_enabled(ST.RECIPE, "r1") is False

    # Biến thể là MỘT TÊN KHÁC theo đúng nghĩa đen — is_enabled() PHẢI đối
    # xử độc lập: nếu khớp mờ (case-insensitive / strip) nó sẽ SAI THEO MỘT
    # TRONG HAI HƯỚNG — hoặc vô tình chặn nhầm thứ không liên quan (đã bị
    # disable "r1" nhưng strip() lại chặn "r1 ") hoặc (nguy hiểm hơn) accept
    # kiểu match lỏng ở legacy code path khác dẫn tới việc disable(" R1 ")
    # không chặn được "r1" thật. Khẳng định so khớp là exact-string tất định:
    assert ks.is_enabled(ST.RECIPE, variant) is True, (
        f"HOLE: biến thể tên {variant!r} bị is_enabled=False dù chỉ 'r1' bị "
        "disable — so khớp không phải exact-string (có thể gây false-positive "
        "chặn nhầm recipe không liên quan)"
    )
    assert ks.guard(ST.RECIPE, variant) is None

    # Và ngược lại: target "r1" vẫn bị khoá dù ta vừa truy vấn các biến thể
    # xung quanh nó — không có side effect nào "dọn dẹp" trạng thái tắt.
    assert ks.guard(ST.RECIPE, "r1") is not None


# ---------------------------------------------------------------------------
# Attack 4 — Release block STICKY: một khi bị chặn (phát hiện sai dữ
# liệu/chữ ký) thì giữ nguyên True mãi, không có auto-clear ngầm; reason
# không rỗng; gọi lại nhiều lần / guard() các target khác không làm nó tự hạ.
# ---------------------------------------------------------------------------


def test_attack_4_release_block_is_sticky_no_auto_clear() -> None:
    ks = KillSwitch()
    assert ks.release_blocked() is False
    assert ks.release_block_reason() == ""

    ks.block_release("bad data")
    assert ks.release_blocked() is True
    assert ks.release_block_reason() == "bad data"

    # KHÔNG có auto-clear: gọi lại release_blocked() nhiều lần, chạm vào các
    # API khác (guard của target hoàn toàn không liên quan, enable/disable
    # target khác) — không có đường nào âm thầm hạ cờ chặn phát hành.
    for _ in range(5):
        assert ks.release_blocked() is True
    ks.enable(ST.TOOL, "unrelated-tool")
    ks.disable(ST.MODEL_PROVIDER, "unrelated-model")
    ks.guard(ST.RECIPE, "unrelated-recipe")
    assert ks.release_blocked() is True, "HOLE: thao tác không liên quan làm release block tự hạ"
    assert ks.release_block_reason() == "bad data"

    # reason mặc định (không truyền) vẫn phải non-empty — không "chặn câm".
    ks2 = KillSwitch()
    ks2.block_release()
    assert ks2.release_blocked() is True
    assert ks2.release_block_reason(), "HOLE: block_release() không reason vẫn để reason rỗng"


# ---------------------------------------------------------------------------
# Attack 5 — Leo thang quyền XUYÊN ĐƠN VỊ là KHÔNG THỂ, NGAY CẢ khi
# user_id trùng khớp hệt với một người có quyền ở đơn vị khác. ĐƠN VỊ phải
# khớp — không phải chỉ user_id.
# ---------------------------------------------------------------------------


def test_attack_5_cross_unit_cannot_edit_or_approve_even_with_matching_user_id() -> None:
    ketoan = UnitPolicy(
        unit_id="ketoan",
        admin_users=("kt",),
        approve_r3_r4_users=("kt",),
    )

    # Principal CÙNG user_id "kt" nhưng ở đơn vị KHÁC ("truong") + role admin
    # — mô phỏng một kẻ tấn công cố "mạo danh" user_id của người có quyền ở
    # đơn vị kế toán, nhưng đang thao tác từ context đơn vị trường.
    impostor = Principal(user_id="kt", unit_id="truong", roles=("admin",))

    assert can_edit_policy(impostor, ketoan) is False, (
        "HOLE: principal khác đơn vị (dù user_id trùng + role admin) vẫn sửa "
        "được chính sách đơn vị khác — leo thang quyền xuyên đơn vị"
    )
    assert can_approve_r3_r4(impostor, ketoan) is False, (
        "HOLE: principal khác đơn vị (dù user_id trùng + role admin) vẫn "
        "duyệt được R3/R4 của đơn vị khác"
    )

    # Đối chứng: CHÍNH người đó, CHÍNH user_id, nhưng ĐÚNG đơn vị ketoan thì
    # phải được phép — nếu không thì bài test này không chứng minh được gì
    # (biết đâu can_edit_policy luôn trả False bất kể gì).
    legit = Principal(user_id="kt", unit_id="ketoan", roles=("admin",))
    assert can_edit_policy(legit, ketoan) is True
    assert can_approve_r3_r4(legit, ketoan) is True


# ---------------------------------------------------------------------------
# Attack 6 — Role alone KHÔNG đồng nghĩa quyền: principal CÙNG đơn vị, role
# "admin" hợp lệ, nhưng user_id KHÔNG nằm trong admin_users/approve_r3_r4_users
# của chính đơn vị đó → vẫn bị từ chối. Membership thật (danh sách uỷ quyền)
# mới là nguồn quyết, không phải chuỗi role tự xưng.
# ---------------------------------------------------------------------------


def test_attack_6_role_alone_is_not_membership() -> None:
    ketoan = UnitPolicy(
        unit_id="ketoan",
        admin_users=("kt-that",),
        approve_r3_r4_users=("kt-duyet",),
    )

    # Cùng đơn vị, tự xưng role "admin", nhưng KHÔNG có trong admin_users.
    fake_admin = Principal(user_id="nguoi-la", unit_id="ketoan", roles=("admin",))
    assert can_edit_policy(fake_admin, ketoan) is False, (
        "HOLE: role='admin' tự xưng (không nằm trong admin_users) vẫn sửa "
        "được chính sách — role không được thay thế membership"
    )

    # Role chứa CẢ hai nhãn admin+helpdesk cũng không giúp gì nếu user_id
    # không được liệt kê — tấn công "spam roles" không có tác dụng.
    fake_admin_multi_role = Principal(
        user_id="nguoi-la-2", unit_id="ketoan", roles=("admin", "helpdesk", "superuser")
    )
    assert can_edit_policy(fake_admin_multi_role, ketoan) is False
    assert can_approve_r3_r4(fake_admin_multi_role, ketoan) is False

    # Đối chứng dương: đúng user_id trong approve_r3_r4_users, dù role rỗng
    # (role không cần thiết khi đã có membership thật trong danh sách).
    legit_approver = Principal(user_id="kt-duyet", unit_id="ketoan", roles=())
    assert can_approve_r3_r4(legit_approver, ketoan) is True


# ---------------------------------------------------------------------------
# Attack 7 — Phạm vi đọc log cho helpdesk: cùng đơn vị + log_collection=True
# mới được đọc; khác đơn vị KHÔNG BAO GIỜ (bất kể log_collection); admin
# cùng đơn vị luôn đọc được dù log_collection=False; role "user" thường
# không bao giờ đọc log dù mọi điều kiện khác thoả.
# ---------------------------------------------------------------------------


def test_attack_7_helpdesk_log_scope_is_unit_and_flag_gated() -> None:
    policy_log_on = UnitPolicy(unit_id="ketoan", admin_users=("kt-admin",), log_collection=True)
    policy_log_off = UnitPolicy(unit_id="ketoan", admin_users=("kt-admin",), log_collection=False)

    same_unit_helpdesk = Principal(user_id="hd1", unit_id="ketoan", roles=("helpdesk",))
    assert can_read_logs(same_unit_helpdesk, policy_log_on) is True
    assert (
        can_read_logs(same_unit_helpdesk, policy_log_off) is False
    ), "HOLE: helpdesk cùng đơn vị đọc được log dù đơn vị tắt log_collection"

    # Khác đơn vị: KHÔNG BAO GIỜ, kể cả khi log_collection=True.
    cross_unit_helpdesk = Principal(user_id="hd2", unit_id="truong", roles=("helpdesk",))
    assert (
        can_read_logs(cross_unit_helpdesk, policy_log_on) is False
    ), "HOLE: helpdesk khác đơn vị vẫn đọc được log dù log_collection=True"

    # Admin cùng đơn vị (trong admin_users) luôn đọc được, bất kể cờ
    # log_collection — quyền admin độc lập với cờ thu-log helpdesk.
    same_unit_admin = Principal(user_id="kt-admin", unit_id="ketoan", roles=("admin",))
    assert (
        can_read_logs(same_unit_admin, policy_log_off) is True
    ), "HOLE: admin cùng đơn vị không đọc được log khi log_collection=False"

    # Role "user" thường: không phải admin, không phải helpdesk — không đọc
    # log dù cùng đơn vị + log_collection=True.
    plain_user = Principal(user_id="nv-thuong", unit_id="ketoan", roles=("user",))
    assert (
        can_read_logs(plain_user, policy_log_on) is False
    ), "HOLE: role 'user' thường vẫn đọc được log — thiếu phân quyền helpdesk/admin"


# ---------------------------------------------------------------------------
# Helper: nguyên liệu log + bí mật dùng xuyên suốt attack 8/9 — literal rõ
# ràng để assert ABSENCE (không phải giả định tên biến); nếu BẤT KỲ chuỗi
# này lọt ra ngoài redacted_logs là một lỗ hổng rò rỉ thật.
# ---------------------------------------------------------------------------

_SECRET_PASSWORD = "Hunter2CorrectHorse"
_SECRET_TOKEN = "ghp_REALTOKEN1xyz"
_SECRET_BEARER = "eyJhbGciSECRETbearer"
_SECRET_PEM_BODY = "MIIBVgIBADANBgkqhkiG9w0BAQEFAASCAfake"
_SECRET_CCCD = "012345678901"


def _vendor_pack(logs: list[str], collaboration: str = "desired"):
    return build_vendor_pack(
        product="MISA",
        version="2024.1",
        environment="wine-9.0",
        raw_logs=logs,
        windows_baseline_result="ok on Windows 11",
        needed_api="ActiveX signing plugin",
        test_cases=["submit a sample invoice"],
        collaboration=collaboration,
    )


# ---------------------------------------------------------------------------
# Attack 8 — Vendor pack redact TOÀN BỘ: password=, token=, Authorization:
# Bearer, khối PEM private key, và CCCD (dãy số dài) — không literal nào
# trong số đó sống sót trong redacted_logs; is_safe_to_share True cho log
# hoàn toàn redact-được.
# ---------------------------------------------------------------------------


def test_attack_8_vendor_pack_redacts_password_token_bearer_pem_pii() -> None:
    pem_block = (
        "-----BEGIN RSA PRIVATE KEY-----\n" f"{_SECRET_PEM_BODY}\n" "-----END RSA PRIVATE KEY-----"
    )
    logs = [
        f"connect failed password={_SECRET_PASSWORD}",
        f"auth retry token={_SECRET_TOKEN}",
        f"Authorization: Bearer {_SECRET_BEARER}",
        pem_block,
        f"khach hang CCCD {_SECRET_CCCD} tu choi dang nhap",
    ]
    pack = _vendor_pack(logs)
    joined = "\n".join(pack.redacted_logs)

    for secret in (
        _SECRET_PASSWORD,
        _SECRET_TOKEN,
        _SECRET_BEARER,
        _SECRET_PEM_BODY,
        _SECRET_CCCD,
        "-----BEGIN RSA PRIVATE KEY-----",
    ):
        assert secret not in joined, f"HOLE: secret/PII {secret!r} còn sót trong redacted_logs"

    assert (
        is_safe_to_share(pack) is True
    ), "HOLE: log hoàn toàn redact-được vẫn bị is_safe_to_share=False"
    assert pack.contains_secrets is False


# ---------------------------------------------------------------------------
# Attack 9 — Secret sống sót qua redact_text() (bare ghp_ token không có
# "token=" đứng trước, nên lớp regex gán-giá-trị bỏ sót) → contains_secrets
# PHẢI True + is_safe_to_share PHẢI False (lớp quét thứ hai của vendorpack
# bắt được, không chỉ dựa một lớp redact). Dãy số dài bất kỳ (không chỉ CCCD)
# cũng phải bị quét sạch khỏi redacted_logs.
# ---------------------------------------------------------------------------


def test_attack_9_surviving_secret_marks_pack_unsafe() -> None:
    bare_token = "ghp_DEADBEEF1234surv"
    # Không có "token"/"password"/... đứng ngay trước dấu ':'/'=' — mô phỏng
    # redact_text() bỏ sót vì không khớp mẫu gán-giá-trị tường minh.
    logs = [f"leaked credential in prose: see value {bare_token} used for API calls"]
    pack = _vendor_pack(logs)

    assert pack.contains_secrets is True, (
        "HOLE: bare ghp_ token sống sót qua redact_text() nhưng vendorpack "
        "không gắn cờ contains_secrets — lớp quét residual không bắt được"
    )
    assert (
        is_safe_to_share(pack) is False
    ), "HOLE: pack còn secret sống sót (ghp_ token) nhưng is_safe_to_share vẫn True"

    # Dãy số dài (>=9 chữ số, không phải CCCD cụ thể) cũng phải bị quét sạch
    # khỏi redacted_logs — ví dụ mã khách hàng/số điện thoại nội bộ dài.
    long_digit_run = "98765432109"
    digit_pack = _vendor_pack([f"internal customer id {long_digit_run} flagged"])
    assert long_digit_run not in "\n".join(
        digit_pack.redacted_logs
    ), f"HOLE: dãy số dài {long_digit_run!r} (>=9 chữ số) không bị scrub khỏi redacted_logs"


# ---------------------------------------------------------------------------
# Attack 10 — KHÔNG có hàm tự gửi/liên hệ vendor trong module; collaboration
# không thể bị ép thành "vendor_approved" bằng giá trị giả/gần-đúng — CHỈ
# đúng chuỗi "vendor_approved" mới được giữ, mọi biến thể khác rơi về mặc
# định bảo thủ "desired".
# ---------------------------------------------------------------------------


def test_attack_10_no_auto_send_function_and_collaboration_not_forgeable() -> None:
    import namios_smartai.vendorpack as vp_module

    public_names = {n for n in dir(vp_module) if not n.startswith("_")}
    forbidden_substrings = ("send", "contact", "submit", "email", "post")
    offenders = {n for n in public_names if any(bad in n.lower() for bad in forbidden_substrings)}
    assert not offenders, f"HOLE: vendorpack có public API nghi tự gửi/liên hệ: {offenders!r}"

    # Giá trị giả/gần-đúng với "vendor_approved" — KHÔNG được chấp nhận.
    for bogus in (
        "vendor_approved_evil",
        "VENDOR_APPROVED",
        " vendor_approved",
        "vendor_approved ",
        "vendor-approved",
        "true",
        "approved",
    ):
        pack = _vendor_pack(["hi"], collaboration=bogus)
        assert pack.collaboration == "desired", (
            f"HOLE: collaboration={bogus!r} (giá trị giả) không bị ép về 'desired', "
            f"thực tế = {pack.collaboration!r}"
        )

    # CHỈ đúng chuỗi chính xác mới được giữ nguyên.
    approved_pack = _vendor_pack(["hi"], collaboration="vendor_approved")
    assert approved_pack.collaboration == "vendor_approved"


# ---------------------------------------------------------------------------
# Attack 11 — Idempotency KHÔNG BAO GIỜ tự gửi lại ở BẤT KỲ trạng thái nào
# (pending/needs_lookup/confirmed); mark_ambiguous() không bao giờ "hoàn
# thành"; confirm() với receipt rỗng/toàn khoảng-trắng không chuyển
# CONFIRMED; hai begin_submission() cùng correlation_id là HAI bản ghi ĐỘC
# LẬP — không có global ẩn khiến xác nhận một bản ghi "lây" sang bản ghi kia
# (tức không có cơ chế ngầm có thể kích hoạt gửi trùng).
# ---------------------------------------------------------------------------


def test_attack_11_idempotency_never_auto_resends_and_requires_real_receipt() -> None:
    pending = begin_submission("corr-x", "vn.tax.sample")
    assert pending.status == SubmissionStatus.PENDING
    assert should_auto_resend(pending) is False

    ambiguous = mark_ambiguous(pending)
    assert ambiguous.status == SubmissionStatus.NEEDS_LOOKUP
    assert should_auto_resend(ambiguous) is False
    assert is_complete(ambiguous) is False

    confirmed = confirm(pending, "RECEIPT-OK-1")
    assert confirmed.status == SubmissionStatus.CONFIRMED
    assert should_auto_resend(confirmed) is False, (
        "HOLE: should_auto_resend()=True cho bản ghi đã CONFIRMED — không được "
        "tự gửi lại ngay cả khi đã xong"
    )
    assert is_complete(confirmed) is True

    # Receipt rỗng / chỉ khoảng trắng → KHÔNG được coi là confirmed.
    for empty_receipt in ("", "   ", "\n", "\t"):
        not_confirmed = confirm(pending, empty_receipt)
        assert (
            not_confirmed.status != SubmissionStatus.CONFIRMED
        ), f"HOLE: receipt={empty_receipt!r} (rỗng/whitespace) vẫn được coi là CONFIRMED"
        assert is_complete(not_confirmed) is False

    # Hai begin_submission() CÙNG correlation_id → hai bản ghi ĐỘC LẬP (dataclass
    # bất biến, không global đăng ký theo correlation_id). Xác nhận bản ghi A
    # không được phép làm thay đổi trạng thái của bản ghi B — nếu có global ẩn
    # theo correlation_id, đây chính là chỗ một lượt gửi trùng có thể bị kích
    # hoạt ngầm.
    rec_a = begin_submission("same-corr", "wf-a")
    rec_b = begin_submission("same-corr", "wf-b")
    assert rec_a.status == SubmissionStatus.PENDING
    assert rec_b.status == SubmissionStatus.PENDING

    rec_a_confirmed = confirm(rec_a, "RECEIPT-A")
    assert rec_a_confirmed.status == SubmissionStatus.CONFIRMED
    # rec_b (bản ghi độc lập, KHÔNG được gán lại từ confirm) phải còn nguyên
    # PENDING — nếu nó "nhảy" theo rec_a thì có global state ẩn nguy hiểm.
    assert rec_b.status == SubmissionStatus.PENDING, (
        "HOLE: xác nhận bản ghi A làm thay đổi trạng thái bản ghi B cùng "
        "correlation_id — nghi có global state ẩn có thể gây gửi trùng"
    )
    assert should_auto_resend(rec_b) is False
    assert should_auto_resend(rec_a_confirmed) is False


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-v"]))
