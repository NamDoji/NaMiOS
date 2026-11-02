# ADR 0011 — Giao diện quen thuộc và ranh giới sở hữu trí tuệ

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §28 (UI-001..007); test UI-04..08; backlog B039, B043; assumptions A80–A87
- **Bổ sung đặc tả:** SUPERSET §28 (delta vòng 2)

## Bối cảnh

Mục tiêu trải nghiệm: người dùng chuyển từ Windows sang NaMiOS ít phải học lại thao tác cơ bản. Cần giao diện có **bố cục quen thuộc** nhưng với **bộ nhận diện riêng**, không chép tài sản độc quyền của Microsoft, và không mặc định rằng KDE Plasma mặc định đã đáp ứng người dùng Việt Nam.

## Quyết định

1. **Bố cục quen thuộc (UI-001):** desktop có taskbar, nút mở app, tìm kiếm, khay hệ thống, đồng hồ, thông báo, danh sách cửa sổ, ghim/bỏ ghim, khu vực file đang mở.
2. **Ánh xạ phím tắt công bố (UI-001):** Alt+Tab, Win+E, Win+D, Ctrl+C/V, Print Screen, chuột phải, kéo-thả, đổi ngôn ngữ — tất cả có mapping công bố, test khi IME + Wine hoạt động. KHÔNG tùy tiện chiếm phím tắt của app.
3. **Ranh giới IP (FACT, ràng buộc):** KHÔNG chép pixel, biểu tượng, âm thanh hay thương hiệu độc quyền của Microsoft [S01]. Dùng icon/âm thanh/thương hiệu RIÊNG của NaMiOS.
4. **Design tokens riêng (UI-004):** lưới khoảng cách, typography đủ dấu Việt, kích cỡ tối thiểu, tương phản, focus, icon riêng, trạng thái lỗi/loading/empty/offline, chế độ sáng/tối, responsive theo DPI. Kèm tài liệu component/style. "Đẹp và giống Windows" KHÔNG thay tiêu chí khả dụng. KHÔNG tuyên bố có một tiêu chuẩn pháp lý thống nhất cho mọi giao diện app Việt Nam khi chưa chỉ ra chuẩn/đơn vị áp dụng.
5. **File manager (UI-002):** Home/Documents/Downloads/Desktop/ổ ngoài/phân vùng Windows đọc-được; tên tiếng Việt, preview, tìm kiếm, SMB khi được cấp quyền, mount/unmount an toàn, trash/restore, nhãn dung lượng + filesystem. KHÔNG gọi ổ Linux là `C:`; ánh xạ `C:` chỉ hiển thị trong phạm vi Wine khi cần.
6. **Cài đặt + onboarding (UI-003/005):** nhóm Công việc/Thiết bị/Mạng/Cá-nhân-hóa/Tài-khoản/Riêng-tư/Cập-nhật/Khôi-phục, tìm kiếm không dấu; luồng đầu tiên chọn chế độ giao diện/cỡ chữ/bộ gõ Telex-VNI/trình duyệt/phần mềm mở DOCX-XLSX-PDF/máy in mặc định/dữ liệu chuyển từ Windows. KHÔNG đặt LibreOffice tên hiển thị là Word/Excel.
7. **Usability (UI-006):** ≥15 người đại diện (văn phòng/giáo viên/kế toán) × 8 tác vụ định trước trên Windows tham chiếu + NaMiOS; đo tỷ lệ hoàn thành, thời gian, lỗi, số lần cần trợ giúp, phỏng vấn ngắn. **TARGET ≥90%** tác vụ cơ bản hoàn thành không cần hướng dẫn sau 15 phút làm quen. Chưa đạt → sửa luồng + thử lại, KHÔNG tự đổi định nghĩa tác vụ.
8. **Bộ "ứng dụng Việt Nam" (UI-007):** theo sản phẩm × phiên bản; mỗi app test Unicode/font/gõ Việt/ngày-tiền/upload-download/pop-up/in/file association. Nhãn "phù hợp sử dụng tại Việt Nam" CHỈ dựa tập tác vụ đã xác minh, KHÔNG phải chứng nhận cơ quan nhà nước.

## Lý do

- "Quen thuộc" giảm chi phí chuyển đổi, nhưng chép tài sản MS là rủi ro pháp lý [S01]; tách "bố cục" (được) khỏi "asset độc quyền" (không).
- Design tokens riêng đảm bảo đủ dấu Việt + tương phản/accessibility mà KDE mặc định chưa chắc đạt.
- Usability đo được (15/8/90%/15 phút) là ngưỡng, không phải tuyên bố đã đạt.

## Hệ quả

- Bộ design tokens + component + tài liệu là deliverable M3 (B039); shell config/file manager cần desktop session thật.
- Nhãn "phù hợp VN" bị semantic rule gắn với evidence app-mode-version (liên quan ADR 0012 + 0008).
- 15/90%/8-tác-vụ/15-phút đều là TARGET trong assumptions A86; báo cáo phải nêu mẫu số thật.

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Host container **headless, không desktop session** (STATUS: "Desktop session: không có"). Design tokens + tài liệu style + mapping phím tắt dạng bảng/config: **M1 làm được** (text/JSON). Bản dựng shell/file manager/onboarding chạy thật + usability 15 người: **M3 BLOCKED** — cần ISO/desktop thật + người dùng tình nguyện.
- Test UI-04..08 chạy trên desktop alpha/pilot → `not_run` tại host này.

## Spike cần làm + điều kiện chấp nhận

- **Spike S-UI-1:** bộ design tokens riêng (màu/typography dấu Việt/tương phản/focus/trạng thái) + kiểm KHÔNG dùng asset MS; tài liệu mapping phím tắt công bố.
- **Spike S-UI-2:** rà text UI không gọi LibreOffice là Word/Excel, không gọi ổ Linux là `C:` ngoài phạm vi Wine.
- **Spike S-UI-3 (khi có desktop, M3):** UI-04 taskbar/search/shortcuts/Alt-Tab khi IME+Wine; UI-05 copy tên Việt/eject/trash/restore không mất dữ liệu; UI-07 usability 15 người đo tỷ lệ/thời gian/lỗi.
- **Điều kiện chấp nhận:** không asset Microsoft bị chép; design tokens có tài liệu + kiểm accessibility; nhãn "phù hợp VN" chỉ gắn khi có evidence tập tác vụ; không chỗ nào đổi 90%/15 người thành "đã đạt" khi chưa đo; tests UI-04..08 `not_run` cho tới khi có desktop + pilot.
