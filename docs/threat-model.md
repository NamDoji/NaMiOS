# Threat model sơ bộ — NaMiOS (NaMiOS)

- **Phạm vi:** B004 (threat model + ADR nền tảng), requirement SEC-001, SEC-003.
- **Ngày:** 02/11/2026. **Trạng thái:** sơ bộ (M0) — là DESIGN, chưa có kiểm chứng; mọi lớp phòng thủ phải được test ở M1 (lõi) và M2 (Wine/sandbox thật).
- **Nguyên tắc gốc:** chạy chương trình Windows là **thực thi mã không tin cậy**; **prefix Wine KHÔNG phải ranh giới bảo mật** (COMP-008); catalog KHÔNG được điều khiển lệnh root (SEC-008).

---

## 1. Tài sản cần bảo vệ

| ID | Tài sản | Vì sao giá trị | Lưu ở |
| --- | --- | --- | --- |
| AS-01 | Thư mục `home` người dùng + tài liệu | Dữ liệu cá nhân/công việc, có thể không hoàn nguyên | `~/` (ngoài prefix) |
| AS-02 | Credentials/secret | Mật khẩu, token, cookie đăng nhập, QR, OTP, key Office/Windows, DB password | KWallet/secret service; KHÔNG trong manifest/log |
| AS-03 | SSH keys & browser profile | Truy cập hệ thống khác, phiên đăng nhập | `~/.ssh`, profile trình duyệt |
| AS-04 | CSDL nghiệp vụ (MISA/SQL) | Dữ liệu kế toán; sai/mất là P0 | SQL lab (Windows), backup app-aware |
| AS-05 | Wine prefix + metadata | Trạng thái app; có thể chứa token/bản quyền | `~/.local/share/namios/prefixes/` |
| AS-06 | Catalog & profile keys (production) | Gốc tin cậy cho manifest/chứng nhận | KHÔNG trong repo/ISO/CI không tin cậy (SEC-007) |
| AS-07 | State store giao dịch | Tính toàn vẹn install/journal | `~/.local/share/namios/state.sqlite3` (không chứa mật khẩu) |
| AS-08 | Toàn vẹn hệ thống (root/OS) | Quyền đặc quyền, boot, bootloader | helper + Polkit; APT ký |
| AS-09 | Log & gói chẩn đoán | Có thể rò secret/PII nếu không lọc | `~/.local/state/namios/logs/`, export do user yêu cầu |

## 2. Kẻ tấn công / nguồn đe dọa

| ID | Actor | Khả năng giả định |
| --- | --- | --- |
| TA-01 | Manifest/profile độc hại | Trường lạ, params sai type, `shell`/URL-script/template nội suy, recipe ngoài allowlist, hash/runner giả |
| TA-02 | Payload/bộ cài độc hại (file người dùng cung cấp hoặc tải về) | PE/installer chứa mã khai thác parser hoặc leo thang khi chạy |
| TA-03 | App Windows không tin cậy chạy qua Wine | Đọc/ghi ngoài prefix, dò SSH keys/browser/token, truy cập X11 phiên, phá dữ liệu |
| TA-04 | Catalog/metadata bị giả mạo (MITM, replay, downgrade, key bị lộ) | Thay profile, hạ version, phát profile revoked, giả chữ ký |
| TA-05 | Caller giả danh gọi helper đặc quyền | Gọi D-Bus/Polkit để leo thang, truyền path/package/command tùy ý |
| TA-06 | Người/tiến trình local khác (multi-user) | Sửa prefix của user khác, đọc secret, race TOCTOU |
| TA-07 | Nguồn tải (SSRF/redirect) | Ép backend tải từ nguồn ngoài policy, `curl|bash` |

## 3. Ranh giới tin cậy (trust boundaries)

```
[App Windows / Wine]  --(B1)-->  [Prefix + sandbox policy]  --(B2)-->  [User session / home]
                                                                 |
[Catalog/metadata ký] --(B3)--> [Validator 2 tầng] --(B4)--> [namios libs/CLI] --(B5)--> [Polkit/helper] --> [root/OS]
```

