# NaMiOS — Hệ thiết kế giao diện (Design System) · PRA-036/037/039/040

> **Phạm vi D0:** đây là **đặc tả hệ thiết kế + từ vựng** để 5 màn hình chính dùng
> CHUNG một ngôn ngữ hình ảnh, KHÔNG sao chép tài sản Microsoft (SYS-006/PRA-018).
> Mockup trong `docs/design/mockups/` minh hoạ các token này. `verified_on_boot: NO`
> cho tới khi dựng KDE thật trên ISO. Nguồn token DUY NHẤT = file này; theme KDE +
> màn hình thật phải bám theo.

## 1. Thương hiệu + màu (PRA-036)

Màu thương hiệu = **RUBY `#a21f46`** (gradient `#e0457a → #a21f46`). Nền tối chủ đạo
(navy), nền sáng cho vùng nội dung. Hỗ trợ **hệ sáng/tối** (dùng chung token theo vai
trò, đổi giá trị theo chế độ).

| Token | Vai trò | Tối (desktop) | Sáng (vùng nội dung) |
| --- | --- | --- | --- |
| `--bg` | Nền ngoài cùng | `#0a1322` | `#f4f6fb` |
| `--bg-raised` | Panel/cửa sổ | `#141f36` | `#ffffff` |
| `--wall-top`/`--wall-bottom` | Gradient hình nền | `#122a4a` / `#0a1322` | — |
| `--text` | Chữ chính | `#eaf0fb` | `#1a2338` |
| `--text-dim` | Chữ phụ | `#9fb0d0` | `#5a6782` |
| `--primary` / `--primary-hi` | Ruby (hành động chính) | `#a21f46` / `#e0457a` | `#a21f46` / `#c0315f` |
| `--on-primary` | Chữ trên nền ruby | `#ffffff` | `#ffffff` |
| `--ok` | Trạng thái ĐẠT | `#3fae72` | `#1f8a52` |
| `--warn` | Cảnh báo / một phần | `#e0a13a` | `#b9790f` |
| `--err` | Lỗi / chặn | `#e0574e` | `#c23127` |
| `--info` | Trung tính / chưa kiểm | `#6f82a6` | `#6f82a6` |
| `--line` | Viền / chia | `#26324c` | `#dfe4ee` |
| `--focus` | Viền focus bàn phím | `#79b8ff` | `#2563c0` |

**Màu trạng thái phải khớp từ vựng trung thực** (PRA-032): `--ok` = đã xác nhận;
`--warn` = một phần/đang chờ; `--err` = thất bại/chặn; `--info` = **chưa kiểm**
(KHÔNG tô xanh "đạt" khi chưa có bằng chứng).

## 2. Typography (PRA-036/039)

- Phông: **Noto Sans** (có đủ tiếng Việt Unicode, dấu chuẩn). KHÔNG dùng phông thương
  mại Windows; không chép phông vào ISO (PRA-018).
- Thang cỡ (px @100%): `H1 28 · H2 22 · H3 18 · body 15 · label 13 · caption 12`.
- Trọng lượng: Regular 400, Bold 700. Dòng cao ≥1.4 cho đoạn văn.
- Số/tiền/ngày định dạng VN: `1.234.567 ₫`, `06/11/2026`, `08:25`.

## 3. Spacing, bo góc, bóng

- Thang spacing (px): `4 · 8 · 12 · 16 · 24 · 32 · 48` (bội số 4).
- Bo góc: nút/ô `8`, thẻ/panel `12`, cửa sổ `12`, chip `999` (bo tròn).
- Bóng: panel nổi `0 8 24 rgba(4,10,22,.35)`; không lạm dụng.

## 4. Trạng thái bắt buộc mỗi thành phần tương tác (PRA-036)

Mọi nút/ô nhập/mục danh sách PHẢI có đủ: **default · hover · focus (viền `--focus`
≥2px, KHÔNG chỉ đổi màu) · active · disabled · error**. Thông báo lỗi nêu **nguyên
nhân quan sát được + việc cần làm** (PRA-039), không chỉ "Đã xảy ra lỗi".

## 5. Tương phản + tiếp cận (PRA-040)

- Tương phản chữ/nền ≥ **4.5:1** (chữ thường), ≥ **3:1** (chữ lớn/icon) — mức WCAG AA.
- **Không truyền thông tin chỉ bằng màu**: trạng thái luôn kèm **nhãn chữ + icon**
  (vd "● Đã xác nhận", "▲ Một phần", "■ Chưa kiểm").
