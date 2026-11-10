# 03. Kiến trúc, tích hợp NaMiOS và bảo mật

## 1. Các lớp

NaMiPDF UI → Document Inspector (sniff, permission, chữ ký, form, annotation, OCR, PDF/A/UA) → PDF core (parse/render/text extraction/object graph/edit/save) → feature engines (forms, OCR, redaction, signature, conversion, preflight) → NaMiOS portals (file/print/scanner/credential/update/SmartAI). Tách parser/renderer file không tin cậy trong worker không mạng, giới hạn tài nguyên.

Không lấy LibreOffice Draw làm toàn bộ editor nếu mở/lưu làm mất annotation, form, chữ ký hoặc incremental updates. Chọn core bằng corpus và audit license: QPDF phù hợp thao tác cấu trúc/encryption nhưng không phải editor UI hoàn chỉnh; OCRmyPDF/Tesseract cho OCR; renderer/editor khảo sát riêng. MuPDF có lựa chọn AGPL hoặc thương mại nên phải quyết định nghĩa vụ trước tích hợp. Nhiều thư viện có thể phối hợp qua interface và pipeline kiểm chứng; không gán “full feature” theo một dependency.

## 2. Xử lý file an toàn

Sniff thay vì tin phần mở rộng; kiểm kích thước/trang/object, xref loop, malformed font/image, decompression bomb, embedded file, JavaScript và link ngoài. Sandbox parser, budget CPU/RAM/time, fuzz corpus; hủy tác vụ không hỏng file. Read-only khi tài liệu không chắc an toàn, không tự gửi PDF hoặc text ra Internet.

Save bằng temp + fsync + rename nguyên tử trên local; SMB/cloud có lock/version conflict và Save As khi không đảm bảo. Tài liệu ký số có nhánh riêng cho incremental update theo permission; không thay bytes đã ký và không nói “còn hợp lệ” khi chưa kiểm. Backup/restore, re-open validation, checksum. Tệp chính sách không có quyền ghi thì chỉ xem.

## 3. Tích hợp hệ điều hành

Cài sẵn, MIME mặc định, mở từ File Manager/email/browser, Recent Files theo lựa chọn, thumbnail sandboxed, update/rollback riêng qua NaMi Update Center. Export PDF từ NaMiWriter/Sheet/Slides qua pipeline thống nhất. Scan từ Device Hub; in CUPS/IPP với lỗi hàng đợi rõ; USB token qua service quyền thiết bị. SmartAI giải thích lỗi, tóm tắt theo quyền, sửa OCR có preview, đề nghị vùng che nhưng không tự áp dụng redaction/ký số hoặc upload. Nội dung PDF có thể chứa prompt độc hại, luôn coi là dữ liệu không tin cậy.

## 4. Bảo mật và quyền riêng tư

Tắt PDF JavaScript, auto-open attachment và network fetch mặc định; link hiện đích trước khi mở. Fuzz font/image/parser/OCR/signature, SBOM, security review, cập nhật gói ký số. Xóa bản tạm/OCR cache/thumbnail/search index cho tệp nhạy cảm theo chính sách; không đưa nội dung vào telemetry. Audit license từng thư viện, font, OCR model, codec, công cụ ký và giữ notices/source obligations; không gói khóa riêng hoặc binary bên thứ ba khi thiếu quyền.
