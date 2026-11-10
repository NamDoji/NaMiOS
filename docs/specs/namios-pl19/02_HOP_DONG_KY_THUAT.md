# 02. Hợp đồng kỹ thuật nâng cấp NaMiOS

## 1. Các thành phần và trách nhiệm

Update Center chỉ là UI không có quyền root; Update Service quyền tối thiểu thực hiện kiểm/tải/xác minh/stage/apply; release repository giữ metadata và payload bất biến; boot manager chọn deployment; health agent báo trạng thái sau boot; recovery manager quay về bản trước; migration manager xử lý dữ liệu ứng dụng có phiên bản; backup service kiểm khả năng phục hồi. SmartAI chỉ đọc trạng thái đã lọc và gọi action được policy cho phép. Tách khóa production khỏi build/test và khỏi quyền AI.

Chọn cơ chế OS image/OSTree/rpm-ostree/A-B hoặc transactional tương đương bằng ADR sau khi khảo sát repo và bootloader. Không coi tên công nghệ trong tài liệu là đã quyết định. Cấu trúc hệ thống phải giữ tối thiểu bản đang boot và bản rollback cho tới khi bản mới hoàn tất health check và thời gian canary; dọn cache không được xóa bản phục hồi. Cần đo dung lượng trên máy yếu trước khi chốt default.

## 2. State machine có journal

DISCOVERED → ELIGIBLE → DOWNLOADING → DOWNLOADED → VERIFIED → PREFLIGHT_OK → STAGED → REBOOT_PENDING → BOOTING_NEW → HEALTH_CHECK → COMMITTED. Nhánh BLOCKED/FAILED/ROLLBACK_PENDING/ROLLED_BACK/RECOVERY_REQUIRED có reason code. Service ghi state và correlation ID bền vững, idempotent qua reboot/kill; không chuyển COMMITTED chỉ vì tool báo đã cài. Mỗi bước có timeout, retry policy và tác vụ được phép hủy.

Metadata/payload phải khớp product, channel, arch, hardware constraints, current/target build, dependency, kích thước, hash, chữ ký và freshness; chống rollback/freeze/replay, thu hồi. Download có resume theo chunk kiểm hash; verify lại trước stage. Gói bị sai chữ ký không được dùng mirror khác chưa tin cậy hoặc nút “cài dù sao”. Máy mất mạng lâu có chế độ tải gói ngoại tuyến đã ký và kiểm chain/expiry/kiến trúc trước cài, không đơn giản chép ISO bất kỳ.

## 3. Preflight và dữ liệu

Tính dung lượng cần cho download, staged image, rollback, journal và backup ứng dụng. Kiểm battery/power, ổ đĩa lỗi, đồng hồ, mã hóa và khóa mở ổ, boot entries, dual boot, network, ứng dụng chưa lưu, phiên bản trung gian bắt buộc. Cho trình kiểm khô không sửa hệ thống. Nếu backup chưa đủ cho migration dữ liệu có nguy cơ, chặn và giải thích.

Rollback OS chỉ khôi phục hệ thống, không rollback tự động thư mục home hoặc database. Mỗi migration có version, chiều tiến/lùi hoặc kế hoạch restore; smoke test trên bản sao, snapshot/backup có test phục hồi. Nếu ứng dụng mới mở dữ liệu rồi đổi schema không tương thích, không cho OS rollback mù. Giữ dữ liệu người dùng ngoài deployment image và xác định rõ phạm vi backup; không xóa phân vùng Windows của dual boot.

## 4. Health check và rollback

Sau boot kiểm kernel/userspace, login, desktop shell, storage mount/khóa, Update Service, dịch vụ mạng cơ bản, boot loop/crash count và một số chức năng phần cứng chứng nhận (Wi-Fi, Bluetooth, in) bằng smoke test không xâm phạm. Mất mạng do môi trường bên ngoài không nhất thiết rollback ngay; cần phân biệt lỗi bản update với lỗi router. Nếu kernel/login/storage/desktop thất bại hoặc health gate P0 không đạt trong thời hạn, boot manager quay lại bản trước; báo rõ đã rollback và giữ log đã lọc.

Không tự rollback firmware nếu thiết bị không hỗ trợ. Firmware là luồng riêng có model, pin/nguồn, chữ ký và xác nhận rõ. App cập nhật riêng có rollback gói app khi khả thi, không đòi boot OS.

## 5. Phát hành từ phía nhà sản xuất

CI build nguồn pinned, SBOM, license/security scan, test VM và máy thật; ký release sau gate; pilot ring → stable theo đợt và tự dừng rollout nếu boot fail/crash/driver regression vượt ngưỡng. Có kill switch/revocation, release notes tiếng Việt, danh sách máy/app đã thử và known issues. Bản vá khẩn có quy trình nhanh nhưng vẫn xác minh chữ ký, preflight, staged/rollback. Các máy quản trị tập trung có lịch và chính sách riêng, người dùng nhìn thấy.

## 6. Hợp đồng API tối thiểu

Các method: check_updates, get_release_notes, get_policy, set_user_policy, download, pause_download, verify, preflight, stage, schedule_reboot, cancel_schedule, get_state, get_history, get_health, request_rollback, export_support_report. Mỗi mutation cần caller, policy decision, idempotency key; response có update_id, state, progress phase, code, user_message_vi, next_actions, restart_required, estimated_bytes, rollback_target. App thường không thể gọi verify/apply với payload tùy ý. Hợp đồng có schema và test chuyển trạng thái hợp lệ.
