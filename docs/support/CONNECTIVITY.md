# Ma trận chuẩn/codec kết nối Bluetooth + Wi-Fi NaMiOS

**Trạng thái thật:** `specified` — có cấu hình/gói trong repo cho mọi hạng
mục dưới đây; **CHƯA có bất kỳ adapter/chip Bluetooth hoặc Wi-Fi thật nào
được test**. Theo nguyên tắc chung của dự án (`docs/STATUS-U13-KIEM-KE.md`
§"Quy ước trạng thái"): *"Nếu không có artifact chạy trên máy thật, trạng
thái vẫn là `specified`, không phải `completed`."* **Ngày:** 09/11/2026.

**Yêu cầu nguồn:** Cuong — *"Bluetooth kết nối hết các chuẩn định dạng. Wifi
cũng vậy."* Cũng đối chiếu với các mã yêu cầu đã có trong
`docs/specs/DAC_TA_HE_DIEU_HANH.md`: HW-002 (*test Wi-Fi/Bluetooth khi có*),
DEV-004 (*mở rộng hồ sơ thiết bị Wi-Fi/Bluetooth, test kết nối/rút nóng/
sleep-resume*), DEV-007 (*"Máy bị mất Wi-Fi... sau cập nhật là lỗi chặn phát
hành tới model được chứng nhận"*), và LIC-006 (*phải ghi rõ thành phần
không tự do, không quảng bá toàn hệ thống là phần mềm tự do*).

**Tài liệu liên quan — KHÔNG trùng, đọc cả hai:**
- `docs/support/peripherals.md` §4 (Bluetooth) + §5 (Wi-Fi) — ma trận THEO
  THIẾT BỊ (tai nghe/HID cụ thể, chip cụ thể), có bảng trạng thái tổng kết
  §7 và kế hoạch test pilot. File này (CONNECTIVITY.md) là ma trận THEO
  CHUẨN/CODEC/PROFILE — bổ sung chi tiết kỹ thuật, không lặp bảng trạng thái.
- `distro/live-build/config/package-lists/0720-connectivity.list.chroot` —
  gói mới thêm cho nhiệm vụ này, có comment giải thích từng lựa chọn.
- `distro/live-build/auto/config` — nơi mở archive area `non-free` (xem §4
  dưới đây).

## 0. Nguyên tắc trung thực (đọc trước khi hứa gì với người dùng)

Danh sách gói/firmware dưới đây **tối đa hoá khả năng tương thích** bằng
cách phủ hầu hết chip Bluetooth/Wi-Fi phổ biến (Intel, Realtek, Qualcomm
Atheros, Broadcom, MediaTek, Marvell Libertas, Texas Instruments) và hầu hết
hồ sơ/codec chuẩn của BlueZ + PipeWire. **KHÔNG CÓ HỆ ĐIỀU HÀNH NÀO đảm bảo
MỌI thiết bị kết nối được** — chip rất mới (driver chưa lên kernel 6.12 của
trixie), chip rất hiếm/độc quyền ngoài Debian, hoặc phần cứng lỗi vẫn có thể
không chạy. **Cửa kiểm chứng cuối cùng = pilot trên phần cứng thật** (nhóm B
theo kế hoạch kiểm thử dự án), không phải danh sách gói trong file này.
Không công bố với người dùng cuối rằng "Bluetooth/Wi-Fi NaMiOS hỗ trợ mọi
chuẩn/mọi thiết bị" — chỉ nói đúng những gì đã kiểm chứng.

## 1. Bluetooth — hồ sơ (profile) và codec

Stack: BlueZ (`bluez`, `bluez-tools`, `bluez-obexd`) + GUI kép (`bluedevil`
cho KDE, `blueman` dự phòng) + PipeWire/SPA (`libspa-0.2-bluetooth`) cho
audio.

