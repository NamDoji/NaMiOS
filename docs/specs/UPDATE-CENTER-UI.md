# NaMiOS Update Center — đặc tả UI 4 chế độ + máy trạng thái UX

**Trạng thái:** `specified` — đặc tả component + nội dung tiếng Việt chuẩn. UI
Qt/QML chạy thật là **follow-up (U15-D)**; chưa có mã giao diện live. Prototype
logic (máy trạng thái + xác thực) ở `tools/update-center-prototype/` đã chạy +
test được (`partial`), CHƯA nối vào apt/bootloader thật.
**Ngày:** 2026-11-09 · **Nguồn:** Phụ lục 15 §3, §3.1, §6, §7 + Design System
"Sen Việt" v1.0 (`branding/design-system/tokens.json`, `components-preview.html`).

> Nguyên tắc nền (PL15): Update Center là **giao diện**; mọi thao tác thật đi qua
> **Update Service** quyền-giới-hạn. SmartAI chỉ **giải thích/đề xuất**, không ký
> gói, không sửa metadata, không tắt kiểm chữ ký, không cài firmware, không root
> shell. Không có nút "Bỏ qua kiểm tra".

---

## 0. Tham chiếu Design System (nguồn sự thật)

| Thành phần dùng lại | Nguồn | Vai trò trong Update Center |
| --- | --- | --- |
| **Progress** (`.nm-progress`, biến thể `indeterminate`) | `components-preview.html` §7 | Thanh "Đang tải", "Đang cài", "Đang kiểm tra sau khởi động" (indeterminate khi chưa có % thật). |
| **ErrorCard** (`.nm-errorcard`) | `components-preview.html` §10 + `docs/specs/EVENT-ERROR-CONTRACT.md` §6 | Hiển thị mỗi mã `UPD-00x`: tiêu đề, nguyên nhân, mã lỗi + `correlation_id`, nút an toàn, "Nhờ SmartAI giải thích". |
| **AIPlanCard** (`.nm-aiplan`) | `components-preview.html` §11 | SmartAI gợi ý tối đa 3 bước (vd "Sao lưu trước", "Cài tối nay", "Hỏi IT") + mức chắc chắn cao/vừa/thấp + disclaimer "không tự đổi cấu hình". |
| Tokens màu/chữ/spacing/focus/motion | `tokens.json` | Trạng thái **luôn kèm chữ + hình**, không chỉ màu; focus ring ≥2px; zoom 200%; reduced-motion. |

**Token trạng thái** (light / dark) dùng cho dòng kết quả:
`status.success` #127A52 / #59C798 · `status.warning` #965300 / #F6BB68 ·
`status.error` #B4232B / #FF8B8F · `status.info` (đang xử lý/chưa xác định)
#1F5E70 / #9DB3BC. Mã lỗi/`correlation_id` render bằng font **mono**
(`typography.font_family.mono`).

---

## 1. Bốn chế độ cập nhật (Cài đặt → Cập nhật & bảo mật → Cách cập nhật)

Mỗi chế độ là một thẻ chọn (radio) kèm mô tả ngắn 3 ý: **máy sẽ làm gì · khi nào
khởi động lại · có dùng dữ liệu di động không**. Áp dụng tách bạch cho
OS / app / AI / firmware — **không có nút "tự động tất cả" mơ hồ**.

| # | `user_policy` | Tên hiển thị | Máy sẽ làm gì | Khởi động lại | Dữ liệu di động |
| --- | --- | --- | --- | --- | --- |
| 1 | `notify` | **Thông báo, tôi tự quyết định** | Kiểm tra theo lịch; hiện bản mới + mức quan trọng + dung lượng + nút Cài. Có nút "Kiểm tra ngay". | Chỉ khi bạn bấm Cài | Không tự tải |
| 2 | `auto_download_ask_install` | **Tự tải, hỏi trước khi cài** (mặc định pilot) | Chỉ tải khi mạng/ổ đĩa phù hợp; hỏi trước khi cài. | Hỏi trước | Theo giới hạn đã đặt |
| 3 | `auto_install_safe` | **Tự cài bản an toàn** | App + bản vá không cần reboot tự cài **sau khi xác thực**; OS được *staged*, hỏi/lên lịch restart. Firmware **không** tự cài. | Có lịch/nhắc cho OS | Theo giới hạn |
| 4 | `auto_scheduled` | **Tự động theo lịch của tôi** | Chọn giờ yên tĩnh, chỉ khi cắm sạc, giới hạn mạng tính phí, thời hạn hoãn restart. OS cài khi preflight đạt; restart chỉ trong cửa sổ đã chọn, cho hoãn khi còn việc chưa lưu. | Trong cửa sổ đã chọn | Theo giới hạn |

