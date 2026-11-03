# NaMiOS — Phụ lục 03: Kiến trúc tương thích và nâng cấp để dùng trong công việc tại Việt Nam

**Ngày:** 03/11/2026. **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam. **Tính chất:** yêu cầu bổ sung độc lập, tiếp nối đặc tả NaMiOS và Phụ lục 02 (ECO-001–ECO-024). Claude Code chỉ cần đọc file này, `docs/STATUS.md` và các hợp đồng/code liên quan đến phần định sửa. Không nhập lại nguyên văn tài liệu cũ. Mã mới là `COMP-025` đến `COMP-054`.

## 1. Mục tiêu sản phẩm và giới hạn cần giữ

NaMiOS dựa trên Linux, đặt mục tiêu là máy làm việc chính cho những nhóm người dùng Việt Nam đã được khảo sát. “Chạy được như Windows” phải được hiểu theo **tác vụ cụ thể, phiên bản cụ thể, thiết bị cụ thể và môi trường cụ thể**. Không thể đảm bảo mọi `.exe`, trình điều khiển Windows, phần mềm dùng ActiveX, giao diện WPF hay dịch vụ chỉ hỗ trợ Windows đều chạy trực tiếp trên Linux. Việc Microsoft hỗ trợ .NET trên Linux không đồng nghĩa .NET Framework, WinForms hoặc WPF chạy native trên Linux [1][2]. Wine chuyển dịch nhiều lệnh gọi API của ứng dụng Windows, nhưng thành công của một ứng dụng không bảo đảm tương thích toàn bộ các phụ thuộc [3].

**Nguyên tắc quyết định:** với mỗi workflow phải chọn đường đi ngắn nhất có bằng chứng hoàn thành và đúng dữ liệu: `native_linux` → `web_linux` → `wine` → `remote_windows` hoặc `windows_vm` theo tính phù hợp, giấy phép, bảo mật và chi phí. Trình tự này là thứ tự điều tra mặc định, không phải cam kết rằng lựa chọn đầu luôn tốt hơn. Máy Windows từ xa/VM phải dùng giấy phép hợp lệ và được đơn vị quản trị cho phép; không đặt tên nó là “chạy native trên NaMiOS”. Không đóng gói hoặc tái phân phối phần mềm/driver thương mại nếu chưa được phép.

## 2. Sơ đồ các tầng cần phát triển

| Tầng | Trách nhiệm | Ranh giới và bằng chứng |
| --- | --- | --- |
| Hệ điều hành Linux | kernel, cập nhật, quyền, đĩa, mạng, CUPS/scanner, desktop | Không cố nạp driver kernel Windows vào Linux. |
| Giao diện NaMiOS | desktop quen thuộc, tiếng Việt, File Explorer, settings, khay hệ thống, thông báo | Giống thao tác quen thuộc nhưng không sao chép tài sản giao diện có bản quyền; điều khiển bằng bàn phím, đọc màn hình. |
| Trung tâm tương thích | catalog + resolver + preflight + runner + trạng thái workflow | Có lý do chọn mode; chứng cứ cho từng bước; không tự động tuyên bố hỗ trợ. |
| Môi trường thực thi | Linux app, browser, Wine prefix theo app, Windows VM/remote | Tách profile, quyền, dữ liệu và log; người dùng biết đang chạy bằng mode nào. |
| Dịch vụ liên thông | file picker, printer/scanner, USB/token, xác thực, tài liệu, DB | Qua API chính thức; mức quyền tối thiểu; không kéo private key ra khỏi token. |
| Chứng nhận vận hành | lab, fixture, hồ sơ kết quả, CI, rollback | Đối chiếu Windows và nghiệp vụ bằng dữ liệu giả; kết quả có phạm vi và ngày hết hạn. |

## 3. Yêu cầu chức năng bổ sung

### 3.1 Chọn và quản lý môi trường chạy

