# NaMiLịch — Âm lịch Việt Nam + ngày lễ (VN-1)

- **Mốc:** scaffold đầu tiên, 11/11/2026 (VN-1,
  `docs/roadmap/NEW-FUNCTIONS-DIRECTION.md` mục "II. Thuần Việt bẩm sinh").
- **verified_on_host: NO cho lớp giao diện PySide6** (`ui.py`/`__main__.py`/
  hook cài đặt) — container phát triển hiện tại KHÔNG có PySide6/display
  (headless, không có `/dev/kvm`/live-build — xem `CLAUDE.md` mục "Môi trường
  build hiện tại"). **ĐÃ chạy thật** (không phải chỉ đọc lại) toàn bộ lớp lõi
  KHÔNG-GUI (`lunar.py`/`holidays.py`) bằng Python 3.11 thật trong sandbox này
  — xem mục 5 cho danh sách cụ thể đã xác minh.

## 1. Đây là gì

NaMiLịch là một app desktop nhỏ, **hoàn toàn ngoại tuyến** (không gọi mạng,
không cần tài khoản), hiển thị:

- Panel "Hôm nay": ngày Dương lịch + ngày Âm lịch + tên năm/tháng/ngày
  Can-Chi + danh sách lễ sắp tới (kể cả nhắc giỗ người dùng tự thêm).
- Lưới tháng điều hướng được (nút Tháng trước/Tháng sau/Hôm nay): mỗi ô ngày
  hiển thị số ngày Dương to + ngày/tháng Âm nhỏ bên dưới, tô màu vàng cho
  ngày có lễ, viền đỏ cho hôm nay, chữ đỏ cho Chủ Nhật.
- Nút "Thêm nhắc giỗ": người dùng nhập tên + ngày/tháng Âm lịch, lưu lại và
  **lặp lại hằng năm** (khớp Dương lịch khác nhau mỗi năm, tự tính lại).

Đây là một trong những khác biệt rõ nhất với Windows: Windows không có âm
lịch Việt Nam tích hợp sẵn ở bất kỳ đâu trong hệ thống lịch/đồng hồ.

## 2. File đã tạo (TOÀN BỘ mới, không sửa file có sẵn nào)

| File | Vai trò |
| --- | --- |
| `includes.chroot/opt/namios/namios_lich-src/__init__.py` | Gói Python — re-export các hàm/kiểu dữ liệu chính |
| `includes.chroot/opt/namios/namios_lich-src/__main__.py` | `python3 -m namios_lich` — mở cửa sổ (import PySide6 trì hoãn trong hàm) |
| `includes.chroot/opt/namios/namios_lich-src/lunar.py` | Lõi đổi lịch Dương↔Âm + Can-Chi — THUẦN PYTHON, không phụ thuộc GUI |
| `includes.chroot/opt/namios/namios_lich-src/holidays.py` | Nạp `holidays_vn.json` + tìm lễ sắp tới + lưu/đọc nhắc giỗ tuỳ chỉnh — THUẦN PYTHON |
| `includes.chroot/opt/namios/namios_lich-src/holidays_vn.json` | Dữ liệu lễ Việt Nam (pháp định + truyền thống phổ biến) |
| `includes.chroot/opt/namios/namios_lich-src/ui.py` | Cửa sổ PySide6: panel Hôm nay + lưới tháng + hộp thoại thêm nhắc giỗ |
| `includes.chroot/opt/namios/namios_lich-src/py.typed` | Marker PEP 561 (mirror `namios_welcome-src/py.typed`) |
| `includes.chroot/usr/share/applications/namios-lich.desktop` | Launcher "NaMiLich / NaMiLịch" |
| `hooks/normal/0307-namios-lich.hook.chroot` | Cài `/opt/namios/namios_lich` + wrapper `/usr/bin/namios-lich` (mirror `0300-namios-welcome.hook.chroot`) |
| `usr/share/namios/docs/NAMILICH.md` | File này |
| `tests/unit/lich/{__init__,conftest,test_lunar,test_holidays}.py` | Test thuần Python cho `lunar.py`/`holidays.py` (xem mục 5) |

**KHÔNG đụng:** `namios_welcome*`, `namios_assistant*`, Plasma
`appletsrc`/`plasmarc`/`plasma-localerc` (skel), calamares, bootloader,
`.gh-token`, package-lists. `python3-pyside6.qtwidgets` ĐÃ có sẵn trong
`0110-desktop-familiar.list.chroot` cho `namios_welcome`/`namios_assistant`
— module này chỉ TÁI DÙNG, không khai báo thêm gói nào.

## 3. Thuật toán âm lịch — nguồn + phạm vi chính xác

**Nguồn:** port trực tiếp thuật toán công khai của **Hồ Ngọc Đức** (Đại học
Leipzig) — "Thuật toán tính lịch Âm lịch Việt Nam dựa trên vị trí thực của
Mặt Trời/Mặt Trăng",
https://www.informatik.uni-leipzig.de/~duc/amlich/calrules.html. Đây là
nguồn công thức được dùng rộng rãi nhất cho lịch âm Việt Nam hiện nay (bản
JS gốc đã được port sang hàng chục ngôn ngữ, là cơ sở của hầu hết lịch âm
trên web/app Việt Nam). NaMiOS **KHÔNG tự chế** thuật toán thiên văn riêng —
chỉ giữ nguyên hằng số/logic đã công bố (xem docstring đầu `lunar.py` cho
chi tiết công thức Sóc/New Moon + hoàng kinh Mặt Trời + xác định tháng
nhuận).

**Múi giờ:** cố định UTC+7 (múi giờ Việt Nam từ 1967 đến nay). Ngày âm lịch
TRƯỚC 1967 tính bằng module này có thể sai 1 ngày (bản gốc Hồ Ngọc Đức dùng
UTC+8 cho các năm trước 1967 — nhánh đó không được port, vì NaMiLịch chỉ
phục vụ ngày hiện tại/tương lai + lịch sử gần).

**Phạm vi chính xác:** khoảng năm 1800–2199 dương lịch (giới hạn đã công bố
rộng rãi của chính xấp xỉ thiên văn này, không phải giới hạn riêng của bản
port).

**Hạn chế đã biết** (giữ nguyên hành vi gốc khi port, xem
`test_xin_sai_thang_nhuan_trong_nam_co_nhuan_bi_bao_khong_ton_tai`):
`convert_lunar_to_solar(..., lunar_leap=1)` chỉ bị chặn/trả `(0, 0, 0)` khi
năm âm lịch đó CÓ 13 tháng nhưng xin SAI tháng nhuận; nếu năm đó CHỈ có 12
tháng (không nhuận), hàm không tự kiểm tra `lunar_leap` — caller cần tự biết
năm nào có tháng nhuận (hoặc dùng `convert_solar_to_lunar` theo chiều ngược
để lấy đúng cờ `leap`).

## 4. Ngày lễ Việt Nam + nhắc giỗ tuỳ chỉnh

`holidays_vn.json` phân 2 nhóm (`cong_lap: true/false`):

- **`cong_lap: true`** (8 mục) — các mốc CỐ ĐỊNH theo Điều 112 Bộ luật Lao
  động 2019: Tết Dương lịch (1/1), Giỗ Tổ Hùng Vương (10/3 âm), Giải phóng
  miền Nam (30/4), Quốc tế Lao động (1/5), Quốc khánh (2/9), Giao thừa + Mùng
  1–3 Tết Nguyên Đán (âm lịch). **KHÔNG tự đoán** số ngày nghỉ bù/nghỉ gộp cụ
  thể từng năm (ví dụ ngày thứ hai nghỉ quanh 2/9, hay đúng 5 ngày Tết gồm
  ngày nào) — các mốc đó do Thủ tướng Chính phủ thông báo riêng mỗi năm,
  ngoài phạm vi một file JSON tĩnh; file này chỉ ghi đúng mốc luật định.
- **`cong_lap: false`** (15 mục) — lễ/Tết truyền thống phổ biến (Rằm tháng
  Giêng, Hàn Thực, Phật Đản, Đoan Ngọ, Vu Lan, Trung Thu, Trùng Cửu, Ông
  Công Ông Táo...) + vài ngày kỷ niệm Dương lịch phổ biến (Phụ nữ Việt Nam,
  Nhà giáo Việt Nam...), chỉ để tham khảo/nhắc nhớ, KHÔNG phải ngày nghỉ
  pháp định.

**Nhắc giỗ:** `holidays.add_reminder(config_dir, name_vi, lunar_day,
lunar_month)` lưu vào `$XDG_CONFIG_HOME/namios/namios_lich/reminders.json`
(ghi đè toàn bộ danh sách, idempotent theo tên — thêm lại cùng tên sẽ cập
nhật ngày/tháng, không tạo bản trùng). Mỗi lần mở app, nhắc giỗ được quy đổi
lại sang Dương lịch của năm hiện tại/kế tiếp qua
`convert_lunar_to_solar` — **lặp lại hằng năm** đúng nghĩa (không phải lưu
một ngày Dương cố định).

## 5. ĐÃ xác minh thật trong sandbox này (không chỉ đọc lại mã)

Chạy bằng Python 3.11 thật (import trực tiếp `lunar.py`/`holidays.py` từ
`includes.chroot/opt/namios/namios_lich-src/`, KHÔNG mock):

- **9 mốc Tết Nguyên Đán liên tiếp (2020–2028)**: cả ngày Dương lịch VÀ tên
  năm Can-Chi khớp 100% với mốc công bố rộng rãi — 25/01/2020 (Canh Tý),
  12/02/2021 (Tân Sửu), 01/02/2022 (Nhâm Dần), 22/01/2023 (Quý Mão),
  10/02/2024 (Giáp Thìn), 29/01/2025 (Ất Tỵ), 17/02/2026 (Bính Ngọ),
  06/02/2027 (Đinh Mùi), 26/01/2028 (Mậu Thân).
- **Giỗ Tổ Hùng Vương 10/3 âm 2024 → 18/04/2024 dương** — khớp mốc nghỉ lễ
  toàn quốc đã công bố chính thức năm 2024.
- **Năm Quý Mão 2023 có tháng nhuận (nhuận tháng 2)** — thuật toán nhận
  diện đúng cờ `leap=1` cho lần xuất hiện đầu của tháng 2 âm (22/03/2023) và
  `leap=0` cho tháng 3 thường kế tiếp (20/04/2023); xin "tháng 3 nhuận" (sai
  tháng nhuận thật của năm đó) trả đúng `(0, 0, 0)`.
- **Round-trip Dương→Âm→Dương**: 900 ngày ngẫu nhiên (3 seed × 300 ngày,
  1950–2100) — 0 lệch (`test_round_trip_solar_lunar_solar`); một lần kiểm
  tay riêng trong quá trình xây dựng đã chạy 2000 ngày ngẫu nhiên — cũng 0
  lệch.
- **Can-Chi ngày chạy chu kỳ 60 ngày liên tục** (không phụ thuộc Âm/Dương)
  — ngày kế tiếp khác Can-Chi, đúng 60 ngày sau quay lại tên cũ.
- **`holidays.py`**: nạp đúng `holidays_vn.json` (≥15 mục qua
  `test_load_bundled_holidays_non_empty`), lễ Dương cố định mỗi năm
  (`quoc_khanh` → luôn 2/9), lễ Âm quy đổi đúng ra ngày Dương đã kiểm ở
  trên (`tet_nguyen_dan_1` → 10/02/2024 và 17/02/2026), `upcoming_holidays`
  trả đúng thứ tự gần nhất trước, nhắc giỗ tuỳ chỉnh lưu/đọc/cập nhật đúng
  (idempotent theo tên, dùng `tmp_path` cô lập — không đụng `$HOME` thật).
- `python3 -m py_compile` toàn bộ `.py` trong `namios_lich-src/` — 0 lỗi
  (bao gồm `ui.py` — PySide6 chỉ được syntax-check, không chạy, vì container
  này thiếu PySide6).
- `ruff check` toàn bộ `namios_lich-src/` + `tests/unit/lich/` — 0 lỗi.
- `bash -n` cho hook `0307-namios-lich.hook.chroot` (kể cả wrapper heredoc
  bên trong) — 0 lỗi.
- Toàn bộ suite test của repo (`pytest tests/`) sau khi thêm các file trên
  vẫn xanh (2558 passed, 5 skipped có từ trước — không tăng số skip/fail).

**Lưu ý về cách test import `namios_lich`:** module này KHÔNG có mirror
`src/namios_lich/` (khác với `namios_welcome` có cả
`src/namios_welcome/` lẫn `includes.chroot/.../namios_welcome-src/` giống
nhau, mirror đó nằm trong `pythonpath` chung của `pyproject.toml`) — theo
đúng phạm vi giao việc (chỉ file dưới `namios_lich-src/` + hook + desktop +
doc). `tests/unit/lich/conftest.py` tự nạp thư mục `namios_lich-src/` vào
`sys.modules["namios_lich"]` bằng `importlib.util` (không sửa
`pyproject.toml`, không copy file) — xem docstring trong file đó.

## 6. CHƯA xác minh — cần desktop KDE Plasma 6 thật

Container phát triển này KHÔNG có PySide6 và KHÔNG cài được `python3-venv`
nên `ui.py`/`__main__.py` CHƯA được import/chạy thật — chỉ qua `py_compile`
+ review API Qt (tên enum `Qt.AlignCenter`/`QFrame.Box`/
`QDialogButtonBox.Ok`/`QDialogButtonBox.Cancel` đã đối chiếu tài liệu
PySide6/Qt6 chính thức).

Checklist xác nhận trên máy/VM thật (điền khi có desktop, không tự đánh dấu
trước):

- [ ] `namios-lich` mở được cửa sổ, không crash; panel "Hôm nay" hiển thị
      đúng ngày Dương/Âm/Can-Chi của NGÀY THẬT trên máy đó.
- [ ] Lưới tháng hiện đúng tháng hiện tại, nút "Tháng trước"/"Tháng sau"
      chuyển đúng, nút "Hôm nay" quay lại đúng tháng hiện tại từ bất kỳ
      tháng nào đang xem.
- [ ] Ô "Hôm nay" có viền đỏ nổi bật; ô có lễ tô nền vàng; chữ Chủ Nhật màu
      đỏ — di chuột vào một ô hiện đúng tooltip (ngày Dương + Âm + tên lễ
      nếu có).
- [ ] Bấm "+ Thêm nhắc giỗ", nhập tên + ngày/tháng âm, bấm OK → lễ xuất hiện
      trong danh sách "Lễ sắp tới" ở panel Hôm nay (không cần khởi động lại
      app).
- [ ] Tắt máy, mở lại app → nhắc giỗ đã thêm vẫn còn (đọc đúng
      `~/.config/namios/namios_lich/reminders.json`).
- [ ] Gỡ tạm `python3-pyside6*` khỏi máy, chạy `namios-lich` từ terminal →
      wrapper in đúng dòng "PySide6 chưa sẵn sàng" + thoát mã 0, KHÔNG treo
      phiên đăng nhập/KHÔNG crash desktop.
- [ ] Màu sắc cửa sổ khớp bộ nhận diện "Sen Việt" (`#CF3540`/`#F2C66D`) — so
      với `usr/share/namios-branding/logo/brand.json` đang cài trên máy đó;
      gỡ tạm file `brand.json` → UI vẫn mở được bằng màu fallback cứng.
- [ ] Đổi `LANG`/giờ hệ thống sang một ngày Tết đã kiểm ở mục 5 (ví dụ
      10/02/2024) → panel "Hôm nay" hiện đúng "Mùng 1 Tết — năm Giáp Thìn".

## 7. Khuyến nghị bổ sung (KHÔNG tự làm — ngoài phạm vi file được giao)

VN-1 (`NEW-FUNCTIONS-DIRECTION.md`) còn gợi ý một hướng bổ sung: cấu hình
**Plasma Digital Clock applet** (`org.kde.plasma.digitalclock`) dùng tính
năng "Lịch thay thế" (*alternate calendar*) sẵn có trong Plasma 6 để hiện
ngày Âm lịch ngay trong popup lịch của khay hệ thống (taskbar) — khác với
NaMiLịch (app cửa sổ riêng). Đây CHỈ là khuyến nghị tham khảo cho một việc
KHÁC (chỉnh `plasma-org.kde.plasma.desktop-appletsrc`/cấu hình applet),
**không thuộc phạm vi các file NaMiLịch liệt kê ở mục 2** — người thực hiện
việc đó cần:

1. Kiểm gói Plasma 6 trên Debian 13 trixie có kèm plugin "lịch thay thế"
   kiểu Việt Nam sẵn hay không (Plasma 6 có framework
   `org.kde.plasma.calendar` hỗ trợ *alternate calendar plugin* dạng QML,
   nhưng bản âm lịch Việt Nam cụ thể — nếu chưa có sẵn trong gói Debian —
   sẽ cần viết một plugin QML riêng tái dùng đúng `lunar.py`/`holidays.py`
   ở trên qua PyQt/QML binding, hoặc port logic sang QML/JS).
2. Nếu viết plugin riêng: đặt tại
   `usr/share/plasma/calendarplugins/org.namios.amlich/` (tên gói quy ước
   của Plasma `org.kde.plasmacalendarplugins`), và set mặc định qua
   `plasma-org.kde.plasma.desktop-appletsrc` (KHU VỰC BỊ CẤM SỬA theo giao
   việc NaMiLịch này — cần một task riêng, giám khảo đối chiếu 50 mốc
   riêng cho plugin đó như VN-1 acceptance criteria đã ghi).
3. KHÔNG tự thêm việc này vào commit của NaMiLịch — giữ đúng ranh giới "chỉ
   file mới, không sửa appletsrc/app khác" đã giao.
