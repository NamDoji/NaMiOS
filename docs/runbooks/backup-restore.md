# Runbook — Sao lưu & Khôi phục dữ liệu người dùng (U13-03)

**Năng lực:** U13-03 "Sao lưu dữ liệu người dùng" (P0) — xem §2 bảng U13-03 trong
`docs/spec-package/NaMiOS_Phu_luc_13_Uu_tien_Nang_cap_va_Cong_Phat_hanh.md`.
**Cấu hình liên quan:** `distro/live-build/config/package-lists/0620-backup.list.chroot`
(gói `kup-backup` + `bup`), `distro/live-build/config/hooks/normal/0620-backup-config.hook.chroot`
(cấu hình mặc định `~/.config/kuprc` + launcher "NaMiOS Sao lưu").

**`verified_on_host: NO`** — runbook này soạn từ đặc tả + mã nguồn upstream
Kup (xem chú thích trong hook `0620-backup-config.hook.chroot`), **CHƯA** chạy
thật trên máy NaMiOS nào (ISO lúc viết file này chưa có gói `kup-backup` trong
một bản build đã xác nhận trên phần cứng thật). Người thực hiện runbook lần
đầu trên máy thật: ghi lại kết quả từng bước + log lỗi (nếu có) vào
`qa/evidence-index/` và cập nhật dòng U13-03 trong `docs/STATUS-U13-KIEM-KE.md`
(`chưa làm` → `partial`/`completed` theo đúng bằng chứng, không tự nâng mức).

## 0. Việc này kiểm tra đúng cửa gì

> *"Khôi phục 10 file đúng hash và một hồ sơ trình duyệt thử nghiệm; không
> ghi đè âm thầm."*

Nghĩa là: (a) sao lưu 10 file thật, xoá/hỏng chúng, khôi phục lại, rồi so
**sha256 trước và sau** phải khớp từng file; (b) khôi phục được một hồ sơ
Firefox để kiểm chứng việc sao lưu không chỉ "chép được văn bản" mà còn đúng
với dữ liệu nhị phân/SQLite phức tạp; (c) trong toàn bộ quá trình, công cụ
khôi phục **không được tự động ghi đè** file đang có mà không hỏi.

## 1. Chuẩn bị

- Máy đã cài NaMiOS với gói `kup-backup` + `bup` (kiểm: `dpkg -s kup-backup bup`).
- Một ổ USB/ổ ngoài rời còn trống vài trăm MB — đây là **đích tách quyền**:
  NaMiOS **cố ý không** đặt sẵn một ổ/đường dẫn nào trên cùng đĩa hệ thống,
  bạn phải tự cắm và tự chọn ổ này trong bước 2.
- Mở **Konsole** (Terminal) để chạy `sha256sum`.

## 2. Bật sao lưu lần đầu và chọn đích (đích tách quyền)

1. Mở launcher **"NaMiOS Sao lưu"** (hoặc **Cài đặt hệ thống → Sao lưu**).
2. Cắm ổ ngoài đã chuẩn bị ở bước 1.
3. Trong kế hoạch **"Sao lưu dữ liệu cá nhân"** (đã có sẵn, xem cấu hình mặc
   định bên dưới), bấm **Chỉnh sửa** → mục **Đích lưu** → chọn đúng ổ ngoài
   vừa cắm. NaMiOS để trống mục này cho tới khi bạn chọn — **không tự gán**
   một ổ nào, kể cả ổ duy nhất đang cắm.
4. Các mục đã đặt sẵn, không cần đổi (trừ khi có lý do khác):
   - **Loại sao lưu:** bup (theo phiên bản + dedup, không phải chụp-đè thô).
   - **Lịch:** mỗi tuần một lần.
   - **Hỏi trước khi sao lưu:** có — Kup sẽ hỏi lại trước khi chạy, không tự
     chạy ngầm lần đầu mà không báo.
5. Để không phải chờ tới lịch hàng tuần: mở icon Kup ở khay hệ thống (system
   tray) → **Sao lưu ngay** cho kế hoạch này. Theo dõi tới khi báo hoàn tất
   (hoặc báo lỗi — xem mục 6 nếu có lỗi).

## 3. Khôi phục 10 file và kiểm đúng hash (cửa kiểm chứng chính)

```sh
# 3.1 — Chuẩn bị 10 file thật để test (dùng file sẵn có hoặc tạo mới)
mkdir -p ~/kiem-tra-backup
for i in 1 2 3 4 5 6 7 8 9 10; do
  echo "Noi dung test file so $i - $(date)" > ~/kiem-tra-backup/file-$i.txt
done

# 3.2 — Ghi lại hash GỐC trước khi sao lưu (để so sánh sau khi khôi phục)
sha256sum ~/kiem-tra-backup/*.txt > ~/kiem-tra-backup.sha256
cat ~/kiem-tra-backup.sha256
```

