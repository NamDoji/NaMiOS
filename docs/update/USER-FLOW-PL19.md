# NaMiOS — Cài đặt → Cập nhật & bảo mật → NaMiOS (đặc tả màn hình, PL19)

**Trạng thái:** `specified` — đặc tả màn hình + nội dung tiếng Việt cho luồng Phụ lục
19. Đây là **PROTOTYPE/spec**, **chưa nối vào apt/package manager/bootloader
thật**. Mọi số liệu (phiên bản, dung lượng, %) trong tài liệu và trong
prototype đi kèm là **dữ liệu minh hoạ**, không phải bản phát hành có thật.
**Ngày:** 2026-11-10 · **Nguồn:**
`docs/specs/namios-pl19/01_LUONG_NGUOI_DUNG.md` (luồng gốc PL19) +
`docs/specs/namios-pl19/02_HOP_DONG_KY_THUAT.md` (state machine/API) +
`docs/specs/UPDATE-CENTER-UI.md` (đặc tả UI PL15, 4 chế độ + ErrorCard/AIPlanCard)
+ Design System "Sen Việt" v1.0 (`branding/design-system/tokens.json`).

> Tài liệu này **mở rộng** `UPDATE-CENTER-UI.md` cho phạm vi PL19 (đường đi
> thông báo → cài → boot → khôi phục), không thay thế. Nơi hai tài liệu trùng
> nội dung (4 chế độ, ErrorCard, AIPlanCard), tài liệu này chỉ bổ sung trường/quy
> tắc còn thiếu và giữ nguyên thuật ngữ đã chốt ở PL15.

---

## 0. Đối chiếu nguồn sự thật

| Khái niệm | Nguồn sự thật | Vai trò trong màn hình này |
| --- | --- | --- |
| 4 chế độ (`user_policy`) | `UPDATE-CENTER-UI.md` §1 | Tái dùng đúng 4 khoá: `notify`, `auto_download_ask_install`, `auto_install_safe`, `auto_scheduled`. |
| Máy trạng thái UX (Vi) | `UPDATE-CENTER-UI.md` §2 | Chuỗi nhãn hiển thị người dùng. |
| Máy trạng thái hợp đồng (máy-đọc) | `docs/specs/namios-pl19/02_HOP_DONG_KY_THUAT.md` §2 | `DISCOVERED → … → COMMITTED` + nhánh `BLOCKED/FAILED/ROLLBACK_PENDING/ROLLED_BACK/RECOVERY_REQUIRED`. |
| Mã lỗi UPD-00x | `distro/.../usr/share/namios/update-error-catalog.json` | ErrorCard bind theo mã; phần "tình huống kit" ở §5 dưới ánh xạ lại 6 mã + rollback. |
| Component UI | `ErrorCard.qml`, `AIPlanCard.qml`, `ConnectionStepper.qml`, `SenVietButton.qml`, `SenVietPalette.qml` | Tái dùng nguyên component, không vẽ lại màu/nét riêng. |
| Token màu/chữ/spacing | `branding/design-system/tokens.json` | Sen Việt: ngà `#FBF8F2`→`#EFE3D1`, đỏ son `#C93643`, mực `#182E3B`; light/dark; WCAG 2.2 AA. |

**Đường đi menu:** Cài đặt → Cập nhật & bảo mật → NaMiOS (các mục NaMiOffice/
NaMiPDF/driver/firmware/SmartAI có tab riêng cùng màn hình cha, không gộp vào
đây — PL19 "Quyết định sản phẩm" §5).

---

## 1. Thông báo có bản mới

Thông báo là một **toast/ErrorCard biến thể info**, xuất hiện khi Update
Service báo `state=available` (đã qua xác thực metadata, đúng kênh/arch/model,
chưa bị thu hồi). Có nút **"Kiểm tra ngay"** luôn sẵn ở màn Update Center để
người dùng tự kiểm bất cứ lúc nào, không cần chờ lịch.

