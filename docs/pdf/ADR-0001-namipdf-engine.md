# ADR 0001 (NaMiPDF) — Chọn engine/stack PDF cho NaMiPDF

- **Trạng thái:** proposed · **Mức thực thi:** `specified` (mốc M0 khảo sát; **chưa** app nào chạy thật trên máy/phần cứng thật → chưa `partial`, chưa `completed`).
- **Ngày:** 10/11/2026 · **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam.
- **Năng lực:** Phụ lục 18 — **NaMiPDF** (ứng dụng PDF cài sẵn, mặc định trên NaMiOS). Đây là **yêu cầu phát triển**, không phải tuyên bố đã hoàn thành hay chứng nhận.
- **Chuỗi ADR:** đây là ADR **cấp sản phẩm NaMiPDF** (series riêng dưới `docs/pdf/`), không trùng với series hạ tầng `docs/adr/` (0001 Linux+Wine … 0019 OS-agent). Liên quan: `docs/adr/ADR-0002` (nền Debian 13 trixie), `docs/adr/ADR-0015` (quy tắc vàng "GUI mở ra ≠ chạy được"), `docs/adr/ADR-0016` (design system), `docs/adr/ADR-0017` (Update Center).
- **Tài liệu đầu vào:** `docs/specs/namipdf-v18/` (README + 01→05).
- **Sản phẩm M0 đi kèm:** `docs/pdf/COMPAT-MATRIX.md` (ma trận 66 dòng), `docs/pdf/M0-BASELINE.md`.
- **Gói ISO hiện có liên quan:** Okular (`distro/live-build/config/package-lists/0100-desktop-kde.list.chroot`), in CUPS + scan SANE (`0500-print.list.chroot`), LibreOffice (`0400-office-browser.list.chroot`).

> **Cổng trung thực (nguyên văn kit, README §Quyết định):** *NaMiPDF "phải phát hiện, thông báo mức tin cậy và lưu bản sao an toàn, không quảng cáo khả năng 'sửa mọi PDF 100%'."* ADR này mã hoá nguyên tắc đó: mỗi concern chỉ được gắn mức C theo **hành vi đã biết của stack**, không theo tên app.

---

## 1. Bối cảnh & ràng buộc

NaMiOS là ISO Debian 13 trixie (live-build) + KDE Plasma 6, **phân phối tự do (free-redistributable)**. Hệ quả ràng buộc giấy phép: mọi thành phần phải **tái phân phối được trong ISO** và giữ **source/notices**; thành phần **AGPL** (có điều khoản "network use") phải được đánh giá nghĩa vụ **trước** khi tích hợp (kit `03 §1`: *"MuPDF có lựa chọn AGPL hoặc thương mại nên phải quyết định nghĩa vụ trước tích hợp"*).

ISO **đã ship Okular** (viewer/annotation/form/print dựa trên Poppler). Vì vậy quyết định đúng không phải "viết mới PDF app" mà là: **tái dùng Okular + bổ sung các engine dòng lệnh đã kiểm giấy phép làm adapter** cho các tác vụ Okular không làm được — y như NaMiMail tái dùng Thunderbird thay vì viết lại mail client.

Một sự thật kỹ thuật phải mã hoá ngay: **không có engine FOSS đơn lẻ nào làm được toàn bộ** (view + true-edit + PAdES + redaction chứng minh + PDF/A/UA). "Full feature" chỉ đạt được bằng **pipeline nhiều thư viện qua interface kiểm chứng** (kit `03 §1`: *"không gán 'full feature' theo một dependency"*).

---

## 2. Benchmark ≥2 stack FOSS cho TỪNG concern

Mỗi concern xét tối thiểu hai lựa chọn khả thi rồi chốt một, kèm lý do + license.

### 2.1 Front-end: viewer / annotation / forms / print

| Lựa chọn | SPDX | Ưu | Nhược | Quyết định |
|---|---|---|---|---|
| **Okular** (KDE) | `GPL-2.0-or-later` | **ĐÃ ship**; annotation phong phú (highlight/note/stamp/freehand/shapes), điền AcroForm + lưu, in qua Qt→CUPS, hiển thị chữ ký (NSS), KIO cho SMB/WebDAV, TTS Qt | Không author form field; không true-edit; không redaction; reorder trang yếu | **CHỌN** — nền KDE sẵn, bề rộng tính năng P0 lớn nhất |
| Evince (GNOME) | `GPL-2.0-or-later` | Nhẹ, ổn định, cũng Poppler | Annotation/form mỏng hơn Okular; GTK lệch khỏi KDE design system | Loại — lệch stack, ít tính năng hơn |
| qpdfview | `GPL-2.0-or-later` | Rất nhẹ, tab tốt | Gần như chỉ xem; không annotation đầy đủ | Loại — thiếu P0 annotation |

