# NaMiOS — website giới thiệu và tải (nguồn cục bộ, pre-release)

Website tĩnh (HTML/CSS/JS thuần, không framework nặng) cho dự án NaMiOS, xây theo
`docs/specs/namios-pl17-website/` (file 01–05). Trạng thái dự án hiện tại: **pre_release**
— chưa có ISO nào được ký/phê duyệt, nên trang Tải **không có nút tải**, chỉ có
CTA "Nhận thông báo khi có bản thử nghiệm" và "Xem tiến độ".

**CHƯA TRIỂN KHAI THỰC TẾ.** Đây là source cục bộ để xem/chỉnh sửa trước khi có
domain, hạ tầng CDN và quy trình duyệt nội dung. Không có nút tải giả ở bất kỳ
đâu trong site này.

## Cách mở / chạy cục bộ

Nhiều trang (compatibility/apps/devices/namioffice/download, home-essentials)
dùng `fetch()` để đọc `data/*.json`. Trình duyệt **chặn fetch file cục bộ qua
`file://`** ở Chrome/Edge (CORS), nên cách chắc chắn nhất là chạy một local
server tĩnh trong thư mục `website/`:

```bash
cd website
python3 -m http.server 8080
# hoặc: npx serve .
# hoặc: php -S 127.0.0.1:8080
```

Rồi mở `http://127.0.0.1:8080/index.html`. Các trang thuần nội dung tĩnh
(`faq.html`, `about.html`, `privacy.html`, `security.html`, `smartai.html`,
`install.html`) có thể mở trực tiếp bằng cách double-click file (`file://`)
vì không fetch JSON, nhưng để nav/footer và toàn site nhất quán, vẫn nên dùng
local server.

Nếu bạn mở một trang cần JSON qua `file://`, trang sẽ hiển thị **error state**
rõ ràng (không phải màn trắng) kèm hướng dẫn chạy local server — xem
`js/compat-data.js#setError`.

## Chạy kiểm thử

```bash
cd website
node tests/validate.mjs
```

Script kiểm 4 nhóm (327 assertion ở lần chạy gần nhất, 0 lỗi):

- **A. `data/release-manifest.json`** khớp field bắt buộc của
  `data/release-manifest.schema.json`; xác nhận `status=pre_release` kéo theo
  `downloads=[]`, `architectures=[]`, `release_date=null`; `notify.mode=demo`.
- **B. `data/compatibility.json`** khớp `data/compatibility.schema.json` cho mọi
  bản ghi app/device (field bắt buộc, enum category/type/result/
  transparency_status, id không trùng).
- **C. Không có nút/link tải ISO giả**: khối `#download-cta` tĩnh trong
  `download.html` chỉ được chứa skeleton loading (không `class="btn"`, không
  `.iso`); quét toàn bộ `*.html` không có `href` trỏ thẳng `*.iso` nào.
- **D. Link nội bộ không 404**: mọi `href="*.html"` trong site trỏ tới file có
  thật trong `website/`.

Không có framework test (Jest/Vitest) được cài vì không muốn kéo `npm install`
qua mạng trong môi trường này; `tests/validate.mjs` chỉ dùng `node:fs` của
Node.js thuần (đã chạy thử với Node v24).

## Cấu trúc thư mục

```
website/
  index.html, apps.html, namioffice.html, compatibility.html, devices.html,
  smartai.html, security.html, download.html, install.html, faq.html,
  about.html, privacy.html
  css/tokens.css        — design tokens "Sen Việt" (từ branding/design-system/tokens.json)
  css/styles.css        — toàn bộ component (button/card/badge/table/form/accordion/…)
  js/main.js             — nav di động, focus, footer year (dùng mọi trang)
  js/compat-data.js      — fetch + helper hiển thị dùng chung cho dữ liệu compatibility
  js/compatibility.js    — logic trang /compatibility.html (tìm/lọc/bảng minh bạch)
  js/apps.js, js/devices.js, js/namioffice.js — render từ compatibility.json cho từng trang
  js/download.js         — đọc release-manifest.json, dựng CTA đúng theo status, form demo
  data/release-manifest.json(.schema.json)   — nguồn sự thật phát hành
  data/compatibility.json(.schema.json)      — ma trận ứng dụng + thiết bị
  assets/logo/            — bản sao từ branding/logo-sen-viet-v2 (logo Sen Việt đã duyệt)
  assets/screenshots/      — ảnh build thật (boot-evidence) + mockup SVG có nhãn rõ
  tests/validate.mjs       — kiểm schema + no-fake-download + link nội bộ
```

