# NaMiOffice — hệ sinh thái ngoài Writer/Sheet/Slides: Mail/Notes/Forms/Data/Collab

**Ngày:** 10/11/2026 · **Trạng thái tài liệu:** kế hoạch + trạng thái thật hiện tại, không phải tuyên bố đã hoàn tất.
**Đọc cùng:** `docs/specs/namioffice-v2/03_MAIL_NOTES_FORMS_COLLAB.md` (kit gốc, không sửa file đó) và `docs/office/COMPAT-MATRIX.md` + `docs/office/feature-registry.json` (bản ghi hiện trạng ML-01..03, NT-01..03 đã cập nhật theo tài liệu này).

> **Quy tắc cứng của kit — nhắc lại ở đây để không ai quên khi code tiếp:**
> 1. **Không giả bằng nút menu.** Mail/Notes/Forms/Data/Collab là **sản phẩm/dịch vụ riêng**, không được "làm giả" bằng cách gắn một nút trong NaMiOffice/LibreOffice rồi gọi là đã có tính năng.
> 2. **Không gọi "tương thích Outlook"** khi mới có IMAP đọc mail. Phải nêu rõ khác biệt lịch, danh bạ, task, thư mục chung (shared mailbox) và add-in.
> 3. **Consent + least-privilege cho mọi thứ chạm cloud.** Bất kỳ tích hợp OneDrive/SharePoint/Google Drive/NaMiCollab-cloud nào đều phải: người dùng cấp quyền theo scope tối thiểu, thấy rõ nhà cung cấp/chỗ lưu/chính sách dữ liệu, xử lý được token hết hạn và API đổi.
> 4. **Tài liệu nhạy cảm không tự gửi cho AI cloud.** SmartAI mặc định chạy cục bộ khi phù hợp; gửi cloud chỉ khi người dùng/tổ chức **opt-in** và biết rõ nội dung gửi đi — prompt nằm trong tài liệu là dữ liệu không tin cậy, không được ra lệnh cho AI đọc tệp khác hay gửi mạng.

---

## 1. NaMiMail — ĐÃ CÓ, dựa trên Mozilla Thunderbird (hôm nay)

**Trạng thái: `partial` — đã đóng gói, CHƯA rebrand UI, CHƯA verified_on_host.**

### Gói đã thêm

`distro/live-build/config/package-lists/0405-mail-notes.list.chroot`:

| Gói | Vai trò | Xác minh tồn tại trixie/main |
|---|---|---|
| `thunderbird` | Client mail/lịch/danh bạ chính | CÓ — xác nhận qua `deb.debian.org/debian/dists/trixie/main/binary-amd64/Packages.gz` (tải trực tiếp 10/11/2026); version `1:140.12.0esr-1~deb13u1` |
| `thunderbird-l10n-vi` | Giao diện tiếng Việt | CÓ — cùng Packages.gz; phụ thuộc đúng version `thunderbird` |
| `hunspell-vi` | Chính tả tiếng Việt khi soạn thư | CÓ — là gói `Recommends` của `thunderbird-l10n-vi`, khai tường minh để chắc có mặt dù build dùng `--no-install-recommends` |

`verified_on_host: NO` theo đúng quy ước repo (chưa chạy `apt-cache show`/`lb build` trên build host Debian 13 trixie thật) — nhưng khác với nhiều file `.list.chroot` khác chỉ đối chiếu qua `madison.php`, lần này đã **tải trực tiếp package index thật** của trixie và `zcat | grep` ra đúng 3 dòng `Package:`. Mức tin cậy cao hơn "chưa kiểm" thông thường, nhưng vẫn không thay thế bước `apt-cache show` trên host thật trước khi phát hành.

### Vì sao chọn Thunderbird (không viết mới)

Kit `03_MAIL_NOTES_FORMS_COLLAB.md` §1 (F2) ghi rõ: *"Nếu chưa triển khai, NaMiOS có thể tích hợp ứng dụng mail Linux đáng tin và gắn nguồn, không cần viết mới ngay."* Thunderbird là:
- Phần mềm FOSS (MPL-2.0) do Mozilla duy trì, dùng rộng rãi, có kiểm toán bảo mật liên tục, nhận bản vá ESR qua Debian security team.
- Đáp ứng **nguyên văn** baseline F1 của kit (§1, dòng F1): *"IMAP/SMTP có TLS, OAuth/OIDC khi nhà cung cấp hỗ trợ, nhiều tài khoản, thư mục, tìm kiếm cục bộ, danh bạ CardDAV/CSV/vCard, lịch CalDAV/ICS, lời mời họp, task cơ bản, thông báo, soạn thư tiếng Việt, chữ ký email, đính kèm an toàn, chế độ ngoại tuyến và khôi phục."* — tất cả đều là tính năng **lõi** của Thunderbird từ bản 102 trở lên (CardDAV/CalDAV đã gộp vào core, không cần add-on rời), không phải tính năng NaMiOS tự viết.

