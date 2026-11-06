# NaMiOS — Đặc tả lớp phủ dịch tiếng Việt (Upstream VI + NaMiOS Overlay)

> Phạm vi: desktop KDE Plasma trên nền Debian 13 "trixie". Mục tiêu: giao diện
> hiển thị tiếng Việt càng đầy đủ càng tốt bằng cách **(a) cài hết gói dịch vi
> upstream có trong trixie** + **(b) ship một lớp phủ `.mo` riêng của NaMiOS để
> GHI ĐÈ và LẤP các chuỗi upstream chưa dịch** (đang rơi về tiếng Anh).
>
> Trạng thái xác minh: các con số + tên gói dưới đây lấy từ `packages.debian.org/trixie`,
> `l10n.kde.org` và tài liệu GNU gettext / KDE ki18n, đã dẫn URL. Chỗ nào CHƯA
> xác minh được thì ghi rõ **"cần xác minh khi build"** — tuyệt đối không coi là
> đã chắc. Số liệu l10n.kde.org là ảnh chụp tại thời điểm soạn (2026-11-06), độ
> phủ cộng đồng thay đổi theo thời gian → đo lại bằng công cụ ở §6 khi build.

---

## 0. Tóm tắt điều hành (đọc cái này trước)

1. **Nền tảng dịch KDE đã đổi mô hình.** Gói `kde-l10n-*` kiểu cũ (một gói dịch
   mỗi ngôn ngữ) ĐÃ KHAI TỬ; tiếng Việt (`vi`) từng bị gỡ khỏi `kde-l10n` vì
   không còn phân phối upstream. KDE hiện ĐÓNG GÓI bản dịch **bên trong chính gói
   ứng dụng / gói `-data`** của nó (vd `plasma-workspace-data`), dưới layout
   gettext chuẩn `/usr/share/locale/vi/LC_MESSAGES/<domain>.mo`. → **Không có gói
   "kde-l10n-vi" nào để cài thêm**; độ phủ KDE = đúng những gì upstream đã nhét
   vào từng gói app.
2. **`task-vietnamese-kde-desktop` gần như rỗng** (chỉ `Depends: tasksel`) đúng vì
   bản dịch KDE đi kèm app rồi. Gói tiếng Việt thật có ích để cài là
   `task-vietnamese-desktop` (nó `Recommends` LibreOffice/Firefox/hunspell vi).
3. **`task-vietnamese` (không hậu tố) KHÔNG tồn tại trong trixie** — danh sách gói
   hiện tại của repo (`0210-l10n-vi.list.chroot`) đang ghi `task-vietnamese` →
   `lb build` sẽ báo "unable to locate package". Cần đổi thành
   `task-vietnamese-desktop`. (Xem §5.1 — chỉ ghi chú, KHÔNG sửa trong spec này.)
4. **Độ phủ thật rất lệch.** Vỏ desktop chính khá ổn (plasma-workspace 68%, kwin
   63%, dolphin 61%, kate 78%) nhưng rất nhiều applet/ứng dụng người dùng gặp
   hàng ngày là **0%**: plasma-nm (mạng), plasma-pa (âm thanh), kscreen (màn hình),
   kscreenlocker (màn khoá), spectacle (chụp màn hình), ark (nén), discover 5%,
   konsole 6%. Đây là danh sách việc dịch ưu tiên (§7).
5. **Cơ chế lớp phủ đề xuất (chính):** một *locale phủ riêng* `vi_NM` + đặt
   `LANGUAGE=vi_NM:vi:en_US`. gettext **và** ki18n đều tra cứu theo thứ tự ưu tiên
   trong `LANGUAGE` *theo từng chuỗi* (per-message fallback). Chuỗi nào NaMiOS dịch
   → thắng; chưa dịch → rơi xuống `vi` upstream; vẫn chưa có → tiếng Anh. **Không
   đụng file upstream, không dpkg-divert, không vá glibc, không build lại gói.**
   Phương án thay thế (in-place merge / dpkg-divert) ở §4.

---

## 1. Bản đồ nguồn dịch upstream cho desktop trixie + KDE Plasma

### 1.1 KDE Plasma / ứng dụng KDE

- **Mô hình đóng gói:** từ KDE Frameworks 5 trở đi, mỗi ứng dụng/thành phần
  Plasma tự mang catalog dịch của mình; `kde-l10n-*` đã bị khai tử (vi bị gỡ vì
  "no longer distributed upstream").
  - Nguồn: Debian `kde-l10n` changelog — <https://launchpad.net/debian/+source/kde-l10n/+changelog>
  - Nguồn (xác nhận mô hình "mỗi gói Plasma tự mang bản dịch"): <https://wiki.ubuntu.com/Translations/Upstream/KDE/KubuntuTranslationsLifecycle>
