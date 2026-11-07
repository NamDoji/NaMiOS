# Phụ lục 12 (UX12-001–048) — Ma trận: yêu cầu → module hiện có → thay đổi → test

> Bắt buộc theo §4/§5 phụ lục 12: map để **tránh viết hệ trạng thái thứ hai**. Nguyên
> tắc: TÁI DÙNG `namios_sys` (`data_authority` — phím tắt không thành lệnh từ nội
> dung tài liệu), `namios_e08.actuator` (tập forbidden-tool-markers cho UX12-024),
> `namios_i18n` (song ngữ VI/EN + glossary); chỉ thêm hợp đồng còn thiếu vào package
> mới `namios_ux`. Đây là lõi **honest-core LÀM-ĐƯỢC-TẠI-CHỖ** (dữ liệu/logic thuần,
> kiểm được bằng `pytest`) — KHÔNG phải framework UI/Storybook/Figma, KHÔNG có
> nghiên cứu người dùng thật, KHÔNG tự xưng đã "đẹp và dễ dùng". Cột **Trạng thái**:
> `DONE-code` = logic + test xanh trong đợt này; `BLOCKED` = cần
> Figma/Storybook/ảnh có quyền/máy pilot/hội đồng nghiệm thu người thật (đúng
> §7 "điểm dừng" của các phụ lục trước); `N/A` = ngoài phạm vi `namios_ux` (quy
> trình con người/ảnh thật/máy thật).
>
> Phạm vi đợt này CHỈ bốn mảnh honest-core nêu trong chỉ đạo: `shortcuts.py`
> (registry phím tắt), `wallpaper.py` (hợp đồng + gate hình nền), `tokens.py`
> (WCAG contrast), `glossary.py` (thuật ngữ tiếng Việt thống nhất). Toàn bộ §4
> "Đầu ra Claude Code phải bàn giao" (Figma, Storybook, prototype, user test,
> accessibility audit, visual regression ảnh thật) nằm NGOÀI phạm vi đợt này —
> `namios_ux` cung cấp lớp dữ liệu/logic để các đầu ra đó DÙNG, không thay thế.

## 0. Bốn mảnh honest-core đã dựng

| Mảnh | File | Nội dung chính |
| --- | --- | --- |
| Registry phím tắt | `src/namios_ux/shortcuts.py` | `ShortcutBinding`/`ShortcutScope`/`PLevel` (:40-71), `detect_conflicts` (:167), `has_blocking_conflict` (:222), `resolve_override` (:232), `ShortcutAction`/`shortcut_action_is_safe` (:75-86, :308), `SHORTCUT_FORBIDDEN_MARKERS` tái dùng `namios_e08.actuator.FORBIDDEN_TOOL_MARKERS` (:20, :130-131). |
| Hình nền | `src/namios_ux/wallpaper.py` | `WallpaperEntry` (:42), `validate_wallpaper` (:81), `wallpaper_is_shippable` (:151), `HARD_GATE_CODES` (:66-74). |
| Design token / WCAG | `src/namios_ux/tokens.py` | `DesignToken`/`TokenCategory` (:36-54), `contrast_ratio` (:97), `meets_wcag` (:110), `token_pair_meets_wcag` (:118). |
| Glossary tiếng Việt | `src/namios_ux/glossary.py` | `REQUIRED_GLOSSARY_TERMS`/`GLOSSARY_TERM_IDS` (:34-46), `load_glossary` (:56), `missing_required_terms` (:73) — tái dùng `namios_i18n` (`ux.glossary.*` trong `src/namios_ux/_i18n.py`) làm kho thuật ngữ, không dựng kho song song. |

Test: `tests/unit/ux/test_ux_shortcuts.py` (23), `test_ux_wallpaper.py` (9),
`test_ux_tokens.py` (13), `test_ux_glossary.py` (7) `test_ux_i18n_parity.py` (3)
— tổng **52 test, 52 pass** (self-contained, không đọc file `design/*.json`
ngoài repo).

## 1. Tuyên ngôn thiết kế + bản đồ giao diện (§1–§2)

