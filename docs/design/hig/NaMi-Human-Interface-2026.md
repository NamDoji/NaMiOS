# PHỤ LỤC 22 — NaMi Human Interface
## Đặc tả sản phẩm và triển khai giao diện hệ điều hành cho người Việt

**Phiên bản:** 1.0 — 11/11/2026  
**Người đề xuất:** Đỗ Chí Cường và Đỗ Bảo Nam  
**Phạm vi:** Hệ điều hành NaMi (NaMiOS là tên dự án đang rà soát), các ứng dụng hệ thống do NaMi phát triển và trải nghiệm cài đặt → sử dụng → cập nhật → khôi phục.  
**Tài sản nhận diện liên quan:** `NaMi_Brand_DongSon_Full_Kit_v1.zip`. Đây là tài liệu **mới, độc lập** để Claude Code đọc và thực hiện, không thay thế các phụ lục về lõi OS, driver hoặc tương thích ứng dụng.

> Tên hiển thị “NaMi” và tên hệ điều hành thương mại cần được quyết định sau khi rà soát nhãn hiệu. Dùng “NaMi” trong bản mẫu này; giữ tên trong design tokens và bản địa hóa để có thể đổi mà không sửa từng màn hình.

---

## 1. Tuyên ngôn sản phẩm

NaMi là trải nghiệm máy tính **đẹp, thân thuộc, dễ học, an toàn và hữu ích** cho người Việt. Người mới dùng có thể hoàn thành tác vụ cơ bản mà không cần hiểu Linux. Người đã dùng Windows có thể dựa vào thao tác, vị trí chức năng và phím tắt quen thuộc. Người thành thạo vẫn có đủ công cụ, khả năng tùy chỉnh và thông tin kỹ thuật.

**Chất lượng tham chiếu, không phải bản sao:** học cách Apple tổ chức phân cấp, khoảng trắng, chuyển động và chi tiết; học cách Windows tổ chức desktop, nhiều cửa sổ và luồng công việc; học GNOME/KDE về khả năng tích hợp Linux và giao diện thích ứng. Tạo ngôn ngữ NaMi riêng từ biểu tượng trống đồng, sắc màu Việt Nam và nội dung tiếng Việt. Không sao chép icon, hình nền, tên gọi, âm thanh, hiệu ứng hoặc bố cục nhận diện đặc thù của hãng khác.

**Ba lời hứa với người dùng:**
1. Bật máy là biết bắt đầu ở đâu.
2. Máy giải thích rõ điều gì đang xảy ra và người dùng có thể làm gì tiếp.
3. Khi lỗi xảy ra, dữ liệu và khả năng phục hồi được ưu tiên hơn hiệu ứng hình ảnh.

## 2. Đối tượng, môi trường và tác vụ ưu tiên

| Nhóm | Tác vụ thường gặp | Trở ngại phải giải quyết |
|---|---|---|
| Gia đình, người lớn tuổi | Zalo, trình duyệt, ảnh, video, in tài liệu | Chữ nhỏ, thông báo kỹ thuật, khó tìm ứng dụng |
| Học sinh, giáo viên | Office, PDF, máy in, Wi‑Fi, họp trực tuyến | File tải về khó tìm, font lỗi, in sai khổ |
| Văn phòng, kế toán | Nhiều cửa sổ, Excel tương thích, USB ký số, scan | Thiết bị/ứng dụng có mức tương thích khác nhau |
| Cơ quan, trường học | Cài hàng loạt, tài khoản, cập nhật, hỗ trợ từ xa | Quyền, bảo mật, quản trị, giải thích sự cố |
| Người có nhu cầu tiếp cận | Bàn phím, đọc màn hình, chữ lớn, tương phản | Thành phần tự vẽ thiếu ngữ nghĩa, focus khó thấy |

**Luồng quan trọng đầu tiên:** cài đặt có kiểm tra thiết bị; mở và tìm tệp; gõ tiếng Việt; trình duyệt; Office/PDF; Wi‑Fi/Bluetooth; in/scan; cài ứng dụng; cập nhật; sao lưu/khôi phục; hỏi trợ lý NaMi AI. Mọi tuyên bố “có sẵn/chạy được” trong giao diện phải lấy từ trạng thái thực tế và ma trận tương thích, không viết cứng như lời quảng cáo.

