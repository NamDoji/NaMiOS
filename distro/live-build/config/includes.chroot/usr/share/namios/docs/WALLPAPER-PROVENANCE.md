# NaMiOS — Wallpaper / Login-Background Provenance Ledger

**Status:** `verified_on_host: NO`. Không có bản build/boot thật nào được chạy để kiểm
chứng các nhận định trong tài liệu này ngoài việc mở trực tiếp từng file ảnh bằng
Pillow/trình xem ảnh trên máy soạn tài liệu. Không có `git commit`/push nào được
thực hiện bởi việc tạo tài liệu này.

**Mục đích:** ghi lại nguồn gốc/quyền sử dụng của TỪNG file ảnh hiện có trong
`usr/share/wallpapers/**`, để hội đồng pháp lý tư liệu (theo UX12-025/UX12-048)
có một danh sách dứt khoát: cái gì AN TOÀN phát hành, cái gì phải gỡ/thay trước
khi phát hành. Tài liệu này KHÔNG tự ý xoá file nào — chỉ gắn cờ.

**Phạm vi sửa đổi của soạn giả (wave này):** chỉ tạo mới 5 gói hình nền ở mục A
bên dưới + chính tài liệu này. Không đụng tới 20 gói đã có (mục B), không đụng
`usr/share/backgrounds/**`, không đụng SDDM/Plymouth/theme Plasma, không đụng
`design/wallpaper-manifest.json`.

---

## A. Hình nền MỚI tạo trong wave này — AN TOÀN phát hành (procedurally generated)

Cả 5 gói dưới đây được tạo **100% bằng thuật toán** (Python + Pillow): gradient
toán học nhiều điểm dừng màu, hình học vector (đường cong Bézier bậc 3 tự viết
cho hình cánh sen, lưới hình thoi, vòng tròn đồng tâm, tam giác toả tia kiểu
"mặt trời"), tô màu bằng đúng mã hex trong
`usr/share/namios-branding/logo/brand.json`. **Không có bất kỳ ảnh chụp, ảnh
kho (stock), hay output từ mô hình AI sinh ảnh (diffusion/GAN) nào được dùng
làm input.** Không có mạng internet, không có file ảnh bên ngoài nào được đọc
trong quá trình tạo — script generator chỉ gọi `PIL.ImageDraw`/`Image` với các
toạ độ/màu tính toán trực tiếp trong code.

