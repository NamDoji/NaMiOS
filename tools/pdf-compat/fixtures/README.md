# NaMiPDF — 13 fixture PDF-01..PDF-13 (tools/pdf-compat/fixtures)

Sinh bởi `make_fixtures.py` (reportlab + pikepdf + Pillow). Chạy lại
(idempotent, không cần mạng, tự ghi đè):

```bash
python3 tools/pdf-compat/fixtures/make_fixtures.py
```

## Về cách đánh số

`docs/specs/namipdf-v18/04_KIEM_THU_PHAT_HANH.md` mục 2 ("Test theo công
việc") đã TỰ đánh số PDF-01..PDF-13 — nhưng đó là **13 CÔNG VIỆC kiểm thử**
(vd "PDF-02: thêm/chỉnh/xoá comment, save/reopen bằng hai viewer"), phần lớn
là **thao tác sống trên một viewer thật** (Okular, hai viewer khác nhau, máy
in CUPS thật...), không phải thuộc tính tĩnh của một file. Bộ 13 file dưới
đây dùng CÙNG cách đánh số 01..13 nhưng là **corpus đại diện tối thiểu**
(mỗi file nhắm một hoặc vài đặc điểm cấu trúc PDF cụ thể) để các công việc đó
CÓ INPUT mà chạy — không phải một phép ánh xạ 1:1 "file số N ⇔ công việc số
N trong kit". Bảng dưới liệt kê rõ fixture nào phục vụ công việc nào của kit
để không bị hiểu nhầm.

| # | File | Mô tả | Phục vụ công việc nào trong kit (04_KIEM_THU...) | Kiểm tra gì |
|---|------|-------|---------------------------------------------------|-------------|
| 01 | `01_text_vn.pdf` | 1 trang văn bản tiếng Việt, **text layer thật** (không phải ảnh), đủ dấu | PDF-01 (mở, search/copy) — bản rút gọn, không phải 200 trang | Text có thể chọn/copy/tìm (Ctrl+F); dấu tiếng Việt không vỡ |
| 02 | `02_scanned_image_only.pdf` | 1 trang render text ra ảnh raster rồi nhúng, **KHÔNG có text layer** | PDF-05 (OCR scan có dấu) — đây là **input** cho bước OCR, không phải bản thân phép đo CER/WER | Xác nhận "đây đúng là ảnh scan" (pdftotext/Ctrl+F phải trả rỗng) trước khi chạy OCR |
| 03 | `03_mixed_text_image.pdf` | 3 trang: text thật → ảnh raster → text thật | PDF-01 (ảnh+vector trộn text), tiền đề cho PDF-03 (sửa text/vector cạnh ảnh) | Text 2 trang đầu/cuối vẫn trích xuất đúng khi có trang ảnh xen giữa |
| 04 | `04_multipage_bookmarks.pdf` | 24 trang, outline/bookmark 2 cấp (chương/mục) | PDF-01 (nhiều trang+bookmark, bản rút gọn từ 200→24 trang), **input nguồn** cho PDF-04 (merge/split/reorder/rotate) | Outline đọc được đúng thứ bậc; dùng làm input cho `run_roundtrip.sh` bước qpdf reorder/split/merge |
| 05 | `05_acroform.pdf` | AcroForm: 1 text field (`ho_ten`) + 1 checkbox (`dong_y_nhan_email`) | PDF-06 (điền/tạo AcroForm, mở viewer thứ hai) | Field tồn tại đúng loại (`/Tx`, `/Btn`); **tab order/giá trị sau khi viewer thứ hai điền** là bước pilot cần Okular/Acrobat thật |
| 06 | `06_encrypted.pdf` | Mã hoá AES-256 (R=6): user password `user-pass`, owner password `owner-pass` | Mục "Corpus có quyền" (tài liệu bị mã hoá); liên quan an toàn mở file ở 05_PROMPT | Mở sai mật khẩu bị từ chối; mở đúng mật khẩu ra đúng nội dung |
| 07 | `07_signature_stub.pdf` | AcroForm có 1 field `/Sig` placeholder, `/Contents` rỗng, `SigFlags=3` | PDF-08 (chữ ký số) — **CHỈ là tiền đề cấu trúc**, KHÔNG đạt yêu cầu PDF-08 thật (5 trạng thái hợp lệ/hết hạn/thu hồi/sửa-sau-ký/offline) | Viewer/parser NHẬN DIỆN "tài liệu có trường chữ ký"; **không** dùng để test xác thực chữ ký thật |
| 08 | `08_attachment.pdf` | 1 tệp đính kèm `ghi-chu.txt` (UTF-8, có dấu) qua `/EmbeddedFiles` | Mục "Corpus có quyền" (tài liệu có embedded content); đối trọng AN TOÀN của PDF-12 (đính kèm thực thi) | Trích xuất đúng tên + nội dung tệp đính kèm, không tự thực thi |
| 09 | `09_js_openaction.pdf` | `/OpenAction` trỏ `/JavaScript`, payload **vô hại** (chỉ `app.alert` tĩnh) | PDF-12 (file có JS/đính kèm thực thi/bomb) — **mẫu JS/OpenAction**, không có decompression-bomb | Xác nhận parser/viewer **không tự chạy JS khi mở file** (an toàn bắt buộc ở 05_PROMPT) |
| 10 | `10_pdfa_ish.pdf` | `/OutputIntent` (ICC sRGB) + XMP khai `pdfaid:part=1`, `pdfaid:conformance=B` | PDF-10 (PDF/A và PDF/UA) — **"-ish"**: CHƯA chạy qua veraPDF, không claim đạt chuẩn PDF/A thật | Có đủ cấu trúc OutputIntent+XMP để tập dượt pipeline; **validate thật cần veraPDF (CI/pilot)** |
| 11 | `11_uri_link.pdf` | 1 liên kết `/URI` ra `https://pdfa.org/pdf-standards/` | PDF-01 (navigation/link) + khía cạnh an toàn (không tự fetch mạng khi mở file) | Link annotation tồn tại, trỏ đúng domain tài liệu chuẩn |
| 12 | `12_vn_heavy_diacritics.pdf` | 1 trang văn bản tiếng Việt dày đặc dấu (tên riêng, đủ 6 thanh điệu, thành ngữ) | PDF-05 (đối chứng "ground truth" dạng text thật, KHÔNG phải bản scan, cho so sánh với kết quả OCR) | Mọi tổ hợp dấu phổ biến còn nguyên khi trích xuất/copy |
| 13 | `13_corrupt_truncated.pdf` | Cắt cụt còn ~55% dung lượng gốc (mất xref/trailer) | PDF-13 (mất điện/hết dung lượng khi Save) + mục "corpus 20 file lỗi/fuzz" | Parser PHẢI phát hiện lỗi rõ ràng, không crash, không âm thầm trả nội dung sai |

## Công việc trong kit KHÔNG thể phủ bằng fixture tĩnh (ghi rõ để không bỏ sót)

- **PDF-02** (thêm/chỉnh/xoá comment, save/reopen bằng hai viewer khác nhau)
  và **PDF-03** (sửa một dòng text/vector, save/reopen) là THAO TÁC SỬA
  TRÊN VIEWER SỐNG — không phải thuộc tính tĩnh của file. Fixture #01/#03/#04
  ở trên cung cấp NGUYÊN LIỆU (file sạch để mở-sửa-lưu), nhưng bản thân
  "thêm comment rồi mở lại bằng viewer thứ hai" phải chạy trong CI/pilot có
  Okular/viewer thật — xem `roundtrip/README.md`.
- **PDF-07** (XFA động) — không sinh fixture XFA riêng: XFA là tính năng
  Adobe LiveCycle legacy, hiếm gặp ngoài form chính phủ cũ; mục tiêu kiểm
  thử là "phát hiện và cảnh báo", việc này cần một file XFA THẬT lấy có
  phép từ nguồn hợp pháp (không tự tạo giả XFA phức tạp rủi ro sai cấu trúc
  chuẩn) — ghi nhận là khoảng trống corpus, không bịa fixture.
- **PDF-09 kit** (redact tên/CCCD/ảnh/OCR có incremental revisions) — không
  sinh ở đây: redaction là tính năng GHI (xoá vĩnh viễn + chứng minh không
  khôi phục được qua content/object/metadata/history), cần bộ fixture +
  kiểm thử độc lập riêng (not thuộc phạm vi vertical-slice fixture tĩnh này).
- **PDF-11 kit** (in USB/LAN, A4/A3, duplex, lỗi máy offline/khổ sai) — là
  kịch bản MÁY IN THẬT; fixture #01 dùng làm nguồn in thử trong
  `roundtrip/run_roundtrip.sh` bước `lp`/`lpr`, nhưng các biến thể
  khổ giấy/duplex/lỗi máy cần phòng lab in thật (CI/pilot).

## Giới hạn trung thực (không giả vờ đạt)

- **#06 (encrypted)**: dùng R=6 (AES-256, tương đương PDF 2.0/ISO 32000-2
  hoặc Extension Level 8 của PDF 1.7) qua `pikepdf.Encryption`. Đã xác nhận
  pikepdf tự mở lại đúng với mật khẩu đúng/sai (xem `check_fixtures.py`),
  nhưng CHƯA xác nhận Adobe Acrobat/Okular cũ hơn có hỗ trợ R=6 hay không
  — đó là bước pilot.
