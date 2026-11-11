# Dùng NaMiOS cho công việc kế toán/tài chính — làm được gì hôm nay, chưa được gì

- **Dành cho:** kế toán, nhân viên tài chính — không cần rành kỹ thuật.
- **verified_on_host: NO** — tài liệu này mô tả **kỳ vọng dựa trên khảo sát
  công khai** (web, ngày khảo sát 11/11/2026), KHÔNG phải kết quả đã chạy
  thử trên máy NaMiOS thật với MISA/HTKK/token chữ ký số thật. Người rành
  kỹ thuật muốn xem phân tích chi tiết + nguồn trích dẫn: `docs/wine/
  WINE-COMPAT-MATRIX.md` và `docs/wine/KY-SO-PKCS11-RESEARCH.md` trong repo
  NaMiOS. Người dùng thường muốn hiểu cách dùng công cụ "Chạy phần mềm
  Windows" nói chung: đọc `CHAY-PHAN-MEM-WINDOWS.md` (cùng thư mục) trước.

## 0. Tóm tắt nhanh — nhìn bảng này trước khi đọc chi tiết

| Việc cần làm | Có làm được trên NaMiOS hôm nay không | Bằng cách nào |
| --- | --- | --- |
| Xem/nhập liệu AMIS Kế toán (web) | **Được** | Mở Firefox, vào `amis.misa.vn` như trên Windows |
| Tra cứu hóa đơn điện tử, xem hồ sơ BHXH (không ký) | **Được** | Firefox |
| Lập + xuất file tờ khai HTKK (chưa ký, chưa nộp) | **Có thể thử được**, chưa chắc 100% | Qua "Chạy phần mềm Windows" + file cấu hình có sẵn — xem mục 2 |
| **Ký số nộp thuế/BHXH/hóa đơn bằng USB Token vật lý** | **Khó/thường KHÔNG được** | Xem mục 3 — đây là việc cần quyết định, không phải việc kỹ thuật đơn thuần |
| Ký số qua dịch vụ "**ký số từ xa**" (SmartCA/MySign…) | **Nhiều khả năng được** | Chỉ cần Firefox + điện thoại — xem mục 3 |
| MISA SME đầy đủ (nhập liệu + báo cáo + ký, dùng hàng ngày) | **Chưa** | Xem mục 4 |

Quy tắc vàng nhắc lại từ `CHAY-PHAN-MEM-WINDOWS.md`: **mở được giao diện
phần mềm KHÔNG có nghĩa dùng được cho công việc thật.** Luôn thử với số
liệu KHÔNG quan trọng trước.

## 1. Việc làm được ngay, không cần Wine gì cả

Mở Firefox (có sẵn trên NaMiOS) và dùng y như trên Windows:

- **MISA AMIS Kế toán** (`amis.misa.vn`) — phần mềm kế toán bản web, không
  cần cài gì. Nhập liệu/xem báo cáo nhiều khả năng dùng tốt qua Firefox.
- **Tra cứu hóa đơn điện tử** (`hoadondientu.gdt.gov.vn`).
- **Cổng Thuế điện tử / BHXH** — xem hồ sơ, tra cứu thông tin (phần KHÔNG
  cần ký số).

Đây là lựa chọn **nên thử trước tiên luôn**, vì không cần Wine, không cần
"ngăn" riêng, không có rủi ro mất dữ liệu do app Windows chạy lạ.

## 2. HTKK — lập tờ khai thuế offline

HTKK (phần mềm của Tổng cục Thuế để lập tờ khai) là app Windows cũ, dùng kỹ
thuật ".NET Framework" (không phải Java, theo khảo sát công khai mới nhất —
chi tiết + nguồn ở `docs/wine/WINE-COMPAT-MATRIX.md`). Vì bản thân HTKK
**không cần máy chủ cơ sở dữ liệu riêng** và **không tự ký số bên trong nó**
(việc nhập/lưu tờ khai tách biệt với việc ký/nộp), đây là app kế toán có
**cơ hội thật nhất** để thử qua Wine trong số các app owner cần.

**Cách thử (có người rành kỹ thuật hỗ trợ sẽ nhanh hơn):**

1. Tự tải bộ cài HTKK từ đúng trang chính thức Tổng cục Thuế.
2. Mở "Chạy phần mềm Windows" → "Cài phần mềm Windows mới" → chọn file cài
   HTKK vừa tải, đặt tên "HTKK".
3. Người rành kỹ thuật có thể dùng sẵn file cấu hình đã chuẩn bị tại
   `~/.config/namios-wine/app-presets/htkk.json` (mở Konsole, gõ
   `namios-wine-capsule create htkk --recipe ~/.config/namios-wine/app-presets/htkk.json`)
   để tự cài thêm thư viện HTKK cần — việc này **chưa được kiểm chứng**,
   chỉ là một gợi ý tốt hơn so với không có gì.
4. Nhập THỬ một tờ khai với **số liệu giả**, lưu, xuất file XML. Nếu bước
   này chạy ổn — tốt. Nếu phần mềm báo lỗi hoặc không mở lên được, HTKK có
   thể không tương thích trên máy bạn, dùng tạm Windows cho riêng việc này.
