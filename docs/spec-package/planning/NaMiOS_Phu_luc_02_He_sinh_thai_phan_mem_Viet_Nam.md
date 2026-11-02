# NaMiOS Phụ lục 02 Hệ sinh thái phần mềm thiết yếu tại Việt Nam

**Ngày:** 02/11/2026. **Nhà sáng lập và chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam. **Loại tài liệu:** phần bổ sung độc lập cho đặc tả NaMiOS 1.1 và lệnh giao việc M0–M2. Tài liệu cũ giữ nguyên; Claude Code chỉ cần đọc file này cùng `docs/STATUS.md` hiện tại để nhận yêu cầu mới. Các mã `ECO-*` chưa tồn tại trong backlog cũ và phải được đưa vào backlog của repository sản phẩm khi triển khai.

## 1 Quyết định sản phẩm

Người dùng chỉ chuyển sang NaMiOS khi **công việc họ bắt buộc làm** chạy được, gồm tải và cài phần mềm nếu phần mềm cần cài, đăng nhập, nhập dữ liệu, ký, nộp, nhận phản hồi, tải kết quả, lưu trữ và in. Một sản phẩm có thể là ứng dụng desktop, trang web, ứng dụng nền ký số, trình điều khiển token, phần mềm trung gian của nhà cung cấp, cơ sở dữ liệu và dịch vụ ngoài. Những thành phần này tạo thành **một chuỗi phụ thuộc**; thiếu một mắt xích thì cả quy trình chưa đạt.

NaMiOS không thể tự khẳng định hỗ trợ mọi phần mềm của các bộ, ngành và địa phương: ứng dụng đổi theo phiên bản, nơi triển khai, phương thức xác thực và nhà cung cấp. Dự án phải xây một **hệ thống khảo sát, chứng nhận và duy trì tương thích liên tục**, thay vì đóng gói một danh sách ứng dụng cố định rồi tuyên bố đã xong. Trạng thái từng quy trình được công bố theo phiên bản, nhà cung cấp và phạm vi đã thử.

## 2 Phạm vi khảo sát có thứ tự

| Nhóm | Workflow đại diện phải khảo sát | Thành phần có thể chặn | Ưu tiên |
| --- | --- | --- | --- |
| Thuế và hộ kinh doanh | Lập tờ khai → xuất XML/PDF → đăng nhập → ký/nộp → lấy biên nhận → tra cứu | HTKK hoặc phần mềm kê khai; eTax; plugin ký; token/chữ ký từ xa; biểu mẫu | P0 |
| Kế toán và hóa đơn | Nhập chứng từ → đối chiếu → xuất báo cáo → ký/phát hành hoặc trao đổi hóa đơn → sao lưu | SME/AMIS và sản phẩm khác; SQL; Office; ký số; máy in | P0 |
| BHXH và lao động | Tạo hồ sơ → kiểm tra dữ liệu → ký/gửi qua cổng hoặc I-VAN → nhận kết quả | Công cụ ký số, plugin, I-VAN, chứng thư, định dạng hồ sơ | P0 |
| Hành chính công | Định danh → điền hồ sơ → tải tệp → ký/xác nhận → thanh toán nếu có → lấy mã hồ sơ và kết quả | Đăng nhập liên thông; plugin Windows; trình duyệt; popup; thanh toán; PDF | P0 |
| Trường học | Sổ điểm/học bạ/báo cáo → nhập/xuất Excel → ký nếu có → in và gửi cơ sở dữ liệu ngành | CSDL ngành, phần mềm trường, Office macro, font, máy in, tài khoản phân quyền | P0 cho pilot giáo dục |
| Phần mềm ngành dọc | Nghiệp vụ của đơn vị → định dạng tệp đặc thù → ký/gửi → tích hợp máy móc | Java/.NET/ActiveX/COM; SQL; scanner; barcode; plugin độc quyền | P1, nâng P0 khi đơn vị pilot bắt buộc |

