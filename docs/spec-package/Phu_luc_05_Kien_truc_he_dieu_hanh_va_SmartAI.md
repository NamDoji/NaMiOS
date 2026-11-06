# NaMiOS — Phụ lục 05: Kiến trúc máy làm việc hằng ngày và SmartAI chủ động

**Ngày:** 06/11/2026  
**Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam  
**Tính chất:** Yêu cầu bổ sung độc lập. Tiếp nối đặc tả nền, ECO-001–024, COMP-025–054 và SAI-001–042. Phụ lục này định nghĩa các điểm còn thiếu để NaMiOS dùng được như **máy làm việc chính** của người dùng Việt Nam. Mã mới **SYS-001–SYS-042**. Claude Code đọc file này, `docs/STATUS.md`, ADR và những hợp đồng/code liên quan đến phần triển khai; không cần đọc lại toàn bộ bộ đặc tả.

## 1. Quyết định kiến trúc

NaMiOS dùng Linux làm nền, giữ quyết định nền Debian 13 amd64 của ADR khởi đầu cho bản thử nghiệm đầu tiên cho tới khi có ADR thay đổi. Desktop có giao diện quen thuộc, nhưng mức tương thích phải được xác nhận theo **ứng dụng + phiên bản + workflow + thiết bị + tổ chức + bản NaMiOS**. Trình cài, lối tắt và cửa sổ giống Windows không làm chương trình phụ thuộc COM, driver kernel hoặc dịch vụ Windows tự chạy.

SmartAI là lớp **điều phối có khả năng quan sát và giải thích**: tiếp nhận mục tiêu, lập kế hoạch, gọi công cụ đã đăng ký, chẩn đoán, thử công thức tương thích trong lab và thu bằng chứng. Bộ quản lý quyền, trạng thái tệp, cập nhật, sao lưu, đăng nhập và quyết định phát hành là mã hệ thống có quy tắc kiểm thử được. Khi dịch vụ AI tắt, người dùng vẫn mở ứng dụng, làm việc offline, sao lưu, đăng nhập và in.

### 1.1 Năm hợp đồng cần ổn định

| Hợp đồng | Thành phần | Quy tắc |
| --- | --- | --- |
| Máy và thiết bị | Kernel/driver Linux, CUPS/SANE, network, session, power | Thiết bị được định danh đến model/chức năng; không nạp Windows kernel driver vào Linux. |
| Desktop | File manager, menu, khay hệ thống, tìm kiếm, thiết lập, bộ gõ | Hành động mở/lưu/in/chia sẻ nhất quán giữa app Linux, Wine và remote khi tính năng thực hỗ trợ. |
| Ứng dụng | Catalog, installer, app capsule, browser, remote/VM | Một app/version có route, license, quyền, phụ thuộc, test và rollback riêng. |
| SmartAI | Planner, tool broker, policy, evidence | AI đề xuất; công cụ thực thi trong quyền cụ thể; validator cấp trạng thái. |
| Quản trị | Policy tổ chức, cập nhật, backup, audit, helpdesk | Rollout theo nhóm, có thể phục hồi, không nâng cấp lỗi khi workflow bắt buộc đang hoạt động. |

### 1.2 Các khoảng trống cần ưu tiên

| Công việc Windows người dùng đang làm | NaMiOS phải cung cấp | Điều kiện tính là đạt |
| --- | --- | --- |
| Bấm đúp tệp Word/Excel/PDF/XML từ ổ cứng hoặc ổ mạng | File association, app chooser, cảnh báo mode và độ đúng tài liệu | Mở đúng ứng dụng được chọn; không làm sai dữ liệu hoặc ghi đè bất ngờ. |
| Cài bản cập nhật phần mềm kế toán và nhập dữ liệu | Installer có nguồn, runtime/DB, app capsule, backup | Cài, chạy, giữ số liệu, restore; test nghiệp vụ đúng phiên bản. |
| In chứng từ, scan, ký và nộp | In/scan, token/middleware, browser, biên nhận | Workflow đầu cuối bằng môi trường được phép, output đúng. |
| Dùng tài khoản công ty và ổ mạng | Identity, VPN, proxy, SMB, quyền, máy in mạng | Đúng vai trò, đúng dữ liệu, mất mạng xử lý được. |
| Đóng máy, mở lại, nhận bản cập nhật | Sleep/resume, pin, update, rollback | Không mất dữ liệu, app và thiết bị hoạt động lại. |
| Nhờ IT khi lỗi | Diagnostics, remote assistance có kiểm soát, backup | IT tái hiện được lỗi mà không nhận bí mật ngoài phạm vi. |

