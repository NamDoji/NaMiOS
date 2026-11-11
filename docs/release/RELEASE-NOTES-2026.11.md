# RELEASE NOTES — NaMi 2026.11 "Đông Sơn" (alpha)

> **Kênh: alpha, bản thử nghiệm.** `verified_on_host: NO` cho **toàn bộ** mục dưới đây trừ khi
> ghi rõ khác — chưa có ISO nào của phiên bản này được build + boot-test thành công trên build
> host thật trong chu kỳ này. Mọi mục là thay đổi **trong mã nguồn/cấu hình repo**, không phải
> tuyên bố "đã chạy được trên máy người dùng". Đọc §KNOWN LIMITATIONS trước khi dùng cho bất kỳ
> việc gì ngoài đọc code.

## 0. Thông tin phiên bản

- Tên hiển thị: **NaMi** · Mã phiên bản: **2026.11** · Tên mã thương hiệu: **"Đông Sơn"** ·
  Kênh: **alpha**
- Nền tảng: Debian 13 "trixie" + KDE Plasma 6 (live-build + Calamares)
- Đóng dấu version: commit `ff7928d` (`os-release`/`namios-release`/`lsb-release`/
  `branding.desc` đồng bộ `2026.11 (Đông Sơn)`); `NAMIOS_BUILD_DATE_UTC`/`NAMIOS_SOURCE_COMMIT`
  vẫn là `TBD` — tự đóng dấu thật trên host lúc build ISO, **chưa có giá trị thật**.
- Tác giả/chủ dự án: Đỗ Chí Cường & Đỗ Bảo Nam (`NAMIOS_AUTHORS` — thêm 11/11/2026).

## 1. Đổi tên thương hiệu "Đông Sơn" + bảng màu navy/gold

- Tên mã bộ nhận diện đổi từ **"Sen Việt" (v2)** sang **"Đông Sơn" (v3)**: logo mark đổi từ
  hoa sen 7 cánh sang **mặt trống đồng Đông Sơn** (4 SVG master + 5 SVG mới); palette đổi từ
  đỏ-son `#C93643`/mực đêm `#122A3A` (v2) sang **navy `#092D4F` / gold `#DEA93E` / vermilion
  `#D64C3E` / teal `#278F8D` / ivory `#FFF9EF`** (`brand.json` v3.0 — DONE trong repo).
- `KColorScheme` (`NaMiOS.colors`) + mới thêm **`NaMi-HighContrast.colors`**: accent gold, chữ
  trên vùng chọn (Selection) đảo chiều sang **navy trên nền gold**; focus-ring đo lại WCAG thật
  = gold-deep `#8B6518` (5.05:1); link dùng `teal-deep`/`teal-light` để đạt AA trên nền
  sáng/tối. **35/36 cặp tương phản PASS** theo `docs/design/HIG-ADOPTION-VERDICT.md` (cặp FAIL
  duy nhất là gold/ivory 2.04:1 — **chủ đích**, chứng minh không dùng gold làm nền nút trên nền
  sáng).
- 34 ảnh raster logo cũ (SEN) được thay bằng bộ trống đồng v3 (biểu tượng nút Bắt đầu, favicon,
  `hicolor`, `NaMiOS-Lotus`) ở commit `93f200a`; **hình nền mặc định/khoá/đăng nhập**
  (`namios-default.png`) cũng đã đổi sang Đông Sơn (navy + hoạ tiết trống đồng, BỎ chữ "NaMiOS").
  SDDM/Plymouth/Calamares được tổ logo báo đã là v3 — **cần boot-test xác nhận bằng mắt** (kiểm
  tra tĩnh giữa các tổ còn mâu thuẫn) — xem §KNOWN LIMITATIONS.

## 2. Tên sản phẩm NaMi + quy ước đặt tên app

- Tên hiển thị hệ điều hành đổi từ **"NaMiOS"** sang **"NaMi"** (giữ nguyên `ID=namios` —
  trường kỹ thuật, không phải nhãn người dùng thấy) theo quyết định chủ dự án (commit
  `291a14c`).
- Quy ước đặt tên app mới: tiền tố **"n" + chức năng (Latin)** hoặc **tên thuần Việt** — KHÔNG
  còn dùng tiền tố "NaMi" cho app mới (ghi đè khuyến nghị cũ của HIG §7.1, xem
  `docs/design/HIG-ADOPTION-VERDICT.md` §1). Áp dụng: `nWord`/`nExcel`/`nPowerPoint`/`nDraw`
  (Start Center `nOffice`) thay cho `NaMiWriter`/`NaMiSheet`/`NaMiSlides`/`NaMiDraw`/
  `NaMiOffice` cũ; `nControl`, `nAssistant`, `nConnect`, `nGuide`.
