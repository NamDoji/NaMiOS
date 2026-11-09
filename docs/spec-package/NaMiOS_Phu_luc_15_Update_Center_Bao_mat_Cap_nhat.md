# NaMiOS — Phụ lục 15: Update Center và bảo mật chuỗi cập nhật

**Ngày:** 09/11/2026 · **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam  
**Trạng thái:** đặc tả độc lập để phát triển; không khẳng định NaMiOS đã có dịch vụ cập nhật hay bản ISO. Tiếp nối phụ lục 13, 14 và bộ Brand/UI/UX v1.0.

## 1. Mục tiêu và quyết định sản phẩm

Khi có phiên bản mới, mọi máy NaMiOS được hỗ trợ phải **biết có bản cập nhật, hiểu lợi ích/rủi ro, chọn cách cài và kiểm tra được kết quả**. Người dùng cá nhân có thể bật tự động cập nhật; tổ chức có thể đặt lịch và phân nhóm máy. Một bản cập nhật bị lỗi phải có đường trở lại trạng thái khởi động được, không làm mất tệp cá nhân. Bảo mật “xuất sắc” là một hệ thống có khóa, chữ ký, xác thực metadata, kiểm thử, phát hành theo nhóm, phát hiện bất thường và quy trình ứng phó; không có lời hứa tuyệt đối rằng sẽ không bao giờ bị tấn công.

**Quyết định kiến trúc:** Update Center là giao diện; **Update Service** có quyền giới hạn mới kiểm tra, tải, xác thực, staged-install, khởi động lại và rollback. SmartAI chỉ giải thích, chẩn đoán và đề xuất lựa chọn, không được ký gói, sửa metadata, vượt policy hay tự cài mã từ URL. Cần ADR chọn nền Linux và cơ chế OS image/transactional update sau khi kiểm kê repo; OSTree/rpm-ostree là phương án tham khảo về deployment và rollback, không mặc định là stack đã chọn [1].

## 2. Phân loại cập nhật và đường tin cậy

| Loại | Ví dụ | Nguồn và kiểm tra | Cần khởi động lại? | Chính sách mặc định đề xuất |
| --- | --- | --- | --- | --- |
| **OS nền** | kernel, system libraries, desktop shell, IME | Repo NaMiOS đã xác thực, metadata có phiên bản/hash/chữ ký | Thường có | Tự tải; cài trong cửa sổ phù hợp; báo trước khi restart. |
| **Bản vá bảo mật** | lỗ hổng browser, TLS, service hệ thống | Kênh security có chữ ký và mức độ ảnh hưởng | Tùy thành phần | Ưu tiên cao, thông báo rõ; tự cài khi an toàn, restart có lịch/nhắc. |
| **Ứng dụng** | browser, Office, App Center | Repo/publisher đã được tin cậy; runtime và quyền mới được xem xét | Thường không | Tự cập nhật mặc định nếu không thêm quyền đáng kể. |
| **SmartAI** | model, prompt template, policy, adapter, knowledge pack | Ký và pin từng phần, kiểm schema, regression; policy tách khỏi model | Thường không | Staged; tự rollback khi lỗi; model không cấp thêm quyền. |
| **Firmware/BIOS/thiết bị** | máy, dock, radio | Vendor/LVFS/fwupd hoặc nguồn OEM hợp lệ; kiểm model, pin, nguồn điện | Thường có | Chỉ đề xuất và xin xác nhận riêng; không chạy khi pin/nguồn không đạt. |
| **Driver/backend thiết bị** | printer application, firmware đi kèm | Repo/nhà sản xuất đã xác minh; test model cụ thể | Có thể | Cài theo model và thông báo rủi ro in/scan. |
| **Recipe Wine/.NET** | prefix/runtime/app compatibility | Recipe đã review, đúng app hash/version/workflow | Không nhất thiết | Thử trong capsule; không đổi profile của app đang dùng nếu chưa kiểm. |

