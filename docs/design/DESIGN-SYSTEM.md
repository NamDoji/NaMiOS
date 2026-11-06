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
