# NaMiOS — Chia ổ đĩa lúc cài (kiểu "C:, D:" quen thuộc với người dùng Windows)

- **Wave:** chia ổ dễ-nhanh cho người ít hiểu kỹ thuật, 10/11/2026.
- **File cấu hình liên quan:** `etc/calamares/modules/partition.conf` (xem comment đầy đủ
  trong chính file đó — mọi khoá đã đối chiếu với file mẫu CHÍNH THỨC của Calamares, không
  bịa khoá).
- **verified_on_host: NO cho TOÀN BỘ file này.** Chưa `lb build` + cài thật lên máy/VM để
  chụp lại đúng từng chữ trên giao diện (tên nút/ô có thể lệch đôi chút giữa bản Calamares
  thật cài trong ảnh và các phiên bản tài liệu công khai đã đối chiếu). Người cầm ISO lên
  máy/VM thật phải đi qua checklist ở mục 5 rồi điền lại.

## 0. Sự thật cần biết trước (không né)

Windows gọi phân vùng là "ổ C:", "ổ D:" — đó là **ký tự ổ đĩa**, một khái niệm CHỈ CÓ trên
Windows. Linux (và NaMiOS) **không có ký tự ổ đĩa**. Thứ tương đương là:

| Khái niệm Windows | Tương đương trên NaMiOS |
| --- | --- |
| Ổ C: (chứa hệ điều hành + chương trình) | **Phân vùng hệ thống**, gắn vào `/` (gọi tắt "gốc") |
| Ổ D: (chứa dữ liệu cá nhân) | **Phân vùng dữ liệu riêng**, gắn vào một **điểm gắn** (mount point) khác, ví dụ `/data` |
| "Đổi tên ổ đĩa" | **Đặt nhãn** (label) cho phân vùng — vẫn hiện trong trình quản lý file, không phải chữ cái |

NaMiOS **không tạo ra ký tự ổ đĩa giả** để giống Windows — làm vậy sẽ gây hiểu lầm nguy hiểm
hơn là giúp ích. Thay vào đó, NaMiOS làm cho 2 lựa chọn **có thật** của trình cài (Calamares)
dễ hiểu và đặt tên quen mắt nhất có thể.

## 1. Lối dễ-nhanh — "Xoá ổ (Erase disk)" — MẶC ĐỊNH, 1 phân vùng

Dành cho người **không cần** tách riêng dữ liệu, hoặc không chắc nên chọn gì. Đây là lựa
chọn **đã được chọn sẵn** khi trang chia ổ ("Choice"/"Lựa chọn phân vùng") hiện ra.

1. Ở trang chia ổ, Calamares đã tự tích sẵn **"Xoá ổ đĩa" / "Erase disk"**.
2. Chọn **đúng ổ đĩa** muốn cài lên (nếu máy có nhiều ổ — ví dụ cả USB cài lẫn ổ cứng trong
   máy, phải chọn đúng ổ **cứng trong máy**, không chọn nhầm USB).
3. Bấm tiếp → trang tổng kết ("Summary") hiện lại toàn bộ thay đổi sẽ ghi xuống đĩa → xem
   lại kỹ → bấm **Cài đặt ngay / Install now**.

Kết quả: **một phân vùng duy nhất** chứa toàn bộ hệ thống + dữ liệu, được đặt nhãn
**"NaMiOS"** (xem được bằng lệnh `lsblk -f` hoặc trong trình quản lý file sau khi cài xong) —
tương đương "ổ C: duy nhất" của một máy Windows không chia ổ.

**Vì sao chọn Erase làm mặc định (có đánh đổi, nói rõ):** bản thân Calamares khuyến nghị
KHÔNG chọn sẵn ô nào (để người dùng buộc phải tự chọn, tránh bấm lướt qua một bước quan
trọng). NaMiOS chọn sẵn "Erase" để đường đi NGẮN NHẤT cho người ít hiểu kỹ thuật, đúng yêu
cầu của việc này. Hai lớp an toàn vẫn còn: (a) vẫn phải tự chọn đúng ổ đĩa, (b) vẫn phải tự
xem trang tổng kết rồi bấm xác nhận — không phải 1 chạm xong tất.

## 2. Lối "C: + D:" — tách hệ thống/dữ liệu — Tự chia tay (Manual), các bước

Dành cho người muốn **giống Windows nhất**: một phân vùng hệ thống riêng + một phân vùng dữ
liệu riêng, để lỡ cài lại hệ thống thì dữ liệu ở phân vùng kia không bị đụng tới.

**Bước 1 — chọn lối tự chia tay:**
Ở trang chia ổ, bấm chọn **"Chia tay / Manual partitioning"** (thay vì "Xoá ổ" đã chọn sẵn).

**Bước 2 — tạo phân vùng hệ thống ("ổ C:"):**
1. Chọn dòng **"Khoảng trống còn trống / Free Space"** trên ổ đĩa muốn cài.
2. Bấm **"Tạo mới / Create"**.
3. Trong hộp thoại hiện ra, điền:
   - **Kích thước (Size):** để khoảng **40–60 GiB** (đủ cho hệ thống + chương trình; máy ít
     dung lượng có thể để thấp hơn, tối thiểu khuyến nghị chung là ~20 GiB).
   - **Hệ thống tệp (File System):** `ext4` (đã chọn sẵn).
   - **Điểm gắn (Mount Point):** `/`
   - **Nhãn (Label):** gõ **`NaMiOS`** (tương đương đặt tên "ổ C:") — đây là ô người dùng
     **tự gõ tay**, Calamares không có sẵn khoá cấu hình để điền trước nhãn này (đã kiểm tra
     tài liệu chính thức, không có khoá như vậy cho lối tự chia tay — chỉ lối tự động ở mục 1
     có nhãn "NaMiOS" sẵn qua `partitionLayout`).
