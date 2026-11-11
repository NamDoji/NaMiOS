# NaMiOS Assistant — chatbot đọc lỗi/ảnh chụp màn hình cho người dùng cuối

- **Mốc:** scaffold đầu tiên, 11/11/2026.
- **verified_on_host: NO cho lớp giao diện PySide6** (``ui.py``/``__main__.py``/
  hook cài đặt) — container phát triển hiện tại KHÔNG có PySide6/display
  (headless, không cài được venv ở đây — xem mục 7). **ĐÃ chạy thật** (không
  phải chỉ đọc lại) toàn bộ lớp lõi KHÔNG-GUI (``config``/``engine.*``/
  ``branding``) bằng Python 3.11 thật trong sandbox này — xem mục 6 cho danh
  sách cụ thể đã xác minh.

## 1. Đây là gì — và KHÔNG phải là gì

NaMiOS Assistant là một **chatbot CHỈ ĐỌC/GIẢI THÍCH**: người dùng dán một
thông báo lỗi hoặc đính kèm ảnh chụp màn hình lỗi, app phân loại lỗi đó về
một **mảng hệ thống** (boot/network/display/wine/office/print/ime/update/
audio/storage) rồi trả lời bằng hướng dẫn xử lý từng bước.

**KHÔNG** liên quan tới ``src/namios_smartai`` (engine Tool Broker điều phối
tác vụ có quyền thay đổi hệ thống thật — policy/capability/consent/audit, xem
``docs/adr/ADR-0018``/``ADR-0021``) hay trợ lý bash đang ship
``/usr/local/bin/namios-smartai`` (kế hoạch ≤3 bước + cổng xin phép +
``pkexec``). NaMiOS Assistant **không tool nào, không capability nào, không
tự chạy lệnh thay đổi hệ thống nào** — chỉ đọc văn bản người dùng cung cấp và
trả lời bằng chữ. Hai hệ thống không đụng tới mã nguồn/file/binary của nhau.

## 2. File đã tạo (TOÀN BỘ mới, không sửa file có sẵn nào)

| File | Vai trò |
| --- | --- |
| `includes.chroot/opt/namios/namios_assistant-src/__init__.py` | Gói Python — re-export + đăng ký i18n khi import |
| `includes.chroot/opt/namios/namios_assistant-src/__main__.py` | `python3 -m namios_assistant` — mở cửa sổ (import PySide6 trì hoãn) |
| `includes.chroot/opt/namios/namios_assistant-src/ui.py` | Cửa sổ chat PySide6 (bong bóng chat, nút Dán lỗi/Đính kèm ảnh/Gửi, chạy engine trong `QThread`) |
| `includes.chroot/opt/namios/namios_assistant-src/branding.py` | Đọc `brand.json` (fail-safe, có fallback cứng) + dựng QSS "Sen Việt" |
| `includes.chroot/opt/namios/namios_assistant-src/config.py` | Nạp `AssistantConfig` (api_key/model/base_url) từ env > file config |
| `includes.chroot/opt/namios/namios_assistant-src/_i18n.py` | Catalog VI/EN riêng của module (`assistant.*`), đăng ký qua `namios_i18n.add_catalog` |
| `includes.chroot/opt/namios/namios_assistant-src/engine/classify.py` | Đoán mảng hệ thống theo từ khoá (không NLP/không model) |
| `includes.chroot/opt/namios/namios_assistant-src/engine/knowledge_base.py` | Nạp + xếp hạng KB ngoại tuyến (JSON) |
| `includes.chroot/opt/namios/namios_assistant-src/engine/offline_backend.py` | Backend ngoại tuyến — LUÔN chạy được, không cần mạng |
| `includes.chroot/opt/namios/namios_assistant-src/engine/online_backend.py` | Backend trực tuyến TUỲ CHỌN (urllib thuần, không phụ thuộc pip mới) |
| `includes.chroot/opt/namios/namios_assistant-src/engine/ocr.py` | OCR ảnh qua `tesseract` đã đóng gói sẵn (fail-safe nếu thiếu) |
| `includes.chroot/opt/namios/namios_assistant-src/engine/backend.py` | `AssistantEngine` — điều phối offline/online, không bao giờ raise |
| `includes.chroot/opt/namios/namios_assistant-src/kb/starter_kb.json` | KB khởi điểm: 19 lỗi thường gặp, 10 mảng, song ngữ |
| `includes.chroot/usr/share/applications/namios-assistant.desktop` | Launcher "NaMiOS Assistant / Trợ lý NaMiOS" |
| `hooks/normal/0305-namios-assistant.hook.chroot` | Cài `/opt/namios/namios_assistant` + wrapper `/usr/bin/namios-assistant` (mirror `0300-namios-welcome.hook.chroot`) |
| `usr/share/namios/docs/SMARTAI-ASSISTANT.md` | File này |

