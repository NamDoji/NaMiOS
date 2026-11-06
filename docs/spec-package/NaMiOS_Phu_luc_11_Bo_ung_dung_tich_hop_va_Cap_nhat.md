# NaMiOS — Phụ lục 11: Bộ ứng dụng thiết yếu tích hợp và cập nhật thống nhất

**Ngày:** 06/11/2026 · **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam · **Mã yêu cầu:** `APP11-001`–`APP11-036`.  
**Mục tiêu:** người dùng Việt Nam mở NaMiOS lần đầu đã thấy và dùng được các ứng dụng phổ biến, biết rõ ứng dụng nào chạy trên máy, ứng dụng nào là dịch vụ web, và khi nào có bản cập nhật. Đây là bổ sung độc lập cho phụ lục 01–10; không cần đọc lại toàn bộ các phụ lục để triển khai phạm vi này.

## 1. Quyết định sản phẩm

**NaMiOS Essentials** là tập hợp ứng dụng cài sẵn và các điểm mở dịch vụ chính thức trong Launcher/App Center. Người dùng không cần tự đi tìm trang tải, cài một wrapper lạ, hoặc đoán cái gì cần cập nhật. Việc tích hợp có ba hình thức khác nhau và UI phải nói đúng:

| Hình thức | Người dùng thấy gì | Bản cập nhật đến từ đâu | Ví dụ |
| --- | --- | --- | --- |
| **Ứng dụng cài trên máy** | Biểu tượng, chức năng hoạt động theo khả năng offline, version; gỡ/đổi mặc định theo quyền | NaMiOS/distro hoặc kho ứng dụng được tin cậy | Office, browser, bộ gõ, công cụ chống mã độc. |
| **Ứng dụng web chính thức** | Biểu tượng trong Launcher, có thể cửa sổ riêng nếu browser hỗ trợ; cần mạng/tài khoản bên thứ ba | Website cập nhật phía dịch vụ; **browser và manifest tích hợp** cập nhật riêng | YouTube, Maps, TikTok, Facebook, Zalo Web, WhatsApp Web. |
| **Ứng dụng Windows qua Wine** | Tùy chọn thêm khi người dùng cần bản desktop và đã có chứng nhận phiên bản | Nhà cung cấp app + recipe/runner NaMiOS, qua lab trước khi áp dụng | Zalo PC hoặc phần mềm ngành nếu nghiệp vụ đạt. |

**Không gọi shortcut là “bản Linux của Facebook/Zalo/WhatsApp”.** Zalo công bố bản PC cho Windows, macOS và Web [1]; WhatsApp có bản Web dùng qua trình duyệt [2]. Web app chỉ có offline nếu chính ứng dụng web hỗ trợ [3]. NaMiOS không cài hay phân phối binary, logo hoặc font thương mại khi thiếu quyền. Nội dung “có sẵn” nghĩa là **điểm truy cập đáng tin đã được thiết lập**, còn đăng nhập và điều khoản dịch vụ thuộc nhà cung cấp.

## 2. Danh mục mặc định có thể đóng gói

