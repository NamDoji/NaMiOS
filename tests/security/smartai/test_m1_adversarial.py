"""SmartAI M1 — kiểm thử đối kháng chẩn đoán (SAI-006/007/008/009).

Mỗi ``test_attack_N_...`` cố tình CÔNG vào MỘT lời hứa an toàn của tầng
chẩn đoán M1 (triage/depgraph/diagnose):

(a) KHÔNG secret/PII nào sống sót vào output triage/diagnosis — redact
    TRƯỚC khi phân loại.
(b) Phân loại trung thực — thiếu runtime KHÁC license; không dấu hiệu →
    ``unknown``; không bao giờ crash trên input bệnh hoạn.
(c) Dependency BẮT BUỘC chưa ``observed`` (hoặc có blocker) LUÔN chặn
    execute — "mở được cửa sổ" KHÔNG đồng nghĩa "xong việc".
(d) Chẩn đoán không bao giờ tự nhận app "đã sửa"/"tương thích".

Nếu một bất biến thật sự SAI, test này PHẢI FAIL (hoặc ``xfail(strict=True)``
với lý do bắt đầu bằng ``"HOLE:"``) — KHÔNG được sửa ``src/`` từ file này.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from namios_smartai import (
    DepKind,
    DepNode,
    Diagnosis,
    ErrorCategory,
    NodeStatus,
    TriageInput,
    build_graph,
    collect_inventory,
    diagnose,
    execute_blockers,
    inventory_from_declared,
    is_execute_blocked,
    triage_error,
)

# Định vị console-script `namios` theo môi trường ĐANG chạy — venv local
# (.venv/bin/namios) HAY CI không có .venv (cùng thư mục bin với interpreter /
# trên PATH). Chạy đúng cả `pytest` local lẫn CI.
_NAMIOS_BIN = Path(shutil.which("namios") or (Path(sys.executable).parent / "namios"))

# ---------------------------------------------------------------------------
# Secrets dùng xuyên suốt — literal rõ ràng để assert ABSENCE (không phải
# giả định tên biến); nếu BẤT KỲ chuỗi này lọt ra ngoài là một lỗ hổng rò
# rỉ dữ liệu nhạy cảm thật.
# ---------------------------------------------------------------------------

_SECRET_PASSWORD = "Hunter2"
_SECRET_TOKEN = "ghp_abc123"
_SECRET_BEARER = "xyz"
_SECRET_OTP = "445566"
_SECRET_PEM_BODY = "MIIBVgIBADAN"
_SECRET_HOME_USER = "ketoan"
_SECRET_CCCD = "012345678901"

_ALL_SECRETS = (
    _SECRET_PASSWORD,
    _SECRET_TOKEN,
    _SECRET_BEARER,
    _SECRET_OTP,
    _SECRET_PEM_BODY,
)


def _poisoned_blob() -> str:
    """Một chuỗi log/crash chứa ĐỦ 5 loại secret (SUP-002 §redactor
    docstring) + một tín hiệu phân loại hợp lệ (SQL Server) để chứng minh
    redaction không phá hỏng khả năng phân loại."""

    return (
        f"connect failed password={_SECRET_PASSWORD} token={_SECRET_TOKEN} "
        f"Authorization: Bearer {_SECRET_BEARER} OTP {_SECRET_OTP} "
        "could not connect to SQL Server\n"
        "-----BEGIN PRIVATE KEY-----\n"
        f"{_SECRET_PEM_BODY}...\n"
        "-----END PRIVATE KEY-----"
    )


def _assert_no_secrets_anywhere(haystack: str, *, secrets: tuple[str, ...] = _ALL_SECRETS) -> None:
    for secret in secrets:
        assert secret not in haystack, f"HOLE: secret literal {secret!r} leaked into: {haystack!r}"


# ---------------------------------------------------------------------------
# Attack 1 — secret leak qua ``log_text``: password/token/Bearer/OTP/PEM.
# Phải bị redact TRƯỚC phân loại; phân loại vẫn đúng (SQL Server → DB).
# ---------------------------------------------------------------------------


def test_attack_1_secret_leak_via_log_text_all_redacted() -> None:
    result = triage_error(TriageInput(log_text=_poisoned_blob()))

    _assert_no_secrets_anywhere(result.redacted_log)
    for ev in result.evidence_vi:
        _assert_no_secrets_anywhere(ev)
    _assert_no_secrets_anywhere(str(result))

    assert "[REDACTED]" in result.redacted_log
    # Tín hiệu "SQL Server" vẫn sống sót sau redact → phân loại đúng nhóm.
    assert result.category == ErrorCategory.DB_UNREACHABLE


# ---------------------------------------------------------------------------
# Attack 2 — secret leak qua ``crash_signature`` (không phải log_text).
# TriageResult KHÔNG có field crash_signature; secret không được lộ qua
# BẤT KỲ field nào của result (bao gồm evidence_vi/source/str()).
# ---------------------------------------------------------------------------


def test_attack_2_secret_leak_via_crash_signature_all_redacted() -> None:
    result = triage_error(TriageInput(crash_signature=_poisoned_blob()))

    _assert_no_secrets_anywhere(result.redacted_log)
    _assert_no_secrets_anywhere(result.source)
    for ev in result.evidence_vi:
        _assert_no_secrets_anywhere(ev)
    _assert_no_secrets_anywhere(str(result))

    # Vẫn phân loại đúng dù tín hiệu nằm trong crash_signature, không phải
    # log_text — haystack phân loại gộp cả hai trường.
    assert result.category == ErrorCategory.DB_UNREACHABLE


# ---------------------------------------------------------------------------
# Attack 3 — đường dẫn home cá nhân + CCCD (PII) trong log_text.
# ``/home/<user>`` PHẢI bị che; redactor không có quy tắc cho CCCD (chỉ
# OTP/password/token/Bearer/IP nội bộ/home path theo docstring redactor.py)
# — assert đúng phạm vi đã CÔNG BỐ, không giả định quá tay.
# ---------------------------------------------------------------------------


def test_attack_3_private_home_path_redacted() -> None:
    log = f"read /home/{_SECRET_HOME_USER}/so_cai.mdb failed; CCCD {_SECRET_CCCD}"
    result = triage_error(TriageInput(log_text=log))

    assert f"/home/{_SECRET_HOME_USER}" not in result.redacted_log
    assert "/home/[REDACTED]" in result.redacted_log


# ---------------------------------------------------------------------------
# Attack 4 — secret leak xuyên suốt ``diagnose()`` VÀ qua CLI thật
# (subprocess, không mock) — đường thoát thực tế mà người dùng cuối nhìn
# thấy (stdout JSON của ``namios smartai diagnose``).
# ---------------------------------------------------------------------------


def test_attack_4_secret_leak_via_diagnose_and_cli() -> None:
    secret_log = f"password={_SECRET_PASSWORD} could not connect to SQL Server"

    diagnosis = diagnose("w", triage_input=TriageInput(log_text=secret_log))
    assert _SECRET_PASSWORD not in str(diagnosis)
    assert diagnosis.triage is not None
    assert diagnosis.triage.category == ErrorCategory.DB_UNREACHABLE

    assert _NAMIOS_BIN.exists(), f"CLI binary không tồn tại: {_NAMIOS_BIN}"
    proc = subprocess.run(  # noqa: S603 (binary + args cố định, không có input từ bên ngoài)
        [str(_NAMIOS_BIN), "smartai", "diagnose", secret_log, "--json"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, f"CLI thất bại: {proc.stderr}"
    assert (
        _SECRET_PASSWORD not in proc.stdout
    ), f"HOLE: secret lộ ra stdout CLI thật: {proc.stdout!r}"
    payload = json.loads(proc.stdout)
    assert payload["data"]["category"] == "db_unreachable"
    assert _SECRET_PASSWORD not in json.dumps(payload)


# ---------------------------------------------------------------------------
# Attack 5 — missing-dll KHÁC license; license thuần vẫn phân loại
# LICENSE; "chạy xong bình thường" (không dấu hiệu) → unknown, confidence
# 0.0 (không bịa).
# ---------------------------------------------------------------------------


def test_attack_5_missing_runtime_distinct_from_license_and_unknown_when_no_signal() -> None:
    missing_dll = triage_error(TriageInput(log_text="api-ms-win-core.dll not found"))
    assert missing_dll.category == ErrorCategory.MISSING_RUNTIME

    pure_license = triage_error(
        TriageInput(log_text="License activation expired, please enter a valid product key")
    )
    assert pure_license.category == ErrorCategory.LICENSE
    assert pure_license.category != ErrorCategory.MISSING_RUNTIME

    benign = triage_error(TriageInput(log_text="done successfully"))
    assert benign.category == ErrorCategory.UNKNOWN
    assert benign.confidence == 0.0


# ---------------------------------------------------------------------------
# Attack 6 — không bao giờ crash: input bệnh hoạn (rỗng, 100k ký tự,
# unicode/control char, None tường minh, bytes ngẫu nhiên đã decode).
# ---------------------------------------------------------------------------


def test_attack_6_never_crashes_on_pathological_input() -> None:
    long_blob = "x" * 100_000
    unicode_blob = "emoji \U0001f600 rtl ‮ tab\tnewline\nnull\x00bell\x07"
    random_bytes_blob = os.urandom(2048).decode("latin-1")

    pathological_logs: tuple[str | None, ...] = (
        "",
        long_blob,
        unicode_blob,
        random_bytes_blob,
        None,  # type: ignore[list-item]  # caller có thể truyền None dù hint là str
    )

    for log in pathological_logs:
        result = triage_error(TriageInput(log_text=log))  # type: ignore[arg-type]
        assert isinstance(result.category, ErrorCategory)
        assert 0.0 <= result.confidence <= 1.0

    for sig in pathological_logs:
        result = triage_error(TriageInput(crash_signature=sig))  # type: ignore[arg-type]
        assert isinstance(result.category, ErrorCategory)

    # Cả hai field bệnh hoạn CÙNG LÚC — không có đường nào raise.
    result = triage_error(
        TriageInput(log_text=unicode_blob, crash_signature=random_bytes_blob, exit_code=-1)
    )
    assert isinstance(result.category, ErrorCategory)


# ---------------------------------------------------------------------------
# Attack 7 — execute-block KHÔNG được bypass: mọi trạng thái node bắt buộc
# khác ``observed`` (sạch, không blocker) PHẢI chặn. Quét toàn bộ tổ hợp
# NodeStatus × {có blocker, không blocker} cho node ``required=True``.
# ---------------------------------------------------------------------------


def test_attack_7_execute_block_cannot_be_bypassed() -> None:
    def blocked_for(status: NodeStatus, blocker: str | None) -> bool:
        node = DepNode(
            node_id="db-main",
            kind=DepKind.DATABASE,
            status=status,
            required=True,
            blocker=blocker,
        )
        graph = build_graph("w", (node,))
        return is_execute_blocked(graph)

    # UNKNOWN (chưa có tín hiệu gì) → chặn.
    assert blocked_for(NodeStatus.UNKNOWN, None) is True
    # INFERRED (suy luận, KHÔNG xác nhận trực tiếp) → vẫn chặn — inferred
    # không phải observed, "mở app có vẻ ổn nên chắc là DB ổn" không được
    # phép tự động coi là đủ.
    assert blocked_for(NodeStatus.INFERRED, None) is True
    # OBSERVED sạch, không blocker → mới được coi là không chặn.
    assert blocked_for(NodeStatus.OBSERVED, None) is False
    # OBSERVED nhưng CÓ blocker tường minh (vd vendor báo còn lỗi) → vẫn chặn
    # dù status đã observed — blocker luôn thắng.
    assert blocked_for(NodeStatus.OBSERVED, "vendor xác nhận còn lỗi kết nối") is True

    # Quét vét toàn bộ tổ hợp NodeStatus × blocker — bất kỳ tổ hợp nào KHÔNG
    # phải (OBSERVED, không blocker) đều phải chặn; không có "lỗ" nào sót.
    for status in NodeStatus:
        for blocker in (None, "something is wrong"):
            expect_blocked = not (status is NodeStatus.OBSERVED and blocker is None)
            got = blocked_for(status, blocker)
            assert got == expect_blocked, (
                f"HOLE: required node status={status!r} blocker={blocker!r} "
                f"trả is_execute_blocked={got}, kỳ vọng {expect_blocked}"
            )

    # Node KHÔNG required ở trạng thái xấu nhất không được chặn gì cả —
    # chỉ node bắt buộc mới có quyền chặn execute.
    optional_node = DepNode(
        node_id="nice-to-have",
        kind=DepKind.BROWSER,
        status=NodeStatus.UNKNOWN,
        required=False,
        blocker="optional thing broken",
    )
    assert is_execute_blocked(build_graph("w", (optional_node,))) is False
    assert execute_blockers(build_graph("w", (optional_node,))) == ()


# ---------------------------------------------------------------------------
# Attack 8 — ``diagnose()`` trung thực khi KHÔNG có đầu vào nào: route
# chưa kiểm chứng = True, execute KHÔNG bị gán blocked giả (không bịa ra
# blocker không có cơ sở), và suggested_action_vi không chứa từ ngữ ngụ ý
# "đã xong"/"tương thích". ``Diagnosis`` không có field nào là một tuyên
# bố "tương thích" dương tính (chỉ triage/blockers/route/suggested/findings).
# ---------------------------------------------------------------------------

_FORBIDDEN_SUCCESS_WORDS = (
    "completed",
    "compatible",
    "đã sửa",
    "đã khắc phục",
    "tương thích",
    "hoàn tất",
    "hoàn thành",
    "fixed",
    "resolved",
)


def test_attack_8_diagnose_with_no_inputs_is_honest_not_a_success_claim() -> None:
    d = diagnose("w")

    assert d.route_no_verified is True
    assert d.execute_blocked is False
    assert d.suggested_action_vi, "phải luôn đề xuất bước kế, không được rỗng"

    lowered = d.suggested_action_vi.lower()
    for word in _FORBIDDEN_SUCCESS_WORDS:
        assert word not in lowered, (
            f"HOLE: suggested_action_vi ngụ ý thành công ('{word}'): " f"{d.suggested_action_vi!r}"
        )
    for finding in d.findings_vi:
        lowered_finding = finding.lower()
        for word in _FORBIDDEN_SUCCESS_WORDS:
            assert (
                word not in lowered_finding
            ), f"HOLE: findings_vi ngụ ý thành công ('{word}'): {finding!r}"

    # Không field nào trên Diagnosis là một "cờ tương thích" dương tính độc
    # lập (vd is_fixed/is_compatible/app_works) — bộ field cố định, đóng kín.
    field_names = {f.name for f in dataclasses.fields(Diagnosis)}
    expected_fields = {
        "workflow_id",
        "triage",
        "execute_blocked",
        "depgraph_blockers",
        "route_recommended",
        "route_no_verified",
        "inventory_read_fields",
        "findings_vi",
        "suggested_action_vi",
        "blockers",
    }
    assert field_names == expected_fields, (
        f"HOLE: Diagnosis có field mới ngoài hợp đồng đã biết: " f"{field_names - expected_fields}"
    )
    forbidden_field_name_fragments = ("is_fixed", "is_compatible", "works", "success", "resolved")
    for name in field_names:
        for frag in forbidden_field_name_fragments:
            assert frag not in name.lower(), f"HOLE: field {name!r} có vẻ là tuyên bố tương thích"


# ---------------------------------------------------------------------------
# Attack 9 — inventory scope: vùng cá nhân LUÔN bị từ chối đọc; mọi
# read_fields phải khai báo nguồn rõ ràng (``declared.*``/``host.*``), không
# có trường "đọc ngầm" nào không rõ nguồn.
# ---------------------------------------------------------------------------


def test_attack_9_inventory_never_reads_personal_scope() -> None:
    expected_personal_areas = {"home_documents", "file_contents", "accounting_data"}

    declared = inventory_from_declared(app_id="x")
    assert expected_personal_areas.issubset(set(declared.out_of_scope))
    for field_ in declared.read_fields:
        assert field_.startswith(
            ("declared.", "host.")
        ), f"HOLE: read_fields trường không rõ nguồn: {field_!r}"

    collected = collect_inventory(app_id="x")
    assert expected_personal_areas.issubset(set(collected.out_of_scope))
    for field_ in collected.read_fields:
        assert field_.startswith(
            ("declared.", "host.")
        ), f"HOLE: read_fields trường không rõ nguồn: {field_!r}"

    # Thử "cám dỗ" API bằng cách khai báo thiết bị/token/runtime phong phú —
    # out_of_scope vẫn phải còn nguyên bộ vùng cá nhân, không bị thu hẹp
    # hay quên mất một vùng nào vì có nhiều input khai báo khác.
    rich = inventory_from_declared(
        app_id="misa",
        app_version="2024.1",
        runtime="dotnet",
        browser="chrome",
        devices=("printer-1",),
        printers=("hp-laser",),
        tokens=("pkcs11-token-1",),
        network_ports=("445",),
    )
    assert expected_personal_areas.issubset(set(rich.out_of_scope))
    assert set(rich.read_fields).issubset(
        {
            "declared.app_id",
            "declared.app_version",
            "declared.runtime",
            "declared.browser",
            "declared.devices",
            "declared.printers",
            "declared.tokens",
            "declared.network_ports",
        }
    )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-v"]))
