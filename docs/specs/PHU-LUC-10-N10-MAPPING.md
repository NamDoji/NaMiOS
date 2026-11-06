# Phụ lục 10 (N10-001–060) — Ma trận: yêu cầu → module hiện có → thay đổi → test

> Bắt buộc theo §4/§5 phụ lục 10: map để **tránh viết hệ trạng thái thứ hai**. Nguyên
> tắc: TÁI DÙNG `namios_odc` (route_matrix, device_cert), `namios_pra` (device_hub,
> office_route, dotnet_classify, progress, doctor), `namios_e08` (install_txn,
> depgraph, actuator), `namios_sys` (data_authority); chỉ thêm hợp đồng M0 còn thiếu
> vào package mới `namios_mig`. Đây là lõi **honest-core LÀM-ĐƯỢC-TẠI-CHỖ** (dữ liệu/
> logic thuần) — KHÔNG có thiết bị/pilot/vendor thật, KHÔNG tự xưng đã "chuyển đổi"
> được máy nào. Cột **Trạng thái**: `DONE-code` = logic + test xanh trong đợt này;
> `BLOCKED` = cần thiết bị/khảo sát/pilot/ADR/vendor thật (đúng §7 "điểm dừng");
> `N/A` = ngoài phạm vi `namios_mig` (thuộc phụ lục khác hoặc quy trình con người).

## 1.1 Nền tảng và ranh giới hệ thống

| N10 | Yêu cầu | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| N10-001 | ADR nền tảng (Linux base) | `N/A` | Quyết định ADR + pilot phần cứng thật — ngoài phạm vi module dữ liệu. |
| N10-002 | Desktop stack | `N/A` | Idem — không liên quan tới lõi chuyển đổi. |
| N10-003 | Ranh giới dịch vụ (IPC) | `N/A` | Thuộc kiến trúc hệ thống tổng (ngoài `namios_mig`). |
| N10-004 | Gói sản phẩm có thể tái tạo | `N/A` | Build/SBOM/CI — ngoài phạm vi. |
| N10-005 | Chế độ offline có chủ đích | `N/A` | `namios_mig` vốn thuần dữ liệu/offline-by-design nhưng không tự công bố UX offline. |
| N10-006 | Hồ sơ thiết bị có trọng số | `BLOCKED` (contract `DONE-code`) | `DeviceManifest`/`PeripheralKind` (`src/namios_mig/_types.py:114,135`) là hợp đồng để ghi hồ sơ; tỷ lệ phủ THẬT theo máy khảo sát = cần survey thật. |

## 1.2 Công cụ chuyển đổi Windows → NaMiOS

