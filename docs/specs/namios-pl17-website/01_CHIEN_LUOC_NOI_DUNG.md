# 01. Nội dung, cấu trúc thông tin và thông điệp

## 1. Đối tượng và lời hứa đúng mức

| Người xem | Câu hỏi chính | Hành động trang cần dẫn đến |
|---|---|---|
| Người dùng cá nhân | Có dễ dùng? Zalo, Facebook, YouTube, Office có sẵn không? | Xem trải nghiệm → kiểm tra máy → thử/tải |
| Giáo viên, học sinh | Có gõ tiếng Việt, soạn bài, in, trình chiếu? | Xem NaMiOffice và thiết bị → tải bản phù hợp |
| Kế toán, văn phòng | Tệp Excel, MISA, chữ ký số, biểu mẫu có đúng không? | Tra cứu phiên bản ứng dụng và hạn chế → pilot |
| IT trường/doanh nghiệp | Driver, cập nhật, bảo mật, hỗ trợ và triển khai nhiều máy? | Tải tài liệu kỹ thuật và danh sách máy kiểm thử |
| Cộng đồng phát triển | Mã nguồn, giấy phép, cách báo lỗi/đóng góp? | Xem nguồn, roadmap và issue tracker thật |

Lời hứa cốt lõi: “Dễ làm quen. Sẵn công cụ thiết yếu. Minh bạch về tương thích.” Có thể dùng câu dẫn trang đầu: **“Một chiếc máy tính quen thuộc hơn, dành cho cách người Việt làm việc và học tập.”** Dòng phụ: “NaMiOS kết hợp giao diện tiếng Việt, NaMiOffice, bộ gõ, trình duyệt, cập nhật và trợ lý SmartAI. Kiểm tra khả năng chạy ứng dụng, thiết bị của bạn trước khi cài.”

## 2. Sitemap và điều hướng

Nav desktop: **Sản phẩm | Ứng dụng | Thiết bị & tương thích | SmartAI | Bảo mật | Tải NaMiOS | Hướng dẫn | Cộng đồng**. Nav di động dạng menu dễ dùng bàn phím; nút “Tải miễn phí” chỉ hiển thị khi phát hành có thật, nếu chưa thì “Nhận tin ra mắt”. Footer có Về dự án, nhóm phát triển, liên hệ thật, nguồn mở/giấy phép, quyền riêng tư, điều khoản, bảo mật, roadmap, trạng thái phát hành, ngôn ngữ.

| Trang/đường dẫn gợi ý | Nội dung và CTA |
|---|---|
| `/` | Hero, sản phẩm thật qua ảnh/video nhẹ, 6 lợi ích, app thiết yếu, thiết bị, SmartAI, bảo mật, câu chuyện Việt Nam, CTA |
| `/features` | Desktop, File Manager, tiếng Việt, tìm kiếm, cập nhật, tính dễ dùng; từng claim có trạng thái |
| `/apps` | NaMiOffice, browser, bộ gõ, PDF, bảo mật; web shortcuts Zalo/YouTube/Maps/Facebook/TikTok/WhatsApp; nhãn giao hàng |
| `/namioffice` | Writer/Sheet/Slides, DOCX/XLSX/PPTX, bảng/công thức/biểu đồ, ma trận tính năng và giới hạn VBA |
| `/compatibility` | Tra phần mềm Windows, model máy/thiết bị, kết quả theo bản OS và ngày kiểm; không ghi “tất cả” |
| `/devices` | In/scan/photo, USB, Wi-Fi, Bluetooth, Ethernet; chọn model, cách kết nối, tính năng đã thử và xử lý lỗi |
| `/smartai` | Ví dụ giải thích lỗi, hỗ trợ thao tác; quyền riêng tư, xác nhận hành động và trạng thái tính năng |
| `/security` | Cập nhật ký số, rollback, sandbox, sao lưu, chống phần mềm độc hại; không hứa không có virus |
| `/download` | Bản phát hành, yêu cầu máy, chọn ISO, hash/chữ ký, hướng dẫn Live USB và sao lưu |
| `/install` | Hướng dẫn cho người mới; thử Live USB, cài mới/dual boot nếu thực sự hỗ trợ, xử lý lỗi |
| `/docs`, `/release-notes`, `/roadmap` | Tài liệu, nhật ký thay đổi, trạng thái công khai, vấn đề còn thiếu |
| `/about`, `/community`, `/contact` | Tầm nhìn, Đỗ Chí Cường và Đỗ Bảo Nam, nguồn mở, đóng góp và kênh hỗ trợ |

Giai đoạn đầu có thể gom feature/devices/smartai/security thành các section trang chủ nhưng các URL quan trọng `/download`, `/compatibility`, `/namioffice`, `/install`, `/privacy` phải tồn tại độc lập trước public release.

## 3. Bố cục trang chủ có nội dung cụ thể

