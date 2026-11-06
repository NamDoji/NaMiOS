# ADR 0013 — Đánh giá engine Office

- **Trạng thái:** proposed (quyết định PHƯƠNG PHÁP đánh giá; CHƯA có engine nào được đo/chốt)
- **Ngày:** 06/11/2026
- **Liên quan:** Phụ lục 07 §1, §2, §7; requirement ODC-001, ODC-002, ODC-003, ODC-004; test T01–T05; roadmap O0

## Bối cảnh

Phụ lục 07 chốt Office là **ứng dụng riêng, cài sẵn, tích hợp sâu với File Manager và SmartAI**
(ODC-001), không viết lại Word/Excel/PowerPoint từ đầu ở mốc đầu tiên. LibreOffice có mã nguồn
và SDK/UNO để làm tiện ích mở rộng/bộ lọc [1], nên được nêu là **ứng viên tham chiếu** — nhưng
chưa có 15 fixture tài liệu thật, chưa có máy Windows đối chứng, và license/thương hiệu của
LibreOffice có nhiều thành phần + nghĩa vụ riêng cần rà trước khi phân phối bản sửa đổi [2].
ADR này phải quyết định **cách đánh giá** (tiêu chí, rubric, fixture plan, audit giấy phép)
trước khi có số đo nào được công bố — không được chọn engine "chỉ từ quảng cáo" (nghiệm thu
ODC-002).

## Quyết định

1. **Giai đoạn A = đóng gói upstream, không fork (ODC-003 Giai đoạn A).** NaMiOS đóng gói
   engine mã nguồn mở hiện có làm ứng dụng Office riêng, có version/kênh cập nhật/rollback
   (ODC-001). LibreOffice là **ứng viên dẫn đầu để thẩm định**, dùng bản từ kho phân phối +
   SDK/UNO, KHÔNG sửa core. Việc fork/sửa mã nguồn (Giai đoạn C) bị hoãn tới khi có blocker
   lặp lại + chủ trì bảo trì + bài regression rõ ràng (ODC-003).
2. **Rubric đánh giá (ODC-002)** — phương pháp, KHÔNG phải kết quả. Mọi ô lẽ ra là số đo đều
   phải ghi **"chưa đo (cần 15 fixture thật + Windows đối chứng)"** cho tới khi có fixture thật;
   không điền % độ đúng hay benchmark suy diễn.

   | Tiêu chí | LibreOffice | Ứng viên khác (cần khảo sát) |
   | --- | --- | --- |
   | Độ đúng DOCX/XLSX/PPTX (round-trip) | chưa đo (cần 15 fixture thật + Windows đối chứng) | chưa khảo sát |
   | Tiếng Việt + font (Unicode, dấu, kiểm chính tả) | chưa đo (cần 15 fixture thật + Windows đối chứng) | chưa khảo sát |
   | In (CUPS: A4/A5, duplex, scale, QR/barcode) | chưa đo (cần 15 fixture thật + Windows đối chứng) | chưa khảo sát |
   | API mở rộng (UNO/SDK, filter, add-in) | chưa đo (cần 15 fixture thật + Windows đối chứng) | chưa khảo sát |
   | Tài nguyên máy (RAM/CPU/thời gian mở) | chưa đo (cần 15 fixture thật + Windows đối chứng) | chưa khảo sát |
   | Bảo trì/nhịp upstream (tần suất bản, vá lỗi) | chưa đo (cần 15 fixture thật + Windows đối chứng) | chưa khảo sát |
   | Nghĩa vụ giấy phép (thành phần, phân phối, thương hiệu) | chưa đo (cần 15 fixture thật + Windows đối chứng) | chưa khảo sát |
   | Khả năng tùy biến UX (theme, ribbon-style, Việt hóa) | chưa đo (cần 15 fixture thật + Windows đối chứng) | chưa khảo sát |

   Cột "ứng viên khác" (ví dụ OnlyOffice, Collabora Online — tên gọi cần xác minh tại thời
   điểm khảo sát) hiện là **chỗ trống cần khảo sát**, không phải loại bỏ; không coi thiếu dữ
   liệu là "LibreOffice thắng tuyệt đối".