3.3. Chạy sao lưu (lại mục 2 bước 5: khay hệ thống → **Sao lưu ngay**), chờ
     báo hoàn tất — 10 file test này phải nằm trong thư mục cá nhân (mặc định
     Kup sao lưu toàn bộ `$HOME`, trừ cache/thùng rác) nên sẽ được chép vào
     bản sao lưu lần này.

```sh
# 3.4 — Giả lập mất dữ liệu: xoá cả 10 file gốc
rm ~/kiem-tra-backup/*.txt
ls ~/kiem-tra-backup   # phải trống
```

3.5. Mở công cụ khôi phục — hai cách:
   - Chạy `kup-filedigger` trong Konsole (mở trực tiếp cửa sổ duyệt bản sao
     lưu), hoặc
   - Chuột phải vào thư mục **cha** còn tồn tại (`kiem-tra-backup`) trong
     Trình quản lý tệp (Dolphin) → **"Restore Previous Version…"** (mục này
     hiện hiển thị tiếng Anh — gói gốc `kup-backup` **chưa có** bản dịch
     `Name[vi]` cho hành động này; xem mục 7).

3.6. Trong cửa sổ khôi phục: chọn đúng repo (đường dẫn ổ ngoài → thư mục
     `Backups`), duyệt tới bản sao lưu vừa tạo ở bước 3.3 (trước khi xoá),
     chọn **cả 10 file**, bấm **Restore…**.

3.7. Màn hình tiếp theo cho chọn nơi khôi phục: chọn **"Restore to original
     location"** (khôi phục về đúng vị trí cũ `~/kiem-tra-backup/`).

3.8. **Kiểm "không ghi đè âm thầm"**: vì ở bước 3.4 bạn đã xoá sạch 10 file,
     lần khôi phục này sẽ không gặp file trùng nên không có gì để hỏi — đó
     là hành vi đúng (không có gì để ghi đè). Để thật sự kiểm tra cơ chế
     chống-ghi-đè, làm thêm một lần: **đừng** xoá `file-1.txt`, chỉ sửa nội
     dung nó (`echo "da sua" > ~/kiem-tra-backup/file-1.txt`), rồi khôi phục
     lại 10 file như bước 3.5–3.7 — lần này công cụ **phải hiện hộp thoại
     xác nhận ghi đè** cho `file-1.txt` trước khi chép đè lên bản đã sửa.
     Nếu nó ghi đè thẳng không hỏi, ghi lại là **lỗi chặn ra bản phát hành**
     (vi phạm đúng cửa kiểm chứng U13-03).

```sh
# 3.9 — Kiểm hash SAU khi khôi phục, so với hash GỐC đã lưu ở bước 3.2
sha256sum -c ~/kiem-tra-backup.sha256
```

- Nếu in ra đúng **10 dòng `OK`** → **đạt** phần "khôi phục 10 file đúng hash".
- Nếu có dòng `FAILED` hoặc báo thiếu file → **chưa đạt**; chụp lại output
  lệnh trên + log Kup (xem mục 6) rồi báo lại, không tự sửa số liệu để "cho
  qua".

## 4. Khôi phục một hồ sơ Firefox thử nghiệm

Hồ sơ Firefox (lịch sử, bookmark, mật khẩu đã lưu, cookie...) nằm ở
`~/.mozilla/firefox/<ten-ngau-nhien>.default-release/` và nằm trong vùng
sao lưu mặc định (toàn bộ `$HOME`). Đây là ca kiểm khó hơn 10 file text vì có
nhiều file SQLite/nhị phân khoá-đang-mở.

1. **Đóng Firefox hoàn toàn** trước khi sao lưu (tránh sao lưu lúc file
   `.sqlite` đang được Firefox giữ khoá, dễ sai lệch).
2. Chạy sao lưu như mục 2 bước 5.
3. Tạo một thay đổi dễ nhận ra để làm "mốc" kiểm chứng: mở Firefox, thêm một
   bookmark tên rõ ràng (ví dụ "ĐÁNH DẤU TEST KHÔI PHỤC"), rồi **đóng Firefox**
   lại.
4. Mở `kup-filedigger`, duyệt tới bản sao lưu **trước khi** thêm bookmark ở
   bước 3 (tức bản ở bước 2), chọn đúng thư mục hồ sơ Firefox
   (`~/.mozilla/firefox/<ten-ho-so>.default-release/`).
