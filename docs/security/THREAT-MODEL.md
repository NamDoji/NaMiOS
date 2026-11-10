# NaMiOS — Mô hình đe dọa hợp nhất Phụ lục 09 (VN09-024)

- **Ngày:** 10/11/2026. **Mốc:** PL09 §2.4, yêu cầu **VN09-024** ("Mỗi đe dọa có điều khiển phòng ngừa, phát hiện, phục hồi và ca kiểm thử").
- **Trạng thái:** `DESIGN` — đây là mô hình đe dọa ở mức thiết kế cho lớp trải nghiệm/ứng dụng/bảo mật PL09. **Chưa biện pháp nào được kiểm trên máy thật**; mã/cấu hình dẫn chiếu có test logic (pytest/`bash -n`) xanh, chưa qua `lb build` + boot pilot.
- **Quan hệ với tài liệu đã có (KHÔNG lặp lại, chỉ dẫn chiếu):**
  - `docs/threat-model.md` — threat model nền tảng M0 (tài sản AS-01..09, actor TA-01..10, ranh giới tin cậy B1..B5, SEC-001..012, test negative M1). Mục 6 của nó đã thêm TA-08 prompt-injection, TA-09 mạo danh thương hiệu, TA-10 chuỗi cung ứng.
  - `docs/security/UPDATE-THREAT-MODEL.md` — threat model chuyên sâu **chuỗi cập nhật** (A1..A8, TA1..15, UPD-003/004/005/009).
  - `docs/release-gates.md` — RG-01..08 (lưới chặn phát hành).
- **Tài liệu NÀY** là **bản hợp nhất theo góc nhìn người dùng cuối PL09**: lấy 11 đe dọa PL09 liệt kê rõ và cho mỗi đe dọa một bảng **Phòng ngừa / Phát hiện / Phục hồi + ca test (T09 / VN09) + rủi ro còn lại + owner**, trỏ ngược về cơ chế thật trong repo.

> **Không hứa an toàn tuyệt đối.** Mọi biện pháp **giảm xác suất và thiệt hại**, không triệt tiêu rủi ro. Nguyên tắc gốc kế thừa: chạy chương trình Windows là **thực thi mã không tin cậy**; **prefix Wine KHÔNG phải ranh giới bảo mật** (COMP-008); "quét sạch" KHÔNG phải bằng chứng máy không bị xâm nhập (VN09-030); catalog/metadata/nội dung web KHÔNG điều khiển lệnh đặc quyền.

## 0. Tài sản & ranh giới (tóm tắt — chi tiết ở `docs/threat-model.md`)

Tài sản ưu tiên bảo vệ: `home`/tài liệu người dùng (AS-01), credential/secret (AS-02), SSH key & browser profile (AS-03), CSDL nghiệp vụ (AS-04), Wine prefix (AS-05), khóa/catalog production (AS-06), khả năng boot/khôi phục (A4 — UPDATE-THREAT-MODEL), tiền/chứng từ (RG-02/03). Mức nghiêm trọng cao nhất gắn trực tiếp RG-01 (mất file), RG-02 (sai tiền), RG-03 (chữ ký số sai), RG-08 (đánh lừa web-shortcut).

---

## 1. Đe dọa theo góc nhìn người Việt dùng máy (PL09 §2.4)

### T-01 — Phishing qua Zalo/Facebook (trang/tên miền mạo danh, màn đăng nhập giả)

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | Shortcut chính thức CHỈ mở HTTPS tới host trong allowlist độc lập (`src/namios_essentials/anti_impersonation.py` — `check_official_url`, allowlist `facebook.com`/`zalo.me`/`id.zalo.me`…); NaMiOS **không nhúng form đăng nhập**, không đóng gói cookie/mật khẩu; chặn redirect ngoài domain kỳ vọng. Nhãn trung thực "Dịch vụ web; cần mạng và tài khoản riêng" (`labels.py`). | `✅ logic` / `🟡` (file `.desktop` ghim **đang dựng**) |
| Phát hiện | Phát hiện domain "gần giống" chứa tên thương hiệu nhưng không allowlisted → cảnh báo TRƯỚC khi hiện form (`anti_impersonation` — brand-impersonation set); SmartAI coi trang web là DỮ LIỆU (`namios_smartai/injection.py`). | `✅ logic` |
| Phục hồi | Người dùng không nhập secret vào NaMiOS (không có wrapper); nếu đã lộ ở trang giả → đổi mật khẩu/bật 2FA ở vendor (ngoài phạm vi OS); không có secret nào do NaMiOS lưu hộ. | `🟡` (hướng dẫn) |
| Test | **T09-B** (click Zalo → miền chính thức HTTPS, không xin mật khẩu qua NaMiOS); `tests/security/essentials/*` (URL `zalo-login.example` bị chặn). VN09-018, VN09-027, VN09-044. | — |
| Rủi ro còn lại | Người dùng tự gõ URL giả vào browser (ngoài shortcut); trang hợp pháp bị XSS; allowlist lỗi thời khi vendor đổi domain. | — |
| Owner | `namios-essentials-team` (shortcut/allowlist) + nhóm bảo mật (cập nhật allowlist ký qua manifest). | — |

