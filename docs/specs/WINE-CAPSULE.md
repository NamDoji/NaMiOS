# Wine Capsule có kiểm soát (U13-10)

- **Trạng thái:** `specified` — đã thiết kế + review logic (`bash -n` + đọc lại
  thủ công), **CHƯA chạy qua wine/winetricks/bwrap thật trên máy nào**. Host
  phát triển hiện tại không có 3 gói này (xem `CLAUDE.md` §"Môi trường build
  hiện tại"). Không tự suy diễn "sẽ chạy đúng trên máy thật" — danh sách test
  bắt buộc trước khi đổi trạng thái nằm ở §7.
- **Nguồn yêu cầu:** `docs/spec-package/NaMiOS_Phu_luc_13_Uu_tien_Nang_cap_va_Cong_Phat_hanh.md`
  dòng U13-10. **Cửa kiểm chứng (nguyên văn):** *"Hai app xung đột DLL không
  ảnh hưởng nhau; app đổi hash cần retest; malware fixture không đọc toàn bộ
  home."*
- **Công cụ hiện thực:** `distro/live-build/config/includes.chroot/usr/local/bin/namios-wine-capsule`
  (bash, chạy ở user thường — KHÔNG root; xem §6 cho lý do).
- **Phạm vi tài liệu này:** mô hình cách ly + schema recipe vận hành cho
  riêng công cụ `namios-wine-capsule`. KHÔNG thay thế, KHÔNG sửa đổi
  `contracts/app-manifest.schema.json` (manifest chính thức của catalog,
  do nhóm khác sở hữu) hay allowlist 6 action trong `src/namios_recipe/`
  (WP10 — recipe engine cấp build-manifest). Quan hệ giữa ba lớp này nằm
  ở §4.

## 1. Vì sao cần capsule (không chỉ "cài Wine rồi chạy")

Wine mặc định dùng **một** `WINEPREFIX` chung (`~/.wine`) cho mọi ứng dụng.
Hai ứng dụng Windows khác nhau cài vào cùng một prefix sẽ **ghi đè DLL/registry
của nhau** (ví dụ app A cần MSVCR100 bản cũ, app B cài đè bản mới — cả hai có
thể gãy). Đây chính là điều U13-10 gọi là "hai app xung đột DLL ảnh hưởng
nhau" nếu không xử lý.

Cách giải quyết chuẩn của hệ sinh thái Wine (không phải NaMiOS tự nghĩ ra):
**mỗi ứng dụng/nhóm ứng dụng một `WINEPREFIX` riêng**. `namios-wine-capsule`
hiện thực hóa điều này một cách có kỷ luật: mỗi app có một **capsule** là một
thư mục độc lập, không chia sẻ gì với capsule khác trừ các gói hệ thống nền
(wine, thư viện /usr) vốn vẫn read-only và chung cho toàn máy theo thiết kế.

## 2. Mô hình cách ly

### 2.1 Cấu trúc một capsule

```
~/.local/share/namios/capsules/<app-id>/
├── prefix/            # WINEPREFIX riêng của app này (KHÔNG chia sẻ)
│   ├── drive_c/...
│   └── dosdevices/
│       ├── c: -> ../drive_c
│       ├── y: -> ../../exchange      # ổ TRAO ĐỔI riêng — xem 2.3 (KHÔNG có z:)
│       └── (z: — ĐÃ GỠ, xem 2.2)
├── exchange/          # thư mục trao đổi tệp — cầu nối DUY NHẤT công bố
├── snapshots/         # *.tar.gz tạo bởi `snapshot`/tự động trước `restore`
├── capsule.json       # trạng thái cục bộ: wine/winetricks version, lịch
│                      #   sử hash file .exe đã chạy, verdict_status
├── wineboot.log / winetricks.log  # log thao tác cài đặt (để debug)
```

`<app-id>` theo đúng pattern `id` của `contracts/app-manifest.schema.json`
(`^[a-z0-9]+(?:[.-][a-z0-9]+)*$`) để một app có thể có cùng id ở cả manifest
catalog và ở capsule vận hành của nó — dễ đối chiếu chéo, không bắt buộc.

### 2.2 Gỡ ổ Z: — chặn đường "cửa sau" phổ biến nhất

Theo mặc định, Wine tạo `dosdevices/z:` trỏ vào `/` (gốc toàn bộ hệ thống
tệp Linux) để tiện cho các ứng dụng "duyệt file Linux" từ bên trong Windows.
Hệ quả: một EXE bên trong prefix có thể mở `Z:\home\<user>\...` và đọc
**bất kỳ tệp nào người dùng đọc được**, bất kể Desktop/Documents có bị
symlink hay không. `docs/threat-model.md` (B1) đã ghi nhận trước: *"Ranh
giới thật là cơ chế Linux duy trì (bubblewrap/AppArmor) + gỡ drive Z (chỉ
giảm tiếp xúc)"* — `namios-wine-capsule create` thực hiện đúng vế gỡ Z: này,
luôn luôn, không cần cờ bật/tắt.

### 2.3 Không symlink Desktop/Documents/Downloads thật

Theo mặc định, lần `wineboot --init` đầu tiên tạo các "thư mục kiểu Windows"
(`Desktop`, `My Documents`, `My Pictures`, `My Music`, `My Video`, `Downloads`,
`Templates`...) dưới `drive_c/users/<user>/` dưới dạng **symlink trỏ vào
$HOME thật** của người dùng (Desktop → `~/Desktop`, Documents → `~/Documents`,
...). Đây là tiện lợi cho người dùng thường nhưng là lỗ hổng cách ly: một
ứng dụng (hoặc fixture độc hại) chỉ cần gọi API Win32 chuẩn
(`SHGetKnownFolderPath`) để đọc thẳng Documents/Desktop **thật** của người
dùng — không cần biết gì về Z: hay đường dẫn Linux.

`namios-wine-capsule create` quét `drive_c/users/*/` sau khi `wineboot --init`
chạy xong; với mỗi thư mục kiểu Windows **đang là symlink trỏ ra ngoài
prefix**, nó bị xóa và thay bằng **một thư mục thật, rỗng, nằm trong chính
prefix**. Ứng dụng trong capsule vẫn thấy "có" Desktop/Documents (không lỗi
API), nhưng đó là bản rỗng cục bộ của capsule — không phải của người dùng
thật. Đã kiểm bằng test thủ công (symlink trỏ ra một thư mục "bí mật" giả
lập, sau `create` thư mục đó trở thành thật + rỗng) — xem nhật ký bàn giao
kèm commit này.

### 2.4 Ổ Y: — cầu nối tệp DUY NHẤT, được công bố

Vì Desktop/Documents không còn trỏ ra thật và Z: đã gỡ, ứng dụng trong
capsule **không có cách nào** đọc/ghi ra ngoài prefix theo mặc định. Để vẫn
dùng được (ví dụ: đưa file cần xử lý vào, lấy file kết quả ra),
`namios-wine-capsule create` tạo **ổ Y:** trỏ vào `exchange/` — một thư mục
con của CHÍNH capsule đó, KHÔNG phải `$HOME` thật. Người dùng tự copy file
cần thiết vào `~/.local/share/namios/capsules/<app-id>/exchange/` bằng trình
quản lý tệp bình thường, rồi trong ứng dụng Windows chọn ổ `Y:`. Đây là cầu
nối duy nhất và phải được **tự tay** làm mỗi lần — không tự động đồng bộ.

### 2.5 Lớp tùy chọn — cách ly tiến trình/mạng/USB bằng `bwrap`

Mục 2.2–2.4 giải quyết "ứng dụng tự nguyện dùng API chuẩn để tìm file người
dùng". Một malware fixture **cố ý** mở đường dẫn tuyệt đối (not qua Z:, mà
Wine dịch path kiểu Unix trực tiếp qua các API `wine_get_unix_file_name`/mở
file bằng cú pháp Unix nếu binary được build để làm vậy) vẫn là tiến trình
Linux thường — nó chỉ thực sự **không thấy** `$HOME` thật nếu bị nhốt trong
một **mount namespace riêng không bind `$HOME` vào đó**. Đó là lý do
`docs/threat-model.md` nói thẳng: **"prefix Wine KHÔNG phải ranh giới bảo
mật"** (COMP-008) và kiến trúc chỉ gọi tên các cơ chế Linux duy trì
(`bubblewrap`/AppArmor) là ranh giới thật.

