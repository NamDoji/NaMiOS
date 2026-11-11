# NaMiOS — Wizard chào mừng lần đầu áp dụng THẬT (FIRST-RUN, UI-005)

- **Wave:** vá lỗ hổng "wizard chỉ ghi `welcome.json`, KHÔNG áp dụng gì thật", 10/11/2026.
- **verified_on_host: NO cho TOÀN BỘ file này.** Môi trường dựng không có desktop session KDE
  Plasma 6 thật (container headless). Tên khoá `kdeglobals`/giá trị enum fcitx5-unikey đã đối chiếu
  mã nguồn upstream công khai (xem mục 4/5) và đã chạy thật bằng script Python mô phỏng lệnh hệ
  thống (fake `kwriteconfig6`/`xdg-mime`/`lpoptions`/`lpstat`/`fcitx5-remote`) — CHƯA chạy qua Fcitx5/
  Plasma đóng gói thật trên Debian 13 trixie. Người cầm ISO lên máy/VM thật phải bấm thử từng dòng
  rồi điền lại checklist ở mục 7.

## 1. Vấn đề đã sửa

Trước wave này, `WelcomeWizard._on_accepted()` (`ui.py`) chỉ gọi
`ConfigApplier(self._config_dir).apply(choices)` — ghi MỘT file JSON
(`~/.config/namios/welcome.json`) ghi lại lựa chọn người dùng, rồi **dừng ở đó**. Bộ gõ Telex/VNI,
cỡ chữ, app mặc định mở docx/xlsx/pdf, máy in — KHÔNG có cơ chế nào thật sự đổi hành vi desktop.
Với người dùng ít rành kỹ thuật (đối tượng chính của NaMiOS, P0 theo đặc tả), một màn hình "xong"
mà không có gì thay đổi là trải nghiệm tệ nhất có thể — họ tin là đã chọn xong, thực tế chưa đổi gì.

## 2. File đã sửa / đã tạo

| File | Loại thay đổi |
| --- | --- |
| `opt/namios/namios_welcome-src/firstrun.py` | Thêm `RuntimeApplyOutcome`/`RuntimeApplyReport` + `apply_runtime_desktop_settings()` (logic áp thật, KHÔNG phụ thuộc GUI) + `ConfigApplier.write_apply_report()` |
| `opt/namios/namios_welcome-src/ui.py` | `_on_accepted()` gọi thêm `apply_runtime_desktop_settings()`; MỌI bước (ghi config, áp thật, chuyển dữ liệu Windows) tự bọc try/except riêng; `_mark_welcome_done()` cũng được bọc |
| `opt/namios/namios_welcome-src/__init__.py` | Re-export 4 tên mới, cập nhật docstring |
| `etc/skel/.config/autostart/namios-welcome.desktop` | Thêm đoạn comment giải thích hành vi mới (KHÔNG đổi `Exec=`/`Icon=`/bất kỳ khoá Desktop Entry nào) |
| `usr/share/namios/docs/FIRST-RUN.md` | File này (mới) |

**KHÔNG đụng:** `etc/skel/.config/{kwinrc,kdeglobals,plasmarc,appletsrc}` (sở hữu bởi wave UX khác —
xem `docs/specs/UX-WINDOWS-FAMILIAR.md`/`UX-INTERACTION.md`), `etc/skel/.config/fcitx5/profile` (sở
hữu bởi hook `0200-fcitx5-default-im.hook.chroot` — chỉ bật sẵn ENGINE Unikey, KHÔNG chọn Telex/VNI),
`etc/skel/.config/plasma-localerc` (ngôn ngữ hiển thị Plasma — xem mục 6 vì sao KHÔNG làm), hook
`0300-namios-welcome.hook.chroot`, `calamares`, bootloader, `sddm`, wine.

## 3. Nguyên tắc thiết kế: "áp được gì thì áp, áp sai còn hơn làm sập phiên"

`apply_runtime_desktop_settings()` (trong `firstrun.py`, Python thuần — test được không cần PySide6)
gọi 6 hàm `_apply_*`, mỗi hàm tự cô lập lỗi của riêng nó:

1. Luôn dùng `namios_security.run_argv` (argv-only, `shell=False`, `argv[0]` phải là đường dẫn tuyệt
   đối đã tồn tại/thực thi được qua `shutil.which`) — đúng quy ước WP8 "mọi WP khác chỉ import từ
   `namios_security`, KHÔNG tự chế subprocess riêng". KHÔNG có `curl|bash`/`eval`/nội suy chuỗi shell
   nào ở đây.
2. Thiếu lệnh hệ thống (`kwriteconfig6`/`xdg-mime`/`lpstat`/`lpoptions`/`fcitx5-remote`) → `"skipped"`,
   KHÔNG thử cách khác, KHÔNG đoán đường dẫn cố định.
