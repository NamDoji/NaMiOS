# NaMiOffice v2 — Vertical Slice Round-trip (tools/office-compat)

Thực hiện bước 3 trong `docs/specs/namioffice-v2/05_PROMPT_CLAUDE_CODE.md`:
> "Ưu tiên vertical slice có build thật: một DOCX dài có bảng/track changes;
> một XLSX có SUMIFS, XLOOKUP, dynamic array, table, chart, Pivot; một PPTX
> có master/chart/notes. Mở → sửa nhỏ → lưu bản sao → mở lại trong
> NaMiOffice và Microsoft Office có giấy phép → report sai khác."

Thư mục này KHÔNG phải sản phẩm NaMiOffice — nó là **bộ fixture + harness
kiểm thử** dùng để đo pipeline "mở an toàn → nhận diện tính năng rủi ro →
chỉnh sửa → lưu bản sao → so sánh" trước khi mở rộng số hàm/biểu đồ/ứng
dụng (theo đúng cảnh báo ở cuối file 05: "Đây là điểm kiểm tra quan trọng để
tránh có nhiều màn hình đẹp nhưng tài liệu thật không dùng được").

## Cấu trúc

```
tools/office-compat/
├── fixtures/
│   ├── make_doc.py      # sinh LongDoc.docx
│   ├── make_sheet.py    # sinh WorkBook.xlsx
│   ├── make_deck.py     # sinh Deck.pptx
│   ├── LongDoc.docx      (đã chạy sẵn — xem nội dung ở dưới)
│   ├── WorkBook.xlsx     (đã chạy sẵn)
│   ├── Deck.pptx         (đã chạy sẵn)
│   └── _assets/logo.png  (ảnh PNG nhỏ tự sinh, dùng chung cho docx+pptx)
├── roundtrip/
│   ├── run_roundtrip.sh  # harness: convert-to pdf + resave + diff (cần soffice)
│   └── compare.py        # comparator: selfcheck (chạy local) + roundtrip (cần CI)
└── README.md             # file này
```

Chạy lại fixture (idempotent, không cần mạng):
```bash
python3 tools/office-compat/fixtures/make_doc.py
python3 tools/office-compat/fixtures/make_sheet.py
python3 tools/office-compat/fixtures/make_deck.py
```

Chạy self-check (chạy được ở MỌI máy có python-docx/openpyxl/python-pptx,
KHÔNG cần soffice):
```bash
python3 tools/office-compat/roundtrip/compare.py selfcheck
```

Chạy harness đầy đủ (tự phát hiện có soffice hay không):
```bash
tools/office-compat/roundtrip/run_roundtrip.sh [out_dir]
```

## Nội dung từng fixture

### LongDoc.docx (NaMiWriter)
Nhiều trang (page break chủ động + nội dung lấp đầy), 7 heading cấp 1/2
(TOC-able), một bảng 4×3 có dòng tiêu đề lặp (`w:tblHeader`) và một ô gộp
ngang ở dòng cuối, một ảnh PNG chèn trong dòng (inline) có alt text
(`docPr/@descr`), một hyperlink ra ngoài (ghi `w:hyperlink` + quan hệ thật,
không phải text giả), một comment thật gắn vào một cụm từ cụ thể
(`Document.add_comment`), footer có field số trang `PAGE / NUMPAGES`.

### WorkBook.xlsx (NaMiSheet)
Sheet `DuLieu` (20 dòng hoá đơn giả lập, Table object `BangHoaDon` với
structured reference, cột `ĐơnGiá`/`ThànhTiền` định dạng tiền VND
`#,##0" ₫"`, cột `NgàyHĐ` định dạng `dd/mm/yyyy`); sheet `BangGia` (bảng tra
cứu cho INDEX/MATCH, XLOOKUP); sheet `TongHop` (SUMIF qua named range +
BarChart "Tổng Thành tiền theo Khu vực"); sheet `CongThuc` (trình diễn
SUMIFS/COUNTIFS/AVERAGEIFS/IF/IFERROR/INDEX-MATCH/XLOOKUP/structured-ref +
3 công thức mảng động FILTER/SORT/UNIQUE); sheet `KỳVọng` (giá trị kỳ vọng
TÍNH ĐỘC LẬP bằng Python cho mọi công thức KHÔNG phải mảng động); sheet
`PivotTable_GhiChu` (xem mục giới hạn Pivot ở dưới). 4 named range
(`ThanhTien_Rng`, `KhuVuc_Rng`, `SoLuong_Rng`, `BangGia_Rng`).

### Deck.pptx (NaMiSlides)
4 slide, tỉ lệ 16:9: (1) Title Slide; (2) Title and Content — chart cột gốc
(native, có `GraphicFrame`/`chart1.xml` + embedded workbook dữ liệu, KHÔNG
phải ảnh chụp); (3) Title Only — bảng 4×3 gốc; (4) **Picture with Caption**
— layout KHÔNG mặc định, có ảnh chèn vào placeholder kiểu PICTURE. Mỗi slide
có speaker notes riêng.

## Hai chế độ của compare.py

1. **`selfcheck`** — chạy ở ĐÂY, máy không có soffice. Mở lại 3 fixture
   bằng python-docx/openpyxl/python-pptx, đếm đối tượng, và — quan trọng
   nhất — **TÍNH LẠI một lần nữa, độc lập, bằng Python** các giá trị
   SUMIFS/COUNTIFS/AVERAGEIFS/IF/IFERROR/INDEX-MATCH/XLOOKUP/SUM từ dữ liệu
   thô đọc trực tiếp trong `WorkBook.xlsx` đã lưu trên đĩa (không import
   hằng số từ `make_sheet.py`), rồi so với sheet `KỳVọng`. Đã chạy; **kết
   quả: PASS** (8/8 công thức khớp 2 lần tính độc lập; xem log chạy ở cuối
   file này).

2. **`roundtrip`** — chạy khi có file đã được LibreOffice/Microsoft Office
   mở-lưu lại (sản phẩm của `run_roundtrip.sh` trong CI/QEMU). Diff số đối
   tượng (bảng/ảnh/comment/hyperlink cho docx; table/named-range/formula
   cho xlsx; slide/chart/table/notes cho pptx) và — với xlsx — so **cached
   value do engine thật tính ra** (sau khi soffice/Excel mở file) với cột
   `KỳVọng`. Đã smoke-test bằng cách coi một BẢN SAO NGUYÊN VẸN (không qua
   soffice) là "bản resave" — kết quả đúng như dự đoán: docx/pptx PASS (vì
   không đổi gì), còn xlsx báo "lệch" vì cached value vẫn là `None` (bản
   sao nguyên vẹn chưa từng được một engine công thức nào tính) — điều này
   XÁC NHẬN logic diff phân biệt được "đã tính" và "chưa tính", nhưng
   **KHÔNG phải là một round-trip thật** (không có soffice ở máy này).

## Chạy local — không có soffice ở máy này

Môi trường build hiện tại (xem `CLAUDE.md` mục môi trường) **không có**
`soffice`/LibreOffice. `run_roundtrip.sh` tự phát hiện điều này: in
```
soffice not present — round-trip step runs in CI only
```
rồi **bỏ qua bước convert-to-pdf + resave + diff**, nhưng **vẫn chạy xong**
bước self-check tĩnh (không cần soffice) ở trên. Round-trip thật (mở bằng
LibreOffice Calc/Writer/Impress, sửa nhỏ, lưu, mở lại, so sánh) chỉ chạy
được trong CI/QEMU có soffice đã cài — đúng kiến trúc kiểm thử ở
`docs/specs/namioffice-v2/04_KIEN_TRUC_KIEM_THU.md`.

## Round-trip với Microsoft Office có giấy phép — PILOT, CHƯA CHẠY

Theo đúng yêu cầu ở bước 3 (05_PROMPT...), bước đối chiếu đầy đủ là "mở lại
trong NaMiOffice **và** Microsoft Office có giấy phép → report sai khác".
Máy hiện tại (và CI hiện tại) **không có Microsoft Office được cấp phép**,
nên vế này **chưa thực hiện được** — đây là một bước pilot cần máy
Windows/Microsoft 365 có giấy phép, nằm ngoài phạm vi môi trường build này.
Không được coi "round-trip qua soffice" là tương đương "round-trip qua
Microsoft Office": đây là hai phép đo khác nhau, theo đúng nguyên tắc ở
`01_PHAM_VI_VA_MA_TRAN.md` ("Một tính năng chỉ được đánh dấu 'Đã hỗ trợ'
khi có... round-trip và thử tương tác... Phân loại theo từng bản
Office/định dạng").

## Giới hạn trung thực (KHÔNG giả vờ đạt)

- **Track changes (DOCX)**: python-docx 1.2.0 **không có API ghi**
  `w:ins`/`w:del` (chèn/xoá có tác giả+thời gian). `LongDoc.docx` **không
  chứa track changes thật**. Đã kiểm tra trực tiếp API của `Document`
  (`add_comment`, `add_heading`, `add_table`, …) — không có phương thức nào
  liên quan "track"/revision. Hướng khắc phục khả thi: (a) ghi `w:ins/w:del`
  bằng cách lắp XML tay (rủi ro cao, không có soffice ở đây để xác nhận
  ngay), hoặc (b) chấp nhận track-changes CHỈ kiểm thử bằng file mẫu lấy từ
  Microsoft Word thật (round-trip giữ nguyên, không tự TẠO mới bằng
  python-docx) — đúng tinh thần "Patch phải đi kèm fixture từ Microsoft
  Office có giấy phép hoặc tệp người dùng có quyền" ở 04_KIEN_TRUC....

- **Comment (DOCX) — ĐÃ SỬA một giả định sai trong mô tả nhiệm vụ gốc**:
  mô tả ban đầu cho rằng "python-docx comments are limited". Đã kiểm tra
  trực tiếp: python-docx **1.2.0 CÓ** `Document.add_comment(runs, text,
  author, initials)` gắn comment thật vào một vùng run cụ thể, sinh đúng
  `word/comments.xml` + quan hệ phần. `LongDoc.docx` dùng API THẬT này
  (không phải đoạn văn giả danh "bình luận").

- **Footnote (DOCX)**: python-docx 1.2.0 không có API mức cao để tạo
  footnote OOXML thật (`w:footnoteReference` + `footnotes.xml`). Để trung
  thực, `LongDoc.docx` chỉ có một "chú thích" thủ công bằng số mũ + đoạn
  văn ở cuối — đoạn văn nói rõ **đây không phải footnote thật**. Không nên
  coi đây là đã hỗ trợ "foot/endnote" (mục F1 ở 02_WRITER....).

- **PivotTable (XLSX)**: openpyxl có các class mức thấp để ĐỌC/giữ nguyên
  pivot đã có sẵn trong file nguồn (`openpyxl.pivot.table.TableDefinition`,
  `openpyxl.pivot.cache.*`), nhưng **không có API mức cao để tạo MỚI** một
  PivotTable kèm đủ `pivotCacheDefinition` + `pivotCacheRecords` + quan hệ
  phần (`.rels`) + mục `[Content_Types].xml` một cách an toàn. Tự ghép các
  phần XML đó bằng tay có rủi ro cao tạo ra file hỏng, và **không có
  soffice/Excel ở máy này để xác nhận ngay** file có mở được hay không.
  → `WorkBook.xlsx` **không chứa PivotTable object thật**; sheet
  `PivotTable_GhiChu` nêu rõ giới hạn này và cung cấp một bảng tổng hợp
  tương đương bằng SUMIFS (KHÔNG phải Pivot — không có pivot cache, không
  refresh được, chỉ là bảng công thức tĩnh).

- **Dynamic array (FILTER/SORT/UNIQUE, XLOOKUP) (XLSX)**: openpyxl **chỉ
  ghi công thức dưới dạng chuỗi văn bản**, không có engine tính toán. Các
  hàm "future function" được ghi với tiền tố theo quy ước lưu trữ OOXML của
  Microsoft: `_xlfn.XLOOKUP(...)` (hàm đơn — chỉ cần `_xlfn.`), và
  `_xlfn._xlws.FILTER(...)` / `_xlfn._xlws.SORT(...)` / `_xlfn._xlws.UNIQUE(...)`
  (các hàm mảng động — cần thêm `_xlws.`). **Tiền tố đúng hay không, và
  công thức có SPILL đúng hay không, CHỈ xác nhận được khi mở bằng
  LibreOffice Calc (đủ mới) hoặc Excel thật** — việc đó thuộc bước CI/QEMU
  (`run_roundtrip.sh` khi có soffice), KHÔNG thực hiện được ở máy local
  này. `compare.py roundtrip` đã có logic đọc cached-value của các ô mảng
  động sau round-trip và báo "có tính ra gì đó hay không" (không có giá trị
  Python đối chiếu cho mảng động, vì bản chất shape của spill range phụ
  thuộc engine).

- **Cached value nói chung (XLSX)**: mọi ô công thức trong `WorkBook.xlsx`
  (sinh bởi openpyxl) **không có giá trị cache** — mở trực tiếp bằng
  openpyxl `data_only=True` sẽ trả `None` cho tới khi một engine công thức
  thật (LibreOffice Calc/Excel) mở và tính lại. `wb.calculation.fullCalcOnLoad
  = True` đã được set để buộc engine tính lại toàn bộ khi mở, nhưng đây chỉ
  là một "gợi ý" trong file XML — bản thân openpyxl không thực thi nó.

- **Mọi so sánh ở local chỉ là "selfcheck"**: không có soffice/LibreOffice
  (và không có Microsoft Office có giấy phép) ở máy build hiện tại (xem
  `CLAUDE.md`), nên **KHÔNG CÓ phép đo round-trip thật nào đã chạy trong
  task này** — chỉ có (a) kiểm tra cấu trúc fixture tự mở lại được bằng
  thư viện Python, và (b) đối chiếu 2 lần tính Python độc lập cho các công
  thức tĩnh. Hai điều đó CHƯA chứng minh LibreOffice/Microsoft Office mở
  file này ra đúng — đó là lý do `run_roundtrip.sh` tồn tại như một bước
  riêng, có guard rõ ràng, để chạy trong CI/QEMU.

## Log chạy thật (tự sinh, không chỉnh tay)

```
$ python3 tools/office-compat/fixtures/make_doc.py
wrote .../fixtures/LongDoc.docx (40 KB)
paragraphs=35 tables=1 inline_shapes=1

$ python3 tools/office-compat/fixtures/make_sheet.py
wrote .../fixtures/WorkBook.xlsx (14 KB)
rows=20 expected SUMIFS=39500000 COUNTIFS=2 AVERAGEIFS=6210000.00
INDEX/MATCH(SP03)=3200000 XLOOKUP(SP05)=5400000 SUM(table)=118130000

$ python3 tools/office-compat/fixtures/make_deck.py
wrote .../fixtures/Deck.pptx (46 KB)
slides=4

$ python3 tools/office-compat/roundtrip/compare.py selfcheck
... (xem toàn bộ ở phần "Hai chế độ của compare.py")
KẾT QUẢ: PASS

$ tools/office-compat/roundtrip/run_roundtrip.sh
soffice not present — round-trip step runs in CI only
(exit code 0 — self-check tĩnh đã PASS trước khi tới bước này)
```