- **Vị trí file `.mo` trong hệ thống:** `/usr/share/locale/vi/LC_MESSAGES/<domain>.mo`
  (layout gettext chuẩn). Thí dụ `plasma-workspace-data` nhét các domain Plasma
  (`plasma_engine_*`, `plasmashell`, …) vào `/usr/share/locale/*/LC_MESSAGES/`.
  - Nguồn (gói + layout): <https://packages.debian.org/trixie/i386/plasma-workspace>
  - **cần xác minh khi build:** chạy `dpkg -L plasma-workspace-data | grep '/vi/LC_MESSAGES'`
    (và tương tự cho dolphin, kwin, systemsettings, konsole…) để biết domain nào
    THỰC SỰ có `vi.mo` trong snapshot trixie đang dùng.
- **Cơ chế nạp của KDE (ki18n / `KLocalizedString` / `KCatalog`):** tìm file dịch
  bằng `QStandardPaths::locate(QStandardPaths::GenericDataLocation, "locale/<lang>/LC_MESSAGES/<domain>.mo")`
  rồi gọi `bindtextdomain(domain, <thư-mục-tìm-thấy-ĐẦU-TIÊN>)`. Nghĩa là ki18n
  dò theo **thứ tự `XDG_DATA_DIRS`** và dùng thư mục khớp đầu tiên → có thể chèn
  một data-dir ưu tiên cao hơn để ghi đè cho app Qt/KDE (xem §4.4).
  - Nguồn (mã nguồn `KCatalog::catalogLocaleDir`): <https://codebrowser.dev/kde/ki18n/src/i18n/kcatalog.cpp.html>
  - ki18n gom danh sách ngôn ngữ "cùng thứ tự ưu tiên như gettext(3)" từ `LANGUAGE`:
    <https://codebrowser.dev/kde/ki18n/src/i18n/klocalizedstring.h.html>

### 1.2 Thư viện Qt (không phải gettext)

- Chuỗi của chính Qt (nút hộp thoại chuẩn, context menu Qt…) nằm trong file
  `.qm` (QTranslator), **không** phải `.mo` gettext → lớp phủ gettext ở §4 KHÔNG
  chạm tới được. Dịch Qt vi đến từ gói riêng:
  - `qt6-translations-l10n` (Qt6 — stack của Plasma 6) — có trong trixie, cung cấp
    `qtbase_vi.qm`, `qt_vi.qm`…; `qttranslations5-l10n` (Qt5) cũng có.
    Nguồn: <https://packages.debian.org/sid/qttranslations5-l10n>, <https://packages.debian.org/bookworm/all/qt6-translations-l10n>
    (**cần xác minh khi build** phiên bản + có `*_vi.qm` thật trong trixie không,
    và độ phủ vi của Qt — thường thấp.)

### 1.3 LibreOffice

- `libreoffice-l10n-vi` — **có trong trixie**, phiên bản `4:25.2.3-2+deb13u8`
  ("office productivity suite -- Vietnamese language package").
  Nguồn: <https://packages.debian.org/trixie/libreoffice-l10n-vi>
- LibreOffice dùng hệ dịch RIÊNG của nó (không qua gettext hệ thống cho UI) → lớp
  phủ `.mo` ở §4 không áp cho UI LibreOffice; dựa vào gói này + độ phủ upstream.

### 1.4 GTK / GNOME (chỉ nếu có mặt trên ảnh)

- NaMiOS mặc định KDE; nếu cài lẫn vài app GTK, chúng dùng gettext chuẩn như KDE
  (`/usr/share/locale/vi/LC_MESSAGES/<domain>.mo`) → **lớp phủ `vi_NM` ở §4 áp
  được cho app GTK/gettext y như KDE** (vì thuần gettext). Bản dịch vi GNOME đi
  kèm từng gói app (không có langpack tách riêng trong Debian).

### 1.5 Phần Debian "ruột" (debconf, apt, dpkg, trình cài…)

- Độ phủ dịch PO tiếng Việt của Debian: **449.135 / 1.237.681 chuỗi (~36%)**.
  Nguồn: <https://www.debian.org/international/l10n/po/vi>
- Những phần này cũng theo layout gettext → lớp phủ `vi_NM` áp được nếu muốn lấp.

---

## 2. Độ phủ tiếng Việt THẬT (ảnh chụp l10n.kde.org, 2026-11-06)

Nguồn gốc: trang thống kê team **vi**, nhánh **stable-kf6**, GUI messages:
<https://l10n.kde.org/stats/gui/stable-kf6/team/vi/> (trang team:
<https://l10n.kde.org/team-infos.php?teamcode=vi>).

> **Lưu ý tối quan trọng về "fuzzy":** `msgfmt` khi biên dịch `.po → .mo` **loại
> bỏ** các mục `fuzzy` (trừ khi `--use-fuzzy`). Nghĩa là **độ phủ hiệu dụng lúc
> chạy = cột "translated" (%) , KHÔNG tính fuzzy.** Vì vậy phần fuzzy vừa là
> "nợ" vừa là "mỏ vàng": chỉ cần rà soát/bỏ cờ fuzzy là lên dịch được ngay.