**COMP-025 P0 — Compatibility Resolver.** Đầu vào: `workflow_id`, `app_id`, phiên bản, kiến trúc CPU, OS build, quyền license, thiết bị bắt buộc, tình trạng mạng, chính sách tổ chức. Đầu ra: danh sách mode khả thi kèm `reason`, phụ thuộc, giới hạn, bước chưa kiểm thử và lựa chọn được đề xuất. Nếu không có mode đã xác minh cho tác vụ bắt buộc, trả `no_verified_route`; không đoán thành “chạy được”. **Nghiệm thu:** 20 profile giả lập có đủ nhánh; thay đổi token model hoặc app version làm mất hiệu lực chứng nhận tương ứng.

**COMP-026 P0 — App Capsule.** Mỗi app Wine có prefix và cấu hình riêng, pin phiên bản Wine/runtime/32–64 bit, thư mục dữ liệu được cấp, bản sao lưu và danh sách phụ thuộc. Ghi hash và nguồn của bộ cài, không tự tải DLL/installer từ kho không xác thực. Mọi chỉnh registry/runtime có thể tái tạo từ manifest; cập nhật một app không làm thay đổi prefix app khác. **Nghiệm thu:** cài hai app yêu cầu cấu hình khác nhau, hỏng một app thì app kia vẫn mở; rollback capsule không xóa dữ liệu người dùng.

**COMP-027 P0 — Install Assistant theo nguồn hợp pháp.** Hiển thị nhà phát hành, URL chính thức, giấy phép, bản x86/x64, hash nếu nhà phát hành công bố, chữ ký nếu có, dung lượng, runtime và mức hỗ trợ. Tệp người dùng chọn được quét metadata và kiểm tra hash/signature khi có chuẩn phù hợp; không đánh đồng “không có chữ ký” với “an toàn”. Giải thích rõ `.exe` có thể tải được nhưng chưa chắc cài/chạy hoặc hoàn thành nghiệp vụ. **Nghiệm thu:** URL bị thay miền hoặc manifest bị sửa bị chặn/cảnh báo; không chạy installer với quyền root mặc định.

**COMP-028 P0 — Runtime Classifier.** Phân biệt .NET hiện đại đa nền tảng, .NET Framework, WinForms, WPF, WinUI, VC++ runtime, Java, COM/OLE, ActiveX, WebView2, service Windows, SQL Server/client, anti-cheat/DRM/driver kernel. Kết quả là nhãn “phát hiện/suy đoán/chưa rõ”, không phải kết luận từ đuôi `.exe`. Có mẫu hướng dẫn vendor chuyển .NET business logic sang Linux hoặc web nếu họ sở hữu mã; NaMiOS không tự chuyển ứng dụng đóng nguồn. **Nghiệm thu:** mẫu .NET console Linux được phân loại khác app WPF; app cần kernel driver bị đánh dấu blocker cho Wine.

**COMP-029 P1 — Desktop Integration Bridge.** Ứng dụng Wine cần file picker cho thư mục được chọn, mở URL bằng browser mặc định, khay hệ thống, thông báo, in, clipboard có kiểm soát, biểu tượng Start/menu và association loại tệp. Hạn chế đường dẫn Windows giả lập và ký tự Unicode; không mount toàn bộ home/ổ mạng mặc định. **Nghiệm thu:** lưu/mở file có dấu Việt và đường dẫn dài, in thử, copy/paste có dấu, một cửa sổ app không chiếm focus vô hạn.

**COMP-030 P1 — Windows Workstation Fallback.** Hỗ trợ khai báo kết nối tới Windows đã được tổ chức cấp phép/duyệt cho app bị chặn, qua phương thức truy cập từ xa được phê duyệt. Thể hiện ranh giới dữ liệu, in, USB redirection, MFA, clipboard, disconnect/reconnect, ghi nhận thời gian phụ thuộc Windows. Không mặc định upload tài liệu nhạy cảm lên máy trung gian. **Nghiệm thu:** khi mất mạng, chỉ báo tác vụ chưa hoàn thành; không tự phát lại thao tác ký/nộp; phiên remote đóng thì thông tin xác thực không lưu lộ.

### 3.2 Phần mềm Việt Nam, ký số và thiết bị

