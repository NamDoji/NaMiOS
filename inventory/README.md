# inventory/ — Gói 1 (M0, P0): "Nắm rõ người dùng và ứng dụng quyết định thành bại"

**Nguồn giao việc:** `docs/specs/GIAO-VIEC-M0-M2.md` Gói 1. **Khung khảo sát 100 app rộng hơn:** `docs/specs/OWNERSHIP-AND-SURVEY.md` Phần B (B038, WIN-001) — file này **mở rộng, không trùng lặp** khung đó: `OWNERSHIP-AND-SURVEY.md` là biểu mẫu 100 app + phương pháp chọn 20 (để trống chờ điền), còn `inventory/` ở đây là **bộ 20 app ưu tiên pilot + devices + 3 workflow** theo đúng trường dữ liệu Gói 1 yêu cầu, có placeholder cụ thể và fixture tính sẵn expected values.

## Placeholder ≠ đã khảo sát

**QUAN TRỌNG:** mọi dòng trong `applications.csv` và `devices.csv` có `status=unknown` hoặc `not_tested`. Đây là **khung công cụ** (field/cột đúng chuẩn Gói 1 + Gói 3), KHÔNG phải kết quả khảo sát thật. Không agent nào được tự:
- Đổi `status` thành `surveyed`/`tested`/`pass` chỉ vì đã có dòng trong CSV.
- Tự đoán `edition_build`, `version`, hoặc model thiết bị thật — mọi ô chưa có dữ liệu thật giữ `UNKNOWN`/`TBD`.
- Suy ra "đã khảo sát 20 app" từ việc file có 20 dòng — 20 dòng này là **danh sách ưu tiên khảo sát** (candidate list), chưa phải kết quả khảo sát (đúng WIN-001: "là TARGET của khảo sát, không tuyên bố đã khảo sát").

`workflows.md` cũng theo nguyên tắc này: 3 workflow có bước đo + tiêu chí pass/fail + fixture **tự tạo, giả định, có quyền dùng** (không copy dữ liệu/tài liệu thật của ai), với `expected` tính bằng Python (`Decimal`/`hashlib`), giám khảo lại được ngay trong `fixtures/workflows/*/`. Nhưng **giao thức đo trên Windows reference và trên NaMiOS thật đều giữ `blocked_external_dependency`** — chưa có máy Windows, Office, MISA, SQL Server hay thiết bị ngoại vi thật trong môi trường build hiện tại (Debian 12 container, không KVM/Wine — xem `CLAUDE.md`).

## Cấu trúc file

| File | Nội dung |
| --- | --- |
| `applications.csv` | ~20 dòng placeholder ưu tiên (Word, Excel, Zalo PC/Web, MISA SME/AMIS, 3 lớp .NET đại diện, + 7 app Việt Nam phổ biến khác) theo đúng trường Gói 1. Mọi dòng `status=unknown`. |
| `devices.csv` | Khung thiết bị theo Gói 3/§27: máy in IPP, máy in cũ cần Printer Application, scanner eSCL/SANE, USB token ký số, máy in hóa đơn/POS. Mọi dòng `support_status=not_tested`. |
| `workflows.md` | 3 workflow (A: DOCX, B: XLSX, C: MISA) có bước, tiêu chí đo, expected outcome (trỏ fixture), hậu quả nếu fail, mode dự kiến, và trạng thái đo trên Windows reference (BLOCKED). |
| `../fixtures/workflows/A_docx/` | `.docx` tiếng Việt thật (python-docx) + `expected.md` (số đoạn/heading/bảng, round-trip NFC) — tự verify bởi `scripts/make_workflow_fixtures.py`. |
| `../fixtures/workflows/B_xlsx/` | `.xlsx` thật (openpyxl, công thức `SUM/AVERAGE/IF/VLOOKUP/XLOOKUP/ROUND`) + CSV locale vi-VN + `expected.json` (Decimal/datetime) — tự verify. |
| `../fixtures/workflows/C_misa/` | Dataset kế toán mock (8 tài khoản, 8 chứng từ hạch toán kép) + `expected-report.md` (trial balance, bất biến Nợ=Có) — KHÔNG mô phỏng MISA thật, chỉ dùng để đối chiếu khi có MISA thật. |

## Danh sách đầu vào THẬT còn thiếu (cần chủ dự án Đỗ Chí Cường + Đỗ Bảo Nam cấp)

Theo đúng mục "Đầu vào cần bổ sung" của `docs/specs/GIAO-VIEC-M0-M2.md`:

1. **Phiên bản Word/Excel có giấy phép** — edition (Microsoft 365 Apps/Office LTSC), channel, build number, 32/64-bit. Không dùng "latest" (APP-OFF-001).
2. **Năm/build MISA SME + loại SQL Server** dự kiến dùng (Express/Standard, chạy trên Windows version nào) — MISA SME 2026 tự chọn SQL Server theo bản Windows, đây là rủi ro kiến trúc cần biết sớm (APP-MIS-002, nguồn [3] trong GIAO-VIEC).
3. **2–3 ứng dụng .NET thật đại diện** — 1 console self-contained, 1 WinForms, 1 WPF — kèm quyền dùng để phân tích tĩnh (NET-001) và thử Wine/VM.
4. **Model thiết bị:** 2 máy in (ưu tiên 1 IPP Everywhere/AirPrint + 1 máy cũ cần driver riêng), 1 scanner (eSCL hoặc cần backend SANE cụ thể), 1 USB token ký số (hãng + model + middleware).
5. **Một máy laptop/PC pilot thật** để cài NaMiOS/Wine thử (môi trường build hiện tại không có KVM — xem `CLAUDE.md`).
6. **3 workflow quan trọng nhất** của nhóm người dùng mục tiêu — hiện `workflows.md` dùng 3 workflow mẫu (A/B/C) theo đúng khung Gói 1; cần xác nhận đây đúng là 3 workflow ưu tiên thật hay cần thay.
7. **Nhóm người dùng pilot cụ thể** (văn phòng phổ thông/giáo viên trước, kế toán SME là nhánh riêng do có DB+ký số) — để chọn đúng 20/100 app theo `priority_score` trong `OWNERSHIP-AND-SURVEY.md` Phần B.3.

**Không gửi password, OTP, dữ liệu kế toán thật hay DB production qua prompt** (CLAUDE.md, APP-MIS-005, APP-ZAL-004). Thiếu các đầu vào trên không chặn phần hạ tầng/fixture đã làm trong phiên này, nhưng chặn mọi bước "đo thật" ở Gói 2/3.