Những điều kiện đã có ở ECO/COMP/SAI vẫn giữ nguyên; mã SYS dưới đây bổ sung hợp đồng kỹ thuật, hành vi UI và cách nghiệm thu, không tạo một hệ thống song song.

## 2. Desktop tương tác như máy Windows quen thuộc

**SYS-001 P0 — Bộ thực thi tác vụ chung.** Desktop đưa hành động `open_file`, `open_app`, `print`, `scan`, `share`, `open_url`, `connect_share` vào một action broker. Mỗi action trả ID, trạng thái, route, quyền và lỗi cấu trúc. SmartAI dùng đúng broker đó; app thường và người dùng cũng dùng được khi AI vắng mặt. **Nghiệm thu:** cùng một file mở bằng chuột, tìm kiếm và yêu cầu tiếng Việt dẫn tới cùng ứng dụng/mode theo policy.

**SYS-002 P0 — Mở tệp và ứng dụng mặc định.** Tôn trọng chuẩn desktop entry và MIME association của Linux [1]; file manager cho đổi ứng dụng mặc định, xem app hỗ trợ và mức tương thích tài liệu; file `.exe` không tự chạy ngay khi nhấp đúp. **Nghiệm thu:** DOCX, XLSX, XML, PDF, CSV, `.url`, tệp có dấu Việt, tên dài và tệp trên ổ mạng mở đúng route; đổi mặc định có thể hoàn tác.

**SYS-003 P0 — Lối tắt, Start/menu và tìm kiếm.** Menu ứng dụng theo nhóm việc (Văn phòng, Thuế, Kế toán, Bảo hiểm, Giáo dục, Hành chính); app Wine có lối tắt gắn đúng capsule, app web mở miền đã xác minh, app remote hiện nhãn Windows từ xa. Tìm có/không dấu, theo tên thông dụng; không hiện sản phẩm chưa được cài như đã cài. **Nghiệm thu:** gõ “hoa don” thấy đúng phần mềm/portal và trạng thái thực, không lẫn launcher mẫu.

**SYS-004 P1 — Khay hệ thống và cửa sổ.** Hỗ trợ thông báo, nhiều cửa sổ, Alt+Tab, snap, màn hình ngoài, scale DPI và khay ứng dụng; ứng dụng Wine chạy nền không biến mất khi đóng cửa sổ chính. SmartAI nhận trạng thái cửa sổ qua API cho phép, không dựa vào chụp màn hình liên tục. **Nghiệm thu:** đa màn hình, sleep/resume, scale 100/125/150%, tiếng Việt và clipboard không rơi ký tự.

**SYS-005 P0 — Clipboard và kéo thả qua các mode.** Clipboard văn bản/hình/tệp có nhãn nguồn, loại nội dung và chính sách dữ liệu; việc chuyển sang remote/VM phải hiển thị đích và quyền. Không cho app không tin cậy đọc lịch sử clipboard hoặc chuyển dữ liệu nhạy cảm sang máy khác mặc định. **Nghiệm thu:** copy bảng tiếng Việt và ảnh qua app Linux↔Wine; kiểm thử remote theo policy, dữ liệu bị hạn chế phải bị chặn.

**SYS-006 P1 — Chế độ học cách dùng NaMiOS.** Các hướng dẫn ngắn “Tệp của tôi”, “Máy in”, “Ứng dụng”, “Ổ mạng”, “Cập nhật”, “Hỏi SmartAI”; cung cấp phím tắt quen thuộc khi không xung đột; không sao chép biểu tượng, asset hoặc giao diện Microsoft có bảo hộ. **Nghiệm thu:** pilot tự hoàn thành năm tác vụ trên sau một buổi hướng dẫn, đo thời gian và lỗi, ghi dữ liệu thật thay vì tự đặt tỷ lệ.