**KHÔNG đụng:** `src/namios_smartai/**`, `/usr/local/bin/namios-smartai*`,
`usr/share/plasma/plasmoids/org.namios.smartai`, `namios-smartai.desktop`,
`usr/share/namios/smartai-tools.schema.json`, `namios_welcome*`, skel Plasma
configs, calamares, bootloader, `.gh-token`, package-lists (không cần sửa —
`python3-pyside6.qtwidgets` và `tesseract-ocr`/`tesseract-ocr-vie` ĐÃ có sẵn
trong `0110-desktop-familiar.list.chroot`/`0420-pdf.list.chroot` cho
NaMiOffice/NaMiPDF, module này chỉ TÁI DÙNG, không khai báo thêm gói nào).

## 3. Kiến trúc backend — offline KB luôn chạy, online LLM tuỳ chọn

```
text (đã dán, hoặc đã OCR từ ảnh)
  -> engine.classify.classify_subsystem()        # đoán mảng (gợi ý, không bắt buộc đúng)
  -> engine.offline_backend.OfflineKbBackend      # LUÔN chạy trước — tra kb/starter_kb.json
  -> NẾU AssistantConfig.is_online_configured:
       engine.online_backend.OnlineLlmBackend.ask()
         thành công -> dùng câu trả lời online, note ghi rõ TÊN MODEL
         lỗi/timeout/phản hồi sai định dạng -> OnlineBackendError
           -> AssistantEngine bắt lỗi, dùng LẠI câu trả lời offline đã có
              sẵn (không gọi lại, không chờ thêm), note ghi rõ LÝ DO rơi
              về offline (đã qua redact_text)
```

`AssistantEngine.ask()` là hợp đồng DUY NHẤT UI cần biết — luôn trả về
`AssistantAnswer(text, source, subsystem, kb_match_ids, note)`, **không bao
giờ raise**. `source` chỉ nhận `"offline_kb"` hoặc `"online_llm"` — UI hiển
thị `note` NGAY DƯỚI câu trả lời, không được bỏ qua field này (xem mục 5
"Honest UX").

### 3.1 Ship OFFLINE (không cần mạng, không cần khoá gì)

- Toàn bộ `engine/classify.py` + `engine/knowledge_base.py` +
  `engine/offline_backend.py` + `kb/starter_kb.json` (19 entry, 10 mảng: boot
  2, network 3, display 1, wine 2, office 2, print 2, ime 1, update 2,
  storage 2, audio 2).
- OCR qua `tesseract-ocr`/`tesseract-ocr-vie` (đã đóng gói sẵn cho NaMiPDF) —
  thiếu tesseract trên máy → `OcrResult(available=False, ...)`, UI yêu cầu
  dán văn bản thủ công, KHÔNG crash.
- Toàn bộ giao diện (cửa sổ, nút, brand QSS) mở được dù KHÔNG có mạng/khoá gì.

### 3.2 Cần CẤU HÌNH thêm (TUỲ CHỌN — không cấu hình thì KHÔNG dùng được, không fallback giả)

Backend AI trực tuyến CHỈ gọi khi **cả ba** giá trị sau đều có — thiếu một
trong ba, `AssistantConfig.is_online_configured` là `False` và app KHÔNG BAO
GIỜ thử gọi (không đoán nhà cung cấp mặc định):

| Nguồn | Biến/khoá |
| --- | --- |
| Biến môi trường (ưu tiên cao nhất) | `NAMIOS_ASSISTANT_API_KEY`, `NAMIOS_ASSISTANT_MODEL`, `NAMIOS_ASSISTANT_BASE_URL`, `NAMIOS_ASSISTANT_TIMEOUT_SECONDS` (tuỳ chọn, mặc định 20s) |
| File `$XDG_CONFIG_HOME/namios/assistant.json` | `{"api_key": "...", "model": "...", "base_url": "...", "request_timeout_seconds": 20}` |

Giao thức giả định: `POST {base_url}/chat/completions` kiểu OpenAI chat
completions (`{"model", "messages": [...]}`, đọc `choices[0].message.content`)
— hình dạng phổ biến nhất cho cổng/gateway tương thích nhiều nhà cung cấp.
Trỏ `base_url` tới BẤT KỲ dịch vụ nào implement đúng hình dạng này (tự lưu trữ
hay thương mại) đều dùng được, KHÔNG hardcode một nhà cung cấp cụ thể nào.

