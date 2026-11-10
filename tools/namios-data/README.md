# NaMi Data Pipeline — prototype (tools/namios-data)

Prototype M4: "Get & Transform tương đương" cho NaMiSheet, theo
`docs/specs/namioffice-v2/02_WRITER_SHEET_SLIDES.md` §B ("F2 nhập và mô hình
dữ liệu") và `docs/office/COMPAT-MATRIX.md` dòng `SH-F2-01`/`SH-F2-02`/`SH-F2-03`.

Đọc `docs/office/NAMI-DATA-PIPELINE.md` trước — đó là tài liệu trung thực đầy
đủ (phạm vi, KHÔNG phải gì, cổng consent). File README này chỉ tóm cấu trúc
code để chạy nhanh.

## Cấu trúc

```
tools/namios-data/
├── table.py        # Table bất biến (columns/dtypes/rows) + hash nội dung
├── typeinfer.py     # suy luận dtype (có thể override) + ép kiểu
├── consent.py        # cổng đồng ý nguồn mạng (SH-F2-03)
├── sources.py         # đọc CSV/JSON cục bộ; chặn sql/web nếu thiếu consent
├── steps.py            # 7 bước: filter/select/rename/merge/append/unpivot/group_by
├── pipeline.py          # lắp nguồn + steps, run()/refresh(), to_json/from_json
├── xlsx_writer.py        # ghi Table ra .xlsx (openpyxl)
├── demo.py                # chạy tay end-to-end, ghi ra sample_data/ + out/
└── tests/                  # pytest — xem docs/office/NAMI-DATA-PIPELINE.md §Test
```

## Chạy

```bash
# demo end-to-end (sinh dữ liệu mẫu, ghi .xlsx vào out/)
python3 tools/namios-data/demo.py

# test
python3 -m pytest tools/namios-data/tests -q
```

Không cần cài gì thêm ngoài `openpyxl` (đã có trong `.venv`/requirements dev).
Không có bước nào gọi mạng theo mặc định (xem `consent.py`).
