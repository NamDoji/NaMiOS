# Đặc tả hệ điều hành miễn phí cho người Việt

**Tên sản phẩm thống nhất:** NaMiOS. Việc tra cứu và bảo hộ nhãn hiệu cần được thực hiện trước phát hành công khai.
**Phiên bản tài liệu:** 1.1 — ngày 02/11/2026, múi giờ Asia/Ho_Chi_Minh.
**Nhà sáng lập và chủ dự án NaMiOS:** ông Đỗ Chí Cường và Đỗ Bảo Nam. **Đối tượng thực hiện:** Claude Code và đội kỹ thuật phụ trách Linux, ứng dụng và kiểm thử.
**Trạng thái:** đặc tả để triển khai và kiểm chứng; chưa có hệ điều hành, ISO hay ứng dụng nào được chứng nhận bởi tài liệu này.

## 1 Mục tiêu và kết luận kỹ thuật

Xây dựng một bản phân phối Linux miễn phí cho người dùng Việt Nam, có giao diện tiếng Việt dễ dùng, làm được công việc thông thường và có cơ chế chạy một số ứng dụng Windows theo hồ sơ tương thích được kiểm thử. Ưu tiên Word, Excel, Zalo, MISA và các ứng dụng .NET. Không cam kết thay thế Windows cho tất cả phần mềm hoặc thiết bị.

Phương án cơ sở là Debian 13 amd64, KDE Plasma và Wine. Dùng công cụ phát hành, trình cài đặt và bộ quản lý gói sẵn có; không tự viết nhân hệ điều hành, trình điều khiển, trình duyệt hay bộ Office. Phần phát triển riêng gồm trung tâm ứng dụng, bộ điều phối tương thích, thiết lập tiếng Việt, hồ sơ kiểm thử, hỗ trợ người dùng và tích hợp bản phân phối.

Quyết định đầu tư tiếp phải dựa vào kết quả chạy các tác vụ thực tế. Đưa được giao diện Word hoặc MISA lên màn hình chưa đủ để kết luận dùng được. Bản thử nghiệm phải kiểm chứng đọc ghi dữ liệu, tính toán, in, cập nhật và phục hồi theo đúng phiên bản.

Các phiên bản ứng dụng, bộ cài có quyền sử dụng, mẫu dữ liệu và máy kiểm thử chưa được chủ dự án cung cấp. Claude vẫn bắt đầu được bằng hạ tầng, mẫu ứng dụng tự viết và báo cáo thiếu đầu vào. Những ứng dụng thương mại không được tự gán trạng thái đạt.

## 2 Cách đọc và mức bắt buộc

- MUST hoặc PHẢI: yêu cầu bắt buộc trong phạm vi mốc phát hành tương ứng.
- SHOULD hoặc NÊN: mặc định thực hiện; nếu bỏ phải ghi lý do và tác động trong ADR.
- MAY hoặc CÓ THỂ: tùy chọn, không phải điều kiện nghiệm thu.
- P0: ảnh hưởng dữ liệu, bảo mật, khả năng chạy hệ thống hoặc kiểm chứng tính khả thi.
- P1: chức năng cần cho pilot. P2: sau pilot, chỉ làm khi P0 và P1 liên quan đã đạt.
- FACT: thông tin nền được dẫn nguồn. DESIGN: quyết định đề xuất của dự án. TARGET: chỉ tiêu cần đo. UNKNOWN: chưa có bằng chứng.

Mọi con số hiệu năng và quy mô trong tài liệu là TARGET hoặc giả định lập kế hoạch, không phải kết quả benchmark hay cam kết đã đạt. Phiên bản phụ thuộc phải được kiểm tra lại lúc triển khai, ghi vào lockfile và SBOM; không dùng từ “latest” trong đầu ra phát hành.

## 3 Phạm vi người dùng và sản phẩm

### 3.1 Nhóm người dùng đầu tiên

Pilot phục vụ người dùng văn phòng, giáo viên, học sinh và doanh nghiệp nhỏ. Lựa chọn nhóm cụ thể cho đợt thử nghiệm đầu thuộc chủ dự án; công cụ phải hỗ trợ cấu hình danh mục ứng dụng theo nhóm mà không tạo nhiều hệ điều hành khác nhau.

Các công việc đại diện gồm soạn tài liệu tiếng Việt, xử lý bảng tính, nhắn tin trao đổi tệp, truy cập phần mềm kế toán, mở tài liệu cũ, in và xuất PDF. Nghiệp vụ kế toán cần một người dùng kế toán kiểm tra; đội lập trình không tự nghiệm thu đúng nghiệp vụ bằng cách quan sát màn hình.

### 3.2 Phạm vi phiên bản đầu

P0 gồm ISO Live khởi động trong máy ảo, thiết lập tiếng Việt, trình duyệt, công cụ văn phòng miễn phí, trung tâm ứng dụng tối thiểu, bộ điều phối Wine có kiểm soát, hợp đồng manifest, dữ liệu kiểm thử, log và quy trình build. Mốc alpha phải có trình cài đặt trên đĩa ảo, cập nhật và phục hồi được thử nghiệm.

Pilot bổ sung bộ phần mềm theo danh mục đã chốt, hồ sơ phần cứng được chứng nhận, hướng dẫn, sao lưu, đóng gói có chữ ký và các kịch bản người dùng. Phần mềm thương mại không vượt qua thử nghiệm Wine phải được ghi là chưa hỗ trợ trên Wine; có thể có lựa chọn web hoặc Windows có giấy phép được hiển thị riêng.

Không thuộc v1: tự viết Windows NT, tương thích toàn bộ driver Windows, hỗ trợ ARM, phát hành x86 32-bit, bảo đảm mọi game, DRM hay anti-cheat, mọi macro/add-in Office, mọi USB token, dịch vụ cloud Windows do dự án vận hành, tự viết MISA thay thế, trợ lý AI bắt buộc, đồng bộ tài liệu lên cloud, hệ thống A/B tự viết. Không fork Wine nếu chưa có lỗi tái hiện và đánh giá chi phí bảo trì.

## 4 Ràng buộc bản quyền và phân phối

### 4.1 Nguyên tắc sản phẩm

LIC-001 P0: không đưa mã nguồn Windows bị rò rỉ, bản Windows đã chỉnh sửa trái phép, công cụ kích hoạt lậu hoặc bộ bẻ khóa vào repository, ISO, hướng dẫn và pipeline.

LIC-002 P0: giấy phép hệ điều hành độc lập với giấy phép ứng dụng. Người dùng có thể dùng hệ điều hành miễn phí nhưng vẫn phải có quyền sử dụng Office, MISA, SQL Server, Windows trong máy ảo hoặc tài nguyên thương mại khác khi điều khoản yêu cầu. Không tuyên bố “miễn phí toàn bộ phần mềm”.

LIC-003 P0: mặc định không phân phối lại bộ cài thương mại. Trung tâm ứng dụng dẫn tới nguồn chính thức hoặc nhận bộ cài do người dùng cung cấp. Tự động tải, đóng gói runtime, font, firmware và binary chỉ khi có quyền phân phối và điều kiện đã được ghi nhận theo từng thành phần. Không xem việc tải được công khai là quyền đóng gói lại.

LIC-004 P0: không sao chép logo, icon, âm thanh, hình nền hay font độc quyền của Windows để tạo cảm giác giống Windows. Xây giao diện quen thuộc về cách thao tác với tài nguyên được phép sử dụng và thương hiệu riêng.

LIC-005 P0: có LICENSE cho mã mới, THIRD_PARTY_NOTICES, danh mục giấy phép, SBOM và quy trình cung cấp mã nguồn tương ứng khi giấy phép yêu cầu. Dự kiến mã mới Apache-2.0; đây là lựa chọn đề xuất, phải kiểm tra tương thích giấy phép của thành phần liên kết, đóng gói và sửa đổi trước phát hành. Không gán Apache-2.0 lên mã của upstream.

LIC-006 P1: tách ảnh core dùng thành phần được phép phân phối khỏi phần cài thêm có điều kiện. Nếu cần firmware không tự do, ghi rõ thành phần, nguồn, quyền phân phối, thiết bị áp dụng; không quảng bá toàn bộ hệ thống là phần mềm tự do nếu còn thành phần không tự do.

Microsoft quy định quyền sao chép, sửa đổi và phân phối phải được cấp theo điều khoản tương ứng [S01]. Tài liệu này là yêu cầu triển khai sản phẩm; quyền cụ thể phải được đối chiếu với đúng giấy phép và hình thức phân phối thực tế.

## 5 Kiến trúc hệ thống

### 5.1 Nền tảng mặc định

| Thành phần | Quyết định DESIGN | Điều kiện xác nhận |
| --- | --- | --- |
| Hệ điều hành | Debian 13 trixie amd64 | Ghi point release, snapshot nguồn gói, kernel và package list thực tế |
| Desktop | KDE Plasma, Dolphin và thiết lập riêng bằng gói Debian | Dùng gói từ nguồn được duy trì; không viết lại desktop |
| Phiên đồ họa | Wayland là ứng viên mặc định; Wine qua XWayland khi cần | Quyết định cuối sau ma trận IME, clipboard, màn hình và sandbox; X11 chỉ là phương án tương thích được gắn nhãn hạn chế |
| Tiếng Việt | vi_VN.UTF-8, Asia/Ho_Chi_Minh, Fcitx5 với bộ gõ tiếng Việt phù hợp | Kiểm tra tên gói/engine thực có trong snapshot; hỗ trợ Telex và VNI qua thử nghiệm |
| Office miễn phí | LibreOffice từ repository được duy trì | Ghi rõ là phần mềm thay thế, không phải Microsoft Word hoặc Excel |
| Trình duyệt | Firefox ESR mặc định | Nếu dịch vụ web cần trình duyệt khác, kiểm tra và thêm có điều kiện, không tắt sandbox |
| Wine | Một runner được khóa phiên bản, hồ sơ riêng từng ứng dụng | Chọn gói Debian hoặc nguồn WineHQ tương thích và có xác minh; không trộn tùy tiện nguồn gói |
| Phần mềm riêng | Python 3 cho CLI/service; PySide6 Qt Quick cho UI | Kiểm tra phiên bản, giấy phép và cách đóng gói trong Debian; dùng thư viện duy trì được |
| Cập nhật hệ thống | APT và repository có chữ ký | Không thiết kế package manager mới |
| ISO | Debian live-build | Có build log và hướng dẫn tái tạo trên môi trường sạch |
| Trình cài đặt | Calamares nếu gói và tích hợp đạt spike | Nếu không đạt, dùng đường cài Debian được kiểm thử; ghi ADR thay đổi trước triển khai |
| Dữ liệu cục bộ | JSON có schema cho catalog; SQLite cho trạng thái giao dịch | Không dùng SQLite làm kho tài liệu người dùng |

Debian 13 có vòng đời upstream được công bố; phạm vi hỗ trợ từng gói và cam kết của dự án phải theo dõi riêng [S09]. Debian live-build cho phép tự động hóa cấu hình ảnh Live [S10]. Những lựa chọn trên là thiết kế dự án, không phải chứng nhận tương thích của Debian với Office hay MISA.

### 5.2 Các mô đun