Vì không có yếu tố "huấn luyện trên ảnh người khác" nào tham gia, các ảnh này
không mang rủi ro bản quyền/thương hiệu của bên thứ ba — tương đương CC0 (tác
giả giữ bản quyền tác phẩm gốc, cấp quyền dùng không giới hạn cho NaMiOS).
Generator script không được lưu trong repo (ngoài phạm vi "chỉ sửa
`includes.chroot/usr/share/wallpapers/**` + tài liệu này"); thuật toán được mô
tả đầy đủ bên dưới để có thể tái tạo/kiểm chứng độc lập mà không cần script.

**Ghi chú màu 11/11/2026 (không sửa thuật toán/PNG đã tạo):** 5 gói dưới đây
được tạo khi `brand.json` còn ở bản "Sen Việt" v2.0 — mã hex mô tả trong mục
"Mô tả thuật toán" bên dưới (`#122A3A`, `#92212E`, `son`/`canh_dark`/
`vang_tam`/`vang_nuoc`...) là ghi chép ĐÚNG THEO PNG đã sinh ra, giữ nguyên để
bảo toàn tính xác thực nguồn gốc (provenance) — KHÔNG đổi để "khớp" bộ màu
mới. Nếu/khi wave hình nền tái sinh các gói này theo bảng NaMiOS v3 "Đông Sơn"
(xem `branding/kit/NaMi_Brand_DongSon_v1`), quy đổi tương ứng là: `muc_dem`
`#122A3A`→navy `#092D4F`; `vang_tam`/`vang_nuoc` (`#F2C66D`/`#BC8A43`)→gold
`#DEA93E`; `son`/`canh_dark`/`dai` (`#C93643`/`#AB2430`/`#92212E`, vai trò
hoa sen/hoạ tiết chính = "signature accent")→gold `#DEA93E` cũng được, hoặc
vermilion `#D64C3E` nếu muốn giữ sắc đỏ nổi bật hơn — cần sha256 lại toàn bộ
bảng trên sau khi tái sinh.

| ID gói | Tên hiển thị | Dùng cho | Kích thước cung cấp | sha256 (3840×2160.png) |
|---|---|---|---|---|
| `NaMiOS-21-Sen-Son-Rang-Dong` | Sen Son Rạng Đông | Desktop (sáng) | 3840×2160, 1920×1080 | `563a567fe6fd1e83772c6816bae5c1771eb6f7e7b19d3d731a5347ebfef51f80` |
| `NaMiOS-22-Hoa-Van-Hinh-Hoc` | Hoạ Văn Hình Học | Desktop (sáng) | 3840×2160, 1920×1080 | `2c4b35c51fe2b08a15ad57cbcf234e161d75e4b6a9ef6e10643ef154f50ff688` |
| `NaMiOS-23-Trong-Dong-Tia-Nang` | Trống Đồng Tia Nắng | Desktop (sáng) | 3840×2160, 1920×1080 | `d4c12ea330f257d1c5969cc0138b4b8b04071806778fa24346970981b89a32c6` |
| `NaMiOS-24-Chan-Troi-Bien-Dong` | Chân Trời Biển Đông | Desktop (sáng, tối giản) | 3840×2160, 1920×1080 | `a984987a56ab7bd108f53794645ed1b02eb3ca5a2ea1065ad09b1e924e118ef8` |
| `NaMiOS-25-Sen-Dem-Dang-Nhap` | Sen Đêm Đăng Nhập | **TỐI — màn hình đăng nhập/khoá máy** | 3840×2160, 1920×1080 | `647e2614c6bf146521c9cb8542b6da69fd1b2187212c2e3caa81da8210f252ca` |

sha256 của bản `1920x1080.png` tương ứng:
`NaMiOS-21`→`2365e2bb1d45c57568b85f484a378a809844ae4ed36aaf3503492a5054e69450`,
`NaMiOS-22`→`14d4e9f8815132399a16c5e0781eece2ada8a397d2d443e71e78222614b348cf`,
`NaMiOS-23`→`8e73df75078207422d05045e5389958306da7a133d0cb28d9415c4e76bdc8976`,
`NaMiOS-24`→`f62cb7d2b0cfc4461e153cfe2d41bd226b1a177dd2802c88c6a7000c078f18fc`,
`NaMiOS-25`→`3bd41b98aa5a9161c2f539e209d6c9dbf955265f34fbfd6a02d4420f530e96f7`.

Mỗi gói đóng gói đúng chuẩn Plasma `org.kde.image`:
```
NaMiOS-2x-.../
├── metadata.json              # KPlugin.Id/Name/Authors/License/Description
└── contents/
    ├── screenshot.png          # 400×225 (giữ cùng quy ước với 20 gói cũ)
    └── images/
        ├── 1920x1080.png
        └── 3840x2160.png
```
`License` trong mỗi `metadata.json` ghi rõ: *"CC0-1.0-equivalent — 100%
procedurally generated original artwork (no photographic input, no
AI-diffusion model, no third-party asset). Copyright NaMiOS / Do Chi Cuong &
Do Bao Nam, dedicated for unrestricted use within NaMiOS."*

### Mô tả thuật toán từng gói (để tái tạo độc lập)

1. **`NaMiOS-21-Sen-Son-Rang-Dong`** — nền gradient dọc 4 điểm dừng (xanh than
   đậm `#122A3A` ở trên → đỏ tía `dai #92212E` ở dưới, mô phỏng "rạng đông"),
   hoa sen hình học góc dưới-phải gồm 4 tầng cánh (10/9/8/7 cánh, co dần kích
   thước), mỗi cánh là đa giác lấy mẫu từ 2 đường Bézier bậc 3 đối xứng (hàm
   `petal_polygon`), màu theo tầng: `dai`→`canh_dark`→`son`→`vang_tam`. Thêm
   vài vòng tròn mờ màu vàng quanh tâm hoa (hiệu ứng "hào quang" nhẹ, Gaussian
   blur) + vignette tối 4 góc.
2. **`NaMiOS-22-Hoa-Van-Hinh-Hoc`** — nền gradient xanh than, phủ lưới hình
   thoi (2 chùm đường chéo 45°, màu `vang_nuoc`, alpha thấp) lấy cảm hứng từ
   hoạ tiết cửa bàn khoa/lưới mắt cáo truyền thống (hình học thuần tuý, không
   chép bất kỳ ảnh cửa gỗ/công trình cụ thể nào), điểm xuyết các viên kim
   cương nhỏ màu `vang_tam` tại một tập con chu kỳ của giao điểm lưới (random
   seed cố định = 1203, để tái lập đúng y hệt), cộng một dải ruy-băng chéo mờ
   màu `son`.
3. **`NaMiOS-23-Trong-Dong-Tia-Nang`** — mô-típ "mặt trời toả tia" (tâm tròn +
   2 lớp tam giác toả tia + nhiều vòng tròn đồng tâm + 2 dải chevron hình
   zíc-zắc) vẽ lại hoàn toàn bằng công thức lượng giác của riêng script này
   (hàm `draw_sun_rays`/`draw_rings`/`draw_chevron_band`), lấy cảm hứng Ở MỨC
   Ý TƯỞNG VĂN HOÁ CHUNG (hoạ tiết "mặt trời"/chim lạc/răng cưa xuất hiện trên
   nhiều mặt trống đồng Đông Sơn nói chung, là mô-típ dân gian cổ, không gắn
   với hiện vật/ảnh chụp bảo tàng cụ thể nào) — KHÔNG sao chép, KHÔNG dựa trên
   ảnh chụp của bất kỳ trống đồng thật/hiện vật bảo tàng cụ thể nào.
4. **`NaMiOS-24-Chan-Troi-Bien-Dong`** — thuần gradient: nửa trên là trời
   (xanh than → đỏ tía → vàng ấm), nửa dưới là "biển" phản chiếu (vàng → nâu
   đỏ → xanh than đậm), một đường chân trời vàng kim + vài vệt phản chiếu
   ngang mờ ngẫu nhiên (seed cố định = 42). Không mô tả địa danh cụ thể nào.
5. **`NaMiOS-25-Sen-Dem-Dang-Nhap`** (biến thể TỐI cho đăng nhập/khoá máy) —
   cùng công thức hoa sen hình học như mục 1 nhưng: (a) alpha cánh hoa hạ
   xuống 70–90/255 (mờ, không rực), (b) hoa đặt lệch sang 1/5 bên phải khung
   hình, (c) có thêm lớp phủ tối dần (gradient alpha đen) phủ 45% phía
   dưới-giữa khung hình để giữ vùng đặt đồng hồ/ô nhập mật khẩu luôn đủ tối,
   đủ tương phản cho chữ trắng — đúng quy ước thiết kế màn khoá máy. Đây là
   gói duy nhất trong 25 gói hiện có được thiết kế/gắn nhãn RÕ RÀNG là biến
   thể "login/lock" tối màu; việc thật sự NỐI nó vào cấu hình SDDM/màn khoá là
   việc của người khác (ngoài phạm vi sửa đổi của soạn giả — không đụng SDDM).

---

## B. 20 hình nền ĐÃ CÓ SẴN trước wave này — GẮN CỜ RỦI RO QUYỀN ẢNH

`NaMiOS-01-Sen-Viet` .. `NaMiOS-20-Bien-Dao-Viet-Nam` (toàn bộ nằm sẵn trong
`usr/share/wallpapers/` trước khi wave này bắt đầu). Mỗi gói có:
`contents/images/3840x2160.jpg` (~1.0–2.5MB, ảnh RGB 3840×2160, cực kỳ
photorealistic — khi mở trực tiếp 2 ảnh mẫu (`NaMiOS-02-Vinh-Ha-Long`,
`NaMiOS-09-Co-Do-Hue`) để kiểm tra bằng mắt, chúng không khác gì ảnh chụp du
lịch chuyên nghiệp thật — và `metadata.json` với **đúng cùng một chuỗi License**
lặp lại y hệt cho cả 20 gói:

> `"License": "Tài sản thương hiệu NaMiOS — ảnh minh hoạ tạo bằng AI (chưa tuyên bố nhãn hiệu đã đăng ký)."`

### Vì sao bị gắn cờ "RỦI RO — PHẢI GỠ HOẶC THAY TRƯỚC KHI PHÁT HÀNH"

1. **Không có bằng chứng cấp phép/nguồn gốc nào được ghi lại** — không có
   `rights_evidence`, không ghi công cụ sinh ảnh, không ghi ngày sinh, không
   ghi seed/prompt, không ghi model. Chuỗi "ảnh minh hoạ tạo bằng AI" là lời
   tự khai, không kèm bằng chứng kiểm chứng được — đúng định nghĩa "rights
   UNKNOWN" mà đợt rà soát trước đã nêu.
2. **Mức độ photorealistic cao = rủi ro cao hơn hẳn so với phong cách
   hình-hoạ/vector.** Ảnh mô phỏng gần như y hệt ảnh chụp du lịch (ánh sáng,
   phản chiếu nước, hậu cảnh tiền cảnh đúng bố cục stock-photo điển hình).
   Mô hình sinh ảnh AI photorealistic có rủi ro tái tạo lại bố cục/đặc trưng
   của ảnh chụp có bản quyền từng xuất hiện trong dữ liệu huấn luyện ("memoi
   hoá" tác phẩm nguồn) — rủi ro này tăng theo mức độ giống ảnh thật, và các
   ảnh này gần như không phân biệt được với ảnh kho (stock) thật bằng mắt
   thường.
3. **10/20 ảnh mô tả địa danh/di tích được xác định rõ ràng theo tên riêng**
   (Vịnh Hạ Long, Cố Đô Huế, Hội An, Tràng An, Phong Nha, Tháp Mỹ Sơn — đều là
   Di sản Thế giới UNESCO; cộng Hồ Gươm, trống đồng Đông Sơn...). Gắn tên địa
   danh cụ thể vào một ảnh có nguồn gốc không rõ làm tăng rủi ro kép: (a) rủi
   ro bản quyền ảnh như mục 2, (b) rủi ro "gắn nhãn sai/không xác minh địa
   điểm" nếu ảnh AI vẽ sai đặc điểm thật của địa danh (ví dụ: không ai xác
   minh bố cục/chi tiết trong ảnh có đúng với địa danh thật hay không).
4. **Mâu thuẫn tài liệu nội bộ, cần hội đồng đối chiếu:** `design/wallpaper-
   manifest.json` (cùng repo) ghi rõ ở `$meta.status`:
   > *"0 ẢNH THẬT TRONG REPO NÀY. Toàn bộ mục dưới đây là PLACEHOLDER... KHÔNG
   > dùng bất kỳ mục nào trong file này để đóng gói ISO hay hiển thị làm hình
   > nền thật cho tới khi rights_evidence được thay bằng bằng chứng cấp
   > phép/quyền sử dụng thật, có người ký duyệt."
   Nhưng 20 gói ở mục B này **đã thực sự nằm trong `includes.chroot`** (tức
   SẼ được đóng vào ISO nếu build chạy) — một khoảng trống quy trình: manifest
   kế hoạch nói "chưa có ảnh thật/chưa duyệt", trong khi file ảnh thật đã tồn
   tại sẵn trong cây đóng gói. Hội đồng pháp lý tư liệu (UX12-025/UX12-048)
   cần đối chiếu hai nơi này.
5. **Một bản sao phái sinh của ảnh bị gắn cờ đã được đặt làm hình nền MẶC ĐỊNH
   thật** — `distro/live-build/config/hooks/normal/0400-qemu-desktop-
   autologin.hook.chroot` ghi đè hình nền gói "Next" mặc định của Plasma 6
   bằng `/usr/share/backgrounds/namios/namios-desktop-default.png`, và comment
   trong chính hook đó ghi: *"Hinh nen DESKTOP mac dinh = Vinh Ha Long (Cuong
   chon anh dep nhat trong 20 anh VN)"*. File này có sha256
   `620842c6697dae949f64de0aaa002c963e4e8c3d183d69ca6f2fd6294db98e85` — khác
   byte-for-byte với `NaMiOS-02-Vinh-Ha-Long/contents/images/3840x2160.jpg`
   (`75ebb3f6...`, do re-encode PNG từ JPG) nhưng là **cùng một bức ảnh Vịnh
   Hạ Long**, cùng nguồn gốc không rõ, cùng rủi ro ở mục 1–3. File này nằm
   ngoài phạm vi sửa đổi được giao (`usr/share/backgrounds/**` không thuộc
   `usr/share/wallpapers/**`) nên KHÔNG bị đụng vào, chỉ ghi nhận ở đây để
   hội đồng biết: nếu gỡ `NaMiOS-02-Vinh-Ha-Long`, hình nền desktop mặc định
   thật đang build cũng phải được thay, không chỉ xoá gói wallpaper.

### Danh sách đầy đủ 20 gói bị gắn cờ + sha256 (ảnh `3840x2160.jpg`)

| ID gói | Tên | sha256 |
|---|---|---|
| NaMiOS-01-Sen-Viet | Sen Việt | `fb8740032a9efdc7338302a68c47efb6a0527a63e5897f5fc11f92889c91906c` |
| NaMiOS-02-Vinh-Ha-Long | Vịnh Hạ Long | `75ebb3f61a10b8debee4342fc62c967cf31202aa068c83957b8c6768068f0f5b` |
| NaMiOS-03-Bien-Da-Nang | Biển Đà Nẵng | `afd64dfd4e7c6a0d93c6caed9f2ded8f165f9a1f0f7feafd1edf857e0e7a2b10` |
| NaMiOS-04-Vinh-Nha-Trang | Vịnh Nha Trang | `96315333a073f15ffc7c9e16630c24cb2f135e87353e9baf114443417024079e` |
| NaMiOS-05-Bien-Phu-Quoc | Biển Phú Quốc | `784d03d0783a96c2574d85505d45153f30ae9e0ddd31a69669f4895872adee65` |
| NaMiOS-06-Bien-Con-Dao | Biển Côn Đảo | `4090af70bed18bc02b1f6db2de2e8e27f19ef12b42a1baa0b0e4a0ce241f7bfd` |
| NaMiOS-07-Trang-An | Tràng An | `97faccb07368ed6b4850791ee20f02e2c7d9b667e2b4ad730de21a7b741c9601` |
| NaMiOS-08-Hoi-An | Hội An | `310fc8135dfc986ce96f49da3f955e670fff98f98ad9467a5d7b9e9e53fe5968` |
| NaMiOS-09-Co-Do-Hue | Cố Đô Huế | `fb32a02e220b72515044848cab765cac1eefa8f67a92f930423664e5858f1a46` |
| NaMiOS-10-Ruong-Bac-Thang-Sa-Pa | Ruộng Bậc Thang Sa Pa | `be6e2d00a40bd142ba4c6ba019712f8a7d702d2a2f6a296200af2789ce43ae3f` |
| NaMiOS-11-Cao-Nguyen-Ha-Giang | Cao Nguyên Hà Giang | `cf4b209e07f77e915dd509ee44bd5e94e33a96ddec495c7c582d1a7499f03287` |
| NaMiOS-12-Thac-Ban-Gioc | Thác Bản Giốc | `537ab7b39d31e48f9adebb18baa88e09f5af2c15178a82cda781e9f2c1c30b0c` |
| NaMiOS-13-Phong-Nha | Phong Nha | `115162e5351488e7391681f787b50b3b7d3df4de26b3c4845efc17f30a5c157d` |
| NaMiOS-14-Da-Lat | Đà Lạt | `40a2b724def9ca53f64239e15175cd2f0bcfafcb6b09346298e2daedc661d319` |
| NaMiOS-15-Mien-Tay-Song-Nuoc | Miền Tây Sông Nước | `970ebc35bb77061f44734f1bbc73c7db1d9872c0552d8c22f7b3184836611bb0` |
| NaMiOS-16-Cao-Nguyen-Ca-Phe | Cao Nguyên Cà Phê | `8d10264ded427c5bfa3444a93cd33a0b0206eb7cdbcb2acc8215aaa032d1e85d` |
| NaMiOS-17-Hoa-Van-Trong-Dong-Son | Hoa Văn Trống Đồng Sơn | `35ab0187302106c6eb24c93206f290f35e13202374e41d6a4b605dfcb8bf52a1` |
| NaMiOS-18-Thap-My-Son | Tháp Mỹ Sơn | `ee20b79057b51ea7819d2979282a42a7165d89a2ca585ddf798a567734f14b76` |
| NaMiOS-19-Ho-Guom | Hồ Gươm | `64473dc4fbc06722b2c3698611e2da4f764544a7fe080d3ca9cc469687a21514` |
| NaMiOS-20-Bien-Dao-Viet-Nam | Biển Đảo Việt Nam | `6008831b93fb4164f7a1717ddc44bd5f6ef5da531fcdf92b9cd206eb78a6de05` |

**Khuyến nghị:** GỠ hoặc THAY toàn bộ 20 gói trên bằng ảnh có
`rights_evidence` thật (hợp đồng/giấy phép kho ảnh ghi rõ quyền phân phối lại
trong một bản phân phối Linux) — hoặc thay bằng ảnh phong cách hình-hoạ/vector
hoàn toàn (như mục A) không có rủi ro "memo hoá ảnh chụp thật" — **trước khi
đóng ISO phát hành chính thức**. Đây là NHẬN ĐỊNH của soạn giả theo đúng yêu
cầu giao việc ("CRITICALLY licensing-clean... flag any pre-existing image...
as must remove or replace before release"); quyết định cuối cùng (gỡ/giữ/thay)
thuộc hội đồng pháp lý tư liệu + chủ dự án, KHÔNG tự ý xoá trong wave này.

---

## C. Tổng kết nhanh cho người duyệt

- **AN TOÀN phát hành ngay:** 5 gói mục A (`NaMiOS-21`..`NaMiOS-25`) — ảnh gốc
  100%, không có input ảnh chụp/AI-diffusion nào, license CC0-tương đương ghi
  rõ trong từng `metadata.json`.
- **RỦI RO — chặn phát hành cho tới khi xử lý:** 20 gói mục B
  (`NaMiOS-01`..`NaMiOS-20`) + 1 file phái sinh ngoài phạm vi
  (`usr/share/backgrounds/namios/namios-desktop-default.png`, bản sao của
  `NaMiOS-02-Vinh-Ha-Long`, hiện đang là hình nền desktop MẶC ĐỊNH thật theo
  hook build 0400).
- **Khoảng trống quy trình cần hội đồng đối chiếu:** `design/wallpaper-
  manifest.json` nói "0 ảnh thật/toàn placeholder", nhưng 20 ảnh thật đã nằm
  sẵn trong cây đóng gói ISO — hai nguồn thông tin đang mâu thuẫn nhau.

Không có thay đổi nào ở mục này đụng tới SDDM, theme Plasma, hay cấu hình
skel — đúng ràng buộc được giao.