## Nguồn asset và quyền sử dụng (asset inventory rút gọn)

| Asset | Nguồn | Trạng thái quyền |
| --- | --- | --- |
| `assets/logo/*.svg`, `NaMiOS_App_Icon_256.png` | Sao chép nguyên văn từ `branding/logo-sen-viet-v2/` (logo "Sen Việt" chủ dự án duyệt làm phương án nhận diện) | **Chưa phải nhãn hiệu đã đăng ký** — xem `branding/logo-sen-viet-v2/README.md`. Dùng được cho preview nội bộ, cần chốt trước khi public. |
| `assets/screenshots/namios-vi-desktop-hero-20261107.png` | `docs/releases/boot-evidence/namios-vi-desktop-hero-20261107.png` — ảnh chụp thật, build QEMU nội bộ, 07/11/2026 | Ảnh build thật của dự án, không phải ảnh ngoài. Ghi rõ "chưa phải bản cài đặt công khai" ở mọi nơi dùng. |
| `assets/screenshots/namios-ruby-desktop-qemu-20261106.png` | `docs/releases/boot-evidence/namios-ruby-desktop-qemu-20261106.png` — ảnh chụp thật, 06/11/2026, theme "Ruby" | Như trên. |
| `assets/screenshots/mockup-*.svg` | Tự vẽ bằng mã nguồn (SVG hình khối, không dùng ảnh AI/bên thứ ba) cho NaMiOffice/Device Hub/SmartAI — các giao diện này **chưa có bản build thật để chụp** | Ghi nhãn "MOCKUP — bản thiết kế dự kiến" trực tiếp trong hình (watermark + `<title>`/`<desc>` SVG) và trong `alt` text mọi nơi dùng. |
| Font `Noto Sans` / `DejaVu Sans` (tham chiếu qua `font-family`, không tự host file font) | Google Noto (SIL OFL) / DejaVu (Bitstream Vera + public domain) — theo đúng `tokens.json` | Giấy phép mở, phù hợp nhúng web. Website hiện dùng font hệ thống qua `font-family` fallback, **chưa tự host file font** — nếu cần tự host để đạt ngân sách hiệu năng/offline, phải tải đúng bản OFL và thêm vào danh mục này. |
| Favicon | `assets/logo/NaMiOS_App_Icon.svg` | Như logo ở trên. |

Không dùng ảnh người, thiết bị, phong cảnh hay logo đối tác nào khác trong site
này. Không có bản đồ lãnh thổ nào được dùng.

## Chốt pre_release → beta → stable (không làm thủ công)

Theo `docs/specs/namios-pl17-website/03_DOWNLOAD_TUONG_THICH.md` §1 và
`docs/release-gates.md`:

1. **pre_release (hiện tại)** — `status` trong `data/release-manifest.json` là
   `"pre_release"`, `downloads=[]`. Trang Tải chỉ hiển thị CTA nhận tin/tiến độ.
   Đây là trạng thái **duy nhất** hợp lệ khi chưa có ISO đã ký.
2. **Chuyển sang `beta`** CHỈ được làm qua CI release-gate, không sửa tay field
   `status`: CI phải xác nhận (a) ISO đã build + ký bằng khóa **production**
   (khóa hiện tại trong repo là khóa **TEST-ONLY**, xem
   `docs/security/UPDATE-KEY-CATALOG.md`), (b) SHA-256 + chữ ký khớp file thật
   đã upload, (c) URL tải thật trả về đúng MIME/size, (d) `known_issues` và
   `minimum_hardware` phản ánh kết quả đo thật, (e) license/notice đã duyệt.
   Sau khi tất cả xanh, CI mới được phép ghi `status: "beta"` +
   `downloads: [...]` vào manifest (qua PR có review, không phải script tự
   động commit thẳng).
3. **Chuyển sang `stable`** cần thêm: release gate 8 điều kiện đỏ (RG-01..08
   trong `docs/release-gates.md`) không còn điều kiện nào mở, pilot thật đã
   chạy, mirror đồng bộ hash, recovery/rollback đã kiểm trên máy thật.
4. Ở cả hai bước, **không có cơ chế "editor đổi nhãn phát hành bằng tay"** —
   trang web chỉ đọc field `status`, nó không tự suy luận hay cache trạng thái
   cũ.

## Honest notes (bắt buộc đọc trước khi public)

- **Không có nút tải giả ở đâu cả.** Đã kiểm bằng `tests/validate.mjs` nhóm C —
  khối CTA trên `download.html` chỉ render nút khi `status !== "pre_release"`
  và khi đó bắt buộc phải có `downloads[]` không rỗng với `sha256` hợp lệ.