### 1.1 Các trường bắt buộc (manifest-driven — KHÔNG có trường giả)

| Trường | Nguồn dữ liệu | Quy tắc hiển thị |
| --- | --- | --- |
| **Phiên bản** | `manifest.version` (vd "NaMiOS 1.1") | Chỉ hiện khi đã xác thực chữ ký/hash; KHÔNG bịa số phiên bản mẫu lên UI thật. |
| **Lợi ích chính** | `manifest.release_notes_vi` (rút gọn ≤2 câu) | Ngôn ngữ phổ thông, không thuật ngữ kỹ thuật ("sửa Wi‑Fi", không "patch kernel driver iwlwifi"). |
| **Mức độ khẩn** | `manifest.severity` ∈ `thường` / `khuyến nghị` / `khẩn cấp` | Hiện bằng **chữ + biểu tượng**, không chỉ màu (tokens §color.rules). "Khẩn cấp" không được dùng để biện minh bỏ xác minh chữ ký (xem §7). |
| **Dung lượng** | `manifest.size_bytes` → đổi hiển thị (vd "1,2 GB") | Chỉ hiện khi đo được từ manifest/registry thật; không ước lượng khi chưa có số. |
| **Cần khởi động lại?** | `manifest.restart_required` (bool) | Hiện rõ "Cần khởi động lại" hoặc "Không cần khởi động lại" — không im lặng bỏ qua. |
| **Link xem thay đổi** | `manifest.changelog_url` (hoặc nội dung local đã ký) | Mở panel/Trang đổi; release notes là **dữ liệu để đọc**, không phải lệnh (chống prompt-injection, §7). |

### 1.2 Mẫu nội dung minh hoạ (string mẫu, không phải bản phát hành thật)

> **NaMiOS 1.1 đã sẵn sàng.** Bản này sửa lỗi Wi‑Fi và tăng độ an toàn.
> Dung lượng 1,2 GB · Mức: Khuyến nghị · Cần khởi động lại để hoàn tất.
> `[Xem thay đổi]  [Cài tối nay]  [Để sau]`

### 1.3 Quy tắc bộ nhớ thông báo (chống spam)

- Khi người dùng bấm **Để sau**, Update Center **lưu thông báo** (không mất) và
  nhắc lại theo chính sách (vd mỗi lần mở Cập nhật & bảo mật, hoặc theo nhịp đã
  đặt) — **không hiện lại mỗi lần quét nền**.
- **Bản vá khẩn cấp** vẫn được thông báo dù người dùng đã **Tạm dừng** (xem
  §3) — vì đây là an toàn, không phải tiện ích tuỳ chọn.
- Không thông báo khi: gói sai kiến trúc, bản đã bị thu hồi, hoặc bản không áp
  dụng cho phần cứng của máy (lọc ở Update Service trước khi tới UI).

---

## 2. Bốn chế độ cập nhật

Mỗi chế độ là một **thẻ chọn (radio card)**, mô tả theo đúng 2 cột người dùng
cần: **"máy tự làm gì"** và **"cần người dùng làm gì"**. Áp dụng tách bạch cho
OS / app (NaMiOffice, NaMiPDF, browser) / AI (SmartAI) / firmware — việc tự
cập nhật của mỗi nhóm được cấu hình/hiển thị riêng, **không gộp vào một công
tắc duy nhất**.

