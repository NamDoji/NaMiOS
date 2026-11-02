# Bảng giả định nền tảng — FACT / DESIGN / TARGET / UNKNOWN

**Ngày tra cứu:** 02/11/2026 (Asia/Ho_Chi_Minh). **Nguồn FACT:** §24 đặc tả (S01–S13) + §30 đặc tả (S14–S17) + inventory M0.

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
| A37 | DESIGN | Layout XDG (`~/.config|.local/share|.cache|.local/state/namios/`...); không hardcode `/home/<name>` | §11.3 | Tôn trọng XDG; path thật không nối chuỗi không kiểm tra |

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

---

> **Bổ sung đặc tả SUPERSET §26–§30 (delta vòng 2, 02/11/2026).** Các nhóm dưới đây thêm cho ownership/brand, thiết bị-driver, giao diện quen thuộc, chuyển đổi thật và kế hoạch đo. Nguyên tắc không đổi: FACT/DESIGN/TARGET/UNKNOWN; mọi con số (90% tác vụ, 20 thiết bị, 30 ngày, 15 người, 100 app) là **TARGET/ngưỡng đề xuất**, KHÔNG phải kết quả. Phần lớn chứng nhận thật thuộc M3/M4 và hiện **BLOCKED** tại host này (thiếu nested-virt + phần cứng thật + bộ cài có quyền). Xem ADR 0009–0012.