**SYS-007 P0 — Bộ gõ và locale xuyên mode.** Telex/VNI, gõ dấu trong browser, Wine, ứng dụng GTK/Qt và remote; locale tiếng Việt, số tiền/ngày/giờ và font tương thích; bảo vệ dữ liệu số không bị thay dấu phân tách ngoài ý muốn. **Nghiệm thu:** bộ câu chữ và số mẫu qua ô nhập, tệp, in, PDF, XML và remote; sai 1 chữ số tiền là fail.

## 3. Tương thích ở mức hệ điều hành và ranh giới Windows

**SYS-008 P0 — Compatibility Profile khớp đúng app.** Metadata nhận dạng app theo nhà phát hành, version, kiến trúc, hash và file phụ trợ; gắn recipe, runtime, runner và mức xác minh. Đây là cách áp dụng có chọn lọc, tương tự ý tưởng cơ sở dữ liệu tương thích theo ứng dụng của Windows [2], nhưng NaMiOS tự quản hợp đồng của mình. **Nghiệm thu:** installer đã đổi hash không tự dùng recipe cũ; kết quả hiển thị lý do chọn route.

**SYS-009 P0 — Phân loại dạng cài đặt.** Hỗ trợ luồng xét bộ cài Linux, Flatpak/định dạng phân phối đã chọn, `.deb` được phép, `.exe`, `.msi`, bộ cài portable và web app. Hiển thị nguồn, giấy phép, phụ thuộc, hành động và quyền; không quảng cáo một định dạng là đã hỗ trợ nếu chưa có executor. **Nghiệm thu:** hai ứng dụng Windows mẫu mở nguồn có đường cài/khôi phục; gói thiếu nguồn có cảnh báo rõ.

**SYS-010 P0 — Ranh giới đường dẫn và profile người dùng.** Tách dữ liệu user, app data, cache, profile Wine, thư mục chia sẻ và backup. Ánh xạ `C:\Users\...` cho app Wine trong capsule, chỉ mount thư mục người dùng đã chọn; xử lý tên có dấu, hoa/thường, dấu cách, path dài, symlink và tệp đang khóa. **Nghiệm thu:** không truy cập được file ngoài quyền; Save As và restore giữ nguyên checksum trên tệp mẫu.

**SYS-011 P1 — COM, shell extension và dịch vụ Windows.** Lập inventory tác động của COM/OLE, Windows service, hook Explorer, filter/virtual drive và scheduled task. Chúng chạy trong Windows thì không tự trở thành extension của desktop Linux; chỉ tích hợp qua API hoặc adapter được phép. **Nghiệm thu:** mẫu app có COM context-menu yêu cầu Windows bị phân loại blocker; không tuyên bố “đã tích hợp” khi chỉ launch được GUI.

**SYS-012 P0 — Cầu nối tệp giữa Linux/Wine/remote.** Quy định chọn tệp, mở, lưu, version/conflict, download và backup; khi remote phải xác định file nằm ở máy nào, có upload không, hash có giống không. Không tự copy dữ liệu pháp lý ra máy Windows từ xa. **Nghiệm thu:** một DOCX có dấu Việt mở, sửa, lưu và trở về đúng nơi; hủy hoặc mất kết nối không tạo bản ghi đè lặng lẽ.

**SYS-013 P0 — Chứng nhận từ đầu đến cuối.** Duy trì ba trục riêng: chạy kỹ thuật, đúng nghiệp vụ, hoàn tất với bên ngoài; GUI mở được, tệp tải được, app cài được đều không đủ. Trạng thái phải tương thích ECO-003, COMP-048, SAI-012. **Nghiệm thu:** mô phỏng sai tổng tiền hoặc thiếu biên nhận thì không thể publish badge workflow.