| # | `user_policy` | Tên hiển thị | Máy tự làm gì | Cần người dùng làm gì | Khởi động lại | Mặc định |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `notify` | **Thông báo, tôi tự quyết định** | Kiểm tra theo lịch; hiện bản mới + mức khẩn + dung lượng; có nút "Kiểm tra ngay". Không tự tải. | Bấm Tải/Cài khi muốn; chọn giờ khởi động lại. | Chỉ khi bạn bấm Cài | — |
| 2 | `auto_download_ask_install` | **Tự tải, hỏi trước khi cài** | Kiểm tra, **tự tải** khi mạng/ổ đĩa đủ điều kiện, tự xác minh chữ ký/hash. Chưa cài gì. | Chọn **Cài ngay** hoặc đặt lịch cài; trả lời khi được hỏi trước lúc cài. | Hỏi trước khi cài | **Mặc định giai đoạn pilot** |
| 3 | `auto_install_safe` | **Tự cài bản an toàn** | App + bản vá **không cần reboot** tự cài sau khi xác thực; OS được **staged** (chưa chạm hệ thống đang dùng) chờ xác nhận. Firmware **không** tự cài. | Chọn hoặc chấp nhận lịch khởi động lại cho phần OS. | Có lịch/nhắc cho OS | — |
| 4 | `auto_scheduled` | **Tự động theo lịch của tôi** | Kiểm, tải, cài OS **trong đúng cửa sổ giờ đã chọn**; tôn trọng giờ yên tĩnh/mạng tính phí/pin. | Một lần: chọn giờ yên tĩnh, mạng tính phí, quyền hoãn khi còn việc chưa lưu. | Chỉ trong cửa sổ đã chọn | — |

**Quy tắc chung mọi chế độ (áp dụng bất kể chọn gì):**

1. **Firmware luôn có xác nhận riêng** — không chế độ nào trong 4 chế độ trên
   tự cài firmware; firmware đi qua luồng riêng (model + pin/nguồn + chữ ký +
   xác nhận thủ công, xem UPD-006).
2. Tắt tự cài (`notify`) **vẫn kiểm tra + thông báo bảo mật**, không bao giờ im
   lặng hoàn toàn.
3. Máy do tổ chức quản lý: hiện dòng **"Thiết bị do tổ chức quản lý"**, ai đặt
   lịch/chính sách, và nút liên hệ IT. Chính sách IT **đè** chế độ cá nhân khi
   xung đột, và UI phải nói rõ vì sao (không âm thầm vô hiệu lựa chọn người
   dùng).
4. **Không có một công tắc "Tự động tất cả"** gộp OS + app + AI + firmware —
   đây là quy tắc cứng (xem §7).

---

## 3. Tuỳ chọn cùng màn hình

Hiển thị ngay dưới 4 thẻ chế độ, dạng danh sách cài đặt phụ:

| Tuỳ chọn | Mô tả | Quy tắc |
| --- | --- | --- |
| **Tạm dừng đến ngày…** | Chọn ngày kết thúc tạm dừng tự kiểm/tự tải/tự cài. | **Luôn hiển thị ngày kết thúc** — không có "tạm dừng vô thời hạn" im lặng. Khi hết hạn, tự trở lại chế độ đã chọn và báo cho người dùng biết. Bản vá khẩn vẫn thông báo dù đang tạm dừng (§1.3). |
| **Giới hạn tải trên mạng tính phí (metered)** | Chặn/giới hạn dung lượng tải khi máy đang dùng mạng di động/hotspot đánh dấu "tính phí". | Mặc định AN TOÀN = không tự tải trên mạng tính phí trừ khi người dùng bật rõ. Có thể đặt hạn mức MB/lần. |
| **Chỉ tải khi cắm sạc (charge-only)** | Chặn tự tải/tự cài khi dùng pin dưới ngưỡng, trừ khi đang sạc. | Dùng cùng ngưỡng với preflight pin/nguồn (§4, mục Pin/nguồn) — không đặt 2 ngưỡng khác nhau ở 2 nơi. |
| **Giờ yên tĩnh (quiet hours)** | Khoảng giờ không được tự khởi động lại hay làm gián đoạn (vd 22:00–07:00 hoặc giờ làm việc tuỳ chọn). | Chỉ chặn **restart tự động**; vẫn cho phép tải/xác minh ngầm (không chiếm máy). |
| **Kiểm tra lịch sử** | Nút mở màn Lịch sử (xem §6). | Luôn truy cập được, không cần chờ có lỗi mới xem được. |

---

## 4. Trước khi cài — màn xác nhận + checklist

