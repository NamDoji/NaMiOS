# 05. Prompt giao Claude Code triển khai NaMiOffice v2

> Hãy đọc NaMiOS_NaMiOffice_Yeu_Cau_Nang_Cap_v1.zip và phụ lục v2 này. Bạn là kiến trúc sư bộ ứng dụng văn phòng chạy trên NaMiOS. Mục tiêu là người Việt hoàn thành công việc như khi dùng bộ Microsoft Office trên các workflow đã kiểm chứng, không phải tuyên bố tương thích tuyệt đối.
>
> 1. Khảo sát repository, commit/version LibreOffice, nền Linux, gói và CI hiện tại. Lập ma trận từng yêu cầu v1/v2: có sẵn upstream, có một phần, cần patch, cần sản phẩm riêng, không khả thi hoặc cần Windows/Microsoft 365 được cấp phép. Chỉ ra bằng test/file/module cụ thể. Nếu không có repo, giao kế hoạch có thể thực hiện; không báo đã code.
> 2. Xây registry tính năng theo format/phiên bản với C0–C3 và severity. Tạo bộ đọc trước khi Save nhận biết macros, advanced formulas, dynamic arrays, Pivot/Data Model, queries, charts, content controls, media, external links, signatures và IRM. Tệp chưa hỗ trợ phải cảnh báo, giữ bản gốc, không tự loại dữ liệu.
> 3. Ưu tiên vertical slice có build thật: một DOCX dài có bảng/track changes; một XLSX có SUMIFS, XLOOKUP, dynamic array, table, chart, Pivot; một PPTX có master/chart/notes. Mở → sửa nhỏ → lưu bản sao → mở lại trong NaMiOffice và Microsoft Office có giấy phép → report sai khác. Dữ liệu thử có quyền/ẩn danh.
> 4. Triển khai F0 theo ứng dụng trước: UX tiếng Việt, phím tắt, mẫu, in/PDF, công thức và chart cốt lõi, atomic save/recovery. Rồi F1 theo dữ liệu pilot. Mail/Notes/Forms/Data/Collab là đề án riêng, không làm giả bằng nút giao diện; đề xuất reuse phần mềm Linux có giấy phép phù hợp trước khi viết mới.
> 5. Không chạy VBA, COM, ActiveX hay external links của tài liệu không tin cậy. Không mô tả Office.js add-ins, Power Query, Power Pivot, Exchange, SharePoint, OneDrive hoặc đồng tác giả thời gian thực là đạt khi chưa có kiểm thử đúng workflow và quyền sử dụng.
> 6. Mỗi PR cung cấp fixture, kỳ vọng, test tự động, kết quả đối chiếu, ảnh chụp khi layout, trạng thái C0–C3, tác động license/security, update/rollback và known limitations. Báo các P0 blocker; không dùng screenshot mockup để nghiệm thu engine.
> 7. Giao lại cho chủ dự án: mã nguồn chạy được, bản cài, ma trận hiện trạng, danh sách chức năng theo F0/F1/F2, số liệu test thực, khả năng tương thích theo phiên bản, rủi ro, lộ trình tiếp theo và tài liệu người dùng bằng tiếng Việt.

## Công việc đầu tiên nên yêu cầu Claude Code hoàn thành

Trong repo thực, tạo báo cáo baseline và một nhánh feature nhỏ chứng minh pipeline “mở an toàn → nhận diện tính năng rủi ro → chỉnh sửa → lưu bản sao → so kết quả”. Chỉ sau khi vertical slice đạt mới mở rộng số hàm, biểu đồ và ứng dụng. Đây là điểm kiểm tra quan trọng để tránh có nhiều màn hình đẹp nhưng tài liệu thật không dùng được.
