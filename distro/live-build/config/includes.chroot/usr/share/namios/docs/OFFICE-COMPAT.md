# NaMiOS — NaMiOffice tương thích Microsoft Office (OFFICE-COMPAT)

- **Wave:** "Office như kế toán/tài chính cần" — ưu tiên CAO NHẤT của Cuong (10/11/2026):
  (a) phím tắt Word/Excel giống Microsoft Office nhất có thể, (b) Calc tương
  thích Excel (cú pháp công thức + tên hàm tiếng Anh + bao phủ hàm đủ rộng).
- **File này SHIP TRONG ISO** (`/usr/share/namios/docs/OFFICE-COMPAT.md`) — khác
  với `docs/support/OFFICE-COMPAT.md`/`docs/support/OFFICE-SUITE.md` trong repo
  (chỉ đọc được từ máy dev, không có trên máy người dùng cuối). File này là bản
  tóm tắt "sống cùng ISO" để người dùng/support mở trực tiếp trên NaMiOS.
- **verified_on_host: NO cho TOÀN BỘ file này.** Mọi khoá registry + phím tắt
  dưới đây đối chiếu trực tiếp với **mã nguồn LibreOffice thật** (file
  `officecfg/registry/data/org/openoffice/Office/Accelerators.xcu` và
  `framework/source/accelerators/keymapping.cxx` trên nhánh `master` của
  `github.com/LibreOffice/core`) + **trang phím tắt chính thức của Microsoft**
  (`support.microsoft.com`, "Keyboard shortcuts in Excel"/"...in Word") +
  một ví dụ `registrymodifications.xcu` THẬT bắt được từ một user LibreOffice
  (GitHub `rhoconlinux/Libreoffice-elementary-config`) để xác nhận đúng cú
  pháp `oor:path`. **CHƯA** build `lb build` + mở LibreOffice thật trên NaMiOS
  để xác nhận các khoá này được nạp đúng — xem checklist mục 6.

## 0. Kết luận chính (đọc trước)

1. **Calc = tương thích Excel đã CÓ SẴN từ trước** (cú pháp công thức Excel A1 +
   tên hàm tiếng Anh + lưu mặc định `.xlsx/.docx/.pptx`) — wave này KHÔNG đổi,
   chỉ nhân bản thêm lớp phòng hộ toàn hệ thống + viết lại rõ trong tài liệu
   ship-trong-ISO này.
2. **Phím tắt kiểu Office** — wave này tìm ra: **nhiều phím đã khớp sẵn** với
   Excel/Word mà không cần sửa (xem mục 3.1), và **thêm 11 phím còn thiếu/sai**
   cho Calc + Writer (mục 3.2), tất cả đối chiếu với trang phím tắt chính thức
   của Microsoft — không đoán.
3. **Bao phủ hàm** — gói `libreoffice` (metapackage Debian) đã kéo đủ 6 module +
   hàm tài chính/thống kê/tra cứu cần thiết, **không cần thêm gói nào** (mục 4).
4. **Khoảng trống THẬT không che** — macro VBA, mảng động/LAMBDA, pixel-perfect
   layout — xem mục 5, không hứa hẹn quá mức.

## 1. File đã sửa / đã tạo trong wave này

| File | Loại thay đổi |
| --- | --- |
| `usr/lib/libreoffice/share/registry/data/registrymodifications-system-wide.xcu` | **File mới** — lớp đăng ký LibreOffice toàn hệ thống (áp mọi user, không phụ thuộc `/etc/skel`): mirror 6 khoá Excel-compat đã có + 13 khoá phím tắt mới |
| `etc/skel/.config/libreoffice/4/user/registrymodifications.xcu` | Thêm comment trỏ sang file toàn-hệ-thống trên — **không đổi** 6 khoá Excel-compat đã có từ trước (đã đúng, không cần sửa) |
| `usr/share/namios/docs/OFFICE-COMPAT.md` | File này (mới) |

Không đổi package-lists (`0400-office-browser.list.chroot`) — gói đã đủ, xem mục 4.

## 2. Calc = Excel-compatible (cú pháp công thức + tên hàm)