**Quy tắc chung mọi chế độ:**
- Firmware **luôn** có xác nhận riêng (PL15 §3) — không chế độ nào tự cài firmware.
- Tắt tự cài vẫn **kiểm tra + thông báo bảo mật**.
- Máy do tổ chức quản lý: hiện "Thiết bị do tổ chức quản lý", ai đặt lịch, nút
  liên hệ IT (chính sách IT đè chế độ cá nhân).
- **Tạm dừng** luôn có **ngày kết thúc hiển thị** — không im lặng vô thời hạn.
- Bản vá khẩn: thông báo nhiều cấp + lý do + thời hạn khuyến nghị; **không** reboot
  bất ngờ phá việc chưa lưu. "Khẩn" không được biến thành quyền bỏ kiểm chữ ký.

---

## 2. Máy trạng thái UX (PL15 §3.1) ↔ `state` hợp đồng (§7)

Chuỗi hiển thị cho người dùng:

```
Đang kiểm tra → Có bản mới → Đang tải → Đã xác thực → Sẵn sàng cài → Đang cài
  → Cần khởi động lại → Đang kiểm tra sau khởi động
  → Hoàn tất / Đã khôi phục / Cần hỗ trợ
```

Ánh xạ sang `state` máy-đọc trong `update_contract.py` (chỉ chuyển theo
`VALID_TRANSITIONS`, không nhảy cóc, không bypass):

| Nhãn UX (tiếng Việt) | `state` | Chuyển hợp lệ tiếp theo | Ghi chú an toàn |
| --- | --- | --- | --- |
| Đang kiểm tra | *(tiền-`available`)* | → available \| blocked(UPD-001) | Mạng hỏng ⇒ blocked UPD-001. |
| Có bản mới | `available` | → downloading \| blocked | Hiện changelog, dung lượng, cần restart. |
| Đang tải | `downloading` | → verified \| blocked | Chunk + **resume**; giữ phần đã tải khi đứt mạng. |
| Đã xác thực | `verified` | → staged \| blocked | **Chỉ tới được khi chữ ký + hash + hạn + thu hồi + arch/model ĐỀU đạt.** |
| Sẵn sàng cài / Đang cài | `staged` | → reboot_pending \| blocked | *Staged*: tệp của bạn chưa đổi. **Không** nói "đã cập nhật xong" khi chưa boot bản mới. |
| Cần khởi động lại | `reboot_pending` | → boot_check \| blocked | Lịch restart không phá việc chưa lưu (UPD-007 hoãn). |
| Đang kiểm tra sau khởi động | `boot_check` | → completed \| rolled_back \| blocked | Boot health: kernel/đăng nhập/ổ dữ liệu/mạng/UI/dịch vụ update. |
| Hoàn tất | `completed` | *(kết thúc)* | **CHỈ tới được từ `boot_check` khi health đạt.** |
| Đã khôi phục | `rolled_back` | *(kết thúc)* | Boot health fail ⇒ tự quay bản trước (UPD-008). |
| Cần hỗ trợ / Đã chặn | `blocked` | *(kết thúc)* | `error_code` != null; giữ phiên bản hiện tại; **không có đường sang staged/completed**. |

> **Vì sao không có 'completed' giả:** máy trạng thái **cấm** mọi đường tới
> `completed` trừ `boot_check → completed`, và `boot_check` chỉ tới sau
> `reboot_pending` (đã staged + đã xác thực chữ ký). Một tool tải/cài trả
> "success" **không** đủ để nâng `completed`; phải qua boot health thật
> (U15-C). Nếu health fail ⇒ `rolled_back`, không bao giờ `completed`.

