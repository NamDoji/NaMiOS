# ADR-0022 — NaMiOS / NaMiOffice Extension & Automation SDK (M4)

**Trạng thái:** `specified` + reference validator CHẠY ĐƯỢC (có pytest). CHƯA nối vào trình cài extension/UNO thật của NaMiOffice. `verified_on_host: NO`.
**Ngày:** 10/11/2026 · **Liên quan:** PL (NaMiOffice v2 §5 Add-in/macro/automation), `docs/specs/SMARTAI-TOOL-BROKER.md`, `capability-registry.schema.json`.

## Bối cảnh

Người dùng/đối tác cần mở rộng NaMiOffice + tự-động-hoá tác vụ (ví dụ đếm từ, xuất PDF, chèn watermark). Microsoft dùng **VBA / COM / VSTO / Office.js** — đều phụ thuộc hệ sinh thái Windows/Office và **không chạy native trên NaMiOS**, nên không thể "tương thích add-in" một cách tổng quát. Cần một SDK **riêng của NaMiOS**, an toàn theo thiết kế, không bịa khả năng.

## Quyết định

NaMiOS Extension & Automation SDK = **manifest có chữ ký + mô hình quyền đóng + sandbox + tuyến tự-động-hoá Python/UNO**, gác bằng **validation 3 lớp** (một manifest chỉ AN TOÀN ĐỂ CÀI khi CẢ BA lớp pass — không lớp nào tự đủ):

1. **Cấu trúc** — `tools/namios-sdk/extension-manifest.schema.json` (JSON Schema 2020-12). `permission_scopes` là **ALLOW-LIST ĐÓNG**: giá trị ngoài danh sách (vd `filesystem:home`, `network:any`) bị schema chặn ngay.
2. **Chính sách (semantic)** — `validator.py::check_policy()`: đối chiếu tổ hợp quyền với `certification_level`; manifest hợp-lệ-schema vẫn **BỊ TỪ CHỐI** nếu xin nhiều quyền hơn mức đã review ("over-permissioned"); kiểm nhất quán revoke.
3. **Chữ ký (fail-closed cuối)** — `validator.py::check_signature()` + `manifest_signing.py`: ký **ed25519**, đối chiếu trust store ghim trước. Không chữ ký hợp lệ ⇒ không cài.

Triết lý (khớp `capability-registry.schema.json`): **"Schema hợp lệ KHÔNG cấp quyền."**

### Mô hình quyền (phạm vi đóng)
- `filesystem:document-only` / `filesystem:<scope>` (KHÔNG có `filesystem:home` toàn phần cho extension thường).
- `network:none` (mặc định) / `network:allowlist` (phải liệt kê host). KHÔNG có `network:any`.
- `office:document` — chỉ thao tác trên tài liệu đang mở, không chạm hệ thống.
- Script từ file tải về KHÔNG được quyền đọc toàn `home` (quy tắc kit §5).

### Tuyến tự-động-hoá
- **Python + LibreOffice UNO** (hoặc API NaMi), chạy trong phạm vi đã review; dry-run + rollback khi khả thi; lịch chạy do người dùng phê duyệt.
- VBA: **mặc định KHÔNG thực thi**; bảo toàn project khi có thể; chỉ xem trong môi trường bảo vệ. Excel/Word VBA gọi COM/Windows API — không chuyển bằng đổi-tên-hàm, không AI-tự-dịch-rồi-chạy.

## Vì sao 3 lớp
Schema chặn cú pháp/giá trị lạ nhưng không hiểu "quyền này có xứng mức review không"; policy chặn over-permission nhưng không chứng minh nguồn gốc; chữ ký chứng minh nguồn + toàn vẹn nhưng không giới hạn phạm vi. Ba lớp bù nhau, fail-closed.

## KHÔNG hỗ trợ (nói thẳng)
- **Office.js add-in gốc** — phụ thuộc host Office + dịch vụ Microsoft; không giả định chạy trong LibreOffice.
- **COM / VSTO / ActiveX** — phụ thuộc Windows; nếu khách bắt buộc → tuyến Windows/M365 có bản quyền (VM/remote), không chạy native.
- **VBA đầy đủ** — chỉ mô phỏng một phần qua LibreOffice Basic; không auto-run.
- Badge "tương thích add-in Office" tổng quát — cấm; chỉ xét adapter cho add-in cụ thể theo hợp đồng + test.

## Phạm vi trung thực (dev vs pilot)
Đã dựng ở dev: schema + reference validator 3 lớp + ký/kiểm ed25519 + 2 manifest mẫu (`word-count-vi`, `pdf-export`) + ví dụ tự-động-hoá chạy thật (python-docx/openpyxl) — **22 pytest PASS**. CHƯA làm: nối vào trình-cài-extension thật của NaMiOffice + chạy UNO trên LibreOffice thật (cần app + pilot = nhóm B); trust store hiện là khoá lab (chưa khoá phát hành thật).

## Tái lập
```sh
cd tools/namios-sdk && python3 -m pytest tests/ -q
python3 validator.py examples/word-count-vi.manifest.json
python3 automation_example.py <tài_liệu.docx>   # ví dụ đếm từ tiếng Việt
```
