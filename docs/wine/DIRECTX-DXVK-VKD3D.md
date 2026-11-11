# NaMiOS — DirectX qua Wine: DXVK + vkd3d (DirectX → Vulkan) cho đồ hoạ/game

- **Trạng thái:** `specified` — thiết kế tuyến đồ hoạ (DirectX→Vulkan) cho
  lớp Wine của NaMiOS. `verified_on_host: NO` cho MỌI kết luận "chạy
  được"/"có gói" dưới đây: host phát triển hiện tại **không có** wine/
  winetricks và **không truy cập được** `packages.debian.org`/`sources.
  debian.org` (bị chặn khi khảo sát 11/11/2026) nên **chưa `apt-cache show`
  xác minh được tên gói nào trên Debian 13 trixie thật** — xem §3.
- **Vì sao có file này:** toàn bộ ma trận Wine cũ (`WINE-COMPAT-MATRIX.md`,
  `WINE-CAPSULE.md`, ADR-0015) tập trung vào app **nghiệp vụ** (.NET/kế
  toán/ký số) và **cố ý im lặng về đồ hoạ/DirectX/game**. Đây là lỗ hổng
  thật: phần lớn giá trị "chạy phần mềm Windows" mà Wine làm **tốt nhất**
  trong thực tế lại là **game + app đồ hoạ DirectX**, và con đường để chúng
  chạy nhanh trên Linux là **DXVK/vkd3d (dịch DirectX sang Vulkan)** — thứ
  chưa được nhắc tới ở bất kỳ đâu trong repo. File này lấp lỗ hổng đó **một
  cách trung thực**, KHÔNG hứa hẹn quá mức.
- **KHÔNG thay đổi** quy tắc verdict của `docs/specs/COMPAT-ROUTING.md` §4
  hay thứ tự tuyến của ADR-0015 (`native → web → dotnet-native → mono → wine
  → wine+dotnet-framework → blocked`). Đồ hoạ/DirectX là **một biến thể của
  tuyến `wine`**, không phải tuyến mới.

## 0. TL;DR trung thực (đọc trước)

- **DXVK/vkd3d KHÔNG làm cho "mọi game Windows" chạy.** Nó dịch lời gọi
  **Direct3D 9/10/11 (DXVK)** và **Direct3D 12 (vkd3d-proton)** sang
  **Vulkan**, giúp nhiều game **không có chống gian lận kernel** chạy mượt
  hơn WineD3D (bản dịch DirectX→OpenGL mặc định của Wine). Nó **không** cấp
  driver kernel, **không** vượt được anti-cheat, **không** sửa được DRM/
  launcher chặn Linux.
- **Điều kiện tiên quyết cứng:** máy phải có **driver Vulkan hoạt động cho
  GPU thật** (Mesa cho Intel/AMD; driver NVIDIA riêng cho card NVIDIA). KHÔNG
  có Vulkan ICD → DXVK hoặc rơi về **llvmpipe (Vulkan phần mềm, cực chậm, gần
  như vô dụng cho game)** hoặc **thất bại khởi tạo thiết bị** — trong cả hai
  trường hợp, "cài DXVK xong" **KHÔNG** nghĩa là game chạy được. Công cụ
  `namios-wine-capsule` nay có **bước tiền-kiểm Vulkan** để nói thẳng điều
  này (§5).
- **CHẮC CHẮN `blocked` (giới hạn kiến trúc Wine toàn cầu, không riêng
  NaMiOS):** game có **chống gian lận chạy ở kernel** (Easy Anti-Cheat và
  BattlEye ở chế độ kernel, Riot **Vanguard**, nProtect **GameGuard**,
  Denuvo Anti-Tamper ở nhiều tựa) — anti-cheat nạp **driver kernel Windows**
  và/hoặc **cố ý phát hiện + từ chối Wine**. Wine chạy ở user-space, không
  nạp `.sys` kernel (ADR-0015, WineHQ) → **không có đường kỹ thuật** nào của
  DXVK/vkd3d sửa được việc này. KHÔNG bao giờ hứa các tựa này chạy.