- **Cảnh báo nhãn hiệu mới, CHƯA rà soát pháp lý:** `nWord`/`nExcel`/`nPowerPoint` cố ý đọc rất
  gần tên sản phẩm đã đăng ký nhãn hiệu của Microsoft (Word®/Excel®/PowerPoint®) — đây là
  **quyết định có chủ đích của chủ dự án**, không phải lỗi, nhưng **cần luật sư sở hữu trí tuệ
  rà soát trước khi phát hành công khai/thương mại** (`docs/branding/
  TRADEMARK-LICENSE-COMPLIANCE.md` §1c). Tên Việt thuần (Văn bản/Bảng tính/Trình chiếu) vẫn có
  sẵn ở `Name[vi]=` làm phương án lùi nếu cần.

## 3. Áp dụng HIG (Human Interface Guidelines) nội bộ + semantic tokens

- `docs/design/hig/NaMi-Human-Interface-2026.md` (Phụ lục 22) được khảo sát + **quyết định áp
  dụng** (`docs/design/HIG-ADOPTION-VERDICT.md`): P0 (khảo sát repo, `docs/design/
  P0-UI-AUDIT.md`) + P1 (token nền tảng) **DONE ở mức tài liệu + token**; P2–P4 (nối vào
  shell/app + boot-test + thử người dùng thật) **CHƯA làm**.
- Token ngữ nghĩa light/dark/high-contrast đo WCAG thật (`docs/design/NAMI-DESIGN-TOKENS.md` +
  `nami-tokens.json`), thuật ngữ tiếng Việt chuẩn hoá (`NAMI-GLOSSARY-VI.md`), đặc tả
  component + mẫu lỗi 5 phần (`NAMI-UI-KIT.md`).
- **Viết token/spec ≠ đã áp dụng khắp mọi app** — đây là nền tảng tài liệu, chưa phải "OS đạt
  HIG" (tự nhắc lại trong chính verdict document, không phải diễn giải thêm ở đây).

## 4. Diện mạo kiểu Windows 11

Theo `docs/design/WINDOWS11-PARITY.md` (tài liệu đặc tả) + commit `93f200a` (phần đã thực thi):

- **Taskbar căn giữa kiểu Win11:** thêm 2 applet `panelspacer` (expanding) quanh cụm Kickoff +
  Task Manager (`AppletOrder` đổi từ `2;3;4;5` sang `6;2;3;7;4;5`); systray + đồng hồ vẫn ghim
  phải. Trước đó taskbar căn trái kiểu Windows 10.
- **Nút điều khiển cửa sổ sang góc phải, thứ tự Windows:** `kwinrc [org.kde.kdecoration2]
  ButtonsOnRight=IAX` (thu nhỏ/phóng to/đóng) trên viền **Breeze mặc định** — theme viền riêng
  `NaMiOSLotus` (Aurorae) **vẫn đang TẮT** (comment trong `kwinrc`) vì nghi từng gây treo đăng
  nhập dưới QEMU/TCG (`dfbbf3c`), chưa bisect xong.
- **Panel nổi + bo góc 28px, Kickoff đầu trái, độ dày panel 36px** — đã có từ wave trước, giữ
  nguyên.
- Mica/Acrylic (KWin Blur + Background Contrast) đã **cấu hình** (`blurEnabled`/
  `contrastEnabled=true`) nhưng **compositing mặc định TẮT** trên máy không GPU/VM — chỉ bật
  khi `namios-auto-compositing.sh` phát hiện GPU thật, nên hiệu ứng kính mờ **không hiện** trên
  hầu hết môi trường thử nghiệm hiện tại (đánh đổi có chủ đích để chạy được máy yếu).
- **KHÔNG đạt 1:1** (nói rõ, không giấu): Snap Layouts flyout khi hover nút phóng to, ribbon
  Explorer, Mica "nền cửa sổ hoà sắc desktop" thật, gộp Action+Notification+Widgets 1 phím —
  xem `WINDOWS11-PARITY.md` §10 "TRUNG THỰC" cho danh sách đầy đủ điều KDE Plasma 6 không khớp
  được Windows 11.

## 5. Phím tắt kiểu Windows + desktop kiểu Windows

