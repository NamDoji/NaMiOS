# Máy chiếu & Màn hình ngoài (namios-manchieu)

- **Mốc:** scaffold đầu tiên, 11/11/2026 — bộ chọn nhanh 1-chạm 4 chế độ
  hiển thị, tương đương **Windows + P**. KDE Plasma đã có Cài đặt Hiển thị
  đầy đủ (`kcm_kscreen`, mở qua `namios-control-panel --category display` —
  xem `do_display()` trong `usr/local/bin/namios-control-panel`), nhưng
  KHÔNG có đường tắt 1-chạm/phím tắt cho 4 chế độ phổ biến nhất khi cắm máy
  chiếu — người dùng ít rành kỹ thuật "chưa thấy chức năng kết nối máy
  chiếu + chọn cách hiển thị". `namios-manchieu` là lối THAM NHANH, KCM vẫn
  là lối chỉnh chi tiết (hai công cụ KHÔNG thay thế nhau).
- **verified_on_host: NO cho TOÀN BỘ hành vi hiển thị thật** (`ui.py`,
  `backend.py` gọi `kscreen-doctor` thật, hook cài đặt, phím tắt Meta+P).
  Container phát triển này KHÔNG có PySide6, KHÔNG có `kscreen-doctor`,
  KHÔNG có display/nhiều màn hình thật. **ĐÃ xác minh thật** (không chỉ đọc
  lại): toàn bộ logic KHÔNG-GUI (`display.py`) bằng 33 test Python 3.11
  thật trong sandbox này + fail-safe của `backend.py` khi thiếu
  `kscreen-doctor` — xem mục 5.

## 1. Đây là gì — 4 chế độ, đúng yêu cầu Win+P

| Nút | Hành vi |
| --- | --- |
| 🪞 **Nhân đôi** | Màn hình trong máy VÀ màn hình ngoài cùng đặt tại vị trí (0,0) — cùng xem một nội dung. |
| 🖥️ **Mở rộng** | Màn hình ngoài đặt BÊN PHẢI màn hình trong máy — kéo cửa sổ qua hai màn hình. |
| 💻 **Chỉ màn hình này** | TẮT màn hình ngoài, chỉ dùng màn hình trong máy. |
| 📽️ **Chỉ màn hình ngoài** | TẮT màn hình trong máy, chỉ dùng màn hình ngoài — ca dùng phổ biến nhất khi chiếu lên máy chiếu/TV phòng họp. |

Khi máy chỉ có **1 màn hình đang kết nối** (chưa cắm cáp), cả 4 nút bị TẮT
(disable) và dòng trạng thái hiện đúng câu:

> "Chưa thấy màn hình ngoài — cắm cáp HDMI/VGA/USB-C vào máy chiếu rồi bấm
> Làm mới."

KHÔNG có hành vi "giả vờ thành công" nào — nếu không đủ màn hình/không tìm
được `kscreen-doctor`, app luôn nói đúng vì sao, không bịa kết quả.

## 2. File đã tạo (TOÀN BỘ mới, không sửa app/module khác)

| File | Vai trò |
| --- | --- |
| `includes.chroot/opt/namios/namios_manchieu-src/__init__.py` | Gói Python — re-export kiểu dữ liệu/hằng số chính từ `display` |
| `includes.chroot/opt/namios/namios_manchieu-src/display.py` | Logic THUẦN Python: parse `kscreen-doctor -o`, phân loại trong/ngoài, dựng token lệnh — KHÔNG subprocess, KHÔNG PySide6 |
| `includes.chroot/opt/namios/namios_manchieu-src/backend.py` | Lớp IO thật: gọi `kscreen-doctor` qua `run_argv` (argv-only, `shell=False`, timeout) |
| `includes.chroot/opt/namios/namios_manchieu-src/branding.py` | Đọc màu thương hiệu "Sen Việt" từ `brand.json` (fail-safe, có fallback cứng) |
| `includes.chroot/opt/namios/namios_manchieu-src/ui.py` | Cửa sổ PySide6: 4 nút to + dòng trạng thái + Làm mới, chạy nền bằng `QThread` |
| `includes.chroot/opt/namios/namios_manchieu-src/__main__.py` | `python3 -m namios_manchieu` — mở cửa sổ (import PySide6 trì hoãn trong hàm) |
| `includes.chroot/opt/namios/namios_manchieu-src/py.typed` | Marker PEP 561 |
| `includes.chroot/usr/share/applications/namios-manchieu.desktop` | Launcher "Máy chiếu & Màn hình ngoài" / "Projector & External Display" |
| `hooks/normal/0311-namios-manchieu.hook.chroot` | Cài `/opt/namios/namios_manchieu` + wrapper `/usr/bin/namios-manchieu` (mirror `0309-namios-antoan.hook.chroot`) |
| `usr/share/namios/docs/MAY-CHIEU.md` | File này |
| `tests/unit/manchieu/{__init__,conftest,test_display}.py` | 33 test Python thuần cho `display.py` |

