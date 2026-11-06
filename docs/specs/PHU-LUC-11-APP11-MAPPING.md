# Phụ lục 11 (APP11-001–036) — Ma trận: yêu cầu → module hiện có → thay đổi → test

> Bắt buộc theo quy ước fleet (giống PHU-LUC-07/08): map để **tránh viết hệ trạng
> thái thứ hai**. Nguyên tắc: TÁI DÙNG `namios_e08` (`Provenance`/`provenance_ok`
> cho nguồn gói native, `run_install_transaction` cho giao dịch cập nhật),
> `namios_sys` (`SourceTrust`/`authorize` — data authority), `namios_odc`
> (`LifecycleRing` lab/pilot/stable, `CertState`/`advance`/`can_publish`/`publish`
> cho state machine chứng nhận); chỉ thêm hợp đồng Phụ lục 11 còn thiếu vào package
> mới `namios_essentials`. KHÔNG dựng Launcher/App Center UI thật ở pha này (cần
> desktop + browser + PKI + máy pilot thật — §7 BLOCKED).

Module mới: `src/namios_essentials/` — `_types.py`, `_errors.py`, `_i18n.py`,
`manifest.py`, `labels.py`, `anti_impersonation.py`, `update_center.py`,
`update_txn.py`, `rings.py`, `smartai_classify.py`, `cert_workflow.py`,
`release_gate.py`. Test: `tests/unit/essentials/test_essentials_*.py` (8 file,
90 test case, bám đúng E11-01..08 §5 + APP11-002/013/017/021/026/028/033/034/036).

## I0 — Contract + logic thuần (buildable NGAY; đợt này làm phần code)

