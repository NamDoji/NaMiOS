"""Smoke test cho ``namios_core`` (WP1): envelope, exitcodes, txstate
transitions, compat, paths. Test CHẠY THẬT trên host hiện tại — không mock
import, không giả lập để báo đạt.
"""

from __future__ import annotations

import dataclasses
import os
import uuid
from pathlib import Path

import pytest

from namios_core.about import FOUNDERS, PRODUCT_NAME, AboutInfo, ComponentLicense
from namios_core.compat import AppMode, CertificationTuple, CompatStatus
from namios_core.envelope import API_VERSION, Envelope, ErrorBody
from namios_core.errors import ERROR_CODE_EXIT_MAP, ErrorCode, exit_code_for
from namios_core.exitcodes import ExitCode
from namios_core.paths import (
    APP_NAME,
    LOG_MAX_AGE_DAYS_DEFAULT,
    LOG_MAX_BYTES_DEFAULT,
    STATE_DB_FILENAME,
    cache_dir,
    config_dir,
    logs_dir,
    prefixes_dir,
    share_ro_dir,
    state_db_path,
    system_var_dir,
)
from namios_core.txstate import TxState, validate_transition

# ---------------------------------------------------------------------------
# envelope
# ---------------------------------------------------------------------------


def test_envelope_ok_status_has_no_error() -> None:
    env = Envelope(
        api_version=API_VERSION,
        operation_id=uuid.uuid4().hex,
        status="ok",
        data={"hello": "the-gioi"},
        warnings=(),
        error=None,
    )
    assert env.status == "ok"
    assert env.error is None
    assert env.data == {"hello": "the-gioi"}
    assert env.api_version == "1.0"


def test_envelope_error_status_has_error_body_and_null_data() -> None:
    body = ErrorBody(
        code=ErrorCode.E_INPUT_SCHEMA.value,
        message_vi="Tham số sai kiểu.",
        details=None,
    )
    env = Envelope(
        api_version=API_VERSION,
        operation_id=uuid.uuid4().hex,
        status="error",
        data=None,
        warnings=(),
        error=body,
    )
    assert env.status == "error"
    assert env.data is None
    assert env.error is not None
    assert env.error.code == "E_INPUT_SCHEMA"