**Sửa (additive, KHÔNG rewrite):** `etc/skel/.config/kglobalshortcutsrc` —
thêm đúng 1 khối `[namios-manchieu.desktop]` ở cuối file, giữ nguyên mọi
khối cũ (xem mục 4).

**KHÔNG đụng:** `package-lists/*`, `namios-control-panel`/`do_display()`,
app/module NaMiOS khác, `pyproject.toml`.

## 3. Cơ chế: `kscreen-doctor` + lệnh chính xác từng chế độ

### 3.1 Vì sao chọn `kscreen-doctor`, phụ thuộc gói nào

`kscreen-doctor` là CLI chính thức của `libkscreen` (lõi quản lý màn hình
dùng bởi chính KCM `kcm_kscreen`). Đã đối chiếu metadata gói Debian trixie
thật (`packages.debian.org/trixie/kscreen`, mục Depends): gói **`kscreen`**
(đã khai ở `0100-desktop-kde.list.chroot:33`) có **Depends CỨNG tới
`libkscreen-bin`** — package chứa chính xác binary `/usr/bin/kscreen-doctor`
(xác nhận qua `packages.debian.org/search?keywords=kscreen-doctor&searchon=contents&suite=trixie`).
**Kết luận: KHÔNG cần thêm dòng khai gói mới** — `kscreen-doctor` ĐÃ được
cài sẵn transitively bất cứ khi nào `kscreen` được cài. Hook 0311 vẫn tự
kiểm `command -v kscreen-doctor` và báo lỗi rõ nếu một ảnh custom nào đó gỡ
`kscreen` đi mà quên gỡ theo module này.

### 3.2 Định dạng output thật — đã đọc trực tiếp mã nguồn, không suy đoán

Đã tải trực tiếp `src/doctor/doctor.cpp` của `libkscreen` nhánh **v6.3.4**
(đúng version Debian trixie khai: `kscreen (4:6.3.4-1)`) từ
`invent.kde.org/plasma/libkscreen`. Hai phát hiện KHÔNG hiển nhiên nếu chỉ
đoán:

1. `kscreen-doctor -o`/`--outputs` **LUÔN in mã màu ANSI**, không kiểm tra
   `isatty()` trước — output đọc qua `subprocess` (không phải TTY) VẪN chứa
   `\x1b[01;32m` v.v. `display.strip_ansi()` xử lý việc này; test
   `test_display.py` dùng fixture CÓ mã màu thật để chứng minh.
2. Cú pháp cài đặt là `output.<name-or-id-or-uuid>.<setting>[.<value>]`.
   Module này LUÔN dùng **ID số** (không dùng tên connector như `HDMI-A-1`)
   để tránh mọi rủi ro tên chứa dấu chấm phá vỡ cú pháp phân tách-bằng-chấm
   của chính `kscreen-doctor`.

### 3.3 Lệnh chính xác từng chế độ (một lần gọi atomic, chỉ enable/disable/position/priority)

Gọi sử dụng ID output thật (vd internal id=1, external id=70, chiều rộng
màn trong 1920px — thay số thật khi chạy):

```
# Nhân đôi
kscreen-doctor output.1.enable output.1.position.0,0 output.1.priority.1 \
               output.70.enable output.70.position.0,0 output.70.priority.2

# Mở rộng (external bên phải internal, X = chiều rộng internal hiện tại)
kscreen-doctor output.1.enable output.1.position.0,0 output.1.priority.1 \
               output.70.enable output.70.position.1920,0 output.70.priority.2

# Chỉ màn hình này
kscreen-doctor output.1.enable output.1.position.0,0 output.1.priority.1 \
               output.70.disable

# Chỉ màn hình ngoài
kscreen-doctor output.70.enable output.70.position.0,0 output.70.priority.1 \
               output.1.disable
```

