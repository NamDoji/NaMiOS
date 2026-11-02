# ADR 0001 — Chọn Linux và Wine

- **Trạng thái:** proposed (cần spike xác nhận; chưa phải kết quả thử nghiệm)
- **Ngày:** 02/11/2026
- **Liên quan:** §1, §5, §6, ADR 0002; requirement COMP-001, COMP-008, APP-MIS-008

## Bối cảnh

Mục tiêu là một bản phân phối Linux miễn phí cho người Việt, chạy được công việc văn phòng và một số ứng dụng Windows qua lớp tương thích đã kiểm thử. Ba hướng khả dĩ: (a) sửa/đóng gói lại Windows, (b) tự viết nhân tương thích Windows, (c) dùng Linux + Wine.

## Quyết định

Chọn (c): nền Linux được duy trì + Wine để thử tương thích Windows theo hồ sơ từng ứng dụng. Không sửa Windows, không tự viết nhân. ReactOS KHÔNG chọn cho pilot nghiệp vụ vì còn ở trạng thái alpha ([S12], tra cứu 02/11/2026).

## Lý do

- Wine là lớp tương thích, không chạy một bản Windows bên dưới ([S02]); tránh gánh nặng bản quyền/driver của việc nhúng Windows.
- Nền Linux + Wine được cộng đồng duy trì, giảm chi phí tự viết; phù hợp mục tiêu miễn phí.
- Chạy app Windows qua Wine là thực thi mã không tin cậy (COMP-008) → phải có hồ sơ cách ly và chứng nhận theo tác vụ (ADR 0008).

## Hệ quả

- Có nền tảng được duy trì, NHƯNG không có bảo đảm app Windows/driver chạy được; đầu tư chỉ tiếp tục theo bằng chứng.
- Tương thích trên Wine ≠ nhà cung cấp hỗ trợ chính thức Linux; hai nhãn phải độc lập.
- Mỗi user/app/major/profile có prefix riêng; không chạy wine/installer bằng root (COMP-001).

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Host build hiện tại là **Debian 12 trong container**, **không có** wine/winetricks, **không có** `/dev/kvm`, CPU thiếu vmx/svm.
- → **Không thể dựng Wine fixture hay chạy app Windows tại host này.** Phần phụ thuộc Wine thuộc M2, hiện **BLOCKED**; cần build host Linux amd64 có nested-virt + bộ cài có quyền dùng do chủ dự án cấp.
- Phần độc lập với Wine (phân tích tĩnh .NET, hồ sơ/manifest, policy cách ly) vẫn thiết kế và test logic được ở M1.

## Spike cần làm + điều kiện chấp nhận

- **Spike S1:** dựng 1 Wine prefix sạch + chạy 1 fixture Win32 tự viết (32-bit và 64-bit theo capability). *Chấp nhận:* fixture chạy thật, ghi runner/WoW64 thực; app không hỗ trợ giữ `blocked`.
- **Spike S2:** chạy wine bằng root bị từ chối; đọc prefix user khác bị từ chối (SEC-05). *Chấp nhận:* negative test đạt.
- **Điều kiện chấp nhận ADR:** có fixture chạy thật, mô hình build rõ, inventory quyền phân phối. *Thay đổi nếu:* app bắt buộc không thể chạy và chủ dự án không chấp nhận phạm vi hẹp hoặc lựa chọn khác (G0 go/no-go).

## Nguồn

- [S02] Wine — https://www.winehq.org/about/
- [S12] ReactOS — https://reactos.org/download/