### Nhãn hiển thị — PHẢI dùng đúng, không hơn không kém

- Gọi là **"NaMiMail (dựa trên Mozilla Thunderbird)"** trong mọi UI/docs/landing page giới thiệu NaMiOS — không gọi trần "NaMiMail" như thể là app NaMiOS tự viết, không gọi trần "Thunderbird" như thể NaMiOS không đóng gói/hỗ trợ gì.
- **KHÔNG** dùng cụm "tương thích Outlook", "tương thích Exchange", "tương thích Microsoft 365" ở bất kỳ đâu. Thunderbird nói chuyện với Exchange/M365 chỉ qua giao thức mở (IMAP/SMTP/CalDAV khi tenant admin bật) hoặc add-on bên thứ ba chưa được kiểm — khác hẳn giao thức MAPI/EWS gốc của Outlook.
- Giữ dòng tín dụng "dựa trên Mozilla Thunderbird" — đúng nghĩa vụ ghi công của MPL-2.0, giống cách `docs/branding/NAMIOFFICE.md` đã giữ tín dụng "dựa trên LibreOffice (The Document Foundation)".

### Việc CÒN LẠI để gọi là "xong F1" (không được coi các mục dưới là đã làm)

1. **Rebrand UI** — hook kiểu `0450-namioffice-brand.hook.chroot` nhưng cho Thunderbird: đổi `Name=`/`Name[vi]=` trong `.desktop` của Thunderbird sang "NaMiMail (Thunderbird)", **không đổi** `Exec=`/`MimeType=`. *(Chưa làm trong lần cập nhật này — chỉ mới thêm gói. Ghi rõ để không ai tưởng UI đã đổi tên.)*
2. **Kiểm SMTP/IMAP/CardDAV/CalDAV bằng tài khoản thử hợp lệ thật** trên máy đã boot ISO — kit F1 yêu cầu "kiểm SMTP/IMAP phổ biến bằng tài khoản thử hợp lệ; không lưu mật khẩu thô." Chưa có tài khoản thử trong môi trường soạn tài liệu này.
3. Trang giới thiệu/launcher NaMiOS cần nêu rõ NaMiMail = Thunderbird-based, link ghi công Mozilla.

### KHÔNG claim (F2/C3 — chưa làm, chưa có hạ tầng)

- S/MIME/PGP có UX khóa đã kiểm.
- Rules nâng cao, shared calendar, delegated/shared mailbox kiểu Exchange.
- Offline sync quy mô lớn, enterprise admin (group policy, autodiscover MDM).
- Kết nối Exchange/Outlook.com/Microsoft 365 qua API được cấp quyền (cần kiểm điều khoản, OAuth scope, giới hạn API, tenant policy trước — chưa làm).
- Add-in Outlook/Office.js — không áp dụng cho Thunderbird, không gọi nhầm.

---

## 2. NaMiNotes — CHƯA PHÁT HÀNH, không ship package tạm

**Trạng thái: `not_shipped` — có chủ đích, đã rà soát trixie/main, không có lựa chọn đủ tốt.**

### Vì sao không ship gì (quyết định "bảo thủ")

Baseline F1 của kit (§2): *"notebook/section/page, text, list, table, ảnh, ghi âm có quyền, vẽ bằng bút nếu thiết bị hỗ trợ, tìm kiếm tiếng Việt không dấu, offline, export PDF/Markdown/ODF."* Đã kiểm `deb.debian.org/.../trixie/main/binary-amd64/Packages.gz` cho các ứng dụng ghi chú FOSS phổ biến:

| Ứng dụng | Có trong trixie/main? | Vì sao KHÔNG đủ cho F1 |
|---|---|---|
| **Joplin** | **KHÔNG** (không có trong Debian — chỉ phát hành qua AppImage/snap/npm riêng của Joplin) | Kit cấm thêm phần mềm ngoài repo chính thức ("không nên đóng gói phần mềm ngoài repo" / không có kiểm soát cập nhật qua `apt`) |
| `zim` | Có (`0.76.3-1`, arch `all`) | Cấu trúc trang kiểu wiki (gần với notebook/page) nhưng KHÔNG có ghi âm, KHÔNG vẽ bằng bút, export PDF chỉ qua in/HTML chứ không có nút "Export PDF" trực tiếp đáng tin |
| `cherrytree` | Có (`1.2.0+dfsg-1`) | Cây phân cấp (gần với notebook/section/page nhất trong các lựa chọn) + export HTML/PDF/văn bản — nhưng KHÔNG ghi âm, KHÔNG vẽ bằng bút, tìm kiếm tiếng Việt không dấu chưa kiểm |
| `gnote` | Có | Ghi chú phẳng (flat), không có notebook/section/page — quá đơn giản so với F1 |
| `tomboy-ng` | Có | Tương tự gnote, phẳng, không đủ cấu trúc |
| `basket` | Có | Có phân nhóm (basket) nhưng dự án gần như ngừng phát triển nhiều năm, không đủ "đáng tin" để gắn thương hiệu NaMiOS |
| `xournalpp` / `xournal` | Có | Rất mạnh về **vẽ bằng bút** (đúng một phần F1) nhưng KHÔNG phải app ghi chú có cấu trúc (không notebook/section/page, không table, tìm kiếm văn bản hạn chế vì nội dung chủ yếu là nét vẽ) |

**Không có một gói nào** đáp ứng đồng thời cấu trúc + rich content (text/list/table/ảnh) + ghi âm + vẽ bút + tìm kiếm + export đa dạng mà kit yêu cầu. Ghép nhiều app lại và gọi chung là "NaMiNotes" sẽ là đúng kiểu "giả bằng nút menu" mà kit cấm (chỉ khác là giả bằng nhiều app rời thay vì một nút). Theo nguyên tắc bảo thủ: **không ship gì mặc định**, để trống rõ ràng còn hơn ship nửa giải pháp rồi gọi là NaMiNotes.

### Lựa chọn tạm (không cài sẵn, không gắn nhãn NaMiOS) cho người dùng cần ngay

Nếu người dùng cần ghi chú có cấu trúc ngay bây giờ, họ có thể tự cài qua Trung tâm phần mềm (Discover/`apt`) — KHÔNG cài sẵn trong ISO, KHÔNG đổi nhãn/tên NaMiOS, hiển thị đúng tên gốc:
- `cherrytree` — gần nhất với "notebook/section/page" (cây phân cấp), export HTML/PDF/văn bản thô.
- `zim` — nếu người dùng thích phong cách wiki/liên kết trang.

Hai gợi ý này là **tạm, của bên thứ ba**, không phải sản phẩm NaMiOS — không được hiển thị trong menu dưới tên "NaMiNotes".

### NaMiNotes thật — việc cần làm khi được giao (chưa bắt đầu)

1. Xác định build trên nền có sẵn (ví dụ fork/đóng gói Joplin có kiểm giấy phép + cập nhật, hoặc viết ứng dụng Qt/Kirigami riêng dùng SQLite + Markdown) hay viết mới hoàn toàn.
2. F1 (bản đầu): notebook/section/page, text/list/table/ảnh, ghi âm có xin quyền microphone rõ ràng, vẽ bằng bút nếu `libinput`/Wacom có hỗ trợ, tìm kiếm tiếng Việt không dấu (cần bộ bỏ dấu tiếng Việt), offline-first, export PDF/Markdown/ODF (định dạng mở, có thể sao lưu).
3. F2 (sau): đồng bộ nhiều thiết bị — chỉ quảng bá sau khi có hệ thống account thật, mã hóa khi truyền/lưu, giải quyết xung đột, lịch sử phiên bản, khả năng xóa dữ liệu triệt để (right to erasure).
4. KHÔNG cam kết round-trip tệp OneNote (`.one`) độc quyền khi chưa kiểm thật bằng tệp mẫu.

---

## 3. NaMiForms — CHƯA PHÁT HÀNH

**Trạng thái: `not_shipped`.** Dịch vụ thu thập phản hồi/khảo sát/quiz, không phải tính năng LibreOffice Calc/Writer gắn thêm nút.