| UX12 | Yêu cầu | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| §1.1 nguyên tắc không thương lượng (6 điểm) | Tuyên ngôn thiết kế tổng thể | `N/A` | Chủ trương thiết kế + học Apple/Windows có chừng mực — quyết định con người/hội đồng thiết kế, không phải hợp đồng dữ liệu. |
| §2 bản đồ giao diện (9 khu vực) | Cấu trúc thông tin Desktop/Launcher/Settings/... | `N/A` | Thuộc Figma/mockup (đã có `docs/design/mockups/*.svg` ở nhánh làm việc khác) — ngoài phạm vi `namios_ux`. |

## 2. Design system có thông số (§3.1–§3.2)

| UX12 | Yêu cầu | Trạng thái | File:line |
| --- | --- | --- | --- |
| §3.1 hệ chữ tiếng Việt (font/type scale) | Token typography | `BLOCKED` | Cần chọn font thật (Be Vietnam Pro/Noto) + kiểm giấy phép + test hiển thị dấu — việc của `design/tokens.json`/nhóm thiết kế, không phải logic kiểm được bằng `pytest`. `TokenCategory.TYPOGRAPHY` (`tokens.py:40`) là CHỖ GẮN khi có giá trị thật. |
| §3.2 khoảng cách/độ cong/màu/độ nổi | Token spacing/radius/elevation | `BLOCKED` (một phần `DONE-code`) | `TokenCategory` đủ nhóm `SPACING`/`RADIUS`/`SIZE`/`MOTION` (`tokens.py:36-45`) làm hợp đồng; giá trị số cụ thể (4/8/12dp...) là quyết định thiết kế, không kiểm bằng invariant. |
| §3.2 [4] WCAG contrast (4.5:1 thường / 3:1 lớn) | Gate màu text/surface | `DONE-code` | `DesignToken` (`tokens.py:49`), `contrast_ratio` (`tokens.py:97`, công thức relative luminance WCAG tự viết), `meets_wcag` (`tokens.py:110`), `token_pair_meets_wcag` (`tokens.py:118`). INVARIANT "cặp màu dưới ngưỡng → fail": `tests/unit/ux/test_ux_tokens.py::test_token_pair_below_threshold_fails_gate`. |

## 3. Thành phần điều khiển và trạng thái (§3.3, UX12-001–012)

| UX12 | Yêu cầu | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| UX12-001 | Component library duy nhất | `BLOCKED` | Cần framework UI thật (Qt/GTK/web) + Storybook — ngoài phạm vi dữ liệu thuần. |
| UX12-002 | Mọi trạng thái (default/hover/.../200% chữ) | `BLOCKED` | Snapshot/visual test cần renderer thật. |
| UX12-003 | Nút (primary/secondary/destructive, 40×40dp) | `BLOCKED` | Hành vi UI thật + đo kích thước pixel. |
| UX12-004 | Link (phân biệt ngoài màu, nhãn vendor) | `BLOCKED` | UI thật. |
| UX12-005 | Combo box/select (tìm có dấu/không dấu) | `BLOCKED` | Có thể TÁI DÙNG tầng tìm kiếm có dấu/không dấu nếu đã có ở `namios_catalog`/`namios_cli` (ngoài phạm vi đợt này — không fork lại ở đây). |
| UX12-006 | Checkbox/radio/switch | `BLOCKED` | UI thật. |
| UX12-007 | Text input (nhãn/IME/lỗi) | `BLOCKED` | UI thật + test IME thật. |
| UX12-008 | Dialog/thông báo | `BLOCKED` | UI thật. |
| UX12-009 | Bảng/danh sách/cây (10.000 dòng mượt) | `BLOCKED` | Benchmark cần renderer + máy pilot thật. |
| UX12-010 | Menu ngữ cảnh | `BLOCKED` | UI thật. |
| UX12-011 | Focus/chỉ dẫn (Tab order, 12 luồng bàn phím) | `BLOCKED` | UI thật — tuy nhiên `shortcuts.detect_conflicts`/`resolve_override` (dưới) là phần LOGIC đứng sau menu "hiện shortcut cạnh action" (UX12-022). |
| UX12-012 | Responsive desktop (1366×768→2560×1440) | `BLOCKED` | Cần renderer + màn hình thật. |