**SYS-014 P1 — Windows fallback hữu hình.** Khi chỉ có Windows VM/remote, người dùng thấy nhãn, chi phí/giấy phép, giới hạn offline, vị trí dữ liệu, khả năng chuyển clipboard/in/token; việc dùng Windows phải được đo riêng. FreeRDP là một triển khai RDP mở, nhưng từng chức năng chuyển thiết bị/clipboard vẫn phải test theo môi trường [3]. **Nghiệm thu:** mất kết nối giữ trạng thái cần xử lý; không tự gửi lại giao dịch.

## 4. Thiết bị và kết nối phục vụ công việc

**SYS-015 P0 — Kho profile phần cứng.** Mỗi model laptop/PC và peripheral có CPU/GPU, Wi-Fi, Bluetooth, audio, webcam, touchpad, màn hình, sleep/resume, pin, Ethernet, USB-C, máy in và token; trạng thái `untested/works/partial/blocked` cho từng chức năng. **Nghiệm thu:** 3 mẫu laptop và 2 mẫu desktop pilot có phiếu kiểm, không suy hỗ trợ từ tên hãng.

**SYS-016 P0 — Máy in/quét có kết quả nhìn thấy.** Phát hiện IPP/CUPS và eSCL/SANE khi thiết bị hỗ trợ; xác nhận model, giấy, lề, hai mặt, QR/barcode, PDF nhiều trang và in chứng từ. IPP-over-USB hữu ích với thiết bị tương thích, không phải lời bảo đảm cho mọi máy USB [4]. **Nghiệm thu:** người nghiệp vụ ký xác nhận output; hàng đợi kẹt/máy offline trả lỗi và cách khôi phục.

**SYS-017 P0 — USB token và thiết bị chuyên ngành.** Device registry + cấp quyền theo phiên cho từng model; bridge chỉ qua Linux middleware/PKCS#11/SDK chính thức của vendor khi có. Rút/cắm, đổi cổng USB, hết hạn chứng thư và lỗi PIN phải xử lý có trạng thái. **Nghiệm thu:** token lab trả certificate metadata đúng, không lưu PIN; portal chỉ có plugin Windows ghi blocker.

**SYS-018 P1 — Webcam, mic, âm thanh và họp trực tuyến.** Test browser và ứng dụng họp đơn vị pilot dùng: chọn thiết bị, echo cancellation, quyền mic/camera, chia sẻ màn hình, headset Bluetooth/USB. **Nghiệm thu:** gọi thử 30 phút, mất/kết nối lại thiết bị và chia sẻ màn hình không lộ cửa sổ khác ngoài phạm vi người dùng chọn.

**SYS-019 P0 — Năng lượng và phục hồi phiên.** Suspend, resume, khóa màn hình, cắm/rút dock, thay Wi-Fi, cạn pin; thông báo khi app Wine/DB/token cần kết nối lại. SmartAI không tự suy rằng hồ sơ đã được nộp sau resume. **Nghiệm thu:** 20 chu kỳ sleep/resume trên phần cứng pilot, so file/DB, tiếp tục in và mạng; lỗi có thể tái hiện.

**SYS-020 P1 — Mạng tổ chức.** Wi-Fi/captive portal, proxy, VPN, TLS certificate trust, DNS nội bộ, đồng bộ giờ, SMB/NAS; cấu hình bởi IT theo quyền. Samba triển khai các giao thức SMB/AD cho Linux, nhưng việc gia nhập domain và chính sách riêng của từng tổ chức cần thử [5]. **Nghiệm thu:** 2 nhóm quyền đọc/ghi ổ mạng đúng, bị ngắt VPN không mất dữ liệu.

**SYS-021 P1 — Đăng nhập doanh nghiệp.** Chế độ local và cơ chế kết nối AD/LDAP/Kerberos/SSO được tổ chức chọn; không hứa thay thế toàn bộ Group Policy Windows. Mapping người dùng/nhóm và chính sách NaMiOS có bản kiểm tra hiệu lực. **Nghiệm thu:** tài khoản bị thu hồi không còn truy cập ổ mạng, quyền kế toán khác quyền giáo viên, audit không chứa password.

## 5. Lõi vận hành của hệ điều hành

