# 02. OCR, biểu mẫu, ký số, lưu trữ và an toàn dữ liệu

## 1. OCR tiếng Việt — P0 đọc, P1 sửa

Nhận dạng ảnh quét tiếng Việt có dấu và tài liệu Việt–Anh, trang xoay, deskew, ảnh xám/màu; tạo text layer có tọa độ để tìm/copy, giữ nguyên hình gốc khi chọn “PDF có thể tìm kiếm”. Trước chạy chọn ngôn ngữ, trang, output, giới hạn CPU; chạy offline theo mặc định. Hiển thị confidence theo vùng, cho sửa OCR trên bản sao, phân biệt “sửa lớp OCR” với “thay hình trang”; đánh dấu số tiền/bảng cần người kiểm tra.

Tích hợp scan qua NaMiOS Device Hub/SANE/eSCL/WSD khi model hỗ trợ, ADF/duplex, xử lý kẹt và ghi rõ trang đã xong. Chỉ gắn nhãn PDF/A khi validator độc lập đạt. Không tự thay đổi tài liệu đã ký.

## 2. Biểu mẫu — P0 AcroForm, P1 nâng cao

Điền text, checkbox, radio, dropdown/list, trường bắt buộc, tab order, validation và calculation khi an toàn; save/reopen giữ giá trị/appearance trên viewer độc lập. Export bản đã điền hoặc bản flatten theo lựa chọn; FDF/XFDF khi đã test. P1 tạo trường, help text, quyền, accessibility label và preview. XFA/dynamic forms: phát hiện và báo chỉ xem/không thể điền an toàn, có fallback client gốc; không làm mất XFA khi lưu. Không chạy PDF JavaScript tùy ý.

## 3. Chữ ký số — P1

Tách chữ ký tay dạng ảnh/nét vẽ (annotation) khỏi chữ ký số mật mã. Hiển thị chứng thư, tổ chức cấp, chuỗi tin cậy, thời gian, vùng byte được ký, sửa đổi sau ký, tình trạng thu hồi, timestamp/LTV hoặc “chưa kiểm được do offline”; không gắn huy hiệu hợp lệ chỉ từ ảnh con dấu.

Ký PAdES theo phiên bản chuẩn được kiểm: khóa trong token/HSM/PKCS#11 hoặc dịch vụ ký hợp lệ; không sao chép khóa riêng, SmartAI không nhận PIN. OCSP/CRL/timestamp theo quyền và mạng, có test vector và viewer độc lập. Mọi sửa, tối ưu hay OCR sau ký phải đánh giá tác động; lưu bản sao, cảnh báo trước, không tự động hủy chữ ký.

## 4. Redaction thật — P1, bắt buộc trước dùng cho công vụ

Hai bước: **đánh dấu vùng → xác nhận áp dụng xóa vĩnh viễn**. Xóa content stream (text/hình/vector), lớp OCR, annotation/form values, metadata, bookmark, file đính kèm, hidden layers, incremental revisions/object cũ. Sanitize bản xuất và kiểm bằng reparse, extract text, tìm chuỗi, xem object, OCR vùng sau rasterize, viewer độc lập. Không giữ bí mật trong thumbnail/cache/autosave/log lâu hơn chính sách. Rectangle đen hoặc đổi màu chữ không phải “che thông tin an toàn”.

Redaction không thể hoàn tác trên tệp xuất; giữ bản gốc theo quyền người dùng. Nếu engine không chứng minh xóa hoàn toàn trên loại PDF nào, vô hiệu hóa “Áp dụng” hoặc cho rasterize toàn trang theo lựa chọn với cảnh báo mất text/accessibility và kiểm ảnh.

## 5. Lưu trữ và trợ năng

PDF/A-1/2/3/4 theo mục đích cụ thể, font/ICC/metadata/attachment theo profile, validator độc lập như veraPDF và lưu report; không ghi PDF/A chỉ vì có dropdown. PDF/UA/Tagged PDF: heading, reading order, alt text, header của bảng, vi-VN, bookmark, form label, keyboard; validator cộng thử screen reader thủ công. Chuyển đổi có thể mất tương tác, phải preview.

## 6. Tài liệu bảo vệ/cấu trúc lạ

Tệp mã hóa/password chỉ mở khi được cấp quyền; không vượt bảo vệ. PDF portfolio/embedded files, optional layers, 3D, video, XFA, DRM/IRM và PDF hỏng: tách trạng thái View/Edit/Preserve/Unsupported từng tính năng. Đính kèm file thực thi không tự chạy; export qua dialog/quét. Tuân thủ giới hạn in/sao chép và giấy phép.