**COMP-031 P0 — Workflow Pack theo ngành.** Mỗi pack là metadata và test plan cho thuế, kế toán, BHXH, giáo dục, hành chính công hoặc ngành dọc; gồm thứ tự bước, đầu vào, vai trò, cổng/nhà cung cấp, artifacts mong đợi, thiết bị và điểm dừng trước giao dịch thật. Pack không chứa thông tin đăng nhập, cookie, PIN hay dữ liệu thật. Phiên bản pack độc lập bản OS. **Nghiệm thu:** có pack mẫu cho sáu nhóm với dữ liệu giả, riêng từng cổng/địa phương/nhà cung cấp được chỉ rõ `unknown` nếu chưa khảo sát.

**COMP-032 P0 — Device Capability Registry.** Không ghi “hỗ trợ máy in/máy quét/token” chung chung. Ghi USB VID/PID khi phù hợp, model, firmware, giao thức, driver Linux/cơ chế chuẩn, chức năng tested, version, điều kiện quyền. Thiết bị cùng hãng khác model không tự được công nhận. Tách in qua IPP/CUPS, quét eSCL/SANE và token PKCS#11/driver vendor; IPP-over-USB có thể cho phép driverless với thiết bị hỗ trợ, không suy ra mọi máy in USB dùng được [4]. **Nghiệm thu:** registry có test in A4 hai mặt, tiếng Việt, in PDF, khay giấy; quét màu nhiều trang và OCR chỉ khi model hỗ trợ; rút cáp giữa job cho kết quả rõ.

**COMP-033 P0 — Signing Broker có sự chấp thuận của vendor.** Thiết kế interface `list_certificates`, `get_certificate_metadata`, `request_signature` (hiện tài liệu/hash và bên yêu cầu), `get_result`, `cancel`; adapter theo API/SDK tài liệu chính thức, PKCS#11 khi vendor có Linux module, hoặc quy trình ký từ xa được vendor hỗ trợ. PKCS#11 là giao diện token chuẩn, nhưng không bảo đảm plugin website hay nghiệp vụ portal hỗ trợ Linux [5]. Ký thực phải có thao tác xác nhận người dùng; không giữ PIN, private key, session credential. Origin allowlist và audit thiếu dữ liệu nhạy cảm. **Nghiệm thu:** ký thử trong sandbox hoặc thiết bị lab và xác minh chữ ký độc lập; nếu thiếu API/vendor hoặc sandbox, trạng thái `blocked_external_dependency`, không mô phỏng như đã ký.

**COMP-034 P0 — Browser Environment Doctor.** Kiểm tra các điều kiện quan sát được: phiên bản browser được portal chấp nhận, pop-up, download, PDF viewer, thời gian hệ thống, DNS/TLS, miền và redirect, middleware ký số, kết nối token. Không tự cài extension, sửa nội dung website, vượt kiểm tra nền tảng hay inject vào portal. **Nghiệm thu:** trả blocker cụ thể và đường dẫn hướng dẫn; trường hợp portal chỉ có plugin Windows ghi rõ giới hạn.

**COMP-035 P1 — Print and Scan Workspace.** Hàng đợi in cho chứng từ, in thử không làm lộ dữ liệu, profile biểu mẫu A4/A5, lề, scale, duplex, PDF/A nếu quy trình yêu cầu; quét thành PDF nhiều trang và OCR tiếng Việt là tính năng tùy cấu hình. Tên, số tiền, dấu và mã QR/barcode phải kiểm bằng mẫu nghiệp vụ; nếu không đạt, cấm công bố “đã in được”. **Nghiệm thu:** đối chiếu mẫu chứng từ đầu ra với bản Windows/chuẩn cơ quan bằng ngưỡng được người nghiệp vụ phê duyệt; in thiếu trang tạo lỗi chứ không pass.

**COMP-036 P1 — Thiết bị chuyên ngành.** Registry cho đầu đọc mã vạch, máy in tem, đầu đọc thẻ, thiết bị học đường, máy chấm công, thiết bị y tế hoặc thiết bị cổng công khi có pilot; dùng HID/serial/network/API chính thức và quyền tối thiểu. Driver Windows kernel hoặc SDK độc quyền thiếu bản Linux là blocker cần vendor hay VM/remote. **Nghiệm thu:** với từng model pilot, xác minh luồng dữ liệu đầy đủ và xử lý rút/cắm lại.

### 3.3 Dữ liệu, ứng dụng văn phòng và cơ sở dữ liệu

