# Chạy phần mềm Windows trên NaMiOS

- **Dành cho:** người dùng NaMiOS nói chung — không cần rành kỹ thuật.
- **verified_on_host: NO** — tài liệu này mô tả CÁCH DÙNG công cụ
  `namios-windows-app`, không phải kết quả đã test thật của bất kỳ phần mềm
  cụ thể nào. Người rành kỹ thuật muốn xem phân tích chi tiết theo tên phần
  mềm (MISA, HTKK, ký số...) xem `docs/wine/WINE-COMPAT-MATRIX.md` trong
  repo NaMiOS.

## 1. Hiểu đúng trước khi dùng (đọc mục này trước, kẻo thất vọng)

NaMiOS dùng một công nghệ gọi là **Wine** để mở một số phần mềm Windows
(`.exe`, `.msi`) ngay trên NaMiOS, không cần cài Windows.

**Wine KHÔNG phải là Windows.** Nó là một "lớp dịch" giúp một số phần mềm
Windows chạy được trên Linux — giống như phụ đề dịch một bộ phim, không
phải quay lại bộ phim đó. Vì vậy:

- Nhiều phần mềm **văn phòng/tiện ích đơn giản** của Windows có cơ hội chạy
  được tốt.
- Phần mềm **kế toán** (ví dụ MISA), phần mềm cần **ký số bằng USB token**
  (chữ ký số nộp thuế/hóa đơn/BHXH), và phần mềm **in hóa đơn/in nghiệp vụ**
  thường **KHÔNG hoạt động đúng**, dù cửa sổ phần mềm vẫn mở lên bình
  thường. Lý do kỹ thuật: Wine không "biết nói chuyện" với USB token hay
  driver máy in đặc thù của Windows — đây là giới hạn chung của Wine trên
  mọi hệ Linux, không riêng gì NaMiOS.

**Mở được giao diện KHÔNG có nghĩa là dùng được đầy đủ.** Nếu bạn cài một
phần mềm kế toán và thấy nó mở lên bình thường, đó CHƯA phải bằng chứng là
bạn có thể nhập số liệu thật, in báo cáo, và ký nộp thuế được — hãy thử
từng bước thật với dữ liệu KHÔNG quan trọng trước, trước khi tin tưởng đưa
dữ liệu thật vào.

## 2. Cách dùng — "Chạy phần mềm Windows"

Mở ứng dụng **"Chạy phần mềm Windows"** từ menu ứng dụng (hoặc tìm "Wine"/
"Windows" trong tìm kiếm). Lần đầu mở, bạn sẽ thấy một thông báo nhắc lại
mục 1 — đọc kỹ rồi bấm OK, nó chỉ hiện một lần.

Menu chính có 4 lựa chọn:

### A. Cài phần mềm Windows mới (.exe / .msi)

1. Bạn cần có SẴN file cài đặt (`.exe` hoặc `.msi`) trên máy — ví dụ đã tải
   từ trang web chính thức của nhà sản xuất, hoặc copy từ USB. Công cụ này
   **không tự tải phần mềm từ mạng** — bạn phải tự tìm và tải trước.
2. Công cụ sẽ hỏi bạn xác nhận đã đọc cảnh báo, rồi cho bạn chọn file cài
   đặt.
3. Đặt một **tên gợi nhớ** cho phần mềm (ví dụ "HTKK", "Notepad cá nhân") —
   mỗi phần mềm sẽ có một "ngăn" riêng, không ảnh hưởng tới phần mềm khác
   bạn đã cài trước đó.
4. Chọn 64-bit (khuyến nghị, cho phần mềm mới) hoặc 32-bit (chỉ cần nếu
   phần mềm rất cũ).
5. Công cụ hỏi có muốn cài thêm vài **thư viện phổ biến** (giúp một số phần
   mềm cũ chạy đúng hơn) — việc này cần mạng Internet và vài phút, bạn có
   thể bỏ qua nếu không chắc.
6. Sau khi chuẩn bị xong, trình cài đặt Windows của phần mềm sẽ hiện lên —
   làm theo các bước cài đặt bình thường như trên Windows. **Đừng tắt công
   cụ** trong lúc này.

### B. Chạy lại phần mềm Windows đã cài trước đó

Vì NaMiOS **chưa** tự thêm phần mềm đã cài vào menu Bắt đầu (một giới hạn
kỹ thuật đã biết — xem mục 4), bạn cần dùng mục này mỗi lần muốn mở lại:
chọn đúng phần mềm từ danh sách, rồi tự tìm tới file `.exe` của phần mềm đó
(thường nằm trong một thư mục kiểu `C:\Program Files\...` bên trong "ngăn"
riêng của phần mềm, công cụ sẽ gợi ý mở đúng thư mục này cho bạn chọn).

### C. Quản lý

- Xem danh sách phần mềm đã cài.
- Mở "thư mục trao đổi" của một phần mềm — đây là CÁCH DUY NHẤT để đưa file
  từ máy bạn vào bên trong phần mềm Windows đó (ví dụ: copy file Excel cần
  phần mềm đó mở, vào thư mục trao đổi, rồi trong phần mềm Windows chọn mở
  file ở ổ `Y:`). Phần mềm Windows chạy trong "ngăn" riêng **không tự thấy**
  các thư mục Tài liệu/Tải xuống thật của bạn — đây là chủ ý, để an toàn
  hơn (một phần mềm lạ không tự đọc được toàn bộ máy bạn).
