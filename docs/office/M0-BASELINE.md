# NaMiOffice — Báo cáo M0 (baseline)

**Ngày:** 10/11/2026 · **Loại:** báo cáo mốc M0 của kế hoạch công việc kit
(`04_KIEN_TRUC_KIEM_THU §5`). · **Phạm vi:** *"M0 pin LibreOffice, audit
license/trademark/font, inventory hiện trạng, lập test harness."*

> **M0 KHÔNG code tính năng.** Đây là bước **pin phiên bản + kiểm kê hiện trạng +
> lập ma trận + dựng registry**. Mọi phát biểu "có/chưa có" dưới đây là **đánh giá
> hiện trạng**, không phải tuyên bố đã hoàn tất tính năng. Theo kit
> (`01_PHAM_VI §3`): **"Có nút menu" chưa đủ** — một tính năng chỉ là "Đã hỗ trợ"
> khi có unit/integration + **round-trip** + thử tương tác.

---

## 1. Phiên bản LibreOffice được pin & cách cài

| Hạng mục | Giá trị |
|---|---|
| Nền | Debian 13 **trixie**, live-build ISO |
| Gói cài | `libreoffice` (metapackage → Writer/Calc/Impress/Draw/Base/Math) |
| **Phiên bản pin** | **LibreOffice 25.2.3** — gói `4:25.2.3-2+deb13u8` |
| Gói kèm | `libreoffice-l10n-vi`, `libreoffice-help-vi`, `mdbtools` |
| Nguồn khai báo | `distro/live-build/config/package-lists/0400-office-browser.list.chroot` |
| Trạng thái build | `verified_on_host: NO` — tên gói l10n-vi/help-vi cần xác nhận lại trên snapshot trixie trước khi `lb build`; nếu thiếu → bỏ dòng + ghi vào build-manifest, **không tự thay gói khác không ghi chú** |

**Cách "pin":** bản này được pin **gián tiếp** qua snapshot kho Debian 13 (gói
`libreoffice` của trixie đang là 25.2.3). Kit (`04 §1`) muốn *"LibreOffice
upstream được pin phiên bản → nhánh NaMiOffice nhỏ theo dõi patch"*. **Hiện chưa
có** nhánh mã nguồn NaMiOffice; ta đang dùng **binary Debian** + lớp cấu
hình/branding. Đây là điểm cần chốt ở M1: pin bằng snapshot URL cố định (hoặc
mirror nội bộ) để build tái lập.

---

## 2. Repo ĐÃ giao gì cho "Office" (kiểm kê trung thực)

Tất cả ở mức **cấu hình + hiển thị + file demo**, **chưa** có patch mã nguồn
LibreOffice, **chưa** có fidelity pipeline, **chưa** round-trip test đối chiếu
Office thật. `verified_on_host: NO` cho toàn bộ.