## 3. Nguyên tắc thiết kế bắt buộc

- **Nội dung dẫn đường:** hành động chính, trạng thái và kết quả dễ thấy hơn trang trí.
- **Đơn giản theo ngữ cảnh:** mặc định chỉ hiện lựa chọn cần dùng; có “Tùy chọn nâng cao” rõ ràng, không giấu chức năng quan trọng.
- **Quen thuộc nhưng nhất quán:** desktop, thanh tác vụ, menu ngữ cảnh, cửa sổ và phím tắt quen; một hành động có cùng tên và kết quả trên toàn hệ thống.
- **Người dùng nắm quyền:** có hủy, hoàn tác, xem trước, xác nhận tác động lớn; luôn nói rõ khi cần quyền quản trị.
- **Riêng tư theo mặc định:** không dùng hộp thoại gây nhầm để ép đồng ý; AI không tự động đọc tệp, gửi dữ liệu hay đổi cấu hình ngoài quyền đã cấp.
- **Đẹp có mục đích:** chuyển động diễn tả chuyển trạng thái; màu sắc giúp nhận biết hành động; hiệu ứng trong suốt dùng tiết chế và phải tắt được.
- **Thích ứng:** màn hình nhỏ, lớn, nhiều màn hình, HiDPI, bàn phím/chuột/touchpad và hỗ trợ cảm ứng nếu phần cứng có.
- **Tôn trọng tiếng Việt:** từ ngữ phổ thông, câu ngắn, dấu và font đúng, ngày giờ và đơn vị theo lựa chọn vùng Việt Nam.

## 4. Kiến trúc trải nghiệm

### 4.1. Vùng hệ thống

| Vùng | Yêu cầu |
|---|---|
| Màn hình cài đặt | Chọn tiếng Việt; kiểm tra Wi‑Fi, ổ đĩa, nguồn; báo tác động xóa dữ liệu trước xác nhận; giải thích bước tiếp theo |
| Khởi động/đăng nhập | Logo trống đồng có chế độ tĩnh; hiển thị người dùng, ngôn ngữ, bàn phím, mạng, trợ năng; lỗi đăng nhập cụ thể nhưng không lộ bí mật |
| Desktop | Hình nền Việt Nam có quyền sử dụng; icon đủ tương phản; menu mở ứng dụng, thanh tác vụ, khay hệ thống, đồng hồ, thông báo |
| Tìm kiếm | Tìm ứng dụng, tệp, cài đặt, trợ giúp; nêu nguồn từng kết quả; nội dung cá nhân không gửi mạng mặc định |
| Trung tâm điều khiển | Wi‑Fi, Bluetooth, âm thanh, độ sáng, nguồn, VPN, chế độ không làm phiền; đi tới cài đặt chi tiết bằng một thao tác |
| Trình quản lý tệp | Vị trí Tải xuống/Tài liệu/Ảnh/USB rõ; xem trước; tìm kiếm; tên tệp Unicode; thùng rác và hoàn tác |
| Cài đặt | Nhóm theo nhiệm vụ người dùng; tìm kiếm bằng từ đồng nghĩa tiếng Việt; hiển thị thay đổi đang áp dụng và cách hoàn nguyên |
| Cập nhật | Phiên bản, lý do, dung lượng, yêu cầu khởi động lại, tiến trình thật, lịch sử, rollback nếu hệ thống hỗ trợ |
| Trung tâm trợ giúp + AI | Giải thích bằng ngôn ngữ phổ thông, chẩn đoán có quyền, nhật ký có thể xuất và che thông tin nhạy cảm |
| Cửa sổ Giới thiệu | Phiên bản, phần mềm nguồn mở, giấy phép, bản dựng, liên hệ hỗ trợ, thông tin tác giả theo chính sách phát hành |

### 4.2. Mô hình điều hướng