5. **DỪNG lại ở bước xuất XML.** Việc nộp + ký số tờ khai làm ở bước 3
   dưới đây, trên trình duyệt — KHÔNG làm trong HTKK.

## 3. Ký số — phần quan trọng nhất, đọc kỹ

Đây là điểm nghẽn lớn nhất của kế toán khi chuyển sang Linux nói chung
(không riêng NaMiOS). Có **hai loại chữ ký số** khác hẳn nhau về khả năng
dùng được:

### 3.1 USB Token vật lý (loại cắm vào máy) — thường KHÔNG ký được

Nếu chữ ký số của bạn là một **USB Token vật lý** (Viettel-CA, VNPT-CA,
FPT-CA...) và bạn ký bằng cách cắm USB vào máy + phần mềm của hãng nhận
diện token đó: theo khảo sát công khai (11/11/2026), **chưa tìm thấy** phần
mềm driver chính hãng cho Linux của 3 hãng lớn nói trên. Lý do kỹ thuật:
token cần một phần mềm "điều khiển" đặc biệt của Windows mà Linux/Wine
không tự có — đây là giới hạn chung của MỌI bản Linux, không riêng NaMiOS.

**Nếu bắt buộc phải dùng USB Token vật lý:** tạm thời cần một máy/máy ảo
Windows riêng cho đúng bước ký, hoặc hỏi thẳng nhà cung cấp chữ ký số của
bạn xem họ đã có phần mềm cho Linux chưa (có thể họ mới ra gần đây mà
khảo sát này chưa thấy).

### 3.2 Ký số "từ xa" (SmartCA, MySign...) — cơ hội tốt nhất

Các nhà cung cấp lớn (VNPT, Viettel, nhiều khả năng cả FPT) hiện có dịch
vụ **"ký số từ xa"**: không cần cắm USB Token nào cả — bạn ký bằng cách mở
trang web, bấm "ký", rồi **xác nhận bằng ứng dụng trên điện thoại** (giống
xác thực 2 lớp ngân hàng). Vì máy tính không cần chạm vào "chìa khóa" ký số
(nó nằm an toàn ở máy chủ của nhà cung cấp), cách này **không liên quan gì
tới Wine/driver cả** — chỉ cần Firefox trên NaMiOS là đủ, y hệt trên
Windows.

Cả cổng Thuế điện tử lẫn cổng BHXH đều cho phép đăng ký dùng loại ký số từ
xa này song song với USB Token. **Nếu hiện bạn chỉ có USB Token truyền
thống, đây là việc nên hỏi nhà cung cấp chữ ký số của bạn: có đổi/đăng ký
thêm dịch vụ ký số từ xa được không** — đây là quyết định về dịch vụ/hợp
đồng, không phải vấn đề kỹ thuật của NaMiOS, và là lối ra thực tế nhất hiện
có cho việc ký số trên Linux.

### 3.3 Một công cụ cộng đồng (nhắc tới để biết, KHÔNG khuyến nghị dùng ngay)

Có một phần mềm mã nguồn mở tên **MacSigner** do một lập trình viên độc lập
làm, có bản chạy thẳng trên Linux (không qua Wine), cố gắng giải quyết đúng
bài toán ký số token trên Linux. Đây **không phải sản phẩm của NaMiOS,
không phải sản phẩm chính hãng** của Viettel/VNPT/FPT, và NaMiOS **chưa tự
kiểm chứng**. Nếu bạn muốn tự thử, hãy thử với dữ liệu KHÔNG quan trọng
trước và tự chịu trách nhiệm — không dùng cho việc ký/nộp thật cho tới khi
bạn tự tin vào độ an toàn của nó.

## 4. MISA SME (bản cài đặt đầy đủ) — chưa dùng được cho công việc hàng ngày

MISA SME (khác với MISA AMIS bản web ở mục 1) cần một **máy chủ cơ sở dữ
liệu** (SQL Server) mà Wine không chạy được đúng cách. Vì vậy:

- **Không khuyến nghị** chuyển hẳn sang MISA SME trên NaMiOS cho công việc
  thật.
- Nếu công ty bạn đang dùng MISA SME và cần tiếp tục: cân nhắc (a) chuyển
  sang **MISA AMIS** (bản web, mục 1) nếu phù hợp nhu cầu, hoặc (b) giữ một
  máy/máy ảo Windows riêng cho MISA SME trong lúc đánh giá.

## 5. Luôn nhớ trước khi tin tưởng dùng cho công việc thật

- Thử với số liệu **giả**, không quan trọng, trước — với BẤT KỲ app kế toán
  nào qua Wine.
- "Mở được giao diện" không phải bằng chứng "dùng được" — phải thử trọn
  một việc (nhập → lưu → xuất/in/ký) để biết chắc.
- In hóa đơn/in nghiệp vụ khổ đặc thù qua Wine **chưa được kiểm chứng** —
  không tin tưởng ngay, in thử một bản nháp trước.
- Có vấn đề, dùng công cụ **"NaMiOS Chẩn đoán"** để xuất log gửi hỗ trợ.
