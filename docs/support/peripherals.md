# Ma trận hỗ trợ ngoại vi NaMiOS (U13-06)

**Trạng thái thật:** `specified` — có cấu hình/gói/công cụ trong repo cho mọi
hàng dưới đây; **CHƯA có bất kỳ model máy in/máy quét/máy fax/thiết bị
Bluetooth/card Wi-Fi/USB nào được test trên phần cứng thật**. Theo nguyên tắc
chung của dự án (xem `docs/STATUS-U13-KIEM-KE.md` §"Quy ước trạng thái"):
*"Nếu không có artifact chạy trên máy thật, trạng thái vẫn là `specified`,
không phải `completed`."* **Ngày:** 09/11/2026.

**Nguồn yêu cầu:** `docs/spec-package/NaMiOS_Phu_luc_13_Uu_tien_Nang_cap_va_Cong_Phat_hanh.md`
§2 dòng U13-06 — *"Wi-Fi, Ethernet, Bluetooth HID/audio, USB, 3–5 printer/MFP
được chọn từ khảo sát"*; cửa kiểm chứng: *"Mỗi model có ca in/scan/kết nối
thực, lỗi và mức hỗ trợ theo chức năng."* Cũng xem §2.1: *"Âm thanh, camera,
micro... Pin, ngủ/đánh thức... Mất mạng/âm thanh sau resume là lỗi P0 của
U13-01/U13-06."*

**Công cụ liên quan:**
`distro/live-build/config/includes.chroot/usr/local/bin/namios-ket-noi-thiet-bi`
(launcher `usr/share/applications/namios-ket-noi-thiet-bi.desktop`) — mở đúng
công cụ hệ thống theo loại thiết bị người dùng chọn. Gói phần mềm nền xem
`distro/live-build/config/package-lists/0150-system-firmware.list.chroot`,
`0160-network.list.chroot`, `0170-audio.list.chroot`,
`0180-bluetooth-power-time.list.chroot`, `0190-storage.list.chroot`,
`0500-print.list.chroot`, `0680-peripherals-extra.list.chroot`.

## 0. Vì sao vẫn chỉ `specified` dù "có vẻ đủ gói"

QEMU (môi trường phát triển hiện tại) **không có** card Wi-Fi, modem fax,
radio Bluetooth, máy in, máy quét hay cổng USB vật lý nào để gắn thiết bị
thật — mọi dòng "có gói X" dưới đây nghĩa là **tên gói tồn tại thật trong kho
Debian trixie và có lý do kỹ thuật để chọn**, KHÔNG phải "đã thấy chạy được".
Cửa kiểm chứng U13-06 (*"Mỗi model có ca in/scan/kết nối thực"*) chỉ đóng được
bằng pilot trên máy/thiết bị thật — xem §5 "Việc cần làm trên phần cứng
thật" bên dưới. Không hứa với người dùng cuối rằng một thiết bị "chắc chắn
chạy" chỉ vì driver có trong danh sách gói.

## Hướng dẫn nhanh cho người dùng (không cần đọc phần kỹ thuật dưới)

Mục này dành cho người KHÔNG rành kỹ thuật — chỉ cần làm theo, không cần hiểu
IPP/driverless/eSCL là gì (những thứ đó giải thích Ở DƯỚI, cho người kiểm
thử/IT). Mở ứng dụng **"Kết nối thiết bị"** (tìm trong menu ứng dụng, gõ
"kết nối" hoặc "thiết bị" để tìm nhanh) — hiện ra một menu, chọn đúng mục:

- **Thêm máy in:** chọn mục "Máy in". Các bước: (1) Cắm dây máy in vào máy
  (máy in mạng thì chỉ cần cùng Wi-Fi, không cần cắm dây) → (2) chờ vài giây
  → (3) bấm "Thêm máy in" trong cửa sổ hiện ra → (4) chọn tên máy in hiện ra
  trong danh sách → Xong. Phần lớn máy in USB/mạng đời mới (khoảng 2015 trở
  lại) tự hiện tên, không cần cài driver riêng. Cách nhanh hơn: chuột phải
  (hoặc nhấn giữ) vào icon ứng dụng "Kết nối thiết bị" ở menu/taskbar → chọn
  thẳng **"Thêm máy in"** — vào ngay màn hình thêm máy in, không cần qua menu
  7 mục. Chi tiết theo từng hãng máy in: xem `docs/support/PRINTING.md`.