`namios-wine-capsule` **không được phép tự thêm gói** (`bubblewrap` không có
trong bất kỳ package-list nào — kiến trúc sư tương thích sở hữu
`distro/packages`/0660 và các danh sách `0600-wine*`). Script xử lý trung
thực theo 2 nhánh:

- **Có `bwrap` trên máy** (`run` tự dò bằng `command -v bwrap`): bọc
  `wine <exe>` trong một sandbox `bwrap` **unshare pid/ipc/uts** +
  **mặc định unshare network** (deny-by-default, mở bằng `--network`) +
  `--dev /dev` của riêng bwrap (devtmpfs tối giản, **không có** node USB
  thật → USB mặc định chặn, không cần cờ riêng) + chỉ bind:
  - `prefix/` + `exchange/` của chính capsule (đọc-ghi),
  - **đúng một** thư mục chứa file `.exe` được chỉ định (chỉ đọc),
  - `/usr /lib /lib64 /lib32 /bin /sbin /opt /etc` (chỉ đọc — hệ thống
    nền, không phải dữ liệu cá nhân),
  - `/tmp/.X11-unix` + `$HOME/.Xauthority` CHỈ KHI có `$DISPLAY` (ngoại lệ
    hiển thị — xem giới hạn ở §8; đây CHÍNH LÀ kiểu ngoại lệ mà
    `docs/threat-model.md` SEC-004 yêu cầu phải ghi lại, không tuyên bố
    cách ly tuyệt đối),
  - KHÔNG bao giờ bind `$HOME` thật — biến `HOME` bên trong sandbox được
    đặt lại thành một thư mục giả `prefix/home-view/` rỗng.
  - Nếu `bwrap` **thất bại khi dựng sandbox** (ví dụ thiếu quyền
    unprivileged user namespace), script **DỪNG — KHÔNG chạy ứng dụng ra
    ngoài sandbox** (fail-closed). Không có lựa chọn "chạy tạm không an
    toàn" — im lặng hạ cấp bảo mật là điều CLAUDE.md cấm.
