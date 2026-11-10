# NaMiPDF — Ma trận tương thích (COMPAT-MATRIX) · M0 baseline

**Ngày:** 10/11/2026 · **Mốc:** M0 (baseline — **PHÂN TÍCH** hiện trạng, KHÔNG phải tuyên bố tính năng đã hoàn tất).
**Stack chọn (ADR-0001 NaMiPDF):** Okular (`GPL-2.0+`) + Poppler/poppler-utils (`GPL-2.0+`) + qpdf (`Apache-2.0`)/pikepdf (`MPL-2.0`) + tesseract-ocr-vie/ocrmypdf (`Apache-2.0`/`MPL-2.0`, +Ghostscript AGPL) + img2pdf (`LGPL-3.0+`) + veraPDF (`MPL-2.0`/`GPL-3.0+`).
**Tài liệu đầu vào:** `docs/specs/namipdf-v18/` (01→05). **Chi tiết chọn engine + license:** `docs/pdf/ADR-0001-namipdf-engine.md`.

> **Cảnh báo trung thực — đọc trước.** Mức C ở đây được **ĐÁNH GIÁ từ hành vi đã biết** của Okular/Poppler/qpdf/Tesseract…, **CHƯA** dòng nào được xác minh bằng **PDF-01..13 trên máy thật** hay **pilot**. Theo kit (`README §19`): *"'Đạt' phải có tệp thử, kết quả mở/lưu lại và bằng chứng."* Cột **Fixture** = tệp thử **CẦN CÓ** (chưa tạo ở M0), là yêu cầu phát triển. Ngay cả dòng **C0** phải hiểu là *"stack làm được theo hiểu biết, chờ xác nhận bằng fixture thật"*.

---

## Chú giải (legend)

### Chế độ / quy trình (Mode)
Xem · Chú thích · Sửa nội dung · Biểu mẫu & Ký số · OCR · Sắp xếp trang · Che dữ liệu · Xuất/In · An toàn (xuyên suốt).

### Mức năng lực (P) — theo kit (README §19)
- **P0** — trước bản dùng rộng rãi (bắt buộc cho bản đầu).
- **P1** — bản chuyên nghiệp.
- **P2** — chuyên sâu.

### Mức tương thích (C) — tái dùng thang kit, gán theo **tệp/tính năng/engine**, KHÔNG theo tên app
- **C0** — **có sẵn & round-trip đạt**: làm được NGAY bằng stack đã chọn, mở lại ở viewer độc lập đạt. *(chờ xác nhận bằng fixture thật)*
- **C1** — **có bằng stack + cấu hình/adapter nhẹ**, sai khác giới hạn.
- **C2** — **một phần**: cần dựng adapter/tích hợp engine mới + **cảnh báo**; chưa chứng nhận.
- **C3** — **không làm được bằng Okular/Poppler đơn thuần**; cần **engine chuyên dụng + chứng nhận độc lập** (hoặc tuyến thay thế). Gồm các **gate tuyệt đối**.

### Mức nghiêm trọng (Severity)
- **P0★** — **cổng tuyệt đối** (kit `04 §3`): mất dữ liệu không cảnh báo / redaction vẫn khôi phục được / xác nhận chữ ký sai / JS–attachment tự chạy / ghi đè bản gốc / "overlay" nói dối là "sửa text gốc".
- **P1** — tác vụ hằng ngày. · **P2** — chuyên nghiệp. · **P3** — nâng cao/ít dùng.

---

## Bảng tổng hợp

### Đếm theo mức C (tổng **66** dòng yêu cầu)

| Mức C | Số dòng | Ý nghĩa |
|---|---|---|
| **C0** | **7** | Có sẵn ngay bằng stack (chờ xác nhận fixture) |
| **C1** | **22** | Có bằng stack + cấu hình/adapter nhẹ |
| **C2** | **28** | Một phần — cần dựng adapter/engine + cảnh báo |
| **C3** | **9** | Không bằng Okular/Poppler đơn thuần — cần engine chuyên dụng + chứng nhận |
| **Tổng** | **66** | |

### Đếm theo nhóm × mức C

