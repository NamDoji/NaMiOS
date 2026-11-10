# NaMiOS — Ma trận hỗ trợ định dạng (PL20 M0)

- **Phạm vi:** Phụ lục 20 §2 (`docs/specs/namios-pl20/02_MO_TEP_VA_DINH_DANG.md`). Mỗi định dạng × app NaMi × mức hỗ trợ. Ánh xạ lên gói Debian 13 THẬT (xem `NAMI-APP-CATALOG.md`).
- **Mốc:** M0 thiết kế + ánh xạ. `verified_on_host: NO` — mọi ô là **mức THIẾT KẾ dựa trên năng lực upstream đã biết**, chưa phải kết quả chạy trên ISO. Round-trip/phát codec/nhấp-đôi thật = vertical-slice/pilot M1–M3.
- **Luật trung thực (kit §1):** KHÔNG gộp "mở được" với "sửa được". Trước chuyển đổi/ghi định dạng khác → bản sao + cảnh báo mất macro/lớp/liên kết/công thức/font/chú thích/chữ ký (xem ADR-0024 `SavePlan`).
- **Ngày:** 2026-11-10.

## Chú giải mức hỗ trợ (kit §2.1)

| Ký hiệu | Nghĩa |
|---|---|
| **Xem** | mở + hiển thị đúng (không sửa) |
| **Sửa** | chỉnh sửa nội dung trong app |
| **Tạo** | tạo mới từ app |
| **Chuyển** | xuất / chuyển đổi sang định dạng khác (kèm `SavePlan` + cảnh báo lossy) |
| **Round-trip** | mở → sửa → lưu → mở lại **không mất dữ liệu** đã kiểm |
| **Chưa thử** | chưa có fixture/kết quả thật (KHÔNG suy từ việc xem) |
| **— / GAP** | không hỗ trợ / lỗ hổng trung thực (quyền/engine/app chưa ship) |

> Mọi "✓" dưới đây = **năng lực thiết kế của gói upstream**, `verified_on_host: NO`. Round-trip để **"CI/pilot"** vì chưa chạy trên ISO; Round-trip Office với **Microsoft Office có giấy phép = chưa chạy** (office-compat README).

---

## 1. Văn bản / Office

| Định dạng | App NaMi (gói) | Xem | Sửa | Tạo | Chuyển | Round-trip | Ghi chú / gap trung thực |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| **DOCX** | NaMiWriter (`libreoffice-writer`) | ✓ | ✓ | ✓ | →PDF/ODT | CI/pilot | Bảng/ảnh/comment/hyperlink OK. **Gap:** VBA/macro, track-changes tạo-mới, footnote mức cao (office-compat README). Round-trip vs MS Office **chưa chạy**. |
| **DOC** (97-2003) | NaMiWriter | ✓ | ✓ | — | →PDF/ODT | CI/pilot | Ghi .doc cũ dễ lệch layout; khuyến nghị lưu DOCX/ODT. |
| **ODT / ODF text** | NaMiWriter | ✓ | ✓ | ✓ | →PDF/DOCX | CI/pilot | Định dạng **gốc** của LibreOffice — fidelity cao nhất. |
| **RTF / TXT** | NaMiWriter (+ `kate` cho TXT) | ✓ | ✓ | ✓ | →PDF/ODT | CI/pilot | TXT mã hoá UTF-8; tên/nội dung tiếng Việt NFC/NFD cần test. |
| **XLSX** | NaMiSheet (`libreoffice-calc`) | ✓ | ✓ | ✓ | →PDF/ODS/CSV | CI/pilot | Công thức/named-range/Table/chart OK. **Gap:** Pivot **tạo-mới**, mảng-động spill (FILTER/SORT/UNIQUE/XLOOKUP), Power Query, XLSM/XLSB macro **chưa xác minh** (office-compat README). |
| **XLS / ODS / CSV / TSV** | NaMiSheet | ✓ | ✓ | ✓ | →PDF/XLSX | CI/pilot | ODS = gốc. CSV: dấu phân cách + mã hoá tiếng Việt cần kiểm. |
| **PPTX / PPT / PPSX** | NaMiSlides (`libreoffice-impress`) | ✓ | ✓ | ✓ (PPTX) | →PDF/ODP | CI/pilot | Master/chart/notes OK. **Gap:** animation, video nhúng, font/object nhúng có thể khác. |
| **ODP** | NaMiSlides | ✓ | ✓ | ✓ | →PDF/PPTX | CI/pilot | Gốc LibreOffice. |
| **MDB / ACCDB** (Access) | NaMiData (`libreoffice-base`) + `mdbtools` | Xem | một phần | — | →CSV | Chưa thử | Chỉ đọc qua mdbtools; KHÔNG hứa workflow Access đầy đủ. |