- Desktop có nút mở ứng dụng ở vị trí dễ thấy, hỗ trợ tìm bằng gõ chữ; ứng dụng đang mở có trạng thái rõ.
- Thanh tác vụ hỗ trợ ghim/bỏ ghim, xem trước, chuyển cửa sổ, kéo sắp xếp nếu nền tảng cho phép; không đổi vị trí ngoài ý muốn sau nâng cấp.
- Trình quản lý tệp hỗ trợ nhấp đúp mở, chuột phải, kéo thả, `Ctrl+C/V/X/Z`, `Delete`, `Shift+Delete` với cảnh báo rõ. Có điều hướng bằng breadcrumb và địa chỉ đường dẫn cho người dùng nâng cao.
- Hộp thoại đóng bằng `Esc` khi an toàn; nút mặc định bằng `Enter`; thứ tự Tab theo mắt đọc; hành động nguy hiểm không là nút mặc định.
- Mỗi luồng quan trọng có đường quay lại, thoát hoặc phục hồi. Không khóa người dùng trong wizard nếu chưa đến bước thay đổi không thể hoàn tác.

## 5. Hệ thống nhận diện và design tokens

### 5.1. Nguồn và phân cấp thương hiệu

Biểu tượng trống đồng trong gói nhận diện là **system mark**. Bản đầy đủ dùng từ 48 px; bản giản lược dùng 16–32 px. Tại vùng rất nhỏ, ưu tiên nhận dạng hơn chi tiết. Logo không thay icon của ứng dụng bên thứ ba trong chính gói của họ. Launcher do NaMi sở hữu có thể dùng icon riêng, kèm thông tin đúng về ứng dụng nền.

Màu khởi tạo từ bộ kit: navy `#092D4F`, vàng `#DEA93E`, đỏ `#D64C3E`, teal `#278F8D`, ivory `#FFF9EF`. **Đây là màu nhận diện, không mặc nhiên là màu chữ/nút đạt tương phản.** Tạo semantic tokens `surface`, `surface-raised`, `text-primary`, `text-secondary`, `action-primary`, `success`, `warning`, `danger`, `focus-ring`, `border`; đo lại từng cặp màu trong cả light/dark/high-contrast.

### 5.2. Thang đo đề xuất để prototype

| Token | Khởi tạo | Cách dùng / giới hạn |
|---|---:|---|
| `space` | 4, 8, 12, 16, 24, 32 px | thang nhất quán; khoảng cách nội dung không tùy tiện |
| `radius` | 8, 12, 16 px | control, card, modal; không bo mọi khối giống nhau |
| Body text | 14–16 px tương đương ở 100% | font hỗ trợ tiếng Việt, line-height 1.4–1.6 |
| Caption | tối thiểu 12 px tương đương | chỉ cho chú thích ít quan trọng; không dùng cho lỗi cần hành động |
| Heading | 20–32 px tùy cấp | tối đa 4 cấp rõ ràng trong một màn |
| Desktop control | mục tiêu vùng bấm ít nhất 32×32 px | mở rộng trong chế độ cảm ứng; kiểm tra bằng người dùng |
| Touch control | mục tiêu vùng chạm 44×44 px | điều chỉnh theo mật độ giao diện và bối cảnh |
| Motion | phần lớn 120–240 ms | bắt buộc tôn trọng Reduce Motion; không chặn tương tác |

Những giá trị trên là **quyết định thiết kế đề xuất**, phải kiểm nghiệm với toolkit, font, DPI và người dùng thật. Không biến chúng thành số cố định nếu gây cắt chữ hoặc giảm khả năng tiếp cận.

### 5.3. Chữ, icon và hình nền