| Nhóm (Mode) | C0 | C1 | C2 | C3 | Tổng |
|---|---|---|---|---|---|
| A. Xem & điều hướng | 1 | 4 | 2 | 0 | 7 |
| B. Chú thích | 0 | 2 | 3 | 0 | 5 |
| C. Sửa nội dung | 0 | 0 | 3 | 2 | 5 |
| D. Sắp xếp trang | 3 | 3 | 1 | 0 | 7 |
| E. OCR (vi) | 0 | 1 | 4 | 0 | 5 |
| F. Biểu mẫu | 0 | 2 | 1 | 2 | 5 |
| G. Ký số | 0 | 1 | 2 | 1 | 4 |
| H. Che dữ liệu (Redaction) | 0 | 0 | 2 | 2 | 4 |
| I. PDF/A & PDF/UA | 0 | 0 | 2 | 1 | 3 |
| J. Xuất / Chuyển đổi / In | 3 | 5 | 1 | 1 | 10 |
| K. An toàn file & Lưu | 0 | 1 | 6 | 0 | 7 |
| L. Tài liệu bảo vệ/lạ | 0 | 3 | 1 | 0 | 4 |
| **Tổng** | **7** | **22** | **28** | **9** | **66** |

### 9 dòng C3 — gap trung thực, rủi ro cao (KHÔNG bằng Okular/Poppler)