Tất cả qua `namios_security.run_argv` (argv-only, `shell=False`, timeout
15s) — KHÔNG `pkexec`: đổi cấu hình output của phiên đăng nhập hiện tại là
hành động người dùng thường có quyền tự làm (giống tự mở System Settings →
Display và bấm Apply), không phải hành động toàn hệ thống cần quyền root.

**Giới hạn trung thực (Nhân đôi):** chỉ đặt CÙNG toạ độ gốc (0,0) cho cả
hai output — đây là cách "overlap = nhân đôi" mà các công cụ kiểu
xrandr/kscreen dùng phổ biến. Module KHÔNG ép đặt lại độ phân giải để hai
màn "giống nhau tuyệt đối" (không có lệnh `.mode`/`.mirror` nào được dùng,
đúng giới hạn 4 primitive enable/disable/position/priority đã giao) — nếu
độ phân giải hai màn khác nhau, phần hiển thị chồng lấn có đúng pixel-perfect
hay không phụ thuộc compositor/backend thật, **CHƯA kiểm chứng trên phần
cứng thật**.

## 4. Phím tắt Meta+P — cơ chế đã dùng + điều cần xác nhận trên máy thật

`etc/skel/.config/kglobalshortcutsrc` ĐÃ có sẵn 3 khối dùng cơ chế
**"_launch" theo desktop-file-id** (KGlobalAccel đọc file `.desktop` trong
`/usr/share/applications/` qua KService khi người dùng bấm phím, KHÔNG cần
app đang chạy sẵn) cho `[org.kde.spectacle.desktop]`, `[org.kde.dolphin.
desktop]`, `[org.kde.krunner.desktop]`. Wave này **tái dùng ĐÚNG cơ chế đó**
— thêm (additive, không xoá/sửa 3 khối cũ):

```ini
[namios-manchieu.desktop]
_launch=Meta+P	XF86Display,Meta+P	XF86Display,Máy chiếu & Màn hình ngoài
_k_friendly_name=Máy chiếu & Màn hình ngoài
```

(dấu cách giữa `Meta+P` và `XF86Display` trong file thật là 1 ký tự TAB —
đúng định dạng nhiều-tổ-hợp-phím đã dùng cho KRunner ở trên trong CHÍNH
file này: `Meta+Space` TAB `Alt+Space` TAB `Alt+F2`.) Cả **Meta+P** (kiểu
Windows) VÀ **XF86Display** (phím vật lý "chuyển màn hình" trên nhiều
laptop) đều mở được app — máy không có phím XF86Display thì tổ hợp đó đơn
giản không bao giờ kích hoạt, không lỗi.

Khác biệt với 3 khối cũ: `org.kde.dolphin.desktop`/`org.kde.spectacle.
desktop`/`org.kde.krunner.desktop` là app KDE **có sẵn**, cơ chế "_launch"
cho các app đó đã coi như chắc chắn hoạt động (dù file này tự ghi
`verified_on_host: NO` cho cả việc đó). `namios-manchieu.desktop` là
desktop-file-id của một app **MỚI tự biên** — cơ chế KService phân giải
desktop-file-id từ `/usr/share/applications/` là cơ chế chuẩn freedesktop,
về lý thuyết hoạt động y hệt cho MỌI `.desktop` hợp lệ bất kể ai cài, nhưng
**CHƯA có ai xác nhận bằng mắt trên Plasma 6 thật cho một app NaMiOS tự
viết** (3 khối cũ chỉ xác nhận cho app KDE lõi).

**CẦN xác nhận trên máy thật (không tự đánh dấu trước):**

- [ ] Bấm Meta+P trên desktop KDE Plasma 6 thật → cửa sổ "Máy chiếu & Màn
      hình ngoài" mở ra.
- [ ] Đối chiếu bằng lệnh:
      `kreadconfig6 --file kglobalshortcutsrc --group namios-manchieu.desktop --key _launch`
      → phải trả đúng giá trị đã khai ở trên.