### 2.1 Tổng thể KDE (stable-kf6, GUI)

| Chỉ số | Số lượng | % |
|---|---|---|
| Translated (hiệu dụng) | 14.390 | 9,04% |
| Fuzzy (không nạp lúc chạy) | 12.170 | 7,65% |
| Untranslated | 132.599 | 83,31% |
| **Tổng** | **159.159** | 100% |

> Để tham chiếu: KF5 trunk ~ 10.004 translated (7%) / 11.309 fuzzy / 112.829
> untranslated — <https://l10n.kde.org/team-infos.php?teamcode=vi>.

### 2.2 Theo thành phần desktop chính (stable-kf6, GUI)

| Domain / module | Translated | % dịch | Fuzzy | Untranslated | Tổng | Đánh giá |
|---|---:|---:|---:|---:|---:|---|
| plasma-workspace | 1.821 | **68%** | 306 | 548 | 2.675 | Tốt |
| kwin | 914 | **63%** | 256 | 278 | 1.448 | Tốt |
| dolphin | 639 | **61%** | 214 | 182 | 1.035 | Tốt |
| systemsettings (vỏ) | 55 | 67% | 9 | 18 | 82 | Vỏ nhỏ; KCM nằm ở chỗ khác |
| kinfocenter | 201 | 69% | 42 | 46 | 289 | Tốt |
| kate | 1.766 | **78%** | 185 | 286 | 2.237 | Rất tốt |
| kio-extras | 248 | 77% | 33 | 41 | 322 | Tốt |
| plasma-desktop | 615 | 30% | **811** | 566 | 1.992 | Yếu + nhiều fuzzy |
| okular | 640 | 45% | 56 | 715 | 1.411 | Trung bình |
| konsole | 69 | **6%** | 365 | 589 | 1.023 | Yếu (nhiều fuzzy) |
| plasma-discover | 45 | **5%** | 171 | 593 | 809 | Yếu |
| plasma-nm (mạng) | 0 | **0%** | 0 | 1.893 | 1.893 | Trống hoàn toàn |
| plasma-pa (âm thanh) | 0 | **0%** | 0 | 164 | 164 | Trống |
| kscreen (màn hình) | 0 | **0%** | 0 | 152 | 152 | Trống |
| kscreenlocker (khoá) | 0 | **0%** | 0 | 75 | 75 | Trống |
| plasma-systemmonitor | 0 | **0%** | 0 | 278 | 278 | Trống |
| spectacle (chụp MH) | 0 | **0%** | 0 | 433 | 433 | Trống |
| ark (nén) | 4 | **0%** | 0 | 398 | 402 | Trống |
| kcalc | 2 | **0%** | 0 | 409 | 411 | Trống |
| gwenview | 3 | **0%** | 3 | 469 | 475 | Trống |

> `kio` (lõi) không hiện thành module riêng trong trang này; kiểm tra `kio-extras`
> và các domain con khi build. Các số trên **cần đo lại bằng công cụ §6 trên chính
> catalog `.mo` đã cài** — vì (a) Debian trixie có thể đóng băng ở một phiên bản
> KDE cụ thể, (b) thống kê web thay đổi.

---

## 3. Cơ chế gettext — nền tảng để GHI ĐÈ + LẤP mà KHÔNG build lại upstream

### 3.1 Quy tắc tra cứu gettext + `LANGUAGE`

- `LANG`/`LC_MESSAGES` đặt locale chính (vd `vi_VN.UTF-8`). `LANGUAGE` là **danh
  sách ưu tiên NGÔN NGỮ** (mã ngôn ngữ, phân tách bằng dấu `:`), gettext ưu tiên
  `LANGUAGE` hơn `LANG` cho việc chọn bản dịch.
- **Fallback theo TỪNG CHUỖI (per-message):** với mỗi `msgid`, gettext thử catalog
  của ngôn ngữ đầu trong `LANGUAGE`; nếu catalog đó **không có bản dịch cho đúng
  chuỗi ấy**, nó thử ngôn ngữ kế, … Tài liệu GNU minh hoạ bằng
  `zh_SG:zh_CN` — "zh_CN đóng vai fallback vì rất ít gói có bản dịch zh_SG"; chỉ
  hợp lý nếu fallback theo từng chuỗi. Đây cũng là hành vi glibc đã biết.
  - Nguồn: <https://www.gnu.org/software/gettext/manual/html_node/The-LANGUAGE-variable.html>
- **`LANGUAGE` bị BỎ QUA nếu locale = `C`.** Phải bật locale trước (đặt `LANG`
  hoặc `LC_ALL` khác `C`) — NaMiOS đã làm (hook `0100-locale-vi` đặt
  `vi_VN.UTF-8`). (cùng nguồn trên)
- Một domain được `bindtextdomain(domain, dir)` buộc vào **đúng một thư mục**;
  gettext KHÔNG trộn hai `.mo` cùng domain trong hai thư mục khác nhau. Muốn "xếp
  lớp" phải dùng **nhiều mã ngôn ngữ trong `LANGUAGE`** (per-message fallback) HOẶC
  trộn sẵn thành một `.mo` (§4.2).