- Dùng một họ chữ mở, giấy phép cho phép phân phối trong OS và hiển thị dấu tiếng Việt chuẩn. Cung cấp fallback cho emoji, ký tự toán học, chữ dân tộc khi có nhu cầu.
- Icon chức năng có phong cách nét, tỷ lệ và lưới thống nhất; phân biệt trạng thái ứng dụng, hành động và loại file. Không dùng cùng biểu tượng trống đồng cho mọi ứng dụng vì khó nhận dạng.
- Hình nền mặc định: ảnh Việt Nam có nguồn, quyền sử dụng và metadata; có ảnh sáng/tối; không đặt chữ lên vùng ảnh quá phức tạp. Không tự đưa biểu tượng chủ quyền/bản đồ thiếu kiểm chứng vào ảnh nền mang tính thông tin.
- Có âm thanh hệ thống tinh tế, có tùy chọn tắt; các trạng thái quan trọng luôn có dấu hiệu thị giác và hỗ trợ đọc màn hình.

## 6. Thư viện thành phần giao diện (NaMi UI Kit)

Mọi ứng dụng hệ thống phải dùng cùng component và token. Mỗi thành phần có API cho nhãn tiếng Việt, tooltip, accessible name, state và test.

| Thành phần | Trạng thái tối thiểu | Điều kiện đặc biệt |
|---|---|---|
| Button chính/phụ/nguy hiểm | idle, hover, focus, pressed, busy, disabled | nút nguy hiểm có câu rõ hành động; busy không gây gửi lặp |
| Text field/search/password | empty, focus, valid, error, readonly, disabled | lỗi gắn ngay cạnh trường; mật khẩu có xem/ẩn |
| Checkbox/radio/switch | off/on/mixed, focus, disabled | không dùng switch cho hành động cần xác nhận lâu |
| Combobox/list/autocomplete | mở/đóng, chọn, không kết quả, lỗi | gõ chữ lọc; phím mũi tên/Enter/Esc hoạt động |
| Menu/context menu | mở/đóng, disabled, separator | tên lệnh và phím tắt nhất quán; không ẩn lệnh chỉ vì không hover |
| Table/list/tree | chọn, multi-select, sort, filter, empty, loading | hỗ trợ bàn phím và cột co giãn; không mất vị trí khi refresh |
| Tabs/sidebar/breadcrumb | active, focus, collapsed | thay đổi kích thước cửa sổ không làm biến mất tính năng |
| Dialog/sheet/toast | info, success, warning, error | nút hành động rõ; toast không là nơi duy nhất hiển thị lỗi |
| Progress | determinate, indeterminate, paused, failed | khi biết % phải hiển thị % thật, tệp hoặc bước đang làm |
| File picker/permission | chọn/không chọn, preview, lỗi | phân biệt quyền đọc, ghi, gửi mạng; cho phép hủy |

**Chất liệu:** có thể dùng blur/translucency ở lớp điều hướng khi GPU và tương phản cho phép; nền nội dung ưu tiên vật liệu ổn định. Khi tắt hiệu ứng, thay bằng nền đặc có thứ bậc. Không dùng kính mờ trên mọi card hoặc màn hình lỗi.

## 7. Quy tắc tiếng Việt và nội dung

### 7.1. Thuật ngữ chuẩn hóa

| Khái niệm | Nhãn mặc định | Tránh |
|---|---|---|
| Settings | Cài đặt | Setting, Thiết lập hệ thống máy tính |
| Update | Cập nhật | Upgrade khi chỉ là bản vá |
| Restart | Khởi động lại | Reboot trong UI phổ thông |
| Download | Tải xuống | Download trong nút chính |
| Print | In | Print |
| Scan | Quét tài liệu | Scan khi ngữ cảnh dành cho người mới |
| Bluetooth pairing | Ghép nối | Pair |
| Restore | Khôi phục | Reset nếu thực tế là phục hồi từ bản sao |
| File manager | Tệp | Explorer nếu không có quyền tên đó |

Không dịch tên riêng ứng dụng bên thứ ba nếu làm sai thương hiệu. Các nhãn ứng dụng hệ thống có thể là “NaMi Tệp”, “NaMi Cài đặt”, “NaMi Cập nhật”, “NaMi AI”. Nếu tên thương mại đổi, tên ứng dụng phải đổi qua một lớp localization trung tâm.

### 7.2. Cấu trúc thông báo và lỗi

