# NaMiOS — Khảo sát ký số USB token / PKCS#11 cho người Việt (kế toán/thuế)

- **Trạng thái:** `specified` — khảo sát **nguồn công khai thật** (web, ngày
  khảo sát 11/11/2026), `verified_on_host: NO` cho MỌI kết luận "chạy được"
  dưới đây — chưa cắm một USB token thật nào vào máy chạy NaMiOS. Tài liệu
  này **bổ sung bằng chứng mới** cho mục "USB token chữ ký số" đã có ở
  `docs/wine/WINE-COMPAT-MATRIX.md` §2, không thay thế quy tắc gán verdict ở
  `docs/specs/COMPAT-ROUTING.md` §4.
- **Vì sao tách file riêng:** chủ đề ký số số USB token là điểm nghẽn lớn
  nhất cho nhóm kế toán/tài chính (`docs/roadmap/NANG-CAP-NHU-CAU-NGUOI-DUNG.md`
  §1.4) — cần đủ chỗ để ghi chi tiết per-vendor thay vì gộp một dòng trong
  ma trận chung.
- **Quy tắc trích dẫn:** mọi "sự thật" dưới đây đến từ trang web công khai
  (vendor, báo/blog hướng dẫn kê khai thuế, hoặc mã nguồn mở có thể xem được)
  — **không phải** tài liệu kỹ thuật nội bộ của CA Việt Nam (các hãng không
  công bố spec driver chi tiết). Một số nguồn là blog/trang dịch vụ bên thứ
  ba (không phải trang chính thức `*-ca.vn`) — đã ghi rõ loại nguồn ở mỗi
  mục, vì trang `.gov.vn`/nhiều trang vendor không mở được từ host phát triển
  hiện tại (xem `source_check` lặp lại trong `catalog/services/*.json`).

## 1. Vì sao đây là vấn đề kiến trúc, không phải "chưa cố đủ"

`docs/adr/ADR-0015-dotnet-windows-compat-strategy.md` đã nêu: Wine là lớp
dịch API Windows ở **user-space**, không nạp driver kernel `.sys` của
Windows. USB token chữ ký số cần **CSP/minidriver** (Windows) hoặc một
**middleware PKCS#11 native Linux do chính vendor build** — không có con
đường thứ ba. Mục tiêu khảo sát này: với TỪNG CA Việt Nam, middleware Linux
đó **có tồn tại hay không**, dựa trên bằng chứng công khai mới nhất tìm
được, thay vì lặp lại giả định "chắc chắn không có" từ các wave trước.

## 2. Per-vendor — những gì tìm được (11/11/2026)

| CA / vendor | Bằng chứng tìm được | Kết luận | Độ tin cậy |
| --- | --- | --- | --- |
| **VNPT-CA** (USB token vật lý) | Trang hướng dẫn kỹ thuật bên thứ ba ghi: nhiều token VN được format theo chuẩn **minidriver Windows (mscp)**, không phải **PKCS#15** — khi cắm vào Linux/macOS và dùng `opensc-pkcs11.so` (driver PKCS#11 mã nguồn mở phổ biến nhất), kết quả là lỗi `CKR_TOKEN_NOT_RECOGNIZED` **dù đầu đọc USB được nhận diện bình thường** ở tầng hệ điều hành. Trang tải chính thức `vnpt-ca.vn/download-page` chỉ liệt kê driver cho Windows x64 và macOS x64 — **không thấy gói Linux** trong kết quả tìm kiếm. | `blocked` qua driver chuẩn OpenSC; middleware Linux CHÍNH HÃNG **không xác nhận tồn tại** từ nguồn công khai đã xem. | Trung bình — nguồn là blog kỹ thuật bên thứ ba, chưa tự tay xác minh lại trên token thật. |
| **Viettel-CA** (USB token vật lý, nhãn "Token Agent") | Các trang tải (`viettel-ca.vn/tai-ve`, `chukyso-viettel-ca.com`) chỉ liệt kê bộ cài `.exe` cho Windows (nhiều phiên bản V0–V6). Không tìm thấy gói `.deb`/`.rpm`/`.pkg` nào trong kết quả tìm kiếm. | `blocked` — không có bằng chứng middleware Linux chính hãng. | Trung bình-thấp — có thể có mà công cụ tìm kiếm không phủ hết; cần hỏi thẳng hotline Viettel-CA nếu muốn chắc 100%. |
| **FPT-CA** (Token Manager v4) | Yêu cầu kỹ thuật công bố: trình duyệt Firefox/IE/Chrome đời cũ + **Java 7.0 trở lên**. Bộ cài là `Fptca_v4_installer.exe` (Windows). Không thấy bản Linux. | `blocked` cho phần driver token; phần "cần Java" KHÔNG đồng nghĩa chạy được trên Linux — Java ở đây chỉ chạy **applet/plugin trình duyệt cũ kiểu NPAPI**, bản thân cơ chế đó đã bị hầu hết trình duyệt hiện đại (kể cả Windows) khai tử, không liên quan tới middleware token. | Trung bình. |
| **Các CA khác** (CA2, Safe-CA, EFY-CA, BKAV-CA…) | **Chưa khảo sát riêng từng hãng** ở vòng này — ưu tiên 3 hãng owner nêu tên (Viettel/VNPT/FPT). | `unknown` — giữ nguyên, không suy đoán. | — |

