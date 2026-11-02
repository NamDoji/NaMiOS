# Bảng giả định nền tảng — FACT / DESIGN / TARGET / UNKNOWN

**Ngày tra cứu:** 02/11/2026 (Asia/Ho_Chi_Minh). **Nguồn FACT:** §24 đặc tả (S01–S13) + inventory M0.

Quy ước (theo §2 đặc tả):
- **FACT** — thông tin nền có nguồn chính thức. Nguồn không xác nhận tương thích thực; tính tương thích phải do test dự án chứng minh.
- **DESIGN** — quyết định đề xuất của dự án (cần spike xác nhận, xem ADR).
- **TARGET** — chỉ tiêu cần đo; **không** phải kết quả benchmark hay cam kết đã đạt.
- **UNKNOWN** — chưa có bằng chứng; phải đóng băng là giả định cho tới khi xác minh.

> Cảnh báo chung: mọi con số hiệu năng và quy mô (boot, RAM, p95, dung lượng) trong đặc tả là **TARGET**, không phải số đo. Phiên bản phụ thuộc phải kiểm tra lại lúc triển khai, ghi vào lockfile/SBOM; không dùng "latest" trong đầu ra phát hành.

---

## 1. Nền tảng hệ điều hành & build

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A01 | FACT | Debian 13 "trixie" là bản phát hành có vòng đời upstream được công bố | [S09](https://www.debian.org/releases/trixie/), 02/11/2026 | Vòng đời upstream ≠ cam kết bảo trì của đội NaMiOS; theo dõi riêng từng gói |
| A02 | DESIGN | Chọn Debian 13 trixie amd64 làm nền (ADR 0002) | §5.1, ADR 0002 | Ghi point release, snapshot nguồn gói, kernel, package list thực tế |
| A03 | FACT | Debian live-build cho phép tự động hóa cấu hình ảnh Live | [S10](https://live-team.pages.debian.net/live-manual/html/live-manual.en.html), 02/11/2026 | Build log + hướng dẫn tái tạo trên môi trường sạch |
| A04 | DESIGN | Dùng live-build để tạo ISO; Calamares làm installer nếu spike đạt | §5.1, ADR 0002 | Nếu Calamares không đạt → đường cài Debian được kiểm thử, ghi ADR thay đổi |
| A05 | FACT | Host build hiện tại là Debian 12 (bookworm), KHÔNG phải Debian 13 | inventory M0 | — |
| A06 | FACT | Host hiện tại thiếu wine/live-build/debootstrap/xorriso/qemu; `/dev/kvm` vắng; CPU không có vmx/svm | inventory M0 | M2/M3/M4 BLOCKED tại đây; cần build host có nested-virt + bộ cài hợp lệ |
| A07 | TARGET | ISO tái tạo được cùng bộ package; bit-for-bit reproducible là mục tiêu sau | §BUILD-004 | Nếu timestamps/mirror/tooling còn sai khác → ghi rõ, không gọi là reproducible byte-for-byte |
| A08 | UNKNOWN | Point release Debian 13, kernel, package snapshot phát hành cụ thể | chưa chốt | Pin ở M3 trong build manifest; không pin snapshot cũ vô thời hạn |

## 2. Desktop & phiên đồ họa

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A09 | DESIGN | Tùy biến KDE Plasma + Dolphin bằng gói Debian; không viết lại desktop (ADR 0003) | §5.1, ADR 0003 | Dùng gói từ nguồn được duy trì |
| A10 | DESIGN | Wayland là ứng viên mặc định; Wine qua XWayland khi cần; X11 chỉ là profile tương thích gắn nhãn hạn chế | §5.1, ADR 0003 | Quyết định cuối sau ma trận IME/clipboard/màn hình/sandbox |
| A11 | UNKNOWN | Phiên bản KDE Plasma/Qt thực có trong snapshot Debian 13 | chưa tra snapshot | Kiểm tra lúc build; không đưa version giả vào lockfile |
| A12 | FACT | XWayland/X11 có rủi ro quan sát/điều khiển phiên (một client X11 có thể theo dõi input/cửa sổ khác) | §SEC-004 (mô hình X11 cổ điển) | Nếu nới policy để tương thích → hạ nhãn cách ly, ghi ngoại lệ |

## 3. Tiếng Việt & bộ gõ

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A13 | DESIGN | Locale vi_VN.UTF-8, TZ Asia/Ho_Chi_Minh, UTF-8 toàn tuyến (cho đổi được) | §5.1, §VN-001 | — |
| A14 | DESIGN | Fcitx5 + bộ gõ tiếng Việt phù hợp, hỗ trợ Telex và VNI | §5.1 | Kiểm tên gói/engine thực trong snapshot; test Telex/VNI qua Qt/GTK/browser/Wine |
| A15 | UNKNOWN | Engine Telex/VNI cụ thể hoạt động đúng trong Wine 32/64-bit | chưa test | VN-01 test matrix; không log nội dung gõ |
| A16 | DESIGN | Font có quyền phân phối, đủ glyph tiếng Việt; không chép font Microsoft | §VN-005, §LIC-004 | So bố cục với font đúng quyền trên môi trường đối chiếu |

## 4. Ứng dụng miễn phí & trình duyệt

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A17 | DESIGN | LibreOffice từ repo duy trì làm office miễn phí (phần mềm thay thế, KHÔNG phải Word/Excel) | §5.1, §APP-OFF-006 | Không tính LibreOffice là "đạt" yêu cầu Microsoft desktop |
| A18 | DESIGN | Firefox ESR mặc định; trình duyệt khác thêm có điều kiện, không tắt sandbox | §5.1 | — |

## 5. Wine & lớp tương thích Windows

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A19 | FACT | Wine là lớp tương thích, KHÔNG chạy một bản Windows bên dưới | [S02](https://www.winehq.org/about/), 02/11/2026 | Tương thích trên Wine ≠ vendor hỗ trợ chính thức Linux |
| A20 | DESIGN | Một Wine runner được khóa phiên bản (pin), hồ sơ riêng từng app; không trộn nguồn gói tùy tiện | §5.1, ADR 0001 | Chọn gói Debian hoặc WineHQ tương thích + xác minh |
| A21 | DESIGN | Mỗi user/app/major/profile có prefix riêng; không chạy wine/installer bằng root | §COMP-001, ADR 0001 | — |
| A22 | FACT | Prefix Wine KHÔNG phải ranh giới bảo mật; chạy app Windows = thực thi mã không tin cậy | §COMP-008 | Gỡ drive Z chỉ giảm tiếp xúc, không đủ sandbox |
| A23 | UNKNOWN | Runner hỗ trợ new WoW64 hay cần gói i386 (multiarch) cho app 32-bit | chưa probe | COMP-002 capability probe; ghi chiến lược + kết quả vào hồ sơ |
| A24 | UNKNOWN | Một build Office/Zalo/MISA cụ thể có chạy đạt tác vụ trên Wine hay không | chưa test | M2/M4 evidence; mặc định `untested`/`blocked` |
| A25 | FACT | ReactOS còn ở trạng thái alpha tại thời điểm tra cứu | [S12](https://reactos.org/download/), 02/11/2026 | Không chọn làm nền pilot nghiệp vụ (ADR 0001) |

## 6. .NET & runtime

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A26 | FACT | WPF được hỗ trợ chính thức trên Windows, dù .NET có tính đa nền tảng | [S07](https://learn.microsoft.com/en-us/dotnet/desktop-wpf/overview/index), 02/11/2026 | WinForms/WPF không tự sang Linux khi cài .NET Runtime Linux |
| A27 | FACT | .NET Framework (2–4.x) khác .NET hiện đại và là công nghệ Windows | [S08](https://github.com/dotnet/docs/blob/main/docs/framework/install/on-windows-and-server.md), 02/11/2026 | Mono/Wine Mono không bảo đảm tương đương Microsoft .NET Framework |
| A28 | FACT | Có thể cài .NET runtime/SDK trên bản phân phối Linux phù hợp | [S11](https://learn.microsoft.com/en-us/dotnet/core/install/linux), 02/11/2026 | Cài runtime Linux ≠ chạy mọi executable Windows |
| A29 | DESIGN | Phân tích .NET bằng tĩnh (PE arch, CLR metadata, runtimeconfig/deps, TargetFramework); không thực thi để nhận diện mặc định | §NET-001/002, ADR 0004 | Giới hạn kích thước/thời gian/quyền parser; input có thể độc hại |
| A30 | DESIGN | Quản lý Wine Mono và Microsoft .NET theo recipe riêng; Winetricks pin revision + ghi URL/hash/điều khoản payload | §NET-003 | Pin script ≠ pin toàn bộ chuỗi cung ứng |

## 7. Phần mềm riêng & stack

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A31 | DESIGN | Python 3 cho CLI/service; PySide6 Qt Quick cho UI (ADR 0006) | §5.1, ADR 0006 | Kiểm version/giấy phép/packaging Qt/PySide trong Debian |
| A32 | FACT | Host hiện tại có python 3.11.2 + venv + pip; đủ chạy lõi M1 Python thuần | inventory M0 | pytest cài qua pip trong venv |
| A33 | DESIGN | Helper đặc quyền tối thiểu qua D-Bus/Polkit; không nhận shell command tùy ý; không HTTP localhost điều khiển đặc quyền | §5.2, §CLI-004, ADR 0006 | Negative test SEC-01 |
| A34 | UNKNOWN | Phiên bản PySide6/Qt khả dụng + chi phí startup + accessibility thực tế | chưa đo | Spike ADR 0006 |

## 8. Dữ liệu cục bộ & lưu trữ

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A35 | DESIGN | JSON có schema cho catalog; SQLite cho trạng thái giao dịch (KHÔNG làm kho tài liệu người dùng) | §5.1 | — |
| A36 | FACT | SQLite transaction chỉ bảo vệ metadata; không biến thay đổi filesystem thành giao dịch nguyên tử | §13 | Phải có journal + hành động bù mỗi bước (TX-001..003) |
| A37 | DESIGN | Layout XDG (`~/.config|.local/share|.cache|.local/state/vietdesk/`...); không hardcode `/home/<name>` | §11.3 | Tôn trọng XDG; path thật không nối chuỗi không kiểm tra |

## 9. Cập nhật, ký metadata & chuỗi cung ứng

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A38 | DESIGN | APT + repo có chữ ký cho gói hệ thống; không thiết kế package manager mới | §5.1 | — |
| A39 | DESIGN | Catalog/profile dùng framework ký metadata được duy trì, ưu tiên đánh giá TUF (ADR 0007) | §SEC-007, ADR 0007 | Spike TUF đạt điều kiện; không tự phát minh giao thức chữ ký |
| A40 | DESIGN | Fail closed khi chữ ký sai/thu hồi; chặn downgrade/replay; không cho catalog điều khiển lệnh root | §SEC-008, ADR 0007 | Negative test SEC-10, UPD-03 |
| A41 | DESIGN | Key production KHÔNG nằm trong repo/ISO/CI không tin cậy; dev key gắn nhãn rõ trong lab | §SEC-007, §BUILD-003 | — |
| A42 | UNKNOWN | TUF (hoặc framework thay thế) có đáp ứng spike cho catalog NaMiOS hay không | chưa spike | ADR 0007 |

## 10. Bảo mật & cách ly

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A43 | DESIGN | Sandbox dùng cơ chế Linux duy trì (bubblewrap/AppArmor) với policy cụ thể; prefix ≠ sandbox | §SEC-003, threat-model.md | Negative test SEC-06/07/08 |
| A44 | FACT | Microsoft quy định quyền sao chép/sửa đổi/phân phối phải được cấp theo điều khoản tương ứng | [S01](https://www.microsoft.com/en-us/legal/intellectualproperty/copyright/permissions), 02/11/2026 | Phần mềm tải công khai ≠ quyền phân phối lại |
| A45 | TARGET | Triage CVE nghiêm trọng ≤24h làm việc; vá/giảm thiểu ≤72h khi khả thi | §SEC-011 | Mục tiêu nội bộ, CHƯA phải SLA thương mại |
| A46 | DESIGN | Mã hóa ổ đĩa cần đạt trước pilot chứa dữ liệu nhạy cảm | §SEC-012 | Phải thử boot/unlock/update/recovery; không tự tuyên bố có mã hóa nếu installer chưa tích hợp |

## 11. Ứng dụng mục tiêu (nguồn vào chính thức)

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A47 | FACT | Zalo có điểm vào chính thức cho PC và Web | [S03](https://www.zalo.me/pc), 02/11/2026 | Không suy ra bản Linux chính thức từ tên gói cộng đồng; từng mode cần test |
| A48 | FACT | MISA SME dùng mô hình client-server/SQL Server với điều kiện hệ thống công bố | [S04](https://helpsme.misa.vn/2026/kb/kiem-tra-cau-hinh-may-tinh-truoc-khi-cai-dat-sme/), 02/11/2026 | Không là bằng chứng Wine hỗ trợ; không mặc định SQL Server Linux thay mọi SME |
| A49 | FACT | AMIS Kế toán có cách truy cập web chính thức | [S05](https://helpact.misa.vn/kb/cach-mo-nhanh-amis-ke-toan-tu-taskbar-hoac-desktop/), 02/11/2026 | Không chứng nhận mọi browser trên Linux |
| A50 | FACT | Nghiệp vụ web MISA (ký số) còn cần công cụ cục bộ / quyền trình duyệt | [S06](https://helpamis.misa.vn/amis-thue-tncn/kb/huong-dan-thiet-lap-quyen-tren-trinh-duyet-web-de-ket-noi-duoc-ung-dung-misa-kyso-khi-ky-to-khai-chung-tu/), 02/11/2026 | Không suy "web nên mọi chức năng chạy Linux" |
| A51 | FACT | Microsoft 365 có yêu cầu hệ thống/trình duyệt theo từng dịch vụ, có thể thay đổi | [S13](https://support.microsoft.com/en-us/accounts-billing/subscriptions/microsoft-365-system-requirements), 02/11/2026 | Đối chiếu từng dịch vụ lúc test web |
| A52 | UNKNOWN | Edition/build/32-64bit/phương thức cấp phép của Word/Excel mục tiêu | chờ chủ dự án (§22.1) | Chặn APP-OFF chứng nhận |
| A53 | UNKNOWN | SME năm/build hay AMIS; SQL version; báo cáo; nhà cung cấp chữ ký số | chờ chủ dự án (§22.2) | Chặn APP-MIS chứng nhận |
| A54 | UNKNOWN | Danh sách ứng dụng .NET cụ thể + bộ cài/source có quyền dùng | chờ chủ dự án (§22.3) | Chặn phân loại/chạy .NET thực |

## 12. Hiệu năng & phần cứng (TẤT CẢ là TARGET)

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A55 | TARGET | Cold boot → desktop p95 ≤60s; idle RAM ≤2 GB; app-center cold start p95 ≤3s | §PERF-001 | Đo ≥20 lần, ghi firmware/kernel/session; thất bại báo số đo, không sửa ngưỡng ngầm |
| A56 | TARGET | Tìm catalog local ≤300ms p95 với 1.000 records trên máy tham chiếu | §PERF-002 | — |
| A57 | TARGET | Cấu hình tham chiếu chính: CPU 4 nhân, RAM 8 GB, SSD 128 GB | §16 | Không coi là bảo đảm đủ cho mọi workload |
| A58 | TARGET | Độ phủ pilot ≥5 cấu hình vật lý + ≥2 máy in khác hãng | §HW-001 | Độ phủ thử nghiệm, không đại diện toàn thị trường |
| A59 | UNKNOWN | Kết quả thực boot/sleep-resume/print/Wi-Fi/token trên phần cứng thật | chưa có máy pilot | M4; driver Windows không mặc nhiên chạy Linux |