Mỗi lỗi có **(1) điều gì không thành công, (2) nguyên nhân xác định được hoặc giới hạn chẩn đoán, (3) việc người dùng có thể làm, (4) nút thử lại/trợ giúp, (5) mã lỗi sao chép được**. Không suy đoán nguyên nhân thành sự thật; tách “có thể do” với “đã phát hiện”. Không yêu cầu người dùng chạy lệnh terminal nếu UI có thể tự xử lý an toàn.

Ví dụ:
- “Không thể kết nối Wi‑Fi ‘LopHoc’. Mật khẩu có thể chưa đúng. Nhập lại mật khẩu hoặc kiểm tra bộ phát.” Nút: **Nhập lại**, **Chẩn đoán**.
- “Máy in đã kết nối nhưng chưa in được. Hàng đợi đang tạm dừng.” Nút: **Mở hàng đợi**, **Tiếp tục in**, **Nhờ NaMi AI**.
- “Cập nhật chưa hoàn tất. Hệ thống đã trở về phiên bản trước; tệp cá nhân của bạn không bị thay đổi.” Chỉ dùng câu này khi rollback và kiểm tra dữ liệu thực sự thành công.

Thông báo thành công ngắn, tự biến mất nếu không cần quyết định. Lỗi cần hành động có lịch sử trong trung tâm thông báo, không biến mất trước khi người dùng xử lý. Trợ lý AI không được thay thế thông báo nguồn từ hệ thống.

## 8. Các hành trình sản phẩm bắt buộc

### 8.1. Cài đặt và lần mở đầu

1. Chọn tiếng Việt mặc định theo vùng, cho phép đổi ngôn ngữ/bàn phím.
2. Kiểm tra dung lượng, RAM, kiến trúc CPU, kết nối, nguồn điện, chế độ boot, phân vùng, mã hóa và khả năng cài đặt. Báo mức hỗ trợ thiết bị theo dữ liệu thực, không cam kết “mọi driver”.
3. Trước thao tác có thể xóa dữ liệu: màn hình tổng kết phân vùng cũ/mới, tệp có nguy cơ mất, tùy chọn sao lưu, xác nhận hai bước. Không dùng nút “Tiếp tục” mơ hồ.
4. Trong khi cài: bước hiện tại, tiến trình thật, ước tính chỉ khi có dữ liệu đủ tin cậy; lỗi có lựa chọn quay lại, thử lại, xuất log.
5. Lần khởi động đầu: gõ tiếng Việt, Wi‑Fi, tùy chọn riêng tư, cập nhật, trình duyệt, Office/PDF; cho phép bỏ qua mục không bắt buộc và làm sau.

### 8.2. Làm quen và khám phá

Một tour không quá 5 điểm: mở ứng dụng; tìm tệp; Wi‑Fi/Bluetooth; cập nhật; gọi trợ lý. Tour có thể đóng và mở lại từ Trợ giúp. Không che các điều khiển thiết yếu. Có chế độ “Mới dùng máy tính” với gợi ý rõ hơn nhưng không biến thành giao diện hoàn toàn khác.

### 8.3. Kết nối thiết bị

Wi‑Fi/Bluetooth/máy in/USB/ổ đĩa ngoài dùng cấu trúc chung: phát hiện → chọn thiết bị → xác nhận quyền/mã → kiểm tra hoạt động → kết quả. Hiển thị tên thiết bị, trạng thái, driver/protocol khi cần, hướng dẫn sửa lỗi theo bước. Máy in phải có trang thử, khổ giấy, in hai mặt khi thiết bị hỗ trợ, hàng đợi và hủy việc in. Với thiết bị không hỗ trợ, nói cụ thể tính năng nào thiếu.

### 8.4. Cập nhật và phục hồi

Màn hình Cập nhật có kênh ổn định, bản bảo mật ưu tiên, chế độ tự động có tùy chọn, lịch khởi động lại, mạng giới hạn dữ liệu, dung lượng cần thiết và changelog tiếng Việt. Không để popup giả danh bản cập nhật. Sau lỗi: nói trạng thái hệ thống, rollback có thật hay chưa, cách lấy log, và nút trợ giúp. Khung UI không tự thực hiện ký số/rollback; tích hợp vào dịch vụ cập nhật đã được kiểm thử.