## 4. Shell, cửa sổ, luồng quen thuộc (§3.4, UX12-013–018)

| UX12 | Yêu cầu | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| UX12-013 | Desktop + thanh tác vụ | `BLOCKED` | Desktop shell thật. |
| UX12-014 | Cửa sổ nhất quán (resize/snap/Wine+Linux) | `BLOCKED` | Window manager thật. |
| UX12-015 | File Manager quen tay | `BLOCKED` | App thật (có thể tái dùng `namios_pra`/`namios_sys.ActionKind.OPEN_FILE` ở tầng khác — ngoài phạm vi đợt này). |
| UX12-016 | Empty/loading/error states | `BLOCKED` | UI thật; mẫu lỗi thống nhất liên quan UX12-040 cũng `BLOCKED` theo cách tương tự (chuỗi lỗi có cấu trúc `code`/`message_vi` đã có khắp `namios_*` qua `ValidationError`, nhưng "8 tình huống có ảnh đã duyệt" cần UI). |
| UX12-017 | Chuyển động (120–250ms, reduce motion) | `BLOCKED` | Renderer + đo trên máy yếu thật. |
| UX12-018 | Giao diện SmartAI (điểm vào nhỏ, tắt không đổi UI) | `BLOCKED` (nền tảng liên quan `DONE-code` ở `namios_sys`) | `namios_sys.data_authority`/`goal`/`WorkContext` (Phụ lục 05) đã có hợp đồng "AI không tự hành động từ dữ liệu không tin cậy" — `namios_ux` không fork lại; phần UI/entry-point SmartAI là `BLOCKED`. |

## 5. Bộ phím tắt (§3.5, UX12-019–024)

| UX12 | Yêu cầu | Trạng thái | File:line |
| --- | --- | --- | --- |
| UX12-019 | Registry phím tắt (action/scope/priority/conflict/overridable), CI chặn 2 action SYSTEM trùng combo | `DONE-code` | `ShortcutBinding`/`ShortcutScope`/`PLevel` (`shortcuts.py:40-71`); `detect_conflicts` (`:167`) + `_scopes_intersect` (`:146`, định nghĩa "giao nhau": SYSTEM giao mọi phạm vi, WINDOW/APP chỉ giao chính nó + SYSTEM); `has_blocking_conflict` (`:222`) = CI gate. INVARIANT: `tests/unit/ux/test_ux_shortcuts.py::test_two_system_p0_same_combo_is_blocking_conflict`. |
| UX12-020 | Bộ phím tắt cơ bản P0 (30 ca thao tác) | `BLOCKED` (hợp đồng `DONE-code`) | `ShortcutBinding` đủ trường để NẠP bảng P0 thật của §3.5; chạy 30 ca thao tác bằng bàn phím cần shell/desktop thật. |
| UX12-021 | Tùy chỉnh/reset, cảnh báo xung đột + phím app chiếm | `DONE-code` | `resolve_override` (`shortcuts.py:232`): từ chối rõ `overridable=False` (`E_UX_SHORTCUT_NOT_OVERRIDABLE`), `unknown_action`, chiếm bởi app (`E_UX_SHORTCUT_CLAIMED_BY_APP`) tách khỏi xung đột chung (`E_UX_SHORTCUT_COMBO_TAKEN`); danh sách KHÔNG đổi khi bị từ chối. Test: `test_resolve_override_denied_when_claimed_by_app`, `test_resolve_override_denied_when_not_overridable`. Reset-về-mặc-định/export-import JSON = `BLOCKED` (cần UI + định dạng file thật, ngoài phạm vi hợp đồng lõi). |
| UX12-022 | Hướng dẫn trong menu (hiện shortcut cạnh action) | `BLOCKED` | UI thật; `ShortcutBinding.combo`/`action_id` là dữ liệu NGUỒN cho UI này, đã `DONE-code`. |
| UX12-023 | Nhiều bố cục bàn phím (US/VN/thiếu PrtSc/remote) | `BLOCKED` | Cần thiết bị/bố cục thật để kiểm; `ShortcutBinding.combo` là chuỗi tổ hợp theo-ký-tự — ánh xạ physical-key thật (layout-independent) ngoài phạm vi đợt này. |
| UX12-024 | Phím tắt không vượt quyền (root/gửi-tệp/bỏ-bảo-vệ) | `DONE-code` | `ShortcutAction` (`shortcuts.py:75`), `SHORTCUT_FORBIDDEN_MARKERS` = hợp nhất `namios_e08.actuator.FORBIDDEN_TOOL_MARKERS` + markers riêng gửi-tệp/bỏ-bảo-vệ (`:115-131`), `shortcut_action_is_safe` fail-closed (`:308`): command rỗng/chứa marker cấm/`privileged` chưa `confirmed` → `False`. Test: `test_root_shell_marker_blocks`, `test_send_file_marker_blocks`, `test_disable_protection_marker_blocks`, `test_sign_submit_marker_blocks`, `test_privileged_without_confirmation_blocks`. |

