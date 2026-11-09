# MAP-01 — Cổng bản đồ chủ quyền Việt Nam

**Trạng thái:** 🚫 BLOCKED — **KHÔNG đóng vào ISO** cho tới khi đủ điều kiện dưới đây.
**Ngày mở:** 09/11/2026 · **Nguồn yêu cầu:** NaMiOS Brand UI/UX v1 (`04_PROMPT_CLAUDE_CODE.md` §"Cổng riêng cho bản đồ") + `README_BAT_DAU.md`.

## Vì sao có cổng này

Bộ tài sản thương hiệu NaMiOS **KHÔNG chứa** bản đồ chủ quyền đã được duyệt. Ảnh wallpaper số 20 ("Biển Đảo Việt Nam") chỉ là **cảnh biển đảo chung do AI tạo**, KHÔNG phải tư liệu bản đồ hành chính/chủ quyền. Một bản đồ thể hiện Hoàng Sa, Trường Sa, Phú Quốc, Côn Đảo và các đảo liên quan là vấn đề **chủ quyền quốc gia** — sai sót hoặc dùng nguồn không hợp lệ có hậu quả nghiêm trọng. Vì vậy mọi asset bản đồ phải qua cổng MAP-01 trước khi cài sẵn vào hệ điều hành.

## TUYỆT ĐỐI KHÔNG

- ❌ **Không nhờ AI tự sinh đường biên giới, đường cơ sở, vị trí hay hình dạng đảo.** AI không được vẽ/suy diễn bản đồ chủ quyền.
- ❌ **Không tự vẽ bản đồ** rồi đóng vào ISO.
- ❌ Không dùng ảnh AI (gồm wallpaper #20, ảnh trống đồng) làm tư liệu bản đồ/khảo cổ gốc.

## Điều kiện BẮT BUỘC để bật asset bản đồ (tất cả, không thiếu cái nào)

1. **Nguồn bản đồ được phép sử dụng** — có giấy phép/bản quyền rõ ràng, từ cơ quan/đơn vị có thẩm quyền.
2. **Bản cập nhật hành chính** mới nhất (địa giới, tên đơn vị hành chính).
3. Thể hiện đầy đủ **Hoàng Sa, Trường Sa, Phú Quốc, Côn Đảo** và các đảo liên quan; **ô phụ (inset)** nếu cần.
4. **Chuyên gia rà soát độc lập** (người có chuyên môn bản đồ/chủ quyền) ký duyệt.
5. **Bằng chứng duyệt** lưu lại (ai duyệt, ngày, phạm vi).
6. **Hash (SHA-256)** của file asset + **giấy phép** đi kèm, ghi vào manifest.

## Trạng thái hiện tại

- Placeholder: CHƯA tạo asset bản đồ nào. CHƯA đóng gì vào ISO.
- **Chờ chủ dự án (Đỗ Chí Cường / Đỗ Bảo Nam)** cung cấp nguồn bản đồ hợp lệ + người có chuyên môn ký duyệt. Khi có đủ, cập nhật mục "Trạng thái" + manifest rồi mới tích hợp qua PR review riêng.

> Quy tắc ngắn: **Không có nguồn hợp lệ + chữ ký chuyên gia ⇒ không có bản đồ trong NaMiOS.**
