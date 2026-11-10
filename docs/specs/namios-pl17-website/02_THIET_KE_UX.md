# 02. Thiết kế thương hiệu và UX website

## 1. Art direction

Hình ảnh nhận diện lấy **logo sen cân đối NaMiOS đã được chủ dự án duyệt** làm nguồn duy nhất; không tái tạo logo bằng AI hoặc tự chọn phiên bản trống đồng/Khuê Văn Các. Tài liệu asset nguồn: NaMiOS_Logo_Sen_Can_Doi_Full_Pack.zip; kiểm chính xác bản biểu tượng, wordmark, khoảng trống bảo vệ, nền tối/sáng và giấy phép trước khi xuất web. Màu nền sáng dịu, chữ navy đậm, đỏ sen là điểm nhấn, vàng dùng tiết chế; đối chiếu mã màu chính xác với pack logo, không lấy màu tùy hứng từ ảnh. Phong cách tối giản, chất lượng hoàn thiện cao, chuyển động nhẹ; tạo cá tính riêng thay vì sao chép giao diện Apple.

Ảnh chính: desktop NaMiOS chạy thật trong màn hình laptop/desktop, crop có chủ đích, không giả mạo tính năng. Thư viện phụ: ảnh phong cảnh Việt Nam đã có quyền, nén AVIF/WebP với fallback, alt text cụ thể, bản đồ lãnh thổ không dùng ảnh AI. Hình nền thiên nhiên có thể làm điểm nhấn, nhưng nội dung và nút phải rõ trên mọi ảnh. Không tự lấy ngẫu nhiên ảnh web.

## 2. Design tokens phải bàn giao

- Color: navy-950, navy-700, lotus-600, lotus-500, gold-500, surface, border, text-muted, semantic success/warning/error; cặp chữ/nền đạt tương phản theo WCAG 2.2 AA.
- Typography: font sans hỗ trợ đầy đủ dấu tiếng Việt và quyền web embedding; tối đa hai họ chữ; body 16–18px, line height 1.5–1.7; H1 responsive khoảng 40–72px desktop và 36–48px mobile; không cố định khiến tràn chữ.
- Spacing: hệ 4/8px, max content width 1200–1280px, gutters 20–32px, section spacing 64–120px; touch targets theo WCAG 2.2 AA; focus ring rõ.
- Component: button primary/secondary/text, nav/dropdown/mobile menu, status badge, card, accordion FAQ, search/filter, release table, download selector, breadcrumb, alert, form đăng ký, skeleton/error/empty state.
- States cho mỗi component: default, hover, focus, pressed, disabled, loading, success, error; tạo tài liệu thành một trang style guide hoặc Storybook tương đương.

## 3. Wireframe bằng lời

**Desktop 1440px:** header gọn trên cùng, wordmark trái, nav giữa, CTA phải. Hero chia 55% copy/CTA và 45% screenshot sản phẩm, phía dưới các trust facts xác minh được. Các section xen kẽ ảnh và văn bản, nhiều khoảng thở. Footer 4 cột với license/privacy/contact. **Mobile 390px:** logo và menu, H1 tối đa ba đến bốn dòng, CTA xếp dọc, screenshot tỷ lệ rõ, card một cột, bảng ma trận chuyển thành card có nhãn hoặc cuộn ngang có chỉ báo. Không có sticky CTA chiếm quá 20% chiều cao màn.

Desktop demo tương tác dạng “xem giao diện” có hotspot: menu ứng dụng, Office, Device Hub, SmartAI; chỉ dùng nếu mô phỏng được ghi nhãn, không giống ảnh chụp thật gây hiểu nhầm. Tắt animation với prefers-reduced-motion; không autoplay video có âm thanh. Tải poster frame trước, video lazy-load khi bấm.

## 4. Luồng người dùng phải thử

1. Người mới: trang chủ → hiểu NaMiOS → so sánh app web/native → tra máy → tải hoặc nhận tin; tối đa 4 bước tới trang phù hợp.
2. Kế toán: tìm MISA/XLSX → thấy phiên bản/feature đã thử và chưa thử → quyết định pilot hay giữ Windows → tải tài liệu đối soát.
3. Giáo viên: xem gõ tiếng Việt/NaMiOffice/in/máy chiếu → Live USB → hướng dẫn in.
4. IT: tra model máy in và chipset mạng → lọc chức năng, ngày test, build → tải release notes/checksum.
5. Người dùng gặp lỗi: từ trang cài đặt/FAQ → tìm mã lỗi → hướng dẫn tiếng Việt → báo lỗi có log đã loại dữ liệu riêng tư.

## 5. Trợ năng và bản địa hóa

Điều hướng bằng bàn phím, skip link, focus không bị che, landmark hợp lý, label/form validation bằng văn bản, heading đúng thứ tự, alt text, caption/transcript, thông báo lỗi không chỉ dựa màu. Kiểm screen reader, phóng 200–400%, 320px, dark/light và mạng chậm. Ngôn ngữ vi/English, URL ổn định, dịch thuật qua message catalog, không dịch tên app tùy tiện. Tìm kiếm không dấu, lỗi gõ thường gặp, nhưng không biến tên phần mềm chưa thử thành “đã hỗ trợ”.
