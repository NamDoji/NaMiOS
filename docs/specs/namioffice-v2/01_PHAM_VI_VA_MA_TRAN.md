# 01. Bản đồ sản phẩm và ma trận chức năng

## 1. Những gì người dùng thực sự kỳ vọng

| Nhu cầu | Thành phần NaMiOffice | Nền triển khai | Mốc |
|---|---|---|---|
 Word: văn bản hành chính, hợp đồng, giáo án, CV | NaMiWriter | LibreOffice Writer + patch/UX | F0/F1 |
 Excel: bảng, công thức, chart, dữ liệu, sổ kế toán | NaMiSheet | LibreOffice Calc + engine/adapters | F0/F1/F2 |
 PowerPoint: bài giảng, báo cáo, thuyết trình | NaMiSlides | LibreOffice Impress + renderer/UX | F0/F1 |
 Outlook: thư, lịch, danh bạ, tác vụ | NaMiMail | Ứng dụng riêng tích hợp chuẩn mail/calendar; không là tính năng LibreOffice | F1 |
 OneNote: sổ ghi chú, mực số, tìm kiếm | NaMiNotes | Ứng dụng riêng, định dạng mở, đồng bộ tùy chọn | F1 |
 Forms: thu thập phản hồi, kiểm tra | NaMiForms | Dịch vụ/form app riêng, quyền dữ liệu | F1/F2 |
 Access: database desktop, form, báo cáo | NaMiData | Đánh giá LibreOffice Base + backend riêng; không giả định tương thích ACCDB/Access VBA | F2 |
 PDF: xem, xuất, ký, chú thích | NaMiPDF | Thành phần riêng + pipeline Office | F0/F1 |
 Lưu đám mây và cộng tác | NaMiDrive/Collab | Dịch vụ có tài khoản, server, bảo mật và vận hành riêng | F2 |

Không gọi bộ này là “Microsoft Office miễn phí”. Trên website và App Center, chỉ app đã phát hành mới có chữ “có sẵn”.

## 2. Lộ trình khả thi

**L0 — thay thế tác vụ phổ thông:** mở/sửa/lưu DOCX/XLSX/PPTX, ODF, PDF; giao diện tiếng Việt và phím tắt quen; công thức/bảng/chart cốt lõi; in; không mất dữ liệu. **L1 — chuyên nghiệp:** layout khó, track changes, mail merge, structured tables, Pivot, dynamic arrays, presenter view, cộng tác qua file/đồng bộ có xung đột, email/notes cơ bản. **L2 — chuyên sâu:** Power Query tương đương theo pipeline mở, model dữ liệu nhiều bảng, add-in SDK, tự động hóa, cộng tác thời gian thực và dịch vụ quản trị. **L3 — tính năng độc quyền không thể chứng nhận chung:** VBA/COM/VSTO, Office.js add-in gốc, IRM/nhãn nhạy cảm từ Microsoft 365, SharePoint/Exchange workflow riêng; chỉ hỗ trợ bằng triển khai cụ thể có quyền và test, hoặc tuyến Windows/Microsoft 365 chính thức.

## 3. Định nghĩa “đầy đủ” phải đo

Mỗi feature có ID, mô tả tác vụ, ứng dụng, mức F, nguồn tài liệu đầu vào, hành vi kỳ vọng, trạng thái hiện có của LibreOffice phiên bản được pin, phần cần viết thêm, trạng thái C0–C3, bộ fixture, người chịu trách nhiệm, bug và ngày kiểm. Một tính năng chỉ được đánh dấu “Đã hỗ trợ” khi có unit/integration, round-trip và thử tương tác; “Có nút menu” chưa đủ.

Phân loại theo từng bản Office/định dạng: OOXML Transitional/Strict, DOC/XLS/PPT cũ, ODF, PDF, CSV, macro-enabled, template, password protected. Không suy từ DOCX mở được rằng DOCM hay DOCX có content controls cũng đạt. Tệp cụ thể phát hiện nội dung rủi ro trước khi lưu; giữ bản gốc và quyền xem/Save As.

## 4. Nguyên tắc UX

Trang đầu cho “Tạo văn bản / Bảng tính / Trình chiếu / Mở tệp”; quick access Save/Undo/Redo; các tab lệnh được tổ chức tương tự thói quen làm việc nhưng kiểu dáng và icon riêng; tìm lệnh bằng tiếng Việt, tên tiếng Anh và từ đồng nghĩa. Menu chuột phải, bàn phím, trợ năng và touch; status bar hiển thị trang/số từ hoặc ô/tổng/zoom. Nâng cấp từ Windows không phải học lại thao tác cơ bản. Không chép UI pixel của Microsoft.

Toàn bộ có mẫu cho văn bản hành chính, bài giảng, bảng điểm, báo cáo doanh nghiệp, thư mời; mẫu công bố nguồn, giấy phép và ngày cập nhật. Bộ gõ Telex/VNI, số VND, ngày dd/MM/yyyy, dấu tiếng Việt, font hợp pháp và in A4 là kiểm thử F0.

## 5. Không phụ thuộc tài khoản

Soạn/sửa/lưu/in ngoại tuyến là mặc định. Mail, cloud/collab và AI cloud là gói tùy chọn với tài khoản và đồng ý rõ. Không yêu cầu đăng ký chỉ để mở tệp. Người dùng có thể chọn ODF làm định dạng mặc định, hoặc giữ định dạng gốc khi nhận tệp OOXML.
