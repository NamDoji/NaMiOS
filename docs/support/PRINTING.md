# Ma trận in ấn/quét theo HÃNG máy in (U13-06 — bổ sung)

**Yêu cầu gốc (Cuong):** "Máy in cứ kết nối hết loại: Canon, HP, Brother,
Panasonic, LG…" — máy phải tự nhận ra và in được, không bắt người dùng cài
driver tay như Windows thường làm.

**Trạng thái thật:** `specified` — có gói/cấu hình trong repo cho mọi hãng
nêu dưới đây; **CHƯA có bất kỳ máy in thật nào của bất kỳ hãng nào được cắm
vào NaMiOS và in thử.** Đọc cùng `docs/support/peripherals.md` §1–2 (ma
trận ngoại vi chung, đã có từ trước) — file này đi SÂU hơn theo từng hãng,
không thay thế file đó. **Ngày:** 10/11/2026.

**Gói/cấu hình liên quan:**
`distro/live-build/config/package-lists/0500-print.list.chroot`,
`0680-peripherals-extra.list.chroot`, `0700-printing.list.chroot` +
`distro/live-build/config/hooks/normal/0710-printing-setup.hook.chroot`.

## 0. Sự thật phải nói trước: KHÔNG hệ điều hành nào đảm bảo "cắm là in được
   với MỌI máy in"

Không một bản Linux, Windows hay macOS nào có thể cam kết in được 100% máy
in từng được sản xuất — máy quá cũ (driver chỉ có cho Windows XP 32-bit),
máy dùng chip/giao thức độc quyền chưa ai reverse-engineer, hoặc máy đời
mới mà hãng chưa phát hành driver Linux, đều có thể KHÔNG chạy được dù đã
cài đủ phần mềm dưới đây. Điều NaMiOS làm được là tối đa hoá tỷ lệ "tự nhận,
tự in" bằng ba lớp cộng lại (driverless chuẩn mở, driver mã nguồn mở theo
hãng, GUI cấu hình thủ công khi cả hai lớp trên không đủ) — **việc công
nhận "hãng X dùng được" chỉ có giá trị sau khi có pilot trên phần cứng thật
(nhóm B theo quy ước dự án)**, không phải vì tên gói "nghe có vẻ đúng".

## 1. Luồng tự nhận diện (vì sao "cắm vào/cùng mạng" lại tự chạy)

1. **Máy in cùng mạng LAN (Wi-Fi/Ethernet):** `avahi-daemon` quảng bá/nghe
   mDNS (DNS-SD) trên mạng LAN → `cups-browsed` (gói mới thêm ở
   `0700-printing.list.chroot`, cấu hình bật ở `0710-printing-setup.hook.chroot`)
   dò thấy máy in quảng bá dịch vụ IPP (`_ipp._tcp`/`_ipps._tcp`) → nếu máy
   in hỗ trợ **IPP Everywhere** (chuẩn Apple AirPrint/Mopria mở rộng, hầu
   hết máy in mạng sản xuất sau ~2015–2017 đều có) → `cups-browsed` tự tạo
   hàng in CUPS **driverless** (không cần PPD/driver riêng) — người dùng mở
   máy in trong ứng dụng, thấy tên máy, in luôn.
2. **Máy in cắm USB:** `ipp-usb` (đã có ở `0500-print.list.chroot`) dò qua
   udev khi cắm — nếu máy in hỗ trợ **IPP-over-USB** (hầu hết máy in/MFP
   USB đời mới của HP/Canon/Epson/Brother có hỗ trợ), `ipp-usb` biến cổng
   USB thành một "máy chủ IPP cục bộ" ảo → CUPS thấy như một máy in IPP
   driverless, in được **không cần driver theo hãng**.
3. **Máy không hỗ trợ driverless (đời cũ hơn, hoặc hãng chưa làm chuẩn này):**
   cần một **driver CUPS/PPD theo hãng hoặc theo chip** — đây là lớp dự
   phòng, chi tiết theo hãng ở bảng §2 dưới.
4. **Máy hoàn toàn không có driver mã nguồn mở nào khớp:** người dùng vẫn
   có thể tự tải driver .deb/.rpm từ trang hãng (ví dụ Canon UFR II, một số
   Brother đời mới) và cài tay — NaMiOS KHÔNG tự làm bước này (không tải
   phần mềm từ xa lúc build theo nguyên tắc an toàn của dự án), chỉ cung cấp
   `system-config-printer`/`print-manager` để người dùng trỏ PPD đã tải về.

