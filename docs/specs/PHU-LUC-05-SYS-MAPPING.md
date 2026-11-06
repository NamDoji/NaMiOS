# Phụ lục 05 (SYS-001–042) — Ma trận: yêu cầu → module hiện có → thay đổi → test

> Bắt buộc theo §10 lệnh giao việc: lập ma trận để **không tạo hệ thống song song**.
> Nguyên tắc: tái dùng gate ECO/COMP/SAI, chỉ thêm **hợp đồng + action broker** mới
> cho tầng "máy làm việc hằng ngày". Cột "Buildable tại chỗ" phân biệt phần code được
> ngay (pure-Python, không cần hạ tầng) với phần **BLOCKED** (ISO/máy thật/thiết bị/
> pilot/vendor — đúng §9 H01–H10).

## K0 — Thiết kế hợp đồng (buildable NGAY, làm trong đợt này)

| SYS | Yêu cầu | Module | Thay đổi | Test | Buildable |
| --- | --- | --- | --- | --- | --- |
| SYS-037 | Hợp đồng dùng chung `device_profile`/`app_route`/`workflow_run` + validator chặn route thiếu source/version & bước completed thiếu evidence | **mới `namios_sys`** (`_types`, `schema`) | Dataclass frozen + validator; nạp từ dict KHÔNG tin nhãn state | `tests/unit/sys/test_schema.py` | ✅ |
| SYS-001 | Action broker chung (`open_file/open_app/print/scan/share/open_url/connect_share`) cho desktop+CLI+SmartAI; trả ID/status/route/quyền/lỗi cấu trúc | **mới `namios_sys.action_broker`** | Broker + `ActionHandler` Protocol tiêm vào; KHÔNG handler thật → `BLOCKED` trung thực (cần desktop/thiết bị) | `tests/unit/sys/test_action_broker.py` | ✅ (thực thi OS thật = BLOCKED) |
| SYS-013 | Chứng nhận 3 trục (chạy kỹ thuật / đúng nghiệp vụ / hoàn tất ngoài); GUI mở / tải / cài KHÔNG đủ | **tái dùng** `namios_eco.status.derive_published_status` + `is_usable`; thêm `namios_sys.certification` layering | Không dựng lại gate — chồng business+external lên gate ECO | `tests/unit/sys/test_certification.py` | ✅ |
| SYS-038 | Danh mục khả năng tách `available_to_download`/`launches`/`workflow_verified` theo app/version/workflow/model/thiết bị/ngày | **tái dùng** `PublishedStatus`; thêm `namios_sys.capability_catalog` | Dùng `NEVER_USABLE_STATUSES`/`USABLE_STATUSES`; chặn overclaim khi add | `tests/unit/sys/test_capability_catalog.py` | ✅ |
| SYS-008 | Compatibility Profile khớp theo publisher/version/arch/hash; đổi hash → không dùng recipe cũ | **tái dùng** `namios_compat.resolver` (COMP-025) + `namios_dotnet` classifier | `namios_sys` chỉ tham chiếu, KHÔNG fork resolver | (đã có test compat) + `test_schema` app_route↔compat | ✅ (adapter mỏng) |
| SYS-002 | Mở tệp/app mặc định theo MIME; `.exe` không tự chạy | `namios_sys.action_broker` (OPEN_FILE route) + handler | Logic chọn route/mode + cờ "exe-không-tự-chạy"; gắn MIME thật = desktop | `test_action_broker` (open_file routing) | ✅ phần logic; gắn desktop = BLOCKED |

## K1 — Máy làm việc hằng ngày (logic buildable / ISO+HW = BLOCKED)

| SYS | Yêu cầu | Trạng thái | Lý do |
| --- | --- | --- | --- |
| SYS-010 | Ranh giới đường dẫn/profile Wine, không ra ngoài quyền | logic buildable (**tái dùng `namios_security.open_within`/`safe_path`**) | Ánh xạ `C:\Users` + mount thật = BLOCKED (cần Wine/host) |
| SYS-003–007, 009, 015, 019, 022–025 | Menu/tìm kiếm, bộ gõ, phân loại cài, profile phần cứng, sleep/resume, cài không phá dữ liệu, update/rollback, backup/restore | **BLOCKED** | Cần ISO trên máy lab + phần cứng thật (H01/H03/H04/H08) |

## K2 — Tương thích nghiệp vụ · K3 — SmartAI chủ động · K4 — Rollout

| SYS | Trạng thái | Lý do / tái dùng |
| --- | --- | --- |
| SYS-011/012/014/016–018/020/021 (K2) | **BLOCKED** | Pilot persona + app/thiết bị/portal/domain thật (H02/H05/H06/H07) |
| SYS-029/030/036 (K3 logic) | một phần buildable | **tái dùng `namios_smartai`**: context-scope (SAI-026/024), goal→honest-status (SAI-003/022), chống lệnh-từ-tài-liệu = `injection` (SAI-019). `namios_sys` chỉ nối qua action broker + evidence |
| SYS-031/032/033/035 (K3) | **BLOCKED/seam** | Wine thật/model thật/đo phần cứng — seam `TrialExecutor`/`ModelProvider` đã có |
| SYS-026/027/028/034/039–042 (K4) | **BLOCKED** | Dashboard readiness + pilot thật + người nghiệp vụ duyệt |

## Chốt phạm vi đợt này

Làm **K0 trọn vẹn bằng code+test** (SYS-001/002-logic/008-adapter/013/037/038) trong package mới
`namios_sys`, **tái dùng** ECO/COMP/SAI (không fork gate), + CLI `namios sys` để desktop/CLI/SmartAI
đọc CÙNG hồ sơ (SYS-037 nghiệm thu). K1–K4 phần cần ISO/máy/thiết bị/pilot/vendor = **BLOCKED**
trung thực (H01–H10 chưa chạy — chưa có chứng nhận NaMiOS trên app/thiết bị thật, đúng §11 giới hạn).