3. **Audit giấy phép/thương hiệu trước khi phân phối bản sửa đổi hoặc đặt tên thương mại
   (ODC-004)** — checklist, chưa có mục nào đã xác nhận xong:
   - [ ] Liệt kê giấy phép **từng thành phần** trong engine đóng gói (engine lõi + mọi
     filter/extension/font đi kèm) — các thành phần có thể khác giấy phép nhau; không giả định
     một license chung cho toàn bộ gói [2].
   - [ ] Xác định nghĩa vụ công bố mã nguồn/notices cho **bản phân phối đã sửa đổi** (nếu Giai
     đoạn A chỉ đóng gói nguyên bản, mục này có thể đơn giản hơn; vẫn phải ghi rõ trạng thái).
   - [ ] Tra cứu quyền thương hiệu/logo (trademark) của engine nguồn — tên và logo nhà cung cấp
     KHÔNG được dùng để ngụ ý chứng nhận/hợp tác khi chưa có phép (đồng nhất ADR 0009 OWN-002).
   - [ ] Quyết định tên sản phẩm NaMiOS cho app Office riêng CHỈ sau khi hai mục trên xong +
     kiểm tra pháp lý; chưa có tên thương mại nào được chốt trong ADR này.
   - [ ] Kiểm UI "About" của app Office phải nêu engine gốc + giấy phép khi người dùng yêu cầu
     (ODC-004), không ẩn nguồn gốc mã nguồn mở.
   - [ ] Ghi rõ nguồn gói (kho phân phối chính thức hay build riêng) và version pin được dùng.
4. **Kế hoạch 15 fixture (ODC-002 nghiệm thu)** — BLOCKED chờ file thật + máy Windows đối
   chứng, chưa chạy. Danh sách loại fixture cần thu thập (đã khử dữ liệu nhạy cảm, theo Phụ
   lục 07 §7 đầu vào pilot):
   - Công văn hành chính (DOCX, có header/footer, số/ký hiệu văn bản).
   - Hợp đồng đơn giản (DOCX, có bảng, chữ ký tay/placeholder).
   - Bảng lương XLSX có công thức (SUM/IF/VLOOKUP hoặc tương đương).
   - Bảng điểm XLSX có merged cells + conditional formatting.
   - XLSM có macro VBA thật (không phải macro giả lập).
   - Văn bản DOCX dùng font không có sẵn trên máy đích (kiểm thay thế font).
   - DOCX có track changes + comment đang mở.
   - Tài liệu có chữ ký số (digital signature) cần giữ hiệu lực sau round-trip.
   - XLSX có pivot table.
   - XLSX có chart/biểu đồ nhúng.
   - PPTX có animation/transition cơ bản.
   - DOCX có table of contents tự động + footnote.
   - PDF form có field điền được (kiểm tương tác, không chỉ render).
   - Tài liệu có external link (liên kết tới file/nguồn ngoài).
   - Bảng tính kế toán nhiều cột rộng (kiểm in không cắt cột số tiền, theo ODC-012).

   **Phương pháp đo (khi có fixture + máy Windows):** mở → sửa (một thay đổi nhỏ có kiểm
   soát) → lưu → mở lại trong engine ứng viên; so **semantic** (số liệu, công thức, chữ ký)
   và **render** (bố cục, số trang, font) với kết quả cùng thao tác trên Windows đối chứng.
   Sai số tiền/trang hoặc chữ ký mất hiệu lực là **fail dù file mở được** (ODC-014). Cho tới
   khi có 15 fixture thật + máy Windows đối chứng, toàn bộ bước này ở trạng thái
   `blocked_external_dependency` — không chạy giả lập rồi báo pass.
5. **Chiến lược tùy biến theo giai đoạn (ODC-003), nhắc lại để ràng ADR này với roadmap:**
   - **Giai đoạn A (ADR này):** đóng gói engine upstream nguyên bản + thiết lập tiếng Việt
     (bộ gõ, kiểm dấu, mẫu VN) + tích hợp Document Broker/File Manager/SmartAI. Không sửa core.
   - **Giai đoạn B:** tiện ích mở rộng/bộ lọc qua SDK/UNO khi cần (ví dụ mẫu VN, kết nối in),
     vẫn không fork mã nguồn engine.
   - **Giai đoạn C:** chỉ sửa core/fork khi có blocker lặp lại đã ghi nhận, có người chủ trì
     bảo trì lâu dài, có bài regression, và có TCO/kế hoạch 2 năm (liên quan ODC-043) — không
     fork "cho đẹp".

## Lý do

- Nghiệm thu ODC-002 đòi rubric + ≥15 fixture + số đo thật, không chấp nhận chọn engine theo
  danh tiếng; ADR quyết định phương pháp trước giúp tránh việc đo sau này bị thiên vị theo
  engine đã "ngầm chọn".
- Tách rạch "đóng gói" (ít rủi ro pháp lý, nhanh) khỏi "fork" (rủi ro bảo trì dài hạn, cần
  chủ trì) đúng theo thứ tự Giai đoạn A/B/C đã chốt ở Phụ lục 07 ODC-003.
- Giấy phép + thương hiệu là rủi ro pháp lý riêng khỏi rủi ro kỹ thuật; đặt tên sản phẩm trước
  khi audit xong có thể tạo kỳ vọng hoặc vi phạm nhãn hiệu không thể rút lại dễ dàng (nhất
  quán với ADR 0009 về quyền sở hữu/thương hiệu).
