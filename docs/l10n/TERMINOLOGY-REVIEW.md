# NaMiOS — Rà soát thuật ngữ EN↔VI (terminology review)

**Phạm vi:** `design/glossary.vi.json` + chuỗi của NaMiOS tự viết
(`distro/live-build/config/includes.chroot/opt/namios/namios_i18n/locale/{en,vi}.json`
— CLI `namios` + wizard "Welcome to NaMiOS"). Có đọc tham chiếu (KHÔNG sửa) các spec
`docs/l10n/*-SPEC.md`, `translations/vi-overlay/`, `translations/desktop-overlay/`,
`docs/design/DESIGN-SYSTEM.md`, `usr/share/namios-branding/logo/brand.json`.

**Trạng thái:** `verified_on_host: NO` — rà soát trên văn bản (text review), CHƯA chạy
thử trên desktop NaMiOS thật. Không có `git commit`/push trong phiên này.

---

## 1. File đã sửa

| File | Số dòng sửa | Loại sửa |
|---|---|---|
| `distro/live-build/config/includes.chroot/opt/namios/namios_i18n/locale/vi.json` | 11 | thuật ngữ (`file`→`tệp`), chính tả nhất quán (`xóa`→`xoá`, `khóa`→`khoá`), bù nghĩa còn thiếu (`volume`→`phân vùng`), thêm thuật ngữ kỹ thuật giữ nguyên (`mount`) |
| `distro/live-build/config/includes.chroot/opt/namios/namios_i18n/locale/en.json` | 1 | làm rõ nghĩa ví dụ tìm kiếm (xem §2.2) |
| `design/glossary.vi.json` | 1 sửa + 1 thêm | gọn lại "Rollback"; thêm mục mới "Mount (storage)" |

Cả 3 file đã qua `python3 -m json.load` — hợp lệ JSON. Không đổi key/id, chỉ đổi
value theo đúng yêu cầu nhiệm vụ. Không đụng `.gh-token`, logic code, hay cấu hình Plasma.

---

## 2. Quyết định thuật ngữ

### 2.1 "File" → "Tệp" trong luồng phổ thông (áp lại đúng quy tắc glossary đã có)

Glossary (`design/glossary.vi.json` dòng 13) đã chốt: *"Không dùng 'file' trần trong
luồng phổ thông."* Nhưng `vi.json` còn 7 chỗ dùng "file" trần trong đúng luồng phổ thông
(wizard Welcome + 2 chuỗi help CLI). Đã sửa:
- `welcome.ui.default_apps.docx_label/xlsx_label/pdf_label`: "Mở file .docx:" → "Mở tệp .docx:" (và .xlsx/.pdf tương tự).
- `welcome.migrate.error.bitlocker_key_skipped`: "tên file khớp mẫu…" → "tên tệp khớp mẫu…".
- `welcome.migrate.error.no_available_rename` / `destination_conflict_renamed`: "file đích" → "tệp đích".
- `cli.parser.arg.manifest_path_help` / `evidence_path_help`: "Đường dẫn file manifest/evidence report." → "Đường dẫn tệp manifest/evidence report." (giữ nguyên "manifest"/"evidence report" — đây là danh từ nghiệp vụ CLI-001/ECO đã dùng tiếng Anh xuyên suốt file, không phải chỗ cần dịch; chỉ từ "file" chung chung đổi theo glossary).

**Lưu ý phân vùng ngữ cảnh:** khối `cli.*`/`eco.*` trong file này là CLI cho người
*vận hành/kỹ thuật* (giữ nguyên nhiều danh từ Anh: manifest, evidence, repo, id, JSON,
operation_id, WP, merge) — tôi KHÔNG dịch thêm các danh từ nghiệp vụ đó vì chúng không
phải "File" trần (không mâu thuẫn quy tắc glossary, vốn chỉ áp cho từ "File" cụ thể).
Khối `welcome.*` là UI người dùng phổ thông — đã áp đúng "File → Tệp" không ngoại lệ.