### 2.1 Vì sao phần cứng "giống hệt" không bảo đảm driver giống hệt

Nhiều token chữ ký số PKI phổ biến trên thế giới dùng chip nền **Gemalto/
SafeNet eToken** (dòng 5110 và họ hàng) — Gemalto có phát hành driver chính
hãng dạng gói Linux `.deb`/`.rpm` thật (thư viện PKCS#11 tên
`libeToken.so`/`libeTPkcs11.so`). **Đây KHÔNG tự động suy ra token của
Viettel-CA/VNPT-CA/FPT-CA chạy được driver đó** — các CA Việt Nam có thể
dùng chip khác, hoặc cùng họ chip nhưng **firmware/applet riêng** (ký hiệu
hãng, OID chứng thư, cấu trúc file hệ thống trên thẻ) khác với bản gốc
Gemalto bán ra thị trường quốc tế, khiến driver gốc không nhận đúng. Cộng
đồng OpenSC cũng ghi nhận **một số dòng eToken (ví dụ 5110 bản gốc) không
được OpenSC hỗ trợ**, chỉ bản `5110+ FIPS` mới có patch hỗ trợ và vẫn còn
báo lỗi trong một số thao tác ký (theo issue tracker OpenSC công khai). **Kết
luận trung thực:** khả năng "vỏ ngoài giống token quốc tế đã có driver Linux"
là một **giả thuyết đáng thử, không phải bằng chứng** — chỉ xác nhận được
bằng cách cắm đúng token Việt Nam thật vào máy Linux thật và thử `pkcs11-tool
--list-slots`/`--list-objects`. Không ai trong NaMiOS đã làm việc này.

## 3. Lớp "bắc cầu" không chính thức — MacSigner (quan trọng, đọc kỹ phần cảnh báo)

Tìm thấy một dự án **mã nguồn mở, bên thứ ba, KHÔNG thuộc NaMiOS và KHÔNG
được bất kỳ CA Việt Nam nào xác nhận chính thức**: **MacSigner**
(`github.com/DeanOpen/MacSigner`, giấy phép Apache 2.0).

- **Làm gì:** dùng chuẩn PKCS#11 để tự dò USB token chữ ký số (không giới
  hạn theo tên vendor cụ thể, tự chọn module PKCS#11 phù hợp với thiết bị
  cắm vào), hỗ trợ hai giao thức ký hay dùng ở VN: **ESIGN** (ký kê khai
  thuế qua WebSocket, kiểu giao thức mà eSigner/HTKK/eTax dùng) và
  **CTSIGN** (tương thích API CTSigningHub — công cụ ký hóa đơn điện tử nêu
  ở mục 4 dưới).