**COMP-037 P0 — Document Fidelity Lab.** Bộ fixture DOCX, XLSX, PPTX, PDF, XML, CSV tiếng Việt: font, tiêu đề, bảng, công thức, pivot, macro, conditional formatting, biểu đồ, merged cells, số tiền, ngày giờ, mã số thuế, Unicode và chữ ký. So round-trip theo dữ liệu và hiển thị; không nhận “mở được file” là đạt. Macro VBA/COM và add-in Windows là đường test riêng; LibreOffice hoặc web Office là sản phẩm/mode khác Microsoft Office desktop. **Nghiệm thu:** test có trường hợp làm sai tiền mà vẫn mở file, phải fail; người dùng xem trước khác biệt trước khi lưu đè.

**COMP-038 P0 — Database Compatibility Profile.** Lập đồ thị client → connector/ODBC/OLE DB → server → schema → backup. Với MISA và các phần mềm tương tự, chỉ chọn cấu hình database đúng phiên bản và nhà cung cấp công bố; Wine client chạy được nhưng DB/service không đạt vẫn là `partial_workflow`. Không chạy chuyển đổi schema trên dữ liệu sản xuất trong lúc khảo sát. **Nghiệm thu:** nhập chứng từ giả, tính sổ/báo cáo, backup, restore vào môi trường lab, so tổng tiền và quyền truy cập; rollback có thể phục hồi.

**COMP-039 P0 — Data Migration Assistant.** Chế độ audit read-only máy Windows cũ: inventory app và phiên bản, license, file, fonts, printer, bookmarks, account dùng SSO, DB, workflow chưa thay thế. Tạo phương án copy được người dùng duyệt, checksum, lưu provenance và cho phép thử trên bản sao; không xóa Windows hoặc dữ liệu gốc. **Nghiệm thu:** báo danh sách blocker trước cài chính; số lượng tệp/checksum và kết quả restore được đối chiếu; chuyển đổi có thể dừng an toàn.

**COMP-040 P1 — Enterprise Identity & Shares.** Có kế hoạch tích hợp SSO/LDAP/Kerberos/AD và SMB/NAS khi pilot yêu cầu; thử quyền tệp, dấu tiếng Việt, khóa tệp đồng thời, roaming profile, VPN/proxy/MFA, đồng bộ giờ. Cần quản trị viên tổ chức cho phép trước khi cấu hình domain; không lưu mật khẩu domain trong catalog. **Nghiệm thu:** test theo ít nhất hai vai trò và trường hợp mất kết nối, quyền không rộng hơn Windows đối chứng.

**COMP-041 P1 — Offline Work and Sync.** Chỉ cho phép draft offline với app/workflow có API hoặc dữ liệu do NaMiOS quản lý; đánh dấu trạng thái “chưa gửi”. Hồ sơ thuế, hóa đơn, bảo hiểm không tự đồng bộ hoặc gửi lại sau reconnect khi trạng thái trên cổng chưa xác minh. **Nghiệm thu:** mất mạng sau nút gửi không tạo hai hồ sơ; người dùng thấy cách tra cứu biên nhận trước khi quyết định gửi lại.

### 3.4 Trải nghiệm người Việt và khả năng triển khai

**COMP-042 P0 — Vietnamese UX Baseline.** Bộ gõ tiếng Việt hỗ trợ Telex/VNI, chuyển nhanh EN/VI, không gõ trùng trên Wine/web/remote; locale `vi-VN`, múi giờ, sắp xếp họ tên, định dạng tiền/ngày, tìm kiếm có/không dấu; font Unicode rõ trên form, PDF và máy in. Đừng tự thay dấu phân cách số khi ứng dụng đang nhập dữ liệu pháp lý. **Nghiệm thu:** 100 câu tiếng Việt có dấu qua clipboard, tên file, in và upload; test 1.234,56 so 1,234.56 ở form nhạy cảm.

