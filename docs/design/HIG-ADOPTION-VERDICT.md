# NaMi HIG (Phụ lục 22) — Phân tích & Quyết định áp dụng

> **Loại tài liệu:** đánh giá độc lập + quyết định phạm vi áp dụng HIG. Trung thực, bám repo.
> **Phạm vi file:** chỉ nhận định + lộ trình. `verified_on_host: NO`. Không `git commit`/push.
> **Ngày:** 2026-11-11. Nguồn: `docs/design/hig/NaMi-Human-Interface-2026.md` + prototype
> `docs/design/prototype-luxury-dongson/` + repo runtime.

## 1. HIG có hợp lý không? — **CÓ, phần lớn (adopt)**

**Vì sao hợp lý:**
1. **Phương pháp đúng:** bắt buộc P0 (khảo sát repo) TRƯỚC khi sửa; cấm "tuyên bố đã tích hợp OS"
   khi mới có prototype (§10.1). Khớp đúng kỷ luật repo này đang theo (`verified_on_host: NO`).
2. **Token theo NGHĨA, đo WCAG thật** (§5.1): "màu nhận diện ≠ màu chữ/nút đạt tương phản" — đúng
   tuyệt đối. Repo đã có tiền lệ (BRAND.md tính vermilion-deep/gold-deep) → HIG chỉ hệ thống hóa.
3. **Trung thực là ràng buộc cứng:** không giả tương thích, không popup giả cập nhật, "nút được vẽ
   ≠ đạt" (§12.1), AI phải xin quyền theo cấp (§8.5). Đây là giá trị cốt lõi khớp memory dự án.
4. **A11y cụ thể, đo được** (§9): 4.5:1/3:1, bàn phím, focus, screen reader, 200% reflow — không
   chung chung.
5. **Tôn trọng ranh giới IP** (§10.3): không chép icon/font/âm thanh Apple/MS; không ghi đè nhận
   diện Firefox/LibreOffice; splash chỉ ở lớp distro kiểm soát, **không hạ bảo mật để thay hình**.

**Điểm cần điều chỉnh khi áp dụng (không phải sai, là cập nhật):**
- §7.1 gợi ý tên "NaMi Tệp / NaMi Cài đặt / NaMi AI" → **GHI ĐÈ** bởi quy tắc mới của chủ dự án
  ("n"+chức năng / VN thuần, không tiền tố). Repo đã theo quy tắc mới.
- §5.2 nói motion "120–220ms"; token dự án dùng **120–240ms** (slow=240). Giữ 240 (vẫn trong tinh
  thần "ngắn"), ghi chú lệch nhẹ.
- §12.2 "min 1024×600" — token để `min_supported` 1024×600 nhưng mốc thực dụng 1366×768 (khớp
  `branding/design-system/tokens.json`). Không mâu thuẫn.

## 2. ADOPT NGAY (P0 + P1 — ĐÃ làm trong wave này)

| Đầu ra | File | Trạng thái |
|---|---|---|
| Khảo sát repo (§10.1) + screen matrix + branding map + 10 tác vụ + risk | `docs/design/P0-UI-AUDIT.md` | **DONE** |
| Semantic tokens light/dark/high-contrast + WCAG đo thật (§5) | `docs/design/NAMI-DESIGN-TOKENS.md` + `docs/design/nami-tokens.json` | **DONE** |
| Thuật ngữ VN chuẩn (§7.1) + audit nhãn lệch | `docs/design/NAMI-GLOSSARY-VI.md` | **DONE** |
| Đặc tả component + mẫu lỗi 5 phần (§6/§7.2) | `docs/design/NAMI-UI-KIT.md` | **DONE** |
| Phân tích + quyết định áp dụng | tài liệu này | **DONE** |

**35/36 cặp tương phản PASS** (cặp FAIL duy nhất gold/ivory 2.04:1 là **chủ đích** — chứng minh
không dùng gold làm nền nút trên nền sáng). Palette v3 Đông Sơn đã CHẠY trong
`brand.json`/`.colors`/desktoptheme từ các wave trước; wave này bổ sung **lớp semantic token
thiếu** (P1 nền tảng) + 5 tài liệu HIG yêu cầu.

> **Viết tokens/specs ≠ ship tokens across every app.** Đây mới là **P1 (nền tảng = tài liệu +
> token)**. Nối vào từng app/shell/màn hình và kiểm chứng trên máy thật là **P2–P4 + boot-test** —
> CHƯA làm. Không được coi 5 tài liệu này là "OS đã đạt HIG".

