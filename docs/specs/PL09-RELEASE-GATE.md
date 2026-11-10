# NaMiOS — Cổng phát hành & lộ trình triển khai Phụ lục 09 (PL09 §4)

- **Ngày:** 10/11/2026. **Nguồn:** PL09 §4 ("Thứ tự triển khai và quyết định cần khóa") + "Cổng phát hành" cuối §4.
- **Trạng thái:** `DESIGN` — khung điều kiện phát hành cho lớp trải nghiệm/ứng dụng/bảo mật PL09; **chưa nối CI/pilot thật** (giống `docs/release-gates.md`). Không bản build/ISO nào đã chạy qua cổng này.
- **Quan hệ:**
  - `docs/release-gates.md` — RG-01..08 (lưới chặn phát hành chung N10/APP11). Tài liệu NÀY **không lặp lại** RG-01..08, mà **bổ sung cổng chuyên PL09** + **lộ trình 3 tầng PL09 §4** + **luật cứng không-tuyên-bố**.
  - `requirements/VN09.md` — ma trận VN09-001..048 → bằng chứng → test.
  - `docs/security/THREAT-MODEL.md` (VN09-024) — mô hình đe dọa hợp nhất.
  - ADR-0012 (tiêu chí chuyển đổi & pilot), ADR-0008 (chứng nhận theo tác vụ).

---

## 1. Nguyên tắc cổng phát hành

Một cổng PL09 là điều kiện **không được bỏ qua** trước khi gắn nhãn một bản NaMiOS/Essentials là "sẵn sàng" cho một vòng (prototype → pilot → community). Cổng **không thay QA/test** — nó là **lưới chặn cuối** khi một năng lực PL09 thiết yếu thất bại theo cách gây hại: mất dữ liệu, sai tiền, lộ bảo mật, hoặc **đánh lừa người dùng về việc gì đang chạy trên máy họ**.

Release manager **không được override cổng đỏ** mà thiếu ADR riêng + người chịu trách nhiệm ký tên (đồng nhất N10-057, `docs/release-gates.md` §3).

> **Giới hạn trung thực:** tự động hóa cổng trong CI, chạy cổng trên pilot thật, và báo cáo cổng thật đều **chưa làm**. Việc tồn tại file này KHÔNG có nghĩa có cơ chế đang chặn build.

## 2. Cổng đỏ chuyên PL09 (bổ sung RG-01..08)

RG-01..08 ở `docs/release-gates.md` vẫn áp dụng đầy đủ (mất file, sai tiền, chữ ký sai, "đã nộp" thiếu receipt, driver mất mạng, browser chưa vá, backup không restore, web-shortcut gắn nhãn sai). Bổ sung cho PL09:

| Mã cổng | Điều kiện ĐỎ (không phát hành nếu còn mở) | VN09 | Vì sao không override |
| --- | --- | --- | --- |
| PL09-G1 | **Gõ tiếng Việt lặp ký tự/mất dấu** ở bất kỳ ô nào (app Linux/Web/Wine đã chứng nhận, gồm ô mật khẩu) | 002, 003 | Bộ gõ là chức năng tối thiểu "mở máy là gõ được"; lỗi gõ làm máy vô dụng với người Việt. |
| PL09-G2 | **Web-shortcut gắn nhãn/ngụ ý "đã cài app Linux/desktop/offline"** cho dịch vụ thực chất là web (Zalo/FB/TikTok/YT) | 016, 018, 019 | = RG-08; đánh lừa kỳ vọng offline + có thể vi phạm cách gọi tên vendor. |
| PL09-G3 | **Security Center hiện "xanh/an toàn" khi một chỉ báo không đạt** (chữ ký quá hạn, backup fail, firewall tắt, chưa vá) | 029, 030, 034 | "Quét sạch" ≠ máy an toàn; báo xanh sai tạo cảm giác an toàn giả, nguy hiểm hơn không báo. |
| PL09-G4 | **SmartAI thực thi lệnh đặc quyền từ nội dung web/tài liệu** (prompt injection) hoặc **tự nhận "đã sửa/đã tương thích/đã an toàn" khi chưa có test/evidence** | 035, 045, 047 | AI là "linh hồn" nhưng không được là lỗ hổng leo thang; nhãn tương thích/bảo mật giả gây hại trực tiếp. |
| PL09-G5 | **App Windows qua Wine đọc được ngoài thư mục được cấp / đọc toàn bộ `home`** | 031 | Prefix ≠ ranh giới bảo mật; rò SSH key/browser/token là mất mát không hoàn nguyên. |
| PL09-G6 | **Mất dữ liệu `/home` sau update/rollback**, hoặc **không boot được bản trước/recovery khi mất điện giữa update** | 026, 037 | = RG-01 ở phạm vi OS; chặn mọi đường cứu hộ + mất niềm tin → quay về Windows. |
| PL09-G7 | **Restore backup không ra đúng hash** trong bài test ransomware giả lập (T09-J) | 032 | = RG-07; backup "có vẻ thành công" nhưng không restore được là an toàn ảo. |
| PL09-G8 | **Có chuỗi chưa dịch / cắt chữ ở luồng người-dùng-mức-lỗi** (cài/đăng nhập/cập nhật/cứu hộ/Security Center) tại độ phân giải pilot | 001 | Người dùng không đọc được hướng dẫn lỗi = không tự cứu được máy. |

