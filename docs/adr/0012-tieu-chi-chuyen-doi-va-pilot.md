# ADR 0012 — Tiêu chí chuyển đổi và pilot

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §29 (WIN-001..008), §30 (MIG-001); test WIN-01..03, UI-07; backlog B038, B042, B043; assumptions A88–A95
- **Bổ sung đặc tả:** SUPERSET §29 + §30 (delta vòng 2)

## Bối cảnh

Mục tiêu chiến lược là tăng dần số **công việc trọn vẹn** người dùng Windows có thể làm trên NaMiOS, KHÔNG phải "mở được .exe". Không thể đặt yêu cầu nghiệm thu "mọi ứng dụng Windows đều chạy" cho nền Linux/Wine: app có driver nhân Windows, chống gian lận, dịch vụ đặc biệt, kích hoạt hoặc tích hợp nội bộ có thể không hoạt động. Cần định nghĩa chặt về tiêu chí chuyển đổi, pilot và ranh giới của WIN-008.

## Quyết định

1. **Tương đương theo tác vụ (WIN-003):** mỗi app xác định các tác vụ bắt buộc — cài/kích hoạt hợp lệ, mở dữ liệu cũ, sửa, tính, lưu, đóng/mở lại, in, xuất, gửi tệp, cập nhật, phục hồi — và so với **Windows tham chiếu cùng phiên bản + dữ liệu thử**. Mở được giao diện KHÔNG đủ.
2. **Khảo sát + pilot (WIN-001):** danh mục 100 app Windows từ người dùng mục tiêu (ghi phiên bản + 10 tác vụ phổ biến/nhóm), chọn 20 app pilot theo tần suất/mức quan trọng/độ khó di chuyển; Word/Excel/Zalo PC/MISA SME + các lớp .NET phải nằm trong khảo sát. 100 và 20 là **TARGET khảo sát**, KHÔNG tuyên bố đã khảo sát hay sẽ có 100 app chạy được.
3. **Mode ghi riêng (WIN-003/005):** `wine / web / native / vm / remote` ghi riêng trong kết quả; KHÔNG cộng gộp mode để báo tỷ lệ tương thích desktop. Binary cần kernel driver Windows → gắn `requires_windows_environment` trừ khi có giải pháp Linux vendor-supported đã test.
4. **Workflow trọn vẹn (WIN-006):** tiêu chí chuyển đổi của một cơ quan/doanh nghiệp lập từ TOÀN BỘ workflow (tạo file Office → gửi Zalo/email → ký số/hóa đơn → lưu kho → in → đối soát MISA, nếu có dùng). Nếu MỘT bước bắt buộc fail → nhóm là **`not_ready_for_migration`**. KHÔNG đưa kết quả app rời rạc thành lời khuyên bỏ Windows.
5. **Pilot 30 ngày (WIN-007):** thí điểm song song 30 ngày với nhóm tự nguyện trên thiết bị đã chứng nhận; theo dõi tác vụ thất bại, số lần quay lại Windows, dữ liệu sai, thời gian hỗ trợ, lỗi sau cập nhật; báo cáo có mẫu số người dùng + số lần. **Ngưỡng đề xuất để xem xét mở rộng:** 0 mất/sai dữ liệu P0, 100% tác vụ bắt buộc đã chốt hoàn thành, ≥90% tác vụ hàng ngày không phải quay lại Windows. Con số là ngưỡng đề xuất, **chốt TRƯỚC khi đo**.
6. **WIN-008 — ranh giới cứng:** nếu mục tiêu kinh doanh đòi **mọi** phần mềm Windows hiện hành chạy nguyên vẹn kể cả kernel driver → phải **đánh giá lại chiến lược nền tảng** trước khi đầu tư rộng. KHÔNG giao Claude Code nhiệm vụ "bảo đảm 100% tương thích" như thể một mức cố gắng lập trình giải quyết được chắc chắn. Kết quả khảo sát có thể dẫn tới **phạm vi thiết bị/app chứng nhận hẹp** hoặc **mô hình máy Windows hợp lệ (VM/remote có license)** phía sau, báo rõ phụ thuộc + chi phí.
7. **Tiếp nhận app lỗi (WIN-004):** repro tối thiểu, log không bí mật, bước gây lỗi, phân loại Wine/runner/prefix/driver/service/activation/ứng dụng, mức mất dữ liệu, người chịu trách nhiệm, test hồi quy. Gửi vá upstream theo giấy phép khi có thể; KHÔNG fork hàng loạt để "hỗ trợ mọi app" khi chưa có đội bảo trì.
8. **Checklist chuyển đổi (MIG-001):** app/thiết bị/phiên bản dữ liệu/backup-restore/tài khoản-giấy phép/người hỗ trợ/kế hoạch quay về/người ký chấp thuận. Thử trên máy phụ hoặc Live mode trước; chỉ chuyển máy chính khi workflow nghiệm thu + có bản sao dữ liệu phục hồi được.

