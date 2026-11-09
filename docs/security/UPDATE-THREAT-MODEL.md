# NaMiOS — Mô hình đe dọa chuỗi cập nhật (Update Threat Model)

**Ngày:** 09/11/2026 · **Mốc:** Phụ lục 15 §4/§7 — **U15-A**. · **Trạng thái:** `specified` (thiết kế; chưa có Update Service, chưa máy thật, chưa khóa thật).
**Đối chiếu:** `docs/spec-package/NaMiOS_Phu_luc_15_Update_Center_Bao_mat_Cap_nhat.md` (§4 Bảo mật chuỗi cung ứng, §7 mã lỗi), `docs/adr/ADR-0017-update-service-architecture.md`, `docs/adr/0007-cap-nhat-bao-ve-metadata.md`, `docs/adr/ADR-0014-update-recovery-strategy.md`, `docs/security/UPDATE-KEY-CATALOG.md`, `docs/spec-package/U15-INVENTORY.md`.

## 0. Phạm vi và lời cảnh báo trung thực

Tài liệu này mô tả **tài sản cần bảo vệ, gốc tin cậy, kẻ tấn công, và biện pháp giảm thiểu** cho chuỗi cập nhật NaMiOS (OS/app/AI/firmware). Đây là **mô hình đe dọa ở mức thiết kế**: phần lớn biện pháp vẫn là `specified` hoặc dựa trên cơ chế upstream (apt GPG) chưa cấu hình riêng NaMiOS. Xem `docs/spec-package/U15-INVENTORY.md` cho trạng thái thật từng cơ chế.

> **Không có lời hứa an toàn tuyệt đối.** Bảo mật "xuất sắc" (PL15 §1) là một **chu trình** khóa–chữ ký–xác thực metadata–kiểm thử–phát hành theo nhóm–phát hiện bất thường–ứng phó, **không** phải một tuyên bố "không bao giờ bị tấn công". Mọi biện pháp dưới đây **giảm xác suất và thiệt hại**, không triệt tiêu rủi ro. NaMiOS **chưa** test trên máy thật nên hiệu lực thực tế của các biện pháp **chưa được chứng minh**.

## 1. Tài sản cần bảo vệ (Assets)

| # | Tài sản | Vì sao quý | Hậu quả nếu mất |
| --- | --- | --- | --- |
| A1 | **Tính toàn vẹn + xác thực của payload cập nhật** (gói OS/app/AI, metadata) | Quyết định mã nào chạy quyền cao trên máy người dùng | Thực thi mã độc quyền root trên diện rộng |
| A2 | **Gốc tin cậy trên client** (trust root cài từ ISO) | Là điểm neo để xác minh mọi thứ | Nếu bị thay → tin gói giả như thật |
| A3 | **Khóa ký** (root/targets/snapshot/timestamp/CI — xem key-catalog) | Ai giữ khóa thì ký được bản "hợp lệ" | Ký bản độc, giả danh nhà phát hành |
| A4 | **Khả năng khởi động + khôi phục** (boot, snapshot Timeshift, GRUB recovery) | "Update lỗi vẫn boot/vào recovery" (ADR 0014) | Máy không boot → người dùng quay về Windows (PL13 §1) |
| A5 | **Dữ liệu cá nhân `/home`** (U13-03) | Mất là mất niềm tin | Mất tệp khi rollback/migration |
| A6 | **Cấu hình updater + channel/policy** | Điều khiển máy nhận bản nào, khi nào | Hạ chuẩn an toàn, ép bản độc/cũ |
| A7 | **Tính sẵn sàng của bản vá bảo mật** | Chậm vá = hở lỗ hổng đã biết | Bị khai thác lỗ hổng cũ (freeze attack) |
| A8 | **Quyền riêng tư của telemetry** (dashboard §8) | Không được thu nội dung tài liệu/web | Rò rỉ dữ liệu người dùng |

## 2. Gốc tin cậy (Trust Root)