## 2. Ma trận theo hãng

| Hãng | Driverless (IPP Everywhere/AirPrint/Mopria, không cần driver) | Driver mã nguồn mở có sẵn trong NaMiOS | Khi nào vẫn cần driver riêng của hãng (người dùng tự cài) |
| --- | --- | --- | --- |
| **Canon** | Hầu hết máy in/MFP mạng và USB sản xuất ~2016 trở lại (dòng PIXMA/MAXIFY mới, MFP văn phòng mới) hỗ trợ IPP Everywhere — tự in qua `cups-browsed`/`ipp-usb`, không cần driver. | `printer-driver-all`/`printer-driver-gutenprint` (đã có ở `0500`/`0680`) có PPD cho một số dòng Canon cũ qua Gutenprint/Foomatic — **KHÔNG đầy đủ**, Canon không có một driver "chính hãng" nào đóng gói sẵn trong Debian. | Máy in laser UFR II (dòng LBP/MF văn phòng), một số scanner MFP cần `cnijfilter2`/UFR II LT driver của Canon — tải trực tiếp từ trang hỗ trợ Canon VN, cài bằng `.deb` hoặc script cài của hãng (ngoài phạm vi NaMiOS). |
| **HP** | Hầu hết máy in/MFP mạng và USB hỗ trợ IPP Everywhere (HP là hãng tích cực nhất với chuẩn này). | `hplip` + `hplip-gui` (đã có ở `0680`) — bộ driver ĐẦY ĐỦ nhất trong ma trận này: in (`hpcups`) + PostScript (`printer-driver-postscript-hp`, mới thêm ở `0700`) + quét (`libsane-hpaio`, SANE backend riêng cho máy AIO cũ/USB không driverless) + fax tích hợp một số model AIO (`hp-sendfax`, chưa kiểm chứng). | Rất hiếm — HPLIP phủ gần hết dòng HP tiêu dùng/văn phòng. Một vài máy in rất mới có thể cần cập nhật `hplip` lên bản mới hơn bản đóng gói trong Debian trixie (hãng ra máy mới nhanh hơn chu kỳ đóng gói Debian). |
| **Brother** | Nhiều máy in/MFP mạng đời mới hỗ trợ IPP Everywhere. | `printer-driver-brlaser` (mới thêm ở `0700`) — driver mã nguồn mở (reverse-engineered) cho **nhiều máy in LASER ĐEN TRẮNG** Brother phổ biến (dòng HL-xxxx, DCP-xxxx) — không chính thức từ Brother nhưng được cộng đồng Linux dùng rộng rãi, ổn định với máy laser cơ bản. | Máy in **màu**, máy phun (inkjet) Brother, và nhiều dòng MFP có scan/fax tích hợp — brlaser CHỈ lo phần in đen trắng cơ bản, KHÔNG có driver quét/fax mã nguồn mở cho Brother trong Debian. Cần driver `.deb` của Brother (trang hỗ trợ Brother VN có gói riêng theo từng model) cho các tính năng này. |
| **Panasonic** | Một số dòng MFP văn phòng mới có IPP Everywhere (ít phổ biến hơn 4 hãng trên ở thị trường tiêu dùng). | KHÔNG có driver "Panasonic" riêng trong Debian. Máy in laser Panasonic đời cũ thường dùng PCL/PostScript chuẩn chung — có thể in được qua PPD generic PostScript/PCL đi kèm `cups-filters`/`printer-driver-all` (không đảm bảo — tuỳ model có tuân thủ chuẩn PCL/PS phổ thông hay không). | Hầu hết trường hợp thực tế — Panasonic không duy trì driver Linux chính thức cho dòng máy in văn phòng; nếu máy không driverless và không dùng PCL/PS chuẩn, NaMiOS không có cách tự động nào để in. |
| **LG** | Chưa xác nhận — LG không còn là hãng máy in tích cực ở thị trường hiện tại (các model LG từng bán tại VN phần lớn là máy cũ, một số là máy OEM gắn nhãn LG dựa trên engine của hãng khác). Nếu model có IPP Everywhere, luồng driverless vẫn áp dụng như trên. | KHÔNG có driver "LG" riêng trong Debian/Linux nói chung — đây là một lỗ hổng thật, không phải thiếu sót trong gói. | Gần như luôn cần — nếu máy LG không driverless, khả năng in được qua NaMiOS (hoặc qua bất kỳ bản Linux nào) là THẤP trừ khi máy dùng chuẩn PCL/PS phổ thông. Đây là hãng duy nhất trong yêu cầu của Cuong mà nhóm cần cân nhắc test thật sớm để biết mức độ rủi ro. |
| **Epson** *(đã có sẵn trong yêu cầu "các hãng phổ biến" trước đó, liệt kê lại để đối chiếu đầy đủ)* | Nhiều máy in/MFP mạng đời mới hỗ trợ IPP Everywhere. | `printer-driver-escpr` (đã có ở `0680`) — driver ESC/P-R do chính Epson phát hành mã nguồn (không hoàn toàn "mở" theo nghĩa cộng đồng viết lại, nhưng được đóng gói hợp lệ trong Debian main) — phủ phần lớn máy in phun Epson phổ biến. | Một số máy in nhãn mực rời (EcoTank) đời rất mới hoặc máy chuyên dụng ảnh có thể cần `epson-inkjet-printer-escpr2` — package này KHÔNG có trong Debian, phải tải trực tiếp từ Epson (ngoài phạm vi NaMiOS). |
| **Samsung** | Máy in Samsung hiện do HP sở hữu mảng in (HP mua lại bộ phận máy in Samsung năm 2017) — máy đời mới có thể hoạt động qua `hplip`. | Máy Samsung cũ hơn (trước sáp nhập HP): không có driver mã nguồn mở riêng trong 0700; một số model laser cũ dùng chip ZjStream có thể khớp với `printer-driver-foo2zjs` (mới thêm ở `0700`) — KHÔNG đảm bảo khớp đúng model. | Driver "Unified Linux Driver" cũ của Samsung đã ngừng phát hành/khó tải — máy rất cũ có rủi ro không in được qua Linux nói chung, không riêng NaMiOS. |
| **Xerox** | Nhiều máy in/MFP văn phòng Xerox đời mới hỗ trợ IPP Everywhere/AirPrint (Xerox khá tích cực với chuẩn mở). | Không có driver "Xerox" riêng trong ma trận `0700` hiện tại — máy không driverless phải dựa vào PPD generic PostScript (nhiều máy Xerox văn phòng hỗ trợ PostScript thật tốt, nên khả năng in qua PPD chung khá cao, nhưng chưa kiểm chứng). | Driver `.deb`/`.ppd` dành riêng của Xerox cho một số model workflow phức tạp (scan-to-email, fax tích hợp) — ngoài phạm vi gói build sẵn. |

