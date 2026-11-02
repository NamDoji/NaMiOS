# Quy tắc phát triển NaMiOS

## Nguồn yêu cầu

Tên chính thức NaMiOS; hai nhà sáng lập và chủ dự án là Đỗ Chí Cường và Đỗ Bảo Nam. Không nhầm quyền đối với phần phát triển riêng với quyền sở hữu các thành phần Linux, Debian, KDE, Wine. Đọc cả mục 26–30 của đặc tả.

Đọc `specs/DAC_TA_HE_DIEU_HANH.md` trước khi triển khai. Các hợp đồng và ví dụ đi kèm là tài liệu thiết kế ban đầu, chưa có sản phẩm đã kiểm chứng. Giữ requirement IDs khi tách thành issue/test. Đọc AGENTS.md và hướng dẫn hiện hữu của repository, hợp nhất thay vì ghi đè.

## Cách làm việc

- Triển khai từng mốc M0 đến M5, dùng gate để đánh giá kết quả. Không nhảy sang UI trang trí trước khi biết khả năng chạy app.
- Ưu tiên thành phần upstream được duy trì; không tự viết kernel, crypto, package manager, browser hoặc driver.
- Kiểm tra tài liệu chính thức hiện hành khi phiên bản/API/giấy phép ảnh hưởng quyết định; lưu URL, ngày tra cứu và phiên bản thực.
- Duy trì docs/STATUS.md, ADR, backlog và test evidence. Mọi nhận định được phân loại fact/design/target/unknown.
- Tiếp tục phần độc lập khi thiếu bộ cài thương mại. Chỉ hỏi đầu vào mà phần việc phụ thuộc sắp cần; không tự bịa.
- Không commit bí mật, installer thương mại, DB thật, prefix có token hoặc artifact không được phép phân phối.

## Các điều kiện không được bỏ qua

- Không root Wine; không shell recipe, eval, shell=True hoặc tải script để chạy ngay.
- Chỉ privileged helper có API hẹp, Polkit và kiểm tra người gọi/đường dẫn. Catalog không phải nguồn lệnh root.
- Kiểm thử path traversal, symlink, race, manifest lạ, hash sai, chữ ký sai, replay và metadata hết hạn.
- Prefix chỉ là môi trường chạy. Sandbox và quyền thư mục/mạng/display cần policy và test riêng.
- Không bypass license/activation. Không dùng mã nguồn Windows bị rò rỉ. Không tự phân phối font hay runtime thương mại.
- Không thay Excel desktop bằng LibreOffice/web mà tính cùng kết quả; không gộp SME với AMIS.
- Không dùng app thử trên dữ liệu thật, không tự ký số/gửi hóa đơn/nộp hồ sơ. Backup phải được restore thử.

## Kiểm chứng

Unit test cho policy/validator/state/redaction và integration trên Linux VM cho Wine. Mock được dùng để test logic nhưng không tính là ứng dụng Windows đã chạy. Không có môi trường/binary/license hợp lệ thì ghi blocked, không pass. Chỉ app-mode-version đúng tuple với evidence mới được task_verified. Người QA phê duyệt chứng nhận nghiệp vụ.

Không ghi test results vào tài liệu như thể đã chạy khi chưa có run. Lệnh CLI và API trong đặc tả là giao diện cần xây, phải phân biệt với công cụ thực có trên host. Mọi thao tác phá hủy đĩa/dữ liệu hoặc công bố public cần phạm vi và xác nhận cụ thể của chủ dự án.

## Hoàn thành task

Code có thể chạy trong môi trường ghi rõ; tests liên quan đã chạy; docs/backlog cập nhật; giới hạn và phần blocked được nêu. Không có TODO thay chức năng được báo hoàn tất. Báo cáo gồm thay đổi, bằng chứng, app compatibility và bước tiếp theo.
