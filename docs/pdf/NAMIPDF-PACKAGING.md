# NaMiOS — NaMiPDF: đóng gói + nhãn hiển thị (ISO level)

**Ngày:** 10/11/2026 · **Trạng thái tài liệu:** trạng thái đóng gói thật hiện tại, không phải tuyên bố NaMiPDF đã đạt "full chức năng" theo kit.
**Đọc cùng:** `docs/specs/namipdf-v18/README.md` + `01_TINH_NANG_UIUX.md` (kit gốc, không sửa file đó); `docs/specs/namipdf-v18/02_PDF_CHUYEN_SAU.md` + `03_KIEN_TRUC_BAO_MAT.md` cho các mốc sau.

> Tài liệu này chỉ nói về **việc đóng gói + nhãn hiển thị ở mức ISO** (package list, hook brand, mimeapps mặc định) — KHÔNG phải ADR kiến trúc hay ma trận tính năng P0/P1/P2 (xem tài liệu ADR/matrix riêng trong `docs/pdf/` do phần việc khác phụ trách, nếu có, để tránh trùng nội dung).

## 1. NaMiPDF là gì, ở mức đóng gói hôm nay

**Trạng thái: `partial` — đã đóng gói đủ pipeline hỗ trợ + rebrand nhãn menu + đặt làm handler PDF mặc định; CHƯA verified_on_host; CHƯA có UI chế độ Sửa nội dung/Biểu mẫu & Ký số riêng của NaMiPDF.**

NaMiPDF = **tên hiển thị cho Okular (KDE)** nguyên bản — ứng dụng đã cài sẵn từ trước qua `distro/live-build/config/package-lists/0100-desktop-kde.list.chroot` (dòng `okular`), cộng thêm một pipeline dòng lệnh hỗ trợ xung quanh (trích xuất văn bản/ảnh, thao tác trang không mất chất lượng, OCR tiếng Việt, ảnh→PDF). Đây **không phải** ứng dụng viết mới từ đầu, và **không phải** "sửa mọi PDF như Adobe Acrobat" — Okular là trình xem/chú thích PDF (+ một số chữ ký/form cơ bản tùy bản build), không phải trình biên tập content-stream đầy đủ.

## 2. Gói đã thêm — `package-lists/0420-pdf.list.chroot`

| Gói | Vai trò | Xác minh tồn tại trong `trixie` |
|---|---|---|
| `poppler-utils` | Trích văn bản/ảnh/metadata (`pdftotext`, `pdftoppm`, `pdfimages`, `pdfinfo`) — dùng cho tìm kiếm toàn văn, xuất ảnh trang, đầu vào OCR | CÓ — `25.03.0-5+deb13u4` theo `qa.debian.org/madison.php` (truy xuất 10/11/2026) |
| `qpdf` | Thao tác trang KHÔNG MẤT DỮ LIỆU: merge/split/xoay/trích trang, mã hoá, linearize | CÓ — `12.2.0-1` |
| `tesseract-ocr` | Engine OCR lõi cho PDF ảnh quét | CÓ — `5.5.0-1+b1` |
| `tesseract-ocr-vie` | Gói ngôn ngữ tiếng Việt cho `tesseract-ocr` (bắt buộc để OCR đúng chữ có dấu) | CÓ — `1:4.1.0-2` |
| `ocrmypdf` | Pipeline OCR hoàn chỉnh: ghép text layer ẩn lên ảnh gốc, xuất PDF tìm/copy được mà vẫn giữ ảnh hiển thị | CÓ — `16.7.0+dfsg1-3` |
| `img2pdf` | Ghép ảnh rời thành PDF không tái nén mất chất lượng (khác `convert` lossy của ImageMagick) | CÓ — `0.6.1-1` |

`okular` (Okular tự thân, gói đã khai sẵn ở `0100-desktop-kde.list.chroot`) **KHÔNG được re-list** trong `0420-pdf.list.chroot` — file chỉ thêm pipeline hỗ trợ, tránh khai trùng gói giữa hai danh sách.

**verified_on_host: NO** theo đúng quy ước repo (chưa chạy `apt-cache show`/`lb build` trên build host Debian 13 trixie thật) — đã đối chiếu cả 6 tên gói qua công cụ `madison` chính thức của Debian (`qa.debian.org/madison.php`), xác nhận mỗi gói đều có bản build sẵn trong suite `trixie` đúng kiến trúc amd64 (và nhiều kiến trúc khác). Mức tin cậy cao hơn "chưa kiểm" thông thường nhưng **không thay thế** bước `apt-cache show` trên build host thật trước khi `lb build` phát hành.