### 2.2 Render / parse / text-extraction

| Lựa chọn | SPDX | Ưu | Nhược | Quyết định |
|---|---|---|---|---|
| **Poppler** (+ `poppler-utils`) | `GPL-2.0-or-later` | **Backend của Okular**; `pdftoppm/pdftotext/pdfimages/pdfinfo/pdffonts/pdfseparate/pdfunite/pdftocairo/pdftohtml`; chữ ký qua NSS; trưởng thành, fuzz nhiều | Không engine edit nội dung | **CHỌN** — đã tích hợp sẵn, GPL sạch |
| MuPDF (`mutool`) | **`AGPL-3.0-or-later`** OR thương mại (Artifex) | Render nhanh; có **API redaction** + chỉnh nội dung mức thấp | **AGPL**: điều khoản network-use; nếu đưa vào dịch vụ mạng phải mở source → phải quản nghĩa vụ | **Flag — không core v1.** Chỉ cân nhắc cho spike redaction/edit M2/M3 **nếu** tuân thủ AGPL rõ ràng (ship source, không dịch vụ mạng proprietary) |
| pdfium (Google) | `BSD-3-Clause` | Permissive; render tốt (nền Chromium) | Không đóng gói tốt trong Debian; build nặng; không thêm giá trị khi Poppler đã tích hợp Okular | Loại — chi phí tích hợp > lợi ích |

### 2.3 Thao tác cấu trúc lossless (merge/split/rotate/reorder/encrypt/linearize)

| Lựa chọn | SPDX | Ưu | Nhược | Quyết định |
|---|---|---|---|---|
| **qpdf** + **pikepdf** | qpdf `Apache-2.0` · pikepdf `MPL-2.0` | qpdf: linearize, encrypt/decrypt, merge/split, giữ cấu trúc; pikepdf = binding Python trên qpdf → scripting MediaBox/CropBox/overlay/metadata; **giữ incremental update + chữ ký theo permission** | Không render; không author form | **CHỌN** — chuẩn công nghiệp, license permissive/weak-copyleft, GPL-compatible |
| pdftk-java | `GPL-2.0-or-later` | Merge/split/FDF quen thuộc | Trùng chức năng qpdf; FDF là điểm mạnh riêng (giữ làm phụ cho form) | Phụ — chỉ dùng cho FDF/XFDF form, không làm core |
| mutool (MuPDF) | `AGPL-3.0-or-later` | Clean/merge/redact | AGPL (xem 2.2) | Loại khỏi core |

> Bằng chứng license: qpdf README — *"Licensed under the Apache License, Version 2.0 … Versions prior to 7 … Artistic License 2.0 (at your option)."* pikepdf README — header SPDX `MPL-2.0`, *"powered by qpdf."*

### 2.4 OCR tiếng Việt

| Lựa chọn | SPDX | Ưu | Nhược | Quyết định |
|---|---|---|---|---|
| **Tesseract** (`tesseract-ocr` + `tesseract-ocr-vie`) + **ocrmypdf** | Tesseract `Apache-2.0` · vie-data `Apache-2.0` · ocrmypdf `MPL-2.0` (non-core MIT, docs CC-BY-SA-4.0) | **Offline**, model VN có dấu; ocrmypdf tạo text-layer giữ ảnh gốc ("searchable PDF"), deskew/clean, xuất PDF/A; TSV confidence theo vùng | ocrmypdf **cần Ghostscript (AGPL)** + Tesseract làm external program; độ chính xác phụ thuộc chất lượng scan | **CHỌN** — duy nhất đạt "offline + model vi + pipeline sẵn" |
| EasyOCR / PaddleOCR | Apache-2.0 / Apache-2.0 | Accuracy cao trên ảnh khó | Nặng (PyTorch/GPU), model lớn, tải runtime; khó offline-mặc-định trong ISO | Loại — quá nặng cho mặc định offline |
| Dịch vụ OCR cloud | — | — | Vi phạm "offline mặc định, không gửi PDF ra Internet" (kit `02 §1`, `03 §4`) | Loại tuyệt đối |