Đây là **nhóm khảo sát**, không phải lời xác nhận rằng các dịch vụ liệt kê đã chạy trên Linux. Ví dụ, Cổng Dịch vụ công Quốc gia giới thiệu đăng nhập bằng SIM/USB ký số và điều hướng sang cổng bộ, ngành, địa phương; phần mềm hỗ trợ trên cùng hệ sinh thái có plugin ký số dành cho Windows [1][2]. BHXH hướng dẫn cài công cụ ký số trước khi nộp một số hồ sơ [3]. CSDL ngành giáo dục có cổng theo cấp quản lý [4]. Những nguồn này chứng minh nhu cầu kiểm tra luồng liên thông, không chứng nhận NaMiOS đã tương thích.

## 3 Định nghĩa mức hỗ trợ bắt buộc

**ECO-001 P0 — Bảy nấc của một quy trình:** `discover`, `acquire`, `install_or_open`, `authenticate`, `execute`, `submit_or_export`, `verify_result`. Mỗi nấc có kết quả riêng. Với phần mềm web không có bộ cài, `install_or_open` là mở trình duyệt đúng đường dẫn chính thức; không đánh dấu `acquire` thành tải một binary. Với thủ tục không cần ký, bước ký được ghi `not_applicable`, không xóa bước khỏi mô hình.

**ECO-002 P0 — Chứng nhận đúng phạm vi:** tuple gồm tên sản phẩm/dịch vụ, nhà cung cấp hoặc cơ quan, URL chính thức hoặc build binary, ngày kiểm, loại người dùng, địa phương/cấp triển khai khi khác biệt, browser/runner, thiết bị ký số, model máy in, mode, OS build và tập tác vụ. Khi cổng, plugin hoặc token đổi phiên bản, kiểm thử lại phần bị ảnh hưởng. Không dùng kết quả cổng của một tỉnh để khẳng định mọi tỉnh.

**ECO-003 P0 — Trạng thái công bố:** `not_inventoried`, `downloadable_only`, `launches_only`, `partial_workflow`, `workflow_verified`, `blocked_external_dependency`, `unsupported`, `revoked`. `downloadable_only` và `launches_only` tuyệt đối không hiển thị là “dùng được”. `workflow_verified` phải có kết quả nộp/nhận trên sandbox hoặc môi trường thử chính thức nếu khả dụng; nếu không có sandbox, chứng nhận chỉ tới bước đã thử và ghi giới hạn. Chức năng pháp lý thực tế cần sự tham gia của đơn vị được phép và quy trình QA riêng.

**ECO-004 P0 — Tách hỗ trợ kỹ thuật và hỗ trợ chính thức:** app có thể chạy qua Wine nhưng nhà cung cấp chỉ hỗ trợ Windows. UI phải hiển thị hai trường độc lập. NaMiOS không tự tuyên bố được cơ quan nhà nước hay nhà cung cấp phần mềm chứng nhận khi không có văn bản xác nhận.

**ECO-005 P0 — Ưu tiên cơ hội chuyển đổi:** xếp theo `số đơn vị dùng × tần suất × tính bắt buộc × chi phí thất bại × khả năng hỗ trợ`, dùng dữ liệu khảo sát, không tạo điểm số giả. Mỗi nhóm người dùng có danh sách các việc “không thể thiếu”. Nếu một việc bắt buộc fail, nhóm đó chưa đủ điều kiện chuyển máy chính, dù phần lớn ứng dụng khác đạt.

## 4 Kiến trúc thêm cho hệ sinh thái Việt Nam

### 4.1 Danh bạ dịch vụ và phần mềm