- **Quét tài liệu (scan):** chọn mục "Máy quét". Công cụ tự dò máy quét
  trước khi mở cửa sổ quét — nếu báo không thấy, kiểm tra máy quét đã bật và
  cùng mạng Wi-Fi (máy mạng) hoặc đã cắm chắc cáp USB.
- **Cắm ổ USB (USB di động, ổ cứng rời...):** chọn mục "USB" để xem máy đã
  nhận cổng USB chưa (dùng khi nghi máy không nhận). Thường thì KHÔNG cần mở
  công cụ này — ổ USB tự hiện trong Dolphin (trình quản lý file), khung bên
  trái, mục "Thiết bị", vài giây sau khi cắm.
- **Cắm điện thoại Android để chép ảnh/file:** chọn mục "Điện thoại (MTP)".
  Trên điện thoại, chọn chế độ "Truyền tệp / File transfer" (KHÔNG chọn "Chỉ
  sạc") khi được hỏi → Dolphin tự hiện điện thoại sau vài giây. (iPhone
  KHÔNG dùng cách này — xem §6 dưới.)

Nếu công cụ báo **"Chưa cài: ..."**, nghĩa là phần mềm đó chưa có sẵn trên
máy — đây không phải lỗi của bạn, hãy báo IT/hỗ trợ thay vì tự cài lại.

## 1. Máy in

| Hạng mục | Có gì trong repo | Mức hỗ trợ dự kiến | Giới hạn thật |
| --- | --- | --- | --- |
| Hạ tầng in (CUPS) | `cups`, `cups-filters`, `print-manager`, `printer-driver-all` (`0500-print.list.chroot`) | Máy in mạng IPP/AirPrint/Mopria và máy in USB driverless thường tự dò được (driverless = không cần PPD riêng). | Chưa xác nhận tự dò hoạt động thật trên mạng/USB thật nào. |
| Driver theo hãng | `printer-driver-gutenprint`, `printer-driver-escpr` (Epson), `hplip`+`hplip-gui` (HP) — khai báo tường minh ở `0680-peripherals-extra.list.chroot` vì `printer-driver-all` chỉ **Recommends** (không Depends) các driver này và dự án **chưa xác nhận** `lb build` có bật cài Recommends hay không (xem `docs/l10n/UPSTREAM-VI-OVERLAY-SPEC.md` §5.1 "cần xác minh khi build"). | Canon dùng driver mã nguồn mở có sẵn trong `printer-driver-all` (không cần gói riêng); Epson qua `escpr`; HP qua `hplip` (gồm cả SANE backend quét `libsane-hpaio`). | Canon/Epson/HP là ba hãng phổ biến nhất ở văn phòng/gia đình Việt Nam theo quan sát thị trường, **không phải kết quả khảo sát 3–5 model** mà U13-06 yêu cầu — khảo sát đó **chưa làm** (xem `docs/STATUS-U13-KIEM-KE.md` dòng U13-06: *"3-5 model máy in từ khảo sát: chưa chọn"*). |
| Giao diện quản lý | `kde-add-printer`, `kde-print-queue` (gói `print-manager`) | Thêm/xoá máy in, xem hàng đợi in bằng GUI tiếng Việt qua `namios-ket-noi-thiet-bi`. | Chưa test luồng "thêm máy in" thật trên máy nào. |

**Cần test trên model thật (theo U13-06):** chọn 3–5 model máy in/MFP theo
khảo sát thật (không phải đoán theo hãng phổ biến), với mỗi model: in một
trang test, in PDF có dấu tiếng Việt, in hai mặt nếu máy hỗ trợ, và — nếu là
máy đa chức năng — ca quét (xem mục 2). Ghi lại ảnh bản in + log lỗi nếu có.

