# 04. Kiến trúc web, vận hành và nghiệm thu

## 1. Cách triển khai

Ưu tiên site tĩnh/SSR hoặc hybrid nhẹ với HTML có nội dung sẵn cho SEO, CDN và cache; framework chọn theo repo sẵn có, năng lực đội ngũ và khả năng bảo trì, không ép công nghệ cụ thể. Các trang giới thiệu, docs, FAQ, release notes có thể từ Markdown/MDX hoặc CMS có quy trình duyệt. Trang ma trận tương thích đọc dữ liệu versioned, cho phép tìm kiếm/lọc; dữ liệu trả về có ngày kiểm. Không build một CMS riêng nếu một lựa chọn đáng tin đáp ứng đủ.

Tách nội dung thành ba lớp: (a) narrative marketing do biên tập duyệt; (b) release manifests và feature claims do kỹ thuật ký/duyệt; (c) ma trận chứng nhận app/thiết bị do lab xuất. CI cấm nội dung marketing trỏ tới claim không có bằng chứng hoặc trạng thái không khớp. Mọi release, trang tải, FAQ và structured data cùng một nguồn. Versioned API/JSON schema; mở API đọc công khai khi có dữ liệu thật.

## 2. Hiệu năng và SEO

- Mục tiêu Core Web Vitals tại percentile 75 của người dùng thực: LCP ≤ 2,5s; INP ≤ 200ms; CLS ≤ 0,1; đo cả mobile 4G và desktop, có dashboard theo trang. Đây là ngưỡng tham chiếu hiện hành, cần đối chiếu tài liệu web.dev khi triển khai.
- HTML semantic, heading hợp lý, title/description duy nhất, canonical, hreflang vi/en nếu có bản dịch, Open Graph/Twitter image, sitemap/robots phù hợp; tránh index trang staging. SoftwareApplication structured data chỉ khi trạng thái và giá/free claims khớp dữ liệu release thật.
- Responsive image srcset, prefetch có kiểm soát, lazy-load media dưới màn, font subset tiếng Việt, preload chỉ tài nguyên cốt lõi, không dùng video nặng làm điều kiện thấy CTA. Mục tiêu ngân sách ban đầu đề xuất: JS khởi tạo < 180KB gzip, hero image < 300KB trên mobile, trang chủ < 1,5MB tải đầu; đo và chỉnh theo thực tế.
- Link nội bộ tránh 404; redirects cho URL thay đổi; error page tiếng Việt có tìm kiếm. Docs và release notes có anchor bền vững, ngày cập nhật.

## 3. An toàn website và phân phối

HTTPS/HSTS, CSP chặt, headers phù hợp, bảo vệ form khỏi spam và abuse, chống XSS/CSRF theo luồng, giới hạn rate, dependency scanning/SBOM, secret chỉ ở server, quyền admin tối thiểu và MFA. Không load script bên thứ ba trên trang tải nếu không thật cần. CI kiểm link tải tồn tại, kích thước/hash, chữ ký, cache headers, download filename và không có redirect tới domain lạ. Có quy trình khóa/ngắt tải ngay nếu phát hiện ISO bị thay thế.

Tên miền và DNS chính thức do chủ dự án xác nhận trước go-live; không giả lập địa chỉ trong website. Đường tải phân biệt stable/beta và không có “latest” redirect không kiểm soát. Public key và fingerprint công bố qua kênh độc lập; hướng dẫn verify phải được nhóm release chạy thử trên cả Windows/macOS/Linux.

Backup nội dung/CMS, phân quyền người biên tập với người phát hành, audit log, staging và preview, checklist duyệt claims, rollback deploy. Trang status cung cấp kênh thông báo khi CDN/download không khả dụng. Có contact security và quy trình disclosure.

## 4. Privacy và quyền nội dung

