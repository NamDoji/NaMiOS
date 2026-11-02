# Expected report — C_misa (mock dataset, KHÔNG phải MISA thật)

Tự sinh bởi `scripts/make_workflow_fixtures.py`. Toàn bộ số liệu dưới đây được TÍNH TRONG PYTHON bằng `Decimal` từ dữ liệu chứng từ tự soạn ở `chungtu.csv` — KHÔNG lấy từ phần mềm MISA/SQL Server thật (không có trong môi trường build này — xem `README.md` cùng thư mục).

## Danh mục tài khoản

| Mã TK | Tên tài khoản |
| --- | --- |
| 111 | Tiền mặt |
| 112 | Tiền gửi ngân hàng |
| 131 | Phải thu của khách hàng |
| 156 | Hàng hóa |
| 331 | Phải trả cho người bán |
| 511 | Doanh thu bán hàng và cung cấp dịch vụ |
| 632 | Giá vốn hàng bán |
| 642 | Chi phí quản lý kinh doanh |

## Danh sách chứng từ (`chungtu.csv`)

| Số CT | Ngày CT | Diễn giải | TK Nợ | TK Có | Số tiền (VNĐ) |
| --- | --- | --- | --- | --- | --- |
| PC001 | 2026-10-01 | Rút tiền gửi ngân hàng về quỹ tiền mặt | 111 | 112 | 20.000.000 |
| PT001 | 2026-10-03 | Thu tiền khách hàng A thanh toán công nợ | 112 | 131 | 15.000.000 |
| HD001 | 2026-10-05 | Bán hàng hóa cho khách hàng B, chưa thu tiền | 131 | 511 | 25.000.000 |
| GV001 | 2026-10-05 | Ghi nhận giá vốn hàng bán theo hóa đơn HD001 | 632 | 156 | 18.000.000 |
| PNK001 | 2026-10-08 | Nhập hàng hóa từ nhà cung cấp C, chưa trả tiền | 156 | 331 | 22.000.000 |
| PC002 | 2026-10-12 | Trả tiền cho nhà cung cấp C | 331 | 111 | 10.000.000 |
| PC003 | 2026-10-20 | Chi phí quản lý văn phòng tháng 10 | 642 | 111 | 4.500.000 |
| PT002 | 2026-10-25 | Thu tiền khách hàng B thanh toán một phần | 111 | 131 | 12.000.000 |

## Bảng tổng hợp (trial balance) theo tài khoản — expected

Công thức: với mỗi tài khoản, `Nợ` = tổng `SoTien` các chứng từ có `TKNo` = tài khoản đó; `Có` = tổng `SoTien` các chứng từ có `TKCo` = tài khoản đó.

| Mã TK | Tên tài khoản | Tổng Nợ (VNĐ) | Tổng Có (VNĐ) |
| --- | --- | --- | --- |
| 111 | Tiền mặt | 32.000.000 | 14.500.000 |
| 112 | Tiền gửi ngân hàng | 15.000.000 | 20.000.000 |
| 131 | Phải thu của khách hàng | 25.000.000 | 27.000.000 |
| 156 | Hàng hóa | 22.000.000 | 18.000.000 |
| 331 | Phải trả cho người bán | 10.000.000 | 22.000.000 |
| 511 | Doanh thu bán hàng và cung cấp dịch vụ | 0 | 25.000.000 |
| 632 | Giá vốn hàng bán | 18.000.000 | 0 |
| 642 | Chi phí quản lý kinh doanh | 4.500.000 | 0 |
| **Tổng** |  | **126.500.000** | **126.500.000** |

Kiểm tra bất biến: Tổng Nợ = Tổng Có = Tổng số tiền tất cả chứng từ = **126.500.000** VNĐ (mỗi chứng từ ghi đúng 1 lần ở cột Nợ và 1 lần ở cột Có trên hai tài khoản khác nhau — bất biến của hạch toán kép, được `assert` trong script sinh fixture).

## Bảng chi tiết (sổ cái rút gọn) theo từng tài khoản — expected

### TK 111 — Tiền mặt

