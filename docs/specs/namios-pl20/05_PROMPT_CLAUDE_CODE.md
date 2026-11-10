# 05. Prompt giao Claude Code

> Hãy phát triển NaMiOS như một bộ sản phẩm dùng được ngay cho người Việt. Đọc Phụ lục 20 này; chỉ mở Phụ lục 11, 12/Brand UI/UX, 18, NaMiOffice v1/v2 khi đụng chức năng liên quan. Logo ưu tiên là gói sen cân đối được duyệt gần nhất. Đây là yêu cầu, không phải báo cáo tính năng đã có.
>
> **Bước 1 — kiểm kê:** đọc repo/ISO/package manifest hiện tại, xác định distro, desktop, launcher, File Manager, MIME, app mặc định, codec, license/SBOM, update path, font/IME và test. Tạo bảng mỗi tên NaMi: nguồn code, trạng thái “đã cài/chỉ có link/đang làm”, chức năng thật, quyền dùng nhãn/asset, phiên bản, owner. Không tự đổi tên binary/website bên thứ ba thành NaMi.
>
> **Bước 2 — kiến trúc:** chọn cách đóng gói từng ứng dụng, shared design tokens, NaMiFiles routing bằng chuẩn MIME, CapabilityReport và SavePlan. Viết ADR cho NaMiArchive, NaMiImages, NaMiMedia, NaMiDraw/NaMiCAD Viewer; đánh giá reuse upstream có bảo trì trước khi viết mới. Ghi rõ những định dạng chỉ xem hoặc cần phần mềm tùy chọn. .zar là unknown cho đến khi có mẫu/đặc tả.
>
> **Bước 3 — vertical slice chạy thật:** trong VM NaMiOS, từ File Manager nhấp đôi một DOCX, PDF, ZIP, PNG, MP3 và MP4 mở đúng app; thử giải nén, crop ảnh, phát subtitle, in PDF, thay app mặc định, gõ tiếng Việt. Tệp lỗi/đuôi giả và archive traversal bị chặn, file gốc không mất. Có UI đẹp theo brand và screenshot thật, không chỉ mockup.
>
> **Bước 4 — mở rộng:** thêm 7z/RAR đọc theo giấy phép, GIF/TIFF/WebP, MKV/WebM/codec đã được quyền phân phối, SVG/ODG, DXF và DWG theo version. Phân biệt container với codec, viewer CAD với editor CAD, Photoshop/Corel file với định dạng mở. Mỗi feature có fixture, kết quả và cấp View/Edit/Create/Export/Round-trip/Unsupported.
>
> **Bước 5 — app thường dùng:** đóng gói NaMiOffice/NaMiPDF/browser/IME/security/updates; ghim lối web chính thức Zalo/YouTube/Maps/Facebook/TikTok/WhatsApp với badge “Cần mạng” và quyền riêng. Không đăng nhập sẵn, không bundle logo/binary thiếu phép. Profile Cá nhân/Giáo viên/Văn phòng/Kế toán có lựa chọn và có thể bỏ ghim.
>
> **Bước 6 — test và phát hành:** chạy F20-01–F20-12, security fuzz và pilot người Việt. Xuất app-manifest/format-matrix đã ký, license inventory, ảnh UI, bản build, kết quả test và những việc chưa hỗ trợ. Đồng bộ danh mục trên website từ release manifest thật. Không tuyên bố “mọi tệp Windows chạy được” hoặc “full codec/CAD” trước corpus và quyền phân phối.

## Mốc bàn giao

M0 inventory/ADR/design tokens; M1 NaMiFiles và các app P0 phổ thông; M2 định dạng nén/media/ảnh mở rộng, app profile; M3 NaMiDraw/CAD Viewer và workflow chuyên ngành; M4 tối ưu máy yếu, bảo mật, rollout stable. Mỗi mốc phải có build chạy, test và bản ghi rủi ro. Nếu thiếu repo hoặc thiết bị, tạo test harness/manifest và ghi blocker chứng nhận; không giả lập là ISO đã có chức năng.
