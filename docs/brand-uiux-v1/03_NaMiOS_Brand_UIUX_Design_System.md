# NaMiOS — Kim chỉ nam nhận diện, hình nền, icon và UI/UX v1.0

**Ngày:** 09/11/2026  
**Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam  
**Phạm vi:** tài sản thiết kế và yêu cầu để phát triển; không phải chứng nhận NaMiOS đã có các tính năng nêu dưới đây.

## 1. Triết lý sản phẩm

NaMiOS dành cho người Việt chuyển từ Windows sang một hệ Linux dễ dùng. Một tác vụ phải bắt đầu từ từ ngữ quen thuộc, có phản hồi tức thì, thành công được xác nhận và thất bại chỉ rõ **việc gì, ở đâu, vì sao đã xác định được, bước tiếp theo**. Giao diện hiện đại và yên tĩnh; hành vi File, thanh ứng dụng, tìm kiếm và phím tắt đủ quen để không phải học lại từ đầu. Lấy cảm hứng từ sự mạch lạc của các hệ điều hành hiện đại, không sao chép giao diện, biểu tượng, ứng dụng hoặc nhãn hiệu của Apple/Microsoft.

Ba nguyên tắc: (1) việc hằng ngày quan trọng hơn hiệu ứng; (2) sự thật về tương thích quan trọng hơn tuyên bố “chạy mọi ứng dụng”; (3) SmartAI giúp giải thích và hỗ trợ sửa lỗi theo quyền, không thay thế cơ chế chẩn đoán xác định hay quyết định của người dùng.

## 2. Nhận diện

**Biểu tượng:** sen Việt v2.0 với cánh đỏ son, tâm vàng, nét nước. **Tên:** NaMiOS, viết đúng chữ hoa/thường; chữ “OS” là điểm nhấn đỏ. Bản logo vector nguồn nằm ở bộ logo riêng đã bàn giao; icon hệ thống trong gói này là một họ nét độc lập. Không dùng quốc kỳ, quốc huy, bản đồ hoặc logo của hãng thứ ba làm icon của NaMiOS.

| Token | Nền sáng | Nền tối | Vai trò |
| --- | --- | --- | --- |
| `surface.base` | `#F5F2EB` | `#122A3A` | Desktop/dialog |
| `surface.card` | `#FFFFFF` | `#1B3748` | Panel |
| `text.primary` | `#182E3B` | `#F8F5EE` | Chữ chính |
| `text.secondary` | `#52646B` | `#C9D3D6` | Chữ phụ |
| `brand.red` | `#C93643` | `#E56365` | Nhận diện, không dùng làm màu thành công |
| `brand.gold` | `#BC8A43` | `#F2C66D` | Trang trí có kiểm soát |
| `action.primary` | `#006E72` | `#65D7C8` | Nút thao tác chính |
| `status.success` | `#127A52` | `#59C798` | Đã xong |
| `status.warning` | `#965300` | `#F6BB68` | Chú ý |
| `status.error` | `#B4232B` | `#FF8B8F` | Lỗi |

Màu là token thiết kế, **phải đo tương phản trên cặp nền/chữ thực tế**, không mặc nhiên coi bảng là đã đạt WCAG. Mục tiêu WCAG 2.2 AA: chữ thường tối thiểu 4.5:1; chữ lớn 3:1; vùng chạm tối thiểu 24×24 theo tiêu chí áp dụng, trong NaMiOS đặt mục tiêu thao tác tiện lợi 40×40 hoặc lớn hơn [4]. Trạng thái luôn có chữ và hình, không truyền đạt chỉ bằng màu.

**Chữ:** ưu tiên Noto Sans với đầy đủ dấu tiếng Việt, fallback DejaVu Sans và font hệ thống; giấy phép font cần lưu trong SBOM. Chữ nội dung 15–16 px ở 100%, nhãn 14 px, tiêu đề 20–32 px, tên trang 28 px. Dòng 1.4–1.6; cho phép phóng 200% mà không mất nút. Không dùng chữ hoa toàn bộ cho câu thông báo.

**Lưới:** 8 px; bán kính 8/12/16 px; panel 16 px; khoảng click tối thiểu 40 px; độ cao input/nút thường 40–44 px; nhóm thông tin 16–24 px. Hiệu ứng mở/đóng 120–220 ms, có chế độ giảm chuyển động và tắt blur. Focus ring nhìn thấy rõ khi dùng bàn phím; icon có nhãn truy cập; screen reader đọc nội dung lỗi và nút.