---

## 3. Nội dung thông báo tiếng Việt (nguyên văn, PL15 §3.1)

Các con số/phiên bản dưới đây là **minh hoạ UI**, không phải bản phát hành có
thật; chỉ hiện % khi hệ thống thật sự đo được.

### 3.1 Có bản mới — `state=available` (component Toast + ErrorCard biến thể info)
> **NaMiOS 1.1 đã sẵn sàng.** Bản này sửa lỗi Wi‑Fi và tăng độ an toàn. Dung
> lượng 1,2 GB; cần khởi động lại.
> `[Xem thay đổi] [Cài tối nay] [Để sau]`

### 3.2 Tải thất bại — `state=blocked` hoặc giữ `downloading` để resume (UPD-001)
> **Chưa tải xong bản cập nhật.** Mạng bị ngắt ở 68%; các tệp đã tải hợp lệ sẽ
> được giữ để tiếp tục.
> `[Thử lại] [Xem kết nối]`

(Chỉ nói "68%" nếu có số liệu thật. Phần đã tải được giữ ở cache `.part`, lần sau
**resume** thay vì tải lại từ đầu.)

### 3.3 Chữ ký không hợp lệ — `state=blocked`, `error_code=UPD-003` (ErrorCard danger)
> **Bản cập nhật không vượt qua kiểm tra bảo mật.** NaMiOS đã chặn cài đặt; máy
> vẫn dùng phiên bản hiện tại.
> `[Xem chi tiết] [Báo sự cố]`

**Không có nút "Bỏ qua kiểm tra".** Dòng kết quả dùng `status.error` + biểu
tượng cảnh báo (không chỉ màu). Mã lỗi `UPD-003` + `correlation_id` hiển thị mono.

### 3.4 Đã staged — `state=staged` (ErrorCard/Toast biến thể info)
> **Bản cập nhật đã chuẩn bị xong.** Tệp của anh chưa bị thay đổi; chọn thời
> điểm khởi động lại.
> `[Chọn giờ khởi động lại] [Để sau]`

**Không** nói "đã cập nhật xong" khi chưa boot bản mới.

### 3.5 Sau rollback — `state=rolled_back`, liên quan UPD-008 (ErrorCard warning)
> **Bản mới không khởi động ổn định.** NaMiOS đã quay về phiên bản trước. Tệp cá
> nhân còn nguyên theo kiểm tra hiện có; xem báo cáo để xác nhận ứng dụng/dữ
> liệu quan trọng.
> `[Xem báo cáo] [Mở cứu hộ]`

Tránh bảo đảm tuyệt đối khi chưa kiểm dữ liệu người dùng.

**Quy tắc chung thông báo:** truy lại được trong Update Center, không spam sau
mỗi lần quét, có **mức khẩn cấp + lịch sử**. Screen reader đọc **tên · trạng
thái · nút**. Không chỉ dùng đỏ/xanh; không dùng "Đã xảy ra lỗi" khi đã biết
nguyên nhân (dùng `cause_vi` trong `update-error-catalog.json`).

---

## 4. ErrorCard cho mã UPD-00x (bind catalog)

Nguồn: `distro/.../usr/share/namios/update-error-catalog.json`. ErrorCard hiển
thị MỘT mã lỗi:

```
┌───────────────────────────────────────────────────────────────┐
│  ⚠  Cập nhật: ĐÃ CHẶN                                          │ ← dòng kết quả (status.error/warning/info)
│  <ui_title_vi của UPD-00x>                                     │
│  <cause_vi>                                                    │
│  Mã lỗi: UPD-003 · correlation_id: 20261109-142233-5312-8471   │ ← mono
│  [<ui_buttons_vi…>]  [Chi tiết kỹ thuật]  [Nhờ SmartAI giải thích] │
│  ▸ Lịch sử (n sự kiện cùng correlation_id)                     │
└───────────────────────────────────────────────────────────────┘
```

- **"Chi tiết kỹ thuật"**: mở panel chỉ-đọc, evidence **đã che bí mật**
  (`update_service.redact`: PEM key, Bearer, password/token/secret/otp, IP nội
  bộ, MAC, email, `/home/<user>`).