- [ ] Nếu Meta+P KHÔNG mở được app: TRƯỚC TIÊN chạy tay
      `/usr/bin/namios-manchieu` xem có mở cửa sổ bình thường không. Nếu
      chạy tay OK mà Meta+P không phản ứng, Plasma 6 có thể cần một bước
      đăng ký KGlobalAccel component riêng (chạy app ít nhất 1 lần để nó tự
      đăng ký) — CHƯA kiểm chứng điều này trên máy thật.
- [ ] Nếu máy test có phím `XF86Display`/"Display"/Fn+F4 vật lý: bấm thử,
      xác nhận cũng mở được app (hoặc ghi nhận máy đó không gửi đúng keysym
      `XF86Display` — tuỳ hãng/driver, không phải lỗi của cấu hình này).

## 5. ĐÃ xác minh thật trong sandbox này (không chỉ đọc lại mã)

Chạy bằng Python 3.11 thật, import trực tiếp `display.py`/`backend.py` từ
`includes.chroot/opt/namios/namios_manchieu-src/` (KHÔNG mock logic):

- **33 test `tests/unit/manchieu/test_display.py`** — PASS 100%: `strip_ansi`
  loại đúng mã màu ANSI thật; `classify_output` đúng cho eDP/LVDS/DSI (trong)
  và HDMI/DP/VGA/DVI/USB-C (ngoài) + fallback theo `output_type` khi tên lạ;
  `parse_outputs` đọc đúng id/tên/connected/enabled/priority/type/geometry/
  mode-hiện-tại từ fixture **CÓ mã màu ANSI thật** theo đúng định dạng
  `doctor.cpp` v6.3.4 (gồm cả output đã rút cáp, output "disable
  unsupported"); `pick_displays` đúng cho cả 2 trường hợp thành công VÀ 4
  trường hợp lỗi (0 output, 1 output, external đã rút cáp, không có
  internal); `build_argv_tokens` đúng CHÍNH XÁC từng token cho cả 4 chế độ,
  xác nhận LUÔN dùng ID (không bao giờ dùng tên connector trong token);
  `plan()` gộp đúng pick+build+describe trong một lần gọi.
- **`backend.read_outputs()`/`backend.apply_mode()` chạy thật** trong
  container này (không có `kscreen-doctor`) → trả đúng
  `success=False` kèm câu "Không tìm thấy kscreen-doctor trên máy này..."
  — KHÔNG crash, KHÔNG raise ra ngoài (xác nhận fail-safe thật, không chỉ
  đọc code).
- `python3 -m py_compile` toàn bộ `.py` trong `namios_manchieu-src/` — 0 lỗi.
- `ruff check` toàn bộ `namios_manchieu-src/` + `tests/unit/manchieu/` — 0 lỗi
  (sau khi sửa 2 lỗi độ dài dòng + 1 import thừa + 1 cảnh báo S105 do đặt
  tên biến trùng từ khoá "token").
- `bash -n` cho hook `0311-namios-manchieu.hook.chroot` (kể cả wrapper
  heredoc bên trong) — 0 lỗi.
- Toàn bộ suite test của repo (`pytest tests/`) sau khi thêm các file trên:
  **2593 passed, 5 skipped** — cùng số skip với baseline trước đó (không
  tăng fail/skip nào do module này).

**Cách test import `namios_manchieu`:** module này KHÔNG có mirror
`src/namios_manchieu/` — đúng phạm vi giao việc (chỉ file dưới
`namios_manchieu-src/` + hook + desktop + doc + kglobalshortcutsrc).
`tests/unit/manchieu/conftest.py` tự nạp thư mục `namios_manchieu-src/`
vào `sys.modules["namios_manchieu"]` bằng `importlib.util` (không sửa
`pyproject.toml`, không copy file) — mirror đúng khuôn
`tests/unit/lich/conftest.py`.

## 6. CHƯA xác minh — cần desktop KDE Plasma 6 thật có nhiều màn hình

Container phát triển này KHÔNG có PySide6, KHÔNG có `kscreen-doctor`,
KHÔNG có display/nhiều màn hình/máy chiếu thật. `ui.py`/`__main__.py`/hook
cài đặt CHƯA được chạy thật — chỉ qua `py_compile` + review API Qt.

Checklist xác nhận trên máy/VM thật có ÍT NHẤT 1 màn hình ngoài (điền khi
có, không tự đánh dấu trước):

- [ ] `namios-manchieu` mở được cửa sổ, không crash; dòng trạng thái hiện
      đúng danh sách output đang kết nối (trong máy/ngoài + tên connector
      thật + đang bật/tắt).
- [ ] Chỉ cắm 1 màn hình (hoặc rút cáp màn ngoài) → 4 nút chế độ bị TẮT +
      hiện đúng câu "Chưa thấy màn hình ngoài — cắm cáp HDMI/VGA/USB-C vào
      máy chiếu rồi bấm Làm mới."
- [ ] Cắm máy chiếu/màn hình ngoài qua HDMI (hoặc VGA/USB-C nếu có) → bấm
      Làm mới → 4 nút chế độ BẬT lại, dòng trạng thái hiện đúng tên
      connector (vd `HDMI-A-1`) + phân loại "Ngoài".
- [ ] Bấm **Nhân đôi** → hộp thoại xác nhận hiện đúng tên 2 màn hình → Có
      → cả hai màn hình cùng hiện một nội dung (quan sát bằng mắt, không
      chỉ tin thông báo "đã áp dụng").
- [ ] Bấm **Mở rộng** → màn hình ngoài hiện BÊN PHẢI màn hình trong máy;
      kéo một cửa sổ từ màn trong qua màn ngoài — hoạt động như desktop mở
      rộng thật.
- [ ] Bấm **Chỉ màn hình này** → màn hình ngoài TẮT (đen/không tín hiệu),
      chỉ còn màn hình trong máy hoạt động.
- [ ] Bấm **Chỉ màn hình ngoài** → màn hình trong máy TẮT, chỉ còn màn
      hình ngoài hoạt động (ca "chiếu lên máy chiếu" — xác nhận đây là ca
      hay dùng nhất, UI không bị lỡ bước nào).
- [ ] Sau mỗi lần đổi chế độ, bấm lại một chế độ KHÁC → chuyển đúng ngay,
      không cần đăng xuất/khởi động lại.
- [ ] Gỡ tạm `python3-pyside6*` khỏi máy, chạy `namios-manchieu` từ
      terminal → wrapper in đúng dòng "thiếu PySide6" + thoát mã khác 0,
      KHÔNG treo phiên đăng nhập/KHÔNG crash desktop.
- [ ] (Nếu kiểm được) gỡ tạm/đổi tên `kscreen-doctor` → wrapper in đúng
      dòng "không tìm thấy kscreen-doctor" + thoát mã khác 0 TRƯỚC KHI mở
      cửa sổ (nhanh hơn, không để người dùng tưởng app "không phản hồi").
- [ ] Bấm Meta+P (và XF86Display nếu máy có) — xem mục 4 checklist riêng.
- [ ] Màu sắc cửa sổ khớp bộ nhận diện "Sen Việt" (`#CF3540`/`#122A3A`); gỡ
      tạm `brand.json` → UI vẫn mở được bằng màu fallback cứng.

## 7. Khuyến nghị bổ sung (KHÔNG tự làm — ngoài phạm vi wave này)

- **Chọn giữa nhiều màn hình ngoài:** phiên bản này chỉ dùng color hình
  ngoài ĐẦU TIÊN (ID nhỏ nhất) nếu có nhiều hơn 1 kết nối cùng lúc — đủ cho
  ca phổ biến (1 trong máy + 1 máy chiếu), nhưng KHÔNG có UI chọn khi có ≥2
  màn ngoài (vd phòng họp nhiều TV). Muốn làm: thêm bước chọn trong
  `ui.py` + hàm `display.pick_displays` nhận tham số "external đã chọn"
  thay vì luôn lấy ID nhỏ nhất.
- **Native mirror/mode:** `kscreen-doctor` có lệnh `output.<id>.mirror.
  <source-id>` (thiết lập replication source thật, thường chỉ hỗ trợ trên
  Wayland) và `output.<id>.mode.<id-or-WxHxR>` (đặt lại độ phân giải) —
  wave này CHỦ Ý không dùng (ngoài phạm vi 4 primitive enable/disable/
  position/priority đã giao), có thể cải thiện độ chính xác của chế độ
  Nhân đôi nếu được giao làm tiếp.
