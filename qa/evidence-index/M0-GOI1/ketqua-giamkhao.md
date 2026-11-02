# Kết quả giám khảo độc lập — M0, Gói 1 (P0)

**Vai trò:** giám khảo độc lập, KHÔNG sửa `inventory/`, `fixtures/`. Chỉ kiểm & báo.
**Phạm vi:** `docs/specs/GIAO-VIEC-M0-M2.md` Gói 1 + `docs/specs/OWNERSHIP-AND-SURVEY.md` + `docs/specs/DAC_TA_HE_DIEU_HANH.md` mục 27–29.

## Meta

- `run_id`: qa-m0-goi1-giamkhao-20261102-001
- `commit_sha`: e8edcdd6a855a9be71f650874e5d3a22c43f3364 (branch `master`, worktree hiện tại)
- `python_runtime`: `/home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python` (3.11.2)
- `host`: Debian 12, không Windows/Office/MISA/Wine/máy in thật
- `timestamp`: 2026-11-02T11:11:10Z
- `reviewer`: agent giám khảo độc lập (phiên này) — chưa có người ký thủ công thứ hai

**Phương pháp:** với mỗi mục, tự suy ra giá trị kỳ vọng bằng Python TRƯỚC khi đọc file "đáp số" (`expected.json`/`expected-report.md`/`expected.md`), sau đó so khớp. Toàn bộ lệnh Python chạy độc lập, không copy công thức từ `scripts/make_workflow_fixtures.py`.

---

## 1. B_xlsx — tự tính lại độc lập bằng `openpyxl` + Decimal, so với `expected.json`

Đọc trực tiếp công thức từng ô trong `fixtures/workflows/B_xlsx/bangtinh.xlsx` (openpyxl, `data_only=False`), không dùng cached value (file này không có cache vì chưa mở bằng Excel thật).

Công thức đọc được (khớp mô tả `expected.json`):
- `F2:F6 = D*E` (SoLuong × DonGiaVND)
- `G2:G6 = ROUND(F*0.08,-3)` (VAT 8%, làm tròn nghìn đồng)
- `H2:H6 = F+G`
- `J2:J6 = I+365` (NgayMua + 365 ngày)
- `K2:K6 = IF(D>=10,"Số lượng lớn","Số lượng nhỏ")`
- `L2:L6 = VLOOKUP(...)`, `M2:M6 = XLOOKUP(...)` tra `BangGia`
- `F7/G7/H7 = SUM(...)`, `E8 = AVERAGE(E2:E6)`

Tự tính lại bằng Python (`Decimal`, `ROUND_HALF_UP` cho `ROUND(x,-3)` kiểu Excel, `date + timedelta` cho ngày):

| Dòng | ThanhTien (F) | VAT8Pct (G) | TongThanhToan (H) | NgayHetBH (J) | XepLoai (K) | VLOOKUP/XLOOKUP |
| --- | --- | --- | --- | --- | --- | --- |
| MH01 (SL=5, giá 1.250.000) | 6.250.000 | 500.000 | 6.750.000 | 2027-01-15 | Số lượng nhỏ | 1.250.000 |
| MH02 (SL=10, giá 1.020.625) | 10.206.250 | 817.000 | 11.023.250 | 2027-02-20 | Số lượng lớn | 1.020.625 |
| MH03 (SL=8, giá 3.200.000) | 25.600.000 | 2.048.000 | 27.648.000 | 2027-03-05 | Số lượng nhỏ | 3.200.000 |
| MH04 (SL=15, giá 620.000) | 9.300.000 | 744.000 | 10.044.000 | 2027-04-18 | Số lượng lớn | 620.000 |
| MH05 (SL=20, giá 950.000) | 19.000.000 | 1.520.000 | 20.520.000 | 2027-05-22 | Số lượng lớn | 950.000 |

Tổng dòng cuối tự tính: `F7=70.356.250`, `G7=5.629.000`, `H7=75.985.250`, `E8=1.408.125` (AVERAGE, float, tolerance 1e-6).

