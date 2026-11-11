# NaMi — Thuật ngữ tiếng Việt chuẩn hóa (HIG §7.1) + audit nhãn hiện tại

> **Loại tài liệu:** đặc tả P1 — bảng thuật ngữ chuẩn (HIG §7.1) + **audit** nơi nhãn/i18n
> hiện tại LỆCH + danh sách sửa cho wave sau. **Phạm vi file:** CHỈ liệt kê diff, **KHÔNG sửa
> app/.desktop/i18n**. `verified_on_host: NO`. Không `git commit`/push. **Ngày:** 2026-11-11.

## 0. Quy tắc đặt tên (ưu tiên cao nhất — của chủ dự án, GHI ĐÈ HIG §7.1)

> **Latin "n"+chức năng** (vd `nAssistant`, `nSettings`) **HOẶC tiếng Việt thuần** (vd "Trợ lý",
> "Lịch") — **KHÔNG dùng tiền tố "NaMi "** trước tên app.

→ **HIG §7.1 gợi ý cũ "NaMi Tệp / NaMi Cài đặt / NaMi AI" nay BỊ GHI ĐÈ** bởi quy tắc trên.
Repo **đã tuân thủ**: `.desktop` dùng `Name=nAssistant`/`Name[vi]=Trợ lý`, KHÔNG có "NaMi Trợ lý".
Mẫu áp dụng thực tế trong repo:

- `Name=` (locale gốc/EN): **Latin "n"+chức năng** — `nAssistant`, `nSettings`, `nConnect`,
  `nSecurity`, `nServices`, `nCalendar`, `nProjector`, `nDiagnostics`, `nGuide`, `nAI`, `nWine`,
  `nUninstall`.
- `Name[vi]=`: **tiếng Việt thuần, không tiền tố** — "Trợ lý", "Lịch", "Kết nối thiết bị"...
- Shortcut CATEGORY trong Cài đặt (`cpl-*`) dùng tên chức năng thuần (Network/Update/Accounts…)
  khớp nhãn danh mục kiểu Windows 11 — chấp nhận được (không phải app độc lập).

## 1. Bảng thuật ngữ chuẩn hóa (HIG §7.1)

| Khái niệm | Nhãn mặc định | Tránh |
|---|---|---|
| Settings | **Cài đặt** | "Setting", "Thiết lập hệ thống máy tính" |
| Update | **Cập nhật** | "Upgrade" khi chỉ là bản vá |
| Restart | **Khởi động lại** | "Reboot" trong UI phổ thông |
| Download | **Tải xuống** | "Download" trong nút chính |
| Print | **In** | "Print" |
| Scan | **Quét tài liệu** | "Scan" (ngữ cảnh người mới) |
| Bluetooth pairing | **Ghép nối** | "Pair" |
| Restore | **Khôi phục** | "Reset" nếu thực tế là phục hồi từ bản sao |
| File manager | **Tệp** | "Explorer" (nếu không có quyền tên đó) |

Bổ sung nhất quán trong repo (không mâu thuẫn HIG): **Trợ lý** (Assistant), **Lịch** (Calendar),
**Kết nối thiết bị** (Connect device), **Chẩn đoán** (Diagnostics), **Gỡ cài đặt** (Uninstall),
**Cá nhân hoá** (Personalization). Quy tắc chung: câu ngắn, dấu đúng, **không viết HOA toàn câu**,
không dịch tên riêng bên thứ 3 (Firefox/LibreOffice/Zalo).

## 2. Audit — nhãn hiện tại trong repo (đã grep)

Nguồn: 25 `.desktop` trong `$CH/usr/share/applications/`, `$CH/opt/namios/*/_i18n.py`,
`$CH/opt/namios/namios_i18n/locale/vi.json` (`$CH` = `distro/live-build/config/includes.chroot`).

### 2.1. Nhãn ĐẠT (giữ nguyên)

| App | `Name` | `Name[vi]` | Đánh giá |
|---|---|---|---|
| assistant | nAssistant | Trợ lý | ĐẠT (n+chức năng / VN thuần) |
| lich | nCalendar | Lịch | ĐẠT |
| ket-noi-thiet-bi | nConnect | Kết nối thiết bị | ĐẠT |
| chan-doan | nDiagnostics | Chẩn đoán | ĐẠT |
| cpl-update | Update | Cập nhật | ĐẠT (khớp §1) |
| cpl-network | Network | Mạng | ĐẠT |
| cpl-accounts | Accounts | Tài khoản | ĐẠT |
| cpl-personalization | Personalization | Cá nhân hoá | ĐẠT |

### 2.2. Nhãn LỆCH (liệt kê để wave sau sửa — KHÔNG sửa ở đây)

