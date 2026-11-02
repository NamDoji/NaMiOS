# ECO — Defects tìm thấy (độc lập, verified bằng test FAIL thật)

2 nhóm defect gốc (root cause riêng biệt), tổng 8 test FAIL thật. Mức độ:
nhóm 1 **cao** (vi phạm trực tiếp GATE "usable" ECO-003/ECO-016 — hiển thị
sai một workflow chưa chạy được gì thật là "dùng được"); nhóm 2 **trung
bình** (bypass GATE ECO-007 bằng biểu diễn Unicode khác, không phải ký tự
lạ/injection).

## Defect ECO-016-QA-01 — `derive_published_status` không coi `discover`/`acquire` bị `BLOCKED` là `blocked_external_dependency`, trả về `partial_workflow` (usable=True) kèm lý do SAI sự thật

- **File/line:** `src/namios_eco/status.py:154` (biến `chain` trong
  `derive_published_status`): `chain = (install, authenticate, by_name[WorkflowStepName.EXECUTE], submit, verify)`
  — chuỗi kiểm "blocked vì phụ thuộc ngoài" CHỦ Ý bắt đầu từ
  `install_or_open`, KHÔNG gồm `discover`/`acquire`.
- **Test chứng minh (FAIL thật):**
  - `tests/qa/ECO/test_eco016_external_block_all_steps_adversarial.py::test_any_step_blocked_by_external_dependency_must_be_blocked_status[discover]`
  - `...[acquire]` (cùng test, tham số khác)
  - `...::test_block_at_discover_or_acquire_must_never_be_shown_usable[discover]`
  - `...[acquire]`
  - `...::test_discover_blocked_reasons_text_must_not_falsely_claim_later_steps_passed`
- **Repro:**
  ```python
  from namios_eco.workflow import WorkflowStep, WorkflowStepName, StepOutcome
  from namios_eco.status import derive_published_status, is_usable

  steps = (
      WorkflowStep(WorkflowStepName.DISCOVER, StepOutcome.BLOCKED,
                   note_vi="Không có kết nối ra ngoài tới domain .gov.vn (ECONNREFUSED) — ECO-016."),
      WorkflowStep(WorkflowStepName.ACQUIRE, StepOutcome.NOT_RUN),
      WorkflowStep(WorkflowStepName.INSTALL_OR_OPEN, StepOutcome.NOT_RUN),
      WorkflowStep(WorkflowStepName.AUTHENTICATE, StepOutcome.NOT_RUN),
      WorkflowStep(WorkflowStepName.EXECUTE, StepOutcome.NOT_RUN),
      WorkflowStep(WorkflowStepName.SUBMIT_OR_EXPORT, StepOutcome.NOT_RUN),
      WorkflowStep(WorkflowStepName.VERIFY_RESULT, StepOutcome.NOT_RUN),
  )
  result = derive_published_status(steps)
  print(result.status.value)   # -> "partial_workflow"
  print(result.reasons_vi)     # -> ("Đã qua authenticate/execute nhưng chưa tới submit_or_export/verify_result.",)
  print(is_usable(result.status))  # -> True
  ```
  (Đã tự chạy trực tiếp bằng `.venv/bin/python3` để xác nhận trước khi viết
  test — không chỉ dựa vào pytest.)