### T-02 — Tệp tải về độc hại

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | Không autorun; không chạy file khi preview (VN09-011/028); kiểm loại tệp thực + đuôi kép, cảnh báo `.exe`/script/macro/shortcut (`src/namios_security/safe_path.py`); chặn download nguy hiểm theo policy browser (RG-06). | `🟡` (logic path-safety có; hành vi mount/preview cần HW) |
| Phát hiện | Scanner on-demand khi chốt bật (ClamAV — hiện **tắt/comment** ở `package-lists/0630-security.list.chroot`, package **đang dựng**); badge vòng-đời-chữ-ký độc lập (`update_center.scanner_badge`). | `🟡`/`⛔` (engine chưa bật) |
| Phục hồi | Quarantine có ID + quyền IT + điều tra + restore + audit, không xóa vô điều kiện (thiết kế VN09-029/T09-F — chưa có engine thật). | `⛔` (quarantine chưa dựng) |
| Test | **T09-C** (`bao_cao.pdf.exe` không chạy qua preview), **T09-F** (scanner báo nhầm → quarantine không xóa mù). VN09-028, VN09-029. | — |
| Rủi ro còn lại | Mã độc mới chưa có chữ ký; ClamAV chỉ on-demand (không thường trú); người dùng tự `chmod +x` rồi chạy. | — |
| Owner | Nhóm bảo mật (scanner/quarantine) + `namios-security` (safe_path). | — |

### T-03 — USB / thiết bị ngoài không tin cậy

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | Không autorun/autoexecute khi mount; mount an toàn khi hệ tệp lỗi; kiểm loại tệp thực (`safe_path.py`); không cấp USB token/thiết bị cho app sandbox theo mặc định (`0630` portal, SEC-003/004). | `🟡` |
| Phát hiện | Quét tùy policy khi mount hoặc trước khi mở file rủi ro (gắn với T-02 scanner); cảnh báo đuôi kép/shortcut đáng ngờ. | `🟡`/`⛔` |
| Phục hồi | Eject an toàn báo rõ file nào chưa xong, bản gốc còn (VN09-011); không ghi đè âm thầm. | `🔴` (hành vi Dolphin cần HW) |
| Test | **T09-C** (USB vào máy không tự thực thi). VN09-011, VN09-028. | — |
| Rủi ro còn lại | BadUSB/HID giả bàn phím; firmware thiết bị độc; người dùng chủ động chạy payload. | — |
| Owner | `namios-security` + nhóm desktop (hành vi mount/eject). | — |

### T-04 — Macro Office độc hại

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | Office bundle (PL07) mặc định tắt/hỏi macro; cảnh báo tài liệu chứa macro trước khi mở; không chạy macro khi preview. | `🟡` (thuộc Office PL07; cấu hình macro-security chưa kiểm HW) |
| Phát hiện | Kiểm loại tệp + cờ chứa macro; scanner on-demand (T-02). | `🟡` |
| Phục hồi | Mở ở chế độ chỉ-xem/an toàn; backup versioned nếu macro đã sửa tệp (`0620-backup`). | `🟡` |
| Test | (ánh xạ T09-C loại tệp rủi ro). VN09-005, VN09-017, VN09-028. | — |
| Rủi ro còn lại | Macro hợp pháp bị lạm dụng; người dùng bật "Enable content". **Chưa có ca T09 riêng + chưa cấu hình macro-policy cụ thể.** | — |
| Owner | Nhóm Office PL07 + bảo mật. | — |