## 6. Hình nền Việt Nam (§3.6, UX12-025–032)

| UX12 | Yêu cầu | Trạng thái | File:line |
| --- | --- | --- | --- |
| UX12-025 | Tuyển chọn biên tập 12–18 ảnh, hội đồng duyệt | `N/A` (quy trình người) | Hợp đồng dữ liệu `WallpaperEntry` (`wallpaper.py:42`) sẵn sàng NẠP khi có ảnh thật; chọn ảnh/hội đồng là quy trình con người. |
| UX12-026 | Bản quyền/nguồn gốc, release manifest đủ license+evidence+hash+credit | `DONE-code` | `WallpaperEntry` (`:42`), `validate_wallpaper` (`:81`), `wallpaper_is_shippable` (`:151`) FAIL-CLOSED: thiếu `license`/`rights_evidence`/`sha256` → `False` qua `HARD_GATE_CODES` (`:66-74`). Test: `test_missing_license_blocks_shippable`, `test_missing_rights_evidence_blocks_shippable`, `test_missing_sha256_blocks_shippable`. |
| UX12-027 | Tiêu chuẩn ảnh (biến thể 16:9/16:10/..., 4K, smart crop) | `BLOCKED` (một phần `DONE-code`) | `WallpaperEntry.variants` (`:42`) + `E_UX_WALLPAPER_MISSING_VARIANTS` (soft issue, `wallpaper.py:81`) là hợp đồng "phải khai biến thể nào đã xuất"; xử lý ảnh/crop thật = `BLOCKED` (cần pipeline ảnh thật, ngoài phạm vi dữ liệu thuần). |
| UX12-028 | Chữ luôn đọc được trên nền (overlay/contrast) | `DONE-code` (nền tảng dùng chung) | TÁI DÙNG trực tiếp `tokens.contrast_ratio`/`meets_wcag` (`tokens.py:97,110`) — cùng công thức gate màu icon/chữ trên bất kỳ nền nào; đo trên 18 ảnh thật + thử mắt người = `BLOCKED`. |
| UX12-029 | Thay đổi có kiểm soát (album, opt-in, offline) | `BLOCKED` | Cần hệ quản lý album + tải mạng thật — ngoài 4 mảnh honest-core được giao. |
| UX12-030 | Hình khóa/đăng nhập (blur/tối đủ đọc mật khẩu) | `BLOCKED` | UI màn hình khóa thật; `token_pair_meets_wcag` là công cụ gate dùng được khi có overlay thật. |
| UX12-031 | Bản sắc Việt không khuôn mẫu, AI phải khai rõ | `DONE-code` | `WallpaperEntry.ai_generated` + `_ai_disclosed` (`wallpaper.py:76`) kiểm `credit`/`source` có nhắc tới AI chưa; `ai_generated=True` mà chưa khai → `E_UX_WALLPAPER_AI_UNDISCLOSED` nằm trong `HARD_GATE_CODES` → `wallpaper_is_shippable=False`. Test: `test_ai_generated_without_disclosure_blocks_shippable`, `test_ai_generated_with_disclosure_passes_hard_gate`. Duyệt caption/địa danh bởi biên tập viên người Việt = `N/A` (quy trình người). |
| UX12-032 | Bộ ảnh theo dịp, không tự tải khi chưa chọn | `BLOCKED` | Cần hệ tải/cache bộ ảnh thật. |