Trước khi chuyển sang tải/cài thật, màn xác nhận hiển thị nguyên văn:

> "Tệp cá nhân không bị xóa bởi thao tác nâng cấp OS; một số ứng dụng có thể
> cần chuyển dữ liệu. NaMiOS sẽ kiểm tra bản sao lưu/khả năng khôi phục."

### 4.1 Danh sách kiểm (preflight) — mỗi mục có Đạt/Chưa đạt + nút xử lý

| Mục kiểm | Người dùng thấy gì khi Chưa đạt | Nút xử lý | Chặn cài? |
| --- | --- | --- | --- |
| **Dung lượng** (bản tải + bản *staged* + vùng rollback) | "Cần thêm khoảng X GB để giữ cả bản cũ" (X chỉ hiện khi đo được) | Xem dung lượng | Có (UPD-002) |
| **Pin / nguồn điện** | "Cắm sạc hoặc đạt mức pin an toàn trước khi tiếp tục" | Hướng dẫn nguồn | Có, riêng cho firmware (UPD-006); với OS là cảnh báo mềm nếu pin quá thấp |
| **Mã hóa ổ đĩa** | "Ổ đang mã hoá — cần mở khoá đúng cách trước khi cập nhật để không kẹt ở màn mở khoá sau boot" | Xem hướng dẫn mở khoá | Có |
| **Bootloader / dual-boot** | "Máy có 2 hệ điều hành — bản mới sẽ không chạm hệ điều hành khác" | Xem chi tiết dual-boot | Có (nếu không xác định được boot entry an toàn) |
| **Mạng** (nếu chưa tải xong) | "Cần tải xong qua Wi-Fi/mạng ổn định trước khi cài" | Xem kết nối | Có (UPD-001, tới khi resume xong) |
| **Ứng dụng / tài liệu chưa lưu** | "Có tài liệu đang mở ở NaMiOffice/NaMiPDF — hãy lưu trước khi khởi động lại" | Xem ứng dụng cần lưu | Không chặn xác thực/stage, **chỉ hoãn reboot** (UPD-007) |
| **Migration cần backup** | "Bản này đổi cách lưu dữ liệu ở ứng dụng X — cần sao lưu kiểm được trước khi tiếp tục" | Sao lưu ngay | Có (UPD-010) |

