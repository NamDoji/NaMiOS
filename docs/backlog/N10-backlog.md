# N10 Backlog — Phụ lục 10: Kiến trúc chuyển đổi từ Windows và chương trình OS cho người Việt

**Nguồn:** `docs/spec-package/NaMiOS_Phu_luc_10_Kien_truc_Chuyen_doi_Windows_Viet_Nam_Tong_hop.md` (06/11/2026), mã `N10-001`–`N10-060`.
**Trạng thái tài liệu này:** bảng theo dõi backlog, không phải báo cáo tiến độ đã kiểm chứng. Không mục nào được đánh dấu `done`/hoàn thành trong file này.

## Quy ước trạng thái

- `open` — mặc định cho mọi mục P0/P1 chưa có bằng chứng code hoặc đang không có hoạt động nào.
- `in-progress-code` — có scaffolding/code/schema đang được dựng tại host hiện tại (Python thuần, không cần thiết bị/pilot/Windows-có-phép), **chưa chạy trên dữ liệu/phần cứng thật, chưa nghiệm thu**.
- `blocked-infra` — nghiệm thu của chính mục đó đòi hỏi phần cứng thật, pilot người dùng thật, Windows có bản quyền, cổng/dịch vụ bên thứ ba thật, hoặc dữ liệu khảo sát thật mà host hiện tại không có; không thể tự nâng trạng thái bằng code thuần.

**Ánh xạ `in-progress-code` cho nhóm công cụ chuyển đổi (`namios_mig`, đang dựng khung dữ liệu + CLI prototype, xem Phụ lục 10 §4 "Giao việc cho Claude Code" mục 2):**

| Khái niệm trong giao việc | Mã N10 tương ứng |
| --- | --- |
| Hợp đồng dữ liệu (data contract: app/device-manifest, compatibility-recipe) | N10-012, N10-026 |
| Assessor (NaMi Migration Assessor) | N10-007 |
| Readiness (điểm sẵn sàng chuyển đổi) | N10-009 |
| Broker route (Compatibility Broker) | N10-017 |
| PE analyzer (bộ phân tích PE an toàn) | N10-018 |
| Workflow/evidence (workflow-test, evidence-record schema) | N10-031, N10-043 |

Ngoài 8 mã trên, mọi mục P0/P1 khác áp dụng quy tắc mặc định `open`, trừ khi nghiệm thu của chính nó nêu rõ cần phần cứng/pilot/Windows có phép/cổng thật → `blocked-infra`. Tại thời điểm viết (07/11/2026), `src/namios_mig/` đã có 4 file (`_types.py`, `_errors.py`, `schema.py`, `assessor.py`); grep trực tiếp trong mã nguồn xác nhận các module này tự gắn nhãn requirement theo đúng mã N10 (ví dụ `_types.py` dòng 1 ghi "Hợp đồng dữ liệu M0 — Phụ lục 10"; `assessor.py` dòng 1 ghi "NaMi Migration Assessor (N10-007)"). Grep cũng cho thấy `_types.py`/`_errors.py` có chạm tới N10-006, N10-008, N10-019 (kiểu dữ liệu `PeripheralKind`, liên kết nhiệm vụ, trường recipe cho Wine capsule) — đây chỉ là định nghĩa kiểu dữ liệu dùng chung, KHÔNG đủ để đổi trạng thái 3 mã đó khỏi `blocked-infra` vì nghiệm thu thật của chúng (khảo sát thiết bị/nhiệm vụ thật, Wine capsule thật) vẫn cần hạ tầng chưa có. Chưa thấy test (`tests/`) riêng cho `namios_mig` và chưa có manifest/dữ liệu thật chạy qua; KHÔNG nâng trạng thái 8 mã trong bảng ánh xạ cao hơn `in-progress-code` chỉ vì file đã tồn tại. Có thêm một mockup UI tĩnh (`docs/design/mockups/namios-migration-assessor.svg`) liên quan N10-007, cũng chỉ là bản vẽ giao diện, không phải bằng chứng đã test.

## Bảng theo dõi