**ECO-006 P0:** tạo `service-catalog` với ID ổn định, nhà cung cấp, cơ quan, mục đích, đường dẫn tải/đăng nhập chính thức, cách kiểm tra nguồn, phiên bản, giấy phép, hệ điều hành công bố, phụ thuộc, điều kiện tài khoản, chi phí dịch vụ, mức dữ liệu nhạy cảm, hồ sơ test, ngày cập nhật và nguồn chứng cứ. Catalog có metadata ký và cơ chế thu hồi; **không host lại bộ cài của cơ quan/nhà cung cấp** nếu chưa có quyền phân phối. Đường dẫn phải mở đúng tên miền, cảnh báo khi miền/redirect thay đổi và không tự điền mật khẩu vào trang giả mạo.

**ECO-007 P0:** người dùng tìm bằng tên phổ thông như “khai thuế”, “bảo hiểm”, “học bạ”, “hóa đơn”, cả có và không dấu. Kết quả hiển thị nhà cung cấp, mode, khả năng hoàn thành quy trình, yêu cầu token/đăng nhập, giới hạn và ngày kiểm. Không dùng từ “ứng dụng chính thức của NaMiOS” để mô tả sản phẩm bên thứ ba.

**ECO-008 P1:** công cụ tự kiểm môi trường trước khi bắt đầu: browser được yêu cầu, chứng thư, token, plugin, quyền cổng USB, công cụ ký, font, PDF/Excel, network, thời gian hệ thống, popup/download và printer. Chẩn đoán chỉ kết luận phần quan sát được; không thu PIN/token key, không xác thực bằng cách tự gửi hồ sơ thật.

### 4.2 Trung tâm ký số và xác thực

**ECO-009 P0:** coi chữ ký số là sản phẩm tích hợp nhiều tầng: token/HSM/ký từ xa → middleware nhà cung cấp → browser hoặc app desktop → nội dung ký → cổng tiếp nhận → biên nhận. Kiểm theo token model, phiên bản middleware, nhà CA, hồ sơ người dùng, cổng và nghiệp vụ. MISA SME hỗ trợ các cách ký khác nhau, trong đó USB token cần phần mềm của token và ký từ xa có luồng riêng [5]. Không suy ra một phương thức dùng được trên mọi cổng.

**ECO-010 P0:** trước khi phát triển bridge ký số cho Linux, kiểm tra giao thức công khai và văn bản hợp tác/quyền tích hợp. Bridge nội bộ chỉ chạy user-level hoặc service hẹp khi cần, có origin allowlist, xác nhận từng lần ký, hiển thị tài liệu/hash được ký, giữ private key trong token/HSM, audit không lưu PIN. Không giả lập plugin để vượt kiểm tra nền tảng, không tự can thiệp trang web hoặc chữ ký nếu không có giao diện tích hợp được phép.

**ECO-011 P0:** hỗ trợ chữ ký từ xa qua kênh chính thức như một hướng nghiên cứu ưu tiên khi đơn vị đã dùng dịch vụ đó; xác nhận bên cung cấp có hỗ trợ browser/thiết bị NaMiOS và có sandbox. Chữ ký từ xa không tự thay thế mọi yêu cầu USB token hoặc ứng dụng desktop. Không tự chuyển phương thức ký của doanh nghiệp.

### 4.3 Cầu nối ứng dụng Windows và dữ liệu

**ECO-012 P0:** với mỗi desktop app, lập dependency graph: installer → runtime `.NET/Java/VC++` → service/COM/ActiveX/WebView → DB → token → browser integration → in/xuất → updater. Công cụ phân tích chỉ gợi ý; test đúng chức năng. Ứng dụng cài được trong Wine nhưng service ký hoặc SQL không chạy phải đánh dấu workflow chưa đạt.

**ECO-013 P0:** định dạng hồ sơ XML, XLSX, DOCX, PDF, CSV phải qua round-trip và so dữ liệu có ý nghĩa, gồm schema/encoding/namespace, ký tự Việt, số tiền và ngày, file size, chữ ký, mã tra cứu. Không tự sửa file XML đã ký. Các macro/COM phụ thuộc Windows được kiểm riêng; thay bằng LibreOffice không tính là cùng ứng dụng.

