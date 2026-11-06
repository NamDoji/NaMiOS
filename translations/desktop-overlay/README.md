# NaMiOS — Lớp phủ TÊN `.desktop` / `.directory` (desktop-names overlay)

Thư mục này là **nguồn** cho lớp phủ Việt hoá **TÊN** trên các bề mặt KHÔNG đi qua gettext `.mo`
(nên lớp phủ `vi_NM` ở `translations/vi-overlay/` **không với tới**):

- `Name` / `GenericName` / `Comment` của **ứng dụng** trong menu Bắt đầu (`.desktop`),
- tên **nhóm Cài đặt hệ thống** (`systemsettings/categories/*.desktop`, `Type=Service`),
- tên **nhóm ứng dụng Kickoff** (`desktop-directories/kf5-*.directory`, `Type=Directory`).

Cơ chế đầy đủ + bằng chứng + điểm cần duyệt: [`docs/l10n/DESKTOP-NAMES-OVERLAY-SPEC.md`](../../docs/l10n/DESKTOP-NAMES-OVERLAY-SPEC.md).

> **Vì sao không dùng `vi_NM`:** giá trị `Name[…]` trong `.desktop`/`.directory` được chọn theo
> **`LC_MESSAGES`** (`vi_VN` → `vi` → mặc định), **không** đọc catalog `.mo` và **không** khớp mã
> `vi_NM`. → Lớp phủ này **chỉ dùng hậu tố `[vi]`**.

## Cách hoạt động (tóm tắt — PA-A trong SPEC §3.1)

1. Dữ liệu dịch nằm trong các file `.tsv` dưới `vi/` — **3 cột, phân tách bằng TAB**:
   ```
   relpath_dưới_data_dir <TAB> Key[vi] <TAB> giá trị tiếng Việt
   ```
   Ví dụ: `applications/org.kde.konsole.desktop<TAB>GenericName[vi]<TAB>Dòng lệnh`
2. Hook build (chroot, SAU khi cài gói — **CHƯA tạo**, chờ Cuong duyệt) với mỗi dòng:
   - sao **nguyên văn** `/usr/share/<relpath>` sang `/usr/local/share/<relpath>` (giữ `Exec`/`Icon`),
   - chèn/ghi đè **chỉ** khoá `[vi]` trên bản sao bằng `kwriteconfig6` (hoặc `desktop-file-edit`).
3. `/usr/local/share` đứng TRƯỚC `/usr/share` trong `XDG_DATA_DIRS` → bản sao **thắng** mà
   **KHÔNG sửa file gói gốc**.

## Quy ước chất lượng (bắt buộc)

1. `relpath` phải là đường dẫn THẬT dưới `/usr/share` của gói trong ảnh — xác minh bằng `dpkg -L`.
2. Chỉ ghi khoá `Name[vi]` / `GenericName[vi]` / `Comment[vi]`. **Không** đụng khoá chức năng.
3. **Chỉ bù chỗ TRỐNG hoặc SỬA chỗ SAI** — không đè chuỗi upstream đã dịch tốt (vd okular, kate).
4. Thuật ngữ theo [`../vi-overlay/GLOSSARY-and-batch1.md`](../vi-overlay/GLOSSARY-and-batch1.md).
5. Dòng nào chưa chắc upstream/English đánh dấu `# [cần xác minh trên ISB]` ngay trên nó.

## Trạng thái

- Đây là **DRAFT nội dung** (bản dịch đề xuất). Hook build + lựa chọn công cụ + PA-A/PA-C cho
  systemsettings categories **chờ Cuong duyệt** (SPEC §9) trước khi ghép vào live-build.
- Các mục KCM/kinfocenter/cảm biến **KHÔNG** ở đây — chúng là JSON nhúng / gettext (SPEC §6),
  thuộc lớp phủ `vi_NM` `.mo` hoặc lớp phủ JSON riêng.
