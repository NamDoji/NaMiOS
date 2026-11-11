# NaMiOS — Đối chiếu bản quyền/nhãn hiệu cho rebrand "NaMi" trên app mặc định

**Yêu cầu Cuong (10/11/2026):** *"mọi app mặc định của NaMiOS phải có nhãn NaMi"* để nhận diện
thương hiệu, **nhưng KHÔNG được vi phạm bản quyền/nhãn hiệu**. Tài liệu này là căn cứ đối chiếu
cho **toàn bộ** app đã đổi nhãn (hook `0450`/`0452`/`0453`/`0454`) + các dịch vụ web bên thứ ba
**KHÔNG** đổi nhãn — để bất kỳ ai audit sau này biết chính xác vì sao mỗi dòng được phép.

**Trạng thái:** `partial` — rebrand mức **HIỂN THỊ** (`Name=`/`Name[vi]=`/`Comment[vi]=` trong
`.desktop`), **KHÔNG** build lại mã nguồn, **KHÔNG** đổi `Exec=`/`Icon=`/`MimeType=` của bất kỳ
app nào. `verified_on_host: NO` — máy soạn tài liệu này không có ảnh KDE trixie thật để đối chiếu
trực tiếp; hook áp dụng dò nhiều tên file `.desktop` khả dĩ và bỏ qua an toàn khi thiếu (xem
comment trong từng hook).

**Cập nhật 10/11/2026 (đối chiếu lại đúng 13 tên hiển thị chính thức ở
`docs/specs/namios-pl20/01_DANH_MUC_VA_THUONG_HIEU.md` §1):**
1. **NaMiMedia (MỚI)** — NaMiOS trước đó **KHÔNG cài** bất kỳ app phát nhạc/video
   hay codec hệ thống nào (lỗ hổng danh mục P0). Đã bổ sung
   `package-lists/0430-media.list.chroot` (gói `vlc` làm player chính duy nhất +
   `gstreamer1.0-plugins-good/bad/ugly` + `gstreamer1.0-libav` làm codec hệ
   thống cho app khác) và hook `0455-namimedia-brand.hook.chroot` đổi nhãn
   `vlc.desktop` → **"NaMiMedia"**. Xem mục 1a dưới cho chi tiết bản quyền/ghi
   chú bằng sáng chế của `gstreamer1.0-plugins-ugly`.
2. **firefox-esr**: `NaMiWeb (Firefox)` → **`NaMiBrowser (Firefox)`** (đổi
   tiền tố cho khớp tên danh mục chính thức "NaMiBrowser"; VẪN giữ chữ
   "Firefox" — không đổi gì về căn cứ nhãn hiệu Mozilla, chỉ đổi phần tiền tố
   NaMi).
3. **ark**: `NaMiNén` → **`NaMiArchive`** (khớp tên danh mục; `Comment[vi]`
   vẫn giữ "Quản lý nén — dựa trên Ark (KDE)").
4. **gwenview**: `NaMiẢnh` → **`NaMiImages`** (khớp tên danh mục; `Name[vi]`
   dùng dạng dài hơn "NaMiImages – Xem ảnh" vì tên tiếng Anh thuần không tự
   giải thích bằng tiếng Việt như "NaMiẢnh" cũ).