**COMP-043 P1 — Accessibility and Familiar Desktop.** Menu, cửa sổ, phím tắt, thanh tác vụ, thông báo, File Manager có bố cục quen thuộc, hỗ trợ phóng to, tương phản, trình đọc màn hình và bàn phím đầy đủ; không sao chép biểu tượng/tài sản Microsoft. Cài đặt giúp người dùng chuyển từ Windows bằng hướng dẫn 5 công việc thường ngày. **Nghiệm thu:** người dùng pilot không được hỗ trợ kỹ thuật thực hiện mở file, in, cài ứng dụng từ nguồn chính thức, tìm văn bản và khôi phục bản sao.

**COMP-044 P0 — Update Rings và Kill Switch.** Có các kênh cập nhật `lab`, `pilot`, `stable`; pin app runner, middleware, driver và pack. Cập nhật có chữ ký, khả năng rollback và snapshot dữ liệu, không thay Wine/driver giữa mùa quyết toán nếu chưa qua regression; tắt nhanh một adapter gây sai dữ liệu/chữ ký mà không tắt toàn OS. **Nghiệm thu:** bản mới fail một workflow P0 → ngăn phát stable; rollback trên pilot phục hồi trạng thái và dữ liệu.

**COMP-045 P0 — Privacy-safe Diagnostics.** Thu log tối thiểu: app/mode/version, bước workflow, mã lỗi, thời điểm, ID thiết bị không nhận diện cá nhân khi có thể. Không thu tài liệu, token PIN, password, CCCD, dữ liệu sổ kế toán hoặc cookie. Mọi telemetry mạng có sự đồng ý và nút tắt, có chế độ xuất gói lỗi đã lọc để đơn vị kiểm tra trước khi chia sẻ. **Nghiệm thu:** fixture có bí mật giả, xuất diagnostics không chứa bí mật; chính sách lưu/xóa công khai.

**COMP-046 P1 — Helpdesk and Status.** Trang lỗi bằng tiếng Việt theo `workflow_id` và `stage`, nêu nguyên nhân quan sát được, bước người dùng có thể thử, cách chuyển cho IT/vendor; support matrix công khai gồm ngày kiểm, app build, OS/runner/browser/token/print model, mức hỗ trợ chính thức của vendor. **Nghiệm thu:** lỗi token, font, hết phiên và máy in offline đều có chỉ dẫn khác nhau; không gợi ý nộp lại khi trạng thái chưa rõ.

**COMP-047 P0 — Security Boundary.** Chạy installer với quyền người dùng trong isolation phù hợp, kiểm soát file/network/USB, nguyên tắc quyền tối thiểu. Wine prefix không phải ranh giới bảo mật hoàn chỉnh; app không tin cậy cần sandbox/VM hoặc cấm chạy theo chính sách. Dịch vụ ký số không lắng nghe mạng công khai; cập nhật và manifest có xác thực nguồn. **Nghiệm thu:** thử app giả tìm đọc thư mục ngoài phạm vi, gọi local signing endpoint từ origin không được phép, và sửa manifest; phải bị từ chối.

## 4. Mô hình dữ liệu tối thiểu và hợp đồng API

Các ví dụ là schema đề xuất để Claude Code cụ thể hóa và version hóa, không phải chứng nhận ứng dụng có thật:

```yaml
schema_version: 1
workflow_id: vn.tax.sample_submission
sector: tax
provider_id: unresolved
service_url: null
region_scope: unresolved
app:
  id: unresolved
  version: unresolved
  architecture: unknown
  license: verify_with_vendor
required_steps: [discover, acquire, install_or_open, authenticate, execute, submit_or_export, verify_result]
requires: [browser, signing_method, document_format, printer_if_needed]
routes:
  - mode: web_linux
    status: not_inventoried
    blockers: []
  - mode: wine
    status: not_inventoried
    blockers: []
certification:
  os_build: null
  browser_or_runner: null
  device_models: []
  tested_at: null
  evidence_ids: []
  technical_status: not_inventoried
  business_status: unreviewed
  end_to_end_status: untested
  vendor_support: unknown
```

**COMP-048 P0 — Schema and Evidence.** JSON Schema hoặc tương đương cho catalog, device registry, workflow pack và test report; migrate schema có version, ID ổn định, ngày hiệu lực, nguồn, license và trạng thái thu hồi. `workflow_verified` chỉ hợp lệ khi tất cả required steps có evidence hợp lệ và business approval theo quy tắc ECO-001–ECO-024. **Nghiệm thu:** validator từ chối `tested_at` trống, “vendor_supported=true” thiếu chứng cứ, hoặc chứng nhận mất hiệu lực khi app/token thay version.