## 3. CHƯA làm — P2 / P3 / P4 (ranh giới rõ ràng)

| Giai đoạn | Nội dung | Điều kiện hoàn thành (HIG §11) | Chưa làm vì |
|---|---|---|---|
| **P2 — Shell** | nối token vào desktop/launcher/taskbar/search/quick-settings/notification; sinh KColorScheme **high-contrast** thật; 1 thư viện widget chung; tái xuất PNG/ICO logo v3; đồng bộ `make-colorscheme.py` | mở app / tìm tệp / đổi Wi-Fi hoàn tất **trên máy thử** | cần boot-test; đụng theme/app/config (ngoài phạm vi P0/P1 docs-only) |
| **P3 — Hành trình** | cài đặt (2 bước xóa đĩa), cập nhật (changelog VN + % thật + rollback), thiết bị, lỗi 5-phần có mã, trợ giúp, AI có quyền | thực nghiệm với **lỗi thật + rollback thật** (VM snapshot) | cần dịch vụ thật + VM |
| **P4 — Hoàn thiện** | motion, wallpaper (có quyền), âm thanh, microcopy, tối ưu máy yếu | kiểm thử thiết bị + **thử người dùng** (≥5 chưa-Linux + ≥5 Windows, §12.1) | cần phần cứng + người dùng thật |

## 4. Điều kiện DỪNG phát hành của HIG mà ta PHẢI tôn trọng

Trích §10.3 / §12 / §14 — các ràng buộc "release-stop", không được vi phạm để "đẹp hơn":

1. **Không giả tương thích:** không đánh dấu UI "đạt" chỉ vì nút được vẽ; không tuyên bố "mọi
   driver / mọi app Windows chạy được" (ảnh hưởng `nWine`/`namios-windows-app`, risk R6).
2. **Không hạ bảo mật để thay hình:** không tự đổi logo firmware/UEFI; splash chỉ ở
   bootloader/Plymouth/login do distro kiểm soát; Secure Boot chưa có thì nói rõ (R8), không tắt
   bảo vệ (§10.3).
3. **Rà soát nhãn hiệu tên "NaMi/NaMiOS"** trước phát hành thương mại (§0, `brand.json`
   `trademark review pending`, R3) + quyền dùng tên/logo dịch vụ bên thứ 3 (R4).
4. **Giấy phép font/hình nền/âm thanh + attribution** đầy đủ (SBOM); không đưa biểu tượng chủ
   quyền/bản đồ chưa kiểm chứng vào nền (§5.3, R5).
5. **AI không chạy hành động đặc quyền khi chưa xác nhận**; xem được log + nguồn + dữ liệu gửi đi
   (§8.5/§12.3).
6. **Không faking rollback:** chỉ hiển thị "đã khôi phục, dữ liệu an toàn" khi rollback + kiểm tra
   dữ liệu THỰC SỰ thành công (§7.2/§8.4, R7).

## 5. Khuyến nghị thứ tự việc tiếp theo (sau khi chủ dự án duyệt 5 tài liệu này)

1. **Hợp nhất 3 bộ token về 1** (lấy `nami-tokens.json` làm nguồn ngữ nghĩa) — chặn drift trước P2.
2. **Tái xuất PNG/ICO** logo trống đồng v3 cho SDDM/Plymouth/Calamares (đang còn logo SEN cũ).
3. **Sinh KColorScheme high-contrast** thật từ token.
4. **Chốt nhãn D1** ("Cài đặt" vs "Bảng điều khiển") + **phân biệt 2 app AI** (D3).
5. Chỉ khi có **build-host + boot-test**: nối shell (P2) rồi đo tác vụ P0 với người dùng thật.

## 6. Verdict (3 dòng)

1. HIG **hợp lý, nên áp dụng** — phương pháp (P0 trước sửa), token-đo-WCAG, trung thực và a11y đều
   đúng; chỉ chỉnh naming theo quy tắc mới của chủ dự án.
2. **P0 + P1 ĐÃ xong dưới dạng tài liệu + token** (5 doc + `nami-tokens.json`, 35/36 cặp PASS) —
   bám palette v3 Đông Sơn đang chạy trong repo.
3. **P2–P4 CHƯA làm** (shell/journeys/polish cần đụng theme-app-config + boot-test + người dùng
   thật); phải tôn trọng các điều kiện dừng-phát-hành của HIG (không giả tương thích, không hạ
   bảo mật, rà soát nhãn hiệu/giấy phép).
