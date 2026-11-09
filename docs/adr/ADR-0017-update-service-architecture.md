# ADR 0017 — Kiến trúc Update Service và ranh giới Update Center / SmartAI (U15-A)

- **Trạng thái:** proposed · **Mức thực thi:** `specified` (chưa có mã Update Service, chưa máy thật)
- **Ngày:** 09/11/2026
- **Năng lực:** Phụ lục 15 — **U15-A "Kiểm kê/ADR"** (chốt nền Linux + cơ chế update/transaction, định ranh giới service).
  Cửa kiểm chứng của chuỗi (U15-B→D): *"Gói giả chữ ký / hash sai / metadata hết hạn / mirror độc hại → 100% bị chặn, có mã lỗi, không bypass; update lỗi vẫn boot hoặc vào recovery; SmartAI không thể cài gói không ký."*
- **Liên quan:** ADR 0002 (nền Debian 13), ADR 0007 (cập nhật + ký metadata, fail-closed), **ADR 0014 (snapshot + rollback + health check — ADR này xây tiếp trên đó)**, ADR 0008 (chứng nhận theo tác vụ), ADR 0016 (design system cho UI). Kiểm kê nền: `docs/spec-package/U15-INVENTORY.md`.

## Bối cảnh

NaMiOS là live-build **Debian 13 "trixie" + KDE Plasma 6**, cài bằng Calamares lên **ext4** (ADR 0014 §Bối cảnh). Kiểm kê U15-A (`docs/spec-package/U15-INVENTORY.md`) xác nhận **sự thật nền**:

- **Đã có (chín, của upstream):** apt + repo Debian ký GPG (`InRelease` + hash trong `Packages`); Discover + PackageKit làm UI update chung của KDE; Flatpak + portal cho app sandbox.
- **Đã có (cấu hình tĩnh NaMiOS, `specified`, chưa máy thật):** unattended-upgrades chỉ pocket security không auto-reboot (hook `0600`); Timeshift snapshot-trước-update + health-check lúc boot (hook `0640`, ADR 0014); backup `/home` Kup+bup (hook `0620`); UFW+AppArmor (hook `0630`); SmartAI userspace chỉ-đọc + polkit-gate cho hành động đổi (hook/script `namios-smartai`).
- **CHƯA có:** Update Service đặc quyền riêng; Update Center 4-chế-độ; metadata kiểu TUF (nhiều vai trò/threshold/chống rollback-freeze-mix); staged A-B deployment; hợp đồng dữ liệu + mã lỗi `UPD-*`; đường firmware (fwupd **vắng mặt**).

ADR 0007 (02/11) đã **quyết định hướng** = apt + repo ký + "ưu tiên đánh giá TUF" cho catalog metadata, fail-closed — nhưng chưa có mã verify metadata. ADR 0014 đã chốt **rollback mức ảnh** (Timeshift rsync) thay vì A-B nguyên tử, và trung thực rằng apt **không** nguyên tử. ADR này phải chốt: **(1)** nền transaction/rollback nào cho Update Service, và **(2)** ranh giới ba thành phần Update Center (UI) ↔ Update Service (đặc quyền) ↔ SmartAI (chỉ-đọc) mà PL15 §1/§6 yêu cầu.

PL15 §1 ghi rõ OSTree/rpm-ostree chỉ là **tham khảo năng lực**, không mặc định là stack đã chọn. Yêu cầu là ADR so sánh trung thực theo phần cứng, gói ứng dụng và năng lực bảo trì — **không** copy một stack vì nó "nghe nguyên tử".

## Các phương án đã cân nhắc

### (a) apt + repo ký + Timeshift-rollback + **Update Service mỏng (thin wrapper)** — ĐƯỢC CHỌN cho alpha

