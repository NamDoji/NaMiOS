# ADR 0024 — NaMiFiles: định tuyến mở tệp theo MIME + CapabilityReport + SavePlan (PL20 M0)

- **Trạng thái:** proposed · **Mức thực thi:** `design` (kiến trúc + ánh xạ lên chuẩn freedesktop + gói thật; `verified_on_host: NO` — nhấp-đôi/định tuyến thật = vertical-slice/pilot ở M1).
- **Ngày:** 2026-11-10.
- **Năng lực:** Phụ lục 20 §4.1 (`docs/specs/namios-pl20/04_KIEN_TRUC_QA.md`) — "File routing và plugin contract". Bước 2 của prompt (`05_PROMPT_CLAUDE_CODE.md`).
- **Liên quan:** ADR 0005 (tách chế độ ứng dụng), ADR 0008 (chứng nhận theo tác vụ), ADR 0013 (office engine), ADR 0016 (design system), ADR 0018/0021 (SmartAI — AI KHÔNG tự gửi tệp online thay app local). Hiện vật thật: `distro/.../etc/skel/.config/mimeapps.list`, `distro/.../usr/share/namios/apps/default-app-manifest.json`, `tools/office-compat/` + `tools/pdf-compat/` (lớp nhận-diện rủi ro).
- **Nguồn chuẩn:** Freedesktop MIME-apps <https://specifications.freedesktop.org/mime-apps/latest-single/> · Shared-MIME-info <https://specifications.freedesktop.org/shared-mime-info/latest-single/>.

## Bối cảnh

Người dùng Việt kỳ vọng "nhấp đôi là mở đúng". Nhưng mở tệp theo **đuôi tên** là lỗ hổng: `Hoa_don.pdf.exe` đổi đuôi sẽ chạy mã thực thi. Kit §2.1 + §4.1 ra luật: **sniff nội dung trước, đuôi chỉ là gợi ý**; trước khi chuyển đổi/ghi định dạng khác phải **tạo bản sao + cảnh báo mất dữ liệu**. NaMiOS KHÔNG phải một "super-app" nuốt mọi loại tệp — mỗi app NaMi (NaMiOffice/NaMiPDF/NaMiArchive/NaMiImages/NaMiMedia…) **độc lập**, chỉ **chia sẻ design tokens** (ADR 0016) và một **hợp đồng định tuyến** chung do NaMiFiles (Dolphin) điều phối.

Nền tảng thật đã có: Dolphin + `shared-mime-info` + `mimeapps.list` + `.desktop MimeType=` của từng gói Debian. Thiếu là **lớp giữa**: chuẩn hoá bước sniff → giải quyết app mặc định → **CapabilityReport** (app đích làm được gì với tệp này) → **SavePlan** (không ghi đè bản gốc khi chuyển đổi rủi ro). Các inspector `namioffice-inspect` và `namipdf-inspect` đã tồn tại chính là **lớp nhận-diện rủi ro** cần nối vào đây.

## Quyết định

### D1 — Pipeline định tuyến 5 bước (nhấp-đôi / chuột-phải "Mở bằng")

```
(1) Trigger        nhấp-đôi, hoặc chuột-phải → "Mở bằng… / Chọn ứng dụng khác /
                   Luôn dùng ứng dụng này / Xem trước / Nén / Giải nén / Quét an toàn"
      │
(2) MIME SNIFF     shared-mime-info: content magic (chữ ký nhị phân) + cấu trúc,
                   ĐỐI CHIẾU đuôi tên. Lệch đuôi↔nội dung → KHÔNG tin đuôi.
                   Thực thi (ELF/PE/script #!) ngụy trang đuôi tài liệu → CHẶN,
                   hiện "Không nhận diện được định dạng / tệp có thể là chương trình"
                   + tùy chọn an toàn (xem, không chạy). Tệp lạ → "Không nhận diện".
      │
(3) RESOLVE        app mặc định từ mimeapps.list ([Default Applications]) →
                   .desktop → app id. "Mở bằng…" + mặc định là QUYỀN người dùng;
                   update app KHÔNG được reset lựa chọn im lặng.
      │
(4) CAPABILITY     app đích trả CapabilityReport: với biến thể định dạng này nó
     REPORT        làm được gì (view / edit / none), tính năng rủi ro, điều chưa rõ,
                   cảnh báo. Lớp nhận-diện = namioffice-inspect / namipdf-inspect
                   (+ archive/image inspector ở M1/M2). Không gộp "mở được"="sửa được".
      │
(5) OPEN + SAVEPLAN mở trong app đích (file từ USB/email/browser vào SANDBOX; preview
                   KHÔNG chạy script/macro). Khi lưu sang định dạng khác / chuyển đổi
                   rủi ro → SavePlan: TẠO BẢN SAO, không ghi đè bản gốc, liệt kê tính
                   năng sẽ mất (macro/lớp/liên kết/công thức/font/chú thích/chữ ký).
```

