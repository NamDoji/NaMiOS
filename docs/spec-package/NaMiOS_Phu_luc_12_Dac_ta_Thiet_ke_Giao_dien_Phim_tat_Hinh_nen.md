# NaMiOS — Phụ lục 12: Đặc tả thiết kế giao diện, phím tắt và hình nền Việt Nam

**Ngày:** 07/11/2026. **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam. **Mã yêu cầu:** `UX12-001`–`UX12-048`.  
**Loại:** tài liệu thiết kế độc lập để giao Claude Code, nhóm thiết kế và nhóm kiểm thử. Bổ sung các phụ lục 01–11; không viết lại yêu cầu hệ thống, Wine hay SmartAI.

## 1. Tuyên ngôn thiết kế

NaMiOS phải tạo ấn tượng ngay từ màn hình đầu tiên: **đẹp, tinh tế, đáng tin, rõ ràng bằng tiếng Việt và dễ làm việc thật**. Học ở Apple cách tổ chức thông tin, tính nhất quán, độ hoàn thiện đồ họa, chuyển động tiết chế và cảm giác chăm chút cho từng chi tiết; tạo ngôn ngữ thị giác **nguyên bản** cho NaMiOS. Học ở Windows các thói quen đã ăn sâu: desktop, cửa sổ, thanh ứng dụng, phím tắt, menu ngữ cảnh, quản lý file và đa nhiệm. Thiết kế cho chuột, bàn phím, trackpad, màn hình từ 1366×768 đến HiDPI/đa màn hình, cùng người ít kinh nghiệm công nghệ. Apple nêu rõ môi trường desktop chủ yếu sử dụng bàn phím và thiết bị trỏ [1]; do đó đẹp nhưng khó bấm hoặc khó dùng bàn phím là chưa đạt.

**Không sao chép** icon, cửa sổ, Dock, hình nền, màu sắc thương hiệu, font độc quyền hoặc bố cục của macOS theo kiểu nhận nhầm là sản phẩm Apple. Không đổi hành vi người dùng Windows chỉ để “trông giống Mac”. Mỗi quyết định thiết kế phải được xem trên máy thật với chữ Việt có dấu, không chỉ trong ảnh mockup tiếng Anh.

### 1.1 Nguyên tắc không thương lượng

1. **Việc quan trọng nhìn thấy ngay:** kết nối mạng, bộ gõ, âm lượng, pin, ứng dụng đang mở, thông báo, tệp và cập nhật.
2. **Một hành động, một kết quả rõ:** mở app, in, lưu, gửi và cập nhật có phản hồi và trạng thái thật; không dùng màu xanh để che thất bại.
3. **Nhất quán:** một kiểu nút chính, một ngôn ngữ lỗi, một hệ icon và một bộ phím tắt xuyên toàn bộ hệ thống.
4. **Đẹp ở cấu hình phổ thông:** hiệu ứng có thể tắt, chữ vẫn đọc được, thao tác không giật trên máy pilot.
5. **Tiếng Việt đúng:** dấu, thuật ngữ, quy tắc viết hoa, ngày giờ và tiền tệ đúng bối cảnh; không để chuỗi dài bị cắt mất ý.
6. **Khả năng tiếp cận mặc định:** chỉ báo focus, phóng chữ, tương phản, điều khiển bàn phím và screen reader là tiêu chí phát hành.

## 2. Bản đồ giao diện và cấu trúc thông tin

| Khu vực | Chức năng phải tìm được | Nguyên tắc trình bày |
| --- | --- | --- |
| Màn hình khóa/đăng nhập | Chọn tài khoản, mật khẩu/PIN theo hỗ trợ, mạng, bàn phím Việt/Anh, accessibility, tắt máy | Không lộ tên tài liệu/thông báo nhạy cảm; trạng thái gõ hiện rõ. |
| Desktop | Hình nền, thanh ứng dụng, mở nhanh, cửa sổ, thông báo | Thoáng, ít icon mặc định; vẫn có lối vào File và Thùng rác. |
| Launcher | Tìm app, file trong quyền, cài đặt và tác vụ | Hỗ trợ có dấu/không dấu, không quảng cáo, có nhóm “Thiết yếu”. |
| Thanh ứng dụng | App ghim/đang chạy, chuyển cửa sổ, menu trạng thái | Vị trí dưới mặc định cho người quen Windows; chế độ dock tinh gọn tùy chọn. |
| Settings | Hiển thị, thiết bị, mạng, tài khoản, quyền, sao lưu, cập nhật | Điều hướng trái, nội dung phải; tìm kiếm tiếng Việt và breadcrumb. |
| File Manager | Thư mục quen, preview, tìm, chọn, sao chép, eject | Rõ file/đuôi file, tiến trình và undo; mặc định không ẩn loại file có nguy cơ. |
| Security Center | Trạng thái các lớp bảo vệ, quét, backup, cảnh báo | Chỉ báo bằng cả chữ và màu; một bước tiếp theo dễ hiểu. |
| Update Center | Bản mới, nguồn, tác động, lịch cài, rollback | Phân biệt bản app cài trên máy và dịch vụ web bên thứ ba. |
| SmartAI | Hỏi bằng tiếng Việt, xem kế hoạch, quyền, kết quả | Có thể đóng/tắt; không chiếm chỗ hoặc chặn tác vụ chính. |