| N10 | Yêu cầu | Trạng thái | File:line (phần done) |
| --- | --- | --- | --- |
| N10-007 | NaMi Migration Assessor | `DONE-code` | `src/namios_mig/assessor.py:175` (`assess_machine`), `:92` (`_scan_secret_paths`), `:43` (`SECRET_FIELD_MARKERS`), `:160` (`AssessmentResult`); opt-in gate ở `:114` (`_build_app`). Test: `tests/unit/mig/test_mig_assessor.py`. |
| N10-008 | Bản đồ công việc trước phần mềm | `DONE-code` (một phần) | `AppManifest.essential` (`_types.py:91-111`) + `WorkflowTest.workflow_id` (`_types.py:186`) tách app khỏi công-việc/workflow — hai app cùng tên nhưng `workflow_id` khác không gộp badge. Phỏng vấn thật theo nhiệm vụ = `BLOCKED`. |
| N10-009 | Điểm sẵn sàng chuyển đổi | `DONE-code` | `src/namios_mig/readiness.py:87` (`compute_machine_readiness`), `:35` (`ReadinessLevel`), `:53` (`AppReadinessInput`). Test bất biến "essential blocked → cả máy blocked": `tests/unit/mig/test_mig_readiness.py::test_one_blocked_essential_blocks_whole_machine`. |
| N10-010 | Sao lưu trước di chuyển | `BLOCKED` (khung giao dịch `DONE-code`) | `assessor.migrate_app_data` (`:232`) tái dùng `namios_e08.install_txn` cho khung check-nguồn→snapshot→apply→đối-chiếu→commit/rollback; backup/restore THẬT trên máy = `BLOCKED`. |
| N10-011 | Di chuyển tệp và cấu trúc | `BLOCKED` | Chủ ý KHÔNG thu thập tên/đường dẫn file thật (`AppManifest.file_types` chỉ lưu ĐUÔI, không lưu path — `_types.py:91-111`) để tránh vấn đề "che tên file riêng tư"; xử lý Unicode/ACL/UNC thật cần máy thật. |
| N10-012 | Chuyển dữ liệu ứng dụng | `DONE-code` | `src/namios_mig/assessor.py:232` (`migrate_app_data`, tái dùng `namios_e08.install_txn.run_install_transaction`). Test: `test_mig_assessor.py::test_migrate_app_data_reuses_install_transaction_state_machine`. |
| N10-013 | Danh tính và đăng nhập | `N/A` | Thuộc tầng Identity hệ thống, ngoài `namios_mig`. |
| N10-014 | Trình nhập browser | `DONE-code` (một phần) | `assessor.assessment_instruction_authorized` (`:219`, tái dùng `namios_sys.data_authority`) đảm bảo nội dung thu thập (tên bookmark…) không tự thành hành động; `SECRET_FIELD_MARKERS` loại `session`/`cookie`. Preview UI bookmark/extension thật = `BLOCKED`. |
| N10-015 | Giai đoạn chạy song song | `N/A` | Quy trình vận hành song song 2–4 tuần — ngoài phạm vi dữ liệu/logic. |
| N10-016 | Kế hoạch rút lui | `DONE-code` (một phần) | `InstallResult.rolled_back` tái dùng qua `migrate_app_data` cho đường lùi kỹ thuật; kế hoạch rút lui đầy đủ (tài liệu + người phụ trách) = `BLOCKED`. |

## 1.3 Kiến trúc tương thích Windows