| Số CT | Ngày CT | Diễn giải | Vai trò | Đối ứng | Số tiền (VNĐ) |
| --- | --- | --- | --- | --- | --- |
| PC001 | 2026-10-01 | Rút tiền gửi ngân hàng về quỹ tiền mặt | Nợ | 112 | 20.000.000 |
| PC002 | 2026-10-12 | Trả tiền cho nhà cung cấp C | Có | 331 | 10.000.000 |
| PC003 | 2026-10-20 | Chi phí quản lý văn phòng tháng 10 | Có | 642 | 4.500.000 |
| PT002 | 2026-10-25 | Thu tiền khách hàng B thanh toán một phần | Nợ | 131 | 12.000.000 |

### TK 112 — Tiền gửi ngân hàng

| Số CT | Ngày CT | Diễn giải | Vai trò | Đối ứng | Số tiền (VNĐ) |
| --- | --- | --- | --- | --- | --- |
| PC001 | 2026-10-01 | Rút tiền gửi ngân hàng về quỹ tiền mặt | Có | 111 | 20.000.000 |
| PT001 | 2026-10-03 | Thu tiền khách hàng A thanh toán công nợ | Nợ | 131 | 15.000.000 |

### TK 131 — Phải thu của khách hàng

| Số CT | Ngày CT | Diễn giải | Vai trò | Đối ứng | Số tiền (VNĐ) |
| --- | --- | --- | --- | --- | --- |
| PT001 | 2026-10-03 | Thu tiền khách hàng A thanh toán công nợ | Có | 112 | 15.000.000 |
| HD001 | 2026-10-05 | Bán hàng hóa cho khách hàng B, chưa thu tiền | Nợ | 511 | 25.000.000 |
| PT002 | 2026-10-25 | Thu tiền khách hàng B thanh toán một phần | Có | 111 | 12.000.000 |

### TK 156 — Hàng hóa

| Số CT | Ngày CT | Diễn giải | Vai trò | Đối ứng | Số tiền (VNĐ) |
| --- | --- | --- | --- | --- | --- |
| GV001 | 2026-10-05 | Ghi nhận giá vốn hàng bán theo hóa đơn HD001 | Có | 632 | 18.000.000 |
| PNK001 | 2026-10-08 | Nhập hàng hóa từ nhà cung cấp C, chưa trả tiền | Nợ | 331 | 22.000.000 |

### TK 331 — Phải trả cho người bán

| Số CT | Ngày CT | Diễn giải | Vai trò | Đối ứng | Số tiền (VNĐ) |
| --- | --- | --- | --- | --- | --- |
| PNK001 | 2026-10-08 | Nhập hàng hóa từ nhà cung cấp C, chưa trả tiền | Có | 156 | 22.000.000 |
| PC002 | 2026-10-12 | Trả tiền cho nhà cung cấp C | Nợ | 111 | 10.000.000 |

### TK 511 — Doanh thu bán hàng và cung cấp dịch vụ

| Số CT | Ngày CT | Diễn giải | Vai trò | Đối ứng | Số tiền (VNĐ) |
| --- | --- | --- | --- | --- | --- |
| HD001 | 2026-10-05 | Bán hàng hóa cho khách hàng B, chưa thu tiền | Có | 131 | 25.000.000 |

### TK 632 — Giá vốn hàng bán

| Số CT | Ngày CT | Diễn giải | Vai trò | Đối ứng | Số tiền (VNĐ) |
| --- | --- | --- | --- | --- | --- |
| GV001 | 2026-10-05 | Ghi nhận giá vốn hàng bán theo hóa đơn HD001 | Nợ | 156 | 18.000.000 |

### TK 642 — Chi phí quản lý kinh doanh

| Số CT | Ngày CT | Diễn giải | Vai trò | Đối ứng | Số tiền (VNĐ) |
| --- | --- | --- | --- | --- | --- |
| PC003 | 2026-10-20 | Chi phí quản lý văn phòng tháng 10 | Nợ | 111 | 4.500.000 |

## Ghi chú số liệu

- Tất cả số tiền là VNĐ nguyên (không có phần lẻ hào/xu) nên không cần quy tắc làm tròn khi tổng hợp — phép `+` Decimal chính xác tuyệt đối, không có sai số float.
- Dataset chỉ có 8 chứng từ, tự soạn cho mục đích test kỹ thuật — KHÔNG phải số liệu doanh nghiệp thật.