1. `namios-base`: package metapackage, branding, mặc định desktop, locale, font và nguồn cập nhật.
2. `namios-welcome`: thiết lập lần đầu, kết nối mạng, bộ gõ, cỡ chữ, giới thiệu ứng dụng và lựa chọn sao lưu.
3. `namios-app-center`: tìm kiếm ứng dụng, chọn chế độ chạy, xem tình trạng tương thích, cài, chạy, gỡ và xem hướng dẫn.
4. `namios-compat`: CLI và thư viện quản lý runner, prefix, quyền, giao dịch, snapshot cấu hình và hồ sơ ứng dụng.
5. `namios-system-helper`: service tối thiểu cho thao tác cần đặc quyền, xác thực qua D-Bus/Polkit; không nhận shell command tùy ý.
6. `namios-diagnostics`: thu thập thông tin kỹ thuật đã lọc, xem trước và xuất gói chẩn đoán theo yêu cầu.
7. `compat-catalog`: manifest, chữ ký, kết quả chứng nhận, thu hồi và hướng dẫn theo phiên bản.
8. `image-builder`: cấu hình live-build, build runner, tạo checksum/SBOM, ký và kiểm thử boot.

UI gọi API thư viện nội bộ cho thao tác thường. Chỉ việc quản trị hệ thống mới đi qua helper. Không mở HTTP localhost để điều khiển đặc quyền trong v1. API trong tài liệu là hợp đồng cần triển khai, chưa phải lệnh đã có sẵn.

### 5.3 Luồng ứng dụng

Người dùng chọn ứng dụng → chọn chế độ rõ ràng → đọc hồ sơ đã ký và kiểm tra trạng thái thu hồi → kiểm tra phụ thuộc và quyền sử dụng → xác thực nguồn bộ cài → lập kế hoạch thay đổi → xác nhận → thực hiện trong vùng staging → kiểm tra sau cài → tạo launcher → ghi kết quả. Nếu lỗi, giữ dữ liệu và log, trở lại trạng thái nhất quán hoặc yêu cầu phục hồi có hướng dẫn.

Không tự chuyển từ Microsoft Excel sang LibreOffice hoặc bản web khi người dùng mở tài liệu. Hệ thống có thể gợi ý, nhưng lựa chọn phải được xác nhận và lưu theo người dùng, loại tệp và chế độ chạy.

## 6 Cách đáp ứng ứng dụng Windows

### 6.1 Các chế độ riêng biệt

| Mode | Ý nghĩa | Phụ thuộc và giới hạn |
| --- | --- | --- |
| native | Bản Linux chính thức hoặc ứng dụng đa nền tảng thực sự | Đúng binary, kiến trúc và phụ thuộc Linux |
| web | Dịch vụ chính thức qua trình duyệt | Tài khoản, Internet và chức năng do nhà cung cấp quyết định |
| wine | Chạy binary Windows qua Wine | Tương thích theo build, tác vụ, runtime, driver và phần cứng |
| vm | Windows trong KVM/QEMU qua libvirt | Cần tài nguyên, giấy phép và hỗ trợ Windows; không còn giải pháp hoàn toàn không phụ thuộc Windows |
| remote | Truy cập máy Windows đã có quyền sử dụng | Cần kết nối, tài khoản và cấu hình máy chủ hợp lệ |

Wine là lớp tương thích, không chạy một bản Windows bên dưới [S02]. Tính tương thích trên Wine không đồng nghĩa nhà cung cấp phần mềm hỗ trợ chính thức Linux. Nhãn “đã kiểm thử bởi NaMiOS” và “được nhà cung cấp hỗ trợ” phải là hai trường độc lập.

### 6.2 Word và Excel

APP-OFF-001 P0: lập inventory riêng Microsoft 365 Apps và từng bản Office có quyền dùng, xác định edition, channel, build, kiến trúc 32/64-bit, công nghệ cài đặt và trạng thái hỗ trợ. Không ghi “Office hỗ trợ” nếu mới kiểm tra một bản.

APP-OFF-002 P0: chưa có build Office nào được chứng nhận tại thời điểm soạn đặc tả. Bắt đầu bằng kiểm tra cài và kích hoạt hợp lệ; không dùng biện pháp vượt kích hoạt, sửa DRM hay đóng băng bản cũ hết hỗ trợ để đạt demo.

APP-OFF-003 P0: Word phải kiểm tra mở/lưu DOCX, tiếng Việt, bảng, ảnh, công thức, section, header/footer, mục lục, Track Changes, bình luận, in và PDF. So sánh tài liệu gốc Windows với bản round-trip trên hệ thống thử. Lưu ra bản mới trước khi ghi đè tài liệu cũ.

APP-OFF-004 P0: Excel phải kiểm tra công thức, kiểu dữ liệu, ngày tháng, dấu phân cách, named ranges, chart, PivotTable, liên kết và in. Bộ thử có giá trị kỳ vọng do người phụ trách xác nhận. Với số tiền dùng giá trị thập phân và quy tắc làm tròn đã định nghĩa; không dùng sai số tương đối để che sai tiền. Với floating point khoa học ghi tolerance riêng theo từng test.

APP-OFF-005 P1: VBA, COM add-in, ODBC, Power Query, Power Pivot, external data, WebView2 và đồng tác giả là nhóm chứng nhận riêng. Nếu chưa kiểm thử, hiển thị chưa xác nhận; không suy ra từ việc mở XLSX thành công. Macro mặc định không tự chạy.

APP-OFF-006 P0: bản web là hồ sơ khác; LibreOffice là sản phẩm khác. Lưu nguyên tên nhà cung cấp, chức năng thiếu và yêu cầu kết nối/tài khoản. Không tính dùng LibreOffice thành đạt yêu cầu chạy Microsoft Excel desktop.

APP-OFF-007 P1: nếu Wine không đủ cho bộ tác vụ bắt buộc, cung cấp tùy chọn Windows hợp lệ ở VM/remote trong nhánh tương thích mở rộng. Không dùng nhánh này để báo nhánh miễn phụ thuộc Windows đã đạt.

### 6.3 Zalo

APP-ZAL-001 P0: tạo hồ sơ riêng `zalo-web` và `zalo-pc-wine`. Nhà cung cấp có trang PC và Web [S03]; không suy ra bản Linux chính thức từ tên một gói cộng đồng.

APP-ZAL-002 P1: kiểm tra đăng nhập, QR, xác nhận thiết bị, gửi/nhận tin, tệp có dấu, ảnh, thông báo, mở liên kết, đăng xuất và đăng nhập lại. Chỉ gửi nội dung thử giữa tài khoản được phép dùng cho QA; không tự nhắn cho người khác.

APP-ZAL-003 P1: cuộc gọi thoại/video, camera/micro và chia sẻ màn hình là nhóm kiểm thử riêng theo mode và phiên bản. Không quảng bá bản web đầy đủ chức năng PC nếu chưa kiểm chứng.

APP-ZAL-004 P0: không lưu mật khẩu, mã OTP, cookie hay QR đăng nhập vào log và ảnh minh chứng. Không sao chép cơ sở dữ liệu chat để “đồng bộ” nếu thiếu cơ chế chính thức và quyền người dùng. Xóa cache không đồng nghĩa xóa dữ liệu trò chuyện đã đồng bộ lên dịch vụ.

APP-ZAL-005 P1: kiểm tra vòng đời tự cập nhật của Zalo PC trong prefix thử nghiệm. Nếu binary đổi so với bản đã chứng nhận, trạng thái bản mới phải trở lại chưa kiểm thử, không tiếp tục dùng nhãn cũ.

### 6.4 MISA

APP-MIS-001 P0: không coi MISA là một ứng dụng duy nhất. Tách MISA SME theo năm/build, AMIS Kế toán theo dịch vụ web, công cụ ký số, kết nối hóa đơn và các sản phẩm khác. Mỗi thành phần có hồ sơ, giấy phép và bộ tác vụ riêng.

APP-MIS-002 P0: MISA SME được ưu tiên kiểm chứng ở mô hình client và SQL Server tách riêng. Trước hết dùng SQL Server trên môi trường Windows được nhà cung cấp hỗ trợ, chỉ dữ liệu giả, mạng thử nghiệm. Đó là mô hình vẫn phụ thuộc Windows ở phía server. Không mặc định cài SQL Server qua Wine và không suy luận SQL Server Linux thay thế được mọi phiên bản SME [S04].

APP-MIS-003 P0: điều tra .NET Framework, SQL client, native DLL, COM, service, font, báo cáo, cơ chế bản quyền, print, SQL authentication hoặc Windows integrated authentication. Việc một ứng dụng dùng .NET không đủ để chọn runner.

APP-MIS-004 P0: bộ kiểm thử SME gồm tạo dữ liệu kế toán thử, kết nối DB, nhập danh mục, nhập chứng từ mẫu, đối chiếu tổng hợp/chi tiết, báo cáo, xuất Excel/PDF, sao lưu và phục hồi bằng công cụ ứng dụng. Người kế toán so sánh dữ liệu với môi trường Windows tham chiếu cùng build và DB.

APP-MIS-005 P0: không mở dữ liệu kế toán thật trên Wine thử nghiệm; không chạy nâng cấp schema trực tiếp trên DB sản xuất. Sao chép DB để thử qua quy trình sao lưu và restore được nhà cung cấp hướng dẫn; snapshot prefix hay chép file MDF đang chạy không được coi là backup nhất quán.

APP-MIS-006 P1: AMIS Kế toán chạy web phải kiểm thử trình duyệt và từng nghiệp vụ thực dùng [S05]. Ký số có thể cần công cụ cục bộ hoặc dịch vụ khác [S06]; không suy ra “web nên tất cả chức năng chạy Linux”. Không đổi phần mềm kế toán hoặc chuyển dữ liệu doanh nghiệp ngầm.

APP-MIS-007 P1: USB token, smartcard, middleware, chứng thư, ký từ xa và MISA KYSO là nhánh kiểm chứng riêng theo hãng/model/driver. Không sao chép private key khỏi token; không tự ký, phát hành hóa đơn hay nộp hồ sơ thật trong QA. Dùng sandbox của nhà cung cấp hoặc ghi `blocked_external_dependency`.

APP-MIS-008 P0: nếu không thể chạy ổn SME trên Wine, báo cáo đúng giới hạn, đề xuất web hoặc VM/remote có giấy phép. Nếu SME trực tiếp không phụ thuộc Windows là điều kiện kinh doanh bắt buộc, dự án phải kết luận chưa đạt điều kiện triển khai cho nhóm này.

### 6.5 Phân loại ứng dụng .NET