File `assistant.json` chứa `api_key` dạng thuần văn bản (như nhiều app desktop
khác) — **khuyến nghị đặt quyền file `600`** (`chmod 600
~/.config/namios/assistant.json`) thủ công; module chỉ ĐỌC, không tự tạo/ghi
file này.

## 4. OCR ảnh chụp màn hình

`engine/ocr.py` gọi `tesseract <ảnh> stdout -l vie+eng` qua
`namios_security.run_argv` (argv tĩnh, không shell, đúng quy ước WP8). Ba
tình huống:

1. **Có tesseract, đọc được chữ** → điền thẳng văn bản OCR vào ô nhập, người
   dùng xem lại rồi bấm Gửi (KHÔNG tự gửi thẳng — luôn cho người dùng kiểm
   tra OCR có đúng không trước khi gửi).
2. **Có tesseract, không đọc được chữ nào** (ảnh mờ/không có chữ) → báo rõ
   "OCR chạy được nhưng không nhận ra chữ nào", gợi ý ảnh rõ/to hơn.
3. **Thiếu tesseract** → báo rõ thiếu công cụ, gợi ý dán văn bản thủ công.

Không tình huống nào bịa văn bản OCR không có thật.

## 5. Honest UX — nhãn nguồn câu trả lời

Mọi `AssistantAnswer.note` LUÔN là một trong ba dạng (catalog `assistant.
engine.note.*` trong `_i18n.py`, song ngữ):

- *"Trả lời từ KB ngoại tuyến (không cần mạng) — KHÔNG phải mô hình AI."*
- *"Trả lời từ model AI trực tuyến (\<tên model\>)."*
- *"Backend AI trực tuyến không trả lời được (\<lý do đã lọc\>) — đang hiển
  thị KB ngoại tuyến thay thế."*

UI (`ui.py`) hiển thị `note` này làm một dòng nhỏ (`BubbleNote`, chữ nghiêng
xám) ngay dưới mỗi câu trả lời của assistant — không có đường nào trong mã để
hiển thị câu trả lời KB mà gắn nhãn "AI trực tuyến" hay ngược lại.

## 6. ĐÃ xác minh thật trong sandbox này (không chỉ đọc lại mã)

Chạy bằng Python 3.11 thật (`PYTHONPATH` trỏ `src/` cho
`namios_core`/`namios_i18n`/`namios_security` + gói `namios_assistant`),
KHÔNG mock:

- `KnowledgeBase.load_default()` nạp đúng 19 entry, 10 mảng.
- `AssistantEngine().ask(...)` cho 4 câu hỏi mẫu (Wi-Fi sai mật khẩu, thiếu
  DLL Wine, hết dung lượng đĩa, một câu vô nghĩa không khớp gì) — phân loại
  đúng mảng, trả đúng entry KB liên quan, câu vô nghĩa rơi đúng vào nhánh
  "không tìm thấy" (không bịa).
- Test song ngữ: cùng câu hỏi với `lang=Lang.EN` trả đúng bản tiếng Anh.
- **Test fallback online→offline THẬT**: đặt `NAMIOS_ASSISTANT_API_KEY`/
  `MODEL`/`BASE_URL` trỏ một cổng không tồn tại (`http://127.0.0.1:1/v1`) —
  `OnlineLlmBackend.ask()` nhận lỗi kết nối thật (`Connection refused`),
  `AssistantEngine` bắt đúng `OnlineBackendError`, rơi về offline, `note` ghi
  đúng lý do đã redact.
- `config.load_config()` đọc đúng file JSON tuỳ chỉnh (tham số
  `config_directory` tiêm cho test).
- `engine.ocr.ocr_image()` trên máy KHÔNG có tesseract → đúng
  `OcrResult(available=False, ...)`, không raise.
- `branding.load_brand_colors()` đọc đúng `brand.json` thật của repo (9 màu
  — tại thời điểm viết test này vẫn là bản "Sen Việt" v2.0 khớp `#CF3540`/...;
  khi wave sở hữu `brand.json` cập nhật sang NaMiOS v3 "Đông Sơn" sẽ là
  vermilion `#D64C3E`/navy `#092D4F`/gold `#DEA93E`...) VÀ fallback cứng khi
  không có file.
- `python3 -m py_compile` toàn bộ `.py` trong `namios_assistant-src/` — 0 lỗi.
- `bash -n`/`sh -n` cho cả hook ngoài lẫn wrapper heredoc bên trong — 0 lỗi.

## 7. CHƯA xác minh — cần desktop KDE Plasma 6 thật

