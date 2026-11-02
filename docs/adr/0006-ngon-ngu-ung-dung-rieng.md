# ADR 0006 — Ngôn ngữ và stack cho phần mềm riêng

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §5.1, §5.2, §12; requirement CLI-004, SEC-001

## Bối cảnh

Phần phát triển riêng (trung tâm ứng dụng, bộ điều phối compat, helper đặc quyền, doctor, diagnostics) cần một stack dễ đóng gói trong Debian, chạy Linux độc lập, và tách nhỏ quyền.

## Quyết định

Dùng **Python 3** cho CLI/service và **PySide6 (Qt Quick)** cho UI. **Helper đặc quyền tách nhỏ, least privilege**, giao tiếp qua **D-Bus/Polkit** với phương thức có kiểu rõ ràng (ví dụ `GetSystemCapabilities`, `PlanPackageInstall`, `ApplyApprovedPackagePlan`, `GetUpdateStatus`). **Không** có `RunCommand`; **không** mở HTTP localhost điều khiển đặc quyền; **không** dùng .NET Framework cho công cụ cốt lõi.

## Lý do

- Python + Qt/PySide thuận tiện đóng gói Debian và phát triển; chạy Linux độc lập (không kéo .NET Framework — công nghệ Windows, [S08]).
- Helper least privilege giảm bề mặt tấn công; caller không truyền repo/key/package tùy ý ngoài allowlist đã phát hành.

## Hệ quả

- JSON output phải có `api_version/operation_id/status/data/warnings/error`, không trộn log vào stdout JSON; exit code theo CLI-003.
- Thao tác phân vùng dùng installer chuyên dụng, không qua app-center helper.

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Host hiện tại có **python 3.11.2 + venv + pip + node v24** → **CLI/service/validator/doctor/state store viết + test được ngay ở M1**.
- **UI PySide6 chưa kiểm chứng** ở đây (môi trường headless, chưa cài Qt); phần GUI + accessibility + startup cost thuộc M3.

## Spike cần làm + điều kiện chấp nhận

- **Spike:** version PySide6/Qt khả dụng trong Debian 13; giấy phép Qt/PySide; desktop integration; accessibility (UX-005); startup cost; packaging .deb.
- **Điều kiện chấp nhận:** stack đóng gói được trong Debian với giấy phép tương thích; nếu đổi stack phải có ADR mới kèm chi phí bảo trì + migration. Negative test SEC-01 (caller không hợp lệ bị Polkit/helper từ chối) đạt.

## Nguồn

- [S08] Microsoft về .NET Framework — https://github.com/dotnet/docs/blob/main/docs/framework/install/on-windows-and-server.md