- **#07 (signature stub)**: `/Contents` là chuỗi hex RỖNG, `/ByteRange` là
  placeholder `[0 0 0 0]` không khớp offset thật. Đây **không phải PAdES
  hợp lệ** — bất kỳ validator chữ ký thật nào (kể cả Acrobat) sẽ báo "chữ ký
  không hợp lệ/hỏng", đúng như kỳ vọng. Mục đích DUY NHẤT là kiểm tra parser
  nhận diện được cấu trúc `/Sig` tồn tại, không phải xác thực mật mã học.
- **#09 (JS/OpenAction)**: payload chỉ gọi `app.alert` tĩnh. Đây là một mẫu
  AN TOÀN để test "có chặn auto-run JS không" — KHÔNG đại diện cho toàn bộ
  không gian tấn công JS/PDF thật (không có obfuscation, không có
  decompression bomb, không có exploit CVE cụ thể). Kiểm thử bảo mật sâu
  hơn (fuzzing, CVE corpus) là một hạng mục riêng, không nằm trong vertical
  slice này.
- **#10 (PDF/A-ish)**: ICC profile là bản sRGB tối giản lấy từ LittleCMS
  (qua `PIL.ImageCms.createProfile("sRGB")`), KHÔNG phải ICC profile đầy đủ
  dùng cho in màu chuyên nghiệp. XMP chỉ khai `pdfaid:part/conformance`,
  CHƯA chạy qua veraPDF — fixture này PHẢI được coi là "PDF/A-ish" (giống
  cấu trúc), không phải "PDF/A đã validate".
- **#13 (corrupt)**: cắt cụt đơn giản (mất xref/trailer ở cuối file) — một
  DẠNG hỏng trong nhiều dạng có thể gặp (bit-flip giữa file, header hỏng,
  object stream hỏng, vòng lặp tham chiếu...). Không đại diện cho toàn bộ
  không gian lỗi cần fuzz-test.

Mọi nội dung (tên người, địa danh, câu văn) trong 13 fixture đều **tự sinh**,
không lấy từ hồ sơ thật.