- Điều hướng bàn phím đầy đủ (Tab/Shift+Tab/Enter/Esc), focus thấy rõ; hỗ trợ screen
  reader (nhãn cho mọi icon); phóng to **125–200%** không vỡ layout; cỡ chữ chỉnh được.

## 6. Layout + responsive (PRA-036)

- Mốc nhỏ nhất **1366×768**; phải đẹp cả màn lớn (≥1920). Mockup vẽ ở khung `1600×1000`.
- Khung chung (shell) mọi màn hình: **taskbar dưới** (nút Bắt đầu trái · ô Tìm kiếm ·
  app ghim · khay phải: VN·Telex / Wi‑Fi / loa / pin / đồng hồ `06/11/2026`) +
  **cửa sổ** có title-bar (nút ◯–▢–✕ tự vẽ) + nội dung.
- Chip "chế độ chạy" (Native / Web / Wine / VM / Remote) hiển thị ở chỗ **dễ thấy nhưng
  không quá tải** (PRA-037) — màu `--info`, có nhãn chữ.

## 7. Năm màn hình chính + từ vựng chung (PRA-036/039)

Tất cả dùng cùng component (nút, thẻ, chip trạng thái, badge chế độ) + **từ vựng**:

| Màn hình | Nội dung chính | Bất biến trung thực thể hiện |
| --- | --- | --- |
| **Màn hình chính** (Desktop) | Taskbar + menu Bắt đầu (nhóm việc Văn phòng/Thuế/Kế toán/Bảo hiểm/Giáo dục/Hành chính) + icon + cửa sổ app | SmartAI là bong bóng phụ trợ (tắt vẫn dùng được) |
| **Ứng dụng** (Apps) | Danh mục app theo nhóm + badge chế độ chạy + trạng thái | "đã tải/mở được" ≠ "dùng được"; app chưa kiểm ghi **Chưa kiểm** |
| **Thiết bị** (Devices) | Máy in/scan/đa chức năng/Wi‑Fi/Bluetooth; **in·scan·copy·fax RIÊNG** từng dòng | copy **Chưa kiểm** dù in+scan ĐẠT (PRA-001) |
| **Mạng** (Network) | Wi‑Fi/Ethernet/VPN; trạng thái + lỗi cụ thể | mỗi lỗi một thông điệp riêng (PRA-029), không "khởi động router" chung |
| **SmartAI** (Bảng tác vụ) | "Tôi muốn làm gì" · tiến độ · bước chặn · quyền đã cấp · nguồn kết quả · nút Hoàn tác | "đã gửi hàng đợi" → "máy báo xong" → "**bạn** xác nhận đã nhận" (PRA-032/038) |

## 8. Từ vựng tiếng Việt chuẩn (PRA-039) — tránh thuật ngữ máy ở luồng phổ thông

| Dùng (phổ thông) | KHÔNG dùng ở luồng phổ thông |
| --- | --- |
| Bắt đầu · Tìm kiếm · Tệp của tôi · Máy này · Thùng rác | Start · Explorer · My PC |
| Mở · Lưu · In · Hủy · Cài đặt · Mặc định | Open/Save/Print trần không dịch |
| Đã gửi hàng đợi in · Máy báo in xong · Bạn đã nhận bản in | "completed" (trạng thái máy) |
| Đã ký · Đã nộp · Cổng đã trả biên nhận | gộp "đã nộp" = "xong" |
| Chạy kiểu: Máy Việt / Web / Thử-Wine / Máy ảo Windows / Máy Windows từ xa | prefix · COM · runtime · P/Invoke |
| Chưa kiểm · Một phần · Đạt · Thất bại · Bị chặn | "tương thích" khi mới discovery |

Thuật ngữ kỹ thuật (`prefix/COM/runtime/.NET`) chỉ xuất hiện trong mục **"Chi tiết cho
kỹ thuật viên"** (PRA-038), không ở luồng người dùng phổ thông.

## 9. Icon (PRA-036/018)

Mọi biểu tượng là **vector tự vẽ** (SVG), KHÔNG dùng icon/logo Microsoft hay bộ icon có
giấy phép hạn chế. Style: nét đơn giản, bo nhẹ, 2 tông (nền + ruby nhấn). Mỗi icon có
nhãn chữ đi kèm (PRA-040).

---

## PL12 — Mở rộng: Phụ lục 12 (UX12-001..048)

