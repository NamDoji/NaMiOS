# NaMiOS — Nâng cấp theo nhu cầu người dùng thật (Gap analysis + Lộ trình ưu tiên)

> **Loại tài liệu:** phân tích hiện trạng (grounded trên repo) + lộ trình nâng cấp có ưu tiên.
> **Ngày:** 2026-11-10. **Người soạn:** rà soát kỹ thuật độc lập.
> **Đối tượng người dùng mục tiêu (chủ dự án chốt):** người Việt phổ thông — **nhân viên văn phòng, kế toán, tài chính, người ít rành công nghệ** — phải dùng được **thành thạo** và cảm thấy **chuyên nghiệp/hiện đại** (quen tay kiểu Windows 11 + ít-thao-tác kiểu macOS).
>
> **Phạm vi tài liệu này:** CHỈ phân tích + đề xuất. KHÔNG sửa code/gói khác, KHÔNG build, KHÔNG commit.
>
> **Quy ước trung thực (giữ theo README §"Nguyên tắc số 1" + DAC_TA §11.2):** mọi khẳng định trạng thái dưới đây lấy từ **bằng chứng repo** (file/gói), KHÔNG phải bằng chứng boot/pilot thật. Toàn hệ hiện ở `verified_on_host: NO` — đã vào được desktop KDE trong QEMU nhưng **chưa có pilot máy thật**, **chưa có app thương mại nào đạt** (`docs/STATUS.md`). Chỗ nào tôi suy đoán sẽ ghi rõ **[GIẢ ĐỊNH]**.

---

## Chú giải mức ưu tiên & công sức

- **P0** — chặn khả dụng văn phòng/kế toán, hoặc an toàn/mất dữ liệu/niềm tin. Phải làm trước pilot.
- **P1** — cần cho pilot nghiệp vụ (G2) hoặc trải nghiệm chuyên nghiệp đủ dùng.
- **P2** — đánh bóng sau pilot.
- Công sức: **S** = vài ngày/1 wave · **M** = 1–2 tuần · **L** = nhiều tuần, **cần build host/phần cứng thật** · **XL** = cần đối tác/nhà cung cấp/pháp lý/pilot thật (ngoài tầm lập trình thuần).

---

## 0. CHẶN GỐC (master dependency) — đọc trước mọi mục

**CURRENT STATE.** Môi trường phát triển hiện tại là Debian 12 trong container **không có `/dev/kvm`**, thiếu `qemu`/`live-build`/`wine` (`docs/STATUS.md` bảng môi trường; `CLAUDE.md` §"Môi trường build"). Mốc **M2 (Wine/.NET), M3 (ISO/boot), M4 (app thương mại) đều BLOCKED**. Gần như **mọi** file đánh dấu `verified_on_host: NO`; mọi tên gói trong `distro/live-build/config/package-lists/*.list.chroot` mang chú thích "PHẢI `apt-cache show` + `lb build` trên build host trixie thật trước khi tin".

**GAP.** Tất cả tuyên bố "chạy được / tương thích cao / 79 hàm khớp / codec phát được / máy in nhận" đều là **kỳ vọng tĩnh**, chưa đo trên hệ thật. Không thể nghiệm thu "dùng thành thạo" cho kế toán/văn phòng khi chưa từng boot bản cài trên phần cứng thật và chạy hết một workflow.

**RECOMMENDATION.** Cấp **một build host Linux amd64 thật có nested-virt** (hoặc máy vật lý) làm việc đầu tiên của mọi wave sau: (1) `lb build` ra ISO; (2) boot QEMU/KVM + **cài Calamares lên đĩa thật**; (3) chạy bộ kiểm chứng tối thiểu (mở `KiemTra_Ham_Office.xlsx`, double-click .docx/.xlsx/.pptx, in thử qua `cups-pdf`, gõ Telex thật, cập nhật APT, snapshot/rollback Timeshift). Mỗi mục dưới đây có đuôi "**cần build host**" chính là mục khoá sau cổng này.

**PRIORITY: P0 · Effort: L** (hạ tầng, không phải code). Đây là **đòn bẩy lớn nhất** — xem Top-10 #1.

---

## 1. Sẵn sàng văn phòng & kế toán

### 1.1 Độ trung thực tương thích Microsoft Office (xlsx/docx/pptx)

