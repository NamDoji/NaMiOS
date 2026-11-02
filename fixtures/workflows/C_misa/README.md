# C_misa — mock dataset kế toán (KHÔNG có MISA thật)

**Trạng thái: test MISA SME thật = BLOCKED** tại môi trường build này (xem
`CLAUDE.md`, `docs/specs/GIAO-VIEC-M0-M2.md` Gói 1/Gói 3). Thư mục này KHÔNG
chứa và KHÔNG mô phỏng MISA SME/AMIS. Lý do blocked:

- Không có bản MISA SME có quyền dùng (license) để cài/kích hoạt.
- Không có SQL Server + máy Windows lab hợp lệ (MISA SME chọn SQL Server
  theo phiên bản Windows — xem đặc tả §4.1/§6.4 và nguồn [3] trong
  `docs/specs/GIAO-VIEC-M0-M2.md`).
- Không có kế toán viên QA để đối chiếu kết quả theo quy trình thật
  (OWNERSHIP-AND-SURVEY.md Phần C, MIG-001).

## Thay vào đó, thư mục này chứa gì

Một **dataset kế toán giả tự soạn** (danh mục tài khoản + chứng từ), đủ để
luyện/kiểm tra logic **tổng hợp (trial balance) và chi tiết (sổ cái rút
gọn)** bằng Python/Decimal — KHÔNG đụng tới phần mềm MISA:

- `danhmuc-taikhoan.csv` — 8 tài khoản mẫu (111, 112, 131, 156, 331, 511,
  632, 642), tên tự soạn theo hệ thống tài khoản kế toán Việt Nam phổ biến
  (không copy từ tài liệu MISA có bản quyền).
- `chungtu.csv` — 8 chứng từ hạch toán kép tự soạn (rút tiền, thu/chi,
  bán hàng, giá vốn, nhập hàng, trả nợ, chi phí).
- `expected-report.md` — báo cáo tổng hợp + chi tiết **tự tính bằng
  Python/Decimal** từ đúng 8 chứng từ trên, kèm bất biến kiểm tra chéo
  (Tổng Nợ = Tổng Có = Tổng số tiền chứng từ).

## Khi có MISA thật để test (M2/M4, sau khi được cấp quyền)

Theo Gói 3 (GIAO-VIEC-M0-M2.md): cần đúng build MISA SME theo năm, SQL
Server trên máy Windows lab hợp lệ, dữ liệu kế toán giả (có thể dùng lại
dataset ở đây làm input nhập tay/import), và kế toán viên đối chiếu kết quả
xuất ra từ MISA với `expected-report.md` này. Bộ test MISA thật tối thiểu
gồm: kết nối DB, nhập chứng từ, xuất báo cáo tổng hợp/chi tiết, in, backup
và restore — KHÔNG được báo `task_verified` nếu thiếu QA kế toán ký.
