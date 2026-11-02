# inventory/workflows.md — 3 workflow có điểm kết thúc đo được (Gói 1, P0)

**Nguồn:** `docs/specs/GIAO-VIEC-M0-M2.md` Gói 1; `docs/specs/DAC_TA_HE_DIEU_HANH.md` §6.2/§6.4/§29 WIN-003/WIN-006.
**Trạng thái chung:** CHƯA chạy thật trên bất kỳ app/Windows reference nào. Mọi workflow dưới đây giữ `status: not_run / blocked_external_dependency` cho tới khi có app build cụ thể + máy Windows tham chiếu + môi trường NaMiOS/Wine/VM thật. Fixture đi kèm là dữ liệu **tự tạo, giả định**, có expected values tính sẵn bằng Python (giám khảo lại được) — KHÔNG phải kết quả đo thật.

> Quy tắc đọc: mỗi workflow có (1) các bước, (2) tiêu chí đo pass/fail cụ thể từng bước, (3) expected outcome (trỏ tới fixture), (4) hậu quả nếu fail, (5) mode dự kiến, (6) giao thức đo trên Windows reference — **BLOCKED** tại môi trường này (không có Windows/Office/MISA/wine thật, theo CLAUDE.md).

---

## Workflow A — Soạn DOCX tiếng Việt → gửi tệp → in

**Ứng dụng liên quan:** Microsoft Word (hồ sơ `inventory/applications.csv` dòng Microsoft Word), kênh gửi: Zalo PC/Web hoặc email (ngoài phạm vi khảo sát sâu ở M0), máy in (hồ sơ `inventory/devices.csv`).

### Các bước
1. Mở Word, tạo văn bản mới, gõ nội dung tiếng Việt có dấu đầy đủ (bảng, có thể có ảnh/mục lục theo APP-OFF-003).
2. Lưu DOCX (Lưu bản mới, không ghi đè tài liệu cũ — APP-OFF-003).
3. Đóng, mở lại DOCX vừa lưu (round-trip) — kiểm tra nội dung còn nguyên.
4. Gửi tệp DOCX qua Zalo PC/Web hoặc email tới một tài khoản QA khác.
5. Người nhận mở lại DOCX, xác nhận nội dung không đổi.
6. In văn bản ra giấy A4, kiểm tra trang in: dấu tiếng Việt, bảng, lề, số trang.

### Tiêu chí đo (pass/fail cụ thể từng bước)
| Bước | Tiêu chí pass | Tiêu chí fail |
| --- | --- | --- |
| 2. Lưu | File `.docx` mở lại được, không báo lỗi corrupt | Lỗi mở file, hoặc mất định dạng |
| 3. Round-trip | `word_count`, `char_count`, `sha256` của nội dung text trích xuất khớp với fixture gốc (dung sai 0 cho text; định dạng DOCX cho phép khác ở tầng XML nhưng nội dung hiển thị phải khớp) | Sai dấu tiếng Việt (vd `ư` → `?`/hộp đen), mất bảng/ảnh, mất mục lục |
| 4–5. Gửi/nhận | Tên tệp và nội dung tệp nhận được giống hệt tệp gửi (so sánh hash) | Tệp bị đổi tên/encoding, hoặc không gửi được tệp có dấu |
| 6. In | Trang in đúng A4, đủ nội dung, dấu tiếng Việt đọc được, không cắt lề | Thiếu nội dung, lỗi font hiển thị hộp vuông (□), sai khổ giấy |