- Phím tắt quen thuộc Windows đã wire (wave #18230, 11/11/2026): snap cửa sổ (Meta+mũi tên),
  Overview/Task View (Meta+Tab, Meta+W), hot-corner trên-trái — xem `docs/specs/
  UX-WINDOWS-FAMILIAR.md` §2bis cho bảng chi tiết + mục **Win+. (emoji picker) KHÔNG wire**
  (lý do kỹ thuật ghi rõ trong tài liệu, không phải bỏ sót).
- Desktop kiểu Windows: 3 icon `.desktop` trên Desktop mặc định — **"Máy tính của tôi"**
  (`computer:/`), **"Tài liệu của tôi"**, **"Thùng rác"** (`trash:/`); chuột-phải desktop →
  **Refresh (F5)** hoạt động từ wave trước (`docs/.../DESKTOP-WINDOWS-LIKE.md`).
- **Chưa có:** nhóm "This PC" gom nhiều ổ đĩa trong Dolphin Places — cần sinh lúc đăng nhập đầu
  (biết `$HOME` thật), không seed tĩnh được qua `/etc/skel` (ghi path sai cho mọi user).

## 6. Plasma splash trống đồng (màn chờ)

- Màn hình chờ sau đăng nhập (trước khi desktop lên hẳn) dùng theme Plymouth/Ksplash thương
  hiệu "Đông Sơn" (trống đồng) thay bản SEN v2 cũ.
- **PNG của màn chờ này chưa được tái xuất từ SVG v3** ở một số nơi (SDDM login dùng
  `NaMiOS_Symbol_Transparent_1024.png` = **logo SEN cũ**) — xem §KNOWN LIMITATIONS.

## 7. 4 ứng dụng Việt Nam mới (wave #18230 + tiếp theo)

| App | Tên hiển thị | Chức năng |
| --- | --- | --- |
| nLịch / Lịch | "Lịch" | Âm lịch + lễ Việt Nam (`namios_lich-src`) |
| Dịch vụ VN | "Dịch vụ VN" | Danh bạ dịch vụ công trực tuyến + ký số (`namios_dichvu-src`) |
| Security Center | "NaMiSecurity" / "An toàn" | Trạng thái `ufw`/AppArmor/ClamAV (script tự viết, không rebrand app thứ ba) |
| Gói ngôn ngữ Việt | — | Lớp phủ dịch `vi_NM` (biên dịch `.po`→`.mo` ngay trong `build-release.yml`) |

Tất cả ở trạng thái **PARTIAL** theo `docs/design/P0-UI-AUDIT.md` §2.2 — có khung/code, **chưa
boot-test** để xác nhận chạy đúng trên desktop thật.

## 8. Máy chiếu / màn hình ngoài (nProjector)

- Hook `0311-namios-manchieu.hook.chroot` + app `namios_manchieu-src` (desktop
  `namios-manchieu.desktop`, "Màn chiếu"): hỗ trợ máy chiếu/màn hình ngoài + phím nhanh
  Win+P. Trạng thái **PARTIAL** (khung đã có, chưa boot-test xoay/mở rộng màn hình thật).

## 9. Add/Remove Programs

- Lối tắt tiếng Việt "**Gỡ cài đặt phần mềm**" (`namios-go-cai-dat`) trỏ thẳng vào tab **Đã
  cài** của Plasma Discover — **không phải app tự viết mới**, chỉ là shortcut dễ thấy kiểu
  Windows "Add/Remove Programs". Toàn bộ logic liệt kê/gỡ/kiểm phụ thuộc do Discover +
  PackageKit đảm nhiệm (đã có sẵn, không phải code mới của release này).
  Xem `usr/share/namios/docs/GO-CAI-DAT.md`. `verified_on_host: NO`.

## 10. Ghi nhận tác giả

- `namios-release`: thêm trường `NAMIOS_AUTHORS="Đỗ Chí Cường & Đỗ Bảo Nam"` (field additive,
  11/11/2026, yêu cầu "sản phẩm thuần của người Việt") — hiển thị tương ứng ở
  `welcome.ui.welcome.body` (`namios_i18n` locale `vi`/`en`).

---

## KNOWN LIMITATIONS / NOT YET VERIFIED

**Đọc mục này trước khi dùng ISO cho bất kỳ việc gì ngoài đọc code.**

1. **`verified_on_host: NO` toàn diện.** Không có ISO nào của 2026.11 "Đông Sơn" được build +
   boot-test thành công trong chu kỳ này. Mọi "DONE" trong release notes này là **DONE trong
   mã nguồn/cấu hình repo**, không phải "đã chạy đúng trên máy". Container soạn tài liệu/code
   hiện tại (Debian 12) không có `live-build`/`debootstrap`/`xorriso`/`/dev/kvm` — không thể tự
   build/boot ở đây kể cả khi muốn.
2. **nWine chỉ chạy MỘT SỐ phần mềm Windows, tuỳ app** (đã sửa microcopy ở commit `93f200a` để
   nói đúng mức này, không còn ngụ ý "chạy mọi app Windows"). Chưa có fixture Wine chạy thật
   trong CI (thiếu `/dev/kvm` + `wine`/`winetricks` ở host hiện tại) — mọi app Windows qua Wine
   còn `in_development`/`blocked` theo `website/data/release-manifest.json`.
3. **MISA SME + chữ ký số USB-token: BLOCKED.** Chưa có máy Windows/MISA SME/SQL Server/USB
   token thật để đo workflow kế toán tham chiếu (`docs/STATUS.md`, `docs/ROADMAP.md` mục B3).
   Ma trận hỗ trợ token mới ở mức khung/thiết kế.
4. **Rà soát nhãn hiệu: CHƯA xong**, cho cả hai lớp rủi ro khác nhau:
   - Tên "NaMi"/"NaMiOS" chưa tra cứu đăng ký bảo hộ (`docs/adr/
     0009-quyen-so-huu-va-thuong-hieu.md` — `approval_status: trademark review pending`).
   - Tên app mới `nWord`/`nExcel`/`nPowerPoint` cố ý gợi tên sản phẩm Microsoft đã đăng ký —
     **cần luật sư trước khi phát hành công khai** (`docs/branding/
     TRADEMARK-LICENSE-COMPLIANCE.md` §1c), khác loại rủi ro với mục trên (đây là trùng tên bên
     thứ ba khác, không phải "được phép đổi tên app FOSS").
5. **Viền cửa sổ Aurorae (`NaMiOSLotus`) + compositing: hoãn, chờ boot-test.** Theme viền cửa
   sổ riêng của NaMi hiện **thiết kế kiểu macOS** (nút tròn 3 màu) — nghịch với mục tiêu "cảm
   giác Windows 11" — và đang **tắt** trong `kwinrc` vì nghi gây treo đăng nhập dưới QEMU/TCG
   (`dfbbf3c`, cùng họ với treo Wayland `23d774a`/`386f89d`). Chưa bisect tách bạch nguyên nhân;
   KHÔNG bật lại cho tới khi boot-test đúng kịch bản từng treo.
6. **"Giới thiệu về KDE" (About KDE) + "KDE Store" (KNewStuff) vẫn hiện nguyên bản trong mọi
   app KDE** (Konsole/Dolphin/Kate/Ark/Gwenview/KCalc...) — các chuỗi này **baked cứng** trong
   thư viện KDE Frameworks (`libkf6xmlgui`, `KNewStuff`), không thể phủ qua `.desktop`/hook như
   các lớp đổi nhãn khác đã làm. Sửa thật cần patch Frameworks — ngoài phạm vi rebrand hiện tại.
7. **Nhận diện logo trên SDDM/Plymouth/Calamares — CẦN BOOT-TEST xác nhận bằng mắt.** Tổ logo
   đã tái xuất 34 ảnh raster v3 + đổi hình nền sang Đông Sơn; tổ logo báo 3 bề mặt này đã là v3
   từ đợt trước, nhưng kiểm tra TĨNH giữa các tổ còn mâu thuẫn (P0-UI-AUDIT từng ghi "còn SEN").
   Chỉ boot-test máy thật (nhìn màn đăng nhập/boot/cài đặt) mới chốt chắc không còn hoa sen cũ.
8. **Secure Boot: chưa hỗ trợ.** Chỉ có module GRUB EFI chưa ký (`grub-efi-amd64-bin`); thiếu
   `shim-signed`/`grub-efi-amd64-signed`. Máy bật Secure Boot sẽ không boot ISO này.
9. **Update/rollback (U19, ADR-0020): `specified`/`partial`.** Chưa có `namios-update-service`
   thật nối apt + Timeshift + GRUB trên máy nào — prototype mới chạy test ở mức thư
   mục/VM-giả-lập. Rollback hiện chỉ dùng được thủ công qua Timeshift/apt, không tự động.
10. **Khoá ký chuỗi cập nhật là khoá KIỂM THỬ (TEST-ONLY, ed25519)** — chưa có hạ tầng khoá
    production cho release-index kiểu TUF (`docs/security/UPDATE-KEY-CATALOG.md`,
    `website/data/release-manifest.json` `signing.note`).
11. **Chưa có thiết bị in/scan/Wi-Fi/Bluetooth vật lý nào được chứng nhận.** Driver đã đóng gói
    sẵn trong package-list nhưng chưa xác minh trên phần cứng pilot thật.
12. **Test tự động:** CI nội bộ (ruff/black/mypy + pytest, ~2593 ca ở commit `93f200a`/`ff7928d`)
    **xanh** — nhưng đây là test đơn vị/tích hợp mức mã nguồn + mô phỏng, **không thay thế**
    test report boot-test/người dùng thật mà HIG §13.5 yêu cầu (chưa có test report đó cho
    release này).

**Tóm tắt một dòng:** 2026.11 "Đông Sơn" là một **snapshot cấu hình/tài liệu/code alpha**, đầy
đủ nhất từ trước tới nay về mặt rebrand + đặc tả Windows-11-feel + semantic tokens, nhưng
**chưa một phần nào** (boot, cài, nâng cấp, rollback, driver, nhãn hiệu) được xác nhận trên máy
hoặc người dùng thật.
