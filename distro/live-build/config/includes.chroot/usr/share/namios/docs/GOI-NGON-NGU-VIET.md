# NaMiOS — Gói ngôn ngữ Việt hợp nhất (GOI-NGON-NGU-VIET)

- **Wave:** VN-4 "Gói ngôn ngữ Việt hợp nhất (chính tả + ngữ + định dạng + tự
  sửa 'quen tay')" — xem `docs/roadmap/NEW-FUNCTIONS-DIRECTION.md` §3, mục
  VN-4 (requirement gốc, không trích lại toàn văn ở đây).
- **File này SHIP TRONG ISO** (`/usr/share/namios/docs/GOI-NGON-NGU-VIET.md`)
  — bản tóm tắt sống cùng máy để người dùng/support mở trực tiếp trên
  NaMiOS, khác bản trong repo dev (file này KHÔNG có bản mirror
  `docs/support/` — chỉ tồn tại ở đây cho wave này).
- **verified_on_host: NO cho TOÀN BỘ file này.** Mọi khẳng định dưới đây đối
  chiếu trực tiếp với: (a) package index thật `Packages.gz` của
  `deb.debian.org/debian/dists/trixie/main/binary-amd64/` (tải trực tiếp,
  11/11/2026); (b) mã nguồn schema LibreOffice thật
  (`officecfg/registry/schema/org/openoffice/Office/Linguistic.xcs`, nhánh
  `master`, `github.com/LibreOffice/core`, tải trực tiếp 11/11/2026); (c) mã
  nguồn dữ liệu locale `vi_VN` thật của glibc
  (`localedata/locales/vi_VN`, nhánh `master`,
  `github.com/bminor/glibc` — mirror chính thức của glibc upstream, tải trực
  tiếp 11/11/2026). **CHƯA** chạy `lb build` + boot ISO thật để xác nhận các
  khoá này được nạp đúng trên máy thật — xem mục 5 "Phải boot-test".

## 0. Kết luận chính (đọc trước)

1. **Chính tả tiếng Việt (hunspell-vi)**: gói CÓ THẬT trong trixie/main,
   **đã được khai báo cài** (từ trước, ở `0405-mail-notes.list.chroot` cho
   Thunderbird + lặp lại có chủ đích ở `0310-vietnamese-langpack.list.chroot`
   mới cho "Gói ngôn ngữ Việt"). Việc **THIẾU** trước wave này là "nối" —
   LibreOffice có dictionary trong máy nhưng KHÔNG mặc định dùng nó cho văn
   bản mới (ngôn ngữ văn bản mặc định có thể vẫn là English). Wave này THÊM
   lớp registry mới `namios-vi.xcu` để đặt ngôn ngữ văn bản mặc định =
   tiếng Việt → chính tả tự động sẽ gọi đúng hunspell-vi.
2. **Từ điển đồng nghĩa (thesaurus) + gạch nối (hyphenation) tiếng Việt**:
   **KHÔNG CÓ** gói nào (`mythes-vi`, `hyphen-vi`) trong Debian 13
   trixie/main tại thời điểm kiểm (11/11/2026) — xác nhận bằng cách tải và
   grep toàn bộ `Packages.gz`, không suy đoán. Ghi nhận **`unknown`/không
   có**, không bịa gói thay thế, không ghi "đã có" sai sự thật.
3. **Định dạng số/tiền/ngày vùng Việt system-wide**: **ĐÃ ĐẠT từ hook có
   sẵn** (`hooks/normal/0100-locale-vi.hook.chroot`), **KHÔNG cần thêm hook
   mới** — xem phân tích đầy đủ ở mục 3. Đây là phần việc "verify + document",
   không phải "thêm mới" (ĐÃ xác nhận mã nguồn locale `vi_VN` thật của glibc
   tạo ra ĐÚNG format mà VN-4 yêu cầu: `1.234.567₫`, số thập phân dấu phẩy,
   ngày `dd/mm/yyyy`, tuần bắt đầu Thứ Hai).
4. **Tự sửa "quen tay" (autocorrect)**: **CHƯA LÀM** trong wave này (ngoài
   phạm vi 4 file được giao) — xem mục 6 "Chưa làm / để lại".

## 1. File đã sửa / đã tạo trong wave này

| File | Loại thay đổi |
| --- | --- |
| `config/package-lists/0310-vietnamese-langpack.list.chroot` | **File mới** — khai `hunspell-vi` (verified, xem mục 2), ghi rõ KHÔNG có `mythes-vi`/`hyphen-vi` |
| `includes.chroot/usr/lib/libreoffice/share/registry/data/namios-vi.xcu` | **File mới** — layer registry LibreOffice riêng (không sửa `registrymodifications-system-wide.xcu` cạnh nó): đặt `DefaultLocale=vi-VN` + `IsSpellAuto=true` |
| `includes.chroot/usr/share/namios/docs/GOI-NGON-NGU-VIET.md` | File này (mới) |

