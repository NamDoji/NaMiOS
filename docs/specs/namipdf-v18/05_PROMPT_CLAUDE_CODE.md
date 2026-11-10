# 05. Prompt triển khai cho Claude Code

> Hãy phát triển **NaMiPDF**, ứng dụng PDF cài sẵn và mặc định trên NaMiOS. Đọc README và bốn file 01–04 của phụ lục này; đối chiếu NaMiOffice v1/v2 và các API NaMiOS hiện có. Đây là yêu cầu phát triển, không phải danh sách tính năng đã hoàn thành.
>
> **Khảo sát trước:** xác định repo, distro/build, UI framework, MIME, File Manager, print/scan, Update Center, SmartAI và font tiếng Việt. Benchmark ít nhất hai stack PDF phù hợp, lập ADR cho parser/renderer/editor/OCR/signature/redaction và audit từng giấy phép, bảo mật, chi phí bảo trì. Không giả định LibreOffice Draw sửa PDF đầy đủ.
>
> **Vertical slice:** tạo bản app chạy thật: mở PDF đa trang trong worker sandbox, tìm/copy tiếng Việt, thêm chú thích, sắp xếp trang, lưu bản sao atomically, mở lại trong NaMiPDF và viewer độc lập, in một trang qua CUPS. Có cảnh báo khi tài liệu ký số/đã khóa và không ghi đè bản gốc.
>
> **Mở rộng theo mốc:** M1 viewer+annotation+print; M2 true content edit+OCR vi-VN+AcroForm+conversion; M3 PAdES+PDF/A/UA+redaction được chứng minh; M4 batch/admin. Mỗi thao tác phải có trạng thái “có thể sửa/giữ nguyên/chỉ xem/chưa hỗ trợ” theo file. Không bật nút PAdES hay redaction thực khi chưa pass bộ test độc lập.
>
> **Bảo mật:** file tải về là dữ liệu không tin cậy; cấm auto JavaScript, attachment execution, network fetch; fuzz parser, giới hạn CPU/RAM, log không chứa tài liệu. AI chỉ đề xuất, xem diff và xin xác nhận; không tự ký hoặc áp dụng redaction. Chữ ký tay dạng ảnh không gắn là chữ ký số.
>
> **Nghiệm thu:** chạy PDF-01–PDF-13, báo pass/fail theo từng fixture và nguy cơ; riêng redaction phải chứng minh text/object/ảnh/OCR/metadata/old revision không khôi phục được; chữ ký kiểm trust/revocation/offline. Bàn giao source, gói cài NaMiOS, SBOM/licenses, test report, screenshots, video thao tác nếu có, known limitations và hướng dẫn người dùng tiếng Việt. Nếu thiếu hardware token hoặc file của nhà cung cấp, ghi blocker rõ và tiếp tục phần độc lập có thể làm.

## Đầu ra đầu tiên để chủ dự án duyệt

ADR chọn PDF engine và bằng chứng license; ma trận tính năng có sẵn/thiếu; bản vertical slice cài được; 13 fixture và báo cáo; ước lượng có điều kiện cho M2–M4. Tuyệt đối không đánh dấu “đã chạy đầy đủ như Acrobat” chỉ từ mockup.