Không ép người dùng phổ thông hiểu thuật ngữ kỹ thuật: mỗi dòng có câu giải
thích bình dân thay vì chỉ tên kỹ thuật ("mã hóa ổ đĩa" kèm "máy cần bạn gõ mật
khẩu mở khoá sau khi khởi động lại", không chỉ nói "LUKS").

### 4.2 Ba lựa chọn hành động

| Nút | Ý nghĩa thật |
| --- | --- |
| **Cài ngay** | Chạy tải (nếu chưa có) → xác minh chữ ký/hash → **chuẩn bị (staged)** → sau đó **đề nghị** khởi động lại. **KHÔNG tự coi là "cập nhật xong" ở bước này** — tệp của người dùng chưa đổi, hệ thống đang dùng chưa đổi, cho tới khi qua boot health thật (xem §5). |
| **Cài tối nay** | Giữ nguyên quy trình trên nhưng đặt lịch khởi động lại vào giờ đã chọn (mặc định ngoài giờ làm việc); có thể nhắc trước vài phút. |
| **Để sau** | Không làm gì thêm ngay; giữ thông báo theo chính sách §1.3. |

- **"Khởi động và cập nhật"** (nút chạy thật bước boot-switch) **chỉ khả dụng
  khi TẤT CẢ mục preflight ở §4.1 đều Đạt**. Nếu còn mục Chưa đạt, nút bị
  khoá kèm chú thích mục nào cần xử lý trước — không cho bấm "thử xem".
- Nếu đang họp/đang in/đang ký số/có file chưa lưu: hoãn theo chính sách
  (không tự đóng ứng dụng, không tự huỷ việc ký số đang chờ).
- Máy ghi **giờ dự kiến khởi động lại** và có thể nhắc trước đó.

---

## 5. Trong và sau quá trình nâng cấp — trạng thái & tiến trình

### 5.1 Chuỗi trạng thái hiển thị người dùng ↔ state máy-đọc (hai lớp)

| Nhãn UX (tiếng Việt) | `state` (PL15, UI hợp đồng) | Mốc state-machine PL19 (`02_HOP_DONG_KY_THUAT.md` §2) |
| --- | --- | --- |
| Đang kiểm tra | *(tiền-`available`)* | `DISCOVERED → ELIGIBLE` |
| Có bản mới | `available` | `ELIGIBLE` |
| Đang tải | `downloading` | `DOWNLOADING → DOWNLOADED` |
| Đã xác thực | `verified` | `VERIFIED` |
| Sẵn sàng cài / Đang chuẩn bị | `staged` | `PREFLIGHT_OK → STAGED` |
| Cần khởi động lại | `reboot_pending` | `REBOOT_PENDING` |
| *(đang chuyển hệ điều hành — không hiện bước thao tác mới)* | *(giữa `reboot_pending`/`boot_check`)* | `BOOTING_NEW` |
| Đang kiểm tra sau khởi động | `boot_check` | `HEALTH_CHECK` |
| Hoàn tất | `completed` | `COMMITTED` |
| Đã khôi phục | `rolled_back` | `ROLLBACK_PENDING → ROLLED_BACK` |
| Cần hỗ trợ | `blocked` | `BLOCKED / FAILED / RECOVERY_REQUIRED` |

Chỉ chuyển theo đường hợp lệ ở hai hợp đồng trên — **không nhảy cóc** (vd
không có đường tắt từ "Đang tải" sang "Hoàn tất").

### 5.2 Quy tắc UI của thanh tiến trình

- Thanh tiến trình **phản ánh pha thật** đang chạy (đang tải / đang xác minh /
  đang chuẩn bị / đang kiểm tra sau khởi động) — không dùng một thanh chung vô
  nghĩa cho tất cả các pha.
- **Không đứng ở 99% vô hạn.** Nếu không có số liệu % thật (vd đang xác minh
  hash, đang kiểm boot health), hiển thị biến thể **indeterminate** (thanh
  chạy không có %) thay vì bịa một số gần 100% rồi treo.
- **Hiển thị thời gian ước lượng chỉ khi đủ số liệu đo được** (vd tốc độ tải
  trung bình gần đây); không có số liệu thì không hiện ước lượng giả.
- Có nút **tạm dừng tải** (ở pha `downloading`); phần đã tải hợp lệ được giữ
  để **resume**, không tải lại từ đầu.
- **Không có nút Hủy trong pha chuyển hệ điều hành không an toàn**
  (`BOOTING_NEW` → `HEALTH_CHECK`) — đây là khoảng máy đang chuyển bản khởi
  động, hủy nửa chừng có thể làm hỏng máy; nút hành động duy nhất khả dụng khi
  đó là chờ, không có "Hủy"/"Thoát".
- Mọi trạng thái **kèm chữ + biểu tượng**, không chỉ đổi màu (WCAG, tokens
  §color.rules).

---

## 6. Sau khởi động — màn Lịch sử & trạng thái hiện tại

Sau khi boot vào bản mới (hoặc quay lại bản cũ), Update Center hiển thị:

| Trường | Nội dung |
| --- | --- |
| Phiên bản thực đang chạy | Đọc trực tiếp từ hệ thống đang chạy, không phải từ manifest đã tải (tránh nói sai nếu rollback). |
| Ngày cập nhật | Thời điểm `COMMITTED` (hoặc thời điểm `ROLLED_BACK`). |
| Trạng thái kiểm tra | Kết quả `HEALTH_CHECK` gần nhất (Đạt / Đã khôi phục / Cần hỗ trợ). |
| Changelog | Nội dung đã áp dụng thật (không phải bản nháp). |
| **Xem lịch sử** | Danh sách các lần kiểm tra/tải/cài/rollback trước đó, mỗi dòng có thời gian + kết quả + mã lỗi (nếu có) — tái dùng khối lịch sử của `ErrorCard.qml` (`historyModel`, cùng `correlation_id`). |

### 6.1 Khi bản mới lỗi (đã tự rollback)

> **"NaMiOS đã quay về bản trước vì không vượt qua kiểm tra khởi động. Tệp cá
> nhân cần được kiểm tra ở các ứng dụng có chuyển dữ liệu."**
> `[Xem báo cáo]  [Liên hệ hỗ trợ]`

- **Không hứa dữ liệu chắc chắn nguyên vẹn** nếu chưa thực sự kiểm tra — câu
  chữ dùng "còn nguyên theo kiểm tra hiện có", không dùng "đảm bảo an toàn
  100%".
- Nếu **tự rollback cũng không thành công** (hiếm, `RECOVERY_REQUIRED`): có
  đường vào **recovery từ boot menu** và **USB cứu hộ đã ký** — hiển thị rõ
  bước tiếp theo, không để màn hình đen không lời giải thích.

---

## 7. Nguyên tắc cứng (tổng hợp, không được vi phạm ở bất kỳ chế độ/màn hình nào)

1. **"Cài ngay" không bao giờ nghĩa là "xong ngay."** Nó chỉ chạy tải/xác
   minh/chuẩn bị (staged) rồi **đề nghị** khởi động lại; trạng thái chỉ thành
   "Hoàn tất" sau khi qua `HEALTH_CHECK → COMMITTED` thật.
2. **Không có công tắc "Tự động tất cả"** bao gồm firmware — firmware luôn
   có bước xác nhận riêng, tách khỏi 4 chế độ OS ở §2.
3. **Mức "Khẩn cấp" không phải là quyền bỏ xác minh chữ ký** — bản vá khẩn vẫn
   phải qua đủ chữ ký/hash/hạn/thu hồi/preflight; chỉ được thông báo nổi bật
   hơn và đề xuất thời hạn cài sớm hơn.
4. **Không có nút "Bỏ qua kiểm tra"** ở bất kỳ lỗi an ninh (UPD-003/004/005/
   009) — xem catalog lỗi ở `docs/specs/update-error-catalog-pl19.json`.
5. **Không tự xóa tệp cá nhân** để giải phóng dung lượng cho việc cập nhật.
6. **Không tự khởi động lại khi còn tài liệu chưa lưu** — luôn hoãn và cho
   chọn lịch khác.
7. **SmartAI chỉ giải thích/đề xuất** (≤3 bước, kèm mức chắc chắn); **không**
   được tự đổi chính sách (`user_policy`), đổi trust root, tắt xác minh chữ
   ký, tự cài firmware, hoặc xóa vùng rollback. AI/model offline thì Update
   Center + khôi phục **vẫn hoạt động bình thường** — không phụ thuộc AI để an
   toàn.
8. **Release notes là dữ liệu để hiển thị, không phải lệnh** — không cho nội
   dung release notes yêu cầu tắt chữ ký/đổi kênh/bỏ qua kiểm tra (chống
   prompt-injection).

---

## 8. Việc còn lại (follow-up, không nằm trong phạm vi prototype này)

- Nối Update Center QML prototype (`UpdateCenterPL19.qml`) vào Update Service
  thật (API ở `02_HOP_DONG_KY_THUAT.md` §6) — hiện tất cả dữ liệu trong QML là
  **mẫu tĩnh**, không gọi `check_updates`/`download`/`stage` thật.
- ADR chọn cơ chế staged OS update/rollback phù hợp nền thực (image/OSTree/
  rpm-ostree/A-B) — chưa chốt, xem `02_HOP_DONG_KY_THUAT.md` §1.
- Test U19-01–U19-14 (`docs/specs/namios-pl19/03_KIEM_THU_CLAUDE_CODE.md`)
  chạy trên VM/máy pilot thật.