### T-05 — Gói phần mềm độc (App Center / nguồn ngoài)

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | Manifest provenance bắt buộc (hash/signature/giấy phép/owner — `essentials-manifest.schema.json`, `manifest.is_shippable`); phân loại nguồn distro/kho kiểm duyệt/vendor/web/Wine (`labels.py`); gói không provenance/chữ ký sai không hiện như tin cậy. | `✅ logic` |
| Phát hiện | Validator 2 tầng + semantic (recipe allowlist, cấm `shell`/`eval`/URL-script — COMP-004); `tests/security/essentials` đối kháng. | `✅ logic` |
| Phục hồi | Gỡ app; rollback OS qua Timeshift nếu gói hệ thống (ADR-0014/0020); audit. | `🟡` |
| Test | `tests/security/essentials/test_essentials_adversarial.py`; `tests/integration/.../not-ready-tbd-app.json`, `injection-shell-recipe.json`. VN09-016, VN09-022. | — |
| Rủi ro còn lại | Khóa ký bị lộ quy mô chuỗi cung ứng (TA-10 / UPDATE-THREAT-MODEL TA3); gói upstream bị compromise trước khi vào kho. | — |
| Owner | `namios-essentials-team` (manifest/App Center) + bảo mật (ký/revocation). | — |

### T-06 — App Windows `.exe` qua Wine thao túng dữ liệu

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | Mỗi app = WINEPREFIX/capsule riêng, chỉ mount thư mục cần cho tác vụ, KHÔNG map toàn bộ `home` (`includes.chroot/.../namios-wine-capsule`, `docs/specs/WINE-CAPSULE.md`, `namios_smartai/capsule.py`); gỡ drive Z; D-Bus lọc (SEC-003). | `🟡` (thiết kế + script; enforce thật M2) |
| Phát hiện | Ranh giới thật là bubblewrap/AppArmor (không phải prefix); app bị chặn không tự chạy lại ngoài sandbox (SEC-005). | `🔴` (M2 — cần Wine/sandbox thật) |
| Phục hồi | File được cấp vẫn ghi nhận rủi ro + backup (VN09-031); rollback OS không đụng `home`. | `🟡` |
| Test | **T09-E** (Wine truy cập ngoài thư mục cấp → chặn, không đọc home); SEC-05/06 (M2, `blocked_external_dependency`). VN09-031. | — |
| Rủi ro còn lại | Mã độc Windows thao tác được trên chính tệp Wine được cấp → scanner + backup KHÔNG thay sandbox; X11/XWayland không cách ly client (phi-ranh-giới công bố). | — |
| Owner | Nhóm Wine/compat (PL01) + bảo mật. | — |

### T-07 — Lạm dụng quyền AI (prompt injection, lệnh đặc quyền)

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | SmartAI mặc định **chỉ đọc**; model KHÔNG nằm trong đường boot/gõ phím/cấp quyền/quyết định "file sạch" (PL09 §2); mọi hành động thay đổi (cài gói/sửa firewall/xóa-quarantine) đi qua **Policy Broker** — kế hoạch ≤3 bước + argv TĨNH + xác nhận + UNDO + AUDIT che bí mật (`includes.chroot/.../namios-smartai-policy.sh`); AI không đọc màn hình/clipboard/email/phím thường trực (`memory_scope.py`). | `✅ logic` |
| Phát hiện | Nội dung web/log/tài liệu coi là DỮ LIỆU, không bao giờ thành `ToolCall` (`namios_smartai/injection.py` — `is_injection`, `scan_untrusted`, marker song ngữ qua `fold_vn`). | `✅ logic` (test xanh) |
| Phục hồi | AUDIT một dòng/hành động đã che bí mật (`smartai_audit`); UNDO (Timeshift cho thay đổi hệ thống); kill switch (`kill_switch.py`). | `✅ logic` |
| Test | **T09-G** (trang "tắt firewall" → không thực thi, giải thích rủi ro); `tests/security/smartai/test_sai_acceptance.py` T03/T11 (injection → 0 tool chạy), T08 (ký&nộp không xác nhận bị chặn). VN09-035, VN09-045, VN09-047. | — |
| Rủi ro còn lại | Runtime LLM thật trên desktop chưa chạy; người dùng tự xác nhận hành động nguy hiểm được AI trình bày trung thực. | — |
| Owner | Nhóm SmartAI (PL04) + bảo mật. | — |

