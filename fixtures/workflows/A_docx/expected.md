# Expected round-trip — A_docx/baocao-tieng-viet.docx

Tự sinh bởi `scripts/make_workflow_fixtures.py` — các số dưới đây được **tính từ chính đối tượng `docx.Document` trước khi lưu file**, sau đó script đã mở lại file vừa lưu (python-docx) và so khớp (assert) — KHÔNG phải test trên Microsoft Word thật (không có trong môi trường build này).

- Tổng số paragraph cấp đỉnh (`doc.paragraphs`, không tính cell trong bảng): **8**
- Số heading (style bắt đầu bằng `Heading`): **1**
- Số đoạn danh sách (style bắt đầu bằng `List`): **4**
- Số bảng: **1**
- Kích thước bảng (rows x cols): **4 x 4** (1 header row + 3 data rows)
- Toàn bộ text tiếng Việt đã được khẳng định ở dạng NFC (`unicodedata.normalize('NFC', text) == text`) cả trước khi lưu và sau khi mở lại — không bị tách dấu (decomposed) qua round-trip.

## Nội dung từng paragraph cấp đỉnh (theo thứ tự)

1. Báo cáo công việc tuần — Dự án NaMiOS
2. Báo cáo này tổng hợp công việc đã hoàn thành trong tuần, dùng để kiểm tra khả năng đọc lại văn bản tiếng Việt có dấu, danh sách và bảng biểu khi mở bằng các công cụ xử lý văn bản khác nhau.
3. Khảo sát ứng dụng Word, Excel, Zalo PC và MISA SME theo yêu cầu khảo sát ưu tiên của Gói 1.
4. Soạn fixture DOCX, XLSX và dữ liệu kế toán mẫu để kiểm tra round-trip đọc/ghi.
5. Đối chiếu giá trị công thức tính bằng Python/Decimal cho phần liên quan tiền tệ.
6. Ghi nhận trạng thái chưa khảo sát (unknown) cho các ứng dụng chưa có dữ liệu thật từ chủ dự án.
7. Bảng theo dõi tiến độ công việc trong tuần:
8. Người lập báo cáo: Đội kỹ thuật NaMiOS — Ngày 02/11/2026.

## Nội dung bảng (expected, bao gồm header)

| STT | Công việc | Người thực hiện | Trạng thái |
| --- | --- | --- | --- |
| 1 | Khảo sát ứng dụng ưu tiên | Đội khảo sát | Đã ghi nhận |
| 2 | Soạn fixture DOCX/XLSX | Đội kỹ thuật | Hoàn thành |
| 3 | Đối chiếu công thức bằng Python | Đội kỹ thuật | Hoàn thành |

## Giới hạn

- Chỉ xác minh round-trip bằng `python-docx`. KHÔNG có Microsoft Word/LibreOffice thật trong môi trường build này nên KHÔNG tuyên bố đã test mở/in bằng Word/LibreOffice thật hay máy in thật (DEV-002). Bước "in" của workflow A vẫn `not_run`/`unknown` cho tới khi có máy in + driver + người xác nhận theo DEV-001/002.