- **F1:** tạo câu hỏi, lựa chọn, thang đo, điều kiện nhánh (hiện/ẩn câu theo câu trước), chế độ anonymous/định danh, giới hạn số lần gửi, export CSV/ODS/XLSX, phân quyền truy cập, màn hình consent + chính sách retention (giữ dữ liệu bao lâu, ai xem được).
- **F2:** chấm điểm tự động kiểu quiz + workflow doanh nghiệp có audit log.
- **Ràng buộc cứng:** nếu thu thập dữ liệu học sinh/cơ quan, chỉ thu ở **mức cần thiết** (data minimization) và phải bảo vệ đúng mức (không lưu trần, không public mặc định).
- **Lựa chọn interim (không cài sẵn, không gắn nhãn NaMiOS):** không có server-side forms app nào trong Debian main đáp ứng được mô hình dịch vụ (cần backend/DB/auth) — đây vốn là dịch vụ web, không phải package desktop để `apt install`. Không có gợi ý interim hợp lý qua package-list; nếu cần ngay, dùng form engine mã nguồn mở tự host (tự đánh giá riêng, ngoài phạm vi tài liệu này) hoặc form built-in của bên thứ ba có chính sách dữ liệu rõ ràng mà người dùng tự chọn.

---

## 4. NaMiData (dịch vụ) — CHƯA PHÁT HÀNH

**Trạng thái: `not_shipped`.** Lưu ý: nhãn "NaMiData" hiện ĐANG dùng cho tên hiển thị của **LibreOffice Base** (xem `docs/branding/NAMIOFFICE-APPS.md`) — đó là ánh xạ Access→Base ở mức rebrand hiển thị, KHÔNG phải dịch vụ dữ liệu/backend riêng mà mục này nói tới. Khi dịch vụ thật ra đời, cân nhắc đổi tên tránh trùng (xem ghi chú "reserved" trong `NAMIOFFICE-APPS.md`).

- **F2 (kit §3):** bảng/khóa/quan hệ, form nhập liệu, validation, query SQL có phân quyền, report, import/export CSV/SQL, lộ trình migration.
- Nếu dùng LibreOffice Base làm nền UI, phải **phân biệt rõ** định dạng file (`.odb`) và backend thật (SQLite/PostgreSQL/MySQL/HSQLDB) — người dùng cần biết dữ liệu nằm ở đâu.
- Access `.accdb`/`.mdb`, Access forms/reports và VBA **không tự tương thích** — hiện NaMiOffice chỉ đọc một phần qua `mdbtools` (xem `docs/support/OFFICE-SUITE.md` §4) — cần lộ trình chuyển dữ liệu **thủ công** + đối soát (verify số dòng/giá trị sau chuyển), không tự động "import rồi coi như xong".
- **Lựa chọn interim:** LibreOffice Base (đã có trong `0400-office-browser.list.chroot`) dùng được ngay cho nhu cầu CSDL cá nhân/nhỏ qua HSQLDB/SQLite embedded — đã ship, không cần thêm gói. Đây KHÔNG phải "NaMiData dịch vụ" theo nghĩa F2 ở trên.

---

## 5. NaMiCollab (cộng tác + lưu trữ) — CHƯA PHÁT HÀNH, sản phẩm dịch vụ riêng

**Trạng thái: `not_shipped`.** Theo kit §4, đây là **3 giai đoạn**, không nhảy cóc:

### Giai đoạn 1 — không cần cloud để dùng Office (nền tảng trước)
File local/SMB/WebDAV theo quyền hệ thống có sẵn, file lock, cảnh báo xung đột (conflict), lịch sử bản cục bộ (ví dụ qua filesystem snapshot hoặc version cục bộ của LibreOffice), link chia sẻ qua hệ thống mạng nội bộ sẵn có (Samba/WebDAV đã có trong NaMiOS qua gói mạng/lưu trữ hiện tại — không phải tính năng mới).

### Giai đoạn 2 — server NaMiCollab hoặc tích hợp nền được phê duyệt
Tài khoản/tổ chức, ACL theo tệp, version history, comments/mentions, share link có hạn, offline sync + xử lý conflict. **Chưa bắt đầu xây.**