- **B1 — App ↔ prefix:** prefix chỉ *tổ chức môi trường*, KHÔNG phải sandbox. Ranh giới thật là cơ chế Linux duy trì (bubblewrap/AppArmor) + gỡ drive Z (chỉ giảm tiếp xúc).
- **B2 — Sandbox ↔ home:** mặc định app chỉ thấy prefix, staging, runtime read-only, thiết bị thực sự cần, thư mục người dùng cấp quyền. Chặn SSH keys/browser/token/DB/home khác. D-Bus lọc; không mount session bus toàn quyền.
- **B3 — Catalog ↔ hệ thống:** metadata ký + revocation; fail closed; catalog KHÔNG điều khiển lệnh root.
- **B4 — Dữ liệu ↔ hành vi:** "schema hợp lệ" ≠ "an toàn để chạy" → semantic validator bắt buộc.
- **B5 — User ↔ root:** helper least-privilege, phương thức typed, Polkit xác thực theo từng thao tác; KHÔNG `RunCommand`, KHÔNG HTTP localhost điều khiển đặc quyền.

**Phi-ranh-giới (phải ghi rõ, không tuyên bố cách ly tuyệt đối):** X11/XWayland (một client có thể quan sát/điều khiển phiên — SEC-004); prefix Wine; checksum tự publish; metadata hết hạn khi offline.

## 4. Lớp phòng thủ map tới SEC-001..SEC-012

| Phòng thủ | Chống actor | Requirement |
| --- | --- | --- |
| Desktop/app chạy user thường, root không login desktop; helper typed + xác thực caller/Polkit/param/path/state | TA-05, TA-06 | **SEC-001** |
| Path handling FD-based: symlink/hardlink/traversal/TOCTOU/race/ownership/filetype/mount; helper không ghi path tùy ý do user truyền | TA-02, TA-03, TA-06 | **SEC-002** |
| Sandbox bằng bubblewrap/AppArmor policy cụ thể; chỉ thấy prefix/staging/runtime-ro/thiết bị cần/thư mục được cấp; D-Bus lọc | TA-03 | **SEC-003** |
| Mạng/audio/camera/in/clipboard/display cấp theo hồ sơ có giải thích; chọn file qua portal; nới policy → hạ nhãn cách ly + ghi ngoại lệ | TA-03 | **SEC-004** |
| App bị từ chối vì sandbox KHÔNG tự chạy lại ngoài sandbox; chế độ unconfined chỉ QA/VM/dữ liệu giả, có nhãn | TA-03 | **SEC-005** |
| Tải HTTPS + verify TLS; verify hash từ catalog tin cậy + chữ ký vendor khi có; chặn redirect ngoài policy; kiểm soát SSRF; không `curl|bash` | TA-02, TA-07 | **SEC-006** |
| Catalog/repo ký riêng; key production ngoài repo/ISO/CI; metadata có version/thời hạn/scope/revocation; ưu tiên TUF | TA-04 | **SEC-007** (ADR 0007) |
| Chặn downgrade/replay; fail closed khi chữ ký sai/revoked; offline theo policy công bố; catalog không điều khiển root | TA-04 | **SEC-008** |
| Secret trong KWallet/secret service; không truyền qua command line/log; không lưu key Office/Windows/DB trong manifest | TA-02, AS-02 | **SEC-009** |
| Firewall mặc định chặn inbound thừa; không mở SQL/RDP/SSH mặc định; không hạ TLS/SMB1/tắt firewall để sửa lỗi | TA-07 | **SEC-010** |
| Quy trình CVE: triage ≤24h, vá/giảm thiểu ≤72h (TARGET nội bộ); kênh báo lỗi + thu hồi profile | — | **SEC-011** |
| Mã hóa ổ đĩa trước pilot dữ liệu nhạy cảm; thử boot/unlock/update/recovery; không lộ recovery key | AS-01, AS-04 | **SEC-012** |