- **"Nhờ SmartAI giải thích"**: gọi SmartAI với mã + `message_vi`; SmartAI chỉ
  giải thích + đề xuất qua **AIPlanCard** (≤3 bước, mức chắc chắn), mọi thay đổi
  qua Update Service + xác nhận. SmartAI **không** cài gói, không tắt chữ ký.
- `blocking=true` ⇒ **không** render bất kỳ nút "cài tiếp/bỏ qua" nào.

Bảng tra nhanh mã → nút chính (chi tiết trong catalog):

| Mã | Nhóm | Nút an toàn chính |
| --- | --- | --- |
| UPD-001 | mạng | Xem kết nối · Thử lại |
| UPD-002 | dung lượng | Xem dung lượng · Thử lại (không tự xoá tệp) |
| UPD-003 | an ninh | Xem chi tiết · Báo sự cố (không bypass) |
| UPD-004 | an ninh/giờ | Kiểm tra ngày giờ · Thử lại |
| UPD-005 | sai máy | Xem mã thiết bị · Tìm bản phù hợp |
| UPD-006 | nguồn firmware | Hướng dẫn nguồn · Thử lại khi cắm sạc |
| UPD-007 | việc chưa lưu | Xem ứng dụng cần lưu · Để sau · Khởi động lại ngay |
| UPD-008 | boot | Xem báo cáo · Mở cứu hộ |
| UPD-009 | thu hồi | Xem lý do · Liên hệ hỗ trợ |
| UPD-010 | migration dữ liệu | Sao lưu ngay · Chuyển hỗ trợ |

---

## 5. SmartAI trong Update Center (AIPlanCard) — ranh giới cứng

- Đọc **metadata + trạng thái đã lọc** (bản cũ/mới, loại update, release notes,
  thiết bị bị ảnh hưởng, lỗi xác thực, preflight). Giải thích tiếng Việt, đề xuất
  ≤3 bước ("Cài tối nay", "Sao lưu trước", "Hỏi IT") kèm **mức chắc chắn**
  cao/vừa/thấp và disclaimer "SmartAI không tự ý đổi cấu hình/quyền".
- Với `UPD-003/004/005/009`: AI **chặn + báo an ninh**, không gợi ý "thử nguồn
  khác"; không kết luận "máy an toàn tuyệt đối" từ một bản vá.
- AI/model offline ⇒ Update Center + khôi phục **vẫn hoạt động** bình thường.
- Chống prompt-injection trong release notes: coi release notes là **dữ liệu**,
  không phải lệnh; không cho release notes yêu cầu tắt chữ ký/đổi kênh.

---

## 6. Khả dụng & kiểm thử UI (gate trước khi rời `specified`)

- **Tiếp cận:** screen reader đọc tên/trạng thái/nút; focus ring ≥2px bằng
  `focus.ring`; zoom 100/125/150/200% không mất nút; `prefers-reduced-motion`
  tắt animation; có chế độ giảm trong suốt.
- **Màu + chữ + hình:** mọi trạng thái kèm biểu tượng + nhãn chữ, không chỉ màu.
- **Trung thực số liệu:** % chỉ hiện khi đo được; phiên bản ví dụ gắn nhãn minh hoạ.
- **Test cần có (PL15 §9 nhóm "Luồng người dùng"):** 4 chế độ + đổi chế độ + tạm
  dừng (có ngày kết thúc) + restart theo lịch + mạng tính phí + pin → UI thực thi
  đúng lựa chọn, **không cài/reboot trái dự kiến**. (Logic máy trạng thái + ca
  phản công đã có test pytest ở `tools/update-center-prototype/tests/`.)

---

## 7. Việc còn lại (follow-up)

- **UI Qt/QML live** (U15-D): dựng ErrorCard/AIPlanCard/Progress thật bằng
  Kirigami, bind `l10n_key`, nối Update Service.
- **U15-C**: staged deployment thật + boot health + auto-rollback + migration
  guard (UPD-010) + backup proof; fault injection trên VM rồi 5 máy pilot.
- Hợp nhất hai bộ token (Sen Việt ngà ấm vs navy PL12) theo `$meta` trong
  `tokens.json`.