## 3. Vì sao chọn đúng các gói mới trong `0700-printing.list.chroot`

| Gói | Vai trò | Hãng/nhóm được phủ thêm |
| --- | --- | --- |
| `cups-client` | Lệnh CLI (`lp`, `lpstat`, `lpoptions`) — thiếu ở `0500` (chỉ có scheduler). | Mọi hãng (hạ tầng, không riêng hãng nào). |
| `cups-browsed` | Tiến trình dò máy in mạng driverless qua DNS-SD — tách gói riêng từ `cups-filters` 1.28, KHÔNG tự có khi chỉ cài `cups`/`cups-filters`. | Mọi hãng hỗ trợ IPP Everywhere (phần lớn Canon/HP/Brother/Epson/Xerox đời mới). |
| `printer-driver-brlaser` | Driver laser đen trắng mã nguồn mở cho Brother. | **Brother.** |
| `printer-driver-foo2zjs` | Driver cho máy laser dùng chip ZjStream (một phần Samsung cũ, Minolta/QMS, Oki, một số HP LaserJet cũ). | Lớp "máy laser rẻ đời cũ" nói chung, có thể khớp một phần Samsung. |
| `printer-driver-postscript-hp` | PPD PostScript chính thức cho HP (khác driver raster `hpcups` mà `hplip` kéo theo). | **HP** (bổ sung, không phải hãng mới). |
| `printer-driver-cups-pdf` | Hàng in ảo "In ra PDF" — không phụ thuộc hãng. | Mọi hãng (và cả khi không có máy in vật lý nào). |
| `avahi-utils` | Lệnh chẩn đoán `avahi-browse`/`avahi-resolve` — trả lời "có thấy máy in quảng bá mDNS không" trước khi đổ lỗi driver. | Mọi hãng (chẩn đoán). |
| `system-config-printer` | GUI cấu hình máy in cổ điển, độc lập desktop — dự phòng cho `print-manager` (KDE) khi cần chọn PPD thủ công chi tiết hơn. | Mọi hãng (đặc biệt hữu ích cho Panasonic/LG/Xerox — các hãng cần chọn PPD generic PostScript/PCL thủ công). |
| `simple-scan` | GUI quét đơn giản, độc lập desktop — dự phòng cho `skanlite` (KDE). | Mọi hãng có scanner (không riêng hãng nào). |