| Loại ứng dụng | Hướng thực hiện | Không được suy diễn |
| --- | --- | --- |
| .NET hiện đại console hoặc ASP.NET Core thuần đa nền tảng | Dùng bản Linux có sẵn hoặc build từ source nếu có quyền | Binary win-x64 không tự thành binary Linux; kiểm tra P/Invoke, native lib và Windows API |
| WinForms trên .NET hiện đại | Thử Windows binary trong Wine theo hồ sơ hoặc VM | Cài .NET Runtime Linux không mang WinForms sang Linux |
| WPF trên .NET hiện đại | Thử Wine có giới hạn hoặc Windows hợp lệ | WPF vẫn chỉ được hỗ trợ chính thức trên Windows [S07] |
| .NET Framework 2 đến 4.x | Thử runtime phù hợp trong prefix riêng, có đối chiếu quyền dùng | Mono/Wine Mono không bảo đảm tương đương Microsoft .NET Framework [S08] |
| Ứng dụng phụ thuộc COM ActiveX GDI registry service | Kiểm tra từng API, kiến trúc và phụ thuộc | Không gọi chung là đã hỗ trợ .NET |
| Source có thể sửa | Ưu tiên port sang framework đa nền tảng phù hợp bằng dự án riêng | Không tự sửa sản phẩm của nhà cung cấp hoặc thay đổi nghiệp vụ |

NET-001 P0: công cụ phân tích thu thập PE architecture, CLR metadata, `.runtimeconfig.json`, `.deps.json`, TargetFramework nếu có, phụ thuộc tĩnh và cấu hình liên quan. Không thực thi binary để “nhận diện” mặc định. Giới hạn kích thước, thời gian và quyền parser vì tệp đầu vào có thể độc hại.

NET-002 P0: trả kết quả `confidence`, bằng chứng nhận diện, phụ thuộc chưa rõ và gợi ý mode. Phân tích tĩnh chỉ là gợi ý, không phải chứng nhận chạy.

NET-003 P0: quản lý Wine Mono và Microsoft .NET theo recipe cụ thể; không tự cài lẫn vào prefix chung. Winetricks nếu dùng phải khóa revision và ghi cả URL/hash/điều khoản của các payload được nó tải tiếp. Không coi pin script là pin toàn bộ chuỗi cung ứng.

NET-004 P1: runtime LTS còn hỗ trợ được chọn theo ngày build và nguồn chính thức [S11]; runtime cũ có thể cần cho app cũ nhưng phải gắn nhãn rủi ro/vòng đời. Không mặc định kéo toàn bộ .NET SDK vào ISO cho người dùng thường.

## 7 Trung tâm ứng dụng và trải nghiệm

UX-001 P1: ứng dụng hiển thị tên, nhà cung cấp, mode, bản/build, tình trạng kiểm thử, giới hạn, quyền truy cập, dung lượng, giấy phép, kết nối Internet cần hay không và ngày xác nhận. Nội dung quan trọng phải đọc được bằng tiếng Việt; mã lỗi kỹ thuật đặt ở phần chi tiết.

UX-002 P0: tách ba loại nhãn: tình trạng tương thích, tình trạng nguồn/bộ cài, và hỗ trợ chính thức của nhà cung cấp. Nhãn “đã kiểm thử” chỉ dùng khi có evidence cho đúng tuple phiên bản. Không dùng huy hiệu giống chứng nhận của Microsoft/MISA.

UX-003 P1: các màn hình tối thiểu gồm Trang chủ, Danh mục, Chi tiết ứng dụng, Chọn chế độ, Lập kế hoạch cài, Tiến trình, Ứng dụng đã cài, Quyền truy cập, Sao lưu khôi phục, Chẩn đoán, Cập nhật và Thông tin phiên bản.

UX-004 P0: người dùng xác nhận trước tải có điều khoản, cài có ảnh hưởng hệ thống, đổi app mặc định, mở quyền thư mục, truy cập micro/camera, xóa dữ liệu, chia sẻ log, ghi USB hoặc định dạng đĩa. Không hỏi lại cho thao tác đọc hay mở app đã được cho phép theo cấu hình.

UX-005 P1: hỗ trợ bàn phím, focus rõ ràng, trình đọc màn hình theo khả năng Qt/KDE, chữ 125/150/200%, màn hình 1366×768 và 1920×1080. Không dùng màu làm tín hiệu duy nhất. Mục tiêu WCAG 2.2 AA cho các bề mặt web do dự án tự viết; desktop đánh giá tác vụ tương đương, không tự tuyên bố đạt chứng nhận web.

UX-006 P1: tìm ứng dụng không phân biệt hoa/thường, ưu tiên khớp tên tiếng Việt có dấu và không dấu. Không sửa tên tệp thật chỉ để phục vụ tìm kiếm. Username hệ thống có thể là ASCII nhưng tên hiển thị hỗ trợ Unicode.

UX-007 P1: khi app không chạy được: giải thích ngắn, giữ log, nút thử lại an toàn, xem chẩn đoán, phục hồi cấu hình trước, mở hướng dẫn. Gợi ý mode khác cần nêu dữ liệu và chi phí liên quan; không tự thay thế phần mềm.

Ví dụ thông báo: “Chưa kiểm thử Excel build này. Bạn có thể thử trong môi trường riêng với bản sao tài liệu.”; “Bản web cần Internet và có thể thiếu chức năng bạn đang dùng.”; “Không đủ dung lượng để cài. Cần thêm dung lượng cho bộ cài và bản phục hồi.”

## 8 Tiếng Việt và dữ liệu người dùng

VN-001 P0: giao diện lõi, trình cài đặt và hướng dẫn phổ thông có tiếng Việt. Dùng UTF-8 toàn tuyến; locale mặc định vi_VN.UTF-8 và múi giờ Asia/Ho_Chi_Minh nhưng cho phép đổi.

VN-002 P0: Telex/VNI được kiểm thử trong Qt, GTK, trình duyệt, ứng dụng Wine 32/64-bit thực tế. Kiểm tra gõ nhanh, dấu kép, xóa dấu, dấu tự do, copy/paste, chuyển bộ gõ, ô mật khẩu và phím tắt. Không log nội dung gõ.

VN-003 P0: tập tên thử có `Đỗ Chí Cường`, `Báo cáo tháng 11`, khoảng trắng, Unicode NFC và NFD, tên dài và ký tự hợp lệ đặc biệt. Linux phân biệt hoa/thường; Windows có quy tắc khác. Không âm thầm chuẩn hóa, gộp hoặc ghi đè hai tên khác nhau. Nếu xung đột, hỏi cách xử lý và giữ bản gốc.

VN-004 P1: ngày hiển thị dd/MM/yyyy và giờ 24h khi phù hợp locale; dữ liệu máy dùng ISO 8601 có timezone. Phải kiểm thử số thập phân, phân cách hàng nghìn, danh sách công thức và CSV dấu phẩy/dấu chấm phẩy. Không đổi locale toàn hệ thống chỉ để chữa một ứng dụng; ưu tiên override theo profile.

VN-005 P1: font có quyền phân phối và đủ glyph tiếng Việt. Tài liệu dùng font thiếu phải báo thay thế. Không tự sao chép font Microsoft từ máy khác vào ISO. So sánh bố cục tài liệu với font đúng quyền dùng trên môi trường đối chiếu.

DATA-001 P0: không ghi đè tài liệu khi chuyển định dạng. Các file mở lần đầu bằng engine khác có bản sao trước khi chỉnh sửa hoặc tùy chọn “Lưu thành”. Dữ liệu người dùng tách khỏi prefix và cache; cập nhật/gỡ ứng dụng mặc định giữ dữ liệu.

DATA-002 P0: import từ Windows là luồng sao chép có báo cáo, không di chuyển/xóa mặc định. Chặn ghi vào NTFS đang hibernated/Fast Startup hoặc volume có lỗi; không tự mở BitLocker và không ghi khóa khôi phục vào log. Hiển thị nguyên nhân và hướng dẫn xử lý trên môi trường được hỗ trợ.

## 9 Bộ điều phối Wine

COMP-001 P0: mỗi người dùng, ứng dụng, phiên bản major và profile có prefix riêng; metadata ghi runner, hash profile, snapshot gói và mode. Không chạy `wine` hay bộ cài ứng dụng bằng root.

COMP-002 P0: capability probe quyết định cách hỗ trợ Windows 32-bit. Kiểm tra runner có new WoW64 hay cần gói i386 truyền thống; không luôn thêm multiarch, không giả định prefix 64-bit chạy mọi app 32-bit. Ghi chiến lược và kết quả vào hồ sơ.

COMP-003 P0: runner nằm dưới thư mục versioned bất biến sau cài; cập nhật runner không tự migrate toàn bộ prefix. Clone cấu hình sang vùng thử và chạy smoke test; chỉ chuyển sau khi người dùng đồng ý khi có thay đổi tương thích. Giữ lựa chọn quay về nếu format prefix còn tương thích.

COMP-004 P0: recipe là các hành động khai báo có allowlist như tạo prefix, cài dependency đã xét duyệt, đặt registry key trong danh sách, chạy installer người dùng cung cấp và tạo launcher. Không hỗ trợ `shell`, `eval`, URL script hoặc template nội suy thành lệnh. Dùng argv array; không ghép tên tệp thành shell command.

COMP-005 P0: mỗi prefix có mutex; thao tác install/repair/update/remove xếp hàng. Launch được phép khi profile ở READY; từ chối đổi prefix khi app còn chạy trừ khi flow dừng ứng dụng đã được xác nhận. Khóa theo người dùng; không để một người sửa prefix của người khác.

COMP-006 P0: launcher lưu ứng dụng và profile ID, không nhúng mật khẩu, URL tải một lần hoặc lệnh thực thi tùy ý. Tệp .exe từ Internet không tự chạy khi click: hiển thị nguồn, trạng thái và lựa chọn môi trường thử.

COMP-007 P1: hỗ trợ font, DLL override, DPI, locale, print và liên kết tệp theo profile; mọi override ghi vào metadata và xuất được. Không sửa `/usr`, global registry hay prefix khác để chữa một ứng dụng.

COMP-008 P0: chạy chương trình Windows là thực thi mã không tin cậy. Prefix chỉ tổ chức môi trường, không phải ranh giới bảo mật. Gỡ drive Z là một biện pháp giảm tiếp xúc, không đủ sandbox. Profile phải khai báo mức cách ly và các ngoại lệ.

## 10 Bảo mật và ranh giới tin cậy

SEC-001 P0: desktop và app chạy dưới tài khoản thường, root không đăng nhập desktop mặc định. Helper chỉ cho các thao tác có kiểu dữ liệu rõ ràng; xác thực danh tính người gọi, Polkit, tham số, đường dẫn và trạng thái hệ thống.

SEC-002 P0: mọi đường dẫn đầu vào xử lý symlink, hardlink, traversal, race TOCTOU, quyền sở hữu, file type và mount. Privileged helper không ghi vào đường dẫn tùy ý do user truyền. Phương án triển khai cần kiểm thử FD-based access và safe directory traversal, không chỉ kiểm tra chuỗi `..`.

SEC-003 P0: sandbox ứng dụng Wine dùng cơ chế Linux được duy trì như bubblewrap/AppArmor với policy cụ thể, không gọi prefix là sandbox. Mặc định chỉ thấy prefix, thư mục staging, runtime chỉ đọc, thiết bị thực sự cần, và thư mục người dùng cấp quyền. Giới hạn truy cập SSH keys, browser profile, token, DB và home khác. D-Bus được lọc; không mount session bus toàn quyền theo mặc định.

SEC-004 P0: mạng, audio, camera, in, clipboard và display được cấp theo hồ sơ có giải thích. Chọn file qua portal hoặc vùng trao đổi file; đường dẫn chỉ có ý nghĩa khi mapping sang Wine được kiểm thử. Truy cập X11/XWayland có rủi ro quan sát/điều khiển phiên; nếu phải nới policy để tương thích, hạ nhãn cách ly và ghi ngoại lệ, không tuyên bố cách ly tuyệt đối.