## 1. Hai lớp dịch DirectX (đừng gộp)

| Lớp | Dịch gì | Thành phần | Trạng thái thực tế |
| --- | --- | --- | --- |
| **WineD3D** (mặc định có sẵn trong Wine) | Direct3D 1–11 → **OpenGL** (và có backend Vulkan thử nghiệm) | Nằm SẴN trong gói `wine` | Không cần cài thêm; **chậm hơn** DXVK cho D3D9–11; đủ cho app đồ hoạ nhẹ, không đủ cho game nặng hiện đại. |
| **DXVK** | Direct3D **9/10/11** → **Vulkan** | DLL PE `d3d9/d3d10core/d3d11/dxgi.dll` (build bằng MinGW) đặt **vào từng WINEPREFIX** | Lựa chọn tốt nhất cho **hiệu năng** game D3D9–11; **CẦN Vulkan ICD thật**. |
| **vkd3d / vkd3d-proton** | Direct3D **12** → **Vulkan** | `vkd3d-proton` (DLL PE `d3d12.dll`) đặt vào prefix; khác với **vkd3d** (thư viện native Linux của chính WineHQ, dùng cho D3D12 cơ bản) | D3D12 kém trưởng thành hơn DXVK; cần **Vulkan 1.1+** và GPU mới hơn. |

**Lưu ý tên dễ nhầm:** `vkd3d` (thư viện native của WineHQ, có thể được
Debian đóng gói thành `libvkd3d*`) **KHÔNG giống** `vkd3d-proton` (fork của
Valve, hiệu năng cao, phát hành PE DLL qua GitHub). winetricks có verb
`vkd3d` cài **vkd3d-proton** vào prefix — đừng nhầm với gói `libvkd3d` của
distro.

## 2. Cách áp DXVK/vkd3d vào MỘT capsule (per-prefix, không toàn hệ)

Đúng mô hình cách ly U13-10: DXVK được cài **vào từng WINEPREFIX riêng**,
KHÔNG cài toàn hệ. Có HAI con đường, cùng dùng cơ chế `winetricks_verbs`
đã có sẵn trong schema recipe (`WINE-CAPSULE.md` §5 — KHÔNG cần thêm trường
mới):

1. **Qua winetricks verb** (khuyến nghị, đơn giản nhất):
   - verb `dxvk` → cài DXVK (D3D9/10/11) vào prefix.
   - verb `vkd3d` → cài vkd3d-proton (D3D12) vào prefix.
   - Trong recipe:
     ```jsonc
     "winetricks_verbs": ["vcrun2019", "dxvk"]
     ```
   - **SỰ THẬT về winetricks `dxvk`:** verb này **tải DXVK từ GitHub release
     của doitsujin/dxvk** lúc chạy — tức cần Internet, và theo NET-003 của
     repo, "pin script winetricks KHÔNG tính là pin cả chuỗi cung ứng": phải
     tự ghi lại URL + hash của chính file DXVK tải về nếu cần tái lập. DXVK
     **không nằm sẵn** trong gói `winetricks` của Debian; `winetricks` chỉ
     là script điều phối tải.

2. **Install-from-release thủ công** (khi winetricks verb không có/không
   chạy được, hoặc cần pin đúng một phiên bản DXVK):
   - Tải tarball `dxvk-<ver>.tar.gz` từ `github.com/doitsujin/dxvk/releases`,
     chạy `setup_dxvk.sh install` **với `WINEPREFIX` trỏ đúng prefix của
     capsule** (KHÔNG chạy toàn hệ). Script đặt DLL + set DLL override
     (`WINEDLLOVERRIDES`) cho `d3d9,d3d10core,d3d11,dxgi` thành `native`.
   - vkd3d-proton tương tự từ `github.com/HansKristian-Work/vkd3d-proton`.
   - **Phải tự ghi URL + sha256** của tarball vào hồ sơ app (cùng kỷ luật
     hash như `installer_sha256`).