## 3. Hình nền mặc định

Thư mục `01_Wallpapers_3840x2160` có **20 JPG** và `wallpapers_manifest.json` ghi tên, hash, trạng thái. `Wallpapers_Contact_Sheet.jpg` cho xem một lượt. Các ảnh được tạo bằng AI, là **minh họa lấy cảm hứng từ địa danh/văn hóa Việt Nam**, không phải ảnh chụp tư liệu hay bằng chứng địa lý. Kích thước ảnh gốc 1672×941; file 3840×2160 được **nội suy**, không mang chi tiết quang học 4K gốc. Với bản thương mại, nên thay từng cảnh địa danh bằng ảnh thật được cấp phép và kiểm chứng tên/góc chụp; lưu tác giả, nguồn, giấy phép và khoản ghi công.

| Nhóm | Mã ảnh | Nội dung |
| --- | --- | --- |
| Biểu tượng | 01, 17 | Hoa sen; cảm hứng hoa văn trống đồng |
| Biển | 02–06, 20 | Hạ Long, Đà Nẵng, Nha Trang, Phú Quốc, Côn Đảo, biển đảo |
| Núi và nước | 07, 10–16 | Tràng An, Sa Pa, Hà Giang, Bản Giốc, Phong Nha, Đà Lạt, miền Tây, cao nguyên |
| Di sản đô thị | 08, 09, 18, 19 | Hội An, Huế, Mỹ Sơn, Hồ Gươm |

**Quy tắc hệ điều hành:** chọn ảnh 01 mặc định; có ảnh nền sáng/tối, xem trước crop ở 16:9/16:10/3:2/2 màn hình; giữ chủ thể khỏi vùng taskbar/desktop icon; tự thêm lớp scrim mỏng đằng sau nhãn icon để đọc được; không thêm khẩu hiệu/chữ trực tiếp lên ảnh; cho phép người dùng tắt xoay ảnh và chọn tệp cá nhân; giữ ảnh mặc định offline; metadata `title_vi`, `artist`, `source`, `license`, `kind`, `sha256`, `safe_area`, `min_supported_resolution`.

### 3.1 Bản đồ và chủ quyền lãnh thổ — cổng kiểm duyệt bắt buộc

Ảnh 20 là **cảnh biển đảo chung, không phải bản đồ**. Gói này **chưa có ảnh bản đồ được xác nhận** thể hiện chính xác đất liền, Hoàng Sa, Trường Sa, Phú Quốc, Côn Đảo và các đảo khác. Không đưa một bản đồ do AI vẽ hoặc biên lại từ trí nhớ vào ISO. Nguồn dữ liệu bản đồ cần được cấp phép sử dụng từ cơ quan có thẩm quyền hoặc đối tác bản đồ; cơ quan chuyên môn kiểm đường biên giới, địa giới, biển đảo, nhãn và tỷ lệ trước khi phát hành. Cổng cung cấp dữ liệu bản đồ và thủ tục thẩm định đã được cơ quan nhà nước công bố [1][2][3].

**Quy trình `MAP-01`:** tiếp nhận bản đồ có nguồn và giấy phép → đối chiếu phiên bản hành chính hiện hành và vùng biển/đảo → thiết kế khung bản đồ 16:9 với ô phụ nếu tỷ lệ khiến các quần đảo không đọc được → người chuyên môn kiểm độc lập 2 lượt → kiểm ảnh ở 1920×1080/4K, đọc được Hoàng Sa, Trường Sa, Phú Quốc → ký duyệt bằng văn bản → thêm manifest `approved_map_source`, `reviewer`, `approval_date`, `version`, `license` → mới đưa vào ảnh mặc định. Nếu chưa có giấy phép hoặc phê duyệt, **giữ ảnh 20 là biển đảo chung và đánh dấu bản đồ pending**. Hình nền không được dùng như bản đồ tra cứu hoặc xác lập pháp lý.

### 3.2 Nhân vật lịch sử

Không tạo chân dung nhân vật lịch sử bằng AI rồi gắn tên người thật nếu chưa kiểm nguồn chân dung, niên đại, quyền sử dụng và nội dung thuyết minh. Khi có hồ sơ được duyệt, thêm một gói wallpaper lịch sử riêng với chú thích trong màn hình giới thiệu, không viết lên ảnh desktop.