> **Phạm vi:** mục này BỔ SUNG cho phần D0 ở trên (§1–9), KHÔNG xoá/ghi đè bất kỳ token
> hay quy ước nào đã chốt phía trên. Nguồn: `docs/spec-package/NaMiOS_Phu_luc_12_Dac_ta_Thiet_ke_Giao_dien_Phim_tat_Hinh_nen.md`.
> Token máy đọc được chi tiết hơn (giá trị + tỉ số tương phản đã tính) nằm ở
> `design/tokens.json`, `design/keyboard-shortcuts.json`, `design/wallpaper-manifest.json`,
> `design/glossary.vi.json`. Theo dõi tiến độ 48 mã UX12 ở `docs/backlog/UX12-backlog.md`.
> `verified_on_boot: NO` cho mọi mục dưới đây — chưa có desktop NaMiOS thật để test.

### PL12.1 Typography tiếng Việt (bổ sung font)

Giữ **Noto Sans** làm phông mặc định đang chốt ở §2 phía trên (đã kiểm license, không
chép phông thương mại — PRA-018). PL12 mở thêm một lựa chọn **có điều kiện**:
**Be Vietnam Pro** (OFL, xem Nguồn [2] trong Phụ lục 12) làm phông UI nâng cấp thẩm mỹ
*nếu* nhóm thiết kế xác nhận glyph tiếng Việt (dấu, chữ ư/ơ/đ) đạt chất lượng trên máy
pilot thật; cho tới lúc đó Noto Sans vẫn là mặc định thật sự đang dùng. Mono: Noto Sans
Mono (đường dẫn, mã lỗi, terminal, log) — không đổi.

Thang chữ chi tiết hơn (dp, không thay số px @100% đã có ở §2, chỉ thêm biên độ cho
nhiều kích thước màn hình): `hero 28-32 · h1 24 · h2 20 · h3 16-18 · body 14-16 (chọn
15/22 cho prototype) · secondary 13-14 · caption 12-13 · button 14-15`. Bắt buộc hỗ trợ
5 mức phóng chữ **100/115/130/150/200%**, mỗi mức phải reflow chứ không cắt nội dung/nút
(WCAG 2.2 SC 1.4.4). Số tiền/tiến trình dùng chữ số `tabular` khi phông hỗ trợ.

### PL12.2 Token màu ngữ nghĩa — kiểm tra tương phản 4.5:1

Bảng màu RUBY + sáng/tối đã chốt ở §1 phía trên là **nguồn sự thật duy nhất cho giá trị
brand**, không đổi. PL12 đo lại tương phản WCAG 2.2 cho từng cặp chữ/nền và phát hiện
**3 token khi dùng làm CHỮ THƯỜNG (không phải nền chip đặc) chưa đạt 4.5:1**:

| Token | Giá trị gốc (§1) | Tỉ số gốc (chữ thường) | Giá trị PL12 đã chỉnh | Tỉ số mới |
| --- | --- | --- | --- | --- |
| `--err` (tối) trên `--bg-raised` | `#e0574e` | 4.41:1 | `#e15b52` | 4.55:1 |
| `--ok` (sáng) trên `--bg`/`--bg-raised` | `#1f8a52` | 4.03:1 / 4.36:1 | `#1d804c` | 4.60:1 / 4.95:1 |
| `--warn` (sáng) trên `--bg`/`--bg-raised` | `#b9790f` | 3.35:1 / 3.62:1 | `#9a650d` | 4.57:1 / 4.95:1 |

Giá trị gốc ở §1 **vẫn hợp lệ** khi dùng làm màu nền của chip/badge đặc kèm icon + nhãn
chữ tương phản cao (đúng quy tắc "không truyền thông tin chỉ bằng màu" ở §5) — chỉ
không đủ tương phản khi tự nó là màu CHỮ cỡ thường. Toàn bộ phép đo, công thức và bảng
đầy đủ nằm ở `design/tokens.json` (`color.contrast_table`). PL12 cũng bổ sung token còn
thiếu ở §1: `link` (tối `#6fb0ef`, sáng `#0b63ce` — khác hue với `--focus` để không nhầm
hai ý nghĩa, luôn kèm gạch chân/weight khác theo UX12-004).

**Phát hiện cần theo dõi:** token `border` (`--line` ở §1) chỉ đạt ~1.2–1.5:1 so với nền,
KHÔNG đạt 3:1 non-text contrast (WCAG 1.4.11) nếu dùng làm cách DUY NHẤT để nhận biết
biên control. Xem `design/tokens.json` → `color.border_warning` và mục theo dõi tương
ứng ở `docs/backlog/UX12-backlog.md`.

### PL12.3 Spacing/radius/control — không đổi, chỉ hợp nhất đơn vị

