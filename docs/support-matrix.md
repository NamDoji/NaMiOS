# Support Matrix — NaMiOS

- **Trạng thái:** DESIGN (07/11/2026) — khung schema chứng nhận, **chưa có badge nào `verified` bằng dữ liệu thật**; không có máy/app/workflow nào đã được test trên bản build thật tại thời điểm viết.
- **Nguồn:** Phụ lục 10 (N10-058 "Ma trận phạm vi hỗ trợ") và Phụ lục 11 (APP11-028 "Chứng nhận workflow", APP11-019 "Dịch vụ web tự thay đổi").
- **Liên quan:** `docs/backlog/N10-backlog.md#N10-058`, `docs/backlog/APP11-backlog.md#APP11-028`, `docs/release-gates.md`, ADR 0008 (chứng nhận theo tác vụ), ADR 0012 (tiêu chí chuyển đổi và pilot).

## 1. Nguyên tắc: không một dấu xanh cho cả app

Nghiệm thu N10-058 nêu rõ: đổi browser/Wine/runtime/driver/version phải **tự động làm mất hiệu lực** phần liên quan của chứng nhận. Vì vậy một "chứng nhận" không phải một badge gắn vào tên app — nó là một bản ghi gắn vào **tổ hợp cụ thể (tuple)** đã được test, với ngày hết hạn ngầm định khi bất kỳ thành phần nào trong tuple thay đổi.

## 2. Schema tuple bắt buộc

Mỗi bản ghi support-matrix phải có đủ các trường sau (không được rút gọn khi công bố công khai):

```json
{
  "machine": {
    "model": "unknown",
    "revision": "unknown",
    "firmware_version": "unknown"
  },
  "os": {
    "distro": "unknown",
    "kernel": "unknown",
    "desktop": "unknown"
  },
  "app": {
    "id": "unknown",
    "version": "unknown",
    "hash": "sha256:unknown"
  },
  "route": "native|web|wine|remote_windows|vendor_port|unsupported",
  "driver_or_token": "unknown",
  "workflow_id": "unknown",
  "fixture_id": "unknown",
  "test_date": null,
  "evidence": [],
  "badge": "not_tested"
}
```

Đây là **mẫu schema gợi ý**, không phải kết quả test. Mọi trường `"unknown"`/`null`/`[]` phải được điền bằng dữ liệu thật trước khi đổi `badge`.

## 3. Badge hợp lệ

| Badge | Ý nghĩa | Điều kiện gán |
| --- | --- | --- |
| `verified` | Tuple đã chạy fixture thật, có evidence, đạt mọi tiêu chí workflow | CHỈ gán khi có `test_date` thật, `evidence` không rỗng, và không gate đỏ nào (xem `docs/release-gates.md`) áp dụng cho tuple đó |
| `partial` | Một phần workflow đạt, phần khác thất bại (ví dụ: mở file đạt, macro/ký số lỗi) | Dùng khi khác biệt chức năng trong cùng app cần tách rõ (đồng nhất N10-023: "mở được workbook nhưng macro hỏng = `partial`, không `ready`") |
| `blocked` | Có blocker đã biết (thiết bị/driver/pháp lý/license) ngăn tuple này hoạt động | Dùng khi biết lý do cụ thể, không phải "chưa rõ" |
| `expired` | Từng `verified`/`partial` nhưng một thành phần trong tuple đã đổi (browser/Wine/runtime/driver/version/OS) từ lần test gần nhất | Tự động áp dụng — không giữ badge cũ khi tuple thay đổi; hệ thống chứng nhận phải phát hiện thay đổi hash/version và tự hạ badge |
| `not_tested` | Chưa có dữ liệu test nào | Badge mặc định cho mọi tuple mới; đây là trạng thái của **toàn bộ** support-matrix tại thời điểm viết tài liệu này |

**Quy tắc chỉ-hạ (đồng nhất mô hình evidence/gate hiện có trong repo):** hệ thống chỉ được tự động hạ badge (ví dụ `verified`→`expired`), không được tự động nâng badge (ví dụ `not_tested`→`verified`) — nâng badge luôn cần evidence mới do test thật tạo ra.

## 4. Nhóm dịch vụ web — ghi chú riêng (APP11-019)

Với các dịch vụ web (Zalo Web, YouTube, Maps, TikTok, Facebook, WhatsApp…), trường `os`/`driver_or_token` không áp dụng theo cùng cách; thay vào đó support-matrix cho nhóm này cần thêm:

- `browser_version` thay cho phần OS driver.
- `service_side_change_detected`: cờ do synthetic smoke test phát hiện khi giao diện/API dịch vụ web đổi — khi cờ này bật, badge phải chuyển `expired`/`blocked` và ghi rõ nguyên nhân là **"sự cố dịch vụ hoặc tương thích"**, không phải "NaMiOS chưa cập nhật" (đồng nhất APP11-019).
- NaMiOS không thể chứng nhận "mãi mãi" một dịch vụ web vì vendor có thể đổi phía server bất kỳ lúc nào ngoài tầm kiểm soát — mọi badge `verified` cho dịch vụ web phải kèm `test_date` gần và được coi là **có hạn ngắn hơn** so với app native/Wine.

## 5. Quan hệ với Office / Fidelity Gate

Theo ADR 0013, Document Broker/Office Route Matrix/Fidelity Gate là code engine-agnostic đã có khung (`namios_pra.office_route`), nhưng validator ở đó **chặn gán `pass`** khi thiếu kết quả đối chứng Windows hoặc thiếu hash fixture. Support-matrix kế thừa cùng nguyên tắc: không gán `verified` cho bất kỳ tuple Office nào cho tới khi có 15 fixture thật + máy Windows đối chứng theo kế hoạch ADR 0013 mục 4 (hiện `blocked_external_dependency`).

## 6. Trạng thái hiện tại của chính ma trận này

| Nhóm | Số tuple đã có badge khác `not_tested` |
| --- | --- |
| Thiết bị (printer/USB/Wi-Fi/…) | 0 |
| Ứng dụng Windows qua Wine | 0 |
| Ứng dụng .NET | 0 |
| Office (round-trip DOCX/XLSX/PPTX) | 0 |
| Dịch vụ web (Zalo/YouTube/Maps/TikTok/Facebook/WhatsApp) | 0 |
| Chữ ký số / hóa đơn điện tử | 0 |

Toàn bộ 0 tuple này là **sự thật tại thời điểm viết (07/11/2026)**, không phải placeholder khiêm tốn — chưa có build host với phần cứng/pilot/Windows đối chứng để tạo bất kỳ bản ghi `verified` nào (xem lý do chi tiết theo từng mục trong `docs/backlog/N10-backlog.md` và `docs/backlog/APP11-backlog.md`, phần lớn đang `blocked-infra`).

## 7. Những điều KHÔNG được suy diễn từ tài liệu này

- Việc tồn tại schema này **không** có nghĩa là có công cụ nào đang tự động điền/kiểm tuple trong CI hiện nay.
- "Phát hiện VID/PID của thiết bị" không đồng nghĩa "chức năng đã dùng được" — badge `verified` chỉ gán cho workflow cụ thể đã test, không gán cho cả thiết bị nói chung (đồng nhất N10-047).
- Không dùng ma trận này để tuyên bố tỷ lệ phần trăm "tương thích tổng thể" của NaMiOS khi chưa có đủ tuple `verified` để tính mẫu số có ý nghĩa.
