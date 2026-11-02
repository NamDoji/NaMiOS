# ECO-BACKLOG — Phụ lục 02 (Hệ sinh thái phần mềm thiết yếu VN)

**Nguồn:** `docs/specs/PHU-LUC-02-HE-SINH-THAI-VN.md` (toàn văn ECO-001..024).
**Phiên này:** triển khai lõi Python thuần `namios_eco` (schema, state machine 7
nấc, validator 2 tầng, coverage, search) + `contracts/service-catalog.schema.json`.
Môi trường build hiện tại (Debian 12, không KVM/wine/token/máy in/cổng nhà
nước thật — xem `CLAUDE.md`) ⇒ phần việc cần giao dịch THẬT với cổng nhà nước
luôn `BLOCKED-sandbox`, không giả lập để báo đạt (ECO-016).

Phân loại trạng thái:
- **done-at-core** — đã có model/logic Python + test unit xanh trong
  `namios_eco`/`tests/unit/eco`.
- **data** — cần dữ liệu khảo sát/thoả thuận thật từ chủ dự án hoặc đơn vị
  pilot; code core không tự bịa dữ liệu này.
- **cli** — phần hiển thị/vận hành (CLI/dashboard/doctor) thuộc WP3/namios_cli
  hoặc namios_doctor, ngoài phạm vi sở hữu `namios_eco` của phiên này.
- **BLOCKED-sandbox** — cần sandbox/host thật/quyền nhà cung cấp, không có ở
  môi trường build hiện tại; KHÔNG giả lập.