## 4. Hệ icon chung

Thư mục `02_Icon_System_SVG` có 24 icon nét cho chức năng cốt lõi: tệp, trình duyệt, kho ứng dụng, cài đặt, Wi‑Fi, Bluetooth, máy in, scan, USB, Ethernet, cập nhật, sao lưu, SmartAI, bảo mật, trợ giúp, lỗi, thành công, cảnh báo, tài liệu, PDF, ảnh, nhạc, camera, thùng rác. Mỗi icon 24×24, nét 1.9, đầu và góc bo, `currentColor`, SVG không tham chiếu mạng. Danh mục file và tên icon dùng thống nhất theo quy ước của Freedesktop khi đưa vào icon theme của Linux [5].

Icon **chỉ là ký hiệu chức năng**, không thay logo thương mại của Zalo, Office, Facebook… mà chưa có quyền. Khi hiển thị app bên thứ ba, dùng icon gốc từ gói ứng dụng hợp pháp; nếu không có thì dùng icon ứng dụng chung + tên rõ. Khi trạng thái lỗi/success hiển thị cùng nội dung văn bản. Thử trên 16, 24, 32, 48 px và nền tối; nếu biểu tượng không phân biệt được ở 16 px thì có bản symbolic giản lược riêng. Trước release chính thức cần làm thêm icon folder, MIME type, action, device, status đầy đủ và review với người dùng; 24 icon hiện tại là **bộ hạt giống**.

## 5. Mẫu desktop và thao tác quen thuộc

- **Thanh ứng dụng:** nút Mở ứng dụng ở trái, app ghim, app đang mở, đồng hồ/trạng thái mạng/âm thanh/pin ở phải. Nhấp một lần để mở/chuyển, nhấp phải để ghim, bỏ ghim, đóng. Mỗi app có nhãn tiếng Việt dễ tìm; không dùng icon trống.
- **Tìm kiếm chung:** mở từ nút Mở ứng dụng hoặc `Super`, ưu tiên ứng dụng, cài đặt, tệp gần đây; tài liệu riêng tư không gửi tới SmartAI hay máy chủ khi người dùng chưa chọn. Tìm không dấu/ có dấu, gợi ý tên cũ tương đương, ví dụ “máy in”/“printer”.
- **Trình quản lý tệp:** Thư mục cá nhân, Tài liệu, Tải về, Hình ảnh, USB, Mạng; breadcrumb; `Ctrl+C/V/X`, `F2`, `Delete`, `Shift+Delete` có xác nhận, thùng rác/hoàn tác. Hiện tiến trình khi sao chép lớn, tình trạng dung lượng và lỗi quyền rõ ràng.
- **Cửa sổ:** `Alt+Tab`, `Alt+F4`, `Super+E`, `Super+D`, `Super+L`, `Ctrl+Shift+Esc` theo hành vi quen thuộc; mở, đóng, thu nhỏ, phóng to; snap trái/phải bằng `Super+←/→`; tránh đè phím gõ tiếng Việt. Trợ giúp hiển thị bảng phím tắt có thể tìm.
- **Cài đặt:** Network, Bluetooth, Printer & Scanner, App, Update, Backup, Security, Input, Display; 1 đường điều hướng rõ, thanh tìm kiếm; trạng thái trước nút hành động.
- **Quyền:** app yêu cầu camera/micro/tệp/USB ghi rõ app nào, quyền gì, trong bao lâu, nút Từ chối/Cấp một lần/Luôn cho phép; thu hồi trong Settings. Không cho AI bấm thay khi quyền có tác động lớn.

## 6. Ngôn ngữ và phản hồi

Mẫu câu: **[Thiết bị/tác vụ] + [kết quả]**. Dòng phụ: **[điều đã kiểm tra] + [nguyên nhân xác định hoặc “chưa xác định”]**. Nút chính là động từ rõ ràng, ví dụ “Thử kết nối lại”, “Mở hàng đợi in”, “Chọn thiết bị khác”. Thông báo thành công 3–5 giây và vào lịch sử; lỗi kéo dài đến khi người dùng đóng hoặc xử lý; việc mất dữ liệu/đòi quyền dùng dialog. Không hiển thị mã kỹ thuật đơn độc. Không suy diễn nguyên nhân từ một tín hiệu mơ hồ. Có nút “Chi tiết kỹ thuật” cho IT, nút “Sao chép mã lỗi” và “Nhờ SmartAI giải thích”.