- Giữ nguyên apt/dpkg + repo Debian ký (nguồn/toàn vẹn gói đã chín). **Thêm một lớp mỏng** `namios-update-service` (daemon/CLI đặc quyền, polkit-gated) **bọc** quanh apt + Timeshift + health-check, thực thi đúng trình tự PL15: `check → verify-metadata → preflight → snapshot(Timeshift) → staged-apply → health-check → rollback-nếu-fail`.
- Rollback = **mức ảnh** (Timeshift rsync, kế thừa ADR 0014) + GRUB recovery entry, **không** phải A-B nguyên tử. Trung thực: mất điện giữa transaction dpkg → phục hồi bằng snapshot, không phải "bật lại A-B tức thì".
- Verify metadata kiểu TUF (vai trò/threshold/thời hạn/revocation) làm ở **tầng catalog/release-index riêng của NaMiOS** (một chỉ mục phát hành ký, trỏ tới gói apt theo version+hash), **không** thay thế apt — apt vẫn là bộ cài; lớp NaMiOS là cổng tin-cậy ở trước.
- **Lợi:** không rời bỏ Debian/apt (không mâu thuẫn ADR 0002); tái dùng toàn bộ package-list/hook/Việt-hoá/Wine/Calamares; dùng lại Timeshift + health-check đã viết; đội bảo trì được; chạy trên ext4.
- **Hại (phải ghi honest):** không nguyên tử; rollback phụ thuộc Timeshift đã cấu hình (nếu chưa chọn ổ snapshot thì lần đó không có điểm quay lui — health-check phải cho người dùng thấy); hai tầng metadata (apt GPG + release-index TUF) cần đồng bộ cẩn thận.

### (b) Image-based transactional (OSTree / rpm-ostree / bootc) — **tham khảo, KHÔNG chọn cho alpha**

- rpm-ostree/bootc cho **A-B deployment nguyên tử thật** + rollback một lệnh [1] → mạnh hơn hẳn (a) về "update lỗi vẫn khởi động".
- **Giá:** rpm-ostree là hệ sinh thái Fedora/OSTree, không dùng apt/dpkg → rời bỏ Debian, mâu thuẫn ADR 0002 + toàn bộ stack hiện có. OSTree-trên-Debian (ostree + bootc/dpkg) **chưa chín**, chưa có đường Calamares + apt chuẩn, đội **chưa có máy thật** để kiểm. Rủi ro bảo trì cao, lợi ích chưa chứng minh ở alpha. Giữ làm mục tiêu dài hạn, không phải alpha.

### (c) Hybrid — apt nền + image-based cho một tập hệ-lõi — **ghi nhận, hoãn**

- Giữ apt cho app; dựng một "ảnh hệ-lõi" nhỏ (kernel + init + desktop) cập nhật kiểu transaction (ostree-style) để có rollback nguyên tử cho phần cốt. Về lý thuyết là "ngon nhất cả hai", nhưng **gấp đôi độ phức tạp vận hành** (hai cơ chế update song song, hai định dạng, hai đường rollback) khi đội còn chưa test nổi một đường trên máy thật. **Hoãn** tới khi (a) chạy thật xong và có nhu cầu chứng minh.

## Quyết định

**Chọn (a) cho bản alpha.** Dựng `namios-update-service` là **lớp điều phối đặc quyền mỏng** trên apt + Timeshift + health-check, với tầng catalog/release-index ký kiểu TUF ở trước. Cụ thể định ranh giới **ba thành phần** (ràng buộc cứng PL15 §1 & §6):

### Ranh giới Update Center (UI) ↔ Update Service (đặc quyền) ↔ SmartAI (chỉ-đọc)