### T-08 — Ransomware (mã hóa hàng loạt tệp người dùng)

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | Sao lưu theo phiên bản + bản lưu tách quyền ghi thường ngày, đích ổ ngoài, Ask-first không ghi đè âm thầm (`hooks/.../0620-backup-config.hook.chroot`, `kup-backup`+`bup`); quyền tối thiểu hạn chế bán kính phá hoại (SEC-001..004). | `🟡` (backup cấu hình; chưa kiểm HW) |
| Phát hiện | Phát hiện biến động tệp hàng loạt bằng quy tắc XÁC ĐỊNH có ngưỡng false-positive, tạm dừng tiến trình khả nghi rồi hỏi người dùng/IT (**KHÔNG dựa duy nhất vào SmartAI**). | `⛔ chưa có` (**mục cần dựng**) |
| Phục hồi | Khôi phục theo phiên bản, kiểm phục hồi định kỳ; restore 10 tệp đúng hash, không đè bản mới khi chưa xem trước; RG-07 (backup phải restore được trên máy khác). | `🟡` (cần HW) |
| Test | **T09-J** (khôi phục 10 tệp đúng hash, hiển thị thời điểm, không đè mù). VN09-032. | — |
| Rủi ro còn lại | Thiếu lớp phát hiện-biến-động → cô lập trước ngưỡng mất dữ liệu chưa khả thi; backup chưa test restore trên HW (RG-07 còn mở). | — |
| Owner | Nhóm bảo mật (phát hiện) + nhóm backup/recovery. | — |

### T-09 — Mất/trộm thiết bị (truy cập vật lý)

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | Mã hóa ổ khi cài mới với recovery key do người dùng quyết định; Secure Boot khi phần cứng/phân phối hỗ trợ (SEC-012). | `🔴 blocked-real-HW` (**chưa có cấu hình LUKS/Secure Boot** trong repo; Calamares mặc định ext4 — ADR-0020) |
| Phát hiện | — (đe dọa vật lý, ngoài mô hình actor mạng). | — |
| Phục hồi | Hướng dẫn mất khóa THỰC TẾ, **không hứa khôi phục nếu không còn khóa**. | `🟡` (hướng dẫn) |
| Test | "Mất thiết bị thử nghiệm không đọc được dữ liệu" — **chưa chạy**. VN09-033. | — |
| Rủi ro còn lại | Kẻ có quyền vật lý + chưa mã hóa = đọc toàn bộ dữ liệu; Secure/measured boot/dm-verity chưa mô hình hóa đầy đủ (UPDATE-THREAT-MODEL §6). | — |
| Owner | Nhóm cài đặt/installer + bảo mật. | — |

### T-10 — Cập nhật bị can thiệp (MITM, downgrade, khóa lộ, mất điện giữa update)

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | KHÔNG tin TLS/200; mỗi payload khớp đồng thời danh tính/channel/version/arch/hash/chữ ký, thiếu một là **fail-closed** (ADR-0007/0017); hai tầng apt GPG + release-index kiểu TUF; cập nhật staged, không ghi nửa vời. | `🟡` (prototype verify fail-closed; **TUF/khóa thật chưa có**) |
| Phát hiện | Mã lỗi có cấu trúc UPD-003 (hash/chữ ký sai), UPD-004 (metadata hết hạn/clock sai), UPD-009 (bản thu hồi); **không có nút "Bỏ qua kiểm tra"** (`docs/security/UPDATE-THREAT-MODEL.md` §5). | `🟡` |
| Phục hồi | Timeshift snapshot trước-update + health-check sau boot + GRUB recovery (`hooks/.../0640-update-recovery`, ADR-0014); mất điện → boot bản trước/recovery, `/home` + log nguyên vẹn; `fault_inject.py` 13 ca. | `🟡` (prototype xanh; HW/apt/bootloader thật chưa nối) |
| Test | **T09-D** (gói cập nhật mất điện → boot bản trước/recovery); `tools/update-center-prototype/tests/*` (66 test), `tests/system/txstate/test_crash_recovery.py`. VN09-026, VN09-037. | — |
| Rủi ro còn lại | Tầng TUF (threshold/revocation/snapshot/timestamp) là thiết kế, chưa mã, chưa khóa thật; firmware (TA13) không có biện pháp kỹ thuật ngoài "không cài tự động"; chưa test mất-điện trên máy thật. | — |
| Owner | Nhóm Update/Recovery (PL15/PL19) + bảo mật (khóa/ký). | — |

### T-11 — Thiết bị mạng không tin cậy (Wi-Fi công cộng, dịch vụ chia sẻ lộ ra ngoài)