def test_envelope_is_frozen() -> None:
    env = Envelope(
        api_version=API_VERSION,
        operation_id="x",
        status="ok",
        data=None,
        warnings=(),
        error=None,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        env.status = "error"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# exitcodes + errors
# ---------------------------------------------------------------------------


def test_exit_code_values_match_table() -> None:
    assert ExitCode.OK == 0
    assert ExitCode.INPUT == 2
    assert ExitCode.DEPENDENCY == 3
    assert ExitCode.NETWORK == 4
    assert ExitCode.PERMISSION == 5
    assert ExitCode.CONFLICT == 6
    assert ExitCode.CANCELLED == 7
    assert ExitCode.VERIFY == 8
    assert ExitCode.INTERNAL == 9
    # mã 1 CỐ Ý không được định nghĩa
    assert 1 not in [e.value for e in ExitCode]


def test_every_error_code_maps_to_an_exit_code() -> None:
    for code in ErrorCode:
        assert code in ERROR_CODE_EXIT_MAP
        assert isinstance(ERROR_CODE_EXIT_MAP[code], ExitCode)


@pytest.mark.parametrize(
    ("code", "expected_exit"),
    [
        (ErrorCode.E_INPUT_SCHEMA, ExitCode.INPUT),
        (ErrorCode.E_SEMANTIC_DEPENDENCY, ExitCode.DEPENDENCY),
        (ErrorCode.E_HASH_MISMATCH, ExitCode.NETWORK),
        (ErrorCode.E_PERMISSION_DENIED, ExitCode.PERMISSION),
        (ErrorCode.E_STATE_CONFLICT, ExitCode.CONFLICT),
        (ErrorCode.E_CANCELLED, ExitCode.CANCELLED),
        (ErrorCode.E_POSTCHECK_FAILED, ExitCode.VERIFY),
        (ErrorCode.E_INTERNAL, ExitCode.INTERNAL),
    ],
)
def test_exit_code_for_known_mappings(code: ErrorCode, expected_exit: ExitCode) -> None:
    assert exit_code_for(code) == expected_exit


# ---------------------------------------------------------------------------
# txstate
# ---------------------------------------------------------------------------


def test_happy_path_transitions_are_valid() -> None:
    happy_path = [
        TxState.NEW,
        TxState.VALIDATED,
        TxState.ACQUIRING,
        TxState.STAGING,
        TxState.INSTALLING,
        TxState.VERIFYING,
        TxState.READY,
    ]
    for before, after in zip(happy_path, happy_path[1:], strict=False):
        assert validate_transition(before, after), f"{before} -> {after} phải hợp lệ"


def test_installing_cannot_skip_verifying_to_ready() -> None:
    assert not validate_transition(TxState.INSTALLING, TxState.READY)


def test_cancelling_from_any_running_state() -> None:
    for running in (
        TxState.ACQUIRING,
        TxState.STAGING,
        TxState.INSTALLING,
        TxState.VERIFYING,
    ):
        assert validate_transition(running, TxState.CANCELLING)


def test_terminal_states_have_no_outgoing_transition() -> None:
    assert not validate_transition(TxState.CANCELLED, TxState.READY)
    assert not validate_transition(TxState.REMOVED, TxState.READY)


def test_recovery_and_removal_paths() -> None:
    assert validate_transition(TxState.FAILED, TxState.RECOVERING)
    assert validate_transition(TxState.RECOVERING, TxState.READY)
    assert validate_transition(TxState.RECOVERING, TxState.NEEDS_ATTENTION)
    assert validate_transition(TxState.READY, TxState.REMOVING)
    assert validate_transition(TxState.REMOVING, TxState.REMOVED)
    assert validate_transition(TxState.REMOVING, TxState.NEEDS_ATTENTION)


# ---------------------------------------------------------------------------
# compat
# ---------------------------------------------------------------------------


def test_compat_status_values() -> None:
    assert {s.value for s in CompatStatus} == {
        "untested",
        "experimental",
        "task_verified",
        "blocked",
        "revoked",
    }


def test_app_mode_values() -> None:
    assert {m.value for m in AppMode} == {"native", "web", "wine", "vm", "remote"}


def test_certification_tuple_is_frozen_dataclass() -> None:
    tup = CertificationTuple(
        os_build="debian-13",
        kernel=None,
        graphics=None,
        desktop_session="kde-plasma",
        runner_hash="a" * 64,
        profile_digest="b" * 64,
        app_build="1.0.0",
        app_hash="c" * 64,
        architecture="x86_64",
        runtime_dependency_versions=("vcrun2019",),
        dataset_revision="rev-1",
        test_suite_revision="rev-1",
        hardware_or_vm_profile="qemu-standard",
    )
    assert tup.os_build == "debian-13"
    with pytest.raises(dataclasses.FrozenInstanceError):
        tup.os_build = "other"  # type: ignore[misc]


def test_about_defaults() -> None:
    assert PRODUCT_NAME == "NaMiOS"
    assert FOUNDERS == ("Đỗ Chí Cường", "Đỗ Bảo Nam")
    info = AboutInfo(
        product_name=PRODUCT_NAME,
        version="0.0.0-dev",
        founders=FOUNDERS,
        legal_entity=None,
        licenses=(ComponentLicense(component="Debian", license="varies", source_url=None),),
        source_urls=(),
        support_contact=None,
    )
    assert info.legal_entity is None  # chưa công bố pháp nhân — UNKNOWN cố ý


# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------


def test_app_name_and_filename_constants() -> None:
    assert APP_NAME == "namios"
    assert STATE_DB_FILENAME == "state.sqlite3"
    assert LOG_MAX_BYTES_DEFAULT == 100 * 1024 * 1024
    assert LOG_MAX_AGE_DAYS_DEFAULT == 14


def test_paths_resolve_under_xdg_env_vars(xdg_tmp_dirs: object) -> None:
    # xdg_tmp_dirs fixture (từ conftest.py gốc) đã set các $XDG_* vào thư mục tạm.
    assert config_dir() == Path(os.environ["XDG_CONFIG_HOME"]) / "namios"
    assert prefixes_dir() == Path(os.environ["XDG_DATA_HOME"]) / "namios" / "prefixes"
    assert state_db_path() == Path(os.environ["XDG_DATA_HOME"]) / "namios" / "state.sqlite3"
    assert cache_dir() == Path(os.environ["XDG_CACHE_HOME"]) / "namios"
    assert logs_dir() == Path(os.environ["XDG_STATE_HOME"]) / "namios" / "logs"


def test_paths_do_not_hardcode_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_home = tmp_path / "someone-else-home"
    fake_home.mkdir()
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(fake_home))
    assert config_dir() == fake_home / ".config" / "namios"


def test_system_wide_paths_are_absolute_and_fixed() -> None:
    assert share_ro_dir() == Path("/usr/share/namios")
    assert system_var_dir() == Path("/var/lib/namios")
