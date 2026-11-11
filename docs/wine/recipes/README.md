# `docs/wine/recipes/` — capsule recipe template theo CATEGORY (đồ hoạ/DirectX, .NET, bộ cài tổng quát)

- **Quan hệ với các thư mục recipe khác (đọc để khỏi nhầm "3 nơi"):**
  - `docs/compat/recipes/` — **template MINH HOẠ theo APP CỤ THỂ** (Notepad++
    = Win32 nhẹ + corefonts; `dotnet-winforms-generic-template.json` = nhảy
    THẲNG vào `dotnet48`) do kỹ sư U13-10 khác sở hữu. **Không sửa.** Các
    template ở thư mục này **KHÁC** chúng (xem cột "Khác gì bản compat" dưới)
    — không trùng lặp, bổ sung cho nhau.
  - `includes.chroot/etc/skel/.config/namios-wine/app-presets/` — preset
    **kế toán/thuế VN** đã điền sẵn (hiện có `htkk.json`), được ship vào
    `$HOME` của mỗi người dùng.
  - **`docs/wine/recipes/` (thư mục này)** — template capsule **theo CATEGORY**
    (đồ hoạ/DirectX/game qua DXVK/vkd3d; app .NET route-mono-trước; bộ cài
    tổng quát chẩn đoán), đặt cùng khối tài liệu `docs/wine/**` với
    `DIRECTX-DXVK-VKD3D.md` + `WINE-COMPAT-MATRIX.md` vì đây là phần tài liệu
    kỹ thuật, KHÔNG phải preset auto-ship vào `$HOME` (đây là khung THỬ theo
    từng người, không cài sẵn cho mọi tài khoản). Dùng qua đường dẫn tuyệt
    đối với `--recipe`. Mỗi file ánh xạ 1-1 với một category trong
    `WINE-COMPAT-MATRIX.md` §3.3.
- **Cùng một schema** `docs/specs/WINE-CAPSULE.md` §5 như mọi recipe khác —
  `namios-wine-capsule create <app-id> --recipe <file>.json` đọc được ngay,
  KHÔNG cần sửa công cụ.
- **`verified_on_host: NO` cho mọi file ở đây** (`verdict.status: untested`,
  `installer_sha256: null`). Đọc `_comment_untested` đầu mỗi file.

## File hiện có

| File | Category (↔ `WINE-COMPAT-MATRIX.md` §3.3) | Điều kiện tiên quyết / pitfall chính | Khác gì bản `docs/compat/recipes/` |
| --- | --- | --- | --- |
| `directx-game-dxvk-template.json` | Game/app **DirectX 9–11** nhẹ/cũ, KHÔNG anti-cheat, KHÔNG DRM chặn Linux | Máy phải có **driver Vulkan thật cho GPU** (Mesa Intel/AMD, hoặc driver NVIDIA). Xem `../DIRECTX-DXVK-VKD3D.md`. | Không có bản tương ứng ở compat — đây là template đồ hoạ duy nhất. |
| `dotnet-app-template.json` | App **.NET Framework** (WinForms/console) | Thử **Wine-Mono (verbs rỗng) TRƯỚC**, chỉ hạ xuống `dotnet40`/`dotnet48` khi thiếu runtime (ADR-0015). WPF nhiều khả năng hỏng trên Mono. | compat nhảy thẳng `dotnet48`; bản này theo **mono-first** (rẻ hơn) + cây quyết định fallback. |
| `generic-installer-template.json` | **Bộ cài tổng quát** (`.exe`/`.msi` lạ, chưa biết cần gì) | Prefix **sạch, verbs rỗng**; chỉ thêm phụ thuộc theo **thông điệp lỗi thật**. Kiểm tuyến web/native TRƯỚC (§3.1). | compat Notepad++ giả định Win32 nhẹ + corefonts; bản này KHÔNG giả định gì + có bước "cách báo lỗi". |

**`verified_on_host: NO` cho mọi file ở đây.** Mọi template là khung THỬ
chưa kiểm chứng — KHÔNG file nào tự nâng verdict lên `ready`.

## Cách dùng template .NET / bộ cài tổng quát (tóm tắt)

1. **Luôn thử tuyến RẺ HƠN trước** (ADR-0015 `native → web → …`): app có bản
   web / Linux native / tương đương NaMiOS (NaMiOffice, Firefox, Okular,
   Ark) không? Có → dùng cái đó, đừng mở Wine (xem `../WINE-COMPAT-MATRIX.md`
   §3.1).
2. `.NET`: dùng `dotnet-app-template.json` — **Wine-Mono trước** (verbs rỗng),
   chỉ thêm `dotnet40`/`dotnet48` khi app kêu thiếu runtime. App WPF nhiều
   khả năng hỏng trên Mono (giới hạn đã biết, không phải lỗi cấu hình).
3. Bộ cài lạ: dùng `generic-installer-template.json` — prefix sạch, thêm
   phụ thuộc TỪNG BƯỚC theo đúng lỗi thật; giữ lại **thông điệp lỗi gốc** +
   dòng cuối `winetricks.log`/`wineboot.log` (đã che bí mật) khi báo lỗi.
4. **Không bao giờ** nâng verdict vì "cài xong"/"mở được" — phải có công
   việc THẬT chạy đúng + `qa_independent` ký (COMPAT-ROUTING §4).

## Cách dùng template game

1. **Đọc `../DIRECTX-DXVK-VKD3D.md` TRƯỚC** — đặc biệt §0 (những gì CHẮC CHẮN
   `blocked`: game anti-cheat kernel / Vanguard / GameGuard / nhiều Denuvo)
   và §3 (DXVK không nằm trong gói Debian main → winetricks tải từ GitHub).
2. Sao chép file template, điền tên game + `installer_sha256` thật, điền
   `runner_id` bằng output `wine --version` thật sau khi test.
3. Kiểm GPU có Vulkan: `vulkaninfo --summary` (gói `vulkan-tools`). KHÔNG có
   ICD cho GPU thật → đừng kỳ vọng DXVK giúp được gì.
4. `namios-wine-capsule create <game-id> --recipe <file>.json` — công cụ tự
   chạy **tiền-kiểm Vulkan** vì recipe có verb `dxvk` (báo tình trạng thật).
5. Tự chạy `test_workflow` trên GPU thật; **KHÔNG** nâng verdict chỉ vì
   "game khởi động" — phải chơi được, ổn định (quy tắc vàng ADR-0015).

## Vì sao KHÔNG ship preset game cụ thể theo tên

Khác nhóm kế toán/thuế (owner nêu tên đích danh), game là lựa chọn cá nhân
rộng + thay đổi nhanh (bản vá, anti-cheat bật/tắt theo mùa) + rủi ro bản
quyền nếu gợi ý tải. Ship một **template trung thực + điều kiện tiên quyết**
đúng hơn là một danh sách game "chạy được" dễ lỗi thời và dễ bị hiểu là bảo
đảm.
