# fixtures/workflows — 3 workflow mẫu cho Gói 1 (M0, P0)

Sinh bởi `scripts/make_workflow_fixtures.py` (chạy lại được, idempotent —
overwrite đúng các file trong thư mục này). Mục đích: chứng minh công cụ
đo workflow trọn vẹn (viết tài liệu → tính toán → đối chiếu) chạy được tại
môi trường build hiện tại (Debian 12, không Office/MISA/Wine/máy in thật —
xem `CLAUDE.md`), TRƯỚC khi có dữ liệu khảo sát/license thật từ chủ dự án.

## Tái tạo

```
/home/node/.openclaw/workspace/code_projects/namios/.venv/bin/pip install -q python-docx openpyxl
/home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python scripts/make_workflow_fixtures.py
```

Script tự verify ngay sau khi sinh (round-trip đọc lại bằng `python-docx` /
`openpyxl`, assert số liệu khớp) — thoát lỗi (`AssertionError`) nếu có sai
lệch, không im lặng bỏ qua.

## Nguồn gốc nội dung (rights-clean)

Toàn bộ văn bản, bảng biểu, số liệu, tên hàng hóa, tên tài khoản và chứng
từ trong ba workflow là **tự soạn** cho mục đích test kỹ thuật. KHÔNG copy
nội dung từ tài liệu có bản quyền (Microsoft, MISA, hay bất kỳ nguồn nào
khác). Không chứa secret, dữ liệu thật hoặc thông tin cá nhân.

## Nguyên tắc "expected tự tính"

Mọi giá trị `expected` (DOCX: số đoạn/heading/bảng; XLSX: kết quả công
thức; MISA mock: báo cáo tổng hợp/chi tiết) đều được **tính lại bằng
Python ngay trong `scripts/make_workflow_fixtures.py`** — không chép tay,
không dựa vào cache công thức Excel hay phần mềm MISA thật. Giám khảo có
thể đọc hàm tính tương ứng hoặc chạy lại script để kiểm tra độc lập.

## A_docx — viết DOCX tiếng Việt → gửi tệp → (mô phỏng) in

- `A_docx/baocao-tieng-viet.docx` — văn bản tiếng Việt có dấu (heading +
  đoạn văn + danh sách + 1 bảng 4x4).
  Tổng 8 paragraph cấp đỉnh, 1 heading,
  4 đoạn danh sách.
- `A_docx/expected.md` — mô tả round-trip kỳ vọng (số đoạn, text NFC giữ
  nguyên, kích thước bảng) + giới hạn (chưa test Word/LibreOffice/máy in
  thật).

## B_xlsx — mở XLSX → tính bằng công thức thật → lưu → đối chiếu giá trị

- `B_xlsx/bangtinh.xlsx` — 2 sheet (`BangGia` tra cứu, `BangTinh` 5 dòng dữ
  liệu) với công thức thật: phép nhân, `SUM`, `AVERAGE`, `IF`, `VLOOKUP`,
  `XLOOKUP`, cộng ngày (`NgayMua + 365`), và `ROUND(x,-3)` làm tròn tiền
  VNĐ đến nghìn đồng gần nhất (round-half-away-from-zero).
- `B_xlsx/bangtinh-vi-VN.csv` — case CSV-locale vi-VN (delimiter `;`, dấu
  chấm phân nghìn, dấu phẩy phân thập phân), khác locale en-US.
- `B_xlsx/expected.json` — giá trị kỳ vọng từng ô công thức (tính bằng
  Python/Decimal/`datetime`), kèm tolerance cho field float (`AVERAGE`) và
  quy tắc làm tròn Decimal cho field tiền tệ, cộng case parse CSV-locale.

## C_misa — KHÔNG có MISA thật: mock dataset kế toán

- `C_misa/danhmuc-taikhoan.csv`, `C_misa/chungtu.csv` — dataset kế toán giả
  tự soạn (8 chứng từ, 8 tài khoản).
- `C_misa/expected-report.md` — báo cáo tổng hợp (trial balance Nợ/Có theo
  tài khoản) + chi tiết (sổ cái rút gọn), tính bằng Python/Decimal, có bất
  biến kiểm tra chéo Tổng Nợ = Tổng Có = Tổng số tiền chứng từ
  (126.500.000 VNĐ).
- `C_misa/README.md` — ghi rõ **test MISA SME thật = BLOCKED** (cần license
  MISA + SQL Server + máy Windows lab + kế toán viên QA), không giả lập để
  báo đạt.

## Giới hạn chung (áp dụng cả 3 workflow)

- Không có Microsoft Word/Excel/MISA thật trong môi trường build này —
  mọi round-trip chỉ xác minh qua `python-docx`/`openpyxl`/Python thuần,
  KHÔNG phải Office/MISA thật.
- Không có máy in/scanner thật — bước "in" trong workflow A và "in chứng
  từ" trong workflow C giữ trạng thái `unknown`/`not_run`, KHÔNG được tính
  là đã khảo sát hay đã pass (theo Gate của Gói 1).
- Dữ liệu 100% tự tạo, không đại diện cho khảo sát người dùng thật —
  không được dùng các số liệu này để kết luận "ứng dụng X khảo sát xong".