**App bên thứ ba:** cài sẵn shortcut web Zalo, YouTube, Facebook, TikTok, Maps, WhatsApp chỉ mở dịch vụ chính thức; NaMiOS không tuyên bố tự cập nhật binary của họ nếu không quản lý gói đó. Với phần mềm thương mại, giữ nguồn, giấy phép, phiên bản và cơ chế cập nhật của nhà phát hành. Không phân phối lại bộ cài có bản quyền khi chưa được phép.

## 3. Chế độ người dùng và mặc định dễ hiểu

Trong **Cài đặt → Cập nhật & bảo mật → Cách cập nhật**, hiển thị 4 lựa chọn:

1. **Thông báo, tôi tự quyết định:** kiểm tra theo lịch; hiện bản mới, mức quan trọng, kích thước, restart và nút Cài. Người dùng vẫn có nút Kiểm tra ngay.
2. **Tự tải, hỏi trước khi cài:** đề xuất mặc định cho máy mới trong giai đoạn pilot. Chỉ tải khi mạng/ổ đĩa phù hợp; cài khi người dùng đồng ý.
3. **Tự cài bản an toàn:** cập nhật ứng dụng và bản vá không cần reboot sau khi xác thực; OS được staged, hỏi/lên lịch restart. Không cài firmware tự động.
4. **Tự động theo lịch của tôi:** chọn giờ yên tĩnh, ngày, giới hạn mạng tính phí, chỉ khi cắm sạc và thời hạn hoãn restart. OS cài khi preflight đạt; restart chỉ trong cửa sổ đã chọn, có cảnh báo và khả năng hoãn khi còn công việc chưa lưu. Firmware luôn có xác nhận riêng.

Mỗi chế độ có mô tả ngắn “máy sẽ làm gì”, “khi nào restart”, “có dùng dữ liệu di động không”; thay đổi áp dụng rõ cho OS/app/AI/firmware, không nút “tự động tất cả” mơ hồ. Nếu người dùng tắt tự cài, vẫn kiểm tra và **thông báo bảo mật**; máy quản lý bởi tổ chức ghi rõ chính sách do IT đặt và nút liên hệ. Cho **Tạm dừng** có ngày kết thúc hiển thị, không im lặng vô thời hạn. Với bản vá khẩn cấp, ưu tiên thông báo nhiều cấp, giải thích lý do và thời hạn khuyến nghị; không phá tệp chưa lưu bằng restart bất ngờ.

### 3.1 Trạng thái UX và nội dung thông báo

`Đang kiểm tra → Có bản mới → Đang tải → Đã xác thực → Sẵn sàng cài → Đang cài → Cần khởi động lại → Đang kiểm tra sau khởi động → Hoàn tất / Đã khôi phục / Cần hỗ trợ`.

- **Có bản mới:** “NaMiOS 1.1 đã sẵn sàng. Bản này sửa lỗi Wi‑Fi và tăng độ an toàn. Dung lượng 1,2 GB; cần khởi động lại. [Xem thay đổi] [Cài tối nay] [Để sau]”. Các con số/phiên bản ở đây là *minh họa UI*, không phải bản phát hành có thật.
- **Tải thất bại:** “Chưa tải xong bản cập nhật. Mạng bị ngắt ở 68%; các tệp đã tải hợp lệ sẽ được giữ để tiếp tục. [Thử lại] [Xem kết nối]”. Chỉ nói 68% nếu hệ thống thực sự có số liệu.
- **Chữ ký không hợp lệ:** “Bản cập nhật không vượt qua kiểm tra bảo mật. NaMiOS đã chặn cài đặt; máy vẫn dùng phiên bản hiện tại. [Xem chi tiết] [Báo sự cố]”. Không có nút “Bỏ qua kiểm tra”.
- **Đã staged:** “Bản cập nhật đã chuẩn bị xong. Tệp của anh chưa bị thay đổi; chọn thời điểm khởi động lại.” Không nói “đã cập nhật xong” khi chưa boot bản mới.
- **Sau rollback:** “Bản mới không khởi động ổn định. NaMiOS đã quay về phiên bản trước. Tệp cá nhân còn nguyên theo kiểm tra hiện có; xem báo cáo để xác nhận ứng dụng/dữ liệu quan trọng.” Tránh bảo đảm tuyệt đối khi chưa kiểm dữ liệu người dùng.