**KHÔNG sửa** (ngoài phạm vi, thuộc mối quan tâm/wave khác):
`0300-fonts.list.chroot`, `0400-office-browser.list.chroot`,
`0405-mail-notes.list.chroot`, `registrymodifications-system-wide.xcu`,
`etc/skel/.config/libreoffice/4/user/registrymodifications.xcu`,
`hooks/normal/0100-locale-vi.hook.chroot`, `etc/skel/.config/plasma-localerc`,
`etc/calamares/modules/locale.conf`.

## 2. Chính tả tiếng Việt — package verify + wiring

| Gói | Có trong trixie/main? | Nguồn xác nhận | Khai ở đâu |
| --- | --- | --- | --- |
| `hunspell-vi` | **CÓ** — `Source: libreoffice-dictionaries`, `Version: 1:25.2.3-1`, `Provides: hunspell-dictionary, hunspell-dictionary-vi` | `Packages.gz` trixie/main, 11/11/2026 | `0405-mail-notes.list.chroot` (đã có từ trước) + `0310-vietnamese-langpack.list.chroot` (mới, lặp lại có chủ đích để có 1 nơi quy chiếu "Gói ngôn ngữ Việt" — xem comment đầu file 0310 giải thích vì sao trùng là an toàn: `apt`/live-build ghép mọi `*.list.chroot` thành 1 lệnh cài, trùng tên gói không gây lỗi) |
| `mythes-vi` (thesaurus) | **KHÔNG CÓ** trong trixie/main | Đã grep toàn bộ `^Package: mythes-` trong `Packages.gz` — danh sách đủ (ar/bg/ca/cs/da/de/en-us/en-au/eo/es/fr/gl/gug/hu/id/is/it/lv/ne/no/pl/pt-br/pt-pt/ro/ru/sk/sl/sv/th/uk), không có `vi` | — (không khai, ghi `unknown`) |
| `hyphen-vi` (hyphenation) | **KHÔNG CÓ** trong trixie/main | Đã grep toàn bộ `^Package: hyphen-` trong `Packages.gz` — danh sách đủ (~45 ngôn ngữ khác), không có `vi` | — (không khai, ghi `unknown`) |

**Vì sao chỉ khai gói mà chưa đủ ("nối" là gì):** `libreoffice` (metapackage
Debian) chỉ **Suggests** `hunspell-dictionary` (virtual package, không phải
Depends/Recommends) — và build NaMiOS dùng `--no-install-recommends` (ghi
trong comment các file `0405`/`0620`/`0700` khác) nên Suggests chắc chắn
KHÔNG tự cài. Khai `hunspell-vi` tường minh giải quyết việc "có mặt trên
đĩa", nhưng **LibreOffice vẫn cần biết dùng dictionary nào cho văn bản nào**
— đó là khoá `DefaultLocale` (ngôn ngữ văn bản mặc định), xem mục 4.

## 3. Định dạng số/tiền/ngày vùng Việt — ĐÃ ĐẠT, không cần hook mới

`hooks/normal/0100-locale-vi.hook.chroot` (đã có, KHÔNG sửa trong wave này)
chạy:

```
update-locale LANG="vi_VN.UTF-8" LANGUAGE="vi_NM:vi:en_US" \
              LC_TIME="vi_VN.UTF-8" LC_NUMERIC="vi_VN.UTF-8"
```

Ghi vào `/etc/default/locale` **4 khoá**: `LANG`, `LANGUAGE`, `LC_TIME`,
`LC_NUMERIC`. **Không có dòng `LC_MONETARY`** — nhưng đây KHÔNG phải thiếu
sót cần vá: theo ngữ nghĩa chuẩn `setlocale()` của glibc/POSIX, khi một biến
`LC_<category>` cụ thể KHÔNG được set (và `LC_ALL` cũng không được set — xác
nhận đúng, Debian mặc định không set `LC_ALL`), category đó **tự động rơi về
giá trị của `LANG`**. Vì `LANG=vi_VN.UTF-8`, `LC_MONETARY` sẽ tự động dùng
dữ liệu tiền tệ của locale `vi_VN.UTF-8` **mà không cần khai riêng** — mọi
tiến trình (terminal, SSH, phiên Plasma, LibreOffice, Thunderbird...) đều
nhất quán vì `/etc/default/locale` được đọc chung qua `pam_env` cho mọi kiểu
đăng nhập.