| APP11 | Yêu cầu | Trạng thái | Module : line | Test |
| --- | --- | --- | --- | --- |
| APP11-001 | Màn hình "Ứng dụng của tôi" (nhóm + nhãn phụ) | **DONE-code** (data model + nhãn) / BLOCKED (Launcher UI thật, nghiệm thu 8/10 người) | `_types.py:94` (`EssentialsManifest.category`), `labels.py:34` (`delivery_label`) | `test_essentials_labels.py` |
| APP11-002 | Manifest có nguồn | **DONE-code** / BLOCKED (ký PKI toàn bộ manifest JSON — chỉ có `package_source.signature_ok` tái dùng `namios_e08.Provenance`, chưa có cơ chế ký cả file) | `_types.py:94` (`EssentialsManifest`), `manifest.py:45` (`validate_manifest`), `manifest.py:70` (`is_shippable`) | `test_essentials_manifest.py` |
| APP11-003 | Link chính thức (allowlist + chặn mạo danh trước login) | **DONE-code** / BLOCKED (crawl redirect chain thật — chỉ kiểm host tĩnh) | `anti_impersonation.py:75` (`check_official_url`), `anti_impersonation.py:113` (`may_render_login_form`) | `test_essentials_anti_impersonation.py` (**E11-06**) |
| APP11-004 | Cửa sổ web app khi khả dụng | BLOCKED (cần browser PWA install API thật) — data placeholder `required_permissions`/`offline` | `_types.py:94` | — |
| APP11-005 | Không tự đăng nhập | **DONE-code** (cấu trúc: không có field credential) + TÁI DÙNG `namios_sys.authorize` cho lệnh-trong-web | `_types.py:94`, `smartai_classify.py:91` (`webpage_instruction_authorized`) | `test_essentials_manifest.py::test_manifest_has_no_credential_field`, `test_essentials_smartai.py::test_webpage_content_never_authorizes_tool_action` |
| APP11-006 | Quyền site dễ hiểu (camera/mic/vị trí/...) | BLOCKED (cần browser permission API thật) — data placeholder `required_permissions` | `_types.py:94` | — |
| APP11-007 | Bộ offline thiết yếu | **DONE-code** (logic: web cần mạng trừ khi khai thật) / BLOCKED (test máy thật rút cáp mạng) | `labels.py:55` (`needs_connection`) | `test_essentials_labels.py` (**E11-01**) |
| APP11-008 | Bản đồ offline tùy chọn | **N/A** đợt này (chưa có app riêng, ngoài 7 hạng mục được giao) | — | — |
| APP11-009 | Office tách vòng đời | **DONE-code** — TÁI DÙNG `namios_odc.lifecycle` (`office_failure_blocks_os`, `can_rollback`, `Component.OFFICE`) qua giao dịch cập nhật | `update_txn.py:31` (`run_essentials_update_transaction`, `channel=OFFICE`) | `test_essentials_update_txn_rings.py` (**E11-05**) |
| APP11-010 | Bộ gõ luôn sẵn sàng (Telex/VNI, hotkey, 200 câu test) | **N/A/BLOCKED** đợt này — chưa có `namios_ime` trong repo, ngoài phạm vi 7 hạng mục được giao; chỉ có `update_channel=ime`/`category` làm chỗ gắn | `_types.py:135` (`UpdateChannel.IME`) | — |
| APP11-011 | Bảo vệ máy có thật (chữ ký độc lập khỏi kết quả quét) | **DONE-code** | `update_center.py:89` (`scanner_badge`) | `test_essentials_update_center.py` (**E11-04**) |
| APP11-012 | Gói profile (Cá nhân/Giáo viên/Văn phòng/Kế toán) | **N/A** đợt này (ngoài 7 hạng mục được giao) | — | — |
| APP11-013 | Bảng trạng thái cập nhật 8 kênh | **DONE-code** | `_types.py:135` (`UpdateChannel`), `update_center.py:44` (`build_update_status`) | `test_essentials_update_center.py` |
| APP11-014 | Nguồn và chữ ký (native + Wine) | **DONE-code** — TÁI DÙNG `namios_e08.provenance_ok` | `manifest.py:29` (`_has_valid_source`), `update_txn.py:31` (stage `sign_ok`) | `test_essentials_manifest.py`, `test_essentials_update_txn_rings.py` |
| APP11-015 | Kiểm tự động, cài có lịch (không reboot giữa tiết học) | **DONE-code** (quyết định lịch) / BLOCKED (cron/scheduler OS thật kiểm định kỳ) | `update_center.py:153` (`schedule_update`) | `test_essentials_update_center.py` (**E11-08**) |
| APP11-016 | Kiểm phụ thuộc giao dịch (stage→sign/space/pin→snapshot→apply→health→commit/rollback) | **DONE-code** — TÁI DÙNG `namios_e08.run_install_transaction` | `update_txn.py:31` (`run_essentials_update_transaction`) | `test_essentials_update_txn_rings.py` (**E11-05**) |
| APP11-017 | Update rings lab/pilot/stable, giữ bản cũ CÓ HẠN | **DONE-code** — TÁI DÙNG `namios_odc.LifecycleRing` | `rings.py:24` (`evaluate_ring_promotion`), `rings.py:64` (`is_retention_expired`) | `test_essentials_update_txn_rings.py` |
| APP11-018 | Cập nhật browser theo SLA + smoke test 6 dịch vụ | **DONE-code** (nguyên liệu smoke-test per-service) / BLOCKED (quy trình người theo dõi security advisory thật) | `update_center.py:127` (`evaluate_web_shortcut`), `release_gate.py:17` (`REQUIRED_WEB_SERVICES`) | `test_essentials_release_gate.py` |
| APP11-019 | Dịch vụ web tự thay đổi (không đổ lỗi "NaMiOS chưa cập nhật") | **DONE-code** | `update_center.py:127` (`evaluate_web_shortcut`) | `test_essentials_update_center.py` (**E11-03**) |
| APP11-020 | Chữ ký malware độc lập (ngày cập nhật hiển thị dù offline lâu) | **DONE-code** | `update_center.py:89` (`scanner_badge`) | `test_essentials_update_center.py` (**E11-04**) |
| APP11-021 | Wine app có kiểm version (hash đổi → needs_retest) | **DONE-code** — TÁI DÙNG `namios_odc.CertState.NEEDS_RETEST` | `cert_workflow.py:98` (`on_binary_hash_change`) | `test_essentials_cert_workflow.py` (**E11-07**) |
| APP11-022 | Changelog tiếng Việt | **N/A** đợt này (nội dung/process, ngoài 7 hạng mục được giao) | — | — |
| APP11-023 | Băng thông và máy yếu | **N/A** đợt này (ngoài phạm vi được giao) | — | — |
| APP11-024 | Ngừng hỗ trợ minh bạch | **N/A/BLOCKED** đợt này — chưa model ngày hết hỗ trợ, ngoài 7 hạng mục được giao | — | — |
| APP11-025 | Khởi động kiểm tra thông minh | BLOCKED (cần browser/network runtime check thật) — data placeholder `required_permissions`/`offline` hỗ trợ bước này về sau | `_types.py:94` | — |
| APP11-026 | SmartAI phân biệt loại ứng dụng/cập nhật | **DONE-code** — TÁI DÙNG `namios_sys.authorize` | `smartai_classify.py:41` (`classify_update_question`), `smartai_classify.py:91` (`webpage_instruction_authorized`) | `test_essentials_smartai.py` |
| APP11-027 | Trình xử lý lỗi ba mức | **DONE-code** (mã lỗi machine-readable) / BLOCKED (UI 3 mức thật: người mới/hỗ trợ/developer) | `_errors.py:10` (`EssentialsErrorCode`) | (dùng xuyên suốt các test khác qua `error_code`) |
| APP11-028 | Chứng nhận workflow per-chức-năng | **DONE-code** — TÁI DÙNG `namios_odc.advance`/`can_publish`/`publish` | `cert_workflow.py:41-98`, `_types.py:290` (`AppFunction`), `_types.py:308` (`AppCertProfile`) | `test_essentials_cert_workflow.py` |
| APP11-029 | Hỗ trợ cài thêm (App Center tìm theo tên/nhu cầu) | **N/A** đợt này (cần App Center UI thật, ngoài 7 hạng mục được giao) | — | — |
| APP11-030 | Tìm không dấu + thuật ngữ quen | **N/A** đợt này (ngoài phạm vi được giao) | — | — |
| APP11-031 | Quyền riêng tư web (profile tách theo user OS) | BLOCKED (cần browser profile-per-OS-user thật) | — | — |
| APP11-032 | Khôi phục khi cập nhật hỏng (web không rollback được) | **DONE-code** | `update_center.py:195` (`recovery_guidance`) | `test_essentials_update_center.py` |
| APP11-033 | Chống mạo danh thương hiệu (trademark status) | **DONE-code** | `anti_impersonation.py:121` (`effective_trademark_status`), `_types.py:83` (`TrademarkStatus`) | `test_essentials_anti_impersonation.py` |
| APP11-034 | Phân phối có giấy phép (bundle chỉ khi license cho phép) | **DONE-code** (invariant) / BLOCKED (SBOM thật khớp từng app trong ISO) | `manifest.py:38` (`may_bundle_binary`), `manifest.py:45` (`validate_manifest`) | `test_essentials_manifest.py` |
| APP11-035 | Đo sử dụng không xâm phạm | **N/A** đợt này (ngoài phạm vi được giao) | — | — |
| APP11-036 | Cổng phát hành | **DONE-code** | `release_gate.py:38` (`evaluate_release_gate`) | `test_essentials_release_gate.py` |