**COMP-049 P0 — Provenance.** Mỗi evidence chứa `test_case_id`, fixture hash, kết quả expected/actual, người xác nhận vai trò nghiệp vụ, timestamp, phiên bản OS/app/runner/device và bước; tách log nhạy cảm khỏi báo cáo chia sẻ. Test trên sandbox và test trên production có nhãn khác nhau, chỉ test được phép mới lưu. **Nghiệm thu:** dashboard truy vết được từ badge tương thích đến từng case và giới hạn của kết quả.

**COMP-050 P1 — Compatibility API.** Endpoint đọc hoặc CLI: `list workflows`, `explain route`, `preflight`, `list evidence`, `report blocker`. Không trả bí mật; output dạng máy đọc được để desktop UI và helpdesk dùng chung. Việc chọn mode, cài app, xin quyền USB hay khởi chạy remote là thao tác riêng có xác nhận người dùng. **Nghiệm thu:** một CLI và UI cho cùng đầu vào cho cùng kết luận; ghi rõ nguyên nhân `no_verified_route`.

## 5. Thứ tự triển khai để tránh làm giao diện trước khi có bằng chứng

| Giai đoạn | Đầu ra của Claude Code | Gate |
| --- | --- | --- |
| A — mô hình | COMP-025, 028, 031, 032, 048, 049; fixtures giả, validator, resolver CLI | 20 profile và các trạng thái không thể bị nâng thành verified bằng metadata giả. |
| B — môi trường chạy | COMP-026, 027, 029; thử hai app open source Windows mẫu, không dùng app thương mại khi chưa có quyền | Cài/rollback, tách dữ liệu, mở/in/file picker có bằng chứng. |
| C — pilot nghiệp vụ | COMP-033–041 với **phần mềm thật mà đơn vị pilot đang dùng**, vendor, token, DB, máy in | Người nghiệp vụ xác nhận output và hoàn thành các bước được phép; blocker được công bố. |
| D — sản phẩm | COMP-042–047, 050, release rings, helpdesk | Một nhóm pilot hoàn thành 100% công việc bắt buộc của họ, không sai dữ liệu, có đường phục hồi. |

**COMP-051 P0 — Phân khúc pilot.** Chọn trước ba chân dung: giáo viên/văn phòng trường, kế toán doanh nghiệp nhỏ, bộ phận hành chính; mỗi chân dung liệt kê 10 tác vụ làm hàng tuần và 2 tác vụ theo mùa. Dữ liệu khảo sát từ người dùng thật, không tự đặt tỷ lệ thành công. Pilot khác ngành không được dùng làm chứng nhận chéo.

**COMP-052 P0 — Acceptance Matrix.** Mỗi case gồm cài, mở, đăng nhập, dữ liệu đúng, ký nếu cần, in, gửi, nhận, khôi phục; các bước không áp dụng ghi `N/A` có lý do. Ba cột pass kỹ thuật, pass nghiệp vụ, pass đầu cuối độc lập. Chỉ workflow đủ toàn bộ bước bắt buộc mới tính “chuyển máy chính được”; một blocker P0 của đơn vị pilot là no-go.

**COMP-053 P1 — TCO và mức phụ thuộc Windows.** Theo dõi chi phí máy, hỗ trợ, license app, VM/remote, số sự cố, thời gian khắc phục, đào tạo và thời gian quay Windows; trình bày hai chỉ số riêng: `tỷ lệ tác vụ hoàn thành trên NaMiOS` và `tỷ lệ không phụ thuộc Windows`. Không suy “OS miễn phí” thành “tổng chi phí bằng 0”.

**COMP-054 P0 — Release Decision.** Trước khi công bố hỗ trợ một workflow, có chủ sở hữu test, nguồn tải chính thức, phiên bản, môi trường, bộ chứng cứ, thời hạn tái kiểm và giới hạn. Nếu vendor hoặc portal thay đổi, chuyển badge sang `needs_retest` nội bộ và công bố lại trạng thái an toàn theo mô hình ECO-003 (thí dụ `revoked` khi chứng nhận cũ không còn giá trị). Không âm thầm giữ badge `workflow_verified`.