- **Expected:** Theo ECO-016 ("dừng trước bước nộp/ký và ghi
  `blocked_external_dependency`" khi không có sandbox/kết nối) và theo
  đúng hành vi ĐÃ ĐÚNG của chính hàm này khi nấc bị blocked là
  `install_or_open`..`verify_result` (5/7 nấc — có test riêng của dev:
  `tests/unit/eco/test_status_gate.py::test_blocked_external_dependency_from_submit_step`),
  nấc `discover`/`acquire` bị `BLOCKED` PHẢI cho ra cùng kết quả
  `blocked_external_dependency`, và `is_usable()` của kết quả đó PHẢI là
  `False`. `reasons_vi` PHẢI phản ánh đúng sự thật là KHÔNG nấc nào sau
  `discover` được chạy.
- **Actual:**
  - `status` = `partial_workflow` (nằm trong `USABLE_STATUSES`).
  - `is_usable(status)` = `True`.
  - `reasons_vi` = `("Đã qua authenticate/execute nhưng chưa tới submit_or_export/verify_result.",)`
    — câu này khẳng định SAI rằng `authenticate`/`execute` đã chạy, trong
    khi dữ liệu đầu vào ghi rõ CẢ HAI là `not_run`.
  - Hành vi giống hệt (`partial_workflow`, `is_usable=True`) khi đổi nấc
    bị blocked thành `acquire` (giữ `discover=PASS`).
- **Tác động:** Đây KHÔNG phải một ca biên hiếm — nó khớp CHÍNH XÁC tình
  huống thật đang xảy ra với TOÀN BỘ 12 entry trong `catalog/services/*.json`
  hiện có: mỗi file đều ghi trong `source_check`
  ("Host build hiện tại... KHÔNG có kết nối ra ngoài tới các domain
  .gov.vn/vendor... thử WebFetch 02/11/2026 trả ECONNREFUSED/ECONNRESET").
  Các entry này hiện đang ở `published_status="not_inventoried"` (vì
  catalog KHÔNG lưu trường `steps` 7 nấc — `ServiceEntry` chỉ lưu
  `published_status` đã suy ra sẵn), nên bug này **chưa** làm sai dữ liệu
  catalog hiện tại. Nhưng NGAY KHI một người vận hành/CLI tương lai tạo
  `WorkflowResult` thật cho một trong các entry này (tức ghi `discover` =
  `blocked` vì đúng tình huống "không kết nối được tới .gov.vn" rồi gọi
  `derive_published_status` để suy ra `published_status` mới — chính là
  luồng mà `validate_status_matches_workflow` ở `validator.py` giả định sẽ
  được dùng), kết quả suy ra sẽ là `partial_workflow` — một trạng thái
  GATE coi là **usable=True** — cho một workflow mà NaMiOS thậm chí còn
  chưa `discover`/`acquire` được do bị chặn ngoài tầm kiểm soát. Đây là vi
  phạm trực tiếp tinh thần ECO-003 ("downloadable_only/launches_only TUYỆT
  ĐỐI không hiển thị là dùng được") áp dụng mở rộng sang trường hợp còn tệ
  hơn hai trạng thái đó (chưa `discover` xong còn ít thông tin hơn
  `downloadable_only`).
- **Verdict:** CONFIRMED (test tự viết, đối chứng bằng hành vi ĐÃ ĐÚNG của
  cùng hàm ở 5/7 vị trí khác; đã tự chạy script độc lập xác nhận trước khi
  viết test, không chỉ tin vào assertion).
- **Khuyến nghị fix (KHÔNG tự sửa, chỉ báo):** mở rộng `chain` trong
  `derive_published_status` để bao gồm `discover`/`acquire`, hoặc thêm một
  nhánh kiểm `blocked` riêng CHO `discover`/`acquire` chạy TRƯỚC nhánh
  `all_not_run`/`discover.outcome == FAIL`/`acquire.outcome == FAIL` hiện
  tại (thứ tự ưu tiên cần: `all_not_run` → `discover/acquire BLOCKED` →
  `discover/acquire FAIL` → ... giữ nguyên phần còn lại). Đồng thời sửa lại
  nhánh fallback cuối (dòng ~230) để không in cố định câu "Đã qua
  authenticate/execute..." khi các nấc đó thật ra `not_run`.

## Defect ECO-007-QA-01 — `validate_no_official_claim_text` bỏ lọt cụm cấm khi văn bản ở dạng Unicode NFD hoặc chèn zero-width space, dù hiển thị giống hệt bản bị cấm

- **File/line:** `src/namios_eco/validator.py:271-286`
  (`validate_no_official_claim_text`) — chỉ gọi `text.casefold()`, KHÔNG
  chuẩn hoá Unicode (`unicodedata.normalize`) trước khi so khớp substring
  với `_FORBIDDEN_OFFICIAL_CLAIM_PHRASES`.
- **Test chứng minh (FAIL thật):**
  - `tests/qa/ECO/test_eco007_official_claim_text_normalization_adversarial.py::test_nfd_decomposed_forbidden_phrase_bypasses_gate`
  - `...::test_zero_width_space_inside_forbidden_phrase_also_bypasses_gate[before-thuc]`
  - `...[before-cua]`
- **Repro (NFD):**
  ```python
  import unicodedata
  from namios_eco.validator import validate_no_official_claim_text

  nfc_text = "ứng dụng chính thức của NaMiOS cho kế toán."
  nfd_text = unicodedata.normalize("NFD", nfc_text)
  assert unicodedata.normalize("NFC", nfd_text) == nfc_text  # cùng nội dung hiển thị

  validate_no_official_claim_text(nfc_text, path="purpose")  # -> 1 lỗi (ĐÚNG)
  validate_no_official_claim_text(nfd_text, path="purpose")  # -> [] (SAI — bypass)
  ```
- **Repro (zero-width space, chèn trước từ "thức"):**
  ```python
  tampered = "ứng dụng chính ​thức của NaMiOS cho kế toán."
  validate_no_official_claim_text(tampered, path="purpose")  # -> [] (SAI — bypass)
  ```
- **Đối chứng kỹ thuật (trong CÙNG package, namios_eco):**
  `namios_eco.search.fold_vn` (dùng cho ECO-007 tìm kiếm) ĐÃ xử lý đúng
  NFD bằng kỹ thuật `unicodedata.normalize("NFD", ...)` → strip ký tự
  category `Mn` → `normalize("NFC", ...)` → `casefold()`
  (`tests/qa/ECO/...::test_fold_vn_in_same_package_already_handles_nfd_correctly`
  — PASS, xác nhận `fold_vn` không có bug này). Chứng minh gap không phải
  do hạn chế của Python/`unicodedata`, mà do `validate_no_official_claim_text`
  không tái dùng kỹ thuật đã có sẵn trong package của chính nó.
- **Expected:** Cụm "ứng dụng chính thức của NaMiOS" PHẢI bị chặn (ECO-007:
  "cấm tuyệt đối") bất kể văn bản ở dạng Unicode nào miễn hiển thị giống
  nhau cho người đọc — NFC/NFD là 2 cách biểu diễn HỢP LỆ của CÙNG văn bản
  tiếng Việt (không phải ký tự lạ bị cấm), và zero-width space là một ký
  tự định dạng vô hình không làm thay đổi nội dung đọc được.
- **Actual:** cả hai biến thể trả về `[]` (không lỗi) — cụm cấm lọt qua
  hoàn toàn.
- **Tác động:** Một người nhập liệu catalog (vô tình, do copy từ nguồn
  dùng chuẩn hoá khác — ví dụ một số export/field cũ trên Windows hay một
  số công cụ xử lý văn bản tiếng Việt dùng NFD) hoặc cố ý (để né kiểm tra)
  có thể đưa cụm "ứng dụng chính thức của NaMiOS" vào trường `purpose`/mô
  tả của MỘT sản phẩm bên thứ ba mà KHÔNG bị `validate_no_official_claim_text`
  chặn — đúng hành vi ECO-007 mô tả là "cấm tuyệt đối".
- **Verdict:** CONFIRMED.
- **Khuyến nghị fix (KHÔNG tự sửa, chỉ báo):** chuẩn hoá `text` (và các
  phần tử của `_FORBIDDEN_OFFICIAL_CLAIM_PHRASES`) qua cùng kỹ thuật đã có
  ở `namios_eco.search.fold_vn` trước khi so khớp substring trong
  `validate_no_official_claim_text` — có thể gọi trực tiếp `fold_vn` (CÙNG
  package, không phải import chéo sang module khác) vì hàm đó vốn đã công
  khai (`__all__` của `search.py`).

## Quan sát phạm vi (KHÔNG phải defect — ghi lại để tránh báo nhầm)

- `validate_official_url` (ECO-006) không phát hiện domain giả mạo kiểu
  subdomain-suffix (ví dụ `https://dichvucong.gov.vn.phishing-example.com/`
  — domain đăng ký thật là `phishing-example.com`, `gov.vn` chỉ là nhãn
  con). Theo đúng docstring hiện tại, hàm CHỈ kiểm scheme http(s) + thông
  tin xác thực nhúng kiểu `user@host`, không nhận "domain kỳ vọng" làm
  tham số nên không thể tự so khớp registrable-domain. Xem
  `tests/qa/ECO/test_eco006_official_url_domain_spoofing_observation.py`
  (test PASS, chỉ xác nhận hành vi hiện tại, không ép fail). Khuyến nghị
  BA/dev cân nhắc: nếu muốn chặn lớp này, cần thêm tham số domain chính
  thức kỳ vọng theo từng entry (ví dụ `source_check`/một field mới) để
  `validate_official_url` so khớp registrable-domain thật, không chỉ nhìn
  chuỗi con.
- `fold_vn` (search) không strip ký tự định dạng vô hình (category `Cf`,
  ví dụ zero-width space) — chỉ strip tổ hợp dấu (category `Mn`). Hệ quả:
  một `purpose` có chèn ZWSP sẽ KHÔNG khớp tìm kiếm dù nhìn giống văn bản
  gốc. Đây là một thiếu sót CHẤT LƯỢNG TÌM KIẾM (bỏ lọt kết quả đúng),
  KHÔNG phải vấn đề GATE/an toàn như ở `validate_no_official_claim_text`
  (bỏ lọt một trường hợp CẤM) — mức độ thấp hơn hẳn, ghi lại tham khảo,
  không viết test FAIL riêng cho mục này.