| Mã | P0/P1 | Tóm tắt | Trạng thái | Owner | Nghiệm thu (rút gọn) | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| N10-001 | P0 | ADR nền tảng (so sánh 2 nền Linux) | blocked-infra | TBD | ADR có điểm số, thử máy, rollback, owner | ADR 0001/0002 đã có ở trạng thái `proposed`; khóa quyết định cần pilot phần cứng thật, chưa làm. |
| N10-002 | P0 | Desktop stack (GNOME/KDE…) | blocked-infra | TBD | 12 luồng UX + 5 app Wine/XWayland chạy trên 2 ứng viên | ADR 0003 đã có (`proposed`); cần chạy app Wine thật trên phần cứng để so sánh. |
| N10-003 | P0 | Ranh giới dịch vụ (IPC version/schema/quyền) | open | TBD | Tắt AI/App Center không hỏng login/IME/mạng/in | Nhiều package `namios_*` trong `src/` đã tách theo service, nhưng chưa verify đúng theo nghiệm thu N10-003 cụ thể. |
| N10-004 | P0 | Gói sản phẩm có thể tái tạo (ISO/SBOM/ký) | blocked-infra | TBD | Hai build cùng input → manifest tương đương | Build ISO cần `live-build`/`qemu` thật; M1-BACKLOG ghi rõ M3 ISO BLOCKED tại host hiện tại. |
| N10-005 | P0 | Chế độ offline có chủ đích | blocked-infra | TBD | 8 giờ offline vẫn hoàn thành việc mẫu | Cần desktop/Office/IME tích hợp thật (M3), chưa có tại host. |
| N10-006 | P1 | Hồ sơ thiết bị có trọng số | blocked-infra | TBD | Tỷ lệ phủ tính theo máy khảo sát thật | Cần khảo sát thiết bị thật tại trường/hộ KD/gia đình. |
| N10-007 | P0 | NaMi Migration Assessor | in-progress-code | TBD | Một máy mẫu xuất manifest review được, che PII | `src/namios_mig/assessor.py` (whitelist trường, đánh dấu `rejected_fields`, chỉ giữ usage 30 ngày khi opt-in); có mockup UI tĩnh liên quan; chưa chạy trên máy Windows thật. |
| N10-008 | P0 | Bản đồ công việc trước phần mềm | blocked-infra | TBD | Hai app cùng tên khác nghiệp vụ không gộp badge | Cần phỏng vấn người dùng thật theo nhiệm vụ. |
| N10-009 | P0 | Điểm sẵn sàng chuyển đổi (ready/blocked/…) | in-progress-code | TBD | Kế toán không ký được = blocked dù app khác chạy | Mã lỗi/nhãn liên quan đã khai trong `src/namios_mig/_errors.py`; chưa thấy rule engine chấm điểm đầy đủ 5 mức (`ready/ready_with_limits/pilot_only/blocked/unknown`) và chưa có input manifest thật. |
| N10-010 | P0 | Sao lưu trước di chuyển | blocked-infra | TBD | Lấy lại 10 file mẫu + 1 DB thử trước khi xóa máy gốc | Cần máy Windows thật + thao tác xóa/phân vùng thật để nghiệm thu. |
| N10-011 | P0 | Di chuyển tệp và cấu trúc | open | TBD | 1.000 tệp dấu Việt/hoa-thường/symlink có báo cáo hash | Có thể viết + test bằng fixture tệp giả (Python thuần), chưa bắt đầu. |
| N10-012 | P0 | Chuyển dữ liệu ứng dụng (recipe export/import) | in-progress-code | TBD | Đối chiếu tổng tiền/chứng từ trên dữ liệu giả | `src/namios_mig/assessor.py` tái dùng state machine `namios_e08.install_txn` (check-source→snapshot→apply→function-test→commit/rollback) cho export/import/đối-chiếu; chưa chạy trên app/dữ liệu giả thật. |
| N10-013 | P0 | Danh tính và đăng nhập | open | TBD | User khác không truy cập; offline vẫn login theo policy | Case local/family có thể test trong sandbox; LDAP/AD/OIDC thật cần hạ tầng tổ chức. |
| N10-014 | P1 | Trình nhập browser (bookmark/extension) | open | TBD | URL bookmark đúng; extension quyền rộng bị đánh dấu | Testable bằng file export bookmark giả, chưa bắt đầu. |
| N10-015 | P0 | Giai đoạn chạy song song (dual boot) | blocked-infra | TBD | 10 tác vụ lặp đối chiếu được, có đường quay lại | Cần máy thật/2-4 tuần vận hành song song thật. |
| N10-016 | P0 | Kế hoạch rút lui | blocked-infra | TBD | Kịch bản mất driver in/ngừng app thuế không mất dữ liệu | Nghiệm thu cần tình huống lỗi thật trên thiết bị/app thật. |
| N10-017 | P0 | Compatibility Broker (chọn tuyến route) | in-progress-code | TBD | App mở GUI được nhưng ký lỗi → đề xuất route khác | Kiểu `CompatRoute` đã khai trong `src/namios_mig/_types.py`; chưa thấy hàm chọn route theo dependency graph/chứng cứ thật, chưa nối API broker. |
| N10-018 | P0 | Bộ phân tích PE an toàn (đọc metadata, không chạy) | in-progress-code | TBD | 20 fixture đã gán nhãn; `.sys` không bị coi là app user mode | Chỉ mới có mã lỗi liên quan trong `src/namios_mig/_errors.py`; CHƯA thấy module parser PE thật — đây là mã sớm nhất trong nhóm 8 mã `in-progress-code`, gần với `open` hơn các mã khác. |
| N10-019 | P0 | Wine capsule versioned | blocked-infra | TBD | 2 app kế toán xung đột DLL không ảnh hưởng nhau; rollback | M1-BACKLOG ghi M2 (Wine/.NET) BLOCKED tại host hiện tại. |
| N10-020 | P0 | Nền tảng API và log chuẩn (phân loại lỗi) | open | TBD | Lỗi app thuế được chỉ ra đúng tầng (token/crypto/browser…) | Thiết kế taxonomy lỗi là code thuần, có thể bắt đầu; chưa làm. |
| N10-021 | P0 | Windows path & file semantics | open | TBD | 100 file dấu Việt/hoa-thường/UNC không ghi đè âm thầm | Testable bằng fixture tên file giả, chưa bắt đầu. |
| N10-022 | P0 | Cầu in ấn và thiết bị | blocked-infra | TBD | Bản in giữ lề/phông/tổng; token bị từ chối khi chưa cấp quyền | Cần máy in/USB token thật. |
| N10-023 | P0 | COM, Office add-in và OLE | blocked-infra | TBD | Workbook mở được nhưng macro hỏng → `partial`, không `ready` | ADR 0013 xác nhận host hiện tại chưa cài LibreOffice/SDK UNO; cần Office/Wine thật. |
| N10-024 | P0 | Cầu crypto/chữ ký số có ranh giới | blocked-infra | TBD | Ký dữ liệu thử, xác minh độc lập, ghi biên nhận | Cần token/thiết bị ký thật + cổng dịch vụ công thật. |
| N10-025 | P0 | Ứng dụng .NET theo loại (routing) | blocked-infra | TBD | 4 fixture console/WinForms/WPF/service phân tuyến đúng | M1-BACKLOG ghi M2 Wine/.NET BLOCKED tại host hiện tại. |
| N10-026 | P1 | Recipe compatibility có thể kiểm toán | in-progress-code | TBD | App đổi hash/version tự `needs_retest` | `src/namios_mig/schema.py` có `validate_recipe`/`recipe_needs_retest`/`promote_recipe`, tái dùng state machine `namios_odc.device_cert`; chưa có recipe ký thật để test vòng đời. |
| N10-027 | P0 | Không tự tải hoặc vá binary (guardrail SmartAI) | open | TBD | Prompt "tải crack để chạy MISA" bị từ chối | Guardrail logic/eval có thể viết bằng Python thuần, chưa bắt đầu. |
| N10-028 | P0 | Windows fallback được quản lý (RemoteApp/VM) | blocked-infra | TBD | Quy trình thuế vẫn có đường xử lý hợp lệ khi Wine fail | Cần Windows có bản quyền + VM/VPN thật. |
| N10-029 | P1 | Hợp tác upstream (Wine/IME/print bug) | blocked-infra | TBD | Mỗi patch downstream có issue upstream hoặc ADR ngoại lệ | Cần bug thật tái hiện trên Wine/IME/print thật theo thời gian. |
| N10-030 | P0 | Catalog theo việc (office/Zalo/kế toán/thuế/…) | blocked-infra | TBD | Mỗi app có owner vendor/version/route/test/blocker | Cần khảo sát địa phương/trường/hộ KD/DN thật. |
| N10-031 | P0 | Bộ 12 hành trình Việt Nam | in-progress-code | TBD | Có fixture và bằng chứng đầu ra từng bước | `WorkflowTest`/`WorkflowTestStatus` trong `src/namios_mig/_types.py` + `validate_workflow_test` trong `schema.py`; các bước cần in/scan/ký thật vẫn `blocked-infra` cho tới khi có thiết bị/fixture thật. |
| N10-032 | P0 | Hồ sơ thuế và kế toán | blocked-infra | TBD | Checksum số tiền/chứng từ trùng nguồn chuẩn | Cần dữ liệu đối chứng từ hệ thống thuế/kế toán thật. |
| N10-033 | P0 | Hóa đơn và chữ ký (tách lập/ký/gửi/nhận mã) | blocked-infra | TBD | "Đã tạo" ≠ "đã phát hành" nếu thiếu chứng cứ ngoài | Cần vendor hóa đơn điện tử thật. |
| N10-034 | P1 | Giáo dục (LMS/font toán/máy chiếu…) | blocked-infra | TBD | 1 giáo viên dạy 45 phút + in 30 phiếu không mất tiếng/định dạng | Cần lớp học/giáo viên/thiết bị thật. |
| N10-035 | P1 | Hành chính công (catalog cổng dịch vụ công) | blocked-infra | TBD | Không hiện "hỗ trợ dịch vụ công" khi chưa có route hợp lệ | Cần kiểm từng cổng dịch vụ công thật, đổi liên tục. |
| N10-036 | P1 | Người dùng ít rành công nghệ (khảo sát hành vi) | blocked-infra | TBD | ≥5 người/persona, ghi video/ghi chú có consent | Cần người dùng thật tham gia khảo sát. |
| N10-037 | P1 | Mẫu tài liệu Việt Nam (thư mời/công văn/hóa đơn thử) | blocked-infra | TBD | Mẫu in đúng trang, Unicode không hỏng | Nghiệm thu cần in thật trên máy in thật; nội dung mẫu có thể soạn trước nhưng chưa bắt đầu. |
| N10-038 | P0 | Design language NaMiOS | blocked-infra | TBD | Test ở 1366×768/1080p/HiDPI/máy yếu; thuật ngữ nhất quán | Cần desktop thật để test (M3, BLOCKED tại host theo M1-BACKLOG B039). |
| N10-039 | P0 | Hỗ trợ tiếng Việt chuyên ngành (glossary có người duyệt) | blocked-infra | TBD | 50 lỗi/tác vụ được người trong ngành đánh giá rõ nghĩa | Cần người chuyên môn (thuế/kế toán/giáo dục…) thật duyệt. |
| N10-040 | P0 | Trải nghiệm từ lỗi đến kết quả (panel "Việc cần làm") | blocked-infra | TBD | Theo dõi 1 task từ mở file → in/scan/ký → kết quả | Cần desktop UI thật + thiết bị in/scan/ký thật (M3). |
| N10-041 | P0 | SmartAI orchestrator (plan có ý định, rollback) | open | TBD | 20 nhiệm vụ mơ hồ, AI hỏi đúng dữ kiện, không chạy root shell | Có thể eval bằng harness + LLM thật không cần phần cứng riêng; module `namios_smartai` đã tồn tại trong `src/` nhưng chưa verify theo đúng nghiệm thu N10-041. |
| N10-042 | P0 | Cơ sở tri thức có nguồn (chống prompt injection) | open | TBD | 10 ca prompt injection không kích hoạt tool | Eval được trong sandbox, chưa bắt đầu theo đúng bộ 10 ca này. |
| N10-043 | P0 | Bằng chứng sau hành động (validator, không tự nhận "đã sửa") | in-progress-code | TBD | Job spool "thành công" nhưng giấy trắng = failed/partial | `EvidenceRecord` trong `src/namios_mig/_types.py` + `validate_evidence_record` trong `schema.py` chặn `status=PASSED` thiếu evidence/ngày kiểm; module `namios_evidence` có sẵn trong repo để tái dùng; cần nối với workflow thật để nghiệm thu. |
| N10-044 | P0 | AI tiếng Việt có đánh giá (eval theo miền/phương ngữ) | blocked-infra | TBD | Công bố tỷ lệ hoàn thành/unsafe/sai/latency/chi phí thật | Cần bộ eval + người đánh giá thật, dữ liệu giả/đã đồng ý. |
| N10-045 | P1 | Chọn local/cloud minh bạch | open | TBD | Rút mạng/tắt AI cloud không ảnh hưởng IME/login/firewall | Thiết kế chính sách + code switch, chưa bắt đầu. |
| N10-046 | P1 | Kiến trúc plugin an toàn (manifest/quyền/chữ ký) | open | TBD | Plugin giả đòi đọc mọi tệp bị từ chối/hiện quyền rõ | Có thể thiết kế schema plugin bằng Python thuần, chưa bắt đầu. |
| N10-047 | P0 | Ma trận ngoại vi theo chức năng | blocked-infra | TBD | "Phát hiện" và "hoạt động" hiển thị riêng | Cần model/firmware/thiết bị thật theo từng dòng máy. |
| N10-048 | P0 | Phát hiện thiết bị và sửa có rollback | blocked-infra | TBD | Mất mạng sau update kernel quay được bản cũ | Cần phần cứng thật + kernel update thật để test rollback. |
| N10-049 | P0 | Bảo mật nhiều lớp (10 ca test) | blocked-infra | TBD | 10 ca (file độc, app vượt quyền, update giả, phục hồi) | `docs/threat-model.md` đã liệt kê các test SEC-0x cần Wine/sandbox thật ở mục "Cần M2 (BLOCKED tại đây)". |
| N10-050 | P0 | Chuỗi cung ứng (SBOM/CVE/ký build) | open | TBD | Mô phỏng khóa ký bị lộ → thu hồi, phát hành thay thế | Quy trình + mô phỏng có thể làm bằng code/process thuần, chưa bắt đầu. |
| N10-051 | P0 | Cập nhật nguyên tử và cứu hộ | blocked-infra | TBD | 3 điểm ngắt điện/full disk/driver regress vẫn khôi phục được | Cần máy thật để test ngắt điện/hết ổ/regress thật. |
| N10-052 | P1 | Hỗ trợ 5 năm (chu kỳ, EOL, ngân sách) | blocked-infra | TBD | Một thay đổi vendor/browser có người nhận incident | Cần quyết định tổ chức/ngân sách thật sau ADR, chưa có. |
| N10-053 | P1 | Quản trị tổ chức (golden image, rings) | blocked-infra | TBD | Rollout 20 máy thử, rollback nhóm không ảnh hưởng nhóm khác | Cần 20 máy thật + tổ chức pilot. |
| N10-054 | P0 | Quyền và giấy phép (license inventory) | open | TBD | Artifact release có manifest license; binary không phép bị loại | Khung đã tạo ở `docs/license-inventory.md`; nội dung từng dòng còn "cần xác minh". |
| N10-055 | P1 | Cộng đồng và nhà cung cấp | blocked-infra | TBD | Bug mẫu có số nhận, môi trường, reproduction, SLA sửa | Cần kênh cộng đồng/báo lỗi hoạt động thật. |
| N10-056 | P0 | Chi phí sống còn (mô hình 1.000/10.000 máy) | open | TBD | Mô hình chi phí có giả định rõ + ngưỡng duy trì | Có thể soạn mô hình/bảng tính, chưa bắt đầu. |
| N10-057 | P0 | Release gate theo tác vụ | open | TBD | CI/pilot tạo báo cáo red gate; không override thiếu ADR | Khung đã tạo ở `docs/release-gates.md`; chưa nối vào CI/pilot thật. |
| N10-058 | P0 | Ma trận phạm vi hỗ trợ (tuple machine/OS/app/route/workflow) | open | TBD | Đổi browser/Wine/runtime/driver/version tự invalidate | Khung schema đã tạo ở `docs/support-matrix.md`; chưa có badge nào `verified` bằng dữ liệu thật. |
| N10-059 | P1 | Thử nghiệm thực địa (pilot 3 nhóm, ≥5 người/nhóm) | blocked-infra | TBD | Báo cáo lỗi/tần suất/ngữ cảnh/cải tiến từ pilot thật | Cần người dùng thật + thiết bị/mạng thật. |
| N10-060 | P0 | Điểm dừng và đổi hướng | blocked-infra | TBD | Quyết định có số liệu, phạm vi, ngày đánh giá lại | Cần số liệu thật từ các mốc trước (đa số đang `open`/`blocked-infra`) để ra quyết định có căn cứ. |

## Ghi chú chung

- Không mục P0 nào trong bảng trên được đánh dấu hoàn thành/`done`; `in-progress-code` chỉ nghĩa là có khung code/schema đang dựng, không phải đã qua test thật.
- Cột "Owner" để `TBD` toàn bộ; cần chủ dự án (Đỗ Chí Cường/Đỗ Bảo Nam) phân công theo năng lực đội trước khi coi là đã có người phụ trách.
- Nhiều mục `blocked-infra` lặp lại cùng một điều kiện mở khóa (build host nested-virt/Wine/.NET thật, phần cứng pilot, Windows có bản quyền, cổng dịch vụ công/vendor thật, người dùng thật) — xem `docs/specs/M1-BACKLOG.md` mục "Ngoài phạm vi M1" để biết các mốc M2–M5 đang BLOCKED tại host hiện tại vì lý do gì.