## 6. Các điều kiện cần chủ dự án/đơn vị pilot cung cấp khi thử thật

1. Danh sách tối thiểu 30 ứng dụng/cổng thực sự dùng tại 3 nhóm pilot; đánh dấu 10 workflow không thể thiếu của mỗi nhóm, sản phẩm/version, địa phương và nhà cung cấp.
2. 2–3 model máy in thực tế, một máy quét, một token hoặc hình thức ký từ xa đang dùng; driver/middleware, nhà CA, trang hướng dẫn chính thức, phạm vi cho phép test.
3. Tài khoản thử, dữ liệu giả và sandbox được đơn vị/cổng cho phép. Nếu không có, chỉ thử đến bước trước khi phát sinh hồ sơ/chữ ký/giao dịch thật.
4. Phần mềm có license hợp lệ, bộ cài từ nhà phát hành, tài liệu API và đầu mối vendor khi có. Đơn vị nghiệp vụ xác nhận kết quả tiền, biểu mẫu và biên nhận.
5. Máy Windows đối chứng cùng phiên bản ứng dụng để so dữ liệu, giao diện in và kết quả nghiệp vụ; người phụ trách kế hoạch backup/rollback.

Những đầu vào này cần cho **chứng nhận thực tế**, không cản việc Claude Code triển khai schema, test fixtures, resolver, UI và bộ preflight trước.

## 7. Lệnh giao việc gửi Claude Code

> Hãy triển khai Phụ lục 03 của NaMiOS theo COMP-025–COMP-054. Đầu tiên đọc `docs/STATUS.md`, các hợp đồng catalog/workflow/runner hiện có và Phụ lục 02 ở những chỗ phụ thuộc; không đọc lại toàn bộ đặc tả khi không cần. Xuất bản kế hoạch diff và kiểm tra trùng với ECO-001–ECO-024. Bắt đầu ở giai đoạn A: schema versioned, registry, route resolver, trạng thái và evidence validator, bộ fixture và test ngăn nâng sai trạng thái. Sau đó làm App Capsule và Install Assistant ở giai đoạn B với ứng dụng thử được phép. Mỗi phần phải có CLI/API hoặc UI quan sát được, tiêu chí nghiệm thu, test thật và báo cáo giới hạn. Không tự nhận tương thích Word/Excel/Zalo/MISA, .NET Framework, cổng thuế/BHXH hay driver/token khi chưa thử đúng phiên bản, nghiệp vụ và thiết bị. Không ký/nộp thật hoặc gửi dữ liệu ra ngoài để test. Ghi rõ blocker cần vendor hoặc đơn vị pilot và quyết định go/no-go; cập nhật `docs/STATUS.md` sau mỗi mốc.

## 8. Nguồn kỹ thuật chính thức tham chiếu (truy cập 03/11/2026)

[1] Microsoft Learn, [Port from .NET Framework to .NET](https://learn.microsoft.com/en-us/dotnet/core/porting/framework-overview): .NET đa nền tảng cho mã không phụ thuộc Windows; .NET Framework là thành phần Windows.

[2] Microsoft Learn, [WPF overview](https://learn.microsoft.com/en-us/dotnet/desktop-wpf/overview/index): WPF chỉ chạy trên Windows.

[3] WineHQ, [About Wine](https://www.winehq.org/about): Wine là tầng tương thích cho ứng dụng Windows trên nền POSIX; không phải Windows kernel.

[4] OpenPrinting, [IPP-over-USB](https://openprinting.github.io/projects/03-ipp-usb): đường chuẩn cho một số máy in/quét USB hỗ trợ IPP/eSCL.

[5] OASIS, [PKCS #11 Specification v3.1](https://docs.oasis-open.org/pkcs11/pkcs11-spec/v3.1/os/pkcs11-spec-v3.1-os.html): giao diện tiêu chuẩn cho token mật mã, không phải chứng nhận tương thích một website cụ thể.

Tài liệu này là yêu cầu và thiết kế đích; **chưa phải báo cáo rằng NaMiOS đã thực hiện hoặc chứng nhận các phần mềm trên**.