## 2. PDF

| Định dạng | App NaMi (gói) | Xem | Sửa | Tạo | Chuyển | Round-trip | Ghi chú / gap trung thực |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| **PDF thường** | NaMiPDF (`okular`) | ✓ | chú thích | — | in/→ảnh | Chưa thử | Xem/chú thích/sắp trang/in. Tạo PDF = xuất từ NaMiOffice hoặc `img2pdf`. |
| **PDF/A** | NaMiPDF | ✓ | chú thích | — | — | Chưa thử | Xem OK; tuân thủ PDF/A khi **xuất** chưa xác minh. |
| **AcroForm** (biểu mẫu) | NaMiPDF | ✓ | điền | — | — | Chưa thử | Điền form cơ bản; **XFA KHÔNG** suy từ việc xem (gap). |
| **PDF có chữ ký số** | NaMiPDF (+ `namipdf-inspect`) | ✓ | — | — | — | Chưa thử | Inspector báo trạng thái chữ ký (severity high); **không làm hỏng chữ ký/bản gốc**. Ký/redact = cổng NaMiPDF-v18 (đang làm). |
| **PDF scan ảnh** | NaMiPDF + `ocrmypdf`/`tesseract-ocr-vie` | ✓ | sau OCR | — | →PDF có text | Chưa thử | OCR tiếng Việt qua toolchain; `namipdf-inspect` phân loại "Scan image" + gợi ý OCR trước khi sửa. OCR chất lượng **chưa xác minh**. |
| **PDF mã hoá / DRM** | NaMiPDF (+inspector) | nếu có mật khẩu | — | — | — | — | Inspector **không bẻ khoá**; thiếu mật khẩu = chặn (severity critical). DRM = gap. |

## 3. Ảnh raster + vector

| Định dạng | App NaMi (gói) | Xem | Sửa | Tạo | Chuyển | Round-trip | Ghi chú / gap trung thực |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| **PNG** | NaMiImages (`gwenview`) | ✓ | crop/rotate/resize | — | →JPEG/WebP | Chưa thử | Alpha giữ; chỉnh màu cơ bản. Editor layer = app khác. |
| **JPEG** | NaMiImages | ✓ | crop/rotate/resize | — | →PNG/WebP | Chưa thử | **Cảnh báo mất dữ liệu khi re-save JPEG**; rotate theo EXIF. |
| **GIF** | NaMiImages | ✓ (động) | hạn chế | — | →PNG | Chưa thử | **Gap:** không lưu ảnh-động thành frame-đầu âm thầm (kit §4.4); sửa frame = chưa. |
| **TIFF** | NaMiImages | ✓ | crop/rotate/resize | — | →PNG/JPEG | Chưa thử | Multi-page/ICC cần kiểm. |
| **WebP** | NaMiImages | ✓ | crop/rotate/resize | — | →PNG/JPEG | Chưa thử | WebP động: xem OK, sửa hạn chế. |
| **BMP** | NaMiImages | ✓ | crop/rotate/resize | — | →PNG | Chưa thử | — |
| **SVG** | NaMiImages (xem) + **NaMiDraw** (`libreoffice-draw`, sửa) | ✓ | ✓ (Draw) | ✓ (Draw) | →PNG/PDF | Chưa thử | **Bảo mật:** chặn script SVG + external-resource mặc định (ADR-0024 D4). Vector/text/layer sửa trong NaMiDraw. |
| **RAW / HEIF / AVIF** | NaMiImages (preview) | preview | — | — | — | Chưa thử | **Gap:** phụ thuộc codec có quyền + test; KHÔNG hứa mọi camera/HEIC 10-bit (kit §2.1). P1. |