- **KHÔNG có `bwrap`:** script CẢNH BÁO RÕ bằng tiếng Việt rằng chỉ có cách
  ly ở mức 2.2–2.4 (prefix + thư mục rỗng), **không có** cách ly tiến
  trình/mạng/USB ở mức hệ điều hành cho lần chạy đó, và một fixture cố ý chỉ
  định đường dẫn tuyệt đối vẫn có thể đọc được các phần khác của `$HOME`.
  Đây là giới hạn đã biết — xem §8 — không phải lỗi ẩn.

**Kết luận trung thực:** lớp 2.2–2.4 (luôn bật, không cần gói thêm) chặn
*con đường mặc định* mà ứng dụng hợp lệ dùng để chạm vào home thật. Lớp 2.5
(tùy chọn, cần `bwrap`) mới là **ranh giới hệ điều hành thật** chặn cả ý đồ
cố tình. Gate U13-10 "*malware fixture không đọc toàn bộ home*" chỉ được coi
là ĐẠT khi test chạy với `bwrap` có mặt — xem case cụ thể ở §7.

## 3. Lệnh & cách dùng

```
namios-wine-capsule create <app-id> [--arch win32|win64] [--recipe <file.json>]
namios-wine-capsule run <app-id> <file.exe> [--network] [--usb] [--share <thư-mục>] [-- tham-số...]
namios-wine-capsule list
namios-wine-capsule snapshot <app-id> [tên-snapshot]
namios-wine-capsule restore <app-id> <tên-hoặc-đường-dẫn-snapshot> [-y]
namios-wine-capsule remove <app-id> [-y]
```