## 13. Quyền sở hữu & thương hiệu NaMiOS (§26, OWN-001..003)

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A60 | DESIGN/FACT | Tên sản phẩm thống nhất là **NaMiOS** (giao diện, bộ cài, tài liệu, website, gói, báo cáo); namespace `namios_*`, CLI `namios`, path `~/.config/namios/` | §26 OWN-001 (chỉ đạo chủ dự án), CLAUDE.md | Áp dụng nhất quán; đây là chỉ đạo đặt tên, KHÔNG phải xác nhận đăng ký bảo hộ |
| A61 | DESIGN/FACT | Hai nhà sáng lập/chủ dự án là **Đỗ Chí Cường và Đỗ Bảo Nam** (theo chỉ đạo) | §26 OWN-001 | Hồ sơ tác giả/nguồn gốc phần tự viết phải ghi rõ để quản trị dài hạn |
| A62 | FACT | NaMiOS KHÔNG sở hữu Debian/Linux/KDE/Wine hay tài sản bên thứ ba; chỉ sở hữu phần tự viết | §26 OWN-001, CLAUDE.md | Cấm mọi câu chữ ngụ ý sở hữu upstream; About phải nêu giấy phép thành phần |
| A63 | DESIGN | Đề xuất Apache-2.0 cho **mã mới tự viết**; phải kiểm tương thích giấy phép với mọi thành phần phụ thuộc trước khi chốt | §26 OWN-003, ADR 0009 | Rà quét license dependency (copyleft/khác); không mặc định tương thích |
| A64 | DESIGN | Hợp đồng lao động/cộng tác, contributor agreement, chuyển giao quyền + quyền dùng tên NaMiOS phải xác lập TRƯỚC phát hành | §26 OWN-001/003, ADR 0009 | Cần chủ thể pháp lý phát hành; Claude không soạn hợp đồng ràng buộc pháp lý |
| A65 | UNKNOWN | Tình trạng nhãn hiệu & tên miền "NaMiOS" (đã bị đăng ký/trùng hay chưa) | chưa tra cứu | Tra cứu trademark/domain trước công bố; ghi trạng thái tra cứu, không tự coi là đã bảo hộ |
| A66 | FACT | Không dùng tên Windows trong thương hiệu HĐH; chỉ dùng khi mô tả khả năng tương thích | §26 OWN-002, [S01](https://www.microsoft.com/en-us/legal/intellectualproperty/copyright/permissions), 02/11/2026 | About/marketing rà từ ngữ; không dựng huy hiệu giống chứng nhận MS |

## 14. Thiết bị & driver (§27, DEV-001..008, HWPLUS)

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A67 | FACT | Driver `.sys` kernel-mode của Windows KHÔNG mặc nhiên nạp/chạy trên nhân Linux | [S17](https://learn.microsoft.com/windows-hardware/drivers/gettingstarted/user-mode-and-kernel-mode), 02/11/2026 | Phải dùng driver Linux / giao thức chuẩn / giải pháp vendor-supported; Wine ≠ phủ driver phần cứng |
| A68 | FACT | In không-driver (IPP Everywhere/AirPrint) được hỗ trợ trong hệ sinh thái Linux qua CUPS | [S14](https://openprinting.github.io/driverless), 02/11/2026 | Nhận được máy in ≠ in đúng nghiệp vụ; cả hai là hai phép thử (DEV-02/04) |
| A69 | FACT | IPP/eSCL over USB khả dụng trên thiết bị tương thích | [S15](https://openprinting.github.io/projects/03-ipp-usb), 02/11/2026 | Chứng nhận theo đúng model; không suy từ model khác cùng hãng |
| A70 | FACT | Scanner tra cứu qua danh sách SANE (eSCL/AirScan/backend) theo model | [S16](https://www.sane-project.org/sane-supported-devices.html), 02/11/2026 | Danh sách SANE chỉ là đầu vào khảo sát; phải thử thật từng model (DEV-03/05) |
| A71 | DESIGN | Cơ sở dữ liệu thiết bị theo vendor ID × product ID × revision × firmware × kết nối × kernel × driver/backend × giấy phép × chức năng × trạng thái × người xác nhận | §27 DEV-001, ADR 0010 | Nhận-diện USB ID ≠ chứng-nhận; không ghi "đã hỗ trợ" khi mới nhận diện |
| A72 | DESIGN | Trung tâm thiết bị tiếng Việt gắn nhãn "hoạt động đầy đủ/một phần/chưa kiểm thử/không hỗ trợ" theo **model × chức năng** + ngày chứng nhận | §27 DEV-008, ADR 0010 | Nhãn phải khớp evidence; không flash firmware mặc định, không tải driver nguồn lạ |
| A73 | DESIGN | Máy đa chức năng chứng nhận phần in và phần quét RIÊNG; thiết bị chuyên dụng chứng nhận cùng phần mềm Windows điều khiển nó | §27 DEV-003/006, ADR 0010 | Hai tầng (thiết bị + app điều khiển) nghiệm thu cùng nhau |
| A74 | UNKNOWN | "Mọi thiết bị kết nối đều chạy" | — | CẤM tuyên bố khi chưa có ma trận model×chức năng + evidence (§27) |
| A75 | TARGET | Lab tối thiểu 20 model ngoại vi (in/scan/token/kết nối) trước G2; không thay yêu cầu ≥5 máy tính + ≥2 máy in ở §16 | §30 HWPLUS-001 | Số 20 là TARGET lập kế hoạch; mỗi model cần ID/firmware/giao thức/chức năng/evidence |
| A76 | UNKNOWN | Kết quả thực in/scan/hotplug/sleep-resume/IPP-over-USB/in-từ-Wine/mất-mạng/cập-nhật-kernel trên thiết bị thật | chưa có lab | M4/§30 HWPLUS-002 BLOCKED tại host này; lỗi sai/thiếu chứng từ là P0 |

## 15. Chữ ký số USB token (§27, DEV-005)

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A77 | DESIGN | Ma trận token: **hãng × model × firmware × middleware × trình duyệt × ứng dụng × nghiệp vụ**; ưu tiên đường PKCS#11/PCSC + driver Linux chính thức khi có | §27 DEV-005, ADR 0010 | Truy cập token bằng user thường, quyền thiết bị hẹp; test đăng nhập/chọn chứng thư/ký sandbox/ngắt/PIN sai/hết hạn/phục hồi |
| A78 | UNKNOWN | Middleware ký số Windows-only có buộc dùng môi trường Windows (VM/remote có license) hay không | chưa test từng hãng | Không cam kết ký số chạy chỉ vì token hiện trong `lsusb`; đánh giá theo từng hãng/model |
| A79 | FACT/DESIGN | Không thực hiện nghiệp vụ ký pháp lý thật trong lab; chỉ ký ở môi trường sandbox / giả lập | §27 DEV-005, CLAUDE.md | DEV-06 chạy sandbox vendor; không ký chứng từ thật |

## 16. Giao diện quen thuộc với người dùng Windows (§28, UI-001..007)

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A80 | DESIGN | Bố cục quen thuộc: taskbar + nút mở app + tìm kiếm + khay hệ thống + đồng hồ + thông báo + danh sách cửa sổ + ghim/bỏ ghim + khu vực file đang mở | §28 UI-001, ADR 0011 | Test khi IME + Wine hoạt động; không coi KDE mặc định đã đủ cho người Việt |
| A81 | DESIGN | Ánh xạ phím tắt công bố: Alt+Tab, Win+E, Win+D, Ctrl+C/V, Print Screen, chuột phải, kéo-thả, đổi ngôn ngữ | §28 UI-001, ADR 0011 | Không tùy tiện chiếm phím tắt của app; mapping được test |
| A82 | FACT | KHÔNG chép pixel/biểu tượng/âm thanh/thương hiệu độc quyền của Microsoft | §28 (ràng buộc), [S01](https://www.microsoft.com/en-us/legal/intellectualproperty/copyright/permissions), 02/11/2026 | Dùng bộ nhận diện riêng; rà asset trước phát hành |
| A83 | DESIGN | Design tokens riêng cho NaMiOS: lưới khoảng cách, typography đủ dấu Việt, kích cỡ tối thiểu, tương phản, focus, icon riêng, trạng thái lỗi/loading/empty/offline, sáng/tối, responsive theo DPI | §28 UI-004, ADR 0011 | "Đẹp và giống Windows" ≠ khả dụng; không tuyên bố có chuẩn pháp lý thống nhất cho UI app Việt khi chưa chỉ ra chuẩn/đơn vị |
| A84 | DESIGN | File manager: Home/Documents/Downloads/Desktop/ổ ngoài/phân vùng Windows đọc-được; tên tiếng Việt, preview, SMB, mount/unmount an toàn, trash/restore, nhãn dung lượng + filesystem | §28 UI-002, ADR 0011 | Không gọi ổ Linux là `C:`; ánh xạ `C:` chỉ trong phạm vi Wine khi cần |
| A85 | DESIGN | Onboarding sau cài: chọn chế độ giao diện/cỡ chữ/bộ gõ Telex-VNI/trình duyệt/phần mềm mở DOCX-XLSX-PDF/máy in mặc định/dữ liệu chuyển từ Windows | §28 UI-005, ADR 0011 | Không đặt LibreOffice tên hiển thị là Word/Excel |
| A86 | TARGET | Usability ≥15 người (văn phòng/giáo viên/kế toán) × 8 tác vụ; ngưỡng ≥90% tác vụ cơ bản hoàn thành không cần hướng dẫn sau 15 phút | §28 UI-006, ADR 0011 | Chưa đạt → sửa luồng + thử lại; KHÔNG tự đổi định nghĩa tác vụ; 15/90%/15 phút là TARGET |
| A87 | DESIGN | Bộ "ứng dụng Việt Nam" theo sản phẩm × phiên bản (trình duyệt chính phủ/thuế, học tập, hóa đơn, ký số, Zalo, MISA...) do nhóm người dùng mục tiêu xác nhận | §28 UI-007, ADR 0011 | Mỗi app test Unicode/font/gõ Việt/ngày-tiền/upload-download/pop-up/in/file association; nhãn "phù hợp VN" chỉ dựa tập tác vụ đã xác minh, không phải chứng nhận nhà nước |

## 17. Điều kiện chuyển đổi thật & pilot (§29–§30, WIN-001..008, MIG-001)

| # | Loại | Nội dung | Nguồn / cơ sở | Điều kiện xác nhận |
| --- | --- | --- | --- | --- |
| A88 | DESIGN | Tiêu chí là **tương đương theo tác vụ / workflow trọn vẹn**, KHÔNG phải "mở được .exe" | §29 WIN-003, ADR 0012 | Mỗi app: cài/kích hoạt hợp lệ, mở dữ liệu cũ, sửa, tính, lưu, đóng/mở lại, in, xuất, gửi, cập nhật, phục hồi — so với Windows tham chiếu cùng phiên bản |
| A89 | TARGET | Khảo sát **100 app** Windows + chọn **20 app** pilot (Word/Excel/Zalo PC/MISA SME/các lớp .NET phải nằm trong khảo sát) | §29 WIN-001 | Đây là TARGET khảo sát; KHÔNG tuyên bố đã khảo sát hoặc sẽ có 100 app chạy được |
| A90 | DESIGN | Mode `wine/web/native/vm/remote` ghi riêng trong kết quả; KHÔNG cộng gộp mode để báo tỷ lệ tương thích desktop | §29 WIN-003/005, ADR 0012 | Binary cần kernel driver Windows → gắn `requires_windows_environment` trừ khi có giải pháp Linux vendor-supported đã test |
| A91 | DESIGN | Workflow trọn vẹn (tạo file Office → Zalo/email → ký số/hóa đơn → lưu kho → in → đối soát MISA): nếu MỘT bước bắt buộc fail → nhóm là `not_ready_for_migration` | §29 WIN-006, ADR 0012 | Không đưa kết quả app rời rạc thành lời khuyên bỏ Windows |
| A92 | TARGET | Pilot song song **30 ngày** với nhóm tự nguyện trên thiết bị đã chứng nhận; ngưỡng xem xét mở rộng: 0 mất/sai dữ liệu P0, 100% tác vụ bắt buộc đạt, ≥90% tác vụ hàng ngày không phải quay lại Windows | §29 WIN-007, §30 MIG-001 | 30 ngày / 90% là ngưỡng đề xuất, chốt TRƯỚC khi đo; báo cáo có mẫu số người dùng + số lần |
| A93 | UNKNOWN | WIN-008: "100% app Windows hiện hành chạy nguyên vẹn kể cả kernel driver" | — | KHÔNG bảo đảm được; KHÔNG giao Claude "bảo đảm 100% tương thích"; nếu mục tiêu kinh doanh đòi điều này → đánh giá lại nền tảng (có thể phải phạm vi hẹp hoặc đường VM/remote có license) |
| A94 | DESIGN | Checklist trước chuyển đổi (MIG-001): app/thiết bị/phiên bản dữ liệu/backup-restore/tài khoản-giấy phép/người hỗ trợ/kế hoạch quay về/người ký; thử trên máy phụ hoặc Live trước, chỉ chuyển máy chính khi workflow nghiệm thu + có bản sao phục hồi được | §30 MIG-001, ADR 0012 | Quy trình tiếp nhận app lỗi (WIN-004): repro tối thiểu, log không bí mật, phân loại Wine/runner/prefix/driver/service/activation; không fork hàng loạt khi chưa có đội bảo trì |
| A95 | UNKNOWN | Kết quả thực của pilot/workflow/usability trên máy + người thật | chưa có lab/pilot | §29–30 phần lớn M3/M4 BLOCKED tại host này (cần build host nested-virt + phần cứng + bộ cài có quyền + người dùng tình nguyện) |
