"""Argv-only exec — hiện thực ``namios_core.security_types.SafeExec``.

KHÔNG ``shell=True``, KHÔNG nối chuỗi thành một command line. ``argv`` luôn
truyền dạng ``list[str]`` tới ``subprocess.run`` với ``shell=False``, nghĩa
là metachar shell (``;``, ``|``, ``$()``, backtick, space, v.v.) trong bất kỳ
phần tử argv chỉ là DỮ LIỆU, không bao giờ được diễn giải lại thành lệnh
phụ bởi một shell.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping, Sequence

from namios_core.errors import ErrorCode
from namios_core.security_types import CompletedProc
from namios_security._errors import ExecPolicyError

__all__ = ["ArgvSafeExec", "run_argv"]


def _validate_argv(argv: Sequence[str]) -> tuple[str, ...]:
    if not argv:
        raise ExecPolicyError(reason_vi="argv rỗng")
    items: list[str] = []
    for i, item in enumerate(argv):
        if not isinstance(item, str):
            raise ExecPolicyError(reason_vi=f"argv[{i}] không phải str (shell=False yêu cầu str)")
        items.append(item)
    program = items[0]
    if not program:
        raise ExecPolicyError(reason_vi="argv[0] rỗng")
    if not os.path.isabs(program):
        raise ExecPolicyError(reason_vi="argv[0] phải là đường dẫn tuyệt đối đã allowlist")
    if "\x00" in program:
        raise ExecPolicyError(reason_vi="argv[0] chứa NUL byte")
    if not os.path.exists(program):
        raise ExecPolicyError(reason_vi=f"argv[0] '{program}' không tồn tại")
    if os.path.isdir(program):
        raise ExecPolicyError(reason_vi=f"argv[0] '{program}' là thư mục, không phải file")
    if not os.access(program, os.X_OK):
        raise ExecPolicyError(reason_vi=f"argv[0] '{program}' không có quyền thực thi")
    return tuple(items)


def run_argv(
    argv: Sequence[str],
    *,
    timeout: float,
    env: Mapping[str, str] | None = None,
) -> CompletedProc:
    """Chạy ``argv`` KHÔNG qua shell. ``env=None`` ⇒ kế thừa env tiến trình
    hiện tại (hành vi mặc định của ``subprocess``); caller muốn cô lập env
    nhạy cảm PHẢI tự truyền ``env`` đã lọc tối thiểu."""

    validated = _validate_argv(argv)
    run_env: dict[str, str] | None = dict(env) if env is not None else None

    try:
        completed = subprocess.run(  # noqa: S603 - argv-only, shell=False, đã validate argv[0]
            list(validated),
            shell=False,
            capture_output=True,
            timeout=timeout,
            env=run_env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExecPolicyError(
            reason_vi=f"tiến trình vượt timeout {timeout}s",
            code=ErrorCode.E_CANCELLED,
        ) from exc
    except OSError as exc:
        raise ExecPolicyError(
            reason_vi=f"không khởi chạy được tiến trình ({exc.strerror or exc})"
        ) from exc

    return CompletedProc(
        argv=validated,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


class ArgvSafeExec:
    """Hiện thực ``namios_core.security_types.SafeExec`` (Protocol)."""

    def run_argv(
        self,
        argv: Sequence[str],
        *,
        timeout: float,
        env: Mapping[str, str] | None = None,
    ) -> CompletedProc:
        return run_argv(argv, timeout=timeout, env=env)