### 8.5. Trợ lý NaMi AI

AI là lớp hỗ trợ tác vụ và chẩn đoán, không là đường duy nhất để dùng OS. Mọi chức năng cốt lõi có UI thủ công. AI trả lời từ trạng thái hệ thống được cấp quyền, nêu nguồn dữ liệu, mức chắc chắn và bước dự kiến. Các mức quyền: **giải thích** → **đề xuất** → **thực hiện sau xác nhận**. Tác vụ nhạy cảm (xóa tệp, đổi quyền, cài gói, gửi log, sửa registry Wine, tắt bảo vệ) cần xem trước phạm vi và xác nhận riêng. Có log hành động và hoàn tác nếu khả thi. Hỗ trợ offline cho chức năng cơ bản khi mô hình cục bộ đáp ứng; nếu không, giao diện nói rõ cần mạng.

## 9. Khả năng tiếp cận và bản địa hóa

- Mục tiêu kiểm thử tối thiểu: WCAG 2.2 AA cho các bề mặt web và các nguyên tắc tương đương trên desktop. Tương phản chữ thông thường ≥4.5:1, chữ lớn ≥3:1, các dấu hiệu giao diện thiết yếu ≥3:1 với nền kề; dùng công cụ đo, không đoán bằng mắt.
- Toàn bộ thao tác chính bằng bàn phím; focus nhìn rõ, thứ tự hợp lý, không kẹt focus; screen reader đọc tên, vai trò, trạng thái và lỗi. Thông báo trạng thái phải được công bố theo khả năng của toolkit.
- Hỗ trợ cỡ chữ lớn, 125/150/200% scaling, high contrast, reduce transparency, reduce motion, điều khiển một tay và bàn phím ảo khi có cảm ứng.
- Tiếng Việt: Unicode chuẩn, dấu câu, chữ hoa, Telex/VNI tùy chọn, phím chuyển bộ gõ rõ; không mất dấu trong đường dẫn tệp. Ngày/tháng, múi giờ, tiền tệ và đơn vị có thể đổi theo vùng. Có tiếng Anh dự phòng cho chẩn đoán kỹ thuật.
- Đánh giá với người dùng lớn tuổi, người chưa dùng Linux và người dùng trình đọc màn hình; ghi số lần nhầm và thời gian hoàn thành tác vụ, không chỉ hỏi họ “thấy đẹp không”.

## 10. Kiến trúc triển khai cho Claude Code

### 10.1. Khảo sát trước khi sửa

Claude phải lập bảng: distro/base Linux, DE/compositor (KDE/GNOME/khác), toolkit (Qt/GTK/web), display manager, bootloader, Plymouth, installer, icon theme, app launcher, update stack, package manager, chính sách Secure Boot, quyền phân phối các ứng dụng gộp. Chỉ sau khi xác định repo thực mới chọn API, đường dẫn và patch. Nếu chưa có repo, chỉ tạo design system và prototype, không tuyên bố đã tích hợp hệ điều hành.

### 10.2. Các lớp mã nguồn

1. **Brand package:** SVG/PNG nguồn, icon theme, font được cấp phép, hình nền được cấp phép, âm thanh, metadata/attribution.
2. **Design tokens:** semantic color, typography, spacing, radii, motion, elevation, density và trạng thái accessibility; có bản light/dark/high-contrast.
3. **Component library:** control, form, dialog, notification, progress, file/device picker; ưu tiên native toolkit và semantic accessibility sẵn có.
4. **Shell integration:** desktop, launcher, taskbar/dock, search, quick settings, notification, lock/login.
5. **System apps:** settings, files, update, devices, help, About, AI; dùng chung component.
6. **Telemetry tùy chọn:** chỉ thu dữ liệu đã đồng ý, tối thiểu hóa và che thông tin cá nhân; lỗi thiết bị có diagnostic bundle người dùng xem trước khi gửi.

### 10.3. Quy tắc thay thế và nâng cấp

