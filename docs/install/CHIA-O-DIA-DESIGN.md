# Thiết kế: Chia ổ C/D/E khi cài — AN TOÀN DỮ LIỆU (NaMi)

**Trạng thái:** THIẾT KẾ + KẾ HOẠCH TEST (chưa wire vào luồng cài thật).
**Nguồn yêu cầu:** Cuong #18365 + #18373 (ổ 1-phân-vùng → cho chọn chia N ổ, chia
đều, OS vào C, KHÔNG mất data; ổ đã ≥2 phân vùng → bỏ qua bước này).
**Quyết định (Avab, #18430):** feature này DATA-CRITICAL → KHÔNG ship mù. Chỉ đưa
vào bản cài sau khi chạy qua TOÀN BỘ checklist test ở §5 trên VM/ổ phụ.
`verified_on_host: NO`.

## 1. Nguyên tắc tối thượng — KHÔNG BAO GIỜ mất data ngoài ý muốn
- Chỉ tạo/xoá phân vùng khi người dùng đã **chủ động chọn** một chế độ ghi-đĩa.
- Chế độ "chia N ổ" CHỈ áp dụng trên vùng đĩa người dùng **đồng ý xoá** (hoặc đĩa
  TRỐNG). Không tự động đụng tới phân vùng đang có dữ liệu.
- Mọi màn có nút Huỷ; có bản tóm tắt "sẽ làm gì với từng phân vùng" TRƯỚC khi ghi.

## 2. Hành vi theo trạng thái ổ (phát hiện lúc cài)
| Trạng thái ổ | Hành vi |
|---|---|
| **Đĩa TRỐNG / chỉ 1 phân vùng-trống** | Hiện bước "Chia thành mấy ổ?" (1–4). Mặc định 2 (C+D). |
| **1 phân vùng CÓ dữ liệu (vd Windows)** | KHÔNG auto-chia. Mời: *Cài song song (giữ Windows+data)* / *Xoá & cài mới (chia N ổ)* / *Thủ công*. Chọn "xoá" mới mở bước chia N. |
| **Đã ≥2 phân vùng** | Bỏ qua bước chia (đúng #18373). Dùng flow Calamares chuẩn (alongside/replace/manual). |

## 3. Chia đều (khi người dùng chọn N ổ trên vùng được phép ghi)
- Gọi tổng dung lượng khả dụng = `S`, số ổ = `N`.
- **C (ổ hệ điều hành/root)** = ổ đầu; **D, E…** = ổ dữ liệu.
- Chia đều: mỗi ổ ≈ `S/N` (ví dụ 300GB, N=3 → mỗi ổ 100GB — đúng ví dụ Cuong).
- **Lưới an toàn kích thước:** nếu `S/N` làm C < **40 GiB** → cảnh báo + đề nghị
  giảm N (OS cần tối thiểu ~25–40GiB cho cập nhật/ứng dụng). Không cho N khiến
  C quá nhỏ dẫn tới cài hỏng.
- EFI (300MiB, có sẵn trong partition.conf) + swap nằm trong phần của C, KHÔNG
  tính vào các ổ dữ liệu.
- **Mount:** C = `/` ; D = `/home` ; E,F… = `/mnt/Data2`, `/mnt/Data3`
  (ext4). → người dùng thấy nhiều "ổ" trong Trình quản lý tệp như Windows, dữ
  liệu cá nhân (D=/home) tách khỏi hệ → cài lại OS không mất data ở D.

## 4. Cơ chế kỹ thuật (Calamares)
Hiện `etc/calamares/modules/partition.conf`: `initialPartitioningChoice: erase`
+ `partitionLayout` 1 phân vùng 100%. Hai hướng hiện thực (chọn khi code):
- **(A) partitionLayout tĩnh nhiều phân vùng** — đơn giản, Calamares hỗ trợ sẵn,
  NHƯNG số ổ cố định (không cho chọn N lúc chạy). Có thể ship "C+D mặc định" an
  toàn bằng cách này trước (low-risk), coi như bước 1.
- **(B) Module chọn-N lúc chạy** — QML/python module Calamares đọc input N rồi
  sinh layout động. Đúng ý "chọn mấy ổ" nhất nhưng là code mới → BẮT BUỘC test
  §5. Đây là bản đầy đủ.
- Giữ `allowManualPartitioning: true` làm đường thoát cho người rành.
- **KHÔNG đổi** `initialPartitioningChoice` sang gì hung hãn hơn; cân nhắc để
  `none` (không auto-chọn xoá) cho an toàn người có data — xác nhận lúc test UX.

## 5. CHECKLIST TEST (bắt buộc trước khi đưa vào bản cài — chạy trên VM/ổ phụ)
Mỗi ca: snapshot đĩa trước → cài → kiểm → so sánh.
1. Đĩa trống 128GB, chọn 1 ổ → 1 phân vùng, boot OK.
2. Đĩa trống 300GB, chọn 3 ổ → C≈100/D≈100/E≈100, OS ở C, D=/home, boot OK, thấy
   3 ổ trong Dolphin.
3. Đĩa 64GB, chọn 4 ổ → cảnh báo C<40GiB, chặn/đề nghị giảm N.
4. **Đĩa có Windows + data (QUAN TRỌNG NHẤT):** chọn "Cài song song" → Windows +
   file người dùng **còn nguyên** sau cài; dual-boot lên được.
5. Đĩa có Windows, chọn "Xoá & cài mới" → có cảnh báo rõ "sẽ xoá Windows" trước
   khi ghi; sau khi đồng ý mới xoá.
6. Đĩa đã 2 phân vùng sẵn → KHÔNG hiện bước chia N (đúng #18373).
7. Ngắt điện/huỷ giữa chừng màn chọn (trước khi ghi) → đĩa KHÔNG đổi.
8. UEFI + Legacy BIOS đều cài + boot được.
9. Cài lại OS lên C, giữ D (/home) → dữ liệu D còn.

## 6. Rollback
- Feature nằm trong `partition.conf` (+ module nếu dùng B). Revert = trả
  `partition.conf` về bản 1-phân-vùng 100% (git). Không ảnh hưởng phần khác của ISO.
- Chỉ merge vào nhánh build sau khi 9/9 ca §5 PASS trên VM thật.

## 7. Việc còn lại trước khi code
- [ ] Chọn (A) hay (B) ở §4 (khuyến nghị: ship (A) "C+D" an toàn trước, rồi (B)).
- [ ] Dựng VM Debian-trixie-Calamares để chạy §5 (môi trường sandbox hiện KHÔNG
      cài được → cần máy/VM thật — đây là lý do chưa wire vào luồng cài).