Thang spacing `4·8·12·16·24·32·48` và bo góc `6/10/16` ở `design/tokens.json` tương
thích với thang đã chốt ở §3 (`4·8·12·16·24·32·48` + bo `8/12/12/999`); PL12 thêm chi
tiết chiều cao control (`32/40/48dp`, mặc định 40), icon (`16/20-24/32dp`), toolbar
(`48-56dp`), sidebar (`224-280dp`) và dialog (`400-560dp`) phục vụ prototype — không có
trong §3 trước đó.

### PL12.4 Phím tắt (UX12-019..024)

Registry đầy đủ (27 action: 9 hệ thống + 4 cửa sổ + 14 ứng dụng/app, mỗi action có
`action_id/scope/default_combo/priority/overridable/p_level`) nằm ở
`design/keyboard-shortcuts.json`. **Đã đối chiếu thủ công: không có 2 action scope=system
nào trùng `default_combo`** (9 action hệ thống đang bật, 1 action `smartai_invoke` để
`enabled:false` chờ audit xung đột IME/desktop theo đúng yêu cầu spec — KHÔNG gán
`Super+Space` làm mặc định đang hoạt động). Ba xung đột tiềm ẩn với phần mềm ngoài
NaMiOS đã ghi lại ở `known_conflicts` trong file: `Ctrl+Space` (IME) vs autocomplete IDE,
`Super+Space` (SmartAI, đang tắt) vs đổi IME kiểu Windows/macOS ở một số DE, `Shift+F10`
(menu ngữ cảnh) vs phím riêng của một số app Wine/trình duyệt. Một bộ phát hiện xung đột
chạy trong CI (yêu cầu ở UX12-019) **chưa được dựng** — kết quả "không trùng" ở trên là
đối chiếu thủ công một lần, không phải bằng chứng CI.

### PL12.5 Hình nền có quyền (UX12-025..032)

`design/wallpaper-manifest.json` khai cấu trúc dữ liệu cho bộ sưu tập "Việt Nam qua từng
vùng đất" (mục tiêu 12–18 ảnh Bắc/Trung/Nam) nhưng **hiện có 0 ảnh thật** — 3 mục trong
file đều là PLACEHOLDER với `license: "placeholder"` và
`rights_evidence: "chưa có — cần cấp phép trước khi đóng gói"`. Không địa danh/tác
giả/nguồn nào được khẳng định là thật. Không mục nào trong file được phép dùng để đóng
gói ISO cho tới khi có bằng chứng cấp phép thật và hội đồng biên tập (thiết kế + biên
tập Việt Nam + pháp lý tư liệu) ký duyệt (UX12-026, UX12-048).

### PL12.6 Accessibility WCAG 2.2 AA (bổ sung mục tiêu rõ ràng)

Mục tiêu phát hành: **WCAG 2.2 AA** cho UI chính (UX12-035) — tương phản chữ thường
≥4.5:1 / chữ lớn-icon ≥3:1 (đã đối chiếu ở PL12.2), bàn phím đầy đủ không bẫy focus
(§5 đã có), phóng chữ 100-200% không vỡ layout (PL12.1), giảm chuyển động có tác dụng
ngay (§3 + `design/tokens.json` → `motion`), tránh flash/animation gây hại. Test tự động
+ thủ công với screen reader và 200% text, lỗi P0 chặn release — **chưa thực hiện**, cần
desktop NaMiOS thật (xem `docs/backlog/UX12-backlog.md` UX12-035, trạng thái
`blocked-infra`).

### PL12.7 Quy tắc tiếng Việt (glossary + văn phong)

`design/glossary.vi.json` bổ sung 55 thuật ngữ (34 phổ thông + 21 chuyên ngành:
driver→trình điều khiển, firmware, kernel, compositor, sandbox, certificate, prefix...)
giải thích cho Help/tra cứu, **không thay đổi** bảng "Dùng/Không dùng" đã chốt ở §8 phía
trên (Bắt đầu/Tìm kiếm/Tệp của tôi/Máy này/Thùng rác, "Đã gửi hàng đợi in"→"Máy báo in
xong"→"Bạn đã nhận bản in", 5 mức Chưa kiểm/Một phần/Đạt/Thất bại/Bị chặn) — file mới chỉ
tham chiếu lại các cặp đó để không tạo hai nguồn sự thật lệch nhau. Văn phong bổ sung
(UX12-038): ngày giờ Việt Nam, không viết HOA toàn câu, tránh tiếng Anh kỹ thuật khi có
từ phổ thông, mã lỗi cố định cho đội kỹ thuật.
