# Release Gates — NaMiOS

- **Trạng thái:** DESIGN (07/11/2026) — khung điều kiện phát hành, **chưa nối vào CI/pilot thật**; không có bản build/ISO nào đã chạy qua gate này.
- **Nguồn:** Phụ lục 10 (N10-057 "Release gate theo tác vụ", N10-060 "Điểm dừng và đổi hướng") và Phụ lục 11 (APP11-036 "Cổng phát hành Essentials").
- **Liên quan:** `docs/backlog/N10-backlog.md`, `docs/backlog/APP11-backlog.md`, `docs/threat-model.md`, `docs/support-matrix.md`, `docs/license-inventory.md`, ADR 0008 (chứng nhận theo tác vụ), ADR 0012 (tiêu chí chuyển đổi và pilot).

## 1. Mục đích

Một gate là điều kiện **không được bỏ qua** trước khi gắn nhãn một bản NaMiOS/App Essentials là "sẵn sàng phát hành" cho một vòng (lab/pilot/stable). Gate không thay thế test/QA — nó là **lưới chặn cuối cùng** khi một tác vụ thiết yếu cho người dùng thật sự thất bại theo cách gây hại (mất tiền, mất dữ liệu, lộ bảo mật, hoặc đánh lừa người dùng về việc gì đã chạy trên máy họ). Release manager không được override một gate đỏ mà thiếu ADR và người chịu trách nhiệm ký tên (N10-057).

**Giới hạn phải nêu rõ:** tài liệu này là khung tiêu chí. Việc tự động hóa gate trong CI, việc chạy gate trên pilot thật, và việc có báo cáo gate thật đều **chưa làm** tại thời điểm viết — xem trạng thái tương ứng ở `docs/backlog/N10-backlog.md#N10-057` và `docs/backlog/APP11-backlog.md#APP11-036`.

## 2. Danh sách điều kiện ĐỎ (không phát hành nếu còn mở)

Mỗi điều kiện dưới đây là **red gate**: nếu phát hiện trong lab/pilot, build không được lên ring kế tiếp (lab→pilot→stable), kể cả khi 90% test khác pass.

| Mã gate | Điều kiện đỏ | Nguồn yêu cầu | Vì sao không được override |
| --- | --- | --- | --- |
| RG-01 | **Mất file** của người dùng trong bất kỳ luồng nào (migrate, update, rollback, backup/restore) | N10-010, N10-011, N10-016, N10-051, APP11-016 | Dữ liệu người dùng (ảnh, hợp đồng, bảng lương) không có bản sao thứ hai do NaMiOS kiểm soát; mất là không hoàn nguyên. |
| RG-02 | **Sai số tiền** ở bất kỳ bước nào (kế toán, thuế, hóa đơn, round-trip Office) | N10-032, N10-033, ADR 0013 (ODC-014) | Sai lệch tài chính có thể gây hậu quả pháp lý/thuế cho người dùng, không chỉ là lỗi UX. |
| RG-03 | **Chữ ký số không hợp lệ** sau khi hệ thống báo "đã ký" | N10-024, N10-033 | Chữ ký sai hiệu lực làm chứng từ vô giá trị pháp lý dù giao diện báo thành công. |
| RG-04 | Trạng thái **"đã nộp" hiển thị mà thiếu receipt/mã biên nhận** từ hệ thống ngoài | N10-033, N10-043, APP11-019 | "Đã nộp" là tuyên bố nghiệp vụ; không có bằng chứng từ cổng/vendor bên ngoài thì tuyên bố đó có thể sai (so N10-043: AI không tự nhận "đã sửa" dựa trên exit code). |
| RG-05 | **Driver làm mất mạng** (Wi-Fi/Ethernet) sau update | N10-048, N10-051 | Mất mạng chặn mọi đường cứu hộ từ xa và các luồng cần internet (nộp thuế, cập nhật, hỗ trợ). |
| RG-06 | **Browser chưa có bản vá nghiêm trọng đã xác nhận** (security advisory đã công bố, chưa áp dụng) | APP11-018, N10-049 | Browser là cửa vào social/ngân hàng/dịch vụ công; lỗ hổng đã công bố công khai là rủi ro đã biết, không phải rủi ro giả định. |
| RG-07 | **Backup không restore được** trên máy khác khi kiểm thử | N10-010, APP11-007 | Một backup "có vẻ tạo thành công" nhưng không restore được là mất an toàn ảo — nguy hiểm hơn không có backup vì tạo cảm giác an toàn sai. |
| RG-08 | **Web shortcut bị gắn nhãn/ngụ ý "đã cài ứng dụng Linux/desktop"** cho một dịch vụ thực chất là trang web (Zalo Web, Facebook, WhatsApp Web…) | APP11-001, APP11-004, APP11-019, điểm "Những điểm tuyệt đối không suy diễn" Phụ lục 10 §5 | Đánh lừa người dùng về việc gì chạy offline/có version cài máy dẫn tới kỳ vọng sai (ví dụ tưởng có thể dùng khi mất mạng), và có thể vi phạm cách gọi tên sản phẩm của vendor. |