Thông báo ở desktop có thể truy lại trong Update Center, không spam sau mỗi lần quét, có mức khẩn cấp và lịch sử. Screen reader đọc tên, trạng thái, nút. Theo bộ UI/UX v1.0, không chỉ dùng màu đỏ/xanh và không dùng “Đã xảy ra lỗi” khi đã biết nguyên nhân.

## 4. Bảo mật chuỗi cung ứng cập nhật

**Nguồn tin cậy:** client có trust root được cài và bảo vệ từ bản ISO; máy không tin chỉ vì TLS hoặc server trả 200. Mỗi payload phải khớp danh tính sản phẩm, channel, phiên bản, kiến trúc, hash, kích thước và chữ ký/metadata đã xác thực. Thiết kế metadata theo các vai trò/threshold, hạn sử dụng và chống rollback/freeze/đổi gói tương tự TUF; TUF nêu rõ rủi ro rollback, freeze và quản trị khóa [2]. Dùng triển khai/chứng thư được kiểm định thay vì tự viết thuật toán chữ ký.

**Quản lý khóa:** root/targets offline hoặc HSM với quorum; khóa phát hành CI tách quyền và có hạn; người xây gói không tự phê duyệt/phát hành một mình; rotation/revocation có quy trình; thiết bị nhận danh sách thu hồi và chặn metadata quá hạn. Thực hành định kỳ tình huống khóa hoặc CDN bị xâm phạm. NTP sai/offline phải có xử lý “không xác minh được thời hạn” thay vì âm thầm bỏ kiểm tra.

**Build và phát hành:** source pin, dependency lock, SBOM, quét lỗ hổng, kiểm giấy phép, build có provenance; ưu tiên build tái tạo được và so sánh hash ở môi trường tách biệt. Kiểm thử unit/integration/hardware, ký sau khi gate đạt; lưu artifact bất biến và release notes có CVE/thiết bị bị ảnh hưởng khi phù hợp. Tách kênh `testing → pilot → stable → security hotfix`, rollout theo nhóm/đợt, tự dừng nếu crash/boot failure/driver regression vượt ngưỡng. Không để hệ thống telemetry thu nội dung tài liệu của người dùng.

**Máy nhận bản:** quyền tối thiểu, storage riêng cho cache, chống thay symlink/path traversal, kiểm lại sau tải và trước apply, bảo vệ cấu hình updater, không thực thi script từ metadata tùy ý, không cho AI/ứng dụng thường sửa channel/policy. Có thể cân nhắc Secure Boot, measured boot, verity và mã hóa theo phần cứng pilot; không ghi “đã bảo vệ” nếu chưa triển khai/kiểm thử.

**Firmware:** đường cập nhật và phục hồi tách OS; kiểm danh tính model, trạng thái pin/nguồn, tương thích, chữ ký và yêu cầu vendor. Không hứa rollback firmware nếu thiết bị không hỗ trợ. fwupd/LVFS có cơ chế metadata ký và ngưỡng pin, nhưng tương thích từng thiết bị cần kiểm thật [3].

## 5. Cập nhật nguyên tử, rollback và dữ liệu

Ưu tiên OS dạng deployment có thể boot lại phiên bản trước, hoặc cơ chế transactional tương đương. Trình cài **staged** vào phiên bản mới thay vì ghi nửa vời lên hệ đang chạy. Boot health check cần xác định: kernel lên, login được, ổ dữ liệu mount, mạng cơ bản, UI không crash lặp, dịch vụ update phản hồi. Boot failure hoặc health fail trong ngưỡng đã định → tự chọn bản trước; không xóa deployment cũ cho tới khi bản mới qua cửa kiểm. OSTree/rpm-ostree có mô hình rollback tham khảo, nhưng lựa chọn cuối cùng phụ thuộc distro và định dạng gói [1].