- **Nền tảng:** viết bằng Rust (Tauri + React cho giao diện) — build ra cả
  Windows (`.msi`/`.exe`), macOS, **và Linux** (`.deb`, `.rpm`, `.AppImage`).
  Đây là điểm khác biệt lớn nhất so với mọi công cụ chính hãng đã khảo sát ở
  mục 2 — **không cần Wine ở bất kỳ phần nào**, vì bản thân app là Linux
  native.
- **Độ trưởng thành (đọc trang releases GitHub, ngày khảo sát 11/11/2026):**
  bản mới nhất `v0.3.0` phát hành 21/10/2026, ghi chú "thêm UI dịch vụ VNPT
  + xác thực token bundle" — tức dự án đang **tích cực được cập nhật** và
  **đã nhắm riêng tới VNPT** (một trong 3 CA owner cần). Các bản trước
  (`v0.2.x`, cũng 10/2026) đều có sẵn gói `.deb`/`.rpm`/`.AppImage`. README
  dự án tự mô tả: ký PDF **đã dùng được**, ký kê khai thuế **đang thử
  nghiệm** — tức ngay chính tác giả cũng chưa tuyên bố "xong" cho phần kê
  khai thuế.

### 3.1 CẢNH BÁO BẮT BUỘC (không được bỏ qua khi nói với owner)

- **KHÔNG phải sản phẩm chính thức** của Viettel-CA/VNPT-CA/FPT-CA/Tổng cục
  Thuế. Không ai trong các cơ quan/doanh nghiệp đó xác nhận tương thích.
- **NaMiOS CHƯA cài thử, CHƯA cắm token thật, CHƯA đọc mã nguồn đầy đủ.**
  Mọi mô tả ở trên lấy từ README/trang release công khai — **không phải**
  đánh giá bảo mật độc lập. Một công cụ xử lý **khóa ký số cá nhân/doanh
  nghiệp** (hậu quả pháp lý nếu bị lộ hoặc ký sai) đòi hỏi mức thận trọng
  cao hơn một app Win32 thông thường trong `docs/wine/WINE-COMPAT-MATRIX.md`.
- Vì gọi tự PKCS#11 generic (không hard-code theo vendor), MacSigner **vẫn
  gặp đúng rào cản ở mục 2.1**: nếu token Việt Nam dùng applet/firmware
  riêng không lộ đúng cấu trúc PKCS#11 chuẩn, MacSigner cũng sẽ không đọc
  được token đó, bất kể Rust/Tauri đẹp tới đâu — đây không phải "phép màu
  vượt qua giới hạn phần cứng", chỉ là **một con đường khác đáng thử**.