| Hồ sơ/codec | Gói cấp | Mức phủ dự kiến | Giới hạn thật |
| --- | --- | --- | --- |
| A2DP — SBC | `libspa-0.2-bluetooth` (phụ thuộc `libsbc1`, có sẵn trong `main`) | Codec BẮT BUỘC của chuẩn A2DP — mọi tai nghe/loa Bluetooth stereo đều hỗ trợ tối thiểu SBC. | Chất lượng thấp nhất trong các codec liệt kê ở đây; luôn là phương án cuối nếu không thương lượng được codec tốt hơn. |
| A2DP — aptX / aptX-HD | `libspa-0.2-bluetooth` (phụ thuộc `libfreeaptx0`, có sẵn trong `main`, KHÔNG cần mở thêm archive area) | Dựng sẵn trong PipeWire của trixie — không cần cấu hình thêm. | Thiết bị phát (tai nghe/loa) phải hỗ trợ aptX/aptX-HD — nhiều thiết bị giá rẻ chỉ có SBC. Chưa test ghép nối thật. |
| A2DP — LDAC | `libspa-0.2-bluetooth` (phụ thuộc `libldacbt-enc2`, `libldacbt-abr2`, có sẵn trong `main`) | Dựng sẵn trong PipeWire của trixie — không cần cấu hình thêm. | Chủ yếu dùng trên thiết bị Sony/Android cao cấp; thiết bị không hỗ trợ sẽ tự rơi về SBC/aptX. Chưa test ghép nối thật. |
| A2DP — AAC | `libfdk-aac2t64` (`0720-connectivity.list.chroot`, khu vực `non-free`) | **Cần archive area `non-free`** (đã mở ở `auto/config`, xem §4). PipeWire/SPA được hiểu là dlopen() thư viện này ở runtime khi có mặt. | **CHƯA xác minh runtime thật** — chưa có cách kiểm chứng trực tiếp hành vi dlopen qua tài liệu nguồn (salsa.debian.org bị chặn khi soát) trong lần làm việc này; nếu không tải được/không dlopen thành công, hệ thống tự rơi về SBC (không lỗi, chỉ giảm chất lượng). Cần test bằng `pw-cli info` hoặc `pactl list sinks` với tai nghe AAC thật. |
| HFP/HSP (thoại/cuộc gọi qua tai nghe) | `bluez` + `libspa-0.2-bluetooth` | Đàm thoại qua tai nghe Bluetooth (voice call, cả mic) khi app hỗ trợ (ví dụ ứng dụng họp trực tuyến). | Chưa test cuộc gọi/họp 45 phút liên tục (yêu cầu §2.1 Phụ lục 13, xem `peripherals.md` §4). |
| HID (bàn phím/chuột Bluetooth) | `bluez` (BlueZ có HID profile tích hợp nhân) | Ghép nối bàn phím/chuột Bluetooth chuẩn. | Chưa test với bàn phím/chuột Bluetooth thật nào. |
| OBEX (truyền file qua Bluetooth) | `bluez-obexd` + GUI (`bluedevil`/`blueman`) | Gửi/nhận file giữa điện thoại và NaMiOS qua Bluetooth. | Chưa test truyền file thật với điện thoại nào. |
| PAN/NAP (chia sẻ mạng qua Bluetooth) | Có trong `bluez` nhưng KHÔNG có công cụ GUI riêng trong danh sách gói hiện tại. | Về lý thuyết `bluez` hỗ trợ; chưa có đường dẫn GUI tiếng Việt qua `namios-ket-noi-thiet-bi`. | CHƯA kiểm chứng, CHƯA có GUI — không hứa tính năng này hoạt động "cắm là chạy". |

## 2. Wi-Fi — chuẩn 802.11 và bảo mật

