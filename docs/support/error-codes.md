# Mã lỗi chẩn đoán NaMiOS (U13-08)

**Trạng thái:** `partial` — taxonomy có thật + tool chạy được trên máy có
`kdialog`/`iproute2`/`NetworkManager`/`pciutils`/`systemd-coredump`; **chưa kiểm
trên máy thật** (`verified_on_host: NO` xuyên suốt — xem
`distro/live-build/config/package-lists/0650-diagnostics.list.chroot`).
**Ngày:** 08/11/2026.

**Nguồn yêu cầu:** `docs/spec-package/NaMiOS_Phu_luc_13_Uu_tien_Nang_cap_va_Cong_Phat_hanh.md`
§2 dòng U13-08 — *"Mã lỗi nhất quán, lịch sử update/crash, log đã che, nút hoàn
tác, hướng dẫn tiếng Việt"*; cửa kiểm chứng: *"Người dùng/IT phân biệt mất
mạng, thiếu driver, quyền bị từ chối, app crash trong 3 màn hình."*

**Công cụ dùng tài liệu này:**
`distro/live-build/config/includes.chroot/usr/local/bin/namios-chan-doan`
(launcher `usr/share/applications/namios-chan-doan.desktop`). File này là
NGUỒN SỰ THẬT của tập mã — sửa ý nghĩa/cách xử lý ở đây thì PHẢI sửa chuỗi
tiếng Việt tương ứng trong script, không để hai nơi lệch nhau. Script không
đọc file này lúc chạy (file không có trên ảnh ISO, chỉ có trong repo) — chuỗi
hiển thị trong script được viết tay khớp với bảng dưới.

**KHÔNG liên quan `namios_core.errors.ErrorCode`** (`E_INPUT_SCHEMA`,
`E_PERMISSION_DENIED`, …) — đó là mã lỗi máy-đọc cho API/CLI nội bộ của các
engine Python (`docs/specs/M1-INTERFACES.md` §3), đi qua `Envelope`. Mã `NM-*`
dưới đây là mã **hướng người dùng cuối/IT hỗ trợ**, hiển thị trong GUI chẩn
đoán. Hai không gian tên tách biệt có chủ đích — không hợp nhất, không đổi
format cho khớp nhau.

## 1. Quy ước

- Dạng `NM-<NHÓM>-<SỐ>` — `NHÓM` ∈ `{NET, DRV, DSK, PERM, APP}`, `SỐ` 3 chữ
  số, **không đổi giá trị sau khi phát hành** (cùng nguyên tắc với `ErrorCode`
  ở `namios_core/errors.py`).
- Mỗi mã gắn với ĐÚNG MỘT trong 3 màn hình chẩn đoán của công cụ (cột
  "Màn hình" ở bảng §2).
- Cột "Phát hiện tự động" = `có` cho MỌI mã trong bảng §3 — không có mã nào ở
  đây là placeholder chưa code; nếu một mã chưa có logic quét thật thì mã đó
  không được thêm vào bảng (tránh TODO giả làm chức năng).

## 2. Ba màn hình → nhóm mã (cửa kiểm chứng U13-08)

| Màn hình | Nhóm mã | Lệnh nền dùng để quét |
| --- | --- | --- |
| 1. Mạng | `NM-NET-*` | `ip`, `nmcli` |
| 2. Phần cứng & driver | `NM-DRV-*`, `NM-DSK-*` | `lspci -k`, `dmesg`, `df` |
| 3. Quyền & ứng dụng | `NM-PERM-*`, `NM-APP-*` | `journalctl`, `coredumpctl` |

Ngoài 3 màn hình trên, tool có 2 hành động phụ không gắn mã lỗi: "Lịch sử cập
nhật & hoàn tác" (đọc log U13-02 có sẵn, xem §4) và "Xuất log đã che bí mật"
(xem §5).

## 3. Bảng mã lỗi

