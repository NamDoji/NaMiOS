# NaMiOS — Preset Wine mặc định cho người dùng (`~/.config/namios-wine`)

- **Thuộc nhiệm vụ:** lớp thân thiện U13-10 ("Chạy phần mềm Windows",
  `namios-windows-app`). **KHÔNG phải** chính công cụ cách ly
  `namios-wine-capsule` (đó là `docs/specs/WINE-CAPSULE.md`, một kỹ sư
  khác sở hữu) — thư mục này chỉ chứa **preset tĩnh** mà
  `namios-windows-app` đọc; không có script/daemon nào sống ở đây.
- **verified_on_host: NO** cho mọi file trong thư mục này (xem chi tiết
  trong từng file).

## Nội dung

| File | Dùng để làm gì |
| --- | --- |
| `default-font-substitution.reg` | Map tên font Microsoft thường gặp ("Arial", "Tahoma", "Segoe UI"...) sang font MỞ đã có sẵn trên NaMiOS (Liberation2/Carlito/Caladea/Noto/DejaVu), áp vào MỖI capsule Wine mới qua `wine regedit /S` ngay sau khi tạo. KHÔNG chứa font Microsoft thật — xem VN-005. |
| `recommended-winetricks-verbs.txt` | Danh sách winetricks verb gợi ý (Visual C++ runtime nhiều bản, GDI+, RichEdit, MSXML) cho phần mềm Windows nghiệp vụ/văn phòng cũ. Người dùng PHẢI được hỏi và đồng ý trước khi `namios-windows-app` cài — không bao giờ tự động/ngầm. |

## Vì sao đặt ở `/etc/skel` (không hard-code trong script)

`/etc/skel/.config/namios-wine/**` được sao chép thành
`$HOME/.config/namios-wine/**` cho **mỗi người dùng mới** khi tạo tài khoản
— cùng cơ chế chuẩn đang dùng cho `kdeglobals`/`dolphinrc` ở cấp trên. Người
dùng có thể tự sửa 2 file này sau khi có tài khoản (ví dụ thêm verb riêng
cho nhu cầu của họ) mà không cần sửa script hệ thống hay rebuild ISO.
`namios-windows-app` luôn đọc bản trong `$HOME/.config/namios-wine/` trước;
nếu bản đó bị xoá/hỏng, nó fallback về bản gốc tại
`/etc/skel/.config/namios-wine/` (chỉ đọc, không tự ghi lại vào `/etc/skel`).

## Không phải là gì

- **KHÔNG phải** cấu hình Plasma/skel khác (`kdeglobals`, `kwinrc`,
  `plasma-org.kde.plasma.desktop-appletsrc`...) — nhiệm vụ "lớp thân thiện
  Wine" này KHÔNG được đụng tới các file đó, và không đụng.
- **KHÔNG phải** "capsule recipe" JSON của U13-10 (xem
  `docs/compat/recipes/README.md`) — đó là schema riêng CHO TỪNG app cụ
  thể (hash bộ cài, runner ghim, test_workflow, verdict). Hai file ở đây là
  preset CHUNG, áp cho MỌI capsule mới, không gắn với một app cụ thể nào.
- **KHÔNG đảm bảo** phần mềm nào chạy đúng chỉ vì preset này được áp dụng —
  xem `docs/wine/WINE-COMPAT-MATRIX.md` cho kỳ vọng thực tế theo từng nhóm
  phần mềm (đặc biệt kế toán/ký số/in nghiệp vụ, phần lớn vẫn `blocked`).
