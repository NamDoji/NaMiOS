# Cách tải NaMiOS và tạo USB để cài/dùng thử

> Dành cho người **chưa quen** việc tải ISO/ghi USB. Viết từng bước, không
> cần biết dòng lệnh (có cả cách bấm-chuột lẫn cách gõ lệnh cho ai thích).
> Có thể chụp màn hình từng bước khi bạn tự làm — tài liệu này không bắt
> buộc phải có ảnh mới dùng được.
>
> **Lưu ý trung thực:** đây là bản **ALPHA** để dùng thử, chưa phải bản phát
> hành chính thức. Trình cài đặt lên đĩa thật (Calamares, xem mục 5) **đã
> được chuẩn bị nhưng chưa được xác nhận trên máy thật** — nếu bạn cài vào
> máy chính đang dùng hằng ngày, hãy **sao lưu dữ liệu quan trọng trước**.

---

## Bạn cần gì trước khi bắt đầu

| Thứ cần có | Vì sao cần |
| --- | --- |
| Một USB rời, dung lượng **từ 8GB trở lên** | File ISO NaMiOS nặng khoảng **2.8GB**; USB sẽ bị **XÓA SẠCH** khi ghi ISO vào, nên dùng USB rảnh, không có dữ liệu quan trọng |
| Máy tính có kết nối Internet | Để tải file ISO (vài trăm MB tới vài GB tùy phần tải) |
| 30–60 phút | Tải + ghép file + ghi USB, tùy tốc độ mạng |
| (Khi cài thật) Dữ liệu quan trọng đã sao lưu | Cài lên đĩa thật có thể **xóa dữ liệu trên ổ đĩa bạn chọn** (mục 5) |

---

## 1. Tải file ISO từ GitHub

NaMiOS phát hành ISO tại trang Releases của dự án:

> **https://github.com/NamDoji/NaMiOS/releases**

Vì file ISO (~2.8GB) lớn hơn giới hạn 2GB/file mà GitHub cho phép, mỗi bản
phát hành bị **chia nhỏ** thành nhiều phần, tên dạng:

```
namios-alpha-YYYYMMDD-amd64.iso.00.part
namios-alpha-YYYYMMDD-amd64.iso.01.part
...
namios-alpha-YYYYMMDD-amd64.iso.sha256      (file để kiểm tra tải đúng/đủ)
ghep-iso.bat                                 (công cụ ghép, dùng trên Windows)
ghep-iso.sh                                  (công cụ ghép, dùng trên Linux/macOS)
```

**Việc cần làm:** mở trang Releases ở trên, chọn bản mới nhất (ở trên cùng),
kéo xuống mục "Assets", **tải HẾT mọi file `.part`, file `.sha256`, và cả
hai file `ghep-iso.bat`/`ghep-iso.sh`** — đặt tất cả vào **chung một thư
mục** (ví dụ thư mục `Tải về\NaMiOS`).

> **Vì sao phải tải đủ hết các phần?** Thiếu một phần `.part` thì ghép ra
> file ISO sẽ hỏng, không boot được. Nếu không chắc đã tải đủ, cứ vào lại
> trang Releases và so tên — các phần được đánh số `.00.`, `.01.`, `.02.`...
> liên tục không được nhảy số.

---

## 2. Ghép các phần `.part` thành một file ISO

### Cách 1 — Tự động, không cần gõ lệnh (khuyến nghị)

- **Trên Windows:** vào thư mục chứa các file đã tải, **bấm đúp** vào file
  `ghep-iso.bat`. Một cửa sổ đen (Command Prompt) sẽ hiện ra, tự ghép file
  thành `namios.iso` và in ra mã SHA256 để bạn so sánh.
- **Trên Linux/macOS:** mở Terminal tại thư mục đó, gõ:

  ```
  sh ghep-iso.sh
  ```

  Script tự ghép file và tự kiểm tra SHA256 giúp bạn (không cần so tay).

### Cách 2 — Gõ lệnh tay (nếu Cách 1 không chạy được)

- **Windows** (mở Command Prompt tại thư mục chứa file, gõ):

  ```
  copy /b namios-alpha-YYYYMMDD-amd64.iso.*.part namios.iso
  certutil -hashfile namios.iso SHA256
  ```

- **Linux/macOS:**

  ```
  cat namios-alpha-YYYYMMDD-amd64.iso.*.part > namios-alpha-YYYYMMDD-amd64.iso
  sha256sum -c namios-alpha-YYYYMMDD-amd64.iso.sha256
  ```

  (thay `YYYYMMDD` bằng ngày thật trong tên file bạn đã tải)

### Kiểm tra lại cho chắc

Mã SHA256 in ra ở bước trên **phải trùng khớp** với nội dung trong file
`*.iso.sha256` (mở bằng Notepad/trình xem văn bản để xem). Nếu **không
trùng** — file tải bị thiếu/hỏng — hãy xóa và **tải lại các phần `.part`**
rồi ghép lại, đừng ghi ra USB một file ISO chưa kiểm tra xong.