1. **Hero:** “NaMiOS. Gần gũi để bắt đầu. Đủ mạnh để làm việc.” Nền ảnh desktop/screenshot thật, logo sen chính thức, CTA động theo trạng thái release và CTA phụ “Khám phá NaMiOS”; nhãn “Dựa trên Linux” và “Miễn phí” theo giấy phép thật.
2. **Thói quen quen thuộc:** desktop, thanh tác vụ, menu ứng dụng, cửa sổ, kéo thả, phím tắt; ảnh trước/sau thao tác. Không so sánh tuyệt đối với Windows hay bắt chước nguyên pixel.
3. **Sẵn từ ngày đầu:** card NaMiOffice, browser, gõ tiếng Việt, PDF/tệp, Security Center; card dịch vụ web riêng có nhãn “Mở trang chính thức · Cần internet/tài khoản”. Mỗi card có `availability`, `last_verified`, `offline`, `source`.
4. **NaMiOffice:** ba cột văn bản, bảng tính, trình chiếu; câu “Làm việc với DOCX, XLSX, PPTX theo ma trận kiểm thử”; link bảng tương thích, cảnh báo macro/biểu mẫu chuyên ngành.
5. **Thiết bị quanh bạn:** đồ họa in/scan, USB, Wi-Fi, Bluetooth, mạng dây; nút “Tra cứu thiết bị”; trạng thái riêng Print/Scan/Duplex/ADF/Bluetooth profile; không dùng một dấu tick cho toàn bộ model.
6. **Phần mềm Windows:** sơ đồ Linux native → web chính thức → Wine đã kiểm chứng → môi trường Windows có giấy phép; ví dụ Zalo PC/MISA/.NET ghi “tùy phiên bản, đang kiểm thử” nếu thiếu bằng chứng. Nút “Tìm phần mềm của tôi”.
7. **SmartAI:** demo có thể kiểm chứng: “Vì sao máy in không in?” → phân tích hàng đợi/kết nối/quyền → hướng dẫn 3 bước; “Mở tệp Excel này có nguy cơ sai công thức không?” → báo tương thích. Không mô tả AI tự sửa mọi app.
8. **An toàn và cập nhật:** card cập nhật OS/app, thông báo bản vá, rollback, sao lưu; tình trạng của build thật; link security policy và release notes.
9. **Cho Việt Nam:** tiếng Việt mặc định, Telex/VNI, VND/ngày tháng, mẫu tài liệu, hình nền Việt Nam. Ảnh cảnh đẹp/di sản phải có nguồn và quyền; bản đồ chủ quyền chỉ dùng tài liệu địa lý có thẩm quyền, không tạo bằng AI.
10. **CTA cuối:** “Kiểm tra máy của bạn” và nút tải/đăng ký chờ phù hợp trạng thái; FAQ ngắn và tài liệu.

## 4. Giọng văn và nội dung mẫu

Ngôn ngữ ưu tiên tiếng Việt tự nhiên, trực tiếp, không lạm dụng “cách mạng”, “100%”, “vượt trội nhất”. Hỗ trợ tiếng Anh đầy đủ ở `/en` sau khi bản tiếng Việt chuẩn. Mỗi tính năng có một trong bốn nhãn **Đã có trên bản phát hành**, **Đã thử nghiệm trên thiết bị/phiên bản cụ thể**, **Bản thử nghiệm**, **Đang phát triển**; thời điểm xác minh hiện rõ.

Ví dụ copy:

> **Làm việc quen tay với NaMiOffice.** Soạn văn bản, bảng tính và bài trình chiếu ngay trên NaMiOS. Mở và lưu các định dạng phổ biến; với tệp có macro, biểu đồ hoặc công thức phức tạp, NaMiOffice sẽ báo mức hỗ trợ trước khi bạn lưu.

> **Kết nối dễ hiểu.** Tìm máy in, máy quét, Wi-Fi và Bluetooth trong một nơi. NaMiOS báo cụ thể khâu nào đang gặp lỗi và gợi ý bước xử lý. Xem danh sách model và chức năng đã kiểm thử trước khi chuyển máy.

> **Ứng dụng thường dùng, đúng cách.** Zalo, YouTube, Maps, Facebook, TikTok và WhatsApp được mở qua dịch vụ web chính thức khi có trong bản cài; đăng nhập do nhà cung cấp quản lý. Các tính năng của bản desktop Windows chỉ được công bố sau kiểm thử.

## 5. FAQ bắt buộc

- NaMiOS miễn phí thật không? Giấy phép của hệ điều hành, ứng dụng, dịch vụ bên thứ ba và chi phí dữ liệu/máy riêng thế nào?
- Có thay Windows ngay được không? Cần kiểm app và thiết bị, sao lưu, thử Live USB; có thể chưa phù hợp với phần mềm chuyên ngành.
- Microsoft Office có chạy không? NaMiOffice là bộ riêng; tệp DOCX/XLSX/PPTX được kiểm theo tính năng. Office desktop và VBA không được bảo đảm.
- Zalo/Facebook/YouTube “cài sẵn” là gì? Phân biệt web shortcut, native app, app Windows qua Wine.
- MISA/.NET/phần mềm thuế, bảo hiểm chạy không? Tra đúng tên, bản phát hành và workflow; khi chưa kiểm phải nói “chưa xác minh”.
- Máy in/scan nào hoạt động? Tra model, cổng kết nối, firmware và chức năng.
- SmartAI có đọc tệp/gửi đám mây không? Chính sách và quyền rõ, mặc định theo bản phát hành.
- Cách cập nhật, quay lại phiên bản trước và báo lỗi? Link tài liệu cụ thể.
