# Tương thích hàm/định dạng Office trong NaMiOS (LibreOffice Calc ↔ Microsoft Excel)

**Trạng thái:** `partial` — tương thích **cao nhưng KHÔNG 100%**. Đo được bằng
bảng tính tự chấm, **chưa xác nhận trên máy thật** (`verified_on_host: NO`).
**Ngày:** 09/11/2026.
**Phiên bản LibreOffice trong ISO:** **25.2.3** (Debian 13 trixie,
`libreoffice` = `4:25.2.3-2+deb13u8`; xem
`distro/live-build/config/package-lists/0400-office-browser.list.chroot`).

> **Sự thật nền tảng (APP-OFF-006).** LibreOffice là **sản phẩm KHÁC** với
> Microsoft Office. Cài LibreOffice **không** đồng nghĩa "đã đạt yêu cầu chạy
> Microsoft Word/Excel". LibreOffice **mở, tính và lưu** được `.xlsx/.docx/.pptx`
> với độ tương thích cao, nhưng vẫn có **khoảng trống đã biết** (macro VBA, vài
> hàm Office-365 rất mới, một số định dạng/pivot phức tạp, trôi font/layout).
> Tài liệu này **ĐO** độ tương thích đó thay vì hứa hẹn.

---

## 1. Cách NaMiOS ĐO độ tương thích

File tự kiểm: `usr/share/namios/demo/KiemTra_Ham_Office.xlsx`
(sinh bởi `tools/demo/make-office-compat-test.py`).

- Bao phủ **79 hàm** thuộc 7 nhóm: Toán, Thống kê, Logic, Tra cứu, Văn bản,
  Ngày-giờ, Tài chính.
- Mỗi hàm có **1 ô "Kết quả" = công thức SỐNG** → LibreOffice Calc **tự tính**
  khi mở file (workbook bật `fullCalcOnLoad`, và `.xcu` đặt "luôn tính lại khi mở").
- Mỗi hàm có **1 ô "Kết quả đúng" = giá trị kỳ vọng được TÍNH ĐỘC LẬP bằng
  Python** ngay trong script sinh file (không nhờ Calc). Đây là chuẩn đối chiếu.
- Ô **"Khớp?"** so hai cột trên:
  - số: `=IF(ROUND(KếtQuả-KếtQuảĐúng,6)=0,"✅ OK","❌ SAI")`
  - chữ: `=IF(EXACT(KếtQuả,KếtQuảĐúng),"✅ OK","❌ SAI")`
- Ô **"TỔNG KẾT"** đếm `COUNTIF(... ,"✅ OK")` / 79 và số ô `❌ SAI`.

**Đọc kết quả:** mở file trên ISO → hàm nào Calc tính đúng hiện **✅**, hàm nào
Calc tính lệch (hoặc không hỗ trợ) hiện **❌** — nhìn một phát biết ngay. Số liệu
trong file là **minh hoạ**, không phải dữ liệu thật.

> Hàm **động** `TODAY()/NOW()` không so được với hằng số nên được kiểm bằng điều
> kiện logic (`TODAY()>DATE(2000,1,1)` → "OK").

---

## 2. Ma trận tương thích (trung thực)

### ✅ Chạy tốt (kỳ vọng ✅ trên ISO)
- **79 hàm** trong bảng tự kiểm, gồm:
  - Toán: SUM, SUMIF, SUMIFS, SUMPRODUCT, ROUND/UP/DOWN, MOD, POWER, SQRT, ABS,
    INT, CEILING, FLOOR, PRODUCT.
  - Thống kê: AVERAGE(IF), COUNT/A/IF/IFS, MAX, MIN, MEDIAN, STDEV, VAR, RANK,
    LARGE, SMALL, PERCENTILE.
  - Logic: IF, IFS, AND, OR, NOT, IFERROR, IFNA, SWITCH, XOR.
  - Tra cứu: VLOOKUP, HLOOKUP, INDEX, MATCH, **XLOOKUP**, CHOOSE, OFFSET, INDIRECT.
  - Văn bản: LEFT, RIGHT, MID, LEN, TRIM, UPPER, LOWER, PROPER, CONCAT, TEXTJOIN,
    SUBSTITUTE, REPLACE, FIND, SEARCH, TEXT, VALUE, REPT.
  - Ngày-giờ: DATE, YEAR, MONTH, DAY, TODAY, EOMONTH, DATEDIF, WEEKDAY, NETWORKDAYS.
  - Tài chính: PMT, FV, PV, NPV, IRR, RATE.
- **Mở + lưu** `.xlsx`, `.docx`, `.pptx` (đã đặt làm định dạng lưu mặc định).
- Công thức, tham chiếu liên sheet, định dạng số/ngày/tiền tệ cơ bản, biểu đồ cột
  đơn giản, freeze panes, merge cell.

### ⚠️ Có khác biệt / cần để ý
- **XLOOKUP (tra cứu vô hướng)**: có từ **LibreOffice 24.8+**, bản 25.2.3 tính gần
  như Excel → mức **C1**.