| # | Hạng mục đã làm | File/cơ chế | Giới hạn trung thực |
|---|---|---|---|
| 1 | **Đổi tên hiển thị → "NaMiOffice"** | hook `0450-namioffice-brand.hook.chroot` (sửa `Name=`/`GenericName=` trong `.desktop`; chép `intro.png`/`about.svg`) | Title bar + dòng chữ trong About **vẫn còn "LibreOffice 25.x"** (chuỗi `ProductName` biên dịch sẵn) — chỉ đổi 100% khi build lại nguồn với `--with-vendor`/`PRODUCTNAME`. Giữ tín dụng "dựa trên LibreOffice (TDF)" cho đúng MPL/LGPL. |
| 2 | **Bộ icon NaMiOffice** 6 app | `…/usr/share/icons/hicolor/*/apps/namioffice-*.png` (5 cỡ) | Thuần hiển thị. |
| 3 | **Định dạng lưu mặc định kiểu Office** | `registrymodifications.xcu`: Calc→`.xlsx`, Writer→`.docx`, Impress→`.pptx`; cú pháp Excel A1; tên hàm tiếng Anh; luôn recalc khi mở; macro security = Trung bình (1) | Cấu hình đúng hướng; **không** tự biến LO thành Office. |
| 4 | **File tự kiểm 79 hàm Excel** | `tools/demo/make-office-compat-test.py` → `KiemTra_Ham_Office.xlsx` | Công thức sống + kỳ vọng tính độc lập bằng Python; **tự chấm khi mở trên ISO**. Chưa chạy trên máy thật → chưa biết số KHỚP thực. Chỉ phủ **hàm 1 giá trị**, **không** chạm mảng động/spill/Table/Pivot. |
| 5 | **Demo PowerPoint thật** | `tools/demo/make-demo-pptx.py` → `GioiThieu_NaMiOffice.pptx` (4 slide, chart cột native OOXML) + hook `0500` tự mở Impress | Chứng minh Impress mở/render **nội dung tĩnh**; chưa kiểm animation/SmartArt/round-trip. |
| 6 | **Demo Excel** | `make-demo-xlsx.py` → `BaoCao_KinhDoanh_Q4_2026.xlsx` | Minh hoạ. |
| 7 | **Liên kết file (double-click)** | `etc/skel/.config/mimeapps.list`: doc/docx→Writer, xls/xlsx→Calc, ppt/pptx/pps/ppsx→Impress, odf→tương ứng, pdf→Okular | Gói Debian đã tự khai `MimeType=`; đây là lớp "khoá chắc". |
| 8 | **Access qua mdbtools** | gói `mdbtools` trong 0400 list | **Chỉ đọc/xuất** `.mdb`, `.accdb` một phần; **không ghi**; không chạy form/report/VBA Access. |
| 9 | **Tài liệu hiện trạng** | `docs/support/OFFICE-SUITE.md`, `docs/support/OFFICE-COMPAT.md`, `docs/branding/NAMIOFFICE.md` | Đã nêu nhiều khoảng trống đúng; M0 này **đính chính** vài chỗ (xem §4). |

---

## 3. Audit license / trademark / font (M0)

- **License:** LibreOffice = MPL-2.0 / LGPL-3.0+ của **The Document Foundation**.
  Cho phép sửa & **đổi tên**; chính sách nhãn hiệu TDF **yêu cầu** bản đã sửa
  phải đổi tên (không gọi tiếp là "LibreOffice"). → Việc đổi tên NaMiOffice là
  **đúng luật**; phải giữ dòng tín dụng "dựa trên LibreOffice (TDF)".
- **Trademark:** không được gọi bộ này là "Microsoft Office miễn phí"
  (`01_PHAM_VI §1`). Trên web/App Center chỉ app **đã phát hành** mới ghi "có sẵn".
- **Font:** rủi ro lớn nhất về fidelity là **thiếu font Microsoft** (Calibri,
  Cambria, Segoe UI…) → thay font → trôi dòng/ngắt trang/cắt chữ. M0 chưa chốt
  bộ font hợp pháp thay thế (metric-compatible: Carlito↔Calibri, Caladea↔Cambria);
  đây là việc **F0 gate** của M1.

---

## 4. Đính chính overclaim trong doc cũ (honest-core)

Các doc `OFFICE-*.md` hiện có vài chỗ nói quá so với hành vi thật của LO 25.2 —
ma trận M0 sửa lại:

1. **"XLOOKUP, LET, LAMBDA, dynamic array (spill): có từ 24.8+ → 25.2 hỗ trợ."**
   → **Sai một phần.** LO 25.2: **XLOOKUP** (1 giá trị) và **LET** có; nhưng
   **LAMBDA** và nhóm **BYROW/BYCOL/MAP/REDUCE/SCAN** **KHÔNG** có; **dynamic
   array spill** (FILTER/SORT/UNIQUE/SEQUENCE tràn ô) **KHÔNG** có. → các dòng
   `SH-F1-01/02/04/05` = **C3**. Theo kit: *"trả cached values không được giả là
   có engine"*.
2. **"Table với structured references"** ngầm hiểu là đạt → **Sai.** Calc không
   có Excel Table (ListObject); tham chiếu `Table1[Cột]` không hỗ trợ native →
   `SH-F0-10`/`SH-F1-06` = **C2**.
