# Prompt Claude Code — thay logo NaMiOS sau khi duyệt

Anh là kỹ sư thiết kế thương hiệu và tích hợp Linux cho NaMiOS. Đọc README và asset SVG v2. Khảo sát mã nguồn, phiên bản desktop/installer/Plymouth/bootloader, hệ icon, website và bản nhận diện cũ; lập bảng chỗ dùng logo có đường dẫn, asset, kích thước, màu nền, owner. Chưa có repo thì chỉ báo nơi cần thay và cách kiểm, không báo đã hoàn thành.

1. Bảo tồn nguồn SVG, xuất PNG/ICO đúng kích thước và tối ưu bản 16/24/32 từ `namios-symbol-small.svg`; không scale trực tiếp từ master chi tiết. Chữ lockup kiểm font có quyền phân phối; đổi sang path trong bản giao production khi cần.
2. Tạo brand component trung tâm với light/dark/mono và safe area. Thay đồng bộ màn cài, boot splash phần mềm kiểm soát được, đăng nhập, menu, About, cập nhật, trợ giúp và web; không thay logo firmware/UEFI của nhà sản xuất. App icon đế chỉ dùng ở nơi cần icon ứng dụng.
3. Kiểm các asset trống/đường dẫn gãy, màn HiDPI, light/dark, wallpaper sáng/tối, 16–1024 px, máy đời cũ. Chạy visual regression và đối chiếu bản v1; QA đặc biệt ở 16/24 px.
4. Cung cấp PR có ảnh trước/sau trên màn thật, mapping old → new, script xuất asset, kiểm giấy phép và nhãn hiệu trước phát hành công khai, cách rollback. Không tự đổi logo chính thức trên máy người dùng trước khi có quyết định duyệt brand và phiên bản phát hành.
