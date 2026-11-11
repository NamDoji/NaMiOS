# `app-presets/` — capsule recipe điền sẵn cho một app Windows cụ thể (kế toán/thuế VN)

- **Khác với 2 file CHUNG ở thư mục cha** (`../recommended-winetricks-verbs.txt`,
  `../default-font-substitution.reg`) — những file đó áp cho **mọi** capsule
  mới, không gắn app nào. Mỗi file trong `app-presets/` là một **"capsule
  recipe"** đúng schema `docs/specs/WINE-CAPSULE.md` §5 — giống hệt định
  dạng `docs/compat/recipes/*.json` (thư mục đó do kỹ sư U13-10 khác sở
  hữu, chỉ giữ TEMPLATE rỗng/minh họa chung, không phải nơi dành cho
  presets theo chủ đề). Thư mục này ship **presets đã điền theo nghiên cứu
  thật** cho đúng nhóm app owner ưu tiên (kế toán/thuế), đặt ở
  `etc/skel/.config/namios-wine/` theo đúng phạm vi việc được giao cho đợt
  này — không sửa/không trùng thư mục `docs/compat/recipes/`.
- **Dùng y hệt cách một capsule recipe thường được dùng** — không cần sửa gì
  trong `namios-wine-capsule` (công cụ đã hỗ trợ sẵn cờ `--recipe` đọc đúng
  schema này):
  ```
  namios-wine-capsule create <app-id> --recipe ~/.config/namios-wine/app-presets/<file>.json
  ```
- **`verified_on_host: NO` cho MỌI file ở đây** — mỗi file có
  `verdict.status: "untested"`, `source.installer_sha256: null` (chưa chốt
  bản cài cụ thể nào), và một mục `test_workflow` yêu cầu làm tay trên máy
  thật trước khi tin bất kỳ kết quả nào. Đọc kỹ trường `_comment_untested`
  ở đầu mỗi file — có thể yêu cầu thử một tuyến RẺ HƠN Wine trước (ví dụ
  Mono trực tiếp, không qua capsule) trước khi dùng recipe.

## File hiện có

| File | App | Vì sao được chọn ship preset (không phải mọi app đều có) |
| --- | --- | --- |
| `htkk.json` | HTKK — Hỗ trợ kê khai thuế (Tổng cục Thuế) | Duy nhất app kế toán/thuế owner ưu tiên có **route Wine khả tín** theo khảo sát 11/11/2026 (`docs/wine/WINE-COMPAT-MATRIX.md` §2): desktop .NET Framework 3.5 cổ điển, KHÔNG có SQL Server/USB-token-bắt-buộc TRONG bản thân app (ký số xảy ra riêng trên web eTax) — khớp đúng loại app Wine có cơ hội thật theo ADR-0015. Preset CHỈ phủ bước lập/xuất tờ khai offline, KHÔNG phủ ký/nộp. |

## Vì sao KHÔNG có preset cho MISA SME / iTaxViewer / công cụ ký số BHXH

Cố ý không ship để tránh ngụ ý "đã có đường chạy" cho các app này —
`docs/wine/WINE-COMPAT-MATRIX.md` §2-3 kết luận cả ba đều `blocked-likely`
vì phụ thuộc hạ tầng Windows mà Wine không cấp được (SQL Server cho MISA
SME; WebView2 — thành phần trình duyệt Windows-only — cho bản iTaxViewer
mới; driver/middleware token Windows cho công cụ ký số BHXH). Ship một
capsule recipe cho các app này sẽ ngụ ý sai rằng chỉ cần cài đúng winetricks
verb là xong, trong khi vấn đề nằm ở tầng kiến trúc, không phải thiếu thư
viện. Nếu owner vẫn muốn thử GUI của các app đó (để xem trước, KHÔNG dùng
nghiệp vụ thật), dùng `namios-windows-app` (lớp thân thiện, tự hỏi cài
winetricks chung) — không cần preset riêng cho việc chỉ "xem thử".
