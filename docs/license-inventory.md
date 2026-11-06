# License Inventory — NaMiOS

- **Trạng thái:** DESIGN (07/11/2026) — khung kiểm kê giấy phép, **mọi ô là "cần xác minh"**; chưa có luật sư/người có thẩm quyền pháp lý xác nhận bất kỳ dòng nào trong bảng.
- **Nguồn:** Phụ lục 10 (N10-054 "Quyền và giấy phép") và Phụ lục 11 (APP11-034 "Phân phối có giấy phép", APP11-033 "Chống mạo danh thương hiệu").
- **Liên quan:** `docs/backlog/N10-backlog.md#N10-054`, `docs/backlog/APP11-backlog.md#APP11-034`, `docs/release-gates.md`, ADR 0009 (quyền sở hữu và thương hiệu), ADR 0013 (đánh giá engine Office).

## 1. Mục đích và giới hạn

Trước khi đóng gói/phân phối bất kỳ ISO hay cập nhật Essentials nào, NaMiOS cần biết: mỗi thành phần trong gói dùng giấy phép gì, có nghĩa vụ công bố mã nguồn/notice nào, và tên/logo của bên thứ ba có được dùng hợp lệ hay không. Tài liệu này **không phải kết quả rà soát pháp lý** — nó là khung để điền, với từng hàng ở trạng thái mặc định `cần xác minh` cho tới khi có người có thẩm quyền (luật sư hoặc người chủ dự án được ủy quyền) xác nhận và ký.

**Không suy diễn:** một dòng xuất hiện trong bảng không có nghĩa là thành phần đó đã được phép bundle, đã được rà soát, hoặc đã có xác nhận từ vendor. "Chưa xác minh" là trạng thái mặc định an toàn — khi nghi ngờ, coi như **chưa được phép phân phối** cho tới khi xác nhận ngược lại.

## 2. Khung kiểm kê theo nhóm thành phần

| Nhóm | Ví dụ thành phần (cần khảo sát cụ thể theo build) | Loại giấy phép dự kiến (chưa xác minh) | Nghĩa vụ cần kiểm | Trạng thái |
| --- | --- | --- | --- | --- |
| Linux distribution (nền) | Debian 13 amd64 (ADR 0002) và các gói hệ thống đi kèm | Debian: hỗn hợp (DFSG, nhiều gói GPL/LGPL/MIT/BSD/Apache tùy package) | Mỗi gói distro có license riêng; không giả định "cả distro một giấy phép" | cần xác minh |
| Wine / compatibility layer | Wine runtime, Wine-staging/patch nếu dùng | LGPL (cần xác minh version/phân nhánh cụ thể dùng trong NaMiOS) | Nghĩa vụ LGPL khi link động/tĩnh; nếu NaMiOS sửa mã Wine (Giai đoạn B/C theo roadmap PL08) phải công bố thay đổi theo điều khoản LGPL | cần xác minh |
| Office engine | Ứng viên dẫn đầu: LibreOffice (ADR 0013, chưa chốt) | MPL 2.0 / LGPL v3 (nhiều thành phần có license khác nhau — theo cảnh báo ADR 0013) | ADR 0013 mục 3 đã lập checklist riêng, **chưa mục nào xong**; không dùng tên thương mại riêng cho tới khi checklist đó hoàn tất | cần xác minh (xem ADR 0013) |
| Font | Font tiếng Việt đi kèm Office/desktop (chưa chốt danh sách cụ thể) | Thường SIL OFL hoặc tương đương (cần xác minh từng font) | Một số font có điều khoản hạn chế đổi tên/bán lại; kiểm trước khi đặt làm font mặc định | cần xác minh |
| Codec | Codec audio/video cho browser/trình phát (ví dụ H.264, AAC nếu dùng) | Một số codec có bằng sáng chế/phí bản quyền riêng ngoài giấy phép phần mềm | Phân biệt "mã nguồn mở" và "miễn phí bản quyền sáng chế" — không phải lúc nào cũng giống nhau | cần xác minh |
| Firmware | Firmware thiết bị (Wi-Fi, GPU, v.v. — `firmware-linux-nonfree` hoặc tương đương) | Thường proprietary-redistributable (điều khoản riêng từng vendor) | Firmware non-free có điều khoản phân phối lại riêng, khác license của distro base | cần xác minh |
| Trademark / thương hiệu bên thứ ba | Tên/logo Zalo, YouTube, Facebook, WhatsApp, Maps, TikTok, Office, Wine, Debian/KDE | Trademark riêng từng chủ sở hữu, KHÔNG phải license phần mềm | Theo APP11-033: mỗi logo có trạng thái `approved/pending/replace_with_text`; mặc định `pending` cho tới khi có xác nhận quyền dùng | cần xác minh (mặc định `pending`) |
| Ứng dụng bên thứ ba (bundled) | Bất kỳ binary/app nào NaMiOS cân nhắc bundle sẵn ngoài distro repo | Theo từng vendor — không giả định được phép bundle chỉ vì tải công khai | APP11-034: chỉ bundle khi điều khoản cho phép rõ ràng; nếu không, dùng link/hướng dẫn tự cài | cần xác minh |
| Windows fallback (VM/RemoteApp) | Bản quyền Windows + ứng dụng Windows chạy trong route N10-028 | License Windows/app thương mại của bên thứ ba, KHÔNG thuộc NaMiOS | NaMiOS không cấp hay kèm theo license Windows; người dùng/tổ chức phải tự có quyền dùng | cần xác minh theo từng triển khai (không áp dụng ở cấp distro) |