## 3. Nhãn hiển thị — `hooks/normal/0453-namipdf-brand.hook.chroot`

- Đổi **Name=/Name[vi]=** trong `/usr/share/applications/org.kde.okular.desktop` (và dò thêm `okular.desktop` nếu tên gói dùng id rút gọn — bỏ qua an toàn nếu không thấy file) thành **"NaMiPDF (Okular)"**.
- **GIỮ NGUYÊN** `Exec=`, `Icon=`, `MimeType=` của Okular — không đổi hành vi chạy/biểu tượng/khai báo MIME.
- Giữ chữ "Okular" trong nhãn hiển thị để ghi nhận nguồn đúng giấy phép KDE/Okular (không gỡ attribution) — đúng tinh thần đã làm với NaMiMail/Thunderbird (`hooks/normal/0452-namimail-brand.hook.chroot`).
- `bash -n` pass; file đã `chmod +x`. **verified_on_host: NO** — máy soạn hook không có Okular cài, chưa chạy thật trên ISO đã boot.

## 4. Ứng dụng mặc định mở PDF — `includes.chroot/etc/skel/.config/mimeapps.list`

`application/pdf=org.kde.okular.desktop` **đã có sẵn** trong cả hai mục `[Default Applications]` và `[Added Associations]` của file này (thêm từ phần việc Windows-familiar UX trước đó, commit `8c3a7e0`, cùng đợt với các association DOCX/XLSX/PPTX→LibreOffice) — không cần sửa thêm để NaMiPDF/Okular là handler PDF mặc định cho user mới. Đã đọc lại toàn bộ file và xác nhận: entry PDF không đụng/không đè các entry Office đã có; file giữ nguyên, không có thay đổi nào cho phần việc này.

Lưu ý còn nguyên trong file: `xdg-mime query default application/pdf` phải được đối chiếu lại trên build host/ISO đã boot thật để xác nhận giá trị trả về đúng là `org.kde.okular.desktop` — tên id là `verified_on_host: NO` cho tới khi có bằng chứng boot thật (xem `docs/specs/UX-WINDOWS-FAMILIAR.md`).

## 5. KHÔNG claim ở mức đóng gói này (mốc sau, theo `docs/specs/namipdf-v18/`)

- **Sửa nội dung thực** (content-stream edit: đổi chữ/font/ảnh/vector tại chỗ, reflow có kiểm soát) — đây là P1 "có kiểm khả năng" của kit (`01_TINH_NANG_UIUX.md` §3); đóng gói hôm nay chỉ cho xem/chú thích (Okular) + thao tác trang không mất dữ liệu (qpdf), KHÔNG phải trình biên tập nội dung PDF đầy đủ.
- **Ký số PAdES / chữ ký điện tử có giá trị pháp lý** — thuộc `02_PDF_CHUYEN_SAU.md` (biểu mẫu & ký số); chưa có hạ tầng CA/timestamp/xác thực chữ ký trong đóng gói này.
- **Redaction (che dữ liệu) có chứng nhận** — che hiển thị không đồng nghĩa xoá dữ liệu khỏi content stream/metadata; cần quy trình kiểm chứng riêng theo `03_KIEN_TRUC_BAO_MAT.md` trước khi gọi là "redaction an toàn".
- **PDF/A, PDF/UA xuất có validator đạt** — chưa thiết lập pipeline validator trong đóng gói này; `01_TINH_NANG_UIUX.md` §4 yêu cầu PDF/A "chỉ khi validator đạt", không phải mặc định bật.
- Mọi tính năng trên đều cần tài liệu/pipeline riêng + kiểm thử độc lập trước khi đổi trạng thái từ `partial`/`not_shipped` sang `done` — không coi việc thêm gói + đổi nhãn menu ở tài liệu này là đã hoàn tất các mục trên.

## 6. Tham chiếu

- `distro/live-build/config/package-lists/0420-pdf.list.chroot`
- `distro/live-build/config/hooks/normal/0453-namipdf-brand.hook.chroot`
- `distro/live-build/config/includes.chroot/etc/skel/.config/mimeapps.list`
- `distro/live-build/config/package-lists/0100-desktop-kde.list.chroot` (gói `okular` gốc)
- Mẫu đã làm trước cho Mail: `distro/live-build/config/hooks/normal/0452-namimail-brand.hook.chroot`, `docs/office/ECOSYSTEM-MAIL-NOTES-FORMS.md`