| Ứng dụng | Ưu tiên | Cách tích hợp ban đầu | Cập nhật cần hiển thị | Điều cần kiểm trước phát hành |
| --- | --- | --- | --- | --- |
| **Office** (Writer, bảng tính, trình chiếu) | P0 | Bộ Office Linux được chọn và cài sẵn; nhãn “NaMi Office” chỉ nếu giấy phép/nhãn hiệu cho phép | Engine, extension, từ điển, mẫu và font, mỗi loại version riêng | DOCX/XLSX/PPTX/PDF, công thức/số tiền, bố cục in, tiếng Việt; macro/add-in theo ma trận. |
| **Browser** | P0 | Trình duyệt Linux cập nhật bảo mật được; chọn mặc định | Binary, engine, extension và trạng thái khởi động lại | Zalo Web/WhatsApp, họp video, bản đồ, quyền site và tải tệp. |
| **Gõ tiếng Việt** | P0 | IME hệ thống với Telex, VNI, Unicode, dễ bật/tắt | Engine, từ điển, cấu hình, test hồi quy | Office, browser, Wine, mật khẩu, remote session và ô chat. |
| **Bảo vệ máy** | P0 | Security Center + scanner Linux được duy trì, backup, firewall và browser protection | Engine scanner, signature, OS security, backup status | Quét không chặn gõ/in; false positive; không cam kết chặn mọi virus. |
| **Zalo** | P0 | Lối mở Zalo Web chính thức, tùy browser có cửa sổ ứng dụng | Dịch vụ web tự đổi; browser/URL manifest/test recipe | QR login, chat, Unicode, file, thông báo; bản PC Wine ghi riêng. |
| **YouTube** | P0 | Website chính thức; cửa sổ riêng tùy browser | Dịch vụ web + browser/codec/DRM | Video, âm thanh, phụ đề, toàn màn hình, tăng tốc trên máy thử. |
| **Maps** | P0 | Lối mở Google Maps chính thức hoặc nhà cung cấp được phê duyệt | Dịch vụ web + browser/manifest | Tìm địa chỉ Việt Nam, chỉ đường, vị trí chỉ khi cấp quyền; bản đồ offline là sản phẩm riêng. |
| **TikTok** | P1 | Website chính thức | Dịch vụ web + browser/manifest | Xem/upload, camera/mic chỉ khi cho phép; tính năng phụ thuộc web. |
| **Facebook** | P0 | Website chính thức | Dịch vụ web + browser/manifest | Đăng nhập riêng, Messenger/notification nếu web hỗ trợ; chống trang giả. |
| **WhatsApp** | P1 | WhatsApp Web chính thức | Dịch vụ web + browser/manifest | Liên kết tài khoản, chat/call/file tùy browser và dịch vụ. |
| **PDF/ảnh/video/tệp** | P0 | Ứng dụng Linux cài sẵn | Kho ứng dụng được xác minh | File association, in, mở file ngoại tuyến, preview an toàn. |

Mức P0/P1 là **ưu tiên tích hợp**, không có nghĩa mọi chức năng của bên thứ ba đã được chứng nhận. Người dùng được bỏ ghim, đổi trình duyệt, gỡ thành phần tùy chọn. Với máy trường học hoặc cơ quan, quản trị viên chọn profile ứng dụng mặc định theo chính sách, không tự đăng nhập dịch vụ giải trí.

## 3. Yêu cầu triển khai

### 3.1 Tích hợp và trải nghiệm người dùng

**APP11-001 P0 — Màn hình “Ứng dụng của tôi”.** Khi đăng nhập lần đầu, Launcher có nhóm Làm việc, Liên lạc, Học tập/Giải trí, Thiết bị và An toàn; đặt ứng dụng nêu trên ở vị trí dễ thấy. Nhãn phụ `Cài trên máy`, `Dịch vụ web`, `Cần kết nối`, `Đã kiểm thử qua Wine`. **Nghiệm thu:** 8/10 người thử nghiệm tìm được Office, Zalo, YouTube, Browser, gõ tiếng Việt và Security Center mà không truy cập kho ứng dụng.

**APP11-002 P0 — Manifest có nguồn.** Mỗi ứng dụng có `id`, tên/nhà cung cấp, category, delivery_type, official_url hoặc package source, license/trademark status, icon provenance, version policy, update channel, required permissions, offline status, support matrix, owner và last_verified. Manifest được ký. **Nghiệm thu:** mục thiếu nguồn hoặc quyền dùng không xuất hiện ở ảnh cài chính thức.

**APP11-003 P0 — Link chính thức.** Shortcut web sử dụng HTTPS, danh sách miền chuẩn được kiểm độc lập, redirect có chính sách; không nhúng bản clone hay biểu mẫu đăng nhập NaMiOS. Cập nhật URL qua manifest đã ký. **Nghiệm thu:** thay link bằng tên miền gần giống Zalo/WhatsApp bị chặn trước khi người dùng nhập mật khẩu.

**APP11-004 P0 — Cửa sổ web app khi khả dụng.** Browser hỗ trợ cài trang thành ứng dụng thì cung cấp cửa sổ và icon riêng; nếu không, mở tab chính thức, giữ tên chính xác. Không giả vờ hỗ trợ offline/notification/call nếu chưa test. **Nghiệm thu:** user xem nguồn trang, quyền site và gỡ shortcut/cửa sổ riêng mà không mất tệp cá nhân.

**APP11-005 P0 — Không tự đăng nhập.** Không kèm cookie, token, tài khoản mẫu hoặc API đăng nhập riêng cho mạng xã hội. Hỗ trợ đăng nhập QR/SSO chỉ qua trang chính thức. **Nghiệm thu:** ISO mới cài không liên hệ domain social trước khi người dùng mở ứng dụng, trừ khi người dùng đồng ý kiểm cập nhật shortcut theo policy.