**Xác nhận bằng chính dữ liệu locale `vi_VN` thật của glibc** (tải
`localedata/locales/vi_VN` từ `github.com/bminor/glibc`, nhánh `master`,
11/11/2026) — 3 khối liên quan khớp CHÍNH XÁC với ví dụ VN-4 yêu cầu:

| Khối glibc | Khoá | Giá trị thật | Kết quả hiển thị |
| --- | --- | --- | --- |
| `LC_MONETARY` | `currency_symbol` | `₫` | |
| `LC_MONETARY` | `mon_thousands_sep` / `mon_decimal_point` | `.` / `,` | |
| `LC_MONETARY` | `frac_digits` / `int_frac_digits` | `0` / `0` | → **`1.234.567₫`** (đúng ví dụ VN-4, không có số lẻ) |
| `LC_NUMERIC` | `decimal_point` / `thousands_sep` | `,` / `.` | → **`1.234,56`** (đúng ví dụ VN-4) |
| `LC_TIME` | `d_fmt` | `%d/%m/%Y` | → **`25/12/2026`** (đúng ví dụ VN-4, dd/mm/yyyy) |
| `LC_TIME` | `first_weekday` | `2` (Thứ Hai) | → tuần bắt đầu **Thứ Hai** (đúng yêu cầu VN-4) |

**Plasma (`etc/skel/.config/plasma-localerc`)**: chỉ có `[Formats]
LANG=vi_VN.UTF-8`, không có khoá `LC_*` riêng — theo đúng cơ chế trên, nghĩa
là "dùng `LANG` cho mọi phân loại định dạng", tức Plasma/Qt áp dụng cùng
format `vi_VN` ở trên cho mọi app KDE. **Không cần sửa file này.**

**Calamares (`etc/calamares/modules/locale.conf`)**: chỉ ghim `region`/`zone`
= `Asia/Ho_Chi_Minh` (điểm neo múi giờ, KHÔNG liên quan định dạng số/tiền/
ngày — đó là module `locale` của Calamares riêng cho timezone, không phải
locale ngôn ngữ). Không liên quan phạm vi VN-4 mục định dạng, không sửa.

**=> Quyết định: KHÔNG tạo hook mới `0312-vn-formats.hook.chroot`.** Cơ chế
hiện có (`LANG` + fallback POSIX cho `LC_MONETARY` + `LC_TIME`/`LC_NUMERIC`
tường minh) đã đạt đúng mục tiêu VN-4, có xác nhận bằng dữ liệu locale thật.
Thêm một hook thứ hai gọi lại `update-locale` sẽ không thay đổi kết quả (vô
hại nhưng vô nghĩa) và tăng rủi ro chạy hook theo thứ tự không như kỳ vọng
— đúng tinh thần "nếu 0100 đã đủ, chỉ ghi lại, không sửa thêm rủi ro" đã
được giao cho wave này.

## 4. LibreOffice — lớp registry mới `namios-vi.xcu`

File mới `usr/lib/libreoffice/share/registry/data/namios-vi.xcu` (KHÔNG sửa
`registrymodifications-system-wide.xcu` cạnh nó — file đó thuộc wave khác,
phím tắt Excel/Word) đặt:

| # | Khoá registry | Giá trị | Tác dụng |
| --- | --- | --- | --- |
| 1 | `org.openoffice.Office.Linguistic/General/DefaultLocale` | `vi-VN` | Ngôn ngữ văn bản mặc định (Western) cho tài liệu MỚI = Vietnamese (Vietnam) — điều kiện để `hunspell-vi` được gọi tự động |
| 2 | `org.openoffice.Office.Linguistic/SpellChecking/IsSpellAuto` | `true` | "Check spelling as you type" — khớp mặc định upstream, ghi tường minh theo yêu cầu "bật mặc định" của VN-4 |