| N10 | Yêu cầu | Trạng thái | File:line |
| --- | --- | --- | --- |
| N10-017 | Compatibility Broker | `DONE-code` | `src/namios_mig/compat_broker.py:68` (`resolve_task_route`), `:48` (`TaskRouteResult`). Bất biến "mở GUI OK nhưng ký FAIL → route khác": `tests/unit/mig/test_mig_compat_broker.py::test_gui_open_ok_but_sign_task_blocked_gets_different_route`. |
| N10-018 | Bộ phân tích PE an toàn | `DONE-code` | `src/namios_mig/pe_analyzer.py:107` (`classify_pe`), `:65` (`PeMetadataInput`), `:97` (`_looks_like_kernel_driver`). 20 fixture đã gán nhãn: `tests/unit/mig/test_mig_pe_analyzer.py::FIXTURES` (+ `test_exactly_twenty_labeled_fixtures`). |
| N10-019 | Wine capsule versioned | `DONE-code` (gate runner-pin) / `BLOCKED` (capsule thật) | `schema.validate_recipe` (`schema.py:82`) chặn `route=WINE` thiếu `runner_id`. Prefix/DLL override/font-profile/snapshot THẬT = `BLOCKED` (cần Wine thật). |
| N10-020 | Nền tảng API và log chuẩn | `N/A` | Đã có ở `namios_pra.doctor`/`Diagnosis` (Phụ lục 06) — `namios_mig` tái dùng (`workflow_verdict.terminal_diagnosis_if_exhausted`) chứ không dựng lại taxonomy lỗi. |
| N10-021 | Windows path & file semantics | `BLOCKED` | Cần máy thật (Unicode NFC/NFD, UNC, case-sensitivity) — chủ ý không giả lập ở M0. |
| N10-022 | Cầu in ấn và thiết bị | `BLOCKED` | Cần máy in/token thật; `readiness.is_device_requirement_met` (`:79`) chỉ là hợp đồng gọi `namios_pra.device_hub.is_supported`, chưa có máy thật để đo. |
| N10-023 | COM, Office add-in và OLE | `DONE-code` (một phần) | `compat_broker.office_task_route`/`office_document_route` (`:186`, `:198`) tái dùng `namios_pra.office_route`/`namios_odc.route_matrix` — macro/add-in không bao giờ ra web. Theo dõi CLSID/version Office thật = `BLOCKED`. |
| N10-024 | Cầu crypto/chữ ký số có ranh giới | `DONE-code` (một phần) | `resolve_task_route`'s invariant PRINTER_TOKEN/COM_SERVICE BLOCKED → không bao giờ Wine (`tests/unit/mig/test_mig_compat_broker.py::test_kernel_token_blocker_never_routes_wine_even_with_windows_available`). PKI/CSP/token THẬT = `BLOCKED`. |
| N10-025 | Ứng dụng .NET theo loại | `DONE-code` | `pe_analyzer.classify_pe` nhánh .NET (`pe_analyzer.py:142-151`) tái dùng `namios_pra.dotnet_classify.classify_dotnet`. 4 lớp fixture (console/winforms/wpf/driver) nằm trong `FIXTURES` của `test_mig_pe_analyzer.py`. |
| N10-026 | Recipe compatibility có thể kiểm toán | `DONE-code` | `schema.py:214` (`recipe_needs_retest`), `:233` (`promote_recipe`, tái dùng `namios_odc.device_cert.advance`), `:242` (`publish_recipe`). Test: `test_mig_contracts.py::test_recipe_needs_retest_on_hash_or_version_change`. |
| N10-027 | Không tự tải hoặc vá binary | `DONE-code` | `compat_broker.py:206` (`proposed_action_is_safe`, tái dùng `namios_e08.actuator.action_is_safe`). Test: `test_mig_compat_broker.py::test_proposed_action_rejects_download_crack`. |
| N10-028 | Windows fallback được quản lý | `DONE-code` (một phần) | `resolve_task_route`'s nhánh `REMOTE_WINDOWS` (`compat_broker.py:68`). Clipboard/USB/pin/print policy thật, phí bảo trì = `BLOCKED`. |
| N10-029 | Hợp tác upstream | `N/A` | Quy trình cộng đồng/con người, không phải code. |

## 1.4 Chương trình ứng dụng và nghiệp vụ Việt Nam

| N10 | Yêu cầu | Trạng thái | File:line |
| --- | --- | --- | --- |
| N10-030 | Catalog theo việc | `BLOCKED` (contract `DONE-code`) | `AppManifest`/`CompatibilityRecipe` có đủ trường owner/version/route/test/blocker/ngày (`_types.py:91,156`); nội dung catalog THẬT (khảo sát VN) = `BLOCKED`. |
| N10-031 | Bộ 12 hành trình Việt Nam | `DONE-code` (động cơ chung) / `BLOCKED` (12 fixture thật) | `WorkflowTest`/`EvidenceRecord` ánh xạ 1-1 mẫu JSON §4 (`_types.py:186,210`) + `workflow_verdict.evaluate_workflow` (`:66`) là động cơ MỌI hành trình dùng chung. 12 fixture thật + sandbox công khai = `BLOCKED`. |
| N10-032 | Hồ sơ thuế và kế toán | `BLOCKED` | Cần luật nghiệp vụ + xác nhận chuyên môn — không tự tính/nộp thuế ở M0. |
| N10-033 | Hóa đơn và chữ ký | `DONE-code` (động cơ) | `EvidenceRecord.print_stage`/`sign_stage` tái dùng `PrintStage`/`SignSubmitStage` (`_types.py:210`) tách đúng "đã tạo ≠ đã ký ≠ đã nộp ≠ có biên nhận"; vendor API thật = `BLOCKED`. |
| N10-034 | Giáo dục | `N/A` | Ngoài phạm vi chuyển đổi Windows. |
| N10-035 | Hành chính công | `BLOCKED` (contract tái dùng được) | `CompatRoute`/`CertState`/`recipe_needs_retest` tái dùng được cho catalog cổng dịch vụ công; khảo sát cổng thật = `BLOCKED`. |
| N10-036 | Người dùng ít rành công nghệ | `N/A` | Khảo sát thực địa con người — không phải code. |
| N10-037 | Mẫu tài liệu Việt Nam | `N/A` | Nội dung mẫu — ngoài phạm vi `namios_mig`. |

