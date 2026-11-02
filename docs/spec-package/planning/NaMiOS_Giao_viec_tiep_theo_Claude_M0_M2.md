# NaMiOS Giao việc tiếp theo cho Claude Code

**Ngày:** 02/11/2026. **Nhà sáng lập và chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam.
**Tài liệu gốc:** bộ đặc tả NaMiOS phiên bản 1.1. Đây là lệnh thực thi tiếp theo cho M0–M2; không thay thế yêu cầu bảo mật, quyền phần mềm và nghiệm thu trong đặc tả gốc.

## Quyết định sản phẩm cần giữ

NaMiOS là hệ điều hành miễn phí dựa trên Debian/Linux, phục vụ người dùng Việt Nam muốn rời Windows mà vẫn làm được công việc hằng ngày. Dự án cần chứng minh một quy trình công việc hoàn chỉnh trên đúng máy và phần mềm người dùng có, thay vì chỉ chứng minh một file `.exe` mở được. Giao diện thân thuộc, in và quét, chữ ký số, Office, Zalo, MISA và .NET đều là điều kiện chuyển đổi. Chế độ Wine, web, ứng dụng Linux, Windows VM hoặc remote phải được ghi riêng; chỉ mode không phụ thuộc Windows mới đạt mục tiêu loại bỏ chi phí giấy phép Windows. Giấy phép Office/MISA vẫn thuộc nhà cung cấp tương ứng.

**Không công bố cam kết tương thích 100% ứng dụng và driver Windows.** Wine là lớp tương thích cho ứng dụng, không phải Windows kernel. WPF chỉ chạy trên Windows theo tài liệu Microsoft; MISA SME 2026 tự chọn SQL Server theo phiên bản Windows, nên MISA là rủi ro kiến trúc cần thử sớm, không phải tính năng có thể thêm sau khi trang trí desktop [1][2][3].

## Mệnh lệnh triển khai cho Claude Code

Đọc toàn bộ bộ đặc tả đã giao, đặc biệt các mục 26–30. Kiểm tra repository, host, quyền sử dụng bộ cài và tài nguyên máy trước khi sửa. Trong cùng phiên, tạo source và kết quả chạy được cho những việc độc lập ở M0/M1; khi có môi trường Linux, tiếp tục spike M2. Không dừng ở đề xuất kế hoạch. Không tự tuyên bố test chạy khi thiếu máy, bộ cài hoặc giấy phép. Giữ `docs/STATUS.md` và evidence theo ngày; cập nhật các task B001–B016 trước khi làm UI lớn hay ISO công khai.

### Gói 1 Nắm rõ người dùng và ứng dụng quyết định thành bại

**P0, thực hiện đầu tiên.** Tạo `inventory/applications.csv` và `inventory/workflows.md` với các trường: ứng dụng/nhà cung cấp, edition/build/32–64 bit, nguồn bộ cài và quyền dùng, tần suất, người dùng, công việc bắt buộc, file đầu vào/đầu ra, driver/dịch vụ/.NET/SQL/token/add-in liên quan, hậu quả nếu không chạy, mode có thể thử, Windows reference và trạng thái `unknown` ban đầu.

Chọn một nhóm người dùng pilot cụ thể: văn phòng phổ thông hoặc giáo viên trước; kế toán SME là nhánh riêng vì DB và ký số. Khảo sát 20 ứng dụng ưu tiên, khởi đầu bằng Word, Excel, Zalo PC/Web, MISA SME/AMIS và ba ứng dụng .NET đại diện. Khi chưa có danh sách phiên bản thực của chủ dự án, dùng hàng placeholder để xây công cụ nhưng **không tính là đã khảo sát**. Tạo ba workflow mẫu có điểm kết thúc đo được: (A) viết DOCX tiếng Việt → gửi tệp → in; (B) mở XLSX → tính → lưu → đối chiếu giá trị; (C) chứng từ thử → báo cáo MISA → xuất/in → khôi phục DB. Đo tác vụ trên Windows chuẩn cùng build trước khi so với NaMiOS.

**Đầu ra:** inventory, bộ fixture tự tạo có quyền dùng, expected outcomes, đánh giá ảnh hưởng khi fail và danh sách đầu vào thật còn thiếu. **Gate:** mỗi kết luận khả thi đều gắn app build + task + mode; thiếu dữ liệu là `blocked`, không phải `pass`.

### Gói 2 Chứng minh nền kỹ thuật ít rủi ro