SEC-005 P0: một ứng dụng bị từ chối vì sandbox không được tự động chạy lại ngoài sandbox. Chế độ thử không cách ly chỉ dành cho QA trên VM dùng dữ liệu giả, có nhãn rõ ràng. Nếu chưa đạt chính sách pilot, ứng dụng không được phát hành dưới nhãn an toàn đã xác nhận.

SEC-006 P0: tải qua HTTPS với kiểm tra TLS; xác minh hash do catalog đáng tin cung cấp và chữ ký nhà cung cấp khi có công cụ phù hợp. Hash đơn lẻ chỉ kiểm tra toàn vẹn so với giá trị kỳ vọng, không chứng minh nhà phát hành. Chặn redirect sang scheme hoặc nguồn ngoài policy; kiểm soát SSRF nếu backend có tải hộ. Không dùng `curl | bash`.

SEC-007 P0: catalog và repo có chữ ký riêng; key production không nằm trong repository, ISO hoặc CI job không tin cậy. Metadata có phiên bản tăng, thời hạn, phạm vi khóa và danh sách thu hồi. Dùng framework ký metadata được duy trì, ưu tiên TUF nếu đáp ứng spike; không tự phát minh giao thức chữ ký. APT tiếp tục xác minh nguồn gói theo cơ chế riêng.

SEC-008 P0: chặn downgrade/metadata replay, fail closed khi chữ ký sai hoặc chứng nhận bị thu hồi. Khi offline cho phép app đã cài chạy theo chính sách đã công bố; không coi metadata hết hạn là xác nhận tương thích mới. Không cho catalog điều khiển lệnh root.

SEC-009 P0: dùng secret service/KWallet phù hợp để lưu bí mật khi thực sự cần. Không truyền mật khẩu qua command line hoặc log; không lưu key Office/Windows hay DB password trong manifest. Không lấy bí mật từ thư mục người dùng để “tự cấu hình”.

SEC-010 P1: firewall mặc định chặn kết nối vào không cần thiết. Không tự mở SQL Server ra Internet, không tạo RDP server mặc định. CUPS/SMB và discovery kiểm thử theo nhu cầu; không hạ TLS, bật SMB1 hay tắt firewall toàn cục để sửa lỗi.

SEC-011 P0: xử lý CVE theo mức ảnh hưởng thực tế. TARGET: triage lỗi nghiêm trọng có khả năng khai thác trong 24 giờ làm việc sau tiếp nhận; mục tiêu bản vá/biện pháp giảm thiểu trong 72 giờ khi khả thi. Đây là mục tiêu nội bộ, chưa phải SLA thương mại. Có kênh báo lỗi, người trực và quy trình thu hồi profile.

SEC-012 P1: mã hóa ổ đĩa là tính năng cần đạt trước pilot chứa dữ liệu nhạy cảm. Phải thử boot, unlock, cập nhật và khôi phục; không tự tuyên bố có mã hóa nếu installer chưa tích hợp. Mã hóa không thay thế backup.

## 11 Hợp đồng dữ liệu

### 11.1 Manifest ứng dụng

`contracts/app-manifest.schema.json` là JSON Schema khởi đầu, không phải manifest có chữ ký production. Mọi thuộc tính không biết bị từ chối. Tách ba lớp: manifest bất biến mô tả app, báo cáo kiểm thử chứa bằng chứng, local state ghi tình trạng trên máy.

Manifest có `schema_version`, `id`, tên, publisher, mode, version/build/architecture, license policy, source policy, runtime, quyền, recipe và compatibility. `compatibility.status` khởi đầu `untested`; `vendor_support` mặc định `unknown`; `last_tested` và `evidence_id` để null. Profile Wine phải nêu runner requirement và kiến trúc prefix; bản mẫu còn TBD không được install.

Validation hai bước: JSON Schema kiểm cấu trúc; semantic validator kiểm điều kiện như Wine cần runner pin, recipe dùng dependency đã duyệt, chứng nhận cần evidence, hash cần đúng payload và trạng thái thu hồi. Không coi “schema hợp lệ” là “an toàn để chạy”.

### 11.2 Trạng thái tương thích

| Trạng thái | Điều kiện |
| --- | --- |
| untested | Chưa có bộ test đủ cho tuple phiên bản |
| experimental | Có bằng chứng chạy một phần, còn lỗi hoặc chưa đủ phạm vi |
| task_verified | Tất cả tác vụ được nêu trong chứng nhận đã đạt trong cấu hình xác định |
| blocked | Tác vụ bắt buộc không đạt hoặc thiếu phụ thuộc ngoài |
| revoked | Chứng nhận/profile bị thu hồi do bảo mật, mất dữ liệu hoặc sai bằng chứng |

Tuple chứng nhận gồm OS build, kernel/graphics khi liên quan, desktop session, runner hash, profile digest, app build/hash/architecture, runtime/dependency versions, bộ dữ liệu, test suite revision và phần cứng hoặc VM config. Kết quả một máy không tự lan sang toàn bộ phần cứng.

Evidence ghi test ID, run ID, commit SHA, lệnh/steps đã chạy, timestamps, dữ liệu giả tham chiếu, expected/actual, result, lỗi, người xác nhận và đường dẫn artifact không chứa bí mật. Không lưu ảnh tài liệu thật. Chứng nhận cần người QA phê duyệt độc lập với việc Claude tự báo pass. Thay đổi tuple quan trọng phải đánh giá lại.

### 11.3 Local state và thư mục

- `~/.config/namios/`: tùy chọn và quyền do người dùng chọn.
- `~/.local/share/namios/prefixes/<app-id>/<instance-id>/`: prefix ứng dụng.
- `~/.local/share/namios/state.sqlite3`: transaction, launcher và trạng thái; không chứa mật khẩu.
- `~/.cache/namios/`: download/staging có TTL và hạn mức; xóa cache không xóa tài liệu.
- `~/.local/state/namios/logs/`: log lọc; mặc định tối đa 100 MB hoặc 14 ngày, giá trị cấu hình được.
- `/usr/share/namios/`: tài nguyên package chỉ đọc.
- `/var/lib/namios/`: metadata hệ thống và cache root với ownership chặt; không dùng làm prefix của user.

Các đường dẫn là layout đề xuất; triển khai phải tôn trọng XDG tương ứng, không hardcode `/home/<name>`. Đường dẫn dữ liệu thật không lấy bằng cách nối chuỗi không kiểm tra.

## 12 Hợp đồng CLI và thao tác đặc quyền

CLI dự kiến: `namios doctor --json`; `namios catalog validate <file>`; `namios app inspect <id> --json`; `namios app plan-install <id> --installer <path>`; `namios app install --plan <plan-id>`; `namios app launch <id> -- <args>`; `namios app repair <id>`; `namios app remove <id>`; `namios evidence validate <report>`; `namios diagnostics export --output <path>`. Đây là giao diện cần xây, không phải hướng dẫn giả định đã cài được.

CLI-001 P0: JSON output có `api_version`, `operation_id`, `status`, `data`, `warnings`, `error`; không trộn log vào stdout JSON. Human output tiếng Việt, mã lỗi ổn định. `--` kết thúc options; đối số app đi qua allowlist/argv, không thành shell.

CLI-002 P0: plan chứa user/host context, profile digest, artifact digests, danh sách thay đổi, dung lượng, permissions và thời hạn. `install` phải xác minh lại vì file và trạng thái có thể đổi sau plan; reject plan sai user, hết hạn hoặc nội dung thay đổi. Xác nhận đặc quyền do Polkit thực hiện theo thao tác cụ thể.

CLI-003 P0: exit code 0 thành công; 2 input/schema sai; 3 thiếu dependency/quyền sử dụng; 4 mạng/xác thực nguồn; 5 không được cấp quyền; 6 xung đột trạng thái/khóa; 7 bị hủy; 8 kiểm tra sau cài thất bại; 9 lỗi nội bộ. Enum là hợp đồng đề xuất, phải có test nhất quán.

CLI-004 P1: helper hỗ trợ các phương thức kiểu `GetSystemCapabilities`, `PlanPackageInstall`, `ApplyApprovedPackagePlan`, `GetUpdateStatus`. Không có `RunCommand`, không cho caller truyền tên repository/key hay danh sách package tùy ý ngoài allowlist đã được phát hành. Các thao tác phân vùng dùng installer chuyên dụng, không qua app-center helper.

## 13 Vòng đời cài đặt và phục hồi

Trạng thái giao dịch: NEW → VALIDATED → ACQUIRING → STAGING → INSTALLING → VERIFYING → READY. Từ các trạng thái đang chạy có thể sang CANCELLING/CANCELLED hoặc FAILED; phục hồi đi qua RECOVERING đến READY hoặc NEEDS_ATTENTION. Gỡ app dùng REMOVING → REMOVED và mặc định giữ dữ liệu. SQLite transaction chỉ bảo vệ metadata; không biến thay đổi ngoài filesystem thành giao dịch nguyên tử.

TX-001 P0: mỗi bước ghi journal trước/sau với operation ID. Restart sau mất điện phát hiện giao dịch dở, kiểm tra thực tế và đưa ra tiếp tục/cleanup an toàn. Không đánh dấu READY chỉ vì installer exit 0.

TX-002 P0: staging trên cùng filesystem nếu cần atomic rename. Kiểm tra dung lượng cho installer, unpack, prefix và bản phục hồi; không chỉ tính kích thước file tải. Có quota và xử lý hết đĩa giữa chừng.

TX-003 P0: không kill installer rồi khẳng định đã rollback. Phải nêu hành động bù cho mỗi bước; khi không đảm bảo hoàn nguyên, chuyển NEEDS_ATTENTION, giữ log và hướng dẫn. Không xóa staging chứa dữ liệu duy nhất.

TX-004 P0: trước thay đổi lớn phải dừng ứng dụng và tiến trình nền liên quan, snapshot/copy prefix nhất quán. DB và tài liệu người dùng sao lưu riêng theo ứng dụng; không rollback dữ liệu nghiệp vụ cùng runner một cách âm thầm.

TX-005 P1: gỡ app tách lựa chọn xóa prefix, cache, launcher và dữ liệu; mặc định chỉ xóa chương trình/launcher. Xóa dữ liệu cần hiển thị chính xác phạm vi và xác nhận riêng. Không dùng glob không kiểm soát hoặc đường dẫn lấy trực tiếp từ manifest.

## 14 Build ISO và cài hệ điều hành

BUILD-001 P0: repository có cấu hình live-build, package lists, hooks được review, asset có giấy phép, script build và script boot test. Dùng build host/VM Linux amd64 sạch. Trên macOS/Windows, Claude tạo hướng dẫn build Linux VM/runner; không giả vờ tạo ISO hợp lệ bằng đổi đuôi archive.

BUILD-002 P0: khóa OS snapshot, package versions, runner, dependency và source commits trong build manifest. Snapshot dùng để tái tạo build lịch sử; image phát hành mới vẫn phải cập nhật bảo mật theo cadence. Không pin snapshot cũ vô thời hạn cho máy người dùng.