**NaMiOS KHÔNG phải super-app.** Mỗi app độc lập, cài/gỡ riêng, có `.desktop` + `MimeType=` riêng. NaMiFiles chỉ **điều phối**: không nhúng viewer của app khác vào chính nó (trừ preview sandbox chỉ-đọc). Thống nhất hình thức qua **design tokens dùng chung** (`design/tokens.json`, ADR 0016), KHÔNG qua một tiến trình khổng lồ.

### D2 — Registry định tuyến (kit §4.1) — một bản ghi cho mỗi association

Mỗi liên kết loại-tệp↔app là một bản ghi kiểm chứng được (nguồn sự thật = `mimeapps.list` + `default-app-manifest.json`, mở rộng thêm cột):

| Trường | Ý nghĩa |
|---|---|
| `mime` | kiểu MIME freedesktop (vd `application/pdf`) |
| `extension` | đuôi gợi ý (chỉ để đối chiếu, KHÔNG để quyết định) |
| `magic` | chữ ký nội dung dùng khi sniff |
| `app_id` | `.desktop` id app đích (vd `org.kde.okular.desktop`) |
| `action` | `view` / `edit` / `create` / `export` được hỗ trợ |
| `offline` | mở được khi tắt mạng hay không |
| `support_level` | **Xem / Sửa / Tạo / Chuyển đổi / Round-trip / Chưa thử** (xem FORMAT-MATRIX.md) |
| `priority` | thứ tự khi nhiều app cùng khai MimeType |
| `version` | phiên bản app đã kiểm |
| `test_fixture` | corpus F20 chứng minh |
| `permission` | quyền tối thiểu app cần |
| `owner` | đội chịu trách nhiệm |
| `last_verified` | ngày kiểm thật (hiện `null` / `verified_on_host: NO`) |

**Chống "chiếm mặc định":** không app nào được giữ mặc định cho hàng trăm MIME nó không xử lý tốt (kit §2.2). Mỗi association kèm `support_level`; người dùng đổi được ở Settings + reset an toàn (không hỏng hệ thống).

### D3 — Hợp đồng plugin viewer/editor (kit §4.1) — 4 lời gọi

NaMiFiles ↔ app đích qua hợp đồng (ánh xạ API kit §4.1), **không** cho app local tự fallback gửi tệp lên dịch vụ online chỉ vì không mở được:

1. **`OpenRequest(file_portal_handle, source_trust, intended_action)`** — truyền *handle qua portal* (không trao đường dẫn thô ra sandbox), kèm độ tin nguồn (local/USB/email/browser) + hành động dự định (view/edit/convert).
2. **`CapabilityReport(format_variant, features, unknowns, warnings)`** — app đích tự khai năng lực THẬT với biến thể này. Lớp nhận-diện rủi ro = `tools/office-compat/namioffice-inspect` (C0–C3 cho DOCX/XLSX/PPTX: macro/track-changes/pivot/mảng-động…) và `tools/pdf-compat/namipdf-inspect` (phân loại Text/Scan/Mixed/Signed/Protected + mã hoá/chữ ký/JavaScript/XFA/AcroForm, severity 0–3) — **kiểm TĨNH, không render, không chạy nội dung, không gọi mạng**.
3. **`SavePlan(output, lossy_features, signature_status)`** — bắt buộc khi ghi sang định dạng khác: output = **bản sao mới** (never-overwrite-original), liệt kê tính năng lossy + trạng thái chữ ký (không làm hỏng chữ ký/bản gốc). CAD: KHÔNG tự chuyển rồi ghi đè bản thiết kế (kit §4.4).
4. **`Result(error_code, safe_next_actions)`** — lỗi kèm hành động kế tiếp an toàn (vd "thiếu codec" / "cần OCR trước khi sửa" / "tệp có thể là chương trình"), không vòng-xoay-loading mãi.