### Expected outcome
Xem fixture `fixtures/workflows/A_docx/baocao-tieng-viet.docx` (văn bản tiếng Việt có dấu, 1 heading, 4 đoạn danh sách, 1 bảng 4x4, 8 paragraph cấp đỉnh) + `fixtures/workflows/A_docx/expected.md` (mô tả round-trip kỳ vọng: số đoạn, text giữ nguyên dạng NFC, kích thước bảng, nội dung từng paragraph/bảng). File sinh + tự verify bởi `scripts/make_workflow_fixtures.py` (round-trip qua `python-docx`, `assert` số liệu khớp ngay khi sinh — giám khảo chạy lại script để kiểm tra độc lập).
Lưu ý: expected trên chỉ xác minh round-trip bằng `python-docx`; giá trị đo khi mở thật bằng Microsoft Word/LibreOffice và in ra giấy là phép đo **khác**, chưa thực hiện (BLOCKED — không có Word/LibreOffice/máy in thật trong môi trường build này).

### Hậu quả nếu fail
- Fail ở bước 2–3 (lưu/round-trip): người dùng không soạn được văn bản công việc hằng ngày → chặn toàn bộ công việc văn phòng cần DOCX, mức **cao**.
- Fail ở bước 4–5 (gửi): không trao đổi tài liệu với đồng nghiệp/khách hàng → gián đoạn phối hợp, mức **trung bình–cao** tùy tần suất.
- Fail ở bước 6 (in): không nộp được bản cứng (hợp đồng, báo cáo cần ký giấy) → chặn nghiệp vụ cần bản in, mức **cao** cho nhóm phải nộp giấy.

### Mode dự kiến
`wine` (Word qua Wine) hoặc `vm`/`remote` (Windows có giấy phép) cho bước soạn/lưu/in; `native`/`web` cho kênh gửi (Zalo Web, email webmail) nếu không cần Word; `web` (Microsoft 365 online) là hồ sơ ứng dụng khác (APP-OFF-006), không tính là đã đạt Word desktop.

### Giao thức đo trên Windows reference — **BLOCKED**
Cần: 1 máy Windows có bản Word cùng edition/build dự kiến thử trên NaMiOS, cùng máy in vật lý (hoặc máy in ảo PDF làm đối chứng tạm), và một người thực hiện đúng 6 bước trên, ghi lại hash + ảnh chụp trang in làm baseline. **Chưa có máy Windows/Word/máy in thật trong môi trường build này** → `status: blocked_external_dependency`. Không tự coi kết quả LibreOffice hoặc mô phỏng là baseline Word.

---

## Workflow B — Mở XLSX → tính → lưu → đối chiếu giá trị

**Ứng dụng liên quan:** Microsoft Excel (`inventory/applications.csv`), phương án đối chứng: LibreOffice Calc (hồ sơ riêng, không tính là Excel — APP-OFF-006).

### Các bước
1. Mở Excel, nhập/mở bảng `BangTinh` (5 dòng mã hàng, số lượng, đơn giá VNĐ, ngày mua) + sheet tra cứu `BangGia` theo fixture.
2. Kiểm công thức dòng: `ThanhTien = SoLuong*DonGiaVND`, `VAT8Pct = ROUND(ThanhTien*8%, -3)` (làm tròn đến nghìn đồng, round-half-away-from-zero), `TongThanhToan = ThanhTien + VAT8Pct`, `NgayGiaoDuKien = NgayMua + 365`, `PhanLoai = IF(SoLuong>=10, "Số lượng lớn", "Số lượng nhỏ")`, `GiaThamKhao` qua `VLOOKUP` và qua `XLOOKUP` (hai cách tra cùng sheet `BangGia`, phải ra cùng kết quả).
3. Tính tổng dòng cuối: `SUM(ThanhTien)`, `SUM(VAT8Pct)`, `SUM(TongThanhToan)`, `AVERAGE(DonGiaVND)`.
4. Lưu file, đóng, mở lại — đối chiếu lại toàn bộ giá trị ở bước 2–3 với lần tính đầu.
5. Mở/so sánh với bản CSV xuất theo locale vi-VN (`bangtinh-vi-VN.csv`: dấu `;` phân cột, `.` phân nghìn, `,` phân thập phân) — parse đúng về cùng giá trị số với bản gốc, không nhầm với locale en-US.