| Khía cạnh | Biện pháp & cơ chế thật | Trạng thái |
| --- | --- | --- |
| Phòng ngừa | Firewall mặc định **deny-incoming**/allow-outgoing (`hooks/.../0630-security-default.hook.chroot` part a, `ufw`); không mở SQL/RDP/SSH mặc định (SEC-010); không hạ TLS/SMB1/tắt firewall để sửa lỗi. | `🟡` (ghi tĩnh; bật "sống" ở máy đích) |
| Phát hiện | Phân loại mạng nhà/cơ quan/công cộng; chia sẻ file/in phải bật có chủ đích + hiện cổng/đối tượng. | `⛔/🟡` (**phân loại mạng + UI cổng chưa dựng**; chỉ có default-deny) |
| Phục hồi | Tắt chia sẻ; UFW giữ deny khi ra mạng công cộng. | `🟡` |
| Test | "Quét từ máy khác ở mạng công cộng không thấy dịch vụ đã tắt" — cần 2 máy thật. VN09-034. | — |
| Rủi ro còn lại | Người dùng tự mở cổng chia sẻ rồi quên; SmartAI/app không được tắt firewall (gắn T-07/T09-G). | — |
| Owner | Nhóm bảo mật/mạng + desktop (UI phân loại mạng). | — |

---

## 2. Ánh xạ nhanh đe dọa → ca T09 → VN09

| Đe dọa | Ca T09 | VN09 chính | Cơ chế repo |
| --- | --- | --- | --- |
| T-01 Phishing Zalo/FB | T09-B | 018, 027, 044 | `anti_impersonation.py`, `labels.py` |
| T-02 Tệp tải về | T09-C/F | 028, 029 | `safe_path.py`, `scanner_badge` |
| T-03 USB | T09-C | 011, 028 | `safe_path.py`, portal 0630 |
| T-04 Macro Office | (T09-C) | 005, 017, 028 | Office PL07 (chưa cấu hình macro-policy) |
| T-05 Gói độc | — | 016, 022 | `manifest.is_shippable`, validator 2 tầng |
| T-06 Wine `.exe` | T09-E | 031 | `namios-wine-capsule`, `capsule.py` |
| T-07 Lạm dụng AI | T09-G | 035, 045, 047 | `namios-smartai-policy.sh`, `injection.py` |
| T-08 Ransomware | T09-J | 032 | `0620-backup`, (phát hiện biến-động **chưa có**) |
| T-09 Mất máy | — | 033 | (mã hóa/Secure Boot **chưa có**) |
| T-10 Cập nhật can thiệp | T09-D | 026, 037 | `update-center-prototype`, `0640-update-recovery` |
| T-11 Mạng không tin | — | 034 | `ufw` default-deny (phân loại mạng **chưa có**) |

## 3. Rủi ro còn lại tổng hợp & owner (VN09-024 "ghi rủi ro còn lại + owner")

1. **Phát hiện ransomware (T-08) chưa có** — nửa "phát hiện biến-động + cô lập tiến trình" vắng. Owner: nhóm bảo mật.
2. **Scanner ClamAV chưa bật + chưa có quarantine** (T-02/03) — package comment, đang dựng; quarantine/false-positive cần làm. Owner: nhóm bảo mật.
3. **Mã hóa ổ/Secure Boot (T-09) chưa có** — dữ liệu khi mất máy chưa được bảo vệ. Owner: nhóm installer + bảo mật.
4. **Enforce sandbox Wine (T-06) là M2** — prefix ≠ ranh giới bảo mật, chưa test với Wine/bubblewrap thật. Owner: nhóm compat/bảo mật.
5. **Tầng TUF + khóa thật (T-10) là thiết kế** — apt GPG kế thừa Debian, release-index chưa tồn tại. Owner: nhóm Update + bảo mật.
6. **Phân loại mạng (T-11)** — mới có default-deny, chưa có nhà/cơ quan/công cộng + UI cổng. Owner: nhóm bảo mật/mạng.
7. **Macro Office policy (T-04)** — chưa cấu hình cụ thể + chưa có ca T09 riêng. Owner: nhóm Office PL07.

> **Cập nhật tài liệu này mỗi release** (VN09-024). Không đổi bất kỳ ô `🟡`/`⛔`/`🔴` thành "đã bảo vệ" khi chưa có bằng chứng chạy thật (ảnh/log đã lọc PII trên máy pilot). Một mô hình đe dọa đúng là tài liệu SỐNG — bổ sung actor/biện pháp khi có mã mới chạy thật, không âm thầm xóa rủi ro còn lại.
