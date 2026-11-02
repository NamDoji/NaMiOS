# ADR 0004 — Hồ sơ khai báo thay cho script

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §5.2, §9, §11, §12; requirement COMP-004, CLI-001, NET-001

## Bối cảnh

Cách cài/chạy ứng dụng (đặc biệt qua Wine) cần được mô tả theo dữ liệu có thể kiểm duyệt, thay vì script tùy ý — vì manifest/catalog có thể đến từ nguồn không hoàn toàn tin cậy và app Windows là mã không tin cậy.

## Quyết định

Catalog chỉ chứa **recipe là hành động khai báo có allowlist** (`create_prefix`, `install_dependency` đã xét duyệt, `set_registry_value` trong danh sách, `run_installer` do người dùng cung cấp, `verify_file`, `create_launcher`). **Cấm** trường `shell`, `eval`, URL-script, template nội suy thành lệnh, và lệnh root tùy ý. Tham số truyền bằng **argv array**, không ghép chuỗi thành shell. **Tách ba lớp:** manifest (bất biến, mô tả) / local state / evidence.

## Lý do

- "Schema hợp lệ" ≠ "an toàn để chạy": cần validation 2 tầng — JSON Schema (cấu trúc) + **semantic validator** (chặn profile TBD, runner chưa pin, dependency chưa duyệt, unknown keys, chứng nhận thiếu evidence, hash/revocation).
- Tách manifest/state/evidence để dữ liệu cài đặt không bị nhầm thành chứng nhận.

## Hệ quả

- Mọi hành động không nằm trong allowlist bị từ chối trước khi thực thi.
- Parser đầu vào (gồm phân tích .NET tĩnh) phải giới hạn kích thước/thời gian/quyền và không thực thi binary để nhận diện (NET-001).

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Host hiện tại có **python 3.11 + venv + pytest (cài được)** → **đủ để viết và test semantic validator ở M1 ngay tại đây** (lõi Python thuần, không cần Wine/KVM).
- Đây là một trong số ít phần có thể hiện thực hóa + kiểm thử negative đầy đủ trong môi trường hiện tại.

## Spike cần làm + điều kiện chấp nhận

- **Spike:** semantic validator; test invalid properties/unknown keys; injection (filename có space/dấu/shell metachar coi là argv); path traversal/symlink/TOCTOU; stale plan; rollback interrupted install (MAN-01..04, SEC-02/03/04).
- **Điều kiện chấp nhận:** manifest có `shell`/trường lạ/params sai type/dependency chưa duyệt bị từ chối **trước khi tạo process**; profile TBD parse được nhưng install-readiness bị từ chối.
