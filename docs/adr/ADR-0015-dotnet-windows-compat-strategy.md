# ADR 0015 — Chiến lược tương thích .NET và ứng dụng Windows (U13-09)

- **Trạng thái:** proposed · **Mức thực thi:** `specified` (chưa app nào chạy thật trên máy/phần cứng thật → chưa `partial`, chưa `completed`).
- **Ngày:** 09/11/2026
- **Năng lực:** Phụ lục 13 — **U13-09 "Bộ chọn tuyến app Windows"** (P1).
  Cửa kiểm chứng (nguyên văn): *"App .NET mở GUI nhưng không in/ký được phải là partial hoặc blocked, không gắn ready."*
- **Liên quan:** ADR 0001 (chọn Linux + Wine), ADR 0002 (nền Debian 13 trixie), ADR 0005 (tách chế độ ứng dụng native/web/Wine), ADR 0008 (chứng nhận theo tác vụ), U13-05 (phân loại native/web/Wine ở App Center), U13-10 (Wine capsule cô lập — **engineer khác** làm phần runner), U13-11 (công cụ chuyển từ Windows).
- **Đặc tả tuyến + schema hồ sơ:** `docs/specs/COMPAT-ROUTING.md`.
- **Gói cài:** `distro/live-build/config/package-lists/0660-dotnet-compat.list.chroot`.
- **Công cụ gợi ý tuyến:** `distro/live-build/config/includes.chroot/usr/local/bin/namios-compat-assessor`.

## Bối cảnh

Chủ dự án yêu cầu rõ: NaMiOS phải chạy được **ứng dụng ".NET Framework của Microsoft"** phổ biến ở Việt Nam (kế toán, hóa đơn, công cụ nghiệp vụ). Để quyết định trung thực, ADR này phải mã hoá một sự thật kỹ thuật thường bị lẫn lộn: **có HAI thế giới ".NET" khác hẳn nhau.**

### Hai thế giới ".NET" (phải phân biệt, không được gộp)

1. **.NET hiện đại — ".NET" (Core / 5 / 6 / 7 / 8, "cross-platform")**
   - Đa nền tảng **ngay từ thiết kế**, chạy **NATIVE trên Linux** qua runtime `dotnet` (gói `dotnet-runtime-8.0`, `aspnetcore-runtime-8.0`). **Không cần Wine, không cần Windows.**
   - Thường gặp ở phần mềm VN **mới** + dịch vụ ASP.NET (web backend). Nhận diện: cạnh file `App.exe` có `App.dll` + `App.runtimeconfig.json` / `App.deps.json`.
   - → Tuyến khuyến nghị: **`dotnet-native`**. Đây là trường hợp **tốt nhất**: chạy như một app Linux bình thường.

2. **.NET Framework cổ điển (1.0 → 4.8) — "của Microsoft", Windows-only**
   - Microsoft **chỉ** phát hành .NET Framework cho **Windows**. Nó **không** có bản Linux chính thức. Đây chính là loại mà phần lớn phần mềm nghiệp vụ VN đời cũ (WinForms/WPF) dựa vào.
   - Chạy trên Linux bằng **một trong hai** lớp tương thích, **theo từng app**:
     - **Mono** — bản hiện thực mã nguồn mở của .NET Framework (gói `mono-complete`). Chạy **native trên Linux, KHÔNG cần Wine**, hợp với app **console + WinForms** mức vừa. **Giới hạn thật:** Mono **không hỗ trợ WPF** (`PresentationFramework`/`WindowsBase`/`System.Xaml`), một số API Framework đời mới + nhiều `P/Invoke` vào DLL Win32 **không có** → app gọi tới sẽ lỗi. → Tuyến **`mono`**.
     - **Wine + wine-mono** — chạy app **trong môi trường Windows mô phỏng của Wine**; `wine-mono` thay cho .NET Framework bên trong prefix. Dùng khi app cần hành vi Windows thật hơn (WPF, tích hợp Win32 sâu). Nếu `wine-mono` chưa đủ, có thể cài **bản .NET Framework redistributable thật của Microsoft** vào prefix qua `winetricks` (ví dụ `dotnet48`) — nhưng **nặng, dễ vỡ, phải pin + retest theo hash**. → Tuyến **`wine`** (app Win32 thuần) hoặc **`wine+dotnet-framework`** (app .NET Framework cần Wine).

### Vì sao Wine KHÔNG phải là Windows (và KHÔNG biến driver Windows thành driver Linux)