### 3.2 Tiền lệ Ubuntu "language-pack" (vì sao tham khảo, vì sao NaMiOS không chép y)

- Ubuntu tách bản dịch khỏi gói app, ship `.mo` trong **`/usr/share/locale-langpack/`**
  (không phải `/usr/share/locale/`) để tránh đụng file. **libc của Ubuntu được VÁ**
  để, khi không thấy `.mo` ở `locale/`, dò tiếp ở `locale-langpack/`; bản langpack
  được ưu tiên → cho phép langpack ghi đè bản trong gói.
  - Nguồn: <https://wiki.ubuntu.com/Translations/TranslationLifecycle>,
    <https://wiki.ubuntu.com/UbuntuDevelopment/Internationalisation/InternationalizationPrimer/Gettext>
- **NaMiOS dùng glibc Debian tiêu chuẩn (không vá)** → *không có* đường
  `locale-langpack` ma thuật. Vì vậy NaMiOS **không** đi theo mô hình langpack;
  thay vào đó dùng `vi_NM` + `LANGUAGE` (§4.1, thuần cơ chế gettext chuẩn, không
  cần vá libc), hoặc trộn/ghi đè in-place (§4.2), hoặc `dpkg-divert` (§4.3).

---

## 4. Các cơ chế lớp phủ — đặc tả chi tiết

### 4.1 PHƯƠNG ÁN CHÍNH — locale phủ riêng `vi_NM` + `LANGUAGE` (không phá, không divert)

**Ý tưởng:** tạo một "ngôn ngữ" giả `vi_NM` chỉ chứa chuỗi NaMiOS tự dịch/ghi đè,
đặt nó đứng TRƯỚC `vi` trong `LANGUAGE`.

- Cài overlay tại **`/usr/share/locale/vi_NM/LC_MESSAGES/<domain>.mo`** — đây là
  **đường dẫn MỚI**, không gói Debian nào sở hữu → **không xung đột dpkg, không
  cần divert, không cần Replaces/Breaks**.
- Đặt **`LANGUAGE=vi_NM:vi:en_US`** (hệ thống + Plasma). Per-message fallback:
  1. `vi_NM` (NaMiOS) — thắng nếu có chuỗi.
  2. `vi` (upstream trong gói app) — lấp phần NaMiOS chưa đụng.
  3. `en_US`/msgid — tiếng Anh khi cả hai đều trống (giới hạn thật, trung thực).
- **Áp cho cả gettext thuần (GTK, phần Debian) LẪN ki18n/KDE** vì cả hai đều đọc
  `LANGUAGE` và dò `locale/<lang>/LC_MESSAGES/<domain>.mo` (§1.1, §3.1). ki18n còn
  tự thu gọn `vi_NM`→`vi` nên fallback kép rất an toàn.
- **Overlay `.mo` chỉ cần chứa chuỗi của NaMiOS** (không phải bản trộn đầy đủ) →
  nhẹ, dễ bảo trì, build nhanh.
- **Không áp cho:** Qt `.qm` (§1.2) và UI LibreOffice (§1.3) — hai hệ dịch riêng.

**Thay đổi cấu hình cần (CHỈ GHI CHÚ — spec này KHÔNG sửa file):**
- Hook `distro/live-build/config/hooks/normal/0100-locale-vi.hook.chroot`:
  `LANGUAGE="vi:en_US"` → **`LANGUAGE="vi_NM:vi:en_US"`**.
- `distro/live-build/config/includes.chroot/etc/skel/.config/plasma-localerc`:
  `[Translations] LANGUAGE=vi:en_US` → **`LANGUAGE=vi_NM:vi:en_US`**.
- Cân nhắc `--bootappend-live` trong `auto/config` nếu đang truyền `LANGUAGE` lúc
  boot Live.

> **Rủi ro cần kiểm thử (ADR 0002 spike):** vài chương trình "cứng tay" tự
> `setlocale` + `textdomain` và bỏ qua `LANGUAGE`, hoặc tự ánh xạ mã ngôn ngữ lạ.
> Nếu gặp app không nhận `vi_NM`, dùng §4.2 cho riêng domain đó. **cần xác minh
> khi build** bằng công cụ §6 (chạy thử 1 app mỗi loại: Plasma shell, Dolphin,
> một app GTK).

### 4.2 PHƯƠNG ÁN THAY THẾ A — trộn + ghi đè in-place `.mo` (build-time, cho ảnh Live)

