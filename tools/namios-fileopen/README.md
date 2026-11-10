# PL20 — MIME routing + archive safety (vertical slice)

Thực hiện phần "dev-verifiable" của PL20: "double-click một tệp → đúng
app, tệp giả mạo bị chặn, bản gốc không bao giờ mất". Đọc trước:

- `docs/specs/namios-pl20/02_MO_TEP_VA_DINH_DANG.md` — luật chung + bảng
  định dạng/app + NaMiFiles/NaMiArchive.
- `docs/specs/namios-pl20/04_KIEN_TRUC_QA.md` — file routing contract,
  bảo mật định dạng, bảng ca F20-01..F20-12 (§4).

## Đây KHÔNG phải gì

Đây **không phải** NaMiFiles/Dolphin thật, không nối vào double-click thật
trên desktop, không mở NaMiOffice/NaMiPDF/NaMiArchive/NaMiImages/NaMiMedia
thật, không giải nén thật, không phát âm thanh/video thật, không phải
virus scanner. Đây là **logic routing + logic an toàn archive** — thuần
Python/stdlib (`zipfile`, `tarfile`), chạy được bằng `pytest`, không cần
máy desktop/QEMU.

## Cấu trúc

```
tools/namios-fileopen/
├── namios_fileopen/
│   ├── __init__.py
│   ├── mime_router.py      # sniff nội dung (magic bytes + ZIP nông) + chọn app + đổi mặc định
│   └── archive_safety.py   # quét ZIP/TAR an toàn: zip-bomb + path traversal/symlink escape
├── namios-fileopen-cli      # CLI: route + (nếu là archive) quét an toàn
├── tests/
│   ├── conftest.py
│   └── test_f20.py          # F20-01..F20-12
└── README.md                 # file này
```

Chạy test:
```bash
python3 -m pytest tools/namios-fileopen/tests/test_f20.py -v
```
Kết quả lần chạy gần nhất (tự sinh, không chỉnh tay): **12 passed** (tất cả
F20-01..F20-12).

Chạy CLI:
```bash
tools/namios-fileopen/namios-fileopen-cli hoa_don.pdf anh.png
tools/namios-fileopen/namios-fileopen-cli --json tep_nen.zip > report.json
```
Mã thoát: `0` nếu không tệp nào bị chặn/archive nào không an toàn, `1` nếu
có ít nhất một.

## `mime_router.py` — tóm tắt thiết kế

1. Đọc 4096 byte đầu tệp, so khớp **magic bytes** (PE `MZ`, ELF `\x7fELF`,
   shebang `#!`, `%PDF-`, PNG/JPEG/GIF/BMP/WEBP/TIFF/WAV/FLAC/OGG/AVI, MP4/
   MOV qua box `ftyp`, Matroska/WebM qua EBML, OLE/CFB cũ, 7z/RAR/gzip/
   bzip2/xz, MP3 qua `ID3` hoặc frame-sync).
2. Nếu là container ZIP: soi NÔNG bằng `zipfile.namelist()` để phân biệt
   OOXML (docx/xlsx/pptx qua `word/`/`xl/`/`ppt/`), ODF (`mimetype` entry),
   JAR, hay ZIP thường — KHÔNG đọc hết nội dung từng part.
3. Nếu là TAR (thường/.gz/.bz2/.xz): `tarfile.is_tarfile()`.
4. So NỘI DUNG đã dò với ĐUÔI khai báo → cờ `extension_content_mismatch`
   khi lệch; dò **đuôi kép** (`.pdf.exe`...) bằng đúng hai tập
   `EXECUTABLE_EXTENSIONS`/`DISGUISE_EXTENSIONS` lấy nguyên từ
   `tools/pl09-tests/t09_min_helpers.py` (T09-C, không fork lại giá trị).
5. Nội dung là PE/ELF/script-shebang thật (bất kể đuôi) → **luôn chặn**
   (`blocked=True`, `app=None`) — không có đường nào mở/route một tệp thực
   thi, kể cả qua "đổi app mặc định".
6. Nếu không bị chặn: tra `CONTENT_KIND_TO_APP` để chọn app NaMiOS +
   `can_view`/`can_edit` theo đúng bảng ở `02_MO_TEP_VA_DINH_DANG.md` §1.
   Khi nội dung thật sự không có tín hiệu nào (`unknown_binary`/zip hỏng),
   **không đoán theo đuôi** — trả `app=None` + ghi chú "Không nhận diện
   được định dạng" (đúng câu chữ §1), tránh âm thầm mở sai.
7. `FileAssociationRegistry` mô hình "Luôn dùng ứng dụng này cho loại
   tệp": chặn đặt một app không tự khai hỗ trợ content_kind làm mặc định
   (tránh "một app chiếm mặc định hàng trăm MIME không xử lý tốt"), và
   **không bao giờ** áp override cho report đã `blocked=True`.