```
  Người dùng
     │  (bấm nút, chọn 1 trong 4 chế độ)
     ▼
┌──────────────────────┐   D-Bus/polkit    ┌──────────────────────────┐
│  Update Center (UI)  │ ───── action ────▶│  Update Service (đặc quyền)│
│  - KHÔNG đặc quyền   │                   │  - polkit-gated, argv tĩnh │
│  - chỉ hiển thị state│◀──── state/UPD-* ─│  - check/download/verify/  │
│  - hợp đồng §7 (JSON)│                   │    preflight/snapshot/     │
└──────────┬───────────┘                   │    staged-apply/health/    │
           │ (đọc state đã lọc)            │    rollback                │
           ▼                               │  - apt + Timeshift + GRUB  │
┌──────────────────────┐   read-only       └──────────────────────────┘
│   SmartAI (userspace)│ ──── đọc state ──────────▲
│  - CHỈ ĐỌC mặc định  │                          │ (chỉ đọc metadata+state
│  - giải thích/đề xuất │                          │  đã lọc; KHÔNG ghi)
│  - plan ≤3 bước       │
└──────────────────────┘
```

**1. Update Center = UI, KHÔNG đặc quyền.**
- Chỉ: hiển thị trạng thái (`Đang kiểm tra → Có bản mới → Đang tải → Đã xác thực → Sẵn sàng cài → Đang cài → Cần khởi động lại → Kiểm tra sau boot → Hoàn tất/Đã khôi phục/Cần hỗ trợ`), changelog tiếng Việt, 4 chế độ (§3), nút Kiểm tra/Cài/Để sau/Tạm dừng.
- **Không** tự chạy apt, **không** ghi metadata, **không** đổi trust-store. Mọi hành động thật gửi qua Update Service bằng một **tập action cố định** (enum), **không** truyền URL/câu lệnh tùy ý.
- Theo design system (ADR 0016): không chỉ dùng màu đỏ/xanh, screen-reader đọc tên+trạng thái+nút, không "Đã xảy ra lỗi" khi đã biết nguyên nhân.

**2. Update Service = thành phần đặc quyền DUY NHẤT, polkit-gated.**
- Chạy quyền root **chỉ khi** một action được polkit cho phép (tái dùng mô hình `pkexec`/polkit đã dùng trong `namios-smartai-policy.sh`). Mỗi action là **argv tĩnh**, **không** `eval`, **không** `curl|bash`, **không** chạy script từ metadata.
- Trách nhiệm: resolve catalog/release-index → **verify chữ ký + vai trò + thời hạn + revocation (fail-closed)** → check kiến trúc/model → preflight (storage/power/network) → **Timeshift snapshot** (ADR 0014) → tải theo chunk/hash, resume → **verify lại toàn bộ trước apply** → staged-apply qua apt → ghi journal để tiếp tục sau reboot → health-check sau boot → **rollback** (Timeshift/GRUB recovery) nếu health fail.
- **Không** tự nâng `completed` chỉ vì apt trả success (PL15 §7). Mọi trạng thái đi qua enum hợp lệ + idempotency + correlation_id.
- Mã lỗi `UPD-001..010` (PL15 §7) là **ngôn ngữ chung** giữa Service → UI → SmartAI. `SIGNATURE_INVALID`/`METADATA_EXPIRED`/`REVOKED`/`HASH_MISMATCH` → chặn + báo an ninh, **không** nút "Bỏ qua kiểm tra", **không** "thử nguồn khác".

**3. SmartAI = chỉ-đọc, giải thích/chẩn đoán/đề xuất.**
- Đọc **metadata + state đã lọc** (bản cũ/mới, loại, release notes, thiết bị bị ảnh hưởng, lỗi xác thực, lịch sử thất bại, preflight). Giải thích tiếng Việt; đề xuất "Cài tối nay"/"Sao lưu trước"/"Hỏi IT".
- **TUYỆT ĐỐI KHÔNG:** ký gói, sửa metadata, tắt signature check, vượt policy, cài từ URL tùy ý, xóa bản cũ, áp patch chưa phát hành, hay có root shell. Mọi hành động đổi-trạng-thái mà SmartAI đề xuất đều phải đi **qua Update Service + polkit + xác nhận người dùng** (đúng mô hình `policy_classify` hiện có: plan ≤3 bước + argv tĩnh + hỏi đồng ý + audit đã che + nêu UNDO).
- Tắt AI → Update Center và khôi phục **vẫn hoạt động bình thường** (PL15 §6). SmartAI **không** là điều kiện cho boot/update/recovery.