## §5 — Test bắt buộc E11-01..08

| Test | Ca | File test | Hàm tiêu biểu |
| --- | --- | --- | --- |
| E11-01 | Máy mới không mạng, mở Office/gõ Việt/PDF | `test_essentials_labels.py` | `needs_connection`, `delivery_label` |
| E11-02 | Nhấn 6 dịch vụ web — HTTPS chính thức, không đăng nhập hộ | `test_essentials_anti_impersonation.py::test_e11_02_six_official_services_are_https_and_allowlisted` | `check_official_url`, `may_render_login_form` |
| E11-03 | Browser cập nhật, Zalo QR đổi | `test_essentials_update_center.py::test_e11_03_broken_web_service_is_service_incident_not_namios_outdated` | `evaluate_web_shortcut` |
| E11-04 | Signature scanner quá hạn | `test_essentials_update_center.py::test_e11_04_expired_signature_warns_even_if_last_scan_clean` | `scanner_badge` |
| E11-05 | Gói Office lỗi sau nâng cấp → rollback | `test_essentials_update_txn_rings.py::test_e11_05_health_check_fail_rolls_back_office` | `run_essentials_update_transaction` |
| E11-06 | Trang giả `whatsapp-login.example` | `test_essentials_anti_impersonation.py::test_e11_06_lookalike_whatsapp_domain_is_blocked` | `check_official_url` |
| E11-07 | App Wine vendor tự đổi phiên bản | `test_essentials_cert_workflow.py::test_e11_07_hash_change_demotes_published_functions_to_needs_retest` | `on_binary_hash_change` |
| E11-08 | Đang dạy online, có update OS | `test_essentials_update_center.py::test_e11_08_busy_context_never_installs_now_even_if_critical` | `schedule_update` |