## `archive_safety.py` — tóm tắt thiết kế

- **ZIP**: chỉ đọc **central directory** (`infolist()` — O(số entry), không
  giải nén nội dung), cộng dồn `file_size`/`compress_size`, chặn khi vượt
  `max_entry_count` (10 000) / một entry > `max_single_entry_bytes`
  (100 MiB) / tổng giải nén > `max_total_uncompressed_bytes` (200 MiB) /
  tỉ lệ nén > `max_ratio` (100:1). Với symlink Unix trong ZIP (mode bit ở
  `external_attr`), chỉ đọc target nếu khai báo ≤ 4096 byte.
- **TAR** (thường/.gz/.bz2/.xz): duyệt **tuần tự từng member** (`for m in
  tar:` — tarfile đọc lười, không có central directory như ZIP), **dừng
  sớm ngay khi vượt ngưỡng** để không tốn CPU/RAM giải mã hết một bomb dài.
- **Path traversal + symlink escape**: `is_unsafe_archive_member_path()`
  chặn `../`, absolute POSIX (`/etc/...`), absolute Windows (`C:\...`), và
  chuẩn hoá bằng `posixpath.normpath` để bắt cả trường hợp "thoát" không
  có `..` lộ liễu. Áp dụng cho CẢ tên entry VÀ target của symlink/hardlink.
- Không bao giờ gọi `extractall()`/`extract()` — chỉ đọc metadata (+ vài
  byte target symlink nhỏ). "Nested archive" (entry `.zip`/`.tar` bên
  trong) chỉ được **gắn cờ theo tên đuôi**, không mở xuống (mở xuống đúng
  là một cách khác để tự biến thành nạn nhân bomb lồng).