**ECO-014 P1:** ưu tiên tích hợp qua API/tài liệu chính thức khi nhà cung cấp cho phép. Không scraping trang đã đăng nhập, đọc cookie hoặc tự động nộp hồ sơ để lách thiếu API. Nếu cơ quan hoặc vendor chỉ hỗ trợ Windows, đưa vào danh sách cần làm việc với họ; không ghi “đã được họ đồng ý”.

### 4.4 Chính sách hỗ trợ chế độ Windows hợp lệ

**ECO-015 P0:** catalog thể hiện `native_linux`, `web_linux`, `wine`, `remote_windows`, `windows_vm`, kèm giấy phép, mạng, phần cứng, dữ liệu qua biên và chi phí. Nếu workflow bắt buộc chỉ đạt qua VM/remote thì NaMiOS có thể là desktop chính, nhưng **nhóm đó chưa đạt mục tiêu loại bỏ hoàn toàn Windows**. Dự án cần thống kê tỷ lệ workflow không phụ thuộc Windows để ra quyết định kinh doanh.

## 5 Bộ hồ sơ khảo sát và thử nghiệm theo ngành

Mỗi ngành có **ít nhất hai sản phẩm hoặc cổng thực được đơn vị pilot dùng**, không chỉ ví dụ trên Internet. Các giá trị dưới đây là kế hoạch thu thập, không phải kết quả đã đạt.

| Ngành | Kịch bản kiểm thử tối thiểu bằng dữ liệu giả | Bằng chứng bắt buộc |
| --- | --- | --- |
| Thuế | Cài/mở phần mềm lập hồ sơ; nhập mẫu; xuất XML; đăng nhập cổng; chọn chứng thư; ký thử nếu có sandbox; lưu biên nhận; in PDF | Input/expected, schema/giá trị, trạng thái cổng sandbox, file/biên nhận giả, mode và build |
| Kế toán | Cài client; kết nối DB test; nhập chứng từ; báo cáo; đối chiếu số tiền; backup/restore; hóa đơn ở môi trường thử | Kế toán viên ký xác nhận giá trị, restore DB thật trong lab, không dùng dữ liệu sản xuất |
| BHXH | Lập hồ sơ giả; kiểm tra dữ liệu; công cụ ký; gửi trên test nếu có; tải kết quả; in | Vendor/I-VAN, token, build ký số, phản hồi, điểm chưa thử nếu không có sandbox |
| Hành chính công | Chọn thủ tục; đăng nhập hợp lệ; điền và tải tài liệu thử; ký/xác nhận; nhận mã hồ sơ thử; truy vấn | Cổng cấp quốc gia và cổng thực tế được điều hướng, địa phương, browser, plugin, phương thức xác thực |
| Giáo dục | Đăng nhập tài khoản thử theo vai trò; nhập/đọc dữ liệu giả; xuất Excel; in; ký nếu quy trình có | Vai trò trường/phòng/sở, dữ liệu giả, bố cục bảng, font, tính đúng |
| Ngành dọc | Chọn một workflow của đơn vị pilot với máy quét/tem/barcode/thiết bị riêng nếu có | Đúng model thiết bị, driver, file, quyền và xử lý lỗi khi ngắt kết nối |

**ECO-016 P0:** không tạo tài khoản hoặc giao dịch trên hệ thống nhà nước chỉ để test nếu chưa có sự cho phép, sandbox hoặc chủ tài khoản giao việc rõ. Trường hợp không có sandbox, dừng trước bước nộp/ký và ghi `blocked_external_dependency`; không ghi giả biên nhận. Chụp màn hình hoặc log có CCCD, mã số thuế, chứng thư, mật khẩu phải che/loại đúng cách trước khi đưa vào repo.