Cả hai khoá xác nhận bằng schema thật
(`officecfg/registry/schema/org/openoffice/Office/Linguistic.xcs`,
`github.com/LibreOffice/core`, nhánh `master`), không suy đoán `oor:path`.
Dùng `oor:op="fuse"` (không `"replace"`) — chỉ đặt giá trị MẶC ĐỊNH, hồ sơ cá
nhân của người dùng (nạp sau, ưu tiên cao hơn) luôn thắng nếu họ tự đổi ngôn
ngữ trong Tools > Options. Không đụng `DefaultLocale_CJK/_CTL` (không liên
quan — tiếng Việt là chữ Latin) và không đụng `UILocale` (cố ý: khoá đó là
ngôn ngữ GIAO DIỆN, không phải ngôn ngữ chính tả — đặt cứng `UILocale=vi-VN`
ở layer system-wide sẽ phá thiết kế đã chốt "đổi tiếng Anh 1-click qua
System Settings, không cần cài lại gì" của NaMiOS).

## 5. Phải boot-test (CHƯA xác nhận trên máy thật)

1. Tạo hồ sơ user MỚI (chưa từng mở LibreOffice) → mở NaMiWriter → Tools >
   Options > General > Languages and Locales → mục "Western" phải hiện
   **"Vietnamese (Vietnam)"**, không phải "English (USA)".
2. Gõ một từ tiếng Việt **cố ý sai dấu/sai chính tả** vào văn bản mới → phải
   thấy **gạch đỏ**. Nếu KHÔNG thấy, kiểm theo thứ tự: (a) `hunspell-vi` đã
   cài đúng chưa (`dpkg -l hunspell-vi`), (b) mục 1 ở trên có đúng
   "Vietnamese (Vietnam)" không (nếu sai → lớp `namios-vi.xcu` không được
   nạp, xem câu hỏi mở (3) ở dưới), (c) "Check spelling as you type" có tích
   không (Tools > Options > ... > Writing Aids, hoặc icon chữ ABC gạch chân
   trên toolbar).
3. **Câu hỏi mở CHƯA có câu trả lời thật** (kế thừa từ file
   `registrymodifications-system-wide.xcu` đã tự nêu trước wave này): gói
   Debian `libreoffice` 25.2.3 trên trixie có THỰC SỰ tạo + nạp mọi `*.xcu`
   trong `share/registry/data/` hay không. **Nếu boot-test cho thấy KHÔNG
   được nạp**: lớp `namios-vi.xcu` này vô hiệu, và 2 khoá ở mục 4 cần được
   thêm vào `etc/skel/.config/libreoffice/4/user/registrymodifications.xcu`
   (file ĐÃ xác nhận chạy thật qua các wave trước) — **CHƯA làm trong wave
   VN-4 này** vì file đó thuộc phạm vi/chủ sở hữu khác, cần duyệt riêng
   trước khi sửa, không tự ý đụng vào.
4. Mở NaMiMail (Thunderbird) → soạn thư mới, gõ sai chính tả tiếng Việt →
   xác nhận gạch đỏ hoạt động (đường độc lập, không qua `namios-vi.xcu` —
   Thunderbird tự chọn dictionary theo ngôn ngữ UI/hệ thống, không qua lớp
   registry LibreOffice).
5. Mở terminal với user mới → `locale` → xác nhận `LC_MONETARY=vi_VN.UTF-8`
   hiện ra ĐÚNG như phân tích ở mục 3 (fallback từ `LANG`, không phải để
   trống).

## 6. Chưa làm / để lại có chủ đích (không bịa, không làm nửa vời)

- **Bảng tự sửa "quen tay" (autocorrect VN, ví dụ "ko" → "không")**: VN-4
  ghi rõ đây là tính năng **tuỳ chọn, mặc định TẮT**. Xây một bảng
  `DocumentList.xml` autocorrect tiếng Việt đúng chuẩn (đúng schema XML của
  LibreOffice `AutoCorrect`, đúng nội dung viết tắt phổ biến, không bịa từ)
  là một khối công việc nội dung riêng, NGOÀI phạm vi 4 file được giao cho
  wave này (chỉ gồm 1 package-list + 1 layer registry + 1 doc). **Để lại cho
  wave sau**, không tự ý mở rộng phạm vi.
- **Thesaurus/hyphenation tiếng Việt**: xác nhận KHÔNG có gói nào trong
  Debian 13 trixie main — ghi `unknown`, không tìm gói ngoài repo chính thức
  để thay (đúng nguyên tắc "không thêm phần mềm ngoài repo chính thức" đã
  áp dụng nhất quán trong toàn repo này, ví dụ mục NaMiNotes ở
  `0405-mail-notes.list.chroot`).
- **Không build `lb build` + không boot QEMU** trong wave này (môi trường
  soạn file không có `lb`/`debootstrap`/`qemu`/`/dev/kvm` — xem ADR 0002).
  Mọi "CÓ THẬT"/"KHÔNG CÓ" ở trên là xác nhận qua **package index thật** +
  **mã nguồn thật** (LibreOffice + glibc), KHÔNG phải qua `apt-cache show`
  trên build host trixie thật — vẫn cần chạy lại `apt-cache show hunspell-vi`
  trên build host thật trước `lb build` theo đúng quy ước các file khác
  trong repo này.