Container phát triển này KHÔNG có PySide6 và KHÔNG cài được `python3-venv`
(môi trường pip "externally-managed", không có quyền cài gói hệ thống) nên
`ui.py`/`__main__.py` CHƯA được import/chạy thật — chỉ qua `py_compile` +
review API Qt (tên enum `Qt.TextFormat.MarkdownText`/`Qt.TextInteractionFlag.
TextSelectableByMouse`/chữ ký `QFileDialog.getOpenFileName`/`QMenu.exec` đã
đối chiếu tài liệu PySide6/Qt6 chính thức).

Checklist xác nhận trên máy/VM thật (điền khi có desktop, không tự đánh dấu
trước):

- [ ] `namios-assistant` mở được cửa sổ, không crash khi KHÔNG cấu hình
      online (chỉ KB ngoại tuyến) — bấm "Gửi" một lỗi mẫu, nhận đúng hướng
      dẫn, dòng trạng thái ghi "KB ngoại tuyến".
- [ ] Nút "Dán lỗi" lấy đúng clipboard text vào ô nhập.
- [ ] Nút "Đính kèm ảnh" → "Chọn tệp ảnh..." chọn một ảnh chụp lỗi thật có
      chữ tiếng Việt có dấu → OCR điền đúng văn bản (kiểm tra dấu không bị
      sai — `tesseract-ocr-vie` đã cài).
- [ ] Nút "Đính kèm ảnh" → "Dán ảnh từ bộ nhớ tạm" sau khi chụp màn hình
      (Print Screen) → OCR chạy trên đúng ảnh vừa chụp.
- [ ] Gõ `Enter` gửi câu hỏi; `Shift+Enter` xuống dòng trong ô nhập (không gửi).
- [ ] Bong bóng chat hiển thị đúng bên (câu hỏi bên phải màu đậm, trả lời bên
      trái màu sáng), chữ đậm/danh sách số trong câu trả lời KB hiển thị đúng
      định dạng (không hiện dấu `**`/`##` thô) — nếu hiện thô, kiểm tra phiên
      bản Qt có hỗ trợ `Qt.TextFormat.MarkdownText` trên gói Debian 13 trixie
      đóng gói hay không.
- [ ] Gỡ tạm `tesseract-ocr` khỏi máy, thử "Đính kèm ảnh" → app báo rõ thiếu
      công cụ, KHÔNG crash.
- [ ] Đặt `NAMIOS_ASSISTANT_API_KEY`/`_MODEL`/`_BASE_URL` trỏ một API thật có
      hiệu lực → dòng trạng thái đổi sang "model AI trực tuyến (\<tên\>)",
      câu trả lời gắn đúng nhãn nguồn.
- [ ] Màu sắc cửa sổ khớp bộ nhận diện NaMiOS v3 "Đông Sơn" — vermilion
      `#D64C3E` làm điểm nhấn header/nút (vai trò "action", thay cho `#CF3540`
      "Sen Việt" v2 cũ) — so với `usr/share/namios-branding/logo/brand.json`
      đang cài trên máy. LƯU Ý: `namios_assistant.branding` KHÔNG do wave này
      sở hữu — kiểm tra fallback cứng thật trong `namios_assistant-src/
      branding.py` trước khi tick mục này.
- [ ] Thay đổi kích thước cửa sổ, cuộn transcript nhiều tin nhắn dài — kiểm
      tra bong bóng chat không bị cắt chữ (hạn chế đã biết: `QListWidgetItem.
      setSizeHint` tính trước khi layout cuối cùng ổn định, có thể cần tinh
      chỉnh nếu chữ bị chồng/cắt trên Qt 6 bản đóng gói trixie thật).

## 8. Thêm entry KB mới (không cần sửa mã Python)

Nối thêm object vào mảng `"entries"` trong `kb/starter_kb.json`, giữ đủ khoá
bắt buộc: `id` (duy nhất), `subsystem`, `title_vi`/`title_en`, `cause_vi`/
`cause_en` (bắt buộc); `keywords_vi`/`keywords_en`/`patterns` (regex)/
`fix_steps_vi`/`fix_steps_en`/`rollback_vi`/`rollback_en` (tuỳ chọn, nên có
để xếp hạng/hướng dẫn tốt hơn). Entry thiếu khoá bắt buộc hoặc sai kiểu bị
**bỏ qua êm** (xem `engine/knowledge_base.py::_parse_entry`), không làm hỏng
toàn bộ KB. Operator cũng có thể bổ sung một bộ KB JSON riêng tại
`/usr/share/namios/assistant/kb/*.json` (quét TRƯỚC `starter_kb.json`, `id`
trùng thì bộ cài riêng thắng) mà không cần sửa file đóng gói cùng module.