- **Client KHÔNG tin chỉ vì TLS hay server trả 200** (PL15 §4). Tin cậy neo ở **trust root cài sẵn và được bảo vệ từ ISO**.
- **Hai tầng** (ADR 0017): **(1) apt GPG** — keyring Debian trong ISO, xác thực gói trong repo đã ký; **(2) NaMiOS release-index kiểu TUF** — khóa root offline neo niềm tin cho targets/snapshot/timestamp (xem `UPDATE-KEY-CATALOG.md`).
- Mỗi payload phải khớp **đồng thời**: danh tính sản phẩm, channel, phiên bản, kiến trúc, hash, kích thước, và chữ ký/metadata đã xác thực. Thiếu một là **fail-closed** (ADR 0007).
- **Trạng thái thật:** tầng (1) kế thừa Debian (chưa repo NaMiOS riêng); tầng (2) **chưa tồn tại** (thiết kế). Vì vậy gốc tin cậy TUF-grade hiện **chưa** có hiệu lực.

## 3. Kẻ tấn công và kịch bản (Adversaries)

Ký hiệu khả năng: **M** = kiểm soát mạng/mirror; **CDN** = kiểm soát máy chủ phân phối; **KEY** = trộm được khóa; **LOCAL** = quyền trên máy nạn nhân (app thường/AI/người dùng).

| ID | Kẻ tấn công / kịch bản | Khả năng | Mục tiêu | Tài sản bị đe dọa |
| --- | --- | --- | --- | --- |
| TA1 | **Mirror độc hại** — máy soi gương repo phục vụ gói/metadata sửa đổi | M | Cài mã độc, hoặc ẩn bản vá | A1, A7 |
| TA2 | **CDN/máy chủ phân phối bị xâm phạm** | CDN | Đổi payload sau khi rời CI | A1 |
| TA3 | **Khóa CI bị trộm** (stolen CI/release key) | KEY | Ký bản độc trông "hợp lệ" | A1, A3 |
| TA4 | **Rollback attack** — ép máy nhận lại **bản cũ có lỗ hổng** đã vá | M/CDN | Mở lại lỗ hổng đã đóng | A7, A1 |
| TA5 | **Freeze attack** — giữ máy ở **metadata cũ**, che giấu rằng đã có bản mới | M/CDN | Ngăn vá, kéo dài cửa sổ tấn công | A7 |
| TA6 | **Mix-and-match** — ghép gói từ các thời điểm/ảnh khác nhau thành tổ hợp không nhất quán | M/CDN | Tạo trạng thái dễ khai thác | A1 |
| TA7 | **Metadata hết hạn phục vụ như còn hiệu lực** | M/CDN | Lách kiểm thời hạn | A1, A7 |
| TA8 | **Tamper đồng hồ / NTP giả** — chỉnh giờ máy để metadata hết hạn trông còn hạn (hoặc ngược lại) | M/LOCAL | Vô hiệu hóa kiểm `Valid-Until` | A1, A7 |
| TA9 | **Bản đã thu hồi (revoked) vẫn được phục vụ** | M/CDN | Cài lại bản đã biết lỗi | A1, A7 |
| TA10 | **Payload path traversal / symlink** trong gói hoặc cache | CDN/LOCAL | Ghi đè file ngoài phạm vi, leo thang | A1, A4 |
| TA11 | **Script trong metadata/release-notes** (gồm **prompt injection** nhắm SmartAI) | M/CDN/LOCAL | Lừa máy/AI chạy lệnh, bỏ kiểm chữ ký | A1, A6 |
| TA12 | **App thường / AI / người dùng thường sửa channel/policy/trust-store** | LOCAL | Hạ chuẩn an toàn để nhận bản độc | A6, A2 |
| TA13 | **Firmware giả / hạ cấp firmware, hoặc nạp lúc pin yếu** | M/CDN/LOCAL | Gạch máy (brick) hoặc cấy backdoor tầng firmware | A4 |
| TA14 | **Mất điện/đứt mạng giữa transaction** (không hẳn cố ý, nhưng phải chống) | — | — (sự cố) | A4, A5 |
| TA15 | **Telemetry thu quá mức** (nội dung tài liệu/URL) | nội bộ | — | A8 |

## 4. Biện pháp giảm thiểu — ánh xạ PL15 §4 (Mitigations)