**Schema sự kiện:** `id`, `correlation_id`, `timestamp`, `component`, `device_id_masked`, `operation`, `phase`, `status`, `detected_cause_code`, `evidence`, `user_message_key`, `safe_actions[]`, `technical_detail_redacted`, `retry_count`, `result_after_action`. Phải phân biệt **thất bại bắt đầu**, **đang thử lại**, **thành công**, **thành công một phần**, **chưa xác định**. Bảo vệ SSID cá nhân, địa chỉ MAC, tên tệp, trang in, nội dung tài liệu, token, mật khẩu trong log gửi đi.

### 6.1 Máy in và máy scan

Luồng: phát hiện USB/mạng → xác định model/protocol → kiểm hỗ trợ in/scan riêng → thêm hàng đợi → in trang thử → xác nhận. Theo từng model, catalog ghi IPP/driver/backend, firmware, in màu/hai mặt, scan, phiên bản OS và trạng thái `tested/partial/unsupported`. Không mặc nhiên dùng driver Windows. Bảng thông điệp:

| Mã | Tín hiệu xác định | Thông báo cho người dùng | Nút an toàn | SmartAI |
| --- | --- | --- | --- | --- |
| `PRN-001` | Không tìm thấy máy trong mạng sau quét | “Chưa tìm thấy máy in. Hãy kiểm tra máy đã bật và cùng mạng Wi‑Fi.” | Quét lại; Xem mạng | Hỏi model/vị trí, không tự đổi router. |
| `PRN-002` | Model thấy được nhưng chưa có backend hỗ trợ | “Đã thấy [model], nhưng NaMiOS chưa có cách in phù hợp.” | Xem cách kết nối khác; Báo model | Tìm catalog/IPP và chỉ dẫn; không tải driver lạ. |
| `PRN-003` | Queue nhận việc, printer báo giấy/mực | “Lệnh in đang chờ: máy báo hết giấy hoặc mực.” | Mở hàng đợi; Thử lại | Giải thích tình trạng từ dữ liệu thiết bị. |
| `PRN-004` | Queue lỗi vận chuyển/timeout | “Máy in đã kết nối nhưng chưa nhận được trang in.” | Thử lại 1 lần; Xem kết nối | Kiểm CUPS/IPP/log đã che, tạo kế hoạch. |
| `SCAN-001` | In được, scan không có backend | “Máy này in được; chức năng quét chưa được hỗ trợ.” | Xem máy khác; Báo hỗ trợ | Không gọi `ready` cho toàn bộ MFP. |

### 6.2 Wi‑Fi và Ethernet

Luồng: radio/hardware → nhận SSID → xác thực → cấp IP → DNS → Internet/captive portal; hiển thị **bước đang thất bại**. Ví dụ `NET-001` tắt radio: “Wi‑Fi đang tắt. Bật Wi‑Fi để tìm mạng.”; `NET-002` mật khẩu sai theo kết quả xác thực: “Không kết nối được [SSID]: mật khẩu có thể không đúng”; `NET-003` có IP nhưng DNS lỗi: “Đã kết nối Wi‑Fi, nhưng chưa phân giải được tên website”; `NET-004` captive portal: “Cần đăng nhập mạng tại trang chào”; `NET-005` adapter chưa có driver/firmware: “Máy chưa nhận bộ thu Wi‑Fi [model]”. Không lộ mật khẩu trong dialog/log; “Internet không có” phải phân biệt với “Wi‑Fi không kết nối”. Ethernet có trạng thái dây chưa cắm, link, DHCP, DNS, portal.

### 6.3 Bluetooth và USB

Luồng Bluetooth: radio → discovery → pairing → profile → service connected. `BT-001`: “Chưa thấy thiết bị; hãy bật chế độ ghép đôi”; `BT-002`: “Đã ghép đôi nhưng tai nghe chưa dùng được âm thanh” (profile lỗi); `BT-003`: “Mã ghép đôi không khớp; thử lại trên cả hai thiết bị”; `BT-004`: “Kết nối bị ngắt khi máy ngủ; đang thử nối lại”. Nút “Quên thiết bị” có xác nhận. USB: phân biệt nhận phần cứng, mount, filesystem hỏng, thiếu quyền, bộ nhớ chỉ đọc, tháo an toàn.