- Tách branding khỏi lõi và gói bên thứ ba. Gói `nami-branding` phải có version và manifest; cập nhật nguyên tử nếu nền tảng hỗ trợ, hoặc rollback rõ ràng.
- Không sửa icon gốc Firefox hay nhận diện của LibreOffice để biến thành sản phẩm NaMi. Với launcher do NaMi quản lý, icon/tên giao diện NaMi phải có thông tin nguồn gốc, giấy phép, cập nhật độc lập và attribution đúng.
- Không tự đổi logo firmware/UEFI. Splash chỉ ở phần bootloader/Plymouth/login do bản phân phối kiểm soát. Không hạ bảo mật để thay hình.
- Migration giữ shortcut, vị trí taskbar, lựa chọn dark mode, cỡ chữ, wallpaper, default app và thiết lập accessibility của người dùng. Nếu đổi tên ứng dụng, cung cấp alias hoặc thông báo.

## 11. Mức ưu tiên triển khai

| Giai đoạn | Đầu ra | Điều kiện hoàn thành |
|---|---|---|
| P0 — Khảo sát | audit repo, ma trận màn hình, 10 tác vụ chính, rủi ro giấy phép | có đường dẫn và người phụ trách từng phần |
| P1 — Nền tảng | tokens, font, icon theme, light/dark/high-contrast, component cơ bản | demo bàn phím và screen reader, tương phản đạt mục tiêu |
| P2 — Shell | desktop, launcher, taskbar, search, quick settings, notification | tác vụ mở app/tìm tệp/đổi Wi‑Fi hoàn tất trên máy thử |
| P3 — Hành trình | cài đặt, cập nhật, thiết bị, lỗi, trợ giúp, AI có quyền | thực nghiệm với lỗi thực và rollback thật |
| P4 — Hoàn thiện | motion, wallpaper, âm thanh, microcopy, tối ưu máy yếu | kiểm thử thiết bị, người dùng, QA phát hành |

Không đợi “thiết kế hoàn tất” mới thử người dùng. Prototype và thử sớm ở P1, sau đó thay đổi token/component trước khi mở rộng toàn hệ thống.

## 12. Tiêu chí nghiệm thu có thể kiểm chứng

### 12.1. Tác vụ người dùng

- Ít nhất 5 người chưa dùng Linux và 5 người quen Windows thử 10 tác vụ P0; ghi tỷ lệ hoàn thành không trợ giúp, lỗi, thời gian, số lần hỏi. Mục tiêu ban đầu: ≥80% hoàn thành độc lập cho 8 tác vụ phổ biến; mục tiêu phát hành: ≥90%, sau vòng cải tiến. Đây là **mục tiêu nội bộ đề xuất**, không phải số liệu thị trường.
- Các tác vụ: mở trình duyệt; tìm tệp tải về; gõ tiếng Việt; mở/sửa DOCX; xem PDF; kết nối Wi‑Fi; ghép Bluetooth; in trang thử; cài cập nhật; tìm lời giải cho lỗi thiết bị. Nếu tính năng tương thích chưa có, không đánh dấu UI đạt chỉ vì nút đã được vẽ.

### 12.2. Thiết bị và giao diện

- Thử 1024×600 tối thiểu theo khả năng nền tảng, 1366×768, 1920×1080, 2560×1440; 100/125/150/200% scaling, màn hình thứ hai, chế độ tối, high contrast và reduced motion.
- Không cắt nhãn, không mất nút xác nhận, không che hộp thoại bằng bàn phím ảo. Cửa sổ co hẹp vẫn dùng được hoặc có giới hạn min-size được giải thích.
- Test phần mềm trên máy GPU yếu: tắt blur/animation vẫn đủ chức năng. Đo thời gian mở menu, tìm kiếm và đổi cửa sổ trên phần cứng mục tiêu, đặt baseline từ bản hiện tại trước khi chọn ngưỡng phát hành; không tự đưa con số FPS tùy tiện.

### 12.3. Chất lượng và an toàn