**Rollback OS không đồng nghĩa rollback dữ liệu cá nhân.** Trước cập nhật có migration schema hoặc thay dữ liệu ứng dụng, cần backup/snapshot được kiểm tra khôi phục; migration phải versioned, có thử dry-run, tương thích tiến/lùi hoặc kế hoạch phục hồi riêng. Cảnh báo trước khi update làm file/database không mở được trên bản cũ. Không xóa file người dùng khi cache đầy; preflight dung lượng cần đủ cho tải, staged deployment, backup và rollback. Với Windows dual boot, không tự sửa phân vùng Windows ngoài phạm vi boot được thiết kế và kiểm thử.

**Mất điện/đứt mạng:** tải tiếp theo chunk/hash; verify toàn bộ trước apply; không reboot khi payload thiếu; nếu mất điện lúc chuyển boot thì có bản boot cũ. Test trên 5 máy pilot, gồm máy cũ, NVMe/SATA, mã hóa, dual boot, mạng chậm và pin yếu.

## 6. SmartAI trong Update Center

SmartAI đọc **metadata và trạng thái đã lọc**: bản cũ/mới, loại update, release notes, thiết bị bị ảnh hưởng, lỗi xác thực, lịch sử thất bại, preflight. Nó giải thích bằng tiếng Việt, ví dụ “Bản này sửa lỗi Bluetooth trên model của anh; máy cần restart, anh đang có tài liệu chưa lưu.” AI có thể đề xuất “Cài tối nay”, “Sao lưu trước”, “Hỏi IT”. Mọi thao tác thực tế đi qua Update Service và policy; AI không tự thay đổi danh sách trust, tắt signature check, cài firmware, xóa bản cũ hay áp dụng patch chưa phát hành.

**Khi update lỗi**, AI nhận mã có cấu trúc, tối đa 3 giả thuyết có bằng chứng và bước xử lý an toàn; phân biệt lỗi mạng, thiếu dung lượng, sai chữ ký, không tương thích máy, lỗi boot. Nếu `SIGNATURE_INVALID`, `METADATA_EXPIRED`, `REVOKED`, `HASH_MISMATCH` → **chặn và báo an ninh**, không có “thử nguồn khác” không tin cậy. Nếu AI/model offline, Update Center và khôi phục vẫn hoạt động bình thường. AI không tự kết luận “máy an toàn tuyệt đối” từ một bản vá đã cài.

## 7. Hợp đồng dữ liệu và mã lỗi

```json
{
  "schema_version": 1,
  "update_id": "opaque-release-id",
  "component": "os|app|ai|firmware|driver|recipe",
  "channel": "stable",
  "target_build": "unresolved",
  "architecture": "x86_64",
  "metadata_version": 1,
  "payload_hash": "sha256:...",
  "signature_status": "verified|failed|unknown",
  "preflight": {"storage": "pass", "power": "pass", "backup": "pass"},
  "state": "available|downloading|verified|staged|reboot_pending|boot_check|completed|rolled_back|blocked",
  "error_code": null,
  "rollback_target": "opaque-deployment-id",
  "user_policy": "auto_download_ask_install",
  "correlation_id": "opaque-id"
}
```

Schema là minh họa hợp đồng, không phải metadata ký trực tiếp. Trong bản triển khai phải version hóa, validate mọi field, chống replay, dùng enum có chuyển trạng thái hợp lệ, idempotency, journal để tiếp tục sau reboot và log không chứa dữ liệu riêng. Máy không tự nâng `completed` chỉ vì download/install tool trả success.

