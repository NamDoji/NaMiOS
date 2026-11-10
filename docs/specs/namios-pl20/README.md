# NaMiOS — Phụ lục 20: Bộ ứng dụng thiết yếu và trung tâm mở tệp cho người Việt

**Ngày:** 10/11/2026 · **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam · **Trạng thái:** yêu cầu phát triển, không phải danh mục ứng dụng đã hoàn thành.

## Tầm nhìn

Người dùng vừa cài NaMiOS có thể gõ tiếng Việt, duyệt web, liên lạc, soạn văn bản, bảng tính và trình chiếu, đọc/sửa PDF, mở ảnh/âm thanh/video, giải nén tệp, in/scan và nhận trợ giúp mà không phải tự tìm một chuỗi chương trình khác. Tác vụ mở bằng nhấp đôi tệp, kéo thả, phím tắt và menu chuột phải theo thói quen Windows; giao diện tinh tế, yên tĩnh theo bộ nhận diện sen NaMiOS đã duyệt, không sao chép Apple/Microsoft.

## Quy tắc tên thương hiệu

**NaMi** đứng đầu tên mọi ứng dụng **do dự án phát triển, fork/rebrand hợp lệ hoặc đóng gói thành sản phẩm có trách nhiệm vận hành**. Tên hiển thị: NaMiOffice, NaMiPDF, NaMiFiles, NaMiArchive, NaMiImages, NaMiMedia, NaMiBrowser, NaMiType, NaMiSecurity, NaMiDevice, NaMiUpdates, NaMiHelp và NaMiAI; tên kỹ thuật/package và chủ sở hữu mã nguồn vẫn phải công khai chính xác. Không đổi tên Zalo/YouTube/Facebook/WhatsApp, FreeCAD hoặc ứng dụng bên thứ ba thành NaMi khi không có quyền; dùng nhãn “Dịch vụ web chính thức” hoặc “Ứng dụng bên thứ ba” với nguồn và giấy phép.

**Quyết định kiến trúc:** NaMiFiles là cửa vào; hệ MIME và bộ dò định dạng chọn ứng dụng phù hợp. Không viết một “siêu ứng dụng” đọc/sửa mọi định dạng. Mỗi app độc lập và cập nhật riêng, nhưng cùng design system, dialog, thông báo lỗi, quyền file, in và SmartAI. Bộ cài mặc định đủ cho tác vụ phổ biến, còn CAD chỉnh sửa chuyên nghiệp/phần mềm ngành là gói tùy chọn theo giấy phép và chứng nhận.

## Tệp trong phụ lục

1. 01_DANH_MUC_VA_THUONG_HIEU.md — danh mục app cài sẵn, lối web, chính sách tên/giấy phép.
2. 02_MO_TEP_VA_DINH_DANG.md — ma trận Office/PDF/ảnh/vẽ/nén/CAD/media, thao tác và mức hỗ trợ.
3. 03_UX_VA_HANH_TRINH.md — desktop, onboarding, UI thương hiệu, lỗi, trợ năng và SmartAI.
4. 04_KIEN_TRUC_QA.md — routing MIME, bảo mật, codec, cập nhật, thử nghiệm và release gate.
5. 05_PROMPT_CLAUDE_CODE.md — câu lệnh giao việc và kết quả bắt buộc.

Phụ lục này bổ sung Phụ lục 11 (Essentials), 12/Brand UI/UX, 17 (website), 18 (NaMiPDF), NaMiOffice v1/v2; không chép lại toàn bộ chức năng Office/PDF. Trong tài liệu, **P0** là bắt buộc ở bản phổ thông, **P1** là mở rộng sau pilot, **P2** là chuyên sâu. Mỗi hỗ trợ định dạng phải gắn mức: xem, sửa, tạo, chuyển đổi, round-trip, hoặc chưa thử.