| Hạng mục | Cấp bởi | Mức phủ dự kiến | Giới hạn thật |
| --- | --- | --- | --- |
| Chuẩn 802.11 (a/b/g/n/ac/ax = Wi-Fi 4/5/6) | Kernel trixie `linux-image-amd64` 6.12.x + firmware tương ứng | Hỗ trợ tốt, driver mac80211 cho các chuẩn này đã ổn định nhiều năm trên kernel 6.x. | Phụ thuộc chip + firmware từng máy; vẫn cần đúng `firmware-*` tương ứng (xem §3). |
| Wi-Fi 6E (băng 6 GHz) | Kernel 6.12 + driver chip hỗ trợ 6 GHz (ví dụ Intel AX210/BE200, MediaTek MT7925) | Hỗ trợ VỀ MẶT KERNEL; thực tế chạy được hay không phụ thuộc chip + firmware + vùng quy định tần số (`wireless-regdb`, đã có ở `0150`). | CHƯA test băng 6 GHz trên adapter thật nào. |
| Wi-Fi 7 (802.11be) | Kernel 6.12 có hỗ trợ từng phần cho một số chip rất mới (Intel BE200, MediaTek MT7996/7925, một số chip Qualcomm/Atheros) | CHỈ hỗ trợ trên chip CÓ driver đã lên kernel 6.12 — KHÔNG phải mọi chip Wi-Fi 7 trên thị trường. | Đây là chuẩn rất mới (2024); danh sách chip được driver kernel 6.12 hỗ trợ đầy đủ còn ngắn và đang thay đổi theo từng bản kernel. KHÔNG hứa "hỗ trợ Wi-Fi 7" như một tính năng hoàn chỉnh. |
| Bảo mật WPA2 | `wpasupplicant` + `network-manager` (`0160`) | Hỗ trợ đầy đủ, chuẩn phổ biến nhất hiện nay. | Không có. |
| Bảo mật WPA3 | `wpasupplicant` (bản trong trixie hỗ trợ WPA3-Personal/SAE) + `network-manager` | Hỗ trợ WPA3-Personal (SAE) qua NetworkManager + wpasupplicant backend. | WPA3-Enterprise (192-bit) phức tạp hơn, CHƯA test; một số router WPA3 cũ/firmware lỗi có thể gây lỗi bắt tay — chưa kiểm chứng trên router thật nào. |
| GUI kết nối | `network-manager` + `plasma-nm` (`0100-desktop-kde.list.chroot`) + `network-manager-gnome` dự phòng (`0720`) | Kết nối Wi-Fi qua GUI tiếng Việt (khay hệ thống Plasma hoặc `namios-ket-noi-thiet-bi`). | Chưa test kết nối Wi-Fi thật, chưa test captive portal (cổng Wi-Fi công cộng cần đăng nhập web). |
| Chẩn đoán khoá radio | `rfkill` (`0720`) | Phát hiện/gỡ khoá cứng/mềm Wi-Fi/Bluetooth khi máy "không thấy" thiết bị dù đủ driver. | Chỉ là công cụ chẩn đoán dòng lệnh, chưa có GUI riêng. |

## 3. Firmware chip — phủ sóng theo hãng

| Hãng/chip | Gói firmware | File |
| --- | --- | --- |
| Intel (iwlwifi) | `firmware-iwlwifi` | `0150-system-firmware.list.chroot` |
| Realtek | `firmware-realtek` | `0150` |
| Qualcomm Atheros | `firmware-atheros` | `0150` |
| Broadcom | `firmware-brcm80211` | `0150` |
| MediaTek | `firmware-mediatek` | `0150` |
| Marvell (Libertas) | `firmware-libertas` | `0720-connectivity.list.chroot` (MỚI thêm) |
| Texas Instruments (WL12xx/WL18xx — Wi-Fi/BT/FM/GPS) | `firmware-ti-connectivity` | `0720` (MỚI thêm) |
| Tổng hợp/khác | `firmware-linux-free`, `firmware-linux-nonfree`, `firmware-misc-nonfree` (bao gồm cả chip Ralink qua `Provides: firmware-ralink`) | `0150` |

Danh sách này phủ 7 hãng chip Wi-Fi/Bluetooth phổ biến nhất trên thị trường
laptop/PC hiện nay. **KHÔNG phủ**: chip cực hiếm, chip cần driver độc quyền
ngoài kho Debian (ví dụ Broadcom `wl` dùng `broadcom-sta-dkms`, hiện CHƯA
đưa vào — cần đánh giá riêng vì đây là kernel module độc quyền, không chỉ
firmware, rủi ro Secure Boot/ký module khác hẳn — xem DEV-007), và chip đời
rất mới chưa có driver lên kernel 6.12.

## 4. Vì sao cần mở thêm archive area "non-free" (không chỉ "non-free-firmware")

`distro/live-build/auto/config` trước đây dùng
`--archive-areas "main contrib non-free-firmware"`. Đã sửa thành
`"main contrib non-free non-free-firmware"` (thêm khu vực `non-free` thuần).

**Lý do cụ thể, đã kiểm bằng cách tải trực tiếp Packages index thật của
trixie** (không đoán): gói `libfdk-aac2t64` (thư viện runtime Fraunhofer FDK
AAC, dùng để bật codec AAC cho A2DP Bluetooth — xem §1) chỉ tồn tại ở khu
vực `non-free` (Section: `non-free/libs`), KHÔNG có ở `non-free-firmware`
hay `main`. Tất cả firmware chip (Wi-Fi/Bluetooth) trong §3 đã nằm ở
`non-free-firmware` theo cách chia lại archive area của Debian từ bản 12 —
`non-free-firmware` KHÔNG đủ cho trường hợp AAC vì đây là thư viện codec
phần mềm, không phải firmware thiết bị.

