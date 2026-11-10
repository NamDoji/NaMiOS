# Các quyết định kiến trúc ban đầu

Ngày 02/11/2026. `proposed` nghĩa là quyết định cần spike xác nhận; chưa phải kết quả thử nghiệm.

## ADR 001 Chọn Linux và Wine

Trạng thái proposed. Chọn bản phân phối Linux thay vì sửa Windows hoặc tự viết nhân. Dùng Wine để thử tương thích Windows. ReactOS chưa chọn cho pilot nghiệp vụ vì trạng thái alpha. Hệ quả: có nền tảng được duy trì nhưng không được bảo đảm ứng dụng Windows/driver chạy được; đầu tư chỉ tiếp tục theo bằng chứng.

Chấp nhận khi: có fixture chạy thật, mô hình build rõ và inventory quyền phân phối. Thay đổi nếu: app bắt buộc không thể chạy và chủ dự án không chấp nhận phạm vi hẹp hoặc lựa chọn khác.

## ADR 002 Nền Debian 13 amd64

Trạng thái proposed. Chọn Debian stable để giảm thay đổi nền và dùng live-build. Pin snapshot cho build tái tạo, vẫn duy trì security updates cho release mới. Hệ quả: phải xác minh version KDE, Qt, Wine và package support; không lấy vòng đời distro thay cho mọi thành phần.

Spike: cài sạch VM, kiểm package availability, runtime architecture, bộ gõ và installer. Không đưa package version giả vào lockfile.

## ADR 003 Desktop và phiên đồ họa

Trạng thái proposed. Tùy biến KDE, không viết desktop mới. Wayland/XWayland là ứng viên mặc định; kiểm chứng bộ gõ và quyền app. X11 có thể là profile tương thích nhưng cần công bố hạn chế cách ly.

Spike: Telex/VNI trong Qt/GTK/browser/Wine, clipboard, DPI, multi-monitor, print, screen sharing, sandbox visibility và quyền display. Chọn sau khi có bảng kết quả; không gọi bất kỳ phiên nào là an toàn tuyệt đối.

## ADR 004 Hồ sơ khai báo thay script

Trạng thái proposed. Catalog chỉ có recipe allowlist, dependency được xét duyệt, hash và dữ liệu typed. Cấm trường shell và lệnh root tùy ý. Tách manifest, local state và evidence để không biến dữ liệu cài đặt thành chứng nhận.

Spike: semantic validator, invalid properties, injection, path traversal, stale plan và rollback interrupted install.

## ADR 005 Tách chế độ ứng dụng

Trạng thái proposed. native/web/wine/vm/remote có ID hoặc instance riêng. Không tự đổi phần mềm. Nhánh core không phụ thuộc Windows; VM/remote optional ghi rõ license và tài nguyên.

Spike: UI và file association thể hiện đúng mode; mở XLSX trong LibreOffice không cập nhật chứng nhận Excel desktop.

## ADR 006 Ngôn ngữ ứng dụng riêng

Trạng thái proposed. Python 3 CLI/service và PySide6 Qt Quick UI để thuận tiện đóng gói và phát triển. Helper tách nhỏ, least privilege. Không dùng .NET Framework cho công cụ cốt lõi vì yêu cầu chạy Linux độc lập.

Spike: phiên bản từ Debian, giấy phép Qt/PySide, desktop integration, accessibility, startup cost và packaging. Nếu đổi sang stack khác cần ADR với chi phí bảo trì và migration.

## ADR 007 Cập nhật và bảo vệ metadata

Trạng thái proposed. APT cho gói hệ thống; catalog dùng framework metadata ký được duy trì, ưu tiên đánh giá TUF. Chưa viết A/B custom cho v1. Snapshot nếu có phải phục hồi thực; DB và tài liệu backup riêng.

Spike: key separation, expired/replayed metadata, offline policy, revocation, interrupted package transaction, kernel fallback và restore. Không dùng checksum tự xuất bản làm bằng chứng nguồn đáng tin.

## ADR 008 Chứng nhận theo tác vụ

Trạng thái proposed. Chỉ cấp task_verified khi tất cả tác vụ bắt buộc của đúng tuple đã đạt và được QA phê duyệt. Vendor support là thuộc tính độc lập. Bản app mới không kế thừa nhãn tự động.

Spike: app build đổi, catalog revoked, evidence không tồn tại, test skip, phần cứng khác và thao tác ngầm đổi mode đều không tạo false pass.
