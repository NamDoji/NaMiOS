# APP11 Backlog — Phụ lục 11: Bộ ứng dụng thiết yếu tích hợp và cập nhật thống nhất

**Nguồn:** `docs/spec-package/NaMiOS_Phu_luc_11_Bo_ung_dung_tich_hop_va_Cap_nhat.md` (06/11/2026), mã `APP11-001`–`APP11-036`.
**Trạng thái tài liệu này:** bảng theo dõi backlog, không phải báo cáo tiến độ đã kiểm chứng. Không mục nào được đánh dấu `done`/hoàn thành trong file này.

## Quy ước trạng thái

- `open` — mặc định cho mọi mục P0/P1 chưa có bằng chứng code hoặc đang không có hoạt động nào.
- `in-progress-code` — có scaffolding/code/logic đang được dựng tại host hiện tại (Python thuần, không cần browser/desktop/thiết bị thật), **chưa chạy trên bản build/máy pilot thật, chưa nghiệm thu**.
- `blocked-infra` — nghiệm thu của chính mục đó đòi hỏi desktop/browser cài sẵn thật, máy pilot thật, dịch vụ web bên thứ ba thật (Zalo/YouTube/Facebook/…), engine/scanner thật, hoặc xác nhận pháp lý/thương hiệu thật; không thể tự nâng trạng thái bằng code thuần.

**Ánh xạ `in-progress-code` cho module `namios_essentials`:** tại thời điểm viết (07/11/2026), `src/namios_essentials/` đã có 12 file Python (`_types.py`, `_errors.py`, `_i18n.py`, `manifest.py`, `labels.py`, `anti_impersonation.py`, `rings.py`, `cert_workflow.py`, `smartai_classify.py`, `release_gate.py`, `update_center.py`, `update_txn.py`) — nhiều hơn một lần kiểm tra sớm hơn trong quá trình viết backlog này tìm thấy, vì module đang được dựng song song bởi một luồng công việc khác. `grep` trực tiếp mã nguồn cho thấy các mã APP11 sau có hàm/logic thật (không chỉ là tên biến) gắn trong docstring:

| File | Mã APP11 có logic thật |
| --- | --- |
| `labels.py` | APP11-001 (`delivery_label` — web KHÔNG BAO GIỜ hiện "đã cài") |
| `manifest.py` | APP11-002, APP11-014 (tái dùng `namios_e08.provenance_ok`), APP11-034 |
| `anti_impersonation.py` | APP11-003, APP11-033 (allowlist domain + `may_render_login_form` + trademark `approved` chỉ khi có hồ sơ quyền) |
| `update_center.py` | APP11-011/APP11-020 (`scanner_badge`, 2 tín hiệu độc lập), APP11-013, APP11-015 (lịch cài không phá việc đang làm), APP11-019 (`evaluate_web_shortcut`), APP11-032 (`recovery_guidance`) |
| `update_txn.py` | APP11-016, APP11-019 |
| `rings.py` | APP11-017 (tái dùng `namios_odc.LifecycleRing`) |
| `cert_workflow.py` | APP11-021, APP11-028 (tái dùng state machine `namios_odc`) |
| `smartai_classify.py` | APP11-021, APP11-026 (tái dùng `namios_sys.data_authority.authorize`) |
| `release_gate.py` | APP11-018 (hằng số `REQUIRED_WEB_SERVICES`), APP11-036 (chỉ tổng hợp invariant có sẵn, không tạo luật mới) |

**Quan trọng — code tồn tại KHÔNG đồng nghĩa đã nghiệm thu:** chưa thấy test (`tests/`) riêng cho `namios_essentials`, chưa có bản build/ISO/browser/pilot thật chạy qua bất kỳ hàm nào trong 10 file trên. Vì vậy mọi mã ở bảng trên được gắn `in-progress-code` (KHÔNG cao hơn), và với các mã mà nghiệm thu gốc đòi hạ tầng thật (ví dụ APP11-018 cần browser + 6 dịch vụ web thật, APP11-021/028 cần Wine + app Windows thật, APP11-033 cần xác nhận pháp lý thật), ghi chú ở bảng dưới nêu rõ phần nào vẫn chờ hạ tầng dù đã có code.