**APP11-006 P1 — Quyền site dễ hiểu.** Camera, mic, vị trí, thông báo, clipboard và upload file cấp theo site/phiên; có trang xem và thu hồi quyền chung. **Nghiệm thu:** Maps chỉ biết vị trí sau consent; TikTok không có camera khi không cấp; thu hồi quyền không xóa phiên đăng nhập khác.

**APP11-007 P0 — Bộ ứng dụng offline thiết yếu.** Office, IME, tệp/PDF, Security Center, backup/restore và màn hình trợ giúp cục bộ hoạt động khi không có internet. **Nghiệm thu:** sau khi tháo cáp mạng, gõ tiếng Việt, soạn tài liệu, lưu PDF và in trên máy in USB thử được.

**APP11-008 P1 — Bản đồ offline tùy chọn.** Nếu dùng dữ liệu bản đồ địa phương/offline, tạo app riêng có license, nguồn dữ liệu, ngày làm mới, dung lượng và phạm vi bản đồ; không gọi Google Maps Web là offline. **Nghiệm thu:** khu vực đã tải tìm địa chỉ cơ bản khi ngắt mạng, và UI hiện rõ khi thiếu dữ liệu.

**APP11-009 P0 — Office tách vòng đời.** Bộ Office phát hành như app độc lập nhưng cài sẵn trong ảnh NaMiOS; cập nhật Office không bắt buộc thay kernel, hệ điều hành không phải chờ Office release. **Nghiệm thu:** cập nhật Office rồi rollback Office không làm mất file tài liệu hoặc đảo version OS.

**APP11-010 P0 — Bộ gõ luôn sẵn sàng.** Telex/VNI, chỉ báo chế độ gõ rõ; hotkey có thể đổi, không đụng hotkey Office và browser; xử lý dấu trong app Wine có hồ sơ ngoại lệ. **Nghiệm thu:** 200 câu có dấu trong 5 loại cửa sổ, không lặp ký tự hoặc ghi phím mật khẩu.

**APP11-011 P0 — Bảo vệ máy có thật.** Security Center tổng hợp OS/browser updates, firewall, scanner/signatures, sandbox và backup; status từng lớp riêng. Scanner on-demand và tùy chính sách quét theo truy cập sau benchmark. **Nghiệm thu:** chữ ký cũ làm badge chuyển cảnh báo ngay cả khi lần quét cuối báo sạch; file trong vùng cách ly có đường phục hồi sau false positive.

**APP11-012 P1 — Gói profile.** `Cá nhân`, `Giáo viên/Học sinh`, `Văn phòng`, `Kế toán` có thứ tự/ghim khác nhau; chỉ cài thêm binary khi user chọn và nguồn hợp lệ. **Nghiệm thu:** profile trường học không tự mở TikTok/Facebook nhưng user gia đình có thể ghim chúng.

### 3.2 NaMi Update Center: một nơi quản lý nhiều vòng đời

**APP11-013 P0 — Bảng trạng thái cập nhật.** Một màn hình hiển thị `Hệ điều hành`, `Bảo mật`, `Browser`, `Office`, `Bộ gõ`, `Ứng dụng khác`, `Wine recipe`, `Shortcut/web test`; có ngày kiểm, phiên bản cài, phiên bản mới, mức độ khẩn và hành động. Dịch vụ web ghi `Được nhà cung cấp cập nhật trực tuyến`, không bịa số phiên bản cài trên máy. **Nghiệm thu:** user phân biệt bản browser cần tải với Facebook Web chỉ thay đổi trên server.

**APP11-014 P0 — Nguồn và chữ ký.** Chỉ lấy gói native từ kho distro/vendor được cấu hình và xác minh chữ ký/hash/metadata; Wine installer từ nguồn được chứng nhận. Kiểm key rotation/revocation. **Nghiệm thu:** gói bị sửa hoặc nguồn mạo danh bị từ chối với mã lỗi dễ hiểu.

**APP11-015 P0 — Kiểm cập nhật tự động, cài có lịch.** Mặc định kiểm định kỳ khi có mạng; bản vá khẩn có thông báo và cửa sổ cài phù hợp, không tự khởi động giữa tiết học/cuộc họp/ký hóa đơn. Người dùng chọn “Cài tối nay”, “Cài và khởi động lại”, hoặc hoãn theo policy bảo mật. **Nghiệm thu:** 20 máy thử không bị reboot giữa tác vụ, bản khẩn quá hạn được nhắc rõ.