| Mã | Tóm tắt | Trạng thái | File/module |
| --- | --- | --- | --- |
| ECO-001 | 7 nấc workflow (discover→verify_result), rule web-app-không-binary, giữ đủ nấc dù not_applicable | **done-at-core** | `src/namios_eco/workflow.py`; test `tests/unit/eco/test_workflow.py` |
| ECO-002 | Chứng nhận đúng phạm vi (tuple: tên/nhà cung cấp/URL/ngày kiểm/OS/mode...) | **done-at-core** (trường trong `ServiceEntry`) + **data** (số liệu thật theo cổng/tỉnh cần khảo sát riêng, không suy rộng) | `src/namios_eco/models.py`; `src/namios_eco/validator.py::validate_official_url` |
| ECO-003 | 8 trạng thái công bố + GATE (downloadable_only/launches_only never usable; workflow_verified cần evidence) | **done-at-core** | `src/namios_eco/status.py` (`derive_published_status`, `is_usable`); test `tests/unit/eco/test_status_gate.py` |
| ECO-004 | Tách `tested_by_namios` / `officially_supported_by_vendor` — 2 trường độc lập | **done-at-core** | `src/namios_eco/models.py` (`ServiceEntry.tested_by_namios`/`officially_supported_by_vendor`); hiển thị UI 2 trường riêng = **cli** (chưa làm) |
| ECO-005 | Ưu tiên cơ hội chuyển đổi theo công thức (số đơn vị × tần suất × bắt buộc × chi phí thất bại × khả năng hỗ trợ) | **data** | Chưa code — cần dữ liệu khảo sát thật, không tạo điểm số giả |
| ECO-006 | Danh bạ dịch vụ (`service-catalog`): ID ổn định, URL chính thức, không host lại bộ cài | **done-at-core** | `contracts/service-catalog.schema.json`; `src/namios_eco/models.py`; `src/namios_eco/catalog_schema.py` |
| ECO-007 | Tìm theo tên phổ thông, có/không dấu; cấm nhãn "ứng dụng chính thức của NaMiOS" cho bên thứ ba | **done-at-core** | `src/namios_eco/search.py`; `src/namios_eco/validator.py::validate_no_official_claim_text`; test `tests/unit/eco/test_search.py` |
| ECO-008 | Công cụ tự kiểm môi trường (browser/token/plugin/font/printer...) | **cli** (thuộc `namios_doctor`, chưa code trong phiên này) | — |
| ECO-009 | Trung tâm ký số nhiều tầng (token/HSM → middleware → browser/app → cổng → biên nhận) | **data** (mô hình hoá một phần qua nấc `authenticate`/`submit_or_export` + `ServiceEntry.dependencies`; chưa có dataclass chuỗi ký riêng — cần xác nhận vendor/token model thật trước khi dựng) | `src/namios_eco/workflow.py` (nấc chung); backlog mở |
| ECO-010 | Nguyên tắc bridge ký số Linux (chỉ khi có văn bản hợp tác/quyền tích hợp; không giả lập plugin) | **BLOCKED-sandbox** (chính sách đã ghi; KHÔNG dựng bridge thật khi chưa có quyền/token thật) | Ghi nguyên tắc ở đây + `PHU-LUC-02` §4.2 |
| ECO-011 | Ký từ xa qua kênh chính thức (cần vendor xác nhận hỗ trợ + sandbox) | **data** | Chưa có — chờ chủ dự án xác nhận vendor/sandbox |
| ECO-012 | Dependency graph desktop app (installer→runtime→COM/ActiveX→DB→token→in) | **data**/ngoài phạm vi `namios_eco` phiên này (gần `namios_planner`/`namios_dotnet`) | `ServiceEntry.dependencies` chỉ ghi danh sách phẳng, chưa phải graph đầy đủ |
| ECO-013 | Round-trip định dạng hồ sơ (XML/XLSX/DOCX/PDF/CSV) theo ngành | **data** (cần fixture thật theo ngành — thuế/kế toán/BHXH) | Chưa code trong `namios_eco` |
| ECO-014 | Ưu tiên API chính thức; cấm scraping/tự nộp hồ sơ lách luật | **data**/chính sách (ghi nguyên tắc, không code riêng) | `PHU-LUC-02` §4.3 |
| ECO-015 | `WindowsMode` (native_linux/web_linux/wine/remote_windows/windows_vm) + tỉ lệ không-phụ-thuộc-Windows | **done-at-core** | `src/namios_eco/status.py` (`WindowsMode`, `is_windows_free`); `src/namios_eco/coverage.py` (`windows_free_ratio`) |
| ECO-016 | Không tạo giao dịch thật trên hệ thống nhà nước khi chưa được phép/không sandbox → `blocked_external_dependency` | **done-at-core** (cơ chế `StepOutcome.BLOCKED` + `PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY`) + **BLOCKED-sandbox** (thực thi thật — không có sandbox/host ở đây) | `src/namios_eco/status.py::derive_published_status` |
| ECO-017 | 3 mức độc lập: (a) kỹ thuật, (b) dữ liệu/nghiệp vụ, (c) đầu-cuối+biên nhận | **done-at-core một phần**: (a) = `StepOutcome` per-nấc; (b)/(c) cần người nghiệp vụ/QA xác nhận — dùng chung `qa_reviewer` của `namios_evidence` (WP9), chưa có trường ECO riêng | `src/namios_eco/workflow.py`; liên kết `namios_core.evidence_types` |
| ECO-018 | Thử lỗi có thực (mất mạng giữa upload, token rút giữa ký, phiên hết hạn...) | **BLOCKED-sandbox** | Chưa code — cần môi trường thật |
| ECO-019 | Danh sách vendor cần liên hệ (Linux/PKCS#11/API/sandbox) | **data** | Chưa có dữ liệu |
| ECO-020 | Chứng cứ cung cấp cho vendor (OS/browser build, log khử bí mật...) | **data** | Chưa làm — hành động ngoài cần chủ dự án duyệt trước |
| ECO-021 | Nhãn "Supported on NaMiOS" (tiêu chí công khai + thời hạn) | **data** | Chưa làm — cần tiêu chí công khai + quyền logo/tên vendor |
| ECO-022 | Dashboard coverage theo workflow khảo sát, tách web/wine/vm/remote, "listed != working" | **done-at-core** (hàm tính) + **cli** (hiển thị dashboard thật chưa làm) | `src/namios_eco/coverage.py` (`compute_coverage`, `listed_vs_working`); test `tests/unit/eco/test_coverage.py` |
| ECO-023 | Quy tắc dừng rollout khi sai dữ liệu/ký sai/mất file/mất phục hồi DB | **data**/quy trình vận hành (nguyên tắc ghi ở `PHU-LUC-02` §7; primitives `PublishedStatus.REVOKED`/`BLOCKED_EXTERNAL_DEPENDENCY` đã có, runbook đầy đủ chưa viết) | `src/namios_eco/validator.py::ALLOWED_STATUS_TRANSITIONS` (revoke luôn khả dụng từ mọi trạng thái đã công bố) |
| ECO-024 | Bảng ứng dụng/cổng đã kiểm theo ngày cho mỗi release công khai | **cli** (render báo cáo từ `coverage.py` + `ServiceEntry.last_updated`, chưa làm trình render) | — |

## Ghi chú thiết kế quan trọng

- `ServiceEntry` (ECO-006) **chủ đích không có trường thực thi/lệnh** nào
  (không `command`/`argv`/`script`) — `contracts/service-catalog.schema.json`
  dùng `additionalProperties: false`; `validator.py::validate_no_executable_keys`
  thêm một lớp phòng vệ quét đệ quy trên JSON thô, độc lập với schema.
- GATE tuyệt đối (ECO-003): `namios_eco.status.NEVER_USABLE_STATUSES` =
  `{downloadable_only, launches_only}` — `is_usable()` luôn trả `False` cho
  hai trạng thái này, không có cấu hình/ngoại lệ nào bật lại.
- `workflow_verified` chỉ được `derive_published_status` trả về khi
  `submit_or_export` **và** `verify_result` đều `pass` **và** có
  `evidence_ref` thật (không rỗng/không chỉ khoảng trắng) — khớp đúng câu
  "workflow_verified PHẢI có bằng chứng nộp/nhận" trong lệnh giao việc.
- Bảy nấc (ECO-001) là một bất biến KẾT CẤU: không có cách tạo
  `WorkflowResult`/`tuple[WorkflowStep, ...]` hợp lệ (qua
  `validate_workflow_structure`) mà thiếu bất kỳ nấc nào trong 7 nấc chuẩn —
  đây là cơ chế duy nhất bảo đảm "không xoá nấc khỏi mô hình dù
  not_applicable".
- `search.py` tự viết lại thuật toán fold tiếng Việt (không import
  `namios_catalog._fold` — module đó là PRIVATE của WP4, quy ước M1-INTERFACES
  §0 cấm import chéo vào implementation private của module khác).
- Mọi mã lỗi dùng lại `namios_core.errors.ErrorCode` khi khớp ngữ nghĩa sẵn có
  (`E_SOURCE_POLICY`, `E_STATE_CONFLICT`, `E_EVIDENCE_MISSING`,
  `E_INPUT_SCHEMA`, `E_INPUT_UNKNOWN_KEY`, `E_SEMANTIC_RECIPE`); chỉ thêm mã
  riêng (`src/namios_eco/_errors.py::EcoErrorCode`) cho vi phạm đặc thù ECO
  không có mã tương đương — **không sửa `namios_core`** (ngoài quyền sở hữu
  của vai trò ECO CORE).

## Lệnh chạy test

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/node/.openclaw/workspace/code_projects/namios/src \
  /home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python -m pytest \
  /home/node/.openclaw/workspace/code_projects/namios/tests/unit/eco -p no:cacheprovider -q
```

Kết quả phiên này: 93 test unit namios_eco pass; toàn bộ `tests/` repo
656 passed, 1 skipped (baseline trước phiên này: 563 passed, 1 skipped —
không có test nào bị phá).