- Các việc nâng cao hơn (lưu bản sao/khôi phục/xoá hẳn một phần mềm) cần
  dùng dòng lệnh `namios-wine-capsule` trong Konsole — công cụ sẽ chỉ bạn
  đúng lệnh khi bạn chọn mục này.

### D. Đọc hướng dẫn

Mở lại chính tài liệu này.

## 3. Những gì NÊN thử (có cơ hội thật)

- Phần mềm tiện ích Windows nhỏ, không cần kết nối máy in/USB token/CSDL
  (ví dụ công cụ soạn thảo đơn giản, công cụ chuyển đổi file).
- Phần mềm văn phòng cũ chỉ cần nhập/xem dữ liệu, không cần ký số/in khổ
  đặc thù.
- **Game Windows đời cũ/nhẹ, KHÔNG có chống gian lận (anti-cheat):** đây là
  thứ Wine làm tốt nhất. NaMiOS dùng công nghệ **DXVK** để dịch đồ hoạ
  DirectX sang Vulkan, giúp nhiều game chạy mượt — **với điều kiện máy có
  card đồ hoạ (GPU) hỗ trợ Vulkan**. Người rành kỹ thuật: xem
  `docs/wine/DIRECTX-DXVK-VKD3D.md` và template
  `docs/wine/recipes/directx-game-dxvk-template.json` trong repo NaMi.

## 4. Những gì KHÓ hoặc KHÔNG nên kỳ vọng (ở bản NaMiOS hiện tại)

- **Phần mềm kế toán đầy đủ (ví dụ MISA SME):** cần máy chủ cơ sở dữ liệu
  riêng (SQL Server) mà Wine không chạy được — chỉ nên thử với dữ liệu giả
  để xem trước, KHÔNG dùng cho công việc thật.
- **Ký số bằng USB token** (nộp thuế, hóa đơn điện tử, BHXH): nhiều khả
  năng **không ký được** qua Wine, vì thiếu phần mềm điều khiển (driver)
  của nhà sản xuất token. Nếu bạn BẮT BUỘC phải ký số, hãy kiểm tra xem nhà
  cung cấp chữ ký số của bạn có công cụ dành riêng cho Linux chưa, hoặc tạm
  dùng một máy/máy ảo Windows có phép riêng cho việc ký.
- **In hóa đơn/in nghiệp vụ** (khổ đặc thù, máy in nhiệt): chưa được kiểm
  chứng, có thể in sai hoặc không in được.
- **Phần mềm tự thêm vào menu Bắt đầu của NaMiOS:** chưa làm được — bạn
  luôn phải tự chọn lại file `.exe` mỗi lần mở (xem mục 2.B).
- **Âm thanh trong phần mềm Windows:** hiện tắt mặc định ở một số máy (giới
  hạn kỹ thuật đã biết).
- **Game có "chống gian lận" (anti-cheat) như nhiều game online đời mới**
  (ví dụ các game yêu cầu Vanguard, GameGuard, Easy Anti-Cheat/BattlEye chế
  độ kernel): **KHÔNG chạy được qua Wine**, và không có cách nào sửa — đây là
  giới hạn chung của Wine trên mọi hệ Linux, vì các phần mềm này đòi chạy sâu
  trong "nhân" Windows mà Wine không có.

## 4b. Khi nào ĐỪNG dùng Wine (đã có cách tốt hơn ngay trên NaMiOS)

Với nhiều phần mềm Windows quen thuộc, bạn **không cần Wine** — NaMiOS đã có
sẵn bản tương đương chạy thẳng, ổn định hơn:

- **Gõ tiếng Việt:** dùng bộ gõ có sẵn của NaMiOS (giống UniKey) — chạy
  UniKey.exe qua Wine KHÔNG giúp gõ tiếng Việt vào các ứng dụng NaMiOS.
- **Zalo:** mở **zalo trên trình duyệt** (`chat.zalo.me` bằng Firefox).
- **Word/Excel/PowerPoint và mở file Office:** dùng **NaMiOffice** có sẵn.
- **Xem PDF:** dùng trình xem PDF có sẵn (không cần Adobe/Foxit bản Windows).
- **Giải nén .rar/.7z/.zip:** dùng trình quản lý nén có sẵn (không cần
  WinRAR/7-Zip bản Windows).
- **Lướt web:** dùng **Firefox** có sẵn (không cần Chrome/Edge bản Windows).

Nhiều dịch vụ kế toán/thuế của Việt Nam (ví dụ AMIS Kế toán, cổng thuế điện
tử, tra cứu hóa đơn điện tử) đã có **bản web** — bạn nên thử mở bằng trình
duyệt (Firefox có sẵn trên NaMiOS) TRƯỚC, vì bản web không cần Wine và
thường ổn định hơn nhiều so với cài phần mềm Windows qua Wine.

## 5. Nếu có vấn đề

- Phần mềm không mở lên sau khoảng 1 phút: nhiều khả năng phần mềm đó không
  tương thích — không phải máy bạn bị treo, bạn có thể đóng công cụ và thử
  phần mềm khác.
- Chữ trong phần mềm bị lỗi/ô vuông: NaMiOS đã tự thay một số font Windows
  bằng font mở tương đương, nhưng không phải lúc nào cũng khớp hoàn hảo.
- Cần trợ giúp thêm: dùng công cụ **"NaMiOS Chẩn đoán"** từ menu ứng dụng
  để xuất log hỗ trợ (đã che thông tin nhạy cảm) gửi cho người hỗ trợ.