Dùng khi muốn **đồng thời vá fuzzy upstream** hoặc cho app không nghe `LANGUAGE`.
Chạy trong chroot **sau khi gói đã cài** (hook `config/hooks/normal/` của
live-build chạy ở cuối, trong chroot — Debian Live Manual, mục "Live/system
scripts (hooks)").

Lệnh cho mỗi domain (cần gói `gettext` trong chroot, hoặc làm trên build host):
```sh
# 1) Giải biên bản upstream đã cài -> .po (chỉ có chuỗi đã dịch)
msgunfmt /usr/share/locale/vi/LC_MESSAGES/<domain>.mo -o /tmp/<domain>.upstream.po

# 2) Trộn: overlay NaMiOS THẮNG trùng msgid (--use-first lấy file đầu)
msgcat --use-first overlay/<domain>.po /tmp/<domain>.upstream.po -o /tmp/<domain>.merged.po

# 3) Biên dịch lại, GHI ĐÈ đúng chỗ (msgfmt tự bỏ untranslated + fuzzy)
msgfmt --check --statistics /tmp/<domain>.merged.po \
    -o /usr/share/locale/vi/LC_MESSAGES/<domain>.mo
```
- Ưu: thắng tuyệt đối (chính là file gốc), không phụ thuộc `LANGUAGE`; vá được
  fuzzy nếu overlay chứa bản đã rà.
- Nhược: ghi đè file dpkg sở hữu (chấp nhận được trong ảnh Live/squashfs vì không
  có đường nâng cấp dpkg; KHÔNG dùng cho gói `.deb` phát qua apt).
- Nếu muốn tránh `gettext` trong ảnh cuối: build `.mo` trên **build host** rồi thả
  vào `includes.chroot/...`; nhưng bản upstream chỉ có trong chroot sau khi cài gói
  → bước trộn phải là hook chroot. Thoả hiệp: cài `gettext`, chạy hook, rồi
  `apt-get purge gettext` cuối hook.

### 4.3 PHƯƠNG ÁN THAY THẾ B — gói `.deb` NaMiOS + `dpkg-divert` (cho kênh apt)

Nếu sau này NaMiOS phát lớp phủ như **gói apt** (không chỉ ảnh Live), dùng gói
`namios-l10n-vi` với `dpkg-divert` trong `postinst`:
```sh
# postinst: chuyển file gốc sang .upstream rồi đặt bản trộn của NaMiOS vào đúng chỗ
dpkg-divert --package namios-l10n-vi --add --rename \
    --divert /usr/share/locale/vi/LC_MESSAGES/<domain>.mo.upstream \
    /usr/share/locale/vi/LC_MESSAGES/<domain>.mo
# rồi ship bản .mo trộn của NaMiOS tại đường gốc (qua chính gói namios-l10n-vi)
# prerm: dpkg-divert --rename --remove ... để hoàn nguyên khi gỡ
```
- Ưu: sống chung được với apt, hoàn nguyên sạch khi gỡ.
- Nhược: nặng (divert hàng trăm file), phải theo dõi khi upstream cập nhật; phức
  tạp hơn nhiều so với §4.1. **Chỉ dùng khi thực sự cần kênh apt.**
- `Replaces`/`Breaks` KHÔNG đủ để "cùng path" an toàn với gói khác đang sở hữu
  file → `dpkg-divert` mới là cách đúng cho đồng-path.

### 4.4 Mẹo bổ trợ (chỉ KDE/Qt) — chèn data-dir ưu tiên qua `XDG_DATA_DIRS`

Vì ki18n dò `locale/<lang>/LC_MESSAGES/<domain>.mo` theo thứ tự `XDG_DATA_DIRS`
và dùng thư mục khớp đầu tiên (§1.1), ta có thể đặt bản dịch tại
`/usr/local/share/locale/vi/LC_MESSAGES/<domain>.mo` — vì `XDG_DATA_DIRS` mặc định
= `/usr/local/share:/usr/share`, app KDE/Qt sẽ thấy bản của ta TRƯỚC. Lưu ý: cách
này **chỉ áp cho app ki18n/Qt**, không áp cho gettext thuần (vốn luôn dùng
`/usr/share/locale`), và `.mo` ở đó phải là bản **đầy đủ/đã trộn** (ki18n buộc
domain vào một thư mục duy nhất, không trộn). → Kém tổng quát hơn §4.1; chỉ ghi để
đối chiếu, **không** chọn làm cơ chế chính.

### 4.5 So sánh & lựa chọn

| Tiêu chí | §4.1 `vi_NM`+LANGUAGE | §4.2 trộn in-place | §4.3 dpkg-divert | §4.4 XDG |
|---|---|---|---|---|
| Đụng file upstream | Không | Có (ghi đè) | Có (divert) | Không |
| Cần vá glibc | Không | Không | Không | Không |
| Áp cho gettext thuần | **Có** | Có | Có | Không |
| Áp cho ki18n/KDE | **Có** | Có | Có | Có |
| Vá được fuzzy upstream | Có (nếu overlay chứa) | **Có** | Có | Có |
| Hợp kênh apt | Có | Không | **Có** | Hạn chế |
| Độ phức tạp | **Thấp** | Trung bình | Cao | Thấp |

**Khuyến nghị:** §4.1 làm cơ chế chính cho ảnh Live; giữ §4.2 cho vài domain cứng
đầu; §4.3 chỉ khi cần phát qua apt.

---

## 5. Kế hoạch triển khai cho live-build NaMiOS

### 5.1 (i) Danh sách gói dịch vi upstream — cài hết cái có trong trixie

Gói đã **xác minh có trong trixie** (dẫn URL ở §1):

| Gói | Vai trò | Xác minh |
|---|---|---|
| `task-vietnamese-desktop` | Kéo theo l10n desktop vi (Recommends: `libreoffice-l10n-vi`, `firefox-esr-l10n-vi \| firefox-l10n-vi`, `hunspell-vi`) | CÓ (3.81) |
| `task-vietnamese-kde-desktop` | Task KDE vi (gần rỗng; dịch KDE đi kèm app) | CÓ (3.81) |
| `libreoffice-l10n-vi` | UI LibreOffice tiếng Việt | CÓ (4:25.2.3-2+deb13u8) |
| `qt6-translations-l10n` | `.qm` Qt6 (stack Plasma 6) | CÓ — **xác minh có `*_vi.qm` khi build** |
| `firefox-esr-l10n-vi` | Firefox ESR vi | CÓ (qua task-vietnamese-desktop) |
| `hunspell-vi` | Từ điển chính tả vi | CÓ (qua task-vietnamese-desktop) |

**Bản dịch KDE (Plasma/Dolphin/KWin/…) KHÔNG có gói riêng** — đi kèm chính gói app
đã liệt kê ở `0100-desktop-kde.list.chroot` (`plasma-workspace-x11`, `dolphin`,
`konsole`, `kate`, `okular`, `spectacle`, `ark`, `plasma-nm`, `plasma-pa`,
`kscreen`, …). Cài các gói đó là đã có phần vi mà upstream kèm theo.

> **SỬA LỖI cần lưu (CHỈ GHI CHÚ — KHÔNG sửa trong spec này):**
> `distro/live-build/config/package-lists/0210-l10n-vi.list.chroot` đang ghi
> `task-vietnamese` — gói này **KHÔNG tồn tại** trong trixie (chỉ có hậu tố
> `-desktop` / `-kde-desktop`). Đổi `task-vietnamese` → `task-vietnamese-desktop`,
> giữ `task-vietnamese-kde-desktop`, và cân nhắc thêm `qt6-translations-l10n`.
> Lưu ý: live-build cài `Recommends` theo mặc định; nếu dự án đặt
> `--apt-recommends false` thì phải liệt kê thẳng `libreoffice-l10n-vi`,
> `firefox-esr-l10n-vi`, `hunspell-vi`. **cần xác minh khi build.**

### 5.2 (ii) Cơ chế lớp phủ NaMiOS — bố cục repo + build + cài

Bố cục đề xuất (TẠO MỚI, không đụng cái sẵn có):
```
distro/live-build/
  l10n-overlay/                         # nguồn .po overlay của NaMiOS (giữ trong git)
    vi/
      plasma-nm.po                      # mỗi domain KDE một .po, chỉ chứa chuỗi NaMiOS dịch/ghi đè
      plasma-pa.po
      kscreenlocker.po
      spectacle.po
      ...
    coverage-baseline.json              # mẫu số (tổng chuỗi/ domain) chụp từ l10n.kde.org + ngày + URL
    README.md
  config/hooks/normal/
    0120-l10n-overlay.hook.chroot       # (TẠO MỚI) build .mo overlay + đặt LANGUAGE (xem dưới)
scripts/
  build-l10n-overlay.sh                 # (TẠO MỚI) compile .po -> .mo cho vi_NM, chạy trên build host
  l10n-coverage.py                      # (TẠO MỚI) công cụ đo phủ (§6)
```

**Bước build (§4.1 — khuyến nghị, chạy trên build host, không cần gettext trong ảnh):**
```sh
# scripts/build-l10n-overlay.sh
set -euo pipefail
SRC=distro/live-build/l10n-overlay/vi
OUT=distro/live-build/config/includes.chroot/usr/share/locale/vi_NM/LC_MESSAGES
mkdir -p "$OUT"
for po in "$SRC"/*.po; do
  dom=$(basename "$po" .po)
  msgfmt --check --statistics "$po" -o "$OUT/$dom.mo"   # msgfmt tự bỏ untranslated/fuzzy
done
```
- `.mo` overlay nằm sẵn trong `includes.chroot` → live-build copy nguyên vào ảnh,
  **không cần hook, không cần gettext trong image**.
- Chỉ cần đảm bảo `LANGUAGE=vi_NM:vi:en_US` (§4.1) — đây là thay đổi ở hook
  `0100-locale-vi` + `plasma-localerc` (ghi chú §4.1).

**Ưu tiên đè đã đảm bảo thế nào:** vì overlay là **ngôn ngữ đứng trước** (`vi_NM`)
trong `LANGUAGE`, per-message fallback khiến chuỗi NaMiOS luôn thắng upstream mà
không cần sửa file gốc. Nếu một domain cần §4.2 (ghi đè in-place), dùng hook
`0120-l10n-overlay.hook.chroot` chạy sau khi cài gói:
```sh
#!/bin/bash
set -euo pipefail
# chỉ cho các domain liệt kê trong danh sách "force-inplace"
apt-get -y install --no-install-recommends gettext
while read -r dom; do
  mo=/usr/share/locale/vi/LC_MESSAGES/$dom.mo
  [ -f "$mo" ] || continue
  msgunfmt "$mo" -o /tmp/$dom.up.po
  msgcat --use-first /opt/namios-l10n/vi/$dom.po /tmp/$dom.up.po -o /tmp/$dom.m.po
  msgfmt --check /tmp/$dom.m.po -o "$mo"
done < /opt/namios-l10n/force-inplace.list
apt-get -y purge gettext && apt-get -y autoremove
```
(An toàn CLAUDE.md: không curl|bash, không tải từ xa, chỉ dùng công cụ đã cài.)

### 5.3 (iii) Thứ tự & ưu tiên

- `0100-locale-vi.hook.chroot` (sẵn có) đặt locale + `LANGUAGE`.
- `0120-l10n-overlay.hook.chroot` (mới, chỉ khi dùng §4.2) chạy **sau** khi gói cài
  xong (tên đánh số lớn hơn). Với §4.1 thuần thì **không cần hook này**.
- `vi_NM` overlay qua `includes.chroot` → live-build áp các include **sau** cài gói
  nhưng đó là đường dẫn MỚI nên không bị gói ghi đè.

---

## 6. Công cụ ĐO ĐỘ PHỦ (trung thực, không đoán)

Mục tiêu: build-time (CI) + tuỳ chọn boot-time, quét domain nào đã có vi `.mo`, bao
nhiêu % `msgstr` đã dịch — **đo trên chính catalog đã cài**, không suy đoán.

**Nguyên tắc tính %:** `.mo` chỉ chứa chuỗi đã dịch (không có mẫu số). Lấy mẫu số
(tổng chuỗi mỗi domain) từ `coverage-baseline.json` (chụp từ l10n.kde.org, kèm
ngày + URL) → honest + tái lập được. Báo cáo 3 cột: **upstream-vi**, **+overlay
(vi_NM)**, **mẫu số**.

Thuật toán (`scripts/l10n-coverage.py`, chuẩn thư viện + `msgunfmt`):
```
1. Liệt kê /usr/share/locale/vi/LC_MESSAGES/*.mo  và  .../vi_NM/LC_MESSAGES/*.mo
2. Với mỗi .mo:  n_tr = số mục có msgstr != "" (giải biên bằng `msgunfmt` rồi đếm,
   hoặc dùng `polib.mofile()` nếu có polib).
3. effective = hợp của msgid đã dịch ở vi_NM (ưu tiên) + vi (lấp) cho mỗi domain.
4. total_dom = coverage-baseline.json[domain]  (từ l10n.kde.org, có URL+ngày).
5. In bảng: domain | vi_tr | overlay_tr | effective | total | %upstream | %effective
6. In tổng + ghi JSON artifact vào build/ (hoặc docs/releases/<ver>/l10n-coverage.json).
```
- Cách nhanh không cần polib: `msgunfmt file.mo | msgfmt --statistics -o /dev/null -`
  → in "N translated messages" ra stderr; parse N. (Chỉ ra số đã dịch, đúng nhu cầu.)
- Boot-time (tuỳ chọn): cùng script, chạy một lần ở phiên Live, đổ ra
  `~/.cache/namios/l10n-coverage.txt` để Welcome Center hiển thị trung thực
  "Giao diện: X% tiếng Việt (upstream) + Y% nhờ lớp phủ NaMiOS".
- **Không báo "đã Việt hoá 100%"** — bám đúng feedback TRUNG THỰC: chỉ báo số đo
  được; chỗ English còn lại là giới hạn thật của hệ sinh thái dịch.

---

## 7. THỨ TỰ ƯU TIÊN worklist dịch overlay (dựa trên §2 + mức độ người dùng gặp)

Ưu tiên = (độ hiển thị hàng ngày) × (độ thiếu hiện tại). Mỗi mục = một `.po` trong
`distro/live-build/l10n-overlay/vi/`. Lấy msgid gốc từ `.po` đầy đủ của KDE
(l10n-vi: <https://github.com/KDE/l10n-vi>, hoặc SVN team vi ở §1.1) rồi dịch phần
trống; với domain nhiều fuzzy thì rà bỏ cờ fuzzy (mỏ vàng).

**Nhóm P0 — applet/màn luôn hiện, đang 0%:** (impact cao nhất, khối lượng nhỏ)
1. `plasma-pa` — âm thanh (164) · 0%
2. `kscreen` — màn hình (152) · 0%
3. `kscreenlocker` — màn khoá/đăng nhập (75) · 0%
4. `plasma-nm` — mạng (1.893) · 0% (khối lớn nhưng cực kỳ hay gặp)
5. `plasma-systemmonitor` — theo dõi hệ thống (278) · 0%

**Nhóm P1 — ứng dụng lõi hay dùng, đang 0–6%:**
6. `spectacle` — chụp màn hình (433) · 0%
7. `ark` — nén/giải nén (402) · 0%
8. `konsole` — terminal (1.023) · 6% + **365 fuzzy để rà nhanh**
9. `plasma-discover` — cửa hàng phần mềm (809) · 5%
10. `kcalc` (411) · `gwenview` (475) · 0%

**Nhóm P2 — vá fuzzy + lấp phần còn thiếu ở vỏ đã khá:**
11. `plasma-desktop` — 30% dịch nhưng **811 fuzzy** → rà bỏ cờ là lên mạnh
12. `okular` — 45% (715 chưa dịch)
13. Lấp nốt `plasma-workspace` (548), `kwin` (278), `dolphin` (182) cho tròn vỏ

**Nhóm P3 — nội dung RIÊNG của NaMiOS:** đã do `src/namios_i18n` kiểm soát (100%
tiếng Việt), không thuộc overlay upstream này nhưng nên để coverage tool báo chung.

> Mọi con số mẫu số ở §7 lấy từ ảnh chụp §2 (l10n.kde.org stable-kf6, 2026-11-06)
> → **đo lại bằng §6 trên snapshot trixie thực tế trước khi chốt khối lượng.**

---

## 8. Danh mục kiểm chứng (checklist "cần xác minh khi build")

- [ ] `dpkg -L plasma-workspace-data | grep /vi/` + tương tự cho mỗi gói KDE →
      domain nào THỰC có `vi.mo` trong trixie đang dùng.
- [ ] `apt-cache policy task-vietnamese-desktop task-vietnamese-kde-desktop
      libreoffice-l10n-vi qt6-translations-l10n firefox-esr-l10n-vi hunspell-vi`
      → xác nhận cài được + phiên bản.
- [ ] Qt: `qt6-translations-l10n` có `*_vi.qm` thật? độ phủ?
- [ ] Thử `LANGUAGE=vi_NM:vi:en_US` với một chuỗi overlay giả trên: Plasma shell,
      Dolphin, một app GTK → xác nhận per-message fallback chạy đúng cho cả 3.
- [ ] Chạy `scripts/l10n-coverage.py` trên chroot sau cài gói → bảng độ phủ thật.
- [ ] Xác nhận `--apt-recommends` của live-build (ảnh hưởng việc kéo l10n qua task).

---

## 9. Nguồn (URL đã dùng)

- Debian trixie packages: task-vietnamese-kde-desktop <https://packages.debian.org/trixie/task-vietnamese-kde-desktop> ·
  tìm kiếm task-vietnamese trong trixie (chỉ có `-desktop` và `-kde-desktop`) ·
  libreoffice-l10n-vi <https://packages.debian.org/trixie/libreoffice-l10n-vi> ·
  plasma-workspace <https://packages.debian.org/trixie/i386/plasma-workspace> ·
  localization section <https://packages.debian.org/stable/localization/>
- tasksel `debian/control` (Depends/Recommends của các task vi): <https://salsa.debian.org/installer-team/tasksel/-/raw/master/debian/control>
- KDE l10n team vi: <https://l10n.kde.org/team-infos.php?teamcode=vi> ·
  stats stable-kf6 GUI <https://l10n.kde.org/stats/gui/stable-kf6/team/vi/>
- kde-l10n (khai tử, vi bị gỡ): <https://launchpad.net/debian/+source/kde-l10n/+changelog>
- Mô hình dịch KDE đi kèm app: <https://wiki.ubuntu.com/Translations/Upstream/KDE/KubuntuTranslationsLifecycle>
- ki18n `KCatalog` (QStandardPaths GenericDataLocation + bindtextdomain): <https://codebrowser.dev/kde/ki18n/src/i18n/kcatalog.cpp.html> ·
  `KLocalizedString` (ưu tiên như gettext): <https://codebrowser.dev/kde/ki18n/src/i18n/klocalizedstring.h.html>
- GNU gettext — biến LANGUAGE (per-message fallback, bỏ qua khi C): <https://www.gnu.org/software/gettext/manual/html_node/The-LANGUAGE-variable.html>
- Ubuntu language-pack / locale-langpack (tiền lệ): <https://wiki.ubuntu.com/Translations/TranslationLifecycle> ·
  <https://wiki.ubuntu.com/UbuntuDevelopment/Internationalisation/InternationalizationPrimer/Gettext>
- Qt translations trixie: <https://packages.debian.org/sid/qttranslations5-l10n> ·
  <https://packages.debian.org/bookworm/all/qt6-translations-l10n>
- Debian PO vi (phần "ruột" Debian, ~36%): <https://www.debian.org/international/l10n/po/vi>
```