> Bằng chứng license: ocrmypdf README — *"licensed under the Mozilla Public License 2.0 (MPL-2.0) … requires external program installations of Ghostscript and Tesseract OCR."*

### 2.5 Ảnh ↔ PDF

| Lựa chọn | SPDX | Ưu | Nhược | Quyết định |
|---|---|---|---|---|
| **img2pdf** (ảnh→PDF) + **poppler** `pdftoppm`/`pdfimages` (PDF→ảnh) | img2pdf `LGPL-3.0-or-later` · poppler `GPL-2.0-or-later` | img2pdf **nhúng lossless** không re-encode; poppler-utils trích ảnh/render chuẩn | — | **CHỌN** |
| ImageMagick `convert` | ApacheV2-ish (ImageMagick License) | Tiện | **Re-encode → mất chất lượng**; từng có policy/CVE | Phụ — chỉ khi cần biến đổi ảnh, không cho "ảnh→PDF" lossless |

### 2.6 Kiểm định PDF/A & PDF/UA

| Lựa chọn | SPDX | Ưu | Nhược | Quyết định |
|---|---|---|---|---|
| **veraPDF** | **dual** `MPL-2.0 OR GPL-3.0-or-later` | Validator **ngành** cho PDF/A (1–4) + PDF/UA; là nguồn chính kit nêu (`04 §4`) | Cần Java runtime | **CHỌN** — dùng nhánh **MPL-2.0**; **gate**: chỉ gắn nhãn PDF/A/UA khi veraPDF đạt |
| (không có đối thủ FOSS tương đương) | — | — | — | — |

> Bằng chứng license: veraPDF README — *"dual-licensed … GPLv3+ … MPLv2+."*

### 2.7 PAdES (ký số mật mã) — **concern khó, honest C3**

| Lựa chọn | SPDX | Ưu | Nhược | Quyết định |
|---|---|---|---|---|
| **pyHanko** | `MIT` | PAdES B-B/B-T/B-LT/B-LTA, **PKCS#11** token/HSM, timestamp/LTV, verify trust/revocation | **Beta** (README: *"not yet production-ready"*); cần test vector + viewer độc lập + chứng nhận | **Ứng viên M3** (chưa bật) |
| EU DSS (Nowina/EC) | `LGPL-2.1` | Bộ tham chiếu PAdES của EU | Java nặng; tích hợp lớn | **Dùng để cross-check** kết quả pyHanko |
| Okular/poppler native signing (NSS) | GPL-2.0+/MPL-2.0 | Có **hiển thị** + ký cơ bản | Không đủ PAdES baseline + token + TSA đã chứng nhận | Chỉ dùng cho **hiển thị** trạng thái, **không** tự tuyên "ký hợp lệ" |

### 2.8 True content-edit & Redaction chứng minh — **không có lời giải FOSS trọn gói**

- **True content-edit (sửa chữ trong content stream như Acrobat):** **không engine FOSS nào đạt.** LibreOffice Draw **bị kit cấm** làm editor đầy đủ (mở/lưu làm mất annotation/form/chữ ký/incremental — kit `03 §1`). Inkscape chỉ sửa **1 trang vector**. mutool (AGPL) sửa mức thấp. → **C3**. **v1 chỉ làm "thêm nội dung" (text-box overlay)** có nhãn phân biệt rõ với "sửa văn bản gốc", **không** quảng cáo overlay là thay text cũ khi text cũ vẫn copy/tìm được (kit `01 §3`).
- **Redaction chứng minh xoá vĩnh viễn:** không FOSS nào **chứng minh sẵn**. Đường đi: **pikepdf/qpdf xoá object + rasterize vùng/trang fallback** rồi **kiểm độc lập** (reparse, extract text, object view, OCR lại vùng, viewer khác). mutool có API redaction nhưng **AGPL**. → **C3, gate tuyệt đối**; **tắt nút "Áp dụng"** cho tới khi bộ kiểm độc lập PASS (kit `02 §4`).

---

## 3. Audit giấy phép (SPDX) — vì sao chấp nhận được cho ISO tự do phân phối