3. **Biểu đồ "đầy đủ"** → thực tế các chart Excel 2016+ (waterfall/treemap/
   sunburst/box plot/funnel/map) **không có native** → `SH-F2-04` = **C3**.
4. **Pivot "đầy đủ"** → PivotTable cơ bản có (DataPilot) nhưng **PivotChart gắn
   động**, **Slicer/Timeline** không có → C2/C3.

---

## 5. Mốc kế tiếp trung thực (go/no-go có bằng chứng)

Theo `04 §5`. Mỗi mốc **phải** có build + test + ảnh/fixture + bug + quyết định;
**không** dự đoán ngày phát hành khi chưa có repo/nhân lực.

- **M1 — F0 polish + Save-Safety.** UX tiếng Việt/phím tắt/mẫu, in/PDF, công
  thức & chart cốt lõi, atomic save/recovery. **Trọng tâm: `PIPE-01`** — dựng
  **Compatibility Inspector** (đọc trước khi Save: macro/dynamic array/pivot/data
  model/queries/charts/content controls/media/external links/signature/IRM →
  cảnh báo, giữ bản gốc, lưu bản sao). Font hợp pháp metric-compatible.
- **M2 — F1 pilot.** Bảng/tính toán/biểu đồ/tài liệu dài; corpus pilot
  (100 DOCX / 150 XLSX / 60 PPTX) + đối chiếu **Microsoft Office có giấy phép**.
- **M3 — Mail/Notes.** Thử **reuse phần mềm Linux có giấy phép** (Thunderbird/
  Evolution, Joplin/Xournal++) thay vì viết mới; F2 Data/Forms chỉ khi có nhu
  cầu + đội vận hành.
- **M4 — Collab + Automation SDK.** Dịch vụ cộng tác (giai đoạn 1→3), SDK
  Python/UNO có governance, **Power Query subset** chỉ theo corpus thật — hoặc
  xác nhận **không khả thi** và chỉ cung cấp tuyến Windows/M365.

Vertical slice ưu tiên (kit §05.3): 1 DOCX dài (bảng + track changes), 1 XLSX
(SUMIFS + XLOOKUP + **dynamic array** + table + chart + Pivot), 1 PPTX (master +
chart + notes): mở → sửa nhỏ → **lưu bản sao** → mở lại bằng NaMiOffice **và**
Microsoft Office có giấy phép → report sai khác. (XLSX này sẽ **lộ ngay** các
C3: dynamic array/Table/Pivot refresh — đó là mục đích.)

---

## 6. Tuyên bố trung thực (bắt buộc)

**KHÔNG có hạng mục nào trong ma trận được coi là "hoàn tất".** Điều kiện tối
thiểu để một dòng chuyển sang "Đã hỗ trợ":

1. **Round-trip test đối chiếu Microsoft Office CÓ GIẤY PHÉP** — *không có sẵn
   trong môi trường này*; cần máy/VM Windows + Office licensed.
2. **Pilot người dùng thật** trên corpus đề xuất (04 §3), công bố dashboard
   fidelity theo feature/version.
3. Vượt **4 cổng tuyệt đối** (04 §3): không mất dữ liệu không cảnh báo; không sai
   tổng kiểm soát fixture kế toán; không tự chạy macro / mở kết nối ngoài; không
   ghi đè bản gốc khi chuyển đổi rủi ro.

Mức C trong ma trận = **đánh giá kỹ thuật dựa trên hành vi đã biết của LO 25.2**,
là **điểm khởi đầu** để viết fixture & test — **không** phải kết quả đo. Mọi con
số đếm (C0=17, C1=44, C2=30, C3=28 / tổng 119) là **số dòng yêu cầu**, không phải
số tính năng đã đạt.

---

## 7. Deliverable M0

| File | Nội dung |
|---|---|
| `docs/office/COMPAT-MATRIX.md` | Ma trận 119 dòng (12 nhóm) + legend + bảng tổng hợp + 8 dòng P0 |
| `docs/office/feature-registry.json` | Bản máy-đọc mirror từng dòng (`id, app, task, flevel, expected, lo_current, gap, clevel, fixture, severity, notes`) |
| `docs/office/M0-BASELINE.md` | Báo cáo này |