### 6.4 Nguyên tắc SmartAI xử lý lỗi

Nhận sự kiện cấu trúc và bản log đã che → đọc trạng thái từ các công cụ chẩn đoán chuẩn → diễn giải bằng tiếng Việt → đề xuất tối đa 3 bước theo mức rủi ro → hiện bằng chứng và mức chắc chắn → xin người dùng xác nhận nếu đổi cấu hình/quyền/tệp → thực hiện qua API có chính sách, ghi audit, kiểm kết quả và có undo. AI **không đoán lỗi là driver** khi thiếu bằng chứng, không tự chạy lệnh tải mã ngoài, không gửi tài liệu/in/log nhạy cảm lên cloud mặc định. Khi AI offline hoặc sai, UI/diagnostics vẫn hoạt động bằng rule và mã lỗi xác định. Đánh giá 30 tình huống đã gắn nhãn bởi kỹ sư (10 in, 10 mạng, 10 Bluetooth) trước pilot; đo tỷ lệ giải đúng, hành động sai và khả năng hoàn tác, không chỉ độ trôi chảy câu trả lời.

## 7. Bàn giao kỹ thuật, triển khai và cổng chất lượng

1. **Design tokens:** file JSON/CSS và mapping sang toolkit desktop thực tế, không hardcode màu/font trong từng app.
2. **Assets:** nhập 20 wallpaper offline và 24 SVG; kiểm hash manifest; đóng gói cache thumbnail, hình nền chỉ đổi theo lựa chọn người dùng; license/AI provenance hiện trong “Thông tin ảnh”.
3. **Component library:** Button, Field, Select, Checkbox, Dialog, Toast, Progress, DeviceCard, ConnectionStepper, ErrorCard, AIPlanCard; mỗi component có trạng thái default/hover/focus/disabled/loading/error/success và bản sáng/tối.
4. **Error catalog:** cùng mã lỗi và văn bản ở UI, tài liệu hỗ trợ, telemetry; viết contract tests cho phase và localization; kiểm có hành động an toàn cho mỗi lỗi.
5. **Usability:** 15 người mới, trong đó có người lớn tuổi, làm 8 việc: tìm tệp, gõ tiếng Việt, kết nối Wi‑Fi, Bluetooth, cài máy in, in thử, đổi ảnh, nhờ AI giải thích lỗi. Quan sát thời gian, lỗi, tỷ lệ tự hoàn thành; sửa trước pilot.
6. **Accessibility:** bàn phím toàn bộ, screen reader, phóng 200%, tương phản, giảm chuyển động, biểu tượng có text; thử có và không có AI. Kiểm nhận diện icon ở 16/24/32 px.
7. **Release:** không gắn `shipped` cho bản đồ khi thiếu kiểm duyệt/giấy phép; không gọi ảnh AI là ảnh tư liệu; không gọi model máy in hỗ trợ hoàn toàn khi scan thất bại; không dùng lỗi chung chung “Đã xảy ra lỗi” khi có mã cụ thể.

## 8. Nguồn và ranh giới

[1] Dịch vụ cung cấp thông tin, dữ liệu, sản phẩm đo đạc và bản đồ: https://dichvucong.monre.gov.vn/pages/ChiTietThuTucHanhChinh.aspx?tt=129  
[2] Thẩm định đường biên giới quốc gia trên bản đồ: https://dichvucong.monre.gov.vn/pages/ChiTietThuTucHanhChinh.aspx?tt=132  
[3] Thẩm định địa giới hành chính trên bản đồ: https://dichvucong.monre.gov.vn/pages/ChiTietDichVuTrucTuyen.aspx?dv=131  
[4] WCAG 2.2 của W3C: https://www.w3.org/TR/WCAG22/  
[5] Freedesktop Icon Naming Specification: https://apol.pages.freedesktop.org/xdg-specs/icon-naming-spec/latest/index.html  
[6] Desktop Notifications Specification: https://specifications.freedesktop.org/notification/latest/  
[7] Danh sách di sản Việt Nam của UNESCO, đối chiếu tên chủ đề: https://whc.unesco.org/en/statesparties/vn

Ảnh tạo bằng AI mang tính nghệ thuật, cần biên tập và kiểm chứng địa danh trước truyền thông. Gói này là **bản thiết kế và tài sản thử nghiệm**, chưa phải hệ icon hoàn chỉnh hoặc bản đồ chủ quyền đã được duyệt.
