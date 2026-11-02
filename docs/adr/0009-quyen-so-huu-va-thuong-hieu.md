# ADR 0009 — Quyền sở hữu và thương hiệu NaMiOS

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §26 (OWN-001/002/003); test OWN-01; backlog B038; assumptions A60–A66
- **Bổ sung đặc tả:** SUPERSET §26 (delta vòng 2)

## Bối cảnh

Đặc tả SUPERSET §26 chốt tên sản phẩm thống nhất là **NaMiOS** và ghi hai nhà sáng lập/chủ dự án là **Đỗ Chí Cường và Đỗ Bảo Nam**. Cần một quyết định rõ để: (1) không nhầm việc đặt tên là đã đăng ký bảo hộ; (2) không ngụ ý dự án sở hữu Debian/Linux/KDE/Wine; (3) xác lập cách cấp phép phần mã tự viết và hồ sơ đóng góp trước khi phát hành.

## Quyết định

1. **Thương hiệu NaMiOS** áp dụng nhất quán trong giao diện, bộ cài, tài liệu, website, gói phần mềm và báo cáo (OWN-001). Namespace code `namios_*`, CLI `namios`, path `~/.config/namios/`.
2. **Hai nhà sáng lập/chủ dự án:** Đỗ Chí Cường + Đỗ Bảo Nam (theo chỉ đạo chủ dự án). Mọi phần do dự án viết phải có hồ sơ tác giả/nguồn gốc để hai nhà sáng lập quản trị dài hạn (OWN-003).
3. **Ranh giới sở hữu (FACT):** NaMiOS chỉ sở hữu phần tự viết; KHÔNG sở hữu Debian/Linux/KDE/Wine hay tài sản bên thứ ba. About phải nêu tên NaMiOS, phiên bản, hai nhà sáng lập, pháp nhân phát hành (nếu đã xác lập), giấy phép các thành phần, liên hệ hỗ trợ và nguồn mở tương ứng (OWN-002).
4. **Giấy phép mã mới:** đề xuất **Apache-2.0** cho mã tự viết, **phải kiểm tương thích** với giấy phép mọi thành phần phụ thuộc trước khi chốt (không mặc định tương thích; rà copyleft/điều kiện khác).
5. **Hồ sơ pháp lý:** hợp đồng lao động/cộng tác, contributor agreement, chuyển giao quyền và quyền sử dụng tên NaMiOS phải xác lập TRƯỚC phát hành; cần chủ thể pháp lý phát hành. Claude KHÔNG soạn/ký văn bản ràng buộc pháp lý thay chủ dự án — chỉ soạn khung/template để chủ dự án + luật sư hoàn thiện.
6. **Tra cứu trademark/domain** "NaMiOS" phải thực hiện và GHI trạng thái trước công bố rộng rãi; việc đặt tên trong tài liệu không tự xem là đã đăng ký bảo hộ (OWN-002).
7. Không dùng tên Windows trong thương hiệu HĐH; chỉ dùng khi mô tả khả năng tương thích. Không dựng huy hiệu/logo gợi chứng nhận của Microsoft/MISA.

## Lý do

- Tách rõ ba điều dễ bị trộn: *đặt tên* ≠ *đăng ký nhãn hiệu* ≠ *sở hữu mã upstream*.
- Giấy phép mã mới phải tương thích toàn chuỗi phụ thuộc, nếu không sẽ không phân phối hợp pháp được (liên quan LIC-* và ADR nền tảng về quyền phân phối).
- Quản trị dài hạn của hai nhà sáng lập cần hồ sơ tác giả/đóng góp từ sớm, tránh tranh chấp quyền về sau.

## Hệ quả

- About + trang giấy phép là deliverable bắt buộc trước G3; thiếu pháp nhân → ghi "pháp nhân: chưa xác lập", không bịa.
- Kết quả tra cứu trademark/domain là đầu vào quyết định có được dùng tên công khai hay không; nếu trùng/bị chặn → phải xử lý trước phát hành.
- Mọi marketing/About phải qua rà từ ngữ ownership để không ngụ ý sở hữu upstream hay "100% tương thích".

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Áp dụng brand/namespace/CLI/path và soạn **khung** About, bảng license thành phần, template contributor agreement/hồ sơ tác giả: **làm được ở M0/M1** (tài liệu + chuỗi text trong code).
- **Dữ liệu thật** (tên pháp nhân, kết quả tra cứu trademark/domain, nội dung hợp đồng ký kết) cần chủ dự án + luật sư → **BLOCKED** chờ chủ dự án; đánh dấu `blocked_external_dependency`.

## Spike cần làm + điều kiện chấp nhận

- **Spike S-OWN-1:** soạn khung About (tên/version/founders/pháp nhân-TBD/giấy phép thành phần/liên hệ/nguồn mở) + kiểm text không có câu ngụ ý sở hữu upstream hay chứng nhận nhà nước.
- **Spike S-OWN-2:** rà tương thích giấy phép — liệt kê license mọi dependency, đối chiếu với Apache-2.0 cho mã mới; báo xung đột (nếu có) thay vì mặc định tương thích.
- **Spike S-OWN-3:** checklist tra cứu trademark + domain (ghi trạng thái, ngày, nguồn tra cứu), chờ chủ dự án xác nhận pháp nhân.
- **Điều kiện chấp nhận:** không chỗ nào trong sản phẩm/tài liệu tuyên bố NaMiOS sở hữu Debian/Linux/KDE/Wine; không coi đặt tên là đã bảo hộ; giấy phép mã mới chỉ chốt sau khi rà tương thích; test **OWN-01** ghi founders đúng và không claim upstream IP.