**ECO-017 P0:** đánh giá theo ba mức độc lập: (a) thực thi kỹ thuật, (b) đúng dữ liệu/nghiệp vụ, (c) đầu cuối với cổng và biên nhận. Chỉ người nghiệp vụ phụ trách mới xác nhận (b); (c) cần môi trường thử phù hợp. Một bài test `pass` ở (a) không suy ra (b) và (c).

**ECO-018 P1:** thử lỗi có thực: mạng mất giữa upload, token rút giữa ký, phiên đăng nhập hết hạn, đổi password, bản cổng thay đổi, file quá giới hạn, đường dẫn/tên file có dấu, chứng thư hết hạn, máy in offline, số tiền dùng dấu chấm/dấu phẩy. Không lặp giao dịch đã nộp khi phản hồi mơ hồ; trình bày trạng thái cần tra cứu trước.

## 6 Chương trình hợp tác nhà cung cấp

**ECO-019 P1:** duy trì danh sách nhà cung cấp cần liên hệ để xin tài liệu Linux/PKCS#11/API, môi trường test, quyền phân phối, lịch cập nhật và kênh báo lỗi. Ưu tiên nhà cung cấp ký số, kế toán/hóa đơn, I-VAN, phần mềm trường học và các cổng cơ quan. Mọi liên hệ hoặc gửi file ra ngoài cần chủ dự án giao việc rõ; tài liệu này chỉ chuẩn bị nội dung và người phụ trách, không tự gửi.

**ECO-020 P1:** cung cấp chứng cứ cho vendor: OS/browser/runner build, cách tái hiện, log đã khử bí mật, kết quả trên Windows đối chiếu, mô tả API/driver cần. Không yêu cầu vendor cam kết Linux khi chưa có năng lực hỗ trợ; ưu tiên API tiêu chuẩn, hướng dẫn môi trường web và chữ ký từ xa được họ hỗ trợ.

**ECO-021 P1:** đề xuất một nhãn `Supported on NaMiOS` có tiêu chí công khai và thời hạn. Chỉ dùng logo/vendor name theo quyền cho phép. `Tested by NaMiOS` khác `Officially supported by vendor`.

## 7 Mốc nghiệm thu và điều kiện để có người dùng thật

| Mốc | Số lượng dự kiến | Gate |
| --- | --- | --- |
| Khảo sát | 100 workflow/ứng dụng được người dùng mục tiêu nêu tên, trong đó 20 workflow ưu tiên đã xác định phiên bản/đơn vị | Dữ liệu khảo sát thật, chưa tính thành tương thích |
| Pilot văn phòng/giáo dục | 3–5 workflow hàng ngày với đủ app và máy in trong danh sách | 100% bước bắt buộc qua test, không sai dữ liệu, có phục hồi |
| Pilot doanh nghiệp | Một chuỗi kế toán → hóa đơn → thuế/BHXH của đơn vị tình nguyện | Từng cổng, ký, DB, biên nhận có bằng chứng hoặc giới hạn được công bố; không chuyển máy chính nếu bước bắt buộc chưa đạt |
| Mở rộng ngành | Từng cơ quan/nhà cung cấp cụ thể theo bản cập nhật | Có người duy trì catalog, kiểm thử lại khi đổi cổng/plugin/driver |

**ECO-022 P0:** dashboard quản trị hiển thị coverage theo **workflow được khảo sát**, phần trăm `workflow_verified`, `partial`, `blocked`, số người dùng và số lần phải quay Windows; tách hoàn toàn web/Wine/VM/remote. Không lấy “100 phần mềm được liệt kê” làm “100 phần mềm chạy được”.

**ECO-023 P0:** quy tắc dừng rollout khi có sai dữ liệu, chữ ký không đúng, mất file, mất khả năng phục hồi DB, in thiếu chứng từ hoặc nhầm người nhận. Rollback bằng bản sao và quy trình nghiệp vụ được xác nhận; không tự gửi lại hồ sơ, hóa đơn hoặc giao dịch trùng.