## 3. Design system có thông số để triển khai

Các số sau là **token khởi điểm để prototype**, không phải quy chuẩn bất biến. Nhóm thiết kế điều chỉnh bằng thử nghiệm thực tế và ghi phiên bản token. Đơn vị `dp` là kích thước logic ở scale 100%; renderer phải xử lý scaling HiDPI và text scaling. Không dùng ảnh bitmap để vẽ chữ/nút.

### 3.1 Hệ chữ tiếng Việt

| Token | Giá trị khởi điểm | Dùng cho |
| --- | --- | --- |
| `font.ui` | **Be Vietnam Pro** nếu bản phân phối kiểm giấy phép OFL và chất lượng glyph; dự phòng **Noto Sans**, tiếp theo sans hệ thống | Toàn bộ UI tiếng Việt. Be Vietnam Pro có metadata giấy phép OFL trên kho Google Fonts [2]. |
| `font.mono` | Noto Sans Mono hoặc mono được phép | Đường dẫn, mã lỗi, terminal, log. |
| `type.hero` | 28–32 dp / line-height 36–40 / semibold | Tên màn hình chào và hero, không dùng trong form dài. |
| `type.h1` | 24 dp / line-height 32 / semibold | Tiêu đề trang Settings/App Center. |
| `type.h2` | 20 dp / line-height 28 / semibold | Mục chính. |
| `type.h3` | 16–18 dp / line-height 24 / semibold | Nhóm trường. |
| `type.body` | **14–16 dp / line-height 21–24** / regular | Nội dung, nhãn và phần lớn UI; chọn 15/22 cho prototype. |
| `type.secondary` | 13–14 dp / line-height 19–21 | Mô tả phụ, metadata; không dùng cho hướng dẫn quan trọng. |
| `type.caption` | 12–13 dp / line-height 17–19 | Chú thích ngắn, chỉ trên nền tương phản tốt; có tăng cỡ chữ. |
| `type.button` | 14–15 dp / semibold, không ép viết HOA | Nút/toolbar. |

Không dùng SF Pro làm font phân phối mặc định khi chưa có quyền phù hợp; đây là sản phẩm Linux. Tránh font quá mảnh ở màn hình phổ thông và dấu tiếng Việt bị đụng dòng. Dùng số `tabular` cho bảng số tiền/cột tiến trình khi font hỗ trợ; chữ Việt và ký hiệu toán học fallback đúng glyph. Cung cấp mức chữ 100/115/130/150/200%; các mức phải reflow, không cắt nút hay nội dung. WCAG 2.2 yêu cầu khả năng phóng chữ đến 200% mà không mất chức năng theo tiêu chí 1.4.4 [3].

### 3.2 Khoảng cách, độ cong, màu và độ nổi

| Token | Giá trị khởi điểm | Quy tắc |
| --- | --- | --- |
| `space` | 4, 8, 12, 16, 24, 32, 48 dp | 8 dp là nhịp chính; không tùy tiện mỗi màn hình. |
| `radius.small/medium/large` | 6 / 10 / 16 dp | Nút, ô nhập, card/panel; không bo tròn thái quá. |
| `control.height.compact/default/large` | 32 / 40 / 48 dp | Mặc định 40 dp cho chuột/trackpad; vùng click không nhỏ hơn vùng nhìn thấy. |
| `icon.small/default/large` | 16 / 20–24 / 32 dp | Stroke nhất quán; bản filled/outline theo trạng thái. |
| `toolbar.height` | 48–56 dp | Có padding click và tiêu đề. |
| `sidebar.width` | 224–280 dp, co được | Trên 1366×768 không lấy hết nội dung. |
| `dialog.width` | 400–560 dp tùy nội dung | Không mở modal quá rộng; tối ưu chữ Việt dài. |