**SYS-022 P0 — Cài máy không phá dữ liệu.** Trước cài đặt kiểm tra firmware, Secure Boot, phân vùng, mã hóa, không gian, backup, app/thiết bị blocker và đường quay Windows; tiến trình chia bước và có biên bản quyết định. Chỉ cài khi người quản lý máy xác nhận phân vùng đích. **Nghiệm thu:** ca thử dual boot/lab giữ dữ liệu Windows; ngắt nguồn ở các bước được mô phỏng có đường khôi phục.

**SYS-023 P0 — Cập nhật có lớp thử và quay lại.** Kênh lab/pilot/stable, chữ ký nguồn, pin kernel/driver/Wine/recipe, snapshot hoặc rollback tương đương; SmartAI chỉ giải thích tác động và lên lịch trong khung cho phép. **Nghiệm thu:** cập nhật lỗi Wi-Fi hoặc phần mềm kế toán không được đi stable; rollback phục hồi boot và dữ liệu người dùng.

**SYS-024 P0 — Backup có thử restore.** Sao lưu tệp cá nhân, app capsule, cấu hình, recipe, DB test và metadata phiên bản theo loại dữ liệu; backup DB sản xuất chỉ theo quy trình vendor/IT đã duyệt. Có mã hóa, thời hạn lưu, trạng thái bản cuối và bài thử restore định kỳ. **Nghiệm thu:** chọn tệp/ứng dụng ngẫu nhiên để restore vào máy lab; đối chiếu hash và mở được app tương ứng.

**SYS-025 P0 — Phân quyền và bí mật.** Tài khoản thường, admin, IT hỗ trợ; khóa màn hình, mã hóa đĩa theo chính sách, kho bí mật hệ thống, xác thực cập nhật, firewall; SmartAI không có root token mặc định. **Nghiệm thu:** user không sửa package/policy tổ chức; bí mật giả không xuất hiện trong logs/recipe.

**SYS-026 P1 — Sức khỏe máy.** Tự chẩn đoán dung lượng, RAM, nhiệt, tình trạng pin/ổ, mạng, máy in, giờ và bản cập nhật với nguồn dữ liệu có sẵn; cảnh báo theo ngưỡng đo được; không dự đoán “sắp hỏng” khi thiếu bằng chứng. **Nghiệm thu:** 5 lỗi mô phỏng có cảnh báo cụ thể và nút điều hướng sửa.

**SYS-027 P0 — Lối hỗ trợ IT.** Export report có bước xem trước và khử dữ liệu; remote assistance chỉ sau khi chủ máy cho phép và có chỉ báo đang chia sẻ; ghi log hành động admin và nút kết thúc phiên. **Nghiệm thu:** người hỗ trợ không thấy tệp chưa chọn; phiên mất mạng hoặc hết hạn tự ngắt.

**SYS-028 P1 — Vòng đời người dùng.** Tạo, chuyển, khóa, xóa account và chuyển máy có xuất dữ liệu; phân tách profile đa người dùng, app capsule cá nhân/chung, quyền printer/share. **Nghiệm thu:** người dùng A không đọc profile SmartAI, tệp hoặc token cấp cho B.

## 6. Nâng cấp SmartAI để thực sự giúp người dùng

**SYS-029 P0 — SmartAI hiểu ngữ cảnh đang làm việc.** Context chỉ gồm cửa sổ/app/tệp/thiết bị mà người dùng chọn hoặc policy cho phép, bước workflow và trạng thái tool; không mặc định đọc màn hình, bàn phím hay mọi tệp. Trả lời “vì sao chưa làm được” bằng evidence ID và cách tiếp tục. **Nghiệm thu:** hai cửa sổ mở cùng lúc, AI không đọc dữ liệu cửa sổ chưa cấp.

**SYS-030 P0 — Mục tiêu đến kết quả.** Người dùng nói “in bảng lương”, SmartAI xác định ứng dụng/tệp, quyền, máy in, trang, người nhận, kết quả cần chứng minh; hỏi lại khi thiếu tài liệu/máy in. Workflow kết thúc sau khi job status và bản in được người dùng xác nhận nếu nghiệp vụ đòi, không kết thúc ở nút Print. **Nghiệm thu:** máy in offline thì status partial/blocked, không trả “đã in xong”.

