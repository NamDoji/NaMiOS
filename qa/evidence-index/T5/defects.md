# T5 defects — WP9 `namios_evidence` + WP4 `namios_catalog` (02/11/2026)

KHÔNG tự sửa code dev — chỉ báo cáo theo quy tắc T5. 5/19 test FAIL do code
sai (không phải test sai); giữ nguyên FAIL, không đổi skip→pass.

---

## D1 — Path traversal qua `..` đọc được file NGOÀI phạm vi khi KHÔNG có
symlink nào tham gia (`namios_evidence._safe_io.read_text_safe` /
`EvidenceValidatorImpl.load`)

- **File/line:** `src/namios_evidence/_safe_io.py:49-52` (kiểm tra
  `base_real = os.path.realpath(base, strict=False)` so với
  `os.path.abspath(base)`).
- **Test lộ ra (FAIL):**
  - `tests/qa/T5/test_t5_adversarial.py::test_path_traversal_via_dotdot_without_symlink_must_be_rejected`
  - `tests/qa/T5/test_t5_adversarial.py::test_evidence_validator_load_rejects_dotdot_traversal_to_outside_file`
- **Repro (độc lập, không phụ thuộc đường dẫn repo):**
  ```python
  import os, tempfile
  from namios_evidence._safe_io import read_text_safe

  with tempfile.TemporaryDirectory() as tmp:
      intended = os.path.join(tmp, "intended", "evidence")
      os.makedirs(intended)
      secret_dir = os.path.join(tmp, "secret")
      os.makedirs(secret_dir)
      secret_file = os.path.join(secret_dir, "out-of-scope.json")
      with open(secret_file, "w") as fh:
          fh.write('{"marker": "T5-SECRET"}')

      traversal_path = os.path.join(intended, "..", "..", "secret", "out-of-scope.json")
      content = read_text_safe(traversal_path)   # KHÔNG raise PathUnsafeError
      print(content)  # in ra nội dung file NGOÀI "intended/evidence"
  ```
  Đã xác nhận thêm bằng file THẬT trong repo (không phải fixture giả): dùng
  path tuyệt đối chứa `..` trỏ từ một thư mục con bất kỳ về
  `pyproject.toml` ở gốc repo (không qua symlink nào) → `read_text_safe`
  ĐỌC THÀNH CÔNG toàn bộ nội dung file, trả về chuỗi text bình thường,
  không raise gì.
- **Expected (FACT CLAUDE.md "Điều kiện KHÔNG được bỏ qua"):** "chống
  traversal/symlink/TOCTOU (ưu tiên FD-based, realpath+kiểm tra prefix,
  KHÔNG CHỈ check chuỗi '..')" — path mang thành phần `..` trỏ RA NGOÀI phạm
  vi dự kiến của caller phải bị từ chối, bất kể có symlink hay không.
- **Actual:** Hàm chỉ kiểm tra **symlink** (qua so sánh `realpath(base) ==
  abspath(base)`, chỉ lệch nhau khi có symlink TRUNG GIAN trong `base`) và
  **mount point** (qua `open_within`/`st_dev` — chỉ chặn khi đích nằm trên
  filesystem KHÁC). Khi `..` thuần tuý đi qua các thư mục THẬT (không
  symlink) và đích nằm CÙNG filesystem (trường hợp rất phổ biến — mọi thứ
  dưới `/home`, `/tmp`, hay cả `/` trên host container này đều cùng một
  overlayfs, `st_dev` giống nhau), hai lớp bảo vệ hiện có **đều không bắt
  được traversal**. Vì `load(path: str)` KHÔNG nhận tham số `base` tách
  riêng (API chỉ nhận 1 path tuyệt đối duy nhất), hàm không có khái niệm
  "phạm vi cho phép" nào để so khớp `..` — "kiểm tra prefix" mà
  CLAUDE.md/M1-INTERFACES yêu cầu KHÔNG được thực hiện ở đây.