Bảng màu NaMiOS v1 cần token ngữ nghĩa (`surface`, `surface-raised`, `text-primary`, `text-secondary`, `border`, `focus`, `brand`, `success`, `warning`, `danger`, `link`) cho sáng/tối; nhà thiết kế chọn màu brand sau khi kiểm tương phản, không khóa màu hex chỉ vì ảnh mockup đẹp. Mục tiêu chữ thường tối thiểu **4.5:1**, chữ lớn **3:1** theo WCAG; focus phải nhìn được, trạng thái không phân biệt chỉ bằng màu [4]. Bóng đổ nhẹ cho phân lớp cửa sổ, nền mờ chỉ khi không ảnh hưởng đọc chữ/hiệu năng; chế độ giảm trong suốt.

### 3.3 Thành phần điều khiển và trạng thái

**UX12-001 P0 — Component library duy nhất.** Dùng token và API cho button, link, text field, password field, number/date input, combobox, select, checkbox, radio, switch, slider, tabs, dialog, toast, tooltip, menu, progress, table, tree, file picker. Không để mỗi nhóm tự vẽ bộ điều khiển khác. **Nghiệm thu:** Settings, File, App Center, Security và SmartAI dùng cùng component/version.

**UX12-002 P0 — Mọi trạng thái.** Mỗi component có default/hover/pressed/focus/disabled/loading/error/success, sáng/tối, keyboard và screen reader; snapshot/visual test 200% chữ. **Nghiệm thu:** tab bàn phím thấy focus ở mọi control; disabled có lý do khi cần.

**UX12-003 P0 — Nút.** Primary tối đa một nút mỗi vùng quyết định; secondary, quiet, destructive tách rõ. Nhãn theo động từ cụ thể: “Cài đặt”, “In trang thử”, “Khôi phục bản trước”; nút xóa/cài driver đặc quyền có confirmation. Minimum target 40×40 dp ở UI mặc định, khoảng cách tránh bấm nhầm. **Nghiệm thu:** 10 tác vụ thử không nhầm “Xóa” với “Hủy”; chạy bàn phím bằng Enter/Space theo loại control.

**UX12-004 P0 — Link.** Gạch chân hoặc phân biệt rõ ngoài màu; URL bên thứ ba có nhãn/mở browser chính thức, hover/focus, không dùng chữ “tại đây”. **Nghiệm thu:** người dùng biết link đưa đến vendor; screen reader đọc mục đích link.

**UX12-005 P0 — Combo box và select.** Tìm theo có dấu/không dấu cho danh sách dài (máy in, mạng, thiết bị); Enter chọn, Esc đóng, mũi tên di chuyển, không mất giá trị khi click ra ngoài. Trên danh sách ngắn dùng select đơn giản. **Nghiệm thu:** 200 máy in không khiến dialog đứng; tên trùng có model/địa chỉ phân biệt.

**UX12-006 P0 — Checkbox, radio, switch.** Checkbox cho nhiều lựa chọn, radio cho một trong nhiều, switch cho trạng thái bật/tắt tác động tức thì; mô tả hệ quả bằng chữ. Vùng nhãn cũng bấm được, trạng thái mixed nếu áp dụng. **Nghiệm thu:** “Tự động cập nhật” hiển thị rõ trạng thái và quyền, screen reader đọc selected/checked.

**UX12-007 P0 — Text input.** Nhãn luôn hiện, không lấy placeholder làm nhãn; trợ giúp nằm gần trường, lỗi chỉ vị trí và cách sửa, ô password không log ký tự, auto-complete chỉ khi phù hợp. **Nghiệm thu:** IME tiếng Việt trong ô tìm kiếm/cấu hình không mất dấu; lỗi không xóa dữ liệu đã nhập.

**UX12-008 P0 — Dialog và thông báo.** Modal chỉ cho quyết định cần chặn tác vụ, Esc đóng khi an toàn; hành động nguy hiểm không được mặc định bằng Enter khi chưa cân nhắc. Toast có lịch sử và nội dung dễ đọc, không mất ngay trước khi người dùng kịp xem. **Nghiệm thu:** người dùng hiểu tác động trước khi xóa tệp/cập nhật firmware, không phải đọc log.

**UX12-009 P0 — Bảng, danh sách và cây.** Sort/filter/search, chọn nhiều, điều hướng bằng bàn phím, nhãn cột rõ, vùng dòng ≥40 dp mặc định; tệp và ứng dụng dài được ellipsis kèm full name khi focus/hover. **Nghiệm thu:** bảng 10.000 tệp vẫn cuộn và tìm mượt trên cấu hình pilot.