## 4. Tệp nén (archive)

| Định dạng | App NaMi (gói) | Xem (list) | Giải nén | Tạo | Chuyển | Round-trip | Ghi chú / gap trung thực |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| **ZIP** | NaMiArchive (`ark`/libarchive) | ✓ | ✓ | ✓ | — | Chưa thử | Chống path-traversal/bomb theo thiết kế (ADR-0024 D4). Thuật toán mã hoá ZIP hiển thị đúng. |
| **7z** | NaMiArchive | ✓ | ✓ | ✓ | — | Chưa thử | Qua libarchive; mật khẩu nhập UI không log. |
| **tar / tar.gz / tgz** | NaMiArchive | ✓ | ✓ | ✓ | — | Chưa thử | — |
| **gz / bz2 / xz** | NaMiArchive | ✓ | ✓ | ✓ | — | Chưa thử | Nén đơn luồng. |
| **RAR** (RAR4/RAR5) | NaMiArchive | ✓ nếu engine | **GAP** | **— không bao giờ** | — | — | **Gap lớn:** không có gói `unrar`/libarchive-RAR trong package-list → **giải nén RAR CHƯA ship**. Tạo RAR = engine không làm được, không gắn badge (kit §3, F20-03). |
| **.zar** | NaMiArchive | **unknown** | unknown | — | — | — | **KHÔNG tự coi `.zar` = `.rar`.** Nhận diện theo signature/MIME; là định dạng riêng thì ghi nhà tạo + cần **mẫu đã lọc dữ liệu + đặc tả** trước khi hỗ trợ → báo "chưa hỗ trợ" rõ ràng (kit §2.1 cuối). |

## 5. Âm thanh + Video (NaMiMedia — CHƯA CÓ APP)

> **GAP LỚN NHẤT:** không có trình phát nào trong ISO (chỉ `pipewire`/`wireplumber` = server âm thanh, `libfdk-aac2t64` = codec lib). Mọi ô dưới đây = **thiết kế, chưa có app phát** → "Chưa thử / chưa ship". Đang dựng ở topic song song.

| Định dạng | App NaMi | Phát | Sửa | Tạo | Chuyển | Ghi chú / gap trung thực |
|---|---|:--:|:--:|:--:|:--:|---|
| **MP3 / WAV / FLAC / OGG(Vorbis/Opus)** | NaMiMedia (**chưa ship**) | **Chưa thử** | — | — | — | Chưa có player; playlist/seek/resume = thiết kế (kit §5). |
| **AAC / M4A** | NaMiMedia (chưa ship) | **Chưa thử** | — | — | — | Codec `libfdk-aac2t64` có mặt nhưng **quyền phân phối AAC chờ legal review** (kit §5). |
| **MP4** (container) | NaMiMedia (chưa ship) | **Chưa thử** | — | — | — | MP4 là **container** ≠ codec; không bảo đảm mọi codec bên trong. |
| **MKV / WebM / MOV / AVI** | NaMiMedia (chưa ship) | **Chưa thử** | — | — | — | Subtitle SRT/VTT, audio-track = thiết kế. |
| **Codec H.264 / H.265 / AV1 / VP9 / DRM** | — | **GAP** | — | — | — | FFmpeg/GStreamer hỗ trợ **kỹ thuật ≠ quyền phân phối**; audit giấy phép/bằng sáng chế/thị trường trước ISO (kit §5, QA §3). Lỗi phát phải nói rõ "thiếu codec / codec hạn chế / DRM", KHÔNG tự tải codec lạ. |

## 6. Vẽ vector + CAD