### D4 — Bảo mật định dạng (kit §4.2) — bất biến mặc định

- **Preview chạy trong process sandbox KHÔNG quyền ghi file**; không chạy script/macro khi preview/thumbnail.
- **Archive** (NaMiArchive/Ark): chặn zip-slip/path-traversal (`../`, absolute, symlink/hardlink escape), archive-bomb, giới hạn số mục/kích thước/độ sâu nested; **không tự chạy chương trình sau giải nén**; mật khẩu nhập ở UI, **không log**.
- **SVG/PDF/CAD**: chặn script, external-reference/network-fetch, embedded-executable **mặc định**.
- **Ảnh/media**: decoder trong sandbox + fuzz + quota thời gian/tài nguyên; thumbnail quyền riêng.
- **Office**: macro chặn mặc định; Save-Safety theo NaMiOffice. **Quét malware KHÔNG thay được parser sandbox** (kit §4.2).
- Cập nhật codec/importer/renderer qua NaMiUpdates **có chữ ký + test hồi quy + rollback** (ADR 0017/0020).

### D5 — Giữ lựa chọn người dùng qua update (kit §4.1 + F20-10)

App mặc định + "Mở bằng…" là quyền người dùng. Khi update app (browser/media/Office) **không** được reset association im lặng; regression định dạng → rollback app. `mimeapps.list` do NaMiOS seed chỉ **đảm bảo mặc định chắc chắn** (chống race-condition theo alphabet khi nhiều `.desktop` cùng khai MimeType), KHÔNG ép buộc; người dùng ghi đè ở `~/.config/mimeapps.list` của mình.

## Hệ quả

- **Tích cực:** một pipeline trung thực, tái dùng chuẩn freedesktop (không viết lại File Manager), nối thẳng vào 2 inspector đã có; mỗi app giữ độc lập + chia sẻ tokens; không mất tệp gốc khi chuyển đổi.
- **Chi phí / chưa làm (`verified_on_host: NO`):** nhấp-đôi THẬT trong VM (DOCX/PDF/ZIP/PNG/MP3/MP4 mở đúng app), chặn đuôi-giả + archive-traversal thật, CapabilityReport/SavePlan từ app đích thật = **vertical-slice M1**. `CapabilityReport`/`SavePlan` hiện là **hợp đồng thiết kế** + 2 inspector CLI, chưa nối vào Dolphin qua service menu/KIO. NaMiMedia chưa có app nên nhánh media của pipeline chưa chạy được end-to-end.

## Corpus nghiệm thu (PL20 §4.4 — gate M1+)

F20-01 (Office đúng app + báo rủi ro + save bản sao + round-trip) · F20-02 (PDF chữ ký/scan/form không hỏng bản gốc) · F20-03 (ZIP/7z/tar + RAR/password/multi-volume — giải nén đúng hoặc cảnh báo, không escape/bomb) · **F20-04 (tên tiếng Việt, đuôi giả, path dài, USB rút giữa chừng — sniff đúng, KHÔNG chạy tệp giả, copy an toàn)** · F20-05 (ảnh EXIF/ICC) · F20-06 (media codec) · F20-07 (SVG/ODG/DXF/DWG) · F20-10 (đổi app mặc định giữ qua update) · F20-11 (mã độc/SVG external/archive traversal bị sandbox chặn).
</content>