### Tiêu chí đo (pass/fail cụ thể từng bước)
| Bước | Tiêu chí pass | Tiêu chí fail |
| --- | --- | --- |
| 2. Công thức dòng | Mỗi ô (`ThanhTien`, `VAT8Pct`, `TongThanhToan`, `NgayGiaoDuKien`, `PhanLoai`, `VLOOKUP`, `XLOOKUP`) khớp đúng `expected_value` tương ứng trong `B_xlsx/expected.json` (so khớp chính xác cho field VNĐ/ngày/text; `VLOOKUP` và `XLOOKUP` phải cho cùng kết quả) | Sai giá trị, hoặc `VLOOKUP`/`XLOOKUP` cho kết quả khác nhau, hoặc làm tròn VAT sai kiểu (banker's rounding thay vì round-half-away-from-zero kiểu Excel — ví dụ 816500 phải thành 817000, không phải 816000) |
| 3. Tổng dòng cuối | Khớp `expected.summary`: `F7=70356250`, `G7=5629000`, `H7=75985250`; `E8=1408125` với tolerance tuyệt đối `1e-6` (field `AVERAGE` là IEEE-754 float) | Sai tổng do lỗi vùng chọn SUM, hoặc so khớp AVERAGE bằng `==` chính xác thay vì tolerance làm fail giả |
| 4. Round-trip lưu/mở | Mọi giá trị ở bước 2–3 không đổi sau khi lưu rồi mở lại | Excel/Wine làm lệch định dạng số, đổi dấu phân cách nghìn/thập phân, hoặc mất công thức thành giá trị tĩnh sai |
| 5. Đối chiếu CSV locale | Giá trị parse từ `bangtinh-vi-VN.csv` (sau khi bỏ `.` rồi đổi `,`→`.`) khớp `expected.csv_locale_case.rows[].expected_parsed_decimal` | Parse nhầm locale (đọc `6.250.000,00` như en-US ra `6.25`), lệch mã hàng do encoding UTF-8/BOM |

### Expected outcome
Xem fixture `fixtures/workflows/B_xlsx/bangtinh.xlsx` (2 sheet: `BangGia` tra cứu + `BangTinh` 5 dòng dữ liệu, công thức thật `=D*E`, `ROUND(x,-3)` VAT 8% làm tròn nghìn đồng kiểu round-half-away-from-zero, `SUM`, `AVERAGE`, `IF`, `VLOOKUP`, `XLOOKUP`, cộng ngày), `fixtures/workflows/B_xlsx/bangtinh-vi-VN.csv` (case CSV-locale vi-VN khác en-US) và `fixtures/workflows/B_xlsx/expected.json` (giá trị kỳ vọng từng ô, tolerance cho field float, quy tắc làm tròn Decimal, case parse CSV-locale) — toàn bộ tính bằng Python (`Decimal`/`datetime`) trong `scripts/make_workflow_fixtures.py`, tự `assert` khớp ngay khi sinh, giám khảo chạy lại script để kiểm tra độc lập.

### Hậu quả nếu fail
- Sai công thức/tổng ở bước 2–3: báo cáo/đối soát tiền sai → rủi ro **cao/CRITICAL** nếu dùng cho chứng từ thật (thuế, hóa đơn, lương).
- Lệch định dạng số sau round-trip (bước 4): người dùng tưởng dữ liệu đúng nhưng Excel/LibreOffice đọc nhầm dấu phân cách → sai số âm thầm, mức **cao** vì khó phát hiện bằng mắt.
- Lệch CSV locale (bước 5): hỏng pipeline tích hợp với hệ thống khác (vd nhập vào MISA, hoặc gửi báo cáo cho đối tác dùng locale khác) → mức **trung bình–cao** tùy workflow nối tiếp.

### Mode dự kiến
`wine` hoặc `vm`/`remote` cho Excel desktop thật; `native` (LibreOffice Calc) là phương án thay thế nhưng phải tự gắn hồ sơ riêng, không được báo là "đã chạy Excel" nếu chỉ chạy LibreOffice (APP-OFF-006); `web` (Excel Online) là hồ sơ khác.

### Giao thức đo trên Windows reference — **BLOCKED**
Cần: máy Windows có Excel đúng edition/build dự kiến, nhập đúng fixture trên, chụp màn hình/giá trị cell làm baseline trước khi so với NaMiOS. **Chưa có máy Windows/Excel thật trong môi trường build này** → `status: blocked_external_dependency`. Nếu dùng tạm LibreOffice để kiểm thử logic công thức, phải ghi rõ đó là kiểm thử công thức, không phải nghiệm thu tương thích Excel.

---

## Workflow C — Chứng từ thử → báo cáo MISA → xuất/in → khôi phục DB

**Ứng dụng liên quan:** MISA SME (`inventory/applications.csv`), SQL Server (môi trường Windows riêng — APP-MIS-002), máy in (báo cáo).

### Các bước
1. Tạo môi trường MISA SME đúng năm/build + SQL Server trên **Windows lab hợp lệ** (APP-MIS-002: không cài SQL Server qua Wine).
2. Nhập danh mục (khách hàng, tài khoản) và chứng từ thử (phiếu thu/phiếu chi) theo fixture — dữ liệu **giả định hoàn toàn**, không phải dữ liệu kế toán thật (APP-MIS-005).
3. Chạy báo cáo tổng hợp/chi tiết theo tài khoản `1111` và các tài khoản đối ứng.
4. Xuất báo cáo ra Excel/PDF và in ra giấy.
5. Thực hiện backup bằng công cụ chính thức của MISA.
6. Thực hiện restore từ bản backup vào môi trường thử khác, kiểm tra dữ liệu khôi phục khớp bước 2–3.

### Tiêu chí đo (pass/fail cụ thể từng bước)
| Bước | Tiêu chí pass | Tiêu chí fail |
| --- | --- | --- |
| 2. Nhập chứng từ | Nhập đủ 8 chứng từ hạch toán kép theo fixture (`chungtu.csv`), không lỗi lưu | Lỗi service/DLL/COM khi lưu chứng từ |
| 3. Báo cáo | Số dư Nợ/Có từng tài khoản khớp bảng tổng hợp trong `expected-report.md` (vd TK `111` Nợ=32.000.000/Có=14.500.000, TK `511` Nợ=0/Có=25.000.000; **bất biến**: Tổng Nợ = Tổng Có = Tổng số tiền chứng từ = `126.500.000` VNĐ) | Sai số dư, thiếu chứng từ trong báo cáo, hoặc vi phạm bất biến Nợ=Có (hạch toán kép sai) |
| 4. Xuất/in | File Excel/PDF xuất ra và bản in khớp số liệu báo cáo, đủ 8 chứng từ | Thiếu dòng, sai font tiếng Việt khi in, số liệu xuất khác màn hình |
| 5. Backup | Backup chạy xong không lỗi, kích thước/journal hợp lý theo công cụ MISA | Lỗi backup, hoặc chỉ copy file MDF đang chạy (APP-MIS-005: không coi là backup nhất quán) |
| 6. Restore | Dữ liệu sau restore khớp 100% với bước 2–3 (đối chiếu lại toàn bộ bảng tổng hợp/chi tiết) | Mất chứng từ, sai số dư sau restore, hoặc restore không chạy được |

### Expected outcome
Xem fixture `fixtures/workflows/C_misa/danhmuc-taikhoan.csv` (8 tài khoản: 111/112/131/156/331/511/632/642), `fixtures/workflows/C_misa/chungtu.csv` (8 chứng từ hạch toán kép tự soạn) và `fixtures/workflows/C_misa/expected-report.md` (bảng tổng hợp trial balance + sổ cái rút gọn từng tài khoản, tính bằng Python/`Decimal`, có bất biến kiểm tra chéo Tổng Nợ = Tổng Có = `126.500.000` VNĐ, được `assert` trong `scripts/make_workflow_fixtures.py`). `fixtures/workflows/C_misa/README.md` ghi rõ dataset này **KHÔNG** mô phỏng MISA — chỉ là dữ liệu+kết quả tính sẵn để đối chiếu khi có MISA thật.

### Hậu quả nếu fail
- Sai số dư ở bước 3 (báo cáo): kết luận tài chính sai → rủi ro **CRITICAL**, có thể dẫn tới quyết định kinh doanh/kê khai sai nếu dùng dữ liệu thật.
- Fail backup/restore (bước 5–6): mất toàn bộ dữ liệu kế toán khi có sự cố → rủi ro **CRITICAL**, đây là điều kiện chặn migration theo APP-MIS-005/WIN-006 — một bước bắt buộc không đạt thì cả workflow C là `not_ready_for_migration`.
- Fail in/xuất (bước 4): không nộp được báo cáo cho cơ quan thuế/kiểm toán đúng hạn → rủi ro **cao**.

### Mode dự kiến
`vm`/`remote` cho cả client MISA SME và SQL Server (APP-MIS-002 xác nhận đây vẫn phụ thuộc Windows ở phía server); `wine` cho client MISA SME **CHƯA xác nhận khả thi** — phải thử riêng trước khi hứa; nếu Wine không đạt, phải báo đúng giới hạn theo APP-MIS-008 (có thể dẫn tới kết luận "chưa đạt điều kiện triển khai" cho nhóm kế toán SME nếu mục tiêu kinh doanh đòi loại bỏ hoàn toàn Windows).

### Giao thức đo trên Windows reference — **BLOCKED**
Cần: máy Windows lab hợp lệ + SQL Server (không phải production), bản MISA SME đúng năm/build có giấy phép, kế toán viên đối chiếu số liệu. **Hoàn toàn chưa có** trong môi trường build này (không có Windows, không có SQL Server, không có giấy phép MISA) → `status: blocked_external_dependency`. Đây là rủi ro kiến trúc lớn nhất trong Gói 1 vì MISA SME tự chọn SQL Server theo phiên bản Windows (nguồn [3] trong `docs/specs/GIAO-VIEC-M0-M2.md`), không thể "thêm sau khi trang trí desktop".

---

## Tổng kết trạng thái 3 workflow

| Workflow | Fixture (expected tính bằng Python, tự `assert` khi sinh) | Trạng thái đo thật | Lý do blocked |
| --- | --- | --- | --- |
| A — DOCX | `fixtures/workflows/A_docx/baocao-tieng-viet.docx` + `expected.md` | `blocked_external_dependency` | thiếu Word/LibreOffice/Windows/máy in thật (chỉ verify round-trip qua `python-docx`) |
| B — XLSX | `fixtures/workflows/B_xlsx/bangtinh.xlsx` + `bangtinh-vi-VN.csv` + `expected.json` | `blocked_external_dependency` | thiếu Excel/LibreOffice/Windows thật (chỉ verify qua `openpyxl` + Python) |
| C — MISA | `fixtures/workflows/C_misa/chungtu.csv` + `danhmuc-taikhoan.csv` + `expected-report.md` | `blocked_external_dependency` | thiếu Windows lab + SQL Server + giấy phép MISA (dataset chỉ là mock kế toán tự soạn, KHÔNG mô phỏng MISA) |

Tái tạo toàn bộ 3 fixture: `scripts/make_workflow_fixtures.py` (xem `fixtures/workflows/README.md` để biết lệnh cài `python-docx`/`openpyxl` và chạy lại — script tự verify, thoát lỗi nếu số liệu lệch).

**Không có workflow nào được gán `pass`.** Mọi kết luận khả thi ở trên gắn với app build cụ thể (còn `TBD`/`UNKNOWN`) + task + mode, đúng gate của Gói 1.