### 2.2 "khai thue"/"hoc bac" → ví dụ có/không dấu rõ nghĩa hơn

`cli.parser.arg.service_query_help` minh hoạ tính năng "tìm theo tên phổ thông, có/không
dấu" (ECO-007) nhưng 2 ví dụ gốc là hai TỪ KHÁC NHAU đều không dấu ('khai thue', 'hoc
bac') — không chứng minh được tính năng. Sửa cả EN lẫn VI dùng CÙNG MỘT từ ở 2 dạng
(có dấu / không dấu) để ví dụ thật sự minh hoạ đúng tính năng:
- EN: `"Search keyword, with or without diacritics (e.g. 'khai thue' or 'khai thuế')."`
- VI: `"Từ khoá tìm kiếm, có dấu hoặc không dấu đều được (vd 'khai thue' hoặc 'khai thuế')."`

### 2.3 "volume" (tiếng Anh trần) → "phân vùng" (nhất quán trong cùng 1 file)

Trong khối `welcome.migrate.error.*`, cùng khái niệm "Windows volume" đã dịch
"Phân vùng Windows" ở `volume_unsafe_prefix` nhưng lại để "volume" trần (không dịch)
ở `cannot_list_volume` và `hibernation_detected` — 2 cách gọi khác nhau cho cùng một
khái niệm trong cùng 1 nhóm khoá. Đã thống nhất về "phân vùng" ở cả 3 chỗ.
`hibernation_detected` cũng dịch thêm "ngủ đông (hibernated)" và "Khởi động nhanh (Fast
Startup)" (theo mẫu "VN + (English)" đã dùng cho firmware/kernel/sandbox trong glossary)
thay vì để nguyên cụm "hibernated/Fast Startup" tiếng Anh.

### 2.4 Chính tả "xoá/khoá" (oá) vs "xóa/khóa" (óa) — chọn chuẩn "oá"

`vi.json` tự mâu thuẫn chính tả NGAY TRONG 1 FILE: dòng 19 "khoá" (từ khoá) nhưng dòng
119 (cũ) "khóa" (khoá khôi phục BitLocker); dòng 59 "xoá" nhưng dòng 104 (cũ) "xóa".
`docs/design/DESIGN-SYSTEM.md` (tài liệu khoá/chốt mà glossary phải bám theo) và
`design/glossary.vi.json` đều dùng kiểu **"oá"** ("xoá", "khoá", "hoạ"). Đã chuẩn hoá
`vi.json` về kiểu "oá" cho khớp 2 nguồn trên.

> **Cảnh báo phạm vi rộng hơn (CHƯA sửa — ngoài phạm vi nhiệm vụ này):**
> `translations/vi-overlay/po/*.vi_NM.po` (~17.8k dòng, là lớp phủ dịch KDE upstream,
> nhiệm vụ này nói rõ "KHÔNG mass-translate upstream KDE") CŨNG mix cả 2 kiểu chính tả
> ("xóa" 10 lần / "xoá" 16 lần; "khóa" 12 lần / "khoá" 8 lần — đã đo bằng `grep -c`).
> Đây là nợ kỹ thuật thật nhưng sửa an toàn 17k dòng cần một lượt riêng (và cần so khớp
> lại `msgctxt`/`.pot` thật trước khi đổi `msgstr`, theo đúng quy tắc chất lượng của
> `translations/vi-overlay/README.md`) — **đề xuất làm thành một việc riêng**, không
> gộp vào đây.

### 2.5 "mount" (thuật ngữ kỹ thuật chưa có trong glossary) → thêm mục + áp dụng

