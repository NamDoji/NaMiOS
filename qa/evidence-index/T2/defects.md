# T2 defects — SEC-04 / SEC-11 (02/11/2026)

Cả hai đều xác nhận bằng test FAIL thật (không phải test viết sai) trong
`tests/qa/T2/`. KHÔNG tự sửa code dev — chỉ báo cáo theo quy tắc T2.

---

## D1 — SEC-04: `namios_recipe._parse._build_run_installer` chỉ bắt
metachar shell thô khi `len(argv) == 1`

- **File/line:** `src/namios_recipe/_parse.py:186-195` (hàm `_build_run_installer`).
- **Test lộ lỗi:** `tests/qa/T2/test_sec04_injection_adversarial.py::test_recipe_run_installer_rejects_raw_shell_metachar_in_non_first_argv_element`
- **Repro:**
  ```python
  raw = [{
      "action": "run_installer",
      "params": {
          "installer_ref": "setup.exe",
          "argv": [
              "/opt/wine/bin/wine",
              "setup.exe",
              "--post-install=;touch /tmp/pwned-recipe-t2;",
          ],
      },
  }]
  parse_recipe_steps(raw)  # KHÔNG raise — mong đợi RecipeParseError
  ```
- **Expected:** `parse_recipe_steps` từ chối (raise `RecipeParseError`,
  `E_SEMANTIC_RECIPE`) vì phần tử argv thứ 3 chứa metachar shell ghép lệnh
  phụ rõ ràng (`;...;`), đúng tinh thần COMP-004 "argv-only, phát hiện dấu
  hiệu ghép lệnh" đã áp dụng cho case `len(argv)==1`.
- **Actual:** `parse_recipe_steps` TRẢ VỀ step hợp lệ (không raise). Lý do:
  `_SHELL_METACHAR_RE` trong `_build_run_installer` CHỈ chạy khi
  `len(argv) == 1`:
  ```python
  if len(argv) == 1 and _SHELL_METACHAR_RE.search(argv[0]):
      ...  # reject
  ```
  Từ phần tử thứ 2 trở đi, chỉ có `_scan_string_for_injection` chạy — hàm
  này CHỈ bắt template nội suy (`{{...}}`/`${...}`/`%(...)s`) và url-script
  (`https://...| sh`), KHÔNG bắt metachar shell thô (`;`, `&&`, `|`, backtick)
  trong các phần tử argv không phải phần tử đầu.
- **Lớp phòng thủ runtime (`dry_run`) có cùng gap:** `src/namios_recipe/_dry_run.py:74-87`
  (`_check_step` cho `RunInstaller`) lặp lại CHÍNH XÁC điều kiện
  `len(step.argv) == 1 and _SHELL_METACHAR_RE.search(...)` — nên `dry_run`
  cũng không bắt case này (không phải "lớp 2 bù cho lớp 1").
- **Mức độ rủi ro thực tế (quan trọng, để dev cân nhắc mức ưu tiên):** vì
  `namios_security.run_argv` (WP8) luôn chạy `shell=False` + argv thật
  (không nối chuỗi), payload này KHÔNG thể biến thành lệnh phụ khi THỰC
  THI thật (M2+). Đây là lỗ hổng ở **tầng validation/biểu diễn** (recipe
  "trông như command injection" lẽ ra phải bị từ chối sớm ở `parse`/`dry_run`
  theo đúng tinh thần đặc tả, không phải lỗ hổng cho phép chạy lệnh phụ thật
  ngay tại M1) — nhưng vẫn là sai lệch so với acceptance WP10 "`RunInstaller`
  với chuỗi shell ghép → bị coi là argv data, reject nếu không phải list
  argv hợp lệ" (M1-WORK-PACKAGES.md WP10) khi áp dụng cho MỌI phần tử, không
  chỉ phần tử duy nhất.
- **Gợi ý cho dev (không áp đặt):** áp dụng `_SHELL_METACHAR_RE.search(item)`
  cho TỪNG phần tử argv (không chỉ khi `len(argv)==1`), đồng bộ ở cả
  `_parse.py` và `_dry_run.py`.

---

## D2 — SEC-11: `namios_security.redactor._OTP_PHRASE_RE` dùng cửa sổ
khoảng cách cố định `{0,12}` ký tự — câu tiếng Việt tự nhiên hơi dài làm OTP
lọt qua redaction

- **File/line:** `src/namios_security/redactor.py:55-58` (`_OTP_PHRASE_RE`).
- **Test lộ lỗi:** `tests/qa/T2/test_sec11_redaction_adversarial.py::test_redact_text_otp_phrase_with_longer_realistic_vietnamese_gap_not_caught`
- **Repro:**
  ```python
  redact_text("Mã OTP của giao dịch chuyển tiền là 773311, không chia sẻ cho ai.")
  # -> "773311" VẪN CÒN trong output
  ```
- **Expected:** số OTP sau cụm từ nhận diện ("OTP"/"mã xác minh"/...) phải
  bị mask bất kể vài từ tiếng Việt tự nhiên chen giữa cụm từ và con số (ví
  dụ dev's test đã pass với "Mã OTP của bạn là 482913" — khoảng cách vừa
  đủ ≤12 ký tự).
- **Actual:** regex `_OTP_PHRASE_RE = r"(?i)\b(OTP|mã xác minh|mã xác thực|
  verification code|security code)\b[^\d]{0,12}(\d{4,8})"` giới hạn CỨNG
  tối đa 12 ký tự không-phải-số giữa cụm từ khoá và chữ số. Câu
  "của giao dịch chuyển tiền là " dài hơn 12 ký tự (≈30 ký tự) → không khớp
  → `773311` không bị mask, lộ ra `details`/log/export thật nếu gặp câu dài
  tương tự (hoàn toàn hợp lý trong hội thoại/log thật tiếng Việt, không
  phải trường hợp hiếm).
- **Gợi ý cho dev (không áp đặt):** tăng ngưỡng khoảng cách (ví dụ 40-60 ký
  tự) hoặc đổi chiến lược: tách cụm từ khoá và tìm CHỮ SỐ 4-8 số GẦN NHẤT
  trong cùng câu/cùng dấu câu (`.`/`,`/`;`) thay vì đếm ký tự cố định — câu
  tiếng Việt có độ dài biến thiên lớn hơn tiếng Anh do cấu trúc trợ từ.

---

## Không phải defect (đã tự sửa test, ghi lại để tránh hiểu nhầm)

- `foo\..\secret-backslash-test.txt` làm candidate cho `resolve_within`:
  ban đầu kỳ vọng sai (nghĩ phải raise `PathUnsafeError` vì không tồn tại).
  Thực tế `resolve_within` CHỦ Ý cho phép leaf chưa tồn tại (dùng cho
  planning trước khi tạo file) — đây là hành vi thiết kế đúng, giống test
  `test_resolve_within_nonexistent_leaf_ok_for_future_create` của dev.
  Backslash không phải separator trên Linux nên toàn chuỗi vẫn là MỘT
  thành phần literal nằm trong base — KHÔNG thoát ra ngoài. Đã cập nhật
  test để khẳng định đúng tính an toàn này.