Dù dùng đường nào, verdict vẫn theo COMPAT-ROUTING §4 — "cài DXVK xong"
**không** tự nâng verdict; phải có **game chạy thật, đo được FPS/ổn định**
trên **GPU thật** (xem "quy tắc vàng" ADR-0015: GUI/khởi động ≠ chạy được).

## 3. Gói trên Debian 13 trixie — phải `apt-cache show` trên build host

**`verified_on_host: NO`** — KHÔNG xác minh được từ host này (packages.
debian.org chặn IP khi khảo sát). Danh sách dưới đây là **kiến thức cần xác
nhận**, KHÔNG phải xác nhận đã làm. Trên build host trixie THẬT, chạy
`apt-cache show <tên>` cho từng dòng TRƯỚC khi thêm vào bất kỳ package-list
nào; nếu tên sai, `lb build` sẽ báo "unable to locate package" — sửa tên,
đừng bỏ qua.

| Mục đích | Tên gói kỳ vọng (CẦN xác minh) | Ghi chú trung thực |
| --- | --- | --- |
| Wine | `wine`, `winetricks` | Đã được `0660-dotnet-compat.list.chroot` dựa vào (nguồn gói đang BẬT). |
| **Vulkan loader** (bắt buộc cho DXVK) | `libvulkan1` | Không có loader → không app Vulkan nào chạy. |
| **Vulkan ICD / driver GPU** | `mesa-vulkan-drivers` (Intel/AMD); NVIDIA cần driver riêng (ngoài main) | **Đây là phần quyết định** — không có ICD đúng cho GPU thật thì DXVK vô dụng (rơi về llvmpipe). |
| Công cụ chẩn đoán Vulkan | `vulkan-tools` (cung cấp `vulkaninfo`) | Dùng để kiểm "máy có Vulkan thật không" — hữu ích cho hỗ trợ. |
| vkd3d native (D3D12 cơ bản, KHÁC vkd3d-proton) | `libvkd3d1` / `libvkd3d-dev` (từ source `vkd3d` của WineHQ) | Có thể có trong trixie; KHÔNG thay thế vkd3d-proton cho game nặng. |
| **DXVK (PE DLL dựng sẵn)** | **Nhiều khả năng KHÔNG có gói drop-in trong Debian main** | Debian main không ship DLL PE của DXVK kiểu cài-thẳng-vào-prefix; con đường chuẩn là **winetricks `dxvk` (tải từ GitHub)** hoặc **install-from-release** (§2). Nếu build host trixie THẬT có gói `dxvk`/`dxvk-wine*`, dùng nó; nếu không → đi đường release. |
| **vkd3d-proton (PE DLL)** | **Nhiều khả năng KHÔNG có gói drop-in** | Như DXVK — qua winetricks `vkd3d` hoặc release GitHub của Valve/HansKristian-Work. |