**SYS-031 P0 — Học từ lỗi có giới hạn.** Tự nhóm lỗi theo app/version/runner/device, tạo giả thuyết sửa, thử trong bản sao, chứng minh output; chỉ công bố recipe sau review/test theo SAI-010–012. Cập nhật kiến thức không làm thay đổi máy người dùng đang làm việc. **Nghiệm thu:** một lỗi đã sửa ở lab không tự thay profile của tổ chức khác.

**SYS-032 P1 — Tự kiểm môi trường theo lịch sự kiện.** Khi app/driver/portal được cập nhật hoặc device thay đổi, gợi ý kiểm lại đúng các workflow liên quan; chẩn đoán chỉ đọc metadata cho tới khi người dùng cho phép thử. Không tự chạy nộp thuế, phát hành hóa đơn hay đăng nhập cổng nhà nước. **Nghiệm thu:** cập nhật browser làm workflow portal cần retest, workflow kế toán offline không bị đánh dấu vô cớ.

**SYS-033 P0 — Cầu nối trợ giúp tại chỗ.** Trên trang lỗi, SmartAI đề xuất tối đa ba bước cụ thể từ catalog/evidence: thử lại an toàn, chuyển route, mở yêu cầu IT/vendor; có nút xem log đã lọc và lý do. Không lặp vô hạn hay khuyên tải DLL ngẫu nhiên. **Nghiệm thu:** lỗi thiếu driver Windows dẫn tới vendor hoặc VM/remote hợp lệ, không “tự tạo driver”.

**SYS-034 P1 — Hướng dẫn chuyển từ Windows theo hồ sơ người dùng.** Sau inventory chỉ đọc, tạo báo cáo `sẵn sàng/chưa sẵn sàng` cho 10 việc bắt buộc, nguồn tải app, thời gian học, chi phí fallback; chủ máy duyệt bước chuyển dữ liệu. **Nghiệm thu:** thiếu một việc P0 làm báo cáo no-go, không cài đè Windows.

**SYS-035 P0 — Đo tài nguyên AI.** Giới hạn CPU/RAM/băng thông/model cost, ưu tiên app của người dùng và pin khi laptop; AI model lỗi thì tool có thể hủy và desktop vẫn dùng. **Nghiệm thu:** chạy inference trong nền không làm app kế toán mất dữ liệu hoặc treo desktop; đo trên phần cứng pilot, chưa đặt số hiệu năng giả.

**SYS-036 P0 — Chính sách dữ liệu và chống lệnh từ tài liệu.** Dữ liệu file, webpage, log là nguồn không tin cậy; chỉ lời người dùng trong kênh tương tác được công cụ xác nhận, cộng policy tổ chức, mới cấp quyền. Tài liệu thuế chứa “xóa backup” không tạo action. **Nghiệm thu:** prompt injection trong DOCX/log không gọi tool xóa hoặc outbound.

## 7. Hợp đồng dữ liệu cho hệ thống

```yaml
schema_version: 1
device_profile:
  machine_id: pseudonymous
  os_build: unresolved
  model: unresolved
  capabilities: [wifi, audio, camera, suspend, printing]
  results: {}
app_route:
  app_id: unresolved
  version: unresolved
  publisher: unresolved
  installer_hash: null
  mode: unresolved
  license_status: unknown
  recipe_id: null
  verified_workflows: []
workflow_run:
  task_id: example
  user_intent: "In chứng từ"
  route_id: null
  steps: []
  evidence_ids: []
  business_approval: pending
  state: proposed
```

**SYS-037 P0 — Hợp đồng dùng chung.** Version hóa `device_profile`, `app_route`, `workflow_run` và action broker; references tới ECO/COMP/SAI thay vì sao chép status và policy. Schema validator chặn route thiếu source/version và bước “completed” thiếu evidence. **Nghiệm thu:** UI, CLI, SmartAI và helpdesk đọc cùng hồ sơ cho cùng trạng thái.

**SYS-038 P0 — Danh mục khả năng thật.** Bảng hỗ trợ hiển thị phạm vi theo app/version, từng workflow, model máy và device, môi trường lab/pilot, ngày test, vendor support và giới hạn. Tách `available to download`, `launches`, `workflow verified`. **Nghiệm thu:** người dùng mở từ menu thấy đúng cảnh báo trước khi chọn máy chính.

