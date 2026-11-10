# NaMiOS — Phụ lục 17: Website giới thiệu và tải hệ điều hành

**Phiên bản:** 1.0 · **Ngày:** 09/11/2026 · **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam  
**Phạm vi:** tài liệu mới, độc lập để giao Claude Code thiết kế, viết nội dung, phát triển và kiểm thử website. Không phải xác nhận NaMiOS đã có bản ISO phát hành.

## Tuyên ngôn

**NaMiOS — Hệ điều hành dành cho người Việt, dễ dùng ngay từ ngày đầu.** Trải nghiệm đẹp và quen thuộc; bộ công cụ thiết yếu, tiếng Việt, thiết bị và hỗ trợ thông minh trong một nơi; miễn phí theo điều kiện giấy phép được công bố.

Website phải cho người xem hiểu trong 30 giây: NaMiOS là gì; ai có thể dùng; khác biệt; ứng dụng nào thực sự cài sẵn và ứng dụng nào là dịch vụ web; máy in, Wi-Fi, Bluetooth và phần mềm Windows được hỗ trợ ở mức nào; cách kiểm tra máy và cài an toàn. Hình ảnh sản phẩm chỉ dùng ảnh chụp build chạy thật, hoặc ghi nhãn rõ “bản thiết kế dự kiến”.

## Quy tắc không được đánh đổi

1. **Không bịa bản phát hành, lượt tải, đối tác, chứng nhận, đánh giá khách hàng hoặc mức tương thích.** Nội dung lấy từ release manifest và ma trận kiểm thử. Một chức năng ở trạng thái “Đang phát triển” không được mô tả như đã có.
2. **Không ghi “chạy mọi phần mềm Windows” hay “mọi máy in, mọi chuẩn Bluetooth/Wi-Fi”.** Chỉ công bố phần mềm, phiên bản và chức năng/model đã kiểm thử; đưa lối kiểm tra và hỗ trợ.
3. **Không gắn logo/nhãn Microsoft, Apple, Zalo, Facebook... để ám chỉ hợp tác.** Tên sản phẩm bên thứ ba chỉ dùng theo nhu cầu mô tả, có nguồn chính thức và phân biệt web/native/Wine; icon chỉ khi có quyền.
4. **Không đăng nút tải giả.** Trước khi có ISO hợp lệ, CTA là “Nhận thông báo khi có bản thử nghiệm” và “Xem tiến độ”. Khi có release, CTA dẫn tới URL release chính thức với SHA-256, chữ ký, ghi chú phát hành và kiểm tra tương thích.
5. **An toàn chuyển máy:** khuyến nghị sao lưu, kiểm tra driver và ứng dụng bắt buộc, thử Live USB trước khi thay Windows. Không hướng dẫn xóa dữ liệu mà thiếu bước kiểm tra.

## Tập tin trong gói

- `01_CHIEN_LUOC_NOI_DUNG.md`: cấu trúc trang, thông điệp, copy gợi ý.
- `02_THIET_KE_UX.md`: ngôn ngữ thị giác, giao diện responsive, tương tác.
- `03_DOWNLOAD_TUONG_THICH.md`: phát hành, trình kiểm tra, dữ liệu và bảo mật.
- `04_KY_THUAT_NGHIEM_THU.md`: kiến trúc web, SEO, accessibility, hiệu năng, QA.
- `05_PROMPT_CLAUDE_CODE.md`: lệnh làm việc và bàn giao.

**Nguồn nội bộ đối chiếu:** Phụ lục 07 thiết bị/Office, 11 ứng dụng thiết yếu, 15 cập nhật, 16 SmartAI và NaMiOffice Spec v1. Nếu hiện trạng repo hoặc release khác tài liệu, hiện trạng được kiểm chứng và release manifest quyết định lời quảng bá.