## I1–I4 (cần Launcher/App Center UI thật, browser/PWA thật, PKI ký manifest thật, máy pilot thật — BLOCKED đúng §7)

| Pha | APP11 | Lý do BLOCKED |
| --- | --- | --- |
| I1 UI thật | 001(UI)/004/006/025/031 | Launcher/App Center/browser PWA/permission API thật trên desktop NaMiOS |
| I2 PKI + distro thật | 002(ký)/014(key rotation thật)/018(advisory process)/034(SBOM thật) | Hạ tầng ký manifest + kho gói distro/vendor thật + đội vận hành SLA |
| I3 nội dung/đo lường | 010/022/023/024/027(UI)/029/030/035 | IME thật, changelog process, telemetry opt-in, App Center search, ngoài 7 hạng mục được giao đợt này |
| I4 pilot + release | 008/012 | Dữ liệu bản đồ offline thật, profile trường/DN thật, pilot thật |

## Chốt phạm vi đợt này

Làm **7 hạng mục bắt buộc** theo yêu cầu giao việc + 3 hạng mục P0 "rẻ nhưng có
giá trị" ăn theo (APP11-015 lịch cài — cần cho E11-08; APP11-032 khôi phục — mở
rộng tự nhiên của update_txn; APP11-036 cổng phát hành — tổng hợp mọi invariant
đã có, không thêm luật mới):

1. `EssentialsManifest` + validator (APP11-002) — `_types.py`, `manifest.py`.
2. Nhãn phân phối đúng (APP11-001/013) — `labels.py`.
3. Update Center lifecycle 8 kênh (APP11-013/019/020) — `update_center.py`.
4. Cập nhật giao dịch (APP11-016) + update rings (APP11-017) — `update_txn.py`, `rings.py`.
5. Chống mạo danh (APP11-003/033) — `anti_impersonation.py`.
6. SmartAI phân loại cập nhật (APP11-026) — `smartai_classify.py`.
7. Chứng nhận workflow per-chức-năng (APP11-021/028) — `cert_workflow.py`.

Phần cần Launcher/App Center UI thật, browser/PWA thật, PKI ký manifest thật,
IME thật, đội vận hành advisory/SBOM thật, máy pilot thật (I1–I4 ở trên) =
**BLOCKED** chờ build-host/thiết bị/pilot thật theo CLAUDE.md.

## Ruff per-file-ignore

**KHÔNG cần thêm** entry `[tool.ruff.lint.per-file-ignores]` nào cho
`src/namios_essentials/` hoặc `tests/unit/essentials/` — `ruff check` sạch với
đúng bộ rule hiện có của repo (`E,F,I,UP,B,S`, ignore `S101,UP042` toàn cục), không
cần miễn trừ riêng (không có enum/hằng chứa từ vựng "password/token/secret" kiểu
false-positive như `namios_e08`/`namios_compat`/`namios_pra`/`namios_smartai`).