### Hai tầng tin cậy (honest về khoảng cách apt-signing vs TUF)

| Tầng | Bảo vệ | Cơ chế |
| --- | --- | --- |
| **apt GPG** (đã có) | Toàn vẹn + nguồn của **gói** trong một repo đã ký | `InRelease`/`Release.gpg` + hash trong `Packages` |
| **NaMiOS release-index** (phải xây, kiểu TUF) | Quản trị **tin cậy ở cấp bản phát hành**: nhiều vai trò, threshold, chống rollback/freeze/mix-and-match, revocation bản, thời hạn ngắn | Thiết kế vai trò root/targets/snapshot/timestamp (xem `docs/security/UPDATE-KEY-CATALOG.md`); dùng **triển khai được kiểm định**, KHÔNG tự viết thuật toán chữ ký |

**apt-signing là nền đủ cho "gói đến từ Debian và không bị sửa", nhưng KHÔNG cho** quản trị khóa nhiều vai trò, threshold, chống rollback/freeze/mix-and-match hay revocation ở cấp bản phát hành NaMiOS. Đó là **khoảng trống TUF-grade** mà release-index phải lấp — và nó là **thiết kế**, chưa có mã, chưa có khóa thật.

## Trung thực về giới hạn (KHÔNG được quảng cáo quá)

- **Chưa có mã Update Service.** ADR này là `specified`. Không tuyên bố NaMiOS "đã có updater".
- **Không nguyên tử.** Rollback là mức ảnh Timeshift + GRUB recovery (ADR 0014), không phải A-B. Mất điện giữa dpkg → phục hồi bằng snapshot, không tức thì.
- **TUF-grade là thiết kế.** Release-index nhiều vai trò/threshold/revocation chưa tồn tại; U15-B mới dựng verify metadata bằng **fixture ký giả, khóa lab gắn nhãn dev** (ADR 0007 §spike). **Không** production key trong repo/CI.
- **Firmware chưa có đường.** fwupd vắng mặt; U15-D mới đánh giá thêm, **không** hứa rollback firmware.
- **Hai tầng metadata** (apt GPG + release-index) tăng bề mặt cấu hình — phải test ca lệch-đồng-bộ.

## Hệ quả

- U15-B hiện thực `namios-update-service` (thin, polkit-gated) + Update Center UI 4-chế-độ + verify metadata (fixture lab) + hợp đồng `UPD-*`; test server giả có signed metadata + ca phản công. Tái dùng Timeshift/health-check/SmartAI-policy đã có.
- U15-C nối staged + boot-health + auto-rollback + migration guard; fault injection VM → 5 máy pilot (gồm mất điện).
- U15-D phân kênh + ring + revocation + fwupd(đánh giá) + SmartAI giải thích; diễn tập khóa lộ/CDN thay.
- Giữ nguyên ADR 0002/0007/0014: không rời Debian, không bỏ fail-closed, không bỏ rollback-mức-ảnh. Nếu sau này Calamares đổi sang **btrfs** hoặc OSTree-trên-Debian chín, **mở lại** ADR này để cân nhắc phương án (b)/(c).

## Nguồn

- [1] rpm-ostree / OSTree atomic rollbacks: https://coreos.github.io/rpm-ostree/administrator-handbook/ ; https://ostreedev.github.io/ostree/atomic-rollbacks/
- [2] The Update Framework — roles & security: https://theupdateframework.io/docs/security/ ; https://theupdateframework.io/docs/metadata/
- ADR 0002 (nền Debian 13), ADR 0007 (ký metadata fail-closed), ADR 0014 (snapshot + rollback + health check), ADR 0016 (design system).
- Kiểm kê: `docs/spec-package/U15-INVENTORY.md`. Threat model: `docs/security/UPDATE-THREAT-MODEL.md`. Danh mục khóa: `docs/security/UPDATE-KEY-CATALOG.md`.
