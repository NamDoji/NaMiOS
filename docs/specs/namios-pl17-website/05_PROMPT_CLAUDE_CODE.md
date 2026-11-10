# 05. Prompt giao Claude Code

Hãy sao chép nguyên phần dưới và đính kèm thư mục phụ lục này cùng các asset logo đã được duyệt:

> Bạn là product designer, content strategist và senior web engineer của NaMiOS. Xây website giới thiệu và tải NaMiOS bằng tiếng Việt, chuẩn quốc tế về chất lượng thiết kế, trợ năng, hiệu năng và minh bạch. Đọc các file 01–04 của phụ lục này trước; đối chiếu NaMiOS Phụ lục 07/11/15/16, NaMiOffice Spec v1 và logo sen cân đối đã duyệt. Không dùng logo hoặc bản mockup sai phiên bản.
>
> Trước khi code, khảo sát repo, domain, framework, brand assets, release manifests, ISO/URL tải, licenses và ma trận kiểm thử. Tạo bảng “Đã xác minh / Chưa xác minh / Không thể công bố”. Nếu chưa có ISO hoặc link chính thức, triển khai pre_release với CTA nhận tin/xem tiến độ, **không tạo nút tải giả**. Form nhận tin chỉ nối dịch vụ gửi mail khi cấu hình và chính sách privacy đã có; nếu chưa, cho chế độ demo không thu email và ghi rõ.
>
> Thiết kế desktop/mobile hoàn chỉnh: home, apps, NaMiOffice, compatibility, devices, SmartAI, security, download, install, FAQ/docs, about, privacy. Ưu tiên home/download/compatibility/install chạy thật trước. Logo chuẩn, hình ảnh có provenance, screenshot build thật hoặc nhãn mockup, bộ component/tokens, trạng thái loading/empty/error và focus rõ. Viết copy tiếng Việt từ file 01, tránh tuyên bố mọi app Windows hoặc mọi thiết bị hoạt động.
>
> Tạo content schema, release manifest schema, app/device compatibility records và claim evidence. App có native/web/Wine/Windows-only khác nhau. Render trạng thái, phiên bản, ngày kiểm, hạn chế và filter. Tất cả CTA/download/structured data lấy từ manifest đã duyệt; việc chuyển pre_release sang beta/stable phải qua CI gate file ISO, hash, chữ ký, release notes, thiết bị và giấy phép. Không tự động publish.
>
> Triển khai bảo mật, SEO, WCAG 2.2 AA và Core Web Vitals theo file 04. Viết test E2E cho trạng thái chưa phát hành và có bản phát hành bằng fixture giả, test search app/model, link, form, bàn phím, responsive, kiểm claim/manifest. Chạy build/lint/tests và báo số liệu thực tế. Để người dùng xem bản preview/staging trước khi công bố.
>
> Bàn giao: source, URL preview nếu có môi trường, screenshot ở 390px/1440px, hướng dẫn chạy và quản trị, asset inventory/license, report accessibility/performance/security, danh sách blocker/known issues và checklist chuyển trạng thái download. Nếu không có repo hoặc môi trường deploy, tạo source cục bộ và hướng dẫn khởi chạy; ghi rõ chưa triển khai thực tế.

## Các dữ liệu chủ dự án cần chốt trước khi bật tải

1. Domain chính thức và hạ tầng tải/CDN.
2. ISO đã được ký, khóa công khai, checksum và release notes.
3. Yêu cầu máy tối thiểu đã kiểm, danh sách thiết bị/app đã thử.
4. Bộ logo sen cuối cùng, ảnh screenshot sản phẩm thật, quyền sử dụng wallpaper/font.
5. Email hỗ trợ/bảo mật, chính sách quyền riêng tư, chủ thể pháp lý và kênh cập nhật.

Các mục này **không chặn việc thiết kế và xây bản preview pre-release**. Chúng chặn việc công bố download/beta/stable như một sản phẩm đã sẵn sàng.
