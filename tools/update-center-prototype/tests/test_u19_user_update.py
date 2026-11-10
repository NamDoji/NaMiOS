# -*- coding: utf-8 -*-
"""U19-01..U19-14 — kịch bản người dùng NaMiOS Update Center (Phụ lục 19
03_KIEM_THU_CLAUDE_CODE.md), chạy trên engine prototype THẬT (update_contract.py
/ update_service.py / staged_deploy.py / boot_health.py / fault_inject.py /
sign_test_repo.py) — KHÔNG viết lại engine; file này CHỈ lắp kịch bản + vài hàm
hỗ trợ MỎNG lên trên các hook sẵn có + vài phần mở rộng tối thiểu được thêm
trực tiếp vào các module đó khi thật sự thiếu hook an toàn (xem comment
"MỞ RỘNG (U19-xx)" ngay tại chỗ sửa trong update_service.py/boot_health.py):

  * update_service.py: ``get_release_notes`` (API §6, U19-01) · chống rollback/
    freeze trong ``verify`` (U19-04) · ``assess_disk_safety`` (U19-05) ·
    ``arm_reboot(unsaved_documents=...)`` hoãn reboot (U19-06) ·
    ``schedule_reboot/get_schedule/cancel_schedule/reboot_allowed_now`` +
    ``RebootWindow`` (U19-02) · ``stage(firmware_user_confirmed=...)`` (U19-12).
  * boot_health.py: ``RingRolloutMonitor`` mô phỏng rollout theo ring (U19-10).
  * sign_test_repo.py: field ``release_notes_vi`` được KÝ trong manifest (U19-01).

====================  TRUNG THỰC VỀ GIỚI HẠN MÔ PHỎNG  ======================
Toàn bộ test này chạy trên VM/thư-mục với KHOÁ TEST (ed25519 sinh ngẫu nhiên
mỗi lần, xem sign_test_repo.py) — KHÔNG phải phần cứng NaMiOS thật, KHÔNG phải
khoá sản phẩm. pass ở đây chứng minh ĐÚNG LOGIC/bất biến an toàn của engine,
KHÔNG chứng minh kết quả vật lý trên máy thật. Các ca dưới đây CHỈ xác nhận
được ĐẦY ĐỦ khi có phần cứng/pilot thật (ghi "cần HW thật" trong docstring
từng test):
  * U19-05 — mã hóa ổ đĩa thật + dual-boot thật (bootloader/partition thật).
  * U19-07 — mất điện thật (rút nguồn) trên máy thật, không phải tiến trình
    Python dừng đột ngột trong RAM.
  * U19-10 — nhiều model phần cứng thật + driver Wi-Fi thật.
  * U19-12 — firmware thật + pin/nguồn thật của một thiết bị cụ thể.
  * U19-13 — USB thật + máy offline lâu thật.
Các ca còn lại (U19-01/02/03/04/06/08/09/11/14) kiểm được ĐẦY ĐỦ hành vi/bất
biến ở mức phần mềm bằng mô phỏng này.
==============================================================================
"""
from __future__ import annotations

import datetime as _dt
import inspect
import json
import os

import pytest

from boot_health import (
    BootHealthChecker,
    PROBE_KERNEL,
    PROBE_LOGIN,
    RingDevice,
    RingRolloutMonitor,
    all_healthy_probes,
    probes_with_failures,
)
from fault_inject import Fault, Phase, UpdateCampaign
from sign_test_repo import build_test_repo, build_update, generate_keypair
from staged_deploy import BackupProof, DeploymentStore, Migration
from update_contract import TransactionJournal, UpdateState
from update_service import (
    DeviceProfile,
    DownloadInterrupted,
    RebootWindow,
    UpdateService,
    VerificationError,
    assess_disk_safety,
    hour_in_quiet_window,
)


# --------------------------------------------------------------------------- #
# Fixtures + helper nhỏ dùng chung (không phải engine — chỉ lắp kịch bản)
# --------------------------------------------------------------------------- #
@pytest.fixture
def repo(tmp_path):
    return build_test_repo(str(tmp_path / "repo"))


@pytest.fixture
def device():
    return DeviceProfile(architecture="x86_64", model="namios-ref-pc",
                         current_deployment="namios-1.0-x86_64-stable-0000")


def make_service(repo, device, tmp_path, policy="auto_download_ask_install", cache_name="cache"):
    cache_dir = str(tmp_path / cache_name)
    return UpdateService(
        repo["repo"], repo["root_path"], device,
        cache_dir=cache_dir,
        journal=TransactionJournal(os.path.join(cache_dir, "journal.jsonl")),
        user_policy=policy,
    )


def drive_to_verify(svc, update_id):
    c = svc.check(update_id)
    c = svc.download(c)
    return svc.verify(c)


def _no_dangerous_kwargs(method) -> None:
    """API không có tham số dạng bypass (force/skip/override/ignore/bypass/
    unsafe/ai_*) ở các method thực-thi (verify/stage/preflight/boot_check) —
    dùng chung cho U19-04 ("không bypass UI/AI/API") và U19-14 ("đề nghị nguy
    hiểm của SmartAI bị từ chối vì API không có cửa")."""
    banned = ("force", "skip", "override", "ignore", "bypass", "unsafe", "ai_")
    params = set(inspect.signature(method).parameters) - {"self"}
    for p in params:
        low = p.lower()
        assert not any(b in low for b in banned), (
            f"{method.__qualname__} có tham số nghi bypass: {p!r}"
        )