---

## 3. Ghi file ISO ra USB

Cắm USB rảnh (sẽ bị **xóa sạch**) vào máy, rồi chọn MỘT trong ba công cụ
dưới đây (đều là **phần mềm miễn phí của bên thứ ba**, không phải NaMiOS làm
ra — tải từ đúng trang chính thức để an toàn):

| Công cụ | Dùng trên | Tải tại | Ghi chú |
| --- | --- | --- | --- |
| **Rufus** | Windows | rufus.ie | Quen thuộc, nhanh, phổ biến nhất với người dùng Windows |
| **balenaEtcher** | Windows / macOS / Linux | balena.io/etcher | Giao diện đơn giản 3 bước, ít tùy chọn dễ bấm nhầm |
| **Ventoy** | Windows / Linux | ventoy.net | Cài 1 lần lên USB, sau đó chỉ cần **chép file .iso vào USB** (không phải ghi lại mỗi lần đổi bản ISO) — hợp nếu bạn hay thử nhiều bản |

### Dùng Rufus (Windows)

1. Mở Rufus (không cần cài đặt, chạy thẳng file tải về).
2. Mục **Device**: chọn đúng USB của bạn — **kiểm tra kỹ dung lượng/tên ổ**,
   chọn nhầm ổ khác sẽ mất dữ liệu ổ đó.
3. Mục **Boot selection**: bấm **SELECT**, trỏ tới file `namios.iso` vừa ghép.
4. Để các tùy chọn khác ở mặc định, bấm **START**.
5. Nếu Rufus hỏi kiểu ghi (ISO Image mode / DD mode) — chọn **ISO Image
   mode** nếu được hỏi.
6. Đợi tới khi thanh tiến trình báo xong (vài phút tùy tốc độ USB).

### Dùng balenaEtcher (mọi hệ điều hành)

1. Mở Etcher → **Flash from file** → chọn `namios.iso`.
2. **Select target** → chọn đúng USB của bạn.
3. Bấm **Flash!** và đợi xong (Etcher tự kiểm tra lại sau khi ghi).

### Dùng Ventoy (nếu muốn dùng lại nhiều lần)

1. Cài Ventoy vào USB **một lần duy nhất** (chạy `Ventoy2Disk` và chọn đúng
   USB — bước này cũng xóa sạch USB).
2. Sau đó, mỗi lần muốn dùng NaMiOS, chỉ cần **mở USB ra như ổ đĩa bình
   thường** và **chép file `namios.iso` vào** — không cần ghi lại từ đầu.
3. Muốn đổi sang ISO khác (bản NaMiOS mới hơn, hoặc hệ điều hành khác):
   xóa/thêm file `.iso` trong USB là xong, Ventoy tự hiện menu chọn khi khởi
   động.

> **An toàn khi ghi USB:** đừng rút USB hay tắt máy giữa chừng lúc đang ghi —
> USB có thể hỏng, phải ghi lại từ đầu. Đợi đúng tới khi phần mềm báo **hoàn
> tất**.

---

## 4. Khởi động máy từ USB

1. Cắm USB đã ghi NaMiOS vào máy muốn chạy thử/cài.
2. Khởi động lại máy, và **ngay khi vừa bật nguồn**, bấm liên tục phím vào
   **Boot Menu** (menu chọn ổ khởi động) — phím tùy hãng máy:

   | Hãng máy | Phím Boot Menu thường dùng |
   | --- | --- |
   | Dell | F12 |
   | HP | F9 hoặc Esc |
   | Lenovo | F12 hoặc Novo button |
   | Asus | F8 hoặc Esc |
   | Acer | F12 |
   | MSI | F11 |
   | Máy tự lắp (mainboard thường) | Del hoặc F11/F12 (vào BIOS/UEFI) |

   Không chắc phím nào — thử các phím trên, hoặc tìm theo tên máy + "boot
   menu key" trên mạng.

3. Trong menu hiện ra, **chọn đúng tên USB của bạn** (thường ghi tên hãng
   USB, ví dụ "Kingston DataTraveler...", hoặc tên "Ventoy" nếu dùng Ventoy).
4. Nếu máy **không thấy USB trong Boot Menu**: vào BIOS/UEFI Setup (thường
   cũng phím Del/F2), tìm mục **Secure Boot** → tạm **tắt (Disable)**, và mục
   **Boot Mode** → thử **UEFI** (khuyến nghị) hoặc **Legacy/CSM** nếu UEFI
   không thấy USB. Lưu lại (thường phím F10) rồi thử lại bước 2.
5. Máy sẽ khởi động vào menu của NaMiOS (GRUB) — dùng phím mũi tên để chọn,
   Enter để xác nhận.

---

## 5. "Dùng thử" (Live) hay "Cài đặt" (Install) — chọn đúng việc bạn muốn

