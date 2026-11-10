# NaMiPDF — Vertical Slice Round-trip (tools/pdf-compat)

Thực hiện bước "Vertical slice" trong
`docs/specs/namipdf-v18/05_PROMPT_CLAUDE_CODE.md`:
> "tạo bản app chạy thật: mở PDF đa trang trong worker sandbox, tìm/copy
> tiếng Việt, thêm chú thích, sắp xếp trang, lưu bản sao atomically, mở lại
> trong NaMiPDF và viewer độc lập, in một trang qua CUPS. Có cảnh báo khi
> tài liệu ký số/đã khóa và không ghi đè bản gốc."

Thư mục `tools/pdf-compat/` KHÔNG phải sản phẩm NaMiPDF — nó là **bộ fixture
+ harness kiểm thử** mirror đúng cấu trúc `tools/office-compat/` (xem
`tools/office-compat/README.md`), dùng để đo pipeline "mở an toàn → nhận
diện tính năng rủi ro → chỉnh sửa → lưu bản sao → mở lại" cho PDF trước khi
mở rộng sang M2 (true edit/OCR/form/conversion).

## Cấu trúc

```
tools/pdf-compat/
├── fixtures/
│   ├── make_fixtures.py   # sinh 13 fixture PDF-01..PDF-13
│   ├── 01_text_vn.pdf .. 13_corrupt_truncated.pdf   (đã chạy sẵn)
│   ├── _assets/            (ảnh/ICC trung gian dùng chung)
│   └── README.md            # mô tả + ánh xạ từng fixture -> công việc kiểm thử trong kit
├── roundtrip/
│   ├── check_fixtures.py   # self-check CHẠY ĐƯỢC Ở ĐÂY (pikepdf + pypdf)
│   ├── run_roundtrip.sh    # harness đầy đủ: tự phát hiện pdfinfo/pdftotext/qpdf/ocrmypdf/lp
│   └── README.md             # file này
└── (namipdf_inspect/, tests/ — thuộc phạm vi một agent khác, không đụng ở đây)
```

## Chạy lại fixture (idempotent, không cần mạng)

```bash
python3 tools/pdf-compat/fixtures/make_fixtures.py
```

## Chạy self-check (chạy được ở MỌI máy có pikepdf + pypdf, KHÔNG cần
Okular/poppler/qpdf/ocrmypdf/CUPS)

```bash
python3 tools/pdf-compat/roundtrip/check_fixtures.py
```

## Chạy harness đầy đủ (tự phát hiện công cụ CLI có sẵn hay không)

```bash
tools/pdf-compat/roundtrip/run_roundtrip.sh [out_dir]
```

`run_roundtrip.sh` thực hiện 6 bước, mỗi bước guard bằng `command -v`:

| Bước | Công cụ | Việc làm | Có ở máy local này? |
|---|---|---|---|
| 0 | pikepdf/pypdf (Python) | self-check tĩnh (gọi `check_fixtures.py`) | CÓ — luôn chạy |
| 1 | `pdfinfo` (poppler-utils) | mở/validate PDF-04 (đa trang+bookmark) | KHÔNG — in "runs in CI only" |
| 2 | `pdftotext` (poppler-utils) | trích text + grep dấu tiếng Việt (PDF-01, PDF-12) | KHÔNG — in "runs in CI only" |
| 3 | `qpdf` | thêm/reorder trang, split, merge — ghi ATOMIC vào bản sao trong `out/`, **không bao giờ sửa `fixtures/`** | KHÔNG — in "runs in CI only" |
| 4 | `pdfinfo` hoặc pikepdf | reopen + re-validate bản đã reorder/merge | fallback pikepdf CÓ chạy nếu bước 3 tạo ra file |
| 5 | `ocrmypdf` (+ Tesseract `vie`) | OCR tiếng Việt trên PDF-02 (scan, không text layer) | KHÔNG — in "runs in CI only" |
| 6 | `lp`/`lpr` (CUPS) | in 1 trang (PDF-01) ra PDF virtual printer nếu có cấu hình | KHÔNG — in "runs in CI only" |

