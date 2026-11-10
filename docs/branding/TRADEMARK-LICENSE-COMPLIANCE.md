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
   giữ** từ nhãn hiệu gốc trong `Name=` hiển thị. → `NaMiWeb (Firefox)` / `NaMiMail (Thunderbird)`,
   **KHÔNG** có biến thể "NaMiWeb" trần không kèm "(Firefox)".
4. **KDE/GNOME/FOSS khác là GPL/LGPL/MPL — giấy phép CHO PHÉP sửa tên hiển thị của bản phân phối
   lại**, miễn **giữ thông báo bản quyền/giấy phép gốc trong mã nguồn** (NaMiOS không sửa mã
   nguồn nên không phát sinh nghĩa vụ này) và **không nhận vơ là bản chính thức**. Đây là cơ sở
   cho nhãn `NaMiXxx` của Dolphin/Kate/Gwenview/Ark/Spectacle/KCalc/Konsole/Discover/Okular/
   Print Manager/system-config-printer/simple-scan/skanlite/blueman.
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
| Mozilla Firefox ESR | `firefox-esr` | MPL-2.0 (mã nguồn) | **Mozilla Foundation** (nhãn hiệu "Firefox") | `NaMiWeb (Firefox)` | **Có** — chữ "Firefox" giữ trong `Name=` (bắt buộc theo chính sách nhãn hiệu Mozilla) | MPL cho sửa mã nguồn, nhưng **nhãn hiệu "Firefox" tách biệt** — chính sách Mozilla yêu cầu bản sửa đổi vẫn ghi rõ dựa trên Firefox, không gỡ tên. Hook `0454` chỉ đổi `Name=`/`Name[vi]=`, không đụng icon/mã nguồn → không phải "bản build lại" cần đổi tên hoàn toàn. |
| Mozilla Thunderbird | `thunderbird` | MPL-2.0 | **Mozilla Foundation** (nhãn hiệu "Thunderbird") | `NaMiMail (Thunderbird)` | **Có** — giữ "Thunderbird" trong `Name=` | Cùng lý do Firefox ở trên. Đã áp từ hook `0452-namimail-brand.hook.chroot` (trước đợt này, giữ nguyên). |
| LibreOffice Writer | `libreoffice` | MPL-2.0 / LGPL-3.0+ | **The Document Foundation (TDF)** | `NaMiWriter` | Không trong `Name=` hiển thị chính (nhãn thuần Việt); **có** trong Comment/README đi kèm ("dựa trên LibreOffice") | Chính sách nhãn hiệu TDF **yêu cầu** bản phân phối lại đã sửa đổi phải **đổi tên** (không tiếp tục gọi "LibreOffice") — đây là nghĩa vụ, không chỉ là quyền. Giữ tín dụng "dựa trên LibreOffice (TDF)" ở splash/About/docs (`docs/branding/NAMIOFFICE.md`). Áp từ hook `0450`, giữ nguyên. |
| LibreOffice Calc | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `NaMiSheet` | như trên | như trên |
| LibreOffice Impress | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `NaMiSlides` | như trên | như trên |
| LibreOffice Draw | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `NaMiDraw` | như trên | như trên |
| LibreOffice Base | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `NaMiData` | như trên | như trên |
| LibreOffice Math | `libreoffice` | MPL-2.0 / LGPL-3.0+ | TDF | `NaMiMath` | như trên | như trên |
| Okular | `okular` | GPL-2.0+ / KDE FreeBSD | **KDE e.V.** (nhãn hiệu "KDE") + tác giả Okular | `NaMiPDF (Okular)` | **Có** — giữ "Okular" trong `Name=` | GPL cho phép đổi tên bản phân phối lại; giữ "Okular" + `Comment[vi]` ghi "dựa trên Okular" để không nhận vơ, không yêu cầu bắt buộc như Mozilla nhưng NaMiOS **chọn giữ** để minh bạch. Áp từ hook `0453`, giữ nguyên. |
| Dolphin | `dolphin` | GPL-2.0+ | KDE e.V. + tác giả Dolphin | `NaMiFiles` | Không trong `Name=` (thuần nhãn NaMi); **có** trong `Comment[vi]=` ("dựa trên Dolphin (KDE)") | GPL cho phép đổi tên hiển thị bản phân phối lại, miễn không tuyên bố là bản KDE chính thức/được KDE e.V. chứng nhận. `Comment[vi]` giữ tín dụng + không đụng `Exec=`/`Icon=`. Áp từ hook `0454` (đợt này). |
| Kate | `kate` | LGPL-2.0+ | KDE e.V. + tác giả Kate | `NaMiText` | như Dolphin (tín dụng ở `Comment[vi]`) | như Dolphin |
| Gwenview | `gwenview` | GPL-2.0+ | KDE e.V. + tác giả Gwenview | `NaMiẢnh` | như Dolphin | như Dolphin |
| Ark | `ark` | GPL-2.0+ | KDE e.V. + tác giả Ark | `NaMiNén` | như Dolphin | như Dolphin |
| Spectacle | `kde-spectacle` | GPL-2.0+ | KDE e.V. + tác giả Spectacle | `NaMiChụp` | như Dolphin | như Dolphin |
| KCalc | `kcalc` | GPL-2.0+ | KDE e.V. + tác giả KCalc | `NaMiTính` | như Dolphin | như Dolphin |
| Konsole | `konsole` | GPL-2.0+ | KDE e.V. + tác giả Konsole | `NaMiDòng lệnh` | như Dolphin | như Dolphin |
| Plasma Discover | `plasma-discover` | GPL-2.0+ / LGPL-2.0+ | KDE e.V. + tác giả Discover | `NaMiCửa hàng` | như Dolphin | như Dolphin |
| Print Manager (KDE) | `print-manager` | GPL-2.0+ / LGPL-2.0+ / BSD-3-Clause | KDE e.V. + tác giả print-manager | `NaMiMáy in` | như Dolphin | như Dolphin. **Lưu ý riêng:** id file `.desktop` của "Thêm máy in"/"Hàng đợi in" đã đổi theo version upstream (cũ ↔ `org.kde.plasma.printqueue`/`org.kde.ConfigurePrinter` hiện tại) — hook `0454` dò nhiều id khả dĩ, **chưa xác nhận** id nào thật có trong snapshot trixie đóng gói (`verified_on_host: NO`). |
| system-config-printer | `system-config-printer` | GPL-2.0+ | OpenPrinting / cộng đồng system-config-printer | `NaMiMáy in (nâng cao)` | Không trong `Name=`; **có** trong `Comment[vi]=` ("dựa trên System Config Printer") | GPL cho phép đổi tên hiển thị bản phân phối lại, cùng nguyên tắc như KDE ở trên (độc lập desktop, không phải KDE nhưng cùng họ giấy phép). |
| Simple Scan | `simple-scan` | LGPL-2.1+ | GNOME Foundation + tác giả Simple Scan | `NaMiQuét` | Không trong `Name=`; **có** trong `Comment[vi]=` ("dựa trên Simple Scan") | LGPL cho phép đổi tên hiển thị bản phân phối lại. |
| Skanlite | `skanlite` | GPL-2.0+ | KDE e.V. + tác giả Skanlite | `NaMiQuét (Skanlite)` | **Có** — giữ "Skanlite" trong `Name=` để phân biệt với Simple Scan (hai công cụ quét song song) | GPL cho phép đổi tên; NaMiOS **chọn giữ** "(Skanlite)" để không gây nhầm hai app quét cùng tên "NaMiQuét". |
| Blueman | `blueman` | GPL-3.0+ | blueman-project + tác giả Blueman | `NaMiBluetooth` | Không trong `Name=`; **có** trong `Comment[vi]=` ("dựa trên Blueman") | GPL cho phép đổi tên hiển thị bản phân phối lại. |

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
Document Foundation, OpenPrinting, blueman-project) chứng nhận hay phát hành bản NaMiOS này.
Nhãn hiệu **Mozilla** ("Firefox"/"Thunderbird") được **giữ nguyên trong `Name=`** theo đúng yêu
cầu bắt buộc của chính sách nhãn hiệu Mozilla — đây là ngoại lệ duy nhất không dùng thuần nhãn
"NaMiXxx" mà phải ghép dạng `NaMiXxx (Tên gốc)`. Các dịch vụ web bên thứ ba (Facebook/Zalo/TikTok/
YouTube) **không** nằm trong phạm vi rebrand vì NaMiOS không phân phối lại phần mềm của các hãng
đó — gắn "NaMi" vào đó mới là hành vi có rủi ro nhãn hiệu, nên được loại trừ có chủ đích.

**`verified_on_host: NO`** cho toàn bộ bảng — tên file `.desktop` thật trên ảnh KDE trixie đã build
cần xác nhận lại (đặc biệt dòng Print Manager, xem cột "Căn cứ" + comment hook `0454`); không ảnh
hưởng tới kết luận bản quyền/nhãn hiệu ở trên (kết luận dựa trên GIẤY PHÉP của từng gói, không phụ
thuộc tên file cụ thể).

## 4. Nguồn

- Mozilla Trademark Policy: <https://www.mozilla.org/en-US/foundation/trademarks/policy/>
- KDE e.V. trademark: <https://kde.org/trademarks/>
- `docs/l10n/DESKTOP-NAMES-OVERLAY-SPEC.md` — đối chiếu id `.desktop` KDE Gear thật đã soi mã nguồn.
- `docs/branding/NAMIOFFICE.md`, `docs/branding/NAMIOFFICE-APPS.md` — chi tiết rebrand LibreOffice.
- Hook áp dụng: `distro/live-build/config/hooks/normal/0450-namioffice-brand.hook.chroot`,
  `0452-namimail-brand.hook.chroot`, `0453-namipdf-brand.hook.chroot`,
  `0454-namios-apps-rebrand.hook.chroot`.