**UX12-010 P1 — Menu ngữ cảnh.** Click phải/Shift+F10 đưa hành động đúng với tệp/app/desktop; hành động thường gặp ở đầu, phá hủy ở cuối, không nhét 20 submenu. **Nghiệm thu:** người quen Windows tìm “Đổi tên”, “Sao chép”, “Thuộc tính” và “Gỡ ứng dụng” đúng chỗ.

**UX12-011 P0 — Focus và chỉ dẫn.** Focus ring tương phản cao, thứ tự Tab theo trực quan, không trap focus ngoài modal, tooltip không che nút, menu phím tắt hiện bên cạnh action. **Nghiệm thu:** hoàn thành 12 luồng chính chỉ bằng bàn phím.

**UX12-012 P1 — Responsive desktop.** 1366×768, 1920×1080, 2560×1440 2× scale, nhiều màn hình, xoay dọc: cửa sổ nhớ kích thước hợp lý, không để nút quan trọng dưới màn hình. **Nghiệm thu:** mở Settings/Update Center ở 1366×768 với chữ 150% vẫn thao tác được.

### 3.4 Shell, cửa sổ và luồng quen thuộc

**UX12-013 P0 — Desktop và thanh tác vụ.** Thanh dưới mặc định, nút Launcher dễ nhận, ghim app, app đang mở, nhóm cửa sổ, khay mạng/âm thanh/pin/IME/đồng hồ; auto-hide là tùy chọn. Dock tinh gọn là theme/chế độ, không bỏ khả năng xem cửa sổ đang mở. **Nghiệm thu:** mở 8 cửa sổ rồi tìm đúng cửa sổ đang in trong ≤3 thao tác thử nghiệm.

**UX12-014 P0 — Cửa sổ nhất quán.** Nút thu nhỏ/phóng to/đóng rõ, có trạng thái unsaved, resize/drag/snap, kéo giữa màn hình; viền và title bar một hệ thống. Không sao chép vị trí/biểu tượng traffic-light của macOS nếu gây nhầm. **Nghiệm thu:** chuyển đổi cửa sổ khi có app Wine và Linux, không mất focus/IME.

**UX12-015 P0 — File Manager quen tay.** Desktop/Home/Downloads/Documents/Pictures/USB/Network, thanh đường dẫn, preview có thể tắt, chọn nhiều, drag/drop, sort, đổi tên, lịch sử Back/Forward, Thùng rác và “Rút an toàn”. **Nghiệm thu:** người từ Windows tự hoàn thành copy file USB và in PDF mà không hướng dẫn terminal.

**UX12-016 P1 — Empty/loading/error states.** Trang chưa có tệp, chưa ghép máy in, mất mạng hoặc app lỗi đều có một câu giải thích và nút hành động; không để bảng trắng hoặc spinner vô hạn. **Nghiệm thu:** 8 tình huống ngoại lệ có ảnh và nội dung tiếng Việt đã duyệt.

**UX12-017 P1 — Chuyển động.** Mục đích là chỉ quan hệ trạng thái/cửa sổ; khoảng 120–250 ms là giả thuyết ban đầu, đo trên máy yếu; reduce motion và tắt blur/animation có tác dụng ngay. **Nghiệm thu:** không chậm phản hồi click hay làm rối người nhạy cảm chuyển động.

**UX12-018 P0 — Giao diện SmartAI.** Điểm vào nhỏ, có thể gọi bằng phím tắt tùy chọn; hiển thị “AI định làm gì, cần quyền nào, đã làm được gì”, không che desktop hoặc tự bật hội thoại mỗi lần cắm USB. **Nghiệm thu:** tắt SmartAI không đổi UI gõ, in, mở file hoặc cập nhật.

### 3.5 Bộ phím tắt: giữ thói quen Windows, giải quyết xung đột Linux

Phím “Super” là phím mang biểu tượng hệ điều hành trên phần lớn bàn phím PC; UI hiển thị biểu tượng phím thực tế và gọi dễ hiểu là “phím hệ thống”. Không vô điều kiện thay mọi tổ hợp của desktop environment: kiểm shortcut của Wayland/compositor, app Wine, IME, browser và accessibility; một registry có chủ sở hữu để xử lý xung đột.