4. Bấm **Xác nhận/OK**.

**Bước 3 — tạo phân vùng dữ liệu ("ổ D:"):**
1. Chọn lại dòng **"Khoảng trống còn trống / Free Space"** (phần còn lại sau bước 2).
2. Bấm **"Tạo mới / Create"**.
3. Điền:
   - **Kích thước (Size):** để **100%** (dùng hết phần còn lại) hoặc một số cụ thể nếu muốn
     để dư khoảng trống chưa dùng.
   - **Hệ thống tệp (File System):** `ext4` (khuyên dùng, để tương thích quyền truy cập Linux
     tốt nhất) — không khuyến nghị `fat32`/`ntfs` cho phân vùng dữ liệu chính vì giới hạn
     quyền sở hữu file kiểu Linux.
   - **Điểm gắn (Mount Point):** gõ **`/data`** (hoặc `/home` nếu muốn toàn bộ thư mục cá
     nhân/Tài liệu/Hình ảnh nằm ở phân vùng riêng này — cách này giống nhất với thói quen
     Windows "Documents ở ổ D:").
   - **Nhãn (Label):** gõ **`DATA`** (tương đương đặt tên "ổ D:").
4. Bấm **Xác nhận/OK**.

**Bước 4 — cài:**
Bấm tiếp → xem lại trang tổng kết → bấm **Cài đặt ngay / Install now**.

Vậy là **3 lần bấm tạo-phân-vùng** (1 lần chọn lối Manual + 2 lần Create) cho ra đúng mô hình
"C: hệ thống, D: dữ liệu" — không có chữ cái ổ đĩa thật, nhưng có **nhãn** và **công dụng**
tương đương.

**Ghi chú an toàn:** nếu máy khởi động kiểu UEFI, Calamares sẽ tự đòi thêm một phân vùng nhỏ
("EFI System Partition", ~300 MiB, gắn vào `/boot/efi`) — đây là phần bắt buộc của UEFI, không
phải lựa chọn, cứ để Calamares tự tạo hoặc tạo theo đúng gợi ý của chính Calamares.

## 3. Phân biệt với 2 lối còn lại (có nhưng không phải trọng tâm của việc này)

- **Thay thế một phân vùng (Replace a partition):** dùng khi máy đã có hệ điều hành khác và
  muốn ghi đè đúng MỘT phân vùng cụ thể, giữ các phân vùng khác. Dành cho người biết mình
  đang làm gì — không phải lối "dễ-nhanh".
- **Cài cạnh (Install alongside):** dùng khi máy đã có Windows/hệ điều hành khác và muốn giữ
  cả hai, chọn "song song khởi động" (dual-boot) lúc mở máy. Không nằm trong phạm vi "chia
  C:/D:" của việc này nhưng người dùng vẫn thấy lựa chọn này trên trang chia ổ.

## 4. Khoá cấu hình thật đã dùng (tóm tắt — xem đầy đủ trong `partition.conf`)

| Khoá | Giá trị | Vì sao |
| --- | --- | --- |
| `allowManualPartitioning` | `true` | Mở đường cho lối "C:/D:" ở mục 2 |
| `initialPartitioningChoice` | `erase` | Lối dễ-nhanh được chọn sẵn (mục 1) |
| `defaultFileSystemType` | `"ext4"` | Khớp giả định Timeshift (rsync, không phải btrfs CoW) đã ghi ở package-lists |
| `userSwapChoices` | `none, small, suspend, file` | Người dùng vẫn chọn được, có mặc định an toàn |
| `initialSwapChoice` | `small` | Mặc định hợp lý, không ép người ít hiểu kỹ thuật phải hiểu "swap" |
| `efi.minimumSize` | `100MiB` | Không chặn cứng lối "Cài cạnh Windows" có ESP cũ nhỏ |
| `partitionLayout` (lối Erase) | 1 phân vùng tên `"NaMiOS"`, `/`, 100% | Nhãn kiểu-Windows cho lối tự động |
| `alwaysShowPartitionLabels` | `true` | Người dùng thấy ngay nhãn mình vừa đặt |

## 5. Checklist xác nhận trên máy/VM thật (điền khi cài thật, không tự đánh dấu trước)

- [ ] Trang chia ổ mở ra, ô **"Xoá ổ / Erase disk"** đã được tích sẵn
- [ ] Chọn ổ đĩa đích → trang tổng kết hiện đúng 1 phân vùng tên "NaMiOS"
- [ ] Cài xong, chạy `lsblk -f`/`blkid` → thấy nhãn `NaMiOS` trên phân vùng gốc (`/`)
- [ ] Thử lại lối "Chia tay/Manual" → tạo được 2 phân vùng theo đúng 2 bước ở mục 2, gõ nhãn
      "NaMiOS"/"DATA" thành công, không bị khoá/ẩn ô Label
- [ ] Máy **UEFI**: thấy phân vùng EFI tự thêm, cài xong khởi động được vào NaMiOS
- [ ] Máy **BIOS/Legacy**: KHÔNG thấy phân vùng EFI (đúng), bảng phân vùng là `msdos`, cài
      xong khởi động được bằng grub-pc (đúng như đã xác nhận ở package-lists/
      0700-installer.list.chroot)
- [ ] Tên nút/nhãn tiếng Việt hiển thị thật trên giao diện khớp (hoặc gần khớp) với tên dùng
      trong tài liệu này — nếu lệch, sửa lại tài liệu cho đúng câu chữ thật