**ECO-024 P1:** một release công khai phải có bảng ứng dụng/cổng đã kiểm thử theo ngày, danh sách thiết bị hỗ trợ, hạn chế, nguồn tải chính thức, cách báo lỗi và chính sách cập nhật. Nhóm người dùng chưa đủ workflow phải được cảnh báo trước khi cài đè lên máy Windows đang dùng.

## 8 Nhiệm vụ Claude Code tiếp theo

Sao chép nguyên đoạn này vào Claude Code **sau khi cung cấp file này và bộ đặc tả hiện tại**:

> Tiếp tục NaMiOS theo phụ lục hệ sinh thái phần mềm Việt Nam. Không đọc lại toàn bộ tài liệu cũ nếu `docs/STATUS.md` và các quyết định đã ghi đủ, nhưng đọc các hợp đồng và yêu cầu cũ liên quan trước khi sửa code. Hãy thêm ECO-001 đến ECO-024 vào backlog và triển khai ngay phần độc lập: schema cho catalog dịch vụ/workflow, bộ quy tắc trạng thái bảy nấc, validator, UI/CLI hiển thị trạng thái trung thực và test ngăn `downloadable_only` thành `workflow_verified`. Tạo inventory theo thuế, kế toán, BHXH, hành chính công, giáo dục, ngành dọc; dùng đúng URL/phiên bản và nguồn chính thức có ngày kiểm, không tự coi mọi ứng dụng trong nhóm đã tương thích. Tiếp tục spike các thành phần Windows, ký số, máy in và trình duyệt trên môi trường được phép. Với bước ký/gửi hồ sơ thực, dừng ở sandbox hoặc báo blocked. Mỗi phiên báo cáo source, test thật, workflow đã kiểm, giới hạn, phụ thuộc cần chủ dự án cung cấp và quyết định go/no-go. Không chỉ làm giao diện hoặc đưa ra một danh sách tên phần mềm.

**Bộ đầu vào chỉ cần khi kiểm thử thực:** đơn vị pilot và 10 workflow đang dùng; tên/phiên bản phần mềm; nhà I-VAN, nhà cung cấp ký số và token model; một máy in; tài khoản thử hoặc sandbox chính thức nếu có. Có thể bắt đầu schema, state machine, inventory và fixture trước khi nhận các đầu vào này.

## 9 Nguồn chính thức và giới hạn suy luận

Tra cứu ngày 02/11/2026; các cổng và phần mềm có thể đổi sau ngày này. Không nguồn nào dưới đây là chứng nhận tương thích NaMiOS.

1. [Cổng Dịch vụ công Quốc gia hướng dẫn sử dụng](https://vpcp.dichvucong.gov.vn/p/home/dvc-huong-dan-cong-dan-doanh-nghiep.html) — ví dụ xác thực bằng USB/SIM ký số và điều hướng tới cổng cơ quan.
2. [Cổng Dịch vụ công Quốc gia phần mềm hỗ trợ](https://vpcp.dichvucong.gov.vn/p/home/dvc-phan-mem-ho-tro.html) — ví dụ plugin ký số được công bố cho Windows.
3. [BHXH Việt Nam hướng dẫn công cụ ký số](https://baohiemxahoi.gov.vn/gioithieu/Pages/gioi-thieu-chung.aspx?CateID=0&ItemID=21610) — ví dụ cần công cụ cài cục bộ cho một dịch vụ.
4. [Bộ GDĐT cơ sở dữ liệu ngành](https://csdl.moet.gov.vn/Default.aspx) — các cổng phục vụ trường và cấp quản lý.
5. [MISA SME 2026 thiết lập ký số](https://helpsme.misa.vn/2026/kb/thiet_lap_ky_so/) — token USB và chữ ký từ xa có phụ thuộc khác nhau.