BUILD-003 P0: artifact gồm ISO, SHA256SUMS, chữ ký tách rời, SBOM SPDX hoặc CycloneDX, package list, source references, build log, test report và release notes. Key production chỉ được đưa vào bước ký của maintainer; Claude được dùng key phát triển có nhãn rõ trong lab.

BUILD-004 P1: mục tiêu tái tạo được cùng bộ package và cấu hình trước; bit-for-bit reproducible ISO là mục tiêu sau. Nếu timestamps, mirror hoặc tooling còn gây sai khác, ghi rõ, không tự gọi là reproducible byte-for-byte.

INSTALL-001 P0 alpha: Live mode thử không ghi ổ trong. Cài đặt trên đĩa ảo trắng phải có preview, chọn đúng thiết bị, xác nhận định dạng, tạo user, locale, bootloader và reboot thành công. Bước ghi đĩa chỉ chạy sau xác nhận rõ đĩa đích.

INSTALL-002 P1: UEFI bắt buộc trên danh sách phần cứng pilot; Legacy BIOS là tùy chọn. Secure Boot phải có chuỗi tin cậy bootloader/kernel/module được thử trên máy thật; không suy ra có Secure Boot chỉ vì dùng shim upstream. Nếu chưa đạt, alpha ghi rõ giới hạn và không hướng dẫn tắt âm thầm tính năng bảo mật.

INSTALL-003 P1: dual boot chưa nằm trong đường cài mặc định v1. Chỉ mở khi có test resize, BitLocker, Fast Startup, boot entry và phục hồi trên thiết bị thử; luôn yêu cầu backup trước thay đổi phân vùng. Không tự thu nhỏ ổ Windows của người dùng.

INSTALL-004 P1: tài khoản local hoạt động không cần tài khoản cloud. Người dùng tự đặt password, không có mật khẩu admin mặc định dùng chung. Live user nếu cần phải tách hoàn toàn và không tồn tại sau cài; SSH không bật mặc định.

## 15 Cập nhật và vòng đời hỗ trợ

UPD-001 P0 alpha: cập nhật hệ thống qua APT; catalog/profile qua metadata có chữ ký và kiểm tra thu hồi. App tự cập nhật phải được phát hiện; không gộp mọi updater vào một cơ chế giả định kiểm soát được.

UPD-002 P0: không cập nhật runner đang dùng tại chỗ; staging runner mới, thử profile rồi mới thay tham chiếu. Package update có thể cần reboot; giữ kernel cũ theo policy dung lượng. Snapshot filesystem là lớp bổ sung nếu đã kiểm thử boot/rollback, không thay backup.

UPD-003 P0: phân biệt rollback package, rollback OS snapshot, rollback prefix, restore dữ liệu, và khôi phục DB. APT downgrade không đảm bảo hoàn nguyên migration. Release notes phải chỉ rõ bước nào có thể đảo ngược và bước nào cần restore từ backup.

UPD-004 P1: kênh development → alpha → pilot → stable; artifact promoted giữ nguyên digest, không rebuild khác nội dung rồi dùng lại chữ ký/chứng nhận. Catalog có kênh tương ứng và không tự đưa experimental vào stable.

UPD-005 P1: mỗi release có ngày hỗ trợ bắt đầu/kết thúc, thành phần không còn hỗ trợ, người bảo trì và phương án chuyển đổi. Vòng đời upstream Debian không tự trở thành cam kết đội NaMiOS. Ứng dụng EOL không được chứng nhận mới để làm đường vòng giá rẻ.

## 16 Phần cứng và hiệu năng

| Cấu hình TARGET | Phạm vi | Mục tiêu |
| --- | --- | --- |
| Intel hoặc AMD x86-64 2 nhân RAM 4 GB SSD trống 40 GB | Core Linux nhẹ; không bảo đảm VM/Office thương mại | Boot desktop và bộ tác vụ cơ bản |
| CPU 4 nhân RAM 8 GB SSD 128 GB còn trống đủ staging | Wine và văn phòng pilot | Cấu hình tham chiếu chính |
| CPU có VT-x/AMD-V RAM 16 GB SSD trống tối thiểu 100 GB cho cấu hình lab | Windows VM tùy chọn | Tài nguyên guest phải theo yêu cầu OS/app thực, không coi đây là bảo đảm đủ cho mọi workload |

PERF-001 P1: trên cấu hình tham chiếu chính, cold boot từ SSD tới desktop dùng được p95 ≤60 giây; idle 5 phút sau login RAM ≤2 GB theo metric định nghĩa trong test; app-center cold start p95 ≤3 giây. Đo ít nhất 20 lần, ghi firmware/kernel/session, cache state và background services; thất bại phải báo số đo, không sửa ngưỡng ngầm.

PERF-002 P1: thao tác tìm catalog local ≤300 ms ở p95 với 1.000 records trên máy tham chiếu; UI không treo khi tải/cài. Download không có SLA thời gian vì phụ thuộc mạng; có tiến trình và hủy an toàn.

PERF-003 P1: đo Word/Excel bằng cùng tập dữ liệu trên máy tương đương Windows reference. Trước tiên so tính đúng; sau đó báo tỷ lệ thời gian/RAM. Không tuyên bố Wine nhanh hơn hoặc nhẹ hơn Windows khi chưa đo.

HW-001 P1: danh sách pilot tối thiểu 5 cấu hình vật lý có Intel/AMD và các GPU tích hợp thực tế, tối thiểu 2 mẫu máy in khác hãng/model được xác định. Đây là độ phủ thử nghiệm, không đại diện toàn bộ thị trường.

HW-002 P1: test Wi-Fi, Ethernet, Bluetooth nếu có, audio, webcam, HDMI, sleep/resume 20 chu kỳ, khóa màn hình, pin, phím chức năng, DPI và đa màn hình. Driver Windows không mặc nhiên chạy Linux. NVIDIA rời, Wi-Fi hiếm và thiết bị chuyên dụng là profile riêng.

HW-003 P1: in tiếng Việt từ Linux và ứng dụng Wine qua CUPS, khổ A4, hai mặt nếu thiết bị có, font, orientation và PDF. Scan dùng driver Linux phù hợp. Không suy ra máy in đạt vì in được trang test của CUPS.

## 17 Sao lưu và hỗ trợ

BACK-001 P0: trước thử app thương mại, dùng bản sao dữ liệu và backup đã restore thử. Backup người dùng có manifest, version, checksum, tùy chọn mã hóa và hướng dẫn giữ khóa. Không để khóa mã hóa trong cùng archive mặc định.

BACK-002 P1: cung cấp thao tác export/import cấu hình NaMiOS và profile có lọc bí mật. Export prefix có thể chứa token/bản quyền; mặc định không đưa vào gói hỗ trợ. Không hỗ trợ chuyển activation sang máy khác nếu nhà cung cấp không cho phép.

SUP-001 P0: telemetry mặc định tắt. Xuất log là thao tác do người dùng yêu cầu, có preview và lọc. Không tự gửi email, chat, báo lỗi public hoặc tải dữ liệu lên server.

SUP-002 P1: bộ chẩn đoán có OS build, app/profile/runner versions, package errors, thiết bị đã ẩn serial, session type và sandbox mode. Loại username, đường dẫn tài liệu, hostname riêng, IP nội bộ khi không cần, token, mật khẩu và nội dung file. Regex lọc không đủ bảo đảm: có test dữ liệu nhạy cảm và bước xem trước.

SUP-003 P1: tài liệu cho người dùng gồm thử Live USB, sao lưu, cài đặt, bộ gõ, phần mềm thay thế, phần mềm Windows, cập nhật, khôi phục và giới hạn. Có danh sách vấn đề đã biết và cách lấy lại quyền truy cập dữ liệu nếu app không chạy.

## 18 Chiến lược kiểm thử và bằng chứng

### 18.1 Các tầng kiểm thử

Unit test cho validator, plan, policy, state machine, path handling và redaction. Integration test dùng Wine trong Linux VM, prefix và fixture tự viết. System test build/boot/install/update/recovery trên đĩa ảo. App test chạy bản phần mềm có quyền dùng trong môi trường tách biệt. UAT có người dùng thật nhưng tài liệu/DB giả hoặc đã khử định danh được cho phép.

Không coi mock/stub là bằng chứng ứng dụng thương mại chạy được. CI không có GUI, KVM, bộ cài hay credentials phải báo blocked/skipped có lý do. Không được đổi skipped thành pass để vượt gate. Một test lỗi vì môi trường khác test app lỗi; cả hai đều chưa tạo bằng chứng đạt.

### 18.2 Bộ dữ liệu bắt buộc

`WORD`: 12 tài liệu tự tạo có quyền dùng, gồm văn bản tiếng Việt, bảng, ảnh, nhiều section, công thức, mục lục, tracked changes và in; mỗi file có expected behavior và bản PDF đối chiếu.

`EXCEL`: 15 workbook tự tạo có giá trị kỳ vọng, gồm công thức cơ bản, lookup, ngày tháng, locale/CSV, pivot/chart, liên kết và nhóm VBA/add-in tách riêng. Nếu macro không nằm trong điều kiện pilot thì ghi ngoài phạm vi, không xóa ca kiểm thử khỏi báo cáo chung.

`MISA`: một doanh nghiệp giả lập, danh mục, số dư đầu kỳ, tập chứng từ mẫu đã được kế toán xác nhận, báo cáo kỳ vọng và quy trình backup/restore. Không dùng kết quả tài chính thật làm fixture public.

`DOTNET`: tối thiểu mẫu console đa nền tảng, ASP.NET Core, WinForms Framework, WPF Framework, WinForms hiện đại, WPF hiện đại, app P/Invoke, COM và service. Source mẫu tự viết và quyền dùng rõ; test app mẫu không thay cho app thương mại tương tự.

`FILES`: cây thư mục Unicode, tên dài, khoảng trắng, symlink, file readonly, collision case/NFC/NFD, dữ liệu quá kích thước và tệp lỗi định dạng. Mẫu tấn công chỉ dùng an toàn trong lab, không chứa mã phá hoại.

### 18.3 Nghiệm thu ứng dụng

Mỗi application-mode-version có một bộ tác vụ bắt buộc do product owner chốt và được ký tên trong báo cáo. 100% tác vụ bắt buộc phải đạt, không có lỗi mất/sai dữ liệu và không còn P0/P1 trong phạm vi công bố. Tính năng tùy chọn chưa đạt ghi rõ. Chạy lại tác vụ lưu/mở ít nhất 10 vòng và tối thiểu một buổi UAT 2 giờ cho ứng dụng nghiệp vụ; thời lượng này là mức sàng lọc, không chứng minh độ tin cậy dài hạn.

Regression bắt buộc khi đổi OS base, Wine, runtime, app build, profile, sandbox, bộ gõ, font hoặc trình duyệt có ảnh hưởng. Có báo cáo delta để tập trung test nhưng không bỏ kiểm thử dữ liệu trọng yếu.

### 18.4 Gate phát hành