| # | App/file | Nhãn hiện tại | Vấn đề | Đề xuất |
|---|---|---|---|---|
| D1 | `namios-control-panel.desktop` | `Name[vi]=Bảng điều khiển` | "Bảng điều khiển" = Control Panel (Windows-ism). HIG §7.1 chuẩn top-level Settings = **"Cài đặt"** | Cân nhắc "Cài đặt" (chuẩn HIG) **hoặc** giữ "Bảng điều khiển" nếu CHỦ ĐÍCH gợi Windows-parity — **chốt 1 nhãn, dùng nhất quán** (hiện Welcome/i18n đã dùng "Cài đặt" cho cùng khái niệm → đang **mâu thuẫn nội bộ**) |
| D2 | `namios-go-cai-dat.desktop` | `Name=nUninstall` / id `go-cai-dat` | id file "go-cai-dat" mơ hồ (gỡ ≠ go-to); nhãn VN "Gỡ cài đặt phần mềm" đúng nhưng id dễ nhầm | đổi id → `namios-go-ung-dung`/`namios-uninstall`; giữ nhãn VN |
| D3 | `namios-smartai.desktop` + `namios-assistant.desktop` | `nAI`/"Hỏi AI" **và** `nAssistant`/"Trợ lý" | **2 app AI** tên khác nhau — người dùng khó phân biệt "Trợ lý" vs "Hỏi AI" | hợp nhất nhãn/định vị: 1 là "Trợ lý" (chẩn đoán lỗi), 1 là "Hỏi AI" (hội thoại) — ghi rõ khác biệt trong GenericName |
| D4 | `namios-windows-app.desktop` | `nWine`/"Chạy phần mềm Windows" | "Wine" là tên dự án bên thứ 3; nhãn gợi "mọi phần mềm Windows chạy" | thêm attribution Wine trong About; GenericName nói mức hỗ trợ theo dữ liệu thật (HIG §14), không hứa "mọi app" |
| D5 | `nConnect` GenericName[vi] | "Thiết lập máy in, máy quét..." | dùng "máy quét" (thiết bị) — khi là HÀNH ĐỘNG scan nên là **"Quét tài liệu"** (HIG §7.1) | giữ "máy quét" cho thiết bị; nút hành động scan = "Quét tài liệu" |
| D6 | web-launcher (facebook/tiktok/youtube/zalo) | `Name=Facebook (Dịch vụ web)` | ĐÚNG hướng (nhãn rõ "Dịch vụ web, cần mạng/tài khoản") nhưng thiếu **attribution + giấy phép** tên/logo bên thứ 3 | giữ nhãn; bổ sung nguồn gốc trong About (HIG §10.3, R4) |
| D7 | Dolphin (file manager) | nhãn hệ thống mặc định | HIG §7.1: file manager → **"Tệp"** | đặt `Name[vi]=Tệp` cho mục Dolphin trong Kickoff/Desktop (wave shell P2) |

### 2.3. Thuật ngữ trong i18n (vi.json) — ghi nhận

- "Cài đặt" dùng đúng làm NOUN cho Settings (`welcome.ui.done.body`: "...trong Cài đặt...").
- "thiết lập" dùng làm ĐỘNG TỪ ("thiết lập bộ gõ") — hợp lệ (HIG chỉ cấm "Thiết lập" làm NOUN cho
  Settings). Không phải lỗi.
- "Khôi phục"/"khôi phục" dùng đúng (không nhầm "Reset").
- Nhiều chuỗi kỹ thuật (CLI/ECO) giữ thuật ngữ chuyên môn — chấp nhận (HIG §9: có tiếng Anh dự
  phòng cho chẩn đoán kỹ thuật), nhưng chuỗi hướng người-dùng-cuối phải theo §1.

## 3. Tổng kết diff

- **Tuân thủ tốt:** quy tắc "n"+chức năng / VN thuần đã áp dụng toàn bộ `.desktop`; HIG §7.1's
  "NaMi X" đã bị thay đúng theo chủ dự án.
- **7 điểm lệch (D1–D7)** — phần lớn là **nhất quán nhãn** (D1 "Bảng điều khiển" vs "Cài đặt"),
  **phân biệt 2 app AI** (D3), và **attribution bên thứ 3** (D4, D6). KHÔNG sửa ở phase này —
  giao wave l10n/shell (P2) kèm `docs/l10n/TERMINOLOGY-REVIEW.md`.
- **Việc cần làm trước phát hành (HIG §0/§14):** rà soát **nhãn hiệu tên "NaMi/NaMiOS"** + quyền
  dùng tên/logo dịch vụ bên thứ 3 — không thuộc phạm vi sửa chữ, thuộc pháp lý.