> Cột **Trạng thái**: `có (upstream)` = cơ chế Debian/KDE đã chín nhưng chưa cấu hình riêng; `specified` = thiết kế trong repo, chưa máy thật; `phải xây` = chưa có, thuộc U15-B/C/D.

| Đe dọa | Biện pháp (PL15 §4) | Cơ chế NaMiOS | Trạng thái | Mã lỗi |
| --- | --- | --- | --- | --- |
| TA1 Mirror độc | Không tin TLS/200; mọi payload phải có chữ ký + hash + khớp danh tính | apt GPG (tầng 1) + release-index ký (tầng 2); verify ở Update Service fail-closed | tầng1 `có (upstream)`, tầng2 `phải xây` | UPD-003 |
| TA2 CDN bị chiếm | Chữ ký tách khỏi kênh phân phối; verify-lại trước apply | Ký ở CI với khóa offline/HSM; CDN chỉ bê bytes; verify lại sau tải (ADR 0017) | `phải xây` | UPD-003 |
| TA3 Khóa CI bị trộm | **Threshold/quorum**, phân tách vai trò, khóa CI có hạn + revocation | Vai trò root/targets offline + threshold; khóa CI ngắn hạn (key-catalog) | `phải xây` | UPD-003/UPD-009 |
| TA4 Rollback | Số phiên bản metadata **tăng nghiêm ngặt**, chống tụt | TUF snapshot role; Update Service từ chối metadata version thấp hơn đã thấy | `phải xây` | UPD-003 |
| TA5 Freeze | Metadata `timestamp` **hạn ngắn**, làm tươi liên tục | TUF timestamp role; cảnh báo khi metadata "quá cũ" | `phải xây` | UPD-004 |
| TA6 Mix-and-match | **Snapshot role** khóa một tập gói nhất quán theo thời điểm | release-index snapshot; apt trong một repo nhất quán là nền | `phải xây` (snapshot role) | UPD-003 |
| TA7 Metadata hết hạn | Kiểm `Valid-Until`/expiry; hết hạn → không coi là xác nhận mới | apt `Valid-Until` (tầng1) + expiry TUF (tầng2) | tầng1 `có (upstream)`, tầng2 `phải xây` | UPD-004 |
| TA8 Đồng hồ/NTP giả | **"Không xác minh được thời hạn" → xử lý tường minh, KHÔNG âm thầm bỏ kiểm** | Update Service: nếu clock không tin được → báo UPD-004, dừng, hướng dẫn kiểm giờ; không tự bỏ qua expiry | `phải xây` | UPD-004 |
| TA9 Bản thu hồi | Danh sách thu hồi + đẩy tới máy; chặn/rollback theo policy | revocation list trong release-index; Update Service đọc trước khi cài | `phải xây` | UPD-009 |
| TA10 Path traversal/symlink | Storage riêng cho cache, chống thay symlink/path traversal, kiểm lại trước apply | Update Service: giải nén an toàn (tái dùng `namios_security.safe_path`), cache tách quyền | `specified` (có `safe_path`), ráp vào service `phải xây` | UPD-003 |
| TA11 Script/prompt injection | **Không thực thi script từ metadata tùy ý**; SmartAI chỉ-đọc, chỉ argv tĩnh | ADR 0017: Service chỉ argv tĩnh, không `eval`/`curl\|bash`; SmartAI đọc state **đã lọc**, không ký/không tắt kiểm (có sẵn trong `namios-smartai-policy.sh`) | Service `phải xây`; SmartAI-guard `specified` | UPD-003 |
| TA12 Sửa channel/policy | **Không cho AI/ứng dụng thường sửa channel/policy/trust**; bảo vệ cấu hình updater | polkit-gate: chỉ Update Service (đặc quyền) ghi được trust/policy; UI+SmartAI không | `specified`/`phải xây` | UPD-003 |
| TA13 Firmware | Đường firmware tách OS; kiểm model/pin/nguồn/chữ ký; **không hứa rollback firmware** | fwupd/LVFS (đánh giá U15-D) + ngưỡng pin; xác nhận riêng (PL15 §2) | `absent` (fwupd chưa có) | UPD-006 |
| TA14 Mất điện/đứt mạng | Tải tiếp theo chunk/hash; verify toàn bộ trước apply; không reboot khi thiếu payload; snapshot để quay lui | Timeshift snapshot trước-update + health-check + GRUB recovery (ADR 0014); download resume (U15-B) | snapshot/health `specified`; resume `phải xây` | UPD-002/UPD-008 |
| TA15 Telemetry | **Dashboard chỉ ghi build/state/health/mã lỗi; KHÔNG thu nội dung file/URL/tên tài liệu** | redactor có sẵn (`namios_security.redact_text`, `smartai_redact`); áp cho mọi log updater | `specified` (redactor có), áp vào updater `phải xây` | — |

