# NaMiOffice — phụ lục nâng cấp v2: mục tiêu bộ Office đầy đủ

**Ngày:** 10/11/2026 · **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam · **Loại:** phụ lục mới, đọc sau NaMiOS_NaMiOffice_Yeu_Cau_Nang_Cap_v1.zip; không thay thế tài liệu v1.

## Mục tiêu và cách hiểu

Người dùng muốn bộ công cụ làm việc quen thuộc và đầy đủ như họ đang dùng Microsoft Office: soạn thảo, bảng tính, trình chiếu, email, ghi chú, biểu mẫu, PDF, tự động hóa và cộng tác. NaMiOffice phát triển từ LibreOffice cho ba ứng dụng đầu và bổ sung các ứng dụng/dịch vụ độc lập khi cần. Mục tiêu **tương đương tác vụ theo kiểm thử**, không sao chép mã, giao diện pixel, nhãn hiệu hoặc công nghệ độc quyền. Cùng tên tính năng không đồng nghĩa cùng ngữ nghĩa; phải đo bằng tệp, kết quả và người dùng thực.

Không thể trung thực cam kết “đầy đủ 100% Microsoft Office” bằng một bản fork LibreOffice: VBA/COM/VSTO, Office.js, Power Query/Power Pivot, tích hợp Exchange/OneDrive/SharePoint, đồng tác giả và cơ chế bảo vệ tài liệu là các hệ sinh thái riêng. Nếu chưa xây được, ứng dụng phải mở an toàn, giữ dữ liệu khi có thể, cảnh báo chính xác và cung cấp tuyến thay thế hợp pháp.

## Gói tài liệu

1. 01_PHAM_VI_VA_MA_TRAN.md — bản đồ sản phẩm, cấp độ tương thích và ưu tiên.
2. 02_WRITER_SHEET_SLIDES.md — checklist chức năng chuyên sâu và tiêu chí nghiệm thu.
3. 03_MAIL_NOTES_FORMS_COLLAB.md — email, ghi chú, biểu mẫu, dữ liệu và cộng tác.
4. 04_KIEN_TRUC_KIEM_THU.md — kỹ thuật tương thích, an toàn và cổng phát hành.
5. 05_PROMPT_CLAUDE_CODE.md — lệnh triển khai và đầu ra.

**Quyết định quan trọng:** NaMiOffice là bộ ứng dụng độc lập, cài sẵn và cập nhật riêng với NaMiOS. Dùng nhãn NaMiWriter/NaMiSheet/NaMiSlides; các ứng dụng bổ sung chỉ mang tên NaMiMail/NaMiNotes/NaMiForms khi đã có sản phẩm thật. “Miễn phí” của NaMiOffice không cấp giấy phép Microsoft 365 hoặc dịch vụ bên thứ ba.

## Quy ước

- Mức tính năng F0: dùng thường ngày, bắt buộc cho bản đầu; F1: chuyên nghiệp, sau pilot; F2: nâng cao, phụ thuộc dữ liệu sử dụng và nguồn lực.
- Tương thích C0: kết quả và round-trip xác minh; C1: đáp ứng chức năng, sai khác được giới hạn; C2: một phần, cảnh báo; C3: không thực hiện, có fallback. Cấp độ theo **tệp/phiên bản/tính năng**, không theo tên sản phẩm.
- Các mục trong backlog là **yêu cầu phát triển**, không phải tuyên bố chức năng đã hoàn tất.
