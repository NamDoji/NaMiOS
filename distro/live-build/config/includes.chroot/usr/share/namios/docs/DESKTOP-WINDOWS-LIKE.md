# NaMiOS — Desktop/taskbar kiểu Windows (DESKTOP-WINDOWS-LIKE)

- **Wave:** "Windows desktop feel" cho người dùng ít rành kỹ thuật (11/11/2026).
- **Phạm vi file được giao sửa:** `etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc`,
  `etc/skel/Desktop/**`, và `etc/skel/.config/kwinrc` (chỉ nếu bắt buộc — wave
  này **không cần** đụng `kwinrc`, xem mục 4).
- **verified_on_host: NO cho TOÀN BỘ file này.** Môi trường soạn việc này là
  container headless, không có desktop session KDE Plasma thật (xem ADR 0011 +
  `docs/_m0_inventory_raw.md`) và **không có truy cập Internet** trong phiên
  làm việc này để đối chiếu trực tiếp mã nguồn KDE như các wave trước đã làm —
  điều này được ghi rõ trung thực ở từng mục, không giấu.

## 0. Tóm tắt 4 yêu cầu và trạng thái

| # | Yêu cầu | Trạng thái | Việc đã làm trong wave này |
| --- | --- | --- | --- |
| 1 | Nút Start kiểu Windows: Kickoff ở đầu TRÁI panel, hiện logo NaMiOS (không phải icon KDE chung) | **ĐÃ ĐẠT TỪ TRƯỚC** — chỉ sửa 1 comment lỗi thời | Không đổi hành vi; sửa lại comment sai sự thật ở đầu `appletsrc` (mục 1) |
| 2 | Icon taskbar to/lệch tỉ lệ → giảm độ dày panel + icon cho cân đối | Đã thêm cấu hình, **mức tin cậy TRUNG BÌNH** (chưa đối chiếu mã nguồn được) | Thêm `[PlasmaViews][Panel 1]` + `[PlasmaViews][Panel 1][Defaults]` `thickness=36` (mục 2) |
| 3 | Icon Desktop kiểu Windows: "Máy tính của tôi", "Tài liệu của tôi", "Thùng rác" | **MỚI LÀM XONG** trong wave này | 3 file `.desktop` ở `etc/skel/Desktop/` (mục 3) |
| 4 | Chuột-phải desktop → Refresh (F5) | **ĐÃ ĐẠT TỪ TRƯỚC** (wave 10/11/2026, xem `WINDOWS-HABITS.md`) | Không đổi gì — xác nhận lại, không làm trùng |

## 1. Nút Start (Kickoff) — đã đạt từ trước, chỉ sửa tài liệu sai

Đọc kỹ `[Containments][1]` (panel) trong `appletsrc`:

```ini
[Containments][1][General]
AppletOrder=2;3;4;5
```

Applet số 2 (`[Containments][1][Applets][2]`, `plugin=org.kde.plasma.kickoff`)
đứng **ĐẦU TIÊN** trong `AppletOrder` — với panel `location=4` (BottomEdge,
ngang), applet đầu danh sách hiển thị **ở đầu trái** của panel. Đây đã đúng
yêu cầu "Start ở đầu trái", không cần sửa.

Về icon: `[Containments][1][Applets][2][Configuration][General]` có
`icon=start-here-namios`. Comment ở đầu file (viết từ 03/11/2026, commit
`8c3a7e07`) nói icon này "CHƯA CÓ, chỉ là placeholder, xem
`README-PLACEHOLDER.md`" — **nhưng đó là thông tin ĐÃ LỖI THỜI**: đối chiếu
git log, icon PNG thật `start-here-namios` (logo hoa sen squircle NaMiOS) đã
được đóng gói từ commit `6060979` ("logo chính thức 'Sen bừng sáng' vào OS"),
tại:

```
usr/share/icons/hicolor/{16,32,48,64,128,256,512}x*/apps/start-here-namios.png
usr/share/icons/NaMiOS-Lotus/{48,64,128,256,512}x*/apps/start-here-namios.png
```

và `etc/skel/.config/kdeglobals` đã có `[Icons] Theme=NaMiOS-Lotus` làm theme
icon mặc định. `README-PLACEHOLDER.md` mà comment cũ trích dẫn **đã bị xoá**
khỏi repo (xác nhận bằng `find`, không còn tồn tại). Đã xem trực tiếp file PNG
128×128 bằng mắt: đúng là logo hoa sen đỏ-vàng squircle của NaMiOS, không phải
icon KDE chung chung.

**Việc đã làm:** sửa lại đúng 3 dòng comment (dòng 14-16 cũ) ở đầu `appletsrc`
cho khớp sự thật hiện tại — **không đổi bất kỳ giá trị key nào** (`icon=`,
`AppletOrder=` giữ nguyên, vì đã đúng từ trước).

