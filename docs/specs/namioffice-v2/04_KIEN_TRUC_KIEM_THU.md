# 04. Kiến trúc triển khai và cổng nghiệm thu

## 1. Tách thành phần

LibreOffice upstream được pin phiên bản → nhánh NaMiOffice nhỏ và theo dõi patch → Writer/Calc/Impress core → compatibility adapters cho OOXML/ODF → Compatibility Inspector → UI tiếng Việt và tích hợp NaMiOS. Mail/Notes/Forms/Data/Collab là gói/dịch vụ tách rời, giao tiếp qua API/file contract; không nhét tất cả vào nhân LibreOffice. Update Center có thể cập nhật và rollback từng gói; file người dùng không bị cuốn theo rollback.

Khởi đầu bằng audit upstream: ghi đúng tính năng đã có trong phiên bản pin, test trước khi fork. Chỉ viết thêm engine nếu test chỉ ra sai khác; ưu tiên đóng góp upstream khi phù hợp. Patch phải đi kèm fixture từ Microsoft Office có giấy phép hoặc tệp người dùng có quyền, so kết quả round-trip chứ không chỉ smoke test.

## 2. Fidelity pipeline

File sniff và validation → sandbox parser → inventory macro/OOXML parts/external links/signature/IRM → chấm rủi ro C0–C3 → import → thao tác người dùng → pre-save diff/cảnh báo → atomic save vào bản mới khi nguy cơ → reopen và kiểm. Unknown parts chỉ giữ khi có thể bảo toàn an toàn; nếu không, yêu cầu người dùng lưu bản sao. Tệp được ký không giữ nhãn “còn hợp lệ” sau chỉnh sửa. Không cố vượt mật khẩu/IRM.

Workbook import tạo feature map: formula grammar/functions, cached values, chart and pivot metadata, structured table, data model, queries, custom XML, macros. File có Power Query hoặc data model chưa hỗ trợ phải hiển thị ngay cả khi các ô hiện tại vẫn nhìn đúng. “Mở được” không đồng nghĩa “refresh được” hoặc “lưu lại nguyên”.

## 3. Bộ đo theo workflow

| Loại | Corpus tối thiểu pilot | Đo |
|---|---|---|
| Writer | 100 DOCX đa ngành, 20 tài liệu dài/biểu mẫu | text, structure, page/paragraph layout, comments, track changes, print/PDF, round-trip |
| Sheet | 150 XLSX, 50 file kế toán/giáo dục ẩn danh, 20 dynamic/Pivot/chart | ô, kiểu, công thức, cached vs recalc, pivot refresh, chart data/layout, VND và ngày |
| Slides | 60 PPTX, 20 bài giảng có animation/media | đối tượng, slide render, notes, timing, projector, PDF |
| Mail/Notes/Forms | mock server + tài khoản thử, dữ liệu không nhạy cảm | sync, conflict, OAuth, offline, export, mất mạng và revoke |
| Security | fuzz OOXML, file hỏng, ZIP bomb, script, external link | 0 thực thi tự động, 0 gửi mạng ngoài ý muốn, recovery và thông báo |

Tỷ lệ là mức corpus đề xuất, không đại diện cho toàn bộ tài liệu Office. Mỗi bản release công khai dashboard theo feature và version. Gate tuyệt đối: không mất dữ liệu không cảnh báo, không sai tổng kiểm soát của fixture kế toán, không tự chạy macro hoặc mở kết nối ngoài, không ghi đè bản gốc khi chuyển đổi rủi ro.

## 4. Chứng nhận theo cấp

**Core Ready:** 10 workflow người dùng mới có thể hoàn thành offline; 100% fixture F0 pass theo ngưỡng riêng, các C2/C3 được nhận diện và cảnh báo. **Professional Ready:** Pivot, dynamic array, tài liệu dài, present media, mẫu doanh nghiệp đạt corpus pilot; có hướng dẫn IT. **Enterprise Ready:** chính sách quản trị, mail/collab đã vận hành và audit, backup/restore, key management, SLA bảo mật và test triển khai nhiều máy. Không đặt badge Enterprise chỉ vì có UI mail.

Các chỉ số phải công bố separately: fidelity DOCX trang, XLSX giá trị/công thức/chart, PPTX đối tượng/animation, tỷ lệ không mất dữ liệu, tốc độ mở/lưu, crash rate, accessibility, update rollback. Chỉ số tổng hợp không được che P0 lỗi kế toán hoặc chữ ký.

## 5. Kế hoạch công việc

M0 pin LibreOffice, audit license/trademark/font, inventory hiện trạng, lập test harness. M1 polish NaMiWriter/Sheet/Slides F0 và Save Safety. M2 bảng/tính toán/biểu đồ/tài liệu dài F1, pilot. M3 thử Mail/Notes (dùng phần mềm Linux sẵn có nếu phù hợp); F2 Data/Forms chỉ khi có nhu cầu và đội vận hành. M4 dịch vụ collab và automation SDK, data model/Power Query subset theo corpus thực. Mọi mốc phải có build, tests, ảnh/fixture, bug và quyết định go/no-go; không dự đoán ngày phát hành khi chưa có repo/nhân lực.

## 6. Nguồn chính thức để kỹ sư đối chiếu

- LibreOffice licensing: https://www.libreoffice.org/licenses/
- LibreOffice VBA support: https://help.libreoffice.org/latest/en-US/text/sbasic/shared/vbasupport.html
- Microsoft Office Add-ins/API requirement sets: https://learn.microsoft.com/en-us/office/dev/add-ins/overview/office-add-ins
- Microsoft Excel function catalog: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb
- Microsoft Power Query and Power Pivot: https://support.microsoft.com/en-us/excel/how-power-query-and-power-pivot-work-together
- Microsoft Office Open XML standards: https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oe376/

Kiểm lại tài liệu gốc và bản LibreOffice pin trước khi khẳng định một tính năng đã hỗ trợ.
