# NaMiOS — Kiểm kê trạng thái thật theo Phụ lục 13 (U13)

**Ngày:** 08/11/2026 · **Người lập:** đội phát triển (Claude Code) · **Đối chiếu:** Phụ lục 13 — "Ưu tiên nâng cấp để đi từ đặc tả đến hệ điều hành dùng được".

## Quy tắc chấm trạng thái (theo §5 Phụ lục 13)

> *"Nếu không có artifact chạy trên máy thật, trạng thái vẫn là `specified`, không phải `completed`."*

- `specified` — đã có yêu cầu/thiết kế/cấu hình trong repo, **chưa** có bằng chứng chạy.
- `partial` — đã build ra artifact + có bằng chứng chạy **một phần** (ví dụ boot trong máy ảo QEMU, không phải máy thật). **Chưa** đủ cửa kiểm chứng.
- `completed` — **chỉ** khi có artifact chạy trên **máy thật** (pilot) + qua đúng "Cửa kiểm chứng" của năng lực đó.

**Sự thật nền:** NaMiOS hiện **chưa được test trên bất kỳ máy thật nào** (không có lab 5 máy pilot + 3 máy in theo M0). Mọi bằng chứng tới nay là **boot trong QEMU/TCG (không GPU)**. Vì vậy, theo đúng quy tắc trên: **không năng lực nào đạt `completed`.** Dưới đây là trạng thái trung thực.

## Bảng kiểm kê 14 năng lực

| ID | Năng lực | Mức | Trạng thái | Đã có trong repo | Thiếu để đạt cửa kiểm chứng |
| --- | --- | --- | --- | --- | --- |
| U13-01 | Ảnh cài + cài an toàn | P0 | **partial** | ISO live-build dựng được (CI), live boot tới desktop (đang ổn định hoá). Có gói Calamares (`0700-installer`). | Cài thật trên 5 máy, cài cạnh Windows, hủy giữa chừng không mất dữ liệu — **chưa test**. Chưa có đường "quay về Windows". |
| U13-02 | Cập nhật + khôi phục OS | P0 | **specified** | `unattended-upgrades` (chỉ security). | **Không có** rollback / bản boot trước (A-B) / health check / USB cứu hộ. Đây là lỗ hổng P0 lớn. |
| U13-03 | Sao lưu dữ liệu người dùng | P0 | **chưa làm** | — | Toàn bộ: backup theo phiên bản, lịch, restore preview. |
| U13-04 | Desktop tiếng Việt đủ dùng | P0 | **partial** | KDE Plasma + Việt hoá vi_NM (menu/Dolphin xác minh trong QEMU), icon squircle, Meta mở menu. Boot-vào-desktop đang ổn định hoá (đổi sang startx). | 10 người thử 8 việc (gõ/lưu/tìm/mở/**in**/Wi-Fi/cài app/tắt máy) trên máy thật — **chưa**. IME gõ trong app thật chưa xác minh. |
| U13-05 | App Center + bộ thiết yếu | P0 | **partial** | LibreOffice, Firefox, Discover/PackageKit, IME fcitx5. | Security Center chưa có. Shortcut chính thức Zalo/YouTube/Maps/FB/TikTok/WhatsApp chưa có. Phân loại native/web/Wine chưa có. |
| U13-06 | Mạng + ngoại vi ưu tiên | P0 | **specified** | NetworkManager, firmware (WiFi/GPU/audio), PipeWire, Bluetooth, CUPS+avahi+sane, NTFS/exFAT, udisks. | **Chưa test** Wi-Fi/in/scan/Bluetooth/USB trên máy thật nào (QEMU không có phần cứng này). 3-5 model máy in từ khảo sát: chưa chọn. |
| U13-07 | Bảo mật mặc định | P0 | **specified** | apt signed updates (mặc định), unattended-upgrades. | Firewall, sandbox/portal (Flatpak), Security Center, scanner — chưa cấu hình/kiểm. |
| U13-08 | Chẩn đoán + hỗ trợ | P0 | **chưa làm** | — | Mã lỗi nhất quán, lịch sử update/crash, log đã che, nút hoàn tác, hướng dẫn VN. |
| U13-09 | Bộ chọn tuyến app Windows | P1 | **chưa làm** | — | Catalog native/web/Wine/blocked, dependency graph, hồ sơ version/test. |
| U13-10 | Wine capsule có kiểm soát | P1 | **specified** | Gói Wine (`0600-wine`, đang disabled). | Prefix riêng, runner pin, quyền hẹp, snapshot, recipe — chưa có. |
| U13-11 | Công cụ chuyển từ Windows | P1 | **chưa làm** | Có "Hướng dẫn nhanh cho người quen Windows" (tài liệu). | Inventory app/font/tệp/máy in/token, báo cáo sẵn sàng, backup trước chuyển. |
| U13-12 | SmartAI giải việc thật | P1 | **partial (UI prototype)** | Plasmoid `org.namios.smartai` (chỉ vỏ UI, chưa render xác nhận; **chưa** có AI thật, chưa diagnostic/plan/rollback). | Giải 10 ca mạng/in/IME; tắt AI máy vẫn chạy. Toàn bộ phần lõi. |
| U13-13 | Nghiệp vụ Việt Nam | P2 | **chưa làm** | — | MISA/thuế/HĐĐT/BH/dịch vụ công/ký số theo vendor. |
| U13-14 | Quản trị nhiều máy + cộng đồng | P2 | **chưa làm** | Có lớp tài liệu cộng đồng + CI gate. | Update rings, policy, golden image, hỗ trợ từ xa, pilot 20 máy. |