Mọi gate trên áp dụng cho **cả hai phạm vi**: lõi hệ điều hành (N10) và bộ ứng dụng Essentials (APP11) — một bản Essentials update không được bỏ qua RG-06/RG-08 chỉ vì nó không đụng tới kernel.

## 3. Quy trình khi gate đỏ

1. Gate đỏ chặn build chuyển ring (lab→pilot, pilot→stable). Không có "exception mặc định".
2. Override chỉ hợp lệ khi có **ADR riêng** ghi rõ lý do, phạm vi người bị ảnh hưởng, thời hạn khắc phục, và **người chịu trách nhiệm ký tên** (đồng nhất N10-057). Không có ADR + người ký = không override.
3. Báo cáo gate (khi có CI/pilot thật) phải liệt kê: build id, gate nào đỏ/xanh, bằng chứng (hash, ảnh, log đã lọc PII), người kiểm, ngày kiểm. Báo cáo mẫu **chưa tồn tại** tại thời điểm viết tài liệu này.
4. Nếu một gate đỏ lặp lại ở nhiều mốc liên tiếp cho cùng một tác vụ thiết yếu (ví dụ ký số hoặc printer fleet chính), áp dụng N10-060 "Điểm dừng và đổi hướng": không quảng bá thay Windows toàn diện, thu hẹp phạm vi hoặc giữ Windows fallback có phép.

## 4. Gate theo vòng (ring) — chỉ là khung, chưa đo

| Vòng | Điều kiện tối thiểu để vào vòng | Trạng thái đo thật |
| --- | --- | --- |
| lab | Không gate đỏ nào ở bộ test nội bộ (fixture giả, Python thuần) | chưa đo — fixture/test suite tương ứng còn ở trạng thái `open`/`in-progress-code` trong backlog |
| pilot | Không gate đỏ nào trên máy/người dùng pilot thật, có consent | chưa đo — chưa có pilot thật (xem N10-059, blocked-infra) |
| stable | Không gate đỏ nào duy trì quá thời hạn công bố; có người chịu trách nhiệm theo dõi | chưa đo — chưa có bản stable nào được phát hành |

## 5. Những điều KHÔNG được suy diễn từ tài liệu này

- Việc có file `docs/release-gates.md` **không** có nghĩa là có cơ chế CI/pilot nào đang thực sự chặn build theo các gate này.
- Không gate nào trong bảng mục 2 đã từng được kiểm tra "pass"/"fail" trên một bản build thật; đây là tiêu chí, không phải kết quả.
- Danh sách 8 gate (RG-01..08) là **tối thiểu bắt buộc theo đặc tả gốc**, không phải danh sách đầy đủ mọi rủi ro phát hành — khi có thêm rủi ro nghiêm trọng phát hiện qua pilot thật, cần bổ sung gate mới qua ADR, không âm thầm sửa bảng này mà không ghi lý do.