Wine là **lớp tương thích** dịch lời gọi **API Windows ở mức user-space** sang tương đương Linux — nó **không** chạy một bản Windows bên dưới và **không** nạp driver kernel-mode `.sys` của Windows [2]. Mọi truy cập phần cứng vẫn đi qua **driver Linux**. Hệ quả **không thể quảng cáo khác đi**:

- **USB token / chữ ký số (CA, ký số thuế/hóa đơn/BHXH):** cần **driver + middleware Windows của nhà cung cấp** (CSP/minidriver cắm vào CryptoAPI). Wine **không** cung cấp driver kernel này → token thường **không ký được**, dù GUI app mở ra. Đây là ca `blocked` điển hình cho tới khi có đường PKCS#11/PC-SC + middleware Linux **được vendor hỗ trợ**.
- **Máy in nghiệp vụ / in hóa đơn:** Wine đẩy in qua **CUPS của host**; app đóng gói driver in Windows riêng hoặc cần tính năng driver đặc thù (máy in nhiệt, khổ hóa đơn) có thể **in thiếu/sai**. "Mở được hộp thoại In" **không** chứng minh "in ra tờ đúng".
- **Tích hợp Win32/kernel sâu, antivirus, công cụ chạm trực tiếp phần cứng:** nằm ngoài khả năng Wine.
- **WPF trên Mono:** không hỗ trợ (phải qua Wine).

**→ Quy tắc vàng, mã hoá vào cả schema lẫn công cụ:** *GUI mở ra* **≠** *app chạy được*. Nếu công việc thật (in / ký số / kết nối thiết bị / đẩy dữ liệu) chưa chứng minh được trên **máy + phần cứng thật**, verdict **chỉ** được là `partial` hoặc `blocked`, **tuyệt đối không `ready`**.

## Các phương án đã cân nhắc (cho .NET Framework "của Microsoft")

| Phương án | Ưu | Nhược / rủi ro | Quyết định alpha |
| --- | --- | --- | --- |
| **Mono native** (`mono-complete`) | Không cần Wine; nhẹ; chạy như app Linux; hợp console + WinForms | Không WPF; thiếu một số API Framework mới + P/Invoke Win32 | **Ưu tiên thử TRƯỚC** cho app .NET Framework |
| **Wine + wine-mono** | Hành vi Windows sát hơn; chạy WPF/Win32 ở mức nhất định | Nặng, theo-app, dễ vỡ theo version; vẫn không có driver kernel | **Thử sau Mono**, chỉ khi Mono không đạt |
| **Wine + .NET Framework thật (winetricks dotnet48)** | Khớp Framework của Microsoft nhất | Cài rất dễ hỏng, phải pin + retest theo hash; chậm; license redistributable | **Chỉ dùng khi bắt buộc**, ghi rõ trong recipe |
| **Chạy Windows thật trong VM (KVM/QEMU) cho app bất trị** | Tương thích cao nhất | Cần **license Windows hợp pháp** + tài nguyên; ngoài phạm vi "chạy trên NaMiOS" | **Tham khảo**, không chọn cho alpha; để ngỏ cho U13-13 theo vendor |

## Quyết định (cho bản alpha)

1. **Thứ tự ưu tiên tuyến (cheapest-safest-first):**
   `native` → `web` → `dotnet-native` → `mono` → `wine` → `wine+dotnet-framework` → `blocked`.
   Luôn thử tuyến **rẻ và an toàn hơn trước**; chỉ xuống Wine khi các tuyến trên không đạt. Chi tiết cây quyết định + schema: `docs/specs/COMPAT-ROUTING.md`.
2. **Cài nền tảng cả ba runtime tương thích** (để tuyến nào cũng thử được), qua `0660-dotnet-compat.list.chroot`: `mono-complete`, (tùy chọn) `dotnet-runtime-8.0`/`aspnetcore-runtime-8.0`, `wine` + `winetricks` + `winbind` + `wine-binfmt`.
   - **Runtime .NET hiện đại của Microsoft:** nếu trixie đã đóng gói `dotnet-runtime-8.0`/`aspnetcore-runtime-8.0` thì dùng gói distro; **nếu không**, lấy từ **apt repo của Microsoft (`packages.microsoft.com`) như một lựa chọn hậu-cài** — **KHÔNG** nhúng repo bên thứ ba vào ISO ở alpha nếu chưa có ADR nguồn-gói riêng (xem ADR 0007 về nguồn/ký cập nhật).
