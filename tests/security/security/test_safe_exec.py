"""Unit test WP8 — ``namios_security.safe_exec`` (SEC-04)."""

from __future__ import annotations

import shutil

import pytest

from namios_security import ArgvSafeExec, ExecPolicyError, run_argv


def _echo_path() -> str:
    path = shutil.which("echo")
    assert path is not None, "cần 'echo' có trong PATH để test run_argv"
    return path


def _sh_path() -> str:
    path = shutil.which("sh")
    assert path is not None, "cần 'sh' có trong PATH để test run_argv"
    return path


def test_run_argv_happy_path_echo() -> None:
    echo = _echo_path()
    result = run_argv([echo, "hello-namios"], timeout=5.0)
    assert result.returncode == 0
    assert b"hello-namios" in result.stdout
    assert result.argv == (echo, "hello-namios")


def test_run_argv_filename_with_shell_metacharacters_is_inert_data() -> None:
    """Chuỗi chứa metachar shell (``; rm -rf /``) truyền qua argv KHÔNG được
    diễn giải lại thành lệnh phụ vì ``shell=False`` — nó chỉ là một đối số
    văn bản được echo lại nguyên vẹn."""

    echo = _echo_path()
    payload = "; rm -rf / # $(whoami) `id` | cat /etc/passwd"
    result = run_argv([echo, payload], timeout=5.0)
    assert result.returncode == 0
    assert payload.encode() in result.stdout


def test_run_argv_rejects_relative_program_path() -> None:
    with pytest.raises(ExecPolicyError):
        run_argv(["echo", "hi"], timeout=5.0)


def test_run_argv_rejects_empty_argv() -> None:
    with pytest.raises(ExecPolicyError):
        run_argv([], timeout=5.0)


def test_run_argv_rejects_nonexistent_program() -> None:
    with pytest.raises(ExecPolicyError):
        run_argv(["/no/such/binary/namios-does-not-exist", "x"], timeout=5.0)


def test_run_argv_rejects_non_executable_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    not_exec = tmp_path / "not-a-binary.txt"
    not_exec.write_text("plain text, not executable")
    not_exec.chmod(0o600)
    with pytest.raises(ExecPolicyError):
        run_argv([str(not_exec)], timeout=5.0)


def test_run_argv_rejects_directory_as_program(tmp_path) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ExecPolicyError):
        run_argv([str(tmp_path)], timeout=5.0)


def test_run_argv_timeout_raises_exec_policy_error() -> None:
    sh = _sh_path()
    with pytest.raises(ExecPolicyError) as exc_info:
        run_argv([sh, "-c", "sleep 5"], timeout=0.2)
    assert exc_info.value.code.value == "E_CANCELLED"


def test_run_argv_passes_explicit_minimal_env() -> None:
    sh = _sh_path()
    result = run_argv(
        [sh, "-c", 'echo "$NAMIOS_TEST_VAR"'],
        timeout=5.0,
        env={"NAMIOS_TEST_VAR": "wp8-value", "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0
    assert b"wp8-value" in result.stdout


def test_run_argv_nonzero_exit_code_is_reported_not_raised() -> None:
    sh = _sh_path()
    result = run_argv([sh, "-c", "exit 7"], timeout=5.0)
    assert result.returncode == 7


def test_argv_safe_exec_protocol_class_delegates() -> None:
    impl = ArgvSafeExec()
    echo = _echo_path()
    result = impl.run_argv([echo, "via-protocol"], timeout=5.0)
    assert result.returncode == 0
    assert b"via-protocol" in result.stdout