## 8. Kế hoạch bàn giao cho Claude Code

| Mốc | Công việc | Kết quả để duyệt |
| --- | --- | --- |
| K0 — Thiết kế hợp đồng | SYS-001, 002, 008, 013, 037, 038; map ECO/COMP/SAI, ADR cho thay đổi | Schema + action broker mẫu + test không nâng status sai; tránh module trùng. |
| K1 — Máy làm việc dùng hằng ngày | SYS-003–007, 009, 010, 015, 019, 022–025 | ISO trên máy lab, cài/boot, login, mở tệp, gõ tiếng Việt, in, sleep, update/rollback, backup/restore. |
| K2 — Tương thích nghiệp vụ | SYS-011, 012, 014, 016–018, 020, 021 | Ba persona pilot, ứng dụng/version/thiết bị thật, so Windows đối chứng; blocker được ghi đúng. |
| K3 — SmartAI chủ động | SYS-029–036 và integration SAI | Tác vụ tiếng Việt → route → quyền → tool → evidence; không cần AI để chạy desktop; test injection/rollback. |
| K4 — Rollout tổ chức | SYS-026–028, 034, dashboard readiness | IT và chủ máy xem rõ no-go/go; hỗ trợ/thu hồi; cập nhật theo vòng có kiểm soát. |

**SYS-039 P0 — Thử trên ba chân dung:** (1) giáo viên/văn phòng trường: Word/Excel, in, cổng giáo dục; (2) kế toán doanh nghiệp nhỏ: DB, báo cáo, hóa đơn, ký/thuế/BHXH; (3) nhân viên hành chính: browser portal, ổ mạng, chữ ký, PDF/in. Mỗi persona đưa 10 việc bắt buộc và hai việc theo mùa, người dùng thật xác nhận. **Nghiệm thu:** hồ sơ từng việc có người duyệt, bản Windows đối chứng, lỗi và khả năng quay lại.

**SYS-040 P0 — Điểm dừng rollout.** Dừng chuyển máy chính nếu có sai số tiền, mất tài liệu, mất DB, thiếu trang in, sai chữ ký/người ký, không lấy được kết quả portal bắt buộc hoặc backup không restore. **Nghiệm thu:** cố tình làm hỏng một fixture nghiệp vụ, release gate chuyển no-go và hỗ trợ rollback.

**SYS-041 P1 — Bảng đo sản phẩm.** Báo tỷ lệ việc bắt buộc hoàn thành trên NaMiOS, tỷ lệ hoàn thành không cần Windows, thời gian hoàn thành so máy đối chứng, số lần SmartAI tự sửa được đã được xác minh, lỗi lặp, thời gian khôi phục và chi phí hỗ trợ. Không suy số lượng app trong catalog thành số lượng app tương thích. **Nghiệm thu:** dashboard truy ngược tới workflow/evidence, không cho tăng số đạt từ feedback chat đơn lẻ.

**SYS-042 P0 — Release note trung thực.** Công bố phần cứng, app/version, workflow, thiết bị, mode và giới hạn, ngày kiểm, giấy phép của fallback, known issues và nguồn cài chính thức; badge hết hạn/tái kiểm khi thành phần phụ thuộc đổi. **Nghiệm thu:** bản phát hành pilot có bảng chức năng đã thử và chưa thử, không có lời hứa “mọi app Windows”.

## 9. Bản kiểm thử tích hợp cần chạy trên máy thật