**APP11-016 P0 — Kiểm phụ thuộc giao dịch.** Stage/download → kiểm chữ ký/dung lượng/pin → snapshot → cập nhật → health check → commit/rollback; tách data người dùng. **Nghiệm thu:** ngắt điện/mất mạng/hết ổ ở ba điểm không mất file, máy khởi động bản trước hoặc vào recovery.

**APP11-017 P0 — Update rings.** `lab`, `pilot`, `stable`; canary theo nhóm phần cứng; trình duyệt, Office, IME, Wine runner và device backend đều có trigger retest riêng. **Nghiệm thu:** browser mới làm lỗi Zalo Web ở lab thì ring stable giữ bản cũ có thời hạn và kèm cảnh báo rủi ro bảo mật, không giữ vô hạn.

**APP11-018 P0 — Cập nhật browser theo SLA.** Browser là cửa vào social, ngân hàng và dịch vụ công; có người theo dõi security advisory, gói được xác minh, regression suite cho Zalo/WhatsApp/YouTube/Maps/TikTok/Facebook. **Nghiệm thu:** mọi browser release lên stable có kết quả smoke test 6 dịch vụ; bản vá bảo mật khẩn được xử lý theo mức nghiêm trọng.

**APP11-019 P0 — Dịch vụ web tự thay đổi.** NaMiOS không thể cố định hay điều khiển version server của Facebook, YouTube, TikTok, Maps, Zalo, WhatsApp. Theo dõi synthetic smoke tests không đăng nhập và ca có tài khoản pilot hợp lệ; khi web đổi giao diện/không chạy, ghi `sự cố dịch vụ hoặc tương thích` cùng hướng xử lý. **Nghiệm thu:** login QR Zalo hỏng được phát hiện và không gọi là “ứng dụng NaMiOS chưa cập nhật”.

**APP11-020 P0 — Chữ ký malware độc lập.** Engine và cơ sở dữ liệu phát hiện cập nhật theo vòng đời riêng; scanner cũ hoặc signature không tải được phải báo có ngày/thời điểm. **Nghiệm thu:** offline 7 ngày hiện thời gian cập nhật cuối, vẫn quét bằng dữ liệu sẵn có nhưng không báo bảo vệ đầy đủ.

**APP11-021 P0 — Wine app có kiểm version.** Với Zalo PC hoặc app Windows tùy chọn, updater của vendor không âm thầm thay binary đã chứng nhận; đưa bản mới qua lab rồi cập nhật recipe/runner/permission và chạy lại workflow. **Nghiệm thu:** app đổi hash chuyển `Cần kiểm thử lại`, giữ cách quay về bản trước khi điều khoản/installer cho phép.

**APP11-022 P0 — Changelog bằng tiếng Việt.** Mỗi bản NaMiOS/app native có mô tả ngắn “sửa gì, tác động gì, có cần khởi động lại không”; cập nhật web của bên thứ ba không bịa changelog, chỉ dẫn tới nguồn chính thức khi có. **Nghiệm thu:** người dùng xem lịch sử và lý do rollback cho từng gói.

**APP11-023 P1 — Băng thông và máy yếu.** Download delta khi nền cho phép, tạm dừng/tiếp tục, tránh kết nối tính cước và giờ làm việc, đặt giới hạn IO/CPU; cache an toàn cho nhóm máy trường học. **Nghiệm thu:** update nền không làm cuộc gọi video giật hoặc trễ gõ tiếng Việt vượt ngưỡng pilot.

**APP11-024 P0 — Ngừng hỗ trợ minh bạch.** Khi OS/browser/Office/IME/Wine app hết hạn hỗ trợ, chỉ ra ngày, rủi ro và lựa chọn nâng cấp/đổi máy/tuyến thay thế. **Nghiệm thu:** hệ thống không gắn nhãn an toàn cho browser hết vá hoặc recipe app hết chứng nhận.

### 3.3 Tương thích, trợ lý và hỗ trợ người dùng

**APP11-025 P0 — Khởi động kiểm tra thông minh.** Trước khi mở app lần đầu, chỉ kiểm những điều cần: mạng cho web, quyền media, dữ liệu offline, phiên bản browser, Office/font; không bắt người dùng qua hàng chục bước. **Nghiệm thu:** “Mở WhatsApp” khi offline nhận giải thích và nút thử lại, không quay vòng loading.