Ngoài các mã trên, mọi mục P0/P1 khác áp dụng quy tắc mặc định `open`, trừ khi nghiệm thu của chính nó nêu rõ cần desktop/browser/thiết bị/dịch vụ web/pháp lý thật mà hoàn toàn chưa có dòng code nào chạm tới → `blocked-infra`.

## Bảng theo dõi

| Mã | P0/P1 | Tóm tắt | Trạng thái | Owner | Nghiệm thu (rút gọn) | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| APP11-001 | P0 | Màn hình "Ứng dụng của tôi" (Launcher nhóm) | in-progress-code | TBD | 8/10 người thử tìm được Office/Zalo/YouTube/Browser/IME/Security Center | `labels.py` có `delivery_label` (4 nhãn phụ, web không bao giờ hiện "đã cài"); phần UI Launcher thật + test 8/10 người vẫn cần desktop thật (M3) — `blocked-infra` cho riêng phần đó. |
| APP11-002 | P0 | Manifest có nguồn (ký, owner, last_verified) | in-progress-code | TBD | Mục thiếu nguồn/quyền không xuất hiện ở ảnh cài chính thức | `manifest.py` có `is_shippable` fail-closed (thiếu nguồn/license/owner/ngày kiểm → không được ship); chưa có chữ ký/ảnh ISO thật để verify. |
| APP11-003 | P0 | Link chính thức (domain allowlist, chống giả mạo) | in-progress-code | TBD | Tên miền giả Zalo/WhatsApp bị chặn trước khi nhập mật khẩu | `anti_impersonation.py` có `OFFICIAL_DOMAIN_ALLOWLIST` + `may_render_login_form` (cổng duy nhất hiện form đăng nhập); chưa chạy trong browser thật. |
| APP11-004 | P0 | Cửa sổ web app khi khả dụng (PWA riêng) | blocked-infra | TBD | User xem nguồn trang, quyền site, gỡ shortcut không mất tệp | Chưa có dòng code nào chạm tới; cần browser thật hỗ trợ cài trang thành app để test. |
| APP11-005 | P0 | Không tự đăng nhập (không kèm cookie/token mạng xã hội) | open | TBD | ISO mới không liên hệ domain social trước khi user mở app | Guardrail có thể viết + test bằng kiểm tra network log giả; chưa thấy file riêng cho mã này. |
| APP11-006 | P1 | Quyền site dễ hiểu (camera/mic/vị trí/thông báo) | blocked-infra | TBD | Maps chỉ biết vị trí sau consent; thu hồi quyền không xóa session khác | Cần browser thật để test luồng cấp/thu hồi quyền. |
| APP11-007 | P0 | Bộ ứng dụng offline thiết yếu | blocked-infra | TBD | Rút cáp mạng vẫn gõ Việt/soạn tài liệu/lưu PDF/in | Cần Office/IME/máy in thật tích hợp (M3), chưa có tại host. |
| APP11-008 | P1 | Bản đồ offline tùy chọn | blocked-infra | TBD | Khu vực đã tải tìm địa chỉ cơ bản khi ngắt mạng | Cần dữ liệu bản đồ offline thật + máy test thật; chưa có app riêng nào được dựng. |
| APP11-009 | P0 | Office tách vòng đời (cài sẵn, version riêng OS) | blocked-infra | TBD | Update/rollback Office không mất file hoặc đảo version OS | ADR 0013 xác nhận host hiện tại chưa cài LibreOffice/SDK UNO; cần engine Office thật. |
| APP11-010 | P0 | Bộ gõ luôn sẵn sàng (Telex/VNI, hotkey) | blocked-infra | TBD | 200 câu có dấu trong 5 loại cửa sổ không lặp ký tự | Package `namios_i18n` đã tồn tại trong `src/` nhưng nghiệm thu đòi test trên Office/browser/Wine thật (M3), chưa làm được tại host. |
| APP11-011 | P0 | Bảo vệ máy có thật (Security Center tổng hợp) | in-progress-code | TBD | Badge chuyển cảnh báo khi chữ ký cũ; false positive có đường phục hồi | `update_center.py` có `scanner_badge` (tuổi chữ ký và kết quả quét xét độc lập, không che nhau); chưa có engine scanner thật + benchmark quét trên máy thật, chưa có cơ chế phục hồi false positive. |
| APP11-012 | P1 | Gói profile (Cá nhân/Giáo viên/Văn phòng/Kế toán) | open | TBD | Profile trường học không tự mở TikTok/Facebook | Thiết kế cấu hình profile là code/config thuần, chưa thấy file riêng cho mã này. |
| APP11-013 | P0 | Bảng trạng thái cập nhật (Update Center) | in-progress-code | TBD | User phân biệt bản browser cần tải với dịch vụ web server-side | `update_center.py` có `build_update_status` (xóa version bịa cho kênh `WEB_SHORTCUT`); chưa có UI/bản build thật để hiển thị. |
| APP11-014 | P0 | Nguồn và chữ ký (verify hash/metadata gói) | in-progress-code | TBD | Gói bị sửa/nguồn mạo danh bị từ chối với mã lỗi rõ | `manifest.py` tái dùng `namios_e08.provenance_ok` (không dựng cơ chế provenance thứ hai); chưa test trên gói/kho thật. |
| APP11-015 | P0 | Kiểm cập nhật tự động, cài có lịch | in-progress-code | TBD | 20 máy thử không bị reboot giữa tác vụ | `update_center.py` có logic quyết định lịch cài (`ScheduleDecision`/`ScheduleAction`, không reboot giữa việc khẩn trừ mức CRITICAL); 20 máy pilot thật để xác nhận không gián đoạn vẫn `blocked-infra`. |
| APP11-016 | P0 | Kiểm phụ thuộc giao dịch (stage→snapshot→commit/rollback) | in-progress-code | TBD | Ngắt điện/mất mạng/hết ổ ở 3 điểm không mất file | `update_txn.py` đã có; chưa thấy test giả lập power-cut/disk-full riêng cho module này, chưa chạy trên máy thật. |
| APP11-017 | P0 | Update rings (lab/pilot/stable) | in-progress-code | TBD | Ring stable giữ bản cũ có thời hạn khi lab phát hiện lỗi | `rings.py` tái dùng `namios_odc.LifecycleRing`, có `is_retention_expired` fail-closed (hạn rỗng = đã hết hạn ngay); chưa chạy trên candidate/ring thật. |
| APP11-018 | P0 | Cập nhật browser theo SLA (security advisory) | in-progress-code | TBD | Mọi browser release có smoke test 6 dịch vụ pass | `release_gate.py` có hằng số `REQUIRED_WEB_SERVICES` (6 dịch vụ); chạy smoke test thật trên browser + 6 dịch vụ web live vẫn `blocked-infra`. |
| APP11-019 | P0 | Dịch vụ web tự thay đổi (không kiểm soát version server) | in-progress-code | TBD | Login QR Zalo hỏng được phát hiện, không gọi là lỗi NaMiOS | `update_center.py` có `evaluate_web_shortcut` (badge `SERVICE_INCIDENT_OR_COMPAT`, không đổ lỗi "chưa cập nhật"); synthetic smoke test chạy thật trên website live vẫn `blocked-infra`. |
| APP11-020 | P0 | Chữ ký malware độc lập (engine/signature) | in-progress-code | TBD | Offline 7 ngày hiện đúng thời điểm cập nhật cuối | Cùng `scanner_badge` ở `update_center.py` (APP11-011); engine scanner thật (ClamAV hoặc tương đương) cài trên máy thật vẫn `blocked-infra`. |
| APP11-021 | P0 | Wine app có kiểm version (Zalo PC…) | in-progress-code | TBD | App đổi hash chuyển `Cần kiểm thử lại`, giữ đường quay lại | `cert_workflow.py`/`smartai_classify.py` có cổng `wine_cert_ok`/`WINE_RECIPE_PENDING_CERT`; chạy thật trên Wine + app Windows thật vẫn `blocked-infra` (M1-BACKLOG ghi M2 Wine/.NET BLOCKED tại host hiện tại). |
| APP11-022 | P0 | Changelog bằng tiếng Việt | open | TBD | User xem lịch sử và lý do rollback từng gói | Nội dung/quy trình changelog có thể soạn trước, chưa thấy file riêng cho mã này. |
| APP11-023 | P1 | Băng thông và máy yếu (delta download, throttle) | blocked-infra | TBD | Update nền không làm giật video call/trễ gõ tiếng Việt | Cần máy yếu thật + đo throttle thật theo pilot. |
| APP11-024 | P0 | Ngừng hỗ trợ minh bạch (EOL OS/browser/Office/IME) | open | TBD | Hệ thống không gắn nhãn an toàn cho thành phần hết hạn | Thiết kế chính sách EOL + hiển thị ngày là code/doc thuần, chưa thấy file riêng cho mã này. |
| APP11-025 | P0 | Khởi động kiểm tra thông minh (preflight trước khi mở app) | blocked-infra | TBD | "Mở WhatsApp" khi offline nhận giải thích + nút thử lại | Cần browser/network thật để test luồng preflight thật. |
| APP11-026 | P0 | SmartAI phân biệt loại ứng dụng (web vs cài máy vs Wine) | in-progress-code | TBD | 10 câu hỏi cập nhật tự nhiên được phân loại đúng | `smartai_classify.py` tái dùng `namios_sys.data_authority.authorize` (nội dung trang web không tự kích hoạt tool); chưa eval bằng LLM thật trên đúng bộ 10 câu hỏi của nghiệm thu. |
| APP11-027 | P0 | Trình xử lý lỗi ba mức (người mới/hỗ trợ/developer) | open | TBD | Phân biệt lỗi web/browser cũ/mất mạng/permission bằng mã khác nhau | Logic phân loại lỗi là code thuần, khả thi ngay; chưa thấy file riêng cho mã này, hiển thị UI 3 mức cần desktop thật (M3) để hoàn thiện đầy đủ. |
| APP11-028 | P0 | Chứng nhận workflow (app/version/browser/OS/hardware) | in-progress-code | TBD | YouTube xem video đạt không suy ra DRM mọi nội dung đạt | `cert_workflow.py` có `AppCertProfile` (mỗi chức năng chứng nhận riêng, tái dùng state machine `namios_odc`); test thật trên tổ hợp app/browser/OS/hardware thật vẫn `blocked-infra`. |
| APP11-029 | P1 | Hỗ trợ cài thêm (App Center tìm theo nhu cầu) | open | TBD | "Zalo desktop Linux" → hiển thị Zalo Web + hạn chế rõ | Logic gợi ý/tìm kiếm là code thuần; chưa thấy file riêng cho mã này, UI App Center cần desktop thật để hoàn thiện. |
| APP11-030 | P1 | Tìm không dấu và thuật ngữ quen (`trinh duyet`, `zalo`…) | open | TBD | 30 truy vấn tìm đúng top 3 | Logic chuẩn hóa tìm kiếm không dấu là code thuần, chưa thấy file riêng cho mã này. |
| APP11-031 | P0 | Quyền riêng tư web (profile browser tách theo user OS) | blocked-infra | TBD | User B không thấy session WhatsApp/Zalo của user A | Cần browser thật + nhiều tài khoản OS thật để test cách ly profile. |
| APP11-032 | P1 | Khôi phục khi cập nhật hỏng (rollback OS/app, không rollback web) | in-progress-code | TBD | Lỗi Office mới mở file sai → quay version app, giữ tệp gốc | `update_center.py` có `recovery_guidance` (phân biệt `WEB_SHORTCUT` không rollback được vs OS/app native rollback qua `install_txn`); health check thật trên OS/app thật vẫn `blocked-infra` (M3). |
| APP11-033 | P0 | Chống mạo danh thương hiệu (logo/trademark) | in-progress-code | TBD | Danh mục có trạng thái `approved/pending/replace_with_text` trước khi đóng ISO | `anti_impersonation.py` gài sẵn luật `approved` chỉ hiệu lực khi có `has_permission_doc`; xác nhận pháp lý/quyền thương hiệu thật cho từng logo trước khi đóng ISO vẫn `blocked-infra` — chưa có xác nhận nào. |
| APP11-034 | P0 | Phân phối có giấy phép (SBOM/license khớp từng app) | in-progress-code | TBD | SBOM và license inventory khớp từng app trong ISO | `manifest.py` chặn `binary_bundled=True` khi license không cho phép tường minh; khung đối chiếu cũng có ở `docs/license-inventory.md`; chưa có ISO thật để đối chiếu SBOM. |
| APP11-035 | P1 | Đo sử dụng không xâm phạm (telemetry opt-in cục bộ) | open | TBD | Người dùng xem/xóa dữ liệu chẩn đoán; tắt không ảnh hưởng bảo mật | Logic tổng hợp cục bộ là code thuần, chưa thấy file riêng cho mã này. |
| APP11-036 | P0 | Cổng phát hành Essentials (release gate) | in-progress-code | TBD | Báo cáo release có manifest/nguồn/ảnh UI/test pass-fail/chữ ký | `release_gate.py` có `P0_GATE_KEYS`/`REQUIRED_WEB_SERVICES`, chỉ tổng hợp invariant có sẵn ở `manifest`/`labels`; khung đối chiếu cũng có ở `docs/release-gates.md`; chưa nối vào CI/pilot thật, chưa có bản build Essentials nào để chạy gate. |