| Mã | Nguyên nhân đã xác định | UI cần nói và hành động |
| --- | --- | --- |
| `UPD-001` | Không tới được server/captive portal | “Chưa kiểm tra được bản mới vì mạng”; mở trạng thái mạng, thử lại. |
| `UPD-002` | Không đủ dung lượng cho staged/rollback | “Cần thêm X GB”; xem mục chiếm dung lượng, không tự xóa tệp cá nhân. |
| `UPD-003` | Hash hoặc chữ ký không hợp lệ | Chặn cài, báo an ninh, giữ bản hiện tại; không cho bypass. |
| `UPD-004` | Metadata hết hạn/clock sai | Nêu bước kiểm giờ và nguồn metadata; không bỏ kiểm để tiếp tục. |
| `UPD-005` | Máy không đúng model/architecture | Chặn bản không phù hợp, ghi mã thiết bị và đề xuất bản đúng nếu có. |
| `UPD-006` | Pin/nguồn không đạt cho firmware | Hoãn firmware, hướng dẫn cắm sạc và ngưỡng vendor. |
| `UPD-007` | App đang hoạt động/tệp chưa lưu | Hoãn restart, nêu app cần lưu/đóng; không ép đóng âm thầm. |
| `UPD-008` | Health check sau boot thất bại | Tự rollback nếu có, hiện báo cáo/đường cứu hộ. |
| `UPD-009` | Bản mới bị thu hồi | Dừng rollout/cài, giữ hoặc rollback theo policy, giải thích rõ. |
| `UPD-010` | Migration dữ liệu không an toàn | Chặn update, yêu cầu backup và kế hoạch chuyển đổi, chuyển hỗ trợ. |

## 8. Quản trị nhiều máy và phát hành theo đợt

Tổ chức có policy theo nhóm `pilot/standard/critical`, cửa sổ bảo trì, mạng, trì hoãn và bắt buộc báo cáo. Không dùng một update global đẩy ngay tới toàn bộ trường học/văn phòng. Máy đã offline nhiều tháng phải kiểm chain metadata, bản trung gian/migration và trạng thái khóa trước khi lên bản mới. Dashboard chỉ ghi build, update state, crash/boot health, phần cứng giả danh và mã lỗi; **không thu nội dung file, địa chỉ web hay tên tài liệu**. Người dùng thấy “Thiết bị do tổ chức quản lý” và ai có thể thay đổi lịch; IT có biện pháp thu hồi/halt rollout, phương án khôi phục USB ngoại tuyến đã ký.

**Phát hành khẩn:** có owner, mức nghiêm trọng, đối tượng bị ảnh hưởng, bản sửa tối thiểu, test rút gọn nhưng bắt buộc chữ ký và rollback, thông báo theo kênh dự phòng. Không biến “khẩn” thành quyền bỏ kiểm chữ ký, bypass QA cốt lõi hoặc reboot bất ngờ.

## 9. Bộ kiểm thử và cổng phát hành

| Nhóm thử | Ca tối thiểu | Điều kiện đạt |
| --- | --- | --- |
| Luồng người dùng | 4 chế độ, đổi chế độ, tạm dừng, restart lịch, mạng tính phí, pin | UI hiển thị và thực thi đúng lựa chọn; không cài/reboot trái dự kiến. |
| Bảo mật | Gói giả chữ ký, hash sai, metadata cũ/hết hạn, repo bị thay, khóa thu hồi, mirror độc hại | 100% trường hợp bị chặn, có mã lỗi và không bypass. |
| Độ tin cậy | Mất mạng, đầy ổ, kill updater, mất điện ở từng pha, boot fail, rollback, dual boot | Máy boot bản cũ hoặc recovery; dữ liệu thử còn hash đúng; không có bản nửa cài. |
| Tương thích | Kernel/GPU/Wi‑Fi, Bluetooth, 3 máy in/MFP, IME, Office/Wine, app .NET đã chứng nhận | Không có regression P0; nếu có thì dừng rollout. |
| AI | Model tắt, prompt injection trong release notes, gợi ý bỏ chữ ký, thao tác firmware | AI không cấp quyền, không nói hoàn tất sai; Update Center vẫn dùng được. |
| Vận hành | 20 máy pilot chia ring, kill switch, thu hồi bản, máy offline lâu ngày | Trạng thái đúng từng máy; rollback một ring không ảnh hưởng ring khác. |

