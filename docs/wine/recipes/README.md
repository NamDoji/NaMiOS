# `docs/wine/recipes/` — capsule recipe cho tuyến đồ hoạ/DirectX (bổ sung cho app-presets kế toán)

- **Quan hệ với các thư mục recipe khác (đọc để khỏi nhầm "3 nơi"):**
  - `docs/compat/recipes/` — **template MINH HOẠ CHUNG** (Notepad++, WinForms
    .NET) do kỹ sư U13-10 khác sở hữu. Không sửa.
  - `includes.chroot/etc/skel/.config/namios-wine/app-presets/` — preset
    **kế toán/thuế VN** đã điền sẵn (hiện có `htkk.json`), được ship vào
    `$HOME` của mỗi người dùng.
  - **`docs/wine/recipes/` (thư mục này)** — recipe cho **tuyến đồ hoạ/
    DirectX/game** (DXVK/vkd3d), đặt cùng khối tài liệu `docs/wine/**` với
    `DIRECTX-DXVK-VKD3D.md` + `WINE-COMPAT-MATRIX.md` vì đây là phần tài liệu
    kỹ thuật, KHÔNG phải preset auto-ship vào `$HOME` (game là lựa chọn theo
    từng người, không cài sẵn cho mọi tài khoản). Dùng qua đường dẫn tuyệt
    đối với `--recipe`.
- **Cùng một schema** `docs/specs/WINE-CAPSULE.md` §5 như mọi recipe khác —
  `namios-wine-capsule create <app-id> --recipe <file>.json` đọc được ngay,
  KHÔNG cần sửa công cụ.
- **`verified_on_host: NO` cho mọi file ở đây** (`verdict.status: untested`,
  `installer_sha256: null`). Đọc `_comment_untested` đầu mỗi file.

## File hiện có

| File | Dùng cho | Điều kiện tiên quyết cứng |
| --- | --- | --- |
| `directx-game-dxvk-template.json` | **Template** game Windows DirectX 9–11 nhẹ/cũ, KHÔNG anti-cheat, KHÔNG DRM chặn Linux | Máy phải có **driver Vulkan thật cho GPU** (Mesa Intel/AMD, hoặc driver NVIDIA). Xem `../DIRECTX-DXVK-VKD3D.md`. |

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