**Lưu ý đặc biệt đã verify lại bằng tay:** MH02 — VAT thô = 10.206.250 × 0,08 = **816.500,00** (đúng nửa nghìn). `ROUND(816500,-3)` kiểu Excel (round-half-AWAY-FROM-ZERO) = **817.000**, KHÔNG phải 816.000 (banker's rounding của `Decimal` mặc định/`round()` Python sẽ cho 816.000 — đây chính là ca kiểm thử bẫy lỗi làm tròn mà `expected.json` ghi rõ). Tự tính bằng `(816500/1000).to_integral_value(ROUND_HALF_UP)*1000 = 817000` → khớp.

**So với `expected.json`:** khớp **100%** cho toàn bộ 7 cột × 5 dòng (35 giá trị) + 4 ô tổng (F7/G7/H7/E8). Không có lệch nào ngoài tolerance.

**CSV locale vi-VN** (`bangtinh-vi-VN.csv`): tự parse `"6.250.000,00"` → bỏ `.` rồi đổi `,`→`.` → `Decimal("6250000.00")`, lặp lại cho 5 dòng — khớp 100% với `expected.csv_locale_case.rows[].expected_parsed_decimal`.

**Kết luận B_xlsx: PASS** (không có defect; expected.json chính xác, giám khảo lại được bằng công cụ độc lập).

---

## 2. C_misa — tự cộng lại tổng hợp/chi tiết từ `chungtu.csv` (Decimal), so với `expected-report.md`

Đọc 8 chứng từ từ `chungtu.csv`, tự cộng Nợ/Có theo từng mã TK bằng `Decimal` (không dùng `scripts/make_workflow_fixtures.py`):

| Mã TK | Tổng Nợ tự tính | Tổng Có tự tính |
| --- | --- | --- |
| 111 | 32.000.000 | 14.500.000 |
| 112 | 15.000.000 | 20.000.000 |
| 131 | 25.000.000 | 27.000.000 |
| 156 | 22.000.000 | 18.000.000 |
| 331 | 10.000.000 | 22.000.000 |
| 511 | 0 | 25.000.000 |
| 632 | 18.000.000 | 0 |
| 642 | 4.500.000 | 0 |
| **Tổng** | **126.500.000** | **126.500.000** |

Tổng số tiền tất cả chứng từ (cộng cột `SoTien`, 8 dòng) = **126.500.000** — khớp bất biến Tổng Nợ = Tổng Có = Tổng chứng từ.

**So với `expected-report.md`:** khớp **100%** cho cả bảng tổng hợp (8 tài khoản × 2 cột) và bất biến chéo 126.500.000 VNĐ. Phần chi tiết sổ cái rút gọn trong `expected-report.md` (từng dòng chứng từ gắn vai trò Nợ/Có + đối ứng cho mỗi TK) cũng tự dò lại bằng tay từ `chungtu.csv` — không phát hiện dòng nào gán sai vai trò hoặc sai đối ứng.

**Kết luận C_misa: PASS** (không có defect). `README.md` cùng thư mục ghi đúng tình trạng BLOCKED test MISA thật (thiếu license + SQL Server lab + kế toán viên QA) — không có tuyên bố vượt quá phạm vi mock dataset.

---

## 3. A_docx — mở lại được + text có dấu còn nguyên NFC

Mở `fixtures/workflows/A_docx/baocao-tieng-viet.docx` bằng `python-docx` độc lập (không qua `make_workflow_fixtures.py`):

- Mở file không lỗi (không corrupt).
- Số paragraph cấp đỉnh: **8** (khớp `expected.md`).
- Số heading: **1**, số đoạn style `List*`: **4**, số bảng: **1**, kích thước bảng: **4×4** — khớp `expected.md`.
- Nội dung text từng paragraph (8/8) và từng cell bảng (16/16 ô) so khớp nguyên văn với `expected.md`, bao gồm dấu tiếng Việt đầy đủ (ví dụ "Báo cáo công việc tuần — Dự án NaMiOS", "Đối chiếu giá trị công thức tính bằng Python/Decimal...").
- Kiểm `unicodedata.normalize('NFC', text) == text` cho toàn bộ 8 paragraph cấp đỉnh + 16 cell bảng: **tất cả đều đã ở dạng NFC**, không bị tách dấu (decomposed) qua round-trip mở lại.

**Kết luận A_docx: PASS** (đúng như `expected.md`, kèm giới hạn đã ghi rõ: chỉ verify round-trip qua `python-docx`, chưa test Word/LibreOffice/máy in thật — KHÔNG claim vượt phạm vi này).

---

## 4. Kiểm `inventory/` — header, trạng thái, workflows.md

### `inventory/applications.csv`

- Header 16 cột: `app,publisher,edition_build,arch_32_64,installer_source,usage_rights,frequency,user_group,required_tasks,input_files,output_files,deps_driver_service_dotnet_sql_token_addin,impact_if_fail,candidate_modes,windows_reference,status` — đủ các trường Gói 1 yêu cầu (ứng dụng/nhà cung cấp, edition/build/arch, nguồn+quyền dùng, tần suất, người dùng, công việc bắt buộc, input/output, deps driver/service/.NET/SQL/token/add-in, hậu quả fail, mode thử, Windows reference, status).
- 16 dòng (bao gồm Word, Excel, Zalo PC, Zalo Web, MISA SME, MISA AMIS, 3 lớp .NET đại diện (console/WinForms/WPF), HTKK, phần mềm ký số, hóa đơn điện tử, bộ gõ tiếng Việt, PDF reader, hội thảo trực tuyến, LibreOffice — có ghi rõ LibreOffice là "SẢN PHẨM KHÁC", không tính là Word/Excel).
- **Tự rà soát toàn bộ cột `status`: 16/16 dòng = `unknown - CHUA khao sat` (một số kèm chú thích BLOCKED cụ thể).** Không có dòng nào bị gán `pass`/`surveyed`/`tested`. Đạt yêu cầu "mọi dòng status=unknown ban đầu" của đề bài.
- Các trường chưa có dữ liệu thật đều ghi `UNKNOWN`/`TBD`, không bị điền giá trị suy đoán/bịa (ví dụ edition/build Word/Excel/MISA đều để UNKNOWN, đúng với `docs/assumptions.md` A52–A54 chưa chốt).

### `inventory/devices.csv`

- Header 11 cột: `vendor_id,product_id,model,firmware,connection,kernel,driver_backend,license,functions_tested,support_status,verified_by` — khớp yêu cầu DEV-001 (§27): vendor ID, product ID, firmware, kết nối, kernel, driver/backend, giấy phép, chức năng đã thử, trạng thái hỗ trợ, người xác nhận.
- 5 dòng đại diện: máy in IPP Everywhere/AirPrint/Mopria, máy in cũ cần Printer Application, scanner eSCL/SANE, USB token ký số, máy in hóa đơn/POS.
- **Tự rà soát toàn bộ cột `support_status`: 5/5 dòng = `not_tested - CHUA KHAO SAT` (kèm chú thích theo DEV-003/DEV-005 nhắc rõ "có trong danh sách SANE"/"lsusb nhận diện" KHÔNG đồng nghĩa đã chứng nhận).** `vendor_id`/`product_id` đều để `TBD` — không bịa ID thiết bị cụ thể khi chưa có máy thật. `verified_by` = "CHUA co nguoi xac nhan" cho cả 5 dòng.

### `inventory/workflows.md`

- Đủ 3 workflow (A DOCX, B XLSX, C MISA) như đề bài yêu cầu, mỗi workflow có: các bước đo được, bảng tiêu chí pass/fail cụ thể từng bước, expected outcome trỏ đúng fixture, hậu quả nếu fail (phân mức rủi ro), mode dự kiến (`wine/vm/remote/native/web`, không cộng gộp mode), và mục **"Giao thức đo trên Windows reference — BLOCKED"** riêng cho cả 3 workflow, nêu rõ lý do blocked (thiếu máy Windows/Office/MISA/SQL Server/máy in thật).
- Bảng tổng kết cuối file: cả 3 workflow đều giữ `blocked_external_dependency`, **không có workflow nào được gán `pass`** — đúng Gate Gói 1 ("mỗi kết luận khả thi gắn app build + task + mode; thiếu dữ liệu là blocked, không phải pass").

**Kết luận mục 4: PASS** — không phát hiện dòng/trạng thái nào bị gán sai thành "đã khảo sát"/"đạt" khi chưa có dữ liệu thật; định dạng và nội dung đúng khung Gói 1 + §27/§29 + B038.

---

## 5. Tái lập bằng chứng (reproducibility)

Chạy lại `scripts/make_workflow_fixtures.py` tại phiên giám khảo (không sửa file, chỉ overwrite đúng các file nó sinh ra, idempotent): thoát với `"status": "ok"`, script tự `assert` lại toàn bộ số liệu (`formula_cells_verified: 39`, `sum_thanh_tien/sum_vat/sum_tong_thanh_toan` cho workflow B, `voucher_count=8`, `total_no=total_co=126500000` cho workflow C, `paragraph_count=8/heading_count=1/table_count=1` cho workflow A) — khớp hoàn toàn với các giá trị giám khảo tự tính độc lập ở mục 1–3 phía trên. Không có `AssertionError`, không có drift.

---

## Tổng kết

| Hạng mục | Kết quả | Defect |
| --- | --- | --- |
| B_xlsx (công thức + CSV locale) | **PASS** | Không |
| C_misa (tổng hợp/chi tiết) | **PASS** | Không |
| A_docx (mở lại + NFC) | **PASS** | Không |
| inventory/applications.csv | **PASS** | Không |
| inventory/devices.csv | **PASS** | Không |
| inventory/workflows.md | **PASS** | Không |
| Script tái lập (`make_workflow_fixtures.py`) | **PASS** (idempotent, tự assert) | Không |

**Không phát hiện defect nào.** Mọi giá trị `expected` trong 3 fixture workflow A/B/C đã được giám khảo **tính lại độc lập bằng Python** (không đọc đáp số trước) và khớp chính xác 100% (không lệch ngoài tolerance khai báo). `inventory/applications.csv` và `inventory/devices.csv` đúng header yêu cầu Gói 1/§27 và giữ nguyên tất cả dòng ở trạng thái `unknown`/`not_tested` — không có dòng nào bị tính nhầm là đã khảo sát hoặc đã pass, đúng Gate "thiếu dữ liệu là blocked, không phải pass". `inventory/workflows.md` đủ 3 workflow với tiêu chí đo cụ thể và phần Windows-reference đánh dấu BLOCKED rõ ràng cho cả 3.

**Giới hạn của lượt kiểm này:** giám khảo chỉ xác minh được tính đúng của phép tính và cấu trúc dữ liệu tại môi trường build (không có Windows/Office/MISA/Wine/máy in thật — theo CLAUDE.md). Không tự tuyên bố đã verify kết quả đo trên Windows reference hay thiết bị thật — các mục đó vẫn đúng là `blocked_external_dependency`/`not_tested` như hồ sơ đã ghi.