| ID | Tác vụ | Vì sao C3 | Đường đi (mốc) |
|---|---|---|---|
| `NP-ED-02` | Sửa chữ trong content stream (đổi font/size/màu) | Không engine FOSS đạt Acrobat; LO Draw phá cấu trúc (kit cấm) | M2 — spike engine riêng; v1 chỉ overlay |
| `NP-ED-03` | Thêm/xóa/di chuyển/thay ảnh–vector object-level | Như trên (watermark/header/footer/page-num subset = C2) | M2 |
| `NP-FM-03` | **Author** AcroForm (tạo field, help, a11y) | Okular không tạo field; không FOSS tốt | M2 |
| `NP-FM-04` | **XFA động** (điền/render) | Poppler chỉ phát hiện; không render XFA | M2 — detect + cảnh báo + fallback |
| `NP-SG-03` | **PAdES ký thật** (token/HSM/PKCS#11, LTV) | Cần engine ký + chứng nhận (pyHanko beta) | M3 — flag tắt tới khi PASS |
| `NP-RD-02` | **Redaction** xoá vĩnh viễn content/object/metadata/rev | Không FOSS chứng minh sẵn; mutool=AGPL | M3 — flag tắt tới khi PASS |
| `NP-RD-03` | **Kiểm độc lập** redaction (reparse/extract/OCR lại) | Phải dựng harness kiểm chứng | M3 |
| `NP-AR-02` | **PDF/UA** tagged (reading order/alt/table header) | Không generator FOSS tốt | M3 — veraPDF + screen reader |
| `NP-EX-06` | Xuất bảng → CSV/ODS/XLSX | Không trích bảng FOSS tin cậy | M2+ (preview + đối soát) |

### 4 gap rủi ro cao nhất (đánh dấu theo yêu cầu) + Severity P0★
**PAdES ký thật (`NP-SG-03`) · Redaction chứng minh (`NP-RD-02/03`) · True-content-edit (`NP-ED-02/03`) · XFA (`NP-FM-04`)** — cộng **PDF/UA (`NP-AR-02`)**. Đây là nơi dễ "overclaim" nhất; **tuyệt đối không** bật nút/ghi nhãn khi chưa pass test độc lập.

---

## Ma trận chi tiết

Cột: **ID | Mode | P | Expected (kỳ vọng) | Available-now-via | Gap/needs-building | C | Fixture | Severity | Notes**

### A. Xem & điều hướng — P0

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-VW-01 | Xem | P0 | Mở PDF 1.x/2.0, đa tab/cửa sổ, USB/SMB/WebDAV, file đính kèm email, PDF mật khẩu (có quyền) | Okular + KIO (smb/webdav); mật khẩu Okular | Xác nhận quyền SMB/WebDAV theo portal NaMiOS | C1 | PDF-01 | P1 | Không tự tải URL ngoài tệp |
| NP-VW-02 | Xem | P0 | Liên tục/đơn/đôi, bìa riêng, xoay nhìn, fit width/page, zoom 25–800%, thumbnails, outline, page labels, history | Okular (native) | — | C0 | PDF-01 | P1 | Không tự đảo màu khi in |
| NP-VW-03 | Xem | P0 | Tìm toàn văn **có/không dấu** + exact, tìm trong annotation/form, highlight | Okular/poppler search | **Tìm không-dấu (accent-insensitive)** cần cấu hình/patch | C1 | PDF-01 | P1 | — |
| NP-VW-04 | Xem | P0 | Copy text giữ Unicode/dấu; nhận biết text-layer / scan / thiếu font | Okular copy; `pdffonts`/`pdftotext` phát hiện | Gắn cờ "thiếu font" trong UI | C1 | PDF-01 | P1 | — |
| NP-VW-05 | Xem | P0 | Chọn/copy text–ảnh–link; link ngoài xác nhận tên miền; mailto/attach không tự chạy; phát hiện script/embedded + cảnh báo | Okular | **Xác nhận tên miền + phát hiện script/embedded** = dựng | C2 | PDF-12 | **P0★** | An toàn link/attachment |
| NP-VW-06 | Xem | P0 | Trợ năng: reading order/tag, phím tắt, high contrast, phóng, TTS hệ thống (tách OCR) | Okular + Qt Speech | Reading-order phụ thuộc tag; TTS tích hợp portal | C2 | PDF-10 | P1 | — |
| NP-VW-07 | Xem | P0 | File Manager preview sandboxed, mở mặc định NaMiPDF, Recent Files theo quyền riêng tư, print dialog thống nhất | Dolphin thumbnailer (poppler) + MIME default | Sandbox thumbnailer + chính sách Recent Files | C1 | — | P1 | — |

### B. Chú thích — P0

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-AN-01 | Chú thích | P0 | Highlight/underline/strikeout/note/callout/textbox/shapes/arrow/stamp/freehand; màu/độ dày/opacity | Okular annotation tools | — | C1 | PDF-02 | P1 | Lưu **vào PDF** (không sidecar) |
| NP-AN-02 | Chú thích | P0 | Lưu annotation vào PDF, giữ author/date xuyên viewer, reply + status resolved + thread | Okular (lưu annotation) | **Reply/thread/status** theo chuẩn = dựng | C2 | PDF-02 | P1 | Không lẫn text gốc |
| NP-AN-03 | Chú thích | P1 | Danh sách chú thích lọc theo người/trang/loại; xuất tóm tắt nhận xét | Okular reviews panel | **Export summary** = dựng | C2 | PDF-02 | P2 | — |
| NP-AN-04 | Chú thích | P0 | Undo/redo; flatten **bản sao** có cảnh báo; không flatten bản gốc âm thầm | Okular undo | **Flatten** qua qpdf/pikepdf/Ghostscript + cảnh báo | C2 | PDF-02 | P1 | — |
| NP-AN-05 | Chú thích | P1 | Stamp có **nguồn/giấy phép** | Okular stamps | Bộ stamp có giấy phép rõ | C1 | — | P2 | — |

### C. Sửa nội dung thực — P1 (có kiểm khả năng)

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-ED-01 | Sửa nội dung | P1 | Hiện trạng thái **Text/Scan/Mixed/Signed/Protected** + font nhúng/thay trước khi sửa | poppler `pdfinfo`/`pdffonts` + sniff | **Document Inspector** = dựng | C2 | PDF-03 | P1 | Điều kiện vào mọi sửa |
| NP-ED-02 | Sửa nội dung | P1 | Sửa/đổi chữ trong content stream; đổi font/size/spacing/màu | — | **Engine edit** riêng; LO Draw bị cấm (phá cấu trúc) | **C3** | PDF-03 | **P0★** | **Gap cao.** Text cũ phải hết copy/tìm hoặc cảnh báo |
| NP-ED-03 | Sửa nội dung | P1 | Thêm/xóa/di chuyển/thay ảnh–vector object; align/crop; watermark/header/footer/số trang | Watermark/header/footer/số-trang qua pikepdf overlay (C2) | **Object-level add/del/move/replace** = C3 | **C3** | PDF-03 | P1 | Subset overlay làm được sớm |
| NP-ED-04 | Sửa nội dung | P1 | Sửa đoạn **không** rasterize cả trang; reflow chỉ khi cấu trúc tin; "thêm nội dung" ≠ "sửa text gốc" | Text-box overlay (pikepdf) + nhãn | Chính sách + nhãn UI | C2 | PDF-03 | **P0★** | **Cấm** quảng cáo overlay là thay text cũ |
| NP-ED-05 | Sửa nội dung | P1 | Dọn trang quét: deskew, tương phản, resize, nén-có-preview, giảm dung lượng, kiểm sau tối ưu | ocrmypdf `--deskew/--clean`; Ghostscript nén | Preview sai khác + kiểm sau = dựng | C2 | PDF-05 | P2 | — |

### D. Sắp xếp trang — P1

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-PG-01 | Sắp xếp trang | P1 | Xoay trang (lossless) | qpdf `--rotate` / pikepdf | — | C0 | PDF-04 | P1 | — |
| NP-PG-02 | Sắp xếp trang | P1 | Chèn/xóa/trích/đổi thứ tự trang | qpdf `--pages` / pikepdf | UI kéo-thả | C1 | PDF-04 | P1 | Okular không reorder → dùng qpdf |
| NP-PG-03 | Sắp xếp trang | P1 | Merge/split nhiều PDF | qpdf / `pdfunite` / `pdfseparate` | — | C0 | PDF-04 | P1 | Metadata/bookmark theo chính sách |
| NP-PG-04 | Sắp xếp trang | P1 | Thay trang quét; crop lề | pikepdf MediaBox/CropBox | Preview crop | C1 | PDF-04 | P2 | — |
| NP-PG-05 | Sắp xếp trang | P1 | Mã hóa/giải mã (có quyền), đặt permission | qpdf `--encrypt/--decrypt` | — | C1 | — | P1 | Không vượt bảo vệ |
| NP-PG-06 | Sắp xếp trang | P2 | Linearize (fast web view) | qpdf `--linearize` | — | C0 | — | P2 | — |
| NP-PG-07 | Sắp xếp trang | P1 | Batch: rename/merge/OCR/export/watermark trên danh sách, preview số tệp, không ghi đè, hủy được, báo từng tệp | — | **Orchestrator batch** qua qpdf/ocrmypdf = dựng | C2 | — | P1 | Mốc M4 |

### E. OCR tiếng Việt — P0 đọc / P1 sửa

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-OCR-01 | OCR | P0 | OCR scan vi có dấu, Việt–Anh, xoay/deskew, gray/color → text-layer có tọa độ, giữ ảnh gốc ("searchable PDF") | ocrmypdf + tesseract-ocr-vie | — | C1 | PDF-05 | P1 | Accuracy tùy chất lượng; không cam kết 1 tỷ lệ |
| NP-OCR-02 | OCR | P1 | Trước chạy chọn ngôn ngữ/trang/output/giới hạn CPU; offline mặc định | ocrmypdf flags | **UI tiền-chạy** = dựng | C2 | PDF-05 | P2 | — |
| NP-OCR-03 | OCR | P1 | Confidence theo vùng; sửa lớp OCR trên bản sao; phân biệt "sửa OCR" vs "thay ảnh trang"; cờ số tiền/bảng cần người kiểm | tesseract TSV confidence | **UI confidence + cờ vùng số** = dựng | C2 | PDF-05 | P1 | — |
| NP-OCR-04 | OCR | P1 | Scan qua Device Hub/SANE/eSCL/WSD, ADF/duplex, xử lý kẹt, ghi trang xong | sane-airscan/skanlite (đã ship 0500) | **Tích hợp OCR↔scan** = dựng | C2 | — | P2 | — |
| NP-OCR-05 | OCR | P0 | Chỉ gắn nhãn PDF/A khi validator độc lập đạt; không sửa tài liệu đã ký | veraPDF gate | Nối gate vào pipeline | C2 | PDF-10 | **P0★** | — |

### F. Biểu mẫu — P0 AcroForm / P1 nâng cao

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-FM-01 | Biểu mẫu | P0 | Điền text/checkbox/radio/dropdown/list, required, tab order, validation/calc an toàn; save/reopen giữ giá trị+appearance xuyên viewer | Okular form fill + save; poppler appearance | — | C1 | PDF-06 | P1 | — |
| NP-FM-02 | Biểu mẫu | P1 | Export bản điền hoặc flatten; FDF/XFDF khi đã test | pdftk-java/pikepdf FDF | **Flatten + FDF/XFDF** kiểm | C2 | PDF-06 | P2 | — |
| NP-FM-03 | Biểu mẫu | P1 | **Tạo** field, help text, quyền, a11y label, preview | — | **Form authoring** = dựng (không FOSS tốt) | **C3** | PDF-06 | P2 | — |
| NP-FM-04 | Biểu mẫu | P1 | **XFA động**: phát hiện + cảnh báo chỉ-xem/không-điền-an-toàn, fallback, không mất XFA khi lưu | poppler phát hiện XFA | **Không render/điền XFA** = C3 | **C3** | PDF-07 | P1 | **Gap cao**; không hỏng tệp gốc |
| NP-FM-05 | Biểu mẫu | P0 | **Không** chạy PDF JavaScript tùy ý | Okular (không exec JS) + chính sách | Khóa chính sách | C1 | PDF-12 | **P0★** | — |

### G. Ký số — P1

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-SG-01 | Ký số | P1 | Tách chữ ký tay (ảnh/nét = annotation) khỏi chữ ký số mật mã | Okular stamp vs signature + chính sách | — | C1 | PDF-08 | **P0★** | Không gắn "hợp lệ" từ ảnh con dấu |
| NP-SG-02 | Ký số | P1 | Hiển thị cert/issuer/trust chain/time/byte-range/sửa-sau-ký/revocation/timestamp-LTV hoặc "chưa kiểm được offline" | Okular/poppler verify (NSS/GnuTLS) | **5 trạng thái phân biệt** đầy đủ = dựng | C2 | PDF-08 | **P0★** | Không báo xanh sai |
| NP-SG-03 | Ký số | P1 | **Ký PAdES** (B-B/B-T/B-LT/B-LTA) qua token/HSM/PKCS#11 hoặc dịch vụ hợp lệ; OCSP/CRL/TSA; SmartAI không nhận PIN; test vector + viewer độc lập | — | **Engine ký (pyHanko M3)** + chứng nhận | **C3** | PDF-08 | **P0★** | **Gap cao.** Nút tắt tới khi PASS |
| NP-SG-04 | Ký số | P1 | Mọi sửa/tối ưu/OCR sau ký đánh giá tác động; lưu bản sao; cảnh báo trước; không tự hủy chữ ký | Chính sách + nhánh incremental-update (pikepdf) | Đánh giá tác động = dựng | C2 | PDF-08 | **P0★** | — |

### H. Che dữ liệu (Redaction) — P1 (bắt buộc trước công vụ)

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-RD-01 | Che dữ liệu | P1 | Hai bước: đánh dấu vùng → **xác nhận áp dụng xóa vĩnh viễn** | — | **UI 2-bước** = dựng | C2 | PDF-09 | **P0★** | — |
| NP-RD-02 | Che dữ liệu | P1 | Xóa content stream (text/hình/vector), lớp OCR, annotation/form, metadata, bookmark, attachment, hidden layers, **incremental revisions/object cũ** | — | **Engine redaction** (pikepdf/qpdf xóa + rasterize fallback; mutool=AGPL) | **C3** | PDF-09 | **P0★** | **Gap cao.** Rectangle đen ≠ che an toàn |
| NP-RD-03 | Che dữ liệu | P1 | **Kiểm độc lập**: reparse, extract text, string search, object view, OCR lại vùng, viewer khác; không rò trong thumbnail/cache/autosave/log | — | **Harness kiểm chứng** = dựng | **C3** | PDF-09 | **P0★** | Gate tuyệt đối |
| NP-RD-04 | Che dữ liệu | P1 | Redaction không hoàn tác trên bản xuất; giữ bản gốc theo quyền; nếu engine chưa chứng minh → **tắt "Áp dụng"** hoặc rasterize toàn trang có cảnh báo | pdftoppm rasterize fallback + chính sách | — | C2 | PDF-09 | **P0★** | — |

### I. Lưu trữ & trợ năng (PDF/A, PDF/UA) — P1/P2

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-AR-01 | Xuất/In | P1 | PDF/A-1/2/3/4 đúng font/ICC/metadata/attachment; **gắn nhãn chỉ khi veraPDF đạt** | ocrmypdf/Ghostscript gen PDF/A-1b/2b + veraPDF validate | Nối validator-gate | C2 | PDF-10 | P1 | "Không ghi PDF/A chỉ vì có dropdown" |
| NP-AR-02 | Xuất/In | P2 | **PDF/UA / Tagged**: heading, reading order, alt text, table header, vi-VN, bookmark, form label, keyboard; veraPDF + screen reader thủ công | veraPDF validate | **Generator tagged-PDF** = dựng (không FOSS tốt) | **C3** | PDF-10 | P2 | **Gap cao** |
| NP-AR-03 | Xuất/In | P2 | Chuyển đổi có thể mất tương tác → **preview** | Chính sách + preview | — | C2 | PDF-10 | P2 | — |

### J. Xuất / Chuyển đổi / In — P0/P1

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-EX-01 | Xuất/In | P0 | Xuất PDF từ NaMiOffice theo khổ/lề/trang, bookmark/hyperlink, font theo giấy phép, metadata, nén ảnh, PDF/A khi validator đạt | LibreOffice export + veraPDF gate | Nối pipeline thống nhất | C1 | PDF-10 | P1 | — |
| NP-EX-02 | Xuất/In | P1 | Xuất ảnh PNG/JPEG/TIFF | `pdftoppm` (poppler-utils) | — | C0 | — | P2 | — |
| NP-EX-03 | Xuất/In | P1 | Xuất text UTF-8 | `pdftotext` | — | C0 | — | P2 | Giữ dấu vi |
| NP-EX-04 | Xuất/In | P1 | Xuất HTML đơn giản | `pdftohtml` | — | C1 | — | P2 | — |
| NP-EX-05 | Xuất/In | P1 | Xuất ODT/DOCX cho tài liệu cấu trúc tin | LibreOffice headless import PDF | Chọn tài liệu "đáng tin" + so layout | C2 | — | P2 | Không cam kết giữ bảng/format |
| NP-EX-06 | Xuất/In | P1 | Xuất bảng → CSV/ODS/XLSX sau preview vùng + đối soát | — | **Trích bảng** = dựng (không FOSS tin cậy) | **C3** | — | P3 | — |
| NP-EX-07 | Xuất/In | P1 | Nhập ảnh → PDF | img2pdf (lossless) | — | C0 | — | P1 | — |
| NP-EX-08 | Xuất/In | P0 | In chọn trang/chẵn/lẻ/n-trang-mỗi-tờ, duplex, scale, poster/booklet khi backend hỗ trợ, nhiều bản + collation | Okular print (Qt→CUPS) | Poster/booklet phụ backend | C1 | PDF-11 | P1 | — |
| NP-EX-09 | Xuất/In | P2 | Print to PDF (máy in ảo) với NaMiPDF làm viewer | cups-pdf / print-to-file | Nối MIME viewer | C1 | PDF-11 | P2 | — |
| NP-EX-10 | Xuất/In | P0 | Gửi CUPS/IPP, trạng thái hàng đợi, lỗi rõ ("A3 không hỗ trợ"/"offline"/"cần xác thực") | CUPS + print-manager (đã ship 0500) | **Surfacing lỗi hàng đợi** rõ tiếng Việt | C1 | PDF-11 | P1 | Spool nhạy cảm theo chính sách |

### K. An toàn file & Lưu — P0 (xuyên suốt)

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-SEC-01 | An toàn | P0 | **Sniff** thay vì tin extension; kiểm size/pages/objects, xref loop, malformed font/image, decompression bomb, embedded file, JS, link ngoài | poppler + libmagic | **Document Inspector** = dựng | C2 | PDF-12 | **P0★** | — |
| NP-SEC-02 | An toàn | P0 | **Sandbox** parser/renderer trong worker **không mạng**, budget CPU/RAM/time, fuzz corpus, hủy không hỏng file | — | **Worker sandbox** (bwrap/namespaces/seccomp) quanh Okular/poppler = dựng | C2 | PDF-12 | **P0★** | — |
| NP-SEC-03 | An toàn | P0 | Tắt PDF JS, auto-open attachment, network fetch mặc định; link hiện đích trước khi mở | Okular defaults + chính sách | Khóa cấu hình | C1 | PDF-12 | **P0★** | — |
| NP-SEC-04 | An toàn | P0 | **Atomic save** (temp+fsync+rename) local; SMB/cloud lock/version conflict + Save As; nhánh incremental cho tài liệu ký | — | Okular lưu nhưng chưa atomic/conflict-aware = dựng | C2 | PDF-13 | **P0★** | Không thay bytes đã ký |
| NP-SEC-05 | An toàn | P0 | Autosave nháp + phục hồi mất điện, backup, re-open validation, checksum | — | = dựng | C2 | PDF-13 | **P0★** | "không gọi file dở là đã lưu" |
| NP-SEC-06 | An toàn | P0 | Xóa temp/OCR cache/thumbnail/search index cho tệp nhạy cảm theo chính sách; không đưa nội dung vào telemetry/log | — | = dựng | C2 | PDF-13/09 | **P0★** | — |
| NP-SEC-07 | An toàn | P1 | SmartAI: giải thích lỗi, tóm tắt theo quyền, **đề xuất** vùng che (không tự áp), xem diff + xin xác nhận; không tự ký/redact/upload; coi PDF là dữ liệu không tin | — | **SmartAI adapter** = dựng | C2 | — | P1 | Nội dung PDF có thể chứa prompt độc |

### L. Tài liệu bảo vệ / cấu trúc lạ — P1

| ID | Mode | P | Expected | Available-now-via | Gap | C | Fixture | Sev | Notes |
|---|---|---|---|---|---|---|---|---|---|
| NP-PR-01 | Xem | P0 | Mã hóa/password **chỉ mở khi có quyền**; không vượt bảo vệ | Okular/qpdf với mật khẩu | — | C1 | PDF-12 | **P0★** | — |
| NP-PR-02 | Xem | P2 | Portfolio/embedded, optional layers (OCG), 3D, video, XFA, DRM/IRM, PDF hỏng: trạng thái **View/Edit/Preserve/Unsupported** từng tính năng | Okular (layers có; 3D/video không) + Inspector | Ma trận trạng thái per-feature = dựng | C2 | PDF-12 | P2 | — |
| NP-PR-03 | Xem | P0 | Đính kèm thực thi **không tự chạy**; export qua dialog/quét | Chính sách | — | C1 | PDF-12 | **P0★** | — |
| NP-PR-04 | Xem | P2 | Tuân thủ giới hạn in/sao chép + giấy phép | Okular honor permissions | — | C1 | — | P2 | — |

---

## Ghi chú thực thi (M0)

- **Chưa dòng nào "Đã hỗ trợ".** Điều kiện tối thiểu để chuyển: (1) pass **fixture PDF-01..13** trên **máy thật** + mở lại ở **viewer độc lập**; (2) với redaction/chữ ký = **gate tuyệt đối**, không lấy trung bình bù lỗi; (3) QA độc lập duyệt.
- Mức C = **đánh giá kỹ thuật** theo hành vi đã biết của stack, là **điểm khởi đầu** viết fixture — **không** phải kết quả đo. Con số (C0=7, C1=22, C2=28, C3=9 / 66) = **số dòng yêu cầu**.
- Pipeline gói **đã có** qua `0420-pdf.list.chroot` (poppler-utils/qpdf/tesseract-ocr-vie/ocrmypdf/img2pdf; xem `docs/pdf/NAMIPDF-PACKAGING.md`); **còn bổ sung** `python3-pikepdf` + `veraPDF` — **`verified_on_host: NO`**, phải `apt-cache show` trên trixie trước `lb build`.