Đã có sẵn từ wave trước, **xác nhận ĐÚNG** theo tài liệu LibreOffice (`Calc >
Formula` ánh xạ 1-1 các khoá `org.openoffice.Office.Calc/Formula/Syntax`):

| # | Khoá registry | Giá trị | Tác dụng |
|---|---|---|---|
| 1 | `Calc/Formula/Syntax/Grammar` | `1` | Cú pháp công thức **Excel A1** (0=Calc A1, 1=Excel A1, 2=Excel R1C1) |
| 2 | `Calc/Formula/Syntax/StringRefAddressSyntax` | `1` | Chuỗi tham chiếu `INDIRECT`/`ADDRESS` kiểu **Excel A1** |
| 3 | `Calc/Formula/Syntax/EnglishFunctionName` | `true` | **Luôn dùng tên hàm tiếng Anh** (SUM, VLOOKUP, PMT…) như Excel, không dịch |
| 4 | `Calc/Formula/Load/OOXMLRecalcMode` + `ODFRecalcMode` | `0` | Luôn tính lại công thức khi mở file, không hỏi |
| 5 | `Setup/.../Factory[Spreadsheet].ooSetupFactoryDefaultFilter` | `Calc MS Excel 2007 XML` | Lưu mặc định sang `.xlsx` |
| 6 | `Common/Security/Scripting/MacroSecurityLevel` | `1` | Macro mức Trung bình — hỏi trước khi chạy, giống Office |

Nạp ở **2 lớp** (phòng hộ kép, xem lý do ở mục 1 của file
`registrymodifications-system-wide.xcu`):
`/etc/skel/.config/libreoffice/4/user/registrymodifications.xcu` (đã chạy thật
qua các wave trước, áp cho user `user` mỗi lần live-config tạo lại hồ sơ) +
`/usr/lib/libreoffice/share/registry/data/registrymodifications-system-wide.xcu`
(lớp toàn hệ thống mới, áp kể cả hồ sơ user đã tồn tại từ trước — cơ chế xác
nhận qua trao đổi dev LibreOffice công khai, 04/2019).

## 3. Phím tắt kiểu Microsoft Office

### 3.1. Đã khớp Excel/Word SẴN (không cần sửa gì) — xác nhận bằng mã nguồn

| Phím | Calc (LibreOffice gốc) | Excel thật | Kết luận |
|---|---|---|---|
| `F2` | `.uno:SetInputMode` (sửa nội dung ô) | Sửa ô tại chỗ | ✅ khớp sẵn |
| `Ctrl+1` | `.uno:FormatCellDialog` | Format Cells | ✅ khớp sẵn |
| `F4` (khi sửa công thức) | `.uno:ToggleRelative` | Xoay vòng tham chiếu tương đối/tuyệt đối | ✅ khớp sẵn |
| `Ctrl+;` | `.uno:InsertCurrentDate` | Chèn ngày hiện tại | ✅ khớp sẵn |
| `Ctrl+Shift+;` | `.uno:InsertCurrentTime` | Chèn giờ hiện tại | ✅ khớp sẵn |
| `Ctrl+Shift+L` | `.uno:DataFilterAutoFilter` | Bật/tắt AutoFilter | ✅ khớp sẵn |
| `` Ctrl+` `` | `.uno:ToggleFormula` | Show Formulas | ✅ khớp sẵn |

### 3.2. Phím THÊM/SỬA trong wave này — mỗi dòng có nguồn đối chiếu

File: `usr/lib/libreoffice/share/registry/data/registrymodifications-system-wide.xcu`.

**Calc (`com.sun.star.sheet.SpreadsheetDocument`):**

| Phím | Lệnh `.uno:` | Khớp Excel | Vì sao phải thêm |
|---|---|---|---|
| `Ctrl+Shift+1` | `NumberFormatDecimal` (Number) | Ctrl+Shift+! | Có sẵn trong LibreOffice gốc nhưng **chỉ build cho Windows/macOS** (`install:module`), bản Linux/NaMiOS không có |
| `Ctrl+Shift+2` | `NumberFormatTime` (Time) | Ctrl+Shift+@ | Bản Windows/macOS gốc của LibreOffice xếp **SAI** vị trí này là "Scientific" — NaMiOS xếp đúng theo Excel thật |
| `Ctrl+Shift+3` | `NumberFormatDate` (Date) | Ctrl+Shift+# | Giống lý do Ctrl+Shift+1 (thiếu trên Linux) |
| `Ctrl+Shift+4` | `NumberFormatCurrency` (Currency) | Ctrl+Shift+$ | Giống lý do Ctrl+Shift+1 |
| `Ctrl+Shift+5` | `NumberFormatPercent` (Percent) | Ctrl+Shift+% | Giống lý do Ctrl+Shift+1 |
| `Ctrl+Shift+6` | `NumberFormatScientific` (Scientific) | Ctrl+Shift+^ | Bản Windows/macOS gốc xếp **SAI** vị trí này là "General" |
| `` Ctrl+Shift+` `` | `NumberFormatStandard` (General) | Ctrl+Shift+~ | Excel đặt General ở phím dấu huyền (`~`), không phải số 6 — NaMiOS xếp đúng |
| `Ctrl+9` | `HideRow` | Ctrl+9 = Hide rows | Chưa gán gì cho en-US trên Calc |
| `Ctrl+0` | `HideColumn` | Ctrl+0 = Hide columns | Chưa gán gì trên Calc |
| `Shift+F2` | `EditAnnotation` (chú thích) | Shift+F2 = Add/edit comment | Calc chỉ có `Ctrl+Alt+C` (vẫn giữ), thêm Shift+F2 cho khớp Excel |
| `Ctrl+Alt+V` | `PasteSpecial` | Ctrl+Alt+V = Paste Special dialog | Chưa gán gì; `Ctrl+Shift+V` cũ vẫn giữ (cũng mở Paste Special) |