Mọi cổng trên áp dụng cho **cả lõi OS và bộ Essentials** — bản Essentials update không được bỏ qua PL09-G2/G3/G4 chỉ vì không đụng kernel.

### Điều kiện khóa quyết định (PL09 §4 "quyết định cần khóa")
Trước khi lên **pilot**, phải có ADR khóa lựa chọn **distro / desktop / IME / package / scanner** (so ứng viên trên: cập nhật bảo mật, thiết bị, tuổi thọ, tài nguyên, pháp lý — **không chọn stack chỉ vì một demo chạy được**). Hiện có: ADR 0002 (Debian 13), 0003 (desktop), 0001 (Linux+Wine), 0013 (Office engine); **ADR chốt scanner (ClamAV) còn mở** — chặn lên pilot cho VN09-029.

## 3. Quy trình khi cổng đỏ

1. Cổng đỏ chặn build chuyển ring (prototype→pilot, pilot→community). Không có "exception mặc định".
2. Override chỉ hợp lệ khi có **ADR riêng** (lý do, phạm vi người ảnh hưởng, thời hạn khắc phục) + **người ký tên** (N10-057). Không ADR + người ký = không override.
3. Báo cáo cổng (khi có CI/pilot thật) phải liệt kê: build id, cổng nào đỏ/xanh, bằng chứng (hash/ảnh/log đã lọc PII), người kiểm, ngày. **Báo cáo mẫu chưa tồn tại.**
4. Cổng đỏ lặp lại nhiều mốc cho cùng năng lực thiết yếu (vd bộ gõ, Zalo Web, ký số, in fleet) → áp N10-060 "Điểm dừng và đổi hướng": không quảng bá thay Windows toàn diện; thu hẹp phạm vi hoặc giữ Windows fallback có phép.

## 4. Lộ trình 3 tầng (PL09 §4)

### Tầng 1 — Prototype (P0)
**Phạm vi:** Linux base + desktop shell/ngôn ngữ + IME + browser + shortcut chính thức + Security Center **trạng thái thực** + cập nhật/rollback + backup; demo 10 ca T09-A..J.

| Điều kiện vào/ra | Cổng liên quan | Trạng thái đo thật |
| --- | --- | --- |
| Không cổng đỏ nào ở bộ test nội bộ (fixture giả, Python thuần) | PL09-G1..G8 + RG-01..08 | **chưa đo** — một số test suite còn `open`/đang dựng (ClamAV, `.desktop` web-shortcut, test T09 chuyên biệt) |
| 10 ca T09 demo được (dù ở mức logic/mô phỏng) | T09-A..J | T09-C/E/F/G/J có test logic SmartAI/essentials; **T09 trên desktop thật chưa chạy** |
| ADR khóa distro/desktop/IME/package + **scanner** | §2 "khóa quyết định" | ADR scanner **còn mở** |

### Tầng 2 — Pilot (P0)
**Phạm vi:** sandbox/portal, App Center provenance, scanner có **đo hiệu năng + false-positive**, Wine capsule tách quyền, thiết bị + Office theo chứng nhận; **pilot người Việt đa cấu hình**.

