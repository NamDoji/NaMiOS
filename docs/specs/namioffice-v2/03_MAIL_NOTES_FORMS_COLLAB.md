# 03. Hệ sinh thái văn phòng ngoài Writer/Sheet/Slides

## 1. NaMiMail — ứng dụng riêng, không hứa thay Outlook ngay

**F1:** IMAP/SMTP có TLS, OAuth/OIDC khi nhà cung cấp hỗ trợ, nhiều tài khoản, thư mục, tìm kiếm cục bộ, danh bạ CardDAV/CSV/vCard, lịch CalDAV/ICS, lời mời họp, task cơ bản, thông báo, soạn thư tiếng Việt, chữ ký email, đính kèm an toàn, chế độ ngoại tuyến và khôi phục. Kiểm SMTP/IMAP phổ biến bằng tài khoản thử hợp lệ; không lưu mật khẩu thô.

**F2:** S/MIME và PGP khi có UX khóa được kiểm, rules, shared calendar, delegated mailbox, offline sync lớn, enterprise admin. Exchange/Outlook.com/Microsoft 365 qua giao thức/API được cấp quyền: phải kiểm điều khoản, OAuth scopes, giới hạn API, tenant policy, calendar/mail workflow. Không gọi “tương thích Outlook” khi mới chỉ có IMAP đọc mail; khác biệt lịch, danh bạ, task, thư mục chung và add-in phải nêu rõ. Nếu chưa triển khai, NaMiOS có thể tích hợp ứng dụng mail Linux đáng tin và gắn nguồn, không cần viết mới ngay.

## 2. NaMiNotes

**F1:** notebook/section/page, text, list, table, ảnh, ghi âm có quyền, vẽ bằng bút nếu thiết bị hỗ trợ, tìm kiếm tiếng Việt không dấu, offline, export PDF/Markdown/ODF. Dùng định dạng có thể xuất và sao lưu. Đồng bộ giữa thiết bị là F2, chỉ quảng bá sau khi có account, mã hóa khi truyền/lưu, giải quyết xung đột, history và khả năng xóa dữ liệu. Không cam kết nhập/round-trip tệp OneNote độc quyền khi chưa kiểm.

## 3. NaMiForms và NaMiData

Forms F1: tạo câu hỏi, lựa chọn, thang đo, điều kiện nhánh, chế độ anonymous/định danh, giới hạn lần gửi, export CSV/ODS/XLSX, quyền truy cập, consent và retention. F2: quiz/chấm điểm và workflow doanh nghiệp có audit. Dữ liệu học sinh/cơ quan phải được bảo vệ và chỉ thu ở mức cần thiết.

Data F2: bảng/khóa/quan hệ, form nhập, validation, query SQL có quyền, report, import/export CSV/SQL và migration. Nếu đánh giá LibreOffice Base làm nền, phân biệt định dạng và backend; Access ACCDB, Access forms/reports và VBA không tự tương thích. Có lộ trình chuyển dữ liệu thủ công và đối soát.

## 4. Cộng tác và lưu trữ — một sản phẩm dịch vụ riêng

**Giai đoạn một:** file local/SMB/WebDAV theo quyền, locks, cảnh báo conflict, lịch sử bản cục bộ, link chia sẻ qua hệ thống sẵn có; không yêu cầu cloud để dùng Office. **Giai đoạn hai:** một server NaMiCollab hoặc tích hợp nền được phê duyệt, tài khoản/tổ chức, ACL theo tệp, version history, comments/mentions, share link hết hạn, offline sync và conflicts. **Giai đoạn ba:** đồng tác giả thời gian thực cần protocol/CRDT/OT hoặc engine được chứng minh, phân quyền và audit; chỉ gắn “cùng sửa trực tiếp” sau test mất mạng, 2–20 người cùng sửa, merge và không mất nội dung.

Không chuyển trực tiếp tài liệu nhạy cảm sang dịch vụ cloud AI hoặc bên thứ ba. Nếu tích hợp OneDrive/SharePoint/Google Drive, người dùng phải cấp quyền theo scope tối thiểu, thấy nhà cung cấp, chỗ lưu, chính sách dữ liệu; xử lý API thay đổi và token hết hạn. Một file XLSX có quyền IRM/nhãn bảo mật của Microsoft 365 có thể không mở được ngoài client hỗ trợ; không né bảo vệ.

## 5. Add-in, macro và tự động hóa

- **API NaMiOffice:** extension SDK có manifest, version, phạm vi quyền, sandbox, review, signature, revoke và test; hỗ trợ automation trong phạm vi được kiểm bằng Python/UNO hoặc API riêng. Không gọi SDK này là Office.js.
- **VBA:** mặc định không thực thi; bảo toàn project khi có thể; chỉ xem nội dung trong môi trường bảo vệ; danh sách macro tương ứng cần chuyển thủ công và test. Excel/Word VBA có thể gọi COM/Windows API, không thể chuyển bằng thay tên hàm. Không tự động dịch bằng AI rồi chạy.
- **COM/VSTO/ActiveX:** phụ thuộc Windows/Office và quyền cài đặt; không chạy native trên Linux. Nếu một khách hàng bắt buộc, xác định workflow dùng Windows có giấy phép, app web chính thức, VM hoặc remote desktop và chính sách dữ liệu.
- **Office.js add-ins:** phụ thuộc host Office, API requirement set và dịch vụ Microsoft; không giả định chạy trong LibreOffice. Chỉ xem xét adapter cho add-in cụ thể theo hợp đồng, giấy phép và test; không gắn badge tổng quát.
- **Script nội bộ:** có trình soạn, debugger/log theo quyền, test fixtures, dry-run, lịch chạy do người dùng phê duyệt, rollback dữ liệu khi khả thi. Không cho script của file tải về quyền đọc toàn home.

## 6. SmartAI trong NaMiOffice

Trợ lý có thể giải thích công thức, phát hiện lỗi tham chiếu, đề nghị biểu đồ, hỗ trợ viết lại câu, làm dàn ý slide, tìm lệnh và lý giải tại sao tệp Office chưa tương thích. Không thay thế engine tính toán; các con số thuế/kế toán cần đối soát. Tạo bản xem trước diff, phạm vi tệp/ô, quyền truy cập, xác nhận và undo. Bản chạy cục bộ khi phù hợp; cloud chỉ khi người dùng/tổ chức opt-in và biết nội dung gửi. Prompt trong tài liệu là dữ liệu không tin cậy, không thể ra lệnh cho AI đọc tệp khác hoặc gửi mạng.