## 7. Tính dễ dùng, an toàn, kiểm chứng (§3.7, UX12-033–048)

| UX12 | Yêu cầu | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| UX12-033 | Nghiên cứu người Việt (5 người/nhóm) | `N/A` | Nghiên cứu người dùng thật. |
| UX12-034 | Bộ 12 tác vụ thử | `N/A` | Vận hành thật trên máy pilot. |
| UX12-035 | Accessibility (WCAG 2.2 AA) | `DONE-code` (một phần — nền tảng kiểm màu) | `tokens.contrast_ratio`/`meets_wcag` (`tokens.py:97,110`) hiện thực ĐÚNG hai ngưỡng AA nêu ở UX12 §3.2 [4]; test tự động/thủ công với screen reader + zoom 200% thật = `BLOCKED`. |
| UX12-036 | Tốc độ cảm nhận (benchmark cold/warm, p95) | `BLOCKED` | Máy pilot thật. |
| UX12-037 | Ngôn ngữ giao diện — glossary thống nhất (Tệp/Thư mục/Ứng dụng/Máy in/Cập nhật/Khôi phục/Bộ gõ) | `DONE-code` | `REQUIRED_GLOSSARY_TERMS`/`GLOSSARY_TERM_IDS` (`glossary.py:34-46`), catalog nguồn `ux.glossary.*` trong `src/namios_ux/_i18n.py` (TÁI DÙNG `namios_i18n`, không dựng kho song song); `load_glossary` (`:56`), `missing_required_terms` (`:73`) fail rõ thuật ngữ thiếu/rỗng. Test: `test_default_catalog_has_no_missing_required_terms`, `test_default_catalog_uses_canonical_vietnamese_terms`, `test_blank_value_counts_as_missing`. Rà soát 100% màn hình/thông báo thật = `BLOCKED` (chưa có UI). |
| UX12-038 | Định dạng/văn phong (ngày giờ, 50 chuỗi dài nhất ở 150%) | `BLOCKED` | Cần UI render thật để đo cắt chữ; định dạng ngày giờ VN đã có ở tầng khác (`namios_i18n`) không fork lại ở đây. |
| UX12-039 | Chân thực trạng thái (web/native/Wine, không đánh lừa "đã gửi/đã ký") | `N/A` (đã có ở tầng khác) | TÁI DÙNG nguyên trạng `namios_sys.ActionStatus`/`namios_sys.certification` (Phụ lục 05) và `namios_eco.status.PublishedStatus` — không dựng hệ trạng thái song song trong `namios_ux`. |
| UX12-040 | Mẫu lỗi thống nhất (title/nguyên nhân/mã/hành động an toàn) | `N/A` (đã có ở tầng khác) | `namios_core.validation.ValidationError` (`code`/`path`/`message_vi`) đã là mẫu dùng xuyên repo; `wallpaper.validate_wallpaper` TÁI DÙNG nguyên kiểu này thay vì tự định nghĩa lỗi hình nền kiểu khác. |
| UX12-041 | Quyền riêng tư ảnh/giao diện (không gửi SmartAI khi chưa cho phép) | `N/A` (đã có ở tầng khác) | Thuộc `namios_sys.data_authority`/`ContextResource` (Phụ lục 05) — `namios_ux` không fork lại cơ chế cấp quyền tài nguyên. |
| UX12-042 | Tùy biến không phá nhất quán (nút "Khôi phục mặc định") | `BLOCKED` | UI thật; `resolve_override` (shortcuts) là mảnh LOGIC tương ứng ở tầng phím tắt, đã `DONE-code`. |
| UX12-043 | Quy trình thiết kế → mã nguồn (token JSON/CSS/Qt/GTK) | `BLOCKED` | `DesignToken` (`tokens.py:49`) là hợp đồng Python; xuất pipeline JSON/CSS/Qt/GTK thật cho `design/tokens.json` = `BLOCKED` (ngoài 4 mảnh được giao, và file `design/tokens.json` đã tồn tại từ một nỗ lực khác — không đụng ở đây). |
| UX12-044 | Visual regression (snapshot sáng/tối/vi-en/100-200%) | `BLOCKED` | Cần renderer + ảnh chụp thật. |
| UX12-045 | Phản hồi người dùng ("Góp ý giao diện") | `BLOCKED` | UI thật. |
| UX12-046 | Tài sản thương hiệu (logo/icon/âm thanh có license+hash) | `DONE-code` (dùng chung cơ chế gate hình nền) | `HARD_GATE_CODES`/`wallpaper_is_shippable` (`wallpaper.py:66-74,151`) là CÙNG một gate fail-closed license/rights_evidence/sha256 mà UX12-046 đòi hỏi cho asset thương hiệu nói chung; áp dụng cho logo/icon/âm thanh THẬT (ngoài wallpaper) + asset manifest đầy đủ = `BLOCKED` (chưa có asset thật). |
| UX12-047 | Giao diện trên máy cũ (theme nhẹ, fallback compositor) | `BLOCKED` | Renderer + máy pilot thật. |
| UX12-048 | Hội đồng nghiệm thu (designer+engineer+QA+biên tập+pilot ký) | `N/A` | Quy trình con người, không phải code. |