## Lý do

- "Mở .exe" là false signal; chỉ workflow trọn vẹn mới phản ánh chuyển đổi thật.
- Cộng gộp mode (web + vm + wine) sẽ thổi phồng tỷ lệ "tương thích desktop" — phải tách.
- WIN-008 là rủi ro chiến lược, không phải bug lập trình; phải chặn kỳ vọng "code chăm hơn = 100% compat".

## Hệ quả

- Schema evidence-report đã có khái niệm mode + tuple (ADR 0008); thêm `requires_windows_environment` và trạng thái nhóm `not_ready_for_migration` vào mô hình — **M1 làm được** (validator + state).
- Khảo sát WIN-01 là review G0 nhưng DỮ LIỆU 100 app cần người dùng mục tiêu → khung/template làm được, dữ liệu thật BLOCKED chờ chủ dự án.
- Pilot/workflow thật (WIN-02/03) thuộc M4, BLOCKED (cần thiết bị chứng nhận + người tình nguyện + bộ cài hợp lệ).

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Host không có Wine/VM/phần cứng/người dùng pilot. Khung khảo sát 100 app, schema tiêu chí tác vụ, state `not_ready_for_migration`, checklist MIG-001: **M0/M1 làm được** (template + Python thuần).
- Chạy workflow Office→Zalo→ký số→MISA và pilot 30 ngày/usability 15 người: **M4 BLOCKED** — ghi `blocked_external_dependency`.

## Spike cần làm + điều kiện chấp nhận

- **Spike S-WIN-1:** template khảo sát 100 app (app × version × 10 tác vụ) + tiêu chí chọn 20 pilot; kiểm KHÔNG claim đã khảo sát/pass.
- **Spike S-WIN-2:** mô hình tác vụ + mode trong evidence → cộng gộp mode KHÔNG tạo được "tỷ lệ tương thích desktop"; binary cần kernel driver → tự gắn `requires_windows_environment`.
- **Spike S-WIN-3:** rule workflow — 1 bước bắt buộc fail ⇒ nhóm `not_ready_for_migration`, không thành "nên bỏ Windows".
- **Spike S-WIN-4 (khi có pilot, M4):** WIN-02 chạy workflow trọn vẹn so Windows tham chiếu; WIN-03 pilot 30 ngày với mẫu số + ngưỡng đã chốt trước.
- **Điều kiện chấp nhận:** không đường nào báo "đạt chuyển đổi" khi còn 1 bước bắt buộc fail; không gộp mode; không tồn tại nhiệm vụ/claim "bảo đảm 100% tương thích"; WIN-008 được xử lý như quyết định chiến lược (go/no-go/phạm vi hẹp/đường VM-remote có license), không phải mục tiêu lập trình; tests WIN-01..03 giữ `not_run` cho tới khi có dữ liệu/pilot.