## Kiểm kê theo mốc M0–M4

| Mốc | Yêu cầu | Trạng thái thật |
| --- | --- | --- |
| **M0 — khảo sát** | Inventory 30-50 máy/app/workflow; chọn 5 máy + 3 máy in lab; ADR chọn nền | **Chưa bắt đầu.** Cần dữ liệu từ chủ dự án (xem §"Cần từ anh" bên dưới). |
| **M1 — máy dùng được** | ISO + desktop Việt + Office/browser/IME + Wi-Fi/USB/in | **Đang làm, chưa đạt.** Nút thắt số 1: boot-vào-desktop ổn định (đang chuyển SDDM→startx). Sau đó mới verify được 8 việc. |
| **M2 — máy đáng tin** | Update/rollback/backup/security/diagnostics | **Chưa** (U13-02/03/07/08 còn specified/chưa làm). |
| **M3 — chuyển đổi** | Assessor + catalog + 3 app Wine/.NET | **Chưa.** |
| **M4 — mở rộng** | SmartAI hữu ích + ký số/thuế + quản trị | **Chưa.** |

## Nút thắt hiện tại (chặn mọi thứ phía sau)

**Boot-vào-desktop chưa ổn định trong máy ảo** → chưa verify được U13-04/05 (menu, IME, app). Diễn biến: autologin SDDM chập chờn theo từng build (Wayland crash / "Login Failed"). **Quyết định 08/11:** bỏ SDDM cho bản ALPHA, dùng `console autologin → startx → startplasma-x11` (gọi thẳng phiên X11, không GPU) để vào desktop tất định rồi mới verify phần còn lại. SDDM greeter + đa người dùng sẽ khôi phục trước pilot (cổng phát hành yêu cầu).

## Đề xuất kỷ luật (theo §5–6 Phụ lục 13)

1. **Dừng mở rộng vỏ desktop/feature.** Theme kính mờ, widget SmartAI, Aurorae nút-màu → **đóng băng** cho tới khi M1 chạy thật.
2. **Dồn vào vòng P0 khép kín:** boot → login → **gõ tiếng Việt trong app thật** → mở Office/PDF → **in** → tắt máy. Đây là M1.
3. **Không gọi `completed` nếu chưa chạy máy thật.** Mọi báo cáo ghi rõ "verified_on_host: NO/QEMU-only".
4. **Cần M0 trước khi hứa gì về thiết bị:** chưa có máy pilot thì mọi tuyên bố mạng/in/Bluetooth chỉ là `specified`.

## Cần từ anh (chủ dự án) để mở khoá M0–M1

Theo §4 Phụ lục 13 — chỉ cần tối thiểu để bắt đầu đo thật:

1. **1 máy thật** (laptop/desktop cũ cũng được) để em hướng dẫn anh cắm USB NaMiOS boot thử — đây là bước biến `partial` (QEMU) thành bằng chứng máy thật đầu tiên.
2. **1 máy in** anh hay dùng (model gì) để làm ca in thật.
3. **Danh sách ~10 việc** nhóm người dùng đầu (gia đình/giáo viên/văn phòng) phải làm xong + ~20 phần mềm/website kèm phiên bản.
4. Ai là **người chốt release** (anh hay anh + Bảo Nam).

> Tài liệu này sẽ cập nhật mỗi khi có bằng chứng mới. Mục tiêu: **khép vòng sản phẩm đầu tiên (M1), không mở thêm checklist.**