- G0 khả thi: một Wine fixture hoạt động, đường phân tích .NET đúng, report cho từng ứng dụng mục tiêu thể hiện pass/fail/blocked/untested và quyết định tiếp tục. Chưa cần mọi app thương mại chạy được.
- G1 alpha kỹ thuật: ISO boot Live, cài/reboot trong VM, chạy app-center và fixture, journal phục hồi, không root Wine, schema/path/signature negative tests đạt.
- G2 pilot nghiệp vụ: danh sách build/mode được chốt, tất cả tác vụ bắt buộc của nhóm pilot đạt, backup/restore, phần cứng, cập nhật và hỗ trợ có người chịu trách nhiệm. Nếu yêu cầu pilot bắt buộc Microsoft desktop hoặc SME chạy Wine mà chưa đạt, G2 bị chặn cho nhóm đó.
- G3 phát hành công khai: kiểm toán quyền phân phối, metadata/package ký production, công bố nguồn/nghĩa vụ giấy phép, support/EOL, ma trận tương thích công khai và quy trình tiếp nhận lỗi. Không được gọi alpha là stable.

Danh sách test chi tiết trong `qa/test-matrix.csv`. Những dòng chưa chạy phải giữ `not_run`. Không có ứng dụng nào được đánh dấu thành công trước khi có run evidence.

## 19 Cấu trúc repository cần triển khai

Đây là cấu trúc đề xuất cho source sản phẩm; gói tài liệu hiện tại chỉ chứa đặc tả và hợp đồng mẫu.

```text
namios-os/
  CLAUDE.md
  README.md
  docs/adr/ docs/specs/ docs/runbooks/ docs/releases/
  distro/live-build/ distro/packages/ distro/branding/
  src/namios_compat/ src/namios_doctor/
  src/namios_app_center/ src/namios_system_helper/
  catalog/manifests/ catalog/recipes/ catalog/revocations/
  contracts/ fixtures/dotnet/ fixtures/documents/
  tests/unit/ tests/integration/ tests/system/ tests/security/
  qa/plans/ qa/reports/ qa/evidence-index/
  packaging/debian/ scripts/ ci/
```

REPO-001 P0: thông tin trạng thái nằm trong `docs/STATUS.md`, quyết định kỹ thuật trong ADR, việc còn lại trong backlog. Không để lý do quan trọng chỉ tồn tại trong hội thoại Claude. README phân biệt phần thực có với roadmap.

REPO-002 P0: không commit ISO, bộ cài thương mại, khóa ký production, dữ liệu thật, prefix chứa credentials hoặc token. Dùng artifact storage phù hợp cho binary có quyền phân phối; Git chứa metadata và source.

REPO-003 P1: CI lint/format/typecheck, unit/security tests, schema validation, license/SBOM checks, package build và Linux integration. Build ISO/KVM nằm ở job có tài nguyên/quyền thích hợp, tách CI không tin cậy khỏi khóa phát hành.

## 20 Kế hoạch triển khai theo mốc

### M0 Khảo sát và đóng băng giả định

Đầu ra: inventory môi trường, dependency/support matrix có nguồn/ngày tra cứu, phiên bản ứng dụng còn TBD được ghi rõ, ADR nền tảng, threat model sơ bộ, backlog và kế hoạch QA. Không cần mua license hay đăng nhập dịch vụ để hoàn thành phần hạ tầng này. Gate: không có tuyên bố tương thích chưa có bằng chứng; xác định build host khả dụng.

### M1 Hạt nhân phần mềm riêng

Đầu ra: Python package, CLI doctor, schema và semantic validator, catalog local, state store và unit tests. Recipe fixture vô hại chạy dry-run, không cài Office/MISA. Gate: invalid schema/path/command/permission bị từ chối, JSON output ổn định, không ghi ngoài workspace cho phép.

### M2 Thử nghiệm Wine và .NET

Đầu ra: runner detection/pin, prefix isolation, sandbox proof, transaction recovery, fixture Win32/.NET, compatibility reports. Thu thập bộ cài mục tiêu có quyền dùng khi có; nếu thiếu giữ BLOCKED và tiếp tục phần độc lập. Gate: fixture chạy thật và negative tests đạt; kết luận ban đầu cho từng app-mode.

### M3 ISO và desktop tiếng Việt

Đầu ra: live-build config, metapackage, Fcitx5/font settings, app-center tối thiểu, ISO thực, QEMU boot/install evidence và package/SBOM. Gate G1; sửa lỗi tích hợp trước thêm tính năng trang trí.

### M4 Ứng dụng và pilot

Đầu ra: hồ sơ phiên bản cụ thể, tác vụ nghiệp vụ, bằng chứng Office/Zalo/MISA/.NET theo mode, hardware tests, backup/restore, update/signing, hướng dẫn. Gate G2 cho phạm vi công bố, không gom app thất bại vào bản web để báo hoàn thành desktop.

### M5 Duy trì phát hành

Đầu ra: kênh stable, keys và quy trình rotation/revocation, người bảo trì, lịch cập nhật, runbooks, phản hồi pilot, báo cáo quyền phân phối và nguồn tương ứng. Gate G3. Không bắt đầu bán dịch vụ SLA khi chưa có người và năng lực đáp ứng.

Không ấn định lịch hoàn thành trước spike. Đội dự kiến cần năng lực Linux/release, desktop/application, security/QA và một người am hiểu nghiệp vụ kế toán; một người có thể kiêm nhiệm nhưng kiểm chứng ứng dụng và trách nhiệm vận hành không thể giao hoàn toàn cho AI. Miễn phí cho người dùng vẫn có chi phí kỹ thuật, hạ tầng, chữ ký, kiểm thử và hỗ trợ.

## 21 Rủi ro và quyết định dừng

| Rủi ro | Dấu hiệu | Cách xử lý | Điều kiện chặn |
| --- | --- | --- | --- |
| Office desktop không cài/kích hoạt/chạy ổn qua Wine | Lỗi Click-to-Run, rendering, macro, update | Báo build cụ thể; thử hướng hợp lệ; web/VM tách riêng | Chặn pilot yêu cầu desktop Wine nếu tác vụ bắt buộc chưa đạt |
| MISA SME phụ thuộc Windows sâu | SQL client, report, COM, ký số lỗi | Test client-server với dữ liệu giả; phối hợp vendor khi được phép | Chặn kế toán sản xuất nếu sai số/liệu hoặc không restore được |
| Ứng dụng tự cập nhật phá profile | App digest thay đổi | Gỡ nhãn chứng nhận của build mới, kiểm thử lại | Không giữ nhãn cũ cho binary mới |
| Sandbox bị nới để đạt tương thích | Mount home, bus hoặc display quá rộng | Đánh giá ngoại lệ, thu hẹp hoặc VM | Không phát hành dưới nhãn cách ly đã xác nhận |
| Đội không đủ khả năng duy trì distro | Bỏ cập nhật, không trực lỗi | Giảm phạm vi, dùng upstream nhiều hơn | Không công bố stable nếu thiếu người bảo trì |
| Dữ liệu bị sai hoặc mất | Excel sai giá trị, DB lỗi, file hỏng | Dừng rollout, giữ bằng chứng, restore và thu hồi profile | P0 chặn phát hành |
| Driver/token không có Linux support | Thiết bị không nhận hoặc middleware lỗi | Chọn thiết bị được xác nhận hoặc Windows hợp lệ | Không tuyên bố mọi phần cứng tương thích |
| Chi phí VM/cloud đi ngược mục tiêu miễn phí | Phải mua/thuê Windows cho đa số tác vụ | Công bố chi phí và phân nhóm người dùng | Không quảng bá nhánh này là không cần giấy phép Windows |

Nếu chủ dự án yêu cầu đồng thời “không mua Windows”, “mọi Word Excel MISA desktop hiện có chạy nguyên vẹn” và “không đổi quy trình”, đây là giả thuyết phải kiểm chứng, không phải ba điều kiện có thể tự bảo đảm bằng Claude Code. Báo cáo no-go hoặc phạm vi hẹp hơn là đầu ra hợp lệ khi bằng chứng cho thấy giới hạn.

## 22 Thông tin cần chủ dự án bổ sung trong quá trình làm

1. Word/Excel: edition, build, 32/64-bit, phương thức cấp phép, macro/add-in/Power Query bắt buộc.
2. MISA: SME năm/build hay AMIS, mô hình DB, SQL version, báo cáo, hóa đơn và nhà cung cấp chữ ký số.
3. Ứng dụng .NET: tên, bộ cài hoặc source có quyền dùng, runtime, phụ thuộc thiết bị và tác vụ bắt buộc.
4. Máy pilot: model, CPU, RAM, GPU, Wi-Fi, printer/token và nhu cầu dual boot.
5. Đội triển khai, nguồn lực bảo trì, nhóm người dùng đầu tiên và mức chấp nhận dùng web/ứng dụng thay thế.

Các câu hỏi này không chặn M0/M1 và fixture M2. Chúng chặn việc chứng nhận ứng dụng thương mại hoặc phát hành pilot chưa đủ dữ liệu. Claude phải gom câu hỏi thực sự cần thiết, chỉ yêu cầu khi bước phụ thuộc sắp bắt đầu, và tiếp tục phần độc lập.

## 23 Yêu cầu giao việc cho Claude Code

Đọc toàn bộ tài liệu, README, CLAUDE.md, contracts, backlog và test matrix trước khi sửa source. Kiểm tra workspace và AGENTS.md hiện có; không ghi đè dự án khác. Đưa ra inventory và bước tiếp theo ngắn gọn, sau đó triển khai M0/M1 trong cùng phiên nếu môi trường cho phép.

Không chỉ trả một kế hoạch hay mockup. Phải có source chạy được cho phạm vi hiện tại, test đã chạy, log và hướng dẫn tái hiện. Tuy nhiên không được bịa môi trường Linux, build ISO, test thương mại hoặc kết quả pass nếu chưa thực hiện. Khi blocked, ghi chính xác nguyên nhân, phần đã làm, phần còn lại và điều kiện mở khóa.

Mọi mốc báo cáo gồm: commit/source revision; thay đổi; lệnh đã chạy và kết quả thực; artifact/path; lỗi còn lại; app compatibility theo mode; rủi ro dữ liệu; bước tiếp theo. Không tối ưu trang trí trước chứng minh Wine/.NET và cập nhật/phục hồi. Không tự gửi liên hệ nhà cung cấp, thanh toán, mua license, đăng nhập tài khoản hoặc phát hành public.

Tiêu chuẩn hoàn thành một task: đáp ứng requirement IDs, test liên quan đạt hoặc blocked rõ, không có TODO giả làm chức năng, tài liệu cập nhật và không có dữ liệu/bí mật bị đưa vào source. Các tài liệu mẫu trong gói này là khởi điểm cần hiện thực hóa, không phải hệ điều hành đã được viết.

## 24 Nguồn tham khảo và phạm vi chứng cứ

Ngày đối chiếu 02/11/2026. Chỉ dùng tài liệu chính thức làm căn cứ nền; tính tương thích thực phải do test dự án xác nhận. Nội dung tóm tắt dưới đây không xác nhận điều khoản cụ thể cho mọi edition hoặc quyền sử dụng của người dùng.