**CURRENT STATE.** Ship `libreoffice` metapackage **25.2.3** (`4:25.2.3-2+deb13u6`, `0400-office-browser.list.chroot`) rebrand hiển thị thành **NaMiOffice / NaMiWriter / NaMiSheet / NaMiSlides / NaMiDraw / NaMiData / NaMiMath** (hook `0450`/`0451`). Đã cấu hình "quen tay": lưu mặc định `.xlsx/.docx/.pptx`, cú pháp công thức Excel A1, tên hàm tiếng Anh, luôn tính lại khi mở (`etc/skel/.config/libreoffice/4/user/registrymodifications.xcu`, tài liệu `docs/support/OFFICE-COMPAT.md`). Có file tự chấm **79 hàm** + demo `.pptx` biểu đồ cột nguyên sinh.

**GAP.**
- **Chưa có round-trip thật** với Microsoft Office có giấy phép — chỉ selfcheck tĩnh + round-trip qua chính soffice ở CI (`NAMI-APP-CATALOG.md` §3.7). Hai phép đo không tương đương.
- **Khoảng trống ĐÃ BIẾT sẽ cắn kế toán:** VBA macro (UserForm/ActiveX/`.xlam`) **không chạy/chạy sai**; **mảng động spill + LAMBDA/LET KHÔNG có trong LO 25.2** (`OFFICE-COMPAT.md` §2 đã đính chính); PivotTable/Power Query/Slicer hạn chế; trôi font/layout do thiếu Calibri/Cambria/Segoe UI.
- **Rebrand chỉ ở nhãn hiển thị** — title bar + hộp About vẫn in "LibreOffice 25.x" (`docs/branding/NAMIOFFICE.md` §"CHƯA làm được"). Người dùng tinh ý sẽ thấy "không phải sản phẩm riêng".

**RECOMMENDATION.**
1. **Đo thật (cần build host):** chạy `KiemTra_Ham_Office.xlsx` trên ISO, ghi số hàm KHỚP thật; dựng **bộ 10–15 workbook/doc kế toán VN điển hình** (bảng lương, khấu hao, SUMIFS/VLOOKUP/XLOOKUP, định dạng `#.##0 ₫`, ngày dd/MM/yyyy, CSV `;`) và round-trip so với Excel tham chiếu. Công bố ma trận "đạt/khác/mất" theo DAC_TA §18.2 `EXCEL`.
2. **Thay thế font metric-compatible** (P0 cho layout drift): cài **Carlito** (thay Calibri) + **Caladea** (thay Cambria) — cả hai OFL, **không phải** font Microsoft, có trong Debian. Hiện `0300-fonts.list.chroot` có Noto/Liberation/Inter nhưng **thiếu Carlito/Caladea** → tài liệu Office mở ra lệch dòng/ngắt trang. Thêm `fonts-crosextra-carlito` + `fonts-crosextra-caladea`.
3. **Soạn lớp cảnh báo VBA trung thực** trong NaMiOffice onboarding/Help: "file có macro → mở ở chế độ chỉ xem/cảnh báo, không tự chạy" (khớp `MacroSecurityLevel=1` đã đặt).
4. **[P2]** Build lại LibreOffice từ nguồn với `--with-vendor=NaMiOS` + `PRODUCTNAME=NaMiOffice` để sạch title bar/About — tầng lớn, xếp sau.

**PRIORITY: P0** (font metric-compat + đo thật) / **P2** (rebuild nguồn) · **Effort: M** (font + đo) / **L** (rebuild).

### 1.2 In ấn, xuất & ký PDF

**CURRENT STATE.** CUPS đầy đủ + driverless (IPP/eSCL/Avahi) + driver theo hãng (gutenprint/escpr/brlaser/foo2zjs/postscript-hp/hplip) + **hàng in ảo "In ra PDF"** (`printer-driver-cups-pdf`) (`0500-print.list.chroot`, `0680`, `0700-printing.list.chroot`). PDF: Okular (NaMiPDF) + `poppler-utils`/`qpdf`/`ocrmypdf`/`tesseract-ocr-vie`/`img2pdf`/`pikepdf` (`0420-pdf.list.chroot`).

**GAP.**
- **Ký số PDF chưa phải tính năng được xác minh** — Okular xem/chú thích/điền AcroForm, nhưng **ký bằng chứng thư/USB token chưa có đường tích hợp** (catalog ghi "ký/redact không suy từ việc xem"). Đây là nhu cầu kế toán/văn phòng thật (ký hợp đồng, tờ trình PDF).
- **In từ app Wine, khổ A4/A5, 2 mặt, font Việt, mã vạch/QR chưa test** (DAC_TA §27 DEV-002) — chưa có phần cứng.
- Không có bộ kiểm "in tiếng Việt có dấu ra đúng" trên máy in thật.