## 8. Cổng phát hành giao diện v1 (đối chiếu honest-core đã có)

Theo "Cổng phát hành giao diện v1" cuối §3.7: *"không có phím tắt hệ thống
trùng nhau"* → `shortcuts.has_blocking_conflict` (`shortcuts.py:222`) là cơ
chế CI gate kiểm đúng điều kiện này (`DONE-code`, CHƯA nối vào pipeline CI
thật — việc nối job CI là `BLOCKED`, ngoài phạm vi sửa `.github/`/`pyproject.toml`
theo yêu cầu của đợt này). *"không có ảnh thiếu quyền"* →
`wallpaper.wallpaper_is_shippable` (`wallpaper.py:151`) kiểm đúng điều kiện
này (`DONE-code`). *"không mất dấu tiếng Việt"*, *"không có tác vụ P0 không
điều khiển được bằng bàn phím"*, *"không có thông báo an toàn sai sự thật"* =
`BLOCKED`/`N/A` (cần UI/renderer/screen-reader thật hoặc đã có ở tầng
`namios_sys`/`namios_i18n` khác, không fork lại).

## 9. Per-file-ignore ruff cần cân nhắc (KHÔNG tự sửa `pyproject.toml`)

Không cần thêm per-file-ignore nào cho đợt này. `UxErrorCode` ban đầu có hai
mã `E_UX_TOKEN_CONTRAST_FAIL`/`E_UX_TOKEN_INVALID_HEX` kích hoạt ruff `S105`
("possible hardcoded password", vì chứa chuỗi con `"token"` — cùng false-
positive đã ghi nhận ở `namios_e08`/`namios_pra`/...); đã đổi tên thành
`E_UX_COLOR_CONTRAST_FAIL`/`E_UX_COLOR_INVALID_HEX` (`src/namios_ux/_errors.py`)
để tránh né false-positive này mà KHÔNG cần sửa `pyproject.toml`. Nếu về sau
thêm hằng số chứa "token"/"secret"/"password" làm TÊN BIẾN (không phải nội
dung logic), cùng mẫu per-file-ignore `S105` cho `src/namios_ux/_errors.py`/
`_types.py`/`_i18n.py` (xem các khối tương tự hiện có trong `pyproject.toml`
cho `namios_compat`/`namios_smartai`/`namios_pra`/`namios_e08`) sẽ cần áp
dụng — nhưng KHÔNG cần ở trạng thái hiện tại.