5. **Khôi phục vào một thư mục KHÁC trước** (ví dụ
   `~/kiem-tra-firefox-restore/`), **không** khôi phục trực tiếp vào hồ sơ
   đang dùng — tránh làm hỏng hồ sơ thật nếu có gì sai.
6. Mở Firefox với hồ sơ vừa khôi phục để kiểm (không đụng hồ sơ mặc định):
   ```sh
   firefox-esr --profile ~/kiem-tra-firefox-restore/<ten-ho-so>.default-release
   ```
   Hồ sơ khôi phục phải **KHÔNG** có bookmark "ĐÁNH DẤU TEST KHÔI PHỤC" (vì
   bản sao lưu được chọn là **trước** khi thêm) — nếu không có, chứng minh
   khôi phục đúng đúng thời điểm (không trộn dữ liệu mới/cũ).
7. Chỉ sau khi chắc chắn hồ sơ khôi phục đọc được và đúng thời điểm, mới cân
   nhắc khôi phục đè lên hồ sơ gốc (và khi đó công cụ phải hỏi xác nhận ghi
   đè đúng như mục 3.8 — không tự làm).

## 5. Vì sao tin được "không ghi đè âm thầm"

Không phải chỉ lời hứa: cửa sổ khôi phục của Kup (FileDigger) có một bước
riêng xác nhận trước khi ghi — xác minh qua đọc mã nguồn upstream
`filedigger/restoredialog.cpp` (nút `mConfirmButton`/`mOverwriteBackButton`,
hàm `fileOverwriteConfirmed()`), không phải suy đoán. Việc chọn đích sao lưu
(mục 2) cũng để trống UUID ổ ngoài theo mặc định — bạn **phải** tự chọn, công
cụ không tự gán một ổ có sẵn.

## 6. Khi báo lỗi

- Nhật ký daemon Kup: icon khay hệ thống → mỗi kế hoạch có nút xem log (file
  log theo từng lần chạy). Nếu không chạy được từ đầu, kiểm `journalctl
  --user -u plasma-kupdaemon* ` hoặc tìm theo tên tiến trình `kupdaemon`.
- Ổ ngoài bị rút giữa lúc sao lưu/khôi phục, hết dung lượng, hoặc mất quyền
  ghi: Kup phải báo trạng thái "lỗi"/"chưa sao lưu được" trên biểu tượng khay
  hệ thống, không được báo "thành công" giả. Ca này **CHƯA** được test trong
  runbook này (phạm vi hiện tại là đường thường — happy path); ghi vào backlog
  nếu phát hiện báo sai khi test thật.

## 7. Trung thực — còn thiếu gì trước khi coi U13-03 là `completed`

- **`verified_on_host: NO`** cho toàn bộ runbook này tới khi có người chạy
  thật trên phần cứng NaMiOS và ghi evidence (log + ảnh/video) vào
  `qa/evidence-index/`.
- Mục chuột phải Dolphin **"Restore Previous Version…"** chưa có `Name[vi]`
  trong gói `kup-backup` gốc (kiểm chứng từ `fileitemaction/kupfileitemaction.json`
  upstream) — hiện hiển thị tiếng Anh. Việc dịch thuộc luồng lớp phủ desktop
  riêng (PL12/UX12, `docs/l10n/DESKTOP-NAMES-OVERLAY-SPEC.md`), **ngoài phạm
  vi** của hook `0620-backup-config.hook.chroot`.
- Cấu hình mặc định `~/.config/kuprc` trong hook `0620-backup-config.hook.chroot`
  được viết dựa trên đọc mã nguồn upstream KDE/kup (nhánh `master`, truy cập
  08/11/2026), **chưa** xác nhận khớp 100% với bản `kup-backup` thật đã biên
  dịch cho Debian 13 trixie (môi trường soạn hook không có apt source trixie).
  Việc đầu tiên khi có máy/host thật: mở System Settings → Sao lưu, xác nhận
  kế hoạch "Sao lưu dữ liệu cá nhân" hiện đúng (không báo lỗi cú pháp cấu
  hình, đúng loại bup/lịch tuần/hỏi-trước) trước khi chạy hết runbook này.
- Runbook chỉ phủ đường thường (sao lưu thành công → khôi phục). Báo lỗi khi
  sao lưu/khôi phục thất bại (mục 6) cần một lượt kiểm riêng, có kịch bản chủ
  động làm hỏng (rút ổ giữa chừng, đầy đĩa) để xem thông báo có đúng/đủ rõ
  tiếng Việt không.