5. **fcitx5-config-qt (MỚI)** → **`NaMiType`**. Gói đã có sẵn trong
   `package-lists/0200-locale-vi.list.chroot` nhưng trước đợt này chưa có
   nhãn hiển thị NaMi. **Lưu ý quan trọng:** đã tải thật gói
   `fcitx5-config-qt_5.1.8-1` (trixie) và chạy `dpkg-deb -c` — file `.desktop`
   thật tên là `org.fcitx.fcitx5-config-qt.desktop` (KHÔNG phải
   `fcitx5-config-qt.desktop` như tên gói), và file này có **`NoDisplay=true`**
   trong bản gốc → mục này **ẨN khỏi menu Bắt đầu theo mặc định** dù đã đổi
   nhãn (NoDisplay không bị đụng, đúng nguyên tắc "chỉ đổi nhãn, không đổi
   hành vi"). Cần Cuong quyết định có bật `NoDisplay=false` để NaMiType hiện
   trong menu hay không — đây là quyết định UX, không phải quyết định bản
   quyền/nhãn hiệu.
6. **Security Center (MỚI)** → **`NaMiSecurity`**. File `.desktop`
   (`namios-security-center.desktop`) là tiện ích **do NaMiOS tự viết** (script
   `kdialog`/`zenity`), không phải rebrand app bên thứ ba — tạo bởi hook
   `0630-security-default.hook.chroot`. Vì hook đó chạy **SAU** hook `0454`
   (0454 < 0630 theo thứ tự `chroot_hooks`), nhãn `NaMiSecurity` được chốt
   **trực tiếp tại nơi tạo file** trong `0630` (không phải qua `0454`) — xem
   ghi chú thứ tự hook trong mục 1b dưới.

### 1a. Ghi chú bản quyền trung thực — `gstreamer1.0-plugins-ugly`

Gói `gstreamer1.0-plugins-ugly` (cài cùng NaMiMedia, package-lists/
`0430-media.list.chroot`) chứa decoder cho các định dạng **có liên quan bằng
sáng chế** tại một số khu vực pháp lý (một phần liên quan các profile
H.264/H.265 phân rã qua `gstreamer1.0-libav`, và các bộ mã hoá MP3/AAC thế hệ
cũ) — đây CHÍNH LÀ lý do Debian xếp gói vào nhóm "ugly" (khác "bad", chỉ là
chưa chín kỹ thuật, không liên quan pháp lý). Debian phân phối công khai
trong repo "main" vì đánh giá riêng của Debian là các bằng sáng chế liên quan
đã hết hạn/không áp dụng theo luật Mỹ/EU nơi Debian phân phối — **đây là đánh
giá của Debian, KHÔNG phải tư vấn pháp lý cho việc NaMiOS phân phối ISO tại
Việt Nam**. Một bản phát hành thương mại Việt Nam (bán/thu phí NaMiOS) **nên**
rà soát lại với luật sở hữu trí tuệ VN + các hiệp ước bằng sáng chế quốc tế VN
tham gia trước khi quảng cáo "phát được mọi định dạng video/audio" ra thị
trường. Gói vẫn được cài theo đúng yêu cầu "phát được nhạc/video" của Cuong —
đây là ghi chú cần đọc trước phát hành thương mại, không phải lý do để bỏ gói.

### 1b. Cảnh báo thứ tự hook (phát hiện 10/11/2026, CHƯA sửa — chờ Cuong chốt hướng)

`hooks/normal/0130-desktop-names-vi.hook.chroot` chạy **TRƯỚC** `0454`
(0130 < 0454) và tạo bản **shadow** trong `/usr/local/share/applications/`
cho 6 app cũng được đổi nhãn ở `0454`: `org.kde.ark.desktop`,
`org.kde.dolphin.desktop`, `org.kde.spectacle.desktop`,
`org.kde.discover.desktop`, `org.kde.kcalc.desktop`, `org.kde.konsole.desktop`.
Theo `XDG_DATA_DIRS` mặc định (`/usr/local/share/:/usr/share/`), file trong
`/usr/local/share` **thắng toàn bộ** (không merge theo khoá) file cùng
desktop-id trong `/usr/share`. Vì bản shadow được `0130` sao chép từ
`/usr/share` **trước khi** `0454` đổi `Name=`, bản shadow mang `Name=` GỐC
(tiếng Anh, chưa NaMi-hoá) — nhãn NaMi cho 6 app này **có thể không hiện**
trong menu thật dù `0454` chạy không lỗi. **CHƯA xác nhận trên ISO thật**
(`verified_on_host: NO`), nên đây chỉ là rủi ro đã ghi nhận, **chưa sửa**
trong đợt này (ngoài phạm vi yêu cầu rebrand/NaMiMedia hôm nay) — cần Cuong
chốt hướng: (a) đổi số `0130` ra sau `0454`, (b) cho `0130` tự đồng bộ lại
sau khi `0454` chạy, hoặc (c) gộp việc đổi `Name[vi]` vào luôn trong `0130`
cho 6 app trùng này. Xem comment chi tiết trong `0454-namios-apps-rebrand.hook.chroot`.

### 1c. CẢNH BÁO NHÃN HIỆU MỚI — nWord/nExcel/nPowerPoint gợi tên Microsoft Office (11/11/2026, CHƯA rà soát pháp lý)

**Đây là loại rủi ro KHÁC** với mọi dòng ở mục 1 phía trên. Mục 1 xử lý câu hỏi
*"NaMiOS có được phép ĐỔI TÊN rời khỏi tên gốc ("LibreOffice"/"Firefox"/…)
không?"* — câu trả lời luôn có vì giấy phép FOSS (MPL/LGPL/GPL) cho phép/TDF
còn yêu cầu đổi tên. Mục này xử lý câu hỏi **khác**: *"tên MỚI được chọn có tự
gây rủi ro nhãn hiệu với một bên thứ ba KHÁC (không phải TDF) không?"*

Yêu cầu Cuong (11/11/2026): đổi `NaMiWriter`/`NaMiSheet`/`NaMiSlides`/`NaMiDraw`
→ **`nWord`/`nExcel`/`nPowerPoint`/`nDraw`** (Start Center → **`nOffice`**),
theo khuôn "tên kiểu Windows, n + tên chức năng". Khác với nhãn `NaMiXxx` cũ
(không trùng/gợi tên sản phẩm cụ thể nào của Microsoft), các tên mới **cố ý
đọc rất gần** tên sản phẩm đã đăng ký nhãn hiệu của Microsoft:

- `nWord` ≈ **Word®** (Microsoft Word)
- `nExcel` ≈ **Excel®** (Microsoft Excel)
- `nPowerPoint` ≈ **PowerPoint®** (Microsoft PowerPoint)

Đây là **quyết định có chủ đích của Cuong** (ghi nhận, không phải lỗi của
agent) — nhưng tài liệu này có trách nhiệm **nói thẳng rủi ro** trước khi phát
hành rộng/thương mại, nhất quán với nguyên tắc đã có sẵn trong
**ADR `docs/adr/0009-quyen-so-huu-va-thuong-hieu.md` §7**: *"Không dùng tên
Windows trong thương hiệu HĐH; chỉ dùng khi mô tả khả năng tương thích. Không
dựng huy hiệu/logo gợi chứng nhận của Microsoft/MISA."* — nguyên tắc đó viết
cho tên "Windows"/badge chứng nhận; `nWord`/`nExcel`/`nPowerPoint` là cùng
HỌ rủi ro áp cho tên sản phẩm Office cụ thể của Microsoft, chưa có điều khoản
ADR 0009 nào xử lý thẳng trường hợp này — cần Cuong/luật sư bổ sung quyết
định rõ (sửa ADR 0009 hoặc ADR mới) trước khi phát hành rộng.

**Khuyến nghị (chưa thực hiện, không phải lý do chặn dev/ISO nội bộ):**
1. Tra cứu nhãn hiệu "Word"/"Excel"/"PowerPoint" tại Cục SHTT Việt Nam (NOIP) +
   đối chiếu phạm vi đăng ký quốc tế của Microsoft trước khi dùng tên này ở
   bản phát hành công khai/thương mại (cùng loại công việc Spike S-OWN-3 ở
   ADR 0009, mở rộng sang "nWord/nExcel/nPowerPoint").
2. Luật sư sở hữu trí tuệ rà rủi ro **gây nhầm lẫn nguồn gốc** (có thể khiến
   người dùng tưởng nWord "tương thích/được Microsoft công nhận" dù Comment
   đã ghi "dựa trên LibreOffice") trước khi quảng bá ra ngoài nhóm dev/pilot
   nội bộ.
3. Nếu rà soát cho kết quả rủi ro cao, có phương án lùi về nhãn không gợi
   trùng tên (vd. giữ "Văn bản"/"Bảng tính"/"Trình chiếu" làm `Name[vi]=`
   chính, bỏ tiền tố "n" + tên MS Office ở `Name=`) — đã có sẵn trong
   `Name[vi]=` hiện tại (Văn bản/Bảng tính/Trình chiếu/Vẽ/Văn phòng) nên việc
   lùi, nếu cần, KHÔNG phải viết lại từ đầu, chỉ đổi khoá `Name=` mặc định.

**`verified_on_host: NO` + CHƯA tra cứu pháp lý** cho riêng mục 1c này — khác
với phần còn lại của tài liệu (vốn chỉ cần đối chiếu giấy phép, không cần tư
vấn luật sư). Đây là ngoại lệ **CẦN** ý kiến luật sư thật trước khi phát hành
công khai, không chỉ đối chiếu tài liệu như các dòng khác trong bảng mục 1.

---

## 0. Nguyên tắc chung (đọc trước khi đọc bảng)

1. **Chỉ đổi NHÃN HIỂN THỊ, không đổi phần mềm.** Binary/`Exec=`/`Icon=`/`MimeType=`/mã nguồn của
   mọi app dưới đây **giữ nguyên 100%** bản gói Debian/upstream đã build sẵn. NaMiOS không build
   lại, không vá resource, không tự nhận "tự viết" cho bất kỳ app nào ở đây.
2. **Không tuyên bố endorsement.** Không nơi nào trong nhãn/Comment NaMiOS tuyên bố KDE e.V.,
   Mozilla, GNOME, The Document Foundation, hay tác giả gốc "chứng nhận"/"phát hành" bản NaMiOS.
   Ngược lại, mọi app đổi nhãn đều giữ dòng **tín dụng nguồn** ("dựa trên …") trong `Comment[vi]=`
   (KDE/FOSS) hoặc giữ nguyên tên nhãn hiệu trong `Name=` (Mozilla).
3. **Mozilla là trường hợp CHẶT nhất.** Chính sách nhãn hiệu Mozilla (Mozilla Trademark Policy,
   <https://www.mozilla.org/en-US/foundation/trademarks/policy/>) **không cho phép** phân phối lại
   bản ĐÃ SỬA ĐỔI của Firefox/Thunderbird mà gỡ bỏ tên "Firefox"/"Thunderbird" — nhãn NaMiOS **PHẢI
   giữ** từ nhãn hiệu gốc trong `Name=` hiển thị. → `NaMiBrowser (Firefox)` / `NaMiMail (Thunderbird)`
   (đổi từ `NaMiWeb (Firefox)` ngày 10/11/2026 cho khớp tên danh mục chính thức — chỉ đổi tiền tố
   NaMi, không đổi gì về căn cứ nhãn hiệu Mozilla), **KHÔNG** có biến thể "NaMiBrowser" trần không
   kèm "(Firefox)".
4. **KDE/GNOME/FOSS khác là GPL/LGPL/MPL — giấy phép CHO PHÉP sửa tên hiển thị của bản phân phối
   lại**, miễn **giữ thông báo bản quyền/giấy phép gốc trong mã nguồn** (NaMiOS không sửa mã
   nguồn nên không phát sinh nghĩa vụ này) và **không nhận vơ là bản chính thức**. Đây là cơ sở
   cho nhãn `NaMiXxx` của Dolphin/Kate/Gwenview (NaMiImages)/Ark (NaMiArchive)/Spectacle/KCalc/
   Konsole/Discover/Okular/Print Manager/system-config-printer/simple-scan/skanlite/blueman/
   fcitx5-config-qt (NaMiType)/VLC (NaMiMedia, GPL-2.0+).
5. **Dịch vụ web bên thứ ba (Facebook/Zalo/TikTok/YouTube) KHÔNG đổi nhãn.** Đây là shortcut mở
   trình duyệt tới dịch vụ của Meta/VNG/ByteDance/Google — NaMiOS không phân phối lại phần mềm của
   các hãng này, chỉ tạo liên kết, nên **không có cơ sở pháp lý nào để NaMiOS tự gắn thương hiệu
   "NaMi" lên dịch vụ không thuộc mình**. Gắn "NaMi" vào đây sẽ là hành vi **gây nhầm lẫn nguồn gốc
   dịch vụ** — vi phạm đúng thứ nguyên tắc Cuong yêu cầu tránh. File `.desktop` giữ tên dịch vụ gốc
   trong `Name=` (file vật lý có tiền tố `namios-` chỉ là tên file nội bộ, không phải nhãn hiển thị).

---

## 1. Bảng đối chiếu — app ĐÃ đổi nhãn "NaMi"

| App | Gói (Debian) | Giấy phép | Chủ nhãn hiệu/bản quyền | Nhãn NaMi | Có giữ tên gốc? | Căn cứ được phép đổi nhãn |
|---|---|---|---|---|---|---|
| Mozilla Firefox ESR | `firefox-esr` | MPL-2.0 (mã nguồn) | **Mozilla Foundation** (nhãn hiệu "Firefox") | `NaMiBrowser (Firefox)` (đổi từ `NaMiWeb (Firefox)` 10/11/2026) | **Có** — chữ "Firefox" giữ trong `Name=` (bắt buộc theo chính sách nhãn hiệu Mozilla) | MPL cho sửa mã nguồn, nhưng **nhãn hiệu "Firefox" tách biệt** — chính sách Mozilla yêu cầu bản sửa đổi vẫn ghi rõ dựa trên Firefox, không gỡ tên. Hook `0454` chỉ đổi `Name=`/`Name[vi]=`, không đụng icon/mã nguồn → không phải "bản build lại" cần đổi tên hoàn toàn. Đã tải thật `.deb` firefox-esr trixie, xác nhận file `.desktop` thật là `firefox-esr.desktop`. |
| Mozilla Thunderbird | `thunderbird` | MPL-2.0 | **Mozilla Foundation** (nhãn hiệu "Thunderbird") | `NaMiMail (Thunderbird)` | **Có** — giữ "Thunderbird" trong `Name=` | Cùng lý do Firefox ở trên. Đã áp từ hook `0452-namimail-brand.hook.chroot` (trước đợt này, giữ nguyên). |
| LibreOffice Writer | `libreoffice` | MPL-2.0 / LGPL-3.0+ | **The Document Foundation (TDF)** | `nWord` (đổi từ `NaMiWriter` 11/11/2026 — xem §1c dưới) | Không trong `Name=` hiển thị chính (nhãn thuần Việt ở `Name[vi]=`); **có** trong Comment/README đi kèm ("dựa trên LibreOffice") | Chính sách nhãn hiệu TDF **yêu cầu** bản phân phối lại đã sửa đổi phải **đổi tên** (không tiếp tục gọi "LibreOffice") — đây là nghĩa vụ, không chỉ là quyền. Giữ tín dụng "dựa trên LibreOffice (TDF)" ở splash/About/docs (`docs/branding/NAMIOFFICE.md`). **LƯU Ý:** căn cứ này chỉ xác nhận được phép/bắt buộc RỜI tên "LibreOffice" — KHÔNG xác nhận tên mới "nWord" không gợi nhãn hiệu bên thứ ba khác (Microsoft); xem §1c. |
| LibreOffice Calc | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `nExcel` (đổi từ `NaMiSheet` 11/11/2026) | như trên | như trên — xem §1c |
| LibreOffice Impress | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `nPowerPoint` (đổi từ `NaMiSlides` 11/11/2026) | như trên | như trên — xem §1c |
| LibreOffice Draw | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `nDraw` (đổi từ `NaMiDraw` 11/11/2026) | như trên | như trên — xem §1c |
| LibreOffice Start Center | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `nOffice` (đổi từ `NaMiOffice` 11/11/2026; MỚI thêm dòng — trước đợt này bảng chưa liệt kê riêng Start Center) | như trên | như trên — xem §1c |
| LibreOffice Base | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `NaMiData` (KHÔNG đổi — ngoài phạm vi yêu cầu 11/11/2026) | như trên | như trên |
| LibreOffice Math | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `NaMiMath` (KHÔNG đổi — ngoài phạm vi yêu cầu 11/11/2026) | như trên | như trên |
| Okular | `okular` | GPL-2.0+ / KDE FreeBSD | **KDE e.V.** (nhãn hiệu "KDE") + tác giả Okular | `NaMiPDF (Okular)` | **Có** — giữ "Okular" trong `Name=` | GPL cho phép đổi tên bản phân phối lại; giữ "Okular" + `Comment[vi]` ghi "dựa trên Okular" để không nhận vơ, không yêu cầu bắt buộc như Mozilla nhưng NaMiOS **chọn giữ** để minh bạch. Áp từ hook `0453`, giữ nguyên. |
| Dolphin | `dolphin` | GPL-2.0+ | KDE e.V. + tác giả Dolphin | `NaMiFiles` | Không trong `Name=` (thuần nhãn NaMi); **có** trong `Comment[vi]=` ("dựa trên Dolphin (KDE)") | GPL cho phép đổi tên hiển thị bản phân phối lại, miễn không tuyên bố là bản KDE chính thức/được KDE e.V. chứng nhận. `Comment[vi]` giữ tín dụng + không đụng `Exec=`/`Icon=`. Áp từ hook `0454` (đợt này). |
| Kate | `kate` | LGPL-2.0+ | KDE e.V. + tác giả Kate | `NaMiText` | như Dolphin (tín dụng ở `Comment[vi]`) | như Dolphin |
| Gwenview | `gwenview` | GPL-2.0+ | KDE e.V. + tác giả Gwenview | `NaMiImages` (đổi từ `NaMiẢnh` 10/11/2026; `Name[vi]` dạng dài "NaMiImages – Xem ảnh") | như Dolphin | như Dolphin. Đã tải thật `.deb` gwenview trixie, xác nhận file `.desktop` thật là `org.kde.gwenview.desktop`. |
| Ark | `ark` | GPL-2.0+ | KDE e.V. + tác giả Ark | `NaMiArchive` (đổi từ `NaMiNén` 10/11/2026; `Comment[vi]` vẫn giữ "Quản lý nén — dựa trên Ark (KDE)") | như Dolphin | như Dolphin. Đã tải thật `.deb` ark trixie, xác nhận file `.desktop` thật là `org.kde.ark.desktop`. |
| Spectacle | `kde-spectacle` | GPL-2.0+ | KDE e.V. + tác giả Spectacle | `NaMiChụp` | như Dolphin | như Dolphin |
| KCalc | `kcalc` | GPL-2.0+ | KDE e.V. + tác giả KCalc | `NaMiTính` | như Dolphin | như Dolphin |
| Konsole | `konsole` | GPL-2.0+ | KDE e.V. + tác giả Konsole | `NaMiDòng lệnh` | như Dolphin | như Dolphin |
| Plasma Discover | `plasma-discover` | GPL-2.0+ / LGPL-2.0+ | KDE e.V. + tác giả Discover | `NaMiCửa hàng` | như Dolphin | như Dolphin |
| Print Manager (KDE) | `print-manager` | GPL-2.0+ / LGPL-2.0+ / BSD-3-Clause | KDE e.V. + tác giả print-manager | `NaMiMáy in` | như Dolphin | như Dolphin. **Lưu ý riêng:** id file `.desktop` của "Thêm máy in"/"Hàng đợi in" đã đổi theo version upstream (cũ ↔ `org.kde.plasma.printqueue`/`org.kde.ConfigurePrinter` hiện tại) — hook `0454` dò nhiều id khả dĩ, **chưa xác nhận** id nào thật có trong snapshot trixie đóng gói (`verified_on_host: NO`). |
| system-config-printer | `system-config-printer` | GPL-2.0+ | OpenPrinting / cộng đồng system-config-printer | `NaMiMáy in (nâng cao)` | Không trong `Name=`; **có** trong `Comment[vi]=` ("dựa trên System Config Printer") | GPL cho phép đổi tên hiển thị bản phân phối lại, cùng nguyên tắc như KDE ở trên (độc lập desktop, không phải KDE nhưng cùng họ giấy phép). |
| Simple Scan | `simple-scan` | LGPL-2.1+ | GNOME Foundation + tác giả Simple Scan | `NaMiQuét` | Không trong `Name=`; **có** trong `Comment[vi]=` ("dựa trên Simple Scan") | LGPL cho phép đổi tên hiển thị bản phân phối lại. |
| Skanlite | `skanlite` | GPL-2.0+ | KDE e.V. + tác giả Skanlite | `NaMiQuét (Skanlite)` | **Có** — giữ "Skanlite" trong `Name=` để phân biệt với Simple Scan (hai công cụ quét song song) | GPL cho phép đổi tên; NaMiOS **chọn giữ** "(Skanlite)" để không gây nhầm hai app quét cùng tên "NaMiQuét". |
| Blueman | `blueman` | GPL-3.0+ | blueman-project + tác giả Blueman | `NaMiBluetooth` | Không trong `Name=`; **có** trong `Comment[vi]=` ("dựa trên Blueman") | GPL cho phép đổi tên hiển thị bản phân phối lại. |
| fcitx5-config-qt (MỚI 10/11/2026) | `fcitx5-config-qt` | LGPL-2.1+ | fcitx project (GitHub `fcitx/fcitx5-configtool`) + cộng đồng fcitx5 | `NaMiType` | Không trong `Name=`; **có** trong `Comment[vi]=` ("dựa trên fcitx5 + Unikey") | LGPL cho phép đổi tên hiển thị bản phân phối lại, cùng nguyên tắc KDE/FOSS ở trên. **Lưu ý riêng:** đã tải thật `.deb` `fcitx5-config-qt_5.1.8-1` (trixie) và `dpkg-deb -c` — file `.desktop` thật là `org.fcitx.fcitx5-config-qt.desktop` (KHÔNG phải `fcitx5-config-qt.desktop`), và có `NoDisplay=true` trong bản gốc → ẨN khỏi menu Bắt đầu theo mặc định dù đã đổi nhãn (không đụng `NoDisplay=`, đúng nguyên tắc "chỉ đổi nhãn"). Cần Cuong quyết định UX có bật hiển thị hay không. |
| Security Center (MỚI 10/11/2026) | tiện ích riêng NaMiOS (`/usr/local/bin/namios-security-center`, tạo bởi hook `0630-security-default.hook.chroot`) | Không áp dụng (mã do NaMiOS tự viết, không fork app bên thứ ba) | **NaMiOS** | `NaMiSecurity` | Không áp dụng — không có "tên gốc" cần giữ vì không phải rebrand | Không phải vấn đề bản quyền/nhãn hiệu — đây là script+`.desktop` do NaMiOS tự viết (wrap `kdialog`/`zenity` đọc trạng thái `ufw`/AppArmor/ClamAV). Nhãn `NaMiSecurity` được set trực tiếp tại nơi tạo file (hook `0630`), KHÔNG qua hook `0454`, vì `0454` chạy trước khi file này tồn tại (xem mục 1b ở trên). |
| VLC media player (MỚI 10/11/2026 — NaMiMedia) | `vlc` | GPL-2.0+ (lõi VLC; một số module LGPL/MPL) | **VideoLAN** (tổ chức phi lợi nhuận Pháp) + tác giả VLC | `NaMiMedia` | **Có** — tên gốc không giữ trong `Name=` (khác Firefox: VideoLAN không có chính sách nhãn hiệu bắt buộc giữ "VLC" khi phân phối lại bản sửa nhãn hiển thị); **có** tín dụng "dựa trên VLC media player (VideoLAN)" trong `Comment[vi]=` | GPL cho phép đổi tên hiển thị bản phân phối lại, cùng nguyên tắc KDE/FOSS ở trên — KHÔNG build lại mã nguồn, không đụng `Exec=`/`Icon=`/`MimeType=`. Đã tải thật `.deb` `vlc_3.0.24-0+deb13u1` (trixie) và `dpkg-deb -c` xác nhận file `.desktop` thật là `vlc.desktop` (Name gốc "VLC media player"). Hook `0455-namimedia-brand.hook.chroot` cũng dò thêm `org.kde.haruna.desktop`/`org.kde.elisa.desktop` phòng hờ đổi lựa chọn player sau này — KHÔNG có nghĩa hai gói đó được cài (xem `package-lists/0430-media.list.chroot`, chỉ cài `vlc`). |

---

## 2. App KHÔNG đổi nhãn (giữ nguyên tên gốc — bắt buộc)

| Mục | File `.desktop` | Vì sao KHÔNG gắn "NaMi" |
|---|---|---|
| Facebook (shortcut web) | `namios-facebook.desktop` | Dịch vụ của **Meta** — NaMiOS không phân phối lại phần mềm Facebook, chỉ mở trình duyệt tới URL chính thức. Gắn "NaMi" sẽ ngụ ý NaMiOS sở hữu/vận hành dịch vụ này — SAI và có thể vi phạm nhãn hiệu Meta. `Name=` giữ "Facebook (Dịch vụ web)". |
| Zalo Web (shortcut web) | `namios-zalo-web.desktop` | Dịch vụ của **VNG/Zalo** — cùng lý do trên. `Name=` giữ "Zalo Web (Dịch vụ web)". |
| TikTok (shortcut web) | `namios-tiktok.desktop` | Dịch vụ của **ByteDance/TikTok** — cùng lý do trên. `Name=` giữ "TikTok (Dịch vụ web)". |
| YouTube (shortcut web) | `namios-youtube.desktop` | Dịch vụ của **Google/YouTube** — cùng lý do trên. `Name=` giữ "YouTube (Dịch vụ web)". |

Tiền tố `namios-` trong **tên file** ở trên chỉ là quy ước đặt tên file nội bộ của NaMiOS (để dễ
quản lý trong `includes.chroot`) — **không** phải nhãn hiển thị trong menu, và **không** được coi
là "đã gắn thương hiệu NaMi" theo nghĩa yêu cầu của Cuong (yêu cầu là nhãn **hiển thị** trong menu,
field `Name=`/`Name[vi]=`).

---

## 3. Kết luận

Toàn bộ thay đổi trong tài liệu này là **rebrand mức nhãn hiển thị** (`Name=`/`Name[vi]=`/
`Comment[vi]=` trong file `.desktop`), được cho phép bởi giấy phép FOSS (GPL/LGPL/MPL) của từng
app — không app nào bị build lại, không `Exec=`/`Icon=`/mã nguồn nào bị đổi, và không nơi nào
tuyên bố được tác giả gốc/tổ chức chủ quản (KDE e.V., Mozilla Foundation, GNOME Foundation, The
Document Foundation, OpenPrinting, blueman-project, VideoLAN, fcitx project) chứng nhận hay phát
hành bản NaMiOS này.
Nhãn hiệu **Mozilla** ("Firefox"/"Thunderbird") được **giữ nguyên trong `Name=`** theo đúng yêu
cầu bắt buộc của chính sách nhãn hiệu Mozilla — đây là ngoại lệ duy nhất không dùng thuần nhãn
"NaMiXxx" mà phải ghép dạng `NaMiXxx (Tên gốc)`. Các dịch vụ web bên thứ ba (Facebook/Zalo/TikTok/
YouTube) **không** nằm trong phạm vi rebrand vì NaMiOS không phân phối lại phần mềm của các hãng
đó — gắn "NaMi" vào đó mới là hành vi có rủi ro nhãn hiệu, nên được loại trừ có chủ đích.

**Riêng NaMiMedia (VLC) có ghi chú bản quyền KHÁC loại** — không phải vấn đề nhãn hiệu mà là vấn đề
**bằng sáng chế** của một gói codec đi kèm (`gstreamer1.0-plugins-ugly`, cài cùng package-lists/
`0430-media.list.chroot`) — xem mục 1a ở đầu file này, CẦN rà soát trước khi phát hành thương mại
Việt Nam.

**`verified_on_host: NO`** cho toàn bộ bảng — tên file `.desktop` thật trên ảnh KDE trixie đã build
cần xác nhận lại (đặc biệt dòng Print Manager, xem cột "Căn cứ" + comment hook `0454`); không ảnh
hưởng tới kết luận bản quyền/nhãn hiệu ở trên (kết luận dựa trên GIẤY PHÉP của từng gói, không phụ
thuộc tên file cụ thể). Ngoại lệ: dòng Firefox/Ark/Gwenview/fcitx5-config-qt/VLC đã được xác nhận
**mạnh hơn** mức "verified_on_host: NO" thường lệ — đã tải THẬT `.deb` từng gói từ `ftp.debian.org`
(nhánh trixie) và chạy `dpkg-deb -c`/`-x` để đọc tên file `.desktop` thật bên trong gói (đối chiếu
2026-11-10), không chỉ đoán theo quy ước tên. Vẫn CẦN `apt-cache show` + boot ISO thật trước khi
phát hành, theo đúng quy ước repo.

## 4. Nguồn

- Mozilla Trademark Policy: <https://www.mozilla.org/en-US/foundation/trademarks/policy/>
- KDE e.V. trademark: <https://kde.org/trademarks/>
- `docs/l10n/DESKTOP-NAMES-OVERLAY-SPEC.md` — đối chiếu id `.desktop` KDE Gear thật đã soi mã nguồn.
- `docs/branding/NAMIOFFICE.md`, `docs/branding/NAMIOFFICE-APPS.md` — chi tiết rebrand LibreOffice.
- VideoLAN (VLC) trademark/licensing: <https://www.videolan.org/legal.html> (GPL-2.0+, không có
  chính sách nhãn hiệu bắt buộc giữ tên "VLC" khi phân phối lại bản sửa nhãn hiển thị như Mozilla).
- Hook áp dụng: `distro/live-build/config/hooks/normal/0450-namioffice-brand.hook.chroot`,
  `0452-namimail-brand.hook.chroot`, `0453-namipdf-brand.hook.chroot`,
  `0454-namios-apps-rebrand.hook.chroot`, `0455-namimedia-brand.hook.chroot` (MỚI),
  `0630-security-default.hook.chroot` (set nhãn NaMiSecurity trực tiếp lúc tạo file, mục (d)).
- Package list NaMiMedia: `distro/live-build/config/package-lists/0430-media.list.chroot` (MỚI).
