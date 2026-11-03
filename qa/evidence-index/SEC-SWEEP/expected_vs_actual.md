# SEC-SWEEP — 4 finding thật (expected vs actual)

Mỗi finding dưới đây là lỗ hổng THẬT xác nhận bằng test tái lập được (giữ
trong `tests/security/sweep/` với `pytest.mark.xfail(strict=True, ...)`).
KHÔNG tự sửa code module khác — chỉ báo cáo.

---

## SEC-SWEEP-001 — TOCTOU đọc nguồn trong `namios_welcome.migrate` (SEC-002, DATA-002)

- **Module/file:line:** `src/namios_welcome/migrate.py:325-330` (phương
  thức `WindowsDataMigrator.migrate`).
- **Test:** `tests/security/sweep/test_data002_welcome_migrate_adversarial.py::test_migrate_toctou_source_file_swapped_to_symlink_leaks_outside_data`
- **Expected (SEC-002 — "mọi đường dẫn đầu vào xử lý symlink... race TOCTOU,
  không chỉ kiểm tra chuỗi `..`"; DATA-002 — chỉ đọc 4 thư mục quen thuộc
  trong `source_root` đã mount, không đọc ngoài phạm vi đó):** sau khi
  `resolve_within(category_root, relative)` xác nhận `relative` không phải
  symlink/không băng mount point, lệnh đọc THẬT phải giữ nguyên bất biến đó
  (FD-based, không theo symlink mới nếu bị đổi sau khi xác nhận).
- **Actual:** dòng 326-330 dùng:
  ```python
  with (
      open(source_abs, "rb") as src,                      # builtin open() — THEO symlink
      open_within(str(dest_home_path), final_relative, "xb") as dst,
  ):
      shutil.copyfileobj(src, dst)
  ```
  `source_abs` là một CHUỖI đường dẫn trả về từ `resolve_within` (đã đóng FD
  trung gian) — không phải một FD đã pin. Giữa thời điểm `resolve_within`
  trả về và thời điểm `open()` thực thi, nếu `source_abs` bị đổi (xóa file
  thường, tạo symlink cùng tên trỏ ra ngoài `source_root`), `open()` BUILTIN
  sẽ theo symlink mới (không có `O_NOFOLLOW`). Repro (mock hóa race bằng
  monkeypatch `resolve_within` để swap NGAY SAU khi nó xác nhận an toàn):
  `migrate()` sao chép đúng nội dung `outside_secret.txt` (ngoài
  `source_root`) vào `dest_home/Documents/report.txt` — không raise, không
  cảnh báo, báo cáo `files_copied=1` như một lần copy bình thường.
- **Ảnh hưởng thực tế:** `source_root` trong luồng DATA-002 là MỘT PHÂN
  VÙNG WINDOWS ĐÃ MOUNT — nếu đó là volume đa người dùng, mount network,
  hoặc bị người dùng khác/tiến trình khác trên máy ghi được trong lúc
  import chạy (ví dụ dual-boot với user khác có quyền trên volume chia sẻ,
  hoặc timing sau khi mount tạm cho import), một symlink-swap đúng lúc có
  thể khiến NaMiOS copy bất kỳ file nào (SSH key, token trình duyệt, DB
  password) vào home người dùng dưới vẻ ngoài một file "Documents" vô hại.
- **Severity:** P1 (đọc-xuyên-ranh-giới có điều kiện race cụ thể; không
  phải lúc nào cũng khai thác được nhưng vi phạm trực tiếp bất biến SEC-002
  mà chính module này tuyên bố tuân theo ở docstring).
- **Khuyến nghị vá (không tự làm):** dùng `namios_security.open_within`
  cho CẢ phía đọc (không chỉ phía viết `dst`), giữ một FD duy nhất xuyên
  suốt thao tác `copyfileobj` thay vì resolve-rồi-mở-lại-bằng-string.

---

## SEC-SWEEP-002 — TOCTOU đọc manifest trong `namios_manifest._safe_io` (SEC-002)