- `create`: tạo prefix (nếu chưa có), áp dụng cách ly §2.2–2.4, ghi
  `capsule.json`, và (nếu có `--recipe`) chạy các `winetricks_verbs` khai báo
  trong recipe + ghi nhận runner thực tế có khớp runner đã ghim hay không.
  **Không** tự chạy installer chính — đó là việc của `run` (xem dưới), để
  giữ đúng nguyên tắc "installer do người dùng cung cấp, chạy qua đường
  `run` được kiểm soát giống hệt mọi lần chạy khác".
- `run`: thực thi một `.exe` (có thể là bộ cài hoặc ứng dụng đã cài) trong
  capsule. Mỗi lần chạy, SHA-256 của file được ghi vào `capsule.json`; nếu
  khác lần trước (cùng tên file trong cùng capsule) → cảnh báo
  **"[CẦN RETEST]"** ngay lập tức, không tự suy ra vẫn ổn.
- `list`: liệt kê capsule hiện có (app-id, `verdict_status` cục bộ, số
  snapshot, kích cỡ, thời điểm tạo).
- `snapshot` / `restore`: đóng gói/khôi phục **đúng thư mục `prefix/`** bằng
  `tar.gz`. `restore` luôn tự động snapshot trạng thái hiện tại trước khi ghi
  đè (`pre-restore-<timestamp>.tar.gz`) và từ chối giải nén nếu tar chứa
  đường dẫn tuyệt đối hoặc `..` (chống ghi đè ngoài ý muốn).
- `remove`: xóa toàn bộ capsule (có xác nhận, trừ khi `-y`).

Mọi lệnh sai cú pháp/thiếu điều kiện đều in thông báo tiếng Việt rõ ràng và
**exit 0** — công cụ chẩn đoán/vận hành không được làm gãy script gọi nó.

## 4. Quan hệ với manifest/recipe-engine chính thức (không trùng, không sửa)

NaMiOS đã có hai lớp chính thức khác, **không thuộc phạm vi sửa đổi của tài
liệu này**:

| Lớp | Sở hữu | Vai trò |
| --- | --- | --- |
| `contracts/app-manifest.schema.json` | Nhóm manifest/catalog | Khai báo chính thức một app (mode, license, runtime, permissions, compatibility) — "nguồn sự thật" cho App Center. |
| `src/namios_recipe/` (6 action: `create_prefix`, `install_dependency`, `set_registry_value`, `run_installer`, `verify_file`, `create_launcher`) + `catalog/recipes/*.json` | WP10 (recipe engine) | Danh sách bước **khai báo** (declarative, allowlist) nạp vào `manifest.recipe[]`, được `RecipeEngine.parse`/`dry_run` kiểm trước khi coi là có thể cài — xem `docs/adr/0004-ho-so-khai-bao.md`. |
| **"Capsule recipe"** (`docs/compat/recipes/*.json`, schema ở §5 dưới) | Tài liệu này (U13-10) | Hồ sơ **vận hành** cho riêng `namios-wine-capsule`: winetricks verbs cần cài, runner ghim, phạm vi file/network/USB, kịch bản test, verdict. KHÔNG phải định dạng mà `RecipeEngineImpl.parse` đọc. |

Ví dụ liên hệ cụ thể: `catalog/recipes/sample-notepad-plusplus.json` (đã có
sẵn, do WP10 sở hữu) là chuỗi 6 action cấp thấp để *build-manifest* biết cài
Notepad++ ra sao (tạo prefix, `install_dependency` vcrun2019-x64, verify
hash, `run_installer`, set registry, tạo launcher). File ví dụ minh họa của
tài liệu này (`docs/compat/recipes/notepadplusplus-template.json`, xem §5)
mô tả **cùng một app đó** nhưng ở góc nhìn vận hành/test: dùng
`namios-wine-capsule` gọi `winetricks corefonts` trước, kịch bản test gõ
tiếng Việt có dấu, và trường `verdict` theo cùng enum với
`compatibility.status` của manifest chính thức. Hai file không mâu thuẫn —
chúng mô tả hai tầng khác nhau của cùng một app. Việc có nên **gộp** hai
schema trong tương lai (ví dụ thêm một khối `capsule` vào
`app-manifest.schema.json`) là quyết định của nhóm sở hữu `contracts/`,
không phải của tài liệu này.