3. App/máy in không tồn tại thật trên máy (desktop-entry-id không khớp file `.desktop` nào trong các
   thư mục `applications/` chuẩn XDG; máy in không có trong `lpstat -p`) → `"skipped"`, **KHÔNG** đặt
   default trỏ vào thứ không có thật.
4. Lệnh hệ thống chạy được nhưng trả mã lỗi/IO lỗi → `"failed"`, ghi lại `stderr` (đã lọc qua
   `namios_security.redact_text` trước khi lưu — report này bị ghi ra đĩa).
5. **Không có aspect nào, lỗi nào, có thể làm hàm `apply_runtime_desktop_settings()` tự nó `raise`** —
   mọi exception đều bị bắt NGAY TRONG hàm `_apply_*` tương ứng.
6. Ở tầng UI (`ui.py`), `_on_accepted()` còn bọc THÊM một lớp try/except quanh TOÀN BỘ luồng (ghi
   `welcome.json`, áp thật, chuyển dữ liệu Windows) — vì PySide6 bản gần đây **mặc định DỪNG tiến
   trình** nếu một slot Qt (nối với signal `accepted`) ném lỗi không bắt (khác Qt5 cũ chỉ in stderr).
   Một aspect áp sai/thiếu công cụ **không bao giờ** làm mất luôn các bước còn lại hay sập phiên đăng
   nhập lần đầu.

Kết quả mỗi lần áp được `ConfigApplier.write_apply_report()` ghi atomic ra
`~/.config/namios/welcome-apply-report.json` (cạnh `welcome.json`) — log để chẩn đoán sau (ví dụ công
cụ `namios-chan-doan`), KHÔNG BAO GIỜ tự nó làm hỏng wizard nếu ghi log thất bại.

## 4. Sáu khía cạnh được áp thật (chỉ áp cái wizard ĐÃ thu thập, không thêm UI mới)

| Khía cạnh (`FirstRunChoices` field) | Cơ chế áp thật | Ghi chú |
| --- | --- | --- |
| `ime_method` (Telex/VNI) | Ghi `~/.config/fcitx5/conf/unikey.conf` (`InputMethod=Telex`/`InputMethod=VNI`) + thử `fcitx5-remote -r` (không chặn nếu lỗi) | Giá trị khoá đối chiếu mã nguồn upstream `fcitx5-unikey` (`src/unikey-config.h`, `src/unikey.conf.in`) — xem mục 5 |
| `ui_scale_percent` (100/125/150) | `kwriteconfig6 --file kdeglobals --group KScreen --key ScaleFactor --type double <1.0\|1.25\|1.5>` | Cần đăng xuất/đăng nhập lại để Plasma áp dụng đầy đủ — KHÔNG khởi động lại `plasmashell` giữa phiên |
| `default_app_docx` | `xdg-mime default <desktop-id> application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Chỉ chạy nếu tìm thấy file `.desktop` thật |
| `default_app_xlsx` | `xdg-mime default <desktop-id> application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | nt |
| `default_app_pdf` | `xdg-mime default <desktop-id> application/pdf` | nt |
| `default_printer` (tuỳ chọn) | `lpstat -p <tên>` xác nhận tồn tại trong CUPS, rồi `lpoptions -d <tên>` | Bỏ qua im lặng nếu `default_printer=None` hoặc máy in chưa cấu hình |

Alias tên app → desktop-entry-id (`_DEFAULT_APP_DESKTOP_ID_ALIASES` trong `firstrun.py`) khớp đúng 3
giá trị mặc định của ô nhập (`libreoffice-writer`/`libreoffice-calc`/`okular`, xem
`docs/specs/PL09-DEFAULT-APPS.md` §3): `libreoffice-writer.desktop`, `libreoffice-calc.desktop`,
`org.kde.okular.desktop`. Giá trị KHÔNG có trong alias vẫn được thử (`<giá trị>.desktop`) nếu người
dùng gõ tên khác — KHÔNG chặn, chỉ không có phím tắt.

## 5. Vì sao TIN được tên khoá `InputMethod=Telex`/`InputMethod=VNI`

Đối chiếu trực tiếp mã nguồn công khai `fcitx/fcitx5-unikey` (GitHub, 10/11/2026):

- `src/unikey.conf.in`: addon input-method khai `Addon=unikey`, `Configurable=True`.
- `src/unikey-config.h`: `FCITX_CONFIGURATION(UnikeyConfig, OptionWithAnnotation<UkInputMethod, ...>
  im{this, "InputMethod", _("Input Method"), UkTelex}; ...)` — khoá tên `InputMethod`, không lồng
  group con nào (nên file config là key=value phẳng, không có header `[Group]`).