## 1.5 Trải nghiệm, SmartAI và niềm tin

| N10 | Yêu cầu | Trạng thái | File:line |
| --- | --- | --- | --- |
| N10-038 | Design language NaMiOS | `N/A` | UI/thiết kế — ngoài phạm vi. |
| N10-039 | Hỗ trợ tiếng Việt chuyên ngành | `DONE-code` (một phần) | `src/namios_mig/_i18n.py` góp catalog VI/EN cho thuật ngữ miền chuyển-đổi (readiness/route/evidence/recipe); glossary có người duyệt đầy đủ = `BLOCKED`. |
| N10-040 | Trải nghiệm từ lỗi đến kết quả | `N/A` | UI panel "Việc cần làm" — ngoài phạm vi (dữ liệu nền đã có qua `Diagnosis`/`MachineReadiness`). |
| N10-041 | SmartAI orchestrator | `N/A` | Thuộc `namios_sys`/`namios_smartai`. |
| N10-042 | Cơ sở tri thức có nguồn | `N/A` | Thuộc `namios_smartai.knowledge_base`. |
| N10-043 | Bằng chứng sau hành động | `DONE-code` | `src/namios_mig/workflow_verdict.py:43` (`evidence_outcome`), `:66` (`evaluate_workflow`), `:114` (`assess_workflow`). Fixture literal "spool OK + giấy trắng = failed": `tests/unit/mig/test_mig_workflow_verdict.py::test_spool_ok_but_blank_page_is_failed`. |
| N10-044 | AI tiếng Việt có đánh giá | `N/A` | Thuộc eval AI — ngoài phạm vi. |
| N10-045 | Chọn local/cloud minh bạch | `N/A` | Thuộc `namios_sys`/SmartAI. |
| N10-046 | Kiến trúc plugin an toàn | `N/A` | Thuộc `namios_smartai` (manifest/quota/chữ ký plugin); `namios_mig` chỉ TÁI DÙNG `action_is_safe` cho một lát cắt hẹp (N10-027). |

## 1.6 Thiết bị, bảo mật và vận hành lâu dài

| N10 | Yêu cầu | Trạng thái | File:line |
| --- | --- | --- | --- |
| N10-047 | Ma trận ngoại vi theo chức năng | `DONE-code` (một phần) | `PeripheralKind`/`DeviceManifest` (`_types.py:114,135`) + `readiness.is_device_requirement_met` (`:79`, tái dùng `namios_pra.device_hub.is_supported`). Ma trận model/firmware/kernel/backend THẬT = `BLOCKED`. |
| N10-048 | Phát hiện thiết bị và sửa có rollback | `N/A` | Thuộc `namios_e08` (Phụ lục 08) — `namios_mig` không dựng lại. |
| N10-049 | Bảo mật nhiều lớp | `N/A` | Ngoài phạm vi module này. |
| N10-050 | Chuỗi cung ứng | `N/A` | Ngoài phạm vi. |
| N10-051 | Cập nhật nguyên tử và cứu hộ | `N/A` | Ngoài phạm vi. |
| N10-052 | Hỗ trợ 5 năm | `N/A` | Chính sách vận hành — không phải code. |
| N10-053 | Quản trị tổ chức | `N/A` | Ngoài phạm vi. |
| N10-054 | Quyền và giấy phép | `N/A` | Ngoài phạm vi. |
| N10-055 | Cộng đồng và nhà cung cấp | `N/A` | Quy trình cộng đồng. |
| N10-056 | Chi phí sống còn | `N/A` | Mô hình chi phí — không phải code. |

