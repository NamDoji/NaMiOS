# 03. Trang tải, kiểm tra tương thích và dữ liệu phát hành

## 1. Ba trạng thái phát hành

| Trạng thái | CTA hiển thị | Điều kiện |
|---|---|---|
| pre_release | “Nhận thông báo khi có bản thử nghiệm”; “Xem tiến độ” | Chưa có ISO phát hành được phê duyệt; không cho nút tải giả |
| beta | “Tải bản thử nghiệm miễn phí” và banner lưu ý; “Kiểm tra máy trước” | ISO kiểm chứng, phạm vi thiết bị, known issues, giấy phép, hỗ trợ |
| stable | “Tải NaMiOS miễn phí”; version/build/arch/size/date; kiểm tra máy | Release gate đầy đủ, chữ ký, checksum, mirror, recovery và hỗ trợ |

Không ghi “Miễn phí mãi mãi” nếu giấy phép/dịch vụ chưa quyết định. “Tải miễn phí” áp dụng phần NaMiOS được phép phân phối; bên thứ ba có thể cần tài khoản/giấy phép riêng.

## 2. Trang tải khi đã có release

Hero gồm phiên bản, ngày, kênh Stable/Beta, kiến trúc x86_64/ARM64 chỉ khi có build thật, kích thước, ngôn ngữ, yêu cầu RAM/ổ/UEFI/Secure Boot/GPU dựa kết quả test. Chọn kiến trúc tự gợi ý từ trình duyệt nhưng không tự tải; giải thích rõ. Hiển thị SHA-256, file chữ ký, khóa công khai/fingerprint, hướng dẫn xác minh Windows/macOS/Linux, release notes, known issues, danh sách máy chứng nhận, hướng dẫn tạo USB và sao lưu. Link tải dùng HTTPS tới hạ tầng do dự án kiểm soát; không trỏ Google Drive cá nhân như kênh phân phối chính thức. Mirror ghi nguồn và hash giống nhau.

**Trước khi tải:** banner “Sao lưu dữ liệu và thử Live USB”; không trình bày cài thay Windows là bước mặc định. Form chọn “Thử không cài / Cài song song nếu đã được hỗ trợ / Cài mới” đi đến hướng dẫn riêng, không thu dữ liệu cá nhân trừ khi có mục đích và consent.

**Xác minh:** trang giải thích checksum xác nhận tệp không lỗi nhưng không thay thế chữ ký/nguồn đáng tin; tuyệt đối không khuyên tắt Secure Boot hoặc cảnh báo hệ điều hành một cách chung chung. Nếu bootloader/chữ ký Secure Boot chưa được kiểm, công khai hạn chế.

## 3. Release manifest — nguồn sự thật duy nhất

Ví dụ dữ liệu khởi tạo, **không phải một release**:

    {
      "product": "NaMiOS",
      "channel": "beta",
      "version": "0.1.0-example",
      "release_date": null,
      "status": "pre_release",
      "architectures": [],
      "minimum_hardware": null,
      "downloads": [],
      "features": [],
      "known_issues": [],
      "support_url": null
    }

CI kiểm schema, chữ ký manifest, URL, hash, file size, MIME, license/notice, ngày, checksum sau upload và khả năng tải từ vị trí địa lý thử nghiệm trước khi chuyển status sang beta/stable. Nội dung trang, schema.org và sitemap lấy từ cùng manifest. Không cho editor CMS đổi nhãn “đã phát hành” bằng tay.

## 4. Ma trận ứng dụng

Mỗi record: tên, vendor, loại native / official_web / wine_tested / windows_only, bản NaMiOS, bản app, ngày thử, workflow (mở, gõ, in, upload, gọi video...), kết quả pass/partial/fail/not_tested, hạn chế, chứng cứ, nguồn cài, quyền phân phối, owner và ngày cần thử lại. Filter theo lĩnh vực “Văn phòng, Kế toán, Thuế, Giáo dục, Hành chính, Liên lạc”. Kết quả tìm “Word” phải giải thích NaMiOffice xử lý DOCX, Microsoft Office desktop là sản phẩm riêng. Kết quả “Zalo” phân biệt Zalo Web và Zalo PC. MISA/.NET chỉ gắn pass trên phiên bản/workflow đã kiểm.

## 5. Ma trận thiết bị

Mỗi record: vendor/model, VID/PID/chipset nếu có, firmware, phương thức USB/LAN/Wi-Fi/Bluetooth, bản NaMiOS/kernel/driver/backend, chức năng print/scan/duplex/ADF/copy-via-PC/Bluetooth audio/HID/Wi-Fi band, kết quả và ngày thử. Một MFP có thể “in đạt, quét chưa thử”; không đặt một nhãn “tương thích” chung. Có nút gửi model để đề nghị kiểm thử; không tự biến yêu cầu thành lời chứng nhận.

## 6. Tính năng và tuyên bố có điều kiện

Mỗi claim marketing có claim_id, đoạn text, trạng thái, release_min, evidence URL hoặc ticket, người duyệt, ngày kiểm và ngày hết hiệu lực. Nếu release rollback hoặc một web service đổi, website rút claim/tình trạng tương ứng. Trang “Có gì mới” lấy từ changelog đã duyệt, không viết AI tự động rồi xuất bản. Trên trang chủ chỉ hiển thị trạng thái build đang tải, không trộn screenshot vNext với build stable.

## 7. Dữ liệu cá nhân và phản hồi

Form nhận tin chỉ yêu cầu email, double opt-in, có hủy nhận, retention và chính sách rõ; không gửi marketing cho người chưa đồng ý. Form báo lỗi hướng dẫn ẩn thông tin cá nhân và không tự gửi tài liệu, log, serial máy. Search tương thích không bắt đăng nhập; đo analytics tối thiểu và opt-in nếu có tracker. Không gửi thông tin máy bằng script fingerprint ngầm.