- **Form "Nhận thông báo" đang ở chế độ demo.** `data/release-manifest.json
  → notify.mode = "demo"`. `js/download.js` không gọi bất kỳ API/network nào
  khi submit — chỉ hiển thị thông báo xác nhận cục bộ và `form.reset()`.
  Không có email nào được gửi đi, lưu lại hay xử lý. Xem `privacy.html`.
- **Ảnh sản phẩm:** hai ảnh desktop là ảnh chụp build thật trong QEMU (có ngày,
  đường dẫn nguồn trong `docs/releases/boot-evidence/`); ba hình còn lại
  (NaMiOffice, Device Hub, SmartAI) là **mockup tự vẽ**, có nhãn "MOCKUP —
  bản thiết kế dự kiến" ngay trong hình và trong `alt` text — không trình bày
  như ảnh chụp thật.
- **Mọi claim "đã có/đã thử" đọc từ `data/release-manifest.json` hoặc
  `data/compatibility.json`**, không phải do trang viết tay. Thay đổi một
  trạng thái thật thì sửa JSON, không sửa câu chữ trong HTML.
- **Chưa có kênh liên hệ/hỗ trợ/bảo mật công khai chính thức** — `about.html`
  và `security.html` nói rõ điều này thay vì bịa một email.
- **Logo "Sen Việt" chưa phải nhãn hiệu đã đăng ký** — xem
  `branding/logo-sen-viet-v2/README.md`; cần tra cứu nhãn hiệu trước khi dùng
  đại trà/public.
- **Chưa triển khai thực tế lên bất kỳ domain hay CDN nào.** Đây là source cục
  bộ; không có URL staging nào tồn tại ngoài việc chạy local server như hướng
  dẫn ở trên.

## Known blockers / chưa làm (không phải do agent quên, mà do thiếu đầu vào thật)

Theo đúng `05_PROMPT_CLAUDE_CODE.md` mục "dữ liệu chủ dự án cần chốt":

1. Domain chính thức + hạ tầng tải/CDN — chưa có.
2. ISO đã ký, khóa công khai, checksum thật, release notes — chưa có (khóa
   hiện tại trong repo là TEST-ONLY).
3. Yêu cầu máy tối thiểu đã đo thật, danh sách thiết bị/app đã thử trên phần
   cứng thật — chưa có (xem bảng minh bạch, toàn bộ record hiện là "Chưa xác
   minh" hoặc "Không thể công bố").
4. Bộ logo sen cuối cùng (bản này là phương án đang xem xét, không phải bản
   chốt cuối), ảnh screenshot sản phẩm đầy đủ hơn, quyền wallpaper/font tự host
   — chưa chốt.
5. Email hỗ trợ/bảo mật, chính sách quyền riêng tư đã ký duyệt, chủ thể pháp lý
   — chưa có.

Các mục này **không chặn việc xem/chỉnh sửa bản preview pre-release** trong
thư mục này — chúng chặn việc public hóa trang Tải như một sản phẩm "đã sẵn
sàng" cho người dùng thật.

## Accessibility & chất lượng đã tự kiểm (mức tác giả, chưa phải audit độc lập)

- Skip link, focus-visible rõ (viền 3px theo `--focus-ring`), landmark
  `header/nav/main/footer`, heading theo thứ tự (h1 → h2 → h3), alt text mô tả
  cho mọi ảnh (kể cả mockup ghi rõ "MOCKUP"), form có `<label>` gắn `for`, lỗi
  form hiển thị bằng văn bản (không chỉ màu).
- `prefers-reduced-motion: reduce` tắt animation/skeleton-wave.
- Màu sắc lấy đúng từ `branding/design-system/tokens.json` (bảng Sen Việt),
  kèm bảng `contrast_table` đã tính WCAG 2.2 trong file tokens gốc — **đã đo
  bằng công thức, CHƯA kiểm bằng screen reader/thiết bị thật hay audit Axe
  độc lập**. Coi đây là "đã thiết kế đúng hướng", không phải "đã chứng nhận
  AA".
- Responsive: layout dùng CSS Grid/Flexbox + `clamp()`, test thủ công bằng
  cách resize cửa sổ trình duyệt xuống ~390px và lên ~1440px (không có ảnh
  chụp màn hình tự động kèm theo trong lần bàn giao này).

Nếu cần audit Axe/Lighthouse/screen reader thật, đó là bước **chưa làm** trong
lần bàn giao này — ghi vào backlog, không tự nhận đã đạt khi chưa chạy công cụ
thật.
