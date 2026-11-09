# -*- coding: utf-8 -*-
"""Bộ kiểm thử Update Center (PL15 §9) — chạy & pass bằng pytest.

Phủ: luồng hợp lệ; các ca phản công (payload sửa→UPD-003, chữ ký giả→UPD-003,
metadata hết hạn→UPD-004, sai arch/model→UPD-005, thu hồi→UPD-009); preflight
(storage→UPD-002, network→UPD-001, firmware power→UPD-006); bất biến máy trạng
thái (không nhảy cóc, không bypass, completed chỉ sau boot_check); resume sau
đứt tải; resume sau reboot qua journal; idempotency; che bí mật trong log.
"""
import datetime as _dt
import os

import pytest

from sign_test_repo import (
    build_test_repo,
    build_update,
    generate_keypair,
    write_revocation,
)
from update_contract import (
    ContractError,
    IllegalTransition,
    Preflight,
    TransactionJournal,
    UpdateContract,
    UpdateState,
    new_correlation_id,
)
from update_service import (
    DeviceProfile,
    DownloadInterrupted,
    UpdateService,
    redact,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def repo(tmp_path):
    """Repo TEST mới + thông tin khoá cho mỗi test."""
    return build_test_repo(str(tmp_path / "repo"))


@pytest.fixture
def device():
    return DeviceProfile(architecture="x86_64", model="namios-ref-pc",
                         current_deployment="namios-1.0-x86_64-stable-0000")


def make_service(repo, device, tmp_path, policy="auto_download_ask_install"):
    return UpdateService(
        repo["repo"], repo["root_path"], device,
        cache_dir=str(tmp_path / "cache"),
        journal=TransactionJournal(str(tmp_path / "cache" / "journal.jsonl")),
        user_policy=policy,
    )


def drive_to_verify(svc, update_id):
    c = svc.check(update_id)
    c = svc.download(c)
    return svc.verify(c)


# --------------------------------------------------------------------------- #
# 1. Luồng hợp lệ → completed
# --------------------------------------------------------------------------- #
def test_valid_flow_completes(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.VERIFIED
    assert c.signature_status == "verified"
    assert c.error_code is None
    c = svc.preflight(c, storage="pass", power="pass", network="pass")
    c = svc.stage(c)
    c = svc.arm_reboot(c)
    c = svc.boot_check(c, health_ok=True)
    assert c.state == UpdateState.COMPLETED
    assert c.error_code is None


# --------------------------------------------------------------------------- #
# 2. Bảo mật — 100% bị chặn, có mã, không bypass (PL15 §9)
# --------------------------------------------------------------------------- #
def test_tampered_payload_blocked_upd003(repo, device, tmp_path):
    # Sửa payload TẠI CHỖ (giữ nguyên size đã ký) → chữ ký manifest vẫn hợp lệ,
    # nhưng hash payload lệch.
    p = os.path.join(repo["repo"], "targets", f"{repo['update_id']}.payload")
    data = bytearray(open(p, "rb").read())
    data[0:5] = b"EVIL!"
    with open(p, "wb") as fh:
        fh.write(data)
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-003"
    assert c.signature_status == "failed"


def test_bad_signature_blocked_upd003(repo, device, tmp_path):
    # Ký manifest bằng khoá KHÁC (giữ key_id = khoá tin cậy) → chữ ký không khớp.
    attacker_priv, _ = generate_keypair()
    build_update(
        repo["repo"], repo["priv"], repo["pub"],
        update_id=repo["update_id"],
        payload=b"payload bi ky bang khoa gia" * 8,
        sign_with=attacker_priv,
    )
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-003"


def test_expired_metadata_blocked_upd004(repo, device, tmp_path):
    past = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=1)
    build_update(
        repo["repo"], repo["priv"], repo["pub"],
        update_id=repo["update_id"],
        payload=b"payload het han" * 16,
        expires=past,  # chữ ký hợp lệ nhưng hạn đã qua
    )
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-004"


def test_wrong_arch_blocked_upd005(repo, device, tmp_path):
    build_update(
        repo["repo"], repo["priv"], repo["pub"],
        update_id=repo["update_id"],
        payload=b"payload sai kien truc" * 16,
        architecture="aarch64",  # máy là x86_64
    )
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-005"


def test_wrong_model_blocked_upd005(repo, device, tmp_path):
    build_update(
        repo["repo"], repo["priv"], repo["pub"],
        update_id=repo["update_id"],
        payload=b"payload sai model" * 16,
        model_whitelist=["namios-other-pc"],  # máy là namios-ref-pc
    )
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-005"


def test_revoked_blocked_upd009(repo, device, tmp_path):
    write_revocation(
        repo["repo"], repo["priv"], repo["pub"],
        revoked_update_ids=[repo["update_id"]], metadata_version=2,
    )
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-009"


def test_missing_revocation_is_fail_closed_upd009(repo, device, tmp_path):
    # Xoá danh sách thu hồi đã ký → không xác minh được "sạch" → fail-closed.
    os.remove(os.path.join(repo["repo"], "revocation.json"))
    os.remove(os.path.join(repo["repo"], "revocation.sig"))
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-009"


# --------------------------------------------------------------------------- #
# 3. Preflight
# --------------------------------------------------------------------------- #
def test_preflight_storage_fail_upd002(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    c = svc.preflight(c, storage="fail", power="pass", network="pass")
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-002"


def test_preflight_network_fail_upd001(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    c = svc.preflight(c, storage="pass", power="pass", network="fail")
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-001"


def test_preflight_firmware_power_fail_upd006(repo, device, tmp_path):
    # Dựng bản firmware để quy tắc power áp dụng.
    build_update(
        repo["repo"], repo["priv"], repo["pub"],
        update_id="namios-fw-0001", payload=b"fake firmware blob" * 16,
        component="firmware",
    )
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, "namios-fw-0001")
    assert c.state == UpdateState.VERIFIED
    c = svc.preflight(c, storage="pass", power="fail", network="pass")
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-006"


def test_check_network_unreachable_upd001(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    c = svc.check(repo["update_id"], network_reachable=False)
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-001"


# --------------------------------------------------------------------------- #
# 4. Bất biến máy trạng thái — không bypass, không nhảy cóc, completed có điều kiện
# --------------------------------------------------------------------------- #
def test_no_bypass_cannot_stage_blocked(repo, device, tmp_path):
    # Chữ ký giả → blocked; KHÔNG được cài đè.
    attacker_priv, _ = generate_keypair()
    build_update(repo["repo"], repo["priv"], repo["pub"],
                 update_id=repo["update_id"], payload=b"x" * 128, sign_with=attacker_priv)
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED
    with pytest.raises(RuntimeError):
        svc.stage(c)  # không có đường từ blocked sang staged


def test_blocked_is_terminal_no_transition(repo):
    c = UpdateContract(
        update_id="u", component="os", channel="stable", target_build="b",
        architecture="x86_64", metadata_version=1,
        payload_hash="sha256:" + "0" * 64, signature_status="failed",
        preflight=Preflight(), state=UpdateState.BLOCKED, error_code="UPD-003",
        rollback_target="none", user_policy="notify", correlation_id="cid",
    ).validate()
    for target in (UpdateState.STAGED, UpdateState.VERIFIED, UpdateState.COMPLETED,
                   UpdateState.DOWNLOADING):
        with pytest.raises(IllegalTransition):
            c.transition(target)


def test_illegal_skips_rejected():
    c = UpdateContract(
        update_id="u", component="os", channel="stable", target_build="b",
        architecture="x86_64", metadata_version=1,
        payload_hash="sha256:" + "0" * 64, signature_status="unknown",
        preflight=Preflight(), state=UpdateState.AVAILABLE, error_code=None,
        rollback_target="none", user_policy="notify", correlation_id="cid",
    ).validate()
    for target in (UpdateState.VERIFIED, UpdateState.STAGED, UpdateState.COMPLETED,
                   UpdateState.BOOT_CHECK, UpdateState.REBOOT_PENDING):
        with pytest.raises(IllegalTransition):
            c.transition(target)
    # available -> downloading hợp lệ
    assert c.transition(UpdateState.DOWNLOADING).state == UpdateState.DOWNLOADING


def test_completed_only_from_boot_check_health_pass(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    c = svc.preflight(c)
    c = svc.stage(c)
    c = svc.arm_reboot(c)
    # Boot health HỎNG → rolled_back, KHÔNG completed.
    rolled = svc.boot_check(c, health_ok=False)
    assert rolled.state == UpdateState.ROLLED_BACK
    assert rolled.state != UpdateState.COMPLETED


def test_cannot_mark_completed_without_verified_signature():
    # Ép 'verified' khi signature_status != 'verified' phải bị từ chối.
    with pytest.raises(ContractError):
        UpdateContract(
            update_id="u", component="os", channel="stable", target_build="b",
            architecture="x86_64", metadata_version=1,
            payload_hash="sha256:" + "0" * 64, signature_status="unknown",
            preflight=Preflight(), state=UpdateState.VERIFIED, error_code=None,
            rollback_target="none", user_policy="notify", correlation_id="cid",
        ).validate()


# --------------------------------------------------------------------------- #
# 5. Độ tin cậy — resume sau đứt tải; resume sau reboot; idempotency
# --------------------------------------------------------------------------- #
def test_resume_after_download_interrupt(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    c = svc.check(repo["update_id"])
    with pytest.raises(DownloadInterrupted):
        svc.download(c, chunk_size=512, interrupt_after_bytes=1500)
    part = os.path.join(str(tmp_path / "cache"), f"{repo['update_id']}.part")
    assert os.path.exists(part)
    partial = os.path.getsize(part)
    assert 0 < partial < 3200  # giữ phần đã tải
    # Gọi lại: resume từ phần đã có, hoàn tất.
    c = svc.download(c, chunk_size=512)
    c = svc.verify(c)
    assert c.state == UpdateState.VERIFIED  # hash đúng sau khi ghép đủ byte


def test_resume_after_reboot_via_journal(repo, device, tmp_path):
    journal_path = str(tmp_path / "cache" / "journal.jsonl")
    j1 = TransactionJournal(journal_path)
    svc = UpdateService(repo["repo"], repo["root_path"], device,
                        cache_dir=str(tmp_path / "cache"), journal=j1)
    c = drive_to_verify(svc, repo["update_id"])
    c = svc.preflight(c)
    staged = svc.stage(c)
    assert staged.state == UpdateState.STAGED

    # --- Giả lập REBOOT: journal mới trỏ cùng file, dựng lại trạng thái ---
    j2 = TransactionJournal(journal_path)
    resumed = j2.resume(repo["update_id"])
    assert resumed is not None
    assert resumed.state == UpdateState.STAGED
    assert resumed.correlation_id == staged.correlation_id

    svc2 = UpdateService(repo["repo"], repo["root_path"], device,
                         cache_dir=str(tmp_path / "cache"), journal=j2)
    r = svc2.arm_reboot(resumed)
    r = svc2.boot_check(r, health_ok=True)
    assert r.state == UpdateState.COMPLETED


def test_journal_idempotent_commit(tmp_path):
    j = TransactionJournal(str(tmp_path / "j.jsonl"))
    c = UpdateContract(
        update_id="u", component="os", channel="stable", target_build="b",
        architecture="x86_64", metadata_version=1,
        payload_hash="sha256:" + "0" * 64, signature_status="unknown",
        preflight=Preflight(), state=UpdateState.AVAILABLE, error_code=None,
        rollback_target="none", user_policy="notify", correlation_id="cid",
    ).validate()
    wrote1, _ = j.append(c, idempotency_key="k1", note="first")
    wrote2, _ = j.append(c, idempotency_key="k1", note="dup")
    assert wrote1 is True
    assert wrote2 is False  # cùng key → no-op
    assert len(j.records_for("u")) == 1


# --------------------------------------------------------------------------- #
# 6. Che bí mật trong log
# --------------------------------------------------------------------------- #
def test_redaction_masks_secrets():
    raw = (
        "token=supersecret123 Bearer abc.def.ghi "
        "password=hunter2 user /home/cuong/file.txt "
        "ip 192.168.1.50 mac 00:11:22:33:44:55 mail a@b.com "
        "-----BEGIN PRIVATE KEY-----\nAAAA\n-----END PRIVATE KEY-----"
    )
    out = redact(raw)
    assert "supersecret123" not in out
    assert "hunter2" not in out
    assert "abc.def.ghi" not in out
    assert "/home/cuong" not in out
    assert "192.168.1.50" not in out
    assert "00:11:22:33:44:55" not in out
    assert "a@b.com" not in out
    assert "BEGIN PRIVATE KEY" not in out


def test_service_logs_are_redacted(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    svc.log("nhat ky co token=abc123 va /home/cuong/secret")
    assert all("abc123" not in ln for ln in svc.logs)
    assert all("/home/cuong" not in ln for ln in svc.logs)


# --------------------------------------------------------------------------- #
# 7. Validate field hợp đồng (§7)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("field_name,bad_value", [
    ("component", "kernelx"),
    ("channel", "nightly"),
    ("architecture", "mips"),
    ("signature_status", "ok"),
    ("user_policy", "auto_everything"),
    ("payload_hash", "md5:abc"),
    ("metadata_version", 0),
    ("error_code", "UPD-999"),
])
def test_contract_rejects_bad_fields(field_name, bad_value):
    base = dict(
        update_id="u", component="os", channel="stable", target_build="b",
        architecture="x86_64", metadata_version=1,
        payload_hash="sha256:" + "0" * 64, signature_status="unknown",
        preflight=Preflight(), state=UpdateState.AVAILABLE, error_code=None,
        rollback_target="none", user_policy="notify", correlation_id="cid",
    )
    base[field_name] = bad_value
    # error_code != None đi với state != blocked cũng phải fail — test đó riêng.
    with pytest.raises(ContractError):
        UpdateContract(**base).validate()


def test_blocked_requires_error_code():
    with pytest.raises(ContractError):
        UpdateContract(
            update_id="u", component="os", channel="stable", target_build="b",
            architecture="x86_64", metadata_version=1,
            payload_hash="sha256:" + "0" * 64, signature_status="failed",
            preflight=Preflight(), state=UpdateState.BLOCKED, error_code=None,
            rollback_target="none", user_policy="notify", correlation_id="cid",
        ).validate()


def test_roundtrip_serialization(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    c = svc.check(repo["update_id"])
    d = c.to_dict()
    c2 = UpdateContract.from_dict(d)
    assert c2.to_dict() == d


def test_contract_matches_json_schema(repo, device, tmp_path):
    jsonschema = pytest.importorskip("jsonschema")
    import json
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "update_contract.schema.json",
    )
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    svc = make_service(repo, device, tmp_path)
    c = svc.check(repo["update_id"])
    jsonschema.validate(instance=c.to_dict(), schema=schema)
    # Một bản blocked cũng phải hợp schema.
    cb = svc.check(repo["update_id"], network_reachable=False)
    jsonschema.validate(instance=cb.to_dict(), schema=schema)