**Writer (`com.sun.star.text.TextDocument`):**

| Phím | Lệnh `.uno:` | Khớp Word | Vì sao phải sửa |
|---|---|---|---|
| `Ctrl+Shift+V` | `PasteUnformatted` (**đổi từ** `PasteSpecial`) | Word: "Paste without formatting → Ctrl+Shift+V" | Writer gốc mở HỘP THOẠI khi bấm tổ hợp này; Word thật **dán ngay, không hỏi** — đổi lại cho khớp hành vi thật |
| `Ctrl+Alt+V` | `PasteSpecial` (mới) | Quy ước Paste Special xuyên bộ Office (đã xác nhận riêng cho Excel ở trên) | Sau khi đổi Ctrl+Shift+V ở trên, cần phím riêng cho hộp thoại Paste Special. **Thành thật:** trang Word hiện tại của Microsoft không liệt kê rõ Ctrl+Alt+V cho bản Windows — đây là **tiện ích nhất quán NaMiOffice**, không khẳng định là phím Word đang công bố chính thức |

Cú pháp phím tắt dùng mã định danh của chính LibreOffice (bảng tra cứu gốc
`framework/source/accelerators/keymapping.cxx`, KHÔNG có mã riêng cho `!@#$%^` —
các ký tự đó vốn là Shift+số nên `Ctrl+Shift+1` chính là `Ctrl+Shift+!`).

## 4. Bao phủ hàm (function coverage)

Gói Debian cài: `libreoffice` — metapackage kéo đủ **Writer/Calc/Impress/Draw/
Base/Math** (không phải bản rút gọn), cộng `libreoffice-l10n-vi` +
`libreoffice-help-vi` (`distro/live-build/config/package-lists/
0400-office-browser.list.chroot`). **Không cần thêm gói nào** cho hàm tài
chính/thống kê — PMT/FV/PV/NPV/IRR/RATE là hàm **lõi** của Calc hiện đại (không
còn cần add-in "Analysis ToolPak" như OpenOffice.org cũ).

File tự kiểm có sẵn trong ISO: `usr/share/namios/demo/KiemTra_Ham_Office.xlsx`
— 79 hàm tự so khớp khi mở bằng Calc (chi tiết: `docs/support/OFFICE-COMPAT.md`
trong repo, mục 1-2).

## 5. Khoảng trống THẬT — không hứa hẹn quá mức