- `FCITX_CONFIG_ENUM_NAME_WITH_I18N(UkInputMethod, N_("Telex"), N_("VNI"), N_("VIQR"),
  N_("Microsoft Vietnamese"), N_("UserIM"), N_("Simple Telex"), N_("Simple Telex2"))` — các chuỗi này
  vừa là tên hiển thị i18n vừa là chuỗi serialize enum (quy ước chung của macro này trong toàn bộ
  fcitx5) ⇒ giá trị ghi đúng trên đĩa là `Telex`/`VNI` nguyên văn.

Mức độ chắc chắn tương đương đúng với cách hook `0200-fcitx5-default-im.hook.chroot` đã tự đánh giá
cho chính file `profile` của nó ("CHƯA xác nhận đúng cú pháp trên gói Fcitx5 đóng gói Debian 13 trixie
thực tế") — wave này áp dụng NGUYÊN mức độ thận trọng đó cho file `unikey.conf`.

## 6. Vì sao KHÔNG áp "ngôn ngữ hiển thị" hay "múi giờ" ở wizard này

`FirstRunChoices` (đã có từ trước, wave này không đổi field nào) **không có** field ngôn ngữ hay múi
giờ — UI 5 bước (`Chào mừng → Bộ gõ/Cỡ chữ → App mặc định → Chuyển dữ liệu Windows → Xong`) không có
trang nào hỏi 2 việc đó. Đúng theo chỉ đạo "không tự bịa thêm UI mới", wizard KHÔNG áp 2 khía cạnh
này. Cả hai đã có mặc định hệ thống riêng, đặt ở nơi khác, người dùng tự đổi qua System Settings:

- **Múi giờ:** `Asia/Ho_Chi_Minh` đặt lúc BUILD bởi `hooks/normal/0110-timezone.hook.chroot`
  (`/etc/localtime` + `/etc/timezone`) — áp dụng cho MỌI user trên máy, không phải lựa chọn per-user.
- **Ngôn ngữ hiển thị Plasma Shell:** mặc định tiếng Anh (`en_US.UTF-8`, quyết định Cuong 10/11/2026 —
  xem `etc/skel/.config/plasma-localerc`), tiếng Việt vẫn cài đầy đủ, người dùng tự đổi 1-click qua
  **System Settings → Region & Language** (Plasma tự ghi lại `~/.config/plasma-localerc` của họ khi
  đổi — không phải việc của `namios-welcome`).

## 7. Checklist xác nhận trên desktop KDE Plasma 6 thật (điền khi có máy, không tự đánh dấu trước)

- [ ] Chạy `namios-welcome`, chọn Telex, bấm Hoàn tất → `~/.config/fcitx5/conf/unikey.conf` có
      `InputMethod=Telex`; mở ứng dụng gõ thử dấu tiếng Việt kiểu Telex ra đúng chữ (không cần đăng
      xuất lại nếu `fcitx5-remote -r` chạy được)
- [ ] Lặp lại với VNI → file đổi thành `InputMethod=VNI`, gõ kiểu VNI ra đúng chữ
- [ ] Chọn cỡ chữ 125%/150% → `kreadconfig6 --file kdeglobals --group KScreen --key ScaleFactor` trả
      đúng `1.25`/`1.5`; đăng xuất/đăng nhập lại → Plasma hiển thị to hơn đúng tỉ lệ
- [ ] Giữ nguyên tên app mặc định (libreoffice-writer/libreoffice-calc/okular) → mở file `.docx`/
      `.xlsx`/`.pdf` từ Dolphin mở đúng app đó, không hiện hộp thoại "chọn ứng dụng"
    - [ ] Gõ sai tên app (app không tồn tại) → KHÔNG đổi gì, kiểm tra
          `~/.config/namios/welcome-apply-report.json` có `"status": "skipped"` đúng aspect đó
- [ ] Gõ tên máy in CHƯA cấu hình trong CUPS → report ghi `"skipped"`, KHÔNG đặt default sai
- [ ] Gõ tên máy in ĐÃ cấu hình trong CUPS → `lpoptions -p default` (hoặc `lpstat -d`) xác nhận đúng
      máy in đã chọn
- [ ] Bấm "Hủy" giữa wizard (không hoàn tất) → `~/.config/namios/welcome-done` vẫn được tạo (đăng
      nhập lần sau KHÔNG tự mở lại wizard — đúng "tiếp cận nhẹ nhàng", xem `firstrun.py`)
- [ ] Gỡ tạm `kwriteconfig6`/`xdg-mime`/`lpoptions` khỏi `PATH` (mô phỏng ảnh thiếu gói) rồi chạy lại
      wizard → KHÔNG crash, mọi aspect liên quan rơi về `"skipped"` trong report
- [ ] Chạy `namios-welcome` lại lần 2 bằng tay (lệnh thủ công) với CÙNG lựa chọn → ghi đè idempotent,
      không lỗi, không tạo file rác `.tmp-*` còn sót (atomic write + `os.replace` đúng thiết kế)