| Thao tác | Mặc định đề xuất | Mức | Ghi chú kiểm thử |
| --- | --- | --- | --- |
| Mở Launcher/tìm | Super | P0 | Ấn một lần; search không dấu. |
| File Manager | Super+E | P0 | Thói quen Windows [5]. |
| Settings | Super+I | P1 | Không giành phím khi app đang gõ tổ hợp. |
| Khóa máy | Super+L | P0 | Khóa ngay, che notification riêng tư. |
| Chuyển cửa sổ | Alt+Tab / Alt+Shift+Tab | P0 | Hiện app/window preview. |
| Đóng cửa sổ | Alt+F4 | P0 | Cảnh báo khi file chưa lưu. |
| Copy/cut/paste | Ctrl+C/X/V | P0 | File, text, app Linux/Wine, clipboard privacy. |
| Chọn tất cả/undo/redo | Ctrl+A/Z/Y hoặc Ctrl+Shift+Z | P0 | Chấp nhận redo theo app, hiện trong menu, tránh sai dữ liệu. |
| Tìm trong ứng dụng | Ctrl+F | P0 | File, browser, Office; IME không xung đột. |
| Lưu/In/Mở | Ctrl+S/P/O | P0 | Ứng dụng tài liệu; dialog đúng tên máy in. |
| Đổi tên file | F2 | P0 | Chỉ chọn phần tên, giữ đuôi. |
| Xóa/Thùng rác | Delete; Shift+Delete có cảnh báo | P0 | Không xóa vĩnh viễn bằng một phím nhầm. |
| Menu ngữ cảnh | Shift+F10 / phím Menu | P0 | Có focus cho bàn phím. |
| Quản lý tác vụ | Ctrl+Shift+Esc | P1 | App không phản hồi, kill có xác nhận. |
| Chụp màn hình | Print Screen, Super+Shift+S | P1 | Chọn vùng, che bí mật theo người dùng. |
| Đổi ngôn ngữ/IME | Ctrl+Space hoặc tổ hợp mặc định đã thử với nhóm Việt | P0 | Người dùng đổi dễ; không phá Ctrl+Space trong IDE. |
| SmartAI | Super+Space hoặc shortcut khác **sau** audit xung đột | P1 | Không chiếm phím của IME/desktop. |
| Xem bảng phím tắt | Super+? hoặc Launcher “Phím tắt” | P1 | Bảng tra cứu/search và nút tùy chỉnh. |

**UX12-019 P0 — Registry phím tắt.** Mỗi shortcut có action ID, scope (system/window/app), ưu tiên, tình trạng conflict, khả năng đổi, hiển thị trong menu/help. **Nghiệm thu:** CI phát hiện hai action hệ thống trùng tổ hợp, không phát hành nếu P0 conflict.

**UX12-020 P0 — Bộ phím tắt cơ bản.** Thực hiện bảng P0 với cùng hành vi ở shell/file manager; app Windows qua Wine và browser chỉ cam kết sau test. **Nghiệm thu:** 30 ca thao tác bằng keyboard, không lặp ký tự tiếng Việt hoặc kẹt focus.

**UX12-021 P0 — Tùy chỉnh và reset.** Người dùng xem, đổi, xuất/nhập thiết lập phím tắt, reset về mặc định; cảnh báo xung đột, phím được ứng dụng chiếm và phím accessibility. **Nghiệm thu:** đổi Super+E không làm mất đường mở File Manager.

**UX12-022 P1 — Hướng dẫn ngay trong menu.** Menu hiển thị shortcut nhất quán; bảng tổng quan có nhóm cửa sổ, file, văn bản, bảo mật, SmartAI; lần đầu có mẹo ngắn có thể tắt. **Nghiệm thu:** user thử lại được 5 thao tác sau một lần xem hướng dẫn.

**UX12-023 P0 — Thử với nhiều bố cục bàn phím.** US/Vietnamese, bàn phím laptop thiếu phím PrtSc, bàn phím rời và remote desktop; tổ hợp theo physical key hoặc ký tự phải được định nghĩa rõ. **Nghiệm thu:** thiết bị pilot không có phím chức năng vẫn có đường UI tương đương.

**UX12-024 P0 — Phím tắt không vượt quyền.** Shortcut không tự chạy lệnh root, gửi tệp hoặc bỏ bảo vệ; tác vụ nguy hiểm vẫn cần xác nhận và audit. **Nghiệm thu:** phím chụp/khóa/AI không rò nội dung màn hình khóa.

### 3.6 Hình nền Việt Nam: bộ sưu tập đẹp, có quyền và đúng địa danh