`welcome.ui.migrate.browse_button`/`dialog_title` dùng "đã mount" (tiếng Anh trần,
không có trong `design/glossary.vi.json`) trong một màn hình nhắm cả người dùng
KHÔNG rành kỹ thuật ("người quen dùng Windows"). Đã:
1. Thêm mục mới vào glossary: `Mount (storage)` → `Gắn (mount)` (category
   `chuyen_nganh`, theo đúng khuôn "thuật ngữ VN ngắn + (English giữ nguyên)" đã dùng
   cho firmware/kernel/compositor/sandbox/certificate/cache/log).
2. Áp vào 2 chuỗi UI: "Chọn thư mục Windows đã mount…" → "Chọn thư mục Windows đã gắn
   (mount) vào máy…" (và tương tự cho `dialog_title`).

### 2.6 "Rollback" trong glossary — gọn lại cho khớp khuôn chung

`term_vi` cũ "Khôi phục bản trước (lùi phiên bản)" là 2 cụm tiếng Việt đồng nghĩa dồn
vào nhau (lệch khuôn "VN ngắn + (English)" mà mọi mục chuyên ngành khác dùng — vd
Kernel/Compositor/Sandbox). Đã gọn thành `"Lùi phiên bản (rollback)"`, vẫn đúng nghĩa
("rollback" là từ mượn khá phổ biến trong giới kỹ thuật VN, khác với "Provenance" —
mục này tôi GIỮ NGUYÊN 2 cụm Việt "Nguồn gốc (xuất xứ)" vì "provenance" không phải từ
mượn thông dụng trong tiếng Việt kỹ thuật, nên glossary 2 cụm Việt hợp lý hơn).

### 2.7 Thuật ngữ đã ĐÚNG, không sửa (xác nhận lại để tránh sửa nhầm)

- `welcome.ui.ime_scale.ime_label` "Bộ gõ tiếng Việt:" khớp đúng glossary "Input Method
  Editor (IME)" → "Bộ gõ".
- `welcome.ui.default_apps.printer_label` "Máy in mặc định…" khớp "Printer" → "Máy in".
- `welcome.ui.done.body` "...trong Cài đặt..." khớp "Settings" → "Cài đặt".
- `cli.parser.cmd.service_help` "Danh bạ dịch vụ..." — dùng "danh bạ" (registry/
  directory theo nghĩa danh sách) phân biệt rõ với "Thư mục" (folder) — ĐÚNG, không
  gộp nhầm 2 khái niệm khác nhau dù tiếng Anh cùng gọi "directory".
- `welcome.ui.migrate.status_label` giữ "SAO CHÉP" viết hoa 2 từ (không phải HOA cả
  câu) — khớp đúng văn phong EN gốc "COPY ONLY" nhấn mạnh, không vi phạm quy tắc
  UX12-038 "không viết HOA toàn câu" (toàn câu vẫn chữ thường, chỉ nhấn 2 từ).

---

## 3. Phát hiện ngoài phạm vi sửa trực tiếp (để Cuong/người duyệt chuyên môn xem)

1. **Số liệu PL12.7 lệch với nội dung glossary thật.** `docs/design/DESIGN-SYSTEM.md`
   §PL12.7 ghi *"glossary.vi.json bổ sung 55 thuật ngữ (34 phổ thông + 21 chuyên
   ngành)"*. Đếm thật bằng `python3 -c "json.load(...)"` trước khi tôi thêm mục
   "Mount": **55 mục, nhưng 43 phổ thông + 12 chuyên ngành** — tổng khớp (55) nhưng tỉ
   lệ phổ thông/chuyên ngành KHÔNG khớp (34/21 vs 43/12 thật). Đây là tài liệu đã
   "chốt" nên tôi KHÔNG tự sửa `DESIGN-SYSTEM.md` (ngoài phạm vi file được giao) —
   chỉ ghi nhận để người duyệt đối chiếu lại số liệu. (Sau khi tôi thêm mục "Mount":
   56 mục — 43 phổ thông + 13 chuyên ngành.)