| Thành phần | Vai trò trong NaMiPDF | SPDX | Loại | Vì sao chấp nhận được |
|---|---|---|---|---|
| **Okular** | front-end view/annot/form/print | `GPL-2.0-or-later` | copyleft mạnh | FOSS, tái phân phối tự do; **đã trong ISO**; giữ source/notices |
| **Poppler** + `poppler-utils` | render/parse/extract | `GPL-2.0-or-later` | copyleft mạnh | như trên; backend Okular |
| **qpdf** | thao tác cấu trúc | `Apache-2.0` | permissive | GPL-compatible; không ràng buộc phân phối ISO |
| **pikepdf** | binding qpdf (page ops/overlay/metadata) | `MPL-2.0` | copyleft yếu (file-level) | chỉ buộc mở **sửa đổi file MPL**; dùng/phân phối tự do |
| **Tesseract** + **tesseract-ocr-vie** | OCR vi | `Apache-2.0` | permissive | model vi Apache; offline |
| **ocrmypdf** | pipeline OCR → searchable/PDF-A | `MPL-2.0` (+MIT/CC-BY-SA-4.0) | copyleft yếu | tái phân phối tự do |
| **Ghostscript** | PDF/A-gen + raster (dep của ocrmypdf + redaction fallback) | **`AGPL-3.0-or-later`** OR commercial (Artifex) | **copyleft mạnh + network** | ⚠️ **Debian main ship**; cho **ứng dụng desktop offline** nghĩa vụ = **ship source + notices** (thoả bằng apt). **Điều khoản mạng CHỈ kích hoạt nếu đưa lên dịch vụ mạng** → **cấm** xây PDF-service hosted proprietary trên Ghostscript. Local NaMiPDF = hợp lệ |
| **img2pdf** | ảnh→PDF lossless | `LGPL-3.0-or-later` | copyleft yếu | dùng như thư viện; tự do phân phối |
| **jbig2enc** | nén JBIG2 cho OCR | `Apache-2.0` | permissive | tự do |
| **veraPDF** | validate PDF/A, PDF/UA | `MPL-2.0 OR GPL-3.0-or-later` | dual | chọn **nhánh MPL-2.0**; tự do |
| **NSS** | backend verify/ký của poppler | `MPL-2.0` | copyleft yếu | tự do |
| **pyHanko** (M3) | PAdES signing | `MIT` | permissive | tự do; **chưa bật** cho tới khi pass test độc lập |
| MuPDF (*không core*) | render/redact/edit (flag) | **`AGPL-3.0-or-later`** OR commercial | **copyleft mạnh + network** | ⚠️ Chỉ dùng nếu tuân thủ AGPL; **ngoài core v1** |

**Nghĩa vụ phải thực thi (SBOM/licenses, kit `03 §4`):** (1) giữ **notices + source-availability** cho mọi gói GPL/AGPL/MPL/LGPL; (2) ghi **AGPL alert** cho Ghostscript & MuPDF trong SBOM, cấm biến thành **network service proprietary**; (3) **không** gói khoá riêng, binary vendor hay font/model thiếu quyền (ví dụ font Microsoft); (4) audit lại SPDX **theo phiên bản thật** lúc build (`apt-cache show` trên trixie — `verified_on_host: NO`).

---

## 4. Quyết định

**NaMiPDF v1 = Okular-based**, bổ sung adapter dòng lệnh đã kiểm giấy phép:

```
Okular (view · annotate · AcroForm fill · print · hiển thị chữ ký)
  ├─ Poppler / poppler-utils      → render, extract, pdftoppm/pdftotext/pdffonts/pdfimages
  ├─ qpdf + pikepdf               → merge/split/rotate/reorder/crop/encrypt/linearize (lossless)
  ├─ tesseract-ocr-vie + ocrmypdf → OCR vi offline → searchable PDF (+ Ghostscript, flag AGPL)
  ├─ img2pdf                      → ảnh → PDF lossless
  └─ veraPDF                      → GATE kiểm PDF/A & PDF/UA (chỉ gắn nhãn khi PASS)
```

với **giới hạn mức C công bố trước** cho edit/sign/redact:

