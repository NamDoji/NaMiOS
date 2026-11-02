# T2 — Security path/injection/redaction — evidence (02/11/2026)

**Tester:** T2 (độc lập, không phải dev WP8/WP10). **Phạm vi:** SEC-02, SEC-03, SEC-04, SEC-11
nhắm vào `namios_security` (WP8) và `namios_recipe` (WP10, phần `run_installer` argv).
**Test file:** `tests/qa/T2/` (3 file, 25 test, viết độc lập với
`tests/security/security/*` và `tests/unit/recipe/test_parse_allowlist.py` của dev).

## Lệnh chạy

```
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/node/.openclaw/workspace/code_projects/namios/src \
/home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python -m pytest \
  /home/node/.openclaw/workspace/code_projects/namios/tests/qa/T2 \
  -p no:cacheprovider -q
```

## Kết quả (commit `b0a96d66`, Python 3.11.2, Debian 12)

```
23 passed, 2 failed in 0.26s
```

21/23 pass là test khẳng định bất biến an toàn ĐANG ĐÚNG (symlink chain nhiều
tầng, symlink loop tự trỏ/chéo, dangling symlink, NUL byte giữa chuỗi,
hardlink defense cho mode `xb`/`ab`, TOCTOU stress 400 lần race thật bằng
thread nền đổi symlink, argv-injection không lọt qua shell=False, env
isolation, redaction case/delimiter variants, nested 4-level export, v.v).

2/25 **FAIL — bằng chứng defect thật** (xem `defects.md`):
- `test_sec04_injection_adversarial.py::test_recipe_run_installer_rejects_raw_shell_metachar_in_non_first_argv_element`
- `test_sec11_redaction_adversarial.py::test_redact_text_otp_phrase_with_longer_realistic_vietnamese_gap_not_caught`

1 test ban đầu viết sai kỳ vọng đã được SỬA LẠI kỳ vọng cho đúng hành vi an
toàn thật (không phải defect): `test_backslash_in_candidate_is_literal_not_separator`
— `resolve_within` cho phép leaf CHƯA TỒN TẠI (hành vi THIẾT KẾ, giống test
`nonexistent leaf ok for future create` của dev), backslash không phải
separator trên Linux nên chuỗi `foo\..\secret` là MỘT tên literal, không
thoát ra ngoài base — xác nhận AN TOÀN, không phải lỗi.

## Không chạy được tại đây (not applicable / không có trong phạm vi WP8/WP10)

Không có dòng `blocked_external_dependency` cho T2 — mọi test SEC-02/03/04/11
ở phạm vi WP8+WP10 argv đều chạy được bằng fixture `tmp_path`, không cần
VM/Wine/Polkit/D-Bus thật (khác T2 không bao gồm WP7 helper — đó là cụm
khác theo `qa/plans/M1-QA-PLAN.md`).