- **Macro VBA**: LibreOffice Basic mô phỏng VBA **một phần**. `UserForm`,
  ActiveX, API `Application.*`, add-in `.xlam` **không chạy hoặc chạy sai**.
  Đây KHÔNG phải phím tắt sửa được — là khoảng trống engine, lớn nhất với
  bảng tính/văn bản nghiệp vụ nặng macro.
- **Mảng động / LAMBDA** (`FILTER/SORT/UNIQUE/SEQUENCE/LET/LAMBDA`,
  `#SPILL!`): LibreOffice **25.2.3** (bản cài trong ISO) **CHƯA** có engine
  tràn ô (spill) — các công thức này không tính đúng, chỉ hiện giá trị cache
  cũ nếu có. Không phải lỗi phím tắt. Chi tiết: `docs/office/COMPAT-MATRIX.md`
  (SH-F1-01/02/04/05).
- **XLOOKUP**: có từ LibreOffice 24.8+, bản 25.2.3 tính gần đúng Excel.
- **Pixel-perfect layout**: thiếu font Microsoft (Calibri, Cambria, Segoe UI)
  → font thay thế → lệch dòng/ngắt trang nhẹ, rõ nhất ở văn bản/trình chiếu
  trình bày dày.
- **Phím tắt Ctrl+Alt+V cho Writer** (mục 3.2): chưa xác nhận là phím Word
  Windows đang công bố chính thức — chỉ là tiện ích nhất quán nội bộ NaMiOffice.
- **Unhide rows/columns** (`Ctrl+Shift+9`/`Ctrl+Shift+0` trong Excel): trang
  phím tắt Windows hiện tại của Microsoft KHÔNG liệt kê tổ hợp này rõ ràng (chỉ
  thấy ở mục macOS) — **CHƯA thêm** vào NaMiOS vì không đủ nguồn xác nhận chắc
  chắn, để tránh bịa. TODO: xác nhận lại khi có bản Windows Excel thật để so,
  rồi bổ sung vào `registrymodifications-system-wide.xcu` mục [8].

## 6. Phải xác nhận bằng mắt trên ISO đã build

`verified_on_host: NO`. Khi có ISO build thật (QEMU/máy thật):

1. Mở **Calc**: `Tools > Options > LibreOffice Calc > Formula` — "Formula
   syntax" phải hiện **Excel A1**, "Use English function names" phải **tick**.
2. Mở `KiemTra_Ham_Office.xlsx` — ô TỔNG KẾT lý tưởng 79/79 ✅.
3. Trong Calc, bấm **Ctrl+Shift+1** trên một ô số — phải đổi định dạng sang
   "Number" (2 chữ số thập phân). Thử tiếp Ctrl+Shift+2 (Time) .. Ctrl+Shift+6
   (Scientific) và **Ctrl+Shift+`** (General).
4. Bấm **Ctrl+9** trên dòng đã chọn — dòng phải ẩn. **Ctrl+0** trên cột — cột
   phải ẩn.
5. Bấm **Shift+F2** trên một ô — phải mở hộp chú thích (comment).
6. Bấm **Ctrl+Alt+V** trong Calc VÀ Writer — phải mở hộp thoại Paste Special.
7. Trong **Writer**, copy văn bản có định dạng từ nơi khác, bấm **Ctrl+Shift+V**
   — phải dán NGAY dạng chữ thường (không mở hộp thoại, không hỏi).
8. Nếu bước nào KHÔNG đúng: kiểm `/usr/lib/libreoffice/share/registry/data/`
   có tồn tại file `registrymodifications-system-wide.xcu` không (gói Debian
   có thể không tạo sẵn thư mục `data/`) — nếu thiếu, lớp `/etc/skel/...` vẫn
   còn giữ 6 khoá Excel-compat cơ bản (mục 2), nhưng 13 phím tắt mới (mục 3.2)
   sẽ KHÔNG hoạt động và cần chuyển hẳn sang ghi trực tiếp vào file skel thay
   cho lớp toàn hệ thống.

Khi đã xem trên máy thật và đạt, đổi `verified_on_host: NO` → `YES (ngày,
phiên bản LibreOffice)` ở đầu file này.
