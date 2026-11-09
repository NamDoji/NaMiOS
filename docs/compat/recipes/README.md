# Capsule recipes (minh họa) — U13-10

Thư mục này chứa **template minh họa, CHƯA KIỂM THỬ** cho schema "capsule
recipe" mô tả ở `docs/specs/WINE-CAPSULE.md` §5, dùng bởi công cụ
`namios-wine-capsule create --recipe <file.json>` (xem
`distro/live-build/config/includes.chroot/usr/local/bin/namios-wine-capsule`).

## Đây KHÔNG phải là gì

- **KHÔNG phải** `contracts/app-manifest.schema.json` — đó là manifest
  chính thức của App Center/catalog, do nhóm manifest sở hữu. Không sửa đổi
  file đó từ thư mục này.
- **KHÔNG phải** `catalog/recipes/*.json` — đó là allowlist 6-action cấp
  thấp (`create_prefix`/`install_dependency`/`set_registry_value`/
  `run_installer`/`verify_file`/`create_launcher`) do WP10 (`src/namios_recipe/`)
  sở hữu và `RecipeEngineImpl.parse`/`dry_run` đọc trực tiếp. File JSON ở
  đây có **schema khác** (xem `docs/specs/WINE-CAPSULE.md` §4 cho bảng so
  sánh ba lớp) — đừng nạp nhầm file ở đây vào recipe engine đó.
- **KHÔNG phải** bằng chứng app chạy được. Mọi file ở đây có
  `verdict.status = "untested"` và các trường hash/runner để `null` hoặc
  giá trị placeholder rõ ràng không phải hash thật.

## Dùng để làm gì

Mẫu để người viết recipe thật (cho một app Windows cụ thể, có bộ cài thật
trong tay) sao chép, điền giá trị thật (sha256 của bộ cài, runner đã test,
winetricks verbs đã xác nhận cần thiết, kịch bản test đo được), rồi chạy:

```
namios-wine-capsule create <app-id> --recipe docs/compat/recipes/<file>.json
```

Sau khi có **bằng chứng chạy thật** (log + hash khớp + kịch bản test đã làm
tay và ghi kết quả), recipe đã điền nên được chuyển ra khỏi thư mục minh họa
này (ví dụ lưu cùng hồ sơ app trong `qa/evidence-index/` hoặc nơi nhóm QA
quyết định) — thư mục `docs/compat/recipes/` chỉ giữ **template rỗng/mẫu**,
không giữ hồ sơ app thật đã verified, để tránh người đọc nhầm "có file ở đây
nghĩa là đã test".

## Hai mẫu hiện có

| File | Minh họa cho | Winetricks verbs mẫu | Ghi chú |
| --- | --- | --- | --- |
| `notepadplusplus-template.json` | App Win32 nhẹ, không cần .NET (kiểu Notepad++) | `corefonts` | Soi cùng `catalog/recipes/sample-notepad-plusplus.json` (6-action cấp thấp, đã có sẵn trong repo) để thấy 2 tầng khác nhau của CÙNG MỘT app minh họa — xem `docs/specs/WINE-CAPSULE.md` §4. |
| `dotnet-winforms-generic-template.json` | App WinForms chạy trên .NET Framework | `dotnet48` | `docs/specs/DAC_TA_HE_DIEU_HANH.md` §"WinForms trên .NET hiện đại": cài runtime .NET không mang WinForms sang Linux — đây chỉ là khung thử, KHÔNG bảo đảm một WinForms app bất kỳ chạy được. |

Cả hai đều có `verdict.status: "untested"`, `source.installer_sha256: null`
(chưa chốt bản/bộ cài cụ thể nào) và `scope.network/usb: "deny"` theo mặc
định an toàn nhất.

## Trước khi tin một recipe đã điền thật

Đối chiếu với cửa kiểm chứng U13-10 (`docs/specs/WINE-CAPSULE.md` §7):
recipe có hash bộ cài đã chốt + `test_workflow` đã làm tay trên máy thật +
chạy thử cùng lúc với một app khác (kiểm DLL không xung đột) + (nếu claim
"đã kiểm cách ly home") đã chạy với `bwrap` có mặt, không phải nhánh suy
giảm. Thiếu bất kỳ điều nào, giữ `verdict.status` ở `untested`/`experimental`
— không tự nâng lên `task_verified`.
