# ADR 0007 — Cập nhật và bảo vệ metadata

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §5.1, §10, §15; requirement SEC-006, SEC-007, SEC-008, UPD-001..003

## Bối cảnh

Hệ thống cần cập nhật gói OS và cập nhật catalog/profile tương thích một cách an toàn, chống giả mạo/replay/downgrade, mà không tự phát minh giao thức chữ ký hay package manager mới.

## Quyết định

Dùng **APT + repo có chữ ký** cho gói hệ thống. Catalog/profile dùng **framework ký metadata được duy trì, ưu tiên đánh giá TUF**. Metadata có phiên bản tăng, thời hạn, phạm vi khóa và danh sách thu hồi. **Fail closed** khi chữ ký sai/bị thu hồi; chặn downgrade/replay. **Chưa** viết cơ chế A/B custom cho v1. Snapshot filesystem (nếu dùng) phải phục hồi thực; DB và tài liệu backup riêng.

## Lý do

- Tự phát minh giao thức chữ ký dễ sai; TUF giải quyết replay/rollback/key-rotation đã được kiểm chứng.
- Hash đơn lẻ chỉ kiểm toàn vẹn so với giá trị kỳ vọng, không chứng minh nhà phát hành (SEC-006); cần chữ ký + revocation.
- Key production KHÔNG nằm trong repo/ISO/CI không tin cậy (SEC-007).

## Hệ quả

- Khi offline: app đã cài chạy theo chính sách đã công bố; metadata hết hạn KHÔNG được coi là xác nhận tương thích mới; catalog KHÔNG điều khiển lệnh root.
- Phân biệt rõ rollback package / OS snapshot / prefix / restore dữ liệu / restore DB (UPD-003). APT downgrade không đảm bảo hoàn nguyên migration.
- Không dùng checksum tự xuất bản làm bằng chứng nguồn đáng tin.

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Logic verify metadata (phiên bản/thời hạn/revocation/fail-closed) có thể **viết + test ở M1** bằng Python thuần với fixture ký giả (dev key gắn nhãn lab).
- Cập nhật OS qua APT và snapshot filesystem thực cần máy cài thật → thuộc M3/M4, hiện **BLOCKED** tại host container này.

## Spike cần làm + điều kiện chấp nhận

- **Spike:** key separation; expired/replayed metadata; offline policy; revocation; interrupted package transaction; kernel fallback; restore (SEC-10, UPD-02, UPD-03).
- **Điều kiện chấp nhận:** đánh giá TUF đạt tiêu chí (hoặc ghi ADR thay thế); ký sai/replay/downgrade/key revoked bị từ chối fail-closed, không install mới; không dùng checksum tự publish làm bằng chứng nguồn.
