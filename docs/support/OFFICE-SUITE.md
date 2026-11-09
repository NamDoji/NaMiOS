# NaMiOffice — bộ Office đầy đủ (Word, Excel, PowerPoint, Access, …)

**Yêu cầu:** Cuong (10/11/2026): *"ngoài Word, Excel thì còn *.ppt và những
phần của bộ office Microsoft thì NaMiOffice đều có và hoạt động xuất sắc."*
**Trạng thái:** `partial` — bộ ứng dụng đầy đủ (gói Debian `libreoffice` là
metapackage đủ 6 module), định dạng lưu mặc định + liên kết file đã cấu hình
kiểu Office, file demo PowerPoint thật đã dựng. **CHƯA xác nhận trên máy
thật** (`verified_on_host: NO`) — xem mục 5.

> **Sự thật nền tảng (APP-OFF-006 — nhắc lại).** NaMiOffice = LibreOffice
> rebrand hiển thị (đổi tên menu/splash/About, xem
> `docs/branding/NAMIOFFICE.md`), **KHÔNG** phải Microsoft Office build lại.
> LibreOffice **mở/soạn/lưu** được định dạng Office với độ tương thích cao
> nhưng có khoảng trống đã biết (mục 4). Tài liệu này mô tả **toàn bộ suite**
> (không chỉ Calc/Excel như `OFFICE-COMPAT.md`).

---

## 1. Ánh xạ Microsoft Office → NaMiOffice

| Microsoft Office | NaMiOffice | Vai trò | Ghi chú |
|---|---|---|---|
| **Word** | **Writer** | Soạn thảo văn bản | Đầy đủ |
| **Excel** | **Calc** | Bảng tính | Đầy đủ — xem `OFFICE-COMPAT.md` (79 hàm tự kiểm) |
| **PowerPoint** | **Impress** | Trình chiếu | Đầy đủ — xem mục 3 (file demo `.pptx` mới) |
| **Access** | **Base** | Cơ sở dữ liệu | Hạn chế với `.accdb`/`.mdb` — xem mục 4 |
| **Publisher** | **Draw** | Dàn trang/vẽ/sơ đồ | Draw không phải bản sao Publisher 1-1; đủ cho vẽ sơ đồ, poster, dàn trang đơn giản |
| *(không có trong Office)* | **Math** | Soạn công thức toán học | Công cụ riêng của LibreOffice, Office không có module tương đương; Word có "Equation Editor" dùng chung chuẩn OMML — Math đọc/ghi được công thức OMML cơ bản |
| **Outlook** | *(không có 1:1)* | Email + lịch | **10/11/2026 — cập nhật:** NaMiOS nay đóng gói **NaMiMail (dựa trên Mozilla Thunderbird)** làm client mail/lịch/danh bạ ngày-1, nằm **ngoài** metapackage `libreoffice` (gói riêng `thunderbird`+`thunderbird-l10n-vi`, `0405-mail-notes.list.chroot`) — vẫn **không** phải tính năng của "bộ Office". **KHÔNG** gọi là "tương thích Outlook/Exchange". Chi tiết + việc còn lại (rebrand UI, kiểm host thật): `docs/office/ECOSYSTEM-MAIL-NOTES-FORMS.md` §1. |

Gói Debian cài: `libreoffice` (metapackage — kéo đủ Writer/Calc/Impress/Draw/
Base/Math) + `libreoffice-l10n-vi` + `libreoffice-help-vi`
(`distro/live-build/config/package-lists/0400-office-browser.list.chroot`).
Tên hiển thị đổi sang "NaMiOffice …" qua hook `0450-namioffice-brand.hook.chroot`
(chỉ sửa `Name=`/`GenericName=` trong `.desktop`, giữ nguyên `Exec=`/`MimeType=`).

---

## 2. Cấu hình "quen tay như Office" đã bật sẵn

### 2a. Định dạng lưu mặc định (registrymodifications.xcu)

File: `etc/skel/.config/libreoffice/4/user/registrymodifications.xcu`
(áp cho **mọi user mới** qua `/etc/skel`). Ba filter mặc định:

| Ứng dụng | `ooSetupFactoryDefaultFilter` | Lưu mặc định sang |
|---|---|---|
| Calc | `Calc MS Excel 2007 XML` | `.xlsx` |
| Writer | `MS Word 2007 XML` | `.docx` |
| Impress | `Impress MS PowerPoint 2007 XML` | `.pptx` |