**Phòng thủ bổ trợ (validator/manifest):** recipe allowlist + argv array, cấm `shell`/`eval`/URL-script/template (COMP-004, ADR 0004); validation 2 tầng; tách manifest/state/evidence; parser .NET giới hạn kích thước/thời gian/quyền, không thực thi để nhận diện (NET-001).

## 5. Danh sách test bảo mật negative cần có ở M1

> M1 chạy được tại host hiện tại (Python thuần). Các test cần Wine/sandbox thật (SEC-06/07 mức device, WINE-*) thuộc M2 — ghi `blocked_external_dependency`, KHÔNG đổi skipped thành pass.

| Test | Map | Mức | Mục tiêu kỳ vọng |
| --- | --- | --- | --- |
| MAN-02 | COMP-004 | unit | Manifest có trường `shell`/trường không biết → từ chối trước thực thi |
| MAN-03 | COMP-004 | unit | Params sai type / dependency chưa duyệt / action lạ → semantic validator từ chối, không tạo process |
| MAN-01 | COMP-004 | unit | Profile TBD: schema pass nhưng install-readiness từ chối |
| MAN-04 | UX-002 | unit | Đặt `task_verified` khi thiếu evidence/required tests → không công bố được |
| SEC-02 | SEC-002 | security | Traversal/absolute path/symlink ra ngoài staging → không đọc/ghi ngoài policy |
| SEC-03 | SEC-002 | security | Đổi symlink giữa plan và apply (TOCTOU) → không vượt ranh giới khi race |
| SEC-04 | COMP-004, CLI-001 | security | Filename có space/dấu/shell metachar → coi là argv, không sinh lệnh phụ |
| SEC-11 | SEC-009, SUP-002 | security | Fake password/token/path trong error + export → không lộ ở log/argv/archive |
| CLI-01 | CLI-001, CLI-003 | unit | stdout JSON sạch (không trộn log); exit code khớp enum lỗi |
| CLI-02/03 | CLI-002 | unit/integration | Plan hết hạn / đổi user / profile revoked → không cài |

**Cần M2 (BLOCKED tại đây):** SEC-01 (caller không hợp lệ gọi helper), SEC-05 (wine root / đọc prefix user khác), SEC-06 (fixture đọc fake SSH keys/browser profile), SEC-07/08 (bus/device/network theo policy; app bị chặn không tự chạy ngoài sandbox), SEC-09/10 (tamper payload/hash/TLS; replay/downgrade/revoked; scan dịch vụ LAN).

---

## 6. Bổ sung từ Phụ lục 10/11 (07/11/2026) — mở rộng phạm vi, KHÔNG sửa nội dung mục 1–5

Phụ lục 10 (N10-049 "Bảo mật nhiều lớp", N10-042 "Cơ sở tri thức có nguồn", N10-050 "Chuỗi cung ứng") và Phụ lục 11 (APP11-003, APP11-020, APP11-033) mở rộng threat model sang ba lớp mà bản DESIGN M0 (mục 1–5) chưa đặt tên riêng: **prompt injection vào SmartAI**, **mạo danh thương hiệu/phishing qua shortcut web**, và **chuỗi cung ứng mở rộng** (ngoài phạm vi catalog/metadata đã có ở SEC-007/008). Mục này **thêm**, không đánh số lại hay sửa TA-01..07/AS-01..09/SEC-001..012 đã chốt ở trên. Trạng thái: DESIGN, chưa có test chạy thật — xem backlog để biết mục nào `open`/`in-progress-code`/`blocked-infra`.

### 6.1 Actor mới