**P0.** Kiểm Debian 13, phiên KDE, Wayland/XWayland và X11, Fcitx5/Telex/VNI, Wine runner, WoW64/i386, CUPS, SANE, `ipp-usb`, quyền package và khả năng build Live. Nếu anh phát triển trên Mac, dùng Linux VM hoặc runner chuyên dụng để build/test; không xem kết quả chạy trên macOS là ISO Linux đã chứng nhận. Khóa phiên bản trong build manifest, ghi cấu hình host và lệnh đã chạy.

Viết CLI `namios doctor --json` và validator manifest hai tầng; semantic validator phải chặn profile TBD, cài từ nguồn không được duyệt, recipe có shell, thiếu checksum khi policy cần và `task_verified` thiếu evidence. Tạo Wine prefix riêng, không chạy root, có transaction journal và cơ chế phát hiện lệnh cài dở sau reboot. Chạy fixture Win32 đơn giản, fixture .NET console đa nền tảng, WinForms/WPF có quyền dùng trong VM Linux. So sánh thực tế, không dùng mock để kết luận tương thích phần mềm thương mại.

**Đầu ra:** source có test, build manifest, báo cáo môi trường, log sạch, cách tái hiện. **Gate:** CLI/validator/fixture hoạt động thật hoặc ghi chính xác điều kiện chặn; không tạo file ISO giả.

### Gói 3 Chốt rủi ro Office, MISA, Zalo và driver

**P0, trước khi cam kết chuyển máy cho người dùng.** Test đúng build Office desktop hợp lệ trên Wine: cài/kích hoạt, DOCX có dấu, Track Changes, bảng, ảnh, công thức, PDF, in; Excel có công thức, ngày, CSV, Pivot, chart, giá trị tiền và vòng lưu/mở lại. VBA, Power Query, add-in, COM, ODBC là bộ test riêng. Nếu thất bại, đánh dấu task thiếu, có thể giới thiệu LibreOffice/web hoặc Windows hợp lệ như đường lựa chọn riêng; không cộng các mode để báo đã chạy Office desktop.

Test Zalo PC và Web độc lập: đăng nhập, QR, tin, file có dấu, thông báo; thoại/video và chia sẻ màn hình tách riêng. Tài khoản QA tự nguyện, không gửi người ngoài và không lưu mã QR/OTP trong log.

Test MISA SME client theo đúng năm/build với SQL Server trên môi trường Windows lab hợp lệ, dữ liệu kế toán giả và kế toán viên đối chiếu. Bộ test gồm kết nối DB, chứng từ, tổng hợp/chi tiết, xuất, in, backup và restore. Test AMIS qua web là sản phẩm khác; ký số với token/middleware là nhánh riêng. Không đưa DB production vào Wine và không thử nộp hồ sơ thật.

Lập `inventory/devices.csv` theo vendor/product ID, model, firmware, giao thức, driver Linux, quyền phân phối và chức năng. Thử máy in IPP Everywhere/AirPrint/Mopria trước; máy cũ cần Printer Application/driver phù hợp, thiết bị chuyên dụng theo model [4][5]. Với scanner, đối chiếu backend SANE rồi thử thật; có tên trong danh sách không đồng nghĩa mọi chức năng đã đạt [6]. In từ Word/MISA qua Wine phải kiểm trang A4, dấu Việt và nội dung chứng từ; nhận máy in tự động chưa phải nghiệm thu.

**Đầu ra:** ma trận `app × build × mode × task` và `device × model × function`, có run IDs, expected/actual, log, phiên bản runner/kernel và người xác nhận. **Gate:** lỗi sai dữ liệu, in thiếu chứng từ hoặc không restore DB chặn pilot của workflow liên quan.

### Gói 4 Giao diện chuyển đổi và chức năng nâng cấp

Chỉ sau khi Gói 2 có bằng chứng, triển khai `NaMiOS Welcome`, `NaMiOS App Center`, `NaMiOS Devices` và bề mặt desktop quen thuộc. Người dùng chọn bộ gõ, cỡ chữ, máy in mặc định, ứng dụng mở DOCX/XLSX/PDF. App Center phải hiển thị ứng dụng có hỗ trợ thực theo đúng build, giới hạn và nguồn tải. Devices hiển thị **đã thử / thử một phần / chưa thử / không hỗ trợ** theo model và chức năng, với nút in thử/quét thử/chẩn đoán.

Hỗ trợ taskbar, tìm kiếm có/không dấu, cửa sổ, phím Alt+Tab/Win+E/Win+D, kéo thả, copy/paste, file manager, mount ổ USB an toàn, thông báo, Wi-Fi, Bluetooth, âm thanh, màn hình ngoài và cập nhật. Thiết kế nhận diện riêng NaMiOS, không dùng icon/font/âm thanh Windows trái quyền. Kiểm tra thao tác với 15 người thuộc nhóm pilot trước khi quyết định giao diện đã dễ dùng.