**RECOMMENDATION.**
1. **Ký PDF nội bộ (P1):** bật đường ký PDF bằng chứng thư mềm (.p12/PKCS#12) ngay trong Okular/LibreOffice (cả hai hỗ trợ sẵn digital signature) + tài liệu tiếng Việt "cách ký PDF bằng chữ ký số". Token USB/eID = nhánh riêng (xem §1.4, cần PKCS#11).
2. **Bộ kiểm in (cần build host + 2 máy in thật, theo HW-001):** A4/A5, 2 mặt, tiếng Việt có dấu, PDF, in từ Wine — ghi evidence theo model (DEV-002/DEV-008).
3. Giữ `cups-pdf` làm đường "In → PDF" mặc định để người dùng luôn xuất PDF được dù không có máy in.

**PRIORITY: P1 · Effort: M** (ký mềm + docs) / **L** (kiểm in phần cứng).

### 1.3 Font & mẫu tài liệu tiếng Việt (hóa đơn/bảng lương)

**CURRENT STATE.** Font có quyền phân phối, đủ glyph Việt: Noto, Liberation2, DejaVu, **Inter** (OFL) (`0300-fonts.list.chroot`). KHÔNG chép font Microsoft (đúng VN-005/LIC-004).

**GAP.**
- **Không có MẪU (template) nghiệp vụ VN nào** được đóng gói: không hóa đơn, bảng lương, công văn, phiếu thu/chi, bảng chấm công. Kế toán/văn phòng mở máy lên là "trang trắng" → phải tự dựng → cảm giác kém chuyên nghiệp so với bộ template Office quen thuộc.
- Thiếu font metric-compat (đã nêu §1.1) → tài liệu từ đối tác lệch layout.

**RECOMMENDATION.**
1. **Bộ template NaMiOffice tiếng Việt (P1, S/M):** 8–12 mẫu `.ott/.ots/.otp` — hóa đơn bán hàng, bảng lương, phiếu thu/chi, công văn, biên bản họp, báo giá, bảng chấm công, thư mời. Ship vào `/usr/share/namios/templates/` + đăng ký vào LibreOffice template manager + mục "Mẫu của tôi" ở `etc/skel`. **Trung thực:** mẫu tự thiết kế, KHÔNG sao chép mẫu bản quyền; hóa đơn chỉ là **mẫu trình bày**, KHÔNG phải hóa đơn điện tử hợp lệ pháp lý (xem §1.4).
2. Thêm Carlito/Caladea (từ §1.1).

**PRIORITY: P1 · Effort: S–M.**

### 1.4 Phần mềm kế toán thật + hóa đơn điện tử + cổng ngân hàng/thuế (ĐIỂM NGHẼN LỚN NHẤT)

**CURRENT STATE.** **KHÔNG có** MISA, HTKK, eTax, phần mềm hóa đơn điện tử, hay bridge ký số nào trong repo. Chỉ có **4 shortcut web** (Facebook, Zalo Web `chat.zalo.me`, TikTok, YouTube — `PL09-DEFAULT-APPS.md` §2) và khung phân tích (`PHU-LUC-02-HE-SINH-THAI-VN.md`, `ECO-001..024`). `support-matrix.md` ghi thẳng: **"Chữ ký số / hóa đơn điện tử | 0"** workflow đã kiểm. Nền .NET/Wine đã cài gói (`mono-complete`, `wine`, `winetricks`, `winbind`, `wine-binfmt` — `0660-dotnet-compat.list.chroot`) nhưng **chưa có capsule/prefix/recipe/evidence** cho app nào.

**GAP (đây là lý do kế toán/tài chính CHƯA THỂ chuyển máy chính):**
- **MISA SME** = client-server .NET + **SQL Server** + COM + report + ký số — Wine **không cấp driver kernel/USB token** (DAC_TA §6.4, STATUS WIN-008). Chưa đánh giá, chưa cert.
- **Chữ ký số USB token / ký từ xa** (Viettel-CA, VNPT-CA, FPT-CA…): cần ma trận `token × model × firmware × middleware × browser × nghiệp vụ` (DAC_TA §27 DEV-005, `ECO-009`). Nhiều plugin ký là **Windows-only** → có thể là blocker cứng.
- **Cổng thuế/BHXH/dịch vụ công**: nhiều cổng cần plugin ký Windows hoặc kiểm tra môi trường; chạy trên Firefox Linux **chưa test luồng ký/nộp/biên nhận**.
- **Cổng ngân hàng (internet banking / Smart OTP)**: đa phần web → **[GIẢ ĐỊNH]** chạy được trên Firefox ESR, nhưng chưa có bằng chứng; một số app ngân hàng doanh nghiệp dùng token/applet riêng.

**RECOMMENDATION (chủ yếu khảo sát + đối tác, KHÔNG phải code thuần).**
1. **Khảo sát workflow thật (P0, XL):** thực hiện `WIN-001`/`ECO-005` — lấy từ 1–2 đơn vị pilot kế toán danh sách "việc không thể thiếu" + phiên bản MISA/HTKK/CA token cụ thể. Không chốt phạm vi được nếu thiếu dữ liệu này.
2. **Thử nghiệm ký số PKCS#11 (P0, L):** với token có driver Linux (nhiều token VN hỗ trợ PKCS#11/PCSC) — thử đăng nhập cổng + ký sandbox. Nếu Windows-only → ghi `blocked_external_dependency`, công bố thẳng (DAC_TA §6.4 APP-MIS-008).
3. **Đường thoát hợp lệ (P1):** với app bắt buộc chạy Windows (MISA SME, plugin ký Windows-only), cung cấp **VM Windows có giấy phép / remote desktop** hiển thị **tách bạch**, KHÔNG gộp vào "đã bỏ Windows" (ECO-015). AMIS Kế toán (web) + HĐĐT web ưu tiên kiểm đường web trước.
4. **Trung thực tuyệt đối:** giữ nhãn `launches_only`/`partial_workflow` ≠ "dùng được" (ECO-003); dashboard coverage theo workflow, tách web/Wine/VM/remote (ECO-022).

**PRIORITY: P0 (khảo sát + quyết định go/no-go) · Effort: XL.** Đây là mục quyết định liệu nhóm kế toán có thể chuyển máy chính hay không — **không giải bằng công sức lập trình**.

---

## 2. Khả dụng hằng ngày cho người ít rành công nghệ

### 2.1 Cài phần mềm dễ dàng (software center)

**CURRENT STATE.** `plasma-discover` + `packagekit` + `appstream` (NaMiCửa hàng) + `flatpak` + `xdg-desktop-portal(-kde)` (`0100`, `0630`). Metapackage riêng `namios-*` **chưa build** (`0900-*.list.chroot.disabled`).

**GAP.** Discover + AppStream metadata **chưa kiểm trên ISO thật** — kho rỗng/thiếu metadata là lỗi phổ biến. Flatpak cài nhưng **chưa thêm remote Flathub** (không có evidence) → người dùng bấm "cài app" có thể không thấy gì. Không có "Trung tâm ứng dụng NaMiOS" theo nhóm việc (Văn phòng/Thuế/Kế toán…) như DESIGN-SYSTEM §7 mô tả — mới là Discover trần.

**RECOMMENDATION.**
1. **Cần build host:** xác minh Discover hiển thị + cài được 1 app; thêm **Flathub remote** (có cảnh báo nguồn bên thứ ba) để người dùng cài Zalo/Zoom/… bản Flatpak khi có.
2. **[P1]** Lớp "Danh mục theo nhóm việc" (ECO-006/007: tìm "khai thuế", "hóa đơn" có/không dấu) phủ lên Discover, trỏ web/native/Wine đúng mode + nhãn trạng thái trung thực.

**PRIORITY: P1 · Effort: M (cần build host để xác minh).**

### 2.2 Cập nhật hệ thống

**CURRENT STATE.** APT + `unattended-upgrades` (vá bảo mật tự động) + `ca-certificates` + `systemd-timesyncd` (`0180`); `needrestart` báo dịch vụ cần restart; `timeshift` snapshot trước update (`0640`). ADR-0014.

**GAP.** Timeshift chạy **rsync (ext4), KHÔNG phải A/B nguyên tử** — APT không nguyên tử, mất điện giữa update vẫn rủi ro (ghi rõ ở `0640` comment). Chưa kiểm luồng update→reboot→rollback thật. Lớp "Update Center" điều phối (SmartAI, ADR-0017) **đang làm, chưa nối thật**.

**RECOMMENDATION.** **Cần build host:** diễn tập một chu kỳ `apt upgrade` → `needrestart` → snapshot → rollback trên VM; tài liệu người dùng "cập nhật an toàn + cách quay lui" bằng tiếng Việt. Giữ `unattended-upgrades` chỉ security-pocket (tránh update ồ ạt gãy máy người ít rành).

**PRIORITY: P1 · Effort: M.**

### 2.3 Driver, máy in, Wi-Fi (nhận thiết bị "như Windows")

**CURRENT STATE.** Firmware rộng (iwlwifi/realtek/atheros/brcm/mediatek/amd-graphics/sof-signed/libertas/ti — `0150`,`0720`); NetworkManager + plasma-nm; Bluetooth bluez/bluedevil/blueman; in/scan phủ nhiều hãng (xem §1.2); `usbutils`/`mtp-tools`/`rfkill`/`efax` + script `namios-ket-noi-thiet-bi` + `namios-chan-doan` (`0650`,`0680`). archive-areas gồm `non-free`+`non-free-firmware` (`auto/config`).

**GAP.** **Toàn bộ phần cứng chưa test máy thật** — danh sách firmware ≠ thiết bị chạy (DAC_TA §27). "Nhận USB ID" ≠ "in/scan đúng nghiệp vụ". NVIDIA rời, Wi-Fi hiếm, scanner ADF chưa có profile. Script thiết bị trả lời được "bus có thấy không" nhưng chưa có DB thiết bị theo model (DEV-001).

**RECOMMENDATION.** **Cần phần cứng pilot (HW-001: ≥5 máy + ≥2 máy in):** chạy ma trận DEV-002..008, dựng **DB thiết bị theo model/chức năng** hiển thị "hoạt động đầy đủ/một phần/chưa kiểm/không hỗ trợ" (DEV-008). Ưu tiên máy in Canon/HP/Epson/Brother phổ biến VN.

**PRIORITY: P1 · Effort: L (phần cứng).**

### 2.4 Kỳ vọng "diệt virus"

**CURRENT STATE.** `clamav` + `clamav-freshclam` **chỉ on-demand** (KHÔNG daemon on-access — `0635`, quyết định VN09-029). `ufw` firewall deny-incoming, `apparmor`.

**GAP.** Người dùng Windows **kỳ vọng "có phần mềm diệt virus đang bảo vệ realtime"**. ClamAV on-demand không bật, không realtime → khoảng cách kỳ vọng. Nhưng bật on-access ClamAV có rủi ro treo/ngốn CPU thật (đã phân tích đúng ở `0635`).

**RECOMMENDATION.** **Giáo dục kỳ vọng, không overclaim:** Security Center tiếng Việt giải thích mô hình bảo vệ Linux (quyền user + AppArmor + firewall + cập nhật) + nút "Quét thư mục này" bằng ClamAV khi cần. **TUYỆT ĐỐI không hứa "chặn 100% mã độc"** (VN09-030). Cân nhắc benchmark on-access trên phần cứng pilot trước khi quyết định (việc riêng, cần số đo).

**PRIORITY: P1 · Effort: S (UI/giáo dục) / M (benchmark on-access).**

### 2.5 Chia sẻ tệp, ổ Windows, Zalo & app VN, media/codec, chụp/quét

**CURRENT STATE.** SMB (`cifs-utils`/`smbclient`/`kio-extras`), NTFS/exFAT (`ntfs-3g`/`exfatprogs`), MTP điện thoại, Thùng rác Dolphin. **Zalo = web shortcut** `chat.zalo.me` (chưa có bản PC/Wine). Media: **VLC + gstreamer good/bad/ugly/libav** đã thêm (`0430-media.list.chroot`). Chụp màn hình `kde-spectacle`; quét `skanlite`/`simple-scan`.

**GAP.**
- **Mâu thuẫn tài liệu:** `NAMI-APP-CATALOG.md` (10/11) ghi "NaMiMedia CHƯA SHIP, không trình phát nào" nhưng `0430-media.list.chroot` **đã thêm VLC**. → cập nhật catalog cho khớp; hoặc xác nhận VLC thật sự vào ISO.
- **Zalo PC** (gọi video, đồng bộ file tốt hơn) chưa có — nhiều người Việt cần bản PC.
- **Codec `gstreamer-plugins-ugly` (H.264/H.265/AAC/MP3)** liên quan **bằng sáng chế** — repo cảnh báo **cần legal review trước phát hành thương mại VN** (`0430` comment).
- **RAR** không giải nén được (thiếu `unrar` — catalog §3.2) — rất phổ biến ở VN.

**RECOMMENDATION.**
1. **[S]** Đồng bộ `NAMI-APP-CATALOG.md` với thực tế gói VLC đã thêm.
2. **[P1]** Thêm giải nén **RAR**: `unrar-free` (main, giải nén được phần lớn) hoặc đánh giá `unar`/`libarchive`+rar — ghi rõ "giải nén, không tạo".
3. **[P1]** Zalo PC qua Wine capsule = nhánh riêng theo version (DAC_TA §6.3), cert riêng; trước mắt giữ web + nêu giới hạn gọi video.
4. **[P0 trước phát hành thương mại]** Legal review quyền phân phối từng codec (H.264/H.265/AAC) theo luật SHTT VN (`TRADEMARK-LICENSE-COMPLIANCE.md` dẫn chiếu) — có thể phải tách ảnh "có codec"/"không codec".

**PRIORITY: P1 (RAR, Zalo, catalog sync) / P0 (legal codec trước bán) · Effort: S–M / XL (legal).**

---

## 3. Chuyên nghiệp & quen thuộc (Win11 + ít-thao-tác macOS)

### 3.1 Giao diện & cảm giác hiện đại

**CURRENT STATE.** KDE Plasma 6 + bộ nhận diện **"Sen Việt" v2** (brand.json mực đêm/đỏ son `#C93643`), ngôn ngữ hình ảnh **squircle iOS + kính mờ + dock** (`branding/style/namios.css`), 20 hình nền chủ đề Việt Nam đã có thư mục (`includes.chroot/usr/share/wallpapers/NaMiOS-01..20`), theme SDDM/Plymouth/Aurorae, font UI **Inter** (OFL). Design system đầy đủ token/typography/spacing/accessibility (`DESIGN-SYSTEM.md`).

**GAP.**
- **Chưa thấy trên desktop thật** (`verified_on_boot: NO` khắp design docs). "Đã có CSS + token" ≠ "theme KDE thật áp đúng". KDE mặc định ≠ cảm giác Win11/macOS nếu chưa cấu hình panel/dock/global-theme.
- **Mâu thuẫn tài liệu bản quyền hình nền:** `DESIGN-SYSTEM.md` PL12.5 ghi "wallpaper-manifest có **0 ảnh thật**, toàn placeholder, cần cấp phép"; nhưng includes.chroot **đã có 20 thư mục wallpaper** → **[CỜ ĐỎ]** cần truy xuất nguồn/giấy phép 20 ảnh này trước khi phát hành (rủi ro bản quyền ảnh địa danh).

**RECOMMENDATION.**
1. **Cần build host (P1):** chốt một **Global Theme NaMiOS** (panel kiểu Win11: taskbar dưới + menu Bắt đầu + khay; hoặc dock kiểu macOS), áp + chụp ảnh thật; xác minh squircle/kính mờ render đúng (compositing có thể OFF trên máy không GPU — xem `0410`).
2. **[P0 bản quyền]** Kiểm chứng giấy phép 20 hình nền; nếu thiếu evidence → gỡ hoặc thay bằng ảnh có quyền (UX12-026/048). Không để ảnh rights-unknown trong ISO.

**PRIORITY: P1 (theme) / P0 (bản quyền wallpaper) · Effort: M.**

### 3.2 Ít-thao-tác & onboarding lần đầu

**CURRENT STATE.** `namios-welcome` (PySide6) có wizard first-run: chọn Telex/VNI, cỡ chữ 100/125/150%, app mặc định docx/xlsx/pdf, máy in; có marker chạy-1-lần + `migrate.py` (nhập dữ liệu từ Windows) (`src/namios_welcome/firstrun.py`, `ui.py`, hook `0300`).

**GAP.**
- **Wizard mới ghi `welcome.json`, CHƯA áp hiệu lực thật lên hệ thống** — firstrun.py nói rõ "có hiệu lực chỉ khi desktop session đọc file này — **nằm ngoài phạm vi module** (ADR 0011)". Tức người dùng chọn Telex nhưng **chưa chắc Fcitx5 đổi theo**; chọn app mặc định chưa chắc ghi `mimeapps.list`. Đây là khoảng trống "có UI, chưa có tác dụng".
- Chưa có **tour 60 giây** kiểu "đây là nút Bắt đầu, đây là Tệp của tôi, đây là cách gõ tiếng Việt" cho người ít rành.

**RECOMMENDATION.**
1. **[P0] Nối wizard → hiệu lực thật:** apply() phải thực sự ghi cấu hình Fcitx5 (Telex/VNI), KDE scale, `mimeapps.list`, máy in mặc định — không chỉ `welcome.json`. Đây là mục làm cho "ít-thao-tác" thành thật.
2. **[P1]** Thêm tour hình ảnh + 3–5 "việc đầu tiên" (mở Word, gõ tiếng Việt, lưu, in PDF, kết nối Wi-Fi).

**PRIORITY: P0 (nối hiệu lực) / P1 (tour) · Effort: M.**

### 3.3 Trợ giúp tiếng Việt & khả năng tiếp cận

**CURRENT STATE.** Design system đặt mục tiêu **WCAG 2.2 AA**, tương phản đã đo/chỉnh 3 token, phóng chữ 100–200%, glossary 55 thuật ngữ, từ vựng phổ thông chuẩn (`DESIGN-SYSTEM.md` PL12). `namios-huong-dan` + HTML hướng dẫn nhanh (`docs/huong-dan/`). **Ngôn ngữ hiển thị mặc định đổi sang tiếng Anh** (10/11) vì bản dịch KDE tiếng Việt chỉ phủ một phần (`0100-locale-vi.hook.chroot`, `0210`).

**GAP.**
- **[CĂNG THẲNG MỤC TIÊU]** Mục tiêu người dùng là "người Việt phổ thông/ít rành công nghệ" nhưng **mặc định đang là tiếng Anh** → ngược nhu cầu. Lý do (dịch KDE chỉ một phần, trộn Việt/Anh xấu) là thật, nhưng với kế toán/văn phòng ít rành thì **tiếng Anh là rào cản lớn hơn** trộn ngôn ngữ.
- Accessibility (screen reader, 200% text) **chưa test** (`blocked-infra`).

**RECOMMENDATION.**
1. **[P0 — cần chủ dự án quyết]** Xem lại quyết định mặc-định-tiếng-Anh cho đúng đối tượng: đề xuất **mặc định tiếng Việt** + đầu tư **lớp phủ dịch vi_NM** (đã có hạ tầng — xem memory "vi_NM overlay") để phủ các chuỗi KDE phổ biến nhất, giảm trộn ngôn ngữ. Hoặc: màn chào đầu tiên cho chọn ngôn ngữ 1-chạm (vẫn mở tiếng Việt sẵn).
2. **[P1]** Trợ giúp offline tiếng Việt theo tác vụ (in, gõ, lưu, ký PDF, kết nối máy in) + tích hợp giải thích lỗi.
3. **Cần build host:** test screen reader + 200% text (UX12-035).

**PRIORITY: P0 (ngôn ngữ mặc định — cần chốt) / P1 (help + a11y) · Effort: S (quyết định) / M (overlay dịch).**

---

## 4. Niềm tin, an toàn & trung thực

**CURRENT STATE (điểm mạnh — giữ bằng mọi giá).** Repo có kỷ luật trung thực hiếm thấy: từ vựng trạng thái `untested/experimental/task_verified/blocked/revoked` (DAC_TA §11.2); `verified_on_host: NO` khắp nơi; nhãn "đã kiểm thử" tách khỏi "nhà cung cấp hỗ trợ" (UX-002/ECO-004); tài liệu bản quyền chi tiết (`TRADEMARK-LICENSE-COMPLIANCE.md`); không chép font/logo Microsoft (LIC-004/VN-005); telemetry mặc định tắt (SUP-001).

**GAP / ĐIỀU KHÔNG ĐƯỢC OVERCLAIM (danh sách kiểm trước mọi phát ngôn marketing):**
1. **KHÔNG** "chạy mọi phần mềm Windows" (WIN-008) — nhất là app có kernel driver / token / anti-cheat.
2. **KHÔNG** "tương thích 100% Microsoft Office" — VBA/spill/Pivot là khoảng trống thật (§1.1).
3. **KHÔNG** "miễn phí toàn bộ phần mềm" — OS free ≠ MISA/Office/Windows-VM free (LIC-002).
4. **KHÔNG** "diệt sạch virus / an toàn tuyệt đối" (VN09-030).
5. **KHÔNG** "tương thích Outlook/Exchange" cho NaMiMail/Thunderbird (`0405`).
6. **KHÔNG** gọi LibreOffice là "Microsoft Word/Excel" trong tên hiển thị (UI-005).
7. **KHÔNG** tuyên bố "được cơ quan nhà nước/nhà cung cấp chứng nhận" khi chưa có văn bản (ECO-004).

**Thành phần không-tự-do / rủi ro pháp lý cần công bố:**
- `non-free`/`non-free-firmware` bật trong `auto/config` → ISO chứa firmware không tự do → **không được quảng bá "100% phần mềm tự do"** (LIC-006). Cần `THIRD_PARTY_NOTICES` + SBOM liệt kê.
- `gstreamer-plugins-ugly` + `libfdk-aac2t64` = rủi ro bằng sáng chế codec tại VN (§2.5) → **legal review trước bán**.
- **Hình nền 20 ảnh địa danh**: rights-unknown (§3.1) → cần evidence cấp phép.

**An ninh cập nhật:** APT có chữ ký; catalog/profile NaMiOS cần metadata ký + chống downgrade/replay, fail-closed (SEC-007/008) — **key production chưa có, chưa ký thật** (còn ở M5/G3).

**RECOMMENDATION.**
1. **[P0]** Dựng **"Tuyên bố giới hạn trung thực"** (1 trang, tiếng Việt) hiển thị ở About + trang tải: 7 điều không-overclaim ở trên. Gắn vào release notes mọi bản.
2. **[P0]** Hoàn tất **SBOM (SPDX/CycloneDX) + THIRD_PARTY_NOTICES + license inventory** cho đúng ISO thật (BUILD-003) trước G3; đặc biệt đánh dấu thành phần non-free + codec + wallpaper.
3. **[P1]** Legal review codec + wallpaper + nhãn hiệu NaMiOS (tra cứu nhãn hiệu trước công bố — OWN-002).
4. **[P1]** Ký metadata catalog (TUF nếu đạt spike) + quy trình thu hồi (SEC-007/008), key production ngoài repo/CI.

**PRIORITY: P0 (tuyên bố giới hạn + SBOM) / P1 (legal + ký) · Effort: S (tuyên bố) / M (SBOM) / XL (legal + ký production).**

---

## 5. Top 10 nâng cấp tác động cao nhất (xếp hạng)

| # | Nâng cấp (1 dòng để dev nhận việc) | Ưu tiên | Effort |
|---|---|---|---|
| 1 | **Cấp build host Linux có nested-virt → `lb build` + boot + CÀI thật + chạy bộ kiểm chứng tối thiểu** (mở khoá mọi `verified_on_host: NO`). | P0 | L |
| 2 | **Khảo sát + go/no-go nhóm kế toán:** lấy phiên bản MISA/HTKK/CA-token thật từ 1 đơn vị pilot; thử ký số PKCS#11; chốt đường web/Wine/VM cho từng workflow (ECO-005, WIN-001). | P0 | XL |
| 3 | **Thêm font metric-compatible Carlito + Caladea** vào `0300-fonts.list.chroot` để hết trôi layout tài liệu Office từ đối tác. | P0 | S |
| 4 | **Nối wizard first-run → hiệu lực thật** (Fcitx5 Telex/VNI + KDE scale + `mimeapps.list` + máy in), không chỉ ghi `welcome.json`. | P0 | M |
| 5 | **Chốt lại ngôn ngữ mặc định = tiếng Việt** (đúng đối tượng ít rành) + đầu tư lớp phủ dịch vi_NM giảm trộn ngôn ngữ. | P0 | S–M |
| 6 | **Bộ 8–12 mẫu nghiệp vụ VN** (hóa đơn/bảng lương/phiếu thu-chi/công văn) ship vào NaMiOffice; tự thiết kế, không chép bản quyền. | P1 | S–M |
| 7 | **Đo tương thích Office thật** (79 hàm + 10–15 workbook kế toán round-trip vs Excel) và công bố ma trận trung thực; ký PDF bằng chứng thư mềm. | P1 | M |
| 8 | **Chốt Global Theme NaMiOS** (Win11-taskbar hoặc macOS-dock) áp + chụp ảnh thật; kiểm render squircle/kính mờ trên máy không GPU. | P1 | M |
| 9 | **Giải nén RAR + đồng bộ catalog media (VLC đã ship)** + thêm Flathub remote cho Discover; Zalo PC = nhánh Wine riêng theo version. | P1 | S–M |
| 10 | **"Tuyên bố giới hạn trung thực" + SBOM/THIRD_PARTY_NOTICES + legal review codec/wallpaper** trước mọi phát hành công khai. | P0/P1 | S–M (+XL legal) |

---

## Phụ lục — Mâu thuẫn tài liệu cần sửa (phát hiện khi rà)

1. **NaMiMedia:** `NAMI-APP-CATALOG.md` §1/§3 ghi "chưa có trình phát nào" nhưng `0430-media.list.chroot` đã thêm **VLC + gstreamer**. → cập nhật catalog.
2. **Hình nền:** `DESIGN-SYSTEM.md` PL12.5 ghi "0 ảnh thật, toàn placeholder cần cấp phép" nhưng `includes.chroot/usr/share/wallpapers/` có **20 thư mục ảnh**. → đối chiếu nguồn/giấy phép hoặc cập nhật manifest.
3. **Ngôn ngữ mặc định:** nhiều file gốc ghi "giao diện mặc định 100% tiếng Việt" (VN-001) nhưng `0100-locale-vi.hook.chroot` (10/11) đổi **mặc định tiếng Anh**. → tài liệu hoá quyết định nhất quán + xét lại theo đối tượng.
4. **Wine:** `0600-wine.list.chroot.disabled` (tắt) nhưng `0660-dotnet-compat.list.chroot` (bật) cũng khai `wine`/`winetricks`. → apt tự khử trùng, nhưng cần một nguồn sự thật khi bật lại 0600.

*Hết tài liệu. Nguồn bằng chứng: `docs/specs/DAC_TA_HE_DIEU_HANH.md`, `distro/live-build/config/package-lists/*`, `docs/apps/NAMI-APP-CATALOG.md`, `docs/support/OFFICE-*.md`, `docs/branding/NAMIOFFICE*.md`, `docs/design/DESIGN-SYSTEM.md`, `docs/specs/PHU-LUC-02-HE-SINH-THAI-VN.md`, `docs/STATUS.md`, `src/namios_welcome/firstrun.py`, `support-matrix.md`.*
