# NaMiOS — Ma trận tương thích Wine cho phần mềm Windows Việt Nam (WINE-COMPAT-MATRIX)

- **Trạng thái:** `specified` — phân tích + kỳ vọng dựa trên bằng chứng repo
  (ADR-0015, COMPAT-ROUTING.md, WINE-CAPSULE.md, DAC_TA_HE_DIEU_HANH.md,
  `catalog/services/*.json`) + kiến thức công khai về Wine/MISA/HTKK, **CHƯA
  chạy thử BẤT KỲ app nào trong danh sách dưới đây**. `verified_on_host: NO`
  cho toàn bộ file.
- **Ngày:** 2026-11-10, cập nhật 2026-11-11 (khảo sát web thật cho
  HTKK/eTax/USB token/ký số từ xa — xem ô "Cập nhật 11/11/2026" trong các
  dòng liên quan ở §2 + file chi tiết mới `docs/wine/KY-SO-PKCS11-RESEARCH.md`).
  Cập nhật này **thay thế** vài kết luận `unknown` cũ bằng kết luận cụ thể
  hơn (vẫn `specified`, chưa test thật trên máy) — KHÔNG đổi bất kỳ verdict
  nào thành `ready`.
- **Phạm vi:** lớp thân thiện U13-10 ("Chạy phần mềm Windows",
  `usr/local/bin/namios-windows-app`) — tài liệu này là phần CÒN THIẾU mà
  `ADR-0015`/`COMPAT-ROUTING.md`/`WINE-CAPSULE.md` CHƯA có: một ma trận **cụ
  thể theo tên phần mềm thật**, trả lời "nên thử cái nào trước, cái nào gần
  như chắc chắn không đáng công".
- **KHÔNG thay thế** schema hồ sơ chính thức của `COMPAT-ROUTING.md` §3 (per-
  app record với `verdict: ready|partial|blocked`, bắt buộc evidence thật).
  Tài liệu này dùng một cột RIÊNG — "Kỳ vọng trước khi test" — KHÔNG phải
  verdict chính thức, xem mục 1 dưới.

## 0. Đọc trước — vì sao owner (chủ dự án) cần đọc kỹ mục này

Chủ dự án muốn phần mềm kế toán/tài chính Việt Nam (MISA, HTKK/eTax, hóa đơn
điện tử, ký số USB token) có **cơ hội tốt nhất có thể**. Kết luận trung thực
sau khi rà toàn bộ bằng chứng đã có trong repo (không phải suy đoán mới):