| Điều kiện vào/ra | Cổng liên quan | Trạng thái đo thật |
| --- | --- | --- |
| Không cổng đỏ nào trên máy/người dùng pilot thật (có consent) | PL09-G1..G8 + RG-01..08 | **chưa đo** — chưa có pilot thật (blocked-infra) |
| Scanner on-access CHỈ bật sau benchmark + chống deadlock/giảm tốc | PL09-G3, VN09-029/038 | **chưa đo** — ClamAV chưa bật, chưa có ngân sách tài nguyên (VN09-038 ⛔) |
| Enforce sandbox Wine thật (bubblewrap/AppArmor) — T09-E | PL09-G5, VN09-031 | **chưa đo** — thuộc M2, cần Wine/sandbox thật |
| Khôi phục 10 tệp đúng hash sau ransomware giả lập — T09-J | PL09-G7, VN09-032 | **chưa đo** — thiếu lớp phát hiện biến-động + restore chưa test HW |

### Tầng 3 — Community (P1)
**Phạm vi:** accessibility hoàn thiện, cá nhân hóa có quyền, quản trị tổ chức, bản địa hóa sâu, SmartAI hướng dẫn/chẩn đoán có audit.

| Điều kiện vào/ra | Cổng liên quan | Trạng thái đo thật |
| --- | --- | --- |
| Không cổng đỏ duy trì quá thời hạn công bố; có người theo dõi | tất cả | **chưa đo** — chưa có bản stable nào phát hành |
| Accessibility đầu-cuối bằng bàn phím/screen reader — T09-H | VN09-006 | **chưa đo** — logic WCAG token xanh, luồng a11y cần desktop thật |
| Dashboard chỉ số có mẫu số/khoảng thời gian/version | VN09-042 | **chưa đo** — có schema evidence, chưa có số pilot thật |

## 5. Luật cứng — KHÔNG được tuyên bố khi chưa có bằng chứng (PL09 §4 "Cổng phát hành")

Những câu sau **tuyệt đối không** được xuất hiện trong UI, website, nhãn App Center, hay câu trả lời SmartAI khi chưa có bằng chứng tương ứng theo từng workflow/thiết bị/ngày thử:

| Tuyên bố bị cấm | Vì sao | Thay bằng (trung thực) |
| --- | --- | --- |
| "Chạy **mọi** phần mềm Windows" / "tương thích 100% Windows" | Wine không chạy mọi `.exe`; nhiều app cần .NET/driver/kernel-mode chưa chứng nhận | "App Windows X phiên bản Y đã kiểm cho workflow Z ngày dd/MM; tính năng A/B thiếu" (ma trận PL07/PL08) |
| "Hỗ trợ **mọi** máy in / **mọi** driver" | Thiết bị/driver theo chứng nhận; chưa test = chưa biết | "Máy in model X đã test in/scan ngày dd/MM; model khác cần kiểm" (ADR-0010) |
| "**Miễn nhiễm** virus" / "diệt sạch mã độc" / "bảo vệ 100%" | Scanner chỉ giảm rủi ro; "quét sạch" ≠ không bị xâm nhập (VN09-030) | "Quét bổ trợ on-demand; báo ngày cập nhật chữ ký + giới hạn; không ngăn 100% mã độc" |
| "**Zalo Linux**" / "Zalo bản NaMiOS/desktop native" | Zalo = Web + PC Windows (Wine); không có bản Linux native (PL09 §1 [1][2]) | "Zalo Web (dịch vụ web, cần mạng)"; "bản PC Windows chỉ là tuyến Wine có chứng nhận" |
| "App đã cài" cho một web-shortcut | Đánh lừa offline + tên vendor (RG-08/PL09-G2) | Nhãn "Dịch vụ web; cần mạng và tài khoản riêng" |
| "Đã nộp / đã in / đã ký" khi chưa có receipt/job/chữ ký hợp lệ | Tuyên bố nghiệp vụ sai (RG-02/03/04, VN09-012) | "Đã gửi yêu cầu; chưa có biên nhận" cho tới khi có bằng chứng từ hệ thống ngoài |
| "99,9%" độ tin cậy / số liệu không có mẫu số | Chưa có pilot thật (VN09-042) | Dashboard nêu mẫu số + khoảng thời gian + version + cấu hình |

Thông tin sản phẩm phải ghi rõ: **loại ứng dụng (A/B/C)**, **mức tương thích từng workflow**, **phần cứng đã thử**, **ngày thử**, **hạn chế còn lại**.

> **Điều KHÔNG được suy diễn từ tài liệu này:** việc có file này không có nghĩa có CI/pilot đang chặn build theo các cổng. Không cổng PL09-G nào từng được kiểm "pass/fail" trên build thật — đây là tiêu chí, không phải kết quả. Bổ sung cổng mới qua ADR khi pilot thật lộ rủi ro nghiêm trọng; không âm thầm sửa bảng này.