## 2. Máy quét (scan)

| Hạng mục | Có gì trong repo | Mức hỗ trợ dự kiến | Giới hạn thật |
| --- | --- | --- | --- |
| Quét qua mạng | `sane-airscan` (eSCL/AirScan), `avahi-daemon`, `libnss-mdns` (`0500-print.list.chroot`) | Máy đa chức năng đời mới hỗ trợ eSCL (chuẩn "driverless scan" của Apple/Mopria) tự được dò qua mạng. | Máy cũ không hỗ trợ eSCL sẽ KHÔNG được dò bằng đường này. |
| Quét HP qua USB/cũ | `hplip` → kéo theo `libsane-hpaio` (`0680-peripherals-extra.list.chroot`) | Backend SANE riêng của HP cho máy không hỗ trợ eSCL. | Chưa test — HPLIP cần `hp-setup` chạy lần đầu trên một số model, chưa xác nhận bước này hoạt động tự động. |
| Giao diện quét | `skanlite` (`0500-print.list.chroot`) | GUI quét tiếng Việt (ngôn ngữ theo hệ thống) qua `namios-ket-noi-thiet-bi`. | Chưa test quét ra file PDF/ảnh thật nào. |
| Chẩn đoán | `sane-utils` (lệnh `scanimage -L`, đã có ở `0500`) | `namios-ket-noi-thiet-bi` chạy lệnh này trước khi mở GUI để báo máy có thấy scanner hay không. | Không thay thế được test thật — chỉ cho biết "thấy ở tầng driver", không đảm bảo ảnh quét đúng màu/đúng khổ giấy. |

**Cần test trên model thật:** với mỗi máy đa chức năng trong 3–5 model đã
chọn ở mục 1 — quét một trang có chữ tiếng Việt có dấu, kiểm tra file ra đúng
khổ giấy (A4) và không lệch màu.

## 3. Máy fax

| Hạng mục | Có gì trong repo | Mức hỗ trợ dự kiến | Giới hạn thật |
| --- | --- | --- | --- |
| Phần mềm fax | `efax` (`0680-peripherals-extra.list.chroot`) — xem file đó để biết lý do chọn `efax` thay vì `efax-gtk` (không tồn tại trong Debian trixie) hoặc `hylafax-client` (cần thêm `hylafax-server` chạy cục bộ, nặng hơn nhiều, thiết kế cho máy chủ fax dùng chung). | Gửi/nhận fax G3 bằng dòng lệnh (`fax send`, `fax answer`) **qua modem fax thật cắm USB/serial**. | **KHÔNG hỗ trợ fax qua Internet/email-to-fax, KHÔNG fax qua máy in thường.** Cần đúng loại modem fax analog (hiếm ở Việt Nam hiện nay — hầu hết văn phòng đã chuyển sang máy đa chức năng HP/Brother có fax tích hợp hoặc dịch vụ fax qua email của nhà mạng). |
| Fax tích hợp trên máy đa chức năng HP | `hplip` có công cụ `hp-sendfax` cho một số model HP AIO có modem fax phần cứng tích hợp. | Nếu model HP đã chọn có fax tích hợp, có thể gửi fax qua `hp-sendfax` thay vì modem rời. | **Hoàn toàn chưa xác minh** — chưa có model HP AIO fax thật nào để test; tài liệu HPLIP nói có tính năng này nhưng NaMiOS chưa chạy thử. |
| Giao diện | Không có GUI fax trong kho gói Debian trixie. `namios-ket-noi-thiet-bi` hiển thị hướng dẫn tiếng Việt + lệnh thật (không giả vờ có nút bấm không tồn tại). | Người dùng cần sửa `/etc/efax.rc` (quyền quản trị) để trỏ đúng thiết bị modem trước khi dùng lần đầu. | Đây là bước cấu hình thủ công, không "cắm là chạy" như Windows thường quảng cáo — cần ghi rõ với người dùng cuối, không hứa quá. |