## 2. Bộ kiểm thử chấp nhận theo thời điểm

| N10 | Yêu cầu | Trạng thái | File:line |
| --- | --- | --- | --- |
| N10-057 | Release gate theo tác vụ | `BLOCKED` (nguyên liệu `DONE-code`) | `WorkflowTestStatus.FAILED`/`MachineReadiness.BLOCKED` là tín hiệu fail-closed một release gate thật sẽ đọc; quy trình release/CI thật = `BLOCKED`. |
| N10-058 | Ma trận phạm vi hỗ trợ | `DONE-code` (hợp đồng) | `CompatibilityRecipe` + `WorkflowTest` + `EvidenceRecord` + `CertState` (tái dùng `namios_odc`) cùng tạo đúng tuple app/version/hash/route × workflow × evidence × ngày kiểm; badge `needs_retest` đóng vai trò "expired-khi-đổi". Dữ liệu tuple THẬT theo máy/model = `BLOCKED`. |
| N10-059 | Thử nghiệm thực địa | `N/A` | Pilot con người — không phải code. |
| N10-060 | Điểm dừng và đổi hướng | `DONE-code` (một phần) | `workflow_verdict.py:158` (`terminal_diagnosis_if_exhausted`, tái dùng `namios_pra.doctor.next_after_attempts`) — nguyên lý "dừng sau N lần fail". Quyết định tổ chức (thu hẹp nhóm khách hàng, ngày đánh giá lại) = `BLOCKED`. |

## Chốt phạm vi đợt này

Làm **M0 phần code** (6 hạng mục giao việc, mỗi hạng mục có test riêng trong
`tests/unit/mig/`):

1. Hợp đồng dữ liệu + validator (`namios_mig._types` + `namios_mig.schema`) —
   `AppManifest`/`DeviceManifest`/`CompatibilityRecipe`/`WorkflowTest`/`EvidenceRecord`/
   `MigrationInventory`; recipe đổi hash/version tự `needs_retest` (N10-026).
2. Migration Assessor (`namios_mig.assessor`) — chỉ kiểm kê/preview; loại + đánh dấu
   trường nhạy cảm; usage 30-ngày chỉ giữ khi opt-in; nội dung thu thập không thành
   hành động (N10-007/012/014).
3. Readiness score (`namios_mig.readiness`) — 5 mức, essential blocked → cả máy
   blocked (N10-009).
4. Compatibility Broker route (`namios_mig.compat_broker`) — route theo TÁC VỤ từ
   dependency graph; driver/token-chỉ-Windows không bao giờ Wine (N10-017/027).
5. PE analyzer an toàn (`namios_mig.pe_analyzer`) — phân loại metadata struct, driver
   `.sys` không bao giờ thành app user-mode, 20 fixture (N10-018/025).
6. Workflow verdict + evidence (`namios_mig.workflow_verdict`) — "đã xong" chỉ khi có
   evidence hợp lệ, exit-code/spool một mình không đủ (N10-043/060).

TÁI DÙNG xuyên suốt (không dựng hệ trạng thái thứ hai): `namios_odc.route_matrix` +
`namios_odc.device_cert` (`CertState`/`EvidenceKind`/`advance`/`publish`),
`namios_pra.device_hub`/`office_route`/`dotnet_classify`/`progress`/`doctor`,
`namios_e08.install_txn`/`depgraph`/`actuator`, `namios_sys.data_authority`.

Mọi phần cần **thiết bị/khảo sát/pilot/vendor/ADR thật** (30–50 máy thật, ADR nền
tảng, Wine prefix thật, 12 fixture hành trình thật, catalog VN thật, pilot 3 nhóm
người dùng, ma trận thiết bị firmware thật…) = **`BLOCKED`** đúng §7 "điểm dừng và
đổi hướng" — KHÔNG được đánh dấu hoàn thành bằng văn bản.