An toàn ghi file: bước 3 luôn ghi ra file tạm (`*.tmp.$$`) rồi `mv -f` sang
tên đích — tránh để lại file nửa vời nếu `qpdf` bị ngắt giữa chừng, và
**tuyệt đối không ghi đè file gốc trong `fixtures/`** (đúng yêu cầu "lưu bản
sao atomically... không ghi đè bản gốc" ở 05_PROMPT).

## Môi trường build hiện tại — KHÔNG có công cụ render/in

Theo đúng ghi chú môi trường: **không có** Okular/poppler/qpdf/ocrmypdf/CUPS
ở máy build hiện tại. Đã chạy `run_roundtrip.sh` thật — bước 0 (self-check)
PASS 42/42, các bước 1–6 đều in đúng dòng "not present — step runs in CI
only" và SCRIPT VẪN CHẠY TIẾP tới cuối (exit code 0), không dừng giữa chừng.
`bash -n tools/pdf-compat/roundtrip/run_roundtrip.sh` sạch (không lỗi cú
pháp).

Ghi chú nhỏ: khi `check_fixtures.py` thử mở fixture #13 (cố ý hỏng) ở chế
độ "recovery", thư viện `pikepdf`/QPDF bên dưới có thể in một dòng cảnh báo
trực tiếp ra stderr kiểu `EOF marker not found` — đây là log CHẨN ĐOÁN của
QPDF khi cố phục hồi file hỏng (đúng như kỳ vọng với một file bị cố ý
truncate), KHÔNG phải lỗi của harness; exit code vẫn 0 vì mọi assertion
PASS.

## Round-trip với Okular/Adobe Acrobat thật — PILOT, CHƯA CHẠY

Yêu cầu đầy đủ ở "Vertical slice" là mở file trong NaMiPDF **và** "viewer
độc lập" (vd Okular), cộng với bước nghiệm thu PDF-01..PDF-13 ở
`05_PROMPT_CLAUDE_CODE.md` ("Nghiệm thu: chạy PDF-01–PDF-13, báo pass/fail
theo từng fixture và nguy cơ"). Máy build hiện tại **không có** renderer GUI
nào, nên:

- Render/xem bằng mắt, thao tác chuột (click annotation, kéo thả trang)
- Xác nhận Okular/Adobe Acrobat mở đúng 13 fixture, không cảnh báo sai
- OCR tiếng Việt thật bằng Tesseract (đo CER/WER theo 04_KIEM_THU...)
- Validate PDF/A thật bằng veraPDF (fixture #10)
- Xác thực trạng thái chữ ký thật (5 trạng thái theo PDF-08 của kit — fixture
  #07 ở đây CHỈ LÀ STUB CẤU TRÚC, không đủ để test điều này)
- In thật qua CUPS tới máy in vật lý/ảo

… đều là bước **PILOT/CI**, chưa thực hiện được ở môi trường này. Không được
coi self-check tĩnh (pikepdf/pypdf) là tương đương "đã nghiệm thu PDF-01..13
qua Okular/Acrobat thật" — đây là hai phép đo khác nhau, đúng nguyên tắc đã
áp dụng ở `tools/office-compat/README.md` ("Không được coi round-trip qua
soffice là tương đương round-trip qua Microsoft Office").

## Giới hạn trung thực tổng hợp (KHÔNG giả vờ đạt)

- **PDF-07 (chữ ký số)**: fixture là **structural stub** — có `/Sig` dict
  trong AcroForm nhưng `/Contents` rỗng và `/ByteRange` là placeholder,
  KHÔNG phải chữ ký PAdES/PKCS7 hợp lệ về mặt mật mã học. Bất kỳ validator
  chữ ký thật nào mở fixture này sẽ (đúng ra) báo "không hợp lệ". Dùng để
  test "viewer có nhận diện được tài liệu có trường chữ ký" chứ không test
  5 trạng thái (hợp lệ/hết hạn/thu hồi/sửa-sau-ký/offline) mà kit yêu cầu ở
  PDF-08 — việc đó cần ký thật qua token/dịch vụ đã chứng nhận.
- **Annotation/edit round-trip (PDF-02, PDF-03 của kit)**: chất lượng
  "thêm/sửa/xoá comment, save/reopen 2 viewer" và "sửa text/vector, layout
  không vỡ" cần Okular/Poppler (hoặc engine render NaMiPDF thật) chạy trong
  CI/pilot — không đo được bằng pikepdf/pypdf tĩnh.
- **OCR (PDF-02 fixture, PDF-05 của kit)**: độ chính xác CER/WER tiếng Việt
  cần Tesseract (gói `tesseract-ocr-vie`) chạy trên build thật; máy hiện tại
  không có Tesseract nên bước 5 của `run_roundtrip.sh` chỉ in "runs in CI
  only". Fixture #02 chỉ xác nhận được (bằng self-check) rằng nó ĐÚNG LÀ một
  trang ảnh-không-text, tức là input hợp lệ cho bài kiểm OCR — chưa đo được
  accuracy.
- **PDF/A (fixture #10)**: có OutputIntent + XMP conformance tag nhưng CHƯA
  qua veraPDF — gọi là "PDF/A-ish", không phải "đã validate PDF/A".
- **In ấn (bước 6)**: không có CUPS/PDF virtual printer ở máy này; "bản giấy
  đúng" theo PDF-11 của kit chỉ xác nhận được khi có máy in thật/ảo trong
  CI/pilot.

## Log chạy thật (tự sinh khi thực hiện task, không chỉnh tay)

```
$ python3 tools/pdf-compat/fixtures/make_fixtures.py
Đã sinh 13 fixture PDF-01..PDF-13 tại .../tools/pdf-compat/fixtures
  PDF-01: 01_text_vn.pdf (47,175 bytes)
  PDF-02: 02_scanned_image_only.pdf (50,310 bytes)
  PDF-03: 03_mixed_text_image.pdf (63,423 bytes)
  PDF-04: 04_multipage_bookmarks.pdf (63,629 bytes)
  PDF-05: 05_acroform.pdf (50,734 bytes)
  PDF-06: 06_encrypted.pdf (46,794 bytes)
  PDF-07: 07_signature_stub.pdf (46,277 bytes)
  PDF-08: 08_attachment.pdf (45,732 bytes)
  PDF-09: 09_js_openaction.pdf (46,356 bytes)
  PDF-10: 10_pdfa_ish.pdf (46,134 bytes)
  PDF-11: 11_uri_link.pdf (45,640 bytes)
  PDF-12: 12_vn_heavy_diacritics.pdf (47,388 bytes)
  PDF-13: 13_corrupt_truncated.pdf (24,938 bytes)

$ python3 tools/pdf-compat/roundtrip/check_fixtures.py
== NaMiPDF vertical-slice — self-check 13 fixture (pikepdf + pypdf) ==
... (42 assertion, xem chi tiết khi chạy trực tiếp)
TỔNG KẾT: 42/42 assertion PASS, 0 FAIL

$ bash -n tools/pdf-compat/roundtrip/run_roundtrip.sh
(không có output — cú pháp sạch)

$ tools/pdf-compat/roundtrip/run_roundtrip.sh
== NaMiPDF vertical-slice round-trip harness ==
--- [0/6] self-check tĩnh ... --- self-check: PASS
--- [1/6] pdfinfo not present — step runs in CI only
--- [2/6] pdftotext not present — step runs in CI only
--- [3/6] qpdf not present — step runs in CI only
--- [4/6] KHÔNG có bản merge để reopen (bước 3 đã bị bỏ qua vì thiếu qpdf)
--- [5/6] ocrmypdf not present — step runs in CI only
--- [6/6] lp/lpr not present — step runs in CI only
(exit code 0)
```