- **Sửa nội dung thực** → **C3**; v1 chỉ "thêm nội dung" overlay có nhãn trung thực. Document Inspector phải hiện trạng thái **Text/Scan/Mixed/Signed/Protected** trước khi cho sửa.
- **PAdES ký thật** → **C3**; **không bật** nút ký cho tới khi pyHanko (hoặc tương đương) pass test vector + viewer độc lập + token thật (PDF-08). Okular chỉ **hiển thị** trạng thái; chữ ký tay dạng ảnh **không** gắn là chữ ký số.
- **Redaction chứng minh** → **C3, gate tuyệt đối**; **tắt "Áp dụng"** cho tới khi kiểm độc lập chứng minh không khôi phục được (content/object/metadata/attachment/old-revision/OCR) — PDF-09.
- **XFA động** → **C3**; chỉ phát hiện + cảnh báo + fallback, **không** làm hỏng/mất XFA khi lưu (PDF-07).
- **PDF/UA (tagged)** → **C3**; không có generator FOSS tốt → cần dựng + validate veraPDF + screen reader thủ công.

**Thứ tự ưu tiên (cheapest-safest-first), giống ADR 0015:** dùng tính năng **Okular/Poppler sẵn** trước → adapter **qpdf/pikepdf/ocrmypdf/img2pdf** → chỉ dựng engine mới (hoặc cân nhắc MuPDF AGPL) cho edit/redact khi thật cần và đã xử lý nghĩa vụ license + test độc lập.

---

## 5. Hệ quả

- NaMiPDF có **nền tảng viewer P0 mạnh ngay** (Okular đã ship) + đường rõ cho page-ops/OCR/convert, **nhưng không** đi kèm bảo đảm edit/sign/redact kiểu Acrobat — đầu tư tiếp **theo bằng chứng chạy thật** (PDF-01..13 + pilot).
- Package-list pipeline **đã được tạo** bởi phần việc packaging song song: `distro/live-build/config/package-lists/0420-pdf.list.chroot` (`poppler-utils qpdf tesseract-ocr tesseract-ocr-vie ocrmypdf img2pdf`; versions đã xác minh madison — xem `docs/pdf/NAMIPDF-PACKAGING.md`). **Còn thiếu & cần bổ sung:** `python3-pikepdf` (page-ops scripting) và `verapdf` (nếu đóng gói trixie, hoặc tải qua Update Center). `ghostscript` kéo theo ocrmypdf. **Tên gói phải `apt-cache show` trên trixie trước build** (`verified_on_host: NO`).
- Hai nhãn tách bạch: "xem/chú thích/sắp xếp/OCR/in **đã có đường**" ≠ "**đã chứng nhận** như Acrobat". Release-note công bố từng feature + mức C + ngày kiểm (kit `04 §3`).
- **Stop-release** (kit `04 §3`) khi: mất dữ liệu, che thông tin vẫn khôi phục được, xác nhận chữ ký sai, JS/attachment chạy, hoặc file hỏng ảnh hưởng hệ thống.

## 6. Nguồn

- qpdf (Apache-2.0, trước v7 Artistic-2.0): https://github.com/qpdf/qpdf · https://qpdf.readthedocs.io/
- pikepdf (MPL-2.0, trên qpdf): https://github.com/pikepdf/pikepdf
- OCRmyPDF (MPL-2.0; cần Ghostscript + Tesseract): https://ocrmypdf.readthedocs.io/ · https://github.com/ocrmypdf/OCRmyPDF
- Tesseract (Apache-2.0) + dữ liệu `vie`: https://github.com/tesseract-ocr/tesseract
- Ghostscript (AGPL-3.0 OR commercial, Artifex): https://www.ghostscript.com/licensing/
- MuPDF (AGPL-3.0 OR commercial): https://mupdf.com/licensing/
- img2pdf (LGPL-3.0): https://gitlab.mister-muffin.de/josch/img2pdf
- veraPDF (MPL-2.0 OR GPL-3.0+): https://github.com/veraPDF/veraPDF-library · https://verapdf.org/
- pyHanko (MIT, PAdES/PKCS#11): https://github.com/MatthiasValvekens/pyHanko
- Okular / Poppler (GPL-2.0+): https://okular.kde.org/ · https://poppler.freedesktop.org/
- PDF Association (chuẩn + redaction an toàn), ETSI PAdES — xem `docs/specs/namipdf-v18/04 §4`.
- `docs/adr/ADR-0002` (Debian 13 trixie), `docs/adr/ADR-0015` ("GUI mở ≠ chạy được").