| ID | Actor | Khả năng giả định | Nguồn |
| --- | --- | --- | --- |
| TA-08 | Nội dung web/tài liệu không tin cậy đưa vào ngữ cảnh SmartAI | Trang web/app bên thứ ba chèn chỉ thị ẩn ("cài package", "tắt firewall", "chạy lệnh X") mà AI có thể hiểu nhầm là lệnh người dùng | N10-042 |
| TA-09 | Trang/tên miền mạo danh thương hiệu (Zalo/WhatsApp/Facebook/dịch vụ công…) | Domain giống thật, màn hình login giả, mục đích lấy mật khẩu/OTP của người dùng NaMiOS | N10-049, APP11-003, APP11-033 |
| TA-10 | Tác nhân chuỗi cung ứng (gói thượng nguồn, dependency, hoặc khóa ký bị lộ ở quy mô vượt ngoài catalog NaMiOS) | Package thượng nguồn bị compromise trước khi vào kho NaMiOS; CVE chưa được triage; khóa ký release bị lộ cần thu hồi trên diện rộng | N10-050 |

### 6.2 Phòng thủ bổ sung (không thay thế SEC-001..012, chỉ nêu rõ phạm vi thêm)

| Phòng thủ (thêm) | Chống actor | Nguồn yêu cầu | Trạng thái |
| --- | --- | --- | --- |
| SmartAI coi mọi nội dung web/app bên thứ ba là **dữ liệu không tin cậy, không phải lệnh**; tool chỉ chạy qua Policy Broker đã định nghĩa (không phải do nội dung trang web kích hoạt) | TA-08 | N10-042 (nghiệm thu: 10 ca prompt injection không kích hoạt tool) | `open` — xem `docs/backlog/N10-backlog.md#N10-042` |
| Danh sách miền chính thức được kiểm độc lập cho mọi shortcut web Essentials; chặn redirect ngoài policy; không nhúng form đăng nhập giả trong NaMiOS | TA-09 | APP11-003 (nghiệm thu: domain giả Zalo/WhatsApp bị chặn trước khi nhập mật khẩu — đây cũng là RG-08 ở `docs/release-gates.md`) | `open` — xem `docs/backlog/APP11-backlog.md#APP11-003` |
| Kiểm quyền logo/trademark trước khi đóng ISO; danh mục `approved/pending/replace_with_text`, mặc định `pending` | TA-09 | APP11-033; chi tiết khung ở `docs/license-inventory.md` | `blocked-infra` — cần xác nhận pháp lý thật, xem `docs/backlog/APP11-backlog.md#APP11-033` |
| SBOM theo release, CVE triage, nguồn gói/dependency khóa, reproducible manifest, ký build, rotation/revocation key quy mô chuỗi cung ứng (mở rộng ngoài catalog NaMiOS ở SEC-007/008) | TA-10 | N10-050 (nghiệm thu: mô phỏng khóa ký bị lộ → thu hồi, phát hành bản thay thế, thông báo người dùng) | `open` — xem `docs/backlog/N10-backlog.md#N10-050` |
| Engine/signature quét mã độc có vòng đời cập nhật riêng, báo rõ ngày/thời điểm khi signature quá hạn (không báo "bảo vệ đầy đủ" khi dữ liệu cũ) | TA-02, TA-10 | APP11-020 | `blocked-infra` — cần engine scanner thật, xem `docs/backlog/APP11-backlog.md#APP11-020` |

### 6.3 Liên kết gate

TA-09 (mạo danh thương hiệu) tương ứng trực tiếp gate **RG-08** trong `docs/release-gates.md`; TA-10 (chuỗi cung ứng) và việc khóa ký bị lộ liên quan quy trình override gate ở mục 3 của tài liệu đó (cần ADR + người ký trước khi phát hành tiếp sau một sự cố chuỗi cung ứng).

### 6.4 Giới hạn

Mục 6 là bổ sung phạm vi theo yêu cầu mới (Phụ lục 10/11), **chưa có test nào trong mục 6.2 được chạy**; các ID TA-08/09/10 chưa có test case tương ứng trong bảng mục 5 (M1) — cần bổ sung test ID riêng (ví dụ SEC-12, SEC-13…) khi bắt đầu code, không suy diễn rằng phòng thủ đã tồn tại chỉ vì có dòng trong bảng này.