NaMiOS cần bộ sưu tập **“Việt Nam qua từng vùng đất”** được biên tập như một sản phẩm ảnh, không lấy ngẫu nhiên ảnh trên mạng. Các nhóm gợi ý: núi và ruộng bậc thang, thác và rừng, biển/đảo, sông hồ, phố cổ/đô thị, di sản văn hóa, di tích lịch sử, sinh hoạt và nghề truyền thống. Hình ảnh giữ tính xác thực địa điểm; thông tin địa danh, tác giả, thời điểm/nguồn, giấy phép và giới hạn sử dụng hiển thị trong “Thông tin hình nền”. Không mặc định dùng ảnh vị trí nhạy cảm hoặc hình ảnh người có thể nhận diện khi thiếu quyền.

**UX12-025 P0 — Tuyển chọn biên tập.** Đợt đầu chọn 12–18 ảnh đa dạng Bắc/Trung/Nam, không lặp phong cảnh cùng một vùng; hội đồng ít nhất thiết kế + biên tập Việt Nam + pháp lý tư liệu. **Nghiệm thu:** mỗi ảnh có phiếu chọn và lý do (chủ thể, màu, khoảng trống đặt icon, độ sắc, ý nghĩa).

**UX12-026 P0 — Bản quyền và nguồn gốc.** Ưu tiên ảnh đặt chụp/được cấp phép rõ bằng văn bản hoặc nguồn mở cho phép phân phối/sửa nếu chỉnh màu/crop; lưu tác giả, giấy phép, cách ghi công, nguồn gốc file, quyền chân dung/địa điểm khi cần. Không dùng ảnh tìm kiếm Google hay watermark đã xóa. **Nghiệm thu:** release manifest cho từng ảnh có file gốc, license, bằng chứng quyền, hash và credit.

**UX12-027 P0 — Tiêu chuẩn ảnh.** Master chất lượng cao, bản xuất 16:9, 16:10, ultrawide/portrait khi có, light/dark/blur preview; không kéo giãn mặt người/công trình, smart crop có vùng an toàn đặt icon. Mốc 4K ngang là mục tiêu cho master phổ thông, không upscale ảnh nhỏ để giả chi tiết. **Nghiệm thu:** 1366×768, 1080p, 4K/HiDPI và hai màn hình đều sắc nét/crop đúng.

**UX12-028 P0 — Chữ luôn đọc được.** Hình nền tự điều chỉnh overlay/contrast cho nhãn icon và thanh ứng dụng; chế độ tăng tương phản có nền đơn sắc. Không khiến người dùng phải đổi ảnh để đọc tên file. **Nghiệm thu:** 18 hình nền pass độ đọc icon/trạng thái sáng/tối, đo tương phản và thử mắt người.

**UX12-029 P1 — Thay đổi có kiểm soát.** Cho chọn cố định/đổi theo ngày/giờ, album người dùng, chọn ảnh theo màn hình; tải thêm bộ sưu tập **opt-in**, hiện dung lượng và nguồn. Không tự dùng vị trí GPS hay đẩy ảnh cá nhân lên cloud. **Nghiệm thu:** offline vẫn có sẵn bộ ảnh; đổi tự động không làm mất tập trung trong cuộc họp.

**UX12-030 P1 — Hình khóa và đăng nhập.** Chọn hình/ảnh trong bộ đã cấp phép với blur/tối đủ để ô mật khẩu rõ; không hiện thông tin nhạy cảm hoặc quảng cáo trên màn hình khóa. **Nghiệm thu:** cả màn hình laptop tối và ngoài sáng đọc được ô nhập và trạng thái IME.

**UX12-031 P1 — Bản sắc Việt không khuôn mẫu.** Di sản và biển đảo ghi tên chính xác theo metadata đã xác minh, tránh gắn nhãn sai địa điểm, tô vẽ lịch sử hoặc dùng hình AI như ảnh tư liệu. Ảnh được tạo/sửa bằng AI phải ghi rõ bản chất và quyền sử dụng nếu phát hành. **Nghiệm thu:** biên tập viên Việt Nam duyệt caption, giấy phép và nội dung trước release.

**UX12-032 P1 — Bộ ảnh theo dịp.** Có thể tạo bộ Tết, mùa lúa, mùa biển và ngày di sản sau này, nhưng mặc định không tải nội dung mới khi chưa chọn; không thay ảnh đột ngột trong giờ làm. **Nghiệm thu:** đổi bộ không tải lại toàn bộ nền khi đã có cache và có rollback.

### 3.7 Tính dễ dùng, an toàn và kiểm chứng

**UX12-033 P0 — Nghiên cứu người Việt.** Thử ít nhất 5 người mỗi nhóm khởi đầu: học sinh/giáo viên, nhân viên văn phòng, người lớn tuổi/ít kỹ thuật; đo tác vụ và lỗi, không chỉ hỏi “có đẹp không”. **Nghiệm thu:** bảng vấn đề, mức nghiêm trọng và bản sửa sau mỗi vòng.