## 3. Nghĩa vụ công bố mã nguồn/notice

- Với mọi thành phần GPL/LGPL/MPL được **phân phối** (không chỉ dùng nội bộ), cần xác định: (a) mã nguồn tương ứng có kèm theo hoặc có offer-to-provide hợp lệ; (b) notice/copyright giữ nguyên trong bản phân phối; (c) nếu NaMiOS **sửa đổi** mã nguồn của thành phần đó, nghĩa vụ công bố phần sửa đổi theo đúng điều khoản license gốc.
- Hiện tại (07/11/2026): NaMiOS ở Giai đoạn A cho Office (đóng gói nguyên bản, không fork — ADR 0013) và chưa có bản ISO nào được đóng gói thật; do đó nghĩa vụ công bố mã nguồn **chưa phát sinh cụ thể** nhưng phải được thiết kế trước khi có bản phát hành đầu tiên, không phải xử lý "khi bị hỏi".

## 4. Quy trình kiểm trước khi đóng gói (checklist khung, chưa chạy)

- [ ] Liệt kê đầy đủ danh sách gói/thành phần trong manifest build (SBOM) — phụ thuộc N10-004 (gói sản phẩm có thể tái tạo), hiện ở trạng thái `blocked-infra` (cần build host ISO thật).
- [ ] Với mỗi thành phần: tra license từ metadata gói distro (hoặc nguồn chính thức nếu bundle riêng) — chưa chạy.
- [ ] Đối chiếu danh sách trademark (Zalo/YouTube/Facebook/WhatsApp/Maps/TikTok/Office/Debian/KDE/Wine…) với trạng thái `approved/pending/replace_with_text` theo APP11-033 — chưa có mục nào `approved`.
- [ ] Xác nhận không có binary nào bị bundle mà thiếu quyền phân phối lại (APP11-034) — chưa chạy vì chưa có ISO thật để kiểm.
- [ ] Ký xác nhận bởi người có thẩm quyền (chủ dự án hoặc luật sư được ủy quyền) trước khi gắn gate RG liên quan trong `docs/release-gates.md` thành "xanh".

## 5. Những điều KHÔNG được suy diễn từ tài liệu này

- Bảng ở mục 2 là **khung phân loại**, không phải kết quả audit; "loại giấy phép dự kiến" là suy đoán hợp lý dựa trên hiểu biết chung về các dự án đó, **không thay thế việc tra cứu license file thật của từng gói/version cụ thể được dùng**.
- Không coi "có mặt trong bảng" là "đã được phép phân phối". Trạng thái mặc định của mọi dòng là `cần xác minh`.
- Tài liệu này không phải tư vấn pháp lý; quyết định cuối cùng về việc có được bundle/đặt tên thương mại hay không cần người có thẩm quyền pháp lý xác nhận, đồng nhất với ADR 0009 và ADR 0013.