### Chống mã hóa boot / máy nhận bản (PL15 §4 "Máy nhận bản")

- **Quyền tối thiểu:** Update Service là thành phần đặc quyền **duy nhất**, polkit-gated; UI + SmartAI không quyền.
- **Staged, không ghi nửa vời:** cài vào bản mới dạng staged; verify toàn bộ trước apply; không reboot khi payload thiếu (PL15 §5).
- **Cân nhắc tương lai:** Secure Boot / measured boot / dm-verity / mã hóa đĩa — **chưa triển khai/kiểm**, **không** ghi "đã bảo vệ" (PL15 §4). Để `specified`, đánh giá sau pilot.

## 5. Ánh xạ mã lỗi an ninh (PL15 §7) → UPD-003/004/005/009

Khi phát hiện tấn công/bất thường, Update Service phát mã **có cấu trúc** cho UI + SmartAI; **không bao giờ** có nút "Bỏ qua kiểm tra" hay "thử nguồn khác":

- **UPD-003** (hash/chữ ký không hợp lệ) ← TA1, TA2, TA3, TA4, TA6, TA10, TA11, TA12 → **chặn cài, báo an ninh, giữ bản hiện tại, không bypass**.
- **UPD-004** (metadata hết hạn / clock sai) ← TA5, TA7, TA8 → **nêu bước kiểm giờ + nguồn metadata; KHÔNG bỏ kiểm để tiếp tục**.
- **UPD-005** (sai model/architecture) ← TA6 (một phần), bản không hợp thiết bị → **chặn bản không phù hợp, ghi mã thiết bị**.
- **UPD-009** (bản bị thu hồi) ← TA9, TA3 (sau khi phát hiện khóa lộ) → **dừng rollout/cài, giữ hoặc rollback theo policy, giải thích rõ**.
- Phụ trợ: **UPD-002** (thiếu dung lượng cho staged/rollback) + **UPD-008** (health-check sau boot fail → tự rollback) bảo vệ A4/A5 trước TA14.

SmartAI khi gặp `SIGNATURE_INVALID`/`METADATA_EXPIRED`/`REVOKED`/`HASH_MISMATCH` → **chặn + báo an ninh**, tối đa 3 giả thuyết có bằng chứng, **không** gợi ý nguồn không tin cậy (PL15 §6).

## 6. Giả định và điểm chưa chứng minh (Honest gaps)

- **Giả định:** trust root trong ISO không bị thay trước khi tới tay người dùng (phụ thuộc kênh phát hành ISO + chữ ký ISO — ngoài phạm vi tài liệu này, thuộc build/release).
- **Chưa chứng minh:** toàn bộ tầng TUF (vai trò/threshold/revocation/snapshot/timestamp) là **thiết kế**, chưa có mã, chưa khóa thật (dùng khóa lab ở U15-B).
- **Chưa test máy thật:** chống mất-điện, rollback thật, chặn-vượt-quyền, firmware — tất cả **chưa** chạy trên 5 máy pilot (cửa U15-C/D).
- **Firmware:** fwupd vắng mặt → TA13 hiện **không có biện pháp kỹ thuật nào** ngoài "không cài firmware tự động".
- **Secure/measured boot, disk encryption:** chưa có → kẻ có quyền vật lý (ngoài scope các TA mạng ở trên) chưa được mô hình hóa đầy đủ.

> Cập nhật tài liệu này mỗi khi có mã/biện pháp mới chạy thật. Một bản cập nhật an toàn là **chu trình phát hành–xác thực–cài–kiểm–khôi phục**, không chỉ một nút "Update".