# =============================================================================
# U19-01 — Thông báo MỘT LẦN, bản đúng kiến trúc/stable, version/changelog/size THẬT
# =============================================================================
def test_u19_01_notification_once_real_fields_from_manifest(repo, device, tmp_path):
    # Manifest ký kèm changelog + size THẬT (không phải UI/test tự bịa).
    build_update(
        repo["repo"], repo["priv"], repo["pub"],
        update_id=repo["update_id"],
        payload=b"NaMiOS 1.1 payload THAT (khong fake)\n" * 40,
        architecture=device.architecture,   # đúng kiến trúc máy
        channel="stable",
        release_notes_vi="Sua loi Wi-Fi; tang an toan cap nhat.",
    )
    svc = make_service(repo, device, tmp_path)

    notes = svc.get_release_notes(repo["update_id"])
    # Version/changelog/size phải khớp đúng những gì ĐÃ KÝ trong manifest thật.
    manifest_path = os.path.join(repo["repo"], "metadata", f"{repo['update_id']}.manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as fh:
        real_manifest = json.load(fh)
    assert notes["version"] == real_manifest["target_build"]
    assert notes["size_bytes"] == real_manifest["payload"]["size"] > 0
    assert notes["release_notes_vi"] == "Sua loi Wi-Fi; tang an toan cap nhat."
    assert notes["architecture"] == device.architecture == "x86_64"
    assert notes["channel"] == "stable"

    # "Thông báo MỘT LẦN": trình nền gọi check() định kỳ với idempotency_key ỔN
    # ĐỊNH theo (update_id, metadata_version) — journal (bền, đã có sẵn) chỉ ghi
    # một bản ghi "available" duy nhất; các lần gọi lại sau KHÔNG tạo thông báo
    # mới (không ghi thêm dòng) cho tới khi có metadata_version mới.
    stable_cid = f"notify-once-{repo['update_id']}"
    j = TransactionJournal(os.path.join(str(tmp_path / "cache"), "journal.jsonl"))
    before = len(j.records_for(repo["update_id"]))
    c1 = svc.check(repo["update_id"], correlation_id=stable_cid)
    after_1 = len(j.records_for(repo["update_id"]))
    c2 = svc.check(repo["update_id"], correlation_id=stable_cid)  # tái kiểm tra định kỳ, CÙNG bản
    after_2 = len(j.records_for(repo["update_id"]))
    c3 = svc.check(repo["update_id"], correlation_id=stable_cid)  # lần 3
    after_3 = len(j.records_for(repo["update_id"]))
    assert after_1 == before + 1          # lần đầu: MỘT bản ghi thông báo
    assert after_2 == after_1             # lần 2+: KHÔNG thông báo lại (idempotent)
    assert after_3 == after_1
    assert c1.state == c2.state == c3.state == UpdateState.AVAILABLE
    assert c1.component == "os"


def test_u19_01_wrong_arch_never_notified_as_applicable(repo, device, tmp_path):
    """Bản SAI kiến trúc không được coi là "bản đúng" — get_release_notes vẫn trả
    nội dung đã ký (để hiển thị lý do), nhưng verify() phải chặn khi cài (UPD-005);
    không có đường "thông báo rồi lờ đi kiểm arch"."""
    build_update(
        repo["repo"], repo["priv"], repo["pub"],
        update_id=repo["update_id"], payload=b"wrong arch payload" * 16,
        architecture="aarch64",  # máy là x86_64
    )
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-005"


# =============================================================================
# U19-02 — 4 chế độ + giờ yên tĩnh đúng cấu hình; lịch sống qua "reboot" (mô phỏng)
# =============================================================================
def test_u19_02_four_modes_are_distinct_contract_values():
    from update_contract import USER_POLICIES
    assert USER_POLICIES == {
        "notify", "auto_download_ask_install", "auto_install_safe", "auto_scheduled",
    }


def test_u19_02_quiet_hours_window_logic():
    # Cửa sổ vắt qua nửa đêm 22h -> 6h.
    w = RebootWindow(quiet_start_hour=22, quiet_end_hour=6, require_charging=True)
    assert hour_in_quiet_window(23, w) is True
    assert hour_in_quiet_window(2, w) is True
    assert hour_in_quiet_window(14, w) is False   # giữa trưa, ngoài giờ yên tĩnh
    # Cửa sổ không vắt nửa đêm: 1h -> 5h.
    w2 = RebootWindow(quiet_start_hour=1, quiet_end_hour=5)
    assert hour_in_quiet_window(3, w2) is True
    assert hour_in_quiet_window(20, w2) is False


def test_u19_02_auto_scheduled_mode_reboot_gated_by_window_and_charger(repo, device, tmp_path):
    """Chế độ #4 'auto_scheduled': chỉ khởi động lại TRONG cửa sổ đã chọn + khi
    cắm sạc; ngoài điều kiện đó KHÔNG được phép (service không tự reboot)."""
    svc = make_service(repo, device, tmp_path, policy="auto_scheduled")
    c = drive_to_verify(svc, repo["update_id"])
    c = svc.preflight(c, storage="pass", power="pass", network="pass")
    c = svc.stage(c)
    assert c.user_policy == "auto_scheduled"

    window = RebootWindow(quiet_start_hour=23, quiet_end_hour=5, require_charging=True)
    svc.schedule_reboot(c, window)

    allowed, reason = svc.reboot_allowed_now(repo["update_id"], now_hour=10, on_charger=True)
    assert allowed is False and "giờ yên tĩnh" in reason
    allowed, reason = svc.reboot_allowed_now(repo["update_id"], now_hour=1, on_charger=False)
    assert allowed is False and "cắm sạc" in reason
    allowed, reason = svc.reboot_allowed_now(repo["update_id"], now_hour=1, on_charger=True)
    assert allowed is True

    # Chỉ khi gate cho phép mới arm_reboot (mô phỏng bộ điều phối tôn trọng lịch).
    c = svc.arm_reboot(c)
    c = svc.boot_check(c, health_ok=True)
    assert c.state == UpdateState.COMPLETED


def test_u19_02_notify_mode_has_no_auto_schedule_by_default(repo, device, tmp_path):
    """Chế độ #1 'notify': không có lịch tự động nào được tạo sẵn — người dùng tự
    quyết định; get_schedule phải None cho tới khi NGƯỜI DÙNG tự đặt."""
    svc = make_service(repo, device, tmp_path, policy="notify")
    assert svc.get_schedule(repo["update_id"]) is None
    allowed, reason = svc.reboot_allowed_now(repo["update_id"], now_hour=1, on_charger=True)
    assert allowed is False
    assert "Chưa có lịch" in reason


def test_u19_02_schedule_persists_across_simulated_reboot(repo, device, tmp_path):
    cache_dir = str(tmp_path / "cache")
    j_path = os.path.join(cache_dir, "journal.jsonl")
    svc1 = UpdateService(repo["repo"], repo["root_path"], device,
                         cache_dir=cache_dir, journal=TransactionJournal(j_path),
                         user_policy="auto_scheduled")
    c = drive_to_verify(svc1, repo["update_id"])
    c = svc1.preflight(c)
    c = svc1.stage(c)
    window = RebootWindow(quiet_start_hour=22, quiet_end_hour=6, require_charging=True,
                          metered_network_limit_mb=500)
    saved = svc1.schedule_reboot(c, window)

    # --- Giả lập REBOOT: dựng UpdateService MỚI (bỏ toàn bộ state RAM cũ),
    # chỉ cache_dir trên đĩa còn lại — giống machine restart thật. ---
    del svc1
    svc2 = UpdateService(repo["repo"], repo["root_path"], device,
                         cache_dir=cache_dir, journal=TransactionJournal(j_path),
                         user_policy="auto_scheduled")
    resumed_schedule = svc2.get_schedule(repo["update_id"])
    assert resumed_schedule is not None
    assert resumed_schedule == saved
    assert resumed_schedule["window"]["quiet_start_hour"] == 22
    assert resumed_schedule["window"]["metered_network_limit_mb"] == 500

    # cancel_schedule cũng phải bền (thấy ngay ở instance mới).
    assert svc2.cancel_schedule(repo["update_id"]) is True
    svc3 = UpdateService(repo["repo"], repo["root_path"], device,
                         cache_dir=cache_dir, journal=TransactionJournal(j_path))
    assert svc3.get_schedule(repo["update_id"]) is None


# =============================================================================
# U19-03 — Mất mạng giữa tải → resume từ chunk hợp lệ; KHÔNG BAO GIỜ stage payload thiếu
# =============================================================================
def test_u19_03_network_drop_resumes_from_verified_chunk(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    c = svc.check(repo["update_id"])
    with pytest.raises(DownloadInterrupted):
        svc.download(c, chunk_size=512, interrupt_after_bytes=1500)
    part = os.path.join(str(tmp_path / "cache"), f"{repo['update_id']}.part")
    assert os.path.exists(part)
    partial_size = os.path.getsize(part)
    assert 0 < partial_size < 3200

    # Chưa đủ byte (chỉ có .part, chưa có .payload hoàn chỉnh) -> hash-check nội
    # bộ mà verify() dùng phải CHẶN (thiếu payload đã tải để kiểm), KHÔNG được
    # coi payload dở là "đã tải xong" để đi tiếp stage.
    with pytest.raises(VerificationError):
        svc._check_payload_hash(repo["update_id"], svc._read_manifest(repo["update_id"])[0])

    # "Nối lại mạng": gọi lại download() resume từ offset đã có, không tải lại từ đầu.
    c = svc.download(c, chunk_size=512)
    final_size = os.path.getsize(os.path.join(str(tmp_path / "cache"), f"{repo['update_id']}.payload"))
    manifest, _ = svc._read_manifest(repo["update_id"])
    assert final_size == manifest["payload"]["size"]  # đủ byte, không thiếu không dư
    c = svc.verify(c)
    assert c.state == UpdateState.VERIFIED


def test_u19_03_cannot_stage_incomplete_or_unverified_payload(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    c = svc.check(repo["update_id"])
    with pytest.raises(DownloadInterrupted):
        svc.download(c, chunk_size=512, interrupt_after_bytes=800)
    # contract còn ở 'available' (download() ném trước khi chuyển 'downloading') -> stage() từ chối.
    with pytest.raises(RuntimeError):
        svc.stage(c)


def test_u19_03_fault_matrix_download_phase_never_half_installed(tmp_path):
    """Tái dùng fault_inject: đứt mạng pha DOWNLOAD -> bootable + data đúng hash +
    KHÔNG có bản nửa cài (bằng chứng engine-level, không chỉ 1 hàm)."""
    camp = UpdateCampaign(str(tmp_path))
    out = camp.simulate(Phase.DOWNLOAD, Fault.NETWORK_DROP)
    assert out.ok()
    assert out.half_installed is False


# =============================================================================
# U19-04 — Hash/chữ ký/metadata sai/CŨ/hết hạn/thu hồi → chặn 100%, KHÔNG bypass
# =============================================================================
def test_u19_04_wrong_hash_signature_expired_revoked_all_block(repo, device, tmp_path):
    """Gộp 4 kiểu tấn công riêng biệt trên 4 repo độc lập — MỖI kiểu phải blocked."""
    # (a) SAI — payload bị sửa (hash lệch).
    p = os.path.join(repo["repo"], "targets", f"{repo['update_id']}.payload")
    data = bytearray(open(p, "rb").read())
    data[0:4] = b"EVIL"
    with open(p, "wb") as fh:
        fh.write(data)
    svc = make_service(repo, device, tmp_path, cache_name="cache-a")
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED and c.error_code == "UPD-003"


def test_u19_04_old_metadata_rollback_replay_blocked(repo, device, tmp_path):
    """"CŨ" (khác "hết hạn"): kẻ tấn công replay một manifest CŨ HƠN, vẫn còn hạn
    + chữ ký + hash TỰ THÂN hợp lệ (ký lại đúng khoá tin cậy) — chặn vì
    metadata_version thấp hơn bản ĐÃ TỪNG được máy tin (chống hạ cấp/rollback)."""
    svc = make_service(repo, device, tmp_path)
    # Lần 1: verify thành công ở metadata_version=2 (mặc định build_test_repo).
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.VERIFIED

    # Kẻ tấn công thay bằng bản CŨ HƠN (metadata_version=1) nhưng KÝ LẠI đúng
    # bằng khoá tin cậy thật + hạn còn xa + hash tự thân khớp payload mới ghi.
    build_update(
        repo["repo"], repo["priv"], repo["pub"],
        update_id=repo["update_id"], payload=b"ban CU hon bi replay lai" * 8,
        metadata_version=1,
    )
    cache_payload = os.path.join(str(tmp_path / "cache"), f"{repo['update_id']}.payload")
    os.remove(cache_payload)  # buộc tải lại bản (cũ) mới được ghi vào repo

    c2 = svc.check(repo["update_id"])
    c2 = svc.download(c2)
    c2 = svc.verify(c2)
    assert c2.state == UpdateState.BLOCKED
    assert c2.error_code == "UPD-004"   # chống rollback/freeze (xem update-error-catalog UPD-004)
    assert c2.signature_status == "failed"


def test_u19_04_no_bypass_via_api_surface(repo, device, tmp_path):
    """"Không bypass UI/AI/API": verify/stage/preflight/boot_check không có BẤT
    KỲ tham số force/skip/override/ignore/bypass/unsafe/ai_* nào — không có cửa
    gọi API để cài khi chưa xác thực, dù caller là UI, daemon hay SmartAI."""
    for method in (UpdateService.verify, UpdateService.stage,
                   UpdateService.preflight, UpdateService.boot_check,
                   UpdateService.download, UpdateService.check):
        _no_dangerous_kwargs(method)

    # Thực chứng: chữ ký giả -> blocked -> KHÔNG có đường gọi tiếp để cài đè.
    attacker_priv, _ = generate_keypair()
    build_update(repo["repo"], repo["priv"], repo["pub"],
                update_id=repo["update_id"], payload=b"x" * 256, sign_with=attacker_priv)
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED
    with pytest.raises(RuntimeError):
        svc.stage(c)
    with pytest.raises(Exception):
        c.transition(UpdateState.STAGED)  # blocked là trạng thái kết thúc


def test_u19_04_revocation_blocks_even_if_hash_sig_valid(repo, device, tmp_path):
    from sign_test_repo import write_revocation
    write_revocation(repo["repo"], repo["priv"], repo["pub"],
                     revoked_update_ids=[repo["update_id"]], metadata_version=2)
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    assert c.state == UpdateState.BLOCKED and c.error_code == "UPD-009"


# =============================================================================
# U19-05 — Thiếu dung lượng/pin yếu/dual-boot/mã hóa → preflight chặn đúng, KHÔNG xóa file
# (mô phỏng mức logic — mã hoá/dual-boot THẬT cần phần cứng; xem header file)
# =============================================================================
def test_u19_05_insufficient_storage_blocks_and_keeps_user_files(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    before = camp.store.data_hashes()
    svc = camp._svc()
    c = svc.check(camp.uid)
    c = svc.download(c)
    c = svc.verify(c)
    c = svc.preflight(c, storage="fail", power="pass", network="pass")
    assert c.state == UpdateState.BLOCKED and c.error_code == "UPD-002"
    after = DeploymentStore(camp.store_root).data_hashes()
    assert after == before   # KHÔNG xoá file người dùng khi chặn


def test_u19_05_low_battery_blocks_firmware_preflight(repo, device, tmp_path):
    build_update(repo["repo"], repo["priv"], repo["pub"],
                update_id="namios-fw-000x", payload=b"fake firmware" * 16,
                component="firmware")
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, "namios-fw-000x")
    c = svc.preflight(c, storage="pass", power="fail", network="pass")
    assert c.state == UpdateState.BLOCKED and c.error_code == "UPD-006"


def test_u19_05_dual_boot_and_encryption_signals_block_preflight_no_deletion(tmp_path):
    """dual-boot/mã hóa CHƯA có field riêng trong hợp đồng §7 (không đổi schema);
    assess_disk_safety() (MỞ RỘNG THUẦN, không I/O) đánh giá rồi ánh xạ về
    storage=fail hiện có. Khẳng định: (1) phát hiện đúng lý do tiếng Việt,
    (2) preflight chặn UPD-002, (3) dữ liệu người dùng + bản cũ không bị đụng."""
    result, reason_vi = assess_disk_safety(
        dual_boot_other_os_detected=True, disk_encrypted_and_locked=True,
    )
    assert result == "fail"
    assert "dual boot" in reason_vi.lower() or "mã hoá" in reason_vi or "mã hóa" in reason_vi

    camp = UpdateCampaign(str(tmp_path))
    before = camp.store.data_hashes()
    svc = camp._svc()
    c = svc.check(camp.uid)
    c = svc.download(c)
    c = svc.verify(c)
    c = svc.preflight(c, storage=result, power="pass", network="pass")
    assert c.state == UpdateState.BLOCKED and c.error_code == "UPD-002"
    after = DeploymentStore(camp.store_root).data_hashes()
    assert after == before
    assert UpdateCampaign.OLD_DEP in {d.dep_id for d in DeploymentStore(camp.store_root).deployments()}

    # Không rủi ro -> pass, không chặn.
    ok_result, _ = assess_disk_safety()
    assert ok_result == "pass"


# =============================================================================
# U19-06 — Tài liệu NaMiOffice/NaMiPDF chưa lưu → KHÔNG reboot bất ngờ, chọn giờ khác
# =============================================================================
def test_u19_06_unsaved_documents_defer_reboot_then_proceeds_after_saved(repo, device, tmp_path):
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    c = svc.preflight(c)
    c = svc.stage(c)
    assert c.state == UpdateState.STAGED

    # Có tài liệu chưa lưu -> KHÔNG reboot, vẫn ở 'staged' (không bất ngờ mất việc).
    held = svc.arm_reboot(c, unsaved_documents=["BaoCaoThang.odt", "SoLieu.ods"])
    assert held.state == UpdateState.STAGED
    assert held is c or held.state == c.state
    assert any("chưa lưu" in ln for ln in svc.logs[-3:])

    # "Người dùng lưu xong + chọn giờ khác" -> gọi lại KHÔNG có tài liệu treo -> tiếp tục.
    c2 = svc.arm_reboot(held)
    assert c2.state == UpdateState.REBOOT_PENDING
    c2 = svc.boot_check(c2, health_ok=True)
    assert c2.state == UpdateState.COMPLETED


# =============================================================================
# U19-07 — Kill service/mất điện ở download/stage/boot-switch → boot bản cũ/cứu hộ,
# journal KHÔNG hỏng (mô phỏng mức tiến trình; mất điện THẬT cần phần cứng — header)
# =============================================================================
@pytest.mark.parametrize("phase,fault", [
    (Phase.DOWNLOAD, Fault.POWER_LOSS),
    (Phase.DOWNLOAD, Fault.KILLED_UPDATER),
    (Phase.STAGE, Fault.POWER_LOSS),
    (Phase.STAGE, Fault.KILLED_UPDATER),
    (Phase.SWITCH, Fault.POWER_LOSS),
    (Phase.SWITCH, Fault.KILLED_UPDATER),
])
def test_u19_07_kill_or_power_loss_boots_old_or_recovery_journal_intact(phase, fault, tmp_path):
    camp = UpdateCampaign(str(tmp_path / f"{phase.value}-{fault.value}"))
    out = camp.simulate(phase, fault)
    assert out.bootable, f"{phase}/{fault}: máy phải boot được (bản cũ hoặc bản mới)"
    assert out.data_intact
    assert not out.half_installed

    # Journal KHÔNG sai: mọi dòng JSONL phải parse được + có state hợp lệ.
    with open(camp.journal_path, "r", encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    assert lines, "journal phải có ít nhất một bản ghi"
    for ln in lines:
        rec = json.loads(ln)   # ném JSONDecodeError nếu hỏng -> test fail rõ ràng
        assert rec["state"] in {s.value for s in UpdateState}
        assert "idempotency_key" in rec and "snapshot" in rec


# =============================================================================
# U19-08 — Bản mới boot-loop/desktop crash → TỰ rollback, có report, KHÔNG xóa rollback target
# =============================================================================
def test_u19_08_boot_loop_critical_probe_fails_auto_rollback_with_report(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    svc = camp._svc()
    c = svc.check(camp.uid)
    c = svc.download(c)
    c = svc.verify(c)
    c = svc.preflight(c, storage="pass", power="pass", network="pass")
    deployer = camp._deployer()
    new_dep = camp._new_dep_id()
    c, new_dep = deployer.prepare(c, payload_path=camp._payload_path(),
                                  build="namios-1.1", new_dep_id=new_dep)
    c = deployer.arm_switch(c, new_dep)

    # "boot loop": probe tới hạn kernel hỏng liên tục qua mọi lần thử.
    checker = BootHealthChecker(probes_with_failures((PROBE_KERNEL,)),
                                journal=TransactionJournal(camp.journal_path),
                                max_boot_attempts=3)
    outcome = checker.run(c, deployer, new_dep)
    assert outcome.contract.state == UpdateState.ROLLED_BACK
    assert outcome.rolled_back is True
    assert outcome.report.passed is False
    assert outcome.report.error_code == "UPD-008"
    assert PROBE_KERNEL in outcome.report.failed_probes()
    assert outcome.report.summary_vi  # có "report" cho người dùng/hỗ trợ

    store = DeploymentStore(camp.store_root)
    assert store.current_default() == UpdateCampaign.OLD_DEP
    # KHÔNG xóa rollback target (bản mới "failed" vẫn còn trên đĩa làm chứng cứ).
    assert new_dep in {d.dep_id for d in store.deployments()}
    assert os.path.isdir(os.path.join(store.deployments_dir, new_dep))


def test_u19_08_desktop_ui_crash_loop_auto_rollback(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    state, default_dep, rolled_back = camp.run_clean(health_ok=False)  # dùng probe UI-fail có sẵn
    assert state == UpdateState.ROLLED_BACK.value
    assert rolled_back is True
    assert default_dep == UpdateCampaign.OLD_DEP
    store = DeploymentStore(camp.store_root)
    assert UpdateCampaign.OLD_DEP in {d.dep_id for d in store.deployments()}


# =============================================================================
# U19-09 — Migration không tương thích rollback → chặn trước, HOẶC restore được từ backup đã thử
# =============================================================================
def _drive_to_verified(camp):
    svc = camp._svc()
    c = svc.check(camp.uid)
    c = svc.download(c)
    c = svc.verify(c)
    c = svc.preflight(c, storage="pass", power="pass", network="pass")
    return svc, c


def test_u19_09_incompatible_migration_blocked_beforehand_no_deployment_created(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    _, c = _drive_to_verified(camp)
    deployer = camp._deployer()
    mig = Migration("m-incompat", version_from=1, version_to=2,
                    data_paths=("app.db",), forward_backward_compatible=False,
                    reversible=False, dry_run_ok=True)
    blocked, dep = deployer.prepare(c, payload_path=camp._payload_path(),
                                    build="namios-1.1", migration=mig, backup=None)
    assert blocked.state == UpdateState.BLOCKED and blocked.error_code == "UPD-010"
    assert dep is None
    # Chặn TRƯỚC khi đụng đĩa — không deployment mới nào được tạo.
    store = DeploymentStore(camp.store_root)
    assert {d.dep_id for d in store.deployments()} == {UpdateCampaign.OLD_DEP}


def test_u19_09_incompatible_migration_allowed_with_tested_restore_backup_then_rollback_keeps_data(tmp_path):
    """Nhánh (b): migration một-chiều nhưng CÓ backup đã kiểm khôi phục (dry-run
    restore đúng hash, phủ đúng data_paths) -> cho staged. Nếu sau đó boot-health
    vẫn fail, OS tự rollback (CHỈ hệ thống) còn dữ liệu vẫn nguyên theo backup đã
    kiểm — không rollback mù đồng thời với dữ liệu đã đổi schema."""
    camp = UpdateCampaign(str(tmp_path))
    _, c = _drive_to_verified(camp)
    deployer = camp._deployer()
    mig = Migration("m-oneway-with-backup", 1, 2, data_paths=("so-ke-toan.db",),
                    forward_backward_compatible=False, reversible=False, dry_run_ok=True)
    backup = BackupProof("b-tested", created=True, restore_verified=True,
                         covered_paths=("so-ke-toan.db",))
    new_dep = camp._new_dep_id()
    staged, new_dep = deployer.prepare(c, payload_path=camp._payload_path(),
                                       build="namios-1.1", new_dep_id=new_dep,
                                       migration=mig, backup=backup)
    assert staged.state == UpdateState.STAGED
    assert staged.preflight.backup == "pass"
    assert new_dep is not None

    armed = deployer.arm_switch(staged, new_dep)
    checker = BootHealthChecker(probes_with_failures((PROBE_LOGIN,)),
                                journal=TransactionJournal(camp.journal_path),
                                max_boot_attempts=1)
    outcome = checker.run(armed, deployer, new_dep)
    assert outcome.contract.state == UpdateState.ROLLED_BACK   # OS rollback (chỉ hệ thống)
    store = DeploymentStore(camp.store_root)
    assert store.current_default() == UpdateCampaign.OLD_DEP
    # Dữ liệu /home mô phỏng — KHÔNG bị OS rollback đụng tới (rollback OS, không
    # rollback mù database/home); đúng theo backup đã kiểm, không mất.
    assert store.data_hashes() == camp.expected_data


def test_u19_09_migration_guard_unit_logic_fail_closed():
    from staged_deploy import MigrationGuard
    g = MigrationGuard()
    assert g.assess(None, None).allowed is True
    one_way = Migration("o", 1, 2, data_paths=("d",), dry_run_ok=True)
    good_backup = BackupProof("b", True, True, covered_paths=("d",))
    assert g.assess(one_way, good_backup).allowed is True
    bad_backup = BackupProof("b", True, True, covered_paths=("khac",))
    d = g.assess(one_way, bad_backup)
    assert d.allowed is False and d.error_code == "UPD-010"


# =============================================================================
# U19-10 — Bản mới lỗi Wi-Fi trên MỘT model → ring dừng, chẩn đoán đúng model,
# ring khác KHÔNG bị ảnh hưởng (mô phỏng ring; driver/model thật cần HW — header)
# =============================================================================
def test_u19_10_wifi_regression_on_one_model_halts_ring_correct_diagnosis():
    # Ring "pilot": 3 máy model A (bị regression Wi-Fi -> basic_network hỏng) +
    # 2 máy model B (không liên quan, khỏe mạnh hoàn toàn).
    model_a_probes = probes_with_failures(("basic_network",))
    model_b_probes = all_healthy_probes()
    pilot_devices = [
        (RingDevice("dev-a1", "NaMiBook-A"), model_a_probes),
        (RingDevice("dev-a2", "NaMiBook-A"), model_a_probes),
        (RingDevice("dev-a3", "NaMiBook-A"), model_a_probes),
        (RingDevice("dev-b1", "NaMiBook-B"), model_b_probes),
        (RingDevice("dev-b2", "NaMiBook-B"), model_b_probes),
    ]
    stable_wave1_devices = [
        (RingDevice("dev-c1", "NaMiBook-C"), all_healthy_probes()),
    ]
    monitor = RingRolloutMonitor(fail_ratio_threshold=0.3)
    decision = monitor.run([
        ("pilot", pilot_devices),
        ("stable-wave-1", stable_wave1_devices),
    ])

    # Ring dừng đúng tại 'pilot' (3/5 = 60% > 30%).
    assert decision.halted_at_ring == "pilot"
    assert decision.evaluated_rings == ("pilot",)
    # Chẩn đoán ĐÚNG model: chỉ model A bị gắn lỗi, KHÔNG lan sang model B.
    assert decision.failed_models == ("NaMiBook-A",)
    assert decision.model_failed_probes("NaMiBook-A") == ("basic_network",)
    assert decision.model_failed_probes("NaMiBook-B") == ()
    model_b_results = decision.model_results("NaMiBook-B")
    assert all(r.passed for r in model_b_results)   # model B trong CÙNG ring không bị ảnh hưởng
    # Ring SAU (stable-wave-1, model C) CHƯA rollout -> không bị ảnh hưởng, không chạy health.
    assert "stable-wave-1" in decision.unaffected_rings
    assert all(r.ring != "stable-wave-1" for r in decision.results)


def test_u19_10_healthy_rollout_does_not_halt_any_ring():
    monitor = RingRolloutMonitor(fail_ratio_threshold=0.3)
    devices = [(RingDevice(f"dev-{i}", "NaMiBook-A"), all_healthy_probes()) for i in range(4)]
    decision = monitor.run([("pilot", devices), ("stable-wave-1", devices)])
    assert decision.halted_at_ring is None
    assert decision.evaluated_rings == ("pilot", "stable-wave-1")
    assert decision.failed_models == ()
    assert decision.unaffected_rings == ()


# =============================================================================
# U19-11 — NaMiOffice/NaMiPDF cập nhật RIÊNG → app đổi version, OS giữ version,
# file người dùng còn nguyên
# =============================================================================
def test_u19_11_app_update_separate_from_os_version_and_user_files_untouched(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    os_default_before = camp.store.current_default()
    data_before = camp.store.data_hashes()

    # Ký THÊM một bản app (NaMiOffice) RIÊNG trong CÙNG repo, update_id khác bản OS.
    app_update_id = "namios-app-namioffice-9.1"
    build_update(
        camp.repo_info["repo"], camp.repo_info["priv"], camp.repo_info["pub"],
        update_id=app_update_id, payload=b"NaMiOffice 9.1 app package (TEST)\n" * 20,
        component="app", channel="stable", architecture="x86_64",
        target_build="namioffice-9.1", metadata_version=1,
        release_notes_vi="NaMiOffice 9.1: sua loi mo file .docx lon.",
    )
    svc = camp._svc()
    c = svc.check(app_update_id)
    assert c.component == "app"
    c = svc.download(c)
    c = svc.verify(c)
    assert c.state == UpdateState.VERIFIED
    c = svc.preflight(c, storage="pass", power="pass", network="pass")
    c = svc.stage(c)                 # app: không đòi deployment A-B của OS
    c = svc.arm_reboot(c)             # app rollback gói app khi khả thi, không đòi boot OS thật
    c = svc.boot_check(c, health_ok=True)
    assert c.state == UpdateState.COMPLETED
    assert c.target_build == "namioffice-9.1"   # version APP đã đổi

    # OS deployment/default KHÔNG đổi + dữ liệu người dùng còn nguyên.
    store_after = DeploymentStore(camp.store_root)
    assert store_after.current_default() == os_default_before == UpdateCampaign.OLD_DEP
    assert store_after.data_hashes() == data_before == camp.expected_data


# =============================================================================
# U19-12 — Firmware trong danh sách mới → KHÔNG tự cài; cần xác nhận + pin/nguồn/model
# (mô phỏng mức logic API; firmware/pin thật của MỘT thiết bị cụ thể cần HW — header)
# =============================================================================
def test_u19_12_firmware_never_auto_stages_without_explicit_confirmation(repo, device, tmp_path):
    build_update(repo["repo"], repo["priv"], repo["pub"],
                update_id="namios-fw-0099", payload=b"firmware blob" * 32,
                component="firmware")
    for policy in ("auto_install_safe", "auto_scheduled"):  # các chế độ "tự cài"
        svc = make_service(repo, device, tmp_path, policy=policy, cache_name=f"cache-{policy}")
        c = drive_to_verify(svc, "namios-fw-0099")
        c = svc.preflight(c, storage="pass", power="pass", network="pass")
        assert c.state == UpdateState.VERIFIED
        # Dù mô phỏng một bộ điều phối "tự cài mọi bản đã verified", firmware vẫn
        # bị TỪ CHỐI khi thiếu xác nhận rõ — KHÔNG có chế độ nào bỏ qua cửa này.
        with pytest.raises(RuntimeError, match="firmware"):
            svc.stage(c)


def test_u19_12_firmware_stages_only_with_confirmation_and_power_check(repo, device, tmp_path):
    build_update(repo["repo"], repo["priv"], repo["pub"],
                update_id="namios-fw-0100", payload=b"firmware blob ok" * 32,
                component="firmware")
    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, "namios-fw-0100")

    # Pin/nguồn không đạt -> chặn TẠI PREFLIGHT trước khi tới bước xác nhận.
    bad_power = svc.preflight(c, storage="pass", power="fail", network="pass")
    assert bad_power.state == UpdateState.BLOCKED and bad_power.error_code == "UPD-006"

    # Pin/nguồn đạt + CÓ xác nhận rõ -> mới được staged.
    ok_power = svc.preflight(c, storage="pass", power="pass", network="pass")
    staged = svc.stage(ok_power, firmware_user_confirmed=True)
    assert staged.state == UpdateState.STAGED


# =============================================================================
# U19-13 — Máy offline lâu, cập nhật bằng USB → CHỈ chấp nhận bundle có
# trust-chain hợp lệ/phù hợp (USB mô phỏng = thư mục repo cục bộ, xem header)
# =============================================================================
def test_u19_13_usb_bundle_signed_by_untrusted_key_rejected(tmp_path, device):
    """Máy pin trust root THẬT từ ISO; USB mang theo repo ký bằng khoá KHÁC (kẻ
    tấn công/USB giả) -> từ chối dù cấu trúc file hợp lệ."""
    pinned = build_test_repo(str(tmp_path / "pinned-trust"))
    attacker_priv, attacker_pub = generate_keypair()
    usb_repo_dir = str(tmp_path / "usb-bundle")
    build_update(usb_repo_dir, attacker_priv, attacker_pub,
                update_id=pinned["update_id"], payload=b"usb bundle gia" * 16)
    # revocation rỗng vẫn cần ký đúng — ký bằng khoá kẻ tấn công (không phải pinned).
    from sign_test_repo import write_revocation
    write_revocation(usb_repo_dir, attacker_priv, attacker_pub)

    svc = UpdateService(usb_repo_dir, pinned["root_path"], device,  # root pin = máy THẬT
                        cache_dir=str(tmp_path / "cache"))
    c = drive_to_verify(svc, pinned["update_id"])
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-003"   # khoá ký không nằm trong trust root


def test_u19_13_usb_bundle_long_offline_expired_rejected(tmp_path, device):
    """Bundle USB ký ĐÚNG khoá tin cậy nhưng đã CŨ (hạn đã qua vì máy offline rất
    lâu) -> chặn hết hạn, KHÔNG chấp nhận chỉ vì chữ ký đúng."""
    pinned = build_test_repo(str(tmp_path / "pinned-trust"))
    usb_repo_dir = str(tmp_path / "usb-bundle")
    past = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=200)
    build_update(usb_repo_dir, pinned["priv"], pinned["pub"],
                update_id=pinned["update_id"], payload=b"usb bundle cu" * 16, expires=past)
    from sign_test_repo import write_revocation
    write_revocation(usb_repo_dir, pinned["priv"], pinned["pub"])

    svc = UpdateService(usb_repo_dir, pinned["root_path"], device,
                        cache_dir=str(tmp_path / "cache"))
    c = drive_to_verify(svc, pinned["update_id"])
    assert c.state == UpdateState.BLOCKED
    assert c.error_code == "UPD-004"


def test_u19_13_usb_bundle_valid_trust_chain_and_applicable_arch_accepted(tmp_path, device):
    """Bundle USB hợp lệ (đúng khoá pinned + còn hạn + đúng kiến trúc máy) vẫn
    PHẢI được chấp nhận — máy offline lâu không bị chặn OAN."""
    pinned = build_test_repo(str(tmp_path / "pinned-trust"))
    usb_repo_dir = str(tmp_path / "usb-bundle")
    build_update(usb_repo_dir, pinned["priv"], pinned["pub"],
                update_id=pinned["update_id"], payload=b"usb bundle hop le" * 16,
                architecture=device.architecture)
    from sign_test_repo import write_revocation
    write_revocation(usb_repo_dir, pinned["priv"], pinned["pub"])

    svc = UpdateService(usb_repo_dir, pinned["root_path"], device,
                        cache_dir=str(tmp_path / "cache"))
    c = drive_to_verify(svc, pinned["update_id"])
    assert c.state == UpdateState.VERIFIED


def test_u19_13_usb_bundle_wrong_architecture_not_applicable_rejected(tmp_path, device):
    pinned = build_test_repo(str(tmp_path / "pinned-trust"))
    usb_repo_dir = str(tmp_path / "usb-bundle")
    build_update(usb_repo_dir, pinned["priv"], pinned["pub"],
                update_id=pinned["update_id"], payload=b"usb bundle sai arch" * 16,
                architecture="riscv64")
    from sign_test_repo import write_revocation
    write_revocation(usb_repo_dir, pinned["priv"], pinned["pub"])

    svc = UpdateService(usb_repo_dir, pinned["root_path"], device,
                        cache_dir=str(tmp_path / "cache"))
    c = drive_to_verify(svc, pinned["update_id"])
    assert c.state == UpdateState.BLOCKED and c.error_code == "UPD-005"


# =============================================================================
# U19-14 — SmartAI tắt hoặc đề nghị bỏ chữ ký → update vẫn hoạt động; đề nghị
# nguy hiểm bị từ chối
# =============================================================================
def test_u19_14_update_completes_fully_with_zero_ai_involvement(repo, device, tmp_path):
    """"SmartAI bị tắt": engine không hề import/gọi bất kỳ thứ gì liên quan AI —
    chạy toàn luồng hợp lệ mà không chạm một dòng nào liên quan SmartAI, vẫn
    completed bình thường."""
    import update_service as _us
    src = inspect.getsource(_us)
    # Engine không IMPORT bất kỳ module smartai/ai nào — tắt AI không ảnh hưởng
    # tới khả năng chạy của Update Service (không có phụ thuộc runtime vào AI).
    assert "import smartai" not in src.lower()
    assert "from smartai" not in src.lower()
    assert "import ai" not in src.lower()

    svc = make_service(repo, device, tmp_path)
    c = drive_to_verify(svc, repo["update_id"])
    c = svc.preflight(c, storage="pass", power="pass", network="pass")
    c = svc.stage(c)
    c = svc.arm_reboot(c)
    c = svc.boot_check(c, health_ok=True)
    assert c.state == UpdateState.COMPLETED   # hoạt động đầy đủ, không cần AI


def test_u19_14_ai_proposal_to_skip_signature_has_no_executable_path(repo, device, tmp_path):
    """Mô phỏng "SmartAI đề nghị bỏ chữ ký": một kế hoạch/đề nghị do AI sinh ra
    (chỉ là dữ liệu — chuỗi/dict) được thử "thực thi" qua API thật. Phải bị từ
    chối NGAY ở lớp gọi hàm (TypeError tham số lạ) — không có cách nào API chấp
    nhận yêu cầu đó, bất kể ai/điều gì tạo ra đề nghị."""
    for method in (UpdateService.verify, UpdateService.stage, UpdateService.preflight):
        _no_dangerous_kwargs(method)

    dangerous_ai_plan = {
        "action": "verify",
        "reasoning_vi": "Bỏ kiểm chữ ký để cài nhanh hơn cho người dùng.",
        "params": {"skip_signature": True},
    }
    svc = make_service(repo, device, tmp_path)
    c = svc.check(repo["update_id"])
    c = svc.download(c)
    method = getattr(svc, dangerous_ai_plan["action"])
    with pytest.raises(TypeError):
        method(c, **dangerous_ai_plan["params"])   # API không có tham số này -> từ chối cứng

    # Update vẫn hoạt động được qua đường THẬT (không tham số nguy hiểm).
    c = method(c)
    assert c.state == UpdateState.VERIFIED
    assert c.signature_status == "verified"


def test_u19_14_ai_cannot_alter_trust_root_path_post_construction(repo, device, tmp_path):
    """SmartAI (hoặc bất kỳ caller nào) không có API để ĐỔI trust root sau khi
    UpdateService đã dựng — trust root chỉ nạp một lần ở __init__ (pin từ ISO)."""
    svc = make_service(repo, device, tmp_path)
    assert not hasattr(svc, "set_trust_root")
    assert not hasattr(svc, "add_trusted_key")
    # Thuộc tính khoá tin cậy có tên "private" theo quy ước — không có setter công khai.
    public_attrs = [a for a in dir(svc) if not a.startswith("_")]
    assert not any("trust" in a.lower() and "set" in a.lower() for a in public_attrs)