- **Khuyến nghị cho owner:** nếu quyết định thử, (a) dùng dữ liệu/tờ khai
  **không quan trọng** trước, (b) đối chiếu đúng mã nguồn đã build (không
  tải bản build lạ ngoài trang GitHub release chính chủ), (c) coi đây là
  **thử nghiệm cá nhân rủi ro tự chịu**, KHÔNG phải tính năng NaMiOS hỗ trợ
  chính thức, cho tới khi có người nghiệp vụ ký duyệt theo đúng quy trình
  `COMPAT-ROUTING.md` §3-4. KHÔNG đóng gói MacSigner vào ISO NaMiOS ở alpha
  (ngoài phạm vi U13-10, cần ADR nguồn-gói riêng theo CLAUDE.md "không nhúng
  repo bên thứ ba vào ISO nếu chưa có ADR nguồn-gói").

## 4. Lớp quan trọng nhất tìm được — "Ký số từ xa" (remote/cloud signing)

Đây là phát hiện có khả năng thay đổi toàn bộ bài toán, **không nằm trong Wine
hay PKCS#11 nữa**: cả ba CA lớn owner quan tâm hiện đều có dịch vụ **ký số
từ xa** (khóa bí mật lưu trên **HSM của nhà cung cấp**, không lưu trên USB
token vật lý):

| Dịch vụ | Nhà cung cấp | Cơ chế |
| --- | --- | --- |
| **VNPT SmartCA** | VNPT-CA | Ký qua web (RESTful Web API chuẩn theo tài liệu tích hợp công khai `doitac-smartca.vnpt.vn`) + xác nhận trên **app điện thoại** VNPT SmartCA (PIN/sinh trắc học). Không cần USB Token, không cần cài phần mềm/plugin nào trên MÁY TÍNH khi dùng trực tiếp trên web. |
| **Viettel-CA Cloud / MySign** | Viettel-CA | Tương tự: khóa bí mật trên HSM phía Viettel, ký trực tiếp bằng app điện thoại MySign, không cần USB Token/SIM CA. Triển khai từ 01/04/2020 theo trang chính thức Viettel-CA. |
| **FPT-CA remote** | FPT-CA | Chưa tìm được trang mô tả kỹ thuật chi tiết riêng ở vòng khảo sát này — các CA lớn khác (VNPT/Viettel) đều đã có, nhiều khả năng FPT-CA cũng có dịch vụ tương đương (`unknown`, chưa xác nhận tên sản phẩm cụ thể). |

**Vì sao đây là tuyến đáng ưu tiên nhất:** cơ chế "ký web + duyệt trên điện
thoại" có nghĩa **máy tính không bao giờ chạm vào khóa bí mật** — toàn bộ
việc "ký" xảy ra giữa server HSM của CA và app điện thoại, máy tính chỉ hiển
thị trang web và nhận kết quả. Điều này **hoàn toàn không liên quan tới
Wine/PKCS11/driver USB** — chạy tốt trên **bất kỳ máy nào mở được trình
duyệt**, bao gồm NaMiOS + Firefox. Bằng chứng công khai xác nhận CẢ cổng
thuế điện tử (`thuedientu.gdt.gov.vn`, cho phép đăng ký loại CA "ký số từ
xa" song song với USB Token khi đăng ký chữ ký số trên hệ thống) **và** cổng
BHXH (`dichvucong.baohiemxahoi.gov.vn`, liệt kê VNPT SmartCA/Viettel MySign
là lựa chọn nhà cung cấp chữ ký số) đều hỗ trợ tuyến này — tức đây không
phải suy đoán, hai hệ thống nghiệp vụ owner cần nhất đã có đường ký-từ-xa
thật, công khai.

### 4.1 Vì sao đây KHÔNG phải việc NaMiOS phải code gì thêm

Tuyến này đã là `web` (tuyến rẻ nhất theo thứ tự ADR-0015) — NaMiOS chỉ cần
**Firefox đã có sẵn**, không cần Wine, không cần `namios-wine-capsule`,
không cần preset nào. Việc owner cần làm là **quyết định nghiệp vụ**: có
đổi/đăng ký thêm dịch vụ ký số từ xa (nếu công ty/kế toán hiện chỉ có USB
Token truyền thống) hay không — đây là quyết định hợp đồng với CA, không
phải giới hạn kỹ thuật của NaMiOS.

## 5. Kết luận — tuyến đáng tin nhất cho ký số trên NaMiOS

**Theo thứ tự ưu tiên thật (không phải suy đoán mới, dựa trên bằng chứng
mục 2–4):**

1. **Ký số từ xa (SmartCA/MySign/tương đương)** — `web`, không cần Wine,
   **khuyến nghị owner chuyển sang/đăng ký thêm nếu khả thi về hợp đồng với
   CA hiện dùng.** Đây là câu trả lời thực tế nhất cho "làm sao ký số trên
   NaMiOS", không phải một thủ thuật Wine nào.
2. **USB Token vật lý qua driver PKCS#11 chính hãng Linux** — `blocked`
   theo bằng chứng mục 2 cho cả 3 CA đã khảo sát (chưa tìm thấy middleware
   Linux chính hãng công khai). Cần hỏi thẳng vendor để xác nhận 100%
   (chưa làm — ngoài phạm vi khảo sát web).
3. **MacSigner (cộng đồng, PKCS#11 generic, có build Linux)** — `unverified
   nhưng đáng theo dõi`, KHÔNG khuyến nghị dùng cho nghiệp vụ thật tới khi
   owner tự đánh giá + test với token thật + dữ liệu không quan trọng.
   Không đóng gói vào ISO ở bản alpha.
4. **USB Token qua Wine** — `blocked` theo ADR-0015 (không driver kernel) —
   giữ nguyên kết luận cũ, bằng chứng mới ở mục 2–3 không thay đổi điều
   này: vấn đề nằm ở driver/middleware chưa tồn tại hoặc chưa xác nhận trên
   Linux nói chung, **không phải** riêng Wine.

## 6. Nguồn (truy cập 11/11/2026, lưu ý loại nguồn ở mỗi dòng)

- VNPT-CA trang tải chính thức: https://vnpt-ca.vn/download-page (vendor,
  chỉ liệt kê Windows/macOS trong kết quả xem được).
- Ghi chú kỹ thuật mscp/PKCS#15/OpenSC cho token VN: tổng hợp từ kết quả
  tìm kiếm web (blog kỹ thuật bên thứ ba, không phải trang `vnpt-ca.vn`
  chính thức — độ tin cậy trung bình, xem mục 2).
- Viettel-CA trang tải: https://viettel-ca.vn/tai-ve ; token agent:
  https://viettel-ca-token-agent.updatestar.com/ (bên thứ ba).
- FPT-CA yêu cầu hệ thống Token Manager v4: tổng hợp từ các trang hướng dẫn
  cài đặt công khai (`fpt-ca.com.vn`, `tiennguyenvn.com`, bên thứ ba).
- OpenSC — hỗ trợ SafeNet eToken 5110/5110+ FIPS (ghi nhận hạn chế):
  https://github.com/OpenSC/OpenSC/issues/3478,
  https://github.com/OpenSC/OpenSC/issues/3494,
  https://sourceforge.net/p/opensc/mailman/message/36443342/.
- Gemalto/SafeNet đổi tên + driver Linux chính hãng (thông tin lịch sử sản
  phẩm, không riêng cho token VN): https://data-protection-updates.gemalto.com/2016/01/21/safenet-is-now-gemalto-new-name-same-commitment/.
- MacSigner (mã nguồn mở, bên thứ ba): https://github.com/DeanOpen/MacSigner
  + trang releases cùng repo (xem mục 3, ngày phát hành 20-21/10/2026).
- VNPT SmartCA — tích hợp Web API + không cần cài plugin khi ký trên web:
  https://doitac-smartca.vnpt.vn/tich-hop-ky-so , https://smartca.vnpt.vn/.
- Viettel-CA Cloud/MySign (ký không cần USB Token, từ 01/04/2020):
  https://viettel-ca.vn/tin-tuc/viettel-ra-mat-giai-phap-ky-so-tu-xa-viettel-ca-cloud-khong-can-thiet-bi ,
  https://viettelca.vn/chu-ky-so-tu-xa-mysign-viettel.
- Cổng thuế điện tử hỗ trợ đăng ký chữ ký số từ xa song song USB Token
  (bên thứ ba hướng dẫn, tham chiếu `thuedientu.gdt.gov.vn`):
  https://vinaphonehanoi.vnpt.vn/..., https://helpesign.misa.vn/knowledge-base/dang-ky-tai-khoan-tren-trang-thue-dien-tu-ap-dung-voi-doanh-nghiep-moi/.
- Cổng BHXH hỗ trợ VNPT SmartCA/Viettel MySign (bên thứ ba hướng dẫn):
  https://onesme.vn/blog/tin-tuc-su-kien/huong-dan-ky-so-bang-smartca-tren-cong-dich-vu-cong.html.
- `docs/adr/ADR-0015-dotnet-windows-compat-strategy.md`, `docs/specs/COMPAT-ROUTING.md`,
  `docs/wine/WINE-COMPAT-MATRIX.md` — khung phân tích + quy tắc verdict đã
  có sẵn trong repo, tài liệu này KHÔNG thay đổi các quy tắc đó.