### Giai đoạn 3 — đồng tác giả thời gian thực
Cần protocol/CRDT/OT đã được chứng minh (ví dụ Y.js, Automerge, hoặc engine tương đương), phân quyền + audit. **Chỉ được gắn nhãn "cùng sửa trực tiếp"** sau khi test: mất mạng giữa chừng, 2–20 người sửa cùng lúc, merge không mất nội dung. **Chưa bắt đầu xây — không tuyên bố ở giai đoạn này.**

### Ràng buộc cứng xuyên suốt 3 giai đoạn
- **Không** chuyển trực tiếp tài liệu nhạy cảm sang dịch vụ cloud AI hoặc bên thứ ba.
- Nếu tích hợp OneDrive/SharePoint/Google Drive: phải xin quyền theo **scope tối thiểu**, hiển thị rõ nhà cung cấp/chỗ lưu/chính sách dữ liệu cho người dùng thấy, xử lý được token hết hạn và API thay đổi phía nhà cung cấp.
- File XLSX/DOCX có IRM/nhãn bảo mật của Microsoft 365 có thể **không mở được** ngoài client chính chủ hỗ trợ — không né tránh bảo vệ đó (không được "giả vờ mở được" hay bẻ khóa).
- **Lựa chọn interim cho Giai đoạn 1:** NaMiOS đã có hạ tầng SMB/mạng (xem `0160-network.list.chroot`, `0720-connectivity.list.chroot`) — Dolphin (file manager) đã hỗ trợ duyệt `smb://`/`webdav://` sẵn qua KIO. Không cần gói mới để làm Giai đoạn 1 ở mức cơ bản; cần kiểm UX lock/conflict/version thật trước khi gọi là "đạt Giai đoạn 1".

---

## 6. Add-in/macro/automation và SmartAI trong hệ sinh thái này

Nhắc gọn (chi tiết đầy đủ ở kit §5–§6, không lặp lại toàn văn):
- SDK extension NaMiOffice riêng (không gọi là "Office.js"), có manifest/scope/sandbox/review/signature/revoke.
- VBA: mặc định KHÔNG thực thi; chỉ xem trong môi trường bảo vệ; KHÔNG tự động dịch bằng AI rồi chạy.
- COM/VSTO/ActiveX: không chạy native trên Linux — cần Windows có phép/app web chính thức/VM/remote desktop nếu khách hàng bắt buộc.
- Office.js add-in: phụ thuộc host Microsoft — chỉ adapter theo hợp đồng cụ thể, không gắn badge tổng quát.
- SmartAI: chạy cục bộ khi phù hợp; cloud chỉ khi **opt-in** rõ ràng; luôn có preview diff + phạm vi + xác nhận + undo; **không** để prompt nhúng trong tài liệu ra lệnh được cho AI đọc file khác hay gửi mạng; số liệu thuế/kế toán luôn cần người đối soát, AI không thay engine tính toán.

---

## 7. Tổng hợp trạng thái (để tra nhanh)

| Sản phẩm | Trạng thái | Gói/hạ tầng đã có | Đổi gì trong lần cập nhật này |
|---|---|---|---|
| **NaMiMail** | `partial` — đã đóng gói Thunderbird, chưa rebrand UI/chưa verified_on_host | `thunderbird`, `thunderbird-l10n-vi`, `hunspell-vi` | **MỚI:** `0405-mail-notes.list.chroot`; cập nhật `COMPAT-MATRIX.md`/`feature-registry.json` (ML-01, ML-02: C3→C1); cập nhật `NAMIOFFICE-APPS.md` + `OFFICE-SUITE.md` (không còn nói "chưa có app") |
| **NaMiNotes** | `not_shipped` — có chủ đích | Không gói nào; gợi ý interim `cherrytree`/`zim` (không cài sẵn) | Tài liệu hóa quyết định không ship + lý do từng app bị loại |
| **NaMiForms** | `not_shipped` | Không có | Không đổi |
| **NaMiData (dịch vụ)** | `not_shipped` | LibreOffice Base (interim, không phải dịch vụ F2 thật) | Không đổi |
| **NaMiCollab** | `not_shipped` | SMB/WebDAV qua Dolphin KIO (Giai đoạn 1, chưa kiểm UX) | Không đổi |

**Không coi tài liệu này là "đã hoàn thành NaMiOffice hệ sinh thái"** — chỉ NaMiMail nhúc nhích từ "chưa có" sang "có bản dựa trên Thunderbird, chưa verified_on_host, chưa rebrand UI". Bốn sản phẩm còn lại vẫn ở điểm xuất phát.