**Gate trước stable:** không phát hành nếu update có thể làm mất tệp, không boot/recovery được trên máy đã chứng nhận, signature verifier có bypass, rollback target bị xóa sớm, firmware thiếu kiểm model/power, hoặc SmartAI có thể cài gói không ký. Mỗi bản phát hành có changelog tiếng Việt, danh sách model/app đã thử và vấn đề còn mở. Đo tỷ lệ update thành công, rollback, boot fail, thời gian hồi phục và cập nhật chậm trên máy offline; ngưỡng chốt sau pilot, không bịa số hiệu năng khi chưa có máy.

## 10. Lộ trình cho Claude Code

**U15-A — Kiểm kê/ADR:** xác định distro, package manager, image/transaction model, bootloader, backup, app channel, firmware path; so sánh lựa chọn và chốt kiến trúc. Tạo threat model và danh mục khóa/owner. Nếu chưa có repo/ISO, dựng prototype với giả lập state, không tuyên bố đã có updater thật.

**U15-B — Update Center MVP:** UI 4 chế độ, check bản mới, changelog, download resume, metadata verify, preflight storage/power/network, log mã lỗi và thông báo tiếng Việt. Test server giả có signed metadata và các ca phản công. Không dùng production key cho test.

**U15-C — Transaction/rollback:** staged deployment, boot health, automatic rollback/recovery, migration guard, backup proof; chạy fault injection trên VM rồi 5 máy pilot. Bản test phải chứng minh khôi phục cả khi mất điện.

**U15-D — Mở rộng:** app/AI/firmware phân kênh, ring rollout, IT policy, revocation, SmartAI giải thích; diễn tập khóa bị lộ/CDN bị thay và bản lỗi Wi‑Fi. Ký release chỉ sau QA, SBOM/provenance và phê duyệt.

**Mỗi mốc bàn giao:** mã nguồn, build commands, giao diện chạy được, kết quả test pass/fail, log đã che, phiên bản thiết bị, video rollback, rủi ro và danh sách chưa làm. Không biến câu lệnh trong tài liệu thành cam kết chức năng đã chạy.

### Lệnh giao Claude Code nguyên văn

> Đọc phụ lục 13, 14, Brand/UI/UX v1.0 và phụ lục 15. Kiểm kê repo NaMiOS trước, báo cơ chế update/backup/boot/firmware thật hiện có. Viết ADR và threat model, chọn giao diện service theo nền Linux hiện tại. Triển khai U15-A rồi U15-B thành mã có thể chạy và test gói giả hợp lệ/sai chữ ký/metadata cũ. Không viết updater giả luôn trả “thành công”; không bỏ chữ ký; không cấp root shell cho SmartAI. Sau đó làm U15-C staged update, boot health và rollback bằng VM/fault injection, rồi U15-D theo ring trên máy thật. UI cho người dùng 4 chế độ, thông báo tiếng Việt, lịch restart không phá việc chưa lưu. Kết thúc từng mốc bằng commit, artifact, test, bằng chứng máy thật, blocker. Không phát hành ISO công khai khi gate chưa đạt.

## 11. Nguồn kỹ thuật đối chiếu (09/11/2026)

[1] OSTree atomic rollbacks, rpm-ostree administration: https://ostreedev.github.io/ostree/atomic-rollbacks/ ; https://coreos.github.io/rpm-ostree/administrator-handbook/  
[2] The Update Framework, security threats and metadata roles: https://theupdateframework.io/docs/security/ ; https://theupdateframework.io/docs/metadata/  
[3] fwupd metadata signing and battery requirements: https://fwupd.github.io/libfwupdplugin/only-trusted.html ; https://fwupd.github.io/libfwupd/method.Client.get_battery_threshold.html  
[4] Flatpak updates and repositories: https://docs.flatpak.org/en/latest/using-flatpak.html ; https://docs.flatpak.org/en/latest/repositories.html  
[5] Reproducible Builds quickstart: https://reproducible-builds.org/docs/getting-started/

Các nguồn này minh họa cơ chế có sẵn và rủi ro thực tế; lựa chọn của NaMiOS phải căn cứ repo, đội vận hành và thử nghiệm. **Bản cập nhật an toàn là một chu trình phát hành–xác thực–cài–kiểm–khôi phục, không chỉ là nút “Update”.**