> **Phần lớn khối "kế toán/thuế/ký số" sẽ KHÔNG chạy đầy đủ qua Wine ở bản
> alpha, không phải vì NaMiOS "làm chưa đủ cố gắng", mà vì Wine về kiến trúc
> không cấp driver kernel Windows** — USB token chữ ký số, in nghiệp vụ cần
> driver đặc thù, và SQL Server (MISA SME) đều cần thứ Wine không có (xem
> `docs/adr/ADR-0015-dotnet-windows-compat-strategy.md`, dẫn WineHQ [2]; và
> `WIN-008` trong `DAC_TA_HE_DIEU_HANH.md`: *"Không được giao nhiệm vụ 'bảo
> đảm 100% tương thích' như thể một mức cố gắng lập trình có thể giải quyết
> chắc chắn."*). Đây **không phải** giới hạn riêng của NaMiOS — nó đúng với
> MỌI bản Linux + Wine, kể cả các bản Linux dùng Wine đã có từ lâu.

Tin tốt: (1) một phần việc kế toán/văn phòng (xem/nhập dữ liệu thử, xem báo
cáo không cần ký) có cơ hội thật qua Wine hoặc qua web; (2) nhiều dịch vụ
VN hiện đã có đường **web** thay cho app Windows (AMIS Kế toán, eTax, Hóa
đơn điện tử tra cứu) — đường web **không cần Wine, không cần đánh giá Wine
gì cả**, và nên luôn được thử TRƯỚC (đúng thứ tự `native → web → ... → wine
→ blocked` của ADR-0015).

## 1. Vocabulary — "Kỳ vọng trước khi test" KHÔNG phải verdict chính thức

| Giá trị | Nghĩa |
| --- | --- |
| `works-likely` | Dựa trên kiến thức công khai về Wine + bản chất app, NHIỀU KHẢ NĂNG mở và dùng được phần lớn tính năng chính. |
| `partial-likely` | Phần cốt lõi (mở app, nhập/xem dữ liệu) nhiều khả năng được, nhưng MỘT bước quan trọng (in, ký số, kết nối thiết bị/DB) nhiều khả năng KHÔNG được. |
| `blocked-likely` | Nhiều khả năng không dùng được cho mục đích nghiệp vụ thật, do thiếu driver/middleware Windows hoặc phụ thuộc hạ tầng Windows (SQL Server, dịch vụ nền). |
| `unknown` | Chưa đủ dữ liệu công khai/repo để ước lượng — cần khảo sát thật trước khi đoán (ECO-005/WIN-001). |
| `not-applicable-not-wine` | Đây là web/app di động, KHÔNG phải file .exe/.msi — Wine không liên quan, đừng tốn công thử qua Wine. |

**Quy tắc bắt buộc (không được lách):** cột trên là **suy đoán có cơ sở**,
dùng để QUYẾT ĐỊNH có đáng thử hay không. Nó **không bao giờ** được dùng để
tự động gán `verdict: ready` trong hồ sơ `COMPAT-ROUTING.md` §3. Verdict
chính thức CHỈ được nâng sau khi có `workflow_tested` thật trên máy +
`qa_independent` ký duyệt (COMPAT-ROUTING.md §4; WINE-CAPSULE.md §7).

## 2. Ma trận — phần mềm/dịch vụ kế toán, thuế, bảo hiểm, hóa đơn (ưu tiên của owner)

| Phần mềm/dịch vụ | Loại | Kỳ vọng trước test | Vì sao | Cần test gì trước khi tin | Tuyến gợi ý (COMPAT-ROUTING) |
| --- | --- | --- | --- | --- | --- |
| **MISA SME** (`sme.misa.vn`) | Desktop .NET + SQL Server + USB token | `blocked-likely` (cho workflow đầy đủ: nhập liệu + báo cáo + ký nộp) | Client .NET có thể mở qua `wine+dotnet-framework`, nhưng **SQL Server** (catalog: `windows_mode: windows_vm`) không có đường Wine hợp lệ — MISA không hỗ trợ SQL Server trên Linux; chữ ký số USB token mặc định `blocked` theo ADR-0015. Xem `APP-MIS-002/003/008` (`DAC_TA_HE_DIEU_HANH.md`). | Cài thử client trong capsule riêng với dữ liệu GIẢ, kiểm GUI mở được tới đâu; **không mở dữ liệu thật** (APP-MIS-005). Nếu GUI không mở đúng → dừng, ghi `blocked`. Nếu mở được → vẫn cần DB (bản sao/test, KHÔNG sản xuất) để đi xa hơn. | `wine+dotnet-framework` (client) — **không đủ**, cần đánh giá SQL Server riêng theo `APP-MIS-002` (đề xuất: SQL Server trên VM Windows có phép, KHÔNG cài qua Wine). |
| **MISA AMIS Kế toán** (`amis.misa.vn`) | Web SaaS | `works-likely` cho duyệt/nhập liệu qua trình duyệt; `partial-likely` cho bước ký số | Là web — chạy trên Firefox ESR có sẵn, **không cần Wine** (APP-MIS-006: "không suy ra web nên tất cả chức năng chạy Linux"). Bước ký hóa đơn/báo cáo có thể cần plugin trình duyệt Windows-only. | Mở thật bằng Firefox, đăng nhập tài khoản thử, thử đúng bước cần ký — ghi lại plugin nào được yêu cầu (nếu có). | `web` — không phải việc của Wine/`namios-windows-app`. |
| **HTKK — Hỗ trợ kê khai thuế** (`gdt.gov.vn/.../hotrokekhai`) | Desktop, offline (lập tờ khai + xuất XML) | `partial-likely` cho RIÊNG bước lập tờ khai/xuất XML offline (không ký, không nộp) | **Cập nhật 11/11/2026 (xem `docs/wine/KY-SO-PKCS11-RESEARCH.md` §2 cho nguồn đầy đủ):** nhiều trang hướng dẫn cài đặt công khai (bên thứ ba, không phải tài liệu kỹ thuật chính thức `gdt.gov.vn`) hội tụ về cùng một yêu cầu hệ thống: **Windows 7 SP1+ và .NET Framework 3.5** — tức HTKK dùng **.NET Framework cổ điển (WinForms kiểu cũ)**, KHÔNG phải Java (câu hỏi "Java hay .NET" trong bản ma trận trước đã được làm rõ: không có nguồn nào nhắc tới Java cho HTKK). Vì là desktop WinForms .NET Framework thường (không có dấu hiệu dùng WPF trong các mô tả tìm được), theo cây quyết định ADR-0015 → thử `mono` TRƯỚC, hạ xuống `wine+dotnet-framework` nếu Mono không đủ. **Quan trọng:** HTKK tự nó KHÔNG ký số — việc lập/xuất XML tờ khai xảy ra offline trong HTKK, còn bước **ký + nộp** xảy ra RIÊNG trên cổng web `thuedientu.gdt.gov.vn` (xem dòng eTax dưới + `KY-SO-PKCS11-RESEARCH.md` §4) — nên verdict `partial-likely` này CHỈ áp dụng cho phần lập/xuất tờ khai, không bao giờ suy rộng ra "HTKK dùng được trọn vẹn". | Cài thử bằng preset có sẵn `includes.chroot/etc/skel/.config/namios-wine/app-presets/htkk.json` (route `mono` trước, fallback `wine+dotnet-framework` qua `dotnet35sp1`) với bộ cài HTKK thật + dữ liệu GIẢ; kiểm GUI mở, nhập một tờ khai mẫu, xuất XML, đối chiếu XML đó với bản xuất từ Windows thật (nếu có). KHÔNG thử bước ký/nộp trong capsule — bước đó không thuộc phạm vi Wine (xem mục ký số). | `mono` trước → `wine+dotnet-framework` (preset đã ship, `untested`) cho RIÊNG phần lập tờ khai; phần ký/nộp xem dòng "Ký số từ xa" trong §2 dưới. |
| **Thuế điện tử / eTax** (`thuedientu.gdt.gov.vn`) | Web (nộp tờ khai, ký số, nộp thuế) | `not-applicable-not-wine` cho phần web; `blocked-likely` cho ký qua **USB Token + plugin cũ**; `works-likely` cho ký qua **dịch vụ ký số TỪ XA** (xem cột bên) | **Cập nhật 11/11/2026** (`docs/wine/KY-SO-PKCS11-RESEARCH.md` §3-4, nguồn bên thứ ba hướng dẫn kê khai thuế): hai công cụ ký truyền thống của eTax — **"CT Signing"/TCT SigningHub** và **"eSigner Java"** (dù tên có chữ "Java", bộ cài phát hành thực tế là `eSigner_<version>_setup.exe`, kèm yêu cầu .NET Framework 4.8/4.8.1 phía Windows) — được một trang hướng dẫn pháp lý ghi rõ: **"Nếu sử dụng macOS hoặc Linux, phần mềm CT Signing không tương thích, cần chuyển sang máy Windows."** Đây là xác nhận cụ thể nhất từ trước tới giờ cho nhánh USB-Token-cũ. NHƯNG eTax **cũng** cho đăng ký loại CA "ký số **từ xa**" (VNPT SmartCA, Viettel MySign…) song song với USB Token — loại này ký qua web + app điện thoại, **không cần phần mềm Windows nào trên máy tính cả** (xem `KY-SO-PKCS11-RESEARCH.md` §4). | Mở trang thật bằng Firefox, thử đăng nhập; nếu tài khoản CA hiện tại là USB-Token-truyền-thống, xác nhận lại với kế toán/CA xem có thể đổi/đăng ký thêm "ký số từ xa" không — đó là bước quyết định thật, không phải bước kỹ thuật Wine. | `web` cho mọi thao tác không ký; ký qua USB Token cũ → `blocked`; ký qua **dịch vụ từ xa** → `web`, khuyến nghị đây là tuyến chính (xem `KY-SO-PKCS11-RESEARCH.md` §5). |
| **Ký số từ xa / Cloud signing** (VNPT SmartCA, Viettel-CA Cloud "MySign", FPT-CA tương đương `unknown`) | Dịch vụ web + app điện thoại, khóa bí mật lưu trên HSM của CA | `works-likely` — **đây là phát hiện quan trọng nhất của đợt khảo sát này** | Cơ chế: máy tính chỉ hiển thị trang web yêu cầu ký, việc ký thật xảy ra giữa server HSM của CA và app điện thoại (PIN/sinh trắc học) — **máy tính không bao giờ chạm vào khóa bí mật**, nên không liên quan Wine/PKCS11/driver USB gì cả. Xác nhận công khai: cả cổng eTax lẫn cổng BHXH đều cho chọn nhà cung cấp "ký số từ xa" khi đăng ký (`KY-SO-PKCS11-RESEARCH.md` §4, nguồn bên thứ ba + trang tích hợp `doitac-smartca.vnpt.vn`). | Mở Firefox, đăng nhập cổng thật, thử bước "chọn loại chữ ký" xem có tùy chọn ký-từ-xa không; nếu công ty/kế toán hiện CHỈ có USB Token, đây là quyết định đổi/đăng ký dịch vụ với CA — không phải việc kiểm thử kỹ thuật NaMiOS. | `web` — không phải Wine, không cần `namios-windows-app`/capsule gì cả. Xem chi tiết đầy đủ ở `docs/wine/KY-SO-PKCS11-RESEARCH.md`. |
| **iTaxViewer** (công cụ xem/đối chiếu tờ khai XML, hay đi kèm HTKK) | Desktop, Java + (bản mới) thành phần WebView2 | `blocked-likely` cho bản mới nhất | **Cập nhật 11/11/2026:** nguồn công khai (trang hướng dẫn cài đặt bên thứ ba) ghi rõ "iTaxViewer hiện chỉ hỗ trợ Windows... chưa có bản macOS", và bản mới đòi hỏi thêm **.NET Framework 4.0+ và WebView2 Runtime** (thành phần trình duyệt Microsoft Edge nhúng, **chỉ có trên Windows**, Wine không có con đường hợp lý để giả lập WebView2). Lõi Java không đủ để kết luận "chạy được qua OpenJDK" vì phần UI mới phụ thuộc WebView2. | Nếu cần, kiểm tra **bản iTaxViewer cũ hơn** (trước khi thêm WebView2, thường là bản Java thuần) xem có chạy trực tiếp bằng OpenJDK có sẵn không — **chưa thử**, không khẳng định bản cũ chạy được, chỉ là hướng đáng thử rẻ hơn Wine. | Bản mới: `blocked` (WebView2 không có đường Wine đáng tin). Bản Java thuần cũ hơn (nếu còn tải được): hướng thử `dotnet-native`-kiểu-Java tức chạy thẳng bằng OpenJDK, KHÔNG qua Wine — `unknown`, chưa test. |
| **eTax Mobile** (`canhan.gdt.gov.vn`) | App di động (Android/iOS) | `not-applicable-not-wine` | Không phải app Windows — chạy trên điện thoại, không liên quan gì tới Wine/NaMiOS desktop. | Không áp dụng cho `namios-windows-app`. | Không áp dụng. |
| **Hóa đơn điện tử — tra cứu** (`hoadondientu.gdt.gov.vn`) | Web (tra cứu công khai/đăng nhập) | `not-applicable-not-wine` (tra cứu) | Là web. | Mở bằng Firefox, thử tra cứu + đăng nhập. | `web`. |
| **Phần mềm hóa đơn điện tử bên thứ 3** (ví dụ M-Invoice, VNPT Invoice, Viettel S-Invoice, Bkav eHoaDon…) | Đa số web, một số có client Windows cho nhập/ký hàng loạt | `unknown` | **CHƯA khảo sát từng vendor** — roadmap (`§1.4`) yêu cầu khảo sát thật trước khi chốt (ECO-005/WIN-001), repo hiện KHÔNG có entry catalog riêng cho các vendor này (chỉ có `ketoan.hoadondientu` = cổng tra cứu của Tổng cục Thuế, không phải phần mềm của 4 vendor kể trên). KHÔNG suy đoán chi tiết cho từng vendor khi chưa có dữ liệu thật — tránh nói sai tên sản phẩm cụ thể. | Lấy đúng tên bản + bộ cài từ đơn vị pilot thật (WIN-001), test riêng theo app. | Chưa xác định cho tới khi khảo sát. |
| **Công cụ ký số BHXH cài cục bộ** (`bhxh.cong-cu-ky-so`, catalog) | Desktop, cầu nối trình duyệt↔USB token qua localhost | `blocked-likely` | USB token + browser-plugin-qua-localhost thường cần enumerate CSP/middleware Windows thật (APP-MIS-007: "nhánh kiểm chứng riêng theo hãng/model/driver"); Wine không cấp driver kernel cho token (ADR-0015). | Cài thử trong capsule, xác nhận có nhận diện được token cắm vào (USB qua Wine không có driver kernel — dự đoán KHÔNG nhận được thiết bị thật ngay từ bước này). | `blocked` cho tới khi có middleware Linux chính thức từ vendor. |
| **Cổng giao dịch BHXH** (`dichvucong.baohiemxahoi.gov.vn`) | Web | `not-applicable-not-wine` cho phần nộp/xem hồ sơ; `blocked-likely` cho bước ký (phụ thuộc công cụ ký số ở trên) | Web portal. | Mở bằng Firefox, thử các bước không cần ký trước. | `web`. |
| **I-VAN (ví dụ TS24/eBH `ebh.vn`, hoặc BKAV/VNPT/Viettel/MISA/EFY/Thái Sơn…)** | Đa số web, phụ thuộc vendor | `unknown` | Chỉ 1/14 nhà cung cấp I-VAN được BHXH công nhận có entry khảo sát trong catalog (`bhxh.ivan-ts24-ebh`), và entry đó cũng ghi `not_inventoried`. Không đủ dữ liệu để nói chung cho cả nhóm. | Khảo sát theo vendor cụ thể khi có pilot thật. | Chưa xác định. |
| **VNACCS/VCIS hải quan** (qua phần mềm khai báo trung gian như ECUS) | Desktop, cần VPN/mạng hải quan + chữ ký số | `blocked-likely` | Catalog NaMiOS tự gắn `windows_mode: windows_vm` cho entry này — tức đánh giá nội bộ sẵn có đã nghiêng về cần máy Windows thật, không phải Wine. Kết hợp với yêu cầu chữ ký số + kênh mạng chuyên dụng → rủi ro cao. | Nếu cần đánh giá: xác nhận phần mềm khai báo trung gian cụ thể (ECUS hay khác) + thử mở GUI trong capsule, KHÔNG dùng VPN/tài khoản hải quan thật để test. | `windows_vm` (đã ghi sẵn trong catalog) — không ưu tiên Wine cho nhóm này. |
| **USB token chữ ký số (Viettel-CA, VNPT-CA, FPT-CA, CA2, Safe-CA, …) dùng qua app Windows trong Wine** | Driver + middleware Windows | `blocked-likely` | Nguyên tắc kiến trúc ADR-0015: *"USB token/chữ ký số... cần driver + middleware Windows của nhà cung cấp (CSP/minidriver)... Wine KHÔNG cung cấp driver kernel này."* Đây là giới hạn kiến trúc, không phải "chưa làm đủ". **Cập nhật 11/11/2026 — khảo sát chi tiết theo TỪNG hãng (Viettel-CA/VNPT-CA/FPT-CA) + một công cụ cộng đồng (MacSigner, có build Linux) + tuyến ký-số-từ-xa (khả năng thật, không cần Wine) đã chuyển sang file riêng `docs/wine/KY-SO-PKCS11-RESEARCH.md` — đọc file đó trước khi kết luận "hết đường".** | **[ĐÃ KIỂM TRA CÔNG KHAI — xem `KY-SO-PKCS11-RESEARCH.md`]** Cả 3 hãng owner nêu tên đều CHƯA thấy middleware Linux chính hãng công khai (độ tin cậy trung bình, nguồn bên thứ ba — nên hỏi thẳng hotline vendor nếu cần chắc 100%). Tuyến thật đáng thử trước: **ký số từ xa** (không cần driver/Wine gì cả, xem dòng "Ký số từ xa / Cloud signing" ở mục trên). | `blocked` qua Wine (không đổi); `web` qua ký-số-từ-xa (khuyến nghị thử trước); công cụ cộng đồng MacSigner = `unverified`, không khuyến nghị cho nghiệp vụ thật. |

## 3. Ma trận — phần mềm Windows chung (không phải nghiệp vụ thuế/kế toán), để đối chiếu

| Loại app | Ví dụ | Kỳ vọng trước test | Vì sao |
| --- | --- | --- | --- |
| Win32 thuần, nhẹ, không DB/driver/in đặc thù | Notepad++ (đã có template minh họa `docs/compat/recipes/notepadplusplus-template.json`, `untested`) | `works-likely` | Đúng kiểu app Wine chạy tốt nhất trong lịch sử Wine: không cần .NET, không cần driver, không cần DB. Đây là trường hợp tốt nhất để **thử đầu tiên** trên máy thật, trước khi thử bất kỳ app kế toán nào — dùng để xác nhận chuỗi `namios-wine-capsule`/`namios-windows-app` hoạt động đúng cơ bản. |
| .NET Framework WinForms, không DB/in đặc thù | App nội bộ tự viết dạng console/WinForms đơn giản | `partial-likely`→`works-likely` | Theo `mono` trước (nhẹ hơn), hạ xuống `wine+dotnet-framework` nếu Mono không đủ (ADR-0015). |
| .NET Framework dùng WPF | — | `blocked-likely` trên `mono`, `partial-likely` trên Wine | Mono không hỗ trợ WPF (ADR-0015) — phải thử Wine, vẫn không chắc đủ. |
| App cần in hóa đơn/khổ đặc thù/máy in nhiệt | — | `blocked-likely` | Driver in đặc thù qua Wine chưa test trên phần cứng thật (roadmap §1.2); "mở được hộp thoại In" không chứng minh "in ra tờ đúng" (ADR-0015 "quy tắc vàng"). |
| App cần SQL Server/dịch vụ nền Windows | — | `blocked-likely` | Không có đường Wine hợp lệ cho SQL Server; cần máy/VM Windows riêng (`APP-MIS-002`). |

## 4. Những gì CHẮC CHẮN không claim ở bản alpha (nhắc lại từ ADR-0015, không lặp lại tranh luận)

- Ký số **USB token** qua app Windows chạy trên Wine → `blocked` mặc định.
- **In nghiệp vụ** (hóa đơn, máy in nhiệt, khổ đặc thù) qua app Wine → chưa
  chứng minh = `partial`/`blocked`, không `ready`.
- **MISA/HTKK/HĐĐT/BHXH** cụ thể → chưa tuyên bố hỗ trợ; từng app cần hồ sơ
  riêng + người nghiệp vụ ký duyệt (U13-13, P2).
- App .NET Framework dùng **WPF** trên **Mono** → không chạy.
- App cần **driver phần cứng Windows** (scanner đặc thù, thiết bị đo, khóa
  cứng ngoài USB-token đã nêu) → Wine không cấp driver kernel.

## 5. Cách tự kiểm tra một app cụ thể (quy trình, không phải lời hứa kết quả)

1. Thử tuyến RẺ HƠN trước (ADR-0015 §"Quyết định" mục 1): có web không? có
   bản native Linux/middleware Linux của vendor không? Nếu có, dùng tuyến đó
   — đừng mở Wine ra nếu không cần.
2. Nếu phải dùng Wine: dùng `namios-windows-app` (lớp thân thiện) hoặc
   `namios-wine-capsule` trực tiếp (lớp cách ly, cho người rành kỹ thuật) để
   tạo một capsule RIÊNG cho app đó — không dùng chung prefix với app khác.
3. Điền một **hồ sơ app** theo đúng schema `COMPAT-ROUTING.md` §3 — đặc
   biệt mục `workflow_tested` phải là **công việc thật** (xuất file đúng, in
   ra tờ đúng, ký ra chữ ký hợp lệ đối chiếu được), không phải "mở được GUI".
4. Theo danh sách test cần máy thật ở `docs/specs/WINE-CAPSULE.md` §7 (hai
   app không xung đột DLL, đổi hash phải retest, malware fixture không đọc
   toàn bộ home) trước khi tin cách ly đã đạt.
5. Verdict cuối (`ready|partial|blocked`) CHỈ được nâng theo quy tắc
   `COMPAT-ROUTING.md` §4 — không bao giờ tự nâng vì "mở được"/"cài xong"/
   "test trong máy ảo".

## 6. Nguồn

- `docs/adr/ADR-0015-dotnet-windows-compat-strategy.md` — chiến lược tuyến,
  dẫn WineHQ [2] cho giới hạn driver kernel.
- `docs/specs/COMPAT-ROUTING.md` — taxonomy 7 tuyến + schema hồ sơ.
- `docs/specs/WINE-CAPSULE.md` — mô hình cách ly, giới hạn đã biết (§8).
- `docs/spec-package/specs/DAC_TA_HE_DIEU_HANH.md` (`APP-MIS-001..008`,
  `WIN-008`) — phân tích MISA/kế toán chi tiết nhất đã có trong repo.
- `docs/specs/PHU-LUC-02-HE-SINH-THAI-VN.md` (`ECO-003/ECO-005/ECO-009`),
  `docs/STATUS.md` — 8 trạng thái công bố, danh bạ ngành thật.
- `catalog/services/*.json` — 12 entry danh bạ ngành (MISA SME/AMIS, HTKK,
  eTax/eTax Mobile, hóa đơn điện tử, BHXH + công cụ ký số + I-VAN TS24,
  VNACCS hải quan) — mọi entry hiện `not_inventoried` (host build không mở
  được domain .gov.vn/vendor nào, xem `source_check` trong từng file).
- `docs/wine/KY-SO-PKCS11-RESEARCH.md` (mới, 11/11/2026) — khảo sát web thật
  per-vendor (Viettel-CA/VNPT-CA/FPT-CA), công cụ cộng đồng MacSigner, và
  phát hiện "ký số từ xa" (SmartCA/MySign) là tuyến `web` không cần Wine —
  nguồn đầy đủ (URL, ngày truy cập, loại nguồn) ở §6 của file đó. Các dòng
  HTKK/eTax/USB token/iTaxViewer trong §2-3 ở trên đã cập nhật theo khảo sát
  này, đánh dấu rõ "Cập nhật 11/11/2026" để phân biệt với bản phân tích gốc
  10/11/2026.
- `includes.chroot/etc/skel/.config/namios-wine/app-presets/htkk.json` —
  capsule recipe (`untested`) cho riêng bước lập/xuất tờ khai HTKK, dùng
  route `mono` → `wine+dotnet-framework` theo kết luận HTKK dùng .NET
  Framework 3.5 (không phải Java) ở §2 trên.