Chính sách quyền riêng tư nêu email nhận tin, analytics, cookies, log máy chủ, thời hạn lưu, đơn vị xử lý và quyền xóa/thu hồi. Không dùng hình người, thiết bị, phong cảnh, di sản, logo đối tác, screenshot app không rõ giấy phép. Danh mục asset gồm file, nguồn, chủ quyền, phạm vi sử dụng, ghi công, ngày phê duyệt. Chỉ trình bày chủ quyền lãnh thổ bằng nguồn bản đồ chính thức đã xác minh, không dùng bản đồ cách điệu thiếu kiểm duyệt.

Mã nguồn thành phần và giấy phép NaMiOS/NaMiOffice được nêu chính xác; nhãn hiệu và copyright nguồn mở được giữ theo nghĩa vụ. Dịch vụ web bên thứ ba có điều khoản riêng; không mô tả chúng là sản phẩm NaMiOS.

## 5. Bộ kiểm thử và release gates

| Nhóm | Ca tối thiểu | Gate |
|---|---|---|
| Nội dung | Mỗi claim có chứng cứ; app web/native không lẫn; tiếng Việt được biên tập | Không có claim “đã có” thiếu manifest |
| Download | Trước release không có link giả; beta/stable có file thật, hash/chữ ký/notes/hardware, kiểm URL | Không mở public nếu thiếu một thành phần |
| Chức năng | Search app/model, lọc theo version và workflow, CTA theo state, form và unsubscribe | E2E pass desktop/mobile |
| Giao diện | 320/390/768/1366/1920px, zoom 200–400%, screenshot logo chính thức, dark/light | Không tràn chữ, CTA thấy được |
| Trợ năng | Axe tự động + duyệt thủ công keyboard/screen reader, WCAG 2.2 AA | Không có lỗi blocker |
| Hiệu năng | Lighthouse lab và Web Vitals thực tế; mạng chậm, ảnh/video | Theo ngân sách và ngưỡng đã chọn |
| Bảo mật | Headers/CSP, XSS/CSRF, spam, quyền CMS, link hijack, dependency scan | Không có lỗ hổng critical/high chưa xử lý |
| Pháp lý | Giấy phép asset, logo, privacy, TOS, bên thứ ba, attribution | Chủ dự án/pháp lý ký duyệt |

UAT với ít nhất 5 người mới dùng máy tính phổ thông, 5 giáo viên/văn phòng, 3 IT và 3 người làm kế toán khi chuẩn bị public beta; đo thời gian tìm thông tin và lỗi hiểu lầm. Đây là mục tiêu lấy mẫu, không phải số liệu đã thực hiện.

## 6. Lộ trình và đầu ra

**W0:** kiểm repo, trạng thái release, logo/asset có quyền, tên miền, nguồn dữ liệu. **W1:** sitemap, wireframe và design tokens, prototype home/download/compatibility với trạng thái pre-release thật. **W2:** triển khai responsive + CMS/content + manifest schema + tìm app/thiết bị bằng dữ liệu thử có nhãn. **W3:** accessibility, SEO, bảo mật, tối ưu hiệu năng, QA copy và ảnh. **W4:** nối release pipeline, kiểm chữ ký/hash/end-to-end trước beta hoặc stable. Lịch là mốc theo đầu ra; phải ước lượng lại sau khảo sát.

Đầu ra: repo mã nguồn và hướng dẫn chạy, design system, nội dung vi-VN, bản dịch nếu được duyệt, schema và dataset mẫu, admin workflow, test report, asset/license inventory, runbook phát hành, checklist go/no-go, URL staging. Không xuất bản công khai khi chủ dự án chưa chốt domain, bản build và pháp lý.

## 7. Nguồn tham chiếu

- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- web.dev Core Web Vitals: https://web.dev/articles/vitals
- Google Search Central SoftwareApplication: https://developers.google.com/search/docs/appearance/structured-data/software-app
- Nguồn nội bộ: NaMiOS Phụ lục 07, 11, 15, 16; NaMiOffice Spec v1; bộ logo sen cân đối và Brand UI/UX.