## 5. Schema "capsule recipe"

Phiên bản đầu, dùng bởi `namios-wine-capsule create --recipe <file>` (qua
hàm `_recipe_read`/`apply_recipe` trong script) và bởi
`docs/compat/recipes/README.md`. Script chỉ đọc 6 trường vô hại
(`capsule_id`, `app.name`, `source.installer_sha256`, `runner.runner_id`,
`runner.prefix_architecture`, `winetricks_verbs`) bằng `python3`/`json`
(không `eval`); các trường còn lại (`scope`, `test_workflow`, `verdict`) là
**tài liệu/bằng chứng cho con người**, script không tự diễn giải chúng.

```jsonc
{
  "schema_version": "1.0",
  // ^[a-z0-9]+(?:[.-][a-z0-9]+)*$ — giống "id" của app-manifest.schema.json
  "capsule_id": "notepadplusplus-template",

  "app": {
    // Tùy chọn: khớp "id" trong contracts/app-manifest.schema.json nếu app
    // này đã có manifest chính thức. null nếu chỉ là template minh họa.
    "manifest_id": null,
    "name": "Tên hiển thị (tiếng Việt hoặc nguyên ngữ)",
    "publisher": "Tên nhà phát hành"
  },

  "source": {
    // cùng enum "source.acquisition" của app-manifest.schema.json
    "acquisition": "user_provided",
    "official_url": "https://... (trang tải chính thức)",
    // 64 hex thường, hoặc null nếu CHƯA chốt bản cụ thể — KHÔNG được bịa.
    "installer_sha256": null
  },

  "runner": {
    // Chuỗi `wine --version` MONG ĐỢI — script đối chiếu runner thật lúc
    // "create --recipe" và cảnh báo nếu lệch (tổ hợp chưa test).
    "runner_id": "wine-9.0 (Debian 9.0~repack-3)",
    "prefix_architecture": "win64" // "win32" | "win64"
  },

  // Mỗi phần tử phải khớp ^[A-Za-z0-9_.+-]{1,64}$ — đây là TÊN VERB
  // winetricks (định danh), KHÔNG phải lệnh; verb không khớp bị script
  // từ chối và ghi log "rejected_invalid_name", không chạy.
  "winetricks_verbs": ["corefonts"],

  "scope": {
    "filesystem": [
      // enum "scope" mượn từ app-manifest.schema.json permissions.filesystem,
      // CỘNG THÊM "exchange_folder" (khái niệm riêng của capsule, xem §2.4)
      // — đề xuất, CHƯA có trong contracts/app-manifest.schema.json chính
      // thức; cần nhóm sở hữu schema đó quyết định có gộp hay không.
      { "scope": "exchange_folder", "access": "read_write" }
    ],
    // "deny" | "allow_with_user_consent" — giống app-manifest.schema.json.
    // Hiện tại NHỊ PHÂN (toàn bộ mạng bật/tắt bằng --network khi "run"),
    // CHƯA lọc theo allowed_hosts như source.allowed_hosts của manifest.
    "network": "deny",
    // "deny" | "allow_with_user_consent" — trường MỚI, CHƯA có trong
    // contracts/app-manifest.schema.json (không có khái niệm USB ở đó).
    // Ở bản này --usb mới chỉ GHI NHẬN ý định, CHƯA thật sự map thiết bị
    // USB nào vào sandbox — xem giới hạn §8.
    "usb": "deny"
  },

  // Danh sách bước NGƯỜI kiểm thử làm tay trên máy thật — không phải lệnh
  // tự động. Bắt buộc phải có ít nhất 1 bước đo được (không chỉ "mở được").
  "test_workflow": [
    {
      "step": "Mở ứng dụng, gõ văn bản tiếng Việt có dấu, lưu vào ổ Y: (exchange/)",
      "expected": "File lưu đúng nội dung UTF-8, không lỗi font, không crash"
    }
  ],

  "verdict": {
    // cùng enum "compatibility.status" của app-manifest.schema.json
    "status": "untested",
    // 3 cờ ánh xạ trực tiếp 3 vế của cửa kiểm chứng U13-10 — xem §7
    "two_app_dll_isolation_tested": false,
    "hash_retest_required": false,
    "malware_fixture_home_read_blocked": null,
    "evidence_id": null,
    "last_tested": null
  }
}
```