- **Mức độ rủi ro:** Cao cho M1 — đây là primitive đọc file duy nhất của
  WP9; bất kỳ nơi gọi `EvidenceValidatorImpl.load(path)` với `path` có
  nguồn gốc một phần từ input người dùng/manifest/CLI argument (ví dụ ghép
  `evidence_id` từ manifest vào một thư mục gốc rồi gọi `load`) đều có thể
  bị dẫn đọc file bất kỳ trên hệ thống mà tiến trình có quyền đọc (ví dụ
  file cấu hình nhạy cảm khác, không chỉ trong phạm vi evidence).
- **Gợi ý cho dev (không áp đặt):** cân nhắc 1 trong 2 hướng — (a) đổi chữ
  ký nội bộ để `read_text_safe` nhận THÊM một `allowed_root` tường minh và
  tự gọi `namios_security.resolve_within(allowed_root, candidate)` (đã có
  sẵn ở WP8, đúng tinh thần "mọi path do caller cung cấp PHẢI qua
  `resolve_within()`" của M1-INTERFACES §6) thay vì tự chế lại kiểm tra
  path trong `namios_evidence`; hoặc (b) nếu thiết kế CHỦ Ý để `load(path)`
  nhận path tuyệt đối "đã được caller xác định đúng, không cần sandbox"
  (giống kiểu mở file trực tiếp của người dùng) — cần ghi rõ ràng buộc này
  trong docstring `EvidenceValidator.load` ở `namios_core/evidence_types.py`
  và M1-INTERFACES để các WP gọi nó (CLI/wiring) biết PHẢI tự
  `resolve_within` một gốc hợp lệ TRƯỚC khi gọi `load`, tránh hiểu nhầm
  "load() đã tự an toàn hoàn toàn".

---

## D2 — `compute_allowed_status` cấp `task_verified` cho `qa_reviewer` rỗng
hoặc chỉ khoảng trắng (`namios_evidence._gate.compute_allowed_status`)

- **File/line:** `src/namios_evidence/_gate.py:70` (`if rep.qa_reviewer is
  None:`).
- **Test lộ ra (FAIL):**
  - `tests/qa/T5/test_t5_adversarial.py::test_gate_treats_empty_string_reviewer_as_no_reviewer`
  - `tests/qa/T5/test_t5_adversarial.py::test_gate_treats_whitespace_only_reviewer_as_no_reviewer`
- **Repro:**
  ```python
  from namios_core.evidence_types import EvidenceReport, EvidenceTest
  from namios_evidence._gate import compute_allowed_status

  rep = EvidenceReport(
      report_id="r", manifest_id="app-x",
      tests=(EvidenceTest(test_id="T1", required=True, result="pass"),),
      decision="task_verified",
      qa_reviewer="",          # hoặc "   "
      environment={},
  )
  gate = compute_allowed_status(rep)
  print(gate.allowed_status)   # CompatStatus.TASK_VERIFIED — SAI
  ```
- **Expected (FACT §11.2):** `task_verified` chỉ hợp lệ khi có
  `qa_approval.reviewer != null` **VÀ ngụ ý là một danh tính QA thật**
  (không phải placeholder rỗng). Hàm gate — nơi RA QUYẾT ĐỊNH CUỐI CÙNG,
  theo đúng nguyên tắc "schema hợp lệ ≠ an toàn" (tức: không được giả định
  dữ liệu đưa vào gate luôn đã qua đúng một con đường duy nhất là
  `validate_schema` trước) — phải tự đủ điều kiện để không bị qua mặt bằng
  reviewer rỗng/khoảng trắng.
- **Actual:** Gate chỉ kiểm `is None`. Hiện tại nó AN TOÀN trên thực tế chỉ
  vì `EvidenceValidatorImpl.load()` luôn chạy `validate_schema` trước
  (schema có `minLength: 1` trên `qa_approval.reviewer`, chặn `""` — nhưng
  **KHÔNG chặn `"   "` vì khoảng trắng tính là ký tự, độ dài ≥ 1**). Khi
  `EvidenceReport`/`compute_allowed_status` được dùng TRỰC TIẾP (dataclass
  thuần, public API theo Protocol §7.7 — không bắt buộc đi qua `load()`,
  ví dụ bởi CLI wiring tương lai lắp từ nguồn khác như DB/import), lớp
  phòng thủ duy nhất biến mất và `task_verified` bị cấp sai cho một
  "reviewer" không phải danh tính thật (`""`) hoặc rõ ràng vô nghĩa
  (`"   "`).
- **Mức độ rủi ro:** Trung bình — đây là gate "không task_verified khi
  thiếu QA approval" (MAN-04, bất biến cốt lõi nhất của WP9); lỗ hổng chỉ
  lộ khi có caller KHÔNG đi qua `load()`, nhưng Protocol công khai hoàn
  toàn cho phép điều đó (không có gì trong kiểu dữ liệu ép phải qua
  `load()` trước khi gọi `compute_allowed_status()`).
- **Gợi ý cho dev (không áp đặt):** thêm điều kiện
  `rep.qa_reviewer is None or not rep.qa_reviewer.strip()` thay cho
  `is None` đơn thuần tại dòng 70 của `_gate.py` — tự gate đủ điều kiện,
  không phụ thuộc tầng schema đã chạy trước đó.

---

## D3 — `InMemoryCatalogStore.search()` không chuẩn hoá khoảng trắng trong
query (UX-006)

- **File/line:** `src/namios_catalog/store.py:38-45` (xây `haystack` bằng
  `" ".join(...)` — luôn đúng 1 khoảng trắng) so với `search()` dòng 58
  (`folded_query = fold_vn(query).strip()` — chỉ `strip()` 2 đầu, KHÔNG
  collapse khoảng trắng LIÊN TIẾP ở giữa).
- **Test lộ ra (FAIL):**
  `tests/qa/T5/test_t5_adversarial.py::test_search_query_with_double_internal_space_still_matches`
- **Repro:**
  ```python
  store = InMemoryCatalogStore()
  store.add(make_entry("vn-demo", "Đỗ Chí Cường Studio", "NaMiOS"))
  store.search("Đỗ Chí Cường")      # -> 1 kết quả
  store.search("Đỗ  Chí   Cường")   # -> () RỖNG — cùng ý nghĩa, lỗi gõ phổ biến
  ```
- **Expected:** UX-006 chỉ nói accent-insensitive + case-insensitive, không
  nói rõ về khoảng trắng — nhưng theo tinh thần "tìm kiếm tiếng Việt" chịu
  lỗi gõ thực tế (bộ gõ Telex/VNI đôi khi chèn khoảng trắng kép khi gõ
  nhanh hoặc copy-paste từ nguồn khác), substring match không nên vỡ chỉ vì
  số khoảng trắng khác nhau.
- **Actual:** `fold_vn` không collapse whitespace; `search()` so khớp
  substring trực tiếp trên chuỗi đã fold → khoảng trắng kép trong query
  không khớp khoảng trắng đơn trong haystack.
- **Mức độ rủi ro:** Thấp (chất lượng tìm kiếm/UX, KHÔNG phải an toàn) —
  không chặn cài đặt, không rò dữ liệu; chỉ làm người dùng tìm không ra app
  dù gõ đúng tên nhưng lỡ tay thêm khoảng trắng.
- **Gợi ý cho dev (không áp đặt):** collapse khoảng trắng liên tiếp thành 1
  (ví dụ `" ".join(folded_query.split())`) trước khi so khớp substring
  trong `search()`.

---

## Không phải defect

14/19 test khẳng định đúng các bất biến MAN-04 (gate không tin `decision`
tự xưng, không suy diễn `task_verified` từ report rỗng test) và UX-03
(unknown key lồng bị schema chặn, type confusion bị chặn, DoS-by-size bị
chặn, identity app_id phân biệt hoa/thường tách biệt khỏi tầng fold search,
NFD/NFC đều khớp đúng, revoked entry vẫn trả về từ store — đúng thiết kế đã
công bố) đều PASS đúng như kỳ vọng của đặc tả, không có false positive nào
cần chỉnh.