Menu khởi động NaMiOS cho hai lựa chọn khác nhau — **đọc kỹ trước khi chọn**:

| Lựa chọn | Việc gì xảy ra | Có an toàn cho ổ cứng máy bạn không? |
| --- | --- | --- |
| **Dùng thử (Live)** | NaMiOS chạy **thẳng từ USB, trong RAM** — mọi thứ bạn làm (mở app, đổi cài đặt...) **mất hết khi tắt máy** | **An toàn tuyệt đối** — KHÔNG đụng tới ổ cứng máy bạn, rút USB ra là máy trở lại y như cũ |
| **Cài đặt (Install → Calamares)** | Mở trình cài **Calamares**, bạn chọn ổ đĩa/phân vùng để NaMiOS **ghi dữ liệu thật lên đó** | **GHI ĐÈ** lên phân vùng/ổ đĩa bạn chọn trong trình cài — dữ liệu cũ ở đúng phần đó **sẽ mất**. Đọc kỹ từng màn hình, đừng bấm nhanh qua bước chọn ổ đĩa |

**Khuyên dùng:** lần đầu thử NaMiOS, hãy chọn **Dùng thử (Live)** trước để
xem giao diện, gõ tiếng Việt, mở thử ứng dụng — **không mất gì** nếu không
thích. Chỉ chọn **Cài đặt** khi bạn đã:

- Sao lưu xong dữ liệu quan trọng trên máy, và
- Chắc chắn muốn dùng NaMiOS thật trên máy đó (cài riêng ổ mới, cài cạnh
  Windows, hoặc thay hẳn Windows).

> **Trung thực về trình cài:** cơ chế để máy **đã cài xong** khởi động vào
> đúng màn hình đăng nhập đồ họa (SDDM) — thay vì màn hình dòng lệnh dùng
> cho bản Live/demo — đã được chuẩn bị trong mã nguồn nhưng **CHƯA được xác
> nhận bằng một lần cài thật + khởi động lại trên máy/VM thật**. Nếu sau khi
> cài xong máy bạn không vào được màn hình đăng nhập bình thường, đó là điều
> đội NaMiOS cần biết — xem mục 7 "Báo lỗi" bên dưới.

Sau khi cài xong và đăng nhập lần đầu, NaMiOS sẽ tự mở một cửa sổ **"Chào
mừng"** để bạn chọn bộ gõ (Telex/VNI), cỡ chữ, và tùy chọn chuyển dữ liệu từ
Windows — cửa sổ này **chỉ hiện một lần**, không làm phiền ở các lần đăng
nhập sau. Trong đó có nút mở **"Hướng dẫn nhanh cho người quen dùng
Windows"** — xem thêm tại
[`docs/huong-dan/HUONG-DAN-NHANH-WINDOWS.md`](HUONG-DAN-NHANH-WINDOWS.md)
(bản cài sẵn trong máy: menu Bắt đầu → gõ "hướng dẫn").

---

## 6. Lỗi thường gặp khi tải/ghép/ghi USB

| Hiện tượng | Có thể do đâu | Cách thử sửa |
| --- | --- | --- |
| Ghép xong, SHA256 **không trùng** | Thiếu/hỏng một phần `.part` khi tải | Xóa hết, tải lại TOÀN BỘ các phần `.part` (đừng chỉ tải lại phần nghi ngờ) |
| Rufus/Etcher báo lỗi khi ghi | USB lỗi, hoặc ISO ghép chưa xong/hỏng | Thử USB khác; kiểm tra lại SHA256 trước khi ghi |
| Máy không boot vào USB, cứ vào thẳng Windows/hệ cũ | Chưa bấm đúng phím Boot Menu, hoặc Secure Boot đang chặn | Xem lại mục 4 — thử tắt Secure Boot trong BIOS/UEFI |
| Vào được Boot Menu nhưng không thấy tên USB | USB ghi lỗi, hoặc máy chỉ hỗ trợ Legacy/CSM | Ghi lại USB; thử đổi Boot Mode giữa UEFI/Legacy trong BIOS |
| Màn hình đen sau khi chọn "Dùng thử" | Xem phần xử lý sự cố hiển thị trong tài liệu kỹ thuật của dự án (máy không có GPU rời có cơ chế dự phòng riêng) | Đợi vài phút; nếu vẫn đen, ghi lại thông tin máy (tên máy, có GPU rời hay không) để báo lỗi |

---

## 7. Báo lỗi / cần hỗ trợ

Đây là bản **ALPHA dùng thử**. Mọi lỗi gặp phải (không boot được, cài xong
không vào được desktop, thiếu driver máy in/Wi-Fi...) xin báo tại:

> **https://github.com/NamDoji/NaMiOS/issues**

Khi báo lỗi, càng ghi rõ càng giúp được nhanh: tên/model máy, USB dùng công
cụ nào (Rufus/Etcher/Ventoy), chọn Dùng thử hay Cài đặt, và màn hình dừng
lại ở bước nào.