Nhóm nâng cấp sau alpha: import dữ liệu Windows có preview và backup, sao lưu/khôi phục có kiểm chứng, cập nhật có kênh và thu hồi profile, trung tâm chẩn đoán tiếng Việt lọc bí mật, danh mục phần mềm theo nghề nghiệp, trình cài đặt Live USB, mã hóa ổ đĩa, Secure Boot và tài liệu hỗ trợ. Thứ tự nâng cấp do gate dữ liệu/bảo mật quyết định, không theo độ bắt mắt của tính năng.

## Thứ tự, trách nhiệm và mốc ra quyết định

| Giai đoạn | Công việc đủ điều kiện bắt đầu | Sản phẩm xem được | Quyết định |
| --- | --- | --- | --- |
| M0 | Host và người dùng mục tiêu rõ; làm độc lập khi thiếu installer | Inventory, workflow, ADR, nguồn và quyền | Có đủ dữ liệu để định nghĩa pilot hay không |
| M1 | M0 đã định khung, có host phát triển | CLI, validator, journal, fixture và test | Lõi có thể vận hành an toàn hay không |
| M2 | Linux VM, runner và bộ cài có quyền dùng khi cần | Báo cáo Wine/.NET/Office/MISA/Zalo và thiết bị | Chọn scope pilot hoặc no-go cho workflow bắt buộc |
| M3 | G0 đạt cho scope đã chọn | ISO Live, desktop Việt và cài trên đĩa ảo | G1 alpha kỹ thuật |
| M4 | Lab thiết bị, dữ liệu giả và người UAT | Pilot 30 ngày, ma trận chứng nhận, backup/restore | G2 chuyển nhóm người dùng cụ thể |

**Điều kiện dừng đầu tư đại trà:** ứng dụng bắt buộc chỉ chạy khi dùng Windows VM/remote mà mục tiêu là loại bỏ hoàn toàn Windows; sai lệch dữ liệu Office/MISA; token hoặc thiết bị thiết yếu không có đường hoạt động; hoặc thiếu năng lực cập nhật bảo mật. Báo cáo no-go phải chỉ ra ứng dụng/model, task thất bại, phương án thay đổi và chi phí. Kết quả này có giá trị cho quyết định sản phẩm.

## Nội dung anh có thể gửi ngay cho Claude Code

> Tiếp tục dự án NaMiOS của hai nhà sáng lập Đỗ Chí Cường và Đỗ Bảo Nam. Đọc bộ đặc tả phiên bản 1.1 và tài liệu giao việc M0–M2 này. Hãy kiểm tra workspace và môi trường thật, thực hiện ngay M0/M1 và các thử nghiệm M2 có thể chạy trong phiên. Tạo source, test, inventory, STATUS và bằng chứng tái hiện. Ưu tiên ứng dụng Windows và thiết bị ngoại vi quyết định người dùng có chuyển sang NaMiOS được không. Phân biệt Word/Excel desktop, LibreOffice, web và Windows VM; MISA SME, AMIS và ký số; app .NET đa nền tảng với WinForms/WPF. Không gán trạng thái đạt nếu chưa thử đúng build, tác vụ và model. Mỗi lượt báo cáo kết quả thực, giới hạn, rủi ro dữ liệu và câu hỏi chỉ khi cần bộ cài, máy hoặc quyền dùng cụ thể. Đừng dừng ở kế hoạch hay giao diện mô phỏng.

## Đầu vào cần bổ sung khi đi vào test thật

Anh có thể gửi sau khi Claude hoàn thành phần hạ tầng: phiên bản Word/Excel có giấy phép; năm/build MISA và loại SQL Server; 2–3 ứng dụng .NET; model 2 máy in, 1 scanner, USB token; một máy laptop/PC pilot và 3 workflow quan trọng nhất. Không gửi password hoặc dữ liệu kế toán thật qua prompt. Thiếu đầu vào không chặn phần mềm nền và fixture.

## Căn cứ kỹ thuật chính thức

1. [WineHQ giới thiệu Wine](https://www.winehq.org/about/).
2. [Microsoft Learn về WPF trên Windows](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/overview).
3. [MISA SME 2026 và SQL Server](https://helpsme.misa.vn/2026/kb/tu-dong-cai-dat-sql-server-tuong-thich-theo-he-dieu-hanh/).
4. [OpenPrinting về máy in không cần driver truyền thống](https://openprinting.github.io/driverless).
5. [OpenPrinting về driver/Printer Applications](https://openprinting.github.io/cups/drivers.html).
6. [SANE về model máy quét](https://www.sane-project.org/sane-supported-devices.html).