**Cần test trên model thật:** đây là hạng mục RỦI RO CAO NHẤT trong U13-06 vì
chưa rõ dự án có modem fax thật hoặc máy đa chức năng có fax để test hay
không. Nếu đội pilot không có thiết bị fax thật, nên công bố fax ở mức
"hỗ trợ lý thuyết qua `efax`, chưa kiểm chứng" thay vì liệt kê như đã xong.

## 4. Bluetooth

| Hạng mục | Có gì trong repo | Mức hỗ trợ dự kiến | Giới hạn thật |
| --- | --- | --- | --- |
| Stack lõi | `bluez` (`0180-bluetooth-power-time.list.chroot`) | Driver/daemon Bluetooth chuẩn của Linux. | Phụ thuộc chip Bluetooth của từng máy có driver kernel mã nguồn mở hay không — chưa kiểm trên máy thật nào. |
| Ghép nối + GUI | `bluedevil` (`0180`) — nhị phân `bluedevil-wizard` dùng trực tiếp trong `namios-ket-noi-thiet-bi` | Ghép nối tai nghe/loa/bàn phím/chuột qua trình hướng dẫn GUI tiếng Việt (theo hệ thống). | Chưa test ghép nối với bất kỳ thiết bị HID/audio Bluetooth thật nào. |
| Audio Bluetooth | `libspa-0.2-bluetooth` (`0170-audio.list.chroot`, plugin PipeWire) | Phát nhạc/thoại qua tai nghe/loa Bluetooth sau khi ghép nối. | §2.1 Phụ lục 13 yêu cầu rõ: *"loa, tai nghe Bluetooth... phải qua test họp/học trực tuyến 45 phút"* — **chưa làm**. |

**Cần test trên model thật:** 2 thiết bị Bluetooth theo yêu cầu dữ liệu M0
(§4 Phụ lục 13: *"2 thiết bị Bluetooth"*) — tối thiểu một tai nghe/loa (audio
profile) và một bàn phím/chuột (HID profile), mỗi loại ghép nối + dùng thật
45 phút liên tục (cuộc gọi/họp) để bắt lỗi rớt kết nối.

## 5. Wi-Fi

| Hạng mục | Có gì trong repo | Mức hỗ trợ dự kiến | Giới hạn thật |
| --- | --- | --- | --- |
| Firmware chip Wi-Fi | `firmware-iwlwifi` (Intel), `firmware-realtek`, `firmware-atheros`, `firmware-brcm80211` (Broadcom), `firmware-mediatek`, `wireless-regdb` (`0150-system-firmware.list.chroot`) | Phủ phần lớn chipset Wi-Fi laptop/PC phổ biến (Intel/Realtek/Qualcomm Atheros/Broadcom/MediaTek). | Danh sách firmware KHÔNG đồng nghĩa "mọi card Wi-Fi chạy" — một số chip rất mới hoặc rất hiếm (driver độc quyền ngoài Debian) vẫn có thể không chạy. Chưa test trên máy thật nào. |
| Kết nối + GUI | `network-manager`, `wpasupplicant`, `iw`, `modemmanager` (`0160-network.list.chroot`) + `plasma-nm` (`0100-desktop-kde.list.chroot`, cung cấp KCM `kcm_networkmanagement`, dùng trong `namios-ket-noi-thiet-bi`) | Kết nối Wi-Fi WPA2/WPA3 qua GUI tiếng Việt (icon khay hệ thống hoặc qua công cụ Kết nối thiết bị). | Chưa test kết nối Wi-Fi thật, chưa test cổng Wi-Fi công cộng (captive portal) nào. |
| Mất mạng sau ngủ/đánh thức | Không có cơ chế riêng trong `0680`; đây là hạng mục của U13-01/U13-06 theo §2.1 Phụ lục 13. | Không có gì đảm bảo tự kết nối lại sau khi máy ngủ/thức dậy. | §2.1: *"Mất mạng/âm thanh sau resume là lỗi P0"* — **chưa test, chưa có fix riêng.** |

