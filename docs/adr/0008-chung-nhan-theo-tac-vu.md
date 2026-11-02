# ADR 0008 — Chứng nhận theo tác vụ

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §6.1, §11.2, §18.3, §18.4; requirement UX-002, APP-ZAL-005

## Bối cảnh

Việc "mở được giao diện" một ứng dụng không chứng minh nó dùng được. Cần một định nghĩa chặt về khi nào một ứng dụng được coi là đạt, tránh false pass và tránh kế thừa nhãn khi binary thay đổi.

## Quyết định

Chỉ cấp **`task_verified`** khi **tất cả tác vụ bắt buộc** của **đúng tuple** (OS build, kernel/graphics khi liên quan, desktop session, runner hash, profile digest, app build/hash/arch, runtime/dependency versions, bộ dữ liệu, test suite revision, phần cứng/VM) đã đạt **và** có **QA phê duyệt độc lập** với việc Claude tự báo pass. **`vendor_support` là thuộc tính độc lập.** Bản app mới (sau tự cập nhật) KHÔNG kế thừa nhãn — trở về `untested`.

## Lý do

- Kết quả một máy không tự lan sang toàn bộ phần cứng; tuple cố định phạm vi của bằng chứng.
- Mock/stub không phải bằng chứng app thương mại chạy; test skip vì môi trường không được đổi thành pass.
- Ba loại nhãn (tình trạng tương thích / nguồn-bộ-cài / vendor support) phải tách; không dùng huy hiệu giống chứng nhận của Microsoft/MISA (UX-002).

## Hệ quả

- Trạng thái tương thích: `untested` → `experimental` → `task_verified` / `blocked` / `revoked`.
- Thay đổi tuple quan trọng (OS/Wine/runtime/app build/profile/sandbox/bộ gõ/font/browser) buộc đánh giá lại (regression).
- Evidence phải ghi test/run ID, commit SHA, steps, timestamps, expected/actual, người xác nhận, artifact không chứa bí mật; không lưu tài liệu thật.

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Mô hình evidence/state machine chứng nhận (schema `evidence-report`, semantic rule chặn `task_verified` thiếu evidence) **viết + test được ở M1** bằng Python thuần.
- Chứng nhận ứng dụng thương mại thực (Word/Excel/Zalo/MISA) cần bộ cài + môi trường + QA/kế toán → thuộc M4, hiện **BLOCKED**.

## Spike cần làm + điều kiện chấp nhận

- **Spike:** đặt `task_verified` khi thiếu evidence/required tests bị từ chối (MAN-04); đổi app hash sau tự cập nhật → build mới `untested`, không kế thừa nhãn (MAN-05); catalog revoked/evidence không tồn tại/test skip/phần cứng khác/đổi mode ngầm đều không tạo false pass.
- **Điều kiện chấp nhận:** không có đường nào tạo `task_verified` mà thiếu evidence đúng tuple + QA ký độc lập.