**UX12-034 P0 — Bộ 12 tác vụ thử.** Mở Zalo, gõ chữ có dấu, đổi Wi‑Fi, tìm/in file, kết nối máy in, tìm phần mềm, cập nhật, khôi phục, phóng chữ, bật tương phản, quản quyền site, nhờ SmartAI giải thích lỗi. **Nghiệm thu:** log thời gian, số lần bấm sai, mức trợ giúp, tỷ lệ hoàn thành theo persona.

**UX12-035 P0 — Accessibility.** Đặt mục tiêu WCAG 2.2 AA cho UI chính và chuẩn accessibility desktop phù hợp: keyboard, focus, screen reader, tên điều khiển, contrast, zoom/reflow, giảm chuyển động, tránh flash. **Nghiệm thu:** test tự động + thủ công với screen reader và 200% text; lỗi P0 chặn release.

**UX12-036 P0 — Tốc độ cảm nhận.** UI phản hồi tức thì với loading state khi chờ I/O; không để AI, quét virus hoặc wallpaper làm chậm gõ, mở Launcher, kéo cửa sổ. Định ngưỡng bằng máy pilot và ghi cấu hình; không hứa tốc độ chỉ từ mockup. **Nghiệm thu:** benchmark cold/warm và p95 theo phần cứng; regression đáng kể chặn ring stable.

**UX12-037 P0 — Ngôn ngữ giao diện.** Tạo `glossary.vi.json` có thuật ngữ phổ thông và chuyên ngành; thống nhất “Tệp”, “Thư mục”, “Ứng dụng”, “Máy in”, “Cập nhật”, “Khôi phục”, “Bộ gõ”, giải thích “driver” trong trợ giúp. **Nghiệm thu:** 100% màn hình P0, thông báo lỗi và hộp xác nhận đã review tiếng Việt.

**UX12-038 P1 — Định dạng và văn phong.** Ngày giờ Việt Nam, thông báo súc tích, không viết HOA toàn câu, tránh tiếng Anh kỹ thuật khi có từ phổ thông; mã lỗi cố định cho IT. **Nghiệm thu:** 50 chuỗi dài nhất hiển thị đầy đủ ở 1366×768/150% text.

**UX12-039 P0 — Chân thực trạng thái.** App web có nhãn “dịch vụ web”, Office native có version, app Wine có tình trạng chứng nhận; màu đẹp không đánh lừa về việc “đã gửi”, “đã ký” hay “máy an toàn”. **Nghiệm thu:** reviewer nghiệp vụ đọc UI và phân biệt được chờ/đang làm/hoàn tất/thất bại.

**UX12-040 P1 — Mẫu lỗi thống nhất.** Error title tiếng Việt, nguyên nhân biết được, hành động an toàn, mã, xem chi tiết/hỗ trợ; mọi lỗi mạng/USB/Office/update áp dụng cùng cấu trúc. **Nghiệm thu:** 20 lỗi test có nhãn và đường thoát, không chỉ “Something went wrong”.

**UX12-041 P0 — Quyền riêng tư của ảnh và giao diện.** Không gửi ảnh nền cá nhân, ảnh chụp màn hình hay nội dung cửa sổ cho SmartAI nếu chưa cho phép; preview trong task switcher/màn hình khóa che nội dung nhạy cảm theo policy. **Nghiệm thu:** tài khoản B không xem preview tài liệu tài khoản A.

**UX12-042 P1 — Tùy biến không phá nhất quán.** Chọn sáng/tối/theo giờ, cỡ chữ, màu nhấn trong bảng an toàn, vị trí dock/taskbar, hình nền và độ mờ; luôn có nút “Khôi phục giao diện mặc định”. **Nghiệm thu:** đổi theme không đổi ý nghĩa nút, focus hay shortcut.

**UX12-043 P0 — Quy trình thiết kế → mã nguồn.** Figma hoặc công cụ design tương đương có library versioned; token xuất JSON/CSS/Qt/GTK theo stack chọn, icon SVG nguồn, ảnh wallpaper asset pipeline. Mã UI dùng token, không hardcode ở từng màn hình. **Nghiệm thu:** sửa màu nhấn hoặc font trong design token cập nhật được 5 màn hình mẫu với ít sửa tay.