Script **không bao giờ** tự ghi `verdict.status` thành `task_verified` —
giống nguyên tắc đã có cho `compatibility.status` (`docs/adr/0004...`,
`CLAUDE.md`): chỉ quy trình QA/evidence độc lập (ngoài phạm vi công cụ này)
mới được nâng trạng thái, sau khi có bằng chứng chạy thật.

## 6. Vì sao chạy bằng user thường, không root

`wine`/`winetricks`/`namios-wine-capsule` không bao giờ chạy bằng `sudo`/root
(`docs/adr/0001-linux-wine.md`: "không chạy wine/installer bằng root").
Prefix nằm dưới `$HOME` của chính người dùng (qua `$XDG_DATA_HOME`, mặc định
`~/.local/share`), nên quyền file Linux chuẩn đã ngăn user khác đọc prefix
của mình — không cần `chmod` đặc biệt ngoài `700` ở cấp thư mục capsule
(đã làm trong `cmd_create`). `bwrap` (khi có) tận dụng **unprivileged user
namespaces** (đã bật mặc định trên Debian từ nhiều bản, `sysctl
kernel.unprivileged_userns_clone=1`) — không cần setuid/sudo để dựng sandbox.

## 7. Ánh xạ sang cửa kiểm chứng U13-10 + test cần máy thật

| Vế cửa kiểm chứng | Cơ chế trong công cụ | Test thật cần làm (chưa làm — BLOCKED tại host này) |
| --- | --- | --- |
| **"Hai app xung đột DLL không ảnh hưởng nhau"** | Mỗi app-id một `WINEPREFIX` vật lý riêng (§2.1); không có bước nào trong script ghi vào prefix của app khác. | Tạo 2 capsule (vd `app-a`, `app-b`), cài **cùng một thư viện ở hai phiên bản khác nhau** vào mỗi bên bằng `winetricks` (ví dụ `vcrun2015` vs bản tự build khác version), xác nhận: (a) `diff -r` hai `prefix/drive_c/windows/system32` cho thấy không có ghi chéo; (b) gỡ/hỏng app A (xóa `prefix/drive_c` của A) không ảnh hưởng app B vẫn chạy được. |
| **"App đổi hash cần retest"** | `run` tính SHA-256 mỗi lần, so với `capsule.json.exe_history`, in `[CẦN RETEST]` khi khác — đã kiểm bằng test thủ công (đổi nội dung file giữa 2 lần `run`, xem log bàn giao kèm commit). | Trên máy thật: build 2 bản khác nhau của cùng 1 fixture (đổi 1 byte), xác nhận cảnh báo xuất hiện ĐÚNG ở lần `run` thứ hai, và xác nhận `winetricks_verbs`/`runner_id` lệch so với recipe ghim cũng bị cảnh báo (đã code trong `apply_recipe`, chưa chạy `winetricks` thật). |
| **"Malware fixture không đọc toàn bộ home"** | §2.2–2.5: gỡ Z:, bỏ symlink Desktop/Documents, cách ly mount namespace qua `bwrap` (không bind `$HOME` thật) khi có `bwrap`. | **Bắt buộc cần máy thật có `bwrap` cài sẵn** (chưa có trong package-list nào, xem §2.5): viết một fixture Win32 nhỏ cố tình mở `Z:\home\<user>\...`, `C:\users\<user>\Documents\...`, và (nếu còn Z:) đường dẫn tuyệt đối khác trong `$HOME` (ví dụ giả lập `~/.ssh/id_rsa`), chạy qua `namios-wine-capsule run` **CÓ** `bwrap`, xác nhận: (a) Z: không tồn tại (mở thất bại, không phải "thành công nhưng rỗng"); (b) Documents trong capsule là bản rỗng cục bộ; (c) mọi đường dẫn tuyệt đối ngoài prefix/exchange trả lỗi "No such file" ở mức OS (không tồn tại trong mount namespace) chứ không phải "permission denied" (khác nhau về bản chất: ENOENT ở mount namespace là KHÔNG THỂ BYPASS bằng leo quyền trong tiến trình; EACCES vẫn có thể bị bypass nếu tiến trình leo quyền). Lặp lại **không có** `bwrap` để xác nhận cảnh báo "cách ly yếu hơn" xuất hiện đúng và tài liệu không tuyên bố quá mức. |