- **Module/file:line:** `src/namios_manifest/_safe_io.py:53-68` (hàm
  `read_text_safe`).
- **Test:** `tests/security/sweep/test_sec002_manifest_safeio_toctou_finding.py::test_read_text_safe_toctou_intermediate_dir_swap_leaks_outside_file`
- **Expected (SEC-002 — "Privileged helper không ghi vào đường dẫn tùy ý...
  không chỉ kiểm tra chuỗi `..`"; M1-INTERFACES §7.1 `ManifestValidator.load`
  "dùng `resolve_within` + safe read"):** đọc file manifest từ một nguồn
  KHÔNG tin cậy (TA-01 — "Manifest/profile độc hại") phải chống được
  symlink TRUNG GIAN bị đổi GIỮA lúc kiểm và lúc đọc, giống hệt bất biến mà
  `namios_security.safe_path` (FD-based, `dir_fd` + `O_NOFOLLOW` MỖI bước)
  đã chứng minh giữ được (xem `test_sec002_safe_path_adversarial.py` —
  cùng kịch bản race, phòng thủ đó GIỮ).
- **Actual:** hàm này (tự nhận trong docstring là "lớp đọc file tối thiểu
  interim — chờ `namios_security` của WP8... TODO chuyển sang gọi nó") làm:
  1. `real = os.path.realpath(path)`; so sánh với `abspath(path)` — CHỈ xác
     nhận "không có symlink NGAY LÚC NÀY".
  2. `fd = os.open(path, O_RDONLY | O_NOFOLLOW | ...)` — dùng LẠI chuỗi
     `path` gốc, không phải FD-based walk.
  `O_NOFOLLOW` trong `open()` chỉ chặn symlink ở THÀNH PHẦN CUỐI của
  đường dẫn khi kernel resolve — các thành phần THƯ MỤC TRUNG GIAN vẫn được
  resolve bình thường (theo symlink) vì không có cách truyền "O_NOFOLLOW
  cho từng thành phần" qua một lệnh `open()` bằng chuỗi path đầy. Repro
  (monkeypatch `os.open` để swap thư mục `profiles/` thành symlink → thư
  mục attacker NGAY TRƯỚC lệnh `os.open` thật chạy): `read_text_safe()` trả
  về nội dung file trong thư mục ATTACKER (`DA BI DOC TU NGOAI...`), không
  raise `PathUnsafeError`.
- **Ảnh hưởng thực tế:** `ManifestValidatorImpl.load()` — API tải manifest
  công khai của WP2 — gọi thẳng hàm này (`validator.py:56`). Đây là đường
  nạp dữ liệu KHÔNG TIN CẬY chính (catalog/profile của actor TA-01). Một
  attacker kiểm soát timing ghi vào thư mục chứa profile (vd race ngay sau
  khi CLI vừa `stat`/liệt kê thư mục catalog cache, hoặc một symlink race
  cổ điển trên thư mục dùng chung nhiều tiến trình) có thể khiến NaMiOS
  đọc một manifest KHÁC (bị thay bởi attacker) mà vẫn tưởng đang đọc đúng
  file đã kiểm.
- **Severity:** P1 — cùng lớp lỗ hổng với SEC-SWEEP-001, khác module; xác
  nhận đây là một lớp lỗi HỆ THỐNG (bất cứ ai tự chế lại "kiểm rồi mở bằng
  string" thay vì dùng `namios_security.safe_path` thật sẽ mắc lại).
- **Khuyến nghị vá (không tự làm):** đúng như TODO trong docstring của
  chính module — chuyển `read_text_safe` sang gọi
  `namios_security.open_within` (đã CHỨNG MINH giữ được race này, xem
  `test_sec002_safe_path_adversarial.py::test_resolve_within_toctou_intermediate_dir_swapped_mid_walk`).

---

## SEC-SWEEP-003 — PEM/SSH private key lộ qua `redact_text`/`redact_obj` khi ở chuỗi tự do (SEC-009)

- **Module/file:line:** `src/namios_security/redactor.py:46-91` (các regex
  lớp "content-based": `_ASSIGNMENT_RE`, `_BEARER_RE`, `_OTP_PHRASE_RE`,
  `_PRIVATE_IPV4_RE`, `_HOME_PATH_RE` — không có mẫu nào cho khối PEM).
- **Test:**
  `tests/security/sweep/test_redaction_adversarial.py::test_redact_text_masks_pem_rsa_private_key_block_in_free_text`,
  `::test_redact_text_masks_openssh_private_key_block_in_free_text`,
  `::test_redact_obj_masks_pem_private_key_embedded_in_free_text_field`.
- **Expected (SEC-009 + chỉ đạo sweep — "password/token/cookie/OTP/QR/
  private-key KHÔNG bao giờ lộ ra log/envelope/diagnostics/export"; docstring
  `redactor.py` tự liệt "private key" trong danh sách field nhạy cảm cần
  lọc "bất kể kiểu dữ liệu"):** một khối PEM/SSH private key tình cờ lọt
  vào MỘT CHUỖI TỰ DO (không dưới field tên `private_key`) — ví dụ message
  lỗi khi parse file config của người dùng, hoặc traceback nhúng nội dung
  file — PHẢI vẫn được `redact_text()`/`redact_obj()` ẩn đi, vì đây chính
  là kịch bản log/diagnostics thực tế (lỗi KHÔNG xảy ra dưới một field tên
  gọn gàng "private_key", mà trong một câu mô tả lỗi).
- **Actual:**
  ```python
  >>> redact_text("Lỗi khi nạp khóa: -----BEGIN RSA PRIVATE KEY-----\n"
  ...              "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcw...\n"
  ...              "-----END RSA PRIVATE KEY-----\n")
  'Lỗi khi nạp khóa: -----BEGIN RSA PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcw...\n-----END RSA PRIVATE KEY-----\n'
  ```
  Toàn bộ khối PEM (header, base64 payload, footer) đi qua NGUYÊN VẸN.
  Tương tự với `redact_obj({"message": <PEM>})` — field "message" không
  khớp tên nhạy cảm nên chỉ chạy `redact_text` trên giá trị, vẫn lộ.
  Nguyên nhân: `_ASSIGNMENT_RE` chỉ bắt dạng `key: value`/`key=value` với
  `value` KHÔNG chứa khoảng trắng/dấu phẩy/chấm phẩy (`[^\s,;]+`) — một
  khối PEM nhiều dòng với base64 không khớp mẫu "gán giá trị đơn" này, và
  không có regex riêng nào cho `-----BEGIN ... PRIVATE KEY-----`.
- **Ảnh hưởng thực tế:** mọi điểm trong hệ thống gọi `redact_text`/
  `redact_obj` trên log/diagnostics-export/`ErrorBody.details` (theo đúng
  M1-INTERFACES §7.8 "Mọi `ErrorBody.details`, log, diagnostics export
  phải đi qua `Redactor`") sẽ KHÔNG chặn được rò khóa riêng nếu nội dung
  khóa lọt vào một message tự do — ví dụ exception message khi Wine/app
  đọc lỗi một file `.pem`/`id_rsa` do người dùng cấu hình nhầm đường dẫn,
  hoặc log debug in nguyên văn nội dung file input.
- **Severity:** P1 (lộ bí mật dài hạn — private key không xoay được dễ như
  password/OTP; nằm đúng trong nhóm tài sản AS-02/AS-03 của threat model).
- **Khuyến nghị vá (không tự làm):** thêm một regex nhận diện khối
  `-----BEGIN [A-Z ]*PRIVATE KEY-----...-----END [A-Z ]*PRIVATE KEY-----`
  (DOTALL) vào lớp content-based của `redact_text`, chạy TRƯỚC các regex
  khác (để không bị `_ASSIGNMENT_RE` cắt vụn trước).

---

## SEC-SWEEP-004 — `open_within()` treo vô hạn khi mở FIFO (DoS, NET-001 class)

- **Module/file:line:** `src/namios_security/safe_path.py:203`
  (`open_flags = extra_flags | os.O_NOFOLLOW | ...` — thiếu `O_NONBLOCK`).
- **Test:**
  `tests/security/sweep/test_sec002_evidence_safeio_adversarial.py::test_rejects_non_regular_file_fifo_without_hanging_process`
  (chạy trong subprocess với `timeout=3.0` để không treo cả sweep khi lỗ
  hổng còn mở — xác nhận riêng, không qua test, bằng `timeout 5
  python -c "..."` thật trên host: tiến trình bị kernel kill ở giây thứ 5,
  không tự thoát).
- **Expected (nguyên tắc DoS — "giới hạn kích thước/độ sâu parser"; mở
  rộng tự nhiên: input không tin cậy không được khiến caller TREO VÔ HẠN):**
  mở một đường dẫn không phải file thường (FIFO/socket/char device) qua
  `open_within` phải THẤT BẠI NHANH (raise `PathUnsafeError`), không bao
  giờ block tiến trình gọi vô thời hạn.
- **Actual:** `open_within()` build `open_flags` không có `os.O_NONBLOCK`.
  Khi `candidate` là một FIFO (`os.mkfifo`) chưa có writer kết nối,
  `os.open(leaf, open_flags, ..., dir_fd=parent_fd)` ở dòng 205 BLOCK VÔ
  HẠN bên trong kernel (chờ writer) — code kiểm `S_ISREG` sau khi mở
  KHÔNG BAO GIỜ được chạy tới vì `open()` chưa trả về. Xác nhận bằng
  `timeout 5 python -c "open_within(...)"` → exit code 124 (bị kill do
  timeout), không có output "opened: ...".
  `namios_manifest/_safe_io.py` (một module KHÁC, không dùng
  `namios_security`) đã tự thêm `os.O_NONBLOCK` với comment rõ ràng "tránh
  treo nếu path là FIFO" — nghĩa là rủi ro này ĐÃ được một dev khác nhận ra
  và vá ở MỘT nơi, nhưng module nền chung `namios_security.safe_path` (mà
  mọi WP khác "chỉ import từ đây" theo M1-INTERFACES §0) lại thiếu.
- **Ảnh hưởng thực tế:** mọi caller dùng `open_within`/`read_text_safe`
  của `namios_evidence` (và tương tự nếu `namios_dotnet`/module khác
  chuyển sang dùng `open_within` cho đọc như TODO khuyến nghị ở
  SEC-SWEEP-001/002) trên một đường dẫn mà NỘI DUNG do nguồn không tin cậy
  kiểm soát (ví dụ thư mục chứa evidence report do một profile tải về) có
  thể bị treo vô hạn một luồng xử lý — DoS cục bộ (không crash, nhưng
  "hang" một request/CLI invocation cho tới khi bị kill ngoài).
- **Severity:** P2 (cần điều kiện đặc thù — kẻ tấn công phải đặt được một
  FIFO tại đúng path sẽ bị đọc; không rò dữ liệu, "chỉ" treo).
- **Khuyến nghị vá (không tự làm):** thêm `os.O_NONBLOCK` vào
  `open_flags` trong `safe_path.open_within` (giống cách
  `namios_manifest/_safe_io.py` đã làm), rồi `fcntl`/clear lại
  `O_NONBLOCK` sau khi mở thành công nếu caller cần blocking I/O thông
  thường trên file thường (file thường mở với `O_NONBLOCK` không ảnh
  hưởng hành vi đọc/ghi, chỉ FIFO/device mới khác biệt).

---

## Tóm tắt test KHÔNG lộ lỗ hổng (phòng thủ giữ) — 140/146

Xem `README.md` bảng theo file; chi tiết từng case nằm trực tiếp trong tên
test + docstring của từng file `tests/security/sweep/test_*.py` (đặt tên
mô tả hành vi tấn công + kỳ vọng, không cần lặp lại ở đây).
