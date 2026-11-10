# 01. Chức năng và trải nghiệm NaMiPDF

## 1. Xem và điều hướng — P0

- Mở PDF 1.x/2.0 phổ biến, nhiều tệp/tab/cửa sổ, tập tin từ ổ cứng, USB, SMB/WebDAV được cấp quyền và file đính kèm email; hỗ trợ PDF mật khẩu khi người dùng có quyền. Không tự tải URL ngoài tệp.
- Hiển thị liên tục, trang đơn/đôi, bìa riêng, xoay nhìn, fit width/page, zoom 25–800% hoặc giới hạn theo engine, thumbnails, bookmarks/outline, page labels, history trước/sau, dark UI nhưng không tự đảo màu tài liệu khi in.
- Tìm toàn văn có dấu/không dấu và tùy chọn chính xác, tìm trong annotation/form, tìm theo trang, highlight kết quả; copy text giữ Unicode/dấu tiếng Việt; nhận biết text layer, ảnh quét và ký tự bị thiếu font.
- Chọn/copy văn bản, ảnh và liên kết; link ngoài luôn có xác nhận tên miền, mailto và tệp đính kèm không tự thực thi; phát hiện nội dung script/embedded file và cảnh báo.
- Đọc màn hình bằng reading order/tag nếu có, keyboard shortcuts, high contrast, phóng lớn, text-to-speech qua dịch vụ hệ thống có quyền và tách biệt với OCR. Các tác vụ cơ bản không cần mạng/tài khoản.
- File Manager preview thumbnail sandboxed, mở mặc định bằng NaMiPDF, Recent Files theo tùy chọn quyền riêng tư, print dialog thống nhất NaMiOS.

## 2. Chú thích và review — P0

Highlight, underline, strikeout, sticky note, text comment, callout, textbox, shapes, mũi tên, stamp có nguồn/giấy phép, freehand bút cảm ứng, màu/độ dày/opacity, reply và status resolved; danh sách chú thích lọc theo người/trang/loại, xuất bản tóm tắt nhận xét. Undo/redo, nhiều người gửi file qua lại giữ annotation author/date và thread khi chuẩn cho phép. Có tùy chọn flatten bản sao với cảnh báo không còn sửa chú thích; không flatten bản gốc âm thầm.

## 3. Sửa nội dung thực — P1, có kiểm khả năng

- Chọn/đổi chữ trong content stream, thêm/xóa/di chuyển khối chữ, ảnh, đường/vectơ; đổi font, size, khoảng cách, màu; xóa/thay hình; căn chỉnh đối tượng, crop, watermark, header/footer, đánh số trang.
- Trước khi sửa hiển thị trạng thái **Text PDF / Scan image / Mixed / Signed / Protected** và font có thể nhúng/thay thế; thiếu font hoặc layout có nguy cơ → đề nghị sửa bản gốc trong NaMiWriter hoặc chuyển đổi sang ODT/DOCX với bản sao và so layout.
- Sửa một đoạn không làm thay toàn trang thành ảnh. Reflow chỉ khi cấu trúc đáng tin và người dùng chọn; nếu không, đặt text box với nhãn “thêm nội dung” khác “sửa văn bản gốc”. Không quảng cáo text overlay là thay text cũ khi text cũ vẫn copy/tìm được.
- Hỗ trợ xoay, chèn/xóa/cắt/đổi thứ tự/trích trang, merge/split nhiều PDF, thay trang quét, crop lề, deskew, tăng tương phản, resize, nén ảnh có preview sai khác, giảm dung lượng, kiểm tài liệu sau tối ưu.
- Batch operation P1: đổi tên, merge, OCR, export và watermark trên danh sách tệp; luôn preview số tệp, không ghi đè mặc định, khả năng hủy và báo kết quả từng tệp.

## 4. Xuất, chuyển đổi và in — P0/P1

- P0: xuất PDF từ NaMiOffice theo khổ/lề/trang chọn, bookmark/hyperlink, font theo giấy phép, metadata, nén ảnh, PDF/A chỉ khi validator đạt; in chọn trang/chẵn/lẻ/n trang mỗi tờ, duplex, scale, poster/booklet khi backend hỗ trợ, nhiều bản và collation.
- P1: xuất ảnh PNG/JPEG/TIFF, text UTF-8, HTML đơn giản, ODT/DOCX cho tài liệu có cấu trúc đáng tin, CSV/ODS/XLSX cho bảng sau preview vùng và đối soát; nhập ảnh thành PDF; không cam kết giữ nguyên bảng/định dạng khi chuyển PDF ngược thành Office.
- Print to PDF từ hệ thống gắn NaMiPDF làm viewer; gửi tới máy in qua CUPS/IPP, trạng thái hàng đợi và lỗi rõ như “khổ A3 không hỗ trợ”, “máy offline”, “cần xác thực”. Với tài liệu nhạy cảm, lịch sử in và bản spool tuân thủ quyền/xóa theo chính sách.

## 5. UX tiếng Việt

Menu: Tệp, Xem, Chỉnh sửa, Chú thích, Trang, Biểu mẫu, Ký số, Công cụ, Trợ giúp. Thanh công cụ thích ứng, tối đa ba hành động chính trong từng ngữ cảnh; chế độ người mới có hướng dẫn 1–3 bước, người nâng cao có Properties/Preflight. Ctrl+O/S/Shift+S/P/F/Z/Y, Home/End, PageUp/Down, dấu cộng/trừ zoom; tránh xung đột IME Telex/VNI. Cỡ chữ giao diện, vùng bấm, màu và logo theo NaMiOS design system; light/dark và WCAG 2.2 AA cho UI.

Trạng thái Save: “Đã lưu”, “Đang lưu”, “Bản gốc chưa đổi”, “Sửa sẽ ảnh hưởng chữ ký”, “Một số đối tượng chưa hỗ trợ”; lỗi có mã, vị trí trang/đối tượng, nguyên nhân khả dĩ và nút xử lý. Tự lưu bản nháp và phục hồi sau mất điện, atomic save, file backup và cảnh báo xung đột file trên ổ mạng.