**APP11-026 P0 — SmartAI phân biệt loại ứng dụng.** Câu “cập nhật Zalo/Facebook” phải giải thích phần web do nhà cung cấp cập nhật; NaMiOS có thể cập nhật browser, manifest và kiểm tương thích. Nếu user dùng Zalo PC trong Wine, chỉ cập nhật sau chứng nhận. **Nghiệm thu:** 10 câu hỏi cập nhật tự nhiên được phân loại đúng và không tải wrapper lạ.

**APP11-027 P0 — Trình xử lý lỗi ba mức.** Người mới thấy “Kiểm mạng/Thử lại/Xem hướng dẫn”; người hỗ trợ thấy URL, browser, permission, update status; developer thấy trace đã lọc. **Nghiệm thu:** phân biệt website lỗi, browser cũ, mất mạng và permission bị từ chối bằng mã lỗi khác nhau.

**APP11-028 P0 — Chứng nhận workflow.** Ghi theo app/version/browser/OS/hardware/permission/test date: mở, đăng nhập, tiếng Việt, upload, notification, call/video khi phù hợp, in/file xuất. **Nghiệm thu:** YouTube xem video đạt không suy ra DRM mọi nội dung đạt; WhatsApp chat đạt không suy ra call đạt.

**APP11-029 P1 — Hỗ trợ cài thêm.** App Center tìm phần mềm theo tên/nhu cầu tiếng Việt; đề xuất Linux/web/Wine đã chứng nhận/Windows có phép và độ tin cậy; không tải “bản mod” từ nguồn không xác minh. **Nghiệm thu:** yêu cầu “Zalo desktop Linux” hiển thị Zalo Web và hạn chế, không gắn một wrapper không chính thức là bản vendor.

**APP11-030 P1 — Tìm không dấu và thuật ngữ quen.** `trinh duyet`, `browser`, `chrome`, `go tieng viet`, `zalo`, `ban do`, `maps`, `diet virus` tìm đúng mục; không đổi tên chính thức của nhà cung cấp. **Nghiệm thu:** 30 truy vấn của người dùng Việt tìm đúng top 3.

**APP11-031 P0 — Quyền riêng tư web.** Profile browser tách theo người dùng OS, không đồng bộ cookie giữa tài khoản; logout app do chính user/vendor xử lý; shortcut không đọc tin nhắn hay danh bạ. **Nghiệm thu:** user B không thấy WhatsApp/Zalo session của user A.

**APP11-032 P1 — Khôi phục khi cập nhật hỏng.** Một nút xem bản gần nhất, kết quả health check và rollback trong phạm vi OS/app; riêng web service không thể rollback server, nên mở trang chính thức/trình duyệt khác có kiểm, hoặc báo vendor. **Nghiệm thu:** lỗi Office mới mở file không đúng có đường quay version app mà vẫn giữ tệp gốc.

**APP11-033 P0 — Chống mạo danh thương hiệu.** Logo/icon dùng theo quy định từng vendor, đường link chính thức, nhãn rõ `Bên thứ ba`; không bán dịch vụ dưới tên vendor hoặc nhúng màn hình login giả. **Nghiệm thu:** kiểm quyền logo/trademark trước đóng ISO; danh mục có trạng thái `approved/pending/replace_with_text`.

**APP11-034 P0 — Phân phối có giấy phép.** Các binary bên thứ ba chỉ bundle khi điều khoản cho phép; nếu không, cung cấp link chính thức hoặc hướng dẫn tự cài theo quyền. **Nghiệm thu:** SBOM và license inventory khớp từng app trong ISO.

**APP11-035 P1 — Đo sử dụng không xâm phạm.** Tổng hợp cục bộ số lần mở app, lỗi/crash và bản cập nhật theo opt-in/ẩn định danh; không gửi URL cá nhân, tin nhắn, nội dung video/tệp. **Nghiệm thu:** người dùng xem/xóa được dữ liệu chẩn đoán, tắt telemetry không ảnh hưởng cập nhật bảo mật.

**APP11-036 P0 — Cổng phát hành.** Không phát hành Essentials nếu IME, Office, browser, Security Center hoặc cập nhật/rollback P0 lỗi; không ghi “đã cài app Linux” cho shortcut web; 6 dịch vụ web kiểm trên browser ship và máy pilot. **Nghiệm thu:** báo cáo release có manifest, nguồn, ảnh UI, phiên bản, test pass/fail, blocker và chữ ký người chịu trách nhiệm.