3. **Công cụ gợi ý tuyến `namios-compat-assessor`** (stub) đọc file (.exe/.msi/.dll/.deb/url) và **đề xuất** tuyến bằng heuristic rẻ (`file`, cờ PE .NET vs native, phần mở rộng). Nó **chỉ gợi ý**: verdict cuối cùng **bắt buộc** một lần chạy thật + công việc thật.
4. **Wine capsule cô lập (WINEPREFIX riêng từng app, quyền hẹp, snapshot, recipe) — KHÔNG thuộc ADR này.** Đó là U13-10, do **engineer khác** làm. ADR này chỉ: chốt chiến lược tuyến, liệt kê gói, định nghĩa schema hồ sơ, và giao công cụ assessor.

### Những gì sẽ KHÔNG chạy ở alpha (công bố trước, không giấu)

- Ký số bằng **USB token / chữ ký số** qua app Windows chạy trên Wine → mặc định **blocked** (thiếu driver + middleware kernel; xem trên) cho tới khi có đường PKCS#11/PC-SC được vendor hỗ trợ và **test ký thật đối chiếu biên nhận**.
- **In nghiệp vụ** (hóa đơn, máy in nhiệt, khổ đặc thù) qua app Wine → chưa chứng minh được = **partial/blocked**, không `ready`.
- Phần mềm **kế toán/thuế/HĐĐT/BHXH** cụ thể (MISA, các cổng ký) → **chưa** tuyên bố hỗ trợ; thuộc U13-13 theo từng vendor + có dữ liệu test + người nghiệp vụ ký duyệt.
- App .NET Framework dùng **WPF** trên **Mono** → không chạy (phải thử Wine).
- Bất kỳ app nào cần **driver phần cứng Windows** (scanner đặc thù, thiết bị đo, khóa cứng) → Wine không cấp driver kernel [2].
- **Driver máy in/thiết bị "của Windows"** không trở thành driver Linux chỉ vì Wine chạy được GUI của app [2] (Phụ lục 13 §6).

## Hệ quả

- NaMiOS có **nền tảng tương thích** (3 runtime) + **bộ chọn tuyến trung thực**, nhưng **không** đi kèm bảo đảm app Windows/.NET nào chạy được — đầu tư chỉ tiếp tục theo **bằng chứng chạy thật** (ADR 0001, Phụ lục 13 §5–6).
- Hai nhãn phải tách bạch: "tương thích trên NaMiOS (đã test app X, việc Y, model Z)" **≠** "nhà cung cấp hỗ trợ chính thức Linux".
- Mọi hồ sơ app theo schema `COMPAT-ROUTING.md`: thiếu bằng chứng công việc thật → verdict `partial`/`blocked`, không bao giờ tự nâng lên `ready`.
- Tên gói ở `0660` **phải** xác minh `apt-cache show` trên host trixie thật trước khi build (`verified_on_host: NO`).

## Điều kiện để một app lên `ready` (cửa U13-09 + M3)

Cần **máy + phần cứng thật** (chưa làm được trong QEMU/CI — xem CLAUDE.md "Môi trường build"):

1. Ghi đủ hồ sơ: **app + version + hash** của binary đã test.
2. Chạy **đúng workflow công việc thật** tới kết quả (không chỉ "mở GUI"): ví dụ xuất file đúng, **in ra tờ đúng**, **ký số ra chữ ký hợp lệ đối chiếu được**, kết nối đúng thiết bị.
3. Ghi **thiết bị phụ thuộc** (máy in model gì, token loại gì) + kết quả theo chức năng.
4. Có **QA độc lập** phê duyệt (CLAUDE.md "task_verified").

Chưa đủ 4 điều trên thì app **chỉ** được `partial` hoặc `blocked`. Không gắn "hỗ trợ Windows" cho cả một ngành chỉ từ vài app (Phụ lục 13 §3, mốc M3).

## Nguồn

- [2] WineHQ — Wine là compatibility layer dịch Windows API (không phải Windows, không nạp driver kernel): https://www.winehq.org/about/
- Microsoft — .NET (hiện đại, đa nền tảng) vs .NET Framework (Windows-only): https://learn.microsoft.com/dotnet/fundamentals/
- Mono — bản hiện thực mã nguồn mở .NET Framework (giới hạn WPF): https://www.mono-project.com/
- WineHQ — wine-mono (thay .NET Framework trong prefix): https://gitlab.winehq.org/wine/wine-mono
- Debian — đóng gói .NET/`dotnet` (xác minh `apt-cache show` trên trixie): https://packages.debian.org/
- ADR 0001 (Linux + Wine), ADR 0002 (Debian 13), ADR 0008 (chứng nhận theo tác vụ), Phụ lục 13 §6 (cổng phát hành).