- Automation kiểm tra contrast/token, thiếu accessible name, Tab order, bản dịch thiếu, icon kích thước nhỏ, đường dẫn tài sản bị hỏng.
- Screenshot regression cho màn cài đặt, desktop, settings, printer, Wi‑Fi, update, lỗi, dark/high contrast; có đánh giá thủ công vì ảnh giống nhau không chứng minh hành vi đúng.
- Test cập nhật và rollback bằng VM có snapshot; mất mạng, hết dung lượng, mất nguồn mô phỏng khi phù hợp; giữ dữ liệu người dùng. Test driver và thiết bị thực được ghi theo model/version.
- Không có hành động AI đặc quyền nào chạy khi chưa có xác nhận phù hợp; xem được log, nguồn thông tin và dữ liệu gửi đi.

## 13. Gói bàn giao phải có

1. Source code + patch/PR theo repo thực, không chỉ mockup.
2. Tài liệu `NaMi UI Kit`: token, component, ảnh và trạng thái, quy tắc tiếng Việt, accessibility, icon.
3. Bộ tài sản SVG/PNG + manifest, giấy phép/font/hình nền/âm thanh và attribution.
4. Mapping branding cũ → mới cho installer, boot splash, login, shell, ứng dụng hệ thống và website.
5. Báo cáo kiểm thử, ảnh ở các độ phân giải, danh sách thiết bị, kết quả thử người dùng, lỗi còn mở, cách rollback.
6. Hướng dẫn build, cài thử trên VM, nâng cấp từ bản cũ, gỡ branding và hoàn nguyên.

## 14. Prompt khởi động cho Claude Code

> Đọc toàn bộ Phụ lục 22 này và `NaMi_Brand_DongSon_Full_Kit_v1.zip`. Khảo sát repo trước khi chỉnh sửa. Hãy bắt đầu ở P0: lập báo cáo kiến trúc UI hiện tại, danh sách mọi màn hình/asset/desktop entry cần sửa, bảng ưu tiên 10 tác vụ và các rủi ro về accessibility, giấy phép, driver, update. Sau đó thực hiện P1 bằng patch thực tế: design tokens theo nghĩa sử dụng, component library, icon/theme và màn hình mẫu cài đặt + desktop + thiết bị + cập nhật; thử trên VM. Không sao chép Apple/Windows; giữ thao tác quen và nhận diện trống đồng NaMi. Mỗi thay đổi phải có tiêu chí nghiệm thu, ảnh chứng minh, kết quả test và đường hoàn nguyên. Nếu không có repo hoặc thiếu thành phần, nói chính xác phần nào chưa thể triển khai và cung cấp prototype/module độc lập để tích hợp sau. Không tự tuyên bố mọi ứng dụng Windows hoặc driver đều tương thích chỉ vì giao diện hiển thị chúng.

---

## 15. Cơ sở tham chiếu để đội phát triển tra cứu

Các tài liệu sau là **nguồn nguyên tắc**, không phải giấy phép sao chép giao diện:

- Apple Human Interface Guidelines — Design principles: https://developer.apple.com/design/human-interface-guidelines/design-principles/
- Apple — Designing for macOS: https://developer.apple.com/design/human-interface-guidelines/designing-for-macos
- Apple — Materials (Liquid Glass dùng có chọn lọc): https://developer.apple.com/design/human-interface-guidelines/materials
- Microsoft — Design Windows apps / Fluent: https://learn.microsoft.com/en-us/windows/apps/design/
- GNOME HIG — Accessibility và Adaptive Design: https://developer.gnome.org/hig/guidelines/accessibility.html ; https://developer.gnome.org/hig/guidelines/adaptive.html
- KDE HIG — Desktop, tích hợp và khả năng thích ứng: https://develop.kde.org/hig/
- Material Design 3 — Foundations và design tokens: https://m3.material.io/foundations/
- W3C — WCAG 2.2: https://www.w3.org/TR/WCAG22/

**Phạm vi xác nhận:** các nguồn trên cung cấp nguyên tắc thiết kế; lựa chọn token, chỉ tiêu thử người dùng và lộ trình là đề xuất riêng cho NaMi, cần xác minh trong repo và thử nghiệm thực tế.