**UX12-044 P0 — Visual regression.** Chụp/snapshot UI trong sáng/tối, vi/en, 100/150/200% chữ, low/high DPI; có threshold và người duyệt cho khác biệt do rendering. **Nghiệm thu:** thay font làm tràn button/cắt dấu được phát hiện trước release.

**UX12-045 P1 — Phản hồi người dùng.** Nút “Góp ý về giao diện” cho ảnh chụp tùy chọn, người dùng xem/che nội dung trước gửi; lưu lỗi đã sửa và kết quả test. **Nghiệm thu:** không tự tải screenshot hay văn bản riêng tư.

**UX12-046 P0 — Tài sản thương hiệu.** Logo NaMiOS, icon ứng dụng hệ thống, màn hình boot, onboarding, hình nền và âm thanh có hướng dẫn và giấy phép; icon mạng xã hội dùng theo quyền từng vendor, không trộn thành logo NaMiOS. **Nghiệm thu:** asset manifest có nguồn, tác giả, license, hash và phiên bản.

**UX12-047 P1 — Giao diện trên máy cũ.** Theme nhẹ dùng CPU/GPU vừa phải; đường fallback khi compositor/blur lỗi, không buộc GPU hiện đại mới đọc được UI. **Nghiệm thu:** máy pilot thấp nhất vẫn đăng nhập, gõ, tìm file, mở browser và in ổn định.

**UX12-048 P0 — Hội đồng nghiệm thu.** Một nhà thiết kế, một kỹ sư desktop, một QA accessibility, một biên tập tiếng Việt và người dùng pilot duyệt trước khi “đẹp và dễ dùng” được công bố; ảnh minh họa không thay chứng cứ thao tác. **Nghiệm thu:** checklist có người ký, vấn đề mở, độ ưu tiên và build test.

## 4. Đầu ra Claude Code phải bàn giao

1. `design/NaMiOS-Design-System.md`: nguyên tắc, typography, màu ngữ nghĩa, spacing, component anatomy, states, accessibility và quy tắc tiếng Việt.
2. `design/tokens.json` và bản tương thích framework UI đã chọn; `design/components/` chứa button, link, field, combobox, checkbox, radio, dialog, table, toast; Storybook hoặc preview tương đương cho tất cả trạng thái.
3. `design/keyboard-shortcuts.json`: action/scope/default/conflict/override, giao diện tra cứu và tự đổi phím; test Linux/Wine/IME/browser.
4. `design/wallpaper-manifest.json`: mỗi ảnh có tiêu đề/địa điểm/tác giả/nguồn/quyền/hash/biến thể/credit; 12–18 ảnh chỉ được đóng gói **sau khi có quyền sử dụng**. Trong prototype dùng ảnh có license hợp lệ hoặc placeholder rõ ràng.
5. Mockup **không chỉ mockup**: prototype desktop, Launcher, Settings, File Manager, Update Center, Security Center, SmartAI, đăng nhập; light/dark, 1366×768/1080p/HiDPI và chữ Việt thật.
6. Báo cáo `design/ux-test-report.md` và `design/accessibility-audit.md`: tác vụ, người thử, build, tỉ lệ hoàn thành, lỗi, ảnh/clip có consent, thay đổi sau thử; CI visual regression.

**Cổng phát hành giao diện v1:** tất cả `UX12 P0` có code, bài test và màn hình chạy thật; không có phím tắt hệ thống trùng nhau, không mất dấu tiếng Việt, không có ảnh thiếu quyền, không có tác vụ P0 không điều khiển được bằng bàn phím, không có thông báo an toàn sai sự thật.

## 5. Nguồn đối chiếu (truy cập 07/11/2026)

[1] Apple Human Interface Guidelines, Designing for macOS: https://developer.apple.com/design/human-interface-guidelines/designing-for-macos  
[2] Google Fonts, metadata Be Vietnam Pro và OFL: https://github.com/google/fonts/blob/main/ofl/bevietnampro/METADATA.pb  
[3] W3C, WCAG 2.2 Understanding Resize Text: https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html  
[4] W3C, WCAG 2.2: https://www.w3.org/TR/WCAG22/  
[5] Microsoft Support, Keyboard shortcuts in Windows: https://support.microsoft.com/en-us/windows/keyboard-shortcuts-in-windows-dcc61a57-8ff0-cffe-9796-cb9706c75eec

Các thông số và nguồn là cơ sở thiết kế ban đầu; ảnh, font, shortcut và khả năng tiếp cận phải được thử trên bản NaMiOS thật trước phát hành. Người dùng cần cảm nhận sự chuyên nghiệp ở **toàn bộ hành trình**, không chỉ ở hình nền hoặc màn hình chào.