| Mã | Ý nghĩa | Phát hiện tự động | Cách xử lý (tiếng Việt, hiển thị trong tool) |
| --- | --- | --- | --- |
| `NM-NET-001` | Mất mạng hoàn toàn — không có giao diện mạng nào đang hoạt động, hoặc có giao diện lên nhưng không có default route. | Có (`ip -o link show up` + `ip route show default`) | Kiểm tra Wi-Fi đã bật / cáp Ethernet đã cắm / chế độ máy bay đang tắt; thử kết nối lại từ khay hệ thống (NetworkManager). |
| `NM-NET-002` | Có mạng nội bộ nhưng không ra được Internet (DNS lỗi, captive portal, hoặc NetworkManager báo `limited`/`portal`/`none`). | Có (`nmcli networking connectivity`) | Mở trình duyệt thử một trang bất kỳ (có thể cần đăng nhập cổng Wi-Fi công cộng); nếu vẫn lỗi, đổi DNS hoặc báo IT. |
| `NM-DRV-001` | Thiếu firmware cho thiết bị (kernel báo tải firmware thất bại). | Có (`dmesg` lọc mẫu `firmware...fail`) | Cần gói firmware tương ứng (ví dụ `firmware-iwlwifi` cho Wi-Fi Intel); gửi log đã xuất cho hỗ trợ để xác định đúng gói. Nếu không đọc được `dmesg` (cần quyền root), tool báo rõ "không xác định", không báo sai thành OK. |
| `NM-DRV-002` | Thiếu driver cho thiết bị PCI (không có dòng "Kernel driver in use"). | Có (`lspci -k`) | Thử App Center/Driver Manager nếu máy có; một số thiết bị hiếm (vân tay, card mạng cũ) chưa có driver mã nguồn mở cho Linux — đây là giới hạn phần cứng, không phải lỗi cấu hình. |
| `NM-DSK-001` | Sắp hết dung lượng đĩa (phân vùng gốc `/` dùng ≥ 90%). | Có (`df -P`) | Xoá file tải xuống/thùng rác, dọn `/var/log` cũ, hoặc gắn thêm ổ lưu trữ; đĩa đầy có thể làm cập nhật hệ thống thất bại giữa chừng (xem `ADR-0014`). |
| `NM-PERM-001` | Hành động bị chặn bởi quyền hệ thống (polkit từ chối, hoặc không có trong sudoers). | Có (`journalctl -p err` lọc mẫu `polkit...deny`/`not in sudoers`) | Hành động này cần quyền quản trị; đăng nhập tài khoản có quyền admin hoặc nhập mật khẩu khi được polkit hỏi. |
| `NM-PERM-002` | Quyền truy cập tệp/thiết bị bị từ chối (`Permission denied`) ghi trong nhật ký hệ thống. | Có (`journalctl -p err` lọc mẫu `Permission denied`) | Chuột phải vào file/thư mục → Thuộc tính → kiểm chủ sở hữu và quyền; nếu là thiết bị (USB/máy in), thử cắm lại hoặc khởi động lại. |
| `NM-APP-001` | Ứng dụng bị crash (có core dump được systemd ghi nhận). | Có (`coredumpctl list`) | Mở lại ứng dụng; nếu lặp lại nhiều lần, dùng "Xuất log (đã che bí mật)" trong tool rồi gửi cho hỗ trợ. |
| `NM-APP-002` | Lỗi ứng dụng khác trong nhật ký hệ thống (segfault/"terminated by signal") không có core dump — ví dụ máy thiếu `systemd-coredump`. | Có (`journalctl -p err` lọc mẫu `segfault`/`terminated by signal`) | Giống `NM-APP-001`; nếu máy không có `systemd-coredump`, cài thêm để lần sau có bản ghi đầy đủ hơn. |

Mỗi lần quét, nếu lệnh nền cần (`lspci`, `dmesg`, `journalctl`, `coredumpctl`,
`nmcli`...) không có trên máy hoặc bị chặn quyền đọc, tool in rõ "không xác
định được" cho đúng mục đó — KHÔNG suy diễn thành `[OK]` khi không có dữ liệu
thật (false negative là nguy hiểm hơn im lặng).

## 4. "Nút hoàn tác" — phạm vi thật (không quảng cáo quá)

`namios-chan-doan` KHÔNG tự chế cơ chế rollback riêng. Nút "Hoàn tác" gọi
thẳng cơ chế **snapshot Timeshift** đã có từ U13-02
(`distro/live-build/config/hooks/normal/0640-update-recovery.hook.chroot`,
`docs/adr/ADR-0014-update-recovery-strategy.md`):

- Nếu Timeshift **chưa cài** hoặc **chưa cấu hình ổ lưu**
  (`/etc/timeshift/timeshift.json` không tồn tại) → tool báo đúng sự thật là
  **chưa có điểm khôi phục nào**, không giả vờ có nút hoàn tác hoạt động. Đây
  là giới hạn đã biết của bản alpha (U13-02 vẫn `partial`), không phải lỗi
  riêng của `namios-chan-doan`.
- Nếu đã cấu hình → nút mở `timeshift-gtk` (qua `pkexec`, sau khi người dùng
  bấm "Có" ở hộp thoại xác nhận) để người dùng TỰ chọn điểm khôi phục; tool
  KHÔNG tự động chạy `timeshift --restore` mà không hỏi, và KHÔNG tự chọn
  điểm khôi phục hộ người dùng.
- Mục GRUB "NaMiOS — Khôi phục (recovery)" nêu trong `ADR-0014` vẫn ở trạng
  thái `specified` (chưa implement) — `namios-chan-doan` KHÔNG hiển thị như
  đã có.

Màn hình "Lịch sử cập nhật & hoàn tác" của tool đọc trực tiếp
`/var/log/namios-health.log` (health check sau khởi động, U13-02) và
`/var/log/namios-snapshot.log` (log tạo snapshot trước cập nhật) — đây là
nguồn "lịch sử update" thật đã tồn tại sẵn, tool không tự ghi một log riêng
song song với nó.

## 5. Xuất log đã che bí mật

"Xuất log" ghép 3 báo cáo ở §2 + lịch sử cập nhật ở §4 thành một file, rồi
che qua `namios_security.redact_text` (đã có kiểm chứng ở
`src/namios_security/redactor.py` — PEM private key, `Bearer ...`,
`password=`/`token=`/`secret=`/..., cụm OTP, IP nội bộ RFC1918/loopback,
đường dẫn `/home/<user>`) **cộng thêm** regex email + MAC riêng cho luồng
xuất log này (hai mẫu này KHÔNG có trong `redact_text` gốc, vì gốc dùng cho
`ErrorBody.details` nội bộ chứ không phải gói log xuất cho người dùng cuối).

Nếu máy không có `python3` hoặc không import được module `namios_security`
(ví dụ ảnh rút gọn thiếu `/opt/namios`), tool dùng một bộ `sed` dự phòng kém
toàn diện hơn và **ghi rõ cảnh báo ngay đầu file xuất ra** — không che giấu
việc đang dùng đường dự phòng, để người nhận log tự quyết định có nên chia sẻ
tiếp hay không.