- [S01 Microsoft về sử dụng và phân phối nội dung có bản quyền](https://www.microsoft.com/en-us/legal/intellectualproperty/copyright/permissions) — cần quyền phù hợp để sửa đổi/phân phối; phần mềm tải công khai không mặc nhiên được phân phối lại.
- [S02 Wine giới thiệu dự án](https://www.winehq.org/about/) — cơ chế lớp tương thích và hoạt động của dự án; không chứng minh một build ứng dụng riêng chạy được.
- [S03 Zalo PC](https://www.zalo.me/pc) — điểm vào chính thức cho PC/Web; khả năng cụ thể từng mode cần kiểm thử.
- [S04 MISA SME kiểm tra cấu hình](https://helpsme.misa.vn/2026/kb/kiem-tra-cau-hinh-may-tinh-truoc-khi-cai-dat-sme/) — mô hình client-server/SQL Server và điều kiện hệ thống; không là bằng chứng Wine hỗ trợ.
- [S05 MISA AMIS Kế toán truy cập web](https://helpact.misa.vn/kb/cach-mo-nhanh-amis-ke-toan-tu-taskbar-hoac-desktop/) — cách truy cập chính thức; không chứng nhận mọi browser trên Linux.
- [S06 MISA về công cụ ký số và quyền trình duyệt](https://helpamis.misa.vn/amis-thue-tncn/kb/huong-dan-thiet-lap-quyen-tren-trinh-duyet-web-de-ket-noi-duoc-ung-dung-misa-kyso-khi-ky-to-khai-chung-tu/) — ví dụ nghiệp vụ web còn liên quan công cụ cục bộ; không suy rộng điều kiện của một sản phẩm sang mọi MISA.
- [S07 Microsoft WPF](https://learn.microsoft.com/en-us/dotnet/desktop-wpf/overview/index) — WPF chạy trên Windows dù .NET có tính đa nền tảng.
- [S08 Microsoft về .NET Framework](https://github.com/dotnet/docs/blob/main/docs/framework/install/on-windows-and-server.md) — .NET Framework khác .NET hiện đại và là công nghệ Windows.
- [S09 Debian 13 trixie](https://www.debian.org/releases/trixie/) — nền tảng và vòng đời upstream; không là cam kết bảo trì NaMiOS hoặc mọi gói.
- [S10 Debian Live Manual](https://live-team.pages.debian.net/live-manual/html/live-manual.en.html) — công cụ và cấu hình tạo ảnh Live.
- [S11 Microsoft cài .NET trên Linux](https://learn.microsoft.com/en-us/dotnet/core/install/linux) — cài runtime/SDK trên bản phân phối phù hợp; không đồng nghĩa chạy mọi executable Windows.
- [S12 ReactOS tải về](https://reactos.org/download/) — dự án còn alpha tại thời điểm tra cứu; không chọn làm nền pilot nghiệp vụ.
- [S13 Yêu cầu Microsoft 365](https://support.microsoft.com/en-us/accounts-billing/subscriptions/microsoft-365-system-requirements) — đối chiếu trình duyệt/hệ thống cho từng dịch vụ; điều kiện có thể thay đổi.

## 25 Danh mục đầu ra và giới hạn của gói tài liệu

Gói đi kèm có đặc tả này, lệnh khởi động Claude, quy tắc CLAUDE.md, backlog, danh sách test, schema manifest, profile mẫu chưa kiểm thử, schema bằng chứng, mẫu báo cáo và ADR. Đây là bộ đầu vào phát triển, không chứa bộ cài Windows/Office/MISA, source của các sản phẩm đó, key kích hoạt, ISO hay phần mềm NaMiOS đã triển khai.

Các schema minh họa chủ đích chặn profile còn TBD ở lớp semantic validator; việc file mẫu parse được không cho phép cài production. Tài liệu không xác nhận bản quyền nhãn NaMiOS, không thay thế thỏa thuận giấy phép cụ thể và không xác nhận bất kỳ tương thích ứng dụng nào khi chưa có test.

## 26 Bổ sung định hướng sản phẩm và quyền sở hữu NaMiOS

OWN-001 P0: tên sản phẩm thống nhất là **NaMiOS** trong giao diện, bộ cài, tài liệu, website, gói phần mềm và báo cáo. Ông **Đỗ Chí Cường và Đỗ Bảo Nam** là hai nhà sáng lập và chủ dự án NaMiOS. Thông tin này không được dùng để tuyên bố họ sở hữu mã nguồn Debian, Linux, KDE, Wine hoặc tài sản của bên thứ ba. Hợp đồng lao động, cộng tác, đóng góp mã và chuyển giao quyền đối với phần phát triển riêng phải quy định rõ chủ thể pháp lý sở hữu, quyền cấp phép và quyền sử dụng tên NaMiOS trước khi phát hành.

OWN-002 P1: giao diện About thể hiện tên NaMiOS, phiên bản, hai nhà sáng lập, tên pháp nhân phát hành nếu đã xác lập, giấy phép các thành phần, liên hệ hỗ trợ và nguồn mở tương ứng. Không dùng tên Windows trong thương hiệu hệ điều hành, chỉ dùng khi mô tả khả năng tương thích. Kiểm tra tên miền và nhãn hiệu trước khi công bố rộng rãi; trạng thái tra cứu phải được ghi, không tự xem việc đặt tên trong tài liệu là đăng ký bảo hộ.

OWN-003 P0: hệ điều hành có quyền miễn phí sử dụng theo điều khoản phân phối dự án; các dịch vụ hỗ trợ, kho ứng dụng bên thứ ba hoặc ứng dụng thương mại nếu có phải công bố điều kiện riêng. Các phần do dự án viết cần hồ sơ tác giả và nguồn gốc rõ để hai nhà sáng lập có thể quản trị dài hạn.

## 27 Tương thích thiết bị và driver

Một driver `.sys` dành cho nhân Windows không mặc nhiên nạp hoặc hoạt động trên nhân Linux. NaMiOS phải dùng driver Linux, giao thức tiêu chuẩn, giải pháp được nhà sản xuất hỗ trợ hoặc phát triển driver Linux có quyền và tài liệu kỹ thuật. Wine là giải pháp chạy ứng dụng, không phải giải pháp bao phủ mọi driver phần cứng. Tài liệu phát hành không được dùng câu “mọi thiết bị kết nối đều chạy” khi không có ma trận model và chức năng.

DEV-001 P0: xây **cơ sở dữ liệu thiết bị** theo vendor ID, product ID, revision, firmware, phương thức kết nối, bản kernel, driver/backend, giấy phép, chức năng đã thử, trạng thái hỗ trợ và người xác nhận. Hệ thống nhận diện thiết bị phải hiển thị kết quả đúng model và đường dẫn xử lý khi thiếu hỗ trợ; không tải driver từ nguồn lạ. Một nhà sản xuất có nhiều model, không dùng kết quả của model A để chứng nhận model B.

DEV-002 P0: ưu tiên giao thức in chuẩn IPP Everywhere, AirPrint hoặc Mopria qua CUPS; thử IPP over USB cho máy in tương thích. Thiết bị cũ có thể cần Printer Application hoặc driver Linux chính thức theo model. Khả năng nhận máy in và khả năng in đúng nghiệp vụ là hai phép thử khác nhau. In từ Wine phải được kiểm thử cả ánh xạ printer, khổ A4/A5, hai mặt, khay giấy, số bản, lề, font Việt, ảnh, mã vạch/QR và PDF. Các nguồn chính thức [S14] và [S15] mô tả đường in không cần driver truyền thống; chưa xác nhận bất kỳ model cụ thể nào của NaMiOS.

DEV-003 P0: máy quét dùng eSCL/AirScan, SANE hoặc backend hợp lệ theo model. Kiểm tra scan 1 mặt/2 mặt, ADF, DPI, màu, nhiều trang, tiếng Việt trong tên file, PDF/TIFF/JPEG, quyền truy cập và lỗi mất kết nối. Danh sách thiết bị SANE chỉ là đầu vào khảo sát; chứng nhận phải thử thật theo model [S16]. Máy đa chức năng phải chứng nhận phần in và phần quét riêng.

DEV-004 P1: mở rộng hồ sơ thiết bị cho USB storage, điện thoại MTP, webcam UVC, micro, tai nghe USB/Bluetooth, Wi-Fi, Ethernet, Bluetooth, HDMI/DisplayPort, máy chiếu, bàn phím/chuột, màn hình cảm ứng, thẻ thông minh, đầu đọc mã vạch, máy in hóa đơn, cân điện tử và thiết bị POS khi nằm trong thị trường mục tiêu. Với mỗi loại cần test kết nối/rút nóng, cắm lại, sleep/resume, quyền ứng dụng, nhiều thiết bị đồng thời và hậu quả khi mất kết nối giữa giao dịch.

DEV-005 P0: chữ ký số USB token, smartcard và thiết bị nghiệp vụ Việt Nam cần ma trận **hãng token × model × firmware × middleware × trình duyệt × ứng dụng × nghiệp vụ**. Tìm driver Linux chính thức và đường PKCS#11/PCSC khi có; truy cập token bằng người dùng thường với quyền thiết bị hẹp. Phải test đăng nhập, chọn chứng thư, ký ở môi trường sandbox, ngắt token, PIN sai, hết hạn và phục hồi. Không cam kết ứng dụng ký số chạy chỉ vì token hiển thị trong `lsusb`; một thành phần Windows-only có thể buộc dùng môi trường Windows hợp lệ.

DEV-006 P1: kiểm thử thiết bị chuyên dụng với đúng phần mềm Windows dùng nó. Một máy in tem có thể in qua CUPS nhưng phần mềm thiết kế tem lại phụ thuộc Windows API; hai tầng phải được nghiệm thu cùng nhau. Danh mục pilot ưu tiên thiết bị phổ biến của trường học, văn phòng, kế toán và hộ kinh doanh Việt Nam do khảo sát thực tế chọn, không suy ra từ thị phần chưa có nguồn.

DEV-007 P0: cập nhật kernel/firmware/driver phải chạy lại các bài test thiết bị có rủi ro. Firmware chỉ tải từ nguồn có quyền và kiểm chữ ký/hash theo hướng dẫn nhà cung cấp; không flash firmware mặc định. Secure Boot phải kiểm tra module bên thứ ba và chuỗi chữ ký trên thiết bị thật. Máy bị mất Wi-Fi hoặc máy in sau cập nhật là lỗi chặn phát hành tới model được chứng nhận.

DEV-008 P1: Trung tâm thiết bị bằng tiếng Việt hiển thị “hoạt động đầy đủ”, “hoạt động một phần”, “chưa kiểm thử”, “không hỗ trợ” theo **model và chức năng**, kèm cách in/scan thử, driver/backend đang dùng và ngày chứng nhận. Không viết “đã hỗ trợ” khi mới nhận diện USB ID.

## 28 Giao diện quen thuộc với người dùng Windows

Mục tiêu trải nghiệm là người dùng chuyển sang NaMiOS ít phải học lại thao tác cơ bản. Giao diện sử dụng bố cục quen thuộc và bộ nhận diện riêng; không chép pixel, biểu tượng, âm thanh hoặc thương hiệu độc quyền của Microsoft. Không được giả định desktop KDE mặc định đã đáp ứng toàn bộ yêu cầu người dùng Việt Nam.

UI-001 P0: màn hình desktop có thanh tác vụ, nút mở ứng dụng, tìm kiếm, khay hệ thống, đồng hồ, thông báo, danh sách cửa sổ, thao tác ghim/bỏ ghim và khu vực file đang mở. Các thao tác chuột phải, kéo thả, Alt+Tab, Win+E, Win+D, Ctrl+C/V, Print Screen và đổi ngôn ngữ cần có mapping công bố, được test khi IME và Wine đang hoạt động. Không tùy tiện chiếm phím tắt của app.

UI-002 P0: trình quản lý tệp hiển thị Home, Documents, Downloads, Desktop, ổ ngoài và phân vùng Windows được phép đọc; hỗ trợ thao tác tên tiếng Việt, preview, tìm kiếm, đường dẫn dễ hiểu, kết nối SMB khi được cấp quyền, mount/unmount an toàn, thùng rác và khôi phục. Gắn nhãn dung lượng và filesystem. Không gọi ổ Linux là `C:` nếu điều đó làm người dùng nhầm với ổ Windows; ánh xạ C: chỉ hiển thị trong phạm vi Wine khi cần.

UI-003 P1: cài đặt hệ thống nhóm theo Công việc, Thiết bị, Mạng, Cá nhân hóa, Tài khoản, Riêng tư, Cập nhật và Khôi phục. Các thao tác ghép máy in, đổi đầu vào âm thanh, Wi-Fi, Bluetooth và màn hình ngoài phải có đường dẫn ngắn với thông báo tiếng Việt. Có tìm kiếm không dấu.

UI-004 P1: quy định thiết kế nội bộ cho NaMiOS gồm lưới khoảng cách, typography hỗ trợ đủ dấu Việt, kích cỡ tối thiểu, độ tương phản, focus, icon riêng, trạng thái lỗi, loading, empty, offline, ánh sáng/tối và bố cục responsive theo DPI. Claude tạo bộ component/style token và tài liệu tương ứng, kiểm tra với người dùng phổ thông. “Đẹp và giống Windows” không thay thế tiêu chí khả dụng. Không tuyên bố có một tiêu chuẩn pháp lý thống nhất cho mọi giao diện ứng dụng Việt Nam khi chưa chỉ ra chuẩn/đơn vị áp dụng.

UI-005 P1: luồng đầu tiên sau cài cho phép chọn chế độ giao diện quen thuộc, cỡ chữ, bộ gõ Telex/VNI, trình duyệt, phần mềm mở DOCX/XLSX/PDF, máy in mặc định và dữ liệu muốn chuyển từ Windows. Có hướng dẫn chuyển đổi từng bước và tùy chọn xem lại. Không đặt LibreOffice thành Word hoặc Excel trong tên hiển thị.

UI-006 P1: thử nghiệm khả dụng với ít nhất 15 người đại diện (nhân viên văn phòng, giáo viên và người dùng kế toán), mỗi người thực hiện 8 tác vụ định trước trên Windows tham chiếu và NaMiOS. Ghi tỷ lệ hoàn thành, thời gian, lỗi, số lần cần trợ giúp và phỏng vấn ngắn. TARGET: ít nhất 90% tác vụ cơ bản hoàn thành không cần hướng dẫn sau 15 phút làm quen; nếu chưa đạt, sửa luồng và thử lại, không tự đổi định nghĩa tác vụ.

UI-007 P1: lập bộ “ứng dụng Việt Nam” theo sản phẩm và phiên bản: trình duyệt chính phủ/thuế, phần mềm học tập, hóa đơn, ký số, Zalo, MISA và phần mềm doanh nghiệp phổ biến do nhóm người dùng mục tiêu xác nhận. Mỗi app có kiểm tra Unicode, font, gõ tiếng Việt, định dạng ngày tiền, upload/download, pop-up, in và file association. Nhãn “phù hợp sử dụng tại Việt Nam” chỉ dựa trên tập tác vụ đã xác minh, không phải chứng nhận của cơ quan nhà nước.

## 29 Điều kiện tương thích với phần mềm Windows để chuyển đổi thật

Mục tiêu chiến lược là tăng dần số **công việc trọn vẹn** mà người dùng đang làm trên Windows có thể thực hiện trên NaMiOS. Một tệp `.exe` mở được không đủ. Không thể đặt yêu cầu nghiệm thu “mọi ứng dụng viết cho Windows đều chạy” cho bản Linux/Wine: ứng dụng có driver nhân Windows, phụ thuộc hệ thống chống gian lận, dịch vụ đặc biệt, kích hoạt hoặc tích hợp nội bộ có thể không hoạt động. Câu này là mục tiêu nghiên cứu dài hạn, không được dùng làm bảo đảm sản phẩm. Với trường hợp buộc phải chạy Windows, có thể cung cấp đường VM hoặc remote có giấy phép, nhưng báo rõ phụ thuộc và chi phí.

WIN-001 P0: danh mục 100 ứng dụng Windows được khảo sát từ người dùng mục tiêu, ghi phiên bản cụ thể và 10 tác vụ phổ biến nhất mỗi nhóm. Chọn bộ 20 ứng dụng ưu tiên cho pilot dựa trên tần suất sử dụng, mức độ quan trọng và độ khó di chuyển; Word, Excel, Zalo PC, MISA SME và các lớp .NET phải nằm trong nhóm khảo sát. Đây là TARGET của khảo sát, không tuyên bố đã khảo sát hoặc sẽ có 100 app chạy được.

WIN-002 P0: cho từng app xác định installation type, runtime, kiến trúc 32/64-bit, WebView, fonts, COM/ActiveX, service, registry, ODBC/OLEDB, .NET, VC runtime, USB/serial, printer, network, update, activation, add-in, macro và liên kết liên ứng dụng. Phân tích động chỉ trong máy ảo cô lập với bản dùng hợp pháp. Một binary cần Windows kernel driver bị gắn `requires_windows_environment` trừ khi có giải pháp Linux vendor-supported đã test.

WIN-003 P0: yêu cầu tương đương theo **tác vụ**, gồm cài/kích hoạt hợp lệ, mở dữ liệu cũ, chỉnh sửa, tính toán, lưu, đóng/mở lại, in, xuất, gửi tệp, cập nhật và phục hồi. Tất cả tác vụ bắt buộc phải được so với Windows tham chiếu cùng phiên bản ứng dụng và dữ liệu thử. Tên mode `wine`, `web`, `native`, `vm`, `remote` được ghi trong kết quả; không cộng gộp mode để báo tỷ lệ tương thích desktop.

WIN-004 P0: quy trình tiếp nhận app lỗi gồm bản tái hiện tối thiểu, log không bí mật, bước gây lỗi, phân loại Wine/runner/prefix/driver/service/activation/ứng dụng, mức độ mất dữ liệu, người chịu trách nhiệm và test hồi quy. Gửi bản vá upstream theo giấy phép và điều kiện đóng góp phù hợp khi có thể. Không fork hàng loạt để “hỗ trợ mọi app” nếu chưa có đội bảo trì.

WIN-005 P1: catalog công bố một bảng minh bạch: app, edition/build, mode, OS/runner, phần cứng đã thử, các tác vụ đã đạt/chưa đạt, giới hạn, lần kiểm tra gần nhất, và nhà cung cấp có hỗ trợ môi trường đó hay không. Có nút báo lỗi và cách xuất chẩn đoán đã lọc. Tự cập nhật app hoặc thay đổi runner/kernel sẽ làm chứng nhận của tuple cũ không còn áp dụng cho tuple mới.

WIN-006 P1: tiêu chí chuyển đổi của một cơ quan/doanh nghiệp phải lập từ **toàn bộ workflow**: tạo file Office → gửi Zalo/email → ký số/hóa đơn → lưu kho → in → đối soát MISA, nếu workflow đó có sử dụng. Nếu một bước bắt buộc không hoàn thành được, hồ sơ nhóm này là `not_ready_for_migration`; không đưa kết quả app rời rạc thành lời khuyên bỏ Windows.

WIN-007 P1: thí điểm song song 30 ngày với nhóm người dùng tự nguyện và thiết bị đã được chứng nhận. Theo dõi tác vụ thất bại, số lần quay lại Windows, dữ liệu sai, thời gian hỗ trợ và lỗi sau cập nhật; báo cáo có mẫu số người dùng và số lần thực hiện. TARGET để xem xét mở rộng: không có mất/sai dữ liệu P0, 100% tác vụ bắt buộc đã chốt hoàn thành, tối thiểu 90% tác vụ hàng ngày của nhóm pilot không phải quay lại Windows. Con số là ngưỡng đề xuất, cần quyết định trước khi đo.

WIN-008 P0: nếu mục tiêu kinh doanh của chủ dự án đòi **mọi** phần mềm Windows hiện hành chạy nguyên vẹn kể cả driver Windows, phải đánh giá lại chiến lược nền tảng trước khi đầu tư rộng. Không được giao cho Claude Code nhiệm vụ “bảo đảm 100% tương thích” như thể một mức cố gắng lập trình có thể giải quyết chắc chắn. Kết quả khảo sát có thể dẫn tới phạm vi thiết bị/app được chứng nhận hoặc mô hình máy Windows hợp lệ ở phía sau.

## 30 Bổ sung chứng cứ và kế hoạch đo

HWPLUS-001 P0: trước G2 phải có lab ít nhất 20 model thiết bị ngoại vi thuộc các nhóm máy in, máy quét, USB token và thiết bị kết nối ưu tiên; mỗi model có ID, firmware, giao thức, chức năng, tài liệu và evidence. Số 20 là TARGET lập kế hoạch, không thay thế yêu cầu 5 mẫu máy tính và 2 mẫu máy in tối thiểu ở mục 16.

HWPLUS-002 P1: bổ sung vào ma trận kiểm thử các ca cắm nóng/rút nóng, máy in mạng, IPP over USB, in từ ứng dụng Wine, scanner ADF, ký số giả lập, sleep/resume, mất mạng và cập nhật kernel. Mỗi bài có kết quả riêng theo model. Lỗi làm sai chứng từ hoặc in thiếu nội dung là P0 cho workflow dùng chứng từ đó.

MIG-001 P1: có checklist trước chuyển đổi gồm danh sách ứng dụng, thiết bị, phiên bản dữ liệu, cơ chế backup/restore, tài khoản/giấy phép, người hỗ trợ, kế hoạch quay về và người ký chấp thuận. Thử trên máy phụ hoặc Live mode trước; chỉ chuyển máy chính khi workflow được nghiệm thu và có bản sao dữ liệu phục hồi được.

### Nguồn cho phần bổ sung

- [S14 OpenPrinting về driverless printing](https://openprinting.github.io/driverless) — IPP Everywhere/AirPrint là lựa chọn được hỗ trợ trong hệ sinh thái Linux.
- [S15 OpenPrinting về IPP qua USB](https://openprinting.github.io/projects/03-ipp-usb) — khả năng IPP/eSCL trên thiết bị tương thích.
- [S16 SANE danh sách thiết bị](https://www.sane-project.org/sane-supported-devices.html) — tra cứu scanner/backend theo model, không thay thế thử thực tế.
- [S17 Microsoft về driver ở kernel mode](https://learn.microsoft.com/windows-hardware/drivers/gettingstarted/user-mode-and-kernel-mode) — cơ sở phân biệt tầng driver Windows với ứng dụng user mode.