| Test | Chuỗi hành động | Pass khi |
| --- | --- | --- |
| H01 | Cài NaMiOS trên máy lab giữ Windows; khởi động hai hệ | Windows/NaMiOS boot, dữ liệu gốc nguyên, đường hồi phục rõ. |
| H02 | Wi-Fi → VPN → SMB, sửa tệp có dấu và khóa tệp | Quyền đúng, checksum đúng, mất mạng có báo trạng thái. |
| H03 | DOCX/XLSX mẫu → mở → sửa → in → PDF | Dữ liệu số, font, trang và bản in được so theo tiêu chí nghiệp vụ. |
| H04 | App Wine mẫu → cài → update → rollback → mở lại | Capsule tách biệt, file test còn và app hoạt động. |
| H05 | App kế toán thử có DB → báo cáo → backup → restore | Số tiền khớp Windows đối chứng, DB phục hồi. |
| H06 | Portal sandbox → login → ký thử → nhận kết quả | Có quyền thử, biên nhận hợp lệ; thiếu sandbox ghi blocker. |
| H07 | In mất mạng/máy in offline, rút token trong lúc ký | Không báo thành công sai, không tạo giao dịch lặp. |
| H08 | Sleep/resume 20 lần, docking và monitor ngoài | Dữ liệu nguyên, mạng/thiết bị nối lại hoặc lỗi cụ thể. |
| H09 | SmartAI nhận yêu cầu tiếng Việt, tool fail và log có prompt injection | Trạng thái fail, không cấp quyền, không lộ file. |
| H10 | Update bản pilot gây lỗi app P0 | Release stable bị chặn, rollback dùng được. |

## 10. Lệnh giao việc để gửi Claude Code

> Triển khai phụ lục 05 SYS-001–SYS-042 cho NaMiOS. Trước tiên đọc `docs/STATUS.md`, ADR khởi đầu, schema/action/policy đang có và những mục ECO/COMP/SAI có liên quan. Tạo ma trận “yêu cầu mới → module hiện có → thay đổi cụ thể → test” để tránh trùng. Thực hiện K0 rồi K1 bằng code và test, không dừng ở tài liệu/giao diện. Desktop, CLI và SmartAI phải dùng cùng action broker, route và evidence; AI lỗi không được làm máy không dùng được. Tiếp tục K2 trên fixture trước, đòi phần mềm và thiết bị pilot thật để chứng nhận nghiệp vụ. Với giao dịch thật, ký số, license, domain và driver vendor, áp dụng quyền, nguồn và môi trường test đã được cấp; thiếu thì ghi blocker. Cập nhật `docs/STATUS.md` sau mỗi mốc: commit/code paths, test đã chạy, số liệu đo, workflow được kiểm, giới hạn, go/no-go và việc cần chủ dự án cung cấp. Không gắn badge “tương thích” cho app chỉ cài hay mở được.

**Đầu vào để kiểm thử thật:** ba mẫu máy và hai model máy in người dùng đang có; một trường/đơn vị văn phòng và một doanh nghiệp kế toán tình nguyện; tên/version app, license, máy Windows đối chứng, file/DB test, loại token/middleware, quyền dùng portal sandbox và quản trị viên cho VPN/domain. Các đầu vào này không cản phát triển K0 và phần độc lập của K1.

## 11. Nguồn kỹ thuật được đối chiếu (06/11/2026)

[1] freedesktop.org, [Desktop Entry Specification](https://wiki.freedesktop.org/www/Specifications/desktop-entry-spec/) và [MIME Applications Associations](https://specifications.freedesktop.org/mime-apps/latest/): menu/lối tắt và ứng dụng mặc định.

[2] Microsoft Learn, [Application Compatibility Database](https://learn.microsoft.com/en-us/windows/win32/devnotes/application-compatibility-database): cơ chế Windows nhận diện theo thuộc tính ứng dụng và áp dụng khắc phục theo app; dùng như bài học thiết kế, không sao chép thành phần Windows.

[3] FreeRDP, [Remote Desktop Protocol Implementation](https://www.freerdp.com/): một lựa chọn client RDP; chức năng phải kiểm trong môi trường cụ thể.

[4] OpenPrinting, [IPP-over-USB](https://openprinting.github.io/projects/03-ipp-usb): in/quét không driver theo chuẩn khi thiết bị hỗ trợ.

[5] Samba, [What is Samba?](https://www.samba.org/samba/what_is_samba.html): triển khai giao thức SMB và Active Directory trên Linux.

**Giới hạn:** tài liệu này là đặc tả bổ sung. Các bài kiểm H01–H10 là điều kiện phải thực hiện; chưa có kết quả chứng nhận NaMiOS trên ứng dụng hoặc thiết bị thật.