## 4. Archive area — non-free/contrib (ghi chú cho người giữ `auto/config`)

Đã kiểm tra `distro/live-build/auto/config`: `lb config` hiện gọi với
`--archive-areas "main contrib non-free-firmware"` — **đã bật `contrib` và
`non-free-firmware`**, nhưng **CHƯA bật `non-free`** (khu vực khác
`non-free-firmware` — `non-free-firmware` chỉ chứa firmware/blob thiết bị,
không chứa phần mềm ứng dụng độc quyền). File đó đã tồn tại từ trước, do
một luồng khác của dự án phụ trách — hook/package-list trong tài liệu này
**KHÔNG sửa file đó**, chỉ ghi nhận ở đây để người giữ file đó biết lý do
nếu cần.

Toàn bộ 9 gói mới trong `0700-printing.list.chroot` (cups-client,
cups-browsed, printer-driver-brlaser, printer-driver-foo2zjs,
printer-driver-postscript-hp, printer-driver-cups-pdf, avahi-utils,
system-config-printer, simple-scan) nằm trong khu vực **`main`** của Debian
trixie (đã đối chiếu qua `madison.php` đích `trixie` — xác nhận có bản cho
trixie, KHÔNG xác nhận khu vực `main` riêng từng gói qua lệnh `apt-cache
show` thật, vì môi trường viết tài liệu này không có mirror apt trixie).
**KHÔNG có gói in ấn nào trong danh sách này cần `non-free` hay
`non-free-firmware`.**

Phần mềm cần `non-free` thật sự (nếu có) sẽ là **driver độc quyền của
chính hãng** mà Debian không đóng gói lại được (ví dụ driver UFR II của
Canon, driver proprietary cũ của Samsung, plugin nhị phân HP qua
`hp-plugin`) — những thứ này **KHÔNG nằm trong kho apt Debian ở bất kỳ khu
vực nào** (main/contrib/non-free/non-free-firmware), chúng được tải trực
tiếp từ website hãng, nên việc bật/tắt `non-free` không ảnh hưởng đến chúng.

## 5. Việc cần làm trên phần cứng thật trước khi công bố "hỗ trợ"

Theo đúng quy ước dự án (`docs/STATUS-U13-KIEM-KE.md` §"Quy ước trạng
thái"): không nâng trạng thái lên `partial`/`completed` chỉ vì thêm gói.
Cần, tối thiểu:

1. Một máy in driverless (IPP Everywhere/AirPrint) của **một hãng bất kỳ**
   cùng mạng LAN — xác nhận hàng in tự xuất hiện trong vài giây sau khi
   NaMiOS boot/kết nối mạng, không cần thao tác tay (xác nhận luồng ở §1.1).
2. Một máy in USB driverless (IPP-over-USB) — xác nhận `ipp-usb` tự dò khi
   cắm (luồng §1.2).
3. **Ít nhất một máy Brother laser** (để xác nhận `printer-driver-brlaser`
   hoạt động thật — đây là gói MỚI, rủi ro cao nhất chưa test).
4. **Ít nhất một máy LG** nếu đội có quyền truy cập — để biết thật mức rủi
   ro của hãng này (bảng §2 đánh dấu "chưa xác nhận").
5. Một máy Panasonic hoặc Xerox dùng PCL/PostScript thuần (không driverless)
   — xác nhận PPD generic có in được hay không, hay cần
   `system-config-printer` chọn PPD thủ công.

Không có bước nào trong tài liệu này thay thế được pilot trên phần cứng
thật — đây là tài liệu "có gì trong repo + lý do kỹ thuật", không phải "đã
test xong".