- **LET, LAMBDA và MẢNG ĐỘNG "tràn ô" (spill: FILTER/SORT/UNIQUE/SEQUENCE/
  BYROW/MAP…)**: ⚠️ **ĐÍNH CHÍNH** khẳng định cũ (từng ghi nhầm "25.2.3 hỗ trợ").
  **LibreOffice 25.2 CHƯA có engine spill/LAMBDA** → các công thức này **không tính
  đúng** (báo lỗi hoặc chỉ hiện giá trị cache đã lưu trong file), **không** phải
  "đã hỗ trợ". Xếp **C3** trong `docs/office/COMPAT-MATRIX.md` (SH-F1-01/02/04/05).
- **`TEXT()` và dấu phân tách theo LOCALE**: định dạng như `#,##0.00` cho ra dấu
  "." hay "," tuỳ locale (vi dùng "." ngàn, "," thập phân). Trong file tự kiểm,
  TEXT được kiểm bằng mẫu **số-thuần** (`"000"`) để không phụ thuộc locale.
- **`INDIRECT()` theo cú pháp tham chiếu**: nhạy với thiết lập cú pháp chuỗi.
  `.xcu` đã đặt **Excel A1** để `INDIRECT("Sheet!A1")` chạy như Excel.
- Hàm tiền tệ **IRR/RATE** là lặp số học → có thể lệch ở chữ số rất nhỏ; ngưỡng
  so sánh `ROUND(...,6)` đủ rộng để vẫn ✅.

### ❌ Khoảng trống ĐÃ BIẾT (không hứa chạy đúng)
- **Macro VBA**: LibreOffice chạy LibreOffice Basic và **mô phỏng VBA một phần**.
  Nhiều `UserForm`, điều khiển **ActiveX**, API Office (`Application.*`), tham
  chiếu COM, add-in `.xlam` **không chạy** hoặc chạy sai. Đây là khoảng trống lớn
  nhất với bảng tính nghiệp vụ nặng macro.
- **Office-365 rất mới**: một số hàm/ngữ nghĩa mảng động mới ra sau mốc 25.2 có
  thể thiếu hoặc khác (phụ thuộc phiên bản).
- **Định dạng có điều kiện phức tạp** (data bar/icon set/biểu thức lồng) và
  **PivotTable/PivotChart** nâng cao: mở được nhưng **có thể mất một phần định
  dạng/tuỳ chọn khi round-trip** (mở → lưu lại `.xlsx`).
- **Font & layout drift**: thiếu font Microsoft (Calibri, Cambria, …) → thay bằng
  font thay thế → **giãn dòng/ngắt trang/độ rộng cột lệch nhẹ**, nhất là tài liệu
  Writer/Impress trình bày dày.
- **Power Query / Power Pivot / data model, liên kết OLE nhúng, một số biểu đồ
  nâng cao, Slicer/Timeline**: hỗ trợ hạn chế hoặc không có.

---

## 3. Cấu hình "quen tay như Office" đã bật sẵn

File: `etc/skel/.config/libreoffice/4/user/registrymodifications.xcu`
(áp cho **mọi user mới** qua `/etc/skel`). Các khoá:

| # | Khoá | Giá trị | Tác dụng |
|---|------|---------|----------|
| 1 | `Factory[...SpreadsheetDocument].ooSetupFactoryDefaultFilter` | `Calc MS Excel 2007 XML` | Calc lưu mặc định `.xlsx` |
| 2 | `Factory[...TextDocument].ooSetupFactoryDefaultFilter` | `MS Word 2007 XML` | Writer lưu mặc định `.docx` |
| 3 | `Factory[...PresentationDocument].ooSetupFactoryDefaultFilter` | `Impress MS PowerPoint 2007 XML` | Impress lưu mặc định `.pptx` |
| 4 | `Calc/Formula/Syntax/Grammar` | `1` | Cú pháp công thức **Excel A1** |
| 4 | `Calc/Formula/Syntax/StringRefAddressSyntax` | `1` | Chuỗi tham chiếu (INDIRECT) kiểu **Excel A1** |
| 4 | `Calc/Formula/Syntax/EnglishFunctionName` | `true` | Dùng **tên hàm tiếng Anh** (SUM, VLOOKUP…) như Excel |
| 5 | `Calc/Formula/Load/OOXMLRecalcMode` (và `ODFRecalcMode`) | `0` | **Luôn tính lại** khi mở file, không hỏi |
| 6 | `Common/Security/Scripting/MacroSecurityLevel` | `1` | Bảo mật macro **Trung bình** = "bật kèm cảnh báo", giống Office |

---

## 4. Phải xác nhận bằng mắt trên ISO đã build

`verified_on_host: NO`. Các con số/định dạng ở trên là **kỳ vọng**; chỉ **đúng
chắc chắn** sau khi:

1. Build ISO (`lb build`) có `libreoffice` + `libreoffice-l10n-vi`.
2. Boot ISO trong QEMU, mở `KiemTra_Ham_Office.xlsx` bằng LibreOffice Calc.
3. Đọc ô **TỔNG KẾT**: lý tưởng **KHỚP 79 / 79**, **LỆCH 0**. Nếu có ô **❌**,
   ghi lại tên hàm → bổ sung vào mục "Khoảng trống đã biết" ở trên (đó chính là
   cách tài liệu này được cập nhật trung thực theo thực đo).
4. Mở lại `.docx/.pptx` mẫu để kiểm font/layout drift.

Khi đã xem trên máy thật và đạt, đổi `verified_on_host: NO` → `YES (ngày, phiên
bản LibreOffice)` và ghi số hàm KHỚP thực tế.