Cộng thêm (đã có từ trước, không đổi): cú pháp công thức Excel A1 + tên hàm
tiếng Anh + luôn tính lại công thức khi mở file + bảo mật macro mức
"Trung bình" — xem `OFFICE-COMPAT.md` mục 3 cho bảng đầy đủ.

### 2b. Liên kết file (double-click mở đúng NaMiOffice)

File: `etc/skel/.config/mimeapps.list` (áp cho mọi user mới qua `/etc/skel`).

Ánh xạ MIME type → `.desktop`:

| Định dạng | MIME type | Mở bằng |
|---|---|---|
| `.doc` | `application/msword` | `libreoffice-writer.desktop` |
| `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `libreoffice-writer.desktop` |
| `.xls` | `application/vnd.ms-excel` | `libreoffice-calc.desktop` |
| `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | `libreoffice-calc.desktop` |
| `.ppt` / `.pps` | `application/vnd.ms-powerpoint` | `libreoffice-impress.desktop` |
| `.pptx` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` | `libreoffice-impress.desktop` |
| `.ppsx` | `application/vnd.openxmlformats-officedocument.presentationml.slideshow` | `libreoffice-impress.desktop` |
| `.odt`/`.ods`/`.odp` | tương ứng `opendocument.text`/`spreadsheet`/`presentation` | Writer/Calc/Impress |
| `.pdf` | `application/pdf` | `org.kde.okular.desktop` |

**Nói thẳng:** gói Debian `libreoffice-writer.desktop`/`calc`/`impress`
**đã tự khai báo** các `MimeType=` này — hook `0450` không sửa dòng đó, nên
association thường TỰ hoạt động ngay cả không có `mimeapps.list`. File này
làm việc gán **chắc chắn/xác định** (không phụ thuộc alphabet hay thứ tự nạp
nhiều `.desktop` cùng khai một MIME) — lớp "khoá chắc" thêm vào, không phải
điều kiện bắt buộc duy nhất.

---

## 3. Demo PowerPoint thật (mới — mảnh còn thiếu trước đây)

- Script sinh: `tools/demo/make-demo-pptx.py` (dùng `python-pptx` 1.0.2).
- File ra: `usr/share/namios/demo/GioiThieu_NaMiOffice.pptx` — 4 slide:
  1. Trang bìa "NaMiOffice — Trình chiếu".
  2. Danh sách 6 ứng dụng (Writer/Calc/Impress/Draw/Base/Math).
  3. **Biểu đồ cột nguyên sinh** (native OOXML chart, không phải ảnh dán) —
     "Doanh thu theo quý", 4 cột.
  4. Bảng ánh xạ Microsoft Office → NaMiOffice (5 dòng).
- Màu theo bộ nhận diện **Sen Việt** (ngà/đỏ son/đỏ đài/vàng tâm/mực).
- Hook `0500-qemu-demo-open-apps.hook.chroot` đã đổi: lần boot QEMU demo kế
  tiếp **tự mở Impress với file `.pptx` này** (trước đây mở Calc) — mục đích
  CHỨNG MINH PowerPoint/Impress render đúng trong ảnh chụp CI, không chỉ Calc.
  Hai file `.xlsx` demo cũ (`BaoCao_KinhDoanh_Q4_2026.xlsx`,
  `KiemTra_Ham_Office.xlsx`) **vẫn còn** trong thư mục demo để người dùng mở
  tay, chỉ đổi file tự mở lúc đăng nhập đầu.
- Tự kiểm: script dùng `python-pptx` **mở lại** chính file vừa ghi và kiểm
  `len(slides) == 4` ngay trong `tools/demo/make-demo-pptx.py` — bắt lỗi cấu
  trúc OOXML sớm, nhưng KHÔNG thay được việc nhìn bằng mắt Impress thật.

---

## 4. Ma trận định dạng hỗ trợ + khoảng trống ĐÃ BIẾT (trung thực)

| Định dạng | Mở | Lưu | Độ tin cậy |
|---|---|---|---|
| `.doc` / `.docx` | ✅ | ✅ | Cao — layout/font có thể trôi nhẹ nếu thiếu font Microsoft |
| `.xls` / `.xlsx` | ✅ | ✅ | Cao — xem `OFFICE-COMPAT.md` (79 hàm, macro VBA là khoảng trống lớn nhất) |
| `.ppt` / `.pptx` | ✅ | ✅ | Khá cao cho nội dung tĩnh (text/bảng/biểu đồ/ảnh); xem cảnh báo dưới cho animation/SmartArt |
| `.pps` / `.ppsx` | ✅ | ✅ | Giống `.ppt`/`.pptx` — chỉ khác cờ "mở ở chế độ trình chiếu", không khác engine render |
| `.odt` / `.ods` / `.odp` | ✅ | ✅ | Cao nhất — định dạng gốc của LibreOffice |
| `.accdb` (Access 2007+) | ⚠️ Hạn chế | ⚠️ Hạn chế | Base **không** có driver `.accdb` gốc; cần `mdbtools`/ODBC ngoài, KHÔNG có sẵn trong gói `libreoffice` cài ở mục 1 |
| `.mdb` (Access cũ) | ⚠️ Hạn chế | ❌ | Tương tự `.accdb`, qua `mdbtools` mới đọc được, không cài sẵn |

### Khoảng trống ĐÃ BIẾT (không hứa chạy hoàn hảo)

- **VBA macro**: LibreOffice mô phỏng VBA **một phần** (LibreOffice Basic +
  tương thích VBA hạn chế). `UserForm`, ActiveX, API `Application.*`, add-in
  `.xlam`/`.pptm` có macro phức tạp **không chạy hoặc chạy sai**. Áp dụng cho
  cả Writer/Calc/Impress, không riêng Calc.
- **Animation & transition PowerPoint**: Impress đọc được animation/transition
  OOXML cơ bản (fade, appear, fly-in...) nhưng **không bảo đảm khớp 100%**
  với PowerPoint thật ở timing/easing — một số hiệu ứng nâng cao (morph,
  animation path phức tạp) có thể render khác hoặc mất.
- **SmartArt**: PowerPoint SmartArt là đối tượng riêng của Microsoft (XML
  `dgm:`); Impress **không render được SmartArt như đồ hoạ động** — thường
  hiện lại dưới dạng ảnh tĩnh hoặc nhóm hình vẽ rời, mất khả năng edit cấu
  trúc SmartArt gốc.
- **`.accdb`/`.mdb` (Access)**: xem bảng trên — Base không có driver gốc
  trong gói cài sẵn; cần cài thêm `mdbtools`/driver ODBC ngoài phạm vi ISO
  hiện tại.
- **OLE nhúng + PivotTable/PivotChart nâng cao**: mở được nhưng có thể mất
  một phần định dạng/tuỳ chọn khi round-trip (mở → lưu lại) — kế thừa từ
  `OFFICE-COMPAT.md`, áp dụng chung cho tài liệu nhúng biểu đồ/bảng Excel
  trong Writer/Impress.
- **Font & layout drift**: thiếu font Microsoft (Calibri, Cambria, Segoe UI…)
  → thay font hệ thống → lệch dòng/ngắt trang/khung văn bản nhẹ, rõ nhất ở
  slide trình chiếu trình bày dày chữ.

---

## 5. Phải xác nhận bằng mắt trên ISO đã build

`verified_on_host: NO` cho toàn bộ tài liệu này. Việc cần làm khi có ISO build
thật trong QEMU/máy thật:

1. Boot ISO, đăng nhập lần đầu → xác nhận autostart tự mở **Impress** với
   `GioiThieu_NaMiOffice.pptx` (hook `0500`), không còn mở Calc.
2. Soi 4 slide bằng mắt: chữ tiếng Việt không vỡ font, biểu đồ cột render
   đúng số liệu, bảng hiển thị đủ 5 dòng, màu Sen Việt không lệch (không có
   nền đen).
3. Double-click thử 1 file `.docx`/`.xlsx`/`.pptx`/`.ppsx` bất kỳ ngoài demo
   → xác nhận mở đúng Writer/Calc/Impress (không rơi về app khác do
   `mimeapps.list` sai desktop-file-id).
4. Mở `Base` thử tạo 1 database `.odb` mới (không cần `.accdb` thật) để xác
   nhận module khởi động được.
5. Nếu có file `.pptx`/`.ppt` thật có animation/SmartArt từ PowerPoint —
   mở thử, ghi lại đúng/sai cụ thể để cập nhật mục 4 (đừng chỉ đoán).

Khi đã xem trên máy thật và đạt, đổi `verified_on_host: NO` → `YES (ngày,
phiên bản LibreOffice)` ở đầu file.