2. **Chính tả "lý" vs "lí" (quản lý/quản lí) lệch giữa 2 nhóm file.**
   `design/glossary.vi.json`, `vi.json` (namios_i18n), và
   `translations/vi-overlay/GLOSSARY-and-batch1.md` đều dùng **"lý"** (vd "Trình quản
   lý tệp", "Quản lý điện năng", "xử lý"). Nhưng `translations/desktop-overlay/vi/
   applications.tsv` + `systemsettings-categories.tsv` dùng **"lí"** ("Quản lí tệp của
   bạn", "Quản lí cửa sổ") — ĐÂY LÀ CÓ CHỦ Ý: dòng đó đi kèm `GenericName[vi]=Trình
   quản lí tệp` của chính Dolphin upstream (đã có sẵn, không bị đè — xem
   `docs/l10n/DESKTOP-NAMES-OVERLAY-SPEC.md` §5.1), nên khớp "lí" để nhất quán NỘI BỘ
   file `.desktop` đó, không phải lỗi. Vẫn ghi nhận: **quy ước chung của dự án NaMiOS
   (3/4 nguồn) nghiêng về "lý"**; nếu sau này viết thuật ngữ MỚI (không bị ràng buộc
   bởi một chuỗi upstream cụ thể) nên dùng "lý" cho nhất quán.
3. **Nút "Mở Hướng dẫn nhanh…" — viết hoa giữa câu.** `welcome.ui.done.
   quick_guide_button`: "Mở Hướng dẫn nhanh cho người quen dùng Windows" viết hoa "H"
   của "Hướng dẫn nhanh" như tên riêng một tài liệu/tính năng. Đây là lựa chọn hợp lý
   (coi là tên gọi cố định), nhưng CHƯA chắc có nhất quán với các tên tính năng khác
   trong toàn bộ UI NaMiOS (phạm vi rà soát của tôi chỉ có 1 file locale). **Đề nghị
   người duyệt bản ngữ xác nhận quy ước viết hoa tên tính năng/tài liệu dùng xuyên
   suốt UI** (nhất là khi `namios-welcome` có thêm màn hình mới).
4. **17.8k dòng `.po` trong `translations/vi-overlay/po/`** (lớp phủ dịch KDE
   upstream) có cùng kiểu lệch chính tả oá/óa nêu ở §2.4 — nhiệm vụ này nói rõ việc
   dịch hàng loạt KDE upstream NGOÀI phạm vi, nên tôi chỉ **đo và ghi nhận**, KHÔNG
   sửa. Nếu muốn dọn, nên làm thành việc riêng (so khớp `.pot` thật trước khi đổi
   `msgstr`, theo README của thư mục đó).
5. **`eco.*`/`cli.*` còn giữ nhiều danh từ tiếng Anh trần** (manifest, evidence,
   repo, WP, merge, operation_id...) — ĐÃ XÁC NHẬN đây là ngữ cảnh CLI cho người vận
   hành/kỹ thuật (không phải luồng phổ thông mà glossary nhắm tới), nên không sửa.
   Nếu sau này CLI `namios` được người dùng phổ thông chạy trực tiếp (không chỉ qua
   script/automation), nên xét lại mức độ Việt hoá các danh từ này.

---

## 4. Việc đã kiểm tra, không có vấn đề

- JSON hợp lệ cả 3 file (`vi.json`, `en.json`, `glossary.vi.json`) sau khi sửa.
- `en.json` và `vi.json` có đúng 1-1 khoá (không thiếu/thừa khoá nào cả 2 chiều).
- Không có lệch placeholder (`{reason}`, `{detail}`, `{id}`, `{status}`...) giữa cặp
  EN/VI ở bất kỳ khoá nào (kiểm bằng regex `\{[^}]+\}` so khớp từng khoá).
- Không đụng `.gh-token`, không đổi khoá/id, không đổi logic code, không đổi cấu hình
  Plasma, không chạy `git commit`/push.