## Ghi chú chung

- Không mục P0 nào trong bảng trên được đánh dấu hoàn thành/`done`; `in-progress-code` chỉ nghĩa là có hàm/logic thật đang dựng bằng Python thuần, không phải đã qua test trên bản build/pilot/browser/Wine thật. Nhiều mã `in-progress-code` ở trên vẫn có một phần nghiệm thu gốc phụ thuộc hạ tầng thật — phần đó được nêu rõ trong cột "Ghi chú", không tự coi là đã đạt.
- Cột "Owner" để `TBD` toàn bộ; cần chủ dự án (Đỗ Chí Cường/Đỗ Bảo Nam) phân công trước khi coi là đã có người phụ trách.
- Các mã còn `blocked-infra` hoàn toàn (APP11-004, 006, 007, 008, 009, 010, 023, 025, 031) chưa có dòng code nào trong `src/namios_essentials/` chạm tới tại thời điểm viết; chúng cần desktop/browser cài sẵn thật (M3, BLOCKED tại host hiện tại theo `docs/specs/M1-BACKLOG.md`) hoặc dữ liệu/pilot thật trước khi có thể bắt đầu code.
- Phụ lục 11 không yêu cầu đọc lại toàn bộ các phụ lục trước để triển khai phạm vi này (ghi trong §0 của Phụ lục), nhưng backlog này vẫn tham chiếu `docs/threat-model.md`, `docs/release-gates.md`, `docs/license-inventory.md`, `docs/support-matrix.md` vì các yêu cầu P0 ở đây (APP11-014, APP11-018, APP11-020, APP11-033, APP11-034, APP11-036) phụ thuộc trực tiếp các khung đó.
- Vì `namios_essentials` đang được một luồng công việc khác dựng đồng thời với lúc viết backlog này, nội dung bảng trên là ảnh chụp tại 07/11/2026 — cần đọc lại mã nguồn thật trước khi dùng bảng này để báo cáo tiến độ chính thức.