- Fidelity thật (round-trip semantic/render) chỉ có nghĩa khi so với Windows đối chứng cùng
  dữ liệu; không có máy đối chứng thì mọi số đo chỉ là nội bộ engine, không chứng minh được
  gì về "đủ thay Windows".

## Hệ quả

- **Chưa có engine nào được "chọn" theo nghĩa production.** LibreOffice vẫn là ứng viên dẫn
  đầu để thẩm định; không app/tài liệu nào được viết "NaMiOS Office chạy trên LibreOffice X.Y
  đã kiểm chứng" cho tới khi rubric ở mục 2 có số đo thật.
- **Chưa có tên thương mại.** Không dùng tên sản phẩm riêng cho app Office cho tới khi checklist
  mục 3 xong và kiểm tra pháp lý xác nhận không vi phạm thương hiệu bên thứ ba.
- **Document Broker, Office Route Matrix và Fidelity Gate là code ENGINE-AGNOSTIC** (đã có
  khung ở `namios_pra.office_route` — `resolve_office_route`/`fidelity_gate` theo `OfficeNeed`,
  không gắn cứng vào một engine cụ thể) — phần này **làm được ngay bây giờ**, không phải chờ
  chốt engine; khi đổi/thêm ứng viên chỉ cần đổi lớp thực thi (executor), không đổi hợp đồng.
- Rubric mục 2 và checklist mục 3 là deliverable O0 theo Roadmap Phụ lục 07 §5: nếu chưa đạt,
  **không đặt tên thương mại** (gate O0 ghi rõ trong bảng roadmap).
- Kế hoạch 15 fixture (mục 4) chỉ là khung thu thập; dữ liệu/đo lường thật `blocked_external_
  dependency` chờ chủ dự án cung cấp file đã khử dữ liệu + máy Windows đối chứng + người xác
  nhận nghiệp vụ (Phụ lục 07 §7).

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Host build hiện tại không có LibreOffice/SDK UNO cài sẵn, không có máy Windows đối chứng,
  không có 15 fixture tài liệu thật (đã khử dữ liệu) từ chủ dự án.
- Phần làm được ngay ở host hiện tại: rubric/checklist dạng tài liệu (ADR này), khung schema
  cho fixture record + evidence (tái dùng mô hình evidence/gate đã có ở `namios_evidence`
  và `namios_pra` — chỉ-HẠ không tự nâng trạng thái), và lớp Document Broker/Route
  Matrix/Fidelity Gate engine-agnostic (đã có khung trong `namios_pra.office_route`).
- Phần BLOCKED: cài đặt + chạy thật LibreOffice (hoặc ứng viên khác) trên 15 fixture, đo
  round-trip so Windows đối chứng, audit giấy phép có chữ ký pháp lý — cần build host có
  engine cài được + chủ dự án cấp fixture + máy Windows đối chứng. Ghi `blocked_external_
  dependency`, không bịa số đo.

## Spike cần làm + điều kiện chấp nhận

- **Spike S-ODC-1:** dựng schema fixture record (loại tài liệu, nguồn, hash, kỳ vọng, kết quả
  Windows đối chứng, kết quả engine, pass/partial/blocked) bằng Python thuần; validator CHẶN
  gán `pass` khi thiếu kết quả Windows đối chứng hoặc thiếu hash fixture.
- **Spike S-ODC-2:** rà checklist license/thương hiệu mục 3 ở dạng khung (không điền dữ liệu
  pháp lý thật); kiểm text không tuyên bố đã hoàn tất kiểm tra pháp lý khi chưa có xác nhận.
- **Spike S-ODC-3 (khi có fixture thật + máy Windows, M4/O0):** chạy round-trip 15 fixture
  qua LibreOffice, điền rubric mục 2 bằng số đo thật thay "chưa đo"; nếu sai số tiền/trang/
  chữ ký ở bất kỳ fixture nào → fail fixture đó dù file mở được (đồng nhất ODC-014).
- **Điều kiện chấp nhận:** không ô rubric nào bị điền số đo khi chưa chạy fixture thật; không
  tài liệu/UI nào gọi engine là "đã chọn chính thức" hay dùng tên thương mại trước khi checklist
  mục 3 xong; Document Broker/Route Matrix/Fidelity Gate vẫn build và test được bằng Python
  thuần không phụ thuộc việc chốt engine; test T01–T05 (Phụ lục 07 §6) giữ `not_run`/`blocked`
  cho tới khi có fixture + máy đối chứng thật.

## Nguồn

- [1] LibreOffice, [SDK/UNO Overview](https://api.libreoffice.org/) và [mã nguồn/SDK](https://www.libreoffice.org/download-other/).
- [2] LibreOffice, [Licenses](https://www.libreoffice.org/licenses/): phần mềm có nhiều thành phần và nghĩa vụ giấy phép; quyền thương hiệu cần xét riêng.