| Định dạng | App NaMi (gói) | Xem | Sửa | Tạo | Chuyển | Round-trip | Ghi chú / gap trung thực |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| **ODG** (OpenDocument Graphics) | NaMiDraw (`libreoffice-draw`) | ✓ | ✓ | ✓ | →PDF/PNG/SVG | Chưa thử | Gốc LibreOffice Draw. Text/vector/layer/shape/arrow. |
| **SVG** (vẽ) | NaMiDraw | ✓ | ✓ | ✓ | →PNG/PDF | Chưa thử | Chặn script/external-resource. Chỉnh thiết kế vector chuyên nghiệp = phạm vi khác. |
| **DXF** | NaMiDraw (import) / **NaMiCAD Viewer (P1, chưa ship)** | ✓ (Draw import) | hạn chế | — | →PDF | Chưa thử | LO Draw import DXF cơ bản. Đo kích thước/layer/model-space/print-to-scale = NaMiCAD Viewer P1 (**chưa có gói**). Xref/SHX cảnh báo. |
| **DWG** | — / NaMiCAD Viewer (P1) | **GAP** | — | — | — | — | **Gap:** không có importer/converter DWG được cấp phép trong ISO → "chưa xác minh bản này", hướng người gửi xuất DXF/PDF. KHÔNG tự chuyển rồi ghi đè bản thiết kế (kit §4.4). FreeCAD hỗ-trợ-file ≠ chứng nhận AutoCAD workflow (QA §3). |
| **Chỉnh sửa CAD (editor)** | — | — | **GAP** | — | — | — | Editor CAD = gói tùy chọn P2+, chưa ship. Phân biệt **viewer CAD ≠ editor CAD**. |
| **STEP / IGES / STL / IFC** (CAD 3D/BIM) | — (P2) | Chưa thử | — | — | — | — | Viewer/app tùy chọn P2; KHÔNG suy là Revit/AutoCAD hay chỉnh native trọn vẹn (kit §2.1). |
| **CDR / AI / PSD** | — | — | — | — | — | — | Định dạng riêng của Corel/Adobe; lớp/effect có thể mất. Chỉ thêm importer khi kiểm phiên bản cụ thể (kit §2.4). Mặc định KHÔNG hứa. |

## 7. Bộ gõ tiếng Việt (xuyên định dạng — NaMiType)

| Bối cảnh nhập | App NaMi (gói) | Trạng thái | Ghi chú / gap trung thực |
|---|---|:--:|---|
| Telex / VNI / Unikey vào Office/PDF/CAD/browser/tên tệp | NaMiType (`fcitx5`+`fcitx5-unikey`) | **đã cài, gõ chưa xác minh** | KHÔNG mất dấu, KHÔNG lộ phím mật khẩu (F20-08). Cài-được ≠ gõ-đúng → test hồi quy VN-002 (manifest `needs_verification`). |

---

## 8. Tổng hợp gap trung thực (nhắc lại, xem NAMI-APP-CATALOG §3)

1. **NaMiMedia — không có trình phát trong ISO** → toàn bộ hàng §5 là "Chưa thử / chưa ship". Gap lớn nhất.
2. **Codec media** (H.264/H.265/AAC/DRM): quyền phân phối ≠ hỗ trợ kỹ thuật — chờ legal review từng codec.
3. **RAR**: không có `unrar` → giải nén RAR chưa ship; tạo RAR không bao giờ.
4. **DWG + editor CAD**: không có importer DWG / editor CAD → chỉ hướng DXF/PDF; viewer CAD (P1) chưa ship.
5. **`.zar`**: unknown — chờ mẫu đã-lọc-dữ-liệu + đặc tả; không giả định là RAR.
6. **Round-trip Office**: chỉ selfcheck tĩnh + round-trip soffice ở CI; round-trip với **Microsoft Office có giấy phép chưa chạy**.
7. **RAW/HEIF/AVIF, Pivot/mảng-động Office, XFA/DRM PDF, OCR chất lượng**: đều "chưa xác minh" — không suy từ việc xem.
</content>