**Quyết định gói (ai sở hữu gì):** gói Vulkan (`libvulkan1`,
`mesa-vulkan-drivers`, `vulkan-tools`) thuộc quyền **kiến trúc sư tương
thích/ảnh nền** (chủ `0660-dotnet-compat.list.chroot` + danh sách GPU/driver),
KHÔNG tự thêm ở lớp Wine thân thiện — xem khuyến nghị đã ghi trong
`config/package-lists/0600-wine.list.chroot.disabled`. DXVK/vkd3d-proton
(PE DLL) **không nên nhúng vào ISO ở alpha** (ngoài main, tải từ GitHub —
cần ADR nguồn-gói riêng theo CLAUDE.md "không nhúng repo/binary bên thứ ba
vào ISO khi chưa có ADR nguồn-gói"); để **người dùng/tester tự cài vào
capsule qua winetricks khi cần** (opt-in, có Internet).

## 4. Vì sao KHÔNG đưa `dxvk` vào danh sách winetricks verb MẶC ĐỊNH

`recommended-winetricks-verbs.txt` (bộ verb hỏi-cài-chung của
`namios-windows-app`) **cố ý KHÔNG** chứa `dxvk`/`vkd3d`, vì:

1. **Chỉ có ích cho app đồ hoạ/game**, vô ích (và tốn mạng/thời gian) cho
   app văn phòng/kế toán — đối tượng chính của NaMiOS. Cài mặc định cho MỌI
   capsule là sai.
2. **Cần Vulkan ICD thật**; cài DXVK trên máy không có GPU Vulkan là tạo kỳ
   vọng sai ("đã cài DXVK" mà game vẫn không chạy).
3. DXVK là lựa chọn **theo từng game** (đôi khi một game chạy TỐT HƠN với
   WineD3D mặc định) — thuộc **capsule recipe riêng cho game đó**, không
   phải preset chung.

→ Đường đúng: dùng **recipe template** `docs/wine/recipes/directx-game-dxvk-
template.json` cho từng game, tự điền + tự test.

## 5. Tiền-kiểm Vulkan trong `namios-wine-capsule` (mới)

Khi một recipe khai báo verb `dxvk`/`vkd3d*` trong `winetricks_verbs`,
`namios-wine-capsule` nay chạy một **bước tiền-kiểm Vulkan** TRƯỚC khi cài,
in ra **tình trạng THẬT** (không chặn, chỉ báo trung thực):

- Có `libvulkan.so.1` (Vulkan loader) trên máy không?
- Có ICD nào ở `/usr/share/vulkan/icd.d/*.json` không (driver GPU Vulkan)?
- Có `vulkaninfo` để người hỗ trợ tự kiểm sâu hơn không?

Nếu thiếu loader hoặc ICD, công cụ **CẢNH BÁO RÕ**: DXVK sẽ không có GPU
Vulkan để dịch tới → game nhiều khả năng **không chạy hoặc rơi về phần mềm
cực chậm**, và **"winetricks dxvk OK" KHÔNG đồng nghĩa game chạy được**. Đây
là áp dụng trực tiếp nguyên tắc "không bao giờ báo thành công giả" của
CLAUDE.md vào tuyến đồ hoạ.

## 6. Ánh xạ sang ma trận + verdict

- Game/app DirectX **nhẹ, cũ, không anti-cheat, không DRM chặn Linux** →
  kỳ vọng `wine-partial` (chưa kiểm chứng) — đáng thử qua DXVK, nhưng chỉ
  nâng verdict sau khi chạy thật trên GPU thật.
- Game có **anti-cheat kernel / Vanguard / GameGuard / nhiều Denuvo** →
  `blocked` (kiến trúc, toàn cầu).
- Game **D3D12** → `wine-partial` qua vkd3d-proton, kém chắc hơn D3D9–11.
- Xem `docs/wine/WINE-COMPAT-MATRIX.md` §3.2 (mục DirectX/game) cho bảng cụ
  thể + vocab trạng thái.

## 7. Nguồn (tham chiếu, truy cập 11/11/2026)

- `docs/adr/ADR-0015-dotnet-windows-compat-strategy.md` — Wine không nạp
  driver kernel; thứ tự tuyến; "quy tắc vàng" GUI≠chạy-được.
- `docs/specs/WINE-CAPSULE.md` §5 — schema recipe (dùng `winetricks_verbs`
  để cài DXVK, không cần trường mới).
- doitsujin/dxvk, HansKristian-Work/vkd3d-proton (GitHub releases) — nguồn
  DXVK/vkd3d-proton PE DLL khi đi đường install-from-release.
- **CHƯA xác minh** gói Debian trixie (packages.debian.org chặn host khảo
  sát) — mọi tên gói ở §3 là **cần `apt-cache show` trên build host thật**.
