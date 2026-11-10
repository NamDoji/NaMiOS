# NaMiOS — Phụ lục 18: NaMiPDF cài sẵn

**Ngày:** 10/11/2026 · **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam · **Trạng thái:** yêu cầu sản phẩm; chưa phải tuyên bố NaMiPDF đã được phát triển hay chứng nhận.

## Quyết định

NaMiPDF là **ứng dụng desktop độc lập, cài sẵn trong NaMiOS**, dùng ngoại tuyến cho tác vụ cơ bản, là ứng dụng mặc định mở PDF và có thể cập nhật riêng qua NaMi Update Center. NaMiWriter/Sheet/Slides xuất PDF sang cùng một pipeline nhưng không thay thế editor PDF. NaMiPDF có bốn chế độ hiển thị rõ: **Xem**, **Chú thích**, **Sửa nội dung**, **Biểu mẫu & Ký số**; thêm các quy trình **OCR**, **Sắp xếp trang**, **Che dữ liệu**, **Xuất/chuyển đổi**.

“Full chức năng” ở đây là danh mục mục tiêu và tiêu chí nghiệm thu đầy đủ cho nhu cầu phổ thông, văn phòng, giáo dục và hành chính Việt Nam. PDF được thiết kế để giữ cách trình bày; một số trang thiếu font, là ảnh quét, có chữ ký, mã hóa hoặc cấu trúc phức tạp sẽ không thể sửa như tài liệu Word mà vẫn giữ nguyên mọi thứ. NaMiPDF phải phát hiện, thông báo mức tin cậy và lưu bản sao an toàn, không quảng cáo khả năng “sửa mọi PDF 100%”.

## Gói tài liệu

1. 01_TINH_NANG_UIUX.md — thao tác người dùng và toàn bộ nhóm chức năng.
2. 02_PDF_CHUYEN_SAU.md — OCR, biểu mẫu, chữ ký, PDF/A, PDF/UA, redaction.
3. 03_KIEN_TRUC_BAO_MAT.md — pipeline, tích hợp NaMiOS, giấy phép và SmartAI.
4. 04_KIEM_THU_PHAT_HANH.md — corpus, bộ kiểm thử, cổng phát hành và lộ trình.
5. 05_PROMPT_CLAUDE_CODE.md — câu lệnh thực thi.

**Quan hệ tài liệu:** phụ lục mới bổ sung NaMiOffice v1/v2 và các phụ lục NaMiOS về thiết bị, Update Center, SmartAI; không yêu cầu Claude Code đọc lại mọi phụ lục không liên quan. Quy ước P0 = trước bản dùng rộng rãi; P1 = bản chuyên nghiệp; P2 = chuyên sâu. “Đạt” phải có tệp thử, kết quả mở/lưu lại và bằng chứng.