## 4. Luồng người dùng mẫu

1. **Bật máy:** thanh ứng dụng hiện Office, Browser, Zalo, YouTube, Maps, Facebook; WhatsApp/TikTok trong nhóm Ứng dụng phổ biến theo profile. Gõ tiếng Việt mặc định sẵn, Security Center hiển thị mức an toàn thực.
2. **Nhấn Zalo:** mở Zalo Web chính thức trong browser/cửa sổ riêng; user tự đăng nhập; NaMiOS quản quyền thông báo/file. Nếu cần tính năng bản PC không có trên Web, Compatibility Broker hiển thị trạng thái Wine theo test từng phiên bản.
3. **Nhấn Cập nhật:** Update Center cho biết Office/Browser/IME/OS có bản cần tải, scanner có signature mới, Facebook/YouTube là dịch vụ web được vendor cập nhật và lần kiểm tương thích gần nhất.
4. **Cập nhật lỗi:** health check không đạt → rollback gói OS/native tương ứng, hiển thị mã lỗi; web service hỏng → báo sự cố và tuyến làm việc khác, không giả rằng có thể rollback website bên ngoài.

## 5. Hợp đồng kỹ thuật và test bắt buộc

```json
{
  "id": "zalo.web",
  "title": "Zalo Web",
  "delivery_type": "official_web",
  "official_url": "https://id.zalo.me/",
  "publisher": "Zalo",
  "offline": false,
  "binary_bundled": false,
  "update": {
    "site": "publisher_managed",
    "browser": "namios_repository",
    "integration_manifest": "signed_manifest"
  },
  "last_verified": null,
  "support": "not_tested"
}
```

Ví dụ trên là schema gợi ý, **không phải chứng nhận Zalo đã chạy trên bản build cụ thể**. Tạo file `essentials-manifest.schema.json`, `essentials-manifest.json`, schema trạng thái Update Center và fixture test có dữ liệu giả. Mọi app phải có owner, nguồn và test date; URL có thể được thay đổi bởi vendor nên phải kiểm trước release.

| Test ID | Ca bắt buộc | Kết quả |
| --- | --- | --- |
| E11-01 | Máy mới không mạng, mở Office/gõ Việt/PDF | Chạy offline; web shortcut giải thích cần mạng. |
| E11-02 | Nhấn 6 dịch vụ web | URL HTTPS chính thức, phân quyền từng site, không đăng nhập hộ. |
| E11-03 | Browser cập nhật, Zalo QR đổi | Smoke test phát hiện lỗi, badge kiểm thử hết hiệu lực. |
| E11-04 | Signature scanner quá hạn | Security Center báo rõ ngày và mức bảo vệ. |
| E11-05 | Gói Office lỗi sau nâng cấp | Rollback Office; tài liệu người dùng không mất. |
| E11-06 | Trang giả `whatsapp-login.example` | Không mở từ shortcut, cảnh báo URL mạo danh. |
| E11-07 | App Wine của vendor tự đổi phiên bản | Recipe chuyển `needs_retest`; không tuyên bố tiếp tục hỗ trợ. |
| E11-08 | Đang dạy online, có update OS | Không reboot; hiển thị lịch cài phù hợp. |

**Đầu ra cho Claude Code:** cập nhật backlog theo 36 mã, prototype Launcher/App Center/Update Center, manifest có schema và test, ADR browser/Office/IME/scanner, screenshot tiếng Việt cho người dùng xem, cùng báo cáo quyền phân phối. Chỉ đánh dấu yêu cầu hoàn thành khi mã chạy và test trên bản build thật.

## 6. Nguồn chính thức tham khảo ngày 06/11/2026

[1] Zalo PC, các phiên bản Windows, macOS và Web: https://www.zalo.me/pc  
[2] WhatsApp Help Center, WhatsApp Web qua trình duyệt: https://faq.whatsapp.com/668538004658079/  
[3] Google Chrome Help, cài và sử dụng web app; khả năng offline tùy từng web app: https://support.google.com/chrome/answer/9658361  
[4] ClamAV Documentation, giới hạn cấu hình on-access scanning: https://docs.clamav.net/manual/OnAccess.html

Các dịch vụ và điều khoản có thể thay đổi. Mỗi lần đóng bản phát hành, đội sản phẩm kiểm lại URL, logo/license, chức năng web và hành vi cập nhật từ nguồn chính thức.