- Ngưỡng mặc định là **số SIM hợp lý cho vertical slice**, không phải số
  đã chốt sản phẩm (pin số thật cần theo dung lượng đĩa máy baseline +
  corpus thật — xem `04_KIEN_TRUC_QA.md` §4: "không đưa số giả trong
  marketing").

## Bảng đối chiếu F20-01..F20-12

Bảng gốc (`04_KIEN_TRUC_QA.md` §4) mô tả gate ở **mức desktop đầy đủ**
(Dolphin, codec thật, bàn phím Telex, mạng, onboarding người dùng...).
Toolkit này chỉ là **logic backend** — ba hàng gốc hoàn toàn không áp dụng
được ở mức backend (F20-07 CAD/SVG font-xref, F20-08 gõ Telex/VNI, F20-09
mạng tắt/web ghim); ba **SLOT SỐ** đó được DÙNG LẠI cho ba việc khác nằm
trong phạm vi toolkit mà nhiệm vụ yêu cầu rõ — ghi rõ trong bảng để không
ai nhầm "test F20-07 pass" = "đã kiểm CAD/font".

| ID | Hàng gốc (04_KIEN_TRUC_QA.md) | Trạng thái ở TOOLKIT NÀY |
|---|---|---|
| F20-01 | DOCX/XLSX/PPTX/ODF → đúng app, round-trip | **SIM (routing)** — `test_f20_01`. Phần round-trip/feature-risk đã có ở `tools/office-compat/namioffice_inspect` (không lặp lại). |
| F20-02 | PDF chữ ký/scan/form → NaMiPDF đúng trạng thái | **SIM (routing + file-not-lost)** — `test_f20_02`. Trạng thái Signed/Scan/Protected đã có ở `tools/pdf-compat/namipdf_inspect`. |
| F20-03 | ZIP/7z/tar, RAR, password/multi-volume — không escape/bomb | **SIM (routing + bomb)** — `test_f20_03`. RAR tạo/password/multi-volume thật là **PILOT** (cần engine RAR/7z thật, ngoài phạm vi stdlib). |
| F20-04 | Tên tiếng Việt, đuôi giả, path dài, USB mất kết nối | **SIM (đuôi giả + tên Unicode)** — `test_f20_04`. Path dài thật trên SMB/USB và "USB mất kết nối giữa chừng" là **PILOT** (cần phần cứng/FS thật). |
| F20-05 | JPEG/PNG/WebP/GIF/TIFF + EXIF/ICC | **SIM (routing 6 định dạng)** — `test_f20_05`. EXIF orientation/ICC/animation là tính năng NaMiImages sâu hơn — **PILOT/future work**. |
| F20-06 | MP3/FLAC/WAV/AAC, MP4/MKV/WebM, codec khác nhau | **SIM một phần** — `test_f20_06`: WAV là tệp thật hợp lệ (module `wave`); MP3/MP4 chỉ đúng **magic bytes**, không phải tệp giải mã/phát được. Codec thật/playback/DRM là **PILOT** (cần NaMiMedia + audit giấy phép thật). |
| F20-07 | SVG/ODG/DXF/DWG có font/xref | **KHÔNG ÁP DỤNG ở backend này — 100% PILOT.** Slot dùng lại: `test_f20_07` kiểm tệp hỏng/rỗng/cắt cụt được xử lý an toàn (không crash, không coi là hợp lệ) — một bất biến khác nằm trong phạm vi toolkit. |
| F20-08 | Gõ Telex/VNI vào Office/PDF/CAD/browser | **KHÔNG ÁP DỤNG ở backend này — 100% PILOT** (cần bàn phím/ô nhập liệu thật). Slot dùng lại: `test_f20_08` kiểm crop/convert ảnh qua PIL round-trip (lưu bản sao, giữ bản gốc) — yêu cầu cụ thể trong nhiệm vụ PL20. |
| F20-09 | Mạng tắt, app web được ghim | **KHÔNG ÁP DỤNG — toolkit này không gọi mạng.** Slot dùng lại: `test_f20_09` quét lại bất biến "không sửa file gốc" trên MỌI loại fixture (docx/pdf/zip/png/wav) trong một test tổng hợp. |
| F20-10 | Update app, đổi app mặc định — MIME giữ nguyên | **SIM đầy đủ** — `test_f20_10`: `FileAssociationRegistry` resolve đúng, từ chối app không khai hỗ trợ, và KHÔNG áp override khi report đã bị chặn. Phần "update không reset ngầm" thật (sau khi cập nhật app qua NaMiUpdates) là **PILOT**. |
| F20-11 | Mã độc thử nghiệm, SVG external, archive traversal | **SIM (archive traversal + symlink escape)** — `test_f20_11`: zip-slip + absolute path + tar symlink escape đều bị chặn, không có bước nào thực sự giải nén. SVG external reference và mã độc polymorphic thật là **PILOT** (ngoài phạm vi 2 module này). |
| F20-12 | Người mới + xử lý lỗi phổ biến, hoàn thành bằng UI/keyboard | **PILOT phần lớn** (không có UI/bàn phím ở đây). Phần kiểm được: `test_f20_12` xác nhận format không nhận diện được luôn có fallback an toàn đúng câu chữ §1, và MỌI report bị chặn/archive không an toàn luôn có lý do cụ thể (không "lỗi câm") — proxy máy-đọc-được cho "lỗi có next action". |

## Giới hạn trung thực khác (không lặp lại ở trên)

- Sniff MIME ở đây là một bảng **tối thiểu** cho vertical slice, không
  phải một engine shared-mime-info đầy đủ (freedesktop thật có hàng nghìn
  rule XML theo thứ tự priority/glob).
- OLE/CFB cũ (`.doc`/`.xls`/`.ppt` nhị phân) dùng CHUNG một magic header —
  không tự phân biệt Writer/Sheet/Slides chỉ từ nội dung chưa mở; công cụ
  dùng đuôi tệp làm phụ trợ CHỈ trong trường hợp này, có ghi chú rõ trong
  `notes_vi` của report (không coi là "đã xác nhận bằng nội dung").
- MP3/MP4/MKV ở mức magic-byte không đảm bảo tệp *giải mã/phát* được —
  chỉ đảm bảo *container đúng loại*. Không suy ra "codec hoạt động" từ
  kết quả sniff này.
- Đây không phải virus scanner: không quét nội dung tìm mã độc polymorphic/
  heuristic, chỉ chặn theo magic PE/ELF/shebang + đuôi kép + cấu trúc
  archive (bomb/traversal/escape/số lượng).
- Không chạy trên QEMU/máy thật — mọi test chạy bằng `pytest` thuần trên
  môi trường build hiện tại, không cần Dolphin/NaMiFiles/NaMiMedia thật.

## Log chạy thật (tự sinh)

```
$ python3 -m pytest tools/namios-fileopen/tests/test_f20.py -v
...
12 passed in 2.19s

$ tools/namios-fileopen/namios-fileopen-cli sample.pdf
=== BÁO CÁO MIME ROUTER (NaMiOS, PL20) ===
...
KẾT QUẢ: mở bằng NaMiPDF (xem: True, sửa: False)

$ tools/namios-fileopen/namios-fileopen-cli --json safe.zip Hoa_don.pdf.exe
[... zip: app=namiarchive, archive_safety.safe=true ...
 ... Hoa_don.pdf.exe: blocked=true, app=null, double_extension_disguise=true ...]
exit code = 1   # vì Hoa_don.pdf.exe bị chặn
```