## 8. Giới hạn đã biết (ghi rõ, không che giấu)

- **`bwrap` chưa có trong package-list nào** của NaMiOS (0600-wine chỉ có
  `wine`/`winetricks`; thêm gói thuộc quyền kiến trúc sư tương thích). Nếu
  không cài, U13-10 vế 3 (home-read) chỉ đạt mức "giảm tiếp xúc", không đạt
  mức "chặn hoàn toàn" — công cụ luôn nói rõ điều này khi chạy.
- **Chỉ hỗ trợ X11/XWayland cho hiển thị**, khớp với việc phiên desktop
  NaMiOS hiện tại chạy X11 (`plasmax11`, xem lịch sử commit
  `fix(boot): ép X11 autologin`). Dùng socket `/tmp/.X11-unix` nghĩa là ứng
  dụng trong capsule **chia sẻ phiên X11 với host** — một client X11 có thể
  quan sát/điều khiển phiên (giới hạn đã ghi sẵn ở `docs/threat-model.md`
  SEC-004, không phải lỗ hổng mới do công cụ này tạo ra). Wayland thuần
  chưa được hỗ trợ.
- **Âm thanh tắt mặc định** trong nhánh có `bwrap` (chưa có cách map hẹp
  theo thiết bị cho PipeWire/Pulse mà không mở rộng `$XDG_RUNTIME_DIR` một
  cách thô).
- **`--usb` mới chỉ ghi nhận ý định**, chưa thật sự ánh xạ thiết bị USB cụ
  thể vào sandbox (USB vẫn bị chặn hoàn toàn, kể cả khi dùng `--usb`, vì
  `/dev` tối giản của `bwrap` không có node USB).
- **`--network` là nhị phân** (toàn bộ mạng bật/tắt), chưa lọc theo
  `allowed_hosts` như `source.allowed_hosts` trong
  `contracts/app-manifest.schema.json`.
- **`--share <thư-mục>` mở một ngoại lệ read-write rõ ràng** — nếu dùng,
  phạm vi "không đọc toàn bộ home" chỉ còn đúng với các thư mục KHÔNG được
  `--share`. Công cụ luôn in cảnh báo khi cờ này được dùng (không âm thầm).
- Nếu file `.exe` được chỉ định nằm **ngay tại gốc** một thư mục lớn (ví dụ
  thẳng `$HOME/setup.exe` thay vì `$HOME/Downloads/vendor/setup.exe`), thư
  mục cha của nó (ở ví dụ này là toàn bộ `$HOME`) sẽ được bind read-only vào
  sandbox — khuyến nghị luôn đặt bộ cài trong một thư mục con riêng (hoặc
  copy vào `exchange/` qua ổ Y: trước, rồi trỏ `run` vào đó) để thu hẹp tối
  đa phạm vi lộ.
- Toàn bộ mục này là **`specified`** — tất cả câu "sẽ chặn"/"sẽ cảnh báo" ở
  trên đã verify bằng test thủ công KHÔNG CÓ wine/winetricks/bwrap thật
  (dùng script giả lập `wine`/`wineboot`/`winetricks`/`bwrap` để kiểm luồng
  bash + tạo symlink/Z: giả rồi xác nhận bị thay đúng) — xem §7 cho danh
  sách test cần làm lại trên máy thật trước khi đổi trạng thái.