## 2. Panel mỏng lại + icon taskbar cân đối (mức tin cậy TRUNG BÌNH)

### 2.1 Vì sao không có khoá "icon size" riêng cho Task Manager

Đã đọc lại `usr/local/bin/namios-panel-polish.sh` (proposal CHƯA GHÉP của wave
trước, ngoài phạm vi sửa của wave này) — phần "GHI CHÚ TRUNG THỰC" cuối file
đã xác nhận, trích thảo luận chính thức `discuss.kde.org` ("Please add zoom
effect for icon only task manager"): đội Plasma **chủ động không có ý định**
thêm cấu hình kích thước icon riêng cho applet `org.kde.plasma.icontasks` đang
dùng ở `[Containments][1][Applets][3]`. Táng tự, Kickoff và System Tray cũng
không có khoá kích thước icon độc lập — cả 3 đều tự co giãn theo **độ dày
(thickness)** của panel chứa chúng. Kết luận: giảm thickness panel là đòn bẩy
DUY NHẤT để thu nhỏ icon, không phải chuyện đổi applet hay thêm khoá icon
riêng.

### 2.2 Khoá đã thêm

```ini
[PlasmaViews][Panel 1]
thickness=36

[PlasmaViews][Panel 1][Defaults]
thickness=36
```

- `"Panel 1"` dùng số **1** vì đó chính là ID containment của panel TRONG FILE
  NÀY (`[Containments][1] plugin=org.kde.panel`) — nhiều ví dụ lưu hành trên
  mạng ghi `"Panel 2"` chỉ vì panel ở MÁY HỌ tình cờ có containment ID=2; copy
  nguyên số đó sang NaMiOS sẽ sai vì panel NaMiOS là ID=1.
- Ghi cả 2 dạng lồng ghép (`[Panel 1]` trực tiếp và `[Panel 1][Defaults]`) vì
  không chắc phiên bản Plasma 6 đóng gói trong Debian 13 trixie dùng dạng nào
  — thừa một dạng thì vô hại (KConfig bỏ qua key/group không nhận ra), không
  phải xung đột.
- `36` (px) chọn nhỏ hơn mức "Medium" mặc định của Plasma (~44px) nhưng không
  nhỏ tới mức khó bấm, nhắm tới mật độ hình ảnh gần Windows 10/11 (taskbar
  Windows ~40-48px tuỳ scale, nhưng vùng icon thực tế hiển thị mỏng hơn do lề).

### 2.3 Thành thật về mức tin cậy

**Đây là khối có mức tin cậy THẤP NHẤT trong toàn bộ `appletsrc`** so với các
khối khác (vốn trích dẫn trực tiếp mã nguồn KDE đã đọc qua `invent.kde.org`).
Phiên làm việc này **không có Internet** để đối chiếu `panel-workspace.git
shell/panelview.cpp` như các wave trước đã làm cho những khối khác — khoá
`thickness` dưới `[PlasmaViews][Panel N]` được soạn từ kiến thức nền về cấu
trúc Plasma Shell, **chưa được xác minh lại bằng mã nguồn trong phiên này**.

**Fail-safe nếu sai:** KConfig (cơ chế đọc file ini này của mọi app KDE) bỏ qua
im lặng mọi group/khoá không nhận ra — nếu tên group không đúng, panel đơn
giản giữ nguyên độ dày mặc định hiện tại (to như bây giờ), **không hỏng,
không crash, không mất applet nào**.

**Đường lui thủ công (CHẮC CHẮN hoạt động bất kể khoá trên đúng hay sai):**
chuột-phải panel → "Enter Edit Mode" (hoặc bấm nút cấu hình nổi lên ở panel) →
kéo cạnh panel bằng chuột để chỉnh độ dày trực tiếp. Đây là tính năng gốc của
Plasma, không phụ thuộc file này.

## 3. Icon Desktop kiểu Windows — mới làm trong wave này

Tạo 3 file tại `etc/skel/Desktop/` (thư mục này **chưa tồn tại trước wave
này**, đã tạo mới):

| File | Type | Name | Đích | Icon |
| --- | --- | --- | --- | --- |
| `may-tinh-cua-toi.desktop` | Link | Máy tính của tôi / This PC | `URL=computer:/` | `computer` |
| `tai-lieu-cua-toi.desktop` | Application | Tài liệu của tôi / My Documents | xem mục 3.2 | `folder-documents` |
| `thung-rac.desktop` | Link | Thùng rác / Trash | `URL=trash:/` | `user-trash` |

### 3.1 "Máy tính của tôi" + "Thùng rác" — Type=Link, không cần Exec

Cả hai dùng KIO protocol **không phụ thuộc đường dẫn user cụ thể**
(`computer:/` và `trash:/` tự động trỏ đúng máy/thùng rác của user đang đăng
nhập, bất kể `/etc/skel` bị copy y nguyên cho mọi user mới — đây chính là lý
do 2 icon này AN TOÀN để làm bằng file tĩnh, như `WINDOWS-HABITS.md` mục 4 đã
từng ghi nhận cho riêng "Thùng rác"). `Type=Link` (không có `Exec=`) nên
**không** bị Plasma Folder View chặn bằng cảnh báo "file không đáng tin cậy"
(cảnh báo đó chỉ áp dụng cho `Type=Application`/`Exec=`).

`computer:/` cần gói cung cấp KIO slave `kio_computer` (thường đi kèm
`kio-extras`, thường được `task-kde-desktop`/`dolphin` kéo theo transitive –
**chưa xác nhận bằng `dpkg -l` trên máy build thật**, giống hệt tình trạng
`plasma-systemmonitor` mà `UX-WINDOWS-FAMILIAR.md` đã ghi nhận). Nếu thiếu,
double-click sẽ hiện lỗi "giao thức không hỗ trợ" trong Dolphin — **không
crash**, chỉ icon đó không mở được, cần kiểm `apt-cache show kio-extras`.

### 3.2 "Tài liệu của tôi" — vì sao KHÔNG dùng Type=Link, và cách giải bài toán "$HOME tĩnh"

Wave trước (`WINDOWS-HABITS.md` mục 4, `UX-WINDOWS-FAMILIAR.md` mục 6) đã né
tạo icon "This PC"/Home trên Desktop vì **`/etc/skel` bị copy NGUYÊN VĂN**
sang `$HOME` của user mới — một `Type=Link URL=file:///home/<user>/...` ghi
cứng path sẽ **SAI** cho mọi user thật (tên user khác nhau). Đây là lý do kỹ
thuật ĐÚNG, nhưng áp dụng cho `Type=Link` — không áp dụng cho `Type=Application`
với `Exec=` được **bọc trong một shell**, vì `$HOME` trong đó được **shell của
chính người dùng đang đăng nhập giãn (expand) lúc double-click chạy thật**,
không phải lúc đóng gói ISO. Đây là cách giải quyết đúng bài toán mà wave
trước để ngỏ.

Nội dung `Exec=` thật trong file (đã escape đúng cú pháp Desktop Entry
Specification — xem mục 3.3 để biết cách đã kiểm tra):

```
Exec=sh -c "d=\"\$HOME/Tài liệu\"; [ -d \"\$d\" ] || d=\"\$HOME/Documents\"; [ -d \"\$d\" ] || d=\"\$HOME\"; dolphin \"\$d\""
```

Sau khi trình phân tích cú pháp Desktop Entry giải-escape, lệnh shell THẬT sự
chạy lúc double-click là:

```sh
d="$HOME/Tài liệu"; [ -d "$d" ] || d="$HOME/Documents"; [ -d "$d" ] || d="$HOME"; dolphin "$d"
```

Logic: thử thư mục tên **"Tài liệu"** trước (khớp với `etc/skel/Tài liệu/`
đã có sẵn trong repo từ trước — một wave khác đã giả định xdg-user-dirs sẽ
tạo thư mục Documents với tên tiếng Việt "Tài liệu" cho locale `vi_VN`, file
này ĐI THEO đúng giả định đó cho nhất quán) → nếu không có, thử "Documents"
(tên mặc định tiếng Anh, phòng trường hợp xdg-user-dirs không dịch) → nếu vẫn
không có, mở thẳng `$HOME` (không bao giờ "chết", luôn mở được một thứ gì đó
hợp lý).

**Quyền thực thi:** đã `chmod 755` file này (khác 2 file Link kia giữ `644`) —
vì Plasma Folder View áp cảnh báo "file không tin cậy, bấm để tin cậy và
chạy" cho MỌI file `Type=Application`/có `Exec=` KHÔNG có bit thực thi; đặt
sẵn bit `+x` trong `/etc/skel` giúp user mới mở được ngay, không cần bấm xác
nhận lần đầu. **verified_on_host: NO** — đây là hiểu biết chung về cơ chế tin
cậy của KDE, chưa xác nhận lại hành vi chính xác trên Plasma 6/Debian 13
trixie thật; nếu cảnh báo vẫn hiện, user chỉ cần bấm "Tin cậy & Chạy" một lần
duy nhất (không mất chức năng, chỉ thêm một cú click lần đầu).

### 3.3 Đã kiểm tra cú pháp Exec= bằng cách nào (trong phiên làm việc này, không phải trên Plasma thật)

Vì không có desktop Plasma thật để bấm thử, đã viết một trình tokenizer Python
mô phỏng ĐÚNG văn phạm "Exec key" của Desktop Entry Specification (tách
argument theo dấu cách ngoài ngoặc kép; bên trong ngoặc kép chỉ `\"`, `` \` ``,
`\$`, `\\` là escape) để giải mã dòng `Exec=` thật trong file thành `argv`, rồi
**chạy argv đó thật sự bằng `subprocess.run`** (thay `dolphin` bằng `echo` để
không cần Dolphin) với 3 kịch bản `$HOME` khác nhau (không có thư mục nào /
chỉ có "Tài liệu" / chỉ có "Documents") — cả 3 case đều ra đúng thư mục mong
đợi. Đây là cách xác minh **cú pháp + logic shell đúng 100%** (độc lập với
KDE) — phần CHƯA xác minh được là hành vi Plasma Folder View thật khi
double-click (ví dụ cảnh báo tin cậy ở mục 3.2).

## 4. F5 / chuột-phải → Refresh — đã đạt từ trước, không làm lại

`WINDOWS-HABITS.md` (wave 10/11/2026) đã nghiên cứu kỹ và kết luận: F5 trên
Desktop **đã hoạt động** nhờ `[Containments][2][General] url=desktop:/`
(Folder View, đã có từ trước, không đổi ở wave này) kết hợp hành vi gốc của
`foldermodel.cpp` (action "Refresh Desktop" có sẵn, shortcut `F5` gắn cứng ở
tầng Qt `WindowShortcut`). Không có khoá nào ở `kwinrc` liên quan tới F5/
refresh — **wave này không đụng `kwinrc`**, đúng như khuyến cáo "chỉ sửa nếu
bắt buộc" của đặc tả. Xem `WINDOWS-HABITS.md` mục 2 để biết chi tiết + trích
dẫn mã nguồn đầy đủ.

## 5. Checklist xác nhận trên máy thật (điền khi có desktop, KHÔNG tự đánh dấu trước)

### Mục 1 — Start button
- [ ] Panel ở đáy màn hình, nút Start (Kickoff) nằm **ở đầu trái**
- [ ] Icon nút Start hiện **logo hoa sen NaMiOS** (đỏ/vàng, squircle) — KHÔNG
      phải icon bánh răng/K chung chung của KDE

### Mục 2 — Panel mỏng + icon cân đối
- [ ] Panel mỏng hơn so với bản build trước (so sánh ảnh chụp cũ nếu có)
- [ ] Icon Task Manager/System Tray/đồng hồ trông cân đối, không to lấn hết
      chiều cao màn hình
- [ ] Nếu KHÔNG đổi gì sau khi đăng nhập: xác nhận khoá `thickness` không ăn
      (ghi lại), rồi dùng đường lui thủ công (Enter Edit Mode → kéo cạnh
      panel) để đạt yêu cầu, và báo lại để sửa khoá đúng ở build sau

### Mục 3 — Icon Desktop
- [ ] Desktop hiện đủ 3 icon: "Máy tính của tôi", "Tài liệu của tôi", "Thùng
      rác" (cùng các icon file/folder khác nếu có trong `~/Desktop`)
- [ ] Double-click "Máy tính của tôi" → Dolphin mở ở `computer:/` (nếu lỗi
      "giao thức không hỗ trợ": chạy `apt-cache show kio-extras` và
      `dpkg -l | grep kio-extras` để xác nhận gói có cài không)
- [ ] Double-click "Tài liệu của tôi" → Dolphin mở đúng thư mục Tài liệu/
      Documents thật của user (không phải thư mục trống/lỗi); nếu Plasma hiện
      cảnh báo "file không tin cậy" lần đầu, bấm "Tin cậy & Chạy" rồi xác nhận
      lần sau không hỏi lại
- [ ] Double-click "Thùng rác" → Dolphin mở `trash:/`, xoá 1 file thử nghiệm
      rồi xác nhận file đó xuất hiện trong `trash:/`

### Mục 4 — F5 Refresh (đã nghiên cứu ở wave trước, xác nhận lại 1 lần)
- [ ] Click vùng trống desktop, bấm F5 → icon desktop tải lại
- [ ] Chuột-phải desktop → menu có mục "Refresh Desktop" / "Làm mới"

## 6. Rollback nhanh (nếu một phần wave này gây lỗi)

- **Icon Start/comment (mục 1):** chỉ là comment, không có key nào đổi — không
  cần rollback, không ảnh hưởng hành vi.
- **Panel thickness (mục 2):** xoá 2 group `[PlasmaViews][Panel 1]` và
  `[PlasmaViews][Panel 1][Defaults]` ở cuối `appletsrc` — panel rơi về độ dày
  mặc định như trước wave này.
- **Icon Desktop (mục 3):** xoá thư mục `etc/skel/Desktop/` — user mới sẽ
  không có 3 icon này nữa (không ảnh hưởng icon file/folder thật khác, vì
  Folder View tự quét `~/Desktop` của user, không phụ thuộc 3 file này tồn
  tại hay không).