**Cần test trên model thật:** đo trên máy cũ, máy mới, có dock, hai màn hình
theo đúng yêu cầu §2.1 Phụ lục 13; đặc biệt kiểm Wi-Fi có tự nối lại sau khi
đóng/mở nắp laptop (sleep/resume) hay không.

## 6. USB (lưu trữ, MTP điện thoại, thiết bị khác)

| Hạng mục | Có gì trong repo | Mức hỗ trợ dự kiến | Giới hạn thật |
| --- | --- | --- | --- |
| Ổ USB (lưu trữ) | `udisks2`, `ntfs-3g`, `exfatprogs`, `dosfstools`, `kio-fuse` (`0190-storage.list.chroot`) | Tự nhận diện + gắn (mount) ổ USB định dạng NTFS/exFAT/FAT32 (ba định dạng phổ biến nhất từ Windows) khi cắm vào, hiện trong Dolphin. | Chưa test cắm ổ USB thật nào; chưa test ổ USB được mã hoá (BitLocker To Go) — khả năng cao KHÔNG đọc được, chưa xác nhận. |
| Chẩn đoán tầng bus | `usbutils` (`lsusb`, `0680-peripherals-extra.list.chroot`) | `namios-ket-noi-thiet-bi` hiện danh sách thiết bị USB đang cắm trước khi mở Dolphin — tách bạch "máy không thấy thiết bị" khỏi "thấy nhưng không mount". | Chỉ là công cụ chẩn đoán, không tự sửa lỗi. |
| Điện thoại (MTP) | `kio-extras` (`0160-network.list.chroot`, đã có sẵn plugin `mtp://` + hành động Solid tự mount trong Dolphin — xác nhận bằng cách đối chiếu danh sách file của gói với chỉ mục Contents chính thức của trixie) + `mtp-tools` (`mtp-detect`, lớp chẩn đoán dự phòng, `0680`) | Cắm điện thoại Android, chọn "Truyền tệp/File transfer" trên điện thoại → Dolphin tự hiện điện thoại. | Chưa test với điện thoại Android thật nào; iPhone KHÔNG dùng MTP (dùng AFC riêng của Apple) — **không được hứa hỗ trợ iPhone qua luồng này**. |

**Cần test trên model thật:** 2 loại USB token nếu có quyền test (yêu cầu dữ
liệu M0 §4 Phụ lục 13), một ổ USB NTFS/exFAT/FAT32 thật mỗi loại, và tối
thiểu một điện thoại Android thật ở chế độ MTP.

## 7. Tổng kết — không có thiết bị nào "đã xong"

| Nhóm | Gói/công cụ | Trạng thái | Việc còn thiếu để lên `partial` |
| --- | --- | --- | --- |
| Máy in | §1 | `specified` | Chọn 3–5 model theo khảo sát thật + in thử. |
| Máy quét | §2 | `specified` | Quét thử trên máy đa chức năng thật. |
| Máy fax | §3 | `specified`, RỦI RO CAO | Xác định có modem/MFP-fax thật để test hay không; nếu không có, công bố rõ "chưa kiểm chứng". |
| Bluetooth | §4 | `specified` | Ghép nối + test 45 phút với ≥2 thiết bị thật (audio + HID). |
| Wi-Fi | §5 | `specified` | Kết nối thật trên ≥5 máy pilot (theo M0), test sleep/resume. |
| USB/MTP | §6 | `specified` | Cắm thử ổ USB + điện thoại Android thật. |

Không một dòng nào trong bảng trên được nâng lên `partial`/`completed` chỉ vì
thêm gói hoặc thêm script — chỉ nâng lên khi có bằng chứng chạy thật (ảnh/
log) theo đúng quy ước `docs/STATUS-U13-KIEM-KE.md`.