Đã đồng bộ sửa `distro/live-build/ci-build.sh` (bước pre-validate trên CI,
dùng `apt-cache show` để kiểm tên gói trước khi build) để mở cùng 4 khu vực
trên trên host container — nếu không đồng bộ, gói chỉ có ở `non-free` (như
`libfdk-aac2t64`) sẽ bị pre-validate DROP oan dù `lb build` thật sẽ cài được.

**LIC-006 (xem `docs/specs/DAC_TA_HE_DIEU_HANH.md`):** việc mở `non-free`
nghĩa là NaMiOS KHÔNG còn là "chỉ dùng thành phần được phép phân phối tự
do" — phải công bố rõ: firmware chip (`non-free-firmware`) + thư viện codec
AAC (`non-free`, gói `libfdk-aac2t64`) là các thành phần KHÔNG tự do, cài để
tối đa hoá tương thích phần cứng/chất lượng âm thanh theo yêu cầu của
Cuong. KHÔNG quảng bá NaMiOS là "100% phần mềm tự do".

## 5. Gói mới thêm cho nhiệm vụ này (tổng hợp)

File `distro/live-build/config/package-lists/0720-connectivity.list.chroot`
(MỚI): `bluez-tools`, `bluez-obexd`, `blueman`, `network-manager-gnome`,
`rfkill`, `firmware-libertas`, `firmware-ti-connectivity`, `libfdk-aac2t64`.

Đã KHÔNG khai lại các gói sau vì đã có sẵn ở nơi khác (tránh trùng ý,
tránh hai nguồn cấu hình xung đột): `bluez`, `libspa-0.2-bluetooth`,
`network-manager`, `wpasupplicant`, `wireless-regdb`, `firmware-linux-free`,
`firmware-linux-nonfree`, `firmware-misc-nonfree`, `firmware-realtek`,
`firmware-atheros`, `firmware-iwlwifi`, `firmware-brcm80211`.

Đã LOẠI (không phải quên — xem comment đầy đủ trong `0720`): `firmware-linux`
(metapackage, cả hai phần Depends đã có sẵn ở `0150`, không thêm phủ sóng
thật nào) và `firmware-ralink` (không phải gói nhị phân thật độc lập trong
trixie — chỉ là virtual package `Provides` bởi `firmware-misc-nonfree` đã
có sẵn; khai lại sẽ bị bước pre-validate CI `apt-cache show` DROP oan).

Hook mới `distro/live-build/config/hooks/normal/0730-connectivity-setup.hook.chroot`:
bật `bluetooth.service` + `NetworkManager.service` qua `systemctl enable`
(best-effort, chroot không chạy systemd thật) kèm fallback symlink `.wants/`
thủ công chắc chắn hơn (cùng kiểu `0640-update-recovery.hook.chroot` đã
làm), xác nhận không có `connman`/`wicd` cạnh tranh, và dọn trạng thái
rfkill-khoá cũ (nếu có) khỏi ảnh.

## 6. Việc cần làm trên phần cứng thật (chưa làm — không bỏ qua)

Giống mọi hạng mục khác trong `docs/support/peripherals.md` §7: KHÔNG hạng
mục nào ở trên được nâng lên `partial`/`completed` chỉ vì thêm gói. Cần,
theo đúng HW-002/DEV-004/DEV-007:

1. Thử AAC/aptX/aptX-HD/LDAC thật với tai nghe/loa hỗ trợ từng codec, xác
   nhận bằng `pw-cli info`/`pactl list sinks` codec nào THỰC SỰ được thương
   lượng (không chỉ tin vào gói đã cài).
2. Ghép HID (bàn phím/chuột Bluetooth) + HFP (cuộc gọi/họp 45 phút).
3. Kết nối Wi-Fi WPA2 và WPA3 trên ít nhất 2 router khác hãng; nếu có
   adapter Wi-Fi 6E/7 thật, test riêng băng 6 GHz.
4. Test sleep/resume giữ kết nối Wi-Fi/Bluetooth (DEV-007: mất Wi-Fi sau
   update/resume là lỗi P0 chặn phát hành).
5. Xác nhận `libfdk-aac2t64` có thật sự được SPA dlopen hay không — đây là
   giả định dựa trên hiểu biết chung về cách PipeWire đóng gói AAC, CHƯA có
   xác nhận trực tiếp từ tài liệu nguồn hoặc máy thật trong lần làm việc này.
